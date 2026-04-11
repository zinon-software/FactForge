import "@fontsource/bebas-neue";
import "@fontsource/dm-sans/700.css";
import "@fontsource/space-mono/700.css";

import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from "remotion";
import { z } from "zod";

import { AccentLine, CategoryBadge, Watermark } from "../components/AccentLine";
import { CountUpNumber } from "../components/CountUpNumber";
import { ImpactFlash, ScalePunch } from "../components/ImpactFlash";
import { Particles } from "../components/Particles";
import { SegmentBackground } from "../components/SegmentBackground";
import { TopProgressBar } from "../components/TopProgressBar";
import { WordByWordReveal } from "../components/WordByWordReveal";
import { COLORS, ColorTheme, getAccentColor } from "../constants/colors";
import { FONT_SIZES, FONTS } from "../constants/typography";

// ─────────────────────────── Schema ────────────────────────────────────────

export const segmentSchema = z.object({
  text: z.string(),
  startFrame: z.number(),
  endFrame: z.number(),
  // visual treatment
  type: z.enum([
    "hook",       // opening line — massive, accent
    "fact",       // normal fact sentence
    "impact",     // level-3 shock — punch + flash
    "number",     // count-up statistic
    "cta",        // call to action
  ]),
  // per-segment background video (staticFile key, e.g. "bg_videos/scene_call.mp4")
  backgroundVideo: z.string().optional(),
  kenBurns: z.enum(["zoom-in", "zoom-out", "pan-left", "pan-right"]).optional(),
  // for type==="number"
  numberValue: z.number().optional(),
  numberPrefix: z.string().optional(),
  numberSuffix: z.string().optional(),
  numberLabel: z.string().optional(),
  // optional words to highlight in accent color
  highlightWords: z.array(z.string()).optional(),
});

export const shortVideoSchema = z.object({
  videoId:             z.string(),
  categoryLabel:       z.string(),          // e.g. "AI CRIME"
  colorTheme:          z.enum(["wealth","power","history","science","comparison","shocking"]),
  segments:            z.array(segmentSchema),
  audioFile:           z.string().nullable(),
  backgroundVideoUrl:  z.string().nullable(),
  totalDurationFrames: z.number(),
});

export type ShortVideoProps = z.infer<typeof shortVideoSchema>;

// ─────────────────────── Background gradient (per theme) ───────────────────

const BG_GRADIENTS: Record<ColorTheme, string> = {
  wealth:     "radial-gradient(ellipse at 30% 70%, #1a1000 0%, #0A0A0F 70%)",
  power:      "radial-gradient(ellipse at 70% 30%, #1a0000 0%, #0A0A0F 70%)",
  history:    "radial-gradient(ellipse at 20% 80%, #001230 0%, #0A0A0F 70%)",
  science:    "radial-gradient(ellipse at 50% 50%, #001a1a 0%, #0A0A0F 70%)",
  comparison: "radial-gradient(ellipse at 80% 20%, #120020 0%, #0A0A0F 70%)",
  shocking:   "radial-gradient(ellipse at 40% 60%, #1a0800 0%, #0A0A0F 70%)",
};

// ─────────────────────────── Vignette ──────────────────────────────────────

const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(0,0,0,0.7) 100%)",
      pointerEvents: "none",
    }}
  />
);

// ─────────────────────── Segment renderer ──────────────────────────────────

interface SegmentViewProps {
  seg: z.infer<typeof segmentSchema>;
  accentColor: string;
  globalBgGradient: string;
}

