"""Mock routing provider for development and testing.

Returns synthetic routes based on coordinates without calling any external API.
Always available, no API key needed.
"""

import uuid

from app.providers.routing.base import (
    RouteOption,
    RoutingProvider,
    RoutingRequest,
    RoutingResponse,
    TrafficSegment,
)

# Mumbai route templates for realistic mock data
ROUTE_NAMES = [
    "via Western Express Highway",
    "via SV Road",
    "via Link Road",
    "via Eastern Express Highway",
    "via LBS Marg",
]


class MockRoutingProvider(RoutingProvider):

    @property
    def name(self) -> str:
        return "mock"

    async def get_routes(self, request: RoutingRequest) -> RoutingResponse:
        lat_diff = abs(request.destination.lat - request.origin.lat)
        lng_diff = abs(request.destination.lng - request.origin.lng)
        approx_km = ((lat_diff * 111) ** 2 + (lng_diff * 85) ** 2) ** 0.5

        num_routes = min(request.max_alternatives, 3) if request.alternatives else 1

        routes = []
        for i in range(num_routes):
            detour_factor = 1.0 + (i * 0.08)
            distance = round(approx_km * detour_factor, 1)
            duration = round(distance * 3.5, 0)  # ~3.5 min/km in Mumbai traffic
            traffic_duration = round(duration * (1.1 + i * 0.05), 0)

            routes.append(
                RouteOption(
                    provider=self.name,
                    distance_km=distance,
                    duration_min=duration,
                    duration_in_traffic_min=traffic_duration,
                    polyline=None,
                    summary=ROUTE_NAMES[i % len(ROUTE_NAMES)],
                )
            )

        return RoutingResponse(
            provider=self.name,
            routes=routes,
            request_id=str(uuid.uuid4()),
        )

    async def get_traffic(self, route_polyline: str) -> list[TrafficSegment]:
        return []

    async def health_check(self) -> bool:
        return True
