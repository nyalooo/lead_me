"""Tests for multi-city configuration service and schemas."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.services.cities.service import SEED_CITIES, _city_to_dict


# --- Seed data ---

def test_seed_cities_has_mumbai():
    slugs = [c["slug"] for c in SEED_CITIES]
    assert "mumbai" in slugs


def test_seed_cities_has_delhi():
    slugs = [c["slug"] for c in SEED_CITIES]
    assert "delhi" in slugs


def test_seed_cities_has_bangalore():
    slugs = [c["slug"] for c in SEED_CITIES]
    assert "bangalore" in slugs


def test_seed_mumbai_is_active():
    mumbai = next(c for c in SEED_CITIES if c["slug"] == "mumbai")
    assert mumbai["active"] is True


def test_seed_delhi_is_inactive():
    delhi = next(c for c in SEED_CITIES if c["slug"] == "delhi")
    assert delhi["active"] is False


def test_seed_mumbai_has_areas():
    mumbai = next(c for c in SEED_CITIES if c["slug"] == "mumbai")
    assert len(mumbai["areas"]) >= 10
    assert "Andheri" in mumbai["areas"]
    assert "Bandra" in mumbai["areas"]


def test_seed_mumbai_has_peak_hours():
    mumbai = next(c for c in SEED_CITIES if c["slug"] == "mumbai")
    assert "morning" in mumbai["peak_hours"]
    assert "evening" in mumbai["peak_hours"]


def test_seed_mumbai_bounding_box():
    mumbai = next(c for c in SEED_CITIES if c["slug"] == "mumbai")
    assert mumbai["lat_min"] < mumbai["lat_max"]
    assert mumbai["lng_min"] < mumbai["lng_max"]
    # CST should be inside the box
    assert mumbai["lat_min"] < 18.94 < mumbai["lat_max"]
    assert mumbai["lng_min"] < 72.84 < mumbai["lng_max"]


# --- _city_to_dict ---

def _make_city(**overrides):
    defaults = {
        "id": uuid.uuid4(),
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
        "areas": ["Andheri", "Bandra"],
        "peak_hours": {"morning": {"start": "08:00", "end": "10:30"}},
        "active": True,
    }
    defaults.update(overrides)
    return type("City", (), defaults)()


def test_city_to_dict():
    city = _make_city()
    result = _city_to_dict(city)
    assert result["slug"] == "mumbai"
    assert result["name"] == "Mumbai"
    assert result["active"] is True
    assert len(result["areas"]) == 2


def test_city_to_dict_inactive():
    city = _make_city(slug="delhi", name="Delhi NCR", active=False)
    result = _city_to_dict(city)
    assert result["active"] is False


# --- Schema validation ---

def test_create_city_request_valid():
    from app.services.cities.schemas import CreateCityRequest
    req = CreateCityRequest(
        slug="pune",
        name="Pune",
        lat_min=18.40,
        lat_max=18.65,
        lng_min=73.72,
        lng_max=74.00,
        center_lat=18.5204,
        center_lng=73.8567,
    )
    assert req.slug == "pune"
    assert req.default_zoom == 12


def test_create_city_request_invalid_slug():
    from app.services.cities.schemas import CreateCityRequest
    with pytest.raises(ValidationError):
        CreateCityRequest(
            slug="Mumbai City!",
            name="Mumbai",
            lat_min=18.89,
            lat_max=19.27,
            lng_min=72.77,
            lng_max=72.98,
            center_lat=19.076,
            center_lng=72.8777,
        )


def test_create_city_request_slug_too_short():
    from app.services.cities.schemas import CreateCityRequest
    with pytest.raises(ValidationError):
        CreateCityRequest(
            slug="m",
            name="Mumbai",
            lat_min=18.89,
            lat_max=19.27,
            lng_min=72.77,
            lng_max=72.98,
            center_lat=19.076,
            center_lng=72.8777,
        )


def test_city_response():
    from app.services.cities.schemas import CityResponse
    resp = CityResponse(
        id=uuid.uuid4(),
        slug="mumbai",
        name="Mumbai",
        country="India",
        timezone="Asia/Kolkata",
        lat_min=18.89,
        lat_max=19.27,
        lng_min=72.77,
        lng_max=72.98,
        center_lat=19.076,
        center_lng=72.8777,
        default_zoom=12,
        areas=["Andheri", "Bandra"],
        active=True,
    )
    assert resp.slug == "mumbai"


def test_city_list_response():
    from app.services.cities.schemas import CityListResponse
    resp = CityListResponse(cities=[], active_count=0)
    assert resp.active_count == 0
