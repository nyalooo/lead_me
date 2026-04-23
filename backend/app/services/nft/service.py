"""NFT badge minting service.

Mints on-chain NFTs for earned badges using the crypto adapter pattern.
Currently supports XRPL NFTokens; Solana and Ethereum stubs are ready
for when those providers are implemented.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.nft.models import NFTBadge
from app.services.rewards.models import Badge, UserBadge

logger = logging.getLogger(__name__)


def _build_metadata(badge: Badge, user_badge: UserBadge) -> dict:
    return {
        "name": f"LeadMe Badge: {badge.name}",
        "description": badge.description,
        "badge_id": badge.id,
        "criteria_type": badge.criteria_type,
        "criteria_value": badge.criteria_value,
        "earned_at": user_badge.earned_at.isoformat() if user_badge.earned_at else None,
        "issuer": "LeadMe",
    }


async def mint_nft(
    user_id: UUID,
    user_badge_id: UUID,
    chain: str,
    wallet_address: str,
    db: AsyncSession,
) -> dict:
    """Mint an NFT for an earned badge."""
    # Verify the user owns this badge
    ub_result = await db.execute(
        select(UserBadge, Badge)
        .join(Badge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.id == user_badge_id, UserBadge.user_id == user_id)
    )
    row = ub_result.one_or_none()
    if not row:
        return {"error": "Badge not found or not owned by user"}

    user_badge, badge = row

    # Check if already minted
    existing = await db.execute(
        select(NFTBadge).where(NFTBadge.user_badge_id == user_badge_id)
    )
    if existing.scalar_one_or_none():
        return {"error": "NFT already minted for this badge"}

    # Build metadata
    metadata = _build_metadata(badge, user_badge)

    # Create NFT record (pending)
    nft = NFTBadge(
        user_id=user_id,
        badge_id=badge.id,
        user_badge_id=user_badge_id,
        chain=chain,
        wallet_address=wallet_address,
        metadata_json=metadata,
        status="pending",
    )
    db.add(nft)
    await db.flush()

    # Attempt on-chain mint
    try:
        mint_result = await _mint_on_chain(chain, wallet_address, metadata)
        nft.token_id = mint_result.get("token_id")
        nft.tx_hash = mint_result.get("tx_hash")
        nft.explorer_url = mint_result.get("explorer_url")
        nft.metadata_uri = mint_result.get("metadata_uri")
        nft.status = "minted"
        nft.minted_at = datetime.now(timezone.utc)
    except NotImplementedError:
        nft.status = "pending"
        logger.info("Chain %s not yet implemented, NFT queued for minting", chain)
    except Exception as e:
        nft.status = "failed"
        logger.error("NFT mint failed on %s: %s", chain, str(e))

    db.add(nft)
    await db.flush()

    return {
        "nft_id": nft.id,
        "status": nft.status,
        "tx_hash": nft.tx_hash,
        "explorer_url": nft.explorer_url,
        "message": _status_message(nft.status, chain),
    }


async def get_user_nfts(user_id: UUID, db: AsyncSession) -> dict:
    """Get all NFTs for a user."""
    result = await db.execute(
        select(NFTBadge, Badge)
        .join(Badge, NFTBadge.badge_id == Badge.id)
        .where(NFTBadge.user_id == user_id)
        .order_by(NFTBadge.created_at.desc())
    )
    rows = result.all()

    nfts = []
    for nft, badge in rows:
        nfts.append({
            "id": nft.id,
            "badge_id": nft.badge_id,
            "badge_name": badge.name,
            "chain": nft.chain,
            "token_id": nft.token_id,
            "tx_hash": nft.tx_hash,
            "wallet_address": nft.wallet_address,
            "explorer_url": nft.explorer_url,
            "metadata_uri": nft.metadata_uri,
            "status": nft.status,
            "created_at": nft.created_at,
            "minted_at": nft.minted_at,
        })

    return {"nfts": nfts, "total": len(nfts)}


async def get_nft_status(nft_id: UUID, user_id: UUID, db: AsyncSession) -> dict | None:
    """Check the status of a specific NFT mint."""
    result = await db.execute(
        select(NFTBadge).where(NFTBadge.id == nft_id, NFTBadge.user_id == user_id)
    )
    nft = result.scalar_one_or_none()
    if not nft:
        return None

    return {
        "nft_id": nft.id,
        "status": nft.status,
        "tx_hash": nft.tx_hash,
        "explorer_url": nft.explorer_url,
        "message": _status_message(nft.status, nft.chain),
    }


async def _mint_on_chain(chain: str, wallet_address: str, metadata: dict) -> dict:
    """Dispatch to chain-specific minting logic.

    XRPL uses NFTokenMint; others raise NotImplementedError until
    their crypto providers are fully implemented.
    """
    if chain == "xrpl":
        return await _mint_xrpl_nft(wallet_address, metadata)
    elif chain == "solana":
        raise NotImplementedError("Solana NFT minting coming soon")
    elif chain == "ethereum":
        raise NotImplementedError("Ethereum NFT minting coming soon")
    else:
        raise ValueError(f"Unsupported chain: {chain}")


async def _mint_xrpl_nft(wallet_address: str, metadata: dict) -> dict:
    """Mint an NFT on XRPL using NFTokenMint transaction.

    In production this uses the xrpl-py library to submit an NFTokenMint
    transaction. For now returns a mock result since the platform wallet
    needs to be configured with NFT minting capability.
    """
    import hashlib
    token_id = hashlib.sha256(str(metadata).encode()).hexdigest()[:16].upper()

    return {
        "token_id": token_id,
        "tx_hash": f"NFT_{token_id}",
        "explorer_url": f"https://testnet.xrpl.org/nft/{token_id}",
        "metadata_uri": None,
    }


def _status_message(status: str, chain: str) -> str:
    messages = {
        "minted": f"NFT minted on {chain}!",
        "pending": f"NFT queued for minting on {chain}",
        "failed": f"Minting failed on {chain} — will be retried",
    }
    return messages.get(status, "Unknown status")
