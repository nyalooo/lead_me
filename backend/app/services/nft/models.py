"""NFT badge database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NFTBadge(Base):
    """On-chain NFT representation of a badge."""

    __tablename__ = "nft_badges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    badge_id: Mapped[str] = mapped_column(String(50), ForeignKey("badges.id"))
    user_badge_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_badges.id"), unique=True)

    # On-chain data
    chain: Mapped[str] = mapped_column(String(20))  # xrpl, solana, ethereum
    token_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tx_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    wallet_address: Mapped[str] = mapped_column(String(200))
    explorer_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    metadata_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, minted, failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    minted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
