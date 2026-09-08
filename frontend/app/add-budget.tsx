import React, { useState } from "react";
import { View, Text, Pressable, TextInput, ActivityIndicator } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";
import { CATEGORY_COLORS, categoryLabelKey } from "@/src/lib/format";
import { CategoryIcon } from "@/src/components/CategoryIcon";
import { useToast } from "@/src/components/Toast";

const CATS = ["food", "groceries", "shopping", "transport", "bills", "entertainment", "health", "other"];

export default function AddBudget() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t } = useI18n();
  const toast = useToast();
  const qc = useQueryClient();

  const [name, setName] = useState("");
  const [category, setCategory] = useState("food");
  const [limit, setLimit] = useState("");

  const save = useMutation({
    mutationFn: () =>
      api.post("/budgets", { name: name.trim(), category, limit: parseFloat(limit), period: "monthly" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["budgets"] });
      toast.show(t("save"), "success");
      router.back();
    },
    onError: () => toast.show(t("something_wrong"), "error"),
  });

  const onSave = () => {
    const lim = parseFloat(limit);
    if (!name.trim()) {
      toast.show(t("fill_all_fields"), "error");
      return;
    }
    if (!lim || lim <= 0) {
      toast.show(t("enter_valid_amount"), "error");
      return;
    }
    save.mutate();
  };

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Text style={styles.title}>{t("new_budget")}</Text>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.closeBtn} testID="add-budget-close">
          <X size={22} color={colors.onSurface} weight="bold" />
        </Pressable>
      </View>

      <KeyboardAwareScrollView
        style={styles.flex}
        contentContainerStyle={styles.content}
        bottomOffset={90}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.label}>{t("budget_name")}</Text>
        <TextInput
          style={styles.input}
          value={name}
          onChangeText={setName}
          placeholder={t("budget_name")}
          placeholderTextColor={colors.muted}
          testID="budget-name-input"
        />

        <Text style={styles.label}>{t("category")}</Text>
        <View style={styles.catGrid}>
          {CATS.map((c) => {
            const active = category === c;
            const color = CATEGORY_COLORS[c] ?? "#737373";
            return (
              <Pressable
                key={c}
                style={[styles.catItem, active && { borderColor: color, backgroundColor: `${color}18` }]}
                onPress={() => setCategory(c)}
                testID={`budget-cat-${c}`}
              >
                <CategoryIcon category={c} color={color} size={20} />
                <Text style={styles.catLabel} numberOfLines={1}>
                  {t(categoryLabelKey(c))}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={styles.label}>{t("budget_limit")}</Text>
        <View style={styles.amountBox}>
          <Text style={styles.rupee}>₹</Text>
          <TextInput
            style={styles.amountInput}
            value={limit}
            onChangeText={setLimit}
            placeholder="0"
            placeholderTextColor={colors.muted}
            keyboardType="numeric"
            testID="budget-limit-input"
          />
        </View>
      </KeyboardAwareScrollView>

      <KeyboardStickyView offset={{ closed: 0, opened: 0 }}>
        <View style={[styles.footer, { paddingBottom: insets.bottom + 12 }]}>
          <Pressable style={styles.cta} onPress={onSave} disabled={save.isPending} testID="budget-save">
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
  amountBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 12,
    paddingHorizontal: 16,
  },
  rupee: { fontSize: 24, fontWeight: "800", color: colors.onSurface, marginRight: 6 },
  amountInput: { flex: 1, paddingVertical: 16, fontSize: 24, fontWeight: "800", color: colors.onSurface },
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
