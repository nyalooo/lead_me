"""Social & referral business logic."""

import hashlib
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.social.models import Referral, ReferralCode, ShareEvent
from app.services.rewards.models import CoinTransaction
from app.services.users.models import User

logger = logging.getLogger(__name__)


def _generate_referral_code(user_id: UUID) -> str:
    digest = hashlib.sha256(str(user_id).encode()).hexdigest()[:6].upper()
    return f"LM-{digest}"


async def get_or_create_referral_code(user_id: UUID, db: AsyncSession) -> dict:
    """Get the user's referral code, creating one if it doesn't exist."""
    result = await db.execute(
        select(ReferralCode).where(ReferralCode.user_id == user_id)
    )
    code_obj = result.scalar_one_or_none()

    if not code_obj:
        code = _generate_referral_code(user_id)
        code_obj = ReferralCode(user_id=user_id, code=code)
        db.add(code_obj)
        await db.flush()

    return {
        "code": code_obj.code,
        "uses": code_obj.uses,
        "max_uses": code_obj.max_uses,
        "active": code_obj.active,
        "share_url": f"{settings.app_base_url}/join?ref={code_obj.code}",
    }


async def get_referral_stats(user_id: UUID, db: AsyncSession) -> dict:
    """Get referral statistics for a user."""
    code_data = await get_or_create_referral_code(user_id, db)

    result = await db.execute(
        select(Referral, User)
        .join(User, Referral.referred_id == User.id)
        .where(Referral.referrer_id == user_id)
        .order_by(Referral.created_at.desc())
    )
    rows = result.all()

    referrals = []
    total_coins = 0
    qualified = 0
    for ref, user in rows:
        total_coins += ref.referrer_coins_earned
        if ref.referred_qualified:
            qualified += 1
        referrals.append({
            "referred_display_name": user.display_name,
            "qualified": ref.referred_qualified,
            "coins_earned": ref.referrer_coins_earned,
            "created_at": ref.created_at,
        })

    return {
        "referral_code": code_data["code"],
        "total_referrals": len(referrals),
        "qualified_referrals": qualified,
        "total_coins_earned": total_coins,
        "referrals": referrals,
    }


async def apply_referral_code(
    user_id: UUID, code: str, db: AsyncSession
) -> dict:
    """Apply a referral code for a new user."""
    # Check if user already has a referral
    existing = await db.execute(
        select(Referral).where(Referral.referred_id == user_id)
    )
    if existing.scalar_one_or_none():
        return {"applied": False, "message": "Already used a referral code", "bonus_coins": 0}

    # Find the referral code
    code_result = await db.execute(
        select(ReferralCode).where(ReferralCode.code == code.upper(), ReferralCode.active.is_(True))
    )
    code_obj = code_result.scalar_one_or_none()
    if not code_obj:
        return {"applied": False, "message": "Invalid referral code", "bonus_coins": 0}

    # Can't refer yourself
    if code_obj.user_id == user_id:
        return {"applied": False, "message": "Cannot use your own referral code", "bonus_coins": 0}

    # Check max uses
    if code_obj.max_uses and code_obj.uses >= code_obj.max_uses:
        return {"applied": False, "message": "Referral code has reached its limit", "bonus_coins": 0}

    # Create referral
    referral = Referral(
        referrer_id=code_obj.user_id,
        referred_id=user_id,
        referred_coins_earned=settings.referral_bonus_referred,
    )
    db.add(referral)

    # Update code usage
    code_obj.uses += 1
    db.add(code_obj)

    # Give welcome bonus to referred user
    bonus = settings.referral_bonus_referred
    if bonus > 0:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        user.total_coins += bonus
        db.add(user)

        tx = CoinTransaction(
            user_id=user_id,
            type="referral_bonus",
            coins=bonus,
            description="Welcome bonus from referral",
        )
        db.add(tx)

    await db.flush()
    return {"applied": True, "message": "Referral code applied!", "bonus_coins": bonus}


async def check_referral_qualification(
    user_id: UUID, db: AsyncSession
) -> bool:
    """Check if a referred user has qualified (completed enough routes).
    Called after route completion. Returns True if newly qualified.
    """
    ref_result = await db.execute(
        select(Referral).where(
            Referral.referred_id == user_id,
            Referral.referred_qualified.is_(False),
        )
    )
    referral = ref_result.scalar_one_or_none()
    if not referral:
        return False

    # Check if user has completed enough routes
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    if user.total_routes < settings.referral_qualify_routes:
        return False

    # Qualify the referral
    now = datetime.now(timezone.utc)
    referral.referred_qualified = True
    referral.qualified_at = now

    # Award bonus to referrer
    bonus = settings.referral_bonus_referrer
    referral.referrer_coins_earned = bonus
    db.add(referral)

    if bonus > 0:
        referrer_result = await db.execute(select(User).where(User.id == referral.referrer_id))
        referrer = referrer_result.scalar_one()
        referrer.total_coins += bonus
        db.add(referrer)

        tx = CoinTransaction(
            user_id=referral.referrer_id,
            type="referral_bonus",
            coins=bonus,
            description=f"Referral qualified: {user.display_name}",
        )
        db.add(tx)

    await db.flush()
    return True


async def track_share(
    user_id: UUID, channel: str, content_type: str, content_id: str | None, db: AsyncSession
) -> dict:
    """Track a social share action."""
    event = ShareEvent(
        user_id=user_id,
        channel=channel,
        content_type=content_type,
        content_id=content_id,
    )
    db.add(event)
    await db.flush()

    code_data = await get_or_create_referral_code(user_id, db)
    share_url = code_data["share_url"]

    messages = {
        "referral": f"Join LeadMe and earn crypto for your commute! Use my code: {code_data['code']} {share_url}",
        "achievement": f"I just unlocked a new achievement on LeadMe! {share_url}",
        "challenge": f"Join me in this LeadMe challenge! {share_url}",
        "route": f"I'm earning crypto on my commute with LeadMe! {share_url}",
    }

    return {
        "shared": True,
        "share_url": share_url,
        "message": messages.get(content_type, f"Check out LeadMe! {share_url}"),
    }
