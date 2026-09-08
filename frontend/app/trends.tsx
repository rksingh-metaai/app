import React from "react";
import { View, Text, Pressable, ScrollView, ActivityIndicator } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { CaretLeft, ArrowDownLeft, ArrowUpRight } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";
import { formatCurrency } from "@/src/lib/format";
import { TrendBars, MonthPoint } from "@/src/components/TrendBars";

const LOCALE: Record<string, string> = {
  en: "en-IN", hi: "hi-IN", ta: "ta-IN", te: "te-IN", bn: "bn-IN", mr: "mr-IN",
};

export default function Trends() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t, lang } = useI18n();

  const { data, isLoading } = useQuery<{ months: MonthPoint[] }>({
    queryKey: ["trends"],
    queryFn: () => api.get("/dashboard/trends"),
  });

  const months = data?.months ?? [];
  const totalExpense = months.reduce((s, m) => s + m.expense, 0);
  const totalIncome = months.reduce((s, m) => s + m.income, 0);
  const activeMonths = months.filter((m) => m.expense > 0).length || 1;
  const avgExpense = totalExpense / activeMonths;

  const monthLabel = (m: MonthPoint) => {
    try {
      return new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { month: "long", year: "numeric" }).format(
        new Date(m.year, m.month - 1, 1),
      );
    } catch {
      return `${m.month}/${m.year}`;
    }
  };

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.backBtn} testID="trends-back">
          <CaretLeft size={22} color={colors.onSurface} weight="bold" />
        </Pressable>
        <Text style={styles.title}>{t("spending_trends")}</Text>
        <View style={{ width: 40 }} />
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.brandPrimary} />
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 24 }} showsVerticalScrollIndicator={false}>
          <View style={styles.summaryRow}>
            <View style={styles.summaryCard}>
              <View style={[styles.sIcon, { backgroundColor: colors.brandTertiary }]}>
                <ArrowUpRight size={16} color={colors.error} weight="bold" />
              </View>
              <Text style={styles.sLabel}>{t("avg_expense")}</Text>
              <Text style={styles.sValue}>{formatCurrency(avgExpense)}</Text>
            </View>
            <View style={styles.summaryCard}>
              <View style={[styles.sIcon, { backgroundColor: colors.brandTertiary }]}>
                <ArrowDownLeft size={16} color={colors.success} weight="bold" />
              </View>
              <Text style={styles.sLabel}>{t("income")}</Text>
              <Text style={styles.sValue}>{formatCurrency(totalIncome / activeMonths)}</Text>
            </View>
          </View>

          <View style={styles.chartCard}>
            <Text style={styles.chartTitle}>{t("last_6_months")}</Text>
            <TrendBars months={months} lang={lang} showIncome height={160} />
          </View>

          {[...months].reverse().map((m, i) => (
            <View key={i} style={styles.monthRow} testID={`trend-month-${m.year}-${m.month}`}>
              <Text style={styles.monthName}>{monthLabel(m)}</Text>
              <View style={styles.monthVals}>
                <Text style={[styles.monthVal, { color: colors.success }]}>+{formatCurrency(m.income)}</Text>
                <Text style={[styles.monthVal, { color: colors.onSurface }]}>-{formatCurrency(m.expense)}</Text>
              </View>
            </View>
          ))}
        </ScrollView>
      )}
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
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  summaryRow: { flexDirection: "row", gap: 12, marginBottom: 16 },
  summaryCard: { flex: 1, backgroundColor: colors.surfaceSecondary, borderRadius: 16, padding: 16, gap: 6 },
  sIcon: { width: 32, height: 32, borderRadius: 10, alignItems: "center", justifyContent: "center", marginBottom: 4 },
  sLabel: { fontSize: 12, color: colors.muted, fontWeight: "600" },
  sValue: { fontSize: 18, fontWeight: "800", color: colors.onSurface },
  chartCard: { backgroundColor: colors.surfaceSecondary, borderRadius: 16, padding: 16, marginBottom: 20 },
  chartTitle: { fontSize: 15, fontWeight: "700", color: colors.onSurface, marginBottom: 20 },
  monthRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  monthName: { fontSize: 14, fontWeight: "600", color: colors.onSurface },
  monthVals: { alignItems: "flex-end", gap: 2 },
  monthVal: { fontSize: 13, fontWeight: "700" },
}));
