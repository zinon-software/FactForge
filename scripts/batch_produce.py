"""
FactForge Batch Producer — 10 videos
Runs full pipeline: script → audio → timestamps → remotion_props
Then prints a render shell script to execute.
"""

import asyncio, json, os, shutil, subprocess, sys
from pathlib import Path
import edge_tts
from faster_whisper import WhisperModel

BASE = Path(__file__).parent.parent
REMOTION_PUBLIC = BASE / "video" / "remotion-project" / "public"

# ─────────────────────────── Video Data ────────────────────────────────────

VIDEOS = {
  "S01062": {
    "title": "EpiPen: $7 to Make. $608 to Buy.",
    "category": "PHARMA SCANDAL",
    "colorTheme": "shocking",
    "bg_sequence": ["scene_hospital","scene_money","scene_office","scene_money","scene_govt","scene_prison","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","impact","cta"],
    "highlights": [["$30","manufacture"],["500%"],["$608","nine years"],["$18.9 million","671%"],["$465 million"],["admitted nothing"],["afford"]],
    "script": """An EpiPen is a plastic tube with a spring and a needle.
It contains 0.3 milligrams of epinephrine — a drug worth less than one cent.
The total cost to manufacture: about $30.
In 2007, a two-pack sold for $100.
By 2016, the same two-pack cost $608.
That is a 500% increase in nine years.
The CEO of Mylan raised her own salary by 671% during the same period.
From $2.4 million a year to $18.9 million.
The same EpiPen cost $69 in the United Kingdom and $80 in Canada.
Congress called her to testify.
She admitted the profit per pen was $100.
No criminal charges were filed.
Mylan paid $465 million to settle a fraud case — and admitted nothing.
The CEO left with a $30 million exit package.
EpiPens still exist. People still can't afford them.
Follow this channel.""",
  },

  "S01110": {
    "title": "University Costs $300 in Germany. $108,000 in the US.",
    "category": "PRICE COMPARISON",
    "colorTheme": "comparison",
    "bg_sequence": ["scene_school","scene_money","scene_city_aerial","scene_money","scene_office","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","cta"],
    "highlights": [["free"],["$108,000"],["$1.84 trillion"],["5.3 million","default"],["$134 million"],["decade"]],
    "script": """In Germany, university is free.
Not cheap. Free.
Students pay a semester fee of about $300 — which also covers unlimited public transit.
In the United States, a four-year degree costs an average of $108,000.
Private universities: $255,000.
Americans collectively owe $1.84 trillion in student loan debt — held by 43 million people.
That is one in six American adults.
As of 2024, 5.3 million borrowers are in active default.
Every single day, American student debt grows by $134 million.
Germany doesn't only offer free tuition to Germans.
Norway offers free university to every student on earth — regardless of nationality.
A German graduate starts their career debt-free.
The average American graduate starts with $29,560 in debt and pays it back for a decade.
Follow this channel.""",
  },

  "S01155": {
    "title": "Africa's Largest Dam — Built With Workers' Salaries",
    "category": "ENGINEERING",
    "colorTheme": "history",
    "bg_sequence": ["scene_city_aerial","scene_factory","scene_office","scene_factory","scene_govt","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","cta"],
    "highlights": [["largest","Africa"],["5,150 megawatts"],["twice","Aswan"],["25,000 workers"],["97%","Nile"],["continues"]],
    "script": """Ethiopia built the largest dam in Africa.
5,150 megawatts of electricity — more than twice the capacity of Egypt's Aswan Dam.
They didn't borrow the money from the World Bank.
The government withheld portions of civil servant salaries and sold bonds to ordinary citizens.
They raised the money themselves.
Construction began in 2011.
25,000 workers — 95% Ethiopian nationals — poured more concrete in a single day than any other dam in history.
The reservoir holds 74 billion cubic meters of water.
More than 70 million Ethiopians currently have no reliable electricity.
GERD is their solution.
Egypt, which gets 97% of its freshwater from the Nile, sees it as an existential threat.
No agreement has been reached.
The dam runs. The dispute continues.
Follow this channel.""",
  },

  "S01183": {
    "title": "A $1 Pill That Cures Hepatitis C — Sold for $84,000",
    "category": "PHARMA SCANDAL",
    "colorTheme": "shocking",
    "bg_sequence": ["scene_hospital","scene_money","scene_office","scene_money","scene_govt","scene_hospital","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","impact","cta"],
    "highlights": [["cure","94","99%"],["$84,000","$1,000 per pill"],["$300","India"],["$10 billion","first year"],["$60 million","taxpayers"],["denied","half"]],
    "script": """Hepatitis C kills 290,000 people a year.
There is a cure. It takes 12 weeks. It works in 94 to 99 percent of cases.
The pill costs roughly $1 to manufacture.
In India, a full 12-week treatment costs $300.
In Egypt, it was negotiated to $900 — then offered free to patients.
In the United States, the same treatment costs $84,000.
That is $1,000 per pill, per day.
Gilead Sciences made $10 billion from this drug in its first year alone.
The original research cost $62 million.
American taxpayers funded $60 million of that through the NIH.
A Senate investigation found Gilead set the price at $84,000 not based on costs — but on what they could extract.
Insurance companies denied more than half of claims.
2.4 million Americans have Hepatitis C. Most can't afford the cure.
Follow this channel.""",
  },

  "S01185": {
    "title": "40 Billion Faces. No Consent. No Warrant.",
    "category": "SURVEILLANCE",
    "colorTheme": "power",
    "bg_sequence": ["scene_cyber","scene_ai","scene_city_aerial","scene_cyber","scene_court","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","cta"],
    "highlights": [["40 billion","consent"],["3,100","warrant"],["100 times","Black"],["wrongful arrest"],["illegal"],["no federal law"]],
    "script": """A company called Clearview AI scraped 40 billion photos from the internet.
Without asking anyone. Without telling anyone.
Over 3,100 US police departments can now search your face — without a warrant.
A 2019 government study found facial recognition misidentifies Black faces up to 100 times more often than white faces.
In 2020, a man named Robert Williams was handcuffed in his driveway in front of his family and held for 30 hours.
He had been matched to blurry shoplifting footage. The match was wrong.
Every documented case of a wrongful arrest caused by facial recognition in America has involved a Black man.
The UK, France, Italy, and Australia have all ruled Clearview AI illegal.
The US has no federal law banning it.
Follow this channel.""",
  },

  "S01190": {
    "title": "One Lawsuit. $9.9 Trillion in Damages. AI on Trial.",
    "category": "AI + LAW",
    "colorTheme": "science",
    "bg_sequence": ["scene_ai","scene_ai_law","scene_office","scene_court","scene_ai_law","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","cta"],
    "highlights": [["$9.9 trillion"],["66 million"],["$150,000 per article"],["trial"],["$1.5 billion","settlement"],["no one knows"]],
    "script": """On December 27, 2023, The New York Times sued OpenAI.
They alleged OpenAI used 66 million pieces of their content — without permission — to train GPT.
The potential damages: $150,000 per article.
Multiply that by 66 million articles.
The theoretical maximum: $9.9 trillion.
More than the GDP of every country except the United States and China.
A federal judge rejected OpenAI's motion to dismiss in 2025. The case is going to trial.
The NYT is not alone.
John Grisham. George R.R. Martin. Getty Images. Universal Music.
Anthropic settled for $1.5 billion — about $3,000 per book.
At least 51 copyright lawsuits have been filed against AI companies globally.
The US Copyright Office rejected a blanket fair use defense for AI training.
No one knows yet how this ends.
Follow this channel.""",
  },

  "S01215": {
    "title": "For 50 Years, the CIA Owned the World's Encryption Company",
    "category": "INTELLIGENCE",
    "colorTheme": "power",
    "bg_sequence": ["scene_cyber","scene_govt","scene_office","scene_cyber","scene_govt","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","cta"],
    "highlights": [["120 governments"],["CIA owned it"],["1970","$5.75 million"],["intelligence coup of the century"],["2020"],["50 years"]],
    "script": """For nearly 50 years, over 120 governments paid to encrypt their most sensitive communications.
Diplomatic cables. Military orders. Intelligence reports.
They trusted a Swiss company called Crypto AG.
Switzerland is neutral. Switzerland is trustworthy.
The CIA owned it.
In 1970, the CIA and West German intelligence secretly purchased Crypto AG for $5.75 million.
They rigged the encryption devices.
For decades, they read the world's secrets in real time.
During the Iran hostage crisis, the CIA could answer 85% of the President's questions about Khomeini's intentions.
During the Falklands War, intercepted Argentine communications were fed directly to Britain.
After the 1986 Berlin disco bombing, the CIA listened as Libyan agents celebrated.
Reagan used those intercepts to justify airstrikes.
The CIA's own history called it — quote — the intelligence coup of the century.
The operation ran until 2018. Revealed publicly in 2020.
Follow this channel.""",
  },

  "S01224": {
    "title": "The 13th Amendment Never Abolished Slavery",
    "category": "LAW + JUSTICE",
    "colorTheme": "shocking",
    "bg_sequence": ["scene_prison","scene_govt","scene_factory","scene_prison","scene_office","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","cta"],
    "highlights": [["except","punishment for crime"],["800,000","$0"],["23 cents","$1.15"],["$411 million","Pentagon"],["convict leasing","modern slavery"],["allows it"]],
    "script": """The 13th Amendment abolished slavery in 1865.
Except for one group.
The exact text: neither slavery nor involuntary servitude shall exist — except as a punishment for crime.
That exception is still active today.
800,000 Americans work in prison right now.
Federal prisoners are paid between 23 cents and $1.15 per hour.
In five states — Alabama, Arkansas, Florida, Georgia, and Texas — many prisoners are paid nothing at all.
The federal government's prison factory earns $411 million per year.
56% of that revenue comes from the Pentagon.
Prisoners make Army combat uniforms, body armor, and military vehicle components.
An investigation found over 500 businesses using prison labor in Alabama alone — including McDonald's, Burger King, and Walmart.
In December 2023, a federal lawsuit called it what it is: convict leasing. Modern slavery.
The 13th Amendment allows it.
Follow this channel.""",
  },

  "S01267": {
    "title": "Sam Altman Is Raising $7 Trillion. Just for the Chips.",
    "category": "AI + MONEY",
    "colorTheme": "science",
    "bg_sequence": ["scene_ai","scene_chatgpt","scene_city_aerial","scene_money","scene_ai","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","cta"],
    "highlights": [["$100 million","GPT-4"],["doubling every 8 months"],["$7 trillion"],["$320 billion","2025"],["more than Japan"],["barely afford"]],
    "script": """Training GPT-3 cost $12 million.
Training GPT-4 cost $100 million. That was two years ago.
AI compute costs are doubling every 8 months.
At that rate, training a model in 2027 could cost $1 billion.
The CEO of Anthropic says $100 billion models are coming soon.
Sam Altman — CEO of OpenAI — is trying to raise $7 trillion.
Not for the AI itself. For the chips needed to build it.
$7 trillion is more than the combined GDP of Germany and Japan.
Microsoft, Google, Amazon, and Meta are spending over $320 billion on AI data centers in 2025 alone.
All the world's data centers already consume more electricity than Japan.
By 2030, that number doubles.
We are building something we can barely afford.
Follow this channel.""",
  },

  "S01268": {
    "title": "A $200 Film Just Played in 58 Cinemas",
    "category": "AI + FILM",
    "colorTheme": "science",
    "bg_sequence": ["scene_chatgpt","scene_ai","scene_office","scene_ai","scene_chatgpt","scene_reveal"],
    "segment_types": ["hook","fact","fact","impact","fact","cta"],
    "highlights": [["$200","102 minutes"],["not real"],["97 percent"],["Lionsgate","John Wick"],["1,000","80%"],["already exists"]],
    "script": """In July 2025, a 102-minute film called Post Truth opened in 58 cinemas.
The actors were not real. The sets were not real. The music was not real.
Everything was generated by artificial intelligence.
It cost about $200 to produce.
A traditional 3-minute short film costs between $5,000 and $30,000.
AI cut that cost by 97 percent.
Lionsgate — the studio behind John Wick and The Hunger Games — signed a deal with an AI company to train a model on their entire film library.
The SAG-AFTRA actors' strike of 2023 was partly about this.
They won protections. The technology kept advancing.
Hollywood VFX crews that once numbered 1,000 per production could shrink by 80 percent.
The first AI feature film already exists.
Follow this channel.""",
  },
}


