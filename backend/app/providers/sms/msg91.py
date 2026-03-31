"""MSG91 SMS provider.

Docs: https://docs.msg91.com/
Popular in India, good for Indian phone numbers.
Pricing: ~₹0.20/SMS
"""

import httpx

from app.config import settings
from app.providers.sms.base import SMSProvider

MSG91_API_URL = "https://control.msg91.com/api/v5/otp"


class MSG91SMSProvider(SMSProvider):

    @property
    def name(self) -> str:
        return "msg91"

    async def send_otp(self, phone: str, otp: str) -> bool:
        # MSG91 can generate OTP internally, but we send our own for consistency
        headers = {
            "authkey": settings.msg91_auth_key,
            "Content-Type": "application/json",
        }
        body = {
            "template_id": settings.msg91_template_id,
            "mobile": phone.lstrip("+"),
            "otp": otp,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(MSG91_API_URL, json=body, headers=headers, timeout=15)
            data = resp.json()
            return data.get("type") == "success"
