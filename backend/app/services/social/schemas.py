"""Social & referral request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReferralCodeResponse(BaseModel):
    code: str
    uses: int
    max_uses: int | None = None
    active: bool
    share_url: str

    model_config = {"from_attributes": True}


class ReferralStatsResponse(BaseModel):
    referral_code: str
    total_referrals: int
    qualified_referrals: int
    total_coins_earned: int
    referrals: list["ReferralEntry"]


class ReferralEntry(BaseModel):
    referred_display_name: str
    qualified: bool
    coins_earned: int
    created_at: datetime


class ApplyReferralRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=20)


class ApplyReferralResponse(BaseModel):
    applied: bool
    message: str
    bonus_coins: int = 0


class ShareRequest(BaseModel):
    channel: str = Field(..., pattern="^(whatsapp|copy_link|twitter)$")
    content_type: str = Field(..., pattern="^(referral|achievement|challenge|route)$")
    content_id: str | None = None


class ShareResponse(BaseModel):
    shared: bool
    share_url: str
    message: str
