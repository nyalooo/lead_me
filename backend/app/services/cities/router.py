"""Cities configuration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.cities.schemas import (
    CityListResponse,
    CityResponse,
    CreateCityRequest,
)
from app.services.cities.service import create_city, get_city, list_cities
from app.services.users.models import User

router = APIRouter()


@router.get("", response_model=CityListResponse)
async def get_cities(db: AsyncSession = Depends(get_db)):
    """List all available cities."""
    result = await list_cities(db)
    return CityListResponse(**result)


@router.get("/{slug}", response_model=CityResponse)
async def get_city_detail(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single city by slug."""
    result = await get_city(slug, db)
    if not result:
        raise HTTPException(status_code=404, detail="City not found")
    return CityResponse(**result)


@router.post("", response_model=CityResponse, status_code=201)
async def create(
    body: CreateCityRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new city configuration (admin)."""
    city = await create_city(body.model_dump(), db)
    await db.commit()
    return CityResponse.model_validate(city)
