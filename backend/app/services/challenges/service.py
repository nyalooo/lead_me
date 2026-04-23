"""Challenges business logic."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.challenges.models import Challenge, ChallengeParticipant
from app.services.rewards.models import CoinTransaction
from app.services.users.models import User

logger = logging.getLogger(__name__)


async def list_challenges(user_id: UUID, db: AsyncSession) -> dict:
    """List all challenges grouped by status, with user's progress."""
    now = datetime.now(timezone.utc)

    all_challenges = await db.execute(
        select(Challenge).where(Challenge.active.is_(True)).order_by(Challenge.starts_at)
    )
    challenges = list(all_challenges.scalars().all())

    # Get user's participations
    participations = await db.execute(
        select(ChallengeParticipant).where(ChallengeParticipant.user_id == user_id)
    )
    user_parts = {p.challenge_id: p for p in participations.scalars().all()}

    # Get participant counts
    counts_result = await db.execute(
        select(ChallengeParticipant.challenge_id, func.count(ChallengeParticipant.id))
        .group_by(ChallengeParticipant.challenge_id)
    )
    counts = dict(counts_result.all())

    active, upcoming, completed = [], [], []
    for c in challenges:
        data = _challenge_to_dict(c, user_parts.get(c.id), counts.get(c.id, 0))
        if now < c.starts_at:
            upcoming.append(data)
        elif now > c.ends_at:
            completed.append(data)
        else:
            active.append(data)

    return {"active": active, "upcoming": upcoming, "completed": completed}


async def get_challenge(challenge_id: UUID, user_id: UUID, db: AsyncSession) -> dict | None:
    """Get single challenge with user progress."""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        return None

    part_result = await db.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge_id,
            ChallengeParticipant.user_id == user_id,
        )
    )
    participation = part_result.scalar_one_or_none()

    count_result = await db.execute(
        select(func.count(ChallengeParticipant.id)).where(
            ChallengeParticipant.challenge_id == challenge_id
        )
    )
    count = count_result.scalar() or 0

    return _challenge_to_dict(challenge, participation, count)


async def join_challenge(challenge_id: UUID, user_id: UUID, db: AsyncSession) -> dict:
    """Join a challenge."""
    result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
    challenge = result.scalar_one_or_none()
    if not challenge:
        return {"challenge_id": challenge_id, "joined": False, "message": "Challenge not found"}

    now = datetime.now(timezone.utc)
    if now > challenge.ends_at:
        return {"challenge_id": challenge_id, "joined": False, "message": "Challenge has ended"}
    if now < challenge.starts_at:
        return {"challenge_id": challenge_id, "joined": False, "message": "Challenge hasn't started yet"}

    # Check if already joined
    existing = await db.execute(
        select(ChallengeParticipant).where(
            ChallengeParticipant.challenge_id == challenge_id,
            ChallengeParticipant.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"challenge_id": challenge_id, "joined": True, "message": "Already joined"}

    # Check max participants
    if challenge.max_participants:
        count_result = await db.execute(
            select(func.count(ChallengeParticipant.id)).where(
                ChallengeParticipant.challenge_id == challenge_id
            )
        )
        count = count_result.scalar() or 0
        if count >= challenge.max_participants:
            return {"challenge_id": challenge_id, "joined": False, "message": "Challenge is full"}

    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=user_id,
    )
    db.add(participant)
    await db.flush()

    return {"challenge_id": challenge_id, "joined": True, "message": "Joined successfully"}


async def update_progress(
    user_id: UUID,
    goal_type: str,
    increment: int,
    area: str | None,
    db: AsyncSession,
) -> list[UUID]:
    """Update progress for all active challenges matching the goal type.

    Called after route completion. Returns list of newly completed challenge IDs.
    """
    now = datetime.now(timezone.utc)
    newly_completed = []

    # Find active challenges the user has joined
    result = await db.execute(
        select(ChallengeParticipant, Challenge)
        .join(Challenge, ChallengeParticipant.challenge_id == Challenge.id)
        .where(
            ChallengeParticipant.user_id == user_id,
            ChallengeParticipant.completed.is_(False),
            Challenge.active.is_(True),
            Challenge.starts_at <= now,
            Challenge.ends_at >= now,
            Challenge.goal_type == goal_type,
        )
    )

    for participant, challenge in result.all():
        # For area challenges, check area match
        if challenge.goal_area and area and challenge.goal_area.lower() != area.lower():
            continue

        participant.progress += increment
        if participant.progress >= challenge.goal_value:
            participant.completed = True
            participant.completed_at = now
            newly_completed.append(challenge.id)

        db.add(participant)

    if newly_completed:
        await db.flush()

    return newly_completed


async def claim_reward(
    challenge_id: UUID, user_id: UUID, db: AsyncSession
) -> dict:
    """Claim reward for a completed challenge."""
    result = await db.execute(
        select(ChallengeParticipant, Challenge)
        .join(Challenge, ChallengeParticipant.challenge_id == Challenge.id)
        .where(
            ChallengeParticipant.challenge_id == challenge_id,
            ChallengeParticipant.user_id == user_id,
        )
    )
    row = result.one_or_none()
    if not row:
        return {"claimed": False, "message": "Not a participant"}

    participant, challenge = row
    if not participant.completed:
        return {"claimed": False, "message": "Challenge not completed yet"}
    if participant.reward_claimed:
        return {"claimed": False, "message": "Reward already claimed"}

    # Award coins
    coins = challenge.reward_coins
    if coins > 0:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        user.total_coins += coins
        db.add(user)

        tx = CoinTransaction(
            user_id=user_id,
            type="challenge_reward",
            coins=coins,
            description=f"Challenge completed: {challenge.title}",
        )
        db.add(tx)

    participant.reward_claimed = True
    db.add(participant)
    await db.flush()

    return {
        "claimed": True,
        "message": "Reward claimed!",
        "coins_earned": coins,
        "xrp_earned": challenge.reward_xrp,
    }


async def create_challenge(data: dict, db: AsyncSession) -> Challenge:
    """Create a new challenge (admin)."""
    challenge = Challenge(**data)
    db.add(challenge)
    await db.flush()
    return challenge


def _challenge_to_dict(challenge: Challenge, participation: ChallengeParticipant | None, count: int) -> dict:
    return {
        "id": challenge.id,
        "title": challenge.title,
        "description": challenge.description,
        "type": challenge.type,
        "category": challenge.category,
        "goal_type": challenge.goal_type,
        "goal_value": challenge.goal_value,
        "goal_area": challenge.goal_area,
        "reward_coins": challenge.reward_coins,
        "reward_xrp": challenge.reward_xrp,
        "reward_badge_id": challenge.reward_badge_id,
        "starts_at": challenge.starts_at,
        "ends_at": challenge.ends_at,
        "max_participants": challenge.max_participants,
        "active": challenge.active,
        "participant_count": count,
        "user_joined": participation is not None,
        "user_progress": participation.progress if participation else 0,
        "user_completed": participation.completed if participation else False,
    }
