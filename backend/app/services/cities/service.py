"""City configuration service.

Manages multi-city support with config-driven city definitions.
Each city has its own bounding box, areas, peak hours, and map defaults.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cities.models import City

logger = logging.getLogger(__name__)

# Default city configs for seeding
SEED_CITIES = [
    {
        "slug": "mumbai",
        "name": "Mumbai",
        "country": "India",
        "timezone": "Asia/Kolkata",
        "lat_min": 18.89,
        "lat_max": 19.27,
        "lng_min": 72.77,
        "lng_max": 72.98,
        "center_lat": 19.076,
        "center_lng": 72.8777,
        "default_zoom": 12,
        "areas": [
            "Andheri", "Bandra", "BKC", "Powai", "Dadar",
            "Churchgate", "CST", "Lower Parel", "Worli", "Juhu",
            "Goregaon", "Malad", "Borivali", "Thane", "Navi Mumbai",
        ],
        "peak_hours": {
            "morning": {"start": "08:00", "end": "10:30"},
            "evening": {"start": "17:30", "end": "20:00"},
        },
        "active": True,
    },
    {
        "slug": "delhi",
        "name": "Delhi NCR",
        "country": "India",
        "timezone": "Asia/Kolkata",
        "lat_min": 28.40,
        "lat_max": 28.88,
        "lng_min": 76.84,
        "lng_max": 77.35,
        "center_lat": 28.6139,
        "center_lng": 77.2090,
        "default_zoom": 11,
        "areas": [
            "Connaught Place", "Gurgaon", "Noida", "Dwarka",
            "Saket", "Nehru Place", "Karol Bagh", "Rajouri Garden",
        ],
        "peak_hours": {
            "morning": {"start": "08:30", "end": "10:30"},
            "evening": {"start": "17:00", "end": "20:00"},
        },
        "active": False,
    },
    {
        "slug": "bangalore",
        "name": "Bangalore",
        "country": "India",
        "timezone": "Asia/Kolkata",
        "lat_min": 12.83,
        "lat_max": 13.14,
        "lng_min": 77.46,
        "lng_max": 77.78,
        "center_lat": 12.9716,
        "center_lng": 77.5946,
        "default_zoom": 12,
        "areas": [
            "Koramangala", "Indiranagar", "Whitefield", "Electronic City",
            "HSR Layout", "Marathahalli", "MG Road", "Jayanagar",
        ],
        "peak_hours": {
            "morning": {"start": "09:00", "end": "11:00"},
            "evening": {"start": "18:00", "end": "20:30"},
        },
        "active": False,
    },
]


async def list_cities(db: AsyncSession) -> dict:
    """List all configured cities."""
    result = await db.execute(select(City).order_by(City.name))
    cities = [_city_to_dict(c) for c in result.scalars().all()]
    active_count = sum(1 for c in cities if c["active"])
    return {"cities": cities, "active_count": active_count}


async def get_city(slug: str, db: AsyncSession) -> dict | None:
    """Get a city by slug."""
    result = await db.execute(select(City).where(City.slug == slug))
    city = result.scalar_one_or_none()
    if not city:
        return None
    return _city_to_dict(city)


async def create_city(data: dict, db: AsyncSession) -> City:
    """Create a new city config (admin)."""
    city = City(**data)
    db.add(city)
    await db.flush()
    return city


async def validate_coordinates(lat: float, lng: float, db: AsyncSession) -> dict | None:
    """Find which active city a coordinate falls within."""
    result = await db.execute(
        select(City).where(City.active.is_(True))
    )
    for city in result.scalars().all():
        if (city.lat_min <= lat <= city.lat_max and
                city.lng_min <= lng <= city.lng_max):
            return _city_to_dict(city)
    return None


async def seed_cities(db: AsyncSession) -> int:
    """Seed default city configurations. Returns count of new cities added."""
    count = 0
    for city_data in SEED_CITIES:
        existing = await db.execute(
            select(City).where(City.slug == city_data["slug"])
        )
        if not existing.scalar_one_or_none():
            city = City(**city_data)
            db.add(city)
            count += 1

    if count:
        await db.flush()

    return count


def _city_to_dict(city: City) -> dict:
    return {
        "id": city.id,
        "slug": city.slug,
        "name": city.name,
        "country": city.country,
        "timezone": city.timezone,
        "lat_min": city.lat_min,
        "lat_max": city.lat_max,
        "lng_min": city.lng_min,
        "lng_max": city.lng_max,
        "center_lat": city.center_lat,
        "center_lng": city.center_lng,
        "default_zoom": city.default_zoom,
        "areas": city.areas,
        "peak_hours": city.peak_hours,
        "active": city.active,
    }
