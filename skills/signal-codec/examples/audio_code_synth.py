#!/usr/bin/env python3
"""Program-generated audio: a note string becomes a WAV through additive synthesis.

No model, no network. The LLM (or the user) writes the score as text; code renders it.
Score syntax, space separated, one token per event:
  C4:0.5     note name + duration in beats      (sharps: F#4, flats: Bb3)
  C4+E4+G4:1 chord (notes joined with +)
  R:0.5      rest
  K:1        kick drum   S:1  snare-like noise burst
Deps: numpy, soundfile.   Run: python audio_code_synth.py out.wav --bpm 100 "C4:1 E4:1 G4:1 C4+E4+G4:2"
"""
import argparse
import numpy as np
import soundfile as sf

SR = 44100
SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_freq(name: str) -> float:
    n = SEMITONE[name[0].upper()]
    rest = name[1:]
    if rest.startswith("#"):
        n, rest = n + 1, rest[1:]
    elif rest.startswith("b"):
        n, rest = n - 1, rest[1:]
    midi = 12 * (int(rest) + 1) + n          # C4 = 60
    return 440.0 * 2 ** ((midi - 69) / 12)


def adsr(n: int, a=0.01, d=0.08, s=0.6, r=0.1) -> np.ndarray:
    a, d, r = (min(int(v * SR), n // 3) for v in (a, d, r))
    env = np.full(n, s)
    env[:a] = np.linspace(0, 1, a, endpoint=False)
    env[a:a + d] = np.linspace(1, s, d, endpoint=False)
    env[n - r:] = np.linspace(s, 0, r)
    return env


def tone(freq: float, seconds: float) -> np.ndarray:
    t = np.arange(int(SR * seconds)) / SR
    harmonics = [1.0, 0.5, 0.25, 0.12]       # additive: fundamental + 3 overtones
    y = sum(h * np.sin(2 * np.pi * freq * (i + 1) * t) for i, h in enumerate(harmonics))
    return y / sum(harmonics) * adsr(len(t))


def kick(seconds: float) -> np.ndarray:
    t = np.arange(int(SR * min(seconds, 0.3))) / SR
    return np.sin(2 * np.pi * (150 * t - 400 * t**2 / 2).clip(min=0)) * np.exp(-t * 18)


def snare(seconds: float, rng) -> np.ndarray:
    t = np.arange(int(SR * min(seconds, 0.2))) / SR
    return rng.standard_normal(len(t)) * np.exp(-t * 25) * 0.6


def render(score: str, bpm: float) -> np.ndarray:
    beat = 60.0 / bpm
    rng = np.random.default_rng(0)
    parts = []
    for token in score.split():
        what, dur = token.rsplit(":", 1)
        seconds = float(dur) * beat
        n = int(SR * seconds)
        if what == "R":
            y = np.zeros(n)
        elif what == "K":
            y = kick(seconds)
        elif what == "S":
            y = snare(seconds, rng)
        else:
            y = sum(tone(note_freq(p), seconds) for p in what.split("+")) / len(what.split("+"))
        parts.append(np.pad(y, (0, max(0, n - len(y))))[:n])
    return np.concatenate(parts)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output")
    ap.add_argument("score")
    ap.add_argument("--bpm", type=float, default=100)
    args = ap.parse_args()
    y = render(args.score, args.bpm)
    peak = np.max(np.abs(y))
    y = 0.8 * y / peak if peak > 0 else y
    sf.write(args.output, y, SR, subtype="PCM_16")
    print(f"wrote {args.output}: {len(y) / SR:.2f}s, sr={SR}")
