"""Cashout API endpoints — wallet management, cashout, and crypto info."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.providers.crypto.registry import get_available_providers, get_crypto_provider
from app.services.cashout.schemas import (
    CashoutCreateRequest,
    CashoutEstimateRequest,
    CashoutEstimateResponse,
    CashoutHistoryResponse,
    CashoutResponse,
    CryptoProviderInfo,
    LinkWalletRequest,
    SupportedCryptosResponse,
    WalletResponse,
    WalletsListResponse,
)
from app.services.cashout.service import (
    MIN_CASHOUT_COINS,
    calculate_cashout,
    check_cashout_eligibility,
    create_cashout,
    get_cashout_history,
    get_user_wallets,
    link_wallet,
    remove_wallet,
)
from app.services.users.models import User

router = APIRouter()


# --- Crypto Info ---

@router.get("/cryptos", response_model=SupportedCryptosResponse)
async def list_supported_cryptos():
    """List all supported cryptocurrencies and their status."""
    provider = get_crypto_provider()
    providers = get_available_providers()
    return SupportedCryptosResponse(
        active_provider=provider.name,
        providers=[CryptoProviderInfo(**p) for p in providers],
    )


# --- Wallets ---

@router.get("/wallets", response_model=WalletsListResponse)
async def list_wallets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all linked wallets for the current user."""
    wallets = await get_user_wallets(user.id, db)
    return WalletsListResponse(
        wallets=[WalletResponse.model_validate(w) for w in wallets]
    )


@router.post("/wallets", response_model=WalletResponse, status_code=201)
async def add_wallet(
    body: LinkWalletRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a cryptocurrency wallet to your account."""
    try:
        wallet = await link_wallet(
            user_id=user.id,
            currency=body.currency,
            address=body.address,
            label=body.label,
            db=db,
        )
        await db.commit()
        return WalletResponse.model_validate(wallet)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/wallets/{wallet_id}")
async def delete_wallet(
    wallet_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a linked wallet."""
    removed = await remove_wallet(user.id, wallet_id, db)
    if not removed:
        raise HTTPException(status_code=404, detail="Wallet not found")
    await db.commit()
    return {"ok": True}


# --- Cashout ---

@router.post("/estimate", response_model=CashoutEstimateResponse)
async def estimate_cashout(
    body: CashoutEstimateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estimate how much crypto you'll receive for a given coin amount."""
    calc = calculate_cashout(body.coins_amount, user.tier, body.currency)
    eligible, reason = await check_cashout_eligibility(
        user, body.coins_amount, body.currency, db
    )
    return CashoutEstimateResponse(
        coins_amount=body.coins_amount,
        crypto_amount=calc["crypto_amount"],
        currency=body.currency,
        tier_bonus=calc["tier_bonus"],
        conversion_rate=calc["conversion_rate"],
        min_cashout_coins=MIN_CASHOUT_COINS,
        eligible=eligible,
        reason=reason,
    )


@router.post("/cashout", response_model=CashoutResponse, status_code=201)
async def do_cashout(
    body: CashoutCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cash out Route Coins to cryptocurrency.

    Converts coins to crypto and transfers to your linked wallet.
    Tier bonus is applied automatically.
    """
    # Check eligibility
    eligible, reason = await check_cashout_eligibility(
        user, body.coins_amount, body.currency, db
    )
    if not eligible:
        raise HTTPException(status_code=400, detail=reason)

    try:
        cashout = await create_cashout(
            user=user,
            coins_amount=body.coins_amount,
            currency=body.currency,
            wallet_id=body.wallet_id,
            db=db,
        )
        await db.commit()
        return CashoutResponse.model_validate(cashout)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=CashoutHistoryResponse)
async def cashout_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get cashout history."""
    cashouts, total, totals = await get_cashout_history(user.id, limit, offset, db)
    return CashoutHistoryResponse(
        cashouts=[CashoutResponse.model_validate(c) for c in cashouts],
        total=total,
        total_cashed_out=totals,
    )
