# Reachable Skill

一个面向 AI Agent 的 skill：`signal-codec`。**读懂原始信号，也能生成信号。**

[安装](#安装) · [用法](#用法) · [工具与验证](#技术栈) · [Skill 路由](skills/signal-codec/SKILL.md)

<details open>
<summary>能力流向 · 动画演示（可收起）</summary>

<picture>
  <source media="(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark)" srcset="assets/readme/overview-dark.svg#still">
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/readme/overview-light.svg#still">
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/overview-dark.svg">
  <img src="assets/readme/overview-light.svg" width="720" alt="两条独立的能力路线：解码将图像、音视频、时序、生理信号、RF/IQ、点云和网格变成文本、数值、图表或原生对象；编码按文本、提示、参数、乐谱或数据生成语音、音乐、图像、视频、波形、IQ 或 3D 几何。">
</picture>

</details>

图示仅表达能力关系，不代表流量、性能或任意格式互转；实际支持与验证范围见[工具与验证](#技术栈)。

- **解码（decode）**：把图像、音频、视频、时序、生物信号、RF/IQ、点云等原始信号，变成人或 LLM 能读懂的数值、图和文本。
- **编码（encode）**：把文本、参数或其他内容，变成语音、音乐、图像、视频、波形、IQ、3D 几何等信号。

仓库提供转换与理解的工具、方法，以及互联网上已有 skill、CLI 和模型的用法与取舍。

**保留工具原生输出。没有统一中间表示、统一结果 schema、强制文本化，也不要求解码与编码互为逆过程。** 接口适配只发生在确实需要连接的两个工具之间。

## 安装

在支持 `SKILL.md` 的 Agent 中，把 `skills/signal-codec` 复制到其 skill 搜索目录。Codex 示例（先 clone 本仓库并进入仓库根目录）：

```bash
mkdir -p ~/.codex/skills
cp -R skills/signal-codec ~/.codex/skills/
```

Claude Code 复制到 `~/.claude/skills/`，或项目内 `.claude/skills/`。重启或刷新客户端后加载。

依赖按任务单独安装，不装“大而全”的环境。本机验证过的组合：

```bash
uv venv .venv && . .venv/bin/activate
uv pip install numpy scipy matplotlib soundfile librosa pandas trimesh \
    piper-tts faster-whisper huggingface_hub sigmf pillow imageio-ffmpeg \
    mido pyloudnorm pedalboard
# 生理信号写读（合成数据，仅供算法测试）
uv pip install mne edfio wfdb neurokit2
```

FFmpeg、GNU Radio、Blender 为独立软件。模型 API 需要各自的 key，通过环境变量设置（`OPENAI_API_KEY`、`GEMINI_API_KEY`、`ELEVENLABS_API_KEY`），不要写进代码。

## 用法

- “用 $signal-codec 看一下这段录音：转写、频谱图、削波情况。”
- “用 $signal-codec 把这份 IMU CSV 画成图并检查时间戳和缺失值。”
- “用 $signal-codec 把这段文字做成语音，再用 ASR 回转写验证。”
- “用 $signal-codec 把这段乐谱渲染成 WAV。”
- “用 $signal-codec 给这段口播写 30 秒 D 小调铺底配乐，人声频段让位，母带 −18 LUFS。”
- “用 $signal-codec 把这份传感器 CSV 变成一段能听出趋势的音乐。”
- “用 $signal-codec 用代码做一段 10 秒的讲解视频：标题、波形动画、结果柱状图，配上刚才的音乐。”
- “用 $signal-codec 生成一段 200–4000 Hz 的扫频测试音。”

生成后按对应指南回读，检查格式、时长、尺寸、采样率与内容是否符合预期；不要求编码与解码互为逆过程。

## 技术栈

各方向独立选工具，保留工具原生输出。图中列的是能力范围，不代表所有工具均已运行。

<details>
<summary>查看完整工具清单与验证状态</summary>

| 层 | 组件 | 作用 | 验证状态 |
|---|---|---|---|
| 识别 | `scripts/probe.py` | 文件签名、扩展名、ffprobe 流信息，给出该读哪份指南 | ✅ 本机运行 |
| 解码·视觉 | VLM（Gemini、OpenAI）、FFmpeg、OpenCV | 读图、抽帧、拼图 | ✅ FFmpeg 拼图实跑（imageio-ffmpeg 自带 7.0.2）；⚠️ VLM 未实跑（无 key） |
| 解码·音频 | faster-whisper、SciPy、librosa | 转写、PSD、节拍 | ✅ ASR 与 PSD 本机运行 |
| 解码·时序 | pandas、SciPy | 时间检查、Welch PSD | ✅ 本机运行 |
| 解码·RF | SigMF、NumPy、GNU Radio | 元数据、IQ 读取、解调 | ✅ SigMF 写读本机运行；GNU Radio 未装 |
| 解码·3D | Trimesh、Open3D、Blender | 网格检查、点云、渲染 | ✅ Trimesh 本机运行；Blender 未装 |
| 解码·生理 | MNE、WFDB、NeuroKit2 | EDF/WFDB 读取、ECG 处理 | ✅ 合成 EDF/WFDB 写读；心率与设定一致 |
| 编码·语音 | Piper（本地）、OpenAI TTS、ElevenLabs | 文本转语音 | ✅ Piper 本机运行并回转写；云端 ⚠️ |
| 编码·音乐（代码） | `examples/music_pipeline.py`：mido → numpy 兜底 / FluidSynth → pyloudnorm → pedalboard；参考 [komiyoo/musician](https://github.com/komiyoo/musician) | 乐谱 → 分轨 MIDI → 混音成品；数据可听化 | ✅ numpy 引擎本机运行；FluidSynth 分支未跑 |
| 编码·音乐（模型） | Lyria、MusicGen | 文本 → 音乐 | ⚠️ 未运行 |
| 编码·图像 | Diffusers、gpt-image、Gemini 图像 | 文生图 | ⚠️ 未运行（需 GPU 或 key） |
| 编码·视频（代码） | `examples/video_code_render.py`、Manim、MoviePy、Remotion | 分镜 → 帧 → MP4，可带音轨 | ✅ 脚本本机实跑；其余工具未跑 |
| 编码·视频（模型） | Veo | 文生视频 | ⚠️ 未运行。Sora 已于 2026-09-24 下线 |
| 编码·波形 | `scripts/synth_wave.py`、NumPy | 测试音、扫频、噪声、IQ | ✅ 本机运行 |
| 编码·3D | Trimesh、Blender | 建模、导出、渲染 | ✅ Trimesh 导出回读；Blender 未装 |

✅ 在本机（CPU、Python 3.13、无 GPU、无 API key）运行通过；⚠️ 依据官方文档编写，未运行。

</details>

## 结构

<details>
<summary>展开目录与脚本说明</summary>

```text
skills/signal-codec/
  SKILL.md                 路由：判断方向、识别输入、选 reference
  scripts/
    probe.py               识别文件格式并建议阅读哪份 reference（仅标准库）
    render_view.py         信号 → 波形 + 频谱图 PNG，供人或多模态模型查看
    synth_wave.py          参数 → 正弦/方波/扫频/噪声/复数 IQ（WAV、CSV、cf32）
  examples/
    audio_code_synth.py    乐谱文本 → WAV（单文件程序合成，最简入口）
    music_pipeline.py      乐谱 JSON → 分轨 MIDI → 渲染 → 响度对齐 → 效果与母带；数据 → 音乐
    tts_asr_roundtrip.py   文本 → Piper 语音 → faster-whisper 转写，检查词召回
    video_code_render.py   分镜 JSON → Pillow 逐帧绘制 → FFmpeg 编码 MP4，可混入音轨
    biosignal_roundtrip.py 合成 ECG/EEG → WFDB 与 EDF → 读回并核对心率、标注、频谱峰
  references/
    decode/{audio,visual,timeseries,biosignals,rf,spatial}.md
    encode/{audio,visual,timeseries,biosignals,rf,spatial}.md
    end-to-end.md          端到端调用：VLM、文生图/视频、TTS、音乐、ASR、信号示例
    external.md            已有的 skill、工具与模型清单
    integration.md         跨工具连接与工程实践
```

</details>

## 内容与状态

- 标 ✅ 的代码在本机运行过。标 ⚠️ 的依据官方文档编写，未实跑。
- 云端模型名、参数与价格会变动，核对日期 2026-10-10。遇到报错先查官方最新文档。
- `references/external.md` 的外部 skill 清单来自目录页与搜索结果，未逐个安装测试。
- 不携带模型权重、用户数据、自动硬件采集或后台上传逻辑。

## 扩展

见 [CONTRIBUTING.md](CONTRIBUTING.md)。
