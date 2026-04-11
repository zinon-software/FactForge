import React from "react";
import { useCurrentFrame } from "remotion";

interface ParticlesProps {
  count?: number;
  accentColor: string;
  width?: number;
  height?: number;
}

// Deterministic pseudo-random so particles are stable across frames
function pseudoRandom(seed: number): number {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}

export const Particles: React.FC<ParticlesProps> = ({
  count = 10,
  accentColor,
  width = 1080,
  height = 1920,
}) => {
  const frame = useCurrentFrame();

  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "hidden" }}>
      {Array.from({ length: count }, (_, i) => {
        const startX = pseudoRandom(i * 7) * width;
        const startY = pseudoRandom(i * 13) * height;
        const speed = 0.4 + pseudoRandom(i * 3) * 0.6;  // 0.4–1.0 px/frame
        const size = 2 + pseudoRandom(i * 11) * 3;       // 2–5 px
        const opacity = 0.08 + pseudoRandom(i * 5) * 0.10; // 0.08–0.18

        const y = (startY - frame * speed * 60) % height;
        const adjustedY = y < 0 ? y + height : y;

        // Gentle horizontal drift
        const drift = Math.sin(frame * 0.015 + i * 1.2) * 12;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: startX + drift,
              top: adjustedY,
              width: size,
              height: size,
              borderRadius: "50%",
              backgroundColor: accentColor,
              opacity,
              boxShadow: `0 0 ${size * 2}px ${accentColor}`,
            }}
          />
        );
      })}
    </div>
  );
};
