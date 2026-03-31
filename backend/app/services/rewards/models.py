"""Rewards database models — coins, streaks, badges."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CoinTransaction(Base):
    """Ledger of Route Coin transactions."""

    __tablename__ = "coin_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    type: Mapped[str] = mapped_column(String(30))  # route_completion, badge_bonus, streak_bonus, leaderboard_reward
    coins: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(200))

    # Reference to what triggered the reward
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("route_assignments.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Streak(Base):
    """User streak tracking."""

    __tablename__ = "streaks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)

    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_completed_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    streak_freezes_remaining: Mapped[int] = mapped_column(Integer, default=0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Badge(Base):
    """Badge definitions."""

    __tablename__ = "badges"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g., "traffic_hero"
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(300))
    coins_bonus: Mapped[int] = mapped_column(Integer, default=0)
    criteria_type: Mapped[str] = mapped_column(String(50))  # routes_count, streak_days, area_count, etc.
    criteria_value: Mapped[int] = mapped_column(Integer)  # threshold to earn


class UserBadge(Base):
    """Badges earned by users."""

    __tablename__ = "user_badges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    badge_id: Mapped[str] = mapped_column(String(50), ForeignKey("badges.id"))
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
