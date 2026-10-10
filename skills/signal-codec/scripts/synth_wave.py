#!/usr/bin/env python3
"""Generate a parametric test waveform as WAV, CSV, or raw complex64 IQ.

Encodes numbers (frequency, amplitude, noise, duration) into a signal. It is a
generator for test and demo signals, not a model of any real device.
Dependencies: numpy; soundfile for WAV output.

Examples:
  synth_wave.py tone.wav --kind sine --freq 440 --fs 48000 --duration 1
  synth_wave.py sweep.wav --kind chirp --freq 200 --freq-end 4000 --duration 2
  synth_wave.py sensor.csv --kind sine --freq 3 --fs 100 --noise 0.05 --seed 7
  synth_wave.py iq.cf32 --kind complex --freq 100000 --fs 1000000 --noise 0.01
"""
import argparse
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output", help=".wav, .csv or .cf32 (raw little-endian complex64, no header)")
    ap.add_argument("--kind", choices=["sine", "square", "chirp", "noise", "complex"], default="sine")
    ap.add_argument("--freq", type=float, default=440.0, help="Hz (start frequency for chirp)")
    ap.add_argument("--freq-end", type=float, help="Hz, chirp end frequency")
    ap.add_argument("--fs", type=float, default=48000.0, help="sampling rate in Hz")
    ap.add_argument("--duration", type=float, default=1.0, help="seconds")
    ap.add_argument("--amp", type=float, default=0.2, help="peak amplitude (0-1 for WAV)")
    ap.add_argument("--noise", type=float, default=0.0, help="Gaussian noise standard deviation")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    nyq = args.fs / 2
    top = max(args.freq, args.freq_end or 0)
    if args.kind != "noise" and top >= nyq:
        raise SystemExit(f"frequency {top:g} Hz must be below Nyquist ({nyq:g} Hz)")
    rng = np.random.default_rng(args.seed)
    n = int(round(args.fs * args.duration))
    t = np.arange(n) / args.fs

    if args.kind == "sine":
        x = np.sin(2 * np.pi * args.freq * t)
    elif args.kind == "square":
        x = np.sign(np.sin(2 * np.pi * args.freq * t))
    elif args.kind == "chirp":
        f1 = args.freq_end if args.freq_end is not None else args.freq * 2
        k = (f1 - args.freq) / args.duration
        x = np.sin(2 * np.pi * (args.freq * t + 0.5 * k * t**2))
    elif args.kind == "noise":
        x = rng.standard_normal(n)
    else:
        x = np.exp(2j * np.pi * args.freq * t)
    x = args.amp * x
    if args.noise:
        x = x + args.noise * (rng.standard_normal(n) + (1j * rng.standard_normal(n) if args.kind == "complex" else 0))

    out = args.output.lower()
    if out.endswith(".wav"):
        if args.kind == "complex":
            raise SystemExit("complex signals cannot be written as WAV; use .cf32")
        if np.max(np.abs(x)) > 1.0:
            raise SystemExit("peak exceeds 1.0 and would clip in WAV; lower --amp or --noise")
        import soundfile as sf
        sf.write(args.output, x, int(args.fs), subtype="PCM_16")
    elif out.endswith(".csv"):
        if args.kind == "complex":
            raise SystemExit("use .cf32 for complex signals")
        np.savetxt(args.output, np.column_stack([t, x]), delimiter=",", header="time_s,value", comments="")
    elif out.endswith(".cf32"):
        np.asarray(x, dtype="<c8").tofile(args.output)
    else:
        raise SystemExit("output extension must be .wav, .csv or .cf32")
    print(f"wrote {args.output}: {n} samples, fs={args.fs:g} Hz, kind={args.kind}, seed={args.seed}")


if __name__ == "__main__":
    main()
