"""Google Routes API provider.

Docs: https://developers.google.com/maps/documentation/routes
Pricing: $5-15/1000 requests, $200/mo free credit
Best for: Most accurate Mumbai traffic data (Android telemetry)
"""

import httpx

from app.config import settings
from app.providers.routing.base import (
    LatLng,
    RouteOption,
    RoutingProvider,
    RoutingRequest,
    RoutingResponse,
    TrafficSegment,
)

GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


class GoogleRoutingProvider(RoutingProvider):

    @property
    def name(self) -> str:
        return "google"

    async def get_routes(self, request: RoutingRequest) -> RoutingResponse:
        body = {
            "origin": {
                "location": {
                    "latLng": {"latitude": request.origin.lat, "longitude": request.origin.lng}
                }
            },
            "destination": {
                "location": {
                    "latLng": {"latitude": request.destination.lat, "longitude": request.destination.lng}
                }
            },
            "travelMode": "DRIVE",
            "computeAlternativeRoutes": request.alternatives,
            "routeModifiers": {"avoidTolls": False, "avoidHighways": False},
        }

        if request.traffic_aware:
            body["routingPreference"] = "TRAFFIC_AWARE_OPTIMAL"

        if request.departure_time:
            body["departureTime"] = request.departure_time.isoformat()

        # Request traffic on polyline for segment-level data
        field_mask = (
            "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,"
            "routes.description,routes.travelAdvisory"
        )

        headers = {
            "X-Goog-Api-Key": settings.google_routes_api_key,
            "X-Goog-FieldMask": field_mask,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(GOOGLE_ROUTES_URL, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        routes = []
        for route_data in data.get("routes", []):
            duration_str = route_data.get("duration", "0s")
            duration_sec = int(duration_str.rstrip("s"))
            distance_m = route_data.get("distanceMeters", 0)

            routes.append(
                RouteOption(
                    provider=self.name,
                    distance_km=round(distance_m / 1000, 1),
                    duration_min=round(duration_sec / 60, 0),
                    duration_in_traffic_min=round(duration_sec / 60, 0),
                    polyline=route_data.get("polyline", {}).get("encodedPolyline"),
                    summary=route_data.get("description", ""),
                    raw_response=route_data,
                )
            )

        return RoutingResponse(provider=self.name, routes=routes)

    async def get_traffic(self, route_polyline: str) -> list[TrafficSegment]:
        # Google includes traffic data in the route response via
        # extraComputations: TRAFFIC_ON_POLYLINE. For on-demand refresh,
        # we'd re-request the route. Returning empty for now.
        # TODO: Implement TRAFFIC_ON_POLYLINE parsing
        return []

    async def health_check(self) -> bool:
        if not settings.google_routes_api_key:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    GOOGLE_ROUTES_URL,
                    json={
                        "origin": {"location": {"latLng": {"latitude": 19.076, "longitude": 72.877}}},
                        "destination": {"location": {"latLng": {"latitude": 19.076, "longitude": 72.878}}},
                        "travelMode": "DRIVE",
                    },
                    headers={
                        "X-Goog-Api-Key": settings.google_routes_api_key,
                        "X-Goog-FieldMask": "routes.duration",
                        "Content-Type": "application/json",
                    },
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False
