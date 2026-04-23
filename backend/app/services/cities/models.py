"""City configuration database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class City(Base):
    """A city where LeadMe operates."""

    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(50), default="India")
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")

    # Bounding box
    lat_min: Mapped[float] = mapped_column(Float)
    lat_max: Mapped[float] = mapped_column(Float)
    lng_min: Mapped[float] = mapped_column(Float)
    lng_max: Mapped[float] = mapped_column(Float)

    # City center (for map defaults)
    center_lat: Mapped[float] = mapped_column(Float)
    center_lng: Mapped[float] = mapped_column(Float)
    default_zoom: Mapped[int] = mapped_column(Integer, default=12)

    # Areas within the city
    areas: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Peak hours (can differ per city)
    peak_hours: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    launched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
