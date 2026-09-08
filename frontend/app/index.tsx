import { Redirect } from "expo-router";
import { View, ActivityIndicator } from "react-native";

import { useAuth } from "@/src/auth/AuthContext";
import { useI18n } from "@/src/i18n";
import { useTheme } from "@/src/theme";

export default function Index() {
  const { colors } = useTheme();
  const { ready, hasChosen } = useI18n();
  const { loading, user } = useAuth();

  if (!ready || loading) {
    return (
      <View
        style={{ flex: 1, backgroundColor: colors.surface, alignItems: "center", justifyContent: "center" }}
        testID="splash-loader"
      >
        <ActivityIndicator size="large" color={colors.brandPrimary} />
      </View>
    );
  }

  if (!hasChosen) return <Redirect href="/onboarding" />;
  if (!user) return <Redirect href="/login" />;
  return <Redirect href="/(tabs)" />;
}
