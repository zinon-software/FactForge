import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONTS } from "../constants/typography";
import { COLORS } from "../constants/colors";

interface CountUpNumberProps {
  value: number;
  prefix?: string;
  suffix?: string;
  label?: string;
  accentColor?: string;
  fontSize?: number;
  countDurationSeconds?: number;
}

export const CountUpNumber: React.FC<CountUpNumberProps> = ({
  value,
  prefix = "",
  suffix = "",
  label = "",
  accentColor = COLORS.ACCENT_SHOCK,
  fontSize = 160,
  countDurationSeconds = 1.0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const countFrames = countDurationSeconds * fps;

  // Ease-out cubic
  const rawT = Math.min(frame / countFrames, 1);
  const t = 1 - Math.pow(1 - rawT, 3);
  const current = Math.round(value * t);

  // Entrance fade
  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Glow pulse once count finishes
  const doneFrame = countFrames;
  const glowProgress = interpolate(frame - doneFrame, [0, 20], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const glowSize = interpolate(glowProgress, [0, 0.5, 1], [10, 50, 20]);

  return (
    <div style={{ textAlign: "center", opacity }}>
      <div
        style={{
          fontSize,
          fontFamily: FONTS.DISPLAY,
          color: accentColor,
          letterSpacing: "0.01em",
          lineHeight: 1,
          textShadow: `0 0 ${glowSize}px ${accentColor}99, 4px 4px 12px rgba(0,0,0,0.9)`,
        }}
      >
        {prefix}{current.toLocaleString()}{suffix}
      </div>
      {label && (
        <div
          style={{
            fontSize: 36,
            fontFamily: FONTS.BODY,
            color: COLORS.TEXT_SECONDARY,
            fontWeight: 600,
            marginTop: 16,
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            opacity: glowProgress,
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};
