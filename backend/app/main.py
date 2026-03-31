"""LeadMe API — Traffic-aware route assignment with XRP rewards."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import engine, Base
from app.services.route_engine.router import router as route_router
from app.services.scheduler.router import router as schedule_router
from app.services.rewards.router import router as reward_router
from app.services.auth.router import router as auth_router
from app.services.users.router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev only; use alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
app.include_router(user_router, prefix=f"{settings.api_v1_prefix}/users", tags=["users"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "leadme"}
