"""NFT badge API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.nft.schemas import (
    MintNFTRequest,
    MintStatusResponse,
    NFTBadgeResponse,
    NFTListResponse,
)
from app.services.nft.service import get_nft_status, get_user_nfts, mint_nft
from app.services.users.models import User

router = APIRouter()


@router.get("", response_model=NFTListResponse)
async def list_nfts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all NFT badges for the current user."""
    result = await get_user_nfts(user.id, db)
    return NFTListResponse(**result)


@router.post("/mint", response_model=MintStatusResponse)
async def mint(
    body: MintNFTRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mint an NFT for an earned badge."""
    result = await mint_nft(user.id, body.user_badge_id, body.chain, body.wallet_address, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return MintStatusResponse(**result)


@router.get("/{nft_id}/status", response_model=MintStatusResponse)
async def status(
    nft_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check the status of an NFT mint."""
    result = await get_nft_status(nft_id, user.id, db)
    if not result:
        raise HTTPException(status_code=404, detail="NFT not found")
    return MintStatusResponse(**result)
