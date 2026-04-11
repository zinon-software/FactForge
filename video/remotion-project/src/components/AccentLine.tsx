import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

interface AccentLineProps {
  accentColor: string;
  maxWidth?: number;
  height?: number;
  delayFrames?: number;
}

// Animated line that draws itself left→right
export const AccentLine: React.FC<AccentLineProps> = ({
  accentColor,
  maxWidth = 200,
  height = 3,
  delayFrames = 10,
}) => {
  const frame = useCurrentFrame();
  const width = interpolate(frame - delayFrames, [0, 25], [0, maxWidth], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: accentColor,
        borderRadius: height,
        boxShadow: `0 0 10px ${accentColor}`,
        marginTop: 16,
      }}
    />
  );
};

interface CategoryBadgeProps {
  label: string;
  accentColor: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ label, accentColor }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 48,
        left: 48,
        opacity,
        display: "flex",
        alignItems: "center",
        gap: 8,
        backgroundColor: `${accentColor}22`,
        border: `1px solid ${accentColor}88`,
        borderRadius: 100,
        paddingLeft: 16,
        paddingRight: 16,
        paddingTop: 8,
        paddingBottom: 8,
        zIndex: 50,
      }}
    >
      <span
        style={{
          fontFamily: "'Space Mono', monospace",
          fontSize: 22,
          color: accentColor,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          fontWeight: 700,
        }}
      >
        {label}
      </span>
    </div>
  );
};

interface WatermarkProps {
  text?: string;
}

export const Watermark: React.FC<WatermarkProps> = ({ text = "FactForge" }) => (
  <div
    style={{
      position: "absolute",
      bottom: 48,
      right: 48,
      fontFamily: "'Space Mono', monospace",
      fontSize: 24,
      color: "rgba(255,255,255,0.30)",
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      zIndex: 50,
    }}
  >
    {text}
  </div>
);
