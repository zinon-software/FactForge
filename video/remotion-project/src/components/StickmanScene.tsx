/**
 * StickmanScene.tsx
 * Animated stickman characters for FactForge videos
 * Used in: explainer segments, concept illustrations, comparisons, cause-effect scenes
 *
 * Usage in DocumentaryVideo / ShortVideo:
 *   <StickmanScene type="walk" accentColor="#d4af37" scale={1.2} />
 *   <StickmanScene type="think" label="Al-Khwarizmi" accentColor="#d4af37" />
 *
 * Available types:
 *   walk | run | think | celebrate | fall | point | read | write | compare
 */

import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// ─── Types ───────────────────────────────────────────────────────────────────

export type StickmanType =
  | "walk"
  | "run"
  | "think"
  | "celebrate"
  | "fall"
  | "point_right"
  | "point_up"
  | "read"
  | "write"
  | "shocked"
  | "idle";

interface StickmanProps {
  type?: StickmanType;
  accentColor?: string;
  scale?: number;
  label?: string;
  labelColor?: string;
  x?: number;        // horizontal position 0–100 (percentage)
  y?: number;        // vertical position 0–100 (percentage)
  flip?: boolean;    // mirror horizontally
  delayFrames?: number;
}

// ─── SVG Helpers ─────────────────────────────────────────────────────────────

const HEAD_R = 18;
const STROKE = 5;
const BODY_LEN = 50;
const LEG_LEN = 42;
const ARM_LEN = 36;

interface StickFigureProps {
  color: string;
  // Joint angles in degrees
  leftHip?: number;
  rightHip?: number;
  leftKnee?: number;
  rightKnee?: number;
  leftShoulder?: number;
  rightShoulder?: number;
  leftElbow?: number;
  rightElbow?: number;
  lean?: number;       // body lean angle
  headTilt?: number;
}

const deg = (d: number) => (d * Math.PI) / 180;

