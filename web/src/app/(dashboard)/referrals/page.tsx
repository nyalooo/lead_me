"use client";

import { useEffect, useState } from "react";
import { getToken } from "@/lib/auth";
import { getReferralCode, getReferralStats, trackShare } from "@/lib/api";

type ReferralCode = {
  code: string;
  uses: number;
  max_uses: number | null;
  active: boolean;
  share_url: string;
};

type ReferralStats = {
  referral_code: string;
  total_referrals: number;
  qualified_referrals: number;
  total_coins_earned: number;
  referrals: Array<{
    referred_display_name: string;
    qualified: boolean;
    coins_earned: number;
    created_at: string;
  }>;
};

export default function ReferralsPage() {
  const token = getToken();
  const [code, setCode] = useState<ReferralCode | null>(null);
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadData = async () => {
    if (!token) return;
    try {
      const [c, s] = await Promise.all([
        getReferralCode(token),
        getReferralStats(token),
      ]);
      setCode(c);
      setStats(s);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleCopyLink = async () => {
    if (!code || !token) return;
    try {
      await navigator.clipboard.writeText(code.share_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      await trackShare("copy_link", "referral", token);
    } catch {
      setMessage({ type: "error", text: "Failed to copy" });
    }
  };

  const handleWhatsApp = async () => {
    if (!token) return;
    const result = await trackShare("whatsapp", "referral", token);
    const text = encodeURIComponent(result.message);
    window.open(`https://wa.me/?text=${text}`, "_blank");
  };

  const handleTwitter = async () => {
    if (!token) return;
    const result = await trackShare("twitter", "referral", token);
    const text = encodeURIComponent(result.message);
    window.open(`https://twitter.com/intent/tweet?text=${text}`, "_blank");
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Invite Friends</h1>
        <p className="text-gray-500 text-sm mt-1">
          Share your referral code and earn coins when friends join
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

      {/* Referral code card */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-xl p-6 text-white">
        <div className="text-sm opacity-80">Your Referral Code</div>
        <div className="text-4xl font-extrabold mt-2 tracking-wider">
          {code?.code ?? "---"}
        </div>
        <div className="text-sm opacity-80 mt-2">
          Share this code and earn {200} coins per qualified referral
        </div>
      </div>

      {/* Share buttons */}
      <div className="grid grid-cols-3 gap-3">
        <button
          onClick={handleWhatsApp}
          className="flex flex-col items-center gap-2 rounded-xl border-2 border-gray-200 p-4 hover:border-green-400 hover:bg-green-50 transition"
        >
          <span className="text-2xl">💬</span>
          <span className="text-sm font-medium text-gray-700">WhatsApp</span>
        </button>
        <button
          onClick={handleTwitter}
          className="flex flex-col items-center gap-2 rounded-xl border-2 border-gray-200 p-4 hover:border-blue-400 hover:bg-blue-50 transition"
        >
          <span className="text-2xl">🐦</span>
          <span className="text-sm font-medium text-gray-700">Twitter</span>
        </button>
        <button
          onClick={handleCopyLink}
          className="flex flex-col items-center gap-2 rounded-xl border-2 border-gray-200 p-4 hover:border-emerald-400 hover:bg-emerald-50 transition"
        >
          <span className="text-2xl">{copied ? "✅" : "🔗"}</span>
          <span className="text-sm font-medium text-gray-700">
            {copied ? "Copied!" : "Copy Link"}
          </span>
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-emerald-600">{stats.total_referrals}</div>
            <div className="text-xs text-gray-500 mt-1">Invited</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-emerald-600">{stats.qualified_referrals}</div>
            <div className="text-xs text-gray-500 mt-1">Qualified</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
            <div className="text-2xl font-bold text-emerald-600">{stats.total_coins_earned}</div>
            <div className="text-xs text-gray-500 mt-1">Coins Earned</div>
          </div>
        </div>
      )}

      {/* How it works */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="font-semibold mb-4">How Referrals Work</h2>
        <div className="space-y-3">
          {[
            { step: "1", text: "Share your referral code with friends" },
            { step: "2", text: "They sign up using your code and get 100 bonus coins" },
            { step: "3", text: "When they complete 3 routes, you earn 200 coins" },
          ].map((item) => (
            <div key={item.step} className="flex items-center gap-3">
              <div className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-sm font-bold flex-shrink-0">
                {item.step}
              </div>
              <span className="text-sm text-gray-700">{item.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Referral history */}
      {stats && stats.referrals.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold mb-4">Your Referrals</h2>
          <div className="space-y-3">
            {stats.referrals.map((ref, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0"
              >
                <div>
                  <div className="text-sm font-medium">{ref.referred_display_name}</div>
                  <div className="text-xs text-gray-400">
                    {new Date(ref.created_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </div>
                </div>
                <div className="text-right">
                  {ref.qualified ? (
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                      +{ref.coins_earned} coins
                    </span>
                  ) : (
                    <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
                      Pending
                    </span>
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
