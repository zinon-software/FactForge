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
  staggerFrames?: number;  // frames between each word
  highlightWords?: string[]; // words to color in accentColor
}

export const WordByWordReveal: React.FC<WordByWordRevealProps> = ({
  text,
  fontSize = 64,
  color = COLORS.TEXT_PRIMARY,
  accentColor = COLORS.ACCENT_SHOCK,
  bold = true,
  textAlign = "center",
  staggerFrames = 4,
  highlightWords = [],
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const words = text.split(" ");

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: textAlign === "center" ? "center" : textAlign === "left" ? "flex-start" : "flex-end",
        alignItems: "baseline",
        gap: "0.25em",
        lineHeight: 1.25,
      }}
    >
      {words.map((word, i) => {
        const wordFrame = frame - i * staggerFrames;
        const progress = spring({
          frame: wordFrame,
          fps,
          config: { damping: 14, stiffness: 220, mass: 0.4 },
        });

        const opacity = interpolate(wordFrame, [0, 8], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

        const translateY = interpolate(progress, [0, 1], [28, 0]);
        const scaleX = interpolate(progress, [0, 1], [0.85, 1]);

        const isHighlighted =
          highlightWords.some((hw) =>
            word.toLowerCase().replace(/[^a-z0-9]/g, "").includes(hw.toLowerCase())
          );

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              opacity,
              transform: `translateY(${translateY}px) scaleX(${scaleX})`,
              fontSize,
              fontFamily: FONTS.DISPLAY,
              fontWeight: bold ? 900 : 600,
              color: isHighlighted ? accentColor : color,
              textTransform: "uppercase",
              letterSpacing: "0.02em",
              textShadow: isHighlighted
                ? `0 0 30px ${accentColor}88, 3px 3px 6px rgba(0,0,0,0.9)`
                : "3px 3px 8px rgba(0,0,0,0.9)",
              whiteSpace: "nowrap",
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
