/**
 * Map provider registry.
 *
 * Selects the right map component based on config:
 * 1. NEXT_PUBLIC_MAP_PROVIDER env var (explicit override)
 * 2. Auto-detect: Mapbox if token set, else Leaflet (free fallback)
 *
 * Usage in components:
 *   import MapView from "@/lib/maps";
 *   <MapView config={...} routes={...} markers={...} />
 */

"use client";

import type { ComponentType } from "react";
import dynamic from "next/dynamic";
import type { MapProviderName, MapProviderProps } from "./types";

// Dynamic imports — each provider is only loaded when selected
const providers: Record<MapProviderName, ComponentType<MapProviderProps>> = {
  mapbox: dynamic<MapProviderProps>(() => import("./mapbox"), { ssr: false }),
  leaflet: dynamic<MapProviderProps>(() => import("./leaflet"), { ssr: false }),
  google: dynamic<MapProviderProps>(
    () => import("./leaflet"), // TODO: implement google maps provider, fallback to leaflet
    { ssr: false },
  ),
};

function getProviderName(): MapProviderName {
  // 1. Explicit override
  const explicit = process.env.NEXT_PUBLIC_MAP_PROVIDER as MapProviderName;
  if (explicit && providers[explicit]) return explicit;

  // 2. Auto-detect based on available tokens
  if (process.env.NEXT_PUBLIC_MAPBOX_TOKEN) return "mapbox";

  // 3. Free fallback
  return "leaflet";
}

export default function MapView(props: MapProviderProps) {
  const providerName = getProviderName();
  const MapComponent = providers[providerName];
  return <MapComponent {...props} />;
}

export { type MapProviderProps, type MapProviderName } from "./types";
