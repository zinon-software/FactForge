"""
batch_produce_2.py — Batch production pipeline for 10 Short videos (Batch 2)
Videos: S00794, S00925, S01066, S01080, S01084, S01097, S01113, S01128, S01131, S01644
"""
import asyncio
import json
import os
import shutil
import subprocess
import warnings
warnings.filterwarnings("ignore")

import edge_tts

BASE = "/Users/ar/Development/projects/FactForge"
PUBLIC = f"{BASE}/video/remotion-project/public"

VIDEOS = {
    "S00794": {
        "title": "The Race to Build an AGI — Who Is Winning and What Happens When They Do",
        "category": "SHOCKING FACTS",
        "color_theme": "science",
        "script": (
            "Every major AI lab has made the same announcement. "
            "AGI — artificial general intelligence — is coming within years. "
            "Sam Altman says a few years. Demis Hassabis says within a decade. "
            "But there is no agreed definition of AGI. No regulatory framework. No safety protocol. "
            "OpenAI is training on more compute than any system in history. "
            "Google DeepMind built AlphaFold — it solved a 50-year biology problem overnight. "
            "China has 50 percent more AI researchers than the United States. "
            "The country that builds AGI first will have an advantage unlike anything in human history. "
            "More powerful than nuclear weapons. "
            "And right now — nobody is in charge."
        ),
        "segments": [
            {"type": "hook", "text": "AGI is coming.\nWho wins?", "highlights": ["AGI", "wins"]},
            {"type": "fact", "text": "Sam Altman:\nAGI in 'a few years'", "highlights": ["Altman", "years"]},
            {"type": "fact", "text": "No definition.\nNo regulation.\nNo plan.", "highlights": ["No"]},
            {"type": "impact", "text": "China has 50% MORE\nAI researchers\nthan the US", "highlights": ["50%", "MORE"]},
            {"type": "fact", "text": "DeepMind solved\na 50-year biology\nproblem overnight", "highlights": ["50-year", "overnight"]},
            {"type": "impact", "text": "The first to build AGI\ngains an advantage\ngreater than nukes", "highlights": ["AGI", "nukes"]},
            {"type": "cta", "text": "Nobody\nis in charge.", "highlights": ["Nobody"]},
        ],
        "bg_sequence": ["scene_tech","scene_data","scene_tech","scene_city_aerial","scene_tech","scene_data","scene_tech"],
    },
    "S00925": {
        "title": "The Oil Companies That Knew About Climate Change in 1977",
        "category": "SHOCKING FACTS",
        "color_theme": "shocking",
        "script": (
            "In 1977, Exxon's own scientists warned the company that burning fossil fuels would cause catastrophic climate change. "
            "They predicted the exact CO2 levels we see today. "
            "Exxon's response was to fund thirty million dollars in climate denial campaigns. "
            "They lobbied against every climate agreement for four decades. "
            "Internal documents show executives knew the science was accurate. "
            "They chose profit over the planet. "
            "California, New York, and Massachusetts are now suing Exxon for damages. "
            "The company that knew first — did the most to stop action. "
            "The bill is now being calculated in trillions."
        ),
        "segments": [
            {"type": "hook", "text": "Exxon knew in 1977.\nThey hid it.", "highlights": ["1977", "hid"]},
            {"type": "fact", "text": "Their own scientists\npredicted catastrophic\nclimate change", "highlights": ["scientists", "catastrophic"]},
            {"type": "impact", "text": "$30 MILLION\nfunded climate\ndenial campaigns", "highlights": ["$30 MILLION", "denial"]},
            {"type": "fact", "text": "Executives knew\nthe science\nwas accurate", "highlights": ["knew", "accurate"]},
            {"type": "impact", "text": "4 decades of lobbying\nagainst every\nclimate agreement", "highlights": ["4 decades"]},
            {"type": "fact", "text": "3 US states\nnow suing\nExxon for damages", "highlights": ["3", "suing"]},
            {"type": "cta", "text": "The bill is\nin trillions.", "highlights": ["trillions"]},
        ],
        "bg_sequence": ["scene_factory","scene_money","scene_factory","scene_city_aerial","scene_factory","scene_money","scene_factory"],
    },
    "S01066": {
        "title": "How El Salvador's Homicide Rate Dropped 95% in Two Years",
        "category": "SHOCKING FACTS",
        "color_theme": "power",
        "script": (
            "In 2015, El Salvador was the most dangerous country on Earth. "
            "One hundred and three murders per hundred thousand people. Every year. "
            "By 2023, that number had fallen to two point four. "
            "A ninety-seven percent drop in eight years. "
            "President Bukele declared a state of exception. "
            "Seventy-five thousand gang members arrested. "
            "El Salvador is now statistically safer than the United States. "
            "But human rights groups documented five thousand cases of arbitrary detention. "
            "Innocent people imprisoned with no trial. "
            "One of the most dramatic crime collapses in history — "
            "and one of the most controversial methods ever used."
        ),
        "segments": [
            {"type": "hook", "text": "The world's most\ndangerous country\nbecame safe in 2 years", "highlights": ["dangerous", "2 years"]},
            {"type": "number", "text": "murders per 100K people in 2015", "highlights": [], "numberValue": 103, "numberSuffix": " per 100K"},
            {"type": "impact", "text": "Now: 2.4 per 100K\nSafer than\nthe United States", "highlights": ["2.4", "United States"]},
            {"type": "fact", "text": "75,000 gang members\narrested in\none operation", "highlights": ["75,000"]},
            {"type": "impact", "text": "97% DROP\nin homicides\nin 8 years", "highlights": ["97%", "DROP"]},
            {"type": "fact", "text": "5,000+ people\ndetained with\nno trial", "highlights": ["5,000+", "no trial"]},
            {"type": "cta", "text": "Safety or freedom?\nEl Salvador chose.", "highlights": ["Safety", "freedom"]},
        ],
        "bg_sequence": ["scene_city_aerial","scene_court","scene_city_aerial","scene_court","scene_city_aerial","scene_court","scene_city_aerial"],
    },
    "S01080": {
        "title": "The AI That Can Clone Your Voice in 3 Seconds",
        "category": "SHOCKING FACTS",
        "color_theme": "science",
        "script": (
            "Three seconds. That is all the audio an AI needs to perfectly clone your voice. "
            "ElevenLabs can replicate any voice from a short recording. "
            "Scammers are already using it. "
            "The FTC reported eleven million dollars in voice-clone scam losses in 2023 alone. "
            "The most common method: clone a family member's voice — then call their parents in fake distress. "
            "OpenAI built Voice Engine. "
            "It was so realistic they refused to release it publicly. "
            "Your voice is now a biometric that can be stolen. "
            "And there is currently no law that specifically criminalizes cloning someone's voice."
        ),
        "segments": [
            {"type": "hook", "text": "3 seconds of audio.\nYour voice is cloned.", "highlights": ["3 seconds", "cloned"]},
            {"type": "fact", "text": "ElevenLabs clones\nany voice from\na short recording", "highlights": ["ElevenLabs", "clones"]},
            {"type": "number", "text": "lost to voice-clone scams in 2023 (FTC)", "highlights": [], "numberValue": 11, "numberPrefix": "$", "numberSuffix": "M"},
            {"type": "impact", "text": "Scammers clone\nyour family's voice\nto steal from them", "highlights": ["clone", "steal"]},
            {"type": "fact", "text": "OpenAI's Voice Engine\nwas too realistic\nto release publicly", "highlights": ["too realistic"]},
            {"type": "impact", "text": "No law criminalizes\ncloning someone's\nvoice — yet", "highlights": ["No law", "yet"]},
            {"type": "cta", "text": "Your voice\ncan be stolen.", "highlights": ["stolen"]},
        ],
        "bg_sequence": ["scene_tech","scene_data","scene_tech","scene_data","scene_tech","scene_data","scene_tech"],
    },
    "S01084": {
        "title": "The $40 Aspirin: How Hospital Billing Became Legalized Robbery",
        "category": "SHOCKING FACTS",
        "color_theme": "shocking",
        "script": (
            "A single aspirin tablet costs one cent at a pharmacy. "
            "US hospitals charge forty dollars for the same pill. "
            "A four-thousand percent markup — completely legal. "
            "Hospitals use a document called the chargemaster — "
            "an internal price list with no regulatory oversight. "
            "A 2013 TIME investigation found one hospital charging eighteen dollars for a diabetic test strip "
            "that costs fifty-five cents. "
            "A pair of surgical gloves — two thousand dollars. "
            "One hospital charged one hundred and twenty thousand dollars for a surgery "
            "that cost ten thousand at the hospital across the street. "
            "The No Surprises Act was passed in 2022. "
            "The loopholes remain. The prices keep rising."
        ),
        "segments": [
            {"type": "hook", "text": "$0.01 aspirin.\n$40 in a hospital.\nLegal.", "highlights": ["$0.01", "$40", "Legal"]},
            {"type": "number", "text": "markup on a single aspirin in US hospitals", "highlights": [], "numberValue": 4000, "numberSuffix": "%"},
            {"type": "fact", "text": "Hospitals use\nthe 'chargemaster' —\nno price regulation", "highlights": ["chargemaster", "no"]},
            {"type": "impact", "text": "Surgical gloves:\n$2,000\nat a US hospital", "highlights": ["$2,000"]},
            {"type": "fact", "text": "Same surgery:\n$10K vs $120K\nat different hospitals", "highlights": ["$10K", "$120K"]},
            {"type": "impact", "text": "The No Surprises Act\npassed in 2022.\nLoopholes remain.", "highlights": ["Loopholes"]},
            {"type": "cta", "text": "The most expensive\nhealthcare system\nin the world.", "highlights": ["expensive"]},
        ],
        "bg_sequence": ["scene_hospital","scene_money","scene_hospital","scene_money","scene_hospital","scene_money","scene_hospital"],
    },
    "S01097": {
        "title": "Quantum Computing Will Break All Encryption Within 10 Years",
        "category": "SHOCKING FACTS",
        "color_theme": "science",
        "script": (
            "Every encrypted message you have ever sent could be read in the future. "
            "A sufficiently powerful quantum computer will break RSA-2048 encryption — "
            "the standard protecting your bank account, your messages, state secrets — "
            "in hours instead of billions of years. "
            "Nation states are already collecting encrypted data today to decrypt it later. "
            "This strategy is called harvest now, decrypt later. "
            "China's quantum program received over fifteen billion dollars in government funding. "
            "NIST published its first post-quantum cryptography standards in 2024. "
            "The window to protect the world's data is closing. "
            "Everything encrypted before the transition could be exposed retroactively."
        ),
        "segments": [
            {"type": "hook", "text": "Every message\nyou ever sent\ncould be read.", "highlights": ["ever", "read"]},
            {"type": "fact", "text": "Quantum computers\nwill break RSA-2048\nin hours — not billions of years", "highlights": ["hours", "billions"]},
            {"type": "impact", "text": "Nations collecting\nencrypted data NOW\nto decrypt later", "highlights": ["NOW", "later"]},
            {"type": "number", "text": "invested in quantum by China's government", "highlights": [], "numberValue": 15, "numberPrefix": "$", "numberSuffix": "B"},
            {"type": "fact", "text": "NIST published\npost-quantum standards\nin 2024 — barely in time", "highlights": ["2024", "barely"]},
            {"type": "impact", "text": "All pre-transition\ndata could be\nexposed retroactively", "highlights": ["exposed", "retroactively"]},
            {"type": "cta", "text": "The clock\nstarted\nalready.", "highlights": ["clock", "already"]},
        ],
        "bg_sequence": ["scene_tech","scene_data","scene_tech","scene_data","scene_tech","scene_data","scene_tech"],
    },
    "S01113": {
        "title": "The Poisoning That Killed a City: Flint Michigan's Water Crisis",
        "category": "SHOCKING FACTS",
        "color_theme": "shocking",
        "script": (
            "In 2014, officials in Flint, Michigan switched the city's water source to cut costs. "
            "They knew the pipes would corrode. They switched anyway. "
            "One hundred thousand people — including eight thousand children — were poisoned with lead. "
            "Lead causes permanent brain damage in children. There is no safe level. There is no cure. "
            "Officials falsified test results to hide the contamination. "
            "Twelve people died of Legionnaire's disease from the same water. "
            "It took eighteen months before the state admitted there was a problem. "
            "Only three people went to prison. "
            "Ten years later, Flint residents still do not fully trust the water. "
            "The cost of the original decision to save money: one point eight billion dollars in settlements."
        ),
        "segments": [
            {"type": "hook", "text": "100,000 people\npoisoned to\nsave money.", "highlights": ["100,000", "poisoned", "money"]},
            {"type": "number", "text": "children poisoned with lead — permanent brain damage", "highlights": [], "numberValue": 8000, "numberSuffix": " children"},
            {"type": "impact", "text": "Officials KNEW\nthe pipes would corrode.\nThey switched anyway.", "highlights": ["KNEW", "anyway"]},
            {"type": "fact", "text": "Test results\nwere falsified\nfor 18 months", "highlights": ["falsified", "18 months"]},
            {"type": "impact", "text": "12 died.\nOnly 3 people\nwent to prison.", "highlights": ["12", "3"]},
            {"type": "number", "text": "in legal settlements — the cost of 'saving money'", "highlights": [], "numberValue": 1.8, "numberPrefix": "$", "numberSuffix": "B settlement"},
            {"type": "cta", "text": "Flint residents\nstill don't trust\nthe water.", "highlights": ["still", "trust"]},
        ],
        "bg_sequence": ["scene_city_aerial","scene_hospital","scene_city_aerial","scene_court","scene_city_aerial","scene_money","scene_city_aerial"],
    },
    "S01128": {
        "title": "Stuxnet: The Cyberweapon That Physically Destroyed Nuclear Centrifuges",
        "category": "SHOCKING FACTS",
        "color_theme": "power",
        "script": (
            "Stuxnet was not a normal computer virus. "
            "It was a physical weapon disguised as code. "
            "Jointly built by the United States and Israel under a program called Operation Olympic Games, "
            "it infiltrated Iran's Natanz nuclear facility and destroyed over one thousand uranium centrifuges — "
            "while displaying normal readings on the control screens. "
            "The operators had no idea anything was wrong until the machines physically failed. "
            "Stuxnet used four zero-day exploits — more than all known malware combined at the time. "
            "It was the first cyberweapon to cause real-world physical destruction. "
            "It changed warfare forever. "
            "Every critical infrastructure system in the world is now a potential target."
        ),
        "segments": [
            {"type": "hook", "text": "A virus that\nphysically destroyed\nnuclear machines.", "highlights": ["physically", "destroyed"]},
            {"type": "fact", "text": "Built by the US\nand Israel:\nOperation Olympic Games", "highlights": ["US", "Israel"]},
            {"type": "number", "text": "uranium centrifuges physically destroyed at Natanz", "highlights": [], "numberValue": 1000, "numberSuffix": "+ centrifuges"},
            {"type": "impact", "text": "Operators saw\nnormal readings\nwhile machines died", "highlights": ["normal", "died"]},
            {"type": "fact", "text": "4 zero-day exploits —\nmore than all\nknown malware combined", "highlights": ["4", "all"]},
            {"type": "impact", "text": "The first cyberweapon\nto cause physical\ndestruction in history", "highlights": ["first", "physical"]},
            {"type": "cta", "text": "Every power grid.\nEvery hospital.\nNow a target.", "highlights": ["Every"]},
        ],
        "bg_sequence": ["scene_tech","scene_data","scene_tech","scene_data","scene_tech","scene_data","scene_tech"],
    },
    "S01131": {
        "title": "The AI That Generates Fake Scientific Papers — And Journals That Publish Them",
        "category": "SHOCKING FACTS",
        "color_theme": "science",
        "script": (
            "In 2024, publisher Wiley retracted over one thousand scientific papers. "
            "Many were identified as AI-generated — complete with fabricated data, fake citations, and invented experiments. "
            "Researchers found a tell-tale sign: the phrase neural network had been replaced by fake brain organoid. "
            "An AI had translated the text — and the translation exposed it. "
            "Paper mills sell authorship slots in fake peer-reviewed journals for five hundred to ten thousand dollars. "
            "Real scientists are seeing their work copied, distorted, and republished by AI systems. "
            "Medical guidelines, engineering standards, and drug approvals all depend on published science being real. "
            "The foundation of scientific knowledge is being corrupted — "
            "and the systems designed to catch fraud were not built for this."
        ),
        "segments": [
            {"type": "hook", "text": "1,000 fake scientific\npapers published\nin real journals.", "highlights": ["1,000", "fake"]},
            {"type": "number", "text": "papers retracted by Wiley in 2024 — many AI-generated", "highlights": [], "numberValue": 1000, "numberSuffix": "+ papers"},
            {"type": "fact", "text": "'Neural network'\nbecame 'fake brain organoid' —\nAI translation exposed it", "highlights": ["fake brain organoid"]},
            {"type": "impact", "text": "Authorship in fake\njournals sold for\n$500–$10,000", "highlights": ["$500", "$10,000"]},
            {"type": "fact", "text": "Medical guidelines\nand drug approvals\ndepend on real science", "highlights": ["Medical", "drug"]},
            {"type": "impact", "text": "The systems to\ncatch fraud were not\nbuilt for AI", "highlights": ["not", "AI"]},
            {"type": "cta", "text": "The foundation of\nscience is being\ncorrupted.", "highlights": ["corrupted"]},
        ],
        "bg_sequence": ["scene_school","scene_tech","scene_school","scene_tech","scene_school","scene_tech","scene_school"],
    },
    "S01644": {
        "title": "Mansa Musa's Pilgrimage: The Day an African King Broke the Global Economy",
        "category": "SHOCKING FACTS",
        "color_theme": "wealth",
        "script": (
            "In 1324, the wealthiest human being who ever lived went on a road trip. "
            "Mansa Musa — Emperor of the Mali Empire — embarked on his hajj to Mecca. "
            "He brought sixty thousand men. "
            "Twelve thousand servants, each carrying one point eight kilograms of gold. "
            "Five hundred servants walked ahead of him, each holding a golden staff. "
            "When he passed through Cairo, he gave away so much gold "
            "that the price of gold across the entire Mediterranean crashed by twenty-five percent. "
            "It took twelve years for the economy to recover. "
            "His net worth in today's money: four hundred billion dollars. "
            "Richer than Elon Musk. Richer than Jeff Bezos. Richer than any human alive today. "
            "He accidentally caused a regional recession — by being too generous."
        ),
        "segments": [
            {"type": "hook", "text": "The richest human\nwho ever lived\ncrashed the economy.", "highlights": ["richest", "crashed"]},
            {"type": "number", "text": "net worth of Mansa Musa in today's money", "highlights": [], "numberValue": 400, "numberPrefix": "$", "numberSuffix": "B"},
            {"type": "fact", "text": "60,000 men.\n12,000 servants.\nEach carrying gold.", "highlights": ["60,000", "12,000"]},
            {"type": "impact", "text": "He gave away so much gold\nthe Mediterranean economy\ncollapsed 25%", "highlights": ["collapsed", "25%"]},
            {"type": "fact", "text": "Gold prices crashed.\nTook 12 years\nto recover.", "highlights": ["12 years", "recover"]},
            {"type": "impact", "text": "Richer than Musk.\nRicher than Bezos.\nRicher than anyone alive.", "highlights": ["Richer", "anyone"]},
            {"type": "cta", "text": "He caused a recession\nby being\ntoo generous.", "highlights": ["too generous"]},
        ],
        "bg_sequence": ["scene_city_aerial","scene_money","scene_city_aerial","scene_money","scene_city_aerial","scene_money","scene_city_aerial"],
    },
}


