# Development Guide

## Prerequisites

- **Python 3.11+** (backend)
- **Node.js 22+** (web + mobile)
- **PostgreSQL 16** (or use Docker)
- **Redis 7** (or use Docker)
- **Docker + Docker Compose** (recommended for full stack)

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/nyalooo/lead_me.git
cd lead_me
docker compose up
```

This starts:
| Service | URL | Port |
|---------|-----|------|
| Backend API | http://localhost:6800 | 6800 |
| Web App | http://localhost:6300 | 6300 |
| PostgreSQL | localhost:6432 | 6432 |
| Redis | localhost:6379 | 6379 |

For mobile development, add the `mobile` profile:
```bash
docker compose --profile mobile up
```

### Manual Setup

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env       # edit with your settings
uvicorn app.main:app --reload --port 8000
```

#### Web

```bash
cd web
npm install
npm run dev
```

#### Mobile

```bash
cd mobile
npm install
npx expo start
```

## Environment Variables

### Backend (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection string |
| `JWT_SECRET_KEY` | Yes | `change-me-in-production` | JWT signing secret |
| `DEBUG` | No | `false` | Enable debug mode |
| `ROUTING_PROVIDER` | No | (auto-detect) | `google`, `mapbox`, `here`, `mock` |
| `GOOGLE_ROUTES_API_KEY` | No | — | Google Routes API key |
| `MAPBOX_ACCESS_TOKEN` | No | — | Mapbox API token |
| `HERE_API_KEY` | No | — | HERE Maps API key |
| `SMS_PROVIDER` | No | (auto-detect) | `twilio`, `msg91`, `console` |
| `TWILIO_ACCOUNT_SID` | No | — | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | No | — | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | No | — | Twilio sender number |
| `MSG91_AUTH_KEY` | No | — | MSG91 auth key |
| `CRYPTO_PROVIDER` | No | (auto-detect) | `xrp`, `mock` |
| `PLATFORM_WALLET_ADDRESS` | No | — | Platform crypto wallet address |
| `PLATFORM_WALLET_SEED` | No | — | Platform wallet seed (KEEP SECRET) |
| `XRPL_NETWORK_URL` | No | testnet | XRPL WebSocket URL |
| `XRPL_WALLET_SEED` | No | — | XRP wallet seed |

### Web (`.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:6800/api/v1` | Backend API URL |
| `NEXT_PUBLIC_MAP_PROVIDER` | (auto-detect) | `mapbox` or `leaflet` |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | — | Mapbox GL JS access token |

## Project Layout

```
lead_me/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # App entrypoint, lifespan, CORS, routers
│   │   ├── config.py           # Pydantic Settings (env-based config)
│   │   ├── core/               # Cross-cutting: database, security, seeds
│   │   ├── common/             # Shared utilities, exception classes
│   │   ├── providers/          # External service adapters
│   │   │   ├── routing/        # Google, Mapbox, HERE, Mock
│   │   │   ├── sms/            # Twilio, MSG91, Console
│   │   │   └── crypto/         # XRP, SOL (stub), ETH (stub), Mock
│   │   └── services/           # Domain modules
│   │       ├── auth/           # Phone OTP authentication
│   │       ├── users/          # User profile and stats
│   │       ├── route_engine/   # Route assignment and tracking
│   │       ├── scheduler/      # Pre-planned commute scheduling
│   │       ├── rewards/        # Coins, streaks, badges, tiers
│   │       └── cashout/        # Coin → crypto conversion
│   ├── alembic/                # Database migrations
│   ├── tests/                  # pytest test suite
│   ├── pyproject.toml          # Python dependencies
│   └── Dockerfile
├── web/                        # Next.js web frontend
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   │   ├── (auth)/         # Login page group
│   │   │   └── (dashboard)/    # Dashboard page group
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks (route tracking)
│   │   └── lib/                # API client, auth, maps, geolocation
│   ├── package.json
│   └── Dockerfile
├── mobile/                     # React Native (Expo) mobile app
│   ├── src/
│   │   ├── screens/            # App screens (6 total)
│   │   ├── hooks/              # Background GPS tracking
│   │   ├── lib/                # API client, auth, theme
│   │   └── navigation/         # Stack + Tab navigation
│   ├── app.json                # Expo config
│   └── Dockerfile
├── docs/                       # Project documentation
├── docker-compose.yml          # Full-stack local dev
└── README.md
```

