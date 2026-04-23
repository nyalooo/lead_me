"""Social & referral database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Referral(Base):
    """Tracks referral relationships between users."""

    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    referred_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)

    referrer_coins_earned: Mapped[int] = mapped_column(Integer, default=0)
    referred_coins_earned: Mapped[int] = mapped_column(Integer, default=0)

    referred_qualified: Mapped[bool] = mapped_column(Boolean, default=False)
    qualified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ReferralCode(Base):
    """Unique referral codes for users."""

    __tablename__ = "referral_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ShareEvent(Base):
    """Tracks social sharing actions (WhatsApp, copy link, etc.)."""

    __tablename__ = "share_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(30))  # whatsapp, copy_link, twitter
    content_type: Mapped[str] = mapped_column(String(30))  # referral, achievement, challenge, route
    content_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
