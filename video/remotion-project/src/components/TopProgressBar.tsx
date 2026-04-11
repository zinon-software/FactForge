import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

interface TopProgressBarProps {
  accentColor: string;
}

export const TopProgressBar: React.FC<TopProgressBarProps> = ({ accentColor }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const pct = (frame / durationInFrames) * 100;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        height: 6,
        backgroundColor: "rgba(255,255,255,0.12)",
        zIndex: 100,
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${pct}%`,
          backgroundColor: accentColor,
          boxShadow: `0 0 12px ${accentColor}`,
        }}
      />
    </div>
  );
};
