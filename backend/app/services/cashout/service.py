"""Cashout business logic — coin-to-crypto conversion and wallet management."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.providers.crypto.base import TransferRequest, TransactionStatus
from app.providers.crypto.registry import get_crypto_provider
from app.services.cashout.models import CashoutRequest, WalletLink
from app.services.rewards.models import CoinTransaction
from app.services.rewards.service import TIERS
from app.services.users.models import User

logger = logging.getLogger(__name__)

# Cashout constraints
MIN_CASHOUT_COINS = 1000  # minimum coins to cash out
CASHOUT_COOLDOWN_HOURS = 24  # hours between cashouts


def get_conversion_rate(currency: str) -> int:
    """Get coins-per-crypto-unit rate for a currency."""
    rates = {
        "XRP": settings.xrp_coins_per_xrp,
        "SOL": settings.sol_coins_per_sol,
        "ETH": settings.eth_coins_per_eth,
    }
    return rates.get(currency, settings.xrp_coins_per_xrp)


def calculate_cashout(coins: int, tier: str, currency: str) -> dict:
    """Calculate crypto amount for a given coin amount with tier bonus.

    Tier bonuses:
    - rookie: 1.0x (no bonus)
    - regular: 1.1x (+10%)
    - pro: 1.25x (+25%)
    - legend: 1.5x (+50%)
    """
    tier_bonus = TIERS.get(tier, TIERS["rookie"])["xrp_bonus"]
    conversion_rate = get_conversion_rate(currency)
    crypto_amount = (coins / conversion_rate) * tier_bonus
    return {
        "crypto_amount": round(crypto_amount, 6),
        "tier_bonus": tier_bonus,
        "conversion_rate": conversion_rate,
    }


async def get_user_wallets(user_id: UUID, db: AsyncSession) -> list[WalletLink]:
    """Get all linked wallets for a user."""
    result = await db.execute(
        select(WalletLink)
        .where(WalletLink.user_id == user_id)
        .order_by(WalletLink.created_at)
    )
    return list(result.scalars().all())


async def get_wallet_by_currency(
    user_id: UUID, currency: str, db: AsyncSession
) -> WalletLink | None:
    """Get primary wallet for a specific currency."""
    result = await db.execute(
        select(WalletLink).where(
            WalletLink.user_id == user_id,
            WalletLink.currency == currency,
            WalletLink.is_primary.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def link_wallet(
    user_id: UUID,
    currency: str,
    address: str,
    label: str,
    db: AsyncSession,
) -> WalletLink:
    """Link a crypto wallet to a user account.

    Validates the address format using the crypto provider.
    One primary wallet per currency per user.
    """
    provider = get_crypto_provider()

    # Validate address if the provider supports this currency
    if provider.currency_code == currency:
        valid = await provider.validate_address(address)
        if not valid:
            raise ValueError(f"Invalid {currency} address: {address}")

    # Check if user already has a wallet for this currency
    existing = await get_wallet_by_currency(user_id, currency, db)
    if existing:
        # Update existing wallet
        existing.address = address
        existing.label = label or existing.label
        db.add(existing)
        await db.flush()
        return existing

    # Create new wallet link
    wallet = WalletLink(
        user_id=user_id,
        currency=currency,
        address=address,
        label=label,
        is_primary=True,
    )
    db.add(wallet)
    await db.flush()
    return wallet


async def remove_wallet(user_id: UUID, wallet_id: UUID, db: AsyncSession) -> bool:
    """Remove a linked wallet."""
    result = await db.execute(
        select(WalletLink).where(
            WalletLink.id == wallet_id,
            WalletLink.user_id == user_id,
        )
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        return False
    await db.delete(wallet)
    await db.flush()
    return True


async def check_cashout_eligibility(
    user: User, coins_amount: int, currency: str, db: AsyncSession
) -> tuple[bool, str | None]:
    """Check if user can cash out.

    Rules:
    - Must have enough coins
    - Must meet minimum cashout threshold
    - Must have a linked wallet for the currency
    - Must respect cooldown period
    - Currency must be active (not "coming soon")
    """
    # Check minimum
    if coins_amount < MIN_CASHOUT_COINS:
        return False, f"Minimum cashout is {MIN_CASHOUT_COINS} Route Coins"

    # Check balance
    if user.total_coins < coins_amount:
        return False, f"Insufficient balance: {user.total_coins} coins available"

    # Check currency availability
    from app.providers.crypto.registry import get_available_providers
    available = {p["currency"]: p["status"] for p in get_available_providers()}
    if currency not in available:
        return False, f"Unsupported currency: {currency}"
    if available[currency] == "coming_soon":
        return False, f"{currency} cashout is coming soon"

    # Check linked wallet
    wallet = await get_wallet_by_currency(user.id, currency, db)
    if not wallet:
        return False, f"No {currency} wallet linked. Please link a wallet first."

    # Check cooldown
    last_cashout = await db.execute(
        select(CashoutRequest)
        .where(
            CashoutRequest.user_id == user.id,
            CashoutRequest.status.in_(["pending", "processing", "completed"]),
        )
        .order_by(CashoutRequest.created_at.desc())
        .limit(1)
    )
    last = last_cashout.scalar_one_or_none()
    if last:
        cooldown_until = last.created_at + timedelta(hours=CASHOUT_COOLDOWN_HOURS)
        if datetime.now(timezone.utc) < cooldown_until:
            remaining = cooldown_until - datetime.now(timezone.utc)
            hours_left = int(remaining.total_seconds() / 3600)
            return False, f"Cooldown active: {hours_left}h remaining before next cashout"

    return True, None


async def create_cashout(
    user: User,
    coins_amount: int,
    currency: str,
    wallet_id: UUID | None,
    db: AsyncSession,
) -> CashoutRequest:
    """Create a cashout request and execute the transfer.

    Flow:
    1. Validate eligibility
    2. Deduct coins from user balance
    3. Record coin transaction (debit)
    4. Create cashout request
    5. Execute crypto transfer via provider
    6. Update cashout status
    """
    # Get wallet
    if wallet_id:
        result = await db.execute(
            select(WalletLink).where(
                WalletLink.id == wallet_id,
                WalletLink.user_id == user.id,
            )
        )
        wallet = result.scalar_one_or_none()
    else:
        wallet = await get_wallet_by_currency(user.id, currency, db)

    if not wallet:
        raise ValueError(f"No {currency} wallet found")

    # Calculate amount
    calc = calculate_cashout(coins_amount, user.tier, currency)

    # Create cashout request
    cashout = CashoutRequest(
        user_id=user.id,
        coins_amount=coins_amount,
        crypto_amount=calc["crypto_amount"],
        currency=currency,
        tier_bonus=calc["tier_bonus"],
        wallet_address=wallet.address,
        status="processing",
    )
    db.add(cashout)

    # Deduct coins from user
    user.total_coins -= coins_amount
    db.add(user)

    # Record coin transaction (debit)
    tx = CoinTransaction(
        user_id=user.id,
        type="cashout",
        coins=-coins_amount,
        description=f"Cashout: {coins_amount} coins → {calc['crypto_amount']} {currency}",
    )
    db.add(tx)
    await db.flush()

    # Execute crypto transfer
    provider = get_crypto_provider()
    transfer_result = await provider.transfer(
        TransferRequest(
            from_address=settings.platform_wallet_address,
            from_seed=settings.platform_wallet_seed,
            to_address=wallet.address,
            amount=calc["crypto_amount"],
            memo=f"LeadMe cashout {cashout.id}",
        )
    )

    if transfer_result.status == TransactionStatus.CONFIRMED:
        cashout.status = "completed"
        cashout.tx_hash = transfer_result.tx_hash
        cashout.explorer_url = transfer_result.explorer_url
        cashout.completed_at = datetime.now(timezone.utc)
    else:
        cashout.status = "failed"
        cashout.failure_reason = "Transfer failed on chain"
        # Refund coins on failure
        user.total_coins += coins_amount
        refund_tx = CoinTransaction(
            user_id=user.id,
            type="cashout_refund",
            coins=coins_amount,
            description=f"Cashout refund: transfer failed",
        )
        db.add(refund_tx)

    db.add(cashout)
    db.add(user)
    await db.flush()

    return cashout


async def get_cashout_history(
    user_id: UUID, limit: int, offset: int, db: AsyncSession
) -> tuple[list[CashoutRequest], int, dict[str, float]]:
    """Get cashout history for a user."""
    # Get cashouts
    result = await db.execute(
        select(CashoutRequest)
        .where(CashoutRequest.user_id == user_id)
        .order_by(CashoutRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    cashouts = list(result.scalars().all())

    # Total count
    count_result = await db.execute(
        select(func.count(CashoutRequest.id)).where(CashoutRequest.user_id == user_id)
    )
    total = count_result.scalar() or 0

    # Total cashed out per currency
    totals_result = await db.execute(
        select(CashoutRequest.currency, func.sum(CashoutRequest.crypto_amount))
        .where(
            CashoutRequest.user_id == user_id,
            CashoutRequest.status == "completed",
        )
        .group_by(CashoutRequest.currency)
    )
    total_by_currency = {"XRP": 0.0, "SOL": 0.0, "ETH": 0.0}
    for currency, amount in totals_result.all():
        total_by_currency[currency] = float(amount or 0)

    return cashouts, total, total_by_currency
