"""User database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100), default="Commuter")
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    xrp_wallet_address: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Gamification
    tier: Mapped[str] = mapped_column(String(20), default="rookie")  # rookie, regular, pro, legend
    total_routes: Mapped[int] = mapped_column(Integer, default=0)
    total_coins: Mapped[int] = mapped_column(Integer, default=0)
    compliance_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
