import React from "react";
import { Composition } from "remotion";
import { LongVideo, longVideoSchema } from "./compositions/LongVideo";
import { ShortVideo, shortVideoSchema } from "./compositions/ShortVideo";

export const Root: React.FC = () => {
  return (
    <>
      {/* YouTube Short: 1080×1920, 60fps */}
      <Composition
        id="ShortVideo"
        component={ShortVideo}
        durationInFrames={60 * 60}
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
        durationInFrames={30 * 600}
        fps={30}
        width={1920}
        height={1080}
        schema={longVideoSchema}
        defaultProps={{
          videoId: "L00000",
          title: "Test Long Video",
          sections: [],
          audioFile: null,
          backgroundVideoUrl: null,
          colorTheme: "general",
        }}
      />
    </>
  );
};
