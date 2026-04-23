/**
 * App navigation structure.
 *
 * Auth flow:
 *   Login → OTP Verify → Main Tabs
 *
 * Main tabs:
 *   Dashboard | Schedule | Leaderboard | Cashout | Profile
 */

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

import { isAuthenticated } from '../lib/auth';
import { colors } from '../lib/theme';

import LoginScreen from '../screens/LoginScreen';
import DashboardScreen from '../screens/DashboardScreen';
import ScheduleScreen from '../screens/ScheduleScreen';
import LeaderboardScreen from '../screens/LeaderboardScreen';
import ChallengesScreen from '../screens/ChallengesScreen';
import CashoutScreen from '../screens/CashoutScreen';
import ProfileScreen from '../screens/ProfileScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          paddingBottom: 4,
          height: 56,
        },
        headerStyle: { backgroundColor: colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          tabBarLabel: 'Home',
          tabBarIcon: ({ color }) => <TabIcon label="🏠" />,
        }}
      />
      <Tab.Screen
        name="Schedule"
        component={ScheduleScreen}
        options={{
          tabBarIcon: ({ color }) => <TabIcon label="📅" />,
        }}
      />
      <Tab.Screen
        name="Challenges"
        component={ChallengesScreen}
        options={{
          tabBarIcon: ({ color }) => <TabIcon label="🎯" />,
        }}
      />
      <Tab.Screen
        name="Leaderboard"
        component={LeaderboardScreen}
        options={{
          tabBarIcon: ({ color }) => <TabIcon label="🏆" />,
        }}
      />
      <Tab.Screen
        name="Cashout"
        component={CashoutScreen}
        options={{
          tabBarLabel: 'Cashout',
          tabBarIcon: ({ color }) => <TabIcon label="💰" />,
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ color }) => <TabIcon label="👤" />,
        }}
      />
    </Tab.Navigator>
  );
}

// Simple emoji icon (replace with proper icon library in production)
function TabIcon({ label }: { label: string }) {
  return (
    <View style={{ alignItems: 'center', justifyContent: 'center' }}>
      <View><React.Fragment>{/* icon */}</React.Fragment></View>
    </View>
  );
}

export default function AppNavigator() {
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    isAuthenticated().then((auth) => {
      setLoggedIn(auth);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {loggedIn ? (
          <Stack.Screen name="Main" component={MainTabs} />
        ) : (
          <Stack.Screen name="Login" component={LoginScreen} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
