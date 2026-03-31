"""Auth request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+91\d{10}$", description="Indian phone number with +91 prefix")


class OTPVerify(BaseModel):
    phone: str = Field(..., pattern=r"^\+91\d{10}$")
    otp: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "AuthUserResponse"


class AuthUserResponse(BaseModel):
    id: UUID
    phone: str
    display_name: str
    tier: str

    model_config = {"from_attributes": True}
