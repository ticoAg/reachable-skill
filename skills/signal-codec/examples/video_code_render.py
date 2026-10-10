#!/usr/bin/env python3
"""Program-generated video: a JSON storyboard becomes an MP4, optionally with an audio track.

No generative model. The LLM (or the user) writes the storyboard; code draws every frame
with Pillow and pipes raw RGB frames into FFmpeg (H.264, yuv420p).

Storyboard (JSON file):
  {"width": 1280, "height": 720, "fps": 30,
   "scenes": [
     {"type": "title", "text": "信号编码", "sub": "code → frames → mp4", "seconds": 2},
     {"type": "wave",  "text": "440 Hz", "freq": 3, "seconds": 3},
     {"type": "bars",  "text": "Results", "values": {"A": 3, "B": 7, "C": 5}, "seconds": 3}
   ]}
Scene types: title (fade in/out), wave (scrolling sine), bars (bars grow to their values).

Deps: numpy, Pillow, and an FFmpeg binary (system `ffmpeg`, or `pip install imageio-ffmpeg`).
Run:  python video_code_render.py storyboard.json out.mp4 [--audio music.wav] [--font latin.ttf --font cjk.ttf]
Without --font only Latin text renders. Mixed Chinese/English text needs a font that covers both
(Noto Sans CJK, Source Han Sans) or a chain such as --font DejaVuSans.ttf --font DroidSansFallbackFull.ttf.
"""
import argparse
import json
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BG = (18, 22, 36)
FG = (235, 238, 245)
ACCENT = (90, 170, 255)


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit("FFmpeg not found: install ffmpeg or `pip install imageio-ffmpeg`")


class FontChain:
    """Several fonts tried in order per character, e.g. a Latin font then a CJK font.

    A glyph counts as missing when it renders the same bitmap as a codepoint no font
    defines (the .notdef box). This avoids a fontTools dependency; it can misjudge a
    font whose real glyph looks exactly like its .notdef box, which is rare.
    """

    def __init__(self, paths, size):
        self.fonts = [ImageFont.truetype(p, size) for p in paths] or [ImageFont.load_default(size=size)]
        self._notdef = [self._mask(f, "\U0010FFFD") for f in self.fonts]

    @staticmethod
    def _mask(font, ch):
        m = font.getmask(ch)
        return m.size, bytes(m)

    def pick(self, ch):
        if ch.isspace():
            return self.fonts[0]
        for f, nd in zip(self.fonts, self._notdef):
            if self._mask(f, ch) != nd:
                return f
        return self.fonts[0]

    def runs(self, text):
        """Split text into (substring, font) runs."""
        out = []
        for ch in text:
            f = self.pick(ch)
            if out and out[-1][1] is f:
                out[-1][0] += ch
            else:
                out.append([ch, f])
        return out


def text_width(draw, text, chain):
    return sum(draw.textlength(t, font=f) for t, f in chain.runs(text))


def draw_text(draw, xy, text, chain, fill):
    x, y = xy
    for t, f in chain.runs(text):
        draw.text((x, y), t, font=f, fill=fill)
        x += draw.textlength(t, font=f)


def centered(draw, y, text, chain, fill):
    draw_text(draw, ((draw.im.size[0] - text_width(draw, text, chain)) / 2, y), text, chain, fill)


def fade(p: float) -> float:
    """Opacity for scene progress p in [0, 1): fade in over the first 20 %, out over the last 20 %."""
    return min(1.0, p / 0.2, (1 - p) / 0.2)


def draw_title(img, s, p, fonts):
    a = fade(p)
    d = ImageDraw.Draw(img)
    color = tuple(int(BG[i] + (FG[i] - BG[i]) * a) for i in range(3))
    h = img.size[1]
    centered(d, h * 0.38, s.get("text", ""), fonts["big"], color)
    centered(d, h * 0.55, s.get("sub", ""), fonts["small"], color)


def draw_wave(img, s, p, fonts):
    w, h = img.size
    d = ImageDraw.Draw(img)
    draw_text(d, (40, 30), s.get("text", ""), fonts["small"], FG)
    cycles = float(s.get("freq", 3))
    x = np.arange(w)
    phase = 2 * np.pi * p * cycles                      # scroll as the scene plays
    y = h / 2 + 0.3 * h * np.sin(2 * np.pi * cycles * x / w - phase)
    d.line(list(zip(x.tolist(), y.tolist())), fill=ACCENT, width=4)
    d.line([(0, h / 2), (w, h / 2)], fill=(70, 75, 95), width=1)


def draw_bars(img, s, p, fonts):
    w, h = img.size
    d = ImageDraw.Draw(img)
    draw_text(d, (40, 30), s.get("text", ""), fonts["small"], FG)
    values = s.get("values", {})
    if not values:
        return
    top = max(values.values()) or 1
    grow = min(1.0, p / 0.6)                            # reach full height at 60 % of the scene
    slot = (w - 160) / len(values)
    base = h - 100
    for i, (label, v) in enumerate(values.items()):
        x0 = 80 + i * slot + slot * 0.2
        x1 = 80 + (i + 1) * slot - slot * 0.2
        bar_h = (h - 260) * (v / top) * grow
        d.rectangle([x0, base - bar_h, x1, base], fill=ACCENT)
        lw = text_width(d, label, fonts["small"])
        draw_text(d, ((x0 + x1 - lw) / 2, base + 15), label, fonts["small"], FG)
        num = f"{v * grow:.1f}"
        nw = text_width(d, num, fonts["small"])
        draw_text(d, ((x0 + x1 - nw) / 2, base - bar_h - 50), num, fonts["small"], FG)


DRAW = {"title": draw_title, "wave": draw_wave, "bars": draw_bars}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("storyboard")
    ap.add_argument("output", help=".mp4")
    ap.add_argument("--audio", help="audio file to mux; video length wins (-shortest)")
    ap.add_argument("--font", action="append", default=[],
                    help="TTF/OTF font path; repeat to add fallbacks, tried in order per character")
    args = ap.parse_args()

    with open(args.storyboard, encoding="utf-8") as f:
        sb = json.load(f)
    w, h, fps = int(sb.get("width", 1280)), int(sb.get("height", 720)), int(sb.get("fps", 30))
    if w % 2 or h % 2:
        raise SystemExit("width and height must be even for yuv420p")
    for s in sb["scenes"]:
        if s["type"] not in DRAW:
            raise SystemExit(f"unknown scene type {s['type']!r}; known: {sorted(DRAW)}")
    fonts = {"big": FontChain(args.font, h // 9), "small": FontChain(args.font, h // 24)}

    cmd = [find_ffmpeg(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-"]
    if args.audio:
        # apad pads short audio with silence; -shortest then cuts at the video's end
        cmd += ["-i", args.audio, "-af", "apad", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", args.output]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    total = 0
    try:
        for s in sb["scenes"]:
            n = max(1, round(float(s.get("seconds", 2)) * fps))
            for i in range(n):
                img = Image.new("RGB", (w, h), BG)
                DRAW[s["type"]](img, s, i / n, fonts)
                proc.stdin.write(img.tobytes())
            total += n
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed; see the error above")
    print(f"wrote {args.output}: {total} frames, {total / fps:.2f}s at {fps} fps, {w}x{h}")


if __name__ == "__main__":
    main()
