# 编码：文本与参数 → 音频

按“内容是什么”选路线。各路线的条件格式互不相通，不要假设能互换。

| 要生成 | 路线 |
|---|---|
| 朗读文字（TTS） | 本地：Piper、Kokoro 等开源模型；云端：OpenAI、ElevenLabs、Google 等 API；免 key：edge-tts。现成 skill：OpenAI `speech`，见 [external](../external.md) |
| 音乐：内容要精确可控（配乐、铺底、主题动机、对齐画面） | 代码作曲：乐谱 → MIDI → 分轨渲染 → 响度对齐 → 效果与母带，见下节 |
| 数据 → 音乐（可听化） | 数据映射为音高、力度、密度，再走代码作曲流程，见下节 |
| 音乐：风格化、写实音色、整首歌 | 生成模型：Lyria、MusicGen 等，见 [end-to-end](../end-to-end.md) 第 5 节 |
| 音效 | AudioCraft 的 AudioGen，或程序合成（噪声 + 包络 + 滤波） |
| 测试音、扫频、噪声 | `python scripts/synth_wave.py tone.wav --kind sine --freq 440` |
| 把文字本身编成声音信号 | 调制：FSK、Morse、DTMF；工具 minimodem、ggwave，或下面的最小示例 |

使用任何 TTS 或音乐模型前，核对权重许可、语言/音色支持，以及能否克隆真人声音。克隆真人声音需要对方授权。

## 代码作曲：作曲与音色分离

参考实现：[komiyoo/musician](https://github.com/komiyoo/musician)（MIT）。核心是**作曲与音色分离**：先把音乐写成 MIDI（只含音高、时值、力度、表情控制），再给每个声部选音源，最后统一响度并加效果。改旋律不用动音色，换音色也不用动旋律。

```text
LLM 写乐谱（和弦、声部职责、主题）
   │ 1. 作曲    mido → midi/<part>.mid + full.mid
   │ 2. 渲染    每个声部选一个引擎：
   │              合成器（Surge XT）· SFZ 采样（sfizz）· SF2/SF3（FluidSynth）
   │              都没有时 numpy 草稿合成：音符完全一样，只是音色粗糙
   │ 3. 响度    每轨对齐到声部目标 LUFS（pyloudnorm, ITU-R BS.1770）
   │ 4. 效果    pedalboard：高通、人声让位（1.5–4 kHz 下凹）、混响；总线压缩
   ▼            母带对齐目标 LUFS，再做峰值限幅
final.wav + report.json（每轨引擎、测得响度、增益）
```

为什么分层：

- **乐谱给 LLM 写，音频给程序渲染。** LLM 擅长和声进行、段落结构、主题安排，不擅长直接输出采样。乐理与作曲决策可用 `music-composition` skill（见 [external](../external.md)）。
- **先对齐响度再加效果。** 换任何音色或采样，层次关系都稳定。musician 的口播铺底目标：钢琴 −21、小提琴 −22、贝斯/鼓 −25、pad/琶音 −29 LUFS；母带 −18 LUFS、峰值 −1 dBFS，放在 −16 到 −14 LUFS 的口播下面。
- **有口播时给人声让位。** 中文语音可懂度集中在 1–4 kHz，旋律声部在此下凹 3–5 dB；musician 还支持按旁白音量自动压低配乐（ducking）。
- **兜底合成器保证一定能出声。** 没装音源时也能先出草稿，用来对画面、对口播节奏。

本仓库的最小可运行版本：`examples/music_pipeline.py`（✅ 本机实跑，numpy 兜底引擎；FluidSynth 分支本机未安装，未跑）。

```bash
python skills/signal-codec/examples/music_pipeline.py render spec.json out/            # 乐谱 → 音乐
python skills/signal-codec/examples/music_pipeline.py render spec.json out/ --narration # 口播铺底
python skills/signal-codec/examples/music_pipeline.py render spec.json out/ --soundfont GeneralUser.sf2
```

乐谱格式（每小节一个和弦，声部按职责自动展开；旋律逐音写出）：

```json
{"bpm": 100, "seed": 7, "master_lufs": -16,
 "chords": ["Dm", "Bb", "F", "C", "Dm", "Bb", "Gm", "A7"],
 "parts": {
  "pad":   {"role": "pad"},
  "bass":  {"role": "bass", "from_bar": 1},
  "arp":   {"role": "arp", "from_bar": 2},
  "lead":  {"role": "melody", "notes": [["A4", 16, 1], ["D5", 17, 1], ["F5", 18, 1.5]]},
  "drums": {"role": "drums", "from_bar": 4}}}
```

`notes` 每项是 `[音高, 起始拍, 拍数, 力度?]`，拍从 0 开始计。

需要更完整的能力时直接用 musician：故事时间表驱动配乐（按段落秒数反算每小节速度，和视频、字幕共用同一速度表）、23 声部管弦配器、MusicXML 总谱与分谱交付、编辑后的 MIDI 回渲染、看图配乐（视觉 LLM 读图 → 情绪、能量、调性、BPM 等参数）、马尔可夫链旋律变奏。

### 混音的两个坑

- **pedalboard 的 `Limiter` 不能当峰值天花板用。** 它封装的 JUCE 限幅器会补偿增益：本机输入 −20 dBFS 正弦，输出变成 −15.25 dBFS。放在响度对齐之后，会把母带从 −16 抬到约 −12 LUFS。musician 和本仓库示例都改用 numpy 前瞻峰值限幅器。
- **效果会改变响度。** 混响抬高、压缩降低，所以每轨对齐的是效果前的响度。最终只以母带测量值为准，写进报告。

## 数据 → 音乐（可听化）

把信号编码成声音的另一种方式：不是还原波形，而是把数据的结构映射成音乐参数，让人用耳朵听出趋势、突变和异常。

```bash
python skills/signal-codec/examples/music_pipeline.py sonify sensor.csv out/ --column value --bars 8
```

示例映射：数值从小到大对应 D 小调音阶 D4 到 C6，相邻点变化越大音符越响；每个点一个八分音符，下面配 pad 和贝斯，和弦循环 Dm–B♭–F–C。映射规则写进 `spec.json` 的 `mapping` 字段，方便回查。本机用 200 点合成数据验证：数据与音高相关系数 0.996，峰值位置一致。

设计映射时：

- 一个维度对应一个听觉参数（音高、力度、节奏密度、音色亮度、协和度），并写下对应关系。
- 量化到音阶会丢失细节：相邻的数值可能落在同一个音上，可听化不能替代数值分析。
- musician 的 `analyze` 模式是更复杂的例子：代码仓库的嵌套深度对应音区，圈复杂度对应节奏密度，可读性对应协和度，import 对应开头的鼓点。

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

时长、声道、采样率、编码、削波、首尾点击声。TTS 要听或用 ASR 回转写比对文字。音乐先查 `report.json` 的母带 LUFS 与峰值，再用 `scripts/render_view.py` 看频谱，最后听风格与节奏。生成音频不是任何源录音的逆变换。

## 来源

- [komiyoo/musician](https://github.com/komiyoo/musician)：代码作曲参考实现（MIT）
- [mido](https://mido.readthedocs.io/)、[pyloudnorm](https://github.com/csteinmetz1/pyloudnorm)、[pedalboard](https://spotify.github.io/pedalboard/)

- [MusicGen / AudioCraft](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md)
- [SoundFile](https://python-soundfile.readthedocs.io/en/0.13.1/)
- [FluidSynth](https://www.fluidsynth.org/)
