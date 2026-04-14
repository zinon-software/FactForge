export const FONTS = {
  DISPLAY: "'Bebas Neue', 'Impact', sans-serif",
  BODY:    "'DM Sans', 'Arial', sans-serif",
  MONO:    "'Space Mono', 'Courier New', monospace",
} as const;

export const FONT_SIZES = {
  HOOK:    108,  // Opening hook — massive (max 2 lines, 5-6 words)
  FACT:     82,  // Main fact — max 2 lines, 6-8 words per segment
  SUPPORT:  54,  // Supporting text
  LABEL:    32,  // Labels / categories
  NUMBER:  172,  // Standalone shock numbers
  CTA:      72,  // Call-to-action
} as const;
