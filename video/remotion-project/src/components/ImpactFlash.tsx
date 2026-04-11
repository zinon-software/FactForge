import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

interface ImpactFlashProps {
  accentColor: string;
  flashDurationFrames?: number;
}

// Full-screen accent flash for Level 3 impact moments
export const ImpactFlash: React.FC<ImpactFlashProps> = ({
  accentColor,
  flashDurationFrames = 8,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 2, flashDurationFrames], [0, 0.35, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (opacity <= 0) return null;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: accentColor,
        opacity,
        pointerEvents: "none",
      }}
    />
  );
};

interface ScalePunchProps {
  children: React.ReactNode;
  peakScale?: number;
}

// Scale punch: zooms in from big → settles at 1
export const ScalePunch: React.FC<ScalePunchProps> = ({ children, peakScale = 1.12 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame,
    fps,
    config: { damping: 9, stiffness: 380, mass: 0.5 },
  });

  const scale = interpolate(progress, [0, 1], [peakScale, 1]);

  return (
    <div style={{ transform: `scale(${scale})`, display: "contents" }}>
      {children}
    </div>
  );
};
