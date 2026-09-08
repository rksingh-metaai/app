import React, { useMemo } from "react";
import { View, Text, Pressable, ScrollView } from "react-native";

import { makeStyles, useTheme } from "@/src/theme";
import { useI18n } from "@/src/i18n";
import { LangCode } from "@/src/i18n/translations";

const LOCALE: Record<LangCode, string> = {
  en: "en-IN", hi: "hi-IN", ta: "ta-IN", te: "te-IN", bn: "bn-IN", mr: "mr-IN",
};

function sameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

export function DateStrip({
  value,
  onChange,
}: {
  value: string;
  onChange: (iso: string) => void;
}) {
  const styles = useStyles();
  const { colors } = useTheme();
  const { lang, t } = useI18n();

  const selected = useMemo(() => (value ? new Date(value) : new Date()), [value]);

  const days = useMemo(() => {
    const out: Date[] = [];
    const today = new Date();
    for (let i = 0; i < 45; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      out.push(d);
    }
    return out;
  }, []);

  const weekdayFmt = new Intl.DateTimeFormat(LOCALE[lang] ?? "en-IN", { weekday: "short" });

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      {days.map((d, i) => {
        const active = sameDay(d, selected);
        const top = i === 0 ? t("today_label") : i === 1 ? t("yesterday_label") : weekdayFmt.format(d);
        return (
          <Pressable
            key={i}
            style={[styles.chip, active && styles.chipActive]}
            onPress={() => {
              const picked = new Date(d);
              picked.setHours(12, 0, 0, 0);
              onChange(picked.toISOString());
            }}
            testID={`date-chip-${i}`}
          >
            <Text style={[styles.top, active && styles.topActive]} numberOfLines={1}>
              {top}
            </Text>
            <Text style={[styles.day, active && styles.dayActive]}>{d.getDate()}</Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const useStyles = makeStyles((colors) => ({
  row: { gap: 8, paddingRight: 8 },
  chip: {
    width: 58,
    paddingVertical: 10,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.surfaceSecondary,
    alignItems: "center",
    gap: 4,
    flexShrink: 0,
  },
  chipActive: { borderColor: colors.brandPrimary, backgroundColor: colors.brandTertiary },
  top: { fontSize: 11, color: colors.muted, fontWeight: "600" },
  topActive: { color: colors.brand },
  day: { fontSize: 18, fontWeight: "800", color: colors.onSurface },
  dayActive: { color: colors.brand },
}));
