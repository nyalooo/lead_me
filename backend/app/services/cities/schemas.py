"""City configuration request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CityResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    country: str
    timezone: str
    lat_min: float
    lat_max: float
    lng_min: float
    lng_max: float
    center_lat: float
    center_lng: float
    default_zoom: int
    areas: list[str] | None = None
    peak_hours: dict | None = None
    active: bool

    model_config = {"from_attributes": True}


class CityListResponse(BaseModel):
    cities: list[CityResponse]
    active_count: int


class CreateCityRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=50, pattern="^[a-z0-9-]+$")
    name: str = Field(..., min_length=2, max_length=100)
    country: str = Field("India", max_length=50)
    timezone: str = Field("Asia/Kolkata", max_length=50)
    lat_min: float
    lat_max: float
    lng_min: float
    lng_max: float
    center_lat: float
    center_lng: float
    default_zoom: int = Field(12, ge=5, le=18)
    areas: list[str] | None = None
    peak_hours: dict | None = None
