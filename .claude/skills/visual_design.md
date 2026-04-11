# VISUAL DESIGN SYSTEM & REMOTION TEMPLATES
# For: Claude Code
# Purpose: Build production-grade video templates that look premium, not AI-generated
# Apply to: ALL video production — Shorts AND Long videos
# Save as: .claude/skills/visual_design.md

---

## 🔴 MANDATORY INSTRUCTION

Every video produced MUST use the templates and design rules in this document.
Generic, boring, or "AI-looking" visuals will kill CTR and retention instantly.
The visual design is the first thing the viewer judges in 0.3 seconds.
Build these templates ONCE — they run automatically for every video after that.
Never use default fonts, default colors, or default animations.
Every frame must look like it was designed by a professional motion designer.

---

## 🎨 PART 1 — THE VISUAL IDENTITY SYSTEM

### Channel Design DNA

Before building any template, commit to this exact design identity.
Every video must feel like it belongs to the same channel.

```
AESTHETIC DIRECTION: "Premium Dark Editorial"
→ Dark backgrounds (not pure black — deep navy, near-black charcoal)
→ Sharp accent colors that create visual electricity
→ Typography-dominant design (words as design elements)
→ Data visualization that feels like art
→ Motion that feels intentional, not decorative
→ The feeling: serious, intelligent, slightly dangerous knowledge
```

### Master Color Palette

```typescript
// Save in: video/remotion-project/src/constants/colors.ts

export const COLORS = {
  // Backgrounds
  BG_PRIMARY: "#0A0A0F",       // Near-black with slight blue — main background
  BG_SECONDARY: "#12121A",     // Slightly lighter — card backgrounds
  BG_OVERLAY: "rgba(10,10,15,0.85)", // Semi-transparent overlay on images
  
  // Accent Colors (rotate by content category)
  ACCENT_WEALTH: "#F0B429",    // Gold — for money/wealth topics
  ACCENT_POWER: "#E53E3E",     // Deep red — for military/power topics
  ACCENT_HISTORY: "#4299E1",   // Royal blue — for history/civilization
  ACCENT_SCIENCE: "#38B2AC",   // Teal — for science/nature topics
  ACCENT_COMPARE: "#9F7AEA",   // Purple — for comparison topics
  ACCENT_SHOCK: "#ED8936",     // Amber — for shocking facts
  
  // Text
  TEXT_PRIMARY: "#FFFFFF",     // Pure white — main text
  TEXT_SECONDARY: "#A0AEC0",   // Cool grey — supporting text
  TEXT_ACCENT: "#ECC94B",      // Warm yellow — highlighted numbers/words
  
  // Gradients
  GRAD_WEALTH: "linear-gradient(135deg, #F0B429 0%, #C05621 100%)",
  GRAD_POWER: "linear-gradient(135deg, #E53E3E 0%, #822727 100%)",
  GRAD_DARK: "linear-gradient(180deg, #0A0A0F 0%, #1A1A2E 100%)",
}

// Usage: pick accent color based on video_idea.category
export function getAccentColor(category: string): string {
  const map: Record<string, string> = {
    "wealth": COLORS.ACCENT_WEALTH,
    "power": COLORS.ACCENT_POWER,
    "history": COLORS.ACCENT_HISTORY,
    "science": COLORS.ACCENT_SCIENCE,
    "comparison": COLORS.ACCENT_COMPARE,
    "shocking": COLORS.ACCENT_SHOCK,
  }
  return map[category] || COLORS.ACCENT_SHOCK
}
```

### Master Typography System

```typescript
// Save in: video/remotion-project/src/constants/typography.ts
// Fonts loaded via Google Fonts in Root.tsx

export const FONTS = {
  // Display font — for titles, numbers, hooks
  // Character: Bold, authoritative, slightly condensed
  DISPLAY: "'Bebas Neue', sans-serif",
  
  // Body font — for facts, descriptions, supporting text  
  // Character: Clean, readable at speed, modern
  BODY: "'DM Sans', sans-serif",
  
  // Accent font — for labels, categories, metadata
  // Character: Geometric, technical feel
  ACCENT: "'Space Mono', monospace",
}

export const FONT_SIZES = {
  // Shorts (1080×1920) — larger because phone screens
  SHORT_HOOK: "88px",          // First sentence — massive
  SHORT_FACT: "52px",          // Main facts
  SHORT_SUPPORT: "36px",       // Supporting text
  SHORT_LABEL: "28px",         // Category labels, source citations
  SHORT_NUMBER: "140px",       // Standalone shocking numbers
  
  // Long video (1920×1080)
  LONG_TITLE: "72px",
  LONG_FACT: "48px",
  LONG_SUPPORT: "32px",
  LONG_LABEL: "24px",
  LONG_NUMBER: "120px",
}
```

