#!/usr/bin/env python3
"""
FactForge — SFX Asset Generator
Generates all procedural sound effects and saves them as WAV files.
Run once to populate audio_engineering/assets/sfx/**/*.wav

Usage:
    python3 audio_engineering/generate_sfx.py
    python3 audio_engineering/generate_sfx.py --topic ocean
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

BASE = Path(__file__).parent
SFX_DIR = BASE / "assets" / "sfx"
SR = 44100  # sample rate


# ─────────────────────────────────────────────────────────────────────────────
# UNIVERSAL BUILDING BLOCKS
# ─────────────────────────────────────────────────────────────────────────────

def envelope(length, attack=0.01, decay=0.1, sustain=0.8, release=0.2, sr=SR):
    """ADSR envelope."""
    n = int(length * sr)
    env = np.zeros(n)
    a = int(attack * sr)
    d = int(decay * sr)
    r = int(release * sr)
    s_len = max(0, n - a - d - r)
    if a: env[:a] = np.linspace(0, 1, a)
    if d: env[a:a+d] = np.linspace(1, sustain, d)
    if s_len: env[a+d:a+d+s_len] = sustain
    if r: env[a+d+s_len:] = np.linspace(sustain, 0, r)
    return env


def sine(freq, duration, sr=SR):
    t = np.linspace(0, duration, int(sr * duration))
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def noise(duration, sr=SR):
    return np.random.uniform(-1, 1, int(sr * duration)).astype(np.float32)


def lowpass(signal, cutoff=800, sr=SR):
    """Simple one-pole lowpass filter."""
    rc = 1.0 / (2 * np.pi * cutoff)
    dt = 1.0 / sr
    alpha = dt / (rc + dt)
    out = np.zeros_like(signal)
    out[0] = signal[0]
    for i in range(1, len(signal)):
        out[i] = out[i-1] + alpha * (signal[i] - out[i-1])
    return out


def save(data: np.ndarray, path: Path, normalize: bool = True):
    if normalize:
        peak = np.max(np.abs(data))
        if peak > 0:
            data = (data / peak * 0.90).astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), data, SR)
    print(f"  ✓ {path.relative_to(BASE)} ({len(data)/SR:.2f}s)")


# ─────────────────────────────────────────────────────────────────────────────
# OCEAN THEME
# ─────────────────────────────────────────────────────────────────────────────

def make_sonar_ping():
    """Deep sonar ping — for stat/number reveals in ocean videos."""
    dur = 0.8
    t = np.linspace(0, dur, int(SR * dur))
    # Two-tone sonar: 1200Hz + 800Hz with decay
    wave = np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 6)
    wave += np.sin(2 * np.pi * 800 * t) * np.exp(-t * 10) * 0.5
    # Add short reverb tail
    reverb = np.zeros(int(SR * 1.2))
    reverb[:len(wave)] = wave
    for delay in [0.12, 0.25, 0.45]:
        start = int(delay * SR)
        end = min(start + len(wave), len(reverb))
        l = end - start
        reverb[start:end] += wave[:l] * (0.3 * np.exp(-delay * 3))
    return reverb.astype(np.float32)


def make_bubble_burst():
    """Rising bubble sound — hook/reveal moment."""
    dur = 0.5
    t = np.linspace(0, dur, int(SR * dur))
    # Frequency rises fast (bubble rising)
    freq = np.linspace(200, 1800, len(t))
    phase = np.cumsum(2 * np.pi * freq / SR)
    wave = np.sin(phase)
    env = np.exp(-t * 5) * (1 - np.exp(-t * 60))
    return (wave * env).astype(np.float32)


def make_pressure_boom():
    """Deep underwater pressure impact — for shocking stat moments."""
    dur = 1.2
    # Sub-bass thud
    t_boom = np.linspace(0, 0.3, int(SR * 0.3))
    boom = np.sin(2 * np.pi * 45 * t_boom) * np.exp(-t_boom * 8)
    # Followed by rumble
    t_rumble = np.linspace(0, 0.9, int(SR * 0.9))
    rumble = lowpass(noise(0.9) * 0.3, cutoff=120) * np.exp(-t_rumble * 4)
    full = np.concatenate([boom, rumble]).astype(np.float32)
    return full


def make_water_transition():
    """Underwater whoosh — scene transition in ocean videos."""
    dur = 0.45
    t = np.linspace(0, dur, int(SR * dur))
    # Rising + falling sweep with water character
    freq = 180 * np.exp(t * 3) * (1 - t / dur * 0.7)
    phase = np.cumsum(2 * np.pi * freq / SR)
    sweep = np.sin(phase)
    # Add filtered noise for water texture
    water_noise = lowpass(noise(dur), cutoff=500) * 0.4
    wave = sweep + water_noise
    env = np.sin(np.pi * t / dur)  # bell envelope
    return (wave * env).astype(np.float32)


def make_depth_tone():
    """Slow, heavy low tone — used on large numbers in ocean context."""
    dur = 1.0
    t = np.linspace(0, dur, int(SR * dur))
    wave = np.sin(2 * np.pi * 55 * t) + np.sin(2 * np.pi * 82 * t) * 0.6
    env = envelope(dur, attack=0.05, decay=0.1, sustain=0.6, release=0.35)
    return (wave * env).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# SPACE THEME
# ─────────────────────────────────────────────────────────────────────────────

def make_sci_fi_beep():
    """Clean electronic beep for space/tech number reveals."""
    dur = 0.3
    t = np.linspace(0, dur, int(SR * dur))
    wave = np.sin(2 * np.pi * 880 * t) + np.sin(2 * np.pi * 1320 * t) * 0.4
    env = np.exp(-t * 12)
    return (wave * env).astype(np.float32)


def make_space_whoosh():
    """Thin, airy whoosh for space transitions."""
    dur = 0.5
    t = np.linspace(0, dur, int(SR * dur))
    freq = np.linspace(3000, 200, len(t))
    phase = np.cumsum(2 * np.pi * freq / SR)
    sweep = np.sin(phase) * 0.3
    air = lowpass(noise(dur) * 0.6, cutoff=3000)
    wave = (sweep + air) * np.sin(np.pi * t / dur)
    return wave.astype(np.float32)


def make_space_thud():
    """Deep space impact — no air, pure sub-bass."""
    dur = 1.0
    t = np.linspace(0, dur, int(SR * dur))
    wave = np.sin(2 * np.pi * 35 * t) * np.exp(-t * 6)
    wave += np.sin(2 * np.pi * 60 * t) * np.exp(-t * 9) * 0.5
    return wave.astype(np.float32)


def make_radio_static():
    """Short radio static burst — space/tech atmosphere."""
    dur = 0.2
    n = lowpass(noise(dur), cutoff=4000)
    env = np.ones(int(SR * dur))
    env[:int(SR * 0.02)] = np.linspace(0, 1, int(SR * 0.02))
    env[-int(SR * 0.05):] = np.linspace(1, 0, int(SR * 0.05))
    return (n * env * 0.7).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# ECONOMY / WEALTH THEME
# ─────────────────────────────────────────────────────────────────────────────

def make_coin_drop():
    """Single coin drop — stat reveal in economy videos."""
    dur = 0.4
    t = np.linspace(0, dur, int(SR * dur))
    # Metallic ring: harmonics of ~1500Hz
    wave = (
        np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 18)
        + np.sin(2 * np.pi * 2800 * t) * np.exp(-t * 30) * 0.4
        + np.sin(2 * np.pi * 4200 * t) * np.exp(-t * 45) * 0.2
    )
    # Impact click at start
    click_len = int(SR * 0.01)
    wave[:click_len] += noise(0.01)[:click_len] * 0.8
    return wave.astype(np.float32)


def make_cash_register():
    """Cash register ding — for money/wealth moments."""
    dur = 0.6
    # Classic "cha-ching": two tones
    t1 = np.linspace(0, 0.15, int(SR * 0.15))
    t2 = np.linspace(0, 0.4, int(SR * 0.4))
    ching1 = np.sin(2 * np.pi * 1760 * t1) * np.exp(-t1 * 15)
    ching2 = np.sin(2 * np.pi * 2200 * t2) * np.exp(-t2 * 8)
    gap = np.zeros(int(SR * 0.05))
    wave = np.concatenate([ching1, gap, ching2])
    return wave.astype(np.float32)


def make_market_crash():
    """Descending crash tone — for shocking negative financial stats."""
    dur = 1.0
    t = np.linspace(0, dur, int(SR * dur))
    freq = np.linspace(800, 80, len(t))
    phase = np.cumsum(2 * np.pi * freq / SR)
    sweep = np.sin(phase) * np.exp(-t * 3)
    rumble = lowpass(noise(dur) * 0.3, cutoff=200) * np.exp(-t * 2)
    return (sweep + rumble).astype(np.float32)


def make_money_whoosh():
    """Paper money/bills sound — transition in economy context."""
    dur = 0.35
    t = np.linspace(0, dur, int(SR * dur))
    # High-freq paper rustle + air movement
    paper = lowpass(noise(dur) * 0.5, cutoff=6000) - lowpass(noise(dur) * 0.5, cutoff=200)
    freq = np.linspace(400, 2000, len(t))
    phase = np.cumsum(2 * np.pi * freq / SR)
    sweep = np.sin(phase) * 0.2
    env = np.sin(np.pi * t / dur)
    return ((paper + sweep) * env).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# TECHNOLOGY / AI THEME
# ─────────────────────────────────────────────────────────────────────────────

def make_digital_glitch():
    """Digital glitch burst — scene change in tech videos."""
    dur = 0.25
    t = np.linspace(0, dur, int(SR * dur))
    # Rapid frequency hopping
    freqs = [440, 880, 1760, 220, 3520]
    chunk = len(t) // len(freqs)
    wave = np.zeros(len(t))
    for i, f in enumerate(freqs):
        start = i * chunk
        end = min(start + chunk, len(t))
        tc = t[start:end] - t[start]
        wave[start:end] = np.sin(2 * np.pi * f * tc)
    # Add digital noise bursts
    wave += noise(dur) * 0.15
    env = np.ones(len(t))
    env[-int(SR * 0.05):] = np.linspace(1, 0, int(SR * 0.05))
    return (wave * env * 0.6).astype(np.float32)


def make_keyboard_click():
    """Mechanical keyboard click — number reveals in tech."""
    dur = 0.08
    t = np.linspace(0, dur, int(SR * dur))
    wave = noise(dur)
    wave[:int(SR * 0.005)] *= 3  # sharp attack
    env = np.exp(-t * 60)
    filtered = lowpass(wave * env, cutoff=5000)
    return filtered.astype(np.float32)


def make_system_alert():
    """System alert tone — impact moments in tech."""
    dur = 0.5
    t = np.linspace(0, dur, int(SR * dur))
    # Three rapid beeps
    wave = np.zeros(len(t))
    for i, start_t in enumerate([0, 0.12, 0.24]):
        start = int(start_t * SR)
        beep_len = int(0.08 * SR)
        if start + beep_len > len(wave):
            break
        tb = t[start:start + beep_len] - t[start]
        wave[start:start + beep_len] = np.sin(2 * np.pi * 1047 * tb) * np.exp(-tb * 30)
    return wave.astype(np.float32)


def make_tech_whoosh():
    """Fast digital sweep — tech scene transitions."""
    dur = 0.3
    t = np.linspace(0, dur, int(SR * dur))
    freq = np.exp(np.linspace(np.log(100), np.log(4000), len(t)))
    phase = np.cumsum(2 * np.pi * freq / SR)
    sweep = np.sin(phase) * 0.5
    digital = (noise(dur) * 0.3 * np.sin(np.pi * t / dur))
    return (sweep + digital).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# HISTORY THEME
# ─────────────────────────────────────────────────────────────────────────────

def make_bell_toll():
    """Ancient bell toll — scene change in history videos."""
    dur = 1.5
    t = np.linspace(0, dur, int(SR * dur))
    wave = (
        np.sin(2 * np.pi * 220 * t) * np.exp(-t * 2.5)
        + np.sin(2 * np.pi * 440 * t) * np.exp(-t * 3.5) * 0.5
        + np.sin(2 * np.pi * 660 * t) * np.exp(-t * 5) * 0.25
    )
    return wave.astype(np.float32)


def make_typewriter_click():
    """Typewriter click — stat reveal in history."""
    dur = 0.1
    t = np.linspace(0, dur, int(SR * dur))
    wave = noise(dur)
    env = np.exp(-t * 50) * 1.5
    env[:int(SR * 0.003)] = np.linspace(0, 1, int(SR * 0.003)) * 2
    return (wave * env).astype(np.float32)


def make_dramatic_sting():
    """Short orchestral sting — impact moments in history."""
    dur = 0.8
    t = np.linspace(0, dur, int(SR * dur))
    # Brass-like: fundamental + harmonics
    wave = (
        np.sin(2 * np.pi * 110 * t)
        + np.sin(2 * np.pi * 220 * t) * 0.6
        + np.sin(2 * np.pi * 330 * t) * 0.3
        + np.sin(2 * np.pi * 440 * t) * 0.15
    )
    env = envelope(dur, attack=0.02, decay=0.1, sustain=0.7, release=0.3)
    return (wave * env).astype(np.float32)


def make_parchment_rustle():
    """Paper/parchment rustle — transitions in history."""
    dur = 0.4
    t = np.linspace(0, dur, int(SR * dur))
    n = lowpass(noise(dur), cutoff=4000) - lowpass(noise(dur), cutoff=300)
    env = np.sin(np.pi * t / dur)
    return (n * env * 0.6).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# UNIVERSAL / GENERIC
# ─────────────────────────────────────────────────────────────────────────────

def make_soft_whoosh():
    """Generic soft whoosh — neutral transitions."""
    dur = 0.35
    t = np.linspace(0, dur, int(SR * dur))
    freq = np.linspace(150, 1200, len(t))
    phase = np.cumsum(2 * np.pi * freq / SR)
    wave = np.sin(phase)
    env = np.sin(np.pi * t / dur)
    return (wave * env * 0.5).astype(np.float32)


def make_hard_impact():
    """Heavy thud — universal impact."""
    dur = 0.6
    t = np.linspace(0, dur, int(SR * dur))
    wave = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 10)
    wave += lowpass(noise(dur) * 0.4, cutoff=300) * np.exp(-t * 8)
    return wave.astype(np.float32)


def make_reveal_sting():
    """Rising tone — information reveal moment."""
    dur = 0.5
    t = np.linspace(0, dur, int(SR * dur))
    freq = np.linspace(300, 900, len(t))
    phase = np.cumsum(2 * np.pi * freq / SR)
    wave = np.sin(phase) + np.sin(phase * 1.5) * 0.3
    env = envelope(dur, attack=0.05, decay=0.05, sustain=0.8, release=0.2)
    return (wave * env).astype(np.float32)


def make_tension_build():
    """Short tension builder — before a big reveal."""
    dur = 0.8
    t = np.linspace(0, dur, int(SR * dur))
    # Low freq oscillation that slowly rises
    freq = np.linspace(80, 140, len(t))
    phase = np.cumsum(2 * np.pi * freq / SR)
    wave = np.sin(phase) * 0.6
    wave += lowpass(noise(dur) * 0.2, cutoff=400)
    env = np.linspace(0, 1, len(t))
    return (wave * env).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# BUILD ALL ASSETS
# ─────────────────────────────────────────────────────────────────────────────

ASSETS = {
    "ocean": [
        ("sonar_ping",       make_sonar_ping),
        ("bubble_burst",     make_bubble_burst),
        ("pressure_boom",    make_pressure_boom),
        ("water_transition", make_water_transition),
        ("depth_tone",       make_depth_tone),
    ],
    "space": [
        ("sci_fi_beep",   make_sci_fi_beep),
        ("space_whoosh",  make_space_whoosh),
        ("space_thud",    make_space_thud),
        ("radio_static",  make_radio_static),
    ],
    "economy": [
        ("coin_drop",     make_coin_drop),
        ("cash_register", make_cash_register),
        ("market_crash",  make_market_crash),
        ("money_whoosh",  make_money_whoosh),
    ],
    "tech": [
        ("digital_glitch",  make_digital_glitch),
        ("keyboard_click",  make_keyboard_click),
        ("system_alert",    make_system_alert),
        ("tech_whoosh",     make_tech_whoosh),
    ],
    "history": [
        ("bell_toll",         make_bell_toll),
        ("typewriter_click",  make_typewriter_click),
        ("dramatic_sting",    make_dramatic_sting),
        ("parchment_rustle",  make_parchment_rustle),
    ],
    "universal": [
        ("soft_whoosh",   make_soft_whoosh),
        ("hard_impact",   make_hard_impact),
        ("reveal_sting",  make_reveal_sting),
        ("tension_build", make_tension_build),
    ],
}


def build_all(topic_filter: str = None):
    total = 0
    for topic, sounds in ASSETS.items():
        if topic_filter and topic != topic_filter:
            continue
        print(f"\n[{topic.upper()}]")
        for name, fn in sounds:
            path = SFX_DIR / topic / f"{name}.wav"
            if path.exists():
                print(f"  ✓ {name}.wav (exists — skipping)")
                continue
            data = fn()
            save(data, path)
            total += 1
    print(f"\n✅ Generated {total} new SFX files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", help="Only generate SFX for this topic")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    if args.force:
        # Remove existing to force regeneration
        for wav in SFX_DIR.rglob("*.wav"):
            wav.unlink()

    build_all(args.topic)
