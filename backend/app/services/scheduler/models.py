"""Scheduler database models."""

import uuid
from datetime import datetime, time, timezone

from sqlalchemy import Boolean, DateTime, Float, String, Time, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Schedule(Base):
    """A user's pre-planned commute schedule."""

    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # Schedule type: recurring, one_time, flexible
    type: Mapped[str] = mapped_column(String(20))

    # Origin and destination
    origin_lat: Mapped[float] = mapped_column(Float)
    origin_lng: Mapped[float] = mapped_column(Float)
    origin_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    destination_lat: Mapped[float] = mapped_column(Float)
    destination_lng: Mapped[float] = mapped_column(Float)
    destination_label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Recurring fields
    days: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)  # ["mon","tue",...]
    departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    # One-time fields
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Flexible fields
    departure_earliest: Mapped[time | None] = mapped_column(Time, nullable=True)
    departure_latest: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
