/**
 * Auth token management using SecureStore (encrypted on device).
 *
 * On mobile, we use expo-secure-store for secure token storage
 * (Keychain on iOS, Keystore on Android).
 */

import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'leadme_token';
const USER_KEY = 'leadme_user';

export async function getToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function setAuth(token: string, user: any): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
  await SecureStore.setItemAsync(USER_KEY, JSON.stringify(user));
}

export async function getUser(): Promise<any | null> {
  const data = await SecureStore.getItemAsync(USER_KEY);
  return data ? JSON.parse(data) : null;
}

export async function clearAuth(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
  await SecureStore.deleteItemAsync(USER_KEY);
}

export async function isAuthenticated(): Promise<boolean> {
  const token = await getToken();
  return !!token;
}
