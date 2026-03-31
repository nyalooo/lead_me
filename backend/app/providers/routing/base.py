"""Abstract base for routing providers.

Any routing provider (Google Routes, Mapbox Directions, HERE, MapmyIndia)
must implement this interface. The route engine service depends only on this
abstraction, never on a concrete provider.

To add a new provider:
1. Create a new file (e.g., here.py) in this directory
2. Subclass RoutingProvider
3. Implement all abstract methods
4. Register it in the factory (registry.py)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LatLng:
    lat: float
    lng: float


@dataclass
class TrafficSegment:
    """Traffic condition on a segment of a route."""
    start: LatLng
    end: LatLng
    speed_category: str  # "normal", "slow", "traffic_jam"
    speed_kmh: float | None = None


@dataclass
class RouteOption:
    """A single route returned by a routing provider."""
    provider: str  # e.g., "google", "mapbox", "here"
    distance_km: float
    duration_min: float
    duration_in_traffic_min: float | None = None
    polyline: str | None = None  # encoded polyline
    summary: str = ""  # e.g., "via Western Express Highway"
    traffic_segments: list[TrafficSegment] = field(default_factory=list)
    toll_cost: float | None = None
    raw_response: dict = field(default_factory=dict)  # provider-specific data


@dataclass
class RoutingRequest:
    """Standardized input for all routing providers."""
    origin: LatLng
    destination: LatLng
    departure_time: datetime | None = None
    alternatives: bool = True
    max_alternatives: int = 3
    traffic_aware: bool = True


@dataclass
class RoutingResponse:
    """Standardized output from all routing providers."""
    provider: str
    routes: list[RouteOption]
    request_id: str | None = None  # provider's request ID for debugging


class RoutingProvider(ABC):
    """Abstract interface for routing/directions providers.

    Implement this to add support for a new maps routing service.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'google', 'mapbox', 'here')."""
        ...

    @abstractmethod
    async def get_routes(self, request: RoutingRequest) -> RoutingResponse:
        """Fetch route alternatives between origin and destination.

        Must return at least one route. Should respect the traffic_aware
        and alternatives flags in the request.
        """
        ...

    @abstractmethod
    async def get_traffic(self, route_polyline: str) -> list[TrafficSegment]:
        """Get current traffic conditions along a route polyline.

        Returns traffic segments with speed categories.
        Some providers include this in get_routes(); implement this
        for on-demand traffic refresh without recalculating routes.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider's API is reachable and authenticated.

        Used for monitoring and automatic failover.
        """
        ...
