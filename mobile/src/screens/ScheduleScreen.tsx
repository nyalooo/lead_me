/**
 * Schedule screen — manage recurring and one-time commute schedules.
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  TextInput,
  RefreshControl,
} from 'react-native';

import { getSchedules, createSchedule, deleteSchedule } from '../lib/api';
import { colors, spacing, radius, fontSize } from '../lib/theme';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function ScheduleScreen() {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Form state
  const [selectedDays, setSelectedDays] = useState<string[]>(['mon', 'tue', 'wed', 'thu', 'fri']);
  const [departureTime, setDepartureTime] = useState('08:30');
  const [label, setLabel] = useState('');

  const loadSchedules = async () => {
    try {
      const data = await getSchedules();
      setSchedules(data);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadSchedules();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await loadSchedules();
    setRefreshing(false);
  };

  const toggleDay = (day: string) => {
    const d = day.toLowerCase();
    setSelectedDays((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]
    );
  };

  const handleCreate = async () => {
    if (selectedDays.length === 0) {
      Alert.alert('Error', 'Select at least one day');
      return;
    }
    try {
      await createSchedule({
        type: 'recurring',
        origin: { lat: 19.1136, lng: 72.8697 }, // Andheri (default)
        destination: { lat: 18.9398, lng: 72.8355 }, // CST (default)
        days: selectedDays,
        departure_time: departureTime,
        label: label || 'My Commute',
      });
      setShowForm(false);
      setLabel('');
      loadSchedules();
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const handleDelete = (id: string) => {
    Alert.alert('Delete Schedule', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          await deleteSchedule(id);
          loadSchedules();
        },
      },
    ]);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>Your Schedules</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowForm(!showForm)}
        >
          <Text style={styles.addButtonText}>{showForm ? 'Cancel' : '+ New'}</Text>
        </TouchableOpacity>
      </View>

      {/* Create form */}
      {showForm && (
        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Label (e.g., Office Commute)"
            value={label}
            onChangeText={setLabel}
          />
          <Text style={styles.formLabel}>Days</Text>
          <View style={styles.daysRow}>
            {DAYS.map((day) => (
              <TouchableOpacity
                key={day}
                style={[
                  styles.dayChip,
                  selectedDays.includes(day.toLowerCase()) && styles.dayChipActive,
                ]}
                onPress={() => toggleDay(day)}
              >
                <Text
                  style={[
                    styles.dayChipText,
                    selectedDays.includes(day.toLowerCase()) && styles.dayChipTextActive,
                  ]}
                >
                  {day}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.formLabel}>Departure Time</Text>
          <TextInput
            style={styles.input}
            value={departureTime}
            onChangeText={setDepartureTime}
            placeholder="08:30"
          />
          <TouchableOpacity style={styles.createButton} onPress={handleCreate}>
            <Text style={styles.createButtonText}>Create Schedule</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Schedule list */}
      {schedules.length === 0 && !showForm && (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No schedules yet</Text>
          <Text style={styles.emptySubtext}>
            Schedule your commutes to get routes pre-assigned
          </Text>
        </View>
      )}

      {schedules.map((s) => (
        <View key={s.id} style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardLabel}>{s.label || 'Commute'}</Text>
            <Text style={styles.cardType}>{s.type}</Text>
          </View>
          <Text style={styles.cardTime}>{s.departure_time}</Text>
          {s.days && (
            <View style={styles.cardDays}>
              {s.days.map((d: string) => (
                <View key={d} style={styles.cardDayChip}>
                  <Text style={styles.cardDayText}>{d.slice(0, 3)}</Text>
                </View>
              ))}
            </View>
          )}
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => handleDelete(s.id)}
          >
            <Text style={styles.deleteText}>Delete</Text>
          </TouchableOpacity>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.md,
  },
  title: { fontSize: fontSize.xl, fontWeight: '700', color: colors.text },
  addButton: {
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
  },
  addButtonText: { color: '#fff', fontWeight: '600' },
  form: {
    backgroundColor: colors.surface,
    margin: spacing.md,
    padding: spacing.lg,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  formLabel: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.xs,
    marginTop: spacing.md,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    fontSize: fontSize.md,
    color: colors.text,
  },
  daysRow: { flexDirection: 'row', gap: spacing.xs, flexWrap: 'wrap' },
  dayChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    borderWidth: 1,
    borderColor: colors.border,
  },
  dayChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  dayChipText: { fontSize: fontSize.sm, color: colors.text },
  dayChipTextActive: { color: '#fff', fontWeight: '600' },
  createButton: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
    marginTop: spacing.lg,
  },
  createButtonText: { color: '#fff', fontWeight: '600', fontSize: fontSize.md },
  empty: {
    alignItems: 'center',
    padding: spacing.xxl,
  },
  emptyText: { fontSize: fontSize.lg, fontWeight: '600', color: colors.textSecondary },
  emptySubtext: { fontSize: fontSize.sm, color: colors.textMuted, marginTop: spacing.xs, textAlign: 'center' },
  card: {
    backgroundColor: colors.surface,
    marginHorizontal: spacing.md,
    marginBottom: spacing.sm,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.xs },
  cardLabel: { fontSize: fontSize.md, fontWeight: '600', color: colors.text },
  cardType: {
    fontSize: fontSize.xs,
    color: colors.primary,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  cardTime: { fontSize: fontSize.lg, fontWeight: '700', color: colors.primary },
  cardDays: { flexDirection: 'row', gap: spacing.xs, marginTop: spacing.sm },
  cardDayChip: {
    backgroundColor: colors.primaryBg,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
  },
  cardDayText: { fontSize: fontSize.xs, color: colors.primary, fontWeight: '600' },
  deleteButton: { marginTop: spacing.md },
  deleteText: { color: colors.danger, fontSize: fontSize.sm },
});
