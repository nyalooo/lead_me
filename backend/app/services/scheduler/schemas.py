"""Scheduler request/response schemas."""

from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.services.route_engine.schemas import LatLng


class LabeledLatLng(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    label: str | None = None


class DepartureWindow(BaseModel):
    earliest: time
    latest: time


class ScheduleCreate(BaseModel):
    type: str = Field(..., pattern="^(recurring|one_time|flexible)$")
    origin: LabeledLatLng
    destination: LabeledLatLng

    # Recurring
    days: list[str] | None = None  # ["mon","tue","wed","thu","fri"]
    departure_time: time | None = None

    # One-time
    scheduled_date: datetime | None = None

    # Flexible
    departure_window: DepartureWindow | None = None

    @model_validator(mode="after")
    def validate_type_fields(self):
        if self.type == "recurring":
            if not self.days or not self.departure_time:
                raise ValueError("Recurring schedules require 'days' and 'departure_time'")
        elif self.type == "one_time":
            if not self.scheduled_date:
                raise ValueError("One-time schedules require 'scheduled_date'")
        elif self.type == "flexible":
            if not self.departure_window:
                raise ValueError("Flexible schedules require 'departure_window'")
        return self


class ScheduleUpdate(BaseModel):
    days: list[str] | None = None
    departure_time: time | None = None
    scheduled_date: datetime | None = None
    departure_window: DepartureWindow | None = None
    active: bool | None = None


class NextAssignment(BaseModel):
    date: str
    route_id: UUID | None = None
    assigned_at: datetime | None = None


class ScheduleResponse(BaseModel):
    id: UUID
    type: str
    origin: LabeledLatLng
    destination: LabeledLatLng
    days: list[str] | None = None
    departure_time: time | None = None
    scheduled_date: datetime | None = None
    departure_window: DepartureWindow | None = None
    active: bool
    next_assignment: NextAssignment | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleListResponse(BaseModel):
    schedules: list[ScheduleResponse]
