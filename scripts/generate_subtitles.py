"""
generate_subtitles.py — Generate SRT subtitle files for 7 languages from word timestamps.

Reads:  output/{video_id}/word_timestamps.json  (list of {word, start_ms, end_ms})
Writes: output/{video_id}/subtitles/{video_id}_{lang}.srt  for EN + 6 other languages

Translation: Google Translate free endpoint (no API key required).
Languages: en, ar, es, fr, hi, pt, tr

Usage: python3 scripts/generate_subtitles.py <video_id>
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Max words per subtitle segment
MAX_WORDS = 6
# Natural pause threshold in ms — split segment here even if under MAX_WORDS
PAUSE_THRESHOLD_MS = 400

LANGUAGES = {
    "ar": "Arabic",
    "es": "Spanish",
    "fr": "French",
    "hi": "Hindi",
    "pt": "Portuguese",
    "tr": "Turkish",
}


# ─── SRT helpers ──────────────────────────────────────────────────────────────

def ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours   = ms // 3_600_000
    ms     -= hours * 3_600_000
    minutes = ms // 60_000
    ms     -= minutes * 60_000
    seconds = ms // 1000
    millis  = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def group_words_into_segments(word_timestamps: list) -> list:
    """
    Group word timestamps into subtitle segments.

    A new segment starts when:
    - MAX_WORDS words have accumulated, OR
    - The gap between consecutive words exceeds PAUSE_THRESHOLD_MS

    Returns list of {text, start_ms, end_ms}.
    """
    segments = []
    if not word_timestamps:
        return segments

    current_words = []
    seg_start_ms  = None

    for i, wt in enumerate(word_timestamps):
        word     = wt.get("word", "").strip()
        start_ms = int(wt.get("start_ms", 0))
        end_ms   = int(wt.get("end_ms", 0))

        if not word:
            continue

        # First word in a new segment
        if seg_start_ms is None:
            seg_start_ms = start_ms

        current_words.append(word)
        last_end_ms = end_ms

        # Check if we should close this segment
        flush = False
        if len(current_words) >= MAX_WORDS:
            flush = True
        elif i + 1 < len(word_timestamps):
            next_start = int(word_timestamps[i + 1].get("start_ms", 0))
            gap = next_start - end_ms
            if gap >= PAUSE_THRESHOLD_MS:
                flush = True
        else:
            # Last word
            flush = True

        if flush:
            segments.append({
                "text":     " ".join(current_words),
                "start_ms": seg_start_ms,
                "end_ms":   last_end_ms,
            })
            current_words = []
            seg_start_ms  = None

    # Flush any remaining words
    if current_words and seg_start_ms is not None:
        segments.append({
            "text":     " ".join(current_words),
            "start_ms": seg_start_ms,
            "end_ms":   last_end_ms,
        })

    return segments


def segments_to_srt(segments: list) -> str:
    """Convert segment list to SRT file content string."""
    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{ms_to_srt_time(seg['start_ms'])} --> {ms_to_srt_time(seg['end_ms'])}")
        lines.append(seg["text"])
        lines.append("")  # blank line between entries
    return "\n".join(lines)


# ─── Translation ──────────────────────────────────────────────────────────────

def translate_text(text: str, target_lang: str, retries: int = 3) -> str:
    """
    Translate text using Google Translate free endpoint.
    No API key required.

    Args:
        text:        Source text in English.
        target_lang: BCP-47 language code, e.g. "ar", "fr".
        retries:     Number of retry attempts on network error.

    Returns:
        Translated string, or original text on failure.
    """
    encoded = urllib.parse.quote(text)
    url = (
        f"https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl={target_lang}&dt=t&q={encoded}"
    )

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # Response format: [[["translated", "original", ...], ...], ...]
            parts = [item[0] for item in data[0] if item[0]]
            return "".join(parts)
        except Exception as exc:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"    [translate:{target_lang}] attempt {attempt+1} failed ({exc}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [translate:{target_lang}] failed after {retries} attempts: {exc}")
                return text  # fall back to original

    return text


def translate_segments(segments: list, target_lang: str) -> list:
    """
    Return a copy of segments with text translated to target_lang.
    Sends requests in small batches to avoid URL length limits.
    """
    translated = []
    batch_size = 10

    for i in range(0, len(segments), batch_size):
        batch = segments[i : i + batch_size]
        for seg in batch:
            tr_text = translate_text(seg["text"], target_lang)
            translated.append({**seg, "text": tr_text})
        # Brief pause between batches to avoid rate limiting
        if i + batch_size < len(segments):
            time.sleep(0.3)

    return translated


# ─── Main ─────────────────────────────────────────────────────────────────────

def generate_subtitles(video_id: str) -> bool:
    """
    Full subtitle generation pipeline for one video.

    Returns True on success, False on missing input.
    """
    out_dir   = ROOT / "output" / video_id
    ts_path   = out_dir / "word_timestamps.json"
    subs_dir  = out_dir / "subtitles"

    if not ts_path.exists():
        print(f"❌ word_timestamps.json not found for {video_id}")
        return False

    word_timestamps = json.loads(ts_path.read_text())
    if not word_timestamps:
        print(f"❌ word_timestamps.json is empty for {video_id}")
        return False

    subs_dir.mkdir(parents=True, exist_ok=True)

    # ── English SRT (source, no translation needed) ──────────────────────────
    print(f"  Grouping {len(word_timestamps)} words into subtitle segments...")
    segments = group_words_into_segments(word_timestamps)
    print(f"  → {len(segments)} segments created")

    en_srt = segments_to_srt(segments)
    en_path = subs_dir / f"{video_id}_en.srt"
    en_path.write_text(en_srt, encoding="utf-8")
    print(f"  ✅ EN → {en_path.name}")

    # ── Translated SRTs ───────────────────────────────────────────────────────
    for lang_code, lang_name in LANGUAGES.items():
        print(f"  Translating to {lang_name} ({lang_code})...")
        tr_segments = translate_segments(segments, lang_code)
        srt_content = segments_to_srt(tr_segments)
        srt_path    = subs_dir / f"{video_id}_{lang_code}.srt"
        srt_path.write_text(srt_content, encoding="utf-8")
        print(f"  ✅ {lang_code.upper()} → {srt_path.name}")

    print(f"\n✅ Subtitles ready: {subs_dir}")
    return True


if __name__ == "__main__":
    video_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not video_id:
        print("Usage: python3 scripts/generate_subtitles.py <video_id>")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"Generating subtitles for {video_id}")
    print(f"{'='*50}\n")

    ok = generate_subtitles(video_id)
    sys.exit(0 if ok else 1)
