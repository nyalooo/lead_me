# Architecture

## Overview

LeadMe uses a client-server architecture with a clear separation between the web frontend and the backend API. The backend is the single source of truth, and both the web app and future mobile app consume the same API.

```
┌──────────────┐    ┌──────────────────────────┐    ┌────────────┐
│   Web App    │───▶│      Backend API          │───▶│ PostgreSQL │
│  (Next.js)   │    │      (FastAPI)            │    │ + Redis    │
└──────────────┘    │                          │    └────────────┘
                    │  ┌─────────────────────┐ │
┌──────────────┐    │  │ Route Engine         │ │    ┌────────────┐
│  Mobile App  │───▶│  │ (weighted balancing) │ │───▶│ Google     │
│  (Phase 2)   │    │  └─────────────────────┘ │    │ Routes API │
└──────────────┘    │  ┌─────────────────────┐ │    └────────────┘
                    │  │ Scheduler Service    │ │
                    │  │ (cron + pre-assign)  │ │    ┌────────────┐
                    │  └─────────────────────┘ │───▶│ Mapbox     │
                    │  ┌─────────────────────┐ │    └────────────┘
                    │  │ Reward Service       │ │
                    │  │ (coins + XRP track)  │ │    ┌────────────┐
                    │  └─────────────────────┘ │───▶│ XRPL       │
                    └──────────────────────────┘    └────────────┘
```

## Backend Services

The backend follows a **domain-module pattern** where each service is self-contained:

### 1. Route Engine (`services/route_engine/`)

Responsible for calculating routes and assigning them to commuters.

**Key responsibilities:**
- Fetch multiple viable routes between origin and destination (Google Routes API)
- Calculate weighted load scores per route
- Assign optimal route to each commuter based on current/scheduled/historical load
- Track active commuters per route in real-time

**Weighted Load Score Formula:**
```
Route Load Score = (active_commuters × 1.0
                  + scheduled_upcoming × 0.7
                  + historical_avg × 0.3)
                  / route_capacity
```

Routes with lower load scores receive more assignments. Routes approaching capacity stop receiving new assignments.

### 2. Scheduler Service (`services/scheduler/`)

Manages pre-planned commutes and advance route assignment.

**Key responsibilities:**
- Store recurring schedules (e.g., Mon-Fri, 8:30am, Home→Office)
- Store one-time scheduled trips
- Run pre-assignment jobs (night before / early morning)
- Support flexible departure windows
- Feed scheduled commuter counts into route engine

**Schedule types:**
- `recurring` — Daily commute pattern, editable
- `one_time` — Ad-hoc future trip
- `flexible` — Departure window (e.g., 8-9am), system optimizes departure time

### 3. Reward Service (`services/rewards/`)

Handles gamification: coins, streaks, badges, tiers, and XRP tracking.

**Key responsibilities:**
- Award Route Coins on route completion (scaled by detour sacrifice)
- Track and apply streak multipliers (3-day: 1.5x, 7-day: 2x, 30-day: 3x)
- Award badges based on achievement criteria
- Manage user tier progression (Rookie → Regular → Pro → Legend)
- Track XRP balance (conversion from Route Coins)
- Area-wise leaderboard calculations

**Penalty model (gentle):**
- Streak reset on missed route (no coin deduction)
- Lower priority for high-reward routes after repeated non-compliance
- Never deduct earned coins or XRP

## Data Flow

### Real-time Route Request
```
User requests route
  → Route Engine fetches alternatives from Google Routes API
  → Engine queries current load per route (active + scheduled commuters)
  → Engine calculates weighted load scores
  → Engine assigns lowest-load viable route
  → User receives assigned route + estimated reward
```

### Scheduled Commute
```
User creates schedule (recurring or one-time)
  → Scheduler stores in database
  → Pre-assignment job runs (e.g., 6am daily)
  → Job queries all departures in upcoming window
  → Route Engine batch-assigns routes
  → Users receive route notification before departure
```

### Route Completion
```
User departs, GPS tracking begins
  → Periodic location updates sent to backend
  → Backend compares actual path vs assigned route
  → On arrival: compliance score calculated
  → Reward Service awards coins (if compliant)
  → Streak updated, badges checked, leaderboard recalculated
```

## Database Schema (High-Level)

- **users** — Profile, phone, tier, XRP wallet address
- **routes** — Cached route geometries, capacity estimates
- **route_assignments** — User ↔ route mapping, compliance status
- **schedules** — Recurring and one-time commute schedules
- **route_coins** — Transaction ledger (earned, converted)
- **streaks** — Current streak per user
- **badges** — Badge definitions + user badge awards
- **leaderboards** — Materialized area-wise rankings

## API Design

All endpoints are versioned under `/api/v1/`. The API follows REST conventions:

- `POST /api/v1/routes/assign` — Request a route assignment
- `GET /api/v1/routes/{id}/status` — Get route load status
- `POST /api/v1/routes/{id}/track` — Submit GPS location update
- `POST /api/v1/routes/{id}/complete` — Mark route as completed
- `GET /api/v1/schedules` — List user's schedules
- `POST /api/v1/schedules` — Create a schedule
- `GET /api/v1/rewards/balance` — Get coin + XRP balance
- `GET /api/v1/rewards/streaks` — Get current streak info
- `GET /api/v1/rewards/badges` — Get badges
- `GET /api/v1/rewards/leaderboard` — Area leaderboard

## External Services

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| Google Routes API | Traffic-aware routing for Mumbai | $200/mo credit |
| Mapbox | Map display + traffic layer | 50K loads + 100K directions/mo |
| XRPL (testnet) | XRP micro-payment tracking | Free (testnet) |

## Security Considerations

- Phone OTP authentication (no passwords)
- JWT tokens for API auth
- Rate limiting on all public endpoints
- GPS data is used only for route compliance, not stored long-term
- XRP wallet addresses are user-provided, not custodial (Phase 2)
