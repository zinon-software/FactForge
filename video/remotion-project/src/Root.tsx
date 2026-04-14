import React from "react";
import { Composition } from "remotion";
import { DocumentaryVideo, documentaryVideoSchema } from "./compositions/DocumentaryVideo";
import { LongVideo, longVideoSchema } from "./compositions/LongVideo";
import { ShortVideo, shortVideoSchema } from "./compositions/ShortVideo";
import { WealthRanking, wealthRankingSchema } from "./compositions/WealthRanking";

export const Root: React.FC = () => {
  return (
    <>
      {/* YouTube Short: 1080×1920, 60fps */}
      <Composition
        id="ShortVideo"
        component={ShortVideo}
        durationInFrames={3600}
        fps={60}
        width={1080}
        height={1920}
        schema={shortVideoSchema}
        defaultProps={{
          videoId: "S00000",
          categoryLabel: "SHOCKING FACTS",
          colorTheme: "shocking",
          totalDurationFrames: 3600,
          segments: [
            {
              type: "hook",
              text: "This will change how you see everything.",
              startFrame: 0,
              endFrame: 180,
              highlightWords: ["change", "everything"],
            },
            {
              type: "fact",
              text: "A fact so shocking it stopped the world.",
              startFrame: 180,
              endFrame: 360,
              highlightWords: [],
            },
          ],
          audioFile: null,
          backgroundVideoUrl: null,
        }}
      />

      {/* Long Video: 1920×1080, 30fps */}
      <Composition
        id="LongVideo"
        component={LongVideo}
        durationInFrames={10691}
        fps={30}
        width={1920}
        height={1080}
        schema={longVideoSchema}
        defaultProps={{
          videoId: "L00016",
          title: "The Wealth Gap",
          sections: [],
          audioFile: null,
          backgroundVideoUrl: null,
          colorTheme: "wealth",
        }}
      />
      {/* Documentary Video: 1920×1080, 30fps — image-heavy cinematic docs */}
      <Composition
        id="DocumentaryVideo"
        component={DocumentaryVideo}
        durationInFrames={18603}
        fps={30}
        width={1920}
        height={1080}
        schema={documentaryVideoSchema}
        defaultProps={{
          videoId: "L00200",
          title: "The Islamic Golden Age",
          colorTheme: "islamic",
          sections: [],
          audioFile: null,
          wordTimestamps: [],
          totalDurationFrames: 18603,
        }}
      />

      {/* Wealth Ranking: 1920×1080, 30fps */}
      <Composition
        id="WealthRanking"
        component={WealthRanking}
        durationInFrames={30 * 420}
        fps={30}
        width={1920}
        height={1080}
        schema={wealthRankingSchema}
        defaultProps={{
          videoId: "L00100",
          audioFile: null,
          totalDurationFrames: 12600,
          segments: [],
        }}
      />
    </>
  );
};
