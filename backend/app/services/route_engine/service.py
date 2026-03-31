"""Route engine business logic — route calculation, assignment, and load balancing."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.route_engine.models import Route, RouteAssignment, LocationUpdate
from app.services.route_engine.schemas import LatLng


def validate_mumbai_coordinates(point: LatLng) -> bool:
    """Check if coordinates fall within Mumbai bounding box."""
    return (
        settings.mumbai_lat_min <= point.lat <= settings.mumbai_lat_max
        and settings.mumbai_lng_min <= point.lng <= settings.mumbai_lng_max
    )


def calculate_load_score(
    active_commuters: int,
    scheduled_commuters: int,
    historical_avg: float,
    capacity: int,
) -> float:
    """Calculate weighted load score for a route.

    Formula:
        score = (active × 1.0 + scheduled × 0.7 + historical × 0.3) / capacity

    Returns a value between 0.0 (empty) and 1.0+ (over capacity).
    """
    if capacity <= 0:
        return 1.0
    weighted_load = (active_commuters * 1.0) + (scheduled_commuters * 0.7) + (historical_avg * 0.3)
    return weighted_load / capacity


def get_load_status(score: float) -> str:
    """Convert numeric load score to human-readable status."""
    if score < 0.4:
        return "clear"
    elif score < 0.7:
        return "moderate"
    return "busy"


def is_peak_hour(dt: datetime) -> bool:
    """Check if the given time falls within Mumbai peak hours."""
    hour = dt.hour
    return (8 <= hour < 10) or (18 <= hour < 21)


async def get_or_create_routes(
    origin: LatLng,
    destination: LatLng,
    db: AsyncSession,
) -> list[Route]:
    """Fetch existing routes or create mock routes for the origin-destination pair.

    In production, this calls Google Routes API to get real alternatives.
    For MVP, we generate synthetic routes based on the coordinates.
    """
    # Check for existing cached routes (within ~500m of origin/destination)
    tolerance = 0.005  # ~500m
    result = await db.execute(
        select(Route).where(
            Route.origin_lat.between(origin.lat - tolerance, origin.lat + tolerance),
            Route.origin_lng.between(origin.lng - tolerance, origin.lng + tolerance),
            Route.destination_lat.between(destination.lat - tolerance, destination.lat + tolerance),
            Route.destination_lng.between(destination.lng - tolerance, destination.lng + tolerance),
        )
    )
    existing = list(result.scalars().all())
    if existing:
        return existing

    # Generate mock routes (replace with Google Routes API call)
    # Calculate approximate distance using simple Euclidean (good enough for mock)
    lat_diff = abs(destination.lat - origin.lat)
    lng_diff = abs(destination.lng - origin.lng)
    approx_km = ((lat_diff * 111) ** 2 + (lng_diff * 85) ** 2) ** 0.5  # rough km

    routes = []
    for i in range(min(settings.max_alternative_routes, 3)):
        detour_factor = 1.0 + (i * 0.08)  # each alternative is ~8% longer
        route = Route(
            origin_lat=origin.lat,
            origin_lng=origin.lng,
            destination_lat=destination.lat,
            destination_lng=destination.lng,
            distance_km=round(approx_km * detour_factor, 1),
            base_duration_min=round(approx_km * detour_factor * 3.5, 0),  # ~3.5 min/km in Mumbai
            capacity_estimate=1000 + (i * 500),  # wider roads for alternative routes
        )
        db.add(route)
        routes.append(route)

    await db.flush()
    return routes


async def assign_best_route(
    routes: list[Route],
    user_id: uuid.UUID,
    origin: LatLng,
    destination: LatLng,
    db: AsyncSession,
    schedule_id: uuid.UUID | None = None,
) -> tuple[RouteAssignment, Route, list[Route]]:
    """Assign the route with the lowest load score to the user.

    Returns (assignment, assigned_route, other_routes).
    """
    # Calculate load scores and pick the best route
    best_route = None
    best_score = float("inf")
    route_scores: dict[uuid.UUID, float] = {}

    for route in routes:
        # Count scheduled commuters for this route
        scheduled_count_result = await db.execute(
            select(func.count(RouteAssignment.id)).where(
                RouteAssignment.route_id == route.id,
                RouteAssignment.status == "assigned",
            )
        )
        scheduled_count = scheduled_count_result.scalar() or 0

        score = calculate_load_score(
            active_commuters=route.active_commuters,
            scheduled_commuters=scheduled_count,
            historical_avg=0.0,  # TODO: implement historical tracking
            capacity=route.capacity_estimate,
        )
        route_scores[route.id] = score

        if score < best_score:
            best_score = score
            best_route = route

    # Calculate detour percentage relative to shortest route
    shortest_distance = min(r.distance_km for r in routes)
    detour_pct = ((best_route.distance_km - shortest_distance) / shortest_distance * 100) if shortest_distance > 0 else 0.0

    # Cap detour at max allowed
    if detour_pct > settings.max_detour_percent:
        # Fall back to shortest route
        best_route = min(routes, key=lambda r: r.distance_km)
        detour_pct = 0.0

    # Create assignment
    assignment = RouteAssignment(
        user_id=user_id,
        route_id=best_route.id,
        schedule_id=schedule_id,
        origin_lat=origin.lat,
        origin_lng=origin.lng,
        destination_lat=destination.lat,
        destination_lng=destination.lng,
        detour_percent=round(detour_pct, 1),
    )
    db.add(assignment)

    # Increment active commuter count
    best_route.active_commuters += 1
    db.add(best_route)
    await db.flush()

    other_routes = [r for r in routes if r.id != best_route.id]
    return assignment, best_route, other_routes


async def record_location(
    assignment_id: uuid.UUID,
    lat: float,
    lng: float,
    timestamp: datetime,
    accuracy_m: float,
    db: AsyncSession,
) -> LocationUpdate:
    """Record a GPS location update for an active assignment."""
    update = LocationUpdate(
        assignment_id=assignment_id,
        lat=lat,
        lng=lng,
        accuracy_m=accuracy_m,
        timestamp=timestamp,
    )
    db.add(update)
    await db.flush()
    return update


async def complete_assignment(
    assignment_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> RouteAssignment:
    """Mark an assignment as completed and calculate compliance."""
    result = await db.execute(
        select(RouteAssignment).where(
            RouteAssignment.id == assignment_id,
            RouteAssignment.user_id == user_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise ValueError("Assignment not found")

    # Count location updates to determine basic compliance
    loc_count_result = await db.execute(
        select(func.count(LocationUpdate.id)).where(
            LocationUpdate.assignment_id == assignment_id
        )
    )
    loc_count = loc_count_result.scalar() or 0

    # Simple compliance: if we have location data, assume compliant
    # TODO: implement actual polyline matching for real compliance scoring
    compliance_score = min(1.0, loc_count / 5.0) if loc_count > 0 else 0.5
    compliant = compliance_score >= 0.6

    assignment.status = "completed"
    assignment.compliant = compliant
    assignment.compliance_score = round(compliance_score, 2)
    assignment.completed_at = datetime.now(timezone.utc)

    # Decrement active commuters on the route
    route_result = await db.execute(select(Route).where(Route.id == assignment.route_id))
    route = route_result.scalar_one_or_none()
    if route and route.active_commuters > 0:
        route.active_commuters -= 1
        db.add(route)

    db.add(assignment)
    await db.flush()
    return assignment