const StickFigure: React.FC<StickFigureProps> = ({
  color,
  leftHip = -20,
  rightHip = 20,
  leftKnee = 0,
  rightKnee = 0,
  leftShoulder = -30,
  rightShoulder = 30,
  leftElbow = 0,
  rightElbow = 0,
  lean = 0,
  headTilt = 0,
}) => {
  // Origin at hip center
  const cx = 0;
  const cy = 0;

  // Body top
  const bx = cx + Math.sin(deg(lean)) * BODY_LEN;
  const by = cy - Math.cos(deg(lean)) * BODY_LEN;

  // Head
  const hx = bx + Math.sin(deg(lean + headTilt)) * (HEAD_R + 2);
  const hy = by - Math.cos(deg(lean + headTilt)) * (HEAD_R + 2);

  // Left leg: hip → knee → foot
  const lhx = cx + Math.sin(deg(leftHip)) * (LEG_LEN * 0.55);
  const lhy = cy + Math.cos(deg(leftHip)) * (LEG_LEN * 0.55);
  const lfx = lhx + Math.sin(deg(leftHip + leftKnee)) * (LEG_LEN * 0.55);
  const lfy = lhy + Math.cos(deg(leftHip + leftKnee)) * (LEG_LEN * 0.55);

  // Right leg
  const rhx = cx + Math.sin(deg(rightHip)) * (LEG_LEN * 0.55);
  const rhy = cy + Math.cos(deg(rightHip)) * (LEG_LEN * 0.55);
  const rfx = rhx + Math.sin(deg(rightHip + rightKnee)) * (LEG_LEN * 0.55);
  const rfy = rhy + Math.cos(deg(rightHip + rightKnee)) * (LEG_LEN * 0.55);

  // Left arm: shoulder → elbow → hand
  const lax = bx + Math.sin(deg(lean + leftShoulder)) * (ARM_LEN * 0.5);
  const lay = by - Math.cos(deg(lean + leftShoulder)) * (ARM_LEN * 0.5);
  const lhndx = lax + Math.sin(deg(lean + leftShoulder + leftElbow)) * (ARM_LEN * 0.5);
  const lhndy = lay - Math.cos(deg(lean + leftShoulder + leftElbow)) * (ARM_LEN * 0.5);

  // Right arm
  const rax = bx + Math.sin(deg(lean + rightShoulder)) * (ARM_LEN * 0.5);
  const ray = by - Math.cos(deg(lean + rightShoulder)) * (ARM_LEN * 0.5);
  const rhndx = rax + Math.sin(deg(lean + rightShoulder + rightElbow)) * (ARM_LEN * 0.5);
  const rhndy = ray - Math.cos(deg(lean + rightShoulder + rightElbow)) * (ARM_LEN * 0.5);

  const s = { stroke: color, strokeWidth: STROKE, strokeLinecap: "round" as const, fill: "none" };

  return (
    <g>
      {/* Head */}
      <circle cx={hx} cy={hy} r={HEAD_R} fill="none" stroke={color} strokeWidth={STROKE} />
      {/* Eyes */}
      <circle cx={hx - 5} cy={hy - 3} r={2.5} fill={color} />
      <circle cx={hx + 5} cy={hy - 3} r={2.5} fill={color} />
      {/* Body */}
      <line x1={bx} y1={by} x2={cx} y2={cy} {...s} />
      {/* Left leg */}
      <line x1={cx} y1={cy} x2={lhx} y2={lhy} {...s} />
      <line x1={lhx} y1={lhy} x2={lfx} y2={lfy} {...s} />
      {/* Right leg */}
      <line x1={cx} y1={cy} x2={rhx} y2={rhy} {...s} />
      <line x1={rhx} y1={rhy} x2={rfx} y2={rfy} {...s} />
      {/* Left arm */}
      <line x1={bx} y1={by} x2={lax} y2={lay} {...s} />
      <line x1={lax} y1={lay} x2={lhndx} y2={lhndy} {...s} />
      {/* Right arm */}
      <line x1={bx} y1={by} x2={rax} y2={ray} {...s} />
      <line x1={rax} y1={ray} x2={rhndx} y2={rhndy} {...s} />
    </g>
  );
};

// ─── Animation States ────────────────────────────────────────────────────────

function getWalkPose(phase: number): StickFigureProps {
  const s = Math.sin(phase * Math.PI * 2);
  return {
    leftHip: s * 35,
    rightHip: -s * 35,
    leftKnee: Math.max(0, s * 20),
    rightKnee: Math.max(0, -s * 20),
    leftShoulder: -s * 25,
    rightShoulder: s * 25,
    lean: s * 3,
  };
}

function getRunPose(phase: number): StickFigureProps {
  const s = Math.sin(phase * Math.PI * 2);
  return {
    leftHip: s * 55,
    rightHip: -s * 55,
    leftKnee: Math.max(0, s * 35),
    rightKnee: Math.max(0, -s * 35),
    leftShoulder: -s * 45,
    rightShoulder: s * 45,
    lean: 12 + s * 4,
  };
}

function getThinkPose(phase: number): StickFigureProps {
  const bob = Math.sin(phase * Math.PI * 2) * 3;
  return {
    leftHip: -5,
    rightHip: 5,
    leftShoulder: -20,
    rightShoulder: 70,
    rightElbow: -50,
    headTilt: 10 + Math.sin(phase * Math.PI * 4) * 5,
    lean: bob * 0.5,
  };
}

function getCelebratePose(phase: number): StickFigureProps {
  const s = Math.sin(phase * Math.PI * 4);
  return {
    leftHip: -10 + s * 5,
    rightHip: 10 - s * 5,
    leftShoulder: -120 + s * 15,
    rightShoulder: 120 - s * 15,
    leftElbow: s * 20,
    rightElbow: -s * 20,
    lean: s * 5,
  };
}

