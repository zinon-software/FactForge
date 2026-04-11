import { Composition } from "remotion";
import { ShortVideo, shortVideoSchema } from "./compositions/ShortVideo";
import { LongVideo, longVideoSchema } from "./compositions/LongVideo";

export const Root: React.FC = () => {
  return (
    <>
      {/* YouTube Short: 1080×1920, 60fps, max 58 seconds */}
      <Composition
        id="ShortVideo"
        component={ShortVideo}
        durationInFrames={60 * 58}
        fps={60}
        width={1080}
        height={1920}
        schema={shortVideoSchema}
        defaultProps={{
          videoId: "test",
          hook: "One man owned more than all of Europe combined",
          segments: [
            { text: "Mansa Musa was the richest human who ever lived.", startFrame: 0, endFrame: 150 },
            { text: "Historians estimate his wealth at four hundred billion dollars.", startFrame: 150, endFrame: 310 },
            { text: "He was so rich his charity caused a decade-long economic depression.", startFrame: 310, endFrame: 500 },
          ],
          audioFile: null,
          backgroundVideoUrl: null,
          colorTheme: "islamic",
          format: "shocking_stat",
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
          videoId: "test",
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
