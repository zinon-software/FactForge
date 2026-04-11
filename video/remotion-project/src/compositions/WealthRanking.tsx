import "@fontsource/bebas-neue";
import "@fontsource/dm-sans/700.css";
import "@fontsource/space-mono/700.css";

import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Sequence,
  Img,
} from "remotion";
import { z } from "zod";
import { COLORS, getAccentColor } from "../constants/colors";
import { FONTS } from "../constants/typography";

// ─────────────────────── Schema ────────────────────────────────────────────

export const wealthPersonSchema = z.object({
  id: z.string(),
  type: z.enum(["hook", "person_reveal", "impact", "reveal", "cta"]),
  rank: z.number().optional(),
  name: z.string().optional(),
  net_worth_billions: z.number().optional(),
  net_worth_display: z.string().optional(),
  image: z.string().optional(),
  text: z.string(),
  startFrame: z.number(),
  durationInFrames: z.number(),
});

export const wealthRankingSchema = z.object({
  videoId: z.string(),
  audioFile: z.string().nullable(),
  segments: z.array(wealthPersonSchema),
  totalDurationFrames: z.number(),
});

export type WealthRankingProps = z.infer<typeof wealthRankingSchema>;

// ─────────────────────── Bar Chart Component ───────────────────────────────

const MAX_WORTH = 839; // Musk = 100% bar width

const WealthBar: React.FC<{
  value: number;
  maxValue: number;
  color: string;
  frame: number;
  delay?: number;
}> = ({ value, maxValue, color, frame, delay = 0 }) => {
  const { width } = useVideoConfig();
  const BAR_MAX_WIDTH = width * 0.55;

  const progress = spring({
    frame: frame - delay,
    fps: 30,
    config: { damping: 20, stiffness: 60 },
  });

  const barWidth = interpolate(progress, [0, 1], [0, (value / maxValue) * BAR_MAX_WIDTH], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const r = parseInt(color.slice(1, 3), 16);
  const g = parseInt(color.slice(3, 5), 16);
  const b = parseInt(color.slice(5, 7), 16);

  return (
    <div
      style={{
        height: 28,
        width: barWidth,
        background: `linear-gradient(90deg, ${color} 0%, rgba(${r},${g},${b},0.6) 100%)`,
        borderRadius: 4,
        boxShadow: `0 0 20px ${color}60`,
        position: "relative",
      }}
    />
  );
};

// ─────────────────────── Count-Up Number ───────────────────────────────────

const CountUp: React.FC<{
  target: number;
  frame: number;
  prefix?: string;
  suffix?: string;
  color: string;
  fontSize?: number;
}> = ({ target, frame, prefix = "$", suffix = "B", color, fontSize = 100 }) => {
  const progress = interpolate(frame, [0, 60], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: (t) => 1 - Math.pow(1 - t, 3),
  });
  const current = Math.round(target * progress);
  const glowPulse = interpolate(Math.sin(frame * 0.2), [-1, 1], [15, 40]);
  const isLocked = frame >= 60;

  return (
    <div
      style={{
        fontFamily: FONTS.DISPLAY,
        fontSize,
        color,
        textShadow: isLocked ? `0 0 ${glowPulse}px ${color}` : "none",
        lineHeight: 1,
        letterSpacing: "0.02em",
      }}
    >
      {prefix}{current.toLocaleString()}{suffix}
    </div>
  );
};

// ─────────────────────── Person Slide ──────────────────────────────────────