---

## 🎬 PART 2 — SHORTS TEMPLATE SYSTEM (1080×1920)

### Template Architecture

```typescript
// Save in: video/remotion-project/src/compositions/ShortVideo.tsx

import { AbsoluteFill, useCurrentFrame, useVideoConfig, 
         spring, interpolate, Sequence } from "remotion"

interface ShortVideoProps {
  hook: string                    // First sentence (max 12 words)
  facts: FactItem[]               // Array of facts to reveal
  peak_fact: string               // The most shocking fact (revealed last)
  cta: string                     // Call to action
  category: string                // Determines color scheme
  background_video?: string       // Optional: path to background video
  background_image?: string       // Optional: path to background image
  accent_color: string            // From getAccentColor(category)
  audio_duration_frames: number   // Total frames = duration × fps
}

interface FactItem {
  text: string
  level: 1 | 2 | 3               // Importance level — affects animation intensity
  timestamp_frames: number        // When to show this fact (synced to audio)
}
```

### Short Video Layer System

```
Every Short has these layers (bottom to top):

LAYER 1 — BACKGROUND (always present)
→ Full-screen background video or image (from Pexels)
→ Heavy dark overlay: rgba(10,10,15,0.88)
→ Subtle noise texture overlay (3% opacity grain)
→ Vignette effect (darker edges, lighter center)

LAYER 2 — AMBIENT PARTICLES (decorative)
→ 8-12 tiny particles floating slowly upward
→ Color: accent color at 15% opacity
→ Size: 2-4px
→ Creates sense of depth and premium feel

LAYER 3 — PROGRESS BAR
→ Thin line at very top (4px height)
→ Color: accent color
→ Animates from 0% to 100% width over video duration
→ Tells viewer how much time is left = retention technique

LAYER 4 — CATEGORY LABEL (top-left corner)
→ Small pill/badge showing topic category
→ Example: "💰 WEALTH FACTS" or "⚔️ MILITARY POWER"
→ Font: ACCENT (Space Mono)
→ Background: accent color at 20% opacity
→ Border: 1px solid accent color at 60% opacity

LAYER 5 — MAIN CONTENT (center)
→ Changes based on current segment of video
→ See segment templates below

LAYER 6 — CHANNEL WATERMARK (bottom-right)
→ Small channel name or logo
→ Opacity: 40% (present but not distracting)
→ Font: ACCENT at 20px
```

### Segment Templates for Shorts

```typescript
// SEGMENT 1: HOOK (frames 0 to hook_end_frame)
// Design: Single line of massive text, letter by letter reveal

export const HookSegment: React.FC<{text: string, frame: number, accentColor: string}> = 
  ({text, frame, accentColor}) => {
  
  const words = text.split(" ")
  
  return (
    <AbsoluteFill style={{justifyContent: "center", alignItems: "center", padding: "60px"}}>
      <div style={{
        fontSize: FONT_SIZES.SHORT_HOOK,
        fontFamily: FONTS.DISPLAY,
        color: COLORS.TEXT_PRIMARY,
        textAlign: "center",
        lineHeight: 1.1,
        letterSpacing: "0.02em",
        textTransform: "uppercase",
      }}>
        {words.map((word, i) => {
          // Each word slides up and fades in, staggered by 3 frames
          const wordEntrance = spring({
            frame: frame - (i * 3),
            fps: 60,
            config: { damping: 12, stiffness: 200 }
          })
          return (
            <span key={i} style={{
              display: "inline-block",
              marginRight: "0.25em",
              opacity: interpolate(wordEntrance, [0, 1], [0, 1]),
              transform: `translateY(${interpolate(wordEntrance, [0, 1], [30, 0])}px)`,
              color: i === words.length - 1 ? accentColor : COLORS.TEXT_PRIMARY
              // Last word is accent color for emphasis
            }}>
              {word}
            </span>
          )
        })}
      </div>
    </AbsoluteFill>
  )
}
```

