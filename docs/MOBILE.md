# Mobile App Development Guide

## Overview

LeadMe's mobile app is built with **React Native (Expo)** and TypeScript. The key mobile advantage over the web app is **background GPS tracking** — the app can track route compliance even when minimized.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | React Native + Expo SDK |
| Language | TypeScript |
| Navigation | React Navigation (Stack + Bottom Tabs) |
| Maps | react-native-maps (Google Maps on Android, Apple Maps on iOS) |
| GPS | expo-location + expo-task-manager (background) |
| Storage | expo-secure-store (encrypted tokens) |

## Project Structure

```
mobile/
├── App.tsx                          # Entry point → AppNavigator
├── app.json                         # Expo config (permissions, splash)
├── src/
│   ├── navigation/
│   │   └── AppNavigator.tsx         # Auth check → Login or Main Tabs
│   ├── screens/
│   │   ├── LoginScreen.tsx          # Phone OTP login
│   │   ├── DashboardScreen.tsx      # Stats, map, quick routes, GPS controls
│   │   ├── ScheduleScreen.tsx       # Recurring commute management
│   │   ├── LeaderboardScreen.tsx    # Area-based rankings
│   │   ├── CashoutScreen.tsx        # Wallet linking, coin→crypto conversion
│   │   └── ProfileScreen.tsx        # User info, badges, stats, logout
│   ├── hooks/
│   │   └── useBackgroundLocation.ts # Background GPS tracking hook
│   └── lib/
│       ├── api.ts                   # Backend API client (shared endpoints)
│       ├── auth.ts                  # SecureStore token management
│       └── theme.ts                 # Design tokens (colors, spacing)
├── assets/                          # App icons, splash screen
├── Dockerfile                       # Expo dev server for Docker
└── package.json
```

## Navigation Flow

```
App Launch
  │
  ├─ Not authenticated → LoginScreen
  │   ├─ Enter phone → Request OTP
  │   └─ Enter OTP → Verify → Navigate to Main
  │
  └─ Authenticated → MainTabs
      ├─ Dashboard  (Home tab)
      ├─ Schedule   (Calendar tab)
      ├─ Leaderboard (Trophy tab)
      ├─ Cashout    (Wallet tab)
      └─ Profile    (User tab)
```

## Background GPS Tracking

This is the core mobile feature. The web app uses `navigator.geolocation.watchPosition` which stops when the tab is backgrounded. The mobile app uses `expo-location` with `expo-task-manager` for true background tracking.

### How It Works

1. **Task registration** (module level in `useBackgroundLocation.ts`):
   ```
   TaskManager.defineTask('leadme-background-location', callback)
   ```
   This runs even when the app is minimized.

2. **Permission flow**:
   - Request foreground location permission (required)
   - Request background location permission (iOS: "Always", Android: "Allow all the time")
   - Start `Location.startLocationUpdatesAsync()` with foreground service notification

3. **Location settings**:
   - Accuracy: High (GPS)
   - Distance interval: 20m minimum between updates
   - Time interval: 5 seconds
   - Foreground service shows "Tracking your route for rewards" notification

4. **Batch upload**:
   - Locations buffer in memory
   - Every 10 seconds, batch upload to `POST /routes/{id}/track`
   - Failed uploads are retried on next batch cycle

### Android Permissions

```xml
ACCESS_COARSE_LOCATION
ACCESS_FINE_LOCATION
ACCESS_BACKGROUND_LOCATION
FOREGROUND_SERVICE
FOREGROUND_SERVICE_LOCATION
```

### iOS Permissions

Configured in `app.json`:
```json
{
  "NSLocationWhenInUseUsageDescription": "...",
  "NSLocationAlwaysAndWhenInUseUsageDescription": "...",
  "UIBackgroundModes": ["location"]
}
```

## Screen Details

### LoginScreen
- Phone input with `+91` prefix (Mumbai-first)
- OTP verification with auto-focus on OTP field
- Dev mode: displays OTP from backend response for testing
- On success: stores token in SecureStore, navigates to Main

### DashboardScreen
- **Stats cards**: Route Coins, streak days, current tier
- **Streak banner**: Shows active multiplier (e.g., "2x streak multiplier active!")
- **Map**: react-native-maps with user location and destination marker
- **Quick routes**: Andheri→CST, Bandra→Thane, Borivali→Dadar
- **Active route controls**: Start tracking → Complete route (with results)
- Pull-to-refresh for stats

### ScheduleScreen
- Day picker (7 chips: Mon–Sun)
- Departure time input
- CRUD: create, view, delete schedules
- Empty state with helpful message

### LeaderboardScreen
- Horizontal area filter chips (Mumbai, Andheri, Bandra, Thane, Navi Mumbai)
- User rank banner
- Rankings list with medals (gold/silver/bronze for top 3)
- Tier color coding per entry

### CashoutScreen
- **Balance card**: Total coins, XRP equivalent, tier bonus display
- **Currency selector**: XRP (active), SOL (coming soon), ETH (coming soon)
- **Wallet management**: Link/view wallet address per currency
- **Cashout form**: Enter coins → estimate → confirm → execute
- **History**: Past cashouts with status (completed/failed/processing)

### ProfileScreen
- Avatar with initials, display name, phone, tier badge
- Inline edit mode for name and area
- Stats grid: routes, coins, compliance %
- Earned badges grid with descriptions
- In-progress badges with progress bars
- Logout button

## Authentication

Tokens are stored in `expo-secure-store` (Keychain on iOS, Keystore on Android):

```typescript
// Store
await SecureStore.setItemAsync('leadme_token', token);

// Retrieve
const token = await SecureStore.getItemAsync('leadme_token');

// Clear on logout
await SecureStore.deleteItemAsync('leadme_token');
```

## API Client

The mobile API client (`src/lib/api.ts`) mirrors the web client (`web/src/lib/api.ts`). Both call the same backend endpoints. The mobile client:

- Uses `fetch()` (React Native built-in)
- Reads token from SecureStore (not localStorage)
- Base URL: `http://<dev-machine-ip>:6800/api/v1` in dev, production URL in release

### Configuring the API URL

In `src/lib/api.ts`, update `BASE_URL` for your local dev environment:

```typescript
const BASE_URL = __DEV__
  ? 'http://192.168.1.100:6800/api/v1'  // your machine's LAN IP
  : 'https://api.leadme.app/api/v1';
```

To find your LAN IP: `ifconfig | grep inet` or check your Wi-Fi network settings.

## Running the Mobile App

### Local Development

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with Expo Go (iOS/Android) to run on your phone.

### Docker

```bash
docker compose --profile mobile up
```

The Expo dev server runs on port 6081 (mapped from 8081).

### Building for Production

```bash
# iOS
npx expo build:ios

# Android
npx expo build:android

# Or use EAS Build (recommended)
npx eas build --platform all
```

## Design System

The mobile app uses the same emerald color palette as the web app. Design tokens are in `src/lib/theme.ts`:

| Token | Value | Usage |
|-------|-------|-------|
| `colors.primary` | `#059669` | Buttons, highlights, active states |
| `colors.primaryLight` | `#34d399` | Secondary actions |
| `colors.primaryBg` | `#ecfdf5` | Light backgrounds |
| `colors.background` | `#f9fafb` | Screen backgrounds |
| `colors.surface` | `#ffffff` | Cards and panels |
| `colors.text` | `#111827` | Primary text |
| `colors.textSecondary` | `#6b7280` | Secondary text |

Tier colors: `rookie` (gray), `regular` (blue), `pro` (purple), `legend` (gold).
