import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from app import db
from app.middleware import get_current_user
from app.email_service import send_invite
import os

router = APIRouter()


class CreateBabyRequest(BaseModel):
    name: str


class InviteRequest(BaseModel):
    email: str


@router.post("/api/babies")
async def create_baby(req: CreateBabyRequest, request: Request):
    user = await get_current_user(request)
    name = req.name.strip()
    if not name:
        raise HTTPException(400, "Baby name is required")

    baby = await db.fetchrow(
        "INSERT INTO babies (name, created_by) VALUES ($1, $2) RETURNING id, name",
        name, user["id"],
    )
    await db.execute(
        "INSERT INTO baby_access (baby_id, user_id, role) VALUES ($1, $2, 'owner')",
        baby["id"], user["id"],
    )
    return {"id": str(baby["id"]), "name": baby["name"], "role": "owner"}


@router.get("/api/babies")
async def list_babies(request: Request):
    user = await get_current_user(request)
    babies = await db.fetch(
        """SELECT b.id, b.name, ba.role
           FROM babies b JOIN baby_access ba ON b.id = ba.baby_id
           WHERE ba.user_id = $1 ORDER BY b.created_at""",
        user["id"],
    )
    return [{"id": str(b["id"]), "name": b["name"], "role": b["role"]} for b in babies]


@router.post("/api/babies/{baby_id}/invite")
async def invite_caregiver(baby_id: str, req: InviteRequest, request: Request):
    user = await get_current_user(request)
    access = await db.fetchrow(
        "SELECT role FROM baby_access WHERE baby_id = $1 AND user_id = $2",
        baby_id, user["id"],
    )
    if not access or access["role"] != "owner":
        raise HTTPException(403, "Only the owner can invite caregivers")

    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Invalid email")

    # Check if already has access
    existing = await db.fetchrow(
        """SELECT ba.id FROM baby_access ba
           JOIN users u ON u.id = ba.user_id
           WHERE ba.baby_id = $1 AND u.email = $2""",
        baby_id, email,
    )
    if existing:
        raise HTTPException(400, "This person already has access")

    baby = await db.fetchrow("SELECT name FROM babies WHERE id = $1", baby_id)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    await db.execute(
        "INSERT INTO invites (baby_id, invited_by, email, token, expires_at) VALUES ($1, $2, $3, $4, $5)",
        baby_id, user["id"], email, token, expires_at,
    )
    await send_invite(email, token, baby["name"], user["name"])
    return {"status": "ok", "message": f"Invite sent to {email}"}


@router.get("/invite/accept")
async def accept_invite(token: str):
    invite = await db.fetchrow(
        "SELECT id, baby_id, email, accepted, expires_at FROM invites WHERE token = $1",
        token,
    )
    if not invite:
        raise HTTPException(400, "Invalid invite")
    if invite["accepted"]:
        raise HTTPException(400, "Invite already accepted")
    if invite["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(400, "Invite expired")

    await db.execute("UPDATE invites SET accepted = true WHERE id = $1", invite["id"])

    # Find or create user
    user = await db.fetchrow("SELECT id FROM users WHERE email = $1", invite["email"])
    if not user:
        user = await db.fetchrow(
            "INSERT INTO users (email) VALUES ($1) RETURNING id", invite["email"]
        )

    # Grant access (ignore if already exists)
    await db.execute(
        """INSERT INTO baby_access (baby_id, user_id, role) VALUES ($1, $2, 'caregiver')
           ON CONFLICT (baby_id, user_id) DO NOTHING""",
        invite["baby_id"], user["id"],
    )

    # Create session
    session_token = secrets.token_urlsafe(32)
    max_age_days = int(os.getenv("SESSION_MAX_AGE_DAYS", "90"))
    expires_at = datetime.now(timezone.utc) + timedelta(days=max_age_days)
    await db.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES ($1, $2, $3)",
        user["id"], session_token, expires_at,
    )

    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        "olive_session",
        session_token,
        max_age=max_age_days * 86400,
        httponly=True,
        samesite="lax",
        secure=os.getenv("SECURE_COOKIES", "false").lower() == "true",
    )
    return response


@router.get("/api/babies/{baby_id}/caregivers")
async def list_caregivers(baby_id: str, request: Request):
    user = await get_current_user(request)
    access = await db.fetchrow(
        "SELECT 1 FROM baby_access WHERE baby_id = $1 AND user_id = $2",
        baby_id, user["id"],
    )
    if not access:
        raise HTTPException(403, "No access")

    caregivers = await db.fetch(
        """SELECT u.id, u.email, u.name, ba.role
           FROM baby_access ba JOIN users u ON u.id = ba.user_id
           WHERE ba.baby_id = $1 ORDER BY ba.created_at""",
        baby_id,
    )
    return [
        {"id": str(c["id"]), "email": c["email"], "name": c["name"], "role": c["role"]}
        for c in caregivers
    ]
