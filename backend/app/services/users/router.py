"""User profile endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.config import settings
from app.services.users.models import User
from app.services.users.schemas import UserResponse, UserStats, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if update.display_name is not None:
        user.display_name = update.display_name
    if update.area is not None:
        user.area = update.area
    if update.xrp_wallet_address is not None:
        user.xrp_wallet_address = update.xrp_wallet_address
    db.add(user)
    await db.flush()
    return user


@router.get("/me/stats", response_model=UserStats)
async def get_stats(user: User = Depends(get_current_user)):
    return UserStats(
        total_routes=user.total_routes,
        total_coins=user.total_coins,
        compliance_rate=user.compliance_rate,
        tier=user.tier,
        xrp_equivalent=user.total_coins / settings.xrp_coins_per_xrp,
        member_since=user.created_at,
    )
