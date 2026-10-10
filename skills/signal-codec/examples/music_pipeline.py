#!/usr/bin/env python3
"""Layered music generation: score -> MIDI -> per-part render -> loudness align -> FX -> master.

A compact version of the approach in https://github.com/komiyoo/musician (MIT):
composition and timbre are separate. The LLM (or the user) writes a small JSON score;
code expands it to MIDI, renders each part, aligns each stem to a loudness target,
adds per-part effects and masters the sum.

  1. score   chords per bar + parts with a role  ->  midi/<part>.mid + midi/full.mid
  2. render  FluidSynth + SoundFont when --soundfont is given and `fluidsynth` exists,
             otherwise a numpy draft synth (same notes, draft timbre)
  3. loudness  each stem -> its role's LUFS target (pyloudnorm, ITU-R BS.1770)
  4. fx/master pedalboard: high-pass, optional voice pocket, reverb; master LUFS + peak ceiling

Subcommands:
  render SPEC.json OUTDIR [--soundfont X.sf2] [--narration]
  sonify DATA.csv OUTDIR --column value [--bars 8]     data -> melody (sonification), then render

Score spec:
  {"bpm": 100, "seed": 7, "master_lufs": -16,
   "chords": ["Dm", "Bb", "F", "C"],                     one chord per 4/4 bar
   "parts": {
     "pad":   {"role": "pad"},
     "bass":  {"role": "bass"},
     "arp":   {"role": "arp", "from_bar": 2},            0-based bar index
     "lead":  {"role": "melody", "notes": [["A4", 0, 1], ["D5", 1, 2, 90]]},  [pitch, beat, beats, vel?]
     "drums": {"role": "drums", "from_bar": 2}}}
Chord symbols: C, Cm, Cdim, Csus4, C7, Cm7, Cmaj7 (with # or b on the root).

Deps: numpy, soundfile, mido, pyloudnorm, pedalboard.  FluidSynth CLI + an SF2/SF3 file are optional.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

import mido
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from pedalboard import Compressor, HighpassFilter, LowpassFilter, PeakFilter, Pedalboard, Reverb
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import lfilter

SR = 44100
TPB = 480                      # MIDI ticks per beat
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUALITY = {"": (0, 4, 7), "m": (0, 3, 7), "dim": (0, 3, 6), "sus4": (0, 5, 7), "sus": (0, 5, 7),
           "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11)}
# General MIDI program and channel per role, so a SoundFont picks a sensible instrument.
GM = {"pad": (89, 0), "bass": (33, 1), "arp": (4, 2), "melody": (0, 3), "drums": (0, 9)}
# Stem loudness targets (LUFS): melody in front, pad and arp behind. Values follow musician's narration bed.
TARGET = {"melody": -21, "pad": -29, "arp": -29, "bass": -25, "drums": -25}


def to_midi(p) -> int:
    if isinstance(p, int):
        return p
    n = NOTE[p[0].upper()]
    rest = p[1:]
    if rest[:1] in ("#", "b"):
        n += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + n                   # C4 = 60


def chord_pcs(symbol: str) -> tuple[int, list[int]]:
    root = NOTE[symbol[0].upper()]
    rest = symbol[1:]
    if rest[:1] in ("#", "b"):
        root += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    if rest not in QUALITY:
        raise SystemExit(f"unsupported chord {symbol!r}; qualities: {sorted(QUALITY)}")
    return root % 12, [(root + i) % 12 for i in QUALITY[rest]]


def near(pc: int, low: int) -> int:
    """Lowest MIDI pitch with pitch class pc at or above `low`."""
    return low + (pc - low) % 12


# ---------- 1. score -> note events ----------

def expand(spec) -> dict[str, list[tuple[int, float, float, int]]]:
    """Return {part: [(pitch, start_beat, beats, velocity)]}."""
    rng = np.random.default_rng(spec.get("seed", 0))
    chords = [chord_pcs(c) for c in spec["chords"]]
    out = {}
    for name, part in spec["parts"].items():
        role, start = part["role"], int(part.get("from_bar", 0))
        ev = []
        if role == "melody":
            for n in part["notes"]:
                ev.append((to_midi(n[0]), float(n[1]), float(n[2]), int(n[3]) if len(n) > 3 else 88))
        for bar, (root, pcs) in enumerate(chords):
            if bar < start or role == "melody":
                continue
            b0 = bar * 4
            hum = lambda v: int(np.clip(v + rng.integers(-6, 7), 1, 127))   # velocity humanize, seeded
            if role == "pad":
                ev += [(near(pc, 55), b0, 4, hum(58)) for pc in pcs[:4]]
            elif role == "bass":
                ev += [(near(root, 36), b0, 2, hum(84)), (near(root, 36), b0 + 2, 2, hum(76))]
            elif role == "arp":
                tones = sorted(near(pc, 62) for pc in pcs) + [near(pcs[0], 62) + 12]
                ev += [(tones[i % len(tones)], b0 + i * 0.5, 0.45, hum(70)) for i in range(8)]
            elif role == "drums":
                ev += [(36, b0, 0.5, hum(96)), (36, b0 + 2, 0.5, hum(90)),
                       (38, b0 + 1, 0.5, hum(80)), (38, b0 + 3, 0.5, hum(84))]
                ev += [(42, b0 + i * 0.5, 0.25, hum(52 if i % 2 else 66)) for i in range(8)]
            else:
                raise SystemExit(f"unknown role {role!r}")
        out[name] = ev
    return out


def write_midi(events, spec, mdir: Path):
    mdir.mkdir(parents=True, exist_ok=True)
    tempo = mido.bpm2tempo(spec["bpm"])
    full = mido.MidiFile(type=1, ticks_per_beat=TPB)
    for name, ev in events.items():
        role = spec["parts"][name]["role"]
        program, ch = GM[role]
        msgs = []
        for pitch, beat, beats, vel in ev:
            msgs.append((round(beat * TPB), 1, mido.Message("note_on", note=pitch, velocity=vel, channel=ch)))
            msgs.append((round((beat + beats) * TPB), 0, mido.Message("note_off", note=pitch, velocity=0, channel=ch)))
        msgs.sort(key=lambda m: (m[0], m[1]))       # note_off before note_on at the same tick
        track = mido.MidiTrack([mido.MetaMessage("track_name", name=name),
                                mido.MetaMessage("set_tempo", tempo=tempo)])
        if ch != 9:
            track.append(mido.Message("program_change", program=program, channel=ch))
        now = 0
        for tick, _, m in msgs:
            track.append(m.copy(time=tick - now))
            now = tick
        single = mido.MidiFile(type=1, ticks_per_beat=TPB)
        single.tracks.append(track)
        single.save(mdir / f"{name}.mid")
        full.tracks.append(track)
    full.save(mdir / "full.mid")


# ---------- 2. render ----------

def adsr(n, a, d, s, r, hold):
    a, d, r = (max(1, int(x * SR)) for x in (a, d, r))
    env = np.zeros(n)
    hold = min(hold, n)
    seg = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, s, d, endpoint=False)])[:hold]
    env[:len(seg)] = seg
    env[len(seg):hold] = s
    tail = min(r, n - hold)
    env[hold:hold + tail] = (env[hold - 1] if hold else s) * np.linspace(1, 0, tail)
    return env


def voice(role, pitch, hold, rng):
    """One note of the draft synth. Returns a mono array."""
    f0 = 440 * 2 ** ((pitch - 69) / 12)
    if role == "drums":
        n = int(0.4 * SR)
        t = np.arange(n) / SR
        if pitch == 36:     # kick: pitch drop
            return np.sin(2 * np.pi * (55 * t + 60 * (1 - np.exp(-t * 30)) / 30)) * np.exp(-t * 9)
        if pitch == 38:     # snare: noise + body
            return 0.6 * rng.standard_normal(n) * np.exp(-t * 22) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 18)
        return 0.3 * np.diff(rng.standard_normal(n + 1)) * np.exp(-t * 60)      # hihat: bright noise
    tail = {"pad": 1.2, "bass": 0.15, "arp": 0.3, "melody": 0.6}[role]
    n = hold + int(tail * SR)
    t = np.arange(n) / SR
    if role == "pad":       # detuned saw-like stack
        sig = sum(np.sin(2 * np.pi * f0 * k * (1 + dc) * t) / k for k in range(1, 8) for dc in (-0.004, 0, 0.004))
        env = adsr(n, 0.8, 0.4, 0.85, tail, hold)
    elif role == "bass":
        sig = np.sin(2 * np.pi * f0 * t) + 0.25 * np.sin(4 * np.pi * f0 * t)
        env = adsr(n, 0.01, 0.15, 0.8, tail, hold)
    elif role == "arp":
        sig = (np.sin(2 * np.pi * f0 * t) + 0.3 * np.sin(6 * np.pi * f0 * t)) * np.exp(-t * 6)
        env = adsr(n, 0.004, 0.05, 1.0, tail, hold)
    else:                   # melody: piano-like decaying partials
        sig = sum(np.sin(2 * np.pi * f0 * k * t) * np.exp(-t * (1.5 + k)) / k ** 1.3 for k in range(1, 7))
        env = adsr(n, 0.01, 0.05, 1.0, tail, hold)
    return sig * env


def render_fallback(ev, role, spb, total, seed):
    rng = np.random.default_rng(seed)
    out = np.zeros((2, total))
    for i, (pitch, beat, beats, vel) in enumerate(ev):
        s0 = int(beat * spb * SR)
        x = voice(role, pitch, int(beats * spb * SR), rng) * (vel / 127) ** 1.6
        pan = {"arp": 0.25 + 0.5 * (i % 2), "pad": 0.4 + 0.2 * (pitch % 2)}.get(role, 0.5)
        e = min(total, s0 + len(x))
        out[0, s0:e] += x[:e - s0] * np.cos(pan * np.pi / 2)
        out[1, s0:e] += x[:e - s0] * np.sin(pan * np.pi / 2)
    return out.astype(np.float32)


def render_fluidsynth(mid: Path, soundfont: str, total: int):
    exe = shutil.which("fluidsynth")
    if not exe or not Path(soundfont).is_file():
        return None
    raw = mid.with_suffix(".fluid.wav")
    subprocess.run([exe, "-ni", "-r", str(SR), "-g", "0.8", "-T", "wav", "-F", str(raw), soundfont, str(mid)],
                   check=True, capture_output=True, timeout=600)
    audio, sr = sf.read(raw, dtype="float32", always_2d=True)
    raw.unlink()
    if sr != SR:
        raise SystemExit(f"FluidSynth wrote {sr} Hz, expected {SR}")
    audio = audio.T
    return np.pad(audio, ((0, 0), (0, max(0, total - audio.shape[1]))))[:, :total]


# ---------- 3 + 4. loudness, fx, master ----------

def lufs(x):
    return pyln.Meter(SR).integrated_loudness(x.T.astype(np.float64))


def peak_limit(audio, ceiling_db=-1.0, lookahead_ms=5.0, release_ms=120.0):
    """Look-ahead peak limiter in numpy, after musician's src/mix/fx.py.

    Not pedalboard.Limiter: that JUCE limiter adds make-up gain (measured +4.75 dB on a
    -20 dBFS sine), which would undo the master loudness target.
    Sample-peak only; inter-sample (true) peaks can still exceed the ceiling slightly.
    """
    ceiling = 10 ** (ceiling_db / 20)
    g = np.minimum(1.0, ceiling / np.maximum(np.max(np.abs(audio), axis=0), 1e-9))
    la = max(1, int(lookahead_ms * SR / 1000))
    att = uniform_filter1d(minimum_filter1d(g, size=2 * la + 1), size=la | 1)   # reduce ahead of each peak
    a = np.exp(-1 / (release_ms * SR / 1000))
    rel, _ = lfilter([1 - a], [1, -a], att, zi=[a * att[0]])                   # smooth release
    return np.clip(audio * np.minimum(att, rel)[None, :], -ceiling, ceiling).astype(np.float32)


def fx_chain(role, narration):
    pocket = [PeakFilter(cutoff_frequency_hz=2500, gain_db=-3.5, q=0.8)] if narration and role != "bass" else []
    return Pedalboard({
        "pad": [HighpassFilter(140), LowpassFilter(7000), *pocket, Reverb(room_size=0.85, wet_level=0.35, dry_level=0.7)],
        "melody": [HighpassFilter(90), *pocket, Compressor(threshold_db=-24, ratio=2), Reverb(room_size=0.55, wet_level=0.2)],
        "arp": [HighpassFilter(300), *pocket, Reverb(room_size=0.7, wet_level=0.28)],
        "bass": [HighpassFilter(35), LowpassFilter(900), Compressor(threshold_db=-22, ratio=3)],
        "drums": [HighpassFilter(30), *pocket, Compressor(threshold_db=-20, ratio=2.5), Reverb(room_size=0.3, wet_level=0.1)],
    }[role])


def run(spec, outdir: Path, soundfont=None, narration=False):
    outdir.mkdir(parents=True, exist_ok=True)
    events = expand(spec)
    write_midi(events, spec, outdir / "midi")
    spb = 60 / spec["bpm"]
    total = int((len(spec["chords"]) * 4 * spb + 3.0) * SR)            # + 3 s reverb tail
    report = {"bpm": spec["bpm"], "bars": len(spec["chords"]), "parts": {}}
    bus = np.zeros((2, total), np.float32)
    (outdir / "stems").mkdir(exist_ok=True)
    for i, (name, ev) in enumerate(events.items()):
        role = spec["parts"][name]["role"]
        audio, engine = None, "fallback"
        if soundfont:
            audio = render_fluidsynth(outdir / "midi" / f"{name}.mid", soundfont, total)
            engine = "fluidsynth" if audio is not None else "fallback (fluidsynth or soundfont missing)"
        if audio is None:
            audio = render_fallback(ev, role, spb, total, spec.get("seed", 0) + i)
        measured = lufs(audio)
        gain = TARGET[role] - measured if np.isfinite(measured) else 0.0
        audio = fx_chain(role, narration)(audio * 10 ** (gain / 20), SR)
        sf.write(outdir / "stems" / f"{name}.wav", audio.T, SR, subtype="FLOAT")
        bus += audio
        report["parts"][name] = {"role": role, "engine": engine, "notes": len(ev),
                                 "measured_lufs": round(float(measured), 2), "gain_db": round(float(gain), 2)}
    target = spec.get("master_lufs", -18 if narration else -16)
    bus = Pedalboard([Compressor(threshold_db=-18, ratio=1.5)])(bus, SR)
    bus *= 10 ** ((target - lufs(bus)) / 20)
    bus = peak_limit(bus, ceiling_db=-1.0)
    sf.write(outdir / "final.wav", bus.T, SR, subtype="PCM_24")
    report["master"] = {"target_lufs": target, "lufs": round(float(lufs(bus)), 2),
                        "peak_dbfs": round(float(20 * np.log10(np.max(np.abs(bus)))), 2),
                        "seconds": round(total / SR, 2)}
    (outdir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


# ---------- sonify: data -> score spec ----------

def sonify_spec(values, bars, bpm):
    """Map a numeric series to a melody in D minor: higher value -> higher pitch,
    larger step-to-step change -> louder note. One eighth note per point after resampling."""
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if len(v) < 2:
        raise SystemExit("need at least 2 finite values")
    n = bars * 8
    v = np.interp(np.linspace(0, len(v) - 1, n), np.arange(len(v)), v)
    scale = [62, 64, 65, 67, 69, 70, 72, 74, 76, 77, 79, 81, 82, 84]   # D minor, D4..C6
    lo, hi = v.min(), v.max()
    idx = np.zeros(n, int) if hi == lo else np.round((v - lo) / (hi - lo) * (len(scale) - 1)).astype(int)
    step = np.abs(np.diff(v, prepend=v[0]))
    vel = 60 + (40 * step / step.max() if step.max() > 0 else np.zeros(n))
    notes = [[scale[k], i * 0.5, 0.5, int(vel[i])] for i, k in enumerate(idx)]
    loop = ["Dm", "Bb", "F", "C"]
    return {"bpm": bpm, "seed": 0, "chords": [loop[b % 4] for b in range(bars)],
            "parts": {"data": {"role": "melody", "notes": notes},
                      "pad": {"role": "pad"}, "bass": {"role": "bass"}},
            "mapping": {"pitch": "min..max -> D4..C6 in D minor", "velocity": "abs change -> 60..100",
                        "points": int(len(values)), "resampled_to": n, "value_range": [float(lo), float(hi)]}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("spec")
    r.add_argument("outdir")
    s = sub.add_parser("sonify")
    s.add_argument("csv")
    s.add_argument("outdir")
    s.add_argument("--column", required=True)
    s.add_argument("--bars", type=int, default=8)
    s.add_argument("--bpm", type=float, default=100)
    for p in (r, s):
        p.add_argument("--soundfont", help="SF2/SF3 file; needs the fluidsynth CLI")
        p.add_argument("--narration", action="store_true", help="cut 2.5 kHz voice pocket, master at -18 LUFS")
    args = ap.parse_args()
    if args.cmd == "render":
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    else:
        data = np.genfromtxt(args.csv, delimiter=",", names=True, dtype=float)
        spec = sonify_spec(data[args.column], args.bars, args.bpm)
        Path(args.outdir).mkdir(parents=True, exist_ok=True)
        (Path(args.outdir) / "spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False))
    run(spec, Path(args.outdir), args.soundfont, args.narration)


if __name__ == "__main__":
    main()
