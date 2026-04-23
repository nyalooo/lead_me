# API Reference

Base URL: `http://localhost:6800/api/v1`

## Authentication

All endpoints (except auth) require a Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Auth Endpoints

#### `POST /api/v1/auth/request-otp`
Request an OTP for phone number login.

**Request:**
```json
{
  "phone": "+919876543210"
}
```

**Response:** `200 OK`
```json
{
  "message": "OTP sent",
  "expires_in": 300
}
```

#### `POST /api/v1/auth/verify-otp`
Verify OTP and receive JWT token.

**Request:**
```json
{
  "phone": "+919876543210",
  "otp": "123456"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "phone": "+919876543210",
    "display_name": "Commuter",
    "tier": "rookie"
  }
}
```

---

## Routes

#### `POST /api/v1/routes/assign`
Request a route assignment from origin to destination.

**Request:**
```json
{
  "origin": { "lat": 19.1136, "lng": 72.8697 },
  "destination": { "lat": 19.0760, "lng": 72.8777 },
  "departure_time": "2026-04-01T08:30:00+05:30"
}
```

**Response:** `200 OK`
```json
{
  "assignment_id": "uuid",
  "assigned_route": {
    "id": "uuid",
    "polyline": "encoded_polyline_string",
    "distance_km": 12.3,
    "estimated_duration_min": 35,
    "load_status": "moderate",
    "detour_percent": 8.5
  },
  "alternative_routes": [
    {
      "id": "uuid",
      "distance_km": 11.1,
      "estimated_duration_min": 42,
      "load_status": "busy"
    }
  ],
  "estimated_reward": {
    "base_coins": 10,
    "detour_multiplier": 1.4,
    "streak_multiplier": 2.0,
    "peak_multiplier": 2.0,
    "total_coins": 56
  }
}
```

#### `GET /api/v1/routes/{route_id}/status`
Get current load status for a route.

**Response:** `200 OK`
```json
{
  "route_id": "uuid",
  "load_score": 0.72,
  "load_status": "busy",
  "active_commuters": 2400,
  "scheduled_commuters": 350,
  "capacity_estimate": 3500
}
```

#### `POST /api/v1/routes/{assignment_id}/track`
Submit GPS location update during active route.

**Request:**
```json
{
  "lat": 19.1000,
  "lng": 72.8750,
  "timestamp": "2026-04-01T08:45:00+05:30",
  "accuracy_m": 15.0
}
```

**Response:** `200 OK`
```json
{
  "on_route": true,
  "progress_percent": 45.2
}
```

#### `POST /api/v1/routes/{assignment_id}/complete`
Mark a route as completed. Backend verifies compliance from GPS data.

**Response:** `200 OK`
```json
{
  "assignment_id": "uuid",
  "compliant": true,
  "compliance_score": 0.94,
  "coins_earned": 56,
  "streak_day": 8,
  "badges_earned": ["traffic_hero"]
}
```

---

## Schedules

#### `GET /api/v1/schedules`
List current user's schedules.

**Query params:** `?type=recurring|one_time|flexible&active=true`

**Response:** `200 OK`
```json
{
  "schedules": [
    {
      "id": "uuid",
      "type": "recurring",
      "origin": { "lat": 19.1136, "lng": 72.8697, "label": "Home" },
      "destination": { "lat": 19.0760, "lng": 72.8777, "label": "Office" },
      "days": ["mon", "tue", "wed", "thu", "fri"],
      "departure_time": "08:30",
      "active": true,
      "next_assignment": {
        "date": "2026-04-01",
        "route_id": "uuid",
        "assigned_at": "2026-03-31T22:00:00+05:30"
      }
    }
  ]
}
```

#### `POST /api/v1/schedules`
Create a new schedule.

**Request (recurring):**
```json
{
  "type": "recurring",
  "origin": { "lat": 19.1136, "lng": 72.8697, "label": "Home" },
  "destination": { "lat": 19.0760, "lng": 72.8777, "label": "Office" },
  "days": ["mon", "tue", "wed", "thu", "fri"],
  "departure_time": "08:30"
}
```