async def generate_audio(text: str, path: str):
    comm = edge_tts.Communicate(text, voice="en-US-AndrewNeural", rate="+8%")
    await comm.save(path)


def get_word_timestamps(audio_path: str):
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny", compute_type="int8")
    segs, _ = model.transcribe(audio_path, word_timestamps=True, language="en", beam_size=1)
    words = []
    for seg in segs:
        for w in (seg.words or []):
            words.append({"word": w.word.strip(), "start_ms": int(w.start * 1000), "end_ms": int(w.end * 1000)})
    return words


def build_props(vid_id: str, data: dict, words: list, duration_s: float) -> dict:
    fps = 60
    total_frames = int(duration_s * fps)
    segs = data["segments"]
    n = len(segs)
    frames_per_seg = total_frames // n
    remotion_segs = []
    for i, seg in enumerate(segs):
        start_f = i * frames_per_seg
        end_f = (i + 1) * frames_per_seg if i < n - 1 else total_frames
        bg = data["bg_sequence"][i] if i < len(data["bg_sequence"]) else None
        entry = {
            "type": seg["type"],
            "text": seg["text"],
            "startFrame": start_f,
            "endFrame": end_f,
            "highlightWords": seg.get("highlights", []),
        }
        if bg:
            entry["backgroundVideo"] = f"bg_videos/{bg}.mp4"
        if seg["type"] == "number":
            entry["numberValue"] = seg.get("numberValue", 0)
            entry["numberPrefix"] = seg.get("numberPrefix", "")
            entry["numberSuffix"] = seg.get("numberSuffix", "")
        remotion_segs.append(entry)

    return {
        "videoId": vid_id,
        "categoryLabel": data["category"],
        "colorTheme": data["color_theme"],
        "segments": remotion_segs,
        "audioFile": f"{vid_id}/audio.mp3",
        "backgroundVideoUrl": None,
        "wordTimestamps": words,
        "totalDurationFrames": total_frames,
        "scale": 1,
    }


