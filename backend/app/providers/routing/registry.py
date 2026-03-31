"""Provider registry — resolves which routing provider to use.

Selection logic:
1. Use the provider specified in ROUTING_PROVIDER env var
2. Auto-detect based on which API keys are configured
3. Fall back to mock provider (always works, no API key needed)

Supports automatic failover: if the primary provider's health check fails,
the registry can try the next available provider.
"""

import logging

from app.config import settings
from app.providers.routing.base import RoutingProvider

logger = logging.getLogger(__name__)

# Lazy-loaded provider instances
_providers: dict[str, RoutingProvider] = {}


def _get_provider(name: str) -> RoutingProvider:
    """Instantiate a provider by name."""
    if name == "google":
        from app.providers.routing.google import GoogleRoutingProvider
        return GoogleRoutingProvider()
    elif name == "mapbox":
        from app.providers.routing.mapbox import MapboxRoutingProvider
        return MapboxRoutingProvider()
    elif name == "here":
        from app.providers.routing.here import HereRoutingProvider
        return HereRoutingProvider()
    elif name == "mock":
        from app.providers.routing.mock import MockRoutingProvider
        return MockRoutingProvider()
    else:
        raise ValueError(f"Unknown routing provider: {name}")


def get_routing_provider() -> RoutingProvider:
    """Get the configured routing provider.

    Priority:
    1. Explicit ROUTING_PROVIDER setting
    2. First provider with a configured API key
    3. Mock provider (fallback)
    """
    # Check explicit config
    explicit = settings.routing_provider
    if explicit:
        if explicit not in _providers:
            _providers[explicit] = _get_provider(explicit)
        return _providers[explicit]

    # Auto-detect based on available API keys
    if settings.google_routes_api_key:
        if "google" not in _providers:
            _providers["google"] = _get_provider("google")
        return _providers["google"]

    if settings.mapbox_access_token:
        if "mapbox" not in _providers:
            _providers["mapbox"] = _get_provider("mapbox")
        return _providers["mapbox"]

    if settings.here_api_key:
        if "here" not in _providers:
            _providers["here"] = _get_provider("here")
        return _providers["here"]

    # Fallback to mock
    logger.warning("No routing API keys configured — using mock provider")
    if "mock" not in _providers:
        _providers["mock"] = _get_provider("mock")
    return _providers["mock"]


async def get_routing_provider_with_failover() -> RoutingProvider:
    """Get a healthy routing provider, with automatic failover.

    Tries the primary provider first. If its health check fails,
    tries others in order: google → mapbox → here → mock.
    """
    primary = get_routing_provider()
    if await primary.health_check():
        return primary

    logger.warning(f"Primary routing provider '{primary.name}' failed health check, trying failover")

    fallback_order = ["google", "mapbox", "here", "mock"]
    for name in fallback_order:
        if name == primary.name:
            continue
        try:
            provider = _get_provider(name)
            if await provider.health_check():
                logger.info(f"Failover to routing provider: {name}")
                _providers[name] = provider
                return provider
        except Exception:
            continue

    # Last resort
    logger.error("All routing providers failed — using mock")
    return _get_provider("mock")
