"""Crypto provider registry — resolves which crypto provider to use.

Selection logic:
1. Use the provider specified in CRYPTO_PROVIDER env var
2. Auto-detect based on which credentials are configured
3. Fall back to mock provider (always works, no credentials needed)

Supports automatic failover: if the primary provider's health check fails,
the registry can try the next available provider.

Supported providers:
- xrp: XRP Ledger (testnet/mainnet) — ACTIVE
- sol: Solana — COMING SOON
- eth: Ethereum/Polygon — COMING SOON
- mock: In-memory ledger (dev/testing) — ALWAYS AVAILABLE
"""

import logging

from app.config import settings
from app.providers.crypto.base import CryptoProvider

logger = logging.getLogger(__name__)

_providers: dict[str, CryptoProvider] = {}


def _get_provider(name: str) -> CryptoProvider:
    """Instantiate a provider by name."""
    if name == "xrp":
        from app.providers.crypto.xrp import XRPProvider
        return XRPProvider()
    elif name == "sol":
        from app.providers.crypto.sol import SolanaProvider
        return SolanaProvider()
    elif name == "eth":
        from app.providers.crypto.eth import EthereumProvider
        return EthereumProvider()
    elif name == "mock":
        from app.providers.crypto.mock import MockCryptoProvider
        return MockCryptoProvider()
    else:
        raise ValueError(f"Unknown crypto provider: {name}")


def get_available_providers() -> list[dict]:
    """List all registered crypto providers and their status."""
    providers = [
        {"name": "xrp", "currency": "XRP", "status": "active", "label": "XRP Ledger"},
        {"name": "sol", "currency": "SOL", "status": "coming_soon", "label": "Solana"},
        {"name": "eth", "currency": "ETH", "status": "coming_soon", "label": "Ethereum / Polygon"},
    ]
    return providers


def get_crypto_provider() -> CryptoProvider:
    """Get the configured crypto provider.

    Priority:
    1. Explicit CRYPTO_PROVIDER setting
    2. First provider with configured credentials
    3. Mock provider (fallback)
    """
    explicit = settings.crypto_provider
    if explicit:
        if explicit not in _providers:
            _providers[explicit] = _get_provider(explicit)
        return _providers[explicit]

    # Auto-detect based on available credentials
    if settings.xrpl_wallet_seed:
        if "xrp" not in _providers:
            _providers["xrp"] = _get_provider("xrp")
        return _providers["xrp"]

    # Future: check for SOL/ETH credentials here

    # Fallback to mock
    logger.warning("No crypto credentials configured — using mock provider")
    if "mock" not in _providers:
        _providers["mock"] = _get_provider("mock")
    return _providers["mock"]


async def get_crypto_provider_with_failover() -> CryptoProvider:
    """Get a healthy crypto provider, with automatic failover.

    Tries the primary provider first. If its health check fails,
    tries others in order: xrp → mock.
    """
    primary = get_crypto_provider()
    if await primary.health_check():
        return primary

    logger.warning(f"Primary crypto provider '{primary.name}' failed health check, trying failover")

    fallback_order = ["xrp", "mock"]
    for name in fallback_order:
        if name == primary.name:
            continue
        try:
            provider = _get_provider(name)
            if await provider.health_check():
                logger.info(f"Failover to crypto provider: {name}")
                _providers[name] = provider
                return provider
        except Exception:
            continue

    # Last resort
    logger.error("All crypto providers failed — using mock")
    return _get_provider("mock")