```typescript
// SEGMENT 2: FACT REVEAL (for each fact in the list)
// Design: Number + description, dramatic entrance

export const FactRevealSegment: React.FC<{
  rank?: number,        // For list videos: 10, 9, 8...
  fact: FactItem,
  frame: number,
  accentColor: string
}> = ({rank, fact, frame, accentColor}) => {
  
  const entrance = spring({frame, fps: 60, config: {damping: 14, stiffness: 180}})
  
  // Level 3 facts get a special "impact" animation (screen flash + scale)
  const isImpact = fact.level === 3
  const impactScale = isImpact ? 
    interpolate(spring({frame, fps: 60, config: {damping: 8, stiffness: 400}}), 
      [0, 1], [1.3, 1]) : 1
  
  return (
    <AbsoluteFill style={{justifyContent: "center", alignItems: "center", padding: "48px"}}>
      
      {/* Rank number (if list video) */}
      {rank && (
        <div style={{
          fontSize: FONT_SIZES.SHORT_NUMBER,
          fontFamily: FONTS.DISPLAY,
          color: accentColor,
          opacity: 0.15,
          position: "absolute",
          top: "10%",
          right: "5%",
          lineHeight: 1,
          transform: `scale(${impactScale})`,
        }}>
          #{rank}
        </div>
      )}
      
      {/* Main fact text */}
      <div style={{
        fontSize: FONT_SIZES.SHORT_FACT,
        fontFamily: FONTS.BODY,
        color: COLORS.TEXT_PRIMARY,
        textAlign: "center",
        fontWeight: 700,
        lineHeight: 1.3,
        transform: `translateY(${interpolate(entrance, [0,1], [50, 0])}px) scale(${impactScale})`,
        opacity: interpolate(entrance, [0, 1], [0, 1]),
        // Accent color on key numbers in the fact
        // (handled by splitting text at numbers)
      }}>
        {highlightNumbers(fact.text, accentColor)}
      </div>
      
      {/* Level 3 impact: accent color flash overlay */}
      {isImpact && frame < 6 && (
        <AbsoluteFill style={{
          backgroundColor: accentColor,
          opacity: interpolate(frame, [0, 6], [0.3, 0]),
        }} />
      )}
      
    </AbsoluteFill>
  )
}

// Helper: wraps numbers in colored spans
function highlightNumbers(text: string, color: string) {
  const parts = text.split(/(\d[\d,\.]*\s*(?:billion|million|trillion|thousand)?)/gi)
  return parts.map((part, i) => 
    /\d/.test(part) ? 
      <span key={i} style={{color, fontFamily: FONTS.DISPLAY}}>{part}</span> : 
      part
  )
}
```