**Request (flexible):**
```json
{
  "type": "flexible",
  "origin": { "lat": 19.1136, "lng": 72.8697, "label": "Home" },
  "destination": { "lat": 19.0760, "lng": 72.8777, "label": "Office" },
  "date": "2026-04-01",
  "departure_window": { "earliest": "08:00", "latest": "09:00" }
}
```

**Response:** `201 Created`

#### `PUT /api/v1/schedules/{id}`
Update an existing schedule.

#### `DELETE /api/v1/schedules/{id}`
Delete a schedule.

---

## Rewards

#### `GET /api/v1/rewards/balance`
Get current coin and XRP balance.

**Response:** `200 OK`
```json
{
  "route_coins": 4250,
  "xrp_equivalent": 0.425,
  "tier": "regular",
  "xrp_conversion_rate": 0.0001,
  "tier_bonus_rate": 1.1
}
```

#### `GET /api/v1/rewards/streaks`
Get streak information.

**Response:** `200 OK`
```json
{
  "current_streak": 8,
  "longest_streak": 23,
  "multiplier": 2.0,
  "next_milestone": { "days": 14, "multiplier": 2.5 },
  "streak_freezes_remaining": 1,
  "last_completed_date": "2026-03-31"
}
```

#### `GET /api/v1/rewards/badges`
Get user's badges.

**Response:** `200 OK`
```json
{
  "earned": [
    {
      "id": "traffic_hero",
      "name": "Traffic Hero",
      "description": "Your detour reduced congestion for 50+ commuters",
      "earned_at": "2026-03-15T10:30:00+05:30",
      "pinned": true
    }
  ],
  "available": [
    {
      "id": "century_club",
      "name": "Century Club",
      "description": "Complete 100 total routes",
      "progress": { "current": 67, "target": 100 }
    }
  ]
}
```

#### `GET /api/v1/rewards/leaderboard`
Get area leaderboard.

**Query params:** `?area=andheri&period=week`

**Response:** `200 OK`
```json
{
  "area": "andheri",
  "period": "2026-W14",
  "rankings": [
    {
      "rank": 1,
      "display_name": "Rohan M.",
      "coins_earned": 1250,
      "tier": "pro",
      "pinned_badges": ["traffic_hero", "perfect_week"]
    }
  ],
  "user_rank": 12,
  "total_participants": 340
}
```

#### `GET /api/v1/rewards/history`
Get coin transaction history.

**Query params:** `?limit=20&offset=0`

**Response:** `200 OK`
```json
{
  "transactions": [
    {
      "id": "uuid",
      "type": "route_completion",
      "coins": 56,
      "description": "Route completed: Andheri → CST",
      "timestamp": "2026-03-31T09:15:00+05:30"
    },
    {
      "type": "badge_bonus",
      "coins": 100,
      "description": "Badge earned: Traffic Hero",
      "timestamp": "2026-03-31T09:15:00+05:30"
    }
  ],
  "total": 142
}
```

---

## User Profile

#### `GET /api/v1/users/me`
Get current user profile.

#### `PUT /api/v1/users/me`
Update profile (display name, area, XRP wallet address).

#### `GET /api/v1/users/me/stats`
Get personal statistics.

**Response:** `200 OK`
```json
{
  "total_routes": 67,
  "total_distance_km": 823.5,
  "total_coins_earned": 4250,
  "compliance_rate": 0.87,
  "time_saved_for_others_min": 1240,
  "co2_reduced_kg": 15.3,
  "favorite_route": "Andheri → BKC",
  "member_since": "2026-01-15"
}
```

---

## Challenges

#### `GET /api/v1/challenges`
List all challenges grouped by active/upcoming/completed, with user progress.

