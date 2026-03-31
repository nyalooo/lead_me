"""Cashout database models — wallet links and cashout requests."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WalletLink(Base):
    """User-linked cryptocurrency wallet addresses.

    Each user can link one wallet per crypto currency.
    Non-custodial: we never hold user funds or private keys.
    """

    __tablename__ = "wallet_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    currency: Mapped[str] = mapped_column(String(10))  # XRP, SOL, ETH
    address: Mapped[str] = mapped_column(String(200))
    label: Mapped[str] = mapped_column(String(100), default="")  # user-friendly name
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CashoutRequest(Base):
    """Record of a cashout (Route Coins → crypto) request.

    Lifecycle: pending → processing → completed / failed
    """

    __tablename__ = "cashout_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    # What the user is cashing out
    coins_amount: Mapped[int] = mapped_column(Integer)  # Route Coins spent
    crypto_amount: Mapped[float] = mapped_column(Float)  # crypto received
    currency: Mapped[str] = mapped_column(String(10))  # XRP, SOL, ETH
    tier_bonus: Mapped[float] = mapped_column(Float, default=1.0)  # multiplier applied

    # Where it's going
    wallet_address: Mapped[str] = mapped_column(String(200))

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, completed, failed
    tx_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    explorer_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
