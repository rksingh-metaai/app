// Design tokens for IndicFinance. Light + Dark themes.
// Keys match the "color" block of /app/design_guidelines.json.

import { useMemo } from "react";
import { Appearance, StyleSheet, useColorScheme } from "react-native";

export type ColorScheme = "light" | "dark";

const light = {
  surface: "#FFFFFF",
  onSurface: "#171717",
  surfaceSecondary: "#F5F5F5",
  onSurfaceSecondary: "#262626",
  surfaceTertiary: "#E5E5E5",
  onSurfaceTertiary: "#404040",
  surfaceInverse: "#171717",
  onSurfaceInverse: "#FFFFFF",
  muted: "#737373",

  brand: "#064E3B",
  onBrand: "#FFFFFF",
  brandPrimary: "#059669",
  onBrandPrimary: "#FFFFFF",
  brandSecondary: "#34D399",
  onBrandSecondary: "#064E3B",
  brandTertiary: "#D1FAE5",
  onBrandTertiary: "#064E3B",

  success: "#16A34A",
  onSuccess: "#FFFFFF",
  warning: "#D97706",
  onWarning: "#FFFFFF",
  error: "#DC2626",
  onError: "#FFFFFF",
  info: "#4B5563",
  onInfo: "#FFFFFF",

  border: "#E5E5E5",
  borderStrong: "#D4D4D4",
  divider: "#F5F5F5",
};

const dark: typeof light = {
  surface: "#171717",
  onSurface: "#F5F5F5",
  surfaceSecondary: "#262626",
  onSurfaceSecondary: "#E5E5E5",
  surfaceTertiary: "#404040",
  onSurfaceTertiary: "#D4D4D4",
  surfaceInverse: "#FFFFFF",
  onSurfaceInverse: "#171717",
  muted: "#A3A3A3",

  brand: "#059669",
  onBrand: "#FFFFFF",
  brandPrimary: "#10B981",
  onBrandPrimary: "#064E3B",
  brandSecondary: "#047857",
  onBrandSecondary: "#FFFFFF",
  brandTertiary: "#064E3B",
  onBrandTertiary: "#D1FAE5",

  success: "#22C55E",
  onSuccess: "#FFFFFF",
  warning: "#F59E0B",
  onWarning: "#FFFFFF",
  error: "#EF4444",
  onError: "#FFFFFF",
  info: "#9CA3AF",
  onInfo: "#171717",

  border: "#404040",
  borderStrong: "#525252",
  divider: "#262626",
};

export type ThemeColors = typeof light;

export const defaultScheme = "light" satisfies ColorScheme;

export const themes: { light: ThemeColors; dark?: ThemeColors } = { light, dark };

export function setColorScheme(scheme: ColorScheme | null) {
  Appearance.setColorScheme?.(scheme);
}

setColorScheme?.(themes.dark ? null : defaultScheme);

export function useTheme(): { scheme: ColorScheme; colors: ThemeColors } {
  const system = useColorScheme();
  const scheme: ColorScheme = system && themes[system] ? system : defaultScheme;
  return { scheme, colors: themes[scheme] ?? themes.light };
}

export function makeStyles<T extends StyleSheet.NamedStyles<T> | StyleSheet.NamedStyles<any>>(
  factory: (colors: ThemeColors) => T & StyleSheet.NamedStyles<any>,
): () => T {
  return function useStyles(): T {
    const { colors } = useTheme();
    return useMemo(() => StyleSheet.create(factory(colors)), [colors]);
  };
}
