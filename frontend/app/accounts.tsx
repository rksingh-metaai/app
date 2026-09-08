import React, { useState } from "react";
import { View, Text, Pressable, ScrollView, TextInput, ActivityIndicator } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CaretLeft, Plus, PencilSimple, Trash, Bank, Money, CreditCard, Wallet, TrendUp } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";
import { formatCurrency, accountLabelKey } from "@/src/lib/format";
import { BottomSheet } from "@/src/components/BottomSheet";
import { useToast } from "@/src/components/Toast";

type Account = { id: string; name: string; type: string; balance: number; color?: string };

const TYPES = ["bank", "cash", "card", "wallet", "investment"];
const TYPE_ICON: Record<string, React.ComponentType<any>> = {
  bank: Bank,
  cash: Money,
  card: CreditCard,
  wallet: Wallet,
  investment: TrendUp,
};

export default function Accounts() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t } = useI18n();
  const toast = useToast();
  const qc = useQueryClient();

  const [sheetOpen, setSheetOpen] = useState(false);
  const [editing, setEditing] = useState<Account | null>(null);
  const [name, setName] = useState("");
  const [atype, setAtype] = useState("bank");
  const [balance, setBalance] = useState("");

  const { data, isLoading } = useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: () => api.get("/accounts"),
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["accounts"] });
    qc.invalidateQueries({ queryKey: ["summary"] });
  };

  const saveMut = useMutation({
    mutationFn: () => {
      const payload = { name: name.trim(), type: atype, balance: parseFloat(balance) || 0 };
      return editing ? api.put(`/accounts/${editing.id}`, payload) : api.post("/accounts", payload);
    },
    onSuccess: () => {
      invalidate();
      setSheetOpen(false);
      toast.show(t("save"), "success");
    },
    onError: () => toast.show(t("something_wrong"), "error"),
  });

  const delMut = useMutation({
    mutationFn: (id: string) => api.del(`/accounts/${id}`),
    onSuccess: invalidate,
  });

  const openAdd = () => {
    setEditing(null);
    setName("");
    setAtype("bank");
    setBalance("");
    setSheetOpen(true);
  };
  const openEdit = (a: Account) => {
    setEditing(a);
    setName(a.name);
    setAtype(a.type);
    setBalance(String(a.balance));
    setSheetOpen(true);
  };

  const onSave = () => {
    if (!name.trim()) {
      toast.show(t("fill_all_fields"), "error");
      return;
    }
    saveMut.mutate();
  };

  return (
    <View style={styles.root}>
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={styles.backBtn} testID="accounts-back">
          <CaretLeft size={22} color={colors.onSurface} weight="bold" />
        </Pressable>
        <Text style={styles.title}>{t("accounts")}</Text>
        <View style={{ width: 40 }} />
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.brandPrimary} />
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 100 }} showsVerticalScrollIndicator={false}>
          {(data ?? []).length === 0 ? (
            <Text style={styles.emptyMuted}>{t("no_accounts")}</Text>
          ) : (
            (data ?? []).map((a) => {
              const Icon = TYPE_ICON[a.type] ?? Bank;
              return (
                <View key={a.id} style={styles.card} testID={`account-card-${a.id}`}>
                  <View style={[styles.iconWrap, { backgroundColor: colors.brandTertiary }]}>
                    <Icon size={22} color={colors.brand} weight="fill" />
                  </View>
                  <View style={styles.mid}>
                    <Text style={styles.accName}>{a.name}</Text>
                    <Text style={styles.accType}>{t(accountLabelKey(a.type))}</Text>
                  </View>
                  <View style={styles.right}>
                    <Text style={[styles.bal, { color: a.balance < 0 ? colors.error : colors.onSurface }]}>
                      {formatCurrency(a.balance)}
                    </Text>
                    <View style={styles.actions}>
                      <Pressable onPress={() => openEdit(a)} hitSlop={8} testID={`account-edit-${a.id}`}>
                        <PencilSimple size={18} color={colors.muted} />
                      </Pressable>
                      <Pressable onPress={() => delMut.mutate(a.id)} hitSlop={8} testID={`account-delete-${a.id}`}>
                        <Trash size={18} color={colors.muted} />
                      </Pressable>
                    </View>
                  </View>
                </View>
              );
            })
          )}
        </ScrollView>
      )}

      <Pressable style={[styles.fab, { bottom: insets.bottom + 16 }]} onPress={openAdd} testID="accounts-add-fab">
        <Plus size={22} color={colors.onBrandPrimary} weight="bold" />
        <Text style={styles.fabText}>{t("add_account")}</Text>
      </Pressable>

      <BottomSheet
        visible={sheetOpen}
        onClose={() => setSheetOpen(false)}
        title={editing ? t("edit_account") : t("add_account")}
        testID="account-sheet"
      >
        <Text style={styles.label}>{t("account_name")}</Text>
        <TextInput
          style={styles.input}
          value={name}
          onChangeText={setName}
          placeholder={t("account_name")}
          placeholderTextColor={colors.muted}
          testID="account-name-input"
        />

        <Text style={styles.label}>{t("account_type")}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.typeRow}>
          {TYPES.map((tp) => {
            const active = atype === tp;
            const Icon = TYPE_ICON[tp];
            return (
              <Pressable
                key={tp}
                style={[styles.typeChip, active && styles.typeChipActive]}
                onPress={() => setAtype(tp)}
                testID={`account-type-${tp}`}
              >
                <Icon size={16} color={active ? colors.brand : colors.muted} weight="fill" />
                <Text style={[styles.typeText, active && styles.typeTextActive]}>{t(accountLabelKey(tp))}</Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <Text style={styles.label}>{t("balance")}</Text>
        <View style={styles.amountBox}>
          <Text style={styles.rupee}>₹</Text>
          <TextInput
            style={styles.amountInput}
            value={balance}
            onChangeText={setBalance}
            placeholder="0"
            placeholderTextColor={colors.muted}
            keyboardType="numeric"
            testID="account-balance-input"
          />
        </View>

        <Pressable style={styles.sheetCta} onPress={onSave} disabled={saveMut.isPending} testID="account-save">
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
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  emptyMuted: { color: colors.muted, fontSize: 14, textAlign: "center", paddingVertical: 40 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 16,
    padding: 14,
    marginBottom: 12,
  },
  iconWrap: { width: 46, height: 46, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  mid: { flex: 1 },
  accName: { fontSize: 15, fontWeight: "700", color: colors.onSurface },
  accType: { fontSize: 12, color: colors.muted, marginTop: 2 },
  right: { alignItems: "flex-end", gap: 8 },
  bal: { fontSize: 15, fontWeight: "800" },
  actions: { flexDirection: "row", gap: 14 },
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
  typeRow: { gap: 8, paddingRight: 8 },
  typeChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    height: 40,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
    flexShrink: 0,
  },
  typeChipActive: { borderColor: colors.brandPrimary, backgroundColor: colors.brandTertiary },
  typeText: { fontSize: 13, fontWeight: "600", color: colors.muted },
  typeTextActive: { color: colors.brand },
  amountBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  rupee: { fontSize: 22, fontWeight: "800", color: colors.onSurface, marginRight: 6 },
  amountInput: { flex: 1, paddingVertical: 16, fontSize: 22, fontWeight: "800", color: colors.onSurface },
  sheetCta: { backgroundColor: colors.brandPrimary, paddingVertical: 16, borderRadius: 14, alignItems: "center" },
  sheetCtaText: { color: colors.onBrandPrimary, fontSize: 16, fontWeight: "700" },
}));
