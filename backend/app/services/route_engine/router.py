"""Route engine API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AssignmentNotFoundError, OutsideMumbaiError
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.route_engine import service
from app.services.route_engine.schemas import (
    EstimatedReward,
    RouteAssignRequest,
    RouteAssignResponse,
    RouteCompleteResponse,
    RouteInfo,
    RouteStatusResponse,
    TrackRequest,
    TrackResponse,
)
from app.services.rewards.service import calculate_reward, process_completion
from app.services.users.models import User

router = APIRouter()


@router.post("/assign", response_model=RouteAssignResponse)
async def assign_route(
    body: RouteAssignRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request a route assignment with load-balanced selection."""
    if not service.validate_mumbai_coordinates(body.origin):
        raise OutsideMumbaiError()
    if not service.validate_mumbai_coordinates(body.destination):
        raise OutsideMumbaiError()

    routes = await service.get_or_create_routes(body.origin, body.destination, db, body.departure_time)
    assignment, assigned_route, other_routes = await service.assign_best_route(
        routes, user.id, body.origin, body.destination, db
    )

    # Calculate estimated reward
    reward = calculate_reward(
        detour_percent=assignment.detour_percent,
        current_streak=0,  # TODO: fetch from rewards service
        departure_time=body.departure_time,
    )

    return RouteAssignResponse(
        assignment_id=assignment.id,
        assigned_route=RouteInfo(
            id=assigned_route.id,
            polyline=assigned_route.polyline,
            distance_km=assigned_route.distance_km,
            estimated_duration_min=assigned_route.base_duration_min,
            load_status=service.get_load_status(
                assigned_route.active_commuters / max(assigned_route.capacity_estimate, 1)
            ),
            detour_percent=assignment.detour_percent,
        ),
        alternative_routes=[
            RouteInfo(
                id=r.id,
                distance_km=r.distance_km,
                estimated_duration_min=r.base_duration_min,
                load_status=service.get_load_status(r.active_commuters / max(r.capacity_estimate, 1)),
            )
            for r in other_routes
        ],
        estimated_reward=reward,
    )


@router.get("/{route_id}/status", response_model=RouteStatusResponse)
async def get_route_status(
    route_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Get current load status for a route."""
    from sqlalchemy import select, func
    from app.services.route_engine.models import Route, RouteAssignment

    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if route is None:
        from app.common.exceptions import RouteNotFoundError
        raise RouteNotFoundError()

    scheduled_result = await db.execute(
        select(func.count(RouteAssignment.id)).where(
            RouteAssignment.route_id == route_id,
            RouteAssignment.status == "assigned",
        )
    )
    scheduled = scheduled_result.scalar() or 0

    load_score = service.calculate_load_score(
        active_commuters=route.active_commuters,
        scheduled_commuters=scheduled,
        historical_avg=0.0,
        capacity=route.capacity_estimate,
    )

    return RouteStatusResponse(
        route_id=route.id,
        load_score=round(load_score, 2),
        load_status=service.get_load_status(load_score),
        active_commuters=route.active_commuters,
        scheduled_commuters=scheduled,
        capacity_estimate=route.capacity_estimate,
    )


@router.post("/{assignment_id}/track", response_model=TrackResponse)
async def track_location(
    assignment_id: UUID,
    body: TrackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit GPS location update during active route."""
    await service.record_location(
        assignment_id=assignment_id,
        lat=body.lat,
        lng=body.lng,
        timestamp=body.timestamp,
        accuracy_m=body.accuracy_m,
        db=db,
    )
    # TODO: implement real on-route detection and progress calculation
    return TrackResponse(on_route=True, progress_percent=0.0)


@router.post("/{assignment_id}/complete", response_model=RouteCompleteResponse)
async def complete_route(
    assignment_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a route as completed and award rewards."""
    try:
        assignment = await service.complete_assignment(assignment_id, user.id, db)
    except ValueError:
        raise AssignmentNotFoundError()

    # Process rewards
    reward_result = await process_completion(user, assignment, db)

    return RouteCompleteResponse(
        assignment_id=assignment.id,
        compliant=assignment.compliant or False,
        compliance_score=assignment.compliance_score or 0.0,
        coins_earned=reward_result["coins_earned"],
        streak_day=reward_result["streak_day"],
        badges_earned=reward_result["badges_earned"],
    )