```typescript
// SEGMENT 3: COMPARISON LAYOUT (for A vs B videos)
// Design: Split screen, two sides with contrasting colors

export const ComparisonSegment: React.FC<{
  leftLabel: string,
  leftValue: string,
  rightLabel: string, 
  rightValue: string,
  frame: number,
}> = ({leftLabel, leftValue, rightLabel, rightValue, frame}) => {
  
  const leftEntrance = spring({frame, fps: 60, config: {damping: 15, stiffness: 150}})
  const rightEntrance = spring({frame: frame - 8, fps: 60, config: {damping: 15, stiffness: 150}})
  
  return (
    <AbsoluteFill style={{flexDirection: "row"}}>
      
      {/* Left side */}
      <div style={{
        flex: 1,
        backgroundColor: "rgba(66, 153, 225, 0.15)",
        borderRight: "2px solid rgba(66, 153, 225, 0.4)",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center", padding: "40px",
        transform: `translateX(${interpolate(leftEntrance, [0,1], [-100, 0])}px)`,
        opacity: interpolate(leftEntrance, [0,1], [0, 1]),
      }}>
        <div style={{fontSize: "32px", fontFamily: FONTS.ACCENT, 
                     color: COLORS.ACCENT_HISTORY, letterSpacing: "0.1em"}}>
          {leftLabel}
        </div>
        <div style={{fontSize: FONT_SIZES.SHORT_NUMBER, fontFamily: FONTS.DISPLAY,
                     color: COLORS.TEXT_PRIMARY, lineHeight: 1}}>
          {leftValue}
        </div>
      </div>
      
      {/* VS divider */}
      <div style={{
        width: "80px", display: "flex", alignItems: "center", 
        justifyContent: "center", zIndex: 10,
      }}>
        <span style={{fontSize: "40px", fontFamily: FONTS.DISPLAY, 
                      color: COLORS.ACCENT_SHOCK, letterSpacing: "0.05em"}}>
          VS
        </span>
      </div>
      
      {/* Right side */}
      <div style={{
        flex: 1,
        backgroundColor: "rgba(229, 62, 62, 0.15)",
        borderLeft: "2px solid rgba(229, 62, 62, 0.4)",
        display: "flex", flexDirection: "column",
        justifyContent: "center", alignItems: "center", padding: "40px",
        transform: `translateX(${interpolate(rightEntrance, [0,1], [100, 0])}px)`,
        opacity: interpolate(rightEntrance, [0,1], [0, 1]),
      }}>
        <div style={{fontSize: "32px", fontFamily: FONTS.ACCENT,
                     color: COLORS.ACCENT_POWER, letterSpacing: "0.1em"}}>
          {rightLabel}
        </div>
        <div style={{fontSize: FONT_SIZES.SHORT_NUMBER, fontFamily: FONTS.DISPLAY,
                     color: COLORS.TEXT_PRIMARY, lineHeight: 1}}>
          {rightValue}
        </div>
      </div>
      
    </AbsoluteFill>
  )
}
```

```typescript
// SEGMENT 4: SHOCKING NUMBER (for stat-reveal videos)
// Design: Number counts up from 0, with scale and glow

export const ShockingNumberSegment: React.FC<{
  number: number,
  prefix?: string,     // "$" or ""
  suffix?: string,     // "billion" or "%"
  label: string,       // What this number means
  frame: number,
  accentColor: string,
}> = ({number, prefix, suffix, label, frame, accentColor}) => {
  
  // Count up animation over 45 frames (0.75 seconds)
  const progress = interpolate(frame, [0, 45], [0, 1], {extrapolateRight: "clamp"})
  const displayNumber = Math.round(number * progress)
  
  // Glow pulse effect
  const glowIntensity = interpolate(
    Math.sin(frame * 0.15), [-1, 1], [20, 60]
  )
  
  return (
    <AbsoluteFill style={{justifyContent: "center", alignItems: "center", padding: "60px"}}>
      
      {/* The number */}
      <div style={{
        fontSize: FONT_SIZES.SHORT_NUMBER,
        fontFamily: FONTS.DISPLAY,
        color: accentColor,
        textShadow: `0 0 ${glowIntensity}px ${accentColor}`,
        lineHeight: 1,
        textAlign: "center",
      }}>
        {prefix}{displayNumber.toLocaleString()}{suffix}
      </div>
      
      {/* Label below */}
      <div style={{
        fontSize: FONT_SIZES.SHORT_SUPPORT,
        fontFamily: FONTS.BODY,
        color: COLORS.TEXT_SECONDARY,
        textAlign: "center",
        marginTop: "24px",
        fontWeight: 500,
        opacity: interpolate(frame, [20, 40], [0, 1], {extrapolateLeft: "clamp"}),
      }}>
        {label}
      </div>
      
    </AbsoluteFill>
  )
}
```

---

## 📺 PART 3 — LONG VIDEO TEMPLATE SYSTEM (1920×1080)

### Long Video Layout Architecture

```typescript
// Save in: video/remotion-project/src/compositions/LongVideo.tsx

// Long videos use a 3-zone layout:
// 
// ┌─────────────────────────────────────────┐
// │  TOP BAR: Progress + Chapter indicator  │ 80px
// ├──────────────┬──────────────────────────┤
// │              │                          │
// │  LEFT PANEL  │    MAIN CONTENT AREA     │
// │  (context)   │    (primary information) │
// │   400px      │    1520px                │
// │              │                          │
// ├──────────────┴──────────────────────────┤
// │  BOTTOM BAR: Source citation            │ 60px
// └─────────────────────────────────────────┘

// Left panel shows:
// - Current rank/position (for list videos)
// - Category/topic label
// - Subtle decorative element

// Main content area shows:
// - Primary fact or visual
// - Supporting data
// - Animated elements
```

