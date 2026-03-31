"""Tests for route engine service logic."""

from datetime import datetime, timezone

from app.services.route_engine.service import (
    calculate_load_score,
    get_load_status,
    is_peak_hour,
    validate_mumbai_coordinates,
)
from app.services.route_engine.schemas import LatLng


def test_validate_mumbai_coordinates_valid():
    """Andheri station should be within Mumbai."""
    point = LatLng(lat=19.1196, lng=72.8464)
    assert validate_mumbai_coordinates(point) is True


def test_validate_mumbai_coordinates_invalid():
    """Delhi should be outside Mumbai."""
    point = LatLng(lat=28.6139, lng=77.2090)
    assert validate_mumbai_coordinates(point) is False


def test_calculate_load_score_empty():
    score = calculate_load_score(
        active_commuters=0,
        scheduled_commuters=0,
        historical_avg=0,
        capacity=1000,
    )
    assert score == 0.0


def test_calculate_load_score_weighted():
    score = calculate_load_score(
        active_commuters=500,
        scheduled_commuters=200,
        historical_avg=100,
        capacity=1000,
    )
    # (500*1.0 + 200*0.7 + 100*0.3) / 1000 = (500 + 140 + 30) / 1000 = 0.67
    assert abs(score - 0.67) < 0.01


def test_calculate_load_score_zero_capacity():
    score = calculate_load_score(
        active_commuters=100,
        scheduled_commuters=0,
        historical_avg=0,
        capacity=0,
    )
    assert score == 1.0


def test_get_load_status():
    assert get_load_status(0.2) == "clear"
    assert get_load_status(0.5) == "moderate"
    assert get_load_status(0.8) == "busy"


def test_is_peak_hour_morning():
    dt = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    assert is_peak_hour(dt) is True


def test_is_peak_hour_evening():
    dt = datetime(2026, 4, 1, 19, 0, tzinfo=timezone.utc)
    assert is_peak_hour(dt) is True


def test_is_not_peak_hour():
    dt = datetime(2026, 4, 1, 14, 0, tzinfo=timezone.utc)
    assert is_peak_hour(dt) is False
