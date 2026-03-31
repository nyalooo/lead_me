"""SMS provider registry — selects which SMS provider to use.

Selection: SMS_PROVIDER env var, or auto-detect from configured keys,
or fallback to console (dev mode).
"""

import logging

from app.config import settings
from app.providers.sms.base import SMSProvider

logger = logging.getLogger(__name__)

_provider: SMSProvider | None = None


def _get_provider(name: str) -> SMSProvider:
    if name == "twilio":
        from app.providers.sms.twilio import TwilioSMSProvider
        return TwilioSMSProvider()
    elif name == "msg91":
        from app.providers.sms.msg91 import MSG91SMSProvider
        return MSG91SMSProvider()
    elif name == "console":
        from app.providers.sms.console import ConsoleSMSProvider
        return ConsoleSMSProvider()
    else:
        raise ValueError(f"Unknown SMS provider: {name}")


def get_sms_provider() -> SMSProvider:
    """Get the configured SMS provider."""
    global _provider
    if _provider is not None:
        return _provider

    # Explicit config
    if settings.sms_provider:
        _provider = _get_provider(settings.sms_provider)
        return _provider

    # Auto-detect
    if settings.twilio_account_sid:
        _provider = _get_provider("twilio")
        return _provider

    if settings.msg91_auth_key:
        _provider = _get_provider("msg91")
        return _provider

    # Fallback
    logger.warning("No SMS provider configured — using console (dev mode)")
    _provider = _get_provider("console")
    return _provider
