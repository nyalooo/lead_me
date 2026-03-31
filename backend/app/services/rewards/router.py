"""Rewards API endpoints — balance, streaks, badges, leaderboard."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.rewards.models import Badge, CoinTransaction, Streak, UserBadge
from app.services.rewards.schemas import (
    BadgeInfo,
    BadgeProgress,
    BadgesResponse,
    BalanceResponse,
    HistoryResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    StreakResponse,
    TransactionEntry,
)
from app.services.rewards.service import TIERS, get_next_milestone, get_or_create_streak, get_streak_multiplier
from app.services.users.models import User

router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(user: User = Depends(get_current_user)):
    tier_bonus = TIERS.get(user.tier, TIERS["rookie"])["xrp_bonus"]
    return BalanceResponse(
        route_coins=user.total_coins,
        xrp_equivalent=user.total_coins / settings.xrp_coins_per_xrp,
        tier=user.tier,
        xrp_conversion_rate=1.0 / settings.xrp_coins_per_xrp,
        tier_bonus_rate=tier_bonus,
    )


@router.get("/streaks", response_model=StreakResponse)
async def get_streaks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    streak = await get_or_create_streak(user.id, db)
    return StreakResponse(
        current_streak=streak.current_streak,
        longest_streak=streak.longest_streak,
        multiplier=get_streak_multiplier(streak.current_streak),
        next_milestone=get_next_milestone(streak.current_streak),
        streak_freezes_remaining=streak.streak_freezes_remaining,
        last_completed_date=str(streak.last_completed_date) if streak.last_completed_date else None,
    )


@router.get("/badges", response_model=BadgesResponse)
async def get_badges(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Earned badges
    earned_result = await db.execute(
        select(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user.id)
    )
    earned = [
        BadgeInfo(
            id=badge.id,
            name=badge.name,
            description=badge.description,
            earned_at=ub.earned_at,
            pinned=ub.pinned,
        )
        for ub, badge in earned_result.all()
    ]

    earned_ids = {b.id for b in earned}

    # Available (not yet earned) badges with progress
    all_badges_result = await db.execute(select(Badge))
    available = []
    for badge in all_badges_result.scalars().all():
        if badge.id in earned_ids:
            continue
        # Calculate progress based on criteria type
        current = 0
        if badge.criteria_type == "routes_count":
            current = user.total_routes
        elif badge.criteria_type == "streak_days":
            streak = await get_or_create_streak(user.id, db)
            current = streak.current_streak

        available.append(
            BadgeProgress(
                id=badge.id,
                name=badge.name,
                description=badge.description,
                progress={"current": current, "target": badge.criteria_value},
            )
        )

    return BadgesResponse(earned=earned, available=available)


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    area: str = Query("mumbai", description="Area name for leaderboard"),
    period: str = Query("week", pattern="^(week|month)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # For MVP, return a simple leaderboard based on total coins
    # TODO: filter by area and time period
    result = await db.execute(
        select(User)
        .order_by(User.total_coins.desc())
        .limit(20)
    )
    users = list(result.scalars().all())

    rankings = []
    user_rank = None
    for i, u in enumerate(users, 1):
        rankings.append(
            LeaderboardEntry(
                rank=i,
                display_name=u.display_name,
                coins_earned=u.total_coins,
                tier=u.tier,
                pinned_badges=[],  # TODO: fetch pinned badges
            )
        )
        if u.id == user.id:
            user_rank = i

    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar() or 0

    return LeaderboardResponse(
        area=area,
        period=period,
        rankings=rankings,
        user_rank=user_rank,
        total_participants=total,
    )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get transactions
    result = await db.execute(
        select(CoinTransaction)
        .where(CoinTransaction.user_id == user.id)
        .order_by(CoinTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    transactions = [
        TransactionEntry(
            id=t.id,
            type=t.type,
            coins=t.coins,
            description=t.description,
            timestamp=t.created_at,
        )
        for t in result.scalars().all()
    ]

    # Total count
    count_result = await db.execute(
        select(func.count(CoinTransaction.id)).where(CoinTransaction.user_id == user.id)
    )
    total = count_result.scalar() or 0

    return HistoryResponse(transactions=transactions, total=total)