function getFallPose(phase: number): StickFigureProps {
  const p = Math.min(1, phase * 3);
  return {
    lean: interpolate(p, [0, 1], [0, 80]),
    leftHip: interpolate(p, [0, 1], [-20, -60]),
    rightHip: interpolate(p, [0, 1], [20, 40]),
    leftShoulder: interpolate(p, [0, 1], [-30, -80]),
    rightShoulder: interpolate(p, [0, 1], [30, 60]),
    headTilt: interpolate(p, [0, 1], [0, 30]),
  };
}

function getPointRightPose(): StickFigureProps {
  return {
    leftHip: -5,
    rightHip: 5,
    leftShoulder: -20,
    rightShoulder: 90,
    rightElbow: -10,
    lean: 5,
  };
}

function getPointUpPose(phase: number): StickFigureProps {
  const bob = Math.sin(phase * Math.PI * 2) * 3;
  return {
    leftHip: -8,
    rightHip: 8,
    leftShoulder: -25,
    rightShoulder: -150,
    rightElbow: 15,
    lean: bob * 0.3,
    headTilt: -10,
  };
}

function getReadPose(phase: number): StickFigureProps {
  const bob = Math.sin(phase * Math.PI * 2) * 2;
  return {
    leftHip: -5,
    rightHip: 5,
    leftShoulder: 40,
    rightShoulder: 40,
    leftElbow: -30,
    rightElbow: -30,
    headTilt: 15 + bob,
    lean: 5,
  };
}

function getWritePose(phase: number): StickFigureProps {
  const s = Math.sin(phase * Math.PI * 6) * 5;
  return {
    leftHip: -5,
    rightHip: 5,
    leftShoulder: -20,
    rightShoulder: 60,
    rightElbow: -20 + s,
    headTilt: 20,
    lean: 8,
  };
}

function getShockedPose(phase: number): StickFigureProps {
  const jolt = phase < 0.1 ? interpolate(phase, [0, 0.1], [0, 1]) : 1;
  return {
    leftShoulder: interpolate(jolt, [0, 1], [-30, -120]),
    rightShoulder: interpolate(jolt, [0, 1], [30, 120]),
    leftElbow: interpolate(jolt, [0, 1], [0, 30]),
    rightElbow: interpolate(jolt, [0, 1], [0, -30]),
    leftHip: interpolate(jolt, [0, 1], -20, -35),
    rightHip: interpolate(jolt, [0, 1], 20, 35),
    headTilt: Math.sin(phase * Math.PI * 8) * 8,
    lean: Math.sin(phase * Math.PI * 4) * 4,
  };
}

// ─── Main Component ──────────────────────────────────────────────────────────

