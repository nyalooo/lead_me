"""Auth business logic — OTP generation, delivery via SMS provider, and verification."""

import logging
import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.providers.sms.registry import get_sms_provider
from app.services.users.models import User

logger = logging.getLogger(__name__)

# In-memory OTP store (replace with Redis in production for multi-instance)
_otp_store: dict[str, tuple[str, datetime]] = {}


def generate_otp() -> str:
    """Generate a cryptographically sufficient 6-digit OTP."""
    return "".join(random.choices(string.digits, k=6))


async def request_otp(phone: str) -> str:
    """Generate an OTP, store it, and send via the configured SMS provider.

    Returns the OTP string (visible in dev mode; production hides it).
    """
    otp = generate_otp()
    expires = datetime.now(timezone.utc) + timedelta(seconds=settings.otp_expire_seconds)
    _otp_store[phone] = (otp, expires)

    # Send via SMS provider (console in dev, Twilio/MSG91 in prod)
    sms = get_sms_provider()
    sent = await sms.send_otp(phone, otp)
    if not sent:
        logger.error(f"Failed to send OTP to {phone} via {sms.name}")

    return otp


async def verify_otp(phone: str, otp: str) -> bool:
    """Verify an OTP for the given phone number."""
    stored = _otp_store.get(phone)
    if stored is None:
        return False
    stored_otp, expires = stored
    if datetime.now(timezone.utc) > expires:
        del _otp_store[phone]
        return False
    if stored_otp != otp:
        return False
    del _otp_store[phone]
    return True


async def get_or_create_user(phone: str, db: AsyncSession) -> User:
    """Get existing user or create a new one."""
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(phone=phone)
        db.add(user)
        await db.flush()
    return user
