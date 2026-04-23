"""Challenges request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChallengeResponse(BaseModel):
    id: UUID
    title: str
    description: str
    type: str
    category: str
    goal_type: str
    goal_value: int
    goal_area: str | None = None
    reward_coins: int
    reward_xrp: float
    reward_badge_id: str | None = None
    starts_at: datetime
    ends_at: datetime
    max_participants: int | None = None
    active: bool
    participant_count: int = 0
    user_joined: bool = False
    user_progress: int = 0
    user_completed: bool = False

    model_config = {"from_attributes": True}


class ChallengesListResponse(BaseModel):
    active: list[ChallengeResponse]
    upcoming: list[ChallengeResponse]
    completed: list[ChallengeResponse]


class JoinChallengeResponse(BaseModel):
    challenge_id: UUID
    joined: bool
    message: str


class ChallengeProgressResponse(BaseModel):
    challenge_id: UUID
    progress: int
    goal_value: int
    percent: float
    completed: bool
    reward_claimed: bool


class CreateChallengeRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    type: str = Field(..., pattern="^(weekly|monthly|event|flash)$")
    category: str = Field("general", pattern="^(general|area|peak|monsoon|festival)$")
    goal_type: str = Field(..., pattern="^(routes_count|distance_km|peak_routes|area_routes|streak_days)$")
    goal_value: int = Field(..., gt=0)
    goal_area: str | None = None
    reward_coins: int = Field(0, ge=0)
    reward_xrp: float = Field(0.0, ge=0)
    reward_badge_id: str | None = None
    starts_at: datetime
    ends_at: datetime
    max_participants: int | None = None
