"""User request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: UUID
    phone: str
    display_name: str
    area: str | None
    tier: str
    xrp_wallet_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = None
    area: str | None = None
    xrp_wallet_address: str | None = None


class UserStats(BaseModel):
    total_routes: int
    total_coins: int
    compliance_rate: float
    tier: str
    xrp_equivalent: float
    member_since: datetime
