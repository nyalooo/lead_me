/**
 * API client for LeadMe backend.
 *
 * All fetch calls to the FastAPI backend go through this module
 * so we have a single place to manage base URL, auth headers, and error handling.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:6800/api/v1";

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
};

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new ApiError(res.status, error.detail || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Auth ---

export function requestOtp(phone: string) {
  return request<{ message: string; expires_in: number; dev_otp?: string }>("/auth/request-otp", {
    method: "POST",
    body: { phone },
  });
}

export function verifyOtp(phone: string, otp: string) {
  return request<{
    access_token: string;
    token_type: string;
    user: { id: string; phone: string; display_name: string; tier: string };
  }>("/auth/verify-otp", {
    method: "POST",
    body: { phone, otp },
  });
}

// --- Routes ---

export function assignRoute(
  origin: { lat: number; lng: number },
  destination: { lat: number; lng: number },
  token: string,
  departureTime?: string,
) {
  return request<{
    assignment_id: string;
    assigned_route: {
      id: string;
      polyline: string | null;
      distance_km: number;
      estimated_duration_min: number;
      load_status: string;
      detour_percent: number;
    };
    alternative_routes: Array<{
      id: string;
      distance_km: number;
      estimated_duration_min: number;
      load_status: string;
    }>;
    estimated_reward: {
      base_coins: number;
      detour_multiplier: number;
      streak_multiplier: number;
      peak_multiplier: number;
      total_coins: number;
    };
  }>("/routes/assign", {
    method: "POST",
    body: { origin, destination, departure_time: departureTime },
    token,
  });
}

export function trackLocation(
  assignmentId: string,
  lat: number,
  lng: number,
  timestamp: string,
  token: string,
) {
  return request<{ on_route: boolean; progress_percent: number }>(
    `/routes/${assignmentId}/track`,
    { method: "POST", body: { lat, lng, timestamp, accuracy_m: 0 }, token },
  );
}

export function completeRoute(assignmentId: string, token: string) {
  return request<{
    assignment_id: string;
    compliant: boolean;
    compliance_score: number;
    coins_earned: number;
    streak_day: number;
    badges_earned: string[];
  }>(`/routes/${assignmentId}/complete`, { method: "POST", token });
}

// --- Schedules ---

export function getSchedules(token: string) {
  return request<{ schedules: Array<Record<string, unknown>> }>("/schedules", { token });
}

export function createSchedule(data: Record<string, unknown>, token: string) {
  return request<Record<string, unknown>>("/schedules", {
    method: "POST",
    body: data,
    token,
  });
}

// --- Rewards ---

export function getBalance(token: string) {
  return request<{
    route_coins: number;
    xrp_equivalent: number;
    tier: string;
    xrp_conversion_rate: number;
    tier_bonus_rate: number;
  }>("/rewards/balance", { token });
}

export function getStreaks(token: string) {
  return request<{
    current_streak: number;
    longest_streak: number;
    multiplier: number;
    next_milestone: { days: number; multiplier: number } | null;
    streak_freezes_remaining: number;
    last_completed_date: string | null;
  }>("/rewards/streaks", { token });
}

export function getBadges(token: string) {
  return request<{
    earned: Array<{
      id: string;
      name: string;
      description: string;
      earned_at: string;
      pinned: boolean;
    }>;
    available: Array<{
      id: string;
      name: string;
      description: string;
      progress: { current: number; target: number };
    }>;
  }>("/rewards/badges", { token });
}

export function getLeaderboard(token: string, area = "mumbai") {
  return request<{
    area: string;
    period: string;
    rankings: Array<{
      rank: number;
      display_name: string;
      coins_earned: number;
      tier: string;
      pinned_badges: string[];
    }>;
    user_rank: number | null;
    total_participants: number;
  }>(`/rewards/leaderboard?area=${area}`, { token });
}

export function getHistory(token: string, limit = 20, offset = 0) {
  return request<{
    transactions: Array<{
      id: string;
      type: string;
      coins: number;
      description: string;
      timestamp: string;
    }>;
    total: number;
  }>(`/rewards/history?limit=${limit}&offset=${offset}`, { token });
}

// --- User ---

export function getProfile(token: string) {
  return request<{
    id: string;
    phone: string;
    display_name: string;
    area: string | null;
    tier: string;
    xrp_wallet_address: string | null;
    created_at: string;
  }>("/users/me", { token });
}

export function getUserStats(token: string) {
  return request<{
    total_routes: number;
    total_coins: number;
    compliance_rate: number;
    tier: string;
    xrp_equivalent: number;
    member_since: string;
  }>("/users/me/stats", { token });
}

// --- Cashout ---

export function getSupportedCryptos(token: string) {
  return request<{
    active_provider: string;
    providers: Array<{
      name: string;
      currency: string;
      status: string;
      label: string;
    }>;
  }>("/cashout/cryptos", { token });
}

export function getWallets(token: string) {
  return request<{
    wallets: Array<{
      id: string;
      currency: string;
      address: string;
      label: string;
      verified: boolean;
      is_primary: boolean;
      created_at: string;
    }>;
  }>("/cashout/wallets", { token });
}

export function linkWallet(currency: string, address: string, label: string, token: string) {
  return request<{
    id: string;
    currency: string;
    address: string;
    label: string;
    verified: boolean;
    is_primary: boolean;
    created_at: string;
  }>("/cashout/wallets", {
    method: "POST",
    body: { currency, address, label },
    token,
  });
}

export function deleteWallet(walletId: string, token: string) {
  return request<{ ok: boolean }>(`/cashout/wallets/${walletId}`, {
    method: "DELETE",
    token,
  });
}

export function estimateCashout(coinsAmount: number, currency: string, token: string) {
  return request<{
    coins_amount: number;
    crypto_amount: number;
    currency: string;
    tier_bonus: number;
    conversion_rate: number;
    min_cashout_coins: number;
    eligible: boolean;
    reason: string | null;
  }>("/cashout/estimate", {
    method: "POST",
    body: { coins_amount: coinsAmount, currency },
    token,
  });
}

export function doCashout(coinsAmount: number, currency: string, token: string, walletId?: string) {
  return request<{
    id: string;
    coins_amount: number;
    crypto_amount: number;
    currency: string;
    tier_bonus: number;
    wallet_address: string;
    status: string;
    tx_hash: string | null;
    explorer_url: string | null;
    failure_reason: string | null;
    created_at: string;
    completed_at: string | null;
  }>("/cashout/cashout", {
    method: "POST",
    body: { coins_amount: coinsAmount, currency, wallet_id: walletId },
    token,
  });
}

export function getCashoutHistory(token: string, limit = 20, offset = 0) {
  return request<{
    cashouts: Array<{
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
    }>;
    total: number;
    total_cashed_out: Record<string, number>;
  }>(`/cashout/history?limit=${limit}&offset=${offset}`, { token });
}

// --- Challenges ---

export function getChallenges(token: string) {
  return request<{
    active: ChallengeItem[];
    upcoming: ChallengeItem[];
    completed: ChallengeItem[];
  }>("/challenges", { token });
}

export function getChallenge(challengeId: string, token: string) {
  return request<ChallengeItem>(`/challenges/${challengeId}`, { token });
}

export function joinChallenge(challengeId: string, token: string) {
  return request<{ challenge_id: string; joined: boolean; message: string }>(
    `/challenges/${challengeId}/join`,
    { method: "POST", token },
  );
}

export function claimChallengeReward(challengeId: string, token: string) {
  return request<{
    claimed: boolean;
    message: string;
    coins_earned?: number;
    xrp_earned?: number;
  }>(`/challenges/${challengeId}/claim`, { method: "POST", token });
}

// --- Social / Referrals ---

export function getReferralCode(token: string) {
  return request<{
    code: string;
    uses: number;
    max_uses: number | null;
    active: boolean;
    share_url: string;
  }>("/social/referral-code", { token });
}

export function getReferralStats(token: string) {
  return request<{
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
  }>("/social/referral-stats", { token });
}

export function applyReferralCode(code: string, token: string) {
  return request<{ applied: boolean; message: string; bonus_coins: number }>(
    "/social/apply-referral",
    { method: "POST", body: { code }, token },
  );
}

export function trackShare(
  channel: "whatsapp" | "copy_link" | "twitter",
  contentType: "referral" | "achievement" | "challenge" | "route",
  token: string,
  contentId?: string,
) {
  return request<{ shared: boolean; share_url: string; message: string }>(
    "/social/share",
    { method: "POST", body: { channel, content_type: contentType, content_id: contentId }, token },
  );
}

export type ChallengeItem = {
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
  reward_badge_id: string | null;
  starts_at: string;
  ends_at: string;
  max_participants: number | null;
  active: boolean;
  participant_count: number;
  user_joined: boolean;
  user_progress: number;
  user_completed: boolean;
};
