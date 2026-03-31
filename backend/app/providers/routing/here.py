"""HERE Routing API provider.

Docs: https://developer.here.com/documentation/routing-api/dev_guide/index.html
Pricing: 250K free transactions/month
Best for: Good India coverage, generous free tier, traffic incidents API
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

HERE_ROUTING_URL = "https://router.hereapi.com/v8/routes"


class HereRoutingProvider(RoutingProvider):

    @property
    def name(self) -> str:
        return "here"

    async def get_routes(self, request: RoutingRequest) -> RoutingResponse:
        params = {
            "apiKey": settings.here_api_key,
            "origin": f"{request.origin.lat},{request.origin.lng}",
            "destination": f"{request.destination.lat},{request.destination.lng}",
            "transportMode": "car",
            "return": "polyline,summary,travelSummary",
            "alternatives": min(request.max_alternatives, 3),
        }

        if request.departure_time:
            params["departureTime"] = request.departure_time.isoformat()

        async with httpx.AsyncClient() as client:
            resp = await client.get(HERE_ROUTING_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        routes = []
        for route_data in data.get("routes", []):
            for section in route_data.get("sections", []):
                summary = section.get("travelSummary", section.get("summary", {}))
                duration_sec = summary.get("duration", 0)
                traffic_duration = summary.get("typicalDuration", duration_sec)
                distance_m = summary.get("length", 0)

                routes.append(
                    RouteOption(
                        provider=self.name,
                        distance_km=round(distance_m / 1000, 1),
                        duration_min=round(duration_sec / 60, 0),
                        duration_in_traffic_min=round(traffic_duration / 60, 0),
                        polyline=section.get("polyline"),
                        summary=section.get("summary", {}).get("text", ""),
                        raw_response=route_data,
                    )
                )

        return RoutingResponse(provider=self.name, routes=routes)

    async def get_traffic(self, route_polyline: str) -> list[TrafficSegment]:
        # HERE offers a Traffic API (v7) for flow and incidents.
        # TODO: Implement /traffic/flow endpoint
        return []

    async def health_check(self) -> bool:
        if not settings.here_api_key:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    HERE_ROUTING_URL,
                    params={
                        "apiKey": settings.here_api_key,
                        "origin": "19.076,72.877",
                        "destination": "19.076,72.878",
                        "transportMode": "car",
                        "return": "summary",
                    },
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False
