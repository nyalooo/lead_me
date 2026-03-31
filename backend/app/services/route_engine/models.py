"""Route engine database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Route(Base):
    """A cached route between two points."""

    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_lat: Mapped[float] = mapped_column(Float)
    origin_lng: Mapped[float] = mapped_column(Float)
    destination_lat: Mapped[float] = mapped_column(Float)
    destination_lng: Mapped[float] = mapped_column(Float)
    polyline: Mapped[str] = mapped_column(String, nullable=True)
    distance_km: Mapped[float] = mapped_column(Float)
    base_duration_min: Mapped[float] = mapped_column(Float)
    capacity_estimate: Mapped[int] = mapped_column(Integer, default=1000)
    active_commuters: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class RouteAssignment(Base):
    """An assignment of a specific route to a user for a trip."""

    __tablename__ = "route_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("routes.id"))
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id"), nullable=True
    )

    # Trip details
    origin_lat: Mapped[float] = mapped_column(Float)
    origin_lng: Mapped[float] = mapped_column(Float)
    destination_lat: Mapped[float] = mapped_column(Float)
    destination_lng: Mapped[float] = mapped_column(Float)
    detour_percent: Mapped[float] = mapped_column(Float, default=0.0)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="assigned")  # assigned, active, completed, cancelled
    compliant: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    coins_earned: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LocationUpdate(Base):
    """GPS location updates during an active route."""

    __tablename__ = "location_updates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_assignments.id"), index=True
    )
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    accuracy_m: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
