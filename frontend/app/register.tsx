import React, { useState } from "react";
import { View, Text, Pressable, TextInput, ActivityIndicator } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { Wallet, Eye, EyeSlash } from "phosphor-react-native";
import * as Haptics from "expo-haptics";
import { Platform } from "react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { useAuth } from "@/src/auth/AuthContext";
import { useToast } from "@/src/components/Toast";

export default function Register() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t, lang } = useI18n();
  const { register } = useAuth();
  const toast = useToast();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!name.trim() || !email.trim() || !password) {
      toast.show(t("fill_all_fields"), "error");
      return;
    }
    if (password.length < 6) {
      toast.show(t("password_placeholder"), "error");
      return;
    }
    setBusy(true);
    try {
      await register(name.trim(), email.trim(), password, lang);
      if (Platform.OS !== "web") Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.replace("/(tabs)");
    } catch (e: any) {
      toast.show(e?.message || t("something_wrong"), "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={styles.root}>
      <KeyboardAwareScrollView
        style={styles.flex}
        contentContainerStyle={[styles.content, { paddingTop: insets.top + 40 }]}
        bottomOffset={90}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.logoCircle}>
          <Wallet size={30} color={colors.onBrandPrimary} weight="fill" />
        </View>
        <Text style={styles.title}>{t("register")}</Text>
        <Text style={styles.sub}>{t("create_account_sub")}</Text>

        <View style={styles.form}>
          <Text style={styles.label}>{t("full_name")}</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder={t("name_placeholder")}
            placeholderTextColor={colors.muted}
            testID="register-name"
          />

          <Text style={styles.label}>{t("email")}</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            placeholder={t("email_placeholder")}
            placeholderTextColor={colors.muted}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            testID="register-email"
          />

          <Text style={styles.label}>{t("password")}</Text>
          <View style={styles.passwordRow}>
            <TextInput
              style={styles.passwordInput}
              value={password}
              onChangeText={setPassword}
              placeholder={t("password_placeholder")}
              placeholderTextColor={colors.muted}
              secureTextEntry={!show}
              autoCapitalize="none"
              testID="register-password"
            />
            <Pressable onPress={() => setShow((s) => !s)} hitSlop={10} testID="register-toggle-password">
              {show ? (
                <EyeSlash size={20} color={colors.muted} />
              ) : (
                <Eye size={20} color={colors.muted} />
              )}
            </Pressable>
          </View>
        </View>

        <Pressable style={styles.switchRow} onPress={() => router.replace("/login")} testID="go-login">
          <Text style={styles.switchMuted}>{t("have_account")} </Text>
          <Text style={styles.switchLink}>{t("sign_in")}</Text>
        </Pressable>
      </KeyboardAwareScrollView>

      <KeyboardStickyView offset={{ closed: 0, opened: 0 }}>
        <View style={[styles.footer, { paddingBottom: insets.bottom + 12 }]}>
          <Pressable
            style={[styles.cta, busy && styles.ctaDisabled]}
            onPress={submit}
            disabled={busy}
            testID="register-submit"
          >
            {busy ? (
              <ActivityIndicator color={colors.onBrandPrimary} />
            ) : (
              <Text style={styles.ctaText}>{t("register")}</Text>
            )}
          </Pressable>
        </View>
      </KeyboardStickyView>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  root: { flex: 1, backgroundColor: colors.surface },
  flex: { flex: 1 },
  content: { paddingHorizontal: 24, paddingBottom: 24 },
  logoCircle: {
    width: 64,
    height: 64,
    borderRadius: 20,
    backgroundColor: colors.brandPrimary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
  },
  title: { fontSize: 26, fontWeight: "800", color: colors.onSurface },
  sub: { fontSize: 14, color: colors.muted, marginTop: 6, marginBottom: 24 },
  form: { gap: 8 },
  label: { fontSize: 13, fontWeight: "600", color: colors.onSurfaceSecondary, marginTop: 12 },
  input: {
    backgroundColor: colors.surfaceSecondary,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 14,
    fontSize: 15,
    color: colors.onSurface,
  },
  passwordRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surfaceSecondary,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: 14,
  },
  passwordInput: { flex: 1, paddingVertical: 14, fontSize: 15, color: colors.onSurface },
  switchRow: { flexDirection: "row", justifyContent: "center", marginTop: 24 },
  switchMuted: { color: colors.muted, fontSize: 14 },
  switchLink: { color: colors.brandPrimary, fontSize: 14, fontWeight: "700" },
  footer: {
    paddingHorizontal: 24,
    paddingTop: 12,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
  },
  cta: {
    backgroundColor: colors.brandPrimary,
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: "center",
  },
  ctaDisabled: { opacity: 0.7 },
  ctaText: { color: colors.onBrandPrimary, fontSize: 16, fontWeight: "700" },
}));
