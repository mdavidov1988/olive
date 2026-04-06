from fastapi import Request, HTTPException
from app import db


async def get_current_user(request: Request):
    token = request.cookies.get("olive_session")
    if not token:
        raise HTTPException(401, "Not authenticated")
    session = await db.fetchrow(
        "SELECT user_id FROM sessions WHERE token = $1 AND expires_at > now()",
        token,
    )
    if not session:
        raise HTTPException(401, "Session expired")
    user = await db.fetchrow("SELECT id, email, name FROM users WHERE id = $1", session["user_id"])
    if not user:
        raise HTTPException(401, "User not found")
    return user


async def require_baby_access(request: Request, user: dict, baby_id: str):
    access = await db.fetchrow(
        "SELECT role FROM baby_access WHERE baby_id = $1 AND user_id = $2",
        baby_id, user["id"],
    )
    if not access:
        raise HTTPException(403, "No access to this baby")
    return access["role"]
