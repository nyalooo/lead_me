"""Challenges & events database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Challenge(Base):
    """A time-bound challenge that users can join for bonus rewards."""

    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(30))  # weekly, monthly, event, flash
    category: Mapped[str] = mapped_column(String(30), default="general")  # general, area, peak, monsoon, festival

    # Goal
    goal_type: Mapped[str] = mapped_column(String(30))  # routes_count, distance_km, peak_routes, area_routes, streak_days
    goal_value: Mapped[int] = mapped_column(Integer)
    goal_area: Mapped[str | None] = mapped_column(String(100), nullable=True)  # specific area for area challenges

    # Rewards
    reward_coins: Mapped[int] = mapped_column(Integer, default=0)
    reward_xrp: Mapped[float] = mapped_column(Float, default=0.0)
    reward_badge_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # optional badge unlock

    # Timing
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Limits
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)  # null = unlimited
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Sponsor link (Phase 3 sponsor pools)
    sponsor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ChallengeParticipant(Base):
    """Tracks a user's enrollment and progress in a challenge."""

    __tablename__ = "challenge_participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("challenges.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    progress: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_claimed: Mapped[bool] = mapped_column(Boolean, default=False)

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
