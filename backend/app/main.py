"""LeadMe API — Traffic-aware route assignment with XRP rewards."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import engine, Base
from app.services.route_engine.router import router as route_router
from app.services.scheduler.router import router as schedule_router
from app.services.rewards.router import router as reward_router
from app.services.cashout.router import router as cashout_router
from app.services.auth.router import router as auth_router
from app.services.users.router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev only; use alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed initial data
    from app.core.database import async_session
    from app.core.seed import seed_all
    async with async_session() as session:
        result = await seed_all(session)
        await session.commit()
        if result.get("badges_inserted"):
            import logging
            logging.getLogger(__name__).info(f"Seeded {result['badges_inserted']} badges")
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Traffic-aware route assignment with XRP rewards for Mumbai commuters.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:6300", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount service routers
app.include_router(auth_router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"])
app.include_router(route_router, prefix=f"{settings.api_v1_prefix}/routes", tags=["routes"])
app.include_router(schedule_router, prefix=f"{settings.api_v1_prefix}/schedules", tags=["schedules"])
app.include_router(reward_router, prefix=f"{settings.api_v1_prefix}/rewards", tags=["rewards"])
app.include_router(cashout_router, prefix=f"{settings.api_v1_prefix}/cashout", tags=["cashout"])
app.include_router(user_router, prefix=f"{settings.api_v1_prefix}/users", tags=["users"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "leadme"}


@app.get("/health/providers")
async def provider_health():
    """Check which providers are active and their health status."""
    from app.providers.routing.registry import get_routing_provider
    from app.providers.crypto.registry import get_crypto_provider

    routing = get_routing_provider()
    crypto = get_crypto_provider()

    routing_healthy = await routing.health_check()
    crypto_healthy = await crypto.health_check()

    return {
        "routing_provider": routing.name,
        "routing_healthy": routing_healthy,
        "crypto_provider": crypto.name,
        "crypto_currency": crypto.currency_code,
        "crypto_network": crypto.network_name,
        "crypto_healthy": crypto_healthy,
    }
