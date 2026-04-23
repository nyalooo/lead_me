# Database Schema

## Overview

LeadMe uses **PostgreSQL 16** with **async SQLAlchemy 2.0** (via `asyncpg`). Migrations are managed with **Alembic** (async mode). All models use UUID primary keys and timezone-aware timestamps.

## Entity Relationship

```
users
  │
  ├── 1:N → route_assignments       (user takes assigned routes)
  ├── 1:N → schedules               (user's pre-planned commutes)
  ├── 1:1 → streaks                 (one streak tracker per user)
  ├── 1:N → coin_transactions       (route coins ledger)
  ├── 1:N → user_badges             (earned achievements)
  ├── 1:N → wallet_links            (linked crypto wallets)
  ├── 1:N → cashout_requests        (coin → crypto conversions)
  └── 1:N → challenge_participants  (joined challenges)

routes
  └── 1:N → route_assignments       (route can be assigned to many users)

route_assignments
  └── 1:N → location_updates        (GPS points during tracking)
  └── 1:N → coin_transactions       (reward linked to assignment)

badges (reference table)
  └── 1:N → user_badges             (many users can earn each badge)

challenges
  └── 1:N → challenge_participants   (users enrolled in challenge)
```

## Tables

### `users`

Core user identity and gamification stats.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK, default uuid4 | User ID |
| `phone` | VARCHAR(15) | UNIQUE, INDEX | Phone number (login key) |
| `display_name` | VARCHAR(100) | default "Commuter" | Display name |
| `area` | VARCHAR(100) | nullable | Mumbai area (Andheri, Bandra, etc.) |
| `xrp_wallet_address` | VARCHAR(100) | nullable | Legacy XRP wallet field |
| `tier` | VARCHAR(20) | default "rookie" | rookie/regular/pro/legend |
| `total_routes` | INT | default 0 | Lifetime completed routes |
| `total_coins` | INT | default 0 | Current coin balance |
| `compliance_rate` | FLOAT | default 0.0 | Recent compliance ratio (0.0–1.0) |
| `created_at` | TIMESTAMPTZ | auto | Account creation |
| `updated_at` | TIMESTAMPTZ | auto, on update | Last profile update |

### `routes`

Cached route geometries between origin/destination pairs.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | Route ID |
| `origin_lat` | FLOAT | | Origin latitude |
| `origin_lng` | FLOAT | | Origin longitude |
| `destination_lat` | FLOAT | | Destination latitude |
| `destination_lng` | FLOAT | | Destination longitude |
| `polyline` | TEXT | nullable | Encoded polyline geometry |
| `distance_km` | FLOAT | | Route distance in km |
| `base_duration_min` | FLOAT | | Estimated travel time |
| `capacity_estimate` | INT | default 1000 | Max commuters this route can handle |
| `active_commuters` | INT | default 0 | Current active users on this route |
| `created_at` | TIMESTAMPTZ | auto | When route was first cached |

### `route_assignments`

Links a user to a route for a specific trip.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | Assignment ID |
| `user_id` | UUID | FK → users.id, INDEX | Assigned user |
| `route_id` | UUID | FK → routes.id | Assigned route |
| `schedule_id` | UUID | FK → schedules.id, nullable | Linked schedule (if pre-assigned) |
| `origin_lat/lng` | FLOAT | | Trip origin |
| `destination_lat/lng` | FLOAT | | Trip destination |
| `detour_percent` | FLOAT | default 0.0 | How much longer than shortest route (%) |
| `status` | VARCHAR(20) | default "assigned" | assigned/active/completed/cancelled |
| `compliant` | BOOLEAN | nullable | Did user follow the route? |
| `compliance_score` | FLOAT | nullable | 0.0–1.0 compliance metric |
| `coins_earned` | INT | nullable | Coins awarded for this trip |
| `assigned_at` | TIMESTAMPTZ | auto | When route was assigned |
| `started_at` | TIMESTAMPTZ | nullable | When GPS tracking started |
| `completed_at` | TIMESTAMPTZ | nullable | When route was marked complete |

