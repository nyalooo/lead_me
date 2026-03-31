/**
 * API client for LeadMe backend.
 *
 * Shared between web and mobile — same endpoints, same types.
 * Base URL is configured for local dev (change for production).
 */

import { getToken } from './auth';

// For Expo development, use your machine's LAN IP or tunnel URL
// In production, this comes from app config / env
const BASE_URL = __DEV__
  ? 'http://192.168.1.100:6800/api/v1' // change to your dev machine IP
  : 'https://api.leadme.app/api/v1';

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// --- Auth ---
export const requestOTP = (phone: string) =>
  request<{ message: string }>('/auth/request-otp', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });

export const verifyOTP = (phone: string, otp: string) =>
  request<{ access_token: string; user: any }>('/auth/verify-otp', {
    method: 'POST',
    body: JSON.stringify({ phone, otp }),
  });

// --- Routes ---
export const assignRoute = (origin: LatLng, destination: LatLng) =>
  request<any>('/routes/assign', {
    method: 'POST',
    body: JSON.stringify({ origin, destination }),
  });

export const trackLocation = (routeId: string, lat: number, lng: number, timestamp: string, accuracy: number) =>
  request<any>(`/routes/${routeId}/track`, {
    method: 'POST',
    body: JSON.stringify({ lat, lng, timestamp, accuracy_m: accuracy }),
  });

export const completeRoute = (routeId: string) =>
  request<any>(`/routes/${routeId}/complete`, { method: 'POST' });

// --- Rewards ---
export const getBalance = () => request<any>('/rewards/balance');
export const getStreaks = () => request<any>('/rewards/streaks');
export const getBadges = () => request<any>('/rewards/badges');
export const getLeaderboard = (area = 'mumbai', period = 'week') =>
  request<any>(`/rewards/leaderboard?area=${area}&period=${period}`);
export const getRewardHistory = (limit = 20, offset = 0) =>
  request<any>(`/rewards/history?limit=${limit}&offset=${offset}`);

// --- Cashout ---
export const getSupportedCryptos = () => request<any>('/cashout/cryptos');
export const getWallets = () => request<any>('/cashout/wallets');
export const linkWallet = (currency: string, address: string, label = '') =>
  request<any>('/cashout/wallets', {
    method: 'POST',
    body: JSON.stringify({ currency, address, label }),
  });
export const estimateCashout = (coins: number, currency = 'XRP') =>
  request<any>('/cashout/estimate', {
    method: 'POST',
    body: JSON.stringify({ coins_amount: coins, currency }),
  });
export const doCashout = (coins: number, currency = 'XRP', walletId?: string) =>
  request<any>('/cashout/cashout', {
    method: 'POST',
    body: JSON.stringify({ coins_amount: coins, currency, wallet_id: walletId }),
  });
export const getCashoutHistory = (limit = 20, offset = 0) =>
  request<any>(`/cashout/history?limit=${limit}&offset=${offset}`);

// --- Schedule ---
export const getSchedules = () => request<any[]>('/schedules');
export const createSchedule = (data: any) =>
  request<any>('/schedules', { method: 'POST', body: JSON.stringify(data) });
export const updateSchedule = (id: string, data: any) =>
  request<any>(`/schedules/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteSchedule = (id: string) =>
  request<void>(`/schedules/${id}`, { method: 'DELETE' });

// --- Profile ---
export const getProfile = () => request<any>('/users/me');
export const updateProfile = (data: any) =>
  request<any>('/users/me', { method: 'PUT', body: JSON.stringify(data) });
export const getUserStats = () => request<any>('/users/me/stats');

// --- Types ---
export interface LatLng {
  lat: number;
  lng: number;
}
