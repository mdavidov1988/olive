from fastapi import APIRouter, Request
from app import db
from app.middleware import get_current_user, require_baby_access

router = APIRouter()


@router.get("/api/babies/{baby_id}/summary")
async def today_summary(baby_id: str, request: Request, tz_offset: int = 0):
    user = await get_current_user(request)
    await require_baby_access(request, user, baby_id)

    # tz_offset is minutes from UTC (e.g., -300 for EST)
    # We calculate "today" in the user's timezone
    offset_interval = f"{-tz_offset} minutes"

    feedings_count = await db.fetchval(
        f"""SELECT COUNT(*) FROM feedings
           WHERE baby_id = $1
           AND (occurred_at AT TIME ZONE 'UTC' + interval '{offset_interval}')::date
               = (now() AT TIME ZONE 'UTC' + interval '{offset_interval}')::date""",
        baby_id,
    )

    total_oz = await db.fetchval(
        f"""SELECT COALESCE(SUM(amount_oz), 0) FROM feedings
           WHERE baby_id = $1
           AND (occurred_at AT TIME ZONE 'UTC' + interval '{offset_interval}')::date
               = (now() AT TIME ZONE 'UTC' + interval '{offset_interval}')::date""",
        baby_id,
    )

    poops_count = await db.fetchval(
        f"""SELECT COUNT(*) FROM poops
           WHERE baby_id = $1
           AND (occurred_at AT TIME ZONE 'UTC' + interval '{offset_interval}')::date
               = (now() AT TIME ZONE 'UTC' + interval '{offset_interval}')::date""",
        baby_id,
    )

    sleep_hrs = await db.fetchval(
        f"""SELECT COALESCE(SUM(duration_hrs), 0) FROM sleeps
           WHERE baby_id = $1
           AND (start_time AT TIME ZONE 'UTC' + interval '{offset_interval}')::date
               = (now() AT TIME ZONE 'UTC' + interval '{offset_interval}')::date""",
        baby_id,
    )

    latest_weight = await db.fetchrow(
        """SELECT pounds, ounces, total_lbs, occurred_at
           FROM weights WHERE baby_id = $1
           ORDER BY occurred_at DESC LIMIT 1""",
        baby_id,
    )

    weight_data = None
    if latest_weight:
        weight_data = {
            "pounds": latest_weight["pounds"],
            "ounces": latest_weight["ounces"],
            "total_lbs": latest_weight["total_lbs"],
            "date": latest_weight["occurred_at"].strftime("%m/%d/%Y"),
        }

    return {
        "feedings_count": feedings_count,
        "feedings_total_oz": round(total_oz, 1),
        "poops_count": poops_count,
        "sleep_hrs": round(sleep_hrs, 1),
        "latest_weight": weight_data,
    }