def check_duration(audio_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", audio_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def main():
    render_commands = []

    for vid_id, data in VIDEOS.items():
        print("=" * 50)
        print(f"[{vid_id}] {data['title']}")

        out_dir = f"{BASE}/output/{vid_id}"
        os.makedirs(out_dir, exist_ok=True)

        # 1. Save script
        script_data = {
            "id": vid_id,
            "title": data["title"],
            "script": data["script"],
            "segments": data["segments"],
        }
        with open(f"{out_dir}/script.json", "w") as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        print("✓ script.json saved")

        # 2. Generate audio
        audio_path = f"{out_dir}/audio.mp3"
        print("→ Generating audio...")
        asyncio.run(generate_audio(data["script"], audio_path))
        duration_s = check_duration(audio_path)
        print(f"✓ audio.mp3 — {duration_s:.1f}s")

        # Duration gate
        if duration_s > 62:
            print(f"⚠️  WARNING: {duration_s:.1f}s exceeds 62s limit!")
        elif duration_s < 33:
            print(f"⚠️  WARNING: {duration_s:.1f}s is below 33s minimum!")

        # 3. Word timestamps
        print("→ Extracting word timestamps...")
        words = get_word_timestamps(audio_path)
        with open(f"{out_dir}/word_timestamps.json", "w") as f:
            json.dump(words, f, indent=2, ensure_ascii=False)
        print(f"✓ {len(words)} words timestamped")

        # 4. Build remotion_props.json
        props = build_props(vid_id, data, words, duration_s)
        with open(f"{out_dir}/remotion_props.json", "w") as f:
            json.dump(props, f, indent=2, ensure_ascii=False)
        print(f"✓ remotion_props.json — {props['totalDurationFrames']} frames")

        # 5. Copy to Remotion public
        pub_dir = f"{PUBLIC}/{vid_id}"
        os.makedirs(pub_dir, exist_ok=True)
        shutil.copy(audio_path, f"{pub_dir}/audio.mp3")
        print("✓ Copied to Remotion public")

        # Collect render command
        render_commands.append((vid_id, out_dir))

    # Generate render_queue_2.sh
    remotion_dir = f"{BASE}/video/remotion-project"
    sh_lines = ["#!/bin/bash", "set -e", f'cd "{remotion_dir}"', ""]
    for vid_id, out_dir in render_commands:
        noaudio = f"{out_dir}/video_noaudio.mp4"
        final = f"{out_dir}/video.mp4"
        audio = f"{out_dir}/audio.mp3"
        props = f"{out_dir}/remotion_props.json"
        sh_lines.append(f'echo "=== Rendering {vid_id} ===" && ./node_modules/.bin/remotion render src/index.ts ShortVideo "{noaudio}" --props="{props}" --codec=h264 --concurrency=4 && echo "✓ Render done {vid_id}" && ffmpeg -i "{noaudio}" -i "{audio}" -c:v copy -c:a aac -b:a 256k -shortest "{final}" -y && echo "✓ Merge done {vid_id}"')
        sh_lines.append("")

    sh_lines.append('python3 scripts/batch_finalize_2.py')
    sh_path = f"{BASE}/scripts/render_queue_2.sh"
    with open(sh_path, "w") as f:
        f.write("\n".join(sh_lines))
    os.chmod(sh_path, 0o755)
    print(f"\n✓ render_queue_2.sh generated")
    print("\n✅ Batch 2 audio pipeline complete — run: bash scripts/render_queue_2.sh")


if __name__ == "__main__":
    main()
