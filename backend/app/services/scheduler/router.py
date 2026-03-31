"""Scheduler API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ScheduleNotFoundError
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.scheduler import service
from app.services.scheduler.schemas import (
    LabeledLatLng,
    ScheduleCreate,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.services.users.models import User

router = APIRouter()


def _schedule_to_response(schedule) -> ScheduleResponse:
    """Convert a Schedule model to a response schema."""
    from app.services.scheduler.schemas import DepartureWindow

    departure_window = None
    if schedule.departure_earliest and schedule.departure_latest:
        departure_window = DepartureWindow(
            earliest=schedule.departure_earliest,
            latest=schedule.departure_latest,
        )

    return ScheduleResponse(
        id=schedule.id,
        type=schedule.type,
        origin=LabeledLatLng(lat=schedule.origin_lat, lng=schedule.origin_lng, label=schedule.origin_label),
        destination=LabeledLatLng(
            lat=schedule.destination_lat, lng=schedule.destination_lng, label=schedule.destination_label
        ),
        days=schedule.days,
        departure_time=schedule.departure_time,
        scheduled_date=schedule.scheduled_date,
        departure_window=departure_window,
        active=schedule.active,
        next_assignment=None,  # TODO: compute from route assignments
        created_at=schedule.created_at,
    )


@router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    type: str | None = Query(None, pattern="^(recurring|one_time|flexible)$"),
    active: bool = Query(True),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    schedules = await service.list_schedules(user.id, db, schedule_type=type, active_only=active)
    return ScheduleListResponse(schedules=[_schedule_to_response(s) for s in schedules])


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    body: ScheduleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    schedule = await service.create_schedule(user.id, body, db)
    return _schedule_to_response(schedule)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    body: ScheduleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    schedule = await service.get_schedule(schedule_id, user.id, db)
    if schedule is None:
        raise ScheduleNotFoundError()
    updated = await service.update_schedule(schedule, body, db)
    return _schedule_to_response(updated)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    schedule = await service.get_schedule(schedule_id, user.id, db)
    if schedule is None:
        raise ScheduleNotFoundError()
    await service.delete_schedule(schedule, db)


@router.post("/pre-assign")
async def trigger_pre_assignment(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger pre-assignment for today's schedules.

    Normally runs as a cron job, but can be triggered via API for testing.
    """
    from app.services.scheduler.jobs import pre_assign_routes

    result = await pre_assign_routes(db=db)
    return result
