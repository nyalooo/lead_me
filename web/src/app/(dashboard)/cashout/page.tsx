"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/lib/auth";
import {
  getBalance,
  getSupportedCryptos,
  getWallets,
  linkWallet,
  deleteWallet,
  estimateCashout,
  doCashout,
  getCashoutHistory,
} from "@/lib/api";

type Balance = {
  route_coins: number;
  xrp_equivalent: number;
  tier: string;
  tier_bonus_rate: number;
};

type CryptoProvider = {
  name: string;
  currency: string;
  status: string;
  label: string;
};

type Wallet = {
  id: string;
  currency: string;
  address: string;
  label: string;
  verified: boolean;
  is_primary: boolean;
};

type Estimate = {
  coins_amount: number;
  crypto_amount: number;
  currency: string;
  tier_bonus: number;
  conversion_rate: number;
  min_cashout_coins: number;
  eligible: boolean;
  reason: string | null;
};

type CashoutEntry = {
  id: string;
  coins_amount: number;
  crypto_amount: number;
  currency: string;
  tier_bonus: number;
  wallet_address: string;
  status: string;
  tx_hash: string | null;
  explorer_url: string | null;
  created_at: string;
  completed_at: string | null;
};

export default function CashoutPage() {
  const token = getToken();
  const [balance, setBalance] = useState<Balance | null>(null);
  const [cryptos, setCryptos] = useState<CryptoProvider[]>([]);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [history, setHistory] = useState<CashoutEntry[]>([]);
  const [totals, setTotals] = useState<Record<string, number>>({});

  // Form state
  const [selectedCurrency, setSelectedCurrency] = useState("XRP");
  const [coinsInput, setCoinsInput] = useState("");
  const [estimate, setEstimate] = useState<Estimate | null>(null);

  // Wallet linking
  const [showWalletForm, setShowWalletForm] = useState(false);
  const [walletAddress, setWalletAddress] = useState("");
  const [walletLabel, setWalletLabel] = useState("");

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadData = async () => {
    if (!token) return;
    try {
      const [b, c, w, h] = await Promise.all([
        getBalance(token),
        getSupportedCryptos(token),
        getWallets(token),
        getCashoutHistory(token),
      ]);
      setBalance(b);
      setCryptos(c.providers);
      setWallets(w.wallets);
      setHistory(h.cashouts);
      setTotals(h.total_cashed_out);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleEstimate = async () => {
    if (!token || !coinsInput) return;
    const coins = parseInt(coinsInput);
    if (isNaN(coins) || coins <= 0) return;
    try {
      const est = await estimateCashout(coins, selectedCurrency, token);
      setEstimate(est);
      setMessage(null);
    } catch (err: unknown) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Estimate failed" });
    }
  };

  const handleCashout = async () => {
    if (!token || !estimate?.eligible) return;
    setLoading(true);
    try {
      const result = await doCashout(estimate.coins_amount, selectedCurrency, token);
      if (result.status === "completed") {
        setMessage({ type: "success", text: `Cashout complete! ${result.crypto_amount} ${result.currency} sent to your wallet.` });
      } else if (result.status === "failed") {
        setMessage({ type: "error", text: result.failure_reason || "Cashout failed" });
      } else {
        setMessage({ type: "success", text: "Cashout processing..." });
      }
      setCoinsInput("");
      setEstimate(null);
      loadData();
    } catch (err: unknown) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Cashout failed" });
    } finally {
      setLoading(false);
    }
  };

  const handleLinkWallet = async () => {
    if (!token || !walletAddress) return;
    setLoading(true);
    try {
      await linkWallet(selectedCurrency, walletAddress, walletLabel, token);
      setShowWalletForm(false);
      setWalletAddress("");
      setWalletLabel("");
      setMessage({ type: "success", text: `${selectedCurrency} wallet linked successfully` });
      loadData();
    } catch (err: unknown) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to link wallet" });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWallet = async (walletId: string) => {
    if (!token) return;
    if (!confirm("Remove this wallet?")) return;
    try {
      await deleteWallet(walletId, token);
      loadData();
    } catch (err: unknown) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to remove wallet" });
    }
  };

  const currentWallet = wallets.find((w) => w.currency === selectedCurrency);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Cashout</h1>
      <p className="text-gray-500 text-sm">Convert Route Coins to cryptocurrency</p>

      {/* Message banner */}
      {message && (
        <div
          className={`rounded-lg p-3 text-sm ${
            message.type === "success"
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
              : "bg-red-50 text-red-700 border border-red-200"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Balance card */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-xl p-6 text-white">
        <div className="text-sm opacity-80">Available Balance</div>
        <div className="text-4xl font-extrabold mt-1">
          {balance?.route_coins?.toLocaleString() ?? "—"}
        </div>
        <div className="text-sm opacity-80">Route Coins</div>
        <div className="mt-3 text-lg font-semibold">
          ≈ {balance?.xrp_equivalent?.toFixed(4) ?? "—"} XRP
        </div>
        {balance && balance.tier !== "rookie" && (
          <div className="mt-1 text-xs opacity-70">
            {balance.tier.toUpperCase()} tier: {balance.tier_bonus_rate}x cashout bonus
          </div>
        )}
      </div>

      {/* Currency selector */}
      <div>
        <h2 className="font-semibold mb-3">Select Currency</h2>
        <div className="grid grid-cols-3 gap-3">
          {cryptos.map((c) => (
            <button
              key={c.name}
              onClick={() => c.status === "active" && setSelectedCurrency(c.currency)}
              disabled={c.status === "coming_soon"}
              className={`rounded-xl border-2 p-4 text-center transition ${
                selectedCurrency === c.currency
                  ? "border-emerald-500 bg-emerald-50"
                  : c.status === "coming_soon"
                    ? "border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed"
                    : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="text-lg font-bold">{c.currency}</div>
              <div className="text-xs text-gray-500">{c.label}</div>
              {c.status === "coming_soon" && (
                <span className="text-[10px] font-medium text-gray-400 mt-1 inline-block">
                  Coming Soon
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Wallet */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold mb-3">{selectedCurrency} Wallet</h2>
        {currentWallet ? (
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-mono text-gray-700 break-all">
                {currentWallet.address}
              </div>
              {currentWallet.label && (
                <div className="text-xs text-gray-500 mt-1">{currentWallet.label}</div>
              )}
            </div>
            <button
              onClick={() => handleDeleteWallet(currentWallet.id)}
              className="text-xs text-red-500 hover:text-red-700"
            >
              Remove
            </button>
          </div>
        ) : showWalletForm ? (
          <div className="space-y-3">
            <input
              type="text"
              placeholder={`Enter ${selectedCurrency} wallet address`}
              value={walletAddress}
              onChange={(e) => setWalletAddress(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:outline-none"
            />
            <input
              type="text"
              placeholder="Label (optional, e.g. 'My Xaman Wallet')"
              value={walletLabel}
              onChange={(e) => setWalletLabel(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:outline-none"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setShowWalletForm(false)}
                className="flex-1 rounded-lg border border-gray-200 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleLinkWallet}
                disabled={loading || !walletAddress}
                className="flex-1 rounded-lg bg-emerald-600 py-2 text-sm text-white font-medium hover:bg-emerald-700 disabled:opacity-50"
              >
                {loading ? "Linking..." : "Link Wallet"}
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowWalletForm(true)}
            className="w-full rounded-lg border-2 border-dashed border-emerald-300 py-3 text-sm text-emerald-600 font-medium hover:bg-emerald-50 transition"
          >
            + Link {selectedCurrency} Wallet
          </button>
        )}
      </div>

      {/* Cashout form */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold mb-3">Cash Out</h2>
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Enter coins amount"
              value={coinsInput}
              onChange={(e) => {
                setCoinsInput(e.target.value);
                setEstimate(null);
              }}
              className="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:border-emerald-500 focus:outline-none"
            />
            <button
              onClick={handleEstimate}
              disabled={!coinsInput}
              className="rounded-lg bg-emerald-100 px-4 py-2.5 text-sm font-medium text-emerald-700 hover:bg-emerald-200 disabled:opacity-50"
            >
              Estimate
            </button>
          </div>

          {/* Quick amounts */}
          <div className="flex gap-2">
            {[1000, 5000, 10000].map((amt) => (
              <button
                key={amt}
                onClick={() => {
                  setCoinsInput(amt.toString());
                  setEstimate(null);
                }}
                className="text-xs px-3 py-1 rounded-full border border-gray-200 text-gray-600 hover:bg-gray-50"
              >
                {amt.toLocaleString()} coins
              </button>
            ))}
            {balance && (
              <button
                onClick={() => {
                  setCoinsInput(balance.route_coins.toString());
                  setEstimate(null);
                }}
                className="text-xs px-3 py-1 rounded-full border border-emerald-200 text-emerald-600 hover:bg-emerald-50"
              >
                Max
              </button>
            )}
          </div>

          {/* Estimate result */}
          {estimate && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">You send</span>
                <span className="font-semibold">{estimate.coins_amount.toLocaleString()} coins</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">You receive</span>
                <span className="font-semibold text-emerald-600">
                  {estimate.crypto_amount} {estimate.currency}
                </span>
              </div>
              {estimate.tier_bonus > 1 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Tier bonus</span>
                  <span className="font-semibold text-amber-600">{estimate.tier_bonus}x</span>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Rate</span>
                <span className="text-gray-600">
                  {estimate.conversion_rate.toLocaleString()} coins = 1 {estimate.currency}
                </span>
              </div>

              <button
                onClick={handleCashout}
                disabled={!estimate.eligible || loading}
                className={`w-full mt-3 rounded-lg py-2.5 text-sm font-semibold transition ${
                  estimate.eligible
                    ? "bg-emerald-600 text-white hover:bg-emerald-700"
                    : "bg-gray-200 text-gray-500 cursor-not-allowed"
                }`}
              >
                {loading
                  ? "Processing..."
                  : estimate.eligible
                    ? `Cash Out ${estimate.crypto_amount} ${estimate.currency}`
                    : estimate.reason ?? "Not eligible"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Total cashed out */}
      {Object.values(totals).some((v) => v > 0) && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold mb-3">Total Cashed Out</h2>
          <div className="grid grid-cols-3 gap-4 text-center">
            {Object.entries(totals).map(([currency, amount]) => (
              <div key={currency}>
                <div className="text-lg font-bold text-emerald-600">
                  {amount > 0 ? amount.toFixed(4) : "—"}
                </div>
                <div className="text-xs text-gray-500">{currency}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cashout history */}
      {history.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold mb-4">Cashout History</h2>
          <div className="space-y-3">
            {history.map((entry) => (
              <div
                key={entry.id}
                className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0"
              >
                <div>
                  <div className="text-sm font-medium">
                    {entry.crypto_amount} {entry.currency}
                  </div>
                  <div className="text-xs text-gray-500">
                    {entry.coins_amount.toLocaleString()} coins
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(entry.created_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </div>
                </div>
                <div className="text-right">
                  <StatusBadge status={entry.status} />
                  {entry.tx_hash && entry.explorer_url && (
                    <a
                      href={entry.explorer_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-blue-500 hover:text-blue-700 block mt-1"
                    >
                      View on chain
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-green-100 text-green-700",
    processing: "bg-yellow-100 text-yellow-700",
    pending: "bg-blue-100 text-blue-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={`text-xs font-medium px-2 py-0.5 rounded-full ${styles[status] ?? "bg-gray-100 text-gray-700"}`}
    >
      {status}
    </span>
  );
}
