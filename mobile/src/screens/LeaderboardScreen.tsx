/**
 * Leaderboard screen — area-based rankings.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from 'react-native';

import { getLeaderboard } from '../lib/api';
import { colors, spacing, radius, fontSize } from '../lib/theme';

const AREAS = ['mumbai', 'andheri', 'bandra', 'thane', 'navi mumbai'];

export default function LeaderboardScreen() {
  const [area, setArea] = useState('mumbai');
  const [data, setData] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const result = await getLeaderboard(area);
      setData(result);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadData();
  }, [area]);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const getMedal = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const tierColor = (tier: string) =>
    (colors as any)[tier] || colors.textSecondary;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />}
    >
      {/* Area filter */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterRow}
        contentContainerStyle={styles.filterContent}
      >
        {AREAS.map((a) => (
          <TouchableOpacity
            key={a}
            style={[styles.filterChip, area === a && styles.filterChipActive]}
            onPress={() => setArea(a)}
          >
            <Text style={[styles.filterText, area === a && styles.filterTextActive]}>
              {a.charAt(0).toUpperCase() + a.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* User's rank */}
      {data?.user_rank && (
        <View style={styles.userRank}>
          <Text style={styles.userRankText}>Your rank: #{data.user_rank}</Text>
          <Text style={styles.participants}>of {data.total_participants} commuters</Text>
        </View>
      )}

      {/* Rankings */}
      {data?.rankings?.map((entry: any) => (
        <View key={entry.rank} style={styles.rankCard}>
          <Text style={styles.rankMedal}>{getMedal(entry.rank)}</Text>
          <View style={styles.rankInfo}>
            <Text style={styles.rankName}>{entry.display_name}</Text>
            <View style={styles.rankMeta}>
              <Text style={[styles.rankTier, { color: tierColor(entry.tier) }]}>
                {entry.tier.toUpperCase()}
              </Text>
            </View>
          </View>
          <View style={styles.rankCoins}>
            <Text style={styles.rankCoinsValue}>{entry.coins_earned.toLocaleString()}</Text>
            <Text style={styles.rankCoinsLabel}>coins</Text>
          </View>
        </View>
      ))}

      {(!data?.rankings || data.rankings.length === 0) && (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No rankings yet</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  filterRow: { marginTop: spacing.md },
  filterContent: { paddingHorizontal: spacing.md, gap: spacing.sm },
  filterChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterText: { fontSize: fontSize.sm, color: colors.text },
  filterTextActive: { color: '#fff', fontWeight: '600' },
  userRank: {
    backgroundColor: colors.primaryBg,
    margin: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  userRankText: { fontSize: fontSize.lg, fontWeight: '700', color: colors.primary },
  participants: { fontSize: fontSize.sm, color: colors.textSecondary },
  rankCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    marginHorizontal: spacing.md,
    marginBottom: spacing.sm,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  rankMedal: { fontSize: fontSize.xl, width: 40, textAlign: 'center' },
  rankInfo: { flex: 1, marginLeft: spacing.sm },
  rankName: { fontSize: fontSize.md, fontWeight: '600', color: colors.text },
  rankMeta: { flexDirection: 'row', gap: spacing.sm, marginTop: 2 },
  rankTier: { fontSize: fontSize.xs, fontWeight: '700' },
  rankCoins: { alignItems: 'flex-end' },
  rankCoinsValue: { fontSize: fontSize.lg, fontWeight: '700', color: colors.primary },
  rankCoinsLabel: { fontSize: fontSize.xs, color: colors.textSecondary },
  empty: { alignItems: 'center', padding: spacing.xxl },
  emptyText: { fontSize: fontSize.md, color: colors.textSecondary },
});
