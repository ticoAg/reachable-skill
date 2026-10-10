# 编码：文本与参数 → 音频

按“内容是什么”选路线。各路线的条件格式互不相通，不要假设能互换。

| 要生成 | 路线 |
|---|---|
| 朗读文字（TTS） | 本地：Piper、Kokoro 等开源模型；云端：OpenAI、ElevenLabs、Google 等 API；免 key：edge-tts。现成 skill：OpenAI `speech`，见 [external](../external.md) |
| 音乐 / 音效 | AudioCraft（MusicGen/AudioGen）接收其版本支持的文本或旋律条件，返回音频张量，按模型自己的采样率保存 |
| 乐谱 → 音频 | 用 mido 或 pretty_midi 写 MIDI，再用 FluidSynth + SoundFont 渲染 |
| 测试音、扫频、噪声 | `python scripts/synth_wave.py tone.wav --kind sine --freq 440` |
| 把文字本身编成声音信号 | 调制：FSK、Morse、DTMF；工具 minimodem、ggwave，或下面的最小示例 |

使用任何 TTS 或音乐模型前，核对权重许可、语言/音色支持，以及能否克隆真人声音。克隆真人声音需要对方授权。

## 程序化合成

```python
import numpy as np
import soundfile as sf
sr = 48000
t = np.arange(int(sr * 1.0)) / sr
sf.write('tone.wav', 0.2 * np.sin(2 * np.pi * 440 * t), sr, subtype='PCM_16')
```

## 文本 → FSK 音频（最小示例，演示用）

每个比特用一个音调表示：0 为 1200 Hz，1 为 2200 Hz，100 baud。无同步头与纠错，只能由同参数的解调器读回。

```python
import numpy as np, soundfile as sf
sr, baud, f0, f1 = 48000, 100, 1200, 2200
bits = np.unpackbits(np.frombuffer('hello'.encode(), dtype=np.uint8))
spb = sr // baud
tone = lambda f: np.sin(2 * np.pi * f * np.arange(spb) / sr)
sf.write('fsk.wav', 0.3 * np.concatenate([tone(f1 if b else f0) for b in bits]), sr)
```

读回（与上面同参数）：

```python
x, sr = sf.read('fsk.wav')
seg = x[: len(x) // spb * spb].reshape(-1, spb)
t = np.arange(spb) / sr
e = lambda f: np.abs(seg @ np.exp(-2j * np.pi * f * t))
print(np.packbits((e(f1) > e(f0)).astype(np.uint8)).tobytes().decode())
```

## 检查输出

时长、声道、采样率、编码、削波、首尾点击声。TTS 要听或用 ASR 回转写比对文字；音乐的风格与节奏另行评价。生成音频不是任何源录音的逆变换。

## 来源

- [MusicGen / AudioCraft](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md)
- [SoundFile](https://python-soundfile.readthedocs.io/en/0.13.1/)
- [FluidSynth](https://www.fluidsynth.org/)
