/**
 * KaraokeCaption — TikTok-style word-by-word captions
 *
 * Shows 1 line at a time at the bottom of the screen.
 * Each word pops in exactly when spoken (synced to audio timestamps).
 * Current word: accent color + scale punch + glow.
 * Past words in line: white, slightly dimmer.
 * On line change: old line fades up, new line slides in from below.
 */

import React from "react";
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { FONTS } from "../constants/typography";

export interface WordTimestamp {
  word: string;
  start_ms: number;
  end_ms: number;
}

interface KaraokeCaptionProps {
  words: WordTimestamp[];
  accentColor: string;
  fontSize?: number;
  wordsPerLine?: number;
  bottomOffset?: number;
  pillPadding?: string;
  style?: "pill" | "outline" | "bold-pop";  // caption style variant
}

// Group words into lines of N words
function groupIntoLines(words: WordTimestamp[], n: number): WordTimestamp[][] {
  const lines: WordTimestamp[][] = [];
  for (let i = 0; i < words.length; i += n) {
    lines.push(words.slice(i, i + n));
  }
  return lines;
}

export const KaraokeCaption: React.FC<KaraokeCaptionProps> = ({
  words,
  accentColor,
  fontSize = 72,
  wordsPerLine = 4,
  bottomOffset = 120,
  pillPadding = "22px 40px",
  style: captionStyle = "bold-pop",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;

  if (!words || words.length === 0) return null;

  const lines = groupIntoLines(words, wordsPerLine);

  // Find active line: the line whose last word has end_ms > currentMs
  // and whose first word has start_ms <= currentMs + small lookahead
  let activeLineIdx = 0;
  for (let i = 0; i < lines.length; i++) {
    const lineStart = lines[i][0].start_ms;
    const lineEnd = lines[i][lines[i].length - 1].end_ms;
    if (currentMs >= lineStart - 100 && currentMs <= lineEnd + 400) {
      activeLineIdx = i;
      break;
    }
    if (currentMs > lineEnd) {
      activeLineIdx = Math.min(i + 1, lines.length - 1);
    }
  }

  const activeLine = lines[activeLineIdx];
  if (!activeLine) return null;

  // Line entrance animation: slides up from bottom on line change
  const lineStartMs = activeLine[0].start_ms;
  const lineEntryFrame = Math.max(0, frame - Math.round((lineStartMs / 1000) * fps));
  const lineEntrance = spring({
    frame: lineEntryFrame,
    fps,
    config: { damping: 14, stiffness: 280, mass: 0.3 },
  });
  const lineSlideY = interpolate(lineEntrance, [0, 1], [40, 0]);
  const lineOpacity = interpolate(lineEntryFrame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottomOffset,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "0 40px",
        transform: `translateY(${lineSlideY}px)`,
        opacity: lineOpacity,
        zIndex: 100,
      }}
    >
      {/* Caption container — dark pill with blur */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          gap: "0.18em",
          backgroundColor: "rgba(0,0,0,0.72)",
          borderRadius: 16,
          padding: pillPadding,
          backdropFilter: "blur(8px)",
          border: `2px solid rgba(255,255,255,0.08)`,
          maxWidth: "96%",
        }}
      >
        {activeLine.map((w, i) => {
          const isSpoken = currentMs >= w.start_ms;
          const isActive = currentMs >= w.start_ms && currentMs < w.end_ms + 150;
          const isFuture = currentMs < w.start_ms;

          const wordEntryFrame = Math.max(0, frame - Math.round((w.start_ms / 1000) * fps));
          const wordSpring = spring({
            frame: isSpoken ? wordEntryFrame : 0,
            fps,
            config: { damping: 8, stiffness: 420, mass: 0.2 },
          });

          const wordScale = isSpoken
            ? interpolate(wordSpring, [0, 0.45, 1], [0.7, 1.18, 1.0])
            : 0.9;

          const wordOpacity = isFuture ? 0.3 : isActive ? 1 : 0.7;

          // Active: accent color + strong glow
          // Spoken (past): white
          // Future: dim white
          const wordColor = isActive ? accentColor : "#FFFFFF";

          const textShadow = isActive
            ? `0 0 20px ${accentColor}ee, 0 0 40px ${accentColor}88, 0 2px 8px rgba(0,0,0,1)`
            : "0 2px 8px rgba(0,0,0,0.95), 0 0 2px rgba(0,0,0,1)";

          const bounceY = isActive
            ? interpolate(wordSpring, [0, 0.35, 1], [8, -5, 0])
            : 0;

          // Bold pop: active word gets slightly larger font
          const activeSize = isActive ? fontSize * 1.06 : fontSize;

          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                fontSize: activeSize,
                fontFamily: FONTS.DISPLAY,
                fontWeight: 900,
                color: wordColor,
                textTransform: "uppercase",
                letterSpacing: "0.02em",
                opacity: wordOpacity,
                transform: `scale(${wordScale}) translateY(${bounceY}px)`,
                textShadow,
                whiteSpace: "nowrap",
                lineHeight: 1,
                // Active word: accent background highlight chip
                ...(isActive ? {
                  backgroundColor: `${accentColor}22`,
                  borderRadius: 6,
                  padding: "2px 6px",
                  margin: "0 -2px",
                } : {}),
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
