import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../constants/typography";
import { COLORS } from "../constants/colors";

interface WordByWordRevealProps {
  text: string;
  fontSize?: number;
  color?: string;
  accentColor?: string;
  bold?: boolean;
  textAlign?: "center" | "left" | "right";
  staggerFrames?: number;
  highlightWords?: string[];
}

export const WordByWordReveal: React.FC<WordByWordRevealProps> = ({
  text,
  fontSize = 82,
  color = COLORS.TEXT_PRIMARY,
  accentColor = COLORS.ACCENT_SHOCK,
  bold = true,
  textAlign = "center",
  staggerFrames = 3,
  highlightWords = [],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Split into lines first (respect \n), then words within each line
  const lines = text.split("\n");

  let wordIndex = 0;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: textAlign === "center" ? "center" : textAlign === "left" ? "flex-start" : "flex-end",
        gap: "0.18em",
        textAlign,
      }}
    >
      {lines.map((line, lineIdx) => {
        const words = line.split(" ").filter(Boolean);
        const lineStartWord = wordIndex;
        wordIndex += words.length;

        return (
          <div
            key={lineIdx}
            style={{
              display: "flex",
              flexWrap: "wrap",
              justifyContent: textAlign === "center" ? "center" : "flex-start",
              alignItems: "baseline",
              gap: "0.22em",
              lineHeight: 1.15,
            }}
          >
            {words.map((word, wIdx) => {
              const globalIdx = lineStartWord + wIdx;
              const wordFrame = frame - globalIdx * staggerFrames;

              const progress = spring({
                frame: wordFrame,
                fps,
                config: { damping: 12, stiffness: 260, mass: 0.35 },
              });

              const opacity = interpolate(wordFrame, [0, 6], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });

              const translateY = interpolate(progress, [0, 1], [40, 0]);
              const scale = interpolate(progress, [0, 0.6, 1], [0.7, 1.08, 1]);

              const cleanWord = word.toLowerCase().replace(/[^a-z0-9%$]/g, "");
              const isHighlighted = highlightWords.some((hw) => {
                const cleanHw = hw.toLowerCase().replace(/[^a-z0-9%$]/g, "");
                return cleanWord.includes(cleanHw) || cleanHw.includes(cleanWord);
              });

              return (
                <span
                  key={wIdx}
                  style={{
                    display: "inline-block",
                    opacity,
                    transform: `translateY(${translateY}px) scale(${scale})`,
                    fontSize,
                    fontFamily: FONTS.DISPLAY,
                    fontWeight: 900,
                    color: isHighlighted ? accentColor : color,
                    textTransform: "uppercase",
                    letterSpacing: "0.03em",
                    textShadow: isHighlighted
                      ? `0 0 40px ${accentColor}cc, 0 0 80px ${accentColor}55, 3px 3px 8px rgba(0,0,0,0.95)`
                      : "3px 3px 10px rgba(0,0,0,0.95), 0 0 20px rgba(0,0,0,0.6)",
                    whiteSpace: "nowrap",
                    // Subtle stroke for readability over any background
                    WebkitTextStroke: isHighlighted ? "0px" : "0.5px rgba(0,0,0,0.3)",
                  }}
                >
                  {word}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};
