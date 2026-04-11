"""
Text Cleaner — Prepares scripts for TTS processing
Strips tags, expands abbreviations, converts numbers to words.
"""

import re
from num2words import num2words


# Abbreviations to always expand for TTS
ABBREVIATIONS = {
    r"\bUS\b": "United States",
    r"\bUK\b": "United Kingdom",
    r"\bUAE\b": "United Arab Emirates",
    r"\bGDP\b": "gross domestic product",
    r"\bGNP\b": "gross national product",
    r"\bIMF\b": "International Monetary Fund",
    r"\bUN\b": "United Nations",
    r"\bNATO\b": "NATO",          # spoken as word — keep
    r"\bNASA\b": "NASA",          # spoken as word — keep
    r"\bFIFA\b": "FIFA",          # spoken as word — keep
    r"\bCEO\b": "chief executive officer",
    r"\bCFO\b": "chief financial officer",
    r"\bGDP\b": "gross domestic product",
    r"\bBC\b": "Before Christ",
    r"\bAD\b": "Anno Domini",
    r"\bBCE\b": "Before Common Era",
    r"\bCE\b": "Common Era",
    r"\bWW1\b": "World War One",
    r"\bWW2\b": "World War Two",
    r"\bWWI\b": "World War One",
    r"\bWWII\b": "World War Two",
    r"\bSq\b": "square",
    r"\bkm\b": "kilometers",
    r"\bkg\b": "kilograms",
    r"\bmph\b": "miles per hour",
    r"\bkph\b": "kilometers per hour",
    r"\bkm2\b": "square kilometers",
}

# TTS script tags to process
PAUSE_TAG = "[PAUSE]"
BREAK_TAG = "[BREAK]"
SLOW_TAG = "[SLOW]"
FAST_TAG = "[FAST]"
EMPHASIS_TAGS = [SLOW_TAG, FAST_TAG]


def remove_script_tags(text: str) -> str:
    """Strip all [TAG] markers from script text, leaving clean speech."""
    for tag in [PAUSE_TAG, BREAK_TAG, SLOW_TAG, FAST_TAG]:
        text = text.replace(tag, " ")
    return re.sub(r'\s+', ' ', text).strip()


def expand_abbreviations(text: str) -> str:
    """Replace abbreviations with full spoken forms."""
    for pattern, replacement in ABBREVIATIONS.items():
        text = re.sub(pattern, replacement, text)
    return text


def convert_currency(text: str) -> str:
    """Convert currency symbols to words: $400B → four hundred billion dollars"""
    # Handle billions
    text = re.sub(
        r'\$(\d+(?:\.\d+)?)\s*(?:billion|B)\b',
        lambda m: f"{_num_to_words(float(m.group(1)))} billion dollars",
        text, flags=re.IGNORECASE
    )
    # Handle trillions
    text = re.sub(
        r'\$(\d+(?:\.\d+)?)\s*(?:trillion|T)\b',
        lambda m: f"{_num_to_words(float(m.group(1)))} trillion dollars",
        text, flags=re.IGNORECASE
    )
    # Handle millions
    text = re.sub(
        r'\$(\d+(?:\.\d+)?)\s*(?:million|M)\b',
        lambda m: f"{_num_to_words(float(m.group(1)))} million dollars",
        text, flags=re.IGNORECASE
    )
    # Handle plain dollar amounts under 1000
    text = re.sub(
        r'\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\b',
        lambda m: f"{_num_to_words(float(m.group(1).replace(',', '')))} dollars",
        text
    )
    return text


def convert_percentages(text: str) -> str:
    """Convert percentages: 25% → twenty-five percent"""
    return re.sub(
        r'(\d+(?:\.\d+)?)\s*%',
        lambda m: f"{_num_to_words(float(m.group(1)))} percent",
        text
    )


def _num_to_words(n: float) -> str:
    """Convert a number to its spoken-word form."""
    try:
        if n == int(n):
            return num2words(int(n))
        return num2words(n)
    except Exception:
        return str(n)


def convert_numbers_in_text(text: str) -> str:
    """Convert standalone numbers to words (when they appear isolated)."""
    # Convert large numbers with commas: 1,000,000 → one million
    text = re.sub(
        r'\b(\d{1,3}(?:,\d{3})+)\b',
        lambda m: _num_to_words(float(m.group(1).replace(',', ''))),
        text
    )
    return text


def clean_punctuation_for_tts(text: str) -> str:
    """Remove punctuation that TTS engines read aloud incorrectly."""
    text = text.replace("...", " ")
    text = text.replace(";", ",")
    text = text.replace(":", ",")
    text = text.replace("&", " and ")
    text = re.sub(r'#{1,6}\s', '', text)  # Markdown headers
    text = re.sub(r'\*+', '', text)        # Markdown bold/italic
    text = re.sub(r'_+', '', text)         # Underscores
    text = re.sub(r'\[.*?\]', '', text)    # Markdown links
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def prepare_for_tts(script: str) -> str:
    """
    Full pipeline: takes a raw script with tags and returns clean TTS-ready text.
    """
    text = remove_script_tags(script)
    text = expand_abbreviations(text)
    text = convert_currency(text)
    text = convert_percentages(text)
    text = convert_numbers_in_text(text)
    text = clean_punctuation_for_tts(text)
    return text


def extract_pause_positions(script: str) -> list[dict]:
    """
    Extract pause positions from script with [PAUSE] and [BREAK] tags.
    Returns list of {position: int, duration: float} for audio processing.
    """
    pauses = []
    pos = 0
    clean = ""

    for part in re.split(r'(\[PAUSE\]|\[BREAK\])', script):
        if part == PAUSE_TAG:
            pauses.append({"position": len(clean), "duration": 0.5})
        elif part == BREAK_TAG:
            pauses.append({"position": len(clean), "duration": 1.0})
        else:
            # Strip other tags before measuring position
            cleaned = remove_script_tags(part)
            clean += cleaned

    return pauses
