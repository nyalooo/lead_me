"""Auth endpoints — OTP-based phone authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.services.auth.schemas import AuthUserResponse, OTPRequest, OTPVerify, TokenResponse
from app.services.auth.service import get_or_create_user, request_otp, verify_otp

router = APIRouter()


@router.post("/request-otp")
async def request_otp_endpoint(body: OTPRequest):
    otp = await request_otp(body.phone)
    # In dev mode, return the OTP for testing. Remove in production.
    return {"message": "OTP sent", "expires_in": 300, "dev_otp": otp}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp_endpoint(body: OTPVerify, db: AsyncSession = Depends(get_db)):
    valid = await verify_otp(body.phone, body.otp)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")
    user = await get_or_create_user(body.phone, db)
    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        user=AuthUserResponse.model_validate(user),
    )
