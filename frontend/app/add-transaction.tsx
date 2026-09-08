import React, { useState } from "react";
import { View, Text, Pressable, TextInput, ScrollView, ActivityIndicator } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter, useLocalSearchParams } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { X } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";
import {
  CATEGORY_COLORS,
  categoryLabelKey,
  accountLabelKey,
  formatCurrency,
} from "@/src/lib/format";
import { CategoryIcon } from "@/src/components/CategoryIcon";
import { useToast } from "@/src/components/Toast";

type Account = { id: string; name: string; type: string; balance: number };

const EXPENSE_CATS = ["food", "groceries", "shopping", "transport", "bills", "entertainment", "health", "other"];
const INCOME_CATS = ["salary", "investment", "other"];

export default function AddTransaction() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const params = useLocalSearchParams<{ type?: string }>();
  const { t } = useI18n();
  const toast = useToast();
  const qc = useQueryClient();

  const [type, setType] = useState<"income" | "expense">(
    params.type === "income" ? "income" : "expense",
  );
  const [amount, setAmount] = useState("");
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState(type === "income" ? "salary" : "food");
  const [accountId, setAccountId] = useState<string | null>(null);
  const [note, setNote] = useState("");

  const accountsQ = useQuery<Account[]>({ queryKey: ["accounts"], queryFn: () => api.get("/accounts") });

  React.useEffect(() => {
    if (accountsQ.data && accountsQ.data.length > 0 && !accountId) {
      setAccountId(accountsQ.data[0].id);
    }
  }, [accountsQ.data, accountId]);

  const cats = type === "income" ? INCOME_CATS : EXPENSE_CATS;

  const switchType = (newType: "income" | "expense") => {
    setType(newType);
    setCategory(newType === "income" ? "salary" : "food");
  };

  const save = useMutation({
    mutationFn: () =>
      api.post("/transactions", {
        type,
        amount: parseFloat(amount),
        title: title.trim(),
        category,
        account_id: accountId,
        note: note.trim() || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["summary"] });
      qc.invalidateQueries({ queryKey: ["accounts"] });
      qc.invalidateQueries({ queryKey: ["budgets"] });
      toast.show(t("save"), "success");
      router.back();
    },
    onError: () => toast.show(t("something_wrong"), "error"),
  });

  const onSave = () => {
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) {
      toast.show(t("enter_valid_amount"), "error");
      return;
    }
    if (!title.trim()) {
      toast.show(t("fill_all_fields"), "error");
      return;
    }
    save.mutate();
  };

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Text style={styles.title}>{t("new_transaction")}</Text>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.closeBtn} testID="add-tx-close">
          <X size={22} color={colors.onSurface} weight="bold" />
        </Pressable>
      </View>

      <KeyboardAwareScrollView
        style={styles.flex}
        contentContainerStyle={styles.content}
        bottomOffset={90}
        showsVerticalScrollIndicator={false}
      >
        {/* type toggle */}
        <View style={styles.toggle}>
          <Pressable
            style={[styles.toggleBtn, type === "expense" && styles.toggleActive]}
            onPress={() => switchType("expense")}
            testID="type-expense"
          >
            <Text style={[styles.toggleText, type === "expense" && styles.toggleTextActive]}>
              {t("add_expense")}
            </Text>
          </Pressable>
          <Pressable
            style={[styles.toggleBtn, type === "income" && styles.toggleActiveIncome]}
            onPress={() => switchType("income")}
            testID="type-income"
          >
            <Text style={[styles.toggleText, type === "income" && styles.toggleTextActive]}>
              {t("add_income")}
            </Text>
          </Pressable>
        </View>

        {/* amount */}
        <View style={styles.amountBox}>
          <Text style={styles.rupee}>₹</Text>
          <TextInput
            style={styles.amountInput}
            value={amount}
            onChangeText={setAmount}
            placeholder="0"
            placeholderTextColor={colors.borderStrong}
            keyboardType="numeric"
            testID="add-tx-amount"
          />
        </View>

        {/* title */}
        <Text style={styles.label}>{t("title")}</Text>
        <TextInput
          style={styles.input}
          value={title}
          onChangeText={setTitle}
          placeholder={t("title_placeholder")}
          placeholderTextColor={colors.muted}
          testID="add-tx-title"
        />

        {/* category */}
        <Text style={styles.label}>{t("category")}</Text>
        <View style={styles.catGrid}>
          {cats.map((c) => {
            const active = category === c;
            const color = CATEGORY_COLORS[c] ?? "#737373";
            return (
              <Pressable
                key={c}
                style={[styles.catItem, active && { borderColor: color, backgroundColor: `${color}18` }]}
                onPress={() => setCategory(c)}
                testID={`cat-${c}`}
              >
                <CategoryIcon category={c} color={color} size={20} />
                <Text style={[styles.catLabel, active && { color: colors.onSurface }]} numberOfLines={1}>
                  {t(categoryLabelKey(c))}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* account */}
        <Text style={styles.label}>{t("account")}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.accRow}>
          {(accountsQ.data ?? []).map((a) => {
            const active = accountId === a.id;
            return (
              <Pressable
                key={a.id}
                style={[styles.accChip, active && styles.accChipActive]}
                onPress={() => setAccountId(a.id)}
                testID={`account-${a.id}`}
              >
                <Text style={[styles.accName, active && styles.accNameActive]}>{a.name}</Text>
                <Text style={[styles.accBal, active && styles.accNameActive]}>{formatCurrency(a.balance)}</Text>
              </Pressable>
            );
          })}
        </ScrollView>

        {/* note */}
        <Text style={styles.label}>{t("note")}</Text>
        <TextInput
          style={styles.input}
          value={note}
          onChangeText={setNote}
          placeholder={t("note_placeholder")}
          placeholderTextColor={colors.muted}
          testID="add-tx-note"
        />
      </KeyboardAwareScrollView>

      <KeyboardStickyView offset={{ closed: 0, opened: 0 }}>
        <View style={[styles.footer, { paddingBottom: insets.bottom + 12 }]}>
          <Pressable style={styles.cta} onPress={onSave} disabled={save.isPending} testID="add-tx-save">
            {save.isPending ? (
              <ActivityIndicator color={colors.onBrandPrimary} />
            ) : (
              <Text style={styles.ctaText}>{t("save")}</Text>
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
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    paddingBottom: 12,
  },
  title: { fontSize: 20, fontWeight: "800", color: colors.onSurface },
  closeBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surfaceSecondary,
    alignItems: "center",
    justifyContent: "center",
  },
  content: { paddingHorizontal: 20, paddingBottom: 24 },
  toggle: {
    flexDirection: "row",
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 12,
    padding: 4,
    marginBottom: 20,
  },
  toggleBtn: { flex: 1, paddingVertical: 12, borderRadius: 9, alignItems: "center" },
  toggleActive: { backgroundColor: colors.error },
  toggleActiveIncome: { backgroundColor: colors.success },
  toggleText: { fontSize: 14, fontWeight: "700", color: colors.muted },
  toggleTextActive: { color: "#FFFFFF" },
  amountBox: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 8,
    marginBottom: 12,
  },
  rupee: { fontSize: 36, fontWeight: "800", color: colors.onSurface, marginRight: 4 },
  amountInput: {
    fontSize: 44,
    fontWeight: "800",
    color: colors.onSurface,
    minWidth: 120,
    textAlign: "center",
    padding: 0,
  },
  label: { fontSize: 13, fontWeight: "700", color: colors.onSurfaceSecondary, marginTop: 16, marginBottom: 10 },
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
  catGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  catItem: {
    width: "23%",
    aspectRatio: 1,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingHorizontal: 4,
  },
  catLabel: { fontSize: 10, color: colors.muted, fontWeight: "600", textAlign: "center" },
  accRow: { gap: 10, paddingRight: 8 },
  accChip: {
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
    paddingHorizontal: 16,
    paddingVertical: 12,
    minWidth: 120,
    flexShrink: 0,
  },
  accChipActive: { borderColor: colors.brandPrimary, backgroundColor: colors.brandTertiary },
  accName: { fontSize: 14, fontWeight: "700", color: colors.onSurface },
  accNameActive: { color: colors.brand },
  accBal: { fontSize: 12, color: colors.muted, marginTop: 2 },
  footer: {
    paddingHorizontal: 20,
    paddingTop: 12,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
  },
  cta: { backgroundColor: colors.brandPrimary, paddingVertical: 16, borderRadius: 16, alignItems: "center" },
  ctaText: { color: colors.onBrandPrimary, fontSize: 16, fontWeight: "700" },
}));
