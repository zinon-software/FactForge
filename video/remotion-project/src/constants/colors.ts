export const COLORS = {
  BG_PRIMARY:   "#0A0A0F",
  BG_SECONDARY: "#12121A",

  ACCENT_WEALTH:  "#F0B429",
  ACCENT_POWER:   "#E53E3E",
  ACCENT_HISTORY: "#4299E1",
  ACCENT_SCIENCE: "#38B2AC",
  ACCENT_COMPARE: "#9F7AEA",
  ACCENT_SHOCK:   "#ED8936",

  TEXT_PRIMARY:   "#FFFFFF",
  TEXT_SECONDARY: "#A0AEC0",
} as const;

export type ColorTheme =
  | "wealth"
  | "power"
  | "history"
  | "science"
  | "comparison"
  | "shocking";

export function getAccentColor(theme: ColorTheme): string {
  const map: Record<ColorTheme, string> = {
    wealth:     COLORS.ACCENT_WEALTH,
    power:      COLORS.ACCENT_POWER,
    history:    COLORS.ACCENT_HISTORY,
    science:    COLORS.ACCENT_SCIENCE,
    comparison: COLORS.ACCENT_COMPARE,
    shocking:   COLORS.ACCENT_SHOCK,
  };
  return map[theme] ?? COLORS.ACCENT_SHOCK;
}

export function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}
