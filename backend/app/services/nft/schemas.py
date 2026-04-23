"""NFT badge request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MintNFTRequest(BaseModel):
    user_badge_id: UUID
    chain: str = Field("xrpl", pattern="^(xrpl|solana|ethereum)$")
    wallet_address: str = Field(..., min_length=10)


class NFTBadgeResponse(BaseModel):
    id: UUID
    badge_id: str
    badge_name: str = ""
    chain: str
    token_id: str | None = None
    tx_hash: str | None = None
    wallet_address: str
    explorer_url: str | None = None
    metadata_uri: str | None = None
    status: str
    created_at: datetime
    minted_at: datetime | None = None

    model_config = {"from_attributes": True}


class NFTListResponse(BaseModel):
    nfts: list[NFTBadgeResponse]
    total: int


class MintStatusResponse(BaseModel):
    nft_id: UUID
    status: str
    tx_hash: str | None = None
    explorer_url: str | None = None
    message: str
