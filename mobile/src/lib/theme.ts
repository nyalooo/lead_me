/**
 * Design tokens — shared color palette and spacing.
 * Matches the emerald/green theme from the web app.
 */

export const colors = {
  // Primary emerald palette
  primary: '#059669',       // emerald-600
  primaryLight: '#34d399',  // emerald-400
  primaryDark: '#047857',   // emerald-700
  primaryBg: '#ecfdf5',     // emerald-50

  // Neutrals
  background: '#f9fafb',    // gray-50
  surface: '#ffffff',
  text: '#111827',           // gray-900
  textSecondary: '#6b7280',  // gray-500
  textMuted: '#9ca3af',      // gray-400
  border: '#e5e7eb',         // gray-200

  // Accents
  gold: '#f59e0b',
  silver: '#94a3b8',
  bronze: '#d97706',
  danger: '#ef4444',
  warning: '#f59e0b',
  success: '#10b981',
  info: '#3b82f6',

  // Tier colors
  rookie: '#6b7280',
  regular: '#3b82f6',
  pro: '#8b5cf6',
  legend: '#f59e0b',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radius = {
  sm: 6,
  md: 12,
  lg: 16,
  xl: 24,
  full: 999,
} as const;

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 22,
  xxl: 28,
  hero: 36,
} as const;
