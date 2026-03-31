"""Console SMS provider — logs OTP to stdout.

Used for development and testing. No external service needed.
"""

import logging

from app.providers.sms.base import SMSProvider

logger = logging.getLogger(__name__)


class ConsoleSMSProvider(SMSProvider):

    @property
    def name(self) -> str:
        return "console"

    async def send_otp(self, phone: str, otp: str) -> bool:
        logger.info(f"[DEV OTP] {phone}: {otp}")
        print(f"\n{'='*40}")
        print(f"  OTP for {phone}: {otp}")
        print(f"{'='*40}\n")
        return True
