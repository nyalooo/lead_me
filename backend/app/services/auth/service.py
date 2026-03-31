"""Auth business logic — OTP generation and verification."""

import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.users.models import User

# In-memory OTP store (replace with Redis in production)
_otp_store: dict[str, tuple[str, datetime]] = {}


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return "".join(random.choices(string.digits, k=6))


async def request_otp(phone: str) -> str:
    """Generate and store an OTP for the given phone number.

    In production, this would send an SMS via a provider like Twilio or MSG91.
    For MVP, the OTP is returned directly (dev mode).
    """
    otp = generate_otp()
    expires = datetime.now(timezone.utc) + timedelta(seconds=settings.otp_expire_seconds)
    _otp_store[phone] = (otp, expires)
    # TODO: Send SMS via MSG91 or Twilio
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
