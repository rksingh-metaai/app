import React from "react";
import { View, Text } from "react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { LangCode } from "@/src/i18n/translations";
import { formatCompact } from "@/src/lib/format";

export type MonthPoint = { year: number; month: number; income: number; expense: number };

const LOCALE: Record<LangCode, string> = {
  en: "en-IN",
  hi: "hi-IN",
  ta: "ta-IN",
  te: "te-IN",
  bn: "bn-IN",
  mr: "mr-IN",
};

export function TrendBars({
  months,
  lang,
  showIncome = true,
  height = 130,
}: {
  months: MonthPoint[];
  lang: LangCode;
  showIncome?: boolean;
  height?: number;
}) {
  const styles = useStyles();
  const { colors } = useTheme();

  const max = Math.max(
    1,
    ...months.map((m) => (showIncome ? Math.max(m.income, m.expense) : m.expense)),
  );

  const label = (m: MonthPoint) => {
    try {
      return new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { month: "short" }).format(
        new Date(m.year, m.month - 1, 1),
      );
    } catch {
      return String(m.month);
    }
  };

  return (
    <View style={styles.wrap}>
      <View style={[styles.barsRow, { height }]}>
        {months.map((m, i) => {
          const eh = Math.max(4, (m.expense / max) * (height - 24));
          const ih = Math.max(4, (m.income / max) * (height - 24));
          const tallest = Math.max(m.expense, showIncome ? m.income : 0);
          return (
            <View key={i} style={styles.col}>
              {tallest > 0 ? (
                <Text style={styles.valueLabel}>{formatCompact(tallest)}</Text>
              ) : (
                <View style={{ height: 14 }} />
              )}
              <View style={styles.barGroup}>
                {showIncome ? (
                  <View style={[styles.bar, { height: ih, backgroundColor: colors.brandSecondary }]} />
                ) : null}
                <View style={[styles.bar, { height: eh, backgroundColor: colors.brandPrimary }]} />
              </View>
              <Text style={styles.monthLabel}>{label(m)}</Text>
            </View>
          );
        })}
      </View>
      {showIncome ? (
        <View style={styles.legend}>
          <View style={styles.legendItem}>
            <View style={[styles.dot, { backgroundColor: colors.brandSecondary }]} />
            <Text style={styles.legendText}>Income</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.dot, { backgroundColor: colors.brandPrimary }]} />
            <Text style={styles.legendText}>Expense</Text>
          </View>
        </View>
      ) : null}
    </View>
  );
}

const useStyles = makeStyles((colors) => ({
  wrap: { width: "100%" },
  barsRow: { flexDirection: "row", alignItems: "flex-end", justifyContent: "space-between" },
  col: { flex: 1, alignItems: "center", justifyContent: "flex-end", gap: 6 },
  barGroup: { flexDirection: "row", alignItems: "flex-end", gap: 3 },
  bar: { width: 10, borderRadius: 4 },
  valueLabel: { fontSize: 9, color: colors.muted, fontWeight: "600" },
  monthLabel: { fontSize: 11, color: colors.muted, fontWeight: "600" },
  legend: { flexDirection: "row", justifyContent: "center", gap: 20, marginTop: 14 },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 6 },
  dot: { width: 10, height: 10, borderRadius: 5 },
  legendText: { fontSize: 12, color: colors.onSurfaceSecondary, fontWeight: "600" },
}));
