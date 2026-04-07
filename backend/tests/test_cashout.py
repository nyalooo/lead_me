"""Tests for cashout service logic and crypto provider registry."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.cashout.service import (
    calculate_cashout,
    get_conversion_rate,
    MIN_CASHOUT_COINS,
    CASHOUT_COOLDOWN_HOURS,
)
from app.providers.crypto.mock import MockCryptoProvider
from app.providers.crypto.base import TransferRequest, TransactionStatus


# --- Conversion rates ---

def test_conversion_rate_xrp():
    rate = get_conversion_rate("XRP")
    assert rate == 10000


def test_conversion_rate_sol():
    rate = get_conversion_rate("SOL")
    assert rate == 5000


def test_conversion_rate_eth():
    rate = get_conversion_rate("ETH")
    assert rate == 50000


# --- Cashout calculation ---

def test_calculate_cashout_rookie():
    result = calculate_cashout(coins=10000, tier="rookie", currency="XRP")
    assert result["crypto_amount"] == 1.0  # 10000 / 10000 * 1.0
    assert result["tier_bonus"] == 1.0
    assert result["conversion_rate"] == 10000


def test_calculate_cashout_regular_tier_bonus():
    result = calculate_cashout(coins=10000, tier="regular", currency="XRP")
    assert result["crypto_amount"] == 1.1  # 10000 / 10000 * 1.1
    assert result["tier_bonus"] == 1.1


def test_calculate_cashout_pro_tier_bonus():
    result = calculate_cashout(coins=10000, tier="pro", currency="XRP")
    assert result["crypto_amount"] == 1.25  # 10000 / 10000 * 1.25
    assert result["tier_bonus"] == 1.25


def test_calculate_cashout_legend_tier_bonus():
    result = calculate_cashout(coins=10000, tier="legend", currency="XRP")
    assert result["crypto_amount"] == 1.5  # 10000 / 10000 * 1.5
    assert result["tier_bonus"] == 1.5


def test_calculate_cashout_small_amount():
    result = calculate_cashout(coins=1000, tier="rookie", currency="XRP")
    assert result["crypto_amount"] == 0.1  # 1000 / 10000 * 1.0


def test_calculate_cashout_sol_rate():
    result = calculate_cashout(coins=5000, tier="rookie", currency="SOL")
    assert result["crypto_amount"] == 1.0  # 5000 / 5000 * 1.0
    assert result["conversion_rate"] == 5000


def test_calculate_cashout_eth_rate():
    result = calculate_cashout(coins=50000, tier="rookie", currency="ETH")
    assert result["crypto_amount"] == 1.0  # 50000 / 50000 * 1.0
    assert result["conversion_rate"] == 50000


# --- Constants ---

def test_min_cashout_coins():
    assert MIN_CASHOUT_COINS == 1000


def test_cooldown_hours():
    assert CASHOUT_COOLDOWN_HOURS == 24


# --- Mock crypto provider ---

@pytest.mark.asyncio
async def test_mock_provider_properties():
    provider = MockCryptoProvider()
    assert provider.name == "mock"
    assert provider.currency_code == "MOCK"
    assert provider.network_name == "mock-devnet"


@pytest.mark.asyncio
async def test_mock_provider_validate_address():
    provider = MockCryptoProvider()
    assert await provider.validate_address("rValidAddress123") is True
    assert await provider.validate_address("ab") is False
    assert await provider.validate_address("") is False


@pytest.mark.asyncio
async def test_mock_provider_health():
    provider = MockCryptoProvider()
    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_mock_provider_balance():
    provider = MockCryptoProvider()
    balance = await provider.get_balance("some_address")
    assert balance == 1_000_000.0


@pytest.mark.asyncio
async def test_mock_provider_transfer():
    provider = MockCryptoProvider()
    result = await provider.transfer(
        TransferRequest(
            from_address="platform_wallet_123456",
            from_seed="seed",
            to_address="user_wallet_123456",
            amount=1.5,
            memo="test cashout",
        )
    )
    assert result.status == TransactionStatus.CONFIRMED
    assert result.amount == 1.5
    assert result.tx_hash.startswith("mock_")
    assert result.currency == "MOCK"


@pytest.mark.asyncio
async def test_mock_provider_transfer_insufficient():
    provider = MockCryptoProvider()
    # Drain the wallet first
    await provider.transfer(
        TransferRequest(
            from_address="empty_wallet_12345",
            from_seed="seed",
            to_address="user_wallet_123456",
            amount=999_999.0,
        )
    )
    # Now try to transfer more than remaining
    result = await provider.transfer(
        TransferRequest(
            from_address="empty_wallet_12345",
            from_seed="seed",
            to_address="user_wallet_123456",
            amount=5000.0,
        )
    )
    assert result.status == TransactionStatus.FAILED


@pytest.mark.asyncio
async def test_mock_provider_get_transaction():
    provider = MockCryptoProvider()
    # Do a transfer first
    transfer_result = await provider.transfer(
        TransferRequest(
            from_address="lookup_wallet_123456",
            from_seed="seed",
            to_address="user_wallet_123456",
            amount=1.0,
        )
    )
    # Look it up
    found = await provider.get_transaction(transfer_result.tx_hash)
    assert found is not None
    assert found.amount == 1.0


@pytest.mark.asyncio
async def test_mock_provider_get_transaction_not_found():
    provider = MockCryptoProvider()
    found = await provider.get_transaction("nonexistent_tx")
    assert found is None


@pytest.mark.asyncio
async def test_mock_provider_min_transfer():
    provider = MockCryptoProvider()
    min_amount = await provider.get_min_transfer_amount()
    assert min_amount == 0.001


# --- Registry ---

def test_registry_get_available_providers():
    from app.providers.crypto.registry import get_available_providers
    providers = get_available_providers()
    assert len(providers) == 3
    names = [p["name"] for p in providers]
    assert "xrp" in names
    assert "sol" in names
    assert "eth" in names
    # XRP should be active
    xrp = next(p for p in providers if p["name"] == "xrp")
    assert xrp["status"] == "active"
    # SOL/ETH coming soon
    sol = next(p for p in providers if p["name"] == "sol")
    assert sol["status"] == "coming_soon"


def test_registry_fallback_to_mock():
    """With no credentials configured, should fall back to mock."""
    from app.providers.crypto.registry import get_crypto_provider
    provider = get_crypto_provider()
    # In test environment with no env vars, should be mock
    assert provider.name in ("mock", "xrp")  # depends on env


# --- Coming soon stubs ---

@pytest.mark.asyncio
async def test_solana_stub_health_check():
    from app.providers.crypto.sol import SolanaProvider
    provider = SolanaProvider()
    assert provider.name == "sol"
    assert provider.currency_code == "SOL"
    assert await provider.health_check() is False


@pytest.mark.asyncio
async def test_ethereum_stub_health_check():
    from app.providers.crypto.eth import EthereumProvider
    provider = EthereumProvider()
    assert provider.name == "eth"
    assert provider.currency_code == "ETH"
    assert await provider.health_check() is False


@pytest.mark.asyncio
async def test_solana_stub_raises():
    from app.providers.crypto.sol import SolanaProvider
    provider = SolanaProvider()
    with pytest.raises(NotImplementedError, match="coming soon"):
        await provider.validate_address("some_address")


@pytest.mark.asyncio
async def test_ethereum_stub_raises():
    from app.providers.crypto.eth import EthereumProvider
    provider = EthereumProvider()
    with pytest.raises(NotImplementedError, match="coming soon"):
        await provider.transfer(
            TransferRequest(
                from_address="a", from_seed="s", to_address="b", amount=1.0
            )
        )
