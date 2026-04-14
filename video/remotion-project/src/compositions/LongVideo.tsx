import "@fontsource/bebas-neue";
import "@fontsource/dm-sans/700.css";

import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from "remotion";
import { z } from "zod";
import { KaraokeCaption, WordTimestamp } from "../components/KaraokeCaption";
import { FONTS } from "../constants/typography";

// ─── Schema ────────────────────────────────────────────────────────────────

const longSectionSchema = z.object({
  id: z.string(),
  type: z.enum(["hook", "explainer", "deep_dive", "global_comparison", "solution", "cta"]),
  title: z.string(),
  startFrame: z.number(),
  endFrame: z.number(),
  tts_script: z.string(),
  visual_notes: z.string().optional(),
  backgroundVideo: z.string().nullable().optional(),
});

const wordTimestampSchema = z.object({
  word: z.string(),
  start_ms: z.number(),
  end_ms: z.number(),
});

export const longVideoSchema = z.object({
  videoId: z.string(),
  title: z.string(),
  sections: z.array(longSectionSchema),
  audioFile: z.string().nullable(),
  backgroundVideoUrl: z.string().nullable(),
  colorTheme: z.enum(["islamic", "wealth", "military", "science", "general", "ancient"]),
  wordTimestamps: z.array(wordTimestampSchema).optional(),
  totalDurationFrames: z.number().optional(),
  fps: z.number().optional(),
});

type LongVideoProps = z.infer<typeof longVideoSchema>;

// ─── Themes ─────────────────────────────────────────────────────────────────

const THEMES = {
  islamic:  { bg: "#0a1628", accent: "#d4af37", text: "#ffffff", secondary: "#a09060", gradient: "radial-gradient(ellipse at 30% 70%, #0d1f40 0%, #0a1628 70%)" },
  wealth:   { bg: "#080808", accent: "#00e676", text: "#ffffff", secondary: "#007740", gradient: "radial-gradient(ellipse at 20% 80%, #001a08 0%, #080808 70%)" },
  military: { bg: "#1a0000", accent: "#ff3232", text: "#ffffff", secondary: "#802020", gradient: "radial-gradient(ellipse at 70% 30%, #2a0000 0%, #1a0000 70%)" },
  science:  { bg: "#0d0021", accent: "#00e5ff", text: "#ffffff", secondary: "#007080", gradient: "radial-gradient(ellipse at 50% 50%, #001a2a 0%, #0d0021 70%)" },
  general:  { bg: "#0f0f1a", accent: "#ff6b35", text: "#ffffff", secondary: "#804020", gradient: "radial-gradient(ellipse at 80% 20%, #1a0f08 0%, #0f0f1a 70%)" },
  ancient:  { bg: "#281400", accent: "#ffa500", text: "#ffffff", secondary: "#804000", gradient: "radial-gradient(ellipse at 40% 60%, #3a1e00 0%, #281400 70%)" },
};

// ─── Top Progress Bar ────────────────────────────────────────────────────────

const LongProgressBar: React.FC<{ accent: string; totalFrames: number }> = ({ accent, totalFrames }) => {
  const frame = useCurrentFrame();
  const progress = frame / totalFrames;
  return (
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 5, zIndex: 100, backgroundColor: "rgba(255,255,255,0.1)" }}>
      <div style={{ height: "100%", width: `${progress * 100}%`, backgroundColor: accent, boxShadow: `0 0 12px ${accent}` }} />
    </div>
  );
};

// ─── Chapter Label ───────────────────────────────────────────────────────────

const ChapterLabel: React.FC<{ num: number; title: string; accent: string }> = ({ num, title, accent }) => {
  const frame = useCurrentFrame();
  const entrance = spring({ frame, fps: 30, config: { damping: 14, stiffness: 180 } });
  const opacity = interpolate(entrance, [0, 1], [0, 1]);
  const x = interpolate(entrance, [0, 1], [-60, 0]);
  return (
    <div style={{ position: "absolute", top: 48, left: 80, opacity, transform: `translateX(${x}px)`, zIndex: 10 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{
          width: 48, height: 48, borderRadius: "50%",
          backgroundColor: accent, display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: FONTS.DISPLAY, fontSize: 22, color: "#000", fontWeight: 900,
        }}>{num}</div>
        <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 28, color: accent, letterSpacing: "0.12em", textTransform: "uppercase" }}>
          {title}
        </div>
      </div>
      <div style={{ height: 3, backgroundColor: accent, marginTop: 10, width: "100%", boxShadow: `0 0 8px ${accent}` }} />
    </div>
  );
};

