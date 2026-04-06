from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from app import db
from app.middleware import get_current_user, require_baby_access

router = APIRouter()


class SleepEntry(BaseModel):
    start_time: str
    end_time: str
    notes: Optional[str] = ""


class SleepUpdate(BaseModel):
    start_time: str
    end_time: str
    notes: Optional[str] = ""


def _calc_sleep(start_str: str, end_str: str):
    start = datetime.fromisoformat(start_str)
    end = datetime.fromisoformat(end_str)
    if end <= start:
        end = end + timedelta(days=1)
    duration_hrs = round((end - start).total_seconds() / 3600, 2)
    return start, end, duration_hrs


@router.post("/api/babies/{baby_id}/sleep")
async def log_sleep(baby_id: str, entry: SleepEntry, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    start, end, duration_hrs = _calc_sleep(entry.start_time, entry.end_time)

    await db.execute(
        """INSERT INTO sleeps (baby_id, logged_by, start_time, end_time, duration_hrs, notes)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        baby_id, user["id"], start, end, duration_hrs, entry.notes or "",
    )
    return {"status": "ok", "message": "Sleep logged"}


@router.get("/api/babies/{baby_id}/sleep")
async def get_sleeps(baby_id: str, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    rows = await db.fetch(
        """SELECT id, start_time, end_time, duration_hrs, notes
           FROM sleeps WHERE baby_id = $1
           ORDER BY start_time DESC""",
        baby_id,
    )
    return [
        {
            "id": str(r["id"]),
            "start_date": r["start_time"].strftime("%m/%d/%Y"),
            "start_time": r["start_time"].strftime("%I:%M %p"),
            "end_date": r["end_time"].strftime("%m/%d/%Y"),
            "end_time": r["end_time"].strftime("%I:%M %p"),
            "duration_hrs": r["duration_hrs"],
            "notes": r["notes"],
        }
        for r in rows
    ]


@router.put("/api/babies/{baby_id}/sleep/{entry_id}")
async def update_sleep(baby_id: str, entry_id: str, entry: SleepUpdate, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    start, end, duration_hrs = _calc_sleep(entry.start_time, entry.end_time)
    result = await db.execute(
        """UPDATE sleeps SET start_time = $1, end_time = $2, duration_hrs = $3, notes = $4
           WHERE id = $5 AND baby_id = $6""",
        start, end, duration_hrs, entry.notes or "", entry_id, baby_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(404, "Entry not found")
    return {"status": "ok"}


@router.delete("/api/babies/{baby_id}/sleep/{entry_id}")
async def delete_sleep(baby_id: str, entry_id: str, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    result = await db.execute(
        "DELETE FROM sleeps WHERE id = $1 AND baby_id = $2", entry_id, baby_id
    )
    if result == "DELETE 0":
        raise HTTPException(404, "Entry not found")
    return {"status": "ok"}
