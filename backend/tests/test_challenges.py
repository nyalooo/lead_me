"""Tests for challenges service logic."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest

from app.services.challenges.service import _challenge_to_dict


# --- Helper factories ---

def _make_challenge(**overrides):
    """Create a mock Challenge-like object."""
    defaults = {
        "id": uuid.uuid4(),
        "title": "Walk 10 Routes",
        "description": "Complete 10 routes this week",
        "type": "weekly",
        "category": "general",
        "goal_type": "routes_count",
        "goal_value": 10,
        "goal_area": None,
        "reward_coins": 500,
        "reward_xrp": 0.5,
        "reward_badge_id": None,
        "starts_at": datetime.now(timezone.utc) - timedelta(days=1),
        "ends_at": datetime.now(timezone.utc) + timedelta(days=6),
        "max_participants": None,
        "active": True,
    }
    defaults.update(overrides)
    return type("Challenge", (), defaults)()


def _make_participant(**overrides):
    """Create a mock ChallengeParticipant-like object."""
    defaults = {
        "id": uuid.uuid4(),
        "challenge_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "progress": 0,
        "completed": False,
        "reward_claimed": False,
        "joined_at": datetime.now(timezone.utc),
        "completed_at": None,
    }
    defaults.update(overrides)
    return type("ChallengeParticipant", (), defaults)()


# --- _challenge_to_dict ---

def test_challenge_to_dict_basic():
    c = _make_challenge()
    result = _challenge_to_dict(c, None, 5)

    assert result["title"] == "Walk 10 Routes"
    assert result["goal_type"] == "routes_count"
    assert result["goal_value"] == 10
    assert result["reward_coins"] == 500
    assert result["reward_xrp"] == 0.5
    assert result["participant_count"] == 5
    assert result["user_joined"] is False
    assert result["user_progress"] == 0
    assert result["user_completed"] is False


def test_challenge_to_dict_with_participation():
    cid = uuid.uuid4()
    c = _make_challenge(id=cid)
    p = _make_participant(challenge_id=cid, progress=7, completed=False)
    result = _challenge_to_dict(c, p, 12)

    assert result["user_joined"] is True
    assert result["user_progress"] == 7
    assert result["user_completed"] is False
    assert result["participant_count"] == 12


def test_challenge_to_dict_completed():
    cid = uuid.uuid4()
    c = _make_challenge(id=cid)
    p = _make_participant(challenge_id=cid, progress=10, completed=True)
    result = _challenge_to_dict(c, p, 20)

    assert result["user_joined"] is True
    assert result["user_progress"] == 10
    assert result["user_completed"] is True


def test_challenge_to_dict_area_challenge():
    c = _make_challenge(goal_area="Andheri", category="area", goal_type="area_routes")
    result = _challenge_to_dict(c, None, 0)

    assert result["goal_area"] == "Andheri"
    assert result["category"] == "area"


def test_challenge_to_dict_flash_type():
    c = _make_challenge(type="flash", reward_coins=1000, reward_xrp=1.0)
    result = _challenge_to_dict(c, None, 0)

    assert result["type"] == "flash"
    assert result["reward_coins"] == 1000
    assert result["reward_xrp"] == 1.0


def test_challenge_to_dict_max_participants():
    c = _make_challenge(max_participants=50)
    result = _challenge_to_dict(c, None, 45)

    assert result["max_participants"] == 50
    assert result["participant_count"] == 45


def test_challenge_to_dict_with_badge():
    c = _make_challenge(reward_badge_id="monsoon_warrior")
    result = _challenge_to_dict(c, None, 0)

    assert result["reward_badge_id"] == "monsoon_warrior"


# --- Schema validation ---

def test_challenge_response_schema():
    from app.services.challenges.schemas import ChallengeResponse

    c = _make_challenge()
    data = _challenge_to_dict(c, None, 3)
    resp = ChallengeResponse(**data)

    assert resp.title == "Walk 10 Routes"
    assert resp.participant_count == 3
    assert resp.user_joined is False


def test_challenge_response_with_participant():
    from app.services.challenges.schemas import ChallengeResponse

    cid = uuid.uuid4()
    c = _make_challenge(id=cid)
    p = _make_participant(challenge_id=cid, progress=5, completed=False)
    data = _challenge_to_dict(c, p, 10)
    resp = ChallengeResponse(**data)

    assert resp.user_joined is True
    assert resp.user_progress == 5
    assert resp.user_completed is False


def test_challenges_list_response_schema():
    from app.services.challenges.schemas import ChallengesListResponse

    c1 = _make_challenge()
    c2 = _make_challenge(
        title="Monthly Peak Challenge",
        starts_at=datetime.now(timezone.utc) + timedelta(days=7),
        ends_at=datetime.now(timezone.utc) + timedelta(days=37),
    )

    resp = ChallengesListResponse(
        active=[_challenge_to_dict(c1, None, 5)],
        upcoming=[_challenge_to_dict(c2, None, 0)],
        completed=[],
    )

    assert len(resp.active) == 1
    assert len(resp.upcoming) == 1
    assert len(resp.completed) == 0


def test_join_challenge_response_schema():
    from app.services.challenges.schemas import JoinChallengeResponse

    cid = uuid.uuid4()
    resp = JoinChallengeResponse(challenge_id=cid, joined=True, message="Joined successfully")
    assert resp.joined is True
    assert resp.message == "Joined successfully"


def test_create_challenge_request_validation():
    from app.services.challenges.schemas import CreateChallengeRequest

    now = datetime.now(timezone.utc)
    req = CreateChallengeRequest(
        title="Test Challenge",
        description="Complete routes to earn bonus",
        type="weekly",
        category="general",
        goal_type="routes_count",
        goal_value=5,
        reward_coins=200,
        reward_xrp=0.2,
        starts_at=now,
        ends_at=now + timedelta(days=7),
    )
    assert req.title == "Test Challenge"
    assert req.goal_value == 5


def test_create_challenge_request_invalid_type():
    from app.services.challenges.schemas import CreateChallengeRequest
    from pydantic import ValidationError

    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        CreateChallengeRequest(
            title="Bad",
            description="This should fail validation",
            type="invalid_type",
            goal_type="routes_count",
            goal_value=5,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        )


def test_create_challenge_request_invalid_goal_type():
    from app.services.challenges.schemas import CreateChallengeRequest
    from pydantic import ValidationError

    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        CreateChallengeRequest(
            title="Bad Goal",
            description="This should fail validation too",
            type="weekly",
            goal_type="invalid_goal",
            goal_value=5,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        )


def test_create_challenge_request_title_too_short():
    from app.services.challenges.schemas import CreateChallengeRequest
    from pydantic import ValidationError

    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        CreateChallengeRequest(
            title="AB",
            description="Description is fine",
            type="weekly",
            goal_type="routes_count",
            goal_value=5,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        )


def test_create_challenge_request_goal_value_zero():
    from app.services.challenges.schemas import CreateChallengeRequest
    from pydantic import ValidationError

    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        CreateChallengeRequest(
            title="Zero Goal",
            description="Goal value must be positive",
            type="weekly",
            goal_type="routes_count",
            goal_value=0,
            starts_at=now,
            ends_at=now + timedelta(days=7),
        )


# --- Challenge progress response ---

def test_challenge_progress_response():
    from app.services.challenges.schemas import ChallengeProgressResponse

    cid = uuid.uuid4()
    resp = ChallengeProgressResponse(
        challenge_id=cid,
        progress=7,
        goal_value=10,
        percent=70.0,
        completed=False,
        reward_claimed=False,
    )
    assert resp.percent == 70.0
    assert resp.completed is False
