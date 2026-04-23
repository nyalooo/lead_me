"""Tests for social/referral service logic and schemas."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.services.social.service import _generate_referral_code


# --- Referral code generation ---

def test_generate_referral_code_format():
    uid = uuid.uuid4()
    code = _generate_referral_code(uid)
    assert code.startswith("LM-")
    assert len(code) == 9  # "LM-" + 6 hex chars


def test_generate_referral_code_deterministic():
    uid = uuid.uuid4()
    c1 = _generate_referral_code(uid)
    c2 = _generate_referral_code(uid)
    assert c1 == c2


def test_generate_referral_code_unique():
    codes = {_generate_referral_code(uuid.uuid4()) for _ in range(100)}
    assert len(codes) == 100


def test_generate_referral_code_uppercase():
    uid = uuid.uuid4()
    code = _generate_referral_code(uid)
    suffix = code[3:]
    assert suffix == suffix.upper()


# --- Schema validation ---

def test_apply_referral_request_valid():
    from app.services.social.schemas import ApplyReferralRequest
    req = ApplyReferralRequest(code="LM-ABC123")
    assert req.code == "LM-ABC123"


def test_apply_referral_request_too_short():
    from app.services.social.schemas import ApplyReferralRequest
    with pytest.raises(ValidationError):
        ApplyReferralRequest(code="AB")


def test_apply_referral_request_too_long():
    from app.services.social.schemas import ApplyReferralRequest
    with pytest.raises(ValidationError):
        ApplyReferralRequest(code="A" * 21)


def test_share_request_valid():
    from app.services.social.schemas import ShareRequest
    req = ShareRequest(channel="whatsapp", content_type="referral")
    assert req.channel == "whatsapp"
    assert req.content_type == "referral"
    assert req.content_id is None


def test_share_request_with_content_id():
    from app.services.social.schemas import ShareRequest
    req = ShareRequest(channel="copy_link", content_type="challenge", content_id="uuid-here")
    assert req.content_id == "uuid-here"


def test_share_request_invalid_channel():
    from app.services.social.schemas import ShareRequest
    with pytest.raises(ValidationError):
        ShareRequest(channel="instagram", content_type="referral")


def test_share_request_invalid_content_type():
    from app.services.social.schemas import ShareRequest
    with pytest.raises(ValidationError):
        ShareRequest(channel="whatsapp", content_type="photo")


def test_referral_code_response():
    from app.services.social.schemas import ReferralCodeResponse
    resp = ReferralCodeResponse(
        code="LM-ABC123",
        uses=5,
        max_uses=None,
        active=True,
        share_url="https://leadme.app/join?ref=LM-ABC123",
    )
    assert resp.code == "LM-ABC123"
    assert resp.uses == 5
    assert resp.share_url.endswith("LM-ABC123")


def test_apply_referral_response():
    from app.services.social.schemas import ApplyReferralResponse
    resp = ApplyReferralResponse(applied=True, message="Referral code applied!", bonus_coins=100)
    assert resp.applied is True
    assert resp.bonus_coins == 100


def test_share_response():
    from app.services.social.schemas import ShareResponse
    resp = ShareResponse(
        shared=True,
        share_url="https://leadme.app/join?ref=LM-ABC123",
        message="Join LeadMe!",
    )
    assert resp.shared is True


def test_referral_stats_response():
    from app.services.social.schemas import ReferralStatsResponse
    resp = ReferralStatsResponse(
        referral_code="LM-ABC123",
        total_referrals=3,
        qualified_referrals=2,
        total_coins_earned=400,
        referrals=[
            {
                "referred_display_name": "Rohan M.",
                "qualified": True,
                "coins_earned": 200,
                "created_at": datetime.now(timezone.utc),
            },
            {
                "referred_display_name": "Priya S.",
                "qualified": True,
                "coins_earned": 200,
                "created_at": datetime.now(timezone.utc),
            },
            {
                "referred_display_name": "Amit K.",
                "qualified": False,
                "coins_earned": 0,
                "created_at": datetime.now(timezone.utc),
            },
        ],
    )
    assert resp.total_referrals == 3
    assert resp.qualified_referrals == 2
    assert len(resp.referrals) == 3
