import React from "react";
import {
  View,
  Text,
  ScrollView,
  Pressable,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import {
  Gear,
  ArrowDownLeft,
  ArrowUpRight,
  PiggyBank,
  Plus,
  Minus,
  Bank,
  Receipt,
  CaretRight,
  Clock,
} from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { useAuth } from "@/src/auth/AuthContext";
import { api } from "@/src/api/client";
import { formatCurrency, formatDate, categoryLabelKey } from "@/src/lib/format";
import { DonutChart } from "@/src/components/DonutChart";
import { CategoryIcon } from "@/src/components/CategoryIcon";
import { TrendBars, MonthPoint } from "@/src/components/TrendBars";

type Summary = {
  total_balance: number;
  income: number;
  expense: number;
  savings: number;
  spending_by_category: { category: string; amount: number; color: string }[];
  recent_transactions: {
    id: string;
    title: string;
    amount: number;
    type: string;
    category: string;
    date: string;
  }[];
};

export default function Dashboard() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t, lang } = useI18n();
  const { user } = useAuth();

  const { data, isLoading, isError, refetch, isRefetching } = useQuery<Summary>({
    queryKey: ["summary"],
    queryFn: () => api.get("/dashboard/summary"),
  });

  const trendsQ = useQuery<{ months: MonthPoint[] }>({
    queryKey: ["trends"],
    queryFn: () => api.get("/dashboard/trends"),
  });

  const billsQ = useQuery<
    { id: string; name: string; amount: number; days_until: number; paid_this_month: boolean }[]
  >({
    queryKey: ["bills"],
    queryFn: () => api.get("/bills"),
  });

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return t("good_morning");
    if (h < 17) return t("good_afternoon");
    return t("good_evening");
  };

  const quickActions = [
    { key: "add_expense", icon: Minus, onPress: () => router.push({ pathname: "/add-transaction", params: { type: "expense" } }) },
    { key: "add_income", icon: Plus, onPress: () => router.push({ pathname: "/add-transaction", params: { type: "income" } }) },
    { key: "accounts", icon: Bank, onPress: () => router.push("/accounts") },
    { key: "bills", icon: Receipt, onPress: () => router.push("/bills") },
  ] as const;

  return (
    <View style={styles.root}>
      {/* Sticky header */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <View>
          <Text style={styles.greeting}>{greeting()}</Text>
          <Text style={styles.name} testID="dashboard-user-name">
            {user?.name ?? ""}
          </Text>
        </View>
        <Pressable style={styles.gearBtn} onPress={() => router.push("/settings")} testID="open-settings">
          <Gear size={22} color={colors.onSurface} />
        </Pressable>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.brandPrimary} />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <Text style={styles.errText}>{t("something_wrong")}</Text>
          <Pressable style={styles.retryBtn} onPress={() => refetch()} testID="dashboard-retry">
            <Text style={styles.retryText}>{t("retry")}</Text>
          </Pressable>
        </View>
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ padding: 16, paddingBottom: 24 }}
          refreshControl={
            <RefreshControl refreshing={isRefetching} onRefresh={refetch} tintColor={colors.brandPrimary} />
          }
        >
          {/* Balance hero */}
          <LinearGradient
            colors={[colors.brand, colors.brandPrimary]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.hero}
          >
            <Text style={styles.heroLabel}>{t("total_balance")}</Text>
            <Text style={styles.heroBalance} testID="dashboard-total-balance">
              {formatCurrency(data?.total_balance ?? 0)}
            </Text>

            <View style={styles.heroStats}>
              <View style={styles.statItem}>
                <View style={styles.statIcon}>
                  <ArrowDownLeft size={15} color="#FFFFFF" weight="bold" />
                </View>
                <View>
                  <Text style={styles.statLabel}>{t("income")}</Text>
                  <Text style={styles.statValue}>{formatCurrency(data?.income ?? 0)}</Text>
                </View>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <View style={styles.statIcon}>
                  <ArrowUpRight size={15} color="#FFFFFF" weight="bold" />
                </View>
                <View>
                  <Text style={styles.statLabel}>{t("expense")}</Text>
                  <Text style={styles.statValue}>{formatCurrency(data?.expense ?? 0)}</Text>
                </View>
              </View>
            </View>
          </LinearGradient>

          {/* Savings pill */}
          <View style={styles.savingsRow}>
            <View style={styles.savingsIcon}>
              <PiggyBank size={20} color={colors.brand} weight="fill" />
            </View>
            <Text style={styles.savingsLabel}>{t("savings")} · {t("this_month")}</Text>
            <Text
              style={[
                styles.savingsValue,
                { color: (data?.savings ?? 0) >= 0 ? colors.success : colors.error },
              ]}
            >
              {formatCurrency(data?.savings ?? 0, (data?.savings ?? 0) > 0)}
            </Text>
          </View>

          {/* Quick actions */}
          <Text style={styles.sectionTitle}>{t("quick_actions")}</Text>
          <View style={styles.quickRow}>
            {quickActions.map((a) => {
              const Icon = a.icon;
              return (
                <Pressable key={a.key} style={styles.quickItem} onPress={a.onPress} testID={`quick-${a.key}`}>
                  <View style={styles.quickIconWrap}>
                    <Icon size={22} color={colors.brand} weight="bold" />
                  </View>
                  <Text style={styles.quickLabel}>{t(a.key as any)}</Text>
                </Pressable>
              );
            })}
          </View>

          {/* Spending by category */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{t("spending_by_category")}</Text>
            {(data?.spending_by_category?.length ?? 0) === 0 ? (
              <Text style={styles.emptyMuted}>{t("no_spending")}</Text>
            ) : (
              <View style={styles.donutRow}>
                <View style={styles.donutWrap}>
                  <DonutChart
                    segments={(data?.spending_by_category ?? []).map((s) => ({
                      amount: s.amount,
                      color: s.color,
                    }))}
                    trackColor={colors.surfaceTertiary}
                    size={140}
                    strokeWidth={20}
                  />
                  <View style={styles.donutCenter}>
                    <Text style={styles.donutCenterValue}>{formatCurrency(data?.expense ?? 0)}</Text>
                    <Text style={styles.donutCenterLabel}>{t("expense")}</Text>
                  </View>
                </View>
                <View style={styles.legend}>
                  {(data?.spending_by_category ?? []).slice(0, 5).map((s) => (
                    <View key={s.category} style={styles.legendRow}>
                      <View style={[styles.legendDot, { backgroundColor: s.color }]} />
                      <Text style={styles.legendLabel} numberOfLines={1}>
                        {t(categoryLabelKey(s.category))}
                      </Text>
                      <Text style={styles.legendValue}>{formatCurrency(s.amount)}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
          </View>

          {/* Spending trends */}
          <Pressable style={styles.recentHeader} onPress={() => router.push("/trends")} testID="open-trends">
            <Text style={styles.sectionTitle}>{t("spending_trends")}</Text>
            <View style={styles.seeAllRow}>
              <Text style={styles.seeAll}>{t("see_all")}</Text>
              <CaretRight size={14} color={colors.brandPrimary} weight="bold" />
            </View>
          </Pressable>
          <Pressable style={styles.card} onPress={() => router.push("/trends")}>
            <Text style={styles.trendCaption}>{t("last_6_months")}</Text>
            <TrendBars months={trendsQ.data?.months ?? []} lang={lang} showIncome={false} height={120} />
          </Pressable>

          {/* Upcoming bills */}
          {(billsQ.data?.length ?? 0) > 0 ? (
            <>
              <Pressable style={styles.recentHeader} onPress={() => router.push("/bills")} testID="open-bills">
                <Text style={styles.sectionTitle}>{t("upcoming_bills")}</Text>
                <View style={styles.seeAllRow}>
                  <Text style={styles.seeAll}>{t("see_all")}</Text>
                  <CaretRight size={14} color={colors.brandPrimary} weight="bold" />
                </View>
              </Pressable>
              <View style={styles.card}>
                {(billsQ.data ?? [])
                  .filter((b) => !b.paid_this_month)
                  .slice(0, 3)
                  .map((b, i, arr) => (
                    <View
                      key={b.id}
                      style={[styles.txRow, i < arr.length - 1 && styles.txRowBorder]}
                      testID={`upcoming-bill-${b.id}`}
                    >
                      <View style={[styles.txIcon, { backgroundColor: colors.brandTertiary }]}>
                        <Receipt size={20} color={colors.brand} weight="fill" />
                      </View>
                      <View style={styles.txMid}>
                        <Text style={styles.txTitle} numberOfLines={1}>
                          {b.name}
                        </Text>
                        <View style={styles.billDueRow}>
                          <Clock size={12} color={colors.muted} weight="fill" />
                          <Text style={styles.txDate}>
                            {b.days_until === 0
                              ? t("due_today")
                              : b.days_until === 1
                                ? t("due_tomorrow")
                                : `${t("due_in")} ${b.days_until} ${t("days")}`}
                          </Text>
                        </View>
                      </View>
                      <Text style={styles.txAmount}>{formatCurrency(b.amount)}</Text>
                    </View>
                  ))}
              </View>
            </>
          ) : null}

          {/* Recent transactions */}
          <View style={styles.recentHeader}>
            <Text style={styles.sectionTitle}>{t("recent_transactions")}</Text>
            <Pressable onPress={() => router.push("/(tabs)/transactions")} testID="see-all-transactions">
              <Text style={styles.seeAll}>{t("see_all")}</Text>
            </Pressable>
          </View>
          <View style={styles.card}>
            {(data?.recent_transactions ?? []).map((tx, i, arr) => (
              <View
                key={tx.id}
                style={[styles.txRow, i < arr.length - 1 && styles.txRowBorder]}
                testID={`recent-tx-${tx.id}`}
              >
                <View style={[styles.txIcon, { backgroundColor: `${txColor(tx.category)}22` }]}>
                  <CategoryIcon category={tx.category} color={txColor(tx.category)} size={20} />
                </View>
                <View style={styles.txMid}>
                  <Text style={styles.txTitle} numberOfLines={1}>
                    {tx.title}
                  </Text>
                  <Text style={styles.txDate}>{formatDate(tx.date, lang)}</Text>
                </View>
                <Text
                  style={[
                    styles.txAmount,
                    { color: tx.type === "income" ? colors.success : colors.onSurface },
                  ]}
                >
                  {tx.type === "income" ? "+" : "-"}
                  {formatCurrency(tx.amount)}
                </Text>
              </View>
            ))}
          </View>
        </ScrollView>
      )}
    </View>
  );
}

const CAT_COLORS: Record<string, string> = {
  food: "#F97316",
  shopping: "#8B5CF6",
  transport: "#0EA5E9",
  bills: "#EF4444",
  entertainment: "#EC4899",
  health: "#14B8A6",
  salary: "#16A34A",
  investment: "#059669",
  groceries: "#84CC16",
  other: "#737373",
};
function txColor(cat: string) {
  return CAT_COLORS[cat] ?? "#737373";
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
  },
  greeting: { fontSize: 13, color: colors.muted },
  name: { fontSize: 22, fontWeight: "800", color: colors.onSurface },
  gearBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: colors.surfaceSecondary,
    alignItems: "center",
    justifyContent: "center",
  },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12 },
  errText: { color: colors.muted, fontSize: 15 },
  retryBtn: {
    backgroundColor: colors.brandPrimary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 10,
  },
  retryText: { color: colors.onBrandPrimary, fontWeight: "700" },
  hero: { borderRadius: 20, padding: 20 },
  heroLabel: { color: "rgba(255,255,255,0.85)", fontSize: 13, fontWeight: "600" },
  heroBalance: { color: "#FFFFFF", fontSize: 34, fontWeight: "800", marginTop: 6 },
  heroStats: { flexDirection: "row", alignItems: "center", marginTop: 20 },
  statItem: { flex: 1, flexDirection: "row", alignItems: "center", gap: 10 },
  statIcon: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: "rgba(255,255,255,0.2)",
    alignItems: "center",
    justifyContent: "center",
  },
  statDivider: { width: 1, height: 32, backgroundColor: "rgba(255,255,255,0.25)" },
  statLabel: { color: "rgba(255,255,255,0.8)", fontSize: 12 },
  statValue: { color: "#FFFFFF", fontSize: 15, fontWeight: "700" },
  savingsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 14,
    padding: 14,
    marginTop: 12,
  },
  savingsIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.brandTertiary,
    alignItems: "center",
    justifyContent: "center",
  },
  savingsLabel: { flex: 1, fontSize: 13, color: colors.onSurfaceSecondary, fontWeight: "600" },
  savingsValue: { fontSize: 16, fontWeight: "800" },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: colors.onSurface, marginTop: 20, marginBottom: 12 },
  quickRow: { flexDirection: "row", justifyContent: "space-between" },
  quickItem: { alignItems: "center", gap: 8, flex: 1 },
  quickIconWrap: {
    width: 54,
    height: 54,
    borderRadius: 18,
    backgroundColor: colors.brandTertiary,
    alignItems: "center",
    justifyContent: "center",
  },
  quickLabel: { fontSize: 12, color: colors.onSurfaceSecondary, fontWeight: "600", textAlign: "center" },
  card: {
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 16,
    padding: 16,
  },
  cardTitle: { fontSize: 15, fontWeight: "700", color: colors.onSurface, marginBottom: 14 },
  emptyMuted: { color: colors.muted, fontSize: 14, textAlign: "center", paddingVertical: 12 },
  donutRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  donutWrap: { width: 140, height: 140, alignItems: "center", justifyContent: "center" },
  donutCenter: { position: "absolute", alignItems: "center" },
  donutCenterValue: { fontSize: 15, fontWeight: "800", color: colors.onSurface },
  donutCenterLabel: { fontSize: 11, color: colors.muted },
  legend: { flex: 1, gap: 10 },
  legendRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  legendDot: { width: 10, height: 10, borderRadius: 5 },
  legendLabel: { flex: 1, fontSize: 13, color: colors.onSurfaceSecondary },
  legendValue: { fontSize: 13, fontWeight: "700", color: colors.onSurface },
  recentHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  seeAll: { color: colors.brandPrimary, fontSize: 13, fontWeight: "700", marginTop: 20, marginBottom: 12 },
  seeAllRow: { flexDirection: "row", alignItems: "center", gap: 3 },
  trendCaption: { fontSize: 12, color: colors.muted, fontWeight: "600", marginBottom: 16 },
  billDueRow: { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 2 },
  txRow: { flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 12 },
  txRowBorder: { borderBottomWidth: 1, borderBottomColor: colors.divider },
  txIcon: { width: 42, height: 42, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  txMid: { flex: 1 },
  txTitle: { fontSize: 15, fontWeight: "600", color: colors.onSurface },
  txDate: { fontSize: 12, color: colors.muted, marginTop: 2 },
  txAmount: { fontSize: 15, fontWeight: "700" },
}));
