# Provider Adapter System

LeadMe uses an adapter pattern for all external services — routing, maps, SMS, and crypto. Providers can be swapped without changing business logic. Each category follows the same structure:

```
providers/<category>/
├── base.py       # Abstract interface
├── registry.py   # Selection + failover logic
├── <impl>.py     # Concrete providers
└── mock.py       # Dev/test fallback
```

**Selection logic** (same for all categories):
1. Explicit setting in `.env` (e.g., `ROUTING_PROVIDER=mapbox`)
2. Auto-detect based on which API keys are configured
3. Fallback to mock/free provider

---

## Routing Providers (`backend/app/providers/routing/`)

### Abstract Interface (`base.py`)

```python
class RoutingProvider(ABC):
    name: str                                          # "google", "mapbox", etc.
    async def get_routes(request) -> RoutingResponse   # fetch route alternatives
    async def get_traffic(polyline) -> [TrafficSegment] # traffic on a route
    async def health_check() -> bool                   # is the API reachable?
```

### Available Providers

| Provider | File | API Key Env Var | Free Tier | Best For |
|----------|------|-----------------|-----------|----------|
| Google Routes | `google.py` | `GOOGLE_ROUTES_API_KEY` | $200/mo credit | Best Mumbai traffic data |
| Mapbox | `mapbox.py` | `MAPBOX_ACCESS_TOKEN` | 100K req/mo | Generous free tier |
| HERE | `here.py` | `HERE_API_KEY` | 250K req/mo | Good India coverage |
| Mock | `mock.py` | None needed | Always free | Development & testing |

### Selection

```bash
ROUTING_PROVIDER=mapbox  # explicit
# or leave empty for auto-detect: google → mapbox → here → mock
```

### Failover

If the primary provider's health check fails, the registry tries the next available provider in order.

### Adding a New Routing Provider

1. Create `backend/app/providers/routing/your_provider.py`
2. Subclass `RoutingProvider` from `base.py`
3. Implement `name`, `get_routes()`, `get_traffic()`, `health_check()`
4. Add API key to `config.py` Settings class
5. Register in `registry.py` (`_get_provider()` and auto-detect logic)

---

## SMS Providers (`backend/app/providers/sms/`)

### Abstract Interface (`base.py`)

```python
class SMSProvider(ABC):
    name: str                                    # "twilio", "msg91", "console"
    async def send_otp(phone, otp) -> bool       # send OTP to phone number
```

### Available Providers

| Provider | File | Env Vars | Free Tier | Best For |
|----------|------|----------|-----------|----------|
| Twilio | `twilio.py` | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | Trial credit | Global SMS |
| MSG91 | `msg91.py` | `MSG91_AUTH_KEY`, `MSG91_TEMPLATE_ID` | 5K SMS/mo | India-optimized, DLT compliant |
| Console | `console.py` | None needed | Always free | Dev mode (logs OTP to stdout) |

### Selection

```bash
SMS_PROVIDER=twilio  # explicit
# or leave empty for auto-detect: twilio → msg91 → console
```

In development, the Console provider logs OTPs to stdout so you can test without real SMS:
```
[CONSOLE SMS] OTP for +919876543210: 123456
```

### Adding a New SMS Provider

1. Create `backend/app/providers/sms/your_provider.py`
2. Subclass `SMSProvider` from `base.py`
3. Implement `name` and `send_otp(phone, otp) -> bool`
4. Add config fields to `config.py`
5. Register in `registry.py`

---

## Crypto Providers (`backend/app/providers/crypto/`)

### Abstract Interface (`base.py`)

```python
class CryptoProvider(ABC):
    name: str                                     # "xrp", "sol", "eth", "mock"
    currency_code: str                            # "XRP", "SOL", "ETH"
    network_name: str                             # "xrpl-testnet", etc.
    async def validate_address(address) -> bool   # check address format
    async def get_balance(address) -> float       # wallet balance
    async def transfer(request) -> TransferResult # send crypto
    async def get_transaction(tx_hash) -> TransferResult | None
    async def health_check() -> bool
    async def get_min_transfer_amount() -> float
```

### Available Providers

| Provider | File | Status | Env Vars | Network |
|----------|------|--------|----------|---------|
| XRP | `xrp.py` | **Active** | `XRPL_NETWORK_URL`, `XRPL_WALLET_SEED` | XRPL testnet/mainnet |
| Solana | `sol.py` | Coming Soon | `SOLANA_RPC_URL`, `SOLANA_WALLET_SEED` | Solana devnet |
| Ethereum | `eth.py` | Coming Soon | `ETH_RPC_URL`, `ETH_WALLET_PRIVATE_KEY` | Polygon Amoy |
| Mock | `mock.py` | Dev only | None needed | In-memory ledger |

### Selection

```bash
CRYPTO_PROVIDER=xrp  # explicit
# or leave empty for auto-detect: xrp (if XRPL_WALLET_SEED set) → mock
```

### Transfer Flow

```
CashoutService calls provider.transfer(TransferRequest)
  → Provider builds transaction (e.g., XRPL Payment)
  → Signs with platform wallet seed
  → Submits to blockchain
  → Returns TransferResult (tx_hash, status, explorer_url)
```

### Adding a New Crypto Provider

1. Create `backend/app/providers/crypto/your_chain.py`
2. Subclass `CryptoProvider` from `base.py`
3. Implement all abstract methods (validate, balance, transfer, health_check, etc.)
4. Add config fields to `config.py` (RPC URL, wallet credentials, conversion rate)
5. Register in `registry.py`
6. Add conversion rate to cashout service

See [CRYPTO.md](CRYPTO.md) for detailed crypto architecture.

---

## Frontend Map Providers (`web/src/lib/maps/`)

### Abstract Interface (`types.ts`)

```typescript
type MapProviderProps = {
  config: MapConfig;       // center, zoom, style
  routes?: RouteLayer[];   // polylines to display
  markers?: MarkerConfig[];// origin/destination pins
  traffic?: TrafficLayerConfig;
  events?: MapEvents;      // onClick, onMoveEnd, etc.
};
```

### Available Providers

| Provider | File | Token Env Var | Free Tier |
|----------|------|---------------|-----------|
| Mapbox GL JS | `mapbox.tsx` | `NEXT_PUBLIC_MAPBOX_TOKEN` | 50K map loads/mo |
| Leaflet + OSM | `leaflet.tsx` | None needed | Always free |

### Selection

```bash
NEXT_PUBLIC_MAP_PROVIDER=mapbox  # explicit
# or leave empty: mapbox (if token set) → leaflet
```

### Usage in Components

```tsx
import MapView from "@/lib/maps";

<MapView
  config={{ center: { lat: 19.076, lng: 72.877 }, zoom: 12 }}
  markers={[
    { id: "origin", position: { lat: 19.12, lng: 72.85 }, color: "#10B981" },
    { id: "dest", position: { lat: 18.94, lng: 72.84 }, color: "#EF4444" },
  ]}
  traffic={{ enabled: true }}
/>
```

### Adding a New Map Provider

1. Create `web/src/lib/maps/your_provider.tsx`
2. Export a default React component accepting `MapProviderProps`
3. Register in `web/src/lib/maps/index.tsx` (add to `providers` map)

---

## Health Check Endpoint

All provider health statuses are available at:

```
GET /health/providers
```

```json
{
  "routing_provider": "mock",
  "routing_healthy": true,
  "crypto_provider": "mock",
  "crypto_currency": "MOCK",
  "crypto_network": "mock-devnet",
  "crypto_healthy": true
}
```
