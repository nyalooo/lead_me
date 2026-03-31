"""Pre-assignment cron job for scheduled commutes.

Runs periodically (typically early morning) to pre-assign routes
for all upcoming scheduled commutes. This allows the route engine
to globally optimize route distribution across all commuters.

Usage:
    # As a standalone script:
    python -m app.services.scheduler.jobs

    # Or via the API endpoint:
    POST /api/v1/schedules/pre-assign
"""

import asyncio
import logging
from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.services.route_engine.schemas import LatLng
from app.services.route_engine.service import assign_best_route, get_or_create_routes
from app.services.scheduler.models import Schedule

logger = logging.getLogger(__name__)

# Map day names to Python weekday numbers (Monday=0)
DAY_TO_WEEKDAY = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3,
    "fri": 4, "sat": 5, "sun": 6,
}


def is_scheduled_for_date(schedule: Schedule, target_date: date) -> bool:
    """Check if a recurring schedule runs on the given date."""
    if schedule.type == "recurring":
        weekday = target_date.weekday()
        return any(DAY_TO_WEEKDAY.get(d) == weekday for d in (schedule.days or []))
    elif schedule.type == "one_time":
        if schedule.scheduled_date:
            return schedule.scheduled_date.date() == target_date
    elif schedule.type == "flexible":
        if schedule.scheduled_date:
            return schedule.scheduled_date.date() == target_date
    return False


async def pre_assign_routes(
    target_date: date | None = None,
    db: AsyncSession | None = None,
) -> dict:
    """Pre-assign routes for all schedules on the target date.

    Returns a summary: {"total_schedules": N, "assigned": N, "errors": N}
    """
    if target_date is None:
        target_date = date.today()

    own_session = db is None
    if own_session:
        session = async_session()
    else:
        session = db

    try:
        # Fetch all active schedules
        result = await session.execute(
            select(Schedule).where(Schedule.active.is_(True))
        )
        schedules = list(result.scalars().all())

        total = 0
        assigned = 0
        errors = 0

        for schedule in schedules:
            if not is_scheduled_for_date(schedule, target_date):
                continue

            total += 1
            try:
                origin = LatLng(lat=schedule.origin_lat, lng=schedule.origin_lng)
                destination = LatLng(lat=schedule.destination_lat, lng=schedule.destination_lng)

                # Determine departure time for traffic-aware routing
                departure_dt = None
                if schedule.departure_time:
                    departure_dt = datetime.combine(
                        target_date, schedule.departure_time, tzinfo=timezone.utc
                    )
                elif schedule.departure_earliest:
                    # For flexible schedules, use the middle of the window
                    earliest = schedule.departure_earliest
                    latest = schedule.departure_latest or earliest
                    mid_seconds = (
                        earliest.hour * 3600 + earliest.minute * 60 +
                        latest.hour * 3600 + latest.minute * 60
                    ) // 2
                    mid_time = time(mid_seconds // 3600, (mid_seconds % 3600) // 60)
                    departure_dt = datetime.combine(target_date, mid_time, tzinfo=timezone.utc)

                routes = await get_or_create_routes(origin, destination, session, departure_dt)
                await assign_best_route(
                    routes, schedule.user_id, origin, destination, session,
                    schedule_id=schedule.id,
                )
                assigned += 1

            except Exception as e:
                logger.error(f"Failed to pre-assign route for schedule {schedule.id}: {e}")
                errors += 1

        if own_session:
            await session.commit()

        summary = {"date": str(target_date), "total_schedules": total, "assigned": assigned, "errors": errors}
        logger.info(f"Pre-assignment complete: {summary}")
        return summary

    finally:
        if own_session:
            await session.close()


# Allow running as a standalone script: python -m app.services.scheduler.jobs
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(pre_assign_routes())
    print(result)