// ─── Animated Stat Card ──────────────────────────────────────────────────────

const StatCard: React.FC<{ value: string; label: string; accent: string; delayFrames?: number }> = ({ value, label, accent, delayFrames = 0 }) => {
  const frame = useCurrentFrame();
  const ent = spring({ frame: Math.max(0, frame - delayFrames), fps: 30, config: { damping: 12, stiffness: 160 } });
  return (
    <div style={{
      opacity: interpolate(ent, [0, 1], [0, 1]),
      transform: `scale(${interpolate(ent, [0, 1], [0.85, 1])}) translateY(${interpolate(ent, [0, 1], [20, 0])}px)`,
      backgroundColor: "rgba(255,255,255,0.05)",
      border: `2px solid ${accent}44`,
      borderRadius: 16,
      padding: "32px 48px",
      textAlign: "center",
      backdropFilter: "blur(8px)",
      boxShadow: `0 0 24px ${accent}22`,
    }}>
      <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 72, color: accent, lineHeight: 1, textShadow: `0 0 20px ${accent}88` }}>{value}</div>
      <div style={{ fontFamily: FONTS.BODY || "DM Sans, sans-serif", fontSize: 28, color: "#cccccc", marginTop: 12, maxWidth: 320 }}>{label}</div>
    </div>
  );
};

// ─── Section Types ───────────────────────────────────────────────────────────