# ─────────────────────────── Pipeline ──────────────────────────────────────

async def gen_audio(text, voice, rate, out_path):
    comm = edge_tts.Communicate(text, voice=voice, rate=rate)
    await comm.save(str(out_path))

def get_duration(path):
    r = subprocess.run(
        ["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",str(path)],
        capture_output=True, text=True)
    return float(r.stdout.strip())

def get_timestamps(audio_path, model):
    segs, _ = model.transcribe(str(audio_path), word_timestamps=True, language="en", beam_size=1)
    words = []
    for seg in segs:
        for w in seg.words:
            word = w.word.strip()
            if word:
                words.append({"word": word, "start_ms": round(w.start*1000), "end_ms": round(w.end*1000)})
    return words

def build_props(vid_id, data, duration_s, words):
    fps = 60
    total_frames = round(duration_s * fps)
    n_segs = len(data["bg_sequence"])
    seg_frames = total_frames // n_segs
    segments = []
    for i, (bg, stype) in enumerate(zip(data["bg_sequence"], data["segment_types"])):
        start = i * seg_frames
        end = (i + 1) * seg_frames if i < n_segs - 1 else total_frames
        kb = ["zoom-in","zoom-out","pan-left","pan-right"][i % 4]
        hw = data["highlights"][i] if i < len(data["highlights"]) else []
        segments.append({
            "type": stype, "text": "", "startFrame": start, "endFrame": end,
            "highlightWords": hw, "backgroundVideo": f"bg_videos/{bg}.mp4", "kenBurns": kb
        })
    return {
        "videoId": vid_id,
        "categoryLabel": data["category"],
        "colorTheme": data["colorTheme"],
        "totalDurationFrames": total_frames,
        "audioFile": f"audio_{vid_id}.mp3",
        "backgroundVideoUrl": None,
        "scale": 1,
        "segments": segments,
        "wordTimestamps": words,
    }


