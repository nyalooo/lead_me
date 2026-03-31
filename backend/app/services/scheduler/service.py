"""Scheduler business logic — manage commute schedules and pre-assignment."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.scheduler.models import Schedule
from app.services.scheduler.schemas import ScheduleCreate, ScheduleUpdate


async def create_schedule(user_id: uuid.UUID, data: ScheduleCreate, db: AsyncSession) -> Schedule:
    """Create a new commute schedule."""
    schedule = Schedule(
        user_id=user_id,
        type=data.type,
        origin_lat=data.origin.lat,
        origin_lng=data.origin.lng,
        origin_label=data.origin.label,
        destination_lat=data.destination.lat,
        destination_lng=data.destination.lng,
        destination_label=data.destination.label,
        days=data.days,
        departure_time=data.departure_time,
        scheduled_date=data.scheduled_date,
        departure_earliest=data.departure_window.earliest if data.departure_window else None,
        departure_latest=data.departure_window.latest if data.departure_window else None,
    )
    db.add(schedule)
    await db.flush()
    return schedule


async def list_schedules(
    user_id: uuid.UUID,
    db: AsyncSession,
    schedule_type: str | None = None,
    active_only: bool = True,
) -> list[Schedule]:
    """List schedules for a user with optional filters."""
    query = select(Schedule).where(Schedule.user_id == user_id)
    if schedule_type:
        query = query.where(Schedule.type == schedule_type)
    if active_only:
        query = query.where(Schedule.active.is_(True))
    query = query.order_by(Schedule.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_schedule(schedule_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Schedule | None:
    """Get a specific schedule belonging to a user."""
    result = await db.execute(
        select(Schedule).where(Schedule.id == schedule_id, Schedule.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_schedule(
    schedule: Schedule,
    data: ScheduleUpdate,
    db: AsyncSession,
) -> Schedule:
    """Update an existing schedule."""
    if data.days is not None:
        schedule.days = data.days
    if data.departure_time is not None:
        schedule.departure_time = data.departure_time
    if data.scheduled_date is not None:
        schedule.scheduled_date = data.scheduled_date
    if data.departure_window is not None:
        schedule.departure_earliest = data.departure_window.earliest
        schedule.departure_latest = data.departure_window.latest
    if data.active is not None:
        schedule.active = data.active
    db.add(schedule)
    await db.flush()
    return schedule


async def delete_schedule(schedule: Schedule, db: AsyncSession) -> None:
    """Delete a schedule."""
    await db.delete(schedule)
    await db.flush()