### Long Video Segment Templates

```typescript
// INTRO HOOK SEGMENT (first 8 seconds)
// Full screen, no layout zones — maximum impact

export const LongIntroHook: React.FC<{
  hook_text: string,
  frame: number,
  accentColor: string,
}> = ({hook_text, frame, accentColor}) => {
  
  // Cinematic zoom effect on background
  const zoomScale = interpolate(frame, [0, 180], [1.1, 1.0])
  
  return (
    <AbsoluteFill>
      {/* Zooming background */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundSize: `${zoomScale * 100}%`,
        backgroundPosition: "center",
        filter: "blur(2px)",
      }} />
      
      {/* Dark overlay */}
      <AbsoluteFill style={{backgroundColor: "rgba(10,10,15,0.75)"}} />
      
      {/* Hook text — cinematic title style */}
      <AbsoluteFill style={{
        justifyContent: "center", alignItems: "center", padding: "120px"
      }}>
        <div style={{
          fontSize: "96px",
          fontFamily: FONTS.DISPLAY,
          color: COLORS.TEXT_PRIMARY,
          textAlign: "center",
          lineHeight: 1.1,
          letterSpacing: "0.03em",
          maxWidth: "1400px",
          textTransform: "uppercase",
        }}>
          {hook_text}
        </div>
        
        {/* Accent underline that draws itself */}
        <div style={{
          height: "4px",
          backgroundColor: accentColor,
          width: `${interpolate(frame, [30, 90], [0, 600], {extrapolateLeft: "clamp", extrapolateRight: "clamp"})}px`,
          marginTop: "32px",
          boxShadow: `0 0 20px ${accentColor}`,
        }} />
      </AbsoluteFill>
    </AbsoluteFill>
  )
}
```

```typescript
// LIST ITEM REVEAL (for top-10 style long videos)
// Shows rank, name, key stat, brief explanation

export const ListItemReveal: React.FC<{
  rank: number,
  title: string,
  key_stat: string,
  description: string,
  image_url?: string,
  frame: number,
  accentColor: string,
}> = ({rank, title, key_stat, description, image_url, frame, accentColor}) => {
  
  const entrance = spring({frame, fps: 30, config: {damping: 18, stiffness: 100}})
  
  return (
    <AbsoluteFill style={{flexDirection: "row", padding: "80px", gap: "60px"}}>
      
      {/* LEFT: Rank + Image */}
      <div style={{
        width: "500px",
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        transform: `translateX(${interpolate(entrance, [0,1], [-80, 0])}px)`,
        opacity: interpolate(entrance, [0, 1], [0, 1]),
      }}>
        {/* Giant rank number */}
        <div style={{
          fontSize: "200px",
          fontFamily: FONTS.DISPLAY,
          color: accentColor,
          opacity: 0.2,
          lineHeight: 1,
          position: "absolute",
        }}>
          {rank}
        </div>
        
        {/* Image if available */}
        {image_url && (
          <img src={image_url} style={{
            width: "400px", height: "300px",
            objectFit: "cover",
            borderRadius: "12px",
            border: `2px solid ${accentColor}40`,
            position: "relative",
          }} />
        )}
      </div>
      
      {/* RIGHT: Content */}
      <div style={{
        flex: 1,
        display: "flex", flexDirection: "column",
        justifyContent: "center", gap: "24px",
        transform: `translateX(${interpolate(entrance, [0,1], [80, 0])}px)`,
        opacity: interpolate(entrance, [0, 1], [0, 1]),
      }}>
        {/* Rank label */}
        <div style={{
          fontSize: "24px", fontFamily: FONTS.ACCENT,
          color: accentColor, letterSpacing: "0.15em",
        }}>
          #{rank}
        </div>
        
        {/* Title */}
        <div style={{
          fontSize: FONT_SIZES.LONG_TITLE,
          fontFamily: FONTS.DISPLAY,
          color: COLORS.TEXT_PRIMARY,
          lineHeight: 1.1,
          textTransform: "uppercase",
        }}>
          {title}
        </div>
        
        {/* Key stat */}
        <div style={{
          fontSize: "56px",
          fontFamily: FONTS.DISPLAY,
          color: accentColor,
          lineHeight: 1,
        }}>
          {key_stat}
        </div>
        
        {/* Description */}
        <div style={{
          fontSize: FONT_SIZES.LONG_SUPPORT,
          fontFamily: FONTS.BODY,
          color: COLORS.TEXT_SECONDARY,
          lineHeight: 1.6,
          fontWeight: 400,
          maxWidth: "900px",
        }}>
          {description}
        </div>
        
        {/* Accent line */}
        <div style={{
          height: "2px", width: "120px",
          backgroundColor: accentColor,
          opacity: 0.6,
        }} />
      </div>
      
    </AbsoluteFill>
  )
}
```

