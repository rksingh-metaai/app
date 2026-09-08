import React, { useState } from "react";
import { View, Text, Pressable, TextInput, ActivityIndicator } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { X, Target } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";
import { useToast } from "@/src/components/Toast";

export default function AddGoal() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t } = useI18n();
  const toast = useToast();
  const qc = useQueryClient();

  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [saved, setSaved] = useState("");

  const save = useMutation({
    mutationFn: () =>
      api.post("/goals", {
        name: name.trim(),
        target: parseFloat(target),
        saved: saved ? parseFloat(saved) : 0,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals"] });
      toast.show(t("save"), "success");
      router.back();
    },
    onError: () => toast.show(t("something_wrong"), "error"),
  });

  const onSave = () => {
    const tgt = parseFloat(target);
    if (!name.trim()) {
      toast.show(t("fill_all_fields"), "error");
      return;
    }
    if (!tgt || tgt <= 0) {
      toast.show(t("enter_valid_amount"), "error");
      return;
    }
    save.mutate();
  };

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Text style={styles.title}>{t("new_goal")}</Text>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.closeBtn} testID="add-goal-close">
          <X size={22} color={colors.onSurface} weight="bold" />
        </Pressable>
      </View>

      <KeyboardAwareScrollView
        style={styles.flex}
        contentContainerStyle={styles.content}
        bottomOffset={90}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.iconWrap}>
          <Target size={32} color={colors.brand} weight="fill" />
        </View>

        <Text style={styles.label}>{t("goal_name")}</Text>
        <TextInput
          style={styles.input}
          value={name}
          onChangeText={setName}
          placeholder={t("goal_name")}
          placeholderTextColor={colors.muted}
          testID="goal-name-input"
        />

        <Text style={styles.label}>{t("target_amount")}</Text>
        <View style={styles.amountBox}>
          <Text style={styles.rupee}>₹</Text>
          <TextInput
            style={styles.amountInput}
            value={target}
            onChangeText={setTarget}
            placeholder="0"
            placeholderTextColor={colors.muted}
            keyboardType="numeric"
            testID="goal-target-input"
          />
        </View>

        <Text style={styles.label}>{t("saved")}</Text>
        <View style={styles.amountBox}>
          <Text style={styles.rupee}>₹</Text>
          <TextInput
            style={styles.amountInput}
            value={saved}
            onChangeText={setSaved}
            placeholder="0"
            placeholderTextColor={colors.muted}
            keyboardType="numeric"
            testID="goal-saved-input"
          />
        </View>
      </KeyboardAwareScrollView>

      <KeyboardStickyView offset={{ closed: 0, opened: 0 }}>
        <View style={[styles.footer, { paddingBottom: insets.bottom + 12 }]}>
          <Pressable style={styles.cta} onPress={onSave} disabled={save.isPending} testID="goal-save">
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
  iconWrap: {
    alignSelf: "center",
    width: 72,
    height: 72,
    borderRadius: 24,
    backgroundColor: colors.brandTertiary,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
    marginBottom: 8,
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
