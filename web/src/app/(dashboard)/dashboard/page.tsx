"use client";

import { useEffect, useState } from "react";
import { getBalance, getStreaks, assignRoute } from "@/lib/api";
import { getToken, getUser } from "@/lib/auth";
import MapView from "@/lib/maps";
import { useRouteTracking } from "@/hooks/useRouteTracking";

type Balance = {
  route_coins: number;
  xrp_equivalent: number;
  tier: string;
  tier_bonus_rate: number;
};

type Streak = {
  current_streak: number;
  longest_streak: number;
  multiplier: number;
  next_milestone: { days: number; multiplier: number } | null;
};

type Assignment = {
  assignment_id: string;
  assigned_route: {
    distance_km: number;
    estimated_duration_min: number;
    load_status: string;
    detour_percent: number;
  };
  estimated_reward: {
    total_coins: number;
  };
};

// Mumbai center
const MUMBAI_CENTER = { lat: 19.076, lng: 72.877 };
// Demo route: Andheri → CST
const DEMO_ORIGIN = { lat: 19.1196, lng: 72.8464 };
const DEMO_DEST = { lat: 18.9398, lng: 72.8355 };

export default function DashboardPage() {
  const [balance, setBalance] = useState<Balance | null>(null);
  const [streak, setStreak] = useState<Streak | null>(null);
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [loading, setLoading] = useState(false);

  const user = getUser();
  const token = getToken();

  const tracking = useRouteTracking(assignment?.assignment_id ?? null);

  useEffect(() => {
    if (!token) return;
    getBalance(token).then(setBalance).catch(console.error);
    getStreaks(token).then(setStreak).catch(console.error);
  }, [token]);

  async function handleQuickRoute() {
    if (!token) return;
    setLoading(true);
    try {
      const result = await assignRoute(DEMO_ORIGIN, DEMO_DEST, token);
      setAssignment(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">
          Welcome back{user ? `, ${user.display_name}` : ""}
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Here&apos;s your commute overview
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Route Coins"
          value={balance?.route_coins?.toLocaleString() ?? "—"}
          sub="total earned"
        />
        <StatCard
          label="XRP Balance"
          value={balance?.xrp_equivalent?.toFixed(4) ?? "—"}
          sub="equivalent"
        />
        <StatCard
          label="Streak"
          value={streak ? `${streak.current_streak} days` : "—"}
          sub={streak ? `${streak.multiplier}x multiplier` : ""}
        />
        <StatCard
          label="Tier"
          value={balance?.tier?.toUpperCase() ?? "—"}
          sub={balance ? `${balance.tier_bonus_rate}x XRP rate` : ""}
        />
      </div>

      {/* Map */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <MapView
          config={{ center: MUMBAI_CENTER, zoom: 12 }}
          markers={
            assignment
              ? [
                  { id: "origin", position: DEMO_ORIGIN, label: "Andheri", color: "#10B981" },
                  { id: "dest", position: DEMO_DEST, label: "CST", color: "#EF4444" },
                ]
              : []
          }
          traffic={{ enabled: true }}
          className="w-full h-[350px]"
        />
      </div>

      {/* Quick route assignment + tracking */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold text-lg mb-4">Quick Route</h2>
        {!assignment ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">
              Request a route assignment to start earning
            </p>
            <button
              onClick={handleQuickRoute}
              disabled={loading}
              className="rounded-lg bg-emerald-600 text-white px-6 py-2.5 font-medium hover:bg-emerald-700 transition disabled:opacity-50"
            >
              {loading ? "Finding route..." : "Get Route (Andheri → CST)"}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Route assigned</span>
              <LoadBadge status={assignment.assigned_route.load_status} />
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-xl font-bold">
                  {assignment.assigned_route.distance_km} km
                </div>
                <div className="text-xs text-gray-500">Distance</div>
              </div>
              <div>
                <div className="text-xl font-bold">
                  {assignment.assigned_route.estimated_duration_min} min
                </div>
                <div className="text-xs text-gray-500">Duration</div>
              </div>
              <div>
                <div className="text-xl font-bold text-emerald-600">
                  +{assignment.estimated_reward.total_coins}
                </div>
                <div className="text-xs text-gray-500">Coins reward</div>
              </div>
            </div>
            {assignment.assigned_route.detour_percent > 0 && (
              <p className="text-xs text-amber-600 text-center">
                {assignment.assigned_route.detour_percent}% detour — earning
                bonus for helping balance traffic
              </p>
            )}

            {/* GPS Tracking controls */}
            <div className="border-t border-gray-100 pt-4">
              {tracking.state === "idle" && (
                <button
                  onClick={tracking.start}
                  className="w-full rounded-lg bg-blue-600 text-white py-2.5 font-medium hover:bg-blue-700 transition"
                >
                  Start Tracking
                </button>
              )}

              {tracking.state === "requesting_permission" && (
                <p className="text-sm text-gray-500 text-center">
                  Requesting location permission...
                </p>
              )}

              {tracking.isTracking && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-sm text-green-700 font-medium">
                        Tracking active
                      </span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {tracking.positionCount} updates sent
                    </span>
                  </div>
                  {tracking.progress > 0 && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-emerald-500 h-2 rounded-full transition-all"
                        style={{ width: `${tracking.progress}%` }}
                      />
                    </div>
                  )}
                  <button
                    onClick={tracking.complete}
                    className="w-full rounded-lg bg-emerald-600 text-white py-2.5 font-medium hover:bg-emerald-700 transition"
                  >
                    Complete Route
                  </button>
                </div>
              )}

              {tracking.state === "completed" && tracking.result && (
                <div className="bg-emerald-50 rounded-lg p-4 text-center space-y-2">
                  <p className="text-lg font-bold text-emerald-700">
                    +{tracking.result.coinsEarned} coins earned!
                  </p>
                  <p className="text-sm text-emerald-600">
                    Streak: {tracking.result.streakDay} days |
                    Compliance: {(tracking.result.complianceScore * 100).toFixed(0)}%
                  </p>
                  {tracking.result.badgesEarned.length > 0 && (
                    <p className="text-sm font-medium text-amber-600">
                      New badges: {tracking.result.badgesEarned.join(", ")}
                    </p>
                  )}
                </div>
              )}

              {tracking.state === "error" && (
                <p className="text-sm text-red-500 text-center">
                  {tracking.error}
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Next milestone */}
      {streak?.next_milestone && (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border border-emerald-200 p-4">
          <p className="text-sm text-emerald-800">
            <strong>{streak.next_milestone.days - streak.current_streak} days</strong> until{" "}
            {streak.next_milestone.multiplier}x streak multiplier
          </p>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs text-gray-400 mt-1">{sub}</div>
    </div>
  );
}

function LoadBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    clear: "bg-green-100 text-green-700",
    moderate: "bg-yellow-100 text-yellow-700",
    busy: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={`text-xs font-medium px-2 py-1 rounded-full ${colors[status] ?? "bg-gray-100 text-gray-700"}`}
    >
      {status}
    </span>
  );
}
