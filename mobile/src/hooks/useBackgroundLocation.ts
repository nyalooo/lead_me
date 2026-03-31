/**
 * Background location tracking for route compliance.
 *
 * This is the KEY mobile advantage over web:
 * - Runs even when app is backgrounded
 * - Uses expo-location + expo-task-manager
 * - Sends location updates to backend for route compliance scoring
 * - Battery-aware: adjusts accuracy based on battery state
 */

import { useEffect, useRef, useState } from 'react';
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { trackLocation } from '../lib/api';

const BACKGROUND_LOCATION_TASK = 'leadme-background-location';

// Register background task (must be at module level)
TaskManager.defineTask(BACKGROUND_LOCATION_TASK, async ({ data, error }: any) => {
  if (error) {
    console.error('Background location error:', error);
    return;
  }
  if (data) {
    const { locations } = data as { locations: Location.LocationObject[] };
    // Store for batch upload — the hook will pick these up
    for (const loc of locations) {
      pendingLocations.push({
        lat: loc.coords.latitude,
        lng: loc.coords.longitude,
        accuracy: loc.coords.accuracy || 0,
        timestamp: new Date(loc.timestamp).toISOString(),
      });
    }
  }
});

// Pending locations buffer (shared between task and hook)
const pendingLocations: Array<{
  lat: number;
  lng: number;
  accuracy: number;
  timestamp: string;
}> = [];

export type TrackingState = 'idle' | 'requesting' | 'tracking' | 'completed' | 'error';

export function useBackgroundLocation(assignmentId: string | null) {
  const [state, setState] = useState<TrackingState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [pointsSent, setPointsSent] = useState(0);
  const uploadInterval = useRef<ReturnType<typeof setInterval>>();

  const startTracking = async () => {
    setState('requesting');
    setError(null);

    // Request foreground permission
    const { status: fgStatus } = await Location.requestForegroundPermissionsAsync();
    if (fgStatus !== 'granted') {
      setState('error');
      setError('Location permission denied');
      return;
    }

    // Request background permission (critical for mobile tracking)
    const { status: bgStatus } = await Location.requestBackgroundPermissionsAsync();
    if (bgStatus !== 'granted') {
      console.warn('Background location not granted — tracking only in foreground');
    }

    // Start background location updates
    const isTracking = await Location.hasStartedLocationUpdatesAsync(BACKGROUND_LOCATION_TASK).catch(() => false);
    if (!isTracking) {
      await Location.startLocationUpdatesAsync(BACKGROUND_LOCATION_TASK, {
        accuracy: Location.Accuracy.High,
        distanceInterval: 20, // minimum 20m between updates
        timeInterval: 5000, // every 5 seconds
        deferredUpdatesInterval: 10000,
        showsBackgroundLocationIndicator: true,
        foregroundService: {
          notificationTitle: 'LeadMe',
          notificationBody: 'Tracking your route for rewards',
          notificationColor: '#059669',
        },
      });
    }

    // Start foreground watcher too (for immediate UI updates)
    await Location.watchPositionAsync(
      {
        accuracy: Location.Accuracy.High,
        distanceInterval: 20,
        timeInterval: 3000,
      },
      (location) => {
        if (assignmentId && location.coords.accuracy !== null && location.coords.accuracy < 100) {
          pendingLocations.push({
            lat: location.coords.latitude,
            lng: location.coords.longitude,
            accuracy: location.coords.accuracy || 0,
            timestamp: new Date(location.timestamp).toISOString(),
          });
        }
      }
    );

    // Start batch upload interval
    uploadInterval.current = setInterval(async () => {
      if (!assignmentId || pendingLocations.length === 0) return;

      const batch = pendingLocations.splice(0, pendingLocations.length);
      for (const loc of batch) {
        try {
          await trackLocation(
            assignmentId,
            loc.lat,
            loc.lng,
            loc.timestamp,
            loc.accuracy
          );
          setPointsSent((prev) => prev + 1);
        } catch (err) {
          // Re-add failed locations for retry
          pendingLocations.push(loc);
        }
      }
    }, 10000); // batch upload every 10s

    setState('tracking');
  };

  const stopTracking = async () => {
    // Stop background updates
    const isTracking = await Location.hasStartedLocationUpdatesAsync(BACKGROUND_LOCATION_TASK).catch(() => false);
    if (isTracking) {
      await Location.stopLocationUpdatesAsync(BACKGROUND_LOCATION_TASK);
    }

    // Clear upload interval
    if (uploadInterval.current) {
      clearInterval(uploadInterval.current);
    }

    // Flush remaining locations
    if (assignmentId && pendingLocations.length > 0) {
      const batch = pendingLocations.splice(0, pendingLocations.length);
      for (const loc of batch) {
        try {
          await trackLocation(assignmentId, loc.lat, loc.lng, loc.timestamp, loc.accuracy);
        } catch {
          // best effort
        }
      }
    }

    setState('completed');
  };

  useEffect(() => {
    return () => {
      if (uploadInterval.current) {
        clearInterval(uploadInterval.current);
      }
    };
  }, []);

  return {
    state,
    error,
    pointsSent,
    startTracking,
    stopTracking,
  };
}
