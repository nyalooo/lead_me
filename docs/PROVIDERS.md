# Provider Adapter System

LeadMe uses an adapter pattern for external services (routing, maps) so providers can be swapped without changing business logic.

## Architecture

```
┌─────────────────────┐
│   Route Engine      │  depends on abstract interface only
│   (service.py)      │
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │  Registry   │  selects provider based on config
    │ (registry.py)│
    └──────┬──────┘
           │
    ┌──────┼──────────────┬──────────────┐
    ▼      ▼              ▼              ▼
┌────────┐┌────────┐┌──────────┐┌────────────┐
│ Google ││ Mapbox ││   HERE   ││   Mock     │
│ Routes ││Directns││ Routing  ││ (dev/test) │
└────────┘└────────┘└──────────┘└────────────┘
```

## Backend Providers (`backend/app/providers/routing/`)

### Abstract Interface (`base.py`)

All providers implement `RoutingProvider`:

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

### Provider Selection

Set `ROUTING_PROVIDER` in your `.env`:

```bash
ROUTING_PROVIDER=mapbox  # explicit selection
```

Or leave empty for **auto-detection** (first provider with a configured API key wins):

```
Priority: google → mapbox → here → mock
```

### Failover

The registry supports automatic failover. If the primary provider's health check fails, it tries the next available provider in order.

### Adding a New Provider

1. Create `backend/app/providers/routing/your_provider.py`
2. Subclass `RoutingProvider` from `base.py`
3. Implement `name`, `get_routes()`, `get_traffic()`, `health_check()`
4. Add API key to `config.py` Settings class
5. Register in `registry.py` (`_get_provider()` and auto-detect logic)

Example skeleton:

```python
from app.providers.routing.base import RoutingProvider, RoutingRequest, RoutingResponse

class MyProvider(RoutingProvider):
    @property
    def name(self) -> str:
        return "my_provider"

    async def get_routes(self, request: RoutingRequest) -> RoutingResponse:
        # Call your API, return standardized RoutingResponse
        ...

    async def get_traffic(self, route_polyline: str) -> list[TrafficSegment]:
        ...

    async def health_check(self) -> bool:
        ...
```

## Frontend Map Providers (`web/src/lib/maps/`)

### Abstract Interface (`types.ts`)

All map components accept `MapProviderProps`:

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

### Provider Selection

Set `NEXT_PUBLIC_MAP_PROVIDER` in `.env.local`:

```bash
NEXT_PUBLIC_MAP_PROVIDER=mapbox  # explicit
```

Or leave empty for auto-detection:
- If `NEXT_PUBLIC_MAPBOX_TOKEN` is set → Mapbox
- Otherwise → Leaflet (free, no signup required)

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

The `MapView` component automatically selects and loads the right provider — no need to import Mapbox or Leaflet directly.

### Adding a New Map Provider

1. Create `web/src/lib/maps/your_provider.tsx`
2. Export a default React component accepting `MapProviderProps`
3. Register in `web/src/lib/maps/index.tsx` (add to `providers` map)
