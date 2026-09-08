import { LangCode } from "@/src/i18n/translations";
import type { TransKey } from "@/src/i18n/translations";

export function formatCurrency(amount: number, withSign = false): string {
  const abs = Math.abs(amount);
  const formatted = new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(Math.round(abs));
  const sign = amount < 0 ? "-" : withSign ? "+" : "";
  return `${sign}₹${formatted}`;
}

export function formatCompact(amount: number): string {
  const abs = Math.abs(amount);
  if (abs >= 10000000) return `₹${(amount / 10000000).toFixed(2)}Cr`;
  if (abs >= 100000) return `₹${(amount / 100000).toFixed(2)}L`;
  if (abs >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;
  return `₹${Math.round(amount)}`;
}

export const CATEGORY_KEYS = [
  "food",
  "groceries",
  "shopping",
  "transport",
  "bills",
  "entertainment",
  "health",
  "salary",
  "investment",
  "other",
] as const;

export type CategoryKey = (typeof CATEGORY_KEYS)[number];

export const CATEGORY_COLORS: Record<string, string> = {
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

export function categoryLabelKey(cat: string): TransKey {
  return `cat_${cat}` as TransKey;
}

export function accountLabelKey(type: string): TransKey {
  return `acc_${type}` as TransKey;
}

export function initials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

const RELATIVE_LOCALE: Record<LangCode, string> = {
  en: "en-IN",
  hi: "hi-IN",
  ta: "ta-IN",
  te: "te-IN",
  bn: "bn-IN",
  mr: "mr-IN",
};

export function formatDate(iso: string, lang: LangCode): string {
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat(RELATIVE_LOCALE[lang] ?? "en-IN", {
      day: "numeric",
      month: "short",
    }).format(d);
  } catch {
    return iso.slice(0, 10);
  }
}
