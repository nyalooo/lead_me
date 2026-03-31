/**
 * LeadMe Mobile — React Native (Expo) entry point.
 *
 * Traffic-aware route assignment with crypto rewards.
 * Key mobile advantage: background GPS tracking.
 */

import { StatusBar } from 'expo-status-bar';
import AppNavigator from './src/navigation/AppNavigator';

export default function App() {
  return (
    <>
      <StatusBar style="light" />
      <AppNavigator />
    </>
  );
}
