from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app import db
from app.middleware import get_current_user, require_baby_access

router = APIRouter()


class WeightEntry(BaseModel):
    datetime: str
    input_mode: str = "lbs_oz"  # 'lbs_oz' or 'decimal'
    pounds: Optional[int] = None
    ounces: Optional[float] = None
    decimal_lbs: Optional[float] = None


class WeightUpdate(BaseModel):
    datetime: str
    input_mode: str = "lbs_oz"
    pounds: Optional[int] = None
    ounces: Optional[float] = None
    decimal_lbs: Optional[float] = None


def _normalize_weight(entry):
    if entry.input_mode == "decimal" and entry.decimal_lbs is not None:
        total_lbs = round(entry.decimal_lbs, 2)
        pounds = int(total_lbs)
        ounces = round((total_lbs - pounds) * 16, 1)
    else:
        pounds = entry.pounds or 0
        ounces = entry.ounces or 0.0
        total_lbs = round(pounds + ounces / 16, 2)
    return pounds, ounces, total_lbs


@router.post("/api/babies/{baby_id}/weight")
async def log_weight(baby_id: str, entry: WeightEntry, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    occurred_at = datetime.fromisoformat(entry.datetime)
    pounds, ounces, total_lbs = _normalize_weight(entry)

    await db.execute(
        """INSERT INTO weights (baby_id, logged_by, occurred_at, pounds, ounces, total_lbs, input_mode)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        baby_id, user["id"], occurred_at, pounds, ounces, total_lbs, entry.input_mode,
    )
    return {"status": "ok", "message": "Weight logged"}


@router.get("/api/babies/{baby_id}/weight")
async def get_weights(baby_id: str, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    rows = await db.fetch(
        """SELECT id, occurred_at, pounds, ounces, total_lbs, input_mode
           FROM weights WHERE baby_id = $1
           ORDER BY occurred_at DESC""",
        baby_id,
    )
    return [
        {
            "id": str(r["id"]),
            "date": r["occurred_at"].strftime("%m/%d/%Y"),
            "time": r["occurred_at"].strftime("%I:%M %p"),
            "pounds": r["pounds"],
            "ounces": r["ounces"],
            "total_lbs": r["total_lbs"],
            "input_mode": r["input_mode"],
        }
        for r in rows
    ]


@router.put("/api/babies/{baby_id}/weight/{entry_id}")
async def update_weight(baby_id: str, entry_id: str, entry: WeightUpdate, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    occurred_at = datetime.fromisoformat(entry.datetime)
    pounds, ounces, total_lbs = _normalize_weight(entry)
    result = await db.execute(
        """UPDATE weights SET occurred_at = $1, pounds = $2, ounces = $3,
           total_lbs = $4, input_mode = $5
           WHERE id = $6 AND baby_id = $7""",
        occurred_at, pounds, ounces, total_lbs, entry.input_mode, entry_id, baby_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(404, "Entry not found")
    return {"status": "ok"}


@router.delete("/api/babies/{baby_id}/weight/{entry_id}")
async def delete_weight(baby_id: str, entry_id: str, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    result = await db.execute(
        "DELETE FROM weights WHERE id = $1 AND baby_id = $2", entry_id, baby_id
    )
    if result == "DELETE 0":
        raise HTTPException(404, "Entry not found")
    return {"status": "ok"}
