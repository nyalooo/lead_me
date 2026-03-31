# API Reference

Base URL: `http://localhost:8000/api/v1`

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
