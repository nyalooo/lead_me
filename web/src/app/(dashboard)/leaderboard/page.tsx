"use client";

import { useEffect, useState } from "react";
import { getLeaderboard } from "@/lib/api";
import { getToken } from "@/lib/auth";

type LeaderboardData = {
  area: string;
  period: string;
  rankings: Array<{
    rank: number;
    display_name: string;
    coins_earned: number;
    tier: string;
  }>;
  user_rank: number | null;
  total_participants: number;
};

const AREAS = ["mumbai", "andheri", "bandra", "powai", "dadar", "bkc"];

const TIER_COLORS: Record<string, string> = {
  rookie: "text-gray-500",
  regular: "text-blue-600",
  pro: "text-purple-600",
  legend: "text-amber-600",
};

export default function LeaderboardPage() {
  const token = getToken();
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [selectedArea, setSelectedArea] = useState("mumbai");

  useEffect(() => {
    if (!token) return;
    getLeaderboard(token, selectedArea).then(setData).catch(console.error);
  }, [token, selectedArea]);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Leaderboard</h1>
        <p className="text-gray-500 text-sm mt-1">
          Top commuters in your area this week
        </p>
      </div>

      {/* Area filter */}
      <div className="flex gap-2 flex-wrap">
        {AREAS.map((area) => (
          <button
            key={area}
            onClick={() => setSelectedArea(area)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition capitalize ${
              selectedArea === area
                ? "bg-emerald-600 text-white"
                : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {area}
          </button>
        ))}
      </div>

      {/* Your rank */}
      {data?.user_rank && (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border border-emerald-200 p-4 flex items-center justify-between">
          <span className="text-sm text-emerald-800">Your rank</span>
          <span className="text-xl font-bold text-emerald-700">
            #{data.user_rank}
            <span className="text-sm font-normal text-emerald-600 ml-1">
              of {data.total_participants}
            </span>
          </span>
        </div>
      )}

      {/* Rankings table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100 text-xs text-gray-500 uppercase">
              <th className="text-left px-4 py-3 w-16">Rank</th>
              <th className="text-left px-4 py-3">Commuter</th>
              <th className="text-left px-4 py-3">Tier</th>
              <th className="text-right px-4 py-3">Coins</th>
            </tr>
          </thead>
          <tbody>
            {data?.rankings.map((entry) => (
              <tr
                key={entry.rank}
                className="border-b border-gray-50 last:border-0 hover:bg-gray-50"
              >
                <td className="px-4 py-3">
                  {entry.rank <= 3 ? (
                    <span className="text-lg">
                      {entry.rank === 1 ? "🥇" : entry.rank === 2 ? "🥈" : "🥉"}
                    </span>
                  ) : (
                    <span className="text-sm text-gray-500">#{entry.rank}</span>
                  )}
                </td>
                <td className="px-4 py-3 font-medium text-sm">
                  {entry.display_name}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`text-xs font-medium capitalize ${TIER_COLORS[entry.tier] ?? "text-gray-500"}`}
                  >
                    {entry.tier}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-sm font-medium">
                  {entry.coins_earned.toLocaleString()}
                </td>
              </tr>
            ))}
            {(!data || data.rankings.length === 0) && (
              <tr>
                <td colSpan={4} className="px-4 py-12 text-center text-gray-400 text-sm">
                  No rankings yet — be the first to earn coins!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
