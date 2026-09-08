import React, { useState } from "react";
import { View, Text, Pressable, ScrollView } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { CaretLeft, Globe, SignOut, Check, CurrencyInr, User } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { useAuth } from "@/src/auth/AuthContext";
import { api } from "@/src/api/client";
import { LANGUAGES, LangCode } from "@/src/i18n/translations";
import { initials } from "@/src/lib/format";
import { BottomSheet } from "@/src/components/BottomSheet";
import { useToast } from "@/src/components/Toast";

export default function Settings() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t, lang, setLang } = useI18n();
  const { user, logout } = useAuth();
  const toast = useToast();

  const [langSheet, setLangSheet] = useState(false);

  const currentLang = LANGUAGES.find((l) => l.code === lang);

  const changeLang = async (code: LangCode) => {
    await setLang(code);
    setLangSheet(false);
    try {
      await api.put("/auth/language", { language: code });
    } catch {
      // ignore
    }
    toast.show(t("save"), "success");
  };

  const doLogout = async () => {
    await logout();
    router.replace("/login");
  };

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.backBtn} testID="settings-back">
          <CaretLeft size={22} color={colors.onSurface} weight="bold" />
        </Pressable>
        <Text style={styles.title}>{t("settings")}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 24 }}>
        {/* Profile */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials(user?.name ?? "U")}</Text>
          </View>
          <Text style={styles.profileName} testID="settings-name">
            {user?.name}
          </Text>
          <Text style={styles.profileEmail}>{user?.email}</Text>
          <View style={styles.memberBadge}>
            <User size={13} color={colors.brand} weight="fill" />
            <Text style={styles.memberText}>{t("member")}</Text>
          </View>
        </View>

        {/* Preferences */}
        <Text style={styles.sectionLabel}>{t("preferences")}</Text>
        <View style={styles.group}>
          <Pressable style={styles.item} onPress={() => setLangSheet(true)} testID="settings-language">
            <View style={styles.itemIcon}>
              <Globe size={20} color={colors.brand} weight="fill" />
            </View>
            <Text style={styles.itemLabel}>{t("language")}</Text>
            <Text style={styles.itemValue}>{currentLang?.native}</Text>
          </Pressable>
          <View style={styles.divider} />
          <View style={styles.item}>
            <View style={styles.itemIcon}>
              <CurrencyInr size={20} color={colors.brand} weight="fill" />
            </View>
            <Text style={styles.itemLabel}>{t("currency")}</Text>
            <Text style={styles.itemValue}>INR (₹)</Text>
          </View>
        </View>

        {/* Logout */}
        <Pressable style={styles.logoutBtn} onPress={doLogout} testID="settings-logout">
          <SignOut size={20} color={colors.error} weight="bold" />
          <Text style={styles.logoutText}>{t("logout")}</Text>
        </Pressable>
      </ScrollView>

      <BottomSheet visible={langSheet} onClose={() => setLangSheet(false)} title={t("language")} testID="language-sheet">
        <View style={{ gap: 8 }}>
          {LANGUAGES.map((l) => {
            const active = l.code === lang;
            return (
              <Pressable
                key={l.code}
                style={[styles.langRow, active && styles.langRowActive]}
                onPress={() => changeLang(l.code)}
                testID={`settings-lang-${l.code}`}
              >
                <View>
                  <Text style={[styles.langNative, active && { color: colors.brand }]}>{l.native}</Text>
                  <Text style={styles.langEnglish}>{l.english}</Text>
                </View>
                {active ? (
                  <View style={styles.check}>
                    <Check size={14} color={colors.onBrandPrimary} weight="bold" />
                  </View>
                ) : null}
              </Pressable>
            );
          })}
        </View>
      </BottomSheet>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  root: { flex: 1, backgroundColor: colors.surface },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surfaceSecondary,
    alignItems: "center",
    justifyContent: "center",
  },
  title: { fontSize: 18, fontWeight: "800", color: colors.onSurface },
  profileCard: {
    alignItems: "center",
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 20,
    padding: 24,
    marginBottom: 24,
  },
  avatar: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: colors.brandPrimary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  avatarText: { color: colors.onBrandPrimary, fontSize: 28, fontWeight: "800" },
  profileName: { fontSize: 20, fontWeight: "800", color: colors.onSurface },
  profileEmail: { fontSize: 14, color: colors.muted, marginTop: 2 },
  memberBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: colors.brandTertiary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    marginTop: 12,
  },
  memberText: { color: colors.brand, fontSize: 12, fontWeight: "700" },
  sectionLabel: { fontSize: 13, fontWeight: "700", color: colors.muted, marginBottom: 10, textTransform: "uppercase" },
  group: {
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 16,
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  item: { flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 16 },
  itemIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: colors.brandTertiary,
    alignItems: "center",
    justifyContent: "center",
  },
  itemLabel: { flex: 1, fontSize: 15, fontWeight: "600", color: colors.onSurface },
  itemValue: { fontSize: 15, color: colors.muted, fontWeight: "600" },
  divider: { height: 1, backgroundColor: colors.divider },
  logoutBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: colors.surfaceSecondary,
    paddingVertical: 16,
    borderRadius: 14,
  },
  logoutText: { color: colors.error, fontSize: 15, fontWeight: "700" },
  langRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  langRowActive: { borderColor: colors.brandPrimary, backgroundColor: colors.brandTertiary },
  langNative: { fontSize: 16, fontWeight: "700", color: colors.onSurface },
  langEnglish: { fontSize: 12, color: colors.muted, marginTop: 2 },
  check: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: colors.brandPrimary,
    alignItems: "center",
    justifyContent: "center",
  },
}));
