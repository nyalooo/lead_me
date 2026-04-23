"""Challenges API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.challenges.schemas import (
    ChallengeResponse,
    ChallengesListResponse,
    CreateChallengeRequest,
    JoinChallengeResponse,
)
from app.services.challenges.service import (
    claim_reward,
    create_challenge,
    get_challenge,
    join_challenge,
    list_challenges,
)
from app.services.users.models import User

router = APIRouter()


@router.get("", response_model=ChallengesListResponse)
async def get_challenges(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all challenges grouped by active/upcoming/completed."""
    result = await list_challenges(user.id, db)
    return ChallengesListResponse(**result)


@router.get("/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge_detail(
    challenge_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single challenge with user progress."""
    result = await get_challenge(challenge_id, user.id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return ChallengeResponse(**result)


@router.post("/{challenge_id}/join", response_model=JoinChallengeResponse)
async def join(
    challenge_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a challenge."""
    result = await join_challenge(challenge_id, user.id, db)
    await db.commit()
    return JoinChallengeResponse(**result)


@router.post("/{challenge_id}/claim")
async def claim(
    challenge_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Claim reward for a completed challenge."""
    result = await claim_reward(challenge_id, user.id, db)
    await db.commit()
    return result


@router.post("", response_model=ChallengeResponse, status_code=201)
async def create(
    body: CreateChallengeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new challenge (admin)."""
    challenge = await create_challenge(body.model_dump(), db)
    await db.commit()
    return ChallengeResponse(
        **{k: getattr(challenge, k) for k in ChallengeResponse.model_fields if hasattr(challenge, k)},
        participant_count=0,
    )
