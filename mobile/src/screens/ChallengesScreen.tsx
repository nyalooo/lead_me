import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  StyleSheet,
} from 'react-native';
import { getChallenges, joinChallenge, claimChallengeReward } from '../lib/api';
import { colors, spacing, typography } from '../lib/theme';

type Challenge = {
  id: string;
  title: string;
  description: string;
  type: string;
  category: string;
  goal_type: string;
  goal_value: number;
  goal_area: string | null;
  reward_coins: number;
  reward_xrp: number;
  starts_at: string;
  ends_at: string;
  max_participants: number | null;
  participant_count: number;
  user_joined: boolean;
  user_progress: number;
  user_completed: boolean;
};

type Tab = 'active' | 'upcoming' | 'completed';

const GOAL_LABELS: Record<string, string> = {
  routes_count: 'routes',
  distance_km: 'km',
  peak_routes: 'peak routes',
  area_routes: 'area routes',
  streak_days: 'day streak',
};

const TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  weekly: { bg: '#DBEAFE', text: '#1D4ED8' },
  monthly: { bg: '#F3E8FF', text: '#7C3AED' },
  event: { bg: '#FEF3C7', text: '#B45309' },
  flash: { bg: '#FEE2E2', text: '#DC2626' },
};

export default function ChallengesScreen() {
  const [tab, setTab] = useState<Tab>('active');
  const [challenges, setChallenges] = useState<{
    active: Challenge[];
    upcoming: Challenge[];
    completed: Challenge[];
  }>({ active: [], upcoming: [], completed: [] });
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await getChallenges();
      setChallenges(data);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const handleJoin = async (id: string) => {
    try {
      const result = await joinChallenge(id);
      Alert.alert(result.joined ? 'Joined!' : 'Error', result.message);
      load();
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to join');
    }
  };

  const handleClaim = async (id: string) => {
    try {
      const result = await claimChallengeReward(id);
      if (result.claimed) {
        const parts = [];
        if (result.coins_earned) parts.push(`${result.coins_earned} coins`);
        if (result.xrp_earned) parts.push(`${result.xrp_earned} XRP`);
        Alert.alert('Reward Claimed!', parts.join(' + '));
      } else {
        Alert.alert('Error', result.message);
      }
      load();
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to claim');
    }
  };

  const current = challenges[tab];

  return (
    <View style={styles.container}>
      {/* Tabs */}
      <View style={styles.tabs}>
        {(['active', 'upcoming', 'completed'] as Tab[]).map((t) => (
          <TouchableOpacity
            key={t}
            style={[styles.tab, tab === t && styles.tabActive]}
            onPress={() => setTab(t)}
          >
            <Text style={[styles.tabText, tab === t && styles.tabTextActive]}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
              {challenges[t].length > 0 ? ` (${challenges[t].length})` : ''}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />}
      >
        {current.length === 0 && (
          <View style={styles.empty}>
            <Text style={styles.emptyText}>No {tab} challenges right now</Text>
          </View>
        )}

        {current.map((c) => (
          <ChallengeCard
            key={c.id}
            challenge={c}
            tab={tab}
            onJoin={() => handleJoin(c.id)}
            onClaim={() => handleClaim(c.id)}
          />
        ))}
      </ScrollView>
    </View>
  );
}

function ChallengeCard({
  challenge: c,
  tab,
  onJoin,
  onClaim,
}: {
  challenge: Challenge;
  tab: Tab;
  onJoin: () => void;
  onClaim: () => void;
}) {
  const progressPercent = c.goal_value > 0
    ? Math.min(100, Math.round((c.user_progress / c.goal_value) * 100))
    : 0;
  const goalLabel = GOAL_LABELS[c.goal_type] ?? c.goal_type;
  const typeColor = TYPE_COLORS[c.type] ?? { bg: '#F3F4F6', text: '#374151' };

  const dateStr = tab === 'upcoming'
    ? `Starts ${new Date(c.starts_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}`
    : tab === 'completed'
      ? `Ended ${new Date(c.ends_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}`
      : `Ends ${new Date(c.ends_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}`;

  return (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={[styles.typeBadge, { backgroundColor: typeColor.bg }]}>
          <Text style={[styles.typeBadgeText, { color: typeColor.text }]}>
            {c.type.toUpperCase()}
          </Text>
        </View>
        {c.goal_area && (
          <View style={styles.areaBadge}>
            <Text style={styles.areaBadgeText}>{c.goal_area}</Text>
          </View>
        )}
      </View>

      <Text style={styles.cardTitle}>{c.title}</Text>
      <Text style={styles.cardDesc}>{c.description}</Text>

      <View style={styles.meta}>
        <Text style={styles.metaText}>
          Goal: <Text style={styles.metaBold}>{c.goal_value} {goalLabel}</Text>
        </Text>
        <Text style={styles.metaText}>
          Reward:{' '}
          <Text style={styles.rewardText}>
            {c.reward_coins > 0 ? `${c.reward_coins} coins` : ''}
            {c.reward_coins > 0 && c.reward_xrp > 0 ? ' + ' : ''}
            {c.reward_xrp > 0 ? `${c.reward_xrp} XRP` : ''}
          </Text>
        </Text>
      </View>

      {c.user_joined && (
        <View style={styles.progressContainer}>
          <View style={styles.progressLabels}>
            <Text style={styles.progressText}>
              {c.user_progress}/{c.goal_value} {goalLabel}
            </Text>
            <Text style={styles.progressText}>{progressPercent}%</Text>
          </View>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${progressPercent}%` },
                c.user_completed && styles.progressComplete,
              ]}
            />
          </View>
        </View>
      )}

      <View style={styles.cardFooter}>
        <Text style={styles.footerText}>
          {c.participant_count} participant{c.participant_count !== 1 ? 's' : ''}
          {c.max_participants ? ` / ${c.max_participants}` : ''}
          {' · '}
          {dateStr}
        </Text>

        {tab === 'active' && !c.user_joined && (
          <TouchableOpacity style={styles.joinBtn} onPress={onJoin}>
            <Text style={styles.joinBtnText}>Join</Text>
          </TouchableOpacity>
        )}
        {tab === 'active' && c.user_joined && c.user_completed && (
          <TouchableOpacity style={styles.claimBtn} onPress={onClaim}>
            <Text style={styles.claimBtnText}>Claim</Text>
          </TouchableOpacity>
        )}
        {tab === 'active' && c.user_joined && !c.user_completed && (
          <View style={styles.inProgressBadge}>
            <Text style={styles.inProgressText}>In Progress</Text>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    gap: spacing.sm,
  },
  tab: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: 20,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  tabText: { fontSize: 13, fontWeight: '500', color: colors.textMuted },
  tabTextActive: { color: '#fff' },
  list: { padding: spacing.md, gap: spacing.md },
  empty: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.xl * 2,
    alignItems: 'center',
  },
  emptyText: { color: colors.textMuted, fontSize: 14 },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardHeader: { flexDirection: 'row', gap: spacing.xs, marginBottom: spacing.xs },
  typeBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  typeBadgeText: { fontSize: 10, fontWeight: '700' },
  areaBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
  },
  areaBadgeText: { fontSize: 10, fontWeight: '500', color: '#6B7280' },
  cardTitle: { fontSize: 17, fontWeight: '600', color: colors.text, marginBottom: 4 },
  cardDesc: { fontSize: 13, color: colors.textMuted, lineHeight: 18 },
  meta: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.sm,
  },
  metaText: { fontSize: 13, color: colors.textMuted },
  metaBold: { fontWeight: '600', color: colors.text },
  rewardText: { fontWeight: '600', color: colors.primary },
  progressContainer: { marginTop: spacing.sm },
  progressLabels: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  progressText: { fontSize: 11, color: colors.textMuted },
  progressBar: {
    height: 6,
    backgroundColor: '#F3F4F6',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#34D399',
    borderRadius: 3,
  },
  progressComplete: { backgroundColor: colors.primary },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
  },
  footerText: { fontSize: 11, color: '#9CA3AF', flex: 1 },
  joinBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  joinBtnText: { color: '#fff', fontSize: 13, fontWeight: '600' },
  claimBtn: {
    backgroundColor: '#F59E0B',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  claimBtnText: { color: '#fff', fontSize: 13, fontWeight: '600' },
  inProgressBadge: {
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  inProgressText: { color: colors.primary, fontSize: 12, fontWeight: '500' },
});
