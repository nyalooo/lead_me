/**
 * Cashout screen — convert Route Coins to crypto.
 *
 * Shows: wallet management, cashout estimate, cashout history.
 * Multi-crypto ready (XRP active, SOL/ETH coming soon).
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

import {
  getBalance,
  getSupportedCryptos,
  getWallets,
  linkWallet,
  estimateCashout,
  doCashout,
  getCashoutHistory,
} from '../lib/api';
import { colors, spacing, radius, fontSize } from '../lib/theme';

export default function CashoutScreen() {
  const [balance, setBalance] = useState<any>(null);
  const [cryptos, setCryptos] = useState<any>(null);
  const [wallets, setWallets] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  // Cashout form
  const [coinsInput, setCoinsInput] = useState('');
  const [selectedCurrency, setSelectedCurrency] = useState('XRP');
  const [estimate, setEstimate] = useState<any>(null);

  // Wallet form
  const [showWalletForm, setShowWalletForm] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');

  const loadData = async () => {
    try {
      const [b, c, w, h] = await Promise.all([
        getBalance(),
        getSupportedCryptos(),
        getWallets(),
        getCashoutHistory(),
      ]);
      setBalance(b);
      setCryptos(c);
      setWallets(w.wallets || []);
      setHistory(h.cashouts || []);
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

  const handleEstimate = async () => {
    const coins = parseInt(coinsInput);
    if (!coins || coins <= 0) return;
    try {
      const est = await estimateCashout(coins, selectedCurrency);
      setEstimate(est);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const handleCashout = async () => {
    if (!estimate?.eligible) {
      Alert.alert('Not Eligible', estimate?.reason || 'Cannot cash out');
      return;
    }
    Alert.alert(
      'Confirm Cashout',
      `Convert ${estimate.coins_amount} coins to ${estimate.crypto_amount} ${selectedCurrency}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          onPress: async () => {
            try {
              const result = await doCashout(estimate.coins_amount, selectedCurrency);
              Alert.alert(
                result.status === 'completed' ? 'Cashout Complete!' : 'Cashout Processing',
                result.status === 'completed'
                  ? `${result.crypto_amount} ${result.currency} sent to your wallet`
                  : 'Your cashout is being processed',
              );
              setCoinsInput('');
              setEstimate(null);
              loadData();
            } catch (err: any) {
              Alert.alert('Error', err.message);
            }
          },
        },
      ]
    );
  };

  const handleLinkWallet = async () => {
    if (!walletAddress) return;
    try {
      await linkWallet(selectedCurrency, walletAddress);
      setShowWalletForm(false);
      setWalletAddress('');
      loadData();
      Alert.alert('Wallet Linked', `${selectedCurrency} wallet added successfully`);
    } catch (err: any) {
      Alert.alert('Error', err.message);
    }
  };

  const hasWallet = wallets.some((w) => w.currency === selectedCurrency);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />}
    >
      {/* Balance */}
      <View style={styles.balanceCard}>
        <Text style={styles.balanceLabel}>Available Balance</Text>
        <Text style={styles.balanceValue}>{balance?.route_coins?.toLocaleString() ?? '—'}</Text>
        <Text style={styles.balanceSub}>Route Coins</Text>
        <Text style={styles.xrpEquiv}>
          ≈ {balance?.xrp_equivalent?.toFixed(4) ?? '—'} XRP
        </Text>
        {balance?.tier && balance.tier !== 'rookie' && (
          <Text style={styles.tierBonus}>
            {balance.tier.toUpperCase()} tier: {balance.tier_bonus_rate}x cashout bonus
          </Text>
        )}
      </View>

      {/* Supported Cryptos */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Select Currency</Text>
        <View style={styles.cryptoRow}>
          {cryptos?.providers?.map((p: any) => (
            <TouchableOpacity
              key={p.name}
              style={[
                styles.cryptoChip,
                selectedCurrency === p.currency && styles.cryptoChipActive,
                p.status === 'coming_soon' && styles.cryptoChipDisabled,
              ]}
              onPress={() => p.status === 'active' && setSelectedCurrency(p.currency)}
              disabled={p.status === 'coming_soon'}
            >
              <Text
                style={[
                  styles.cryptoText,
                  selectedCurrency === p.currency && styles.cryptoTextActive,
                ]}
              >
                {p.currency}
              </Text>
              {p.status === 'coming_soon' && (
                <Text style={styles.comingSoon}>Soon</Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Wallet */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{selectedCurrency} Wallet</Text>
        {hasWallet ? (
          <View style={styles.walletCard}>
            <Text style={styles.walletAddress}>
              {wallets.find((w) => w.currency === selectedCurrency)?.address}
            </Text>
            <Text style={styles.walletStatus}>Linked</Text>
          </View>
        ) : showWalletForm ? (
          <View style={styles.walletForm}>
            <TextInput
              style={styles.input}
              placeholder={`Enter ${selectedCurrency} wallet address`}
              value={walletAddress}
              onChangeText={setWalletAddress}
              autoCapitalize="none"
            />
            <View style={styles.walletFormButtons}>
              <TouchableOpacity
                style={[styles.smallButton, { backgroundColor: colors.border }]}
                onPress={() => setShowWalletForm(false)}
              >
                <Text style={styles.smallButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.smallButton} onPress={handleLinkWallet}>
                <Text style={[styles.smallButtonText, { color: '#fff' }]}>Link</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <TouchableOpacity
            style={styles.linkButton}
            onPress={() => setShowWalletForm(true)}
          >
            <Text style={styles.linkButtonText}>+ Link {selectedCurrency} Wallet</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Cashout Form */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Cash Out</Text>
        <View style={styles.cashoutForm}>
          <TextInput
            style={styles.input}
            placeholder="Enter coins amount"
            value={coinsInput}
            onChangeText={(text) => {
              setCoinsInput(text);
              setEstimate(null);
            }}
            keyboardType="number-pad"
          />
          <TouchableOpacity
            style={styles.estimateButton}
            onPress={handleEstimate}
          >
            <Text style={styles.estimateButtonText}>Estimate</Text>
          </TouchableOpacity>

          {estimate && (
            <View style={styles.estimateCard}>
              <View style={styles.estimateRow}>
                <Text style={styles.estimateLabel}>You send</Text>
                <Text style={styles.estimateValue}>{estimate.coins_amount} coins</Text>
              </View>
              <View style={styles.estimateRow}>
                <Text style={styles.estimateLabel}>You receive</Text>
                <Text style={[styles.estimateValue, { color: colors.primary }]}>
                  {estimate.crypto_amount} {estimate.currency}
                </Text>
              </View>
              {estimate.tier_bonus > 1 && (
                <View style={styles.estimateRow}>
                  <Text style={styles.estimateLabel}>Tier bonus</Text>
                  <Text style={styles.estimateValue}>{estimate.tier_bonus}x</Text>
                </View>
              )}
              <TouchableOpacity
                style={[
                  styles.cashoutButton,
                  !estimate.eligible && styles.cashoutButtonDisabled,
                ]}
                onPress={handleCashout}
                disabled={!estimate.eligible}
              >
                <Text style={styles.cashoutButtonText}>
                  {estimate.eligible ? 'Cash Out Now' : estimate.reason}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>

      {/* History */}
      {history.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Cashout History</Text>
          {history.map((h: any) => (
            <View key={h.id} style={styles.historyCard}>
              <View style={styles.historyRow}>
                <Text style={styles.historyAmount}>
                  {h.crypto_amount} {h.currency}
                </Text>
                <Text
                  style={[
                    styles.historyStatus,
                    h.status === 'completed' && { color: colors.success },
                    h.status === 'failed' && { color: colors.danger },
                  ]}
                >
                  {h.status}
                </Text>
              </View>
              <Text style={styles.historyCoins}>{h.coins_amount} coins</Text>
              <Text style={styles.historyDate}>
                {new Date(h.created_at).toLocaleDateString()}
              </Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  balanceCard: {
    backgroundColor: colors.primary,
    margin: spacing.md,
    padding: spacing.lg,
    borderRadius: radius.lg,
    alignItems: 'center',
  },
  balanceLabel: { color: 'rgba(255,255,255,0.7)', fontSize: fontSize.sm },
  balanceValue: { color: '#fff', fontSize: fontSize.hero, fontWeight: '800', marginTop: spacing.xs },
  balanceSub: { color: 'rgba(255,255,255,0.7)', fontSize: fontSize.sm },
  xrpEquiv: { color: '#fff', fontSize: fontSize.md, fontWeight: '600', marginTop: spacing.sm },
  tierBonus: { color: '#fef3c7', fontSize: fontSize.xs, marginTop: spacing.xs },
  section: { padding: spacing.md },
  sectionTitle: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text, marginBottom: spacing.sm },
  cryptoRow: { flexDirection: 'row', gap: spacing.sm },
  cryptoChip: {
    flex: 1,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
  },
  cryptoChipActive: { borderColor: colors.primary, backgroundColor: colors.primaryBg },
  cryptoChipDisabled: { opacity: 0.5 },
  cryptoText: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  cryptoTextActive: { color: colors.primary },
  comingSoon: { fontSize: fontSize.xs, color: colors.textMuted },
  walletCard: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  walletAddress: { fontSize: fontSize.sm, color: colors.text, flex: 1, marginRight: spacing.sm },
  walletStatus: { color: colors.success, fontWeight: '600', fontSize: fontSize.sm },
  walletForm: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  walletFormButtons: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  smallButton: {
    flex: 1,
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.sm,
    alignItems: 'center',
  },
  smallButtonText: { fontWeight: '600', fontSize: fontSize.sm },
  linkButton: {
    borderWidth: 2,
    borderColor: colors.primary,
    borderStyle: 'dashed',
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  linkButtonText: { color: colors.primary, fontWeight: '600' },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    fontSize: fontSize.md,
    color: colors.text,
  },
  cashoutForm: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  estimateButton: {
    backgroundColor: colors.primaryLight,
    borderRadius: radius.md,
    padding: spacing.sm,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  estimateButtonText: { color: '#fff', fontWeight: '600' },
  estimateCard: {
    marginTop: spacing.md,
    padding: spacing.md,
    backgroundColor: colors.primaryBg,
    borderRadius: radius.md,
  },
  estimateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  estimateLabel: { color: colors.textSecondary, fontSize: fontSize.sm },
  estimateValue: { fontWeight: '700', fontSize: fontSize.sm, color: colors.text },
  cashoutButton: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
    marginTop: spacing.md,
  },
  cashoutButtonDisabled: { backgroundColor: colors.textMuted },
  cashoutButtonText: { color: '#fff', fontWeight: '700', fontSize: fontSize.md },
  historyCard: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.sm,
  },
  historyRow: { flexDirection: 'row', justifyContent: 'space-between' },
  historyAmount: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  historyStatus: { fontSize: fontSize.sm, fontWeight: '600', textTransform: 'uppercase' },
  historyCoins: { fontSize: fontSize.sm, color: colors.textSecondary, marginTop: 2 },
  historyDate: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },
});
