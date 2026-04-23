"""Sponsor reward pool API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.sponsors.schemas import (
    CreateRewardPoolRequest,
    CreateSponsorRequest,
    PoolPayoutResponse,
    RewardPoolListResponse,
    RewardPoolResponse,
    SponsorResponse,
)
from app.services.sponsors.service import (
    create_pool,
    create_sponsor,
    get_pool,
    get_user_payouts,
    list_pools,
)
from app.services.users.models import User

router = APIRouter()


@router.get("/pools", response_model=RewardPoolListResponse)
async def get_pools(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active/upcoming/depleted reward pools."""
    result = await list_pools(db)
    return RewardPoolListResponse(**result)


@router.get("/pools/{pool_id}", response_model=RewardPoolResponse)
async def get_pool_detail(
    pool_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single reward pool."""
    result = await get_pool(pool_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Pool not found")
    return RewardPoolResponse(**result)


@router.get("/my-payouts", response_model=list[PoolPayoutResponse])
async def my_payouts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's sponsor payout history."""
    results = await get_user_payouts(user.id, db)
    return [PoolPayoutResponse(**r) for r in results]


@router.post("/sponsors", response_model=SponsorResponse, status_code=201)
async def create_new_sponsor(
    body: CreateSponsorRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new sponsor (admin)."""
    sponsor = await create_sponsor(body.model_dump(), db)
    await db.commit()
    return SponsorResponse.model_validate(sponsor)


@router.post("/pools", response_model=RewardPoolResponse, status_code=201)
async def create_new_pool(
    body: CreateRewardPoolRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new reward pool (admin)."""
    result = await create_pool(body.model_dump(), db)
    await db.commit()
    return RewardPoolResponse(**result)
