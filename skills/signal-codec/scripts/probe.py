#!/usr/bin/env python3
"""Identify an input file and suggest which signal-codec reference to read.

Standard library only. Uses magic bytes first, then the extension, and adds
ffprobe output when FFmpeg is installed. It does not decode the signal.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

# (magic prefix at offset 0, label, modality)
MAGIC = [
    (b"RIFF", "RIFF container (WAV/AVI/WebP: check bytes 8-12)", None),
    (b"fLaC", "FLAC", "audio"),
    (b"OggS", "Ogg", "audio"),
    (b"ID3", "MP3 (ID3 tag)", "audio"),
    (b"\x89PNG", "PNG", "visual"),
    (b"\xff\xd8\xff", "JPEG", "visual"),
    (b"GIF8", "GIF", "visual"),
    (b"\x1a\x45\xdf\xa3", "Matroska/WebM", "visual"),
    (b"0       ", "EDF", "biosignals"),
    (b"\xffBIOSEMI", "BDF", "biosignals"),
    (b"ply\n", "PLY", "spatial"),
    (b"glTF", "GLB", "spatial"),
    (b"PK\x03\x04", "ZIP container (check contents)", None),
    (b"\x89HDF", "HDF5", None),
]
RIFF_FORMS = {b"WAVE": ("WAV", "audio"), b"AVI ": ("AVI", "visual"), b"WEBP": ("WebP", "visual")}

EXT = {
    "audio": {".wav", ".flac", ".mp3", ".ogg", ".opus", ".m4a", ".aac", ".aiff"},
    "visual": {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif",
               ".mp4", ".mov", ".mkv", ".webm", ".avi"},
    "timeseries": {".csv", ".tsv", ".parquet", ".json", ".jsonl", ".npy", ".npz"},
    "biosignals": {".edf", ".bdf", ".fif", ".set", ".vhdr", ".hea", ".dat"},
    "rf": {".sigmf-meta", ".sigmf-data", ".cfile", ".cf32", ".cs16", ".iq", ".raw"},
    "spatial": {".ply", ".pcd", ".stl", ".obj", ".glb", ".gltf", ".las", ".laz", ".xyz", ".off"},
}
AMBIGUOUS = {".dat": "also WFDB/raw binary", ".raw": "also raw audio/image", ".npy": "any array"}


def identify(path: Path):
    head = b""
    if path.is_file():
        with path.open("rb") as fh:
            head = fh.read(16)
    label, modality = None, None
    for prefix, name, mod in MAGIC:
        if head.startswith(prefix):
            label, modality = name, mod
            break
    if head.startswith(b"RIFF") and head[8:12] in RIFF_FORMS:
        label, modality = RIFF_FORMS[head[8:12]]
    if head[4:8] == b"ftyp":
        label, modality = "ISO BMFF (MP4/MOV/M4A: probe streams)", None
    ext = "".join(path.suffixes[-1:]).lower()
    if path.name.lower().endswith(".sigmf-meta") or path.name.lower().endswith(".sigmf-data"):
        ext = "." + path.name.lower().rsplit(".", 1)[-1]
    by_ext = [m for m, exts in EXT.items() if ext in exts]
    return label, modality, ext, by_ext


def ffprobe(path: Path):
    if not shutil.which("ffprobe"):
        return None
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        return None
    data = json.loads(out.stdout)
    return [
        {k: s.get(k) for k in ("codec_type", "codec_name", "sample_rate", "channels",
                               "width", "height", "avg_frame_rate", "duration")
         if s.get(k) is not None}
        for s in data.get("streams", [])
    ]


def main(argv):
    if len(argv) < 2:
        raise SystemExit("usage: probe.py FILE [FILE...]")
    for arg in argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"{arg}: not found")
            continue
        label, modality, ext, by_ext = identify(path)
        modalities = [modality] if modality else by_ext
        print(f"{arg}")
        print(f"  size: {path.stat().st_size if path.is_file() else 'directory'}")
        print(f"  signature: {label or 'unknown'}; extension: {ext or '-'}")
        if ext in AMBIGUOUS:
            print(f"  note: {ext} is ambiguous ({AMBIGUOUS[ext]}); confirm with the source")
        if not modalities:
            print("  route: unknown; open the file header or ask for the acquisition details")
        for m in dict.fromkeys(modalities):
            print(f"  route: references/decode/{m}.md  (to produce this kind: references/encode/{m}.md)")
        streams = ffprobe(path)
        if streams:
            print(f"  ffprobe streams: {json.dumps(streams, ensure_ascii=False)}")
        print("  the extension is a hint only; sample rate, units and clock must come from "
              "the file header or the recording setup")


if __name__ == "__main__":
    main(sys.argv)
