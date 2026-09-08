import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  Pressable,
  ActivityIndicator,
  TextInput,
  RefreshControl,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Target, Trash } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";
import { formatCurrency, categoryLabelKey } from "@/src/lib/format";
import { CategoryIcon } from "@/src/components/CategoryIcon";
import { BottomSheet } from "@/src/components/BottomSheet";
import { useToast } from "@/src/components/Toast";

type Budget = { id: string; name: string; category: string; limit: number; spent: number };
type Goal = { id: string; name: string; target: number; saved: number };

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

export default function Budgets() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t } = useI18n();
  const toast = useToast();
  const qc = useQueryClient();

  const [addGoalTarget, setAddGoalTarget] = useState<Goal | null>(null);
  const [addAmount, setAddAmount] = useState("");

  const budgetsQ = useQuery<Budget[]>({ queryKey: ["budgets"], queryFn: () => api.get("/budgets") });
  const goalsQ = useQuery<Goal[]>({ queryKey: ["goals"], queryFn: () => api.get("/goals") });

  const addMoney = useMutation({
    mutationFn: ({ id, amount }: { id: string; amount: number }) =>
      api.post(`/goals/${id}/add`, { amount }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals"] });
      setAddGoalTarget(null);
      setAddAmount("");
      toast.show(t("save"), "success");
    },
  });

  const delBudget = useMutation({
    mutationFn: (id: string) => api.del(`/budgets/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["budgets"] }),
  });
  const delGoal = useMutation({
    mutationFn: (id: string) => api.del(`/goals/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });

  const loading = budgetsQ.isLoading || goalsQ.isLoading;

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Text style={styles.title}>{t("budgets")}</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.brandPrimary} />
        </View>
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ padding: 16, paddingBottom: 24 }}
          refreshControl={
            <RefreshControl
              refreshing={budgetsQ.isRefetching || goalsQ.isRefetching}
              onRefresh={() => {
                budgetsQ.refetch();
                goalsQ.refetch();
              }}
              tintColor={colors.brandPrimary}
            />
          }
        >
          {/* Budgets */}
          <View style={styles.sectionHead}>
            <Text style={styles.sectionTitle}>{t("monthly_budgets")}</Text>
            <Pressable
              style={styles.addBtn}
              onPress={() => router.push("/add-budget")}
              testID="add-budget-btn"
            >
              <Plus size={16} color={colors.brand} weight="bold" />
              <Text style={styles.addBtnText}>{t("add_budget")}</Text>
            </Pressable>
          </View>

          {(budgetsQ.data?.length ?? 0) === 0 ? (
            <Text style={styles.emptyMuted}>{t("no_budgets")}</Text>
          ) : (
            budgetsQ.data!.map((b) => {
              const color = CAT_COLORS[b.category] ?? "#737373";
              const pct = Math.min((b.spent / b.limit) * 100, 100);
              const over = b.spent > b.limit;
              return (
                <View key={b.id} style={styles.card} testID={`budget-${b.id}`}>
                  <View style={styles.cardHead}>
                    <View style={[styles.catIcon, { backgroundColor: `${color}22` }]}>
                      <CategoryIcon category={b.category} color={color} size={18} />
                    </View>
                    <Text style={styles.cardName}>{b.name}</Text>
                    <Pressable onPress={() => delBudget.mutate(b.id)} hitSlop={8} testID={`budget-delete-${b.id}`}>
                      <Trash size={16} color={colors.muted} />
                    </Pressable>
                  </View>
                  <View style={styles.track}>
                    <View
                      style={[
                        styles.fill,
                        { width: `${pct}%`, backgroundColor: over ? colors.error : color },
                      ]}
                    />
                  </View>
                  <View style={styles.cardFoot}>
                    <Text style={[styles.footLeft, over && { color: colors.error }]}>
                      {formatCurrency(b.spent)} {t("of")} {formatCurrency(b.limit)}
                    </Text>
                    <Text style={[styles.footRight, over && { color: colors.error }]}>
                      {over ? t("over_budget") : `${formatCurrency(b.limit - b.spent)} ${t("left")}`}
                    </Text>
                  </View>
                </View>
              );
            })
          )}

          {/* Goals */}
          <View style={[styles.sectionHead, { marginTop: 24 }]}>
            <Text style={styles.sectionTitle}>{t("savings_goals")}</Text>
            <Pressable style={styles.addBtn} onPress={() => router.push("/add-goal")} testID="add-goal-btn">
              <Plus size={16} color={colors.brand} weight="bold" />
              <Text style={styles.addBtnText}>{t("add_goal")}</Text>
            </Pressable>
          </View>

          {(goalsQ.data?.length ?? 0) === 0 ? (
            <Text style={styles.emptyMuted}>{t("no_goals")}</Text>
          ) : (
            goalsQ.data!.map((g) => {
              const pct = Math.min((g.saved / g.target) * 100, 100);
              return (
                <View key={g.id} style={styles.card} testID={`goal-${g.id}`}>
                  <View style={styles.cardHead}>
                    <View style={[styles.catIcon, { backgroundColor: colors.brandTertiary }]}>
                      <Target size={18} color={colors.brand} weight="fill" />
                    </View>
                    <Text style={styles.cardName}>{g.name}</Text>
                    <Text style={styles.pctText}>{Math.round(pct)}%</Text>
                    <Pressable onPress={() => delGoal.mutate(g.id)} hitSlop={8} testID={`goal-delete-${g.id}`}>
                      <Trash size={16} color={colors.muted} />
                    </Pressable>
                  </View>
                  <View style={styles.track}>
                    <View style={[styles.fill, { width: `${pct}%`, backgroundColor: colors.brandPrimary }]} />
                  </View>
                  <View style={styles.cardFoot}>
                    <Text style={styles.footLeft}>
                      {formatCurrency(g.saved)} {t("of")} {formatCurrency(g.target)}
                    </Text>
                    <Pressable
                      style={styles.addMoneyBtn}
                      onPress={() => {
                        setAddGoalTarget(g);
                        setAddAmount("");
                      }}
                      testID={`goal-add-money-${g.id}`}
                    >
                      <Text style={styles.addMoneyText}>{t("add_money")}</Text>
                    </Pressable>
                  </View>
                </View>
              );
            })
          )}
        </ScrollView>
      )}

      <BottomSheet
        visible={!!addGoalTarget}
        onClose={() => setAddGoalTarget(null)}
        title={`${t("add_money")} · ${addGoalTarget?.name ?? ""}`}
        testID="add-money-sheet"
      >
        <Text style={styles.label}>{t("amount")}</Text>
        <View style={styles.amountBox}>
          <Text style={styles.rupee}>₹</Text>
          <TextInput
            style={styles.amountInput}
            value={addAmount}
            onChangeText={setAddAmount}
            placeholder="0"
            placeholderTextColor={colors.muted}
            keyboardType="numeric"
            autoFocus
            testID="add-money-input"
          />
        </View>
        <Pressable
          style={styles.sheetCta}
          onPress={() => {
            const amt = parseFloat(addAmount);
            if (!amt || amt <= 0) {
              toast.show(t("enter_valid_amount"), "error");
              return;
            }
            addMoney.mutate({ id: addGoalTarget!.id, amount: amt });
          }}
          testID="add-money-save"
        >
          <Text style={styles.sheetCtaText}>{t("save")}</Text>
        </Pressable>
      </BottomSheet>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  root: { flex: 1, backgroundColor: colors.surface },
  header: {
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  title: { fontSize: 22, fontWeight: "800", color: colors.onSurface },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  sectionHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 12 },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: colors.onSurface },
  addBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: colors.brandTertiary,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 999,
  },
  addBtnText: { color: colors.brand, fontSize: 13, fontWeight: "700" },
  emptyMuted: { color: colors.muted, fontSize: 14, paddingVertical: 12, textAlign: "center" },
  card: {
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  cardHead: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 12 },
  catIcon: { width: 34, height: 34, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  cardName: { flex: 1, fontSize: 15, fontWeight: "700", color: colors.onSurface },
  pctText: { fontSize: 13, fontWeight: "700", color: colors.brand },
  track: { height: 8, borderRadius: 999, backgroundColor: colors.surfaceTertiary, overflow: "hidden" },
  fill: { height: 8, borderRadius: 999 },
  cardFoot: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 10 },
  footLeft: { fontSize: 13, color: colors.onSurfaceSecondary, fontWeight: "600" },
  footRight: { fontSize: 13, color: colors.muted, fontWeight: "600" },
  addMoneyBtn: {
    backgroundColor: colors.brandPrimary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
  },
  addMoneyText: { color: colors.onBrandPrimary, fontSize: 12, fontWeight: "700" },
  label: { fontSize: 13, fontWeight: "600", color: colors.onSurfaceSecondary, marginBottom: 8 },
  amountBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  rupee: { fontSize: 24, fontWeight: "800", color: colors.onSurface, marginRight: 6 },
  amountInput: { flex: 1, paddingVertical: 16, fontSize: 24, fontWeight: "800", color: colors.onSurface },
  sheetCta: { backgroundColor: colors.brandPrimary, paddingVertical: 16, borderRadius: 14, alignItems: "center" },
  sheetCtaText: { color: colors.onBrandPrimary, fontSize: 16, fontWeight: "700" },
}));
