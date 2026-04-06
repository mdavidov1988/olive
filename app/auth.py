import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from app import db
from app.email_service import send_magic_link
import os

router = APIRouter()


class LoginRequest(BaseModel):
    email: str


class UpdateNameRequest(BaseModel):
    name: str


@router.post("/api/auth/login")
async def login(req: LoginRequest):
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Invalid email")

    token = secrets.token_urlsafe(32)
    expiry_min = int(os.getenv("MAGIC_LINK_EXPIRY_MINUTES", "15"))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_min)

    await db.execute(
        "INSERT INTO magic_links (email, token, expires_at) VALUES ($1, $2, $3)",
        email, token, expires_at,
    )
    await send_magic_link(email, token)
    return {"status": "ok", "message": "Check your email for a login link"}


@router.get("/auth/verify")
async def verify(token: str):
    link = await db.fetchrow(
        "SELECT id, email, used, expires_at FROM magic_links WHERE token = $1",
        token,
    )
    if not link:
        raise HTTPException(400, "Invalid link")
    if link["used"]:
        raise HTTPException(400, "Link already used")
    if link["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(400, "Link expired")

    await db.execute("UPDATE magic_links SET used = true WHERE id = $1", link["id"])

    # Find or create user
    user = await db.fetchrow("SELECT id FROM users WHERE email = $1", link["email"])
    if not user:
        user = await db.fetchrow(
            "INSERT INTO users (email) VALUES ($1) RETURNING id", link["email"]
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


@router.get("/api/auth/me")
async def me(request: Request):
    from app.middleware import get_current_user
    user = await get_current_user(request)
    babies = await db.fetch(
        """SELECT b.id, b.name, ba.role
           FROM babies b JOIN baby_access ba ON b.id = ba.baby_id
           WHERE ba.user_id = $1 ORDER BY b.created_at""",
        user["id"],
    )
    return {
        "user": {"id": str(user["id"]), "email": user["email"], "name": user["name"]},
        "babies": [{"id": str(b["id"]), "name": b["name"], "role": b["role"]} for b in babies],
    }


@router.post("/api/auth/logout")
async def logout(request: Request):
    token = request.cookies.get("olive_session")
    if token:
        await db.execute("DELETE FROM sessions WHERE token = $1", token)
    response = JSONResponse({"status": "ok"})
    response.delete_cookie("olive_session")
    return response


@router.post("/api/auth/update-name")
async def update_name(req: UpdateNameRequest, request: Request):
    from app.middleware import get_current_user
    user = await get_current_user(request)
    await db.execute("UPDATE users SET name = $1 WHERE id = $2", req.name.strip(), user["id"])
    return {"status": "ok"}
