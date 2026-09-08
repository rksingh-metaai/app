import React, { useMemo, useState } from "react";
import { View, Text, Pressable, ScrollView, TextInput, ActivityIndicator } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CaretLeft, Plus, PencilSimple, Trash, Receipt, CheckCircle, Clock } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { LangCode } from "@/src/i18n/translations";
import { api } from "@/src/api/client";
import { formatCurrency, formatDate } from "@/src/lib/format";
import { BottomSheet } from "@/src/components/BottomSheet";
import { useToast } from "@/src/components/Toast";

type Bill = {
  id: string;
  name: string;
  amount: number;
  category: string;
  frequency: string;
  due_day: number;
  due_weekday: number;
  due_month: number;
  account_id: string | null;
  next_due: string;
  days_until: number;
  paid_this_month: boolean;
};
type Account = { id: string; name: string; balance: number };
type Payment = { id: string; name: string; amount: number; account_name: string | null; paid_at: string };

const LOCALE: Record<LangCode, string> = {
  en: "en-IN", hi: "hi-IN", ta: "ta-IN", te: "te-IN", bn: "bn-IN", mr: "mr-IN",
};
const FREQS = ["monthly", "weekly", "yearly"] as const;

export default function Bills() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t, lang } = useI18n();
  const toast = useToast();
  const qc = useQueryClient();

  const [tab, setTab] = useState<"upcoming" | "history">("upcoming");
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editing, setEditing] = useState<Bill | null>(null);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [frequency, setFrequency] = useState<(typeof FREQS)[number]>("monthly");
  const [dueDay, setDueDay] = useState("");
  const [dueWeekday, setDueWeekday] = useState(0);
  const [dueMonth, setDueMonth] = useState(1);
  const [accountId, setAccountId] = useState<string | null>(null);

  const billsQ = useQuery<Bill[]>({ queryKey: ["bills"], queryFn: () => api.get("/bills") });
  const accountsQ = useQuery<Account[]>({ queryKey: ["accounts"], queryFn: () => api.get("/accounts") });
  const historyQ = useQuery<Payment[]>({ queryKey: ["bills-history"], queryFn: () => api.get("/bills/history") });

  const weekdayNames = useMemo(() => {
    const fmt = new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { weekday: "short" });
    // 2024-01-01 is a Monday
    return Array.from({ length: 7 }, (_, i) => fmt.format(new Date(2024, 0, 1 + i)));
  }, [lang]);

  const monthNames = useMemo(() => {
    const fmt = new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { month: "short" });
    return Array.from({ length: 12 }, (_, i) => fmt.format(new Date(2024, i, 1)));
  }, [lang]);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["bills"] });
    qc.invalidateQueries({ queryKey: ["bills-history"] });
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
        frequency,
        due_day: frequency === "weekly" ? 1 : parseInt(dueDay, 10) || 1,
        due_weekday: dueWeekday,
        due_month: dueMonth,
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
    setFrequency("monthly");
    setDueDay("");
    setDueWeekday(0);
    setDueMonth(1);
    setAccountId(accountsQ.data?.[0]?.id ?? null);
    setSheetOpen(true);
  };
  const openEdit = (b: Bill) => {
    setEditing(b);
    setName(b.name);
    setAmount(String(b.amount));
    setFrequency((b.frequency as any) ?? "monthly");
    setDueDay(String(b.due_day ?? 1));
    setDueWeekday(b.due_weekday ?? 0);
    setDueMonth(b.due_month ?? 1);
    setAccountId(b.account_id);
    setSheetOpen(true);
  };

  const onSave = () => {
    const amt = parseFloat(amount);
    if (!name.trim()) return toast.show(t("fill_all_fields"), "error");
    if (!amt || amt <= 0) return toast.show(t("enter_valid_amount"), "error");
    if (frequency !== "weekly") {
      const dd = parseInt(dueDay, 10);
      if (!dd || dd < 1 || dd > 31) return toast.show(t("fill_all_fields"), "error");
    }
    saveMut.mutate();
  };

  const dueBadge = (b: Bill) => {
    if (b.paid_this_month) return { text: t("paid"), color: colors.success, bg: colors.brandTertiary };
    if (b.days_until < 0) return { text: t("overdue"), color: colors.error, bg: `${colors.error}22` };
    if (b.days_until === 0) return { text: t("due_today"), color: colors.warning, bg: `${colors.warning}22` };
    if (b.days_until === 1) return { text: t("due_tomorrow"), color: colors.warning, bg: `${colors.warning}22` };
    return { text: `${t("due_in")} ${b.days_until} ${t("days")}`, color: colors.info, bg: colors.surfaceTertiary };
  };

  const freqLabel = (f: string) => t((["monthly", "weekly", "yearly"].includes(f) ? f : "monthly") as any);

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.backBtn} testID="bills-back">
          <CaretLeft size={22} color={colors.onSurface} weight="bold" />
        </Pressable>
        <Text style={styles.title}>{t("bill_reminders")}</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* segmented control */}
      <View style={styles.segmentWrap}>
        <View style={styles.segment}>
          <Pressable
            style={[styles.segBtn, tab === "upcoming" && styles.segActive]}
            onPress={() => setTab("upcoming")}
            testID="bills-tab-upcoming"
          >
            <Text style={[styles.segText, tab === "upcoming" && styles.segTextActive]}>{t("upcoming")}</Text>
          </Pressable>
          <Pressable
            style={[styles.segBtn, tab === "history" && styles.segActive]}
            onPress={() => setTab("history")}
            testID="bills-tab-history"
          >
            <Text style={[styles.segText, tab === "history" && styles.segTextActive]}>{t("history")}</Text>
          </Pressable>
        </View>
      </View>

      {tab === "upcoming" ? (
        billsQ.isLoading ? (
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
                      <View style={styles.metaRow}>
                        <View style={[styles.badge, { backgroundColor: badge.bg }]}>
                          {b.paid_this_month ? (
                            <CheckCircle size={12} color={badge.color} weight="fill" />
                          ) : (
                            <Clock size={12} color={badge.color} weight="fill" />
                          )}
                          <Text style={[styles.badgeText, { color: badge.color }]}>{badge.text}</Text>
                        </View>
                        <Text style={styles.freqTag}>{freqLabel(b.frequency)}</Text>
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
        )
      ) : historyQ.isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.brandPrimary} />
        </View>
      ) : (historyQ.data ?? []).length === 0 ? (
        <View style={styles.center}>
          <View style={styles.emptyIcon}>
            <CheckCircle size={36} color={colors.brand} weight="fill" />
          </View>
          <Text style={styles.emptyTitle}>{t("no_history")}</Text>
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 24 }} showsVerticalScrollIndicator={false}>
          {(historyQ.data ?? []).map((p) => (
            <View key={p.id} style={styles.histRow} testID={`payment-${p.id}`}>
              <View style={[styles.iconWrap, { backgroundColor: colors.brandTertiary }]}>
                <CheckCircle size={20} color={colors.success} weight="fill" />
              </View>
              <View style={styles.mid}>
                <Text style={styles.billName}>{p.name}</Text>
                <Text style={styles.histSub}>
                  {t("paid_on")} {formatDate(p.paid_at, lang)}
                  {p.account_name ? ` · ${p.account_name}` : ""}
                </Text>
              </View>
              <Text style={styles.amount}>-{formatCurrency(p.amount)}</Text>
            </View>
          ))}
        </ScrollView>
      )}

      {tab === "upcoming" ? (
        <Pressable style={[styles.fab, { bottom: insets.bottom + 16 }]} onPress={openAdd} testID="bills-add-fab">
          <Plus size={22} color={colors.onBrandPrimary} weight="bold" />
          <Text style={styles.fabText}>{t("add_bill")}</Text>
        </Pressable>
      ) : null}

      <BottomSheet
        visible={sheetOpen}
        onClose={() => setSheetOpen(false)}
        title={editing ? t("edit_bill") : t("add_bill")}
        testID="bill-sheet"
      >
        <ScrollView showsVerticalScrollIndicator={false}>
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

          <Text style={styles.label}>{t("frequency")}</Text>
          <View style={styles.freqRow}>
            {FREQS.map((f) => {
              const active = frequency === f;
              return (
                <Pressable
                  key={f}
                  style={[styles.freqChip, active && styles.freqChipActive]}
                  onPress={() => setFrequency(f)}
                  testID={`bill-freq-${f}`}
                >
                  <Text style={[styles.freqText, active && styles.freqTextActive]}>{t(f)}</Text>
                </Pressable>
              );
            })}
          </View>

          {frequency === "weekly" ? (
            <>
              <Text style={styles.label}>{t("weekday")}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pickRow}>
                {weekdayNames.map((w, i) => {
                  const active = dueWeekday === i;
                  return (
                    <Pressable
                      key={i}
                      style={[styles.pickChip, active && styles.pickChipActive]}
                      onPress={() => setDueWeekday(i)}
                      testID={`bill-weekday-${i}`}
                    >
                      <Text style={[styles.pickText, active && styles.pickTextActive]}>{w}</Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </>
          ) : (
            <>
              {frequency === "yearly" ? (
                <>
                  <Text style={styles.label}>{t("month")}</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pickRow}>
                    {monthNames.map((mn, i) => {
                      const active = dueMonth === i + 1;
                      return (
                        <Pressable
                          key={i}
                          style={[styles.pickChip, active && styles.pickChipActive]}
                          onPress={() => setDueMonth(i + 1)}
                          testID={`bill-month-${i + 1}`}
                        >
                          <Text style={[styles.pickText, active && styles.pickTextActive]}>{mn}</Text>
                        </Pressable>
                      );
                    })}
                  </ScrollView>
                </>
              ) : null}
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
            </>
          )}

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
        </ScrollView>
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
  segmentWrap: { paddingHorizontal: 16, paddingTop: 12 },
  segment: { flexDirection: "row", backgroundColor: colors.surfaceSecondary, borderRadius: 12, padding: 4 },
  segBtn: { flex: 1, paddingVertical: 10, borderRadius: 9, alignItems: "center" },
  segActive: { backgroundColor: colors.surface, shadowColor: "#000", shadowOpacity: 0.06, shadowRadius: 4, elevation: 1 },
  segText: { fontSize: 14, fontWeight: "700", color: colors.muted },
  segTextActive: { color: colors.onSurface },
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
  card: { backgroundColor: colors.surfaceSecondary, borderRadius: 16, padding: 14, marginBottom: 12 },
  cardTop: { flexDirection: "row", alignItems: "center", gap: 12 },
  iconWrap: { width: 44, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  mid: { flex: 1, gap: 6 },
  billName: { fontSize: 15, fontWeight: "700", color: colors.onSurface },
  metaRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
  },
  badgeText: { fontSize: 11, fontWeight: "700" },
  freqTag: { fontSize: 11, color: colors.muted, fontWeight: "600" },
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
  histRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 14,
    padding: 12,
    marginBottom: 10,
  },
  histSub: { fontSize: 12, color: colors.muted, marginTop: 2 },
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
  label: { fontSize: 13, fontWeight: "700", color: colors.onSurfaceSecondary, marginTop: 12, marginBottom: 10 },
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
  freqRow: { flexDirection: "row", gap: 8 },
  freqChip: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
    alignItems: "center",
  },
  freqChipActive: { borderColor: colors.brandPrimary, backgroundColor: colors.brandTertiary },
  freqText: { fontSize: 13, fontWeight: "700", color: colors.muted },
  freqTextActive: { color: colors.brand },
  pickRow: { gap: 8, paddingRight: 8 },
  pickChip: {
    height: 40,
    minWidth: 48,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 12,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
    flexShrink: 0,
  },
  pickChipActive: { borderColor: colors.brandPrimary, backgroundColor: colors.brandTertiary },
  pickText: { fontSize: 13, fontWeight: "600", color: colors.muted },
  pickTextActive: { color: colors.brand },
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
