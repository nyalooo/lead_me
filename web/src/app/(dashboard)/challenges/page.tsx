"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/lib/auth";
import {
  getChallenges,
  joinChallenge,
  claimChallengeReward,
  type ChallengeItem,
} from "@/lib/api";

type Tab = "active" | "upcoming" | "completed";

const TYPE_COLORS: Record<string, string> = {
  weekly: "bg-blue-100 text-blue-700",
  monthly: "bg-purple-100 text-purple-700",
  event: "bg-amber-100 text-amber-700",
  flash: "bg-red-100 text-red-700",
};

const GOAL_LABELS: Record<string, string> = {
  routes_count: "routes",
  distance_km: "km",
  peak_routes: "peak routes",
  area_routes: "area routes",
  streak_days: "day streak",
};

export default function ChallengesPage() {
  const token = getToken();
  const [tab, setTab] = useState<Tab>("active");
  const [challenges, setChallenges] = useState<{
    active: ChallengeItem[];
    upcoming: ChallengeItem[];
    completed: ChallengeItem[];
  }>({ active: [], upcoming: [], completed: [] });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadChallenges = async () => {
    if (!token) return;
    try {
      const data = await getChallenges(token);
      setChallenges(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadChallenges();
  }, [token]);

  const handleJoin = async (challengeId: string) => {
    if (!token) return;
    setLoading(true);
    try {
      const result = await joinChallenge(challengeId, token);
      setMessage({
        type: result.joined ? "success" : "error",
        text: result.message,
      });
      loadChallenges();
    } catch (err: unknown) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to join" });
    } finally {
      setLoading(false);
    }
  };

  const handleClaim = async (challengeId: string) => {
    if (!token) return;
    setLoading(true);
    try {
      const result = await claimChallengeReward(challengeId, token);
      if (result.claimed) {
        const parts = [];
        if (result.coins_earned) parts.push(`${result.coins_earned} coins`);
        if (result.xrp_earned) parts.push(`${result.xrp_earned} XRP`);
        setMessage({ type: "success", text: `Reward claimed! ${parts.join(" + ")}` });
      } else {
        setMessage({ type: "error", text: result.message });
      }
      loadChallenges();
    } catch (err: unknown) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to claim" });
    } finally {
      setLoading(false);
    }
  };

  const current = challenges[tab];
  const counts = {
    active: challenges.active.length,
    upcoming: challenges.upcoming.length,
    completed: challenges.completed.length,
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Challenges</h1>
        <p className="text-gray-500 text-sm mt-1">
          Complete challenges to earn bonus coins and XRP
        </p>
      </div>

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

      {/* Tabs */}
      <div className="flex gap-2">
        {(["active", "upcoming", "completed"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition capitalize ${
              tab === t
                ? "bg-emerald-600 text-white"
                : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {t}
            {counts[t] > 0 && (
              <span className="ml-1.5 text-xs opacity-75">({counts[t]})</span>
            )}
          </button>
        ))}
      </div>

      {/* Challenge cards */}
      <div className="space-y-4">
        {current.map((c) => (
          <ChallengeCard
            key={c.id}
            challenge={c}
            tab={tab}
            loading={loading}
            onJoin={() => handleJoin(c.id)}
            onClaim={() => handleClaim(c.id)}
          />
        ))}
        {current.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400 text-sm">
            No {tab} challenges right now
          </div>
        )}
      </div>
    </div>
  );
}

function ChallengeCard({
  challenge: c,
  tab,
  loading,
  onJoin,
  onClaim,
}: {
  challenge: ChallengeItem;
  tab: Tab;
  loading: boolean;
  onJoin: () => void;
  onClaim: () => void;
}) {
  const progressPercent = c.goal_value > 0
    ? Math.min(100, Math.round((c.user_progress / c.goal_value) * 100))
    : 0;

  const goalLabel = GOAL_LABELS[c.goal_type] ?? c.goal_type;
  const timeLabel = tab === "upcoming"
    ? `Starts ${new Date(c.starts_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}`
    : tab === "completed"
      ? `Ended ${new Date(c.ends_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}`
      : `Ends ${new Date(c.ends_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}`;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase ${TYPE_COLORS[c.type] ?? "bg-gray-100 text-gray-700"}`}>
              {c.type}
            </span>
            {c.goal_area && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                {c.goal_area}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-lg">{c.title}</h3>
          <p className="text-sm text-gray-500 mt-1">{c.description}</p>
        </div>
      </div>

      {/* Goal & rewards */}
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <span className="text-gray-500">Goal:</span>
          <span className="font-medium">{c.goal_value} {goalLabel}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-gray-500">Reward:</span>
          <span className="font-medium text-emerald-600">
            {c.reward_coins > 0 && `${c.reward_coins} coins`}
            {c.reward_coins > 0 && c.reward_xrp > 0 && " + "}
            {c.reward_xrp > 0 && `${c.reward_xrp} XRP`}
          </span>
        </div>
      </div>

      {/* Progress bar (if joined) */}
      {c.user_joined && (
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>{c.user_progress} / {c.goal_value} {goalLabel}</span>
            <span>{progressPercent}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${c.user_completed ? "bg-emerald-500" : "bg-emerald-400"}`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-1">
        <div className="text-xs text-gray-400">
          {c.participant_count} participant{c.participant_count !== 1 ? "s" : ""}
          {c.max_participants && ` / ${c.max_participants} max`}
          {" · "}
          {timeLabel}
        </div>

        {tab === "active" && !c.user_joined && (
          <button
            onClick={onJoin}
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 transition"
          >
            Join Challenge
          </button>
        )}
        {tab === "active" && c.user_joined && c.user_completed && (
          <button
            onClick={onClaim}
            disabled={loading}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50 transition"
          >
            Claim Reward
          </button>
        )}
        {tab === "active" && c.user_joined && !c.user_completed && (
          <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg">
            In Progress
          </span>
        )}
        {tab === "completed" && c.user_completed && (
          <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg">
            Completed
          </span>
        )}
      </div>
    </div>
  );
}
