"""Cashout request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Wallet ---

class LinkWalletRequest(BaseModel):
    currency: str = Field(..., pattern="^(XRP|SOL|ETH)$", description="Cryptocurrency code")
    address: str = Field(..., min_length=5, max_length=200)
    label: str = Field("", max_length=100)


class WalletResponse(BaseModel):
    id: UUID
    currency: str
    address: str
    label: str
    verified: bool
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletsListResponse(BaseModel):
    wallets: list[WalletResponse]


# --- Cashout ---

class CashoutEstimateRequest(BaseModel):
    coins_amount: int = Field(..., gt=0)
    currency: str = Field("XRP", pattern="^(XRP|SOL|ETH)$")


class CashoutEstimateResponse(BaseModel):
    coins_amount: int
    crypto_amount: float
    currency: str
    tier_bonus: float
    conversion_rate: float  # coins per 1 crypto unit
    min_cashout_coins: int
    eligible: bool
    reason: str | None = None  # why not eligible


class CashoutCreateRequest(BaseModel):
    coins_amount: int = Field(..., gt=0)
    currency: str = Field("XRP", pattern="^(XRP|SOL|ETH)$")
    wallet_id: UUID | None = None  # use primary wallet if not specified


class CashoutResponse(BaseModel):
    id: UUID
    coins_amount: int
    crypto_amount: float
    currency: str
    tier_bonus: float
    wallet_address: str
    status: str
    tx_hash: str | None = None
    explorer_url: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class CashoutHistoryResponse(BaseModel):
    cashouts: list[CashoutResponse]
    total: int
    total_cashed_out: dict[str, float]  # {"XRP": 1.5, "SOL": 0.0}


# --- Crypto Info ---

class CryptoProviderInfo(BaseModel):
    name: str
    currency: str
    status: str  # "active" or "coming_soon"
    label: str


class SupportedCryptosResponse(BaseModel):
    active_provider: str
    providers: list[CryptoProviderInfo]