**Response:** `200 OK`
```json
{
  "active": [
    {
      "id": "uuid",
      "title": "Monsoon Week Challenge",
      "description": "Complete 10 routes during monsoon week",
      "type": "weekly",
      "category": "monsoon",
      "goal_type": "routes_count",
      "goal_value": 10,
      "goal_area": null,
      "reward_coins": 500,
      "reward_xrp": 0.5,
      "reward_badge_id": null,
      "starts_at": "2026-04-20T00:00:00+05:30",
      "ends_at": "2026-04-27T23:59:59+05:30",
      "max_participants": null,
      "active": true,
      "participant_count": 124,
      "user_joined": true,
      "user_progress": 7,
      "user_completed": false
    }
  ],
  "upcoming": [],
  "completed": []
}
```

#### `GET /api/v1/challenges/{challenge_id}`
Get a single challenge with user progress.

**Response:** `200 OK` — same shape as a single item from the list above.

#### `POST /api/v1/challenges/{challenge_id}/join`
Join an active challenge.

**Response:** `200 OK`
```json
{
  "challenge_id": "uuid",
  "joined": true,
  "message": "Joined successfully"
}
```

**Error cases:**
```json
{ "challenge_id": "uuid", "joined": false, "message": "Challenge has ended" }
{ "challenge_id": "uuid", "joined": false, "message": "Challenge is full" }
{ "challenge_id": "uuid", "joined": true, "message": "Already joined" }
```

#### `POST /api/v1/challenges/{challenge_id}/claim`
Claim reward for a completed challenge.

**Response:** `200 OK`
```json
{
  "claimed": true,
  "message": "Reward claimed!",
  "coins_earned": 500,
  "xrp_earned": 0.5
}
```

#### `POST /api/v1/challenges`
Create a new challenge (admin).

**Request:**
```json
{
  "title": "Flash Peak Hour Sprint",
  "description": "Complete 5 routes during peak hours this week",
  "type": "flash",
  "category": "peak",
  "goal_type": "peak_routes",
  "goal_value": 5,
  "reward_coins": 1000,
  "reward_xrp": 1.0,
  "starts_at": "2026-04-23T00:00:00+05:30",
  "ends_at": "2026-04-24T23:59:59+05:30",
  "max_participants": 50
}
```

**Response:** `201 Created` — returns the created challenge.

---

## Social / Referrals

#### `GET /api/v1/social/referral-code`
Get (or create) the current user's referral code.

**Response:** `200 OK`
```json
{
  "code": "LM-A3B2C1",
  "uses": 5,
  "max_uses": null,
  "active": true,
  "share_url": "https://leadme.app/join?ref=LM-A3B2C1"
}
```

#### `GET /api/v1/social/referral-stats`
Get referral statistics and history.

**Response:** `200 OK`
```json
{
  "referral_code": "LM-A3B2C1",
  "total_referrals": 3,
  "qualified_referrals": 2,
  "total_coins_earned": 400,
  "referrals": [
    {
      "referred_display_name": "Rohan M.",
      "qualified": true,
      "coins_earned": 200,
      "created_at": "2026-04-01T10:00:00+05:30"
    }
  ]
}
```

#### `POST /api/v1/social/apply-referral`
Apply a referral code (for new users).

**Request:**
```json
{ "code": "LM-A3B2C1" }
```

**Response:** `200 OK`
```json
{ "applied": true, "message": "Referral code applied!", "bonus_coins": 100 }
```

#### `POST /api/v1/social/share`
Track a social share action and get share content.

**Request:**
```json
{
  "channel": "whatsapp",
  "content_type": "referral",
  "content_id": null
}
```

**Response:** `200 OK`
```json
{
  "shared": true,
  "share_url": "https://leadme.app/join?ref=LM-A3B2C1",
  "message": "Join LeadMe and earn crypto for your commute! Use my code: LM-A3B2C1"
}
```

---

## Sponsors

#### `GET /api/v1/sponsors/pools`
List all reward pools grouped by active/upcoming/depleted.