export const StickmanScene: React.FC<StickmanProps> = ({
  type = "idle",
  accentColor = "#ffffff",
  scale = 1,
  label,
  labelColor,
  x = 50,
  y = 70,
  flip = false,
  delayFrames = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const relFrame = Math.max(0, frame - delayFrames);
  const phase = (relFrame % fps) / fps; // 0→1 per second, loops

  // Entrance spring
  const ent = spring({
    frame: relFrame,
    fps,
    config: { damping: 12, stiffness: 150 },
  });

  const entScale = interpolate(ent, [0, 1], [0, 1]);
  const entOp = interpolate(ent, [0, 1], [0, 1]);

  // Walk cycle: x position drifts if walking/running
  let poseProps: StickFigureProps = {};
  let walkOffset = 0;

  switch (type) {
    case "walk":
      poseProps = getWalkPose(phase);
      walkOffset = (relFrame / fps) * 60; // 60px/sec
      break;
    case "run":
      poseProps = getRunPose(phase);
      walkOffset = (relFrame / fps) * 140;
      break;
    case "think":
      poseProps = getThinkPose(phase);
      break;
    case "celebrate":
      poseProps = getCelebratePose(phase);
      break;
    case "fall":
      poseProps = getFallPose(relFrame / (fps * 1.5));
      break;
    case "point_right":
      poseProps = getPointRightPose();
      break;
    case "point_up":
      poseProps = getPointUpPose(phase);
      break;
    case "read":
      poseProps = getReadPose(phase);
      break;
    case "write":
      poseProps = getWritePose(phase);
      break;
    case "shocked":
      poseProps = getShockedPose(relFrame / fps);
      break;
    default:
      poseProps = { leftHip: -8, rightHip: 8, leftShoulder: -25, rightShoulder: 25 };
  }

  // Think bubble for "think" type
  const thinkBubble =
    type === "think" ? (
      <>
        <circle cx={30} cy={-130} r={6} fill={accentColor} opacity={0.5} />
        <circle cx={44} cy={-148} r={9} fill={accentColor} opacity={0.65} />
        <circle cx={62} cy={-160} r={14} fill={accentColor} opacity={0.8} />
        <text
          x={62}
          y={-155}
          textAnchor="middle"
          fontSize={16}
          fontWeight="bold"
          fill="#000"
        >
          ?
        </text>
      </>
    ) : null;

  // Shadow
  const shadow = (
    <ellipse
      cx={walkOffset}
      cy={8}
      rx={28 * scale}
      ry={7 * scale}
      fill="rgba(0,0,0,0.3)"
    />
  );

  const figureSize = 160 * scale;
  const viewBox = "-80 -200 160 230";

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        transform: `translate(-50%, -100%) scale(${entScale}) ${flip ? "scaleX(-1)" : ""}`,
        opacity: entOp,
        filter: `drop-shadow(0 4px 12px ${accentColor}44)`,
      }}
    >
      <svg
        width={figureSize}
        height={figureSize * 1.4}
        viewBox={viewBox}
        style={{ overflow: "visible" }}
      >
        {shadow}
        <g transform={`translate(${walkOffset}, 0)`}>
          <StickFigure color={accentColor} {...poseProps} />
          {thinkBubble}
        </g>

        {/* Label */}
        {label && (
          <text
            x={walkOffset}
            y={24}
            textAnchor="middle"
            fontFamily="'Bebas Neue', sans-serif"
            fontSize={20}
            fill={labelColor ?? accentColor}
            style={{ textShadow: `0 0 8px ${accentColor}` }}
          >
            {label}
          </text>
        )}
      </svg>
    </div>
  );
};

// ─── Multi-character Scene ────────────────────────────────────────────────────

interface StickmanComparisonProps {
  leftType?: StickmanType;
  rightType?: StickmanType;
  leftLabel?: string;
  rightLabel?: string;
  accentLeft?: string;
  accentRight?: string;
  centerText?: string;
  centerColor?: string;
}

/**
 * Two stickmen side by side — great for "before/after" or "rich vs poor" comparisons
 */
export const StickmanComparison: React.FC<StickmanComparisonProps> = ({
  leftType = "idle",
  rightType = "idle",
  leftLabel,
  rightLabel,
  accentLeft = "#ffffff",
  accentRight = "#ffcc00",
  centerText = "vs",
  centerColor = "#ffffff",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ent = spring({ frame, fps, config: { damping: 10, stiffness: 120 } });

  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: 0 }}>
      <StickmanScene type={leftType} accentColor={accentLeft} label={leftLabel} x={30} y={75} />

      {/* VS badge */}
      <div style={{
        position: "absolute", left: "50%", top: "55%",
        transform: `translate(-50%, -50%) scale(${interpolate(ent, [0, 1], [0.5, 1])})`,
        fontFamily: "'Bebas Neue', sans-serif",
        fontSize: 64,
        color: centerColor,
        textShadow: `0 0 30px ${centerColor}`,
        opacity: interpolate(ent, [0, 1], [0, 1]),
        letterSpacing: "0.1em",
      }}>
        {centerText}
      </div>

      <StickmanScene type={rightType} accentColor={accentRight} label={rightLabel} x={70} y={75} flip />
    </div>
  );
};