const HookSection: React.FC<{ sec: z.infer<typeof longSectionSchema>; theme: (typeof THEMES)["general"]; sectionIndex: number }> = ({ sec, theme, sectionIndex }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = sec.endFrame - sec.startFrame;

  const titleEnt = spring({ frame, fps, config: { damping: 10, stiffness: 140 } });
  const bgScale = interpolate(frame, [0, dur], [1.0, 1.08], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exitOp = interpolate(frame, [dur - 15, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      {sec.backgroundVideo ? (
        <AbsoluteFill style={{ transform: `scale(${bgScale})` }}>
          <Video src={staticFile(sec.backgroundVideo)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <AbsoluteFill style={{ background: "rgba(0,0,0,0.68)" }} />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ background: theme.gradient }} />
      )}
      <AbsoluteFill style={{ background: "linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 60%)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "60px 120px", opacity: exitOp }}>
        <div style={{ textAlign: "center" }}>
          <div style={{
            fontFamily: FONTS.DISPLAY, fontSize: 96, color: theme.accent,
            letterSpacing: "0.08em", textTransform: "uppercase", lineHeight: 1.1,
            transform: `scale(${interpolate(titleEnt, [0, 1], [0.8, 1])})`,
            opacity: interpolate(titleEnt, [0, 1], [0, 1]),
            textShadow: `0 0 40px ${theme.accent}88, 0 4px 12px rgba(0,0,0,0.9)`,
            marginBottom: 32,
          }}>
            {sec.title}
          </div>
          <div style={{
            height: 5, backgroundColor: theme.accent,
            width: `${interpolate(titleEnt, [0, 1], [0, 600])}px`,
            margin: "0 auto",
            boxShadow: `0 0 16px ${theme.accent}`,
          }} />
        </div>
      </AbsoluteFill>
      <ChapterLabel num={sectionIndex + 1} title={sec.title} accent={theme.accent} />
    </AbsoluteFill>
  );
};

const ExplainerSection: React.FC<{ sec: z.infer<typeof longSectionSchema>; theme: (typeof THEMES)["general"]; sectionIndex: number }> = ({ sec, theme, sectionIndex }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = sec.endFrame - sec.startFrame;

  const ent = spring({ frame, fps, config: { damping: 13, stiffness: 160 } });
  const exitOp = interpolate(frame, [dur - 15, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bgScale = interpolate(frame, [0, dur], [1.0, 1.05], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      {sec.backgroundVideo ? (
        <AbsoluteFill style={{ transform: `scale(${bgScale})` }}>
          <Video src={staticFile(sec.backgroundVideo)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <AbsoluteFill style={{ background: "rgba(0,0,0,0.72)" }} />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ background: theme.gradient }} />
      )}
      <AbsoluteFill style={{ background: "linear-gradient(135deg, rgba(0,0,0,0.4) 0%, transparent 60%)", pointerEvents: "none" }} />

      <AbsoluteFill style={{ padding: "120px 100px", opacity: exitOp, flexDirection: "column", justifyContent: "center" }}>
        {/* Title */}
        <div style={{
          fontFamily: FONTS.DISPLAY, fontSize: 64, color: theme.accent,
          textTransform: "uppercase", letterSpacing: "0.06em",
          transform: `translateX(${interpolate(ent, [0, 1], [-80, 0])}px)`,
          opacity: interpolate(ent, [0, 1], [0, 1]),
          marginBottom: 32,
          textShadow: `0 0 20px ${theme.accent}66`,
        }}>
          {sec.title}
        </div>
        <div style={{ height: 4, backgroundColor: theme.accent, width: `${interpolate(ent, [0, 1], [0, 500])}px`, marginBottom: 40, boxShadow: `0 0 12px ${theme.accent}` }} />

        {/* Stats grid */}
        <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
          {sec.id === "section_1" && <>
            <StatCard value="45%" label="of all global wealth owned by the top 1%" accent={theme.accent} delayFrames={10} />
            <StatCard value="2.3%" label="owned by the bottom 50% of humanity" accent={theme.accent} delayFrames={20} />
            <StatCard value="20:1" label="wealth ratio — top 1% vs bottom 50%" accent={theme.accent} delayFrames={30} />
          </>}
          {sec.id === "section_2" && <>
            <StatCard value="×2" label="richest 10 men doubled wealth in 2 years" accent={theme.accent} delayFrames={10} />
            <StatCard value="30hrs" label="new billionaire created every 30 hours during COVID" accent={theme.accent} delayFrames={20} />
            <StatCard value="$1.5T" label="combined wealth of top 10 men by 2022" accent={theme.accent} delayFrames={30} />
          </>}
          {sec.id === "section_7" && <>
            <StatCard value="71%" label="of countries saw rising inequality since 1990" accent={theme.accent} delayFrames={10} />
            <StatCard value="30%" label="of China's wealth held by top 1%" accent={theme.accent} delayFrames={20} />
            <StatCard value="10x" label="Ambani earns in a month what avg Indian earns in a lifetime" accent={theme.accent} delayFrames={30} />
          </>}
        </div>
      </AbsoluteFill>
      <ChapterLabel num={sectionIndex + 1} title={sec.title} accent={theme.accent} />
    </AbsoluteFill>
  );
};

const DeepDiveSection: React.FC<{ sec: z.infer<typeof longSectionSchema>; theme: (typeof THEMES)["general"]; sectionIndex: number }> = ({ sec, theme, sectionIndex }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = sec.endFrame - sec.startFrame;

  const ent = spring({ frame, fps, config: { damping: 14, stiffness: 150 } });
  const exitOp = interpolate(frame, [dur - 15, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bgPan = interpolate(frame, [0, dur], [-3, 3], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Animated bar chart for tax section
  const isTax = sec.id === "section_4";
  const isCEO = sec.id === "section_5";
  const isInheritance = sec.id === "section_6";

  return (
    <AbsoluteFill>
      {sec.backgroundVideo ? (
        <AbsoluteFill style={{ transform: `scale(1.06) translateX(${bgPan}%)` }}>
          <Video src={staticFile(sec.backgroundVideo)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <AbsoluteFill style={{ background: "rgba(0,0,0,0.75)" }} />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ background: theme.gradient }} />
      )}

      <AbsoluteFill style={{ padding: "110px 100px", opacity: exitOp, flexDirection: "column", justifyContent: "center" }}>
        <div style={{
          fontFamily: FONTS.DISPLAY, fontSize: 58, color: theme.accent,
          textTransform: "uppercase", letterSpacing: "0.05em",
          opacity: interpolate(ent, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(ent, [0, 1], [-30, 0])}px)`,
          marginBottom: 24,
          textShadow: `0 0 24px ${theme.accent}55`,
        }}>
          {sec.title}
        </div>
        <div style={{ height: 4, backgroundColor: theme.accent, width: `${interpolate(ent, [0, 1], [0, 400])}px`, marginBottom: 48 }} />

        {/* Tax rate bar chart */}
        {isTax && (
          <div style={{ display: "flex", gap: 48, alignItems: "flex-end", height: 280 }}>
            {[
              { year: "1960", rate: 91, color: theme.accent },
              { year: "1980", rate: 70, color: theme.accent + "cc" },
              { year: "2000", rate: 39.6, color: theme.accent + "99" },
              { year: "2023", rate: 37, color: theme.accent + "77" },
              { year: "Billionaires\nEffective", rate: 8, color: "#ff4444" },
            ].map((d, i) => {
              const barH = spring({ frame: Math.max(0, frame - i * 8), fps, config: { damping: 14, stiffness: 120 } });
              return (
                <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
                  <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 32, color: d.color }}>{d.rate}%</div>
                  <div style={{
                    width: 90, height: `${interpolate(barH, [0, 1], [0, (d.rate / 100) * 220])}px`,
                    backgroundColor: d.color, borderRadius: "8px 8px 0 0",
                    boxShadow: `0 0 16px ${d.color}66`,
                  }} />
                  <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 22, color: "#aaa", textAlign: "center", whiteSpace: "pre-line" }}>{d.year}</div>
                </div>
              );
            })}
          </div>
        )}

        {/* CEO ratio visualization */}
        {isCEO && (
          <div style={{ display: "flex", gap: 60, alignItems: "center" }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 42, color: "#aaa", marginBottom: 12 }}>1978</div>
              <div style={{
                width: 120, height: 120, borderRadius: "50%",
                border: `6px solid ${theme.accent}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: FONTS.DISPLAY, fontSize: 44, color: theme.accent,
              }}>30×</div>
              <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 28, color: "#ccc", marginTop: 12 }}>CEO vs Worker</div>
            </div>
            <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 72, color: theme.accent }}>→</div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 42, color: "#aaa", marginBottom: 12 }}>2023</div>
              <div style={{
                width: 200, height: 200, borderRadius: "50%",
                border: `8px solid #ff4444`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontFamily: FONTS.DISPLAY, fontSize: 54, color: "#ff4444",
                boxShadow: "0 0 32px #ff444466",
                transform: `scale(${interpolate(spring({ frame: Math.max(0, frame - 20), fps, config: { damping: 10, stiffness: 100 } }), [0, 1], [0.5, 1])})`,
              }}>344×</div>
              <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 28, color: "#ccc", marginTop: 12 }}>CEO vs Worker</div>
            </div>
          </div>
        )}

        {/* Inheritance */}
        {isInheritance && (
          <div style={{ display: "flex", gap: 40, flexWrap: "wrap" }}>
            <StatCard value="50–60%" label="of wealth in Western economies comes from inheritance" accent={theme.accent} delayFrames={10} />
            <StatCard value="<10%" label="chance of rising from bottom 20% to top 20%" accent="#ff4444" delayFrames={20} />
            <StatCard value="60%" label="chance of staying in top 20% if born there" accent={theme.accent} delayFrames={30} />
          </div>
        )}

        {/* r > g section */}
        {sec.id === "section_3" && (
          <div style={{ display: "flex", gap: 60, alignItems: "center", marginTop: 20 }}>
            <div style={{
              fontFamily: FONTS.DISPLAY, fontSize: 110,
              background: `linear-gradient(135deg, ${theme.accent}, #ffffff)`,
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
              letterSpacing: "0.1em",
              transform: `scale(${interpolate(spring({ frame, fps, config: { damping: 8, stiffness: 100 } }), [0, 1], [0.7, 1])})`,
            }}>r &gt; g</div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                <StatCard value="~5%" label="annual return on capital (r)" accent={theme.accent} delayFrames={15} />
                <StatCard value="~2%" label="average economic growth (g)" accent="#ff8800" delayFrames={25} />
              </div>
            </div>
          </div>
        )}
      </AbsoluteFill>
      <ChapterLabel num={sectionIndex + 1} title={sec.title} accent={theme.accent} />
    </AbsoluteFill>
  );
};

