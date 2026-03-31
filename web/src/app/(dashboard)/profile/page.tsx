"use client";

import { useEffect, useState } from "react";
import { getProfile, getUserStats, getBadges, getHistory } from "@/lib/api";
import { getToken } from "@/lib/auth";

type Profile = {
  display_name: string;
  phone: string;
  area: string | null;
  tier: string;
  xrp_wallet_address: string | null;
  created_at: string;
};

type Stats = {
  total_routes: number;
  total_coins: number;
  compliance_rate: number;
  tier: string;
  xrp_equivalent: number;
  member_since: string;
};

type BadgeInfo = {
  id: string;
  name: string;
  description: string;
  earned_at?: string;
  pinned?: boolean;
};

type Transaction = {
  id: string;
  type: string;
  coins: number;
  description: string;
  timestamp: string;
};

export default function ProfilePage() {
  const token = getToken();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [badges, setBadges] = useState<BadgeInfo[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    if (!token) return;
    getProfile(token).then(setProfile).catch(console.error);
    getUserStats(token).then(setStats).catch(console.error);
    getBadges(token)
      .then((res) => setBadges(res.earned))
      .catch(console.error);
    getHistory(token)
      .then((res) => setTransactions(res.transactions))
      .catch(console.error);
  }, [token]);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Profile</h1>

      {/* Profile card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-2xl font-bold">
            {profile?.display_name?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div>
            <h2 className="text-lg font-semibold">
              {profile?.display_name ?? "Loading..."}
            </h2>
            <p className="text-sm text-gray-500">{profile?.phone}</p>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 capitalize mt-1 inline-block">
              {profile?.tier ?? "rookie"}
            </span>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Routes" value={stats.total_routes.toString()} />
          <StatCard label="Total Coins" value={stats.total_coins.toLocaleString()} />
          <StatCard
            label="Compliance"
            value={`${(stats.compliance_rate * 100).toFixed(0)}%`}
          />
          <StatCard label="XRP Earned" value={stats.xrp_equivalent.toFixed(4)} />
        </div>
      )}

      {/* Badges */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-semibold mb-4">Badges Earned</h3>
        {badges.length === 0 ? (
          <p className="text-sm text-gray-400">
            No badges yet — complete routes to start earning!
          </p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {badges.map((badge) => (
              <div
                key={badge.id}
                className="rounded-lg border border-gray-100 p-3 bg-gradient-to-br from-amber-50 to-yellow-50"
              >
                <div className="font-medium text-sm">{badge.name}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {badge.description}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent transactions */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="font-semibold mb-4">Recent Transactions</h3>
        {transactions.length === 0 ? (
          <p className="text-sm text-gray-400">No transactions yet</p>
        ) : (
          <div className="space-y-2">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0"
              >
                <div>
                  <div className="text-sm">{tx.description}</div>
                  <div className="text-xs text-gray-400">
                    {new Date(tx.timestamp).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
                <span className="text-sm font-medium text-emerald-600">
                  +{tx.coins}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-xl font-bold">{value}</div>
    </div>
  );
}
