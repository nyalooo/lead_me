"""Rewards business logic — coins, streaks, badges, tier management."""

from datetime import date, datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.rewards.models import Badge, CoinTransaction, Streak, UserBadge
from app.services.route_engine.models import RouteAssignment
from app.services.route_engine.schemas import EstimatedReward
from app.services.users.models import User


# Streak multiplier thresholds
STREAK_MILESTONES = [
    (30, 3.0),
    (14, 2.5),
    (7, 2.0),
    (3, 1.5),
]

# Tier definitions
TIERS = {
    "rookie": {"min_routes": 0, "min_compliance": 0.0, "xrp_bonus": 1.0},
    "regular": {"min_routes": 25, "min_compliance": 0.7, "xrp_bonus": 1.1},
    "pro": {"min_routes": 100, "min_compliance": 0.8, "xrp_bonus": 1.25},
    "legend": {"min_routes": 500, "min_compliance": 0.9, "xrp_bonus": 1.5},
}


def get_streak_multiplier(streak_days: int) -> float:
    """Get the coin multiplier for the current streak length."""
    for threshold, multiplier in STREAK_MILESTONES:
        if streak_days >= threshold:
            return multiplier
    return 1.0


def get_next_milestone(current_streak: int) -> dict | None:
    """Get the next streak milestone the user is approaching."""
    for threshold, multiplier in reversed(STREAK_MILESTONES):
        if current_streak < threshold:
            return {"days": threshold, "multiplier": multiplier}
    return None


def calculate_reward(
    detour_percent: float,
    current_streak: int,
    departure_time: datetime | None = None,
) -> EstimatedReward:
    """Calculate estimated reward for a route assignment."""
    base_coins = 10

    # Detour multiplier: 1.0 (no detour) to 2.0 (max 15% detour)
    detour_multiplier = 1.0 + (detour_percent / settings.max_detour_percent)
    detour_multiplier = min(detour_multiplier, 2.0)

    streak_multiplier = get_streak_multiplier(current_streak)

    # Peak hour multiplier
    peak_multiplier = 1.0
    if departure_time:
        from app.services.route_engine.service import is_peak_hour
        if is_peak_hour(departure_time):
            peak_multiplier = 2.0

    total = int(base_coins * detour_multiplier * streak_multiplier * peak_multiplier)

    return EstimatedReward(
        base_coins=base_coins,
        detour_multiplier=round(detour_multiplier, 1),
        streak_multiplier=streak_multiplier,
        peak_multiplier=peak_multiplier,
        total_coins=total,
    )


async def get_or_create_streak(user_id, db: AsyncSession) -> Streak:
    """Get or create a streak record for a user."""
    result = await db.execute(select(Streak).where(Streak.user_id == user_id))
    streak = result.scalar_one_or_none()
    if streak is None:
        streak = Streak(user_id=user_id)
        db.add(streak)
        await db.flush()
    return streak


async def update_streak(streak: Streak, completed_date: date, db: AsyncSession) -> Streak:
    """Update streak based on route completion date."""
    if streak.last_completed_date is None:
        streak.current_streak = 1
    elif completed_date == streak.last_completed_date:
        # Already completed a route today, no streak change
        pass
    elif (completed_date - streak.last_completed_date).days == 1:
        # Consecutive day
        streak.current_streak += 1
    elif (completed_date - streak.last_completed_date).days == 2 and streak.streak_freezes_remaining > 0:
        # Missed one day but have a freeze
        streak.streak_freezes_remaining -= 1
        streak.current_streak += 1
    else:
        # Streak broken
        streak.current_streak = 1

    streak.last_completed_date = completed_date
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    db.add(streak)
    await db.flush()
    return streak


async def process_completion(
    user: User,
    assignment: RouteAssignment,
    db: AsyncSession,
) -> dict:
    """Process rewards after route completion.

    Returns dict with coins_earned, streak_day, badges_earned.
    """
    coins_earned = 0
    badges_earned = []

    if assignment.compliant:
        # Update streak
        streak = await get_or_create_streak(user.id, db)
        today = date.today()
        streak = await update_streak(streak, today, db)

        # Calculate coins
        reward = calculate_reward(
            detour_percent=assignment.detour_percent,
            current_streak=streak.current_streak,
            departure_time=assignment.assigned_at,
        )
        coins_earned = reward.total_coins

        # Record transaction
        transaction = CoinTransaction(
            user_id=user.id,
            type="route_completion",
            coins=coins_earned,
            description=f"Route completed",
            assignment_id=assignment.id,
        )
        db.add(transaction)

        # Update user totals
        user.total_coins += coins_earned
        user.total_routes += 1

        # Store coins on assignment
        assignment.coins_earned = coins_earned
        db.add(assignment)

        # Check for badges
        badges_earned = await check_badges(user, streak, db)

        # Update tier
        await update_tier(user, db)

        db.add(user)
        await db.flush()

        streak_day = streak.current_streak
    else:
        # Non-compliant: reset streak, no coins
        streak = await get_or_create_streak(user.id, db)
        streak.current_streak = 0
        db.add(streak)

        user.total_routes += 1
        db.add(user)
        await db.flush()

        streak_day = 0

    return {
        "coins_earned": coins_earned,
        "streak_day": streak_day,
        "badges_earned": badges_earned,
    }


async def check_badges(user: User, streak: Streak, db: AsyncSession) -> list[str]:
    """Check and award any newly earned badges."""
    newly_earned = []

    # Get all badges and user's earned badges
    all_badges_result = await db.execute(select(Badge))
    all_badges = list(all_badges_result.scalars().all())

    earned_result = await db.execute(select(UserBadge.badge_id).where(UserBadge.user_id == user.id))
    earned_ids = set(earned_result.scalars().all())

    for badge in all_badges:
        if badge.id in earned_ids:
            continue

        earned = False
        if badge.criteria_type == "routes_count" and user.total_routes >= badge.criteria_value:
            earned = True
        elif badge.criteria_type == "streak_days" and streak.current_streak >= badge.criteria_value:
            earned = True

        if earned:
            user_badge = UserBadge(user_id=user.id, badge_id=badge.id)
            db.add(user_badge)

            # Award bonus coins
            if badge.coins_bonus > 0:
                bonus = CoinTransaction(
                    user_id=user.id,
                    type="badge_bonus",
                    coins=badge.coins_bonus,
                    description=f"Badge earned: {badge.name}",
                )
                db.add(bonus)
                user.total_coins += badge.coins_bonus

            newly_earned.append(badge.id)

    if newly_earned:
        await db.flush()
    return newly_earned


async def update_tier(user: User, db: AsyncSession) -> None:
    """Update user tier based on total routes and compliance rate."""
    # Calculate compliance rate from recent assignments
    result = await db.execute(
        select(func.count(RouteAssignment.id)).where(
            RouteAssignment.user_id == user.id,
            RouteAssignment.status == "completed",
        )
    )
    total = result.scalar() or 0

    compliant_result = await db.execute(
        select(func.count(RouteAssignment.id)).where(
            RouteAssignment.user_id == user.id,
            RouteAssignment.status == "completed",
            RouteAssignment.compliant.is_(True),
        )
    )
    compliant = compliant_result.scalar() or 0

    compliance_rate = compliant / total if total > 0 else 0.0
    user.compliance_rate = round(compliance_rate, 2)

    # Determine tier (check from highest to lowest)
    for tier_name in ["legend", "pro", "regular", "rookie"]:
        tier = TIERS[tier_name]
        if user.total_routes >= tier["min_routes"] and compliance_rate >= tier["min_compliance"]:
            user.tier = tier_name
            break
