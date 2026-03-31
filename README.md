# LeadMe

**Traffic-aware route assignment with crypto rewards for Mumbai commuters.**

LeadMe doesn't just suggest the shortest route — it actively distributes traffic across routes by assigning different drivers different paths, then rewards compliance with cryptocurrency.

## Problem

Navigation apps like Google Maps and Waze suggest the same "best" route to everyone, causing new congestion on that route (herding problem). LeadMe solves this by treating route assignment as a load-balancing problem across the road network.

## How It Works

1. **Route Assignment** — System knows how many commuters are heading A→B and distributes them across multiple viable routes to minimize overall congestion
2. **Schedule Upfront** — Users pre-schedule commutes; system assigns routes in advance using weighted average of commuters per route
3. **GPS Tracking** — Verifies if the assigned route was followed (background tracking on mobile)
4. **Crypto Rewards** — Compliant commuters earn Route Coins convertible to XRP (SOL, ETH coming soon)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web Frontend | Next.js (App Router) + TypeScript |
| Mobile App | React Native (Expo) + TypeScript |
| Backend API | FastAPI (Python) |
| Database | PostgreSQL + Redis |
| Maps | Mapbox / Leaflet (display) + Google/Mapbox/HERE (routing) |
| Crypto | XRPL (XRP), Solana (coming soon), Ethereum (coming soon) |
| Auth | Phone OTP (Mumbai-first) |

## Project Structure

```
lead_me/
├── backend/              # FastAPI backend API
│   ├── app/
│   │   ├── main.py       # FastAPI entrypoint
│   │   ├── config.py     # App settings (pydantic-settings)
│   │   ├── providers/    # External service adapters
│   │   │   ├── routing/  # Google, Mapbox, HERE, Mock
│   │   │   ├── sms/      # Twilio, MSG91, Console
│   │   │   └── crypto/   # XRP, SOL (soon), ETH (soon), Mock
│   │   ├── services/     # Domain services
│   │   │   ├── route_engine/   # Route calculation & assignment
│   │   │   ├── scheduler/      # Pre-planned commute scheduling
│   │   │   ├── rewards/        # Coins, streaks, badges
│   │   │   └── cashout/        # Coin → crypto conversion
│   │   ├── core/         # Database, security, seeds
│   │   └── common/       # Shared utilities
│   ├── alembic/          # Database migrations
│   └── tests/
├── web/                  # Next.js web application
│   ├── src/app/          # App Router pages
│   ├── src/components/   # React components
│   ├── src/lib/          # Utilities, API client, maps
│   └── src/hooks/        # React hooks (tracking)
├── mobile/               # React Native (Expo) mobile app
│   ├── src/screens/      # App screens
│   ├── src/hooks/        # Background GPS tracking
│   ├── src/lib/          # API client, auth, theme
│   └── src/navigation/   # Stack + Tab navigation
├── docs/                 # Project documentation
└── contracts/            # Shared types
```

## Features

### Phase 1 (Complete)
- Web app with map view and route display
- Route assignment engine with weighted load balancing
- Schedule upfront (recurring + one-time)
- GPS tracking + route compliance verification
- Route Coins + streaks + badges + tiers
- Area leaderboard
- Provider adapters for routing, maps, SMS

### Phase 2 (Current)
- **Multi-crypto cashout** — XRP active, SOL/ETH architecture ready
- **React Native mobile app** — Background GPS tracking, all features
- **Cashout service** — Wallet linking, estimates, tier bonuses, auto-refund

### Phase 3 (Planned)
- NFT badges
- Challenges & events
- Social features (referrals, WhatsApp sharing)
- City-wide analytics dashboard
- Multi-city expansion

## Gamification

- **Route Coins** — Earned per completed route, scales with detour sacrifice
- **Streaks** — 3/7/14/30-day multipliers (1.5x/2x/2.5x/3x)
- **Badges** — 12 badges (Traffic Hero, Early Bird, Mumbai Local, etc.)
- **Tiers** — Rookie → Regular → Pro → Legend (better cashout rates)
- **Leaderboards** — Area-wise weekly/monthly rankings
- **Penalties** — Gentle: streak reset, lower priority (never deduct earned crypto)

## Getting Started

### Docker (Recommended)

```bash
docker compose up
```

Services:
- Backend API: http://localhost:6800
- Web App: http://localhost:6300
- PostgreSQL: localhost:6432
- Redis: localhost:6379

For mobile development:
```bash
docker compose --profile mobile up
```

### Manual

```bash
# Backend
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# Web
cd web
npm install && npm run dev

# Mobile
cd mobile
npm install && npx expo start
```

## API Documentation

Once the backend is running:
- Swagger UI: http://localhost:6800/docs
- ReDoc: http://localhost:6800/redoc
- OpenAPI spec: http://localhost:6800/openapi.json

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design, data flow, DB schema
- [Crypto Integration](docs/CRYPTO.md) — Multi-crypto adapter, cashout flow, wallet management
- [Gamification](docs/GAMIFICATION.md) — Rewards, streaks, badges, tiers
- [API Reference](docs/API.md) — Full endpoint documentation
- [Providers](docs/PROVIDERS.md) — Adapter pattern for external services

## License

MIT
