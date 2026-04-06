from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app import db
from app.middleware import get_current_user, require_baby_access

router = APIRouter()


class PoopEntry(BaseModel):
    datetime: str
    poop_type: str
    notes: Optional[str] = ""


class PoopUpdate(BaseModel):
    datetime: str
    poop_type: str
    notes: Optional[str] = ""


@router.post("/api/babies/{baby_id}/poops")
async def log_poop(baby_id: str, entry: PoopEntry, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    occurred_at = datetime.fromisoformat(entry.datetime)

    await db.execute(
        """INSERT INTO poops (baby_id, logged_by, occurred_at, poop_type, notes)
           VALUES ($1, $2, $3, $4, $5)""",
        baby_id, user["id"], occurred_at, entry.poop_type, entry.notes or "",
    )
    return {"status": "ok", "message": "Poop logged"}


@router.get("/api/babies/{baby_id}/poops")
async def get_poops(baby_id: str, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    rows = await db.fetch(
        """SELECT id, occurred_at, poop_type, notes
           FROM poops WHERE baby_id = $1
           ORDER BY occurred_at DESC""",
        baby_id,
    )
    return [
        {
            "id": str(r["id"]),
            "date": r["occurred_at"].strftime("%m/%d/%Y"),
            "time": r["occurred_at"].strftime("%I:%M %p"),
            "poop_type": r["poop_type"],
            "notes": r["notes"],
        }
        for r in rows
    ]


@router.put("/api/babies/{baby_id}/poops/{entry_id}")
async def update_poop(baby_id: str, entry_id: str, entry: PoopUpdate, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    occurred_at = datetime.fromisoformat(entry.datetime)
    result = await db.execute(
        """UPDATE poops SET occurred_at = $1, poop_type = $2, notes = $3
           WHERE id = $4 AND baby_id = $5""",
        occurred_at, entry.poop_type, entry.notes or "", entry_id, baby_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(404, "Entry not found")
    return {"status": "ok"}


@router.delete("/api/babies/{baby_id}/poops/{entry_id}")
async def delete_poop(baby_id: str, entry_id: str, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    result = await db.execute(
        "DELETE FROM poops WHERE id = $1 AND baby_id = $2", entry_id, baby_id
    )
    if result == "DELETE 0":
        raise HTTPException(404, "Entry not found")
    return {"status": "ok"}