---

## 🖼️ PART 4 — THUMBNAIL GENERATION SYSTEM

### Thumbnail Templates (Pillow Python)

```python
# Save in: agents/thumbnail_agent.py

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import requests
from io import BytesIO

def generate_short_thumbnail(
    shocking_text: str,      # Max 3 words
    accent_color: tuple,     # RGB tuple from category
    background_image_url: str,
    output_path: str
) -> str:
    
    # Canvas: 1080×1920
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), "#0A0A0F")
    
    # LAYER 1: Background image (blurred, darkened)
    if background_image_url:
        bg_response = requests.get(background_image_url)
        bg = Image.open(BytesIO(bg_response.content))
        bg = bg.resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=8))
        bg = ImageEnhance.Brightness(bg).enhance(0.3)  # Darken 70%
        img.paste(bg, (0, 0))
    
    draw = ImageDraw.Draw(img)
    
    # LAYER 2: Gradient overlay (darker at edges)
    for y in range(H):
        edge_distance = min(y, H - y) / (H / 2)
        overlay_alpha = int((1 - edge_distance) * 120)
        draw.line([(0, y), (W, y)], 
                  fill=(10, 10, 15, overlay_alpha))
    
    # LAYER 3: Accent color diagonal stripe (subtle)
    stripe_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    stripe_draw = ImageDraw.Draw(stripe_img)
    r, g, b = accent_color
    stripe_draw.polygon(
        [(0, H*0.6), (W, H*0.45), (W, H*0.55), (0, H*0.7)],
        fill=(r, g, b, 30)
    )
    img = Image.alpha_composite(img.convert("RGBA"), stripe_img).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # LAYER 4: Main text (3 words maximum, massive font)
    try:
        font_display = ImageFont.truetype("fonts/BebasNeue-Regular.ttf", 200)
        font_small = ImageFont.truetype("fonts/DMSans-Bold.ttf", 60)
    except:
        font_display = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    words = shocking_text.upper().split()[:3]  # Max 3 words
    
    # Center text vertically
    total_height = len(words) * 220
    start_y = (H - total_height) // 2
    
    for i, word in enumerate(words):
        # Shadow (offset)
        draw.text((W//2 + 4, start_y + i*220 + 4), word,
                  font=font_display, fill=(0,0,0,180), anchor="mm")
        # Main text
        color = accent_color if i == len(words)-1 else (255, 255, 255)
        draw.text((W//2, start_y + i*220), word,
                  font=font_display, fill=color, anchor="mm")
    
    # LAYER 5: Channel watermark (bottom right)
    draw.text((W - 40, H - 40), "FactForge", 
              font=font_small, fill=(255,255,255,100), anchor="rm")
    
    # LAYER 6: Subtle border glow
    r, g, b = accent_color
    for i in range(3):
        draw.rectangle([i*2, i*2, W-i*2, H-i*2],
                       outline=(r, g, b, 60-i*15), width=2)
    
    img.save(output_path, "JPEG", quality=95)
    return output_path


def generate_long_thumbnail(
    title_text: str,          # Max 5 words
    key_number: str,          # Shocking number to display
    accent_color: tuple,
    background_image_url: str,
    output_path: str
) -> str:
    
    # Canvas: 1280×720
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), "#0A0A0F")
    draw = ImageDraw.Draw(img)
    
    # Split layout: left 55% = image, right 45% = text
    split_x = int(W * 0.55)
    
    # LEFT: Background image
    if background_image_url:
        bg_response = requests.get(background_image_url)
        bg = Image.open(BytesIO(bg_response.content))
        bg = bg.resize((split_x, H), Image.LANCZOS)
        img.paste(bg, (0, 0))
        
        # Gradient fade on right edge of image
        fade = Image.new("RGBA", (200, H))
        for x in range(200):
            alpha = int(x / 200 * 255)
            for y in range(H):
                fade.putpixel((x, y), (10, 10, 15, alpha))
        img.paste(bg, (0, 0))
    
    # RIGHT: Dark background with content
    draw.rectangle([split_x - 100, 0, W, H], fill="#0A0A0F")
    
    # Accent color left border on text section
    r, g, b = accent_color
    draw.rectangle([split_x - 6, 0, split_x, H], fill=accent_color)
    
    # Key number (top of text section)
    try:
        font_number = ImageFont.truetype("fonts/BebasNeue-Regular.ttf", 160)
        font_title = ImageFont.truetype("fonts/DMSans-Bold.ttf", 52)
    except:
        font_number = ImageFont.load_default()
        font_title = ImageFont.load_default()
    
    text_center_x = split_x + (W - split_x) // 2
    
    # Number with glow effect
    draw.text((text_center_x + 3, H*0.35 + 3), key_number,
              font=font_number, fill=(0,0,0), anchor="mm")
    draw.text((text_center_x, H*0.35), key_number,
              font=font_number, fill=accent_color, anchor="mm")
    
    # Title text
    words = title_text.split()
    line1 = " ".join(words[:3])
    line2 = " ".join(words[3:]) if len(words) > 3 else ""
    
    draw.text((text_center_x, H*0.62), line1.upper(),
              font=font_title, fill=(255,255,255), anchor="mm")
    if line2:
        draw.text((text_center_x, H*0.75), line2.upper(),
                  font=font_title, fill=(200,200,200), anchor="mm")
    
    img.save(output_path, "JPEG", quality=95)
    return output_path
```