**Response:** `200 OK`
```json
{
  "active": [
    {
      "id": "uuid",
      "sponsor_id": "uuid",
      "sponsor_name": "Mumbai Traffic Corp",
      "title": "Andheri Green Route Fund",
      "description": "Extra XRP for eco-compliant routes through Andheri",
      "currency": "XRP",
      "total_amount": 100.0,
      "remaining_amount": 75.5,
      "reward_per_route": 0.05,
      "target_area": "Andheri",
      "min_compliance": 0.85,
      "starts_at": "2026-04-01T00:00:00+05:30",
      "ends_at": "2026-04-30T23:59:59+05:30",
      "active": true,
      "total_payouts": 490
    }
  ],
  "upcoming": [],
  "depleted": []
}
```

#### `GET /api/v1/sponsors/my-payouts`
Get the current user's sponsor payout history.

#### `POST /api/v1/sponsors/sponsors`
Create a new sponsor (admin).

#### `POST /api/v1/sponsors/pools`
Create a new reward pool (admin).

---

## NFT Badges

#### `GET /api/v1/nft`
List all NFT badges for the current user.

**Response:** `200 OK`
```json
{
  "nfts": [
    {
      "id": "uuid",
      "badge_id": "traffic_hero",
      "badge_name": "Traffic Hero",
      "chain": "xrpl",
      "token_id": "ABC123DEF456",
      "tx_hash": "NFT_ABC123DEF456",
      "wallet_address": "rN7n3473SaZBCG4dFL83w7p1W6cfJRrcmZ",
      "explorer_url": "https://testnet.xrpl.org/nft/ABC123DEF456",
      "status": "minted",
      "created_at": "2026-04-15T10:00:00+05:30",
      "minted_at": "2026-04-15T10:00:05+05:30"
    }
  ],
  "total": 1
}
```

#### `POST /api/v1/nft/mint`
Mint an NFT for an earned badge.

**Request:**
```json
{
  "user_badge_id": "uuid",
  "chain": "xrpl",
  "wallet_address": "rN7n3473SaZBCG4dFL83w7p1W6cfJRrcmZ"
}
```

**Response:** `200 OK`
```json
{
  "nft_id": "uuid",
  "status": "minted",
  "tx_hash": "NFT_ABC123",
  "explorer_url": "https://testnet.xrpl.org/nft/ABC123",
  "message": "NFT minted on xrpl!"
}
```

#### `GET /api/v1/nft/{nft_id}/status`
Check the status of an NFT mint.

---

## Cities

#### `GET /api/v1/cities`
List all configured cities (public endpoint).

**Response:** `200 OK`
```json
{
  "cities": [
    {
      "id": "uuid",
      "slug": "mumbai",
      "name": "Mumbai",
      "country": "India",
      "timezone": "Asia/Kolkata",
      "lat_min": 18.89,
      "lat_max": 19.27,
      "lng_min": 72.77,
      "lng_max": 72.98,
      "center_lat": 19.076,
      "center_lng": 72.8777,
      "default_zoom": 12,
      "areas": ["Andheri", "Bandra", "BKC", "Powai", "..."],
      "peak_hours": {
        "morning": { "start": "08:00", "end": "10:30" },
        "evening": { "start": "17:30", "end": "20:00" }
      },
      "active": true
    }
  ],
  "active_count": 1
}
```

#### `GET /api/v1/cities/{slug}`
Get a single city by slug.

#### `POST /api/v1/cities`
Create a new city configuration (admin).

---

## Cashout

#### `GET /api/v1/cashout/cryptos`
List supported cryptocurrencies and their status.

**Response:** `200 OK`
```json
{
  "active_provider": "xrp",
  "providers": [
    { "name": "xrp", "currency": "XRP", "status": "active", "label": "XRP Ledger" },
    { "name": "sol", "currency": "SOL", "status": "coming_soon", "label": "Solana" },
    { "name": "eth", "currency": "ETH", "status": "coming_soon", "label": "Ethereum / Polygon" }
  ]
}
```

#### `GET /api/v1/cashout/wallets`
List user's linked crypto wallets.

