#!/usr/bin/env python3
"""Render a 1-D signal as a PNG (waveform + spectrogram) for a human or a vision model.

Input: WAV/FLAC/OGG (needs soundfile) or a CSV column / .npy array with --fs.
The PNG is a derived view for inspection. It does not replace the original data.
Dependencies: numpy, scipy, matplotlib; soundfile for audio files.
"""
import argparse
import numpy as np


def load(path, fs, column, channel):
    p = path.lower()
    if p.endswith(".npy"):
        x = np.load(path)
        if fs is None:
            raise SystemExit("--fs is required for .npy input")
    elif p.endswith((".csv", ".tsv")):
        if fs is None:
            raise SystemExit("--fs is required for CSV input")
        x = np.genfromtxt(path, delimiter="," if p.endswith(".csv") else "\t",
                          names=True, dtype=float)
        x = x[column] if column else x[x.dtype.names[0]]
    else:
        import soundfile as sf
        x, fs = sf.read(path, dtype="float32", always_2d=True)
    x = np.asarray(x, dtype=float)
    if x.ndim == 2:
        x = x[:, channel]
    if not np.isfinite(x).all():
        raise SystemExit("input contains NaN/Inf; decide how to handle them first")
    return x, float(fs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input")
    ap.add_argument("output", help="PNG path")
    ap.add_argument("--fs", type=float, help="sampling rate in Hz (required unless the file has one)")
    ap.add_argument("--column", help="CSV column name (default: first column)")
    ap.add_argument("--channel", type=int, default=0, help="channel index for multi-channel audio")
    ap.add_argument("--start", type=float, default=0.0, help="start time in seconds")
    ap.add_argument("--duration", type=float, help="seconds to render (default: all)")
    ap.add_argument("--nperseg", type=int, default=1024, help="STFT window length in samples")
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import signal

    x, fs = load(args.input, args.fs, args.column, args.channel)
    i0 = int(args.start * fs)
    i1 = len(x) if args.duration is None else min(len(x), i0 + int(args.duration * fs))
    x = x[i0:i1]
    if len(x) < 8:
        raise SystemExit("selected segment is too short")
    t = args.start + np.arange(len(x)) / fs
    nper = min(args.nperseg, len(x))
    f, tt, sxx = signal.spectrogram(x, fs=fs, nperseg=nper, noverlap=nper // 2)
    db = 10 * np.log10(sxx + 1e-20)

    fig, (a0, a1) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    a0.plot(t, x, linewidth=0.5)
    a0.set_ylabel("amplitude (input units)")
    a1.pcolormesh(args.start + tt, f, db, shading="auto", vmin=db.max() - 90, vmax=db.max())
    a1.set_ylabel("frequency (Hz)")
    a1.set_xlabel("time (s)")
    fig.suptitle(f"fs={fs:g} Hz, n={len(x)}, peak={np.max(np.abs(x)):.4g}, "
                 f"rms={np.sqrt(np.mean(x**2)):.4g}; spectrogram dB is relative, not calibrated")
    fig.tight_layout()
    fig.savefig(args.output, dpi=120)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
