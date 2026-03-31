"""Route engine request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LatLng(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class RouteAssignRequest(BaseModel):
    origin: LatLng
    destination: LatLng
    departure_time: datetime | None = None


class EstimatedReward(BaseModel):
    base_coins: int
    detour_multiplier: float
    streak_multiplier: float
    peak_multiplier: float
    total_coins: int


class RouteInfo(BaseModel):
    id: UUID
    polyline: str | None = None
    distance_km: float
    estimated_duration_min: float
    load_status: str  # clear, moderate, busy
    detour_percent: float = 0.0

    model_config = {"from_attributes": True}


class RouteAssignResponse(BaseModel):
    assignment_id: UUID
    assigned_route: RouteInfo
    alternative_routes: list[RouteInfo]
    estimated_reward: EstimatedReward


class RouteStatusResponse(BaseModel):
    route_id: UUID
    load_score: float
    load_status: str
    active_commuters: int
    scheduled_commuters: int
    capacity_estimate: int


class TrackRequest(BaseModel):
    lat: float
    lng: float
    timestamp: datetime
    accuracy_m: float = 0.0


class TrackResponse(BaseModel):
    on_route: bool
    progress_percent: float


class RouteCompleteResponse(BaseModel):
    assignment_id: UUID
    compliant: bool
    compliance_score: float
    coins_earned: int
    streak_day: int
    badges_earned: list[str]