### `location_updates`

GPS breadcrumbs sent during active route tracking.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | Update ID |
| `assignment_id` | UUID | FK → route_assignments.id, INDEX | Which trip |
| `lat` | FLOAT | | GPS latitude |
| `lng` | FLOAT | | GPS longitude |
| `accuracy_m` | FLOAT | default 0.0 | GPS accuracy in meters |
| `timestamp` | TIMESTAMPTZ | | When the reading was taken |

### `schedules`

Pre-planned commute schedules for advance route assignment.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | Schedule ID |
| `user_id` | UUID | FK → users.id, INDEX | Schedule owner |
| `type` | VARCHAR(20) | | recurring/one_time/flexible |
| `origin_lat/lng` | FLOAT | | Origin coordinates |
| `origin_label` | VARCHAR(100) | nullable | "Home", "Office", etc. |
| `destination_lat/lng` | FLOAT | | Destination coordinates |
| `destination_label` | VARCHAR(100) | nullable | Friendly name |
| `days` | TEXT[] | nullable | Array: ["mon","tue",...] (recurring) |
| `departure_time` | TIME | nullable | Fixed departure time |
| `scheduled_date` | TIMESTAMPTZ | nullable | Specific date (one_time) |
| `departure_earliest` | TIME | nullable | Window start (flexible) |
| `departure_latest` | TIME | nullable | Window end (flexible) |
| `active` | BOOLEAN | default true | Is schedule active? |
| `created_at` | TIMESTAMPTZ | auto | |
| `updated_at` | TIMESTAMPTZ | auto, on update | |

### `coin_transactions`

Immutable ledger of all Route Coin movements.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | Transaction ID |
| `user_id` | UUID | FK → users.id, INDEX | Account holder |
| `type` | VARCHAR(30) | | route_completion/badge_bonus/streak_bonus/cashout/cashout_refund |
| `coins` | INT | | Amount (+earn, -spend) |
| `description` | VARCHAR(200) | | Human-readable description |
| `assignment_id` | UUID | FK → route_assignments.id, nullable | Related trip |
| `created_at` | TIMESTAMPTZ | auto | Transaction time |

### `streaks`

One row per user tracking consecutive-day compliance.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, UNIQUE | One streak per user |
| `current_streak` | INT | default 0 | Active streak days |
| `longest_streak` | INT | default 0 | All-time best |
| `last_completed_date` | DATE | nullable | Last compliant completion date |
| `streak_freezes_remaining` | INT | default 0 | Miss-a-day passes left |
| `updated_at` | TIMESTAMPTZ | auto, on update | |

### `badges`

Badge definitions (seeded on startup, 12 badges).

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | VARCHAR(50) | PK | Badge slug (e.g., "traffic_hero") |
| `name` | VARCHAR(100) | | Display name |
| `description` | VARCHAR(300) | | Description text |
| `coins_bonus` | INT | default 0 | Bonus coins when earned |
| `criteria_type` | VARCHAR(50) | | routes_count/streak_days/area_count/etc. |
| `criteria_value` | INT | | Threshold to earn (e.g., 100 routes) |

### `user_badges`

Junction table: which users earned which badges.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, INDEX | |
| `badge_id` | VARCHAR(50) | FK → badges.id | |
| `pinned` | BOOLEAN | default false | Shown on leaderboard |
| `earned_at` | TIMESTAMPTZ | auto | When earned |

### `wallet_links`

User-linked crypto wallet addresses (non-custodial).

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, INDEX | |
| `currency` | VARCHAR(10) | | XRP/SOL/ETH |
| `address` | VARCHAR(200) | | Wallet address |
| `label` | VARCHAR(100) | default "" | User-friendly name |
| `verified` | BOOLEAN | default false | Address validated |
| `is_primary` | BOOLEAN | default true | Primary wallet for this currency |
| `created_at` | TIMESTAMPTZ | auto | |
| `updated_at` | TIMESTAMPTZ | auto, on update | |

