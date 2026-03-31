/**
 * Profile screen — user info, stats, badges, and settings.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  Alert,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

import { getProfile, updateProfile, getBadges, getUserStats } from '../lib/api';
import { clearAuth } from '../lib/auth';
import { colors, spacing, radius, fontSize } from '../lib/theme';

export default function ProfileScreen() {
  const navigation = useNavigation<any>();
  const [profile, setProfile] = useState<any>(null);
  const [badges, setBadges] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [area, setArea] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [p, b, s] = await Promise.all([getProfile(), getBadges(), getUserStats()]);
      setProfile(p);
      setBadges(b);
      setStats(s);
      setDisplayName(p.display_name || '');
      setArea(p.area || '');
    } catch {
      // ignore
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

  const handleSave = async () => {
    try {
      await updateProfile({ display_name: displayName, area });
      setEditing(false);
      loadData();
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: async () => {
          await clearAuth();
          navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
        },
      },
    ]);
  };

  const tierColor = (tier: string) =>
    (colors as any)[tier] || colors.textSecondary;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />}
    >
      {/* Profile Card */}
      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {profile?.display_name?.charAt(0)?.toUpperCase() || '?'}
          </Text>
        </View>
        {editing ? (
          <View style={styles.editForm}>
            <TextInput
              style={styles.input}
              value={displayName}
              onChangeText={setDisplayName}
              placeholder="Display name"
            />
            <TextInput
              style={styles.input}
              value={area}
              onChangeText={setArea}
              placeholder="Area (e.g., Andheri)"
            />
            <View style={styles.editButtons}>
              <TouchableOpacity
                style={[styles.editBtn, { backgroundColor: colors.border }]}
                onPress={() => setEditing(false)}
              >
                <Text>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.editBtn} onPress={handleSave}>
                <Text style={{ color: '#fff', fontWeight: '600' }}>Save</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <>
            <Text style={styles.name}>{profile?.display_name || 'Commuter'}</Text>
            <Text style={styles.phone}>{profile?.phone}</Text>
            <Text style={[styles.tier, { color: tierColor(profile?.tier) }]}>
              {profile?.tier?.toUpperCase()} TIER
            </Text>
            <TouchableOpacity onPress={() => setEditing(true)}>
              <Text style={styles.editLink}>Edit Profile</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{profile?.total_routes ?? 0}</Text>
          <Text style={styles.statLabel}>Routes</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{profile?.total_coins ?? 0}</Text>
          <Text style={styles.statLabel}>Coins</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>
            {((profile?.compliance_rate ?? 0) * 100).toFixed(0)}%
          </Text>
          <Text style={styles.statLabel}>Compliance</Text>
        </View>
      </View>

      {/* Badges */}
      {badges && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Badges ({badges.earned?.length || 0})
          </Text>
          {badges.earned?.length > 0 ? (
            <View style={styles.badgeGrid}>
              {badges.earned.map((b: any) => (
                <View key={b.id} style={styles.badgeCard}>
                  <Text style={styles.badgeName}>{b.name}</Text>
                  <Text style={styles.badgeDesc}>{b.description}</Text>
                </View>
              ))}
            </View>
          ) : (
            <Text style={styles.emptyText}>Complete routes to earn badges!</Text>
          )}

          {badges.available?.length > 0 && (
            <>
              <Text style={[styles.sectionTitle, { marginTop: spacing.md }]}>
                In Progress
              </Text>
              {badges.available.map((b: any) => (
                <View key={b.id} style={styles.progressCard}>
                  <View style={styles.progressHeader}>
                    <Text style={styles.progressName}>{b.name}</Text>
                    <Text style={styles.progressCount}>
                      {b.progress.current}/{b.progress.target}
                    </Text>
                  </View>
                  <View style={styles.progressBar}>
                    <View
                      style={[
                        styles.progressFill,
                        { width: `${Math.min(100, (b.progress.current / b.progress.target) * 100)}%` },
                      ]}
                    />
                  </View>
                </View>
              ))}
            </>
          )}
        </View>
      )}

      {/* Logout */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>

      <View style={{ height: spacing.xxl }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  profileCard: {
    backgroundColor: colors.surface,
    margin: spacing.md,
    padding: spacing.lg,
    borderRadius: radius.lg,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  avatarText: { color: '#fff', fontSize: fontSize.xxl, fontWeight: '700' },
  name: { fontSize: fontSize.xl, fontWeight: '700', color: colors.text },
  phone: { fontSize: fontSize.sm, color: colors.textSecondary, marginTop: 2 },
  tier: { fontSize: fontSize.sm, fontWeight: '700', marginTop: spacing.xs },
  editLink: { color: colors.primary, fontSize: fontSize.sm, marginTop: spacing.sm },
  editForm: { width: '100%' },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    fontSize: fontSize.md,
    marginBottom: spacing.sm,
    color: colors.text,
  },
  editButtons: { flexDirection: 'row', gap: spacing.sm },
  editBtn: {
    flex: 1,
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.sm,
    alignItems: 'center',
  },
  statsGrid: {
    flexDirection: 'row',
    marginHorizontal: spacing.md,
    gap: spacing.sm,
  },
  statItem: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  statValue: { fontSize: fontSize.xl, fontWeight: '700', color: colors.primary },
  statLabel: { fontSize: fontSize.xs, color: colors.textSecondary, marginTop: 2 },
  section: { padding: spacing.md },
  sectionTitle: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text, marginBottom: spacing.sm },
  badgeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  badgeCard: {
    backgroundColor: colors.primaryBg,
    borderRadius: radius.md,
    padding: spacing.md,
    width: '48%',
  },
  badgeName: { fontSize: fontSize.sm, fontWeight: '700', color: colors.primary },
  badgeDesc: { fontSize: fontSize.xs, color: colors.textSecondary, marginTop: 2 },
  emptyText: { color: colors.textSecondary, fontSize: fontSize.sm },
  progressCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  progressName: { fontSize: fontSize.sm, fontWeight: '600', color: colors.text },
  progressCount: { fontSize: fontSize.sm, color: colors.primary, fontWeight: '600' },
  progressBar: {
    height: 6,
    backgroundColor: colors.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 3,
  },
  logoutButton: {
    marginHorizontal: spacing.md,
    marginTop: spacing.lg,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.danger,
    alignItems: 'center',
  },
  logoutText: { color: colors.danger, fontWeight: '600' },
});