## Code Conventions

### Backend (Python)

- **Formatter**: Ruff (line-length 88, configured in `pyproject.toml`)
- **Style**: PEP 8 with type hints throughout
- **Async**: All database operations use async SQLAlchemy
- **Domain modules**: Each service has `models.py`, `service.py`, `schemas.py`, `router.py`
- **Provider pattern**: Abstract base → concrete implementations → registry with auto-detect
- **Config**: All settings via `pydantic_settings.BaseSettings` (env vars or `.env` file)

### Frontend (TypeScript)

- **Web**: Next.js App Router, Tailwind CSS, server/client components
- **Mobile**: React Native with Expo, StyleSheet API
- **Shared**: Same API client structure, same endpoint types
- **State**: React hooks (no global state library for MVP)
- **Maps**: Provider adapter pattern (Mapbox/Leaflet on web, react-native-maps on mobile)

## Testing

### Backend Tests

```bash
cd backend
pip install -e ".[dev]"
pytest                    # run all tests
pytest tests/ -v          # verbose output
pytest tests/test_rewards.py -v  # specific file
```

Test files:
- `tests/test_route_engine.py` — Route assignment, load scoring, compliance
- `tests/test_rewards.py` — Coin calculation, streak logic, badge criteria, tier updates

Tests use `pytest-asyncio` for async test functions and don't require a running database (unit tests with mocks).

### Web Build Check

```bash
cd web
npm run build   # TypeScript compilation + Next.js build
npm run lint    # ESLint
```

### Mobile Type Check

```bash
cd mobile
npx tsc --noEmit   # TypeScript type checking
```

## Adding a New Service

To add a new domain service (e.g., `notifications`):

1. Create directory: `backend/app/services/notifications/`
2. Add files following the pattern:
   - `__init__.py` (empty)
   - `models.py` — SQLAlchemy models
   - `schemas.py` — Pydantic request/response schemas
   - `service.py` — Business logic functions
   - `router.py` — FastAPI router with endpoints
3. Mount router in `main.py`:
   ```python
   from app.services.notifications.router import router as notification_router
   app.include_router(notification_router, prefix=f"{settings.api_v1_prefix}/notifications", tags=["notifications"])
   ```
4. Import models in `alembic/env.py` for migration generation
5. Run `alembic revision --autogenerate -m "add notifications"` for migration

## Adding a New Provider

To add a new external service adapter (e.g., a new SMS provider):

1. Create file: `backend/app/providers/sms/your_provider.py`
2. Subclass the abstract base (e.g., `SMSProvider`)
3. Implement all abstract methods
4. Add config fields to `config.py`
5. Register in the category's `registry.py`
6. Update `docs/PROVIDERS.md`

See [PROVIDERS.md](PROVIDERS.md) for detailed examples.

## Docker Development

### Hot Reload

The Docker setup mounts source code as volumes for hot reload:
- Backend: `./backend/app` → `/app/app` (uvicorn `--reload`)
- Web: full `./web` context (Next.js dev server)

### Rebuild After Dependency Changes

```bash
docker compose build backend  # after pyproject.toml changes
docker compose build web      # after package.json changes
docker compose up
```

### Database Access

```bash
# Connect to PostgreSQL
docker compose exec db psql -U postgres -d leadme

# View tables
\dt

# Redis CLI
docker compose exec redis redis-cli
```

## Port Assignments

All external ports are in the 6000 range:

| Service | Port | Internal |
|---------|------|----------|
| Web App | 6300 | 3000 |
| Redis | 6379 | 6379 |
| PostgreSQL | 6432 | 5432 |
| Backend API | 6800 | 8000 |
| Mobile (Expo) | 6081 | 8081 |
