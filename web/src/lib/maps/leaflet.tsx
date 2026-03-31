/**
 * Leaflet + OpenStreetMap map provider.
 *
 * Free, no API key required. Good fallback for development.
 * Docs: https://leafletjs.com/
 */

"use client";

import { useEffect, useRef } from "react";
import type { MapProviderProps } from "./types";

const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
const LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

export default function LeafletMap({
  config,
  markers,
  events,
  className,
}: MapProviderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Load CSS
    if (!document.querySelector(`link[href="${LEAFLET_CSS}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = LEAFLET_CSS;
      document.head.appendChild(link);
    }

    const initMap = () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const L = (window as any).L as Record<string, unknown>;
      if (!L || !containerRef.current) return;

      const map = (L.map as (el: HTMLElement, opts: unknown) => Record<string, unknown>)(
        containerRef.current,
        { center: [config.center.lat, config.center.lng], zoom: config.zoom }
      );
      mapRef.current = map;

      // OpenStreetMap tiles (free, no key)
      (L.tileLayer as (url: string, opts: unknown) => Record<string, unknown>)(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        { attribution: "&copy; OpenStreetMap contributors", maxZoom: 19 }
      );

      // Add markers
      markers?.forEach((marker) => {
        (L.marker as (pos: [number, number]) => Record<string, unknown>)(
          [marker.position.lat, marker.position.lng]
        );
      });

      // Click handler
      if (events?.onMapClick) {
        (map.on as (event: string, cb: (e: { latlng: { lat: number; lng: number } }) => void) => void)(
          "click",
          (e) => events.onMapClick!({ lat: e.latlng.lat, lng: e.latlng.lng })
        );
      }
    };

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if ((window as any).L) {
      initMap();
    } else {
      const script = document.createElement("script");
      script.src = LEAFLET_JS;
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
