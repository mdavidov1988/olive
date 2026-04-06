from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from app import db
from app.middleware import get_current_user, require_baby_access

router = APIRouter()


class FeedingEntry(BaseModel):
    datetime: str
    milk_type: str
    amount_oz: float


class FeedingUpdate(BaseModel):
    datetime: str
    milk_type: str
    amount_oz: float


@router.post("/api/babies/{baby_id}/feedings")
async def log_feeding(baby_id: str, entry: FeedingEntry, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    occurred_at = datetime.fromisoformat(entry.datetime)

    await db.execute(
        """INSERT INTO feedings (baby_id, logged_by, occurred_at, milk_type, amount_oz)
           VALUES ($1, $2, $3, $4, $5)""",
        baby_id, user["id"], occurred_at, entry.milk_type, entry.amount_oz,
    )
    return {"status": "ok", "message": "Feeding logged"}


@router.get("/api/babies/{baby_id}/feedings")
async def get_feedings(baby_id: str, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    rows = await db.fetch(
        """SELECT id, occurred_at, milk_type, amount_oz
           FROM feedings WHERE baby_id = $1
           ORDER BY occurred_at DESC""",
        baby_id,
    )
    return [
        {
            "id": str(r["id"]),
            "date": r["occurred_at"].strftime("%m/%d/%Y"),
            "time": r["occurred_at"].strftime("%I:%M %p"),
            "milk_type": r["milk_type"],
            "amount_oz": r["amount_oz"],
        }
        for r in rows
    ]


@router.put("/api/babies/{baby_id}/feedings/{entry_id}")
async def update_feeding(baby_id: str, entry_id: str, entry: FeedingUpdate, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    occurred_at = datetime.fromisoformat(entry.datetime)
    result = await db.execute(
        """UPDATE feedings SET occurred_at = $1, milk_type = $2, amount_oz = $3
           WHERE id = $4 AND baby_id = $5""",
        occurred_at, entry.milk_type, entry.amount_oz, entry_id, baby_id,
    )
    if result == "UPDATE 0":
        raise HTTPException(404, "Entry not found")
    return {"status": "ok"}


@router.delete("/api/babies/{baby_id}/feedings/{entry_id}")
async def delete_feeding(baby_id: str, entry_id: str, request: Request):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    result = await db.execute(
        "DELETE FROM feedings WHERE id = $1 AND baby_id = $2", entry_id, baby_id
    )
    if result == "DELETE 0":
        raise HTTPException(404, "Entry not found")
    return {"status": "ok"}
