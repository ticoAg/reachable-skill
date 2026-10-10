#!/usr/bin/env python3
"""Synthetic biosignal roundtrip. Not a clinical recording.

Simulates an ECG and two EEG sines, writes WFDB and EDF, then reads them back.
Deps: numpy, scipy, mne, edfio, wfdb, neurokit2.
Run: python biosignal_roundtrip.py out/
"""
import argparse
import warnings
from importlib.metadata import version
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("outdir")
    args = ap.parse_args()
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    import mne
    import wfdb
    import neurokit2 as nk
    from scipy import signal

    mne.set_log_level("ERROR")
    print(
        "versions",
        f"mne {version('mne')}",
        f"edfio {version('edfio')}",
        f"wfdb {version('wfdb')}",
        f"neurokit2 {version('neurokit2')}",
        f"pandas {version('pandas')}",
    )

    fs, duration, hr = 250, 20, 70
    ecg = nk.ecg_simulate(duration=duration, sampling_rate=fs, heart_rate=hr, random_state=42)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        signals, info = nk.ecg_process(ecg, sampling_rate=fs)
    peaks = np.asarray(info["ECG_R_Peaks"])
    mean_hr = 60.0 / (np.diff(peaks).mean() / fs)
    rate_mean = float(np.nanmean(signals["ECG_Rate"]))
    if not np.isfinite(mean_hr) or abs(mean_hr - hr) > 5 or abs(rate_mean - hr) > 5:
        raise SystemExit(f"ECG rate {mean_hr:.2f} / {rate_mean:.2f} bpm is far from {hr}")

    rec = out / "records"
    rec.mkdir(exist_ok=True)
    wfdb.wrsamp(
        "100", fs=fs, units=["mV"], sig_name=["ECG"],
        p_signal=np.asarray(ecg, float).reshape(-1, 1), write_dir=str(rec),
    )
    record = wfdb.rdrecord(str(rec / "100"), sampfrom=0, sampto=3600)
    if record.fs != fs or record.units != ["mV"] or record.sig_name != ["ECG"]:
        raise SystemExit(f"WFDB header mismatch: fs={record.fs} units={record.units} names={record.sig_name}")
    err = float(np.max(np.abs(record.p_signal[:, 0] - ecg[:3600])))
    if err > 1e-6:
        raise SystemExit(f"WFDB roundtrip error {err}")
    wfdb.wrann("100", "atr", sample=peaks, symbol=["N"] * len(peaks), fs=fs, write_dir=str(rec))
    ann = wfdb.rdann(str(rec / "100"), "atr")
    if not np.array_equal(ann.sample, peaks) or set(ann.symbol) != {"N"}:
        raise SystemExit("WFDB annotations do not match the R peaks")

    sfreq = 256.0
    n = int(sfreq * 10)
    t = np.arange(n) / sfreq
    data = np.vstack([
        50e-6 * np.sin(2 * np.pi * 10 * t),
        30e-6 * np.sin(2 * np.pi * 6 * t),
    ])
    raw = mne.io.RawArray(data, mne.create_info(["Fp1", "Cz"], sfreq, ch_types="eeg"), verbose="ERROR")
    onsets, durations, descriptions = [1.0, 4.5], [0.5, 0.2], ["stim", "blink"]
    raw.set_annotations(mne.Annotations(onset=onsets, duration=durations, description=descriptions))
    edf = out / "synth.edf"
    raw.export(edf, fmt="edf", overwrite=True, verbose="ERROR")

    got = mne.io.read_raw_edf(edf, preload=False, verbose="ERROR")
    if got.info["sfreq"] != sfreq or got.ch_names != ["Fp1", "Cz"] or got.get_channel_types() != ["eeg", "eeg"]:
        raise SystemExit(f"EDF header mismatch: {got.info['sfreq']} {got.ch_names} {got.get_channel_types()}")
    if list(got.annotations.description) != descriptions:
        raise SystemExit(f"EDF annotation text mismatch: {list(got.annotations.description)}")
    if not np.allclose(got.annotations.onset, onsets) or not np.allclose(got.annotations.duration, durations):
        raise SystemExit(
            f"EDF annotation times mismatch: {list(got.annotations.onset)} {list(got.annotations.duration)}"
        )
    y = got.get_data(start=0, stop=min(got.n_times, int(sfreq * 10)))
    if y.shape != data.shape:
        raise SystemExit(f"EDF data shape {y.shape}, expected {data.shape}")
    corrs = [float(np.corrcoef(data[i], y[i])[0, 1]) for i in range(2)]
    max_uv = [float(np.max(np.abs(data[i] - y[i])) * 1e6) for i in range(2)]
    if min(corrs) < 0.999 or max(max_uv) > 0.01:
        raise SystemExit(f"EDF quantization too coarse: corr={corrs} max_uV={max_uv}")
    peaks_hz = []
    for row in y:
        f, psd = signal.welch(row, fs=sfreq, nperseg=int(sfreq))
        peaks_hz.append(float(f[int(np.argmax(psd))]))
    if peaks_hz != [10.0, 6.0]:
        raise SystemExit(f"EDF Welch peaks {peaks_hz}, expected 10 Hz and 6 Hz")

    nk_warn = any("ChainedAssignment" in type(w.message).__name__ or "inplace" in str(w.message) for w in caught)
    print(f"ecg peaks {len(peaks)} mean_hr {mean_hr:.2f} bpm ecg_rate {rate_mean:.2f} bpm (simulated {hr})")
    print(f"wfdb fmt {record.fmt} max_abs_err {err:.3e} mV samples {record.p_signal.shape[0]} ann {len(ann.sample)}")
    print(
        f"edf n_times {got.n_times} corr {corrs[0]:.6f} {corrs[1]:.6f} "
        f"max_uV {max_uv[0]:.4g} {max_uv[1]:.4g} welch_hz {peaks_hz[0]:.0f} {peaks_hz[1]:.0f}"
    )
    if nk_warn:
        print("note: neurokit2 0.2.12 emits a pandas copy-on-write warning inside ecg_process; R peaks and ECG_Rate still match")


if __name__ == "__main__":
    main()
