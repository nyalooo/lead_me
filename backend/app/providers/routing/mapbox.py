"""Mapbox Directions API provider.

Docs: https://docs.mapbox.com/api/navigation/directions/
Pricing: 100K free requests/month, then $0.50-5.00/1000
Best for: Generous free tier, good Mumbai coverage, custom map styling
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

MAPBOX_DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox"


class MapboxRoutingProvider(RoutingProvider):

    @property
    def name(self) -> str:
        return "mapbox"

    async def get_routes(self, request: RoutingRequest) -> RoutingResponse:
        # Mapbox uses lng,lat (reversed from Google's lat,lng)
        coords = (
            f"{request.origin.lng},{request.origin.lat}"
            f";{request.destination.lng},{request.destination.lat}"
        )

        profile = "driving-traffic" if request.traffic_aware else "driving"
        url = f"{MAPBOX_DIRECTIONS_URL}/{profile}/{coords}"

        params = {
            "access_token": settings.mapbox_access_token,
            "alternatives": str(request.alternatives).lower(),
            "geometries": "polyline6",
            "overview": "full",
            "annotations": "congestion,duration,speed",
        }

        if request.departure_time:
            params["depart_at"] = request.departure_time.strftime("%Y-%m-%dT%H:%M")

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        routes = []
        for route_data in data.get("routes", []):
            duration_sec = route_data.get("duration", 0)
            distance_m = route_data.get("distance", 0)
            traffic_duration = route_data.get("duration_typical", duration_sec)

            # Parse congestion annotations into traffic segments
            traffic_segments = []
            legs = route_data.get("legs", [])
            for leg in legs:
                annotation = leg.get("annotation", {})
                congestion = annotation.get("congestion", [])
                for level in congestion:
                    speed_cat = {
                        "low": "normal",
                        "moderate": "slow",
                        "heavy": "traffic_jam",
                        "severe": "traffic_jam",
                    }.get(level, "normal")
                    traffic_segments.append(
                        TrafficSegment(
                            start=LatLng(lat=0, lng=0),  # simplified; full impl would decode polyline
                            end=LatLng(lat=0, lng=0),
                            speed_category=speed_cat,
                        )
                    )

            routes.append(
                RouteOption(
                    provider=self.name,
                    distance_km=round(distance_m / 1000, 1),
                    duration_min=round(duration_sec / 60, 0),
                    duration_in_traffic_min=round(traffic_duration / 60, 0),
                    polyline=route_data.get("geometry"),
                    summary=route_data.get("legs", [{}])[0].get("summary", ""),
                    traffic_segments=traffic_segments,
                    raw_response=route_data,
                )
            )

        return RoutingResponse(provider=self.name, routes=routes)

    async def get_traffic(self, route_polyline: str) -> list[TrafficSegment]:
        # Mapbox includes congestion annotations in the directions response.
        # For standalone traffic, Mapbox Traffic tileset (vector tiles) is used
        # on the frontend map layer, not via REST API.
        return []

    async def health_check(self) -> bool:
        if not settings.mapbox_access_token:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{MAPBOX_DIRECTIONS_URL}/driving/72.877,19.076;72.878,19.076",
                    params={"access_token": settings.mapbox_access_token},
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False
