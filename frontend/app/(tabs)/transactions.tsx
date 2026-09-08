import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  FlatList,
  Pressable,
  TextInput,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import { Image } from "expo-image";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { MagnifyingGlass, Plus, Trash } from "phosphor-react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { api } from "@/src/api/client";
import { formatCurrency, formatDate, categoryLabelKey } from "@/src/lib/format";
import { CategoryIcon } from "@/src/components/CategoryIcon";
import { useToast } from "@/src/components/Toast";

type Txn = {
  id: string;
  title: string;
  amount: number;
  type: string;
  category: string;
  date: string;
};

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

const EMPTY_IMG =
  "https://images.unsplash.com/photo-1614260938313-a7fc1a7ad0d2?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzOTB8MHwxfHNlYXJjaHwxfHxlbXB0eSUyMHdhbGxldCUyMGVtcHR5JTIwc3RhdGUlMjBpbGx1c3RyYXRpb258ZW58MHx8fHwxNzg4ODU3NjMwfDA&ixlib=rb-4.1.0&q=85";

export default function Transactions() {
  const styles = useStyles();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { t, lang } = useI18n();
  const toast = useToast();
  const qc = useQueryClient();

  const [filter, setFilter] = useState<"all" | "income" | "expense">("all");
  const [search, setSearch] = useState("");

  const { data, isLoading, isError, refetch } = useQuery<Txn[]>({
    queryKey: ["transactions"],
    queryFn: () => api.get("/transactions"),
  });

  const del = useMutation({
    mutationFn: (id: string) => api.del(`/transactions/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["transactions"] });
      qc.invalidateQueries({ queryKey: ["summary"] });
      qc.invalidateQueries({ queryKey: ["accounts"] });
      qc.invalidateQueries({ queryKey: ["budgets"] });
      toast.show(t("save"), "success");
    },
  });

  const filtered = useMemo(() => {
    let list = data ?? [];
    if (filter !== "all") list = list.filter((x) => x.type === filter);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter((x) => x.title.toLowerCase().includes(q));
    }
    return list;
  }, [data, filter, search]);

  const chips: { key: "all" | "income" | "expense"; label: string }[] = [
    { key: "all", label: t("all") },
    { key: "income", label: t("income") },
    { key: "expense", label: t("expense") },
  ];

  return (
    <View style={styles.root}>
      {/* Sticky header */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Text style={styles.title}>{t("transactions")}</Text>
        <View style={styles.searchBox}>
          <MagnifyingGlass size={18} color={colors.muted} />
          <TextInput
            style={styles.searchInput}
            value={search}
            onChangeText={setSearch}
            placeholder={t("search_transactions")}
            placeholderTextColor={colors.muted}
            testID="tx-search"
          />
        </View>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.chipRow}
        >
          {chips.map((c) => {
            const active = filter === c.key;
            return (
              <Pressable
                key={c.key}
                onPress={() => setFilter(c.key)}
                style={[styles.chip, active && styles.chipActive]}
                testID={`filter-${c.key}`}
              >
                <Text style={[styles.chipText, active && styles.chipTextActive]}>{c.label}</Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.brandPrimary} />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <Text style={styles.muted}>{t("something_wrong")}</Text>
          <Pressable style={styles.retryBtn} onPress={() => refetch()}>
            <Text style={styles.retryText}>{t("retry")}</Text>
          </Pressable>
        </View>
      ) : filtered.length === 0 ? (
        <View style={styles.center}>
          <Image source={{ uri: EMPTY_IMG }} style={styles.emptyImg} contentFit="cover" />
          <Text style={styles.emptyTitle}>{t("no_transactions")}</Text>
          <Text style={styles.muted}>{t("no_transactions_sub")}</Text>
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(x) => x.id}
          contentContainerStyle={{ padding: 16, paddingBottom: 100 }}
          showsVerticalScrollIndicator={false}
          renderItem={({ item }) => {
            const color = CAT_COLORS[item.category] ?? "#737373";
            return (
              <View style={styles.row} testID={`tx-row-${item.id}`}>
                <View style={[styles.icon, { backgroundColor: `${color}22` }]}>
                  <CategoryIcon category={item.category} color={color} size={20} />
                </View>
                <View style={styles.mid}>
                  <Text style={styles.rowTitle} numberOfLines={1}>
                    {item.title}
                  </Text>
                  <Text style={styles.rowSub}>
                    {t(categoryLabelKey(item.category))} · {formatDate(item.date, lang)}
                  </Text>
                </View>
                <Text
                  style={[
                    styles.amount,
                    { color: item.type === "income" ? colors.success : colors.onSurface },
                  ]}
                >
                  {item.type === "income" ? "+" : "-"}
                  {formatCurrency(item.amount)}
                </Text>
                <Pressable
                  onPress={() => del.mutate(item.id)}
                  hitSlop={8}
                  style={styles.delBtn}
                  testID={`tx-delete-${item.id}`}
                >
                  <Trash size={18} color={colors.muted} />
                </Pressable>
              </View>
            );
          }}
        />
      )}

      {/* FAB */}
      <Pressable
        style={[styles.fab, { bottom: 20 }]}
        onPress={() => router.push({ pathname: "/add-transaction", params: { type: "expense" } })}
        testID="add-transaction-fab"
      >
        <Plus size={26} color={colors.onBrandPrimary} weight="bold" />
      </Pressable>
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  root: { flex: 1, backgroundColor: colors.surface },
  header: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  title: { fontSize: 22, fontWeight: "800", color: colors.onSurface, marginBottom: 12 },
  searchBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 12,
    paddingHorizontal: 12,
  },
  searchInput: { flex: 1, paddingVertical: 12, fontSize: 14, color: colors.onSurface },
  chipRow: { gap: 8, paddingVertical: 12, paddingRight: 8 },
  chip: {
    height: 36,
    justifyContent: "center",
    paddingHorizontal: 16,
    borderRadius: 999,
    backgroundColor: colors.surfaceSecondary,
    borderWidth: 1,
    borderColor: colors.border,
    flexShrink: 0,
  },
  chipActive: { backgroundColor: colors.brandPrimary, borderColor: colors.brandPrimary },
  chipText: { fontSize: 13, fontWeight: "600", color: colors.onSurfaceSecondary },
  chipTextActive: { color: colors.onBrandPrimary },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 8 },
  muted: { color: colors.muted, fontSize: 14, textAlign: "center" },
  emptyImg: { width: 150, height: 150, borderRadius: 20, marginBottom: 12 },
  emptyTitle: { fontSize: 17, fontWeight: "700", color: colors.onSurface },
  retryBtn: {
    backgroundColor: colors.brandPrimary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 10,
    marginTop: 8,
  },
  retryText: { color: colors.onBrandPrimary, fontWeight: "700" },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 14,
    padding: 12,
    marginBottom: 10,
    minHeight: 56,
  },
  icon: { width: 44, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  mid: { flex: 1 },
  rowTitle: { fontSize: 15, fontWeight: "600", color: colors.onSurface },
  rowSub: { fontSize: 12, color: colors.muted, marginTop: 2 },
  amount: { fontSize: 15, fontWeight: "700" },
  delBtn: { padding: 4 },
  fab: {
    position: "absolute",
    right: 20,
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: colors.brandPrimary,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
}));
