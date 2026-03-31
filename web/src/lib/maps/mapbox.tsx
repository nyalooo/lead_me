/**
 * Mapbox GL JS map provider.
 *
 * Requires NEXT_PUBLIC_MAPBOX_TOKEN in environment.
 * Docs: https://docs.mapbox.com/mapbox-gl-js/
 */

"use client";

import { useEffect, useRef } from "react";
import type { MapProviderProps } from "./types";

const MAPBOX_CSS = "https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.css";
const MAPBOX_JS = "https://api.mapbox.com/mapbox-gl-js/v3.3.0/mapbox-gl.js";

export default function MapboxMap({
  config,
  routes,
  markers,
  traffic,
  events,
  className,
}: MapProviderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);

  useEffect(() => {
    // Dynamically load Mapbox GL JS to avoid requiring npm package
    if (typeof window === "undefined") return;

    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!token) {
      console.warn("Mapbox: NEXT_PUBLIC_MAPBOX_TOKEN not set");
      return;
    }

    // Load CSS
    if (!document.querySelector(`link[href="${MAPBOX_CSS}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = MAPBOX_CSS;
      document.head.appendChild(link);
    }

    // Load JS
    const initMap = () => {
      const mapboxgl = // eslint-disable-next-line @typescript-eslint/no-explicit-any
(window as any).mapboxgl as {
        accessToken: string;
        Map: new (opts: Record<string, unknown>) => Record<string, unknown>;
        Marker: new (opts?: Record<string, unknown>) => Record<string, unknown>;
      };

      if (!mapboxgl || !containerRef.current) return;

      mapboxgl.accessToken = token;

      const map = new mapboxgl.Map({
        container: containerRef.current,
        style: config.style || "mapbox://styles/mapbox/streets-v12",
        center: [config.center.lng, config.center.lat],
        zoom: config.zoom,
        interactive: config.interactive !== false,
      }) as Record<string, unknown>;

      mapRef.current = map;

      const onLoad = () => {
        // Add traffic layer
        if (traffic?.enabled) {
          (map.addSource as (id: string, source: unknown) => void)("mapbox-traffic", {
            type: "vector",
            url: "mapbox://mapbox.mapbox-traffic-v1",
          });
          (map.addLayer as (layer: unknown) => void)({
            id: "traffic-layer",
            type: "line",
            source: "mapbox-traffic",
            "source-layer": "traffic",
            paint: {
              "line-color": [
                "match",
                ["get", "congestion"],
                "low", "#4CAF50",
                "moderate", "#FFC107",
                "heavy", "#FF5722",
                "severe", "#B71C1C",
                "#888888",
              ],
              "line-width": 2,
            },
          });
        }

        // Add route layers
        routes?.forEach((route, i) => {
          // Placeholder: decode polyline and add as GeoJSON source
          // For now, routes without polyline data are skipped
          if (!route.polyline) return;

          (map.addSource as (id: string, source: unknown) => void)(`route-${route.id}`, {
            type: "geojson",
            data: {
              type: "Feature",
              properties: {},
              geometry: { type: "LineString", coordinates: [] }, // TODO: decode polyline
            },
          });
          (map.addLayer as (layer: unknown) => void)({
            id: `route-layer-${route.id}`,
            type: "line",
            source: `route-${route.id}`,
            paint: {
              "line-color": route.color,
              "line-width": route.width || 4,
              "line-opacity": route.opacity || (i === 0 ? 1 : 0.5),
            },
          });
        });

        // Add markers
        markers?.forEach((marker) => {
          const el = new mapboxgl.Marker({
            color: marker.color || "#10B981",
          }) as Record<string, unknown>;
          (el.setLngLat as (coord: [number, number]) => Record<string, unknown>)(
            [marker.position.lng, marker.position.lat]
          );
          (el.addTo as (map: unknown) => void)(map);
        });
      };

      (map.on as (event: string, cb: () => void) => void)("load", onLoad);

      // Event handlers
      if (events?.onMapClick) {
        (map.on as (event: string, cb: (e: { lngLat: { lat: number; lng: number } }) => void) => void)(
          "click",
          (e) => events.onMapClick!({ lat: e.lngLat.lat, lng: e.lngLat.lng })
        );
      }
    };

    if (// eslint-disable-next-line @typescript-eslint/no-explicit-any
(window as any).mapboxgl) {
      initMap();
    } else {
      const script = document.createElement("script");
      script.src = MAPBOX_JS;
      script.onload = initMap;
      document.head.appendChild(script);
    }

    return () => {
      if (mapRef.current) {
        (mapRef.current as Record<string, unknown> & { remove: () => void }).remove();
        mapRef.current = null;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div
      ref={containerRef}
      className={className || "w-full h-[400px] rounded-xl"}
    />
  );
}