const SegmentView: React.FC<SegmentViewProps> = ({ seg, accentColor, globalBgGradient }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const KB_MODES: Array<"zoom-in" | "zoom-out" | "pan-left" | "pan-right"> =
    ["zoom-in", "zoom-out", "pan-left", "pan-right"];
  const kenBurns = seg.kenBurns ?? KB_MODES[seg.startFrame % 4];

  // Exit: fade + slide up when near segment end
  const segDuration = seg.endFrame - seg.startFrame;
  const exitStart = segDuration - 12;
  const exitOpacity = interpolate(frame, [exitStart, segDuration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitY = interpolate(frame, [exitStart, segDuration], [0, -20], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Per-segment background ────────────────────────────────────────────────
  const bg = seg.backgroundVideo ? (
    <SegmentBackground
      src={seg.backgroundVideo}
      kenBurns={kenBurns}
      overlayOpacity={seg.type === "impact" ? 0.72 : 0.62}
      accentColor={accentColor}
    />
  ) : (
    <AbsoluteFill style={{ background: globalBgGradient }} />
  );

  // ── HOOK ──────────────────────────────────────────────────────────────────
  if (seg.type === "hook") {
    const entrance = spring({ frame, fps, config: { damping: 10, stiffness: 160 } });
    const scale = interpolate(entrance, [0, 1], [0.82, 1]);

    return (
      <AbsoluteFill>
        {bg}
        <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: "60px 64px",
          opacity: exitOpacity,
          transform: `translateY(${exitY}px)`,
        }}
      >
        <div style={{ transform: `scale(${scale})`, textAlign: "center" }}>
          <WordByWordReveal
            text={seg.text}
            fontSize={FONT_SIZES.HOOK}
            color={COLORS.TEXT_PRIMARY}
            accentColor={accentColor}
            staggerFrames={3}
            highlightWords={seg.highlightWords ?? []}
          />
          <div style={{ display: "flex", justifyContent: "center" }}>
            <AccentLine accentColor={accentColor} maxWidth={320} height={4} delayFrames={18} />
          </div>
        </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // ── IMPACT ────────────────────────────────────────────────────────────────
  if (seg.type === "impact") {
    return (
      <AbsoluteFill>
        {bg}
        <ImpactFlash accentColor={accentColor} flashDurationFrames={10} />
        <AbsoluteFill
          style={{
            justifyContent: "center",
            alignItems: "center",
            padding: "60px 64px",
            opacity: exitOpacity,
            transform: `translateY(${exitY}px)`,
          }}
        >
          <ScalePunch peakScale={1.08}>
            <WordByWordReveal
              text={seg.text}
              fontSize={FONT_SIZES.FACT}
              color={COLORS.TEXT_PRIMARY}
              accentColor={accentColor}
              staggerFrames={2}
              highlightWords={seg.highlightWords ?? []}
            />
          </ScalePunch>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // ── COUNT-UP NUMBER ───────────────────────────────────────────────────────
  if (seg.type === "number" && seg.numberValue !== undefined) {
    return (
      <AbsoluteFill>
        {bg}
        <ImpactFlash accentColor={accentColor} flashDurationFrames={6} />
        <AbsoluteFill
          style={{
            justifyContent: "center",
            alignItems: "center",
            flexDirection: "column",
            gap: 24,
            padding: "60px 64px",
            opacity: exitOpacity,
            transform: `translateY(${exitY}px)`,
          }}
        >
          <ScalePunch peakScale={1.06}>
            <CountUpNumber
              value={seg.numberValue}
              prefix={seg.numberPrefix ?? ""}
              suffix={seg.numberSuffix ?? ""}
              label={seg.numberLabel ?? ""}
              accentColor={accentColor}
              fontSize={FONT_SIZES.NUMBER}
              countDurationSeconds={0.8}
            />
          </ScalePunch>
          {seg.text && (
            <div
              style={{
                marginTop: 8,
                opacity: interpolate(frame, [30, 45], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
                transform: `translateY(${interpolate(
                  spring({ frame: frame - 30, fps, config: { damping: 14, stiffness: 160 } }),
                  [0, 1], [20, 0]
                )}px)`,
              }}
            >
              <WordByWordReveal
                text={seg.text}
                fontSize={FONT_SIZES.SUPPORT}
                color={COLORS.TEXT_SECONDARY}
                accentColor={accentColor}
                staggerFrames={5}
                highlightWords={seg.highlightWords ?? []}
              />
            </div>
          )}
        </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // ── CTA ───────────────────────────────────────────────────────────────────
  if (seg.type === "cta") {
    const ctaEntrance = spring({ frame, fps, config: { damping: 12, stiffness: 140 } });
    const ctaOpacity = interpolate(ctaEntrance, [0, 1], [0, 1]);

    return (
      <AbsoluteFill>
        {bg}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          flexDirection: "column",
          gap: 32,
          padding: "60px 64px",
          opacity: exitOpacity,
        }}
      >
        <div
          style={{
            opacity: ctaOpacity,
            transform: `scale(${interpolate(ctaEntrance, [0, 1], [0.9, 1])})`,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontFamily: FONTS.MONO,
              fontSize: 28,
              color: accentColor,
              letterSpacing: "0.15em",
              textTransform: "uppercase",
              marginBottom: 24,
            }}
          >
            ▶ FOLLOW THIS CHANNEL
          </div>
          <WordByWordReveal
            text={seg.text}
            fontSize={FONT_SIZES.CTA}
            color={COLORS.TEXT_PRIMARY}
            accentColor={accentColor}
            staggerFrames={4}
            highlightWords={seg.highlightWords ?? []}
          />
        </div>
      </AbsoluteFill>
      </AbsoluteFill>
    );
  }

  // ── FACT (default) ────────────────────────────────────────────────────────
  return (
    <AbsoluteFill>
      {bg}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: "60px 64px",
          opacity: exitOpacity,
          transform: `translateY(${exitY}px)`,
        }}
      >
        <div style={{ textAlign: "center" }}>
          <WordByWordReveal
            text={seg.text}
            fontSize={FONT_SIZES.FACT}
            color={COLORS.TEXT_PRIMARY}
            accentColor={accentColor}
            staggerFrames={4}
            highlightWords={seg.highlightWords ?? []}
          />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ─────────────────────────── Main Composition ──────────────────────────────

export const ShortVideo: React.FC<ShortVideoProps> = ({
  videoId,
  categoryLabel,
  colorTheme,
  segments,
  audioFile,
  backgroundVideoUrl,
}) => {
  const accentColor = getAccentColor(colorTheme as ColorTheme);
  const bgGradient = BG_GRADIENTS[colorTheme as ColorTheme] ?? BG_GRADIENTS.shocking;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_PRIMARY }}>

      {/* ── Layer 1: Global fallback background (hidden by segment backgrounds) */}
      <AbsoluteFill style={{ background: bgGradient }} />

      {/* ── Layer 2: Ambient particles ───────────────────────────────────── */}
      <Particles count={12} accentColor={accentColor} width={1080} height={1920} />

      {/* ── Layer 3: Top progress bar ────────────────────────────────────── */}
      <TopProgressBar accentColor={accentColor} />

      {/* ── Layer 4: Category badge ──────────────────────────────────────── */}
      <CategoryBadge label={categoryLabel} accentColor={accentColor} />

      {/* ── Layer 5: Content segments (each has own background) ─────────── */}
      {segments.map((seg, i) => (
        <Sequence
          key={i}
          from={seg.startFrame}
          durationInFrames={seg.endFrame - seg.startFrame}
        >
          <SegmentView seg={seg} accentColor={accentColor} globalBgGradient={bgGradient} />
        </Sequence>
      ))}

      {/* ── Layer 6: Watermark ───────────────────────────────────────────── */}
      <Watermark text="FactForge" />

      {/* ── Audio ────────────────────────────────────────────────────────── */}
      {audioFile && <Audio src={audioFile} />}
    </AbsoluteFill>
  );
};
