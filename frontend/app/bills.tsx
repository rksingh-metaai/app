import React, { useState } from "react";
import { View, Text, Pressable, ScrollView, TextInput, ActivityIndicator } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CaretLeft, Plus, PencilSimple, Trash, Receipt, CheckCircle, Clock } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";
import { formatCurrency } from "@/src/lib/format";
import { BottomSheet } from "@/src/components/BottomSheet";
import { useToast } from "@/src/components/Toast";

type Bill = {
  id: string;
  name: string;
  amount: number;
  category: string;
  due_day: number;
  account_id: string | null;
  next_due: string;
  days_until: number;
  paid_this_month: boolean;
};
type Account = { id: string; name: string; balance: number };

export default function Bills() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t } = useI18n();
  const toast = useToast();
  const qc = useQueryClient();

  const [sheetOpen, setSheetOpen] = useState(false);
  const [editing, setEditing] = useState<Bill | null>(null);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDay, setDueDay] = useState("");
  const [accountId, setAccountId] = useState<string | null>(null);

  const billsQ = useQuery<Bill[]>({ queryKey: ["bills"], queryFn: () => api.get("/bills") });
  const accountsQ = useQuery<Account[]>({ queryKey: ["accounts"], queryFn: () => api.get("/accounts") });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["bills"] });
    qc.invalidateQueries({ queryKey: ["summary"] });
    qc.invalidateQueries({ queryKey: ["accounts"] });
    qc.invalidateQueries({ queryKey: ["transactions"] });
  };

  const saveMut = useMutation({
    mutationFn: () => {
      const payload = {
        name: name.trim(),
        amount: parseFloat(amount),
        category: "bills",
        due_day: parseInt(dueDay, 10) || 1,
        account_id: accountId,
      };
      return editing ? api.put(`/bills/${editing.id}`, payload) : api.post("/bills", payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["bills"] });
      setSheetOpen(false);
      toast.show(t("save"), "success");
    },
    onError: () => toast.show(t("something_wrong"), "error"),
  });

  const payMut = useMutation({
    mutationFn: (id: string) => api.post(`/bills/${id}/pay`),
    onSuccess: () => {
      invalidate();
      toast.show(t("paid"), "success");
    },
  });
  const delMut = useMutation({
    mutationFn: (id: string) => api.del(`/bills/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bills"] }),
  });

  const openAdd = () => {
    setEditing(null);
    setName("");
    setAmount("");
    setDueDay("");
    setAccountId(accountsQ.data?.[0]?.id ?? null);
    setSheetOpen(true);
  };
  const openEdit = (b: Bill) => {
    setEditing(b);
    setName(b.name);
    setAmount(String(b.amount));
    setDueDay(String(b.due_day));
    setAccountId(b.account_id);
    setSheetOpen(true);
  };

  const onSave = () => {
    const amt = parseFloat(amount);
    const dd = parseInt(dueDay, 10);
    if (!name.trim()) return toast.show(t("fill_all_fields"), "error");
    if (!amt || amt <= 0) return toast.show(t("enter_valid_amount"), "error");
    if (!dd || dd < 1 || dd > 31) return toast.show(t("fill_all_fields"), "error");
    saveMut.mutate();
  };

  const dueBadge = (b: Bill) => {
    if (b.paid_this_month) return { text: t("paid"), color: colors.success, bg: colors.brandTertiary };
    if (b.days_until === 0) return { text: t("due_today"), color: colors.warning, bg: `${colors.warning}22` };
    if (b.days_until === 1) return { text: t("due_tomorrow"), color: colors.warning, bg: `${colors.warning}22` };
    return { text: `${t("due_in")} ${b.days_until} ${t("days")}`, color: colors.info, bg: colors.surfaceTertiary };
  };

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.backBtn} testID="bills-back">
          <CaretLeft size={22} color={colors.onSurface} weight="bold" />
        </Pressable>
        <Text style={styles.title}>{t("bill_reminders")}</Text>
        <View style={{ width: 40 }} />
      </View>

      {billsQ.isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.brandPrimary} />
        </View>
      ) : (billsQ.data ?? []).length === 0 ? (
        <View style={styles.center}>
          <View style={styles.emptyIcon}>
            <Receipt size={36} color={colors.brand} weight="fill" />
          </View>
          <Text style={styles.emptyTitle}>{t("no_bills")}</Text>
          <Text style={styles.emptySub}>{t("no_bills_sub")}</Text>
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 100 }} showsVerticalScrollIndicator={false}>
          <Text style={styles.sectionTitle}>{t("upcoming_bills")}</Text>
          {(billsQ.data ?? []).map((b) => {
            const badge = dueBadge(b);
            return (
              <View key={b.id} style={styles.card} testID={`bill-${b.id}`}>
                <View style={styles.cardTop}>
                  <View style={[styles.iconWrap, { backgroundColor: colors.brandTertiary }]}>
                    <Receipt size={20} color={colors.brand} weight="fill" />
                  </View>
                  <View style={styles.mid}>
                    <Text style={styles.billName}>{b.name}</Text>
                    <View style={[styles.badge, { backgroundColor: badge.bg }]}>
                      {b.paid_this_month ? (
                        <CheckCircle size={12} color={badge.color} weight="fill" />
                      ) : (
                        <Clock size={12} color={badge.color} weight="fill" />
                      )}
                      <Text style={[styles.badgeText, { color: badge.color }]}>{badge.text}</Text>
                    </View>
                  </View>
                  <View style={styles.right}>
                    <Text style={styles.amount}>{formatCurrency(b.amount)}</Text>
                    <View style={styles.actions}>
                      <Pressable onPress={() => openEdit(b)} hitSlop={8} testID={`bill-edit-${b.id}`}>
                        <PencilSimple size={17} color={colors.muted} />
                      </Pressable>
                      <Pressable onPress={() => delMut.mutate(b.id)} hitSlop={8} testID={`bill-delete-${b.id}`}>
                        <Trash size={17} color={colors.muted} />
                      </Pressable>
                    </View>
                  </View>
                </View>
                {!b.paid_this_month ? (
                  <Pressable style={styles.payBtn} onPress={() => payMut.mutate(b.id)} testID={`bill-pay-${b.id}`}>
                    <CheckCircle size={16} color={colors.onBrandPrimary} weight="fill" />
                    <Text style={styles.payText}>{t("mark_paid")}</Text>
                  </Pressable>
                ) : null}
              </View>
            );
          })}
        </ScrollView>
      )}

      <Pressable style={[styles.fab, { bottom: insets.bottom + 16 }]} onPress={openAdd} testID="bills-add-fab">
        <Plus size={22} color={colors.onBrandPrimary} weight="bold" />
        <Text style={styles.fabText}>{t("add_bill")}</Text>
      </Pressable>

      <BottomSheet
        visible={sheetOpen}
        onClose={() => setSheetOpen(false)}
        title={editing ? t("edit_bill") : t("add_bill")}
        testID="bill-sheet"
      >
        <Text style={styles.label}>{t("bill_name")}</Text>
        <TextInput
          style={styles.input}
          value={name}
          onChangeText={setName}
          placeholder={t("bill_name")}
          placeholderTextColor={colors.muted}
          testID="bill-name-input"
        />

        <Text style={styles.label}>{t("amount")}</Text>
        <View style={styles.amountBox}>
          <Text style={styles.rupee}>₹</Text>
          <TextInput
            style={styles.amountInput}
            value={amount}
            onChangeText={setAmount}
            placeholder="0"
            placeholderTextColor={colors.muted}
            keyboardType="numeric"
            testID="bill-amount-input"
          />
        </View>

        <Text style={styles.label}>{t("due_day")}</Text>
        <TextInput
          style={styles.input}
          value={dueDay}
          onChangeText={setDueDay}
          placeholder="1-31"
          placeholderTextColor={colors.muted}
          keyboardType="numeric"
          maxLength={2}
          testID="bill-dueday-input"
        />

        <Text style={styles.label}>{t("account")}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.accRow}>
          {(accountsQ.data ?? []).map((a) => {
            const active = accountId === a.id;
            return (
              <Pressable
                key={a.id}
                style={[styles.accChip, active && styles.accChipActive]}
                onPress={() => setAccountId(a.id)}
                testID={`bill-account-${a.id}`}
              >
                <Text style={[styles.accName, active && { color: colors.brand }]}>{a.name}</Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <Pressable style={styles.sheetCta} onPress={onSave} disabled={saveMut.isPending} testID="bill-save">
          {saveMut.isPending ? (
            <ActivityIndicator color={colors.onBrandPrimary} />
          ) : (
            <Text style={styles.sheetCtaText}>{t("save")}</Text>
          )}
        </Pressable>
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
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 8 },
  emptyIcon: {
    width: 80,
    height: 80,
    borderRadius: 28,
    backgroundColor: colors.brandTertiary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },
  emptyTitle: { fontSize: 17, fontWeight: "700", color: colors.onSurface },
  emptySub: { fontSize: 14, color: colors.muted, textAlign: "center" },
  sectionTitle: { fontSize: 14, fontWeight: "700", color: colors.muted, marginBottom: 12, textTransform: "uppercase" },
  card: { backgroundColor: colors.surfaceSecondary, borderRadius: 16, padding: 14, marginBottom: 12 },
  cardTop: { flexDirection: "row", alignItems: "center", gap: 12 },
  iconWrap: { width: 44, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  mid: { flex: 1, gap: 6 },
  billName: { fontSize: 15, fontWeight: "700", color: colors.onSurface },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  badgeText: { fontSize: 11, fontWeight: "700" },
  right: { alignItems: "flex-end", gap: 8 },
  amount: { fontSize: 15, fontWeight: "800", color: colors.onSurface },
  actions: { flexDirection: "row", gap: 12 },
  payBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: colors.brandPrimary,
    paddingVertical: 10,
    borderRadius: 10,
    marginTop: 12,
  },
  payText: { color: colors.onBrandPrimary, fontSize: 13, fontWeight: "700" },
  fab: {
    position: "absolute",
    left: 16,
    right: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: colors.brandPrimary,
    paddingVertical: 16,
    borderRadius: 16,
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  fabText: { color: colors.onBrandPrimary, fontSize: 15, fontWeight: "700" },
  label: { fontSize: 13, fontWeight: "700", color: colors.onSurfaceSecondary, marginTop: 8, marginBottom: 10 },
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
  rupee: { fontSize: 22, fontWeight: "800", color: colors.onSurface, marginRight: 6 },
  amountInput: { flex: 1, paddingVertical: 16, fontSize: 22, fontWeight: "800", color: colors.onSurface },
  accRow: { gap: 8, paddingRight: 8 },
  accChip: {
    height: 40,
    justifyContent: "center",
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
    flexShrink: 0,
  },
  accChipActive: { borderColor: colors.brandPrimary, backgroundColor: colors.brandTertiary },
  accName: { fontSize: 13, fontWeight: "600", color: colors.onSurfaceSecondary },
  sheetCta: { backgroundColor: colors.brandPrimary, paddingVertical: 16, borderRadius: 14, alignItems: "center", marginTop: 20 },
  sheetCtaText: { color: colors.onBrandPrimary, fontSize: 16, fontWeight: "700" },
}));
