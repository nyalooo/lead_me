/**
 * Hook for tracking an active route assignment.
 *
 * Manages the lifecycle:
 * 1. Request geolocation permission
 * 2. Start GPS tracking
 * 3. Send location updates to backend
 * 4. Complete the route when user finishes
 *
 * Usage:
 *   const { isTracking, progress, start, stop, complete } = useRouteTracking(assignmentId);
 */

"use client";

import { useCallback, useRef, useState } from "react";
import { trackLocation, completeRoute } from "@/lib/api";
import { getToken } from "@/lib/auth";
import {
  type GeoPosition,
  checkGeolocationPermission,
  startTracking,
} from "@/lib/geolocation";

export type TrackingState = "idle" | "requesting_permission" | "tracking" | "completed" | "error";

export type CompletionResult = {
  compliant: boolean;
  complianceScore: number;
  coinsEarned: number;
  streakDay: number;
  badgesEarned: string[];
};

export function useRouteTracking(assignmentId: string | null) {
  const [state, setState] = useState<TrackingState>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompletionResult | null>(null);
  const [positionCount, setPositionCount] = useState(0);
  const stopRef = useRef<(() => void) | null>(null);

  const handlePosition = useCallback(
    async (pos: GeoPosition) => {
      if (!assignmentId) return;
      const token = getToken();
      if (!token) return;

      try {
        const res = await trackLocation(
          assignmentId,
          pos.lat,
          pos.lng,
          new Date(pos.timestamp).toISOString(),
          token,
        );
        setProgress(res.progress_percent);
        setPositionCount((c) => c + 1);
      } catch (err) {
        console.error("Track location failed:", err);
      }
    },
    [assignmentId],
  );

  const start = useCallback(async () => {
    if (!assignmentId) {
      setError("No active assignment");
      return;
    }

    setState("requesting_permission");
    const permission = await checkGeolocationPermission();

    if (permission === "unsupported") {
      setError("Geolocation is not supported by your browser");
      setState("error");
      return;
    }

    if (permission === "denied") {
      setError("Location permission denied. Please enable it in browser settings.");
      setState("error");
      return;
    }

    setState("tracking");
    setError(null);
    setPositionCount(0);

    const stopFn = startTracking({
      minAccuracy: 100,
      minDistance: 20,
      onPosition: handlePosition,
      onError: (geoError) => {
        if (geoError.code === geoError.PERMISSION_DENIED) {
          setError("Location permission denied");
          setState("error");
        }
      },
    });
    stopRef.current = stopFn;
  }, [assignmentId, handlePosition]);

  const stop = useCallback(() => {
    stopRef.current?.();
    stopRef.current = null;
    setState("idle");
  }, []);

  const complete = useCallback(async () => {
    // Stop tracking first
    stopRef.current?.();
    stopRef.current = null;

    if (!assignmentId) return;
    const token = getToken();
    if (!token) return;

    try {
      const res = await completeRoute(assignmentId, token);
      setResult({
        compliant: res.compliant,
        complianceScore: res.compliance_score,
        coinsEarned: res.coins_earned,
        streakDay: res.streak_day,
        badgesEarned: res.badges_earned,
      });
      setState("completed");
    } catch (err) {
      setError("Failed to complete route");
      setState("error");
    }
  }, [assignmentId]);

  return {
    state,
    isTracking: state === "tracking",
    progress,
    positionCount,
    error,
    result,
    start,
    stop,
    complete,
  };
}