### `cashout_requests`

Coin-to-crypto conversion requests and their status.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `user_id` | UUID | FK → users.id, INDEX | |
| `coins_amount` | INT | | Route Coins spent |
| `crypto_amount` | FLOAT | | Crypto received |
| `currency` | VARCHAR(10) | | XRP/SOL/ETH |
| `tier_bonus` | FLOAT | default 1.0 | Tier multiplier applied |
| `wallet_address` | VARCHAR(200) | | Destination wallet |
| `status` | VARCHAR(20) | default "pending" | pending/processing/completed/failed |
| `tx_hash` | VARCHAR(200) | nullable | Blockchain transaction hash |
| `explorer_url` | TEXT | nullable | Block explorer link |
| `failure_reason` | VARCHAR(500) | nullable | Error description |
| `created_at` | TIMESTAMPTZ | auto | Request time |
| `completed_at` | TIMESTAMPTZ | nullable | Completion time |

### `challenges`

Time-bound challenges that users can join for bonus rewards.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | Challenge ID |
| `title` | VARCHAR(200) | | Challenge title |
| `description` | TEXT | | Full description |
| `type` | VARCHAR(30) | | weekly/monthly/event/flash |
| `category` | VARCHAR(30) | default "general" | general/area/peak/monsoon/festival |
| `goal_type` | VARCHAR(30) | | routes_count/distance_km/peak_routes/area_routes/streak_days |
| `goal_value` | INT | | Target value to complete |
| `goal_area` | VARCHAR(100) | nullable | Specific area for area challenges |
| `reward_coins` | INT | default 0 | Coin reward |
| `reward_xrp` | FLOAT | default 0.0 | XRP reward |
| `reward_badge_id` | VARCHAR(50) | nullable | Badge unlocked on completion |
| `starts_at` | TIMESTAMPTZ | | Challenge start time |
| `ends_at` | TIMESTAMPTZ | | Challenge end time |
| `max_participants` | INT | nullable | null = unlimited |
| `active` | BOOLEAN | default true | Is challenge visible? |
| `sponsor_id` | UUID | nullable | Linked sponsor pool (Phase 3) |
| `created_at` | TIMESTAMPTZ | auto | |

### `challenge_participants`

Tracks a user's enrollment and progress in a challenge.

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | UUID | PK | |
| `challenge_id` | UUID | FK → challenges.id, INDEX | |
| `user_id` | UUID | FK → users.id, INDEX | |
| `progress` | INT | default 0 | Current progress toward goal |
| `completed` | BOOLEAN | default false | Hit goal_value? |
| `reward_claimed` | BOOLEAN | default false | Claimed the reward? |
| `joined_at` | TIMESTAMPTZ | auto | When user joined |
| `completed_at` | TIMESTAMPTZ | nullable | When goal was reached |

## Migrations

LeadMe uses **Alembic** with async SQLAlchemy for database migrations.

### Configuration

- Config: `backend/alembic.ini`
- Env: `backend/alembic/env.py` (imports all models for autogenerate)
- Migrations: `backend/alembic/versions/`

### Commands

```bash
cd backend

# Generate a new migration from model changes
alembic revision --autogenerate -m "add cashout tables"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current migration state
alembic current

# View migration history
alembic history
```

### Dev Mode (Auto-Create)

In development, `main.py`'s lifespan event auto-creates tables:

```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

This is convenient for dev but **use Alembic migrations in production**.

## Seeding

Badge definitions are seeded on app startup in `core/seed.py`. The seed is idempotent — it checks for existing badges before inserting.

12 badges are seeded:
- `first_route`, `regular_commuter`, `century_club`, `five_hundred_club`
- `streak_3`, `streak_7`, `streak_14`, `streak_30`
- `early_bird`, `night_owl`, `peak_warrior`, `traffic_hero`
