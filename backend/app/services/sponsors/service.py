"""Sponsor reward pool business logic."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sponsors.models import Sponsor, RewardPool, PoolPayout

logger = logging.getLogger(__name__)


async def list_pools(db: AsyncSession) -> dict:
    """List all reward pools grouped by status."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(RewardPool, Sponsor)
        .join(Sponsor, RewardPool.sponsor_id == Sponsor.id)
        .where(RewardPool.active.is_(True))
        .order_by(RewardPool.starts_at)
    )
    rows = result.all()

    active, upcoming, depleted = [], [], []
    for pool, sponsor in rows:
        data = _pool_to_dict(pool, sponsor)
        if pool.remaining_amount <= 0:
            depleted.append(data)
        elif now < pool.starts_at:
            upcoming.append(data)
        elif now > pool.ends_at:
            depleted.append(data)
        else:
            active.append(data)

    return {"active": active, "upcoming": upcoming, "depleted": depleted}


async def get_pool(pool_id: UUID, db: AsyncSession) -> dict | None:
    """Get a single reward pool."""
    result = await db.execute(
        select(RewardPool, Sponsor)
        .join(Sponsor, RewardPool.sponsor_id == Sponsor.id)
        .where(RewardPool.id == pool_id)
    )
    row = result.one_or_none()
    if not row:
        return None
    pool, sponsor = row
    return _pool_to_dict(pool, sponsor)


async def check_and_payout(
    user_id: UUID,
    assignment_id: UUID,
    area: str | None,
    compliance_score: float,
    db: AsyncSession,
) -> list[dict]:
    """Check if any active pools match this completed route and pay out.
    Called after route completion. Returns list of payouts made.
    """
    now = datetime.now(timezone.utc)
    payouts = []

    result = await db.execute(
        select(RewardPool, Sponsor)
        .join(Sponsor, RewardPool.sponsor_id == Sponsor.id)
        .where(
            RewardPool.active.is_(True),
            RewardPool.starts_at <= now,
            RewardPool.ends_at >= now,
            RewardPool.remaining_amount > 0,
        )
    )

    for pool, sponsor in result.all():
        # Check area targeting
        if pool.target_area and area and pool.target_area.lower() != area.lower():
            continue

        # Check compliance threshold
        if compliance_score < pool.min_compliance:
            continue

        # Check remaining funds
        if pool.remaining_amount < pool.reward_per_route:
            continue

        # Pay out
        payout = PoolPayout(
            pool_id=pool.id,
            user_id=user_id,
            assignment_id=assignment_id,
            amount=pool.reward_per_route,
            currency=pool.currency,
        )
        db.add(payout)

        pool.remaining_amount -= pool.reward_per_route
        pool.total_payouts += 1
        db.add(pool)

        payouts.append({
            "pool_title": pool.title,
            "sponsor_name": sponsor.name,
            "amount": pool.reward_per_route,
            "currency": pool.currency,
        })

    if payouts:
        await db.flush()

    return payouts


async def get_user_payouts(user_id: UUID, db: AsyncSession, limit: int = 20) -> list[dict]:
    """Get payout history for a user."""
    result = await db.execute(
        select(PoolPayout, RewardPool, Sponsor)
        .join(RewardPool, PoolPayout.pool_id == RewardPool.id)
        .join(Sponsor, RewardPool.sponsor_id == Sponsor.id)
        .where(PoolPayout.user_id == user_id)
        .order_by(PoolPayout.created_at.desc())
        .limit(limit)
    )

    return [
        {
            "pool_title": pool.title,
            "sponsor_name": sponsor.name,
            "amount": payout.amount,
            "currency": payout.currency,
            "created_at": payout.created_at,
        }
        for payout, pool, sponsor in result.all()
    ]


async def create_sponsor(data: dict, db: AsyncSession) -> Sponsor:
    """Create a new sponsor (admin)."""
    sponsor = Sponsor(**data)
    db.add(sponsor)
    await db.flush()
    return sponsor


async def create_pool(data: dict, db: AsyncSession) -> dict:
    """Create a new reward pool (admin)."""
    pool_data = {**data, "remaining_amount": data["total_amount"]}
    pool = RewardPool(**pool_data)
    db.add(pool)
    await db.flush()

    sponsor_result = await db.execute(
        select(Sponsor).where(Sponsor.id == pool.sponsor_id)
    )
    sponsor = sponsor_result.scalar_one()
    return _pool_to_dict(pool, sponsor)


def _pool_to_dict(pool: RewardPool, sponsor: Sponsor) -> dict:
    return {
        "id": pool.id,
        "sponsor_id": pool.sponsor_id,
        "sponsor_name": sponsor.name,
        "title": pool.title,
        "description": pool.description,
        "currency": pool.currency,
        "total_amount": pool.total_amount,
        "remaining_amount": pool.remaining_amount,
        "reward_per_route": pool.reward_per_route,
        "target_area": pool.target_area,
        "min_compliance": pool.min_compliance,
        "starts_at": pool.starts_at,
        "ends_at": pool.ends_at,
        "active": pool.active,
        "total_payouts": pool.total_payouts,
    }
