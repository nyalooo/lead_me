"""Rewards request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BalanceResponse(BaseModel):
    route_coins: int
    xrp_equivalent: float
    tier: str
    xrp_conversion_rate: float
    tier_bonus_rate: float


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    multiplier: float
    next_milestone: dict | None = None  # {"days": int, "multiplier": float}
    streak_freezes_remaining: int
    last_completed_date: str | None = None


class BadgeInfo(BaseModel):
    id: str
    name: str
    description: str
    earned_at: datetime | None = None
    pinned: bool = False


class BadgeProgress(BaseModel):
    id: str
    name: str
    description: str
    progress: dict  # {"current": int, "target": int}


class BadgesResponse(BaseModel):
    earned: list[BadgeInfo]
    available: list[BadgeProgress]


class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    coins_earned: int
    tier: str
    pinned_badges: list[str]


class LeaderboardResponse(BaseModel):
    area: str
    period: str
    rankings: list[LeaderboardEntry]
    user_rank: int | None = None
    total_participants: int


class TransactionEntry(BaseModel):
    id: UUID
    type: str
    coins: int
    description: str
    timestamp: datetime


class HistoryResponse(BaseModel):
    transactions: list[TransactionEntry]
    total: int
