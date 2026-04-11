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

export const longVideoSchema = z.object({
  videoId: z.string(),
  title: z.string(),
  sections: z.array(z.object({
    heading: z.string(),
    text: z.string(),
    startFrame: z.number(),
    durationInFrames: z.number(),
  })),
  audioFile: z.string().nullable(),
  backgroundVideoUrl: z.string().nullable(),
  colorTheme: z.enum(["islamic", "wealth", "military", "science", "general", "ancient"]),
});

type LongVideoProps = z.infer<typeof longVideoSchema>;

const COLOR_THEMES = {
  islamic:  { bg: "#0a1628", accent: "#d4af37", text: "#ffffff", secondary: "#a09060" },
  wealth:   { bg: "#0d0d0d", accent: "#00e676", text: "#ffffff", secondary: "#007740" },
  military: { bg: "#1a0000", accent: "#ff3232", text: "#ffffff", secondary: "#802020" },
  science:  { bg: "#0d0021", accent: "#00e5ff", text: "#ffffff", secondary: "#007080" },
  general:  { bg: "#1a1a2e", accent: "#ff6b35", text: "#ffffff", secondary: "#804020" },
  ancient:  { bg: "#281400", accent: "#ffa500", text: "#ffffff", secondary: "#804000" },
};

const SectionSlide: React.FC<{
  heading: string;
  text: string;
  theme: (typeof COLOR_THEMES)["general"];
}> = ({ heading, text, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headingProgress = spring({ frame, fps, config: { damping: 15 } });
  const textOpacity = interpolate(frame, [20, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "80px 160px",
        backgroundColor: theme.bg,
      }}
    >
      {/* Section heading */}
      <div
        style={{
          transform: `translateX(${interpolate(headingProgress, [0, 1], [-100, 0])}px)`,
          marginBottom: 40,
        }}
      >
        <h2
          style={{
            fontSize: 80,
            fontFamily: "Impact, Arial Black, sans-serif",
            color: theme.accent,
            margin: 0,
            textTransform: "uppercase",
            letterSpacing: 2,
          }}
        >
          {heading}
        </h2>
        {/* Underline bar */}
        <div
          style={{
            height: 6,
            width: `${interpolate(headingProgress, [0, 1], [0, 300])}px`,
            backgroundColor: theme.accent,
            marginTop: 12,
          }}
        />
      </div>

      {/* Section text */}
      <p
        style={{
          fontSize: 52,
          fontFamily: "Arial, sans-serif",
          color: theme.text,
          lineHeight: 1.5,
          opacity: textOpacity,
          maxWidth: 1400,
          margin: 0,
        }}
      >
        {text}
      </p>
    </AbsoluteFill>
  );
};

export const LongVideo: React.FC<LongVideoProps> = ({
  videoId,
  title,
  sections,
  audioFile,
  backgroundVideoUrl,
  colorTheme,
}) => {
  const theme = COLOR_THEMES[colorTheme] || COLOR_THEMES.general;

  return (
    <AbsoluteFill style={{ backgroundColor: theme.bg }}>
      {/* Background */}
      {backgroundVideoUrl && (
        <AbsoluteFill style={{ opacity: 0.15 }}>
          <Video
            src={backgroundVideoUrl}
            style={{ width: "100%", height: "100%", objectFit: "cover", filter: "blur(20px)" }}
          />
        </AbsoluteFill>
      )}

      {/* Sections */}
      {sections.map((section, i) => (
        <Sequence key={i} from={section.startFrame} durationInFrames={section.durationInFrames}>
          <SectionSlide heading={section.heading} text={section.text} theme={theme} />
        </Sequence>
      ))}

      {/* Audio */}
      {audioFile && <Audio src={audioFile} />}

      {/* Persistent accent border */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 6,
          backgroundColor: theme.accent,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
