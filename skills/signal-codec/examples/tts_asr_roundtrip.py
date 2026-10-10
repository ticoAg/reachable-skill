#!/usr/bin/env python3
"""End-to-end, fully local: text -> speech (Piper) -> text (faster-whisper).

Shows that the generated audio carries the words, checked by an independent recognizer.
Deps: piper-tts, faster-whisper.  Voice model: rhasspy/piper-voices en_US-lessac-medium
  (download .onnx and .onnx.json into ./voices/ first; the download path is in references/end-to-end.md section 4a).
Run: python tts_asr_roundtrip.py "The quick brown fox jumps over the lazy dog." ./voices/en_US-lessac-medium.onnx
"""
import sys
import wave
from faster_whisper import WhisperModel
from piper import PiperVoice

text = sys.argv[1] if len(sys.argv) > 1 else "The quick brown fox jumps over the lazy dog."
voice_path = sys.argv[2] if len(sys.argv) > 2 else "voices/en_US-lessac-medium.onnx"
out_wav = "tts_out.wav"

voice = PiperVoice.load(voice_path)
with wave.open(out_wav, "wb") as wav:
    voice.synthesize_wav(text, wav)
print(f"synthesized {out_wav} at {voice.config.sample_rate} Hz")

import librosa
import soundfile as sf

# faster-whisper expects 16 kHz mono float32. Resample explicitly.
audio, sr = sf.read(out_wav, dtype="float32")
audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

asr = WhisperModel("tiny", device="cpu", compute_type="int8")
segments, info = asr.transcribe(audio, language="en")
heard = " ".join(s.text.strip() for s in segments)
print("recognized:", heard)

norm = lambda s: "".join(c for c in s.lower() if c.isalnum() or c == " ").split()
expected, got = norm(text), norm(heard)
match = sum(1 for w in expected if w in got) / len(expected)
print(f"word recall: {match:.2f}")