def main():
    print("Loading Whisper model...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")

    render_cmds = []

    for vid_id, data in VIDEOS.items():
        print(f"\n{'='*50}")
        print(f"[{vid_id}] {data['title']}")
        out_dir = BASE / "output" / vid_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "subtitles").mkdir(exist_ok=True)

        # 1. Save script.json
        script = {
            "video_id": vid_id,
            "tts_voice": "en-US-AndrewNeural",
            "tts_rate": "+8%",
            "script_score": 88,
            "full_text": data["script"].strip(),
        }
        with open(out_dir / "script.json", "w") as f:
            json.dump(script, f, indent=2)
        print(f"  ✓ script.json saved")

        # 2. Generate audio
        audio_path = out_dir / "audio.mp3"
        print(f"  → Generating audio...")
        asyncio.run(gen_audio(data["script"].strip(), "en-US-AndrewNeural", "+8%", audio_path))
        duration = get_duration(audio_path)
        print(f"  ✓ audio.mp3 — {duration:.1f}s")

        # Duration gate: 35–60 seconds
        if duration > 62:
            print(f"  ⚠ WARNING: {duration:.1f}s > 60s — video will be uploaded as regular video, not Short")
        elif duration < 33:
            print(f"  ⚠ WARNING: {duration:.1f}s < 35s — too short")

        # 3. Word timestamps
        print(f"  → Extracting word timestamps...")
        words = get_timestamps(audio_path, model)
        print(f"  ✓ {len(words)} words timestamped")

        ts_path = out_dir / "word_timestamps.json"
        with open(ts_path, "w") as f:
            json.dump({"video_id": vid_id, "words": words}, f, indent=2)

        # 4. Build remotion_props.json
        props = build_props(vid_id, data, duration, words)
        with open(out_dir / "remotion_props.json", "w") as f:
            json.dump(props, f, indent=2)
        print(f"  ✓ remotion_props.json — {props['totalDurationFrames']} frames")

        # 5. Copy audio to remotion public
        dest = REMOTION_PUBLIC / f"audio_{vid_id}.mp3"
        shutil.copy(audio_path, dest)
        print(f"  ✓ Copied to Remotion public")

        # Queue render command
        props_path = BASE / "output" / vid_id / "remotion_props.json"
        out_mp4 = BASE / "output" / vid_id / "video_noaudio.mp4"
        render_cmds.append(
            f'echo "=== Rendering {vid_id} ===" && '
            f'./node_modules/.bin/remotion render src/index.ts ShortVideo '
            f'"{out_mp4}" '
            f'--props="{props_path}" '
            f'--codec=h264 --concurrency=4 && '
            f'echo "✓ Render done {vid_id}" && '
            f'ffmpeg -i "{out_mp4}" '
            f'-i "{BASE}/output/{vid_id}/audio.mp3" '
            f'-c:v copy -c:a aac -b:a 256k -shortest '
            f'"{BASE}/output/{vid_id}/video.mp4" -y && '
            f'echo "✓ Merge done {vid_id}"'
        )

    # Write render queue script
    render_script = BASE / "scripts" / "render_queue.sh"
    with open(render_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("set -e\n")
        f.write(f'cd "{BASE}/video/remotion-project"\n\n')
        for cmd in render_cmds:
            f.write(cmd + "\n\n")
        f.write(f'\necho ""\n')
        f.write(f'echo "✅ ALL 10 VIDEOS RENDERED AND MERGED SUCCESSFULLY"\n')
        f.write(f'echo "Videos ready in: {BASE}/output/"\n')
        f.write(f'python3 "{BASE}/scripts/batch_finalize.py"\n')
    os.chmod(render_script, 0o755)

    print(f"\n{'='*50}")
    print(f"✅ All audio + timestamps + props generated for {len(VIDEOS)} videos")
    print(f"📋 Render queue written to: scripts/render_queue.sh")
    print(f"▶  Run: bash scripts/render_queue.sh")


if __name__ == "__main__":
    main()
