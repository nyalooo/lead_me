"""Abstract base for SMS providers.

Any SMS provider (Twilio, MSG91, console/dev) must implement this interface.
The auth service depends only on this abstraction.

To add a new provider:
1. Create a new file in this directory
2. Subclass SMSProvider
3. Implement send_otp()
4. Register in registry.py
"""

from abc import ABC, abstractmethod


class SMSProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'twilio', 'msg91', 'console')."""
        ...

    @abstractmethod
    async def send_otp(self, phone: str, otp: str) -> bool:
        """Send an OTP to the given phone number.

        Returns True if sent successfully, False otherwise.
        """
        ...
