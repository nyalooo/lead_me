"""Seed initial data — badges, default config, etc."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rewards.models import Badge

# Badge catalog matching docs/GAMIFICATION.md
BADGES = [
    {
        "id": "traffic_hero",
        "name": "Traffic Hero",
        "description": "Your detour reduced congestion for 50+ commuters",
        "coins_bonus": 100,
        "criteria_type": "impact_commuters",
        "criteria_value": 50,
    },
    {
        "id": "early_bird",
        "name": "Early Bird",
        "description": "Complete 10 routes before 7am",
        "coins_bonus": 50,
        "criteria_type": "early_routes",
        "criteria_value": 10,
    },
    {
        "id": "mumbai_local",
        "name": "Mumbai Local",
        "description": "Use LeadMe in 5+ different areas",
        "coins_bonus": 75,
        "criteria_type": "area_count",
        "criteria_value": 5,
    },
    {
        "id": "perfect_week",
        "name": "Perfect Week",
        "description": "Follow all assigned routes for 7 consecutive days",
        "coins_bonus": 100,
        "criteria_type": "streak_days",
        "criteria_value": 7,
    },
    {
        "id": "century_club",
        "name": "Century Club",
        "description": "Complete 100 total routes",
        "coins_bonus": 200,
        "criteria_type": "routes_count",
        "criteria_value": 100,
    },
    {
        "id": "monsoon_warrior",
        "name": "Monsoon Warrior",
        "description": "Complete 20 routes during monsoon season (Jun-Sep)",
        "coins_bonus": 150,
        "criteria_type": "monsoon_routes",
        "criteria_value": 20,
    },
    {
        "id": "night_owl",
        "name": "Night Owl",
        "description": "Complete 10 routes after 9pm",
        "coins_bonus": 50,
        "criteria_type": "night_routes",
        "criteria_value": 10,
    },
    {
        "id": "route_pioneer",
        "name": "Route Pioneer",
        "description": "Be among the first 10 users on a newly added route",
        "coins_bonus": 75,
        "criteria_type": "pioneer",
        "criteria_value": 1,
    },
    {
        "id": "week_warrior",
        "name": "Week Warrior",
        "description": "Maintain a 7-day streak",
        "coins_bonus": 50,
        "criteria_type": "streak_days",
        "criteria_value": 7,
    },
    {
        "id": "monthly_maven",
        "name": "Monthly Maven",
        "description": "Maintain a 30-day streak",
        "coins_bonus": 200,
        "criteria_type": "streak_days",
        "criteria_value": 30,
    },
    {
        "id": "first_ride",
        "name": "First Ride",
        "description": "Complete your first assigned route",
        "coins_bonus": 25,
        "criteria_type": "routes_count",
        "criteria_value": 1,
    },
    {
        "id": "half_century",
        "name": "Half Century",
        "description": "Complete 50 total routes",
        "coins_bonus": 100,
        "criteria_type": "routes_count",
        "criteria_value": 50,
    },
]


async def seed_badges(db: AsyncSession) -> int:
    """Insert badge definitions if they don't already exist.

    Returns the number of badges inserted.
    """
    existing = await db.execute(select(Badge.id))
    existing_ids = set(existing.scalars().all())

    inserted = 0
    for badge_data in BADGES:
        if badge_data["id"] not in existing_ids:
            db.add(Badge(**badge_data))
            inserted += 1

    if inserted:
        await db.flush()
    return inserted


async def seed_all(db: AsyncSession) -> dict:
    """Run all seed operations. Returns summary of what was seeded."""
    badges_inserted = await seed_badges(db)
    return {"badges_inserted": badges_inserted}
