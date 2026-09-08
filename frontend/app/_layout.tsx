import { QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { LogBox } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { KeyboardProvider } from "react-native-keyboard-controller";
import { StatusBar } from "expo-status-bar";

import { ErrorBoundary } from "@/src/components/error-boundary";
import { queryClient } from "@/src/query-client";
import { I18nProvider } from "@/src/i18n";
import { AuthProvider } from "@/src/auth/AuthContext";
import { ToastProvider } from "@/src/components/Toast";

LogBox.ignoreAllLogs(true);

export default function RootLayout() {
  return (
    <ErrorBoundary>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <SafeAreaProvider>
          <KeyboardProvider>
            <QueryClientProvider client={queryClient}>
              <I18nProvider>
                <AuthProvider>
                  <ToastProvider>
                    <StatusBar style="auto" />
                    <Stack screenOptions={{ headerShown: false }}>
                      <Stack.Screen name="index" />
                      <Stack.Screen name="onboarding" />
                      <Stack.Screen name="login" />
                      <Stack.Screen name="register" />
                      <Stack.Screen name="(tabs)" />
                      <Stack.Screen name="settings" options={{ presentation: "card" }} />
                      <Stack.Screen name="add-transaction" options={{ presentation: "modal" }} />
                      <Stack.Screen name="add-budget" options={{ presentation: "modal" }} />
                      <Stack.Screen name="add-goal" options={{ presentation: "modal" }} />
                    </Stack>
                  </ToastProvider>
                </AuthProvider>
              </I18nProvider>
            </QueryClientProvider>
          </KeyboardProvider>
        </SafeAreaProvider>
      </GestureHandlerRootView>
    </ErrorBoundary>
  );
}
