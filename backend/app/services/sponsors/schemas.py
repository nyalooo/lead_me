"""Sponsor reward pool request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SponsorResponse(BaseModel):
    id: UUID
    name: str
    description: str
    logo_url: str | None = None
    website_url: str | None = None
    active: bool

    model_config = {"from_attributes": True}


class RewardPoolResponse(BaseModel):
    id: UUID
    sponsor_id: UUID
    sponsor_name: str = ""
    title: str
    description: str
    currency: str
    total_amount: float
    remaining_amount: float
    reward_per_route: float
    target_area: str | None = None
    min_compliance: float
    starts_at: datetime
    ends_at: datetime
    active: bool
    total_payouts: int

    model_config = {"from_attributes": True}


class RewardPoolListResponse(BaseModel):
    active: list[RewardPoolResponse]
    upcoming: list[RewardPoolResponse]
    depleted: list[RewardPoolResponse]


class CreateSponsorRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: str = ""
    logo_url: str | None = None
    website_url: str | None = None
    contact_email: str | None = None


class CreateRewardPoolRequest(BaseModel):
    sponsor_id: UUID
    title: str = Field(..., min_length=3, max_length=200)
    description: str = ""
    currency: str = Field("XRP", pattern="^(XRP|SOL|ETH)$")
    total_amount: float = Field(..., gt=0)
    reward_per_route: float = Field(..., gt=0)
    target_area: str | None = None
    target_route_id: UUID | None = None
    min_compliance: float = Field(0.8, ge=0, le=1)
    starts_at: datetime
    ends_at: datetime


class PoolPayoutResponse(BaseModel):
    pool_title: str
    sponsor_name: str
    amount: float
    currency: str
    created_at: datetime