**Response:** `200 OK`
```json
{
  "wallets": [
    {
      "id": "uuid",
      "currency": "XRP",
      "address": "rN7n3473SaZBCG4dFL83w7p1W6cfJRrcmZ",
      "label": "My Xaman Wallet",
      "verified": false,
      "is_primary": true,
      "created_at": "2026-03-20T10:00:00+05:30"
    }
  ]
}
```

#### `POST /api/v1/cashout/wallets`
Link a cryptocurrency wallet.

**Request:**
```json
{
  "currency": "XRP",
  "address": "rN7n3473SaZBCG4dFL83w7p1W6cfJRrcmZ",
  "label": "My Xaman Wallet"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "currency": "XRP",
  "address": "rN7n3473SaZBCG4dFL83w7p1W6cfJRrcmZ",
  "label": "My Xaman Wallet",
  "verified": false,
  "is_primary": true,
  "created_at": "2026-03-20T10:00:00+05:30"
}
```

#### `DELETE /api/v1/cashout/wallets/{wallet_id}`
Remove a linked wallet.

**Response:** `200 OK`
```json
{ "ok": true }
```

#### `POST /api/v1/cashout/estimate`
Estimate how much crypto you'll receive for a given coin amount.

**Request:**
```json
{
  "coins_amount": 5000,
  "currency": "XRP"
}
```

**Response:** `200 OK`
```json
{
  "coins_amount": 5000,
  "crypto_amount": 0.55,
  "currency": "XRP",
  "tier_bonus": 1.1,
  "conversion_rate": 10000,
  "min_cashout_coins": 1000,
  "eligible": true,
  "reason": null
}
```

**Ineligible example:**
```json
{
  "coins_amount": 500,
  "crypto_amount": 0.05,
  "currency": "XRP",
  "tier_bonus": 1.0,
  "conversion_rate": 10000,
  "min_cashout_coins": 1000,
  "eligible": false,
  "reason": "Minimum cashout is 1000 Route Coins"
}
```

#### `POST /api/v1/cashout/cashout`
Execute a cashout — convert Route Coins to cryptocurrency.

**Request:**
```json
{
  "coins_amount": 5000,
  "currency": "XRP",
  "wallet_id": null
}
```

`wallet_id` is optional — uses primary wallet for the currency if omitted.

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "coins_amount": 5000,
  "crypto_amount": 0.55,
  "currency": "XRP",
  "tier_bonus": 1.1,
  "wallet_address": "rN7n3473SaZBCG4dFL83w7p1W6cfJRrcmZ",
  "status": "completed",
  "tx_hash": "A1B2C3D4E5F6...",
  "explorer_url": "https://testnet.xrpl.org/transactions/A1B2C3D4E5F6...",
  "failure_reason": null,
  "created_at": "2026-04-01T10:30:00+05:30",
  "completed_at": "2026-04-01T10:30:05+05:30"
}
```

**Error responses:**
- `400` — Insufficient balance, minimum not met, no wallet linked, currency unavailable
- `400` — Cooldown active (24h between cashouts)

#### `GET /api/v1/cashout/history`
Get cashout history.

**Query params:** `?limit=20&offset=0`

**Response:** `200 OK`
```json
{
  "cashouts": [
    {
      "id": "uuid",
      "coins_amount": 5000,
      "crypto_amount": 0.55,
      "currency": "XRP",
      "tier_bonus": 1.1,
      "wallet_address": "rN7n3473SaZBCG4dFL83w7p1W6cfJRrcmZ",
      "status": "completed",
      "tx_hash": "A1B2C3D4E5F6...",
      "explorer_url": "https://testnet.xrpl.org/transactions/A1B2C3D4E5F6...",
      "created_at": "2026-04-01T10:30:00+05:30",
      "completed_at": "2026-04-01T10:30:05+05:30"
    }
  ],
  "total": 3,
  "total_cashed_out": {
    "XRP": 1.65,
    "SOL": 0.0,
    "ETH": 0.0
  }
}
```
