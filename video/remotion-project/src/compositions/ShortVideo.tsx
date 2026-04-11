import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Video,
  Sequence,
} from "remotion";
import { z } from "zod";

export const shortVideoSchema = z.object({
  videoId: z.string(),
  hook: z.string(),
  segments: z.array(z.object({
    text: z.string(),
    startFrame: z.number(),
    endFrame: z.number(),
  })),
  audioFile: z.string().nullable(),
  backgroundVideoUrl: z.string().nullable(),
  colorTheme: z.enum(["islamic", "wealth", "military", "science", "general", "ancient"]),
  format: z.string(),
});

type ShortVideoProps = z.infer<typeof shortVideoSchema>;

const COLOR_THEMES = {
  islamic:  { bg: "#0a1628", accent: "#d4af37", text: "#ffffff" },
  wealth:   { bg: "#0d0d0d", accent: "#00e676", text: "#ffffff" },
  military: { bg: "#1a0000", accent: "#ff3232", text: "#ffffff" },
  science:  { bg: "#0d0021", accent: "#00e5ff", text: "#ffffff" },
  general:  { bg: "#1a1a2e", accent: "#ff6b35", text: "#ffffff" },
  ancient:  { bg: "#281400", accent: "#ffa500", text: "#ffffff" },
};

const AnimatedText: React.FC<{
  text: string;
  startFrame: number;
  theme: typeof COLOR_THEMES["general"];
  isHook?: boolean;
}> = ({ text, startFrame, theme, isHook = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - startFrame,
    fps,
    config: { damping: 12, stiffness: 200, mass: 0.5 },
  });

  const opacity = interpolate(frame - startFrame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const translateY = interpolate(progress, [0, 1], [40, 0]);

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${translateY}px)`,
        padding: "0 60px",
        textAlign: "center",
      }}
    >
      <p
        style={{
          fontSize: isHook ? 72 : 56,
          fontFamily: "Impact, Arial Black, sans-serif",
          color: isHook ? theme.accent : theme.text,
          lineHeight: 1.25,
          textShadow: "4px 4px 8px rgba(0,0,0,0.8)",
          margin: 0,
          fontWeight: 900,
          textTransform: "uppercase",
        }}
      >
        {text}
      </p>
    </div>
  );
};

const ProgressBar: React.FC<{ theme: typeof COLOR_THEMES["general"] }> = ({ theme }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const progress = frame / durationInFrames;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        right: 0,
        height: 8,
        backgroundColor: "rgba(255,255,255,0.2)",
      }}
    >
      <div
        style={{
          height: "100%",
          width: `${progress * 100}%`,
          backgroundColor: theme.accent,
          transition: "width 0.1s linear",
        }}
      />
    </div>
  );
};

export const ShortVideo: React.FC<ShortVideoProps> = ({
  videoId,
  hook,
  segments,
  audioFile,
  backgroundVideoUrl,
  colorTheme,
  format,
}) => {
  const theme = COLOR_THEMES[colorTheme] || COLOR_THEMES.general;
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: theme.bg }}>
      {/* Background video (blurred) */}
      {backgroundVideoUrl && (
        <AbsoluteFill style={{ opacity: 0.3 }}>
          <Video
            src={backgroundVideoUrl}
            style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(8px)" }}
          />
        </AbsoluteFill>
      )}

      {/* Dark gradient overlay */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, ${theme.bg}cc 0%, ${theme.bg}88 50%, ${theme.bg}cc 100%)`,
        }}
      />

      {/* Accent top bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 8,
          backgroundColor: theme.accent,
        }}
      />

      {/* Content area — centered */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 40,
        }}
      >
        {/* Hook (always visible) */}
        <AnimatedText text={hook} startFrame={0} theme={theme} isHook />

        {/* Script segments — sequential reveal */}
        {segments.map((segment, i) => (
          <Sequence key={i} from={segment.startFrame} durationInFrames={segment.endFrame - segment.startFrame}>
            <AnimatedText text={segment.text} startFrame={0} theme={theme} />
          </Sequence>
        ))}
      </AbsoluteFill>

      {/* Progress bar */}
      <ProgressBar theme={theme} />

      {/* Audio */}
      {audioFile && <Audio src={audioFile} />}
    </AbsoluteFill>
  );
};