---

## ⚡ PART 5 — ANIMATION PRINCIPLES

### The 5 Animation Rules

```typescript
// Rule 1: SPRING PHYSICS ONLY
// Never use linear animations — they look robotic
// Always use spring() from Remotion for all movement
// Config guide:
//   damping: 12-15 = bouncy (for list items, numbers)
//   damping: 18-22 = smooth (for text reveals, transitions)
//   stiffness: 100-150 = slow entrance (for important facts)
//   stiffness: 200-300 = fast entrance (for quick reveals)

// Rule 2: STAGGER EVERYTHING
// Never animate multiple elements at the same time
// Offset each element by 4-8 frames
// This creates a cascade effect that feels designed, not automated

// Rule 3: NUMBERS ALWAYS COUNT UP
// Never show a number statically
// Always animate from 0 to the final value
// Duration: 30-60 frames (0.5-1 second)
// Use easeOut curve (fast start, slow end)

// Rule 4: TEXT ENTERS FROM BOTTOM, EXITS UPWARD
// Entrance: translateY(40px → 0) + opacity(0 → 1)
// Exit: translateY(0 → -40px) + opacity(1 → 0)
// This creates natural reading flow

// Rule 5: ONE IMPACT MOMENT PER VIDEO SEGMENT
// The Level 3 (most shocking) fact gets a special treatment:
// - Brief white/accent flash (2-3 frames)
// - Scale punch (1.2 → 1.0 spring)
// - Text glow effect
// - Everything else fades slightly
// This trains the viewer to watch for these moments
```

### Transition System Between Segments

```typescript
// Use these transitions, never "cut" directly between segments

export const TRANSITIONS = {
  
  FADE: (frame: number, duration = 15) => ({
    opacity: interpolate(frame, [0, duration], [0, 1], {extrapolateLeft: "clamp"})
  }),
  
  SLIDE_UP: (frame: number, duration = 20) => ({
    opacity: interpolate(frame, [0, duration], [0, 1], {extrapolateLeft: "clamp"}),
    transform: `translateY(${interpolate(
      spring({frame, fps: 60, config: {damping: 15, stiffness: 150}}),
      [0, 1], [60, 0]
    )}px)`
  }),
  
  SCALE_IN: (frame: number) => ({
    transform: `scale(${interpolate(
      spring({frame, fps: 60, config: {damping: 12, stiffness: 200}}),
      [0, 1], [0.85, 1]
    )})`,
    opacity: interpolate(frame, [0, 10], [0, 1], {extrapolateLeft: "clamp"})
  }),
  
  WIPE_RIGHT: (frame: number, width: number, duration = 20) => ({
    clipPath: `inset(0 ${interpolate(
      frame, [0, duration], [100, 0], {extrapolateLeft: "clamp"}
    )}% 0 0)`
  }),
}
```

