/**
 * Dashboard — main screen after login.
 *
 * Shows: stats cards, quick route assignment, GPS tracking controls.
 * On mobile we have BACKGROUND GPS — the key advantage over web.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
} from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';

import { getBalance, getStreaks, assignRoute, completeRoute } from '../lib/api';
import { useBackgroundLocation } from '../hooks/useBackgroundLocation';
import { colors, spacing, radius, fontSize } from '../lib/theme';

// Mumbai center
const MUMBAI = { latitude: 19.076, longitude: 72.8777, latitudeDelta: 0.1, longitudeDelta: 0.1 };

// Quick routes for MVP
const QUICK_ROUTES = [
  { label: 'Andheri → CST', origin: { lat: 19.1136, lng: 72.8697 }, dest: { lat: 18.9398, lng: 72.8355 } },
  { label: 'Bandra → Thane', origin: { lat: 19.0596, lng: 72.8295 }, dest: { lat: 19.2183, lng: 72.9781 } },
  { label: 'Borivali → Dadar', origin: { lat: 19.2307, lng: 72.8567 }, dest: { lat: 19.0176, lng: 72.8423 } },
];

export default function DashboardScreen() {
  const [balance, setBalance] = useState<any>(null);
  const [streak, setStreak] = useState<any>(null);
  const [assignment, setAssignment] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  const { state: trackingState, pointsSent, startTracking, stopTracking } = useBackgroundLocation(
    assignment?.assignment_id
  );

  const loadData = async () => {
    try {
      const [b, s] = await Promise.all([getBalance(), getStreaks()]);
      setBalance(b);
      setStreak(s);
    } catch {
      // not logged in or network error
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleAssignRoute = async (route: typeof QUICK_ROUTES[0]) => {
    try {
      const result = await assignRoute(route.origin, route.dest);
      setAssignment(result);
      Alert.alert('Route Assigned', `Estimated reward: ${result.estimated_reward.total_coins} coins`);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const handleStartTracking = async () => {
    await startTracking();
  };

  const handleComplete = async () => {
    if (!assignment) return;
    await stopTracking();
    try {
      const result = await completeRoute(assignment.assignment_id);
      Alert.alert(
        result.compliant ? 'Route Completed!' : 'Route Completed',
        result.compliant
          ? `You earned ${result.coins_earned} Route Coins! Streak: ${result.streak_day} days`
          : 'Route was not followed. Keep trying for rewards!',
      );
      setAssignment(null);
      loadData();
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />}
    >
      {/* Stats Cards */}
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{balance?.route_coins ?? '—'}</Text>
          <Text style={styles.statLabel}>Route Coins</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{streak?.current_streak ?? '—'}</Text>
          <Text style={styles.statLabel}>Day Streak</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{balance?.tier ?? '—'}</Text>
          <Text style={styles.statLabel}>Tier</Text>
        </View>
      </View>

      {/* Streak multiplier */}
      {streak && streak.multiplier > 1 && (
        <View style={styles.streakBanner}>
          <Text style={styles.streakText}>
            {streak.multiplier}x streak multiplier active!
          </Text>
        </View>
      )}

      {/* Map */}
      <View style={styles.mapContainer}>
        <MapView
          style={styles.map}
          initialRegion={MUMBAI}
          provider={PROVIDER_GOOGLE}
          showsUserLocation
          showsMyLocationButton
        >
          {assignment && (
            <Marker
              coordinate={{
                latitude: 18.9398,
                longitude: 72.8355,
              }}
              title="Destination"
            />
          )}
        </MapView>
      </View>

      {/* Quick Routes */}
      {!assignment && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Routes</Text>
          {QUICK_ROUTES.map((route) => (
            <TouchableOpacity
              key={route.label}
              style={styles.routeCard}
              onPress={() => handleAssignRoute(route)}
            >
              <Text style={styles.routeLabel}>{route.label}</Text>
              <Text style={styles.routeArrow}>→</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Active Assignment */}
      {assignment && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Active Route</Text>
          <View style={styles.activeCard}>
            <Text style={styles.activeRoute}>
              {assignment.assigned_route.distance_km.toFixed(1)} km • ~{assignment.assigned_route.estimated_duration_min.toFixed(0)} min
            </Text>
            <Text style={styles.activeReward}>
              Est. reward: {assignment.estimated_reward.total_coins} coins
            </Text>

            {trackingState === 'idle' && (
              <TouchableOpacity style={styles.button} onPress={handleStartTracking}>
                <Text style={styles.buttonText}>Start GPS Tracking</Text>
              </TouchableOpacity>
            )}

            {trackingState === 'tracking' && (
              <>
                <View style={styles.trackingBanner}>
                  <Text style={styles.trackingText}>
                    GPS Tracking Active • {pointsSent} points sent
                  </Text>
                  <Text style={styles.trackingSubtext}>
                    Background tracking enabled
                  </Text>
                </View>
                <TouchableOpacity
                  style={[styles.button, { backgroundColor: colors.primaryDark }]}
                  onPress={handleComplete}
                >
                  <Text style={styles.buttonText}>Complete Route</Text>
                </TouchableOpacity>
              </>
            )}

            {trackingState === 'requesting' && (
              <Text style={styles.trackingText}>Requesting permissions...</Text>
            )}

            {trackingState === 'error' && (
              <Text style={[styles.trackingText, { color: colors.danger }]}>
                Location permission denied
              </Text>
            )}
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  statsRow: {
    flexDirection: 'row',
    padding: spacing.md,
    gap: spacing.sm,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  statValue: {
    fontSize: fontSize.xl,
    fontWeight: '700',
    color: colors.primary,
  },
  statLabel: {
    fontSize: fontSize.xs,
    color: colors.textSecondary,
    marginTop: 2,
  },
  streakBanner: {
    backgroundColor: '#fef3c7',
    marginHorizontal: spacing.md,
    padding: spacing.sm,
    borderRadius: radius.sm,
    alignItems: 'center',
  },
  streakText: {
    color: '#92400e',
    fontWeight: '600',
  },
  mapContainer: {
    height: 250,
    margin: spacing.md,
    borderRadius: radius.lg,
    overflow: 'hidden',
  },
  map: { flex: 1 },
  section: {
    padding: spacing.md,
  },
  sectionTitle: {
    fontSize: fontSize.lg,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  routeCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  routeLabel: {
    fontSize: fontSize.md,
    fontWeight: '500',
    color: colors.text,
  },
  routeArrow: {
    fontSize: fontSize.lg,
    color: colors.primary,
  },
  activeCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 2,
    borderColor: colors.primary,
  },
  activeRoute: {
    fontSize: fontSize.md,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  activeReward: {
    fontSize: fontSize.sm,
    color: colors.primary,
    fontWeight: '600',
    marginBottom: spacing.md,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  buttonText: {
    color: '#fff',
    fontSize: fontSize.md,
    fontWeight: '600',
  },
  trackingBanner: {
    backgroundColor: colors.primaryBg,
    padding: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  trackingText: {
    color: colors.primary,
    fontWeight: '600',
    fontSize: fontSize.sm,
  },
  trackingSubtext: {
    color: colors.textSecondary,
    fontSize: fontSize.xs,
    marginTop: 2,
  },
});
