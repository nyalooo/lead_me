"""Social & referral API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.social.schemas import (
    ApplyReferralRequest,
    ApplyReferralResponse,
    ReferralCodeResponse,
    ReferralStatsResponse,
    ShareRequest,
    ShareResponse,
)
from app.services.social.service import (
    apply_referral_code,
    get_or_create_referral_code,
    get_referral_stats,
    track_share,
)
from app.services.users.models import User

router = APIRouter()


@router.get("/referral-code", response_model=ReferralCodeResponse)
async def get_referral_code(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's referral code."""
    result = await get_or_create_referral_code(user.id, db)
    await db.commit()
    return ReferralCodeResponse(**result)


@router.get("/referral-stats", response_model=ReferralStatsResponse)
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get referral statistics for the current user."""
    result = await get_referral_stats(user.id, db)
    return ReferralStatsResponse(**result)


@router.post("/apply-referral", response_model=ApplyReferralResponse)
async def apply_referral(
    body: ApplyReferralRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply a referral code."""
    result = await apply_referral_code(user.id, body.code, db)
    await db.commit()
    return ApplyReferralResponse(**result)


@router.post("/share", response_model=ShareResponse)
async def share(
    body: ShareRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Track a social share action and return share content."""
    result = await track_share(user.id, body.channel, body.content_type, body.content_id, db)
    await db.commit()
    return ShareResponse(**result)
