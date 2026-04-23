"""Tests for sponsor reward pool schemas and helpers."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from pydantic import ValidationError


# --- Schema validation ---

def test_create_sponsor_request_valid():
    from app.services.sponsors.schemas import CreateSponsorRequest
    req = CreateSponsorRequest(
        name="Mumbai Traffic Corp",
        description="Government initiative for traffic reduction",
        contact_email="info@mtc.gov.in",
    )
    assert req.name == "Mumbai Traffic Corp"


def test_create_sponsor_request_name_too_short():
    from app.services.sponsors.schemas import CreateSponsorRequest
    with pytest.raises(ValidationError):
        CreateSponsorRequest(name="A")


def test_create_reward_pool_valid():
    from app.services.sponsors.schemas import CreateRewardPoolRequest
    now = datetime.now(timezone.utc)
    req = CreateRewardPoolRequest(
        sponsor_id=uuid.uuid4(),
        title="Andheri Green Route Fund",
        currency="XRP",
        total_amount=100.0,
        reward_per_route=0.05,
        target_area="Andheri",
        min_compliance=0.85,
        starts_at=now,
        ends_at=now + timedelta(days=30),
    )
    assert req.total_amount == 100.0
    assert req.reward_per_route == 0.05
    assert req.target_area == "Andheri"


def test_create_reward_pool_zero_amount():
    from app.services.sponsors.schemas import CreateRewardPoolRequest
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        CreateRewardPoolRequest(
            sponsor_id=uuid.uuid4(),
            title="Empty Pool",
            total_amount=0,
            reward_per_route=0.1,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        )


def test_create_reward_pool_invalid_currency():
    from app.services.sponsors.schemas import CreateRewardPoolRequest
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        CreateRewardPoolRequest(
            sponsor_id=uuid.uuid4(),
            title="Bad Currency Pool",
            currency="BTC",
            total_amount=10.0,
            reward_per_route=0.1,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        )


def test_reward_pool_response():
    from app.services.sponsors.schemas import RewardPoolResponse
    now = datetime.now(timezone.utc)
    resp = RewardPoolResponse(
        id=uuid.uuid4(),
        sponsor_id=uuid.uuid4(),
        sponsor_name="Test Corp",
        title="Green Fund",
        description="Rewards for eco-routes",
        currency="XRP",
        total_amount=50.0,
        remaining_amount=45.5,
        reward_per_route=0.05,
        target_area="Bandra",
        min_compliance=0.8,
        starts_at=now,
        ends_at=now + timedelta(days=30),
        active=True,
        total_payouts=90,
    )
    assert resp.remaining_amount == 45.5
    assert resp.total_payouts == 90


def test_reward_pool_list_response():
    from app.services.sponsors.schemas import RewardPoolListResponse
    resp = RewardPoolListResponse(active=[], upcoming=[], depleted=[])
    assert len(resp.active) == 0


def test_pool_payout_response():
    from app.services.sponsors.schemas import PoolPayoutResponse
    resp = PoolPayoutResponse(
        pool_title="Green Fund",
        sponsor_name="Test Corp",
        amount=0.05,
        currency="XRP",
        created_at=datetime.now(timezone.utc),
    )
    assert resp.amount == 0.05


def test_sponsor_response():
    from app.services.sponsors.schemas import SponsorResponse
    resp = SponsorResponse(
        id=uuid.uuid4(),
        name="City Transport",
        description="Municipal transport authority",
        logo_url="https://example.com/logo.png",
        active=True,
    )
    assert resp.name == "City Transport"


# --- Service helper ---

def test_pool_to_dict():
    from app.services.sponsors.service import _pool_to_dict

    now = datetime.now(timezone.utc)
    pool = type("RewardPool", (), {
        "id": uuid.uuid4(),
        "sponsor_id": uuid.uuid4(),
        "title": "Test Pool",
        "description": "desc",
        "currency": "XRP",
        "total_amount": 100.0,
        "remaining_amount": 75.0,
        "reward_per_route": 0.05,
        "target_area": "Powai",
        "min_compliance": 0.8,
        "starts_at": now,
        "ends_at": now + timedelta(days=30),
        "active": True,
        "total_payouts": 500,
    })()
    sponsor = type("Sponsor", (), {"name": "Sponsor Inc"})()

    result = _pool_to_dict(pool, sponsor)
    assert result["sponsor_name"] == "Sponsor Inc"
    assert result["remaining_amount"] == 75.0
    assert result["total_payouts"] == 500
    assert result["target_area"] == "Powai"
