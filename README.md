# LeadMe

**Traffic-aware route assignment with incentives for Mumbai commuters.**

LeadMe doesn't just suggest the shortest route — it actively distributes traffic across routes by assigning different drivers different paths, then rewards compliance with XRP cryptocurrency.

## Problem

Navigation apps like Google Maps and Waze suggest the same "best" route to everyone, causing new congestion on that route (herding problem). LeadMe solves this by treating route assignment as a load-balancing problem across the road network.

## How It Works

1. **Route Assignment** — System knows how many commuters are heading A→B and distributes them across multiple viable routes to minimize overall congestion
2. **Schedule Upfront** — Users pre-schedule commutes; system assigns routes in advance using weighted average of commuters per route
3. **GPS Tracking** — Verifies if the assigned route was followed
4. **XRP Rewards** — Compliant commuters earn Route Coins convertible to XRP; non-compliance gently reduces future earning potential

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Frontend | Next.js (App Router) + TypeScript |
| Backend API | FastAPI (Python) |
| Database | PostgreSQL + Redis |
| Maps | Mapbox (display) + Google Routes API (traffic data) |
| Crypto | XRPL.js (XRP Ledger) |
| Auth | Phone OTP (Mumbai-first) |

## Project Structure

```
lead_me/
├── backend/              # FastAPI backend API
│   ├── app/
│   │   ├── main.py       # FastAPI entrypoint
│   │   ├── config.py     # App settings (pydantic-settings)
│   │   ├── services/     # Domain services
│   │   │   ├── route_engine/   # Route calculation & assignment
│   │   │   ├── scheduler/      # Pre-planned commute scheduling
│   │   │   └── rewards/        # Coins, streaks, badges, XRP
│   │   ├── core/         # Database, security, middleware
│   │   └── common/       # Shared utilities
│   ├── alembic/          # Database migrations
│   └── tests/
├── web/                  # Next.js web application
│   ├── app/              # App Router pages
│   ├── components/       # React components
│   ├── lib/              # Utilities and API client
│   └── public/           # Static assets
├── docs/                 # Project documentation
└── contracts/            # Shared OpenAPI spec
```

## MVP Scope (Phase 1) — Mumbai

- Web app with map view and route display
- Route assignment engine with weighted load balancing
- Schedule upfront (recurring + one-time)
- Commuter load per route (busy/moderate/clear)
- GPS tracking + route compliance verification
- Route Coins + streaks + basic badges
- Area leaderboard
- XRP balance tracking (cashout in Phase 2)

## Gamification

- **Route Coins** — Earned per completed route, scales with detour sacrifice
- **Streaks** — 3/7/30-day multipliers (1.5x/2x/3x)
- **Badges** — Traffic Hero, Early Bird, Mumbai Local, Perfect Week
- **Tiers** — Rookie → Regular → Pro → Legend (better routes + XRP rates)
- **Leaderboards** — Area-wise weekly rankings
- **Penalties** — Gentle: streak reset, lower priority (never deduct earned XRP)

## Getting Started

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Web

```bash
cd web
npm install
npm run dev
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:6800/docs
- ReDoc: http://localhost:6800/redoc
- OpenAPI spec: http://localhost:6800/openapi.json

## License

MIT