---

## 🔧 PART 6 — BACKGROUND MEDIA SYSTEM

### Automated Background Selection

```python
# Save in: agents/media_agent.py

import requests

PEXELS_CATEGORIES = {
    "wealth": ["gold coins", "luxury mansion", "stock market", "currency"],
    "power": ["military tanks", "capitol building", "army soldiers", "warship"],
    "history": ["ancient ruins", "historical map", "medieval castle", "old city"],
    "science": ["space galaxy", "laboratory", "dna strand", "quantum physics"],
    "comparison": ["city skyline", "globe earth", "flags", "world map"],
    "nature": ["deep ocean", "rainforest", "volcano", "wildlife"],
}

def fetch_background_media(category: str, count: int = 5) -> list:
    queries = PEXELS_CATEGORIES.get(category, ["abstract dark"])
    
    results = []
    for query in queries[:2]:  # Use first 2 queries
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 3, "orientation": "portrait"}
        )
        videos = response.json().get("videos", [])
        
        for video in videos:
            # Get the HD version (not 4K — too large)
            hd_file = next(
                (f for f in video["video_files"] if f["quality"] == "hd"),
                video["video_files"][0]
            )
            results.append({
                "id": video["id"],
                "url": hd_file["link"],
                "width": hd_file["width"],
                "height": hd_file["height"],
                "duration": video["duration"],
                "credit": video["user"]["name"],
            })
    
    return results[:count]
```

---

## ✅ PART 7 — VISUAL QUALITY CHECKLIST

Every video passes this before rendering final version.
Minimum score: 14/16

```
DESIGN CONSISTENCY (4 points):
[ ] Uses correct color palette for category
[ ] Correct fonts (Bebas Neue + DM Sans + Space Mono)
[ ] Channel watermark present and subtle
[ ] Visual style matches channel identity

ANIMATION QUALITY (4 points):
[ ] Spring physics used (no linear animations)
[ ] Elements staggered (no simultaneous animations)
[ ] Numbers count up from zero
[ ] Level 3 fact has impact moment animation

READABILITY (4 points):
[ ] Text readable at mobile screen size
[ ] Numbers highlighted in accent color
[ ] Contrast ratio > 4.5:1 (accessibility minimum)
[ ] Background doesn't compete with text

TECHNICAL (4 points):
[ ] Shorts: 1080×1920, 60fps
[ ] Long: 1920×1080, 30fps
[ ] Thumbnail: correct dimensions, named with keyword
[ ] File size optimized (no unnecessary 4K assets)

VISUAL SCORE: __ / 16
Minimum to render: 14/16
```

---

## 📋 FINAL IMPLEMENTATION INSTRUCTION

Install required fonts in project:
```bash
mkdir -p video/remotion-project/public/fonts
# Download to that folder:
# BebasNeue-Regular.ttf (Google Fonts)
# DMSans-Bold.ttf (Google Fonts)
# SpaceMono-Regular.ttf (Google Fonts)
```

Install required npm packages:
```bash
cd video/remotion-project
npm install @remotion/motion-blur
```

The full production pipeline with all 4 quality gates:

```python
PRODUCTION_ORDER = [
    "1. select_idea()",
    "2. research_and_verify()",        # fact_verification.md  → 18/20
    "3. write_script()",               # content_psychology.md → 80/100
    "4. generate_voice()",
    "5. generate_background_media()",  # visual_design.md
    "6. generate_video()",             # Remotion render
    "7. check_visual_score()",         # visual_design.md      → 14/16
    "8. generate_thumbnail()",         # visual_design.md
    "9. generate_metadata()",
    "10. check_seo_score()",           # youtube_seo.md        → 18/22
    "11. translate_metadata()",
    "12. schedule_and_publish()",
]

# FOUR quality gates:
# Accuracy    >= 18/20  → Content    >= 80/100
# Visual      >= 14/16  → SEO        >= 18/22
# All four must pass. No exceptions.
```

The visual system is the final layer that transforms
verified facts + great scripts + SEO optimization
into a video that looks worth watching before the first second plays.
Design is not decoration — it is credibility at first glance.
