/**
 * Abstract types for map providers.
 *
 * All map components depend on these types, never on a specific
 * provider (Mapbox, Google Maps, Leaflet, etc.) directly.
 */

export type LatLng = {
  lat: number;
  lng: number;
};

export type MapBounds = {
  north: number;
  south: number;
  east: number;
  west: number;
};

export type RouteLayer = {
  id: string;
  polyline: string; // encoded polyline
  color: string;
  width?: number;
  opacity?: number;
};

export type MarkerConfig = {
  id: string;
  position: LatLng;
  label?: string;
  color?: string;
};

export type TrafficLayerConfig = {
  enabled: boolean;
};

/**
 * Configuration passed to any map provider.
 */
export type MapConfig = {
  center: LatLng;
  zoom: number;
  style?: string; // provider-specific style URL
  interactive?: boolean;
};

/**
 * Events emitted by map providers.
 */
export type MapEvents = {
  onMapClick?: (latlng: LatLng) => void;
  onMarkerClick?: (markerId: string) => void;
  onMoveEnd?: (center: LatLng, zoom: number) => void;
};

/**
 * Abstract interface for a map provider.
 *
 * To add a new provider:
 * 1. Create a new file (e.g., google-maps.tsx) in web/src/lib/maps/
 * 2. Implement the MapProvider interface
 * 3. Export a React component that accepts MapProviderProps
 * 4. Register it in the provider map in index.ts
 */
export type MapProviderProps = {
  config: MapConfig;
  routes?: RouteLayer[];
  markers?: MarkerConfig[];
  traffic?: TrafficLayerConfig;
  events?: MapEvents;
  className?: string;
};

/**
 * Supported map provider names.
 */
export type MapProviderName = "mapbox" | "google" | "leaflet";
