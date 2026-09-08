import React, { useState } from "react";
import { View, Text, Pressable, ScrollView } from "react-native";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { Globe, Check, ArrowRight } from "phosphor-react-native";
import * as Haptics from "expo-haptics";
import { Platform } from "react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { LANGUAGES, LangCode, translations } from "@/src/i18n/translations";

const HERO =
  "https://images.unsplash.com/photo-1614851099511-773084f6911d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxNzV8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBhYnN0cmFjdCUyMGdyYWRpZW50JTIwYmFja2dyb3VuZHxlbnwwfHx8fDE3ODg4NTc2MzB8MA&ixlib=rb-4.1.0&q=85";

export default function Onboarding() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { setLang } = useI18n();
  const [selected, setSelected] = useState<LangCode>("en");

  const onContinue = async () => {
    if (Platform.OS !== "web") Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    await setLang(selected);
    router.replace("/login");
  };

  const t = (k: string) => translations[selected]?.[k] ?? translations.en[k] ?? k;

  return (
    <View style={styles.root}>
      <View style={styles.hero}>
        <Image source={{ uri: HERO }} style={styles.heroImg} contentFit="cover" />
        <LinearGradient
          colors={["rgba(6,78,59,0.35)", "rgba(6,78,59,0.95)"]}
          style={styles.scrim}
        />
        <View style={[styles.heroContent, { paddingTop: insets.top + 24 }]}>
          <View style={styles.badge}>
            <Globe size={16} color="#FFFFFF" weight="fill" />
            <Text style={styles.badgeText}>IndicFinance</Text>
          </View>
          <Text style={styles.heroTitle}>{t("welcome_title")}</Text>
          <Text style={styles.heroSub}>{t("welcome_sub")}</Text>
        </View>
      </View>

      <ScrollView
        style={styles.body}
        contentContainerStyle={styles.bodyContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.pickTitle}>{t("choose_language")}</Text>
        <Text style={styles.pickSub}>{t("choose_language_sub")}</Text>

        <View style={styles.list}>
          {LANGUAGES.map((l) => {
            const active = selected === l.code;
            return (
              <Pressable
                key={l.code}
                onPress={() => {
                  if (Platform.OS !== "web") Haptics.selectionAsync();
                  setSelected(l.code);
                }}
                style={[styles.row, active && styles.rowActive]}
                testID={`lang-option-${l.code}`}
              >
                <View style={styles.rowLeft}>
                  <Text style={[styles.native, active && styles.nativeActive]}>{l.native}</Text>
                  <Text style={styles.english}>{l.english}</Text>
                </View>
                {active ? (
                  <View style={styles.checkCircle}>
                    <Check size={15} color={colors.onBrandPrimary} weight="bold" />
                  </View>
                ) : (
                  <View style={styles.emptyCircle} />
                )}
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      <View style={[styles.footer, { paddingBottom: insets.bottom + 16 }]}>
        <Pressable style={styles.cta} onPress={onContinue} testID="onboarding-continue">
          <Text style={styles.ctaText}>{t("get_started")}</Text>
          <ArrowRight size={20} color={colors.onBrandPrimary} weight="bold" />
        </Pressable>
      </View>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  root: { flex: 1, backgroundColor: colors.surface },
  hero: { height: 300 },
  heroImg: { ...({ position: "absolute" } as const), width: "100%", height: "100%" },
  scrim: { position: "absolute", width: "100%", height: "100%" },
  heroContent: { flex: 1, justifyContent: "flex-end", padding: 24 },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    alignSelf: "flex-start",
    backgroundColor: "rgba(255,255,255,0.18)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    marginBottom: 14,
  },
  badgeText: { color: "#FFFFFF", fontSize: 13, fontWeight: "700" },
  heroTitle: { color: "#FFFFFF", fontSize: 28, fontWeight: "800", lineHeight: 34 },
  heroSub: { color: "rgba(255,255,255,0.9)", fontSize: 14, lineHeight: 20, marginTop: 8 },
  body: { flex: 1 },
  bodyContent: { padding: 20, paddingBottom: 24 },
  pickTitle: { fontSize: 20, fontWeight: "800", color: colors.onSurface },
  pickSub: { fontSize: 13, color: colors.muted, marginTop: 4, marginBottom: 16 },
  list: { gap: 10 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
  },
  rowActive: { borderColor: colors.brandPrimary, backgroundColor: colors.brandTertiary },
  rowLeft: { flexDirection: "row", alignItems: "baseline", gap: 10 },
  native: { fontSize: 18, fontWeight: "700", color: colors.onSurface },
  nativeActive: { color: colors.brand },
  english: { fontSize: 13, color: colors.muted },
  checkCircle: {
    width: 24,
    height: 24,
    borderRadius: 999,
    backgroundColor: colors.brandPrimary,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyCircle: {
    width: 24,
    height: 24,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: colors.borderStrong,
  },
  footer: {
    paddingHorizontal: 20,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    backgroundColor: colors.surface,
  },
  cta: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: colors.brandPrimary,
    paddingVertical: 16,
    borderRadius: 16,
  },
  ctaText: { color: colors.onBrandPrimary, fontSize: 16, fontWeight: "700" },
}));
