"""Twilio SMS provider.

Docs: https://www.twilio.com/docs/sms
Pricing: ~$0.0079/SMS to India
"""

import httpx

from app.config import settings
from app.providers.sms.base import SMSProvider

TWILIO_API_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


class TwilioSMSProvider(SMSProvider):

    @property
    def name(self) -> str:
        return "twilio"

    async def send_otp(self, phone: str, otp: str) -> bool:
        url = TWILIO_API_URL.format(sid=settings.twilio_account_sid)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                data={
                    "To": phone,
                    "From": settings.twilio_phone_number,
                    "Body": f"Your LeadMe verification code is: {otp}. Valid for 5 minutes.",
                },
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                timeout=15,
            )
            return resp.status_code == 201
