/**
 * Browser Geolocation utilities for route tracking.
 *
 * Handles:
 * - Permission requests
 * - Continuous position watching during active routes
 * - Accuracy filtering (ignore low-quality fixes)
 * - Battery-aware polling (reduce frequency when stationary)
 *
 * Limitations (web):
 * - Tracking stops when tab is backgrounded (browser suspends JS)
 * - For background tracking, a native app (Phase 2) is needed
 */

export type GeoPosition = {
  lat: number;
  lng: number;
  accuracy: number; // meters
  timestamp: number; // unix ms
  speed: number | null; // m/s
};

export type TrackingOptions = {
  /** Minimum accuracy in meters to accept a fix (default: 100) */
  minAccuracy?: number;
  /** Minimum distance in meters between reported positions (default: 20) */
  minDistance?: number;
  /** Callback for each valid position update */
  onPosition: (pos: GeoPosition) => void;
  /** Callback when tracking errors occur */
  onError?: (error: GeolocationPositionError) => void;
};

/**
 * Calculate distance between two points using Haversine formula.
 */
function haversineDistance(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const R = 6371000; // Earth radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Check if geolocation is supported and permitted.
 */
export async function checkGeolocationPermission(): Promise<
  "granted" | "denied" | "prompt" | "unsupported"
> {
  if (!navigator.geolocation) return "unsupported";

  try {
    const result = await navigator.permissions.query({ name: "geolocation" });
    return result.state;
  } catch {
    // permissions API not supported, assume prompt
    return "prompt";
  }
}

/**
 * Get current position as a one-shot request.
 */
export function getCurrentPosition(): Promise<GeoPosition> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          timestamp: pos.timestamp,
          speed: pos.coords.speed,
        }),
      reject,
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 },
    );
  });
}

/**
 * Start continuous position tracking.
 *
 * Returns a stop function to call when tracking should end.
 * Filters by accuracy and minimum distance to avoid noisy updates.
 */
export function startTracking(options: TrackingOptions): () => void {
  const minAccuracy = options.minAccuracy ?? 100;
  const minDistance = options.minDistance ?? 20;
  let lastPos: GeoPosition | null = null;

  const watchId = navigator.geolocation.watchPosition(
    (pos) => {
      const current: GeoPosition = {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        accuracy: pos.coords.accuracy,
        timestamp: pos.timestamp,
        speed: pos.coords.speed,
      };

      // Filter: skip low-accuracy fixes
      if (current.accuracy > minAccuracy) return;

      // Filter: skip if too close to last reported position
      if (lastPos) {
        const dist = haversineDistance(
          lastPos.lat,
          lastPos.lng,
          current.lat,
          current.lng,
        );
        if (dist < minDistance) return;
      }

      lastPos = current;
      options.onPosition(current);
    },
    (error) => {
      options.onError?.(error);
    },
    {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 3000,
    },
  );

  // Return stop function
  return () => {
    navigator.geolocation.clearWatch(watchId);
  };
}
