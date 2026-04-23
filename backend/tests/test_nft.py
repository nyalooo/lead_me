"""Tests for NFT badge service logic and schemas."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.services.nft.service import _build_metadata, _status_message


# --- Helper factories ---

def _make_badge(**overrides):
    defaults = {
        "id": "traffic_hero",
        "name": "Traffic Hero",
        "description": "Your detour reduced congestion for 50+ commuters",
        "coins_bonus": 100,
        "criteria_type": "routes_count",
        "criteria_value": 50,
    }
    defaults.update(overrides)
    return type("Badge", (), defaults)()


def _make_user_badge(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "badge_id": "traffic_hero",
        "pinned": False,
        "earned_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return type("UserBadge", (), defaults)()


# --- Metadata builder ---

def test_build_metadata():
    badge = _make_badge()
    ub = _make_user_badge()
    meta = _build_metadata(badge, ub)

    assert meta["name"] == "LeadMe Badge: Traffic Hero"
    assert meta["badge_id"] == "traffic_hero"
    assert meta["criteria_type"] == "routes_count"
    assert meta["criteria_value"] == 50
    assert meta["issuer"] == "LeadMe"
    assert "earned_at" in meta


def test_build_metadata_custom_badge():
    badge = _make_badge(id="streak_30", name="30 Day Streak", criteria_type="streak_days", criteria_value=30)
    ub = _make_user_badge(badge_id="streak_30")
    meta = _build_metadata(badge, ub)

    assert meta["name"] == "LeadMe Badge: 30 Day Streak"
    assert meta["criteria_type"] == "streak_days"


# --- Status messages ---

def test_status_message_minted():
    assert "minted" in _status_message("minted", "xrpl").lower()


def test_status_message_pending():
    assert "queued" in _status_message("pending", "solana").lower()


def test_status_message_failed():
    assert "failed" in _status_message("failed", "ethereum").lower()


def test_status_message_unknown():
    msg = _status_message("unknown_status", "xrpl")
    assert msg == "Unknown status"


# --- XRPL mock mint ---

@pytest.mark.asyncio
async def test_mint_xrpl_nft():
    from app.services.nft.service import _mint_xrpl_nft
    result = await _mint_xrpl_nft("rTestAddress123", {"name": "Test Badge"})

    assert "token_id" in result
    assert "tx_hash" in result
    assert result["tx_hash"].startswith("NFT_")
    assert "explorer_url" in result


@pytest.mark.asyncio
async def test_mint_xrpl_nft_deterministic():
    from app.services.nft.service import _mint_xrpl_nft
    r1 = await _mint_xrpl_nft("addr", {"name": "Badge"})
    r2 = await _mint_xrpl_nft("addr", {"name": "Badge"})
    assert r1["token_id"] == r2["token_id"]


# --- Chain dispatch ---

@pytest.mark.asyncio
async def test_mint_on_chain_solana_not_implemented():
    from app.services.nft.service import _mint_on_chain
    with pytest.raises(NotImplementedError):
        await _mint_on_chain("solana", "addr", {})


@pytest.mark.asyncio
async def test_mint_on_chain_ethereum_not_implemented():
    from app.services.nft.service import _mint_on_chain
    with pytest.raises(NotImplementedError):
        await _mint_on_chain("ethereum", "addr", {})


@pytest.mark.asyncio
async def test_mint_on_chain_invalid():
    from app.services.nft.service import _mint_on_chain
    with pytest.raises(ValueError):
        await _mint_on_chain("bitcoin", "addr", {})


# --- Schema validation ---

def test_mint_request_valid():
    from app.services.nft.schemas import MintNFTRequest
    req = MintNFTRequest(
        user_badge_id=uuid.uuid4(),
        chain="xrpl",
        wallet_address="rN7n3473SaZBCG4dFL83w7p1W6cfJRrcmZ",
    )
    assert req.chain == "xrpl"


def test_mint_request_invalid_chain():
    from app.services.nft.schemas import MintNFTRequest
    with pytest.raises(ValidationError):
        MintNFTRequest(
            user_badge_id=uuid.uuid4(),
            chain="bitcoin",
            wallet_address="addr123456789",
        )


def test_mint_request_short_address():
    from app.services.nft.schemas import MintNFTRequest
    with pytest.raises(ValidationError):
        MintNFTRequest(
            user_badge_id=uuid.uuid4(),
            chain="xrpl",
            wallet_address="short",
        )


def test_nft_badge_response():
    from app.services.nft.schemas import NFTBadgeResponse
    resp = NFTBadgeResponse(
        id=uuid.uuid4(),
        badge_id="traffic_hero",
        badge_name="Traffic Hero",
        chain="xrpl",
        token_id="ABC123",
        tx_hash="NFT_ABC123",
        wallet_address="rTestAddr",
        explorer_url="https://testnet.xrpl.org/nft/ABC123",
        status="minted",
        created_at=datetime.now(timezone.utc),
        minted_at=datetime.now(timezone.utc),
    )
    assert resp.status == "minted"
    assert resp.badge_name == "Traffic Hero"


def test_nft_list_response():
    from app.services.nft.schemas import NFTListResponse
    resp = NFTListResponse(nfts=[], total=0)
    assert resp.total == 0


def test_mint_status_response():
    from app.services.nft.schemas import MintStatusResponse
    resp = MintStatusResponse(
        nft_id=uuid.uuid4(),
        status="minted",
        tx_hash="NFT_123",
        explorer_url="https://testnet.xrpl.org/nft/123",
        message="NFT minted on xrpl!",
    )
    assert resp.status == "minted"