const PersonSlide: React.FC<{
  seg: z.infer<typeof wealthPersonSchema>;
  accentColor: string;
}> = ({ seg, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const entrance = spring({ frame, fps, config: { damping: 18, stiffness: 120 } });
  const exitStart = durationInFrames - 15;
  const exitOpacity = interpolate(frame, [exitStart, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const rankColors: Record<number, string> = {
    1: "#F0B429", 2: "#E2E8F0", 3: "#CD7F32",
    4: "#48BB78", 5: "#4299E1", 6: "#9F7AEA",
    7: "#ED64A6", 8: "#667EEA", 9: "#38B2AC", 10: "#FC8181",
  };
  const color = rankColors[seg.rank ?? 10] ?? accentColor;

  const isReveal = seg.type === "reveal";
  const isBig = isReveal || (seg.rank ?? 99) <= 2;

  return (
    <AbsoluteFill
      style={{
        background: isReveal
          ? "radial-gradient(ellipse at 50% 50%, #1a0f00 0%, #0A0A0F 70%)"
          : "radial-gradient(ellipse at 30% 70%, #0A0A0F 0%, #0d0d1a 100%)",
        opacity: exitOpacity,
      }}
    >
      {/* Top rank badge */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 80,
          fontFamily: FONTS.MONO,
          fontSize: 22,
          color: color,
          letterSpacing: "0.2em",
          opacity: interpolate(entrance, [0, 1], [0, 1]),
          transform: `translateX(${interpolate(entrance, [0, 1], [-30, 0])}px)`,
          border: `1px solid ${color}50`,
          padding: "6px 16px",
          borderRadius: 4,
          backgroundColor: `${color}15`,
        }}
      >
        {seg.rank ? `#${seg.rank} RICHEST PERSON ON EARTH` : "THE GAP"}
      </div>

      {/* Main layout: left photo, right info */}
      <div
        style={{
          position: "absolute",
          top: 130,
          left: 0,
          right: 0,
          bottom: 0,
          display: "flex",
          flexDirection: "row",
          gap: 0,
        }}
      >
        {/* LEFT: Photo */}
        <div
          style={{
            width: isBig ? 480 : 380,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "40px 40px 40px 80px",
            transform: `translateX(${interpolate(entrance, [0, 1], [-60, 0])}px)`,
            opacity: interpolate(entrance, [0, 1], [0, 1]),
            flexShrink: 0,
          }}
        >
          {seg.image && (
            <div
              style={{
                width: isBig ? 360 : 290,
                height: isBig ? 360 : 290,
                borderRadius: "50%",
                overflow: "hidden",
                border: `4px solid ${color}`,
                boxShadow: `0 0 40px ${color}50`,
              }}
            >
              <Img
                src={staticFile(seg.image)}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </div>
          )}
        </div>

        {/* RIGHT: Name, worth, bar, description */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            paddingRight: 80,
            paddingTop: 20,
            gap: 20,
            transform: `translateX(${interpolate(entrance, [0, 1], [60, 0])}px)`,
            opacity: interpolate(entrance, [0, 1], [0, 1]),
          }}
        >
          {/* Name */}
          <div
            style={{
              fontFamily: FONTS.DISPLAY,
              fontSize: isBig ? 72 : 60,
              color: COLORS.TEXT_PRIMARY,
              lineHeight: 1,
              textTransform: "uppercase",
              letterSpacing: "0.03em",
            }}
          >
            {seg.name?.replace(" — #2", "")}
          </div>

          {/* Net worth count-up */}
          {seg.net_worth_billions && (
            <CountUp
              target={seg.net_worth_billions}
              frame={frame}
              color={color}
              fontSize={isBig ? 88 : 72}
              suffix=" Billion"
            />
          )}

          {/* Wealth bar */}
          {seg.net_worth_billions && (
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <WealthBar
                value={seg.net_worth_billions}
                maxValue={MAX_WORTH}
                color={color}
                frame={frame}
                delay={10}
              />
              <div
                style={{
                  fontFamily: FONTS.MONO,
                  fontSize: 18,
                  color: `${color}90`,
                  whiteSpace: "nowrap",
                }}
              >
                {Math.round((seg.net_worth_billions / MAX_WORTH) * 100)}% of #1
              </div>
            </div>
          )}

          {/* Description text — word by word */}
          <div
            style={{
              fontFamily: FONTS.BODY,
              fontSize: 26,
              color: COLORS.TEXT_SECONDARY,
              lineHeight: 1.6,
              maxWidth: 720,
              marginTop: 8,
              opacity: interpolate(frame, [20, 45], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
            }}
          >
            {/* Show 3 key fact lines only */}
            {seg.text
              .split("\n")
              .filter((l) => l.trim().length > 0)
              .slice(2, 5)
              .join("  ·  ")}
          </div>
        </div>
      </div>

      {/* Impact flash for reveal */}
      {isReveal && frame < 8 && (
        <AbsoluteFill
          style={{
            backgroundColor: color,
            opacity: interpolate(frame, [0, 8], [0.6, 0]),
          }}
        />
      )}
    </AbsoluteFill>
  );
};

// ─────────────────────── Hook Slide ────────────────────────────────────────

const HookSlide: React.FC<{ seg: z.infer<typeof wealthPersonSchema> }> = ({ seg }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const words = seg.text.split(/\s+/);
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(ellipse at 50% 50%, #1a1000 0%, #0A0A0F 70%)",
        justifyContent: "center",
        alignItems: "center",
        padding: "80px 120px",
        opacity: exitOpacity,
      }}
    >
      {/* Glitch flash */}
      {frame < 4 && (
        <AbsoluteFill
          style={{
            backgroundColor: COLORS.ACCENT_WEALTH,
            opacity: interpolate(frame, [0, 4], [0.5, 0]),
          }}
        />
      )}

      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontFamily: FONTS.DISPLAY,
            fontSize: 72,
            color: COLORS.TEXT_PRIMARY,
            lineHeight: 1.15,
            letterSpacing: "0.03em",
            textTransform: "uppercase",
          }}
        >
          {words.map((word, i) => {
            const sp = spring({
              frame: frame - i * 2,
              fps,
              config: { damping: 10, stiffness: 280 },
            });
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  marginRight: "0.28em",
                  opacity: interpolate(sp, [0, 1], [0, 1]),
                  transform: `translateY(${interpolate(sp, [0, 1], [-50, 0])}px)`,
                  color:
                    word.includes("ONE") || word.includes("150") || word.includes("trillion")
                      ? COLORS.ACCENT_WEALTH
                      : COLORS.TEXT_PRIMARY,
                }}
              >
                {word}
              </span>
            );
          })}
        </div>

        {/* Accent underline */}
        <div
          style={{
            height: 4,
            backgroundColor: COLORS.ACCENT_WEALTH,
            marginTop: 32,
            width: interpolate(frame, [30, 80], [0, 600], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
            marginLeft: "auto",
            marginRight: "auto",
            boxShadow: `0 0 20px ${COLORS.ACCENT_WEALTH}`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────── Impact Slide ──────────────────────────────────────

const ImpactSlide: React.FC<{ seg: z.infer<typeof wealthPersonSchema> }> = ({ seg }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const shakeX = frame < 8 ? Math.sin(frame * 3) * interpolate(frame, [0, 8], [12, 0]) : 0;
  const exitOpacity = interpolate(
    frame,
    [durationInFrames - 15, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(ellipse at 50% 50%, #1a0000 0%, #0A0A0F 70%)",
        justifyContent: "center",
        alignItems: "center",
        padding: "80px 120px",
        opacity: exitOpacity,
        transform: `translateX(${shakeX}px)`,
      }}
    >
      {frame < 6 && (
        <AbsoluteFill
          style={{
            backgroundColor: COLORS.ACCENT_POWER,
            opacity: interpolate(frame, [0, 6], [0.4, 0]),
          }}
        />
      )}

      <div style={{ textAlign: "center", maxWidth: 1400 }}>
        <div
          style={{
            fontFamily: FONTS.DISPLAY,
            fontSize: 60,
            color: COLORS.TEXT_PRIMARY,
            lineHeight: 1.3,
            letterSpacing: "0.02em",
            textTransform: "uppercase",
          }}
        >
          {seg.text.split("\n").map((line, i) => (
            <div
              key={i}
              style={{
                opacity: interpolate(frame, [i * 8, i * 8 + 20], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
                color: line.includes("five hundred") || line.includes("cliff") || line.includes("582")
                  ? COLORS.ACCENT_POWER
                  : COLORS.TEXT_PRIMARY,
              }}
            >
              {line}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────── CTA Slide ─────────────────────────────────────────

const CTASlide: React.FC<{ seg: z.infer<typeof wealthPersonSchema> }> = ({ seg }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entrance = spring({ frame, fps, config: { damping: 14, stiffness: 120 } });

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(ellipse at 50% 50%, #0f1a00 0%, #0A0A0F 70%)",
        justifyContent: "center",
        alignItems: "center",
        padding: "80px 120px",
        flexDirection: "column",
        gap: 40,
      }}
    >
      <div
        style={{
          fontFamily: FONTS.MONO,
          fontSize: 32,
          color: COLORS.ACCENT_WEALTH,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          opacity: interpolate(entrance, [0, 1], [0, 1]),
        }}
      >
        ▶ FOLLOW THIS CHANNEL
      </div>
      <div
        style={{
          fontFamily: FONTS.DISPLAY,
          fontSize: 52,
          color: COLORS.TEXT_PRIMARY,
          textAlign: "center",
          lineHeight: 1.3,
          maxWidth: 1200,
          textTransform: "uppercase",
          opacity: interpolate(entrance, [0, 1], [0, 1]),
          transform: `scale(${interpolate(entrance, [0, 1], [0.9, 1])})`,
        }}
      >
        {seg.text.split("\n").map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────── Main Composition ──────────────────────────────────

export const WealthRanking: React.FC<WealthRankingProps> = ({
  videoId,
  audioFile,
  segments,
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.BG_PRIMARY }}>
      {/* Channel watermark */}
      <div
        style={{
          position: "absolute",
          bottom: 30,
          right: 40,
          fontFamily: FONTS.MONO,
          fontSize: 22,
          color: "rgba(255,255,255,0.25)",
          letterSpacing: "0.1em",
          zIndex: 100,
        }}
      >
        FactForge
      </div>

      {/* Segments */}
      {segments.map((seg, i) => (
        <Sequence key={i} from={seg.startFrame} durationInFrames={seg.durationInFrames}>
          {seg.type === "hook" && <HookSlide seg={seg} />}
          {seg.type === "impact" && <ImpactSlide seg={seg} />}
          {seg.type === "cta" && <CTASlide seg={seg} />}
          {(seg.type === "person_reveal" || seg.type === "reveal") && (
            <PersonSlide seg={seg} accentColor={COLORS.ACCENT_WEALTH} />
          )}
        </Sequence>
      ))}

      {/* Audio */}
      {audioFile && <Audio src={staticFile(audioFile)} />}
    </AbsoluteFill>
  );
};
