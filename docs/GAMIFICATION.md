# Gamification System

## Overview

LeadMe's gamification layer incentivizes commuters to follow assigned routes through a multi-layered reward system backed by XRP cryptocurrency.

## 1. Route Coins (Primary Currency)

Route Coins are the in-app currency earned for every completed assigned route.

### Earning Formula
```
coins_earned = base_reward × detour_multiplier × streak_multiplier × peak_multiplier
```

| Factor | Value |
|--------|-------|
| Base reward | 10 coins per completed route |
| Detour multiplier | 1.0 (no detour) to 2.0 (max detour, 15% longer) |
| Streak multiplier | 1.0x (no streak) / 1.5x (3-day) / 2.0x (7-day) / 3.0x (30-day) |
| Peak hour multiplier | 2.0x during 8-10am, 6-9pm |

### XRP Conversion
- Rate: **1,000 Route Coins = 0.1 XRP** (adjustable)
- Conversion available weekly (Phase 2: real cashout)
- Higher tiers get better conversion rates

## 2. Streaks

Consecutive days of following assigned routes.

| Streak | Multiplier | Bonus |
|--------|-----------|-------|
| 3 days | 1.5x | — |
| 7 days | 2.0x | "Week Warrior" badge |
| 14 days | 2.5x | — |
| 30 days | 3.0x | "Monthly Maven" badge |

### Streak Rules
- One completed assigned route per day maintains the streak
- Missing a day resets the streak to 0
- **Streak Freeze**: 1 free miss per month (earned at Regular tier)
- Streak counter visible on dashboard

## 3. Badges

Achievement-based unlockables displayed on profile.

### Badge Catalog

| Badge | Criteria | Coins Bonus |
|-------|----------|-------------|
| Traffic Hero | Your detour reduced congestion for 50+ commuters | 100 |
| Early Bird | Complete 10 routes before 7am | 50 |
| Mumbai Local | Use LeadMe in 5+ different areas | 75 |
| Perfect Week | Follow all assigned routes for 7 consecutive days | 100 |
| Century Club | Complete 100 total routes | 200 |
| Monsoon Warrior | Complete 20 routes during monsoon season (Jun-Sep) | 150 |
| Night Owl | Complete 10 routes after 9pm | 50 |
| Route Pioneer | Be among first 10 users on a newly added route | 75 |

### Badge Display
- Badges appear on user profile
- Top 3 badges can be "pinned" for leaderboard display
- Shareable to WhatsApp/social media

## 4. Tiers

Progressive levels based on total routes completed and compliance rate.

| Tier | Routes Required | Compliance Rate | Perks |
|------|----------------|-----------------|-------|
| Rookie | 0 | — | Base rewards |
| Regular | 25+ | 70%+ | Streak freeze (1/month), 1.1x XRP rate |
| Pro | 100+ | 80%+ | Priority for shorter routes, 1.25x XRP rate |
| Legend | 500+ | 90%+ | Best route priority, 1.5x XRP rate, exclusive badges |

### Tier Rules
- Tier is recalculated monthly
- Compliance rate = (routes followed / routes assigned) over last 30 days
- Tier can go down if compliance drops (with 1-week grace period)

## 5. Leaderboards

### Area-wise Leaderboard
- Rankings per Mumbai area (Andheri, Bandra, Powai, Dadar, etc.)
- Based on coins earned in the current week
- Resets every Monday at midnight IST
- Top 3 get bonus coins: 1st = 500, 2nd = 300, 3rd = 100

### City-wide Impact
- Not competitive — shows collective impact
- "LeadMe users saved Mumbai X hours this month"
- "Y kg CO2 reduced through optimized routing"

## 6. Challenges & Events (Phase 2)

### Weekly Challenges
- "Follow 5 routes through Dadar this week — earn 3x coins"
- "Complete 3 peak-hour routes — earn Traffic Hero badge"

### City Events
- Mumbai Marathon day — help clear routes for bonus XRP
- Festival traffic challenges (Ganesh Chaturthi, Diwali)
- Monsoon season survival challenge

## 7. Penalties (Gentle)

LeadMe uses **positive reinforcement** over punishment.

| Scenario | Consequence |
|----------|------------|
| Don't follow assigned route | No coins earned, streak resets |
| Repeated non-compliance (5+ in a row) | "Explorer" status: lower priority for high-reward routes |
| Extended inactivity (30+ days) | Tier review, possible demotion |
| Cancel scheduled route without notice | No penalty (life happens) |

### What We NEVER Do
- Never deduct earned Route Coins
- Never deduct earned XRP
- Never lock users out of the app
- Never publicly shame non-compliant users

## 8. XRP Integration Details

### Phase 1 (MVP)
- Users see XRP balance (calculated from Route Coins)
- Balance is tracked in our database
- No actual XRP transfers yet

### Phase 2
- Users link XUMM/Xaman wallet
- Weekly cashout: coins → XRP → user's wallet
- Minimum cashout: 1,000 coins (0.1 XRP)
- Transaction on XRPL testnet first, mainnet after audit

### Sponsor Pools (Phase 3)
- Local businesses fund XRP reward pools
- Routes passing near sponsor locations earn bonus XRP
- Organic, non-intrusive advertising model