const SolutionSection: React.FC<{ sec: z.infer<typeof longSectionSchema>; theme: (typeof THEMES)["general"]; sectionIndex: number }> = ({ sec, theme, sectionIndex }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = sec.endFrame - sec.startFrame;
  const ent = spring({ frame, fps, config: { damping: 12, stiffness: 140 } });
  const exitOp = interpolate(frame, [dur - 15, dur], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      {sec.backgroundVideo ? (
        <AbsoluteFill>
          <Video src={staticFile(sec.backgroundVideo)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <AbsoluteFill style={{ background: "rgba(0,0,0,0.72)" }} />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill style={{ background: theme.gradient }} />
      )}
      <AbsoluteFill style={{ padding: "100px 100px", opacity: exitOp, flexDirection: "column", justifyContent: "center" }}>
        <div style={{
          fontFamily: FONTS.DISPLAY, fontSize: 58, color: theme.accent,
          textTransform: "uppercase", letterSpacing: "0.05em",
          opacity: interpolate(ent, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(ent, [0, 1], [-30, 0])}px)`,
          marginBottom: 24,
        }}>
          {sec.title}
        </div>
        <div style={{ height: 4, backgroundColor: theme.accent, width: `${interpolate(ent, [0, 1], [0, 400])}px`, marginBottom: 48 }} />
        <div style={{ display: "flex", gap: 40, flexWrap: "wrap" }}>
          <StatCard value="$1.7T" label="raised annually by 5% wealth tax on billionaires (Oxfam)" accent={theme.accent} delayFrames={10} />
          <StatCard value="2×" label="enough to end extreme poverty — twice over" accent={theme.accent} delayFrames={20} />
          <StatCard value="Norway" label="highest social mobility + lowest inequality — strong unions + free education" accent={theme.accent} delayFrames={30} />
        </div>
      </AbsoluteFill>
      <ChapterLabel num={sectionIndex + 1} title={sec.title} accent={theme.accent} />
    </AbsoluteFill>
  );
};

const CtaSection: React.FC<{ sec: z.infer<typeof longSectionSchema>; theme: (typeof THEMES)["general"] }> = ({ sec, theme }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = sec.endFrame - sec.startFrame;
  const ent = spring({ frame, fps, config: { damping: 10, stiffness: 120 } });
  const pulse = Math.sin(frame / 12) * 0.04 + 1;

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: theme.gradient }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 40,
        opacity: interpolate(ent, [0, 1], [0, 1]),
        transform: `scale(${interpolate(ent, [0, 1], [0.92, 1])})`,
      }}>
        <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 80, color: theme.accent, textAlign: "center",
          textShadow: `0 0 40px ${theme.accent}`, letterSpacing: "0.06em", transform: `scale(${pulse})` }}>
          SUBSCRIBE
        </div>
        <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 36, color: "#cccccc", textAlign: "center", maxWidth: 900, lineHeight: 1.4 }}>
          More videos on the forces shaping our world
        </div>
        <div style={{ width: 120, height: 6, backgroundColor: theme.accent, borderRadius: 3, boxShadow: `0 0 20px ${theme.accent}` }} />
        <div style={{ fontFamily: FONTS.DISPLAY, fontSize: 28, color: theme.accent, opacity: 0.8 }}>
          ▶ FactForge
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ─── Main Composition ────────────────────────────────────────────────────────

export const LongVideo: React.FC<LongVideoProps> = ({
  videoId,
  title,
  sections,
  audioFile,
  wordTimestamps,
  colorTheme,
  totalDurationFrames,
}) => {
  const theme = THEMES[colorTheme] || THEMES.general;
  const { durationInFrames } = useVideoConfig();
  const totalFrames = totalDurationFrames ?? durationInFrames;

  const renderSection = (sec: z.infer<typeof longSectionSchema>, i: number) => {
    const dur = sec.endFrame - sec.startFrame;
    let content: React.ReactNode;

    switch (sec.type) {
      case "hook":
        content = <HookSection sec={sec} theme={theme} sectionIndex={i} />;
        break;
      case "explainer":
      case "global_comparison":
        content = <ExplainerSection sec={sec} theme={theme} sectionIndex={i} />;
        break;
      case "deep_dive":
        content = <DeepDiveSection sec={sec} theme={theme} sectionIndex={i} />;
        break;
      case "solution":
        content = <SolutionSection sec={sec} theme={theme} sectionIndex={i} />;
        break;
      case "cta":
        content = <CtaSection sec={sec} theme={theme} />;
        break;
      default:
        content = <ExplainerSection sec={sec} theme={theme} sectionIndex={i} />;
    }

    return (
      <Sequence key={sec.id} from={sec.startFrame} durationInFrames={dur}>
        {content}
      </Sequence>
    );
  };

  return (
    <AbsoluteFill style={{ backgroundColor: theme.bg }}>
      {/* Background fallback */}
      <AbsoluteFill style={{ background: theme.gradient }} />

      {/* Sections */}
      {sections.map((sec, i) => renderSection(sec, i))}

      {/* Karaoke captions */}
      {wordTimestamps && wordTimestamps.length > 0 && (
        <KaraokeCaption
          words={wordTimestamps as WordTimestamp[]}
          accentColor={theme.accent}
          fontSize={56}
          wordsPerLine={5}
          bottomOffset={80}
          pillPadding="16px 28px"
        />
      )}

      {/* Top progress bar */}
      <LongProgressBar accent={theme.accent} totalFrames={totalFrames} />

      {/* Watermark */}
      <div style={{
        position: "absolute", bottom: 28, right: 48,
        fontFamily: FONTS.DISPLAY, fontSize: 26, color: "rgba(255,255,255,0.3)",
        letterSpacing: "0.12em",
      }}>
        FACTFORGE
      </div>

      {/* Audio */}
      {audioFile && <Audio src={staticFile(audioFile)} />}
    </AbsoluteFill>
  );
};
