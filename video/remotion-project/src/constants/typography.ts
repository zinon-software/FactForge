export const FONTS = {
  DISPLAY: "'Bebas Neue', 'Impact', sans-serif",
  BODY:    "'DM Sans', 'Arial', sans-serif",
  MONO:    "'Space Mono', 'Courier New', monospace",
} as const;

export const FONT_SIZES = {
  HOOK:    96,   // Opening hook — massive
  FACT:    64,   // Main fact sentences
  SUPPORT: 48,   // Supporting text
  LABEL:   32,   // Labels / categories
  NUMBER:  160,  // Standalone shock numbers
  CTA:     52,   // Call-to-action
} as const;
