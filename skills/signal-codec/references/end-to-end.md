# 端到端示例：模型调用与程序合成

每段代码都是一条完整的链路：输入 → 模型或程序 → 文件 → 检查。

**运行状态说明（核对日期 2026-10-10）**

- **已实跑**：标为 ✅ 的示例在本机（CPU，无 GPU，无 API key）运行通过。
- **未实跑**：标为 ⚠️ 的示例依据官方文档写成，本机没有对应的 API key 或 GPU，没有运行。使用前先设置环境变量，跑一个最小请求确认。
- 云端模型名、参数、价格会变。以官方页面为准，遇到 404 或参数错误时先查最新文档。

示例都假定 `OPENAI_API_KEY`、`GEMINI_API_KEY`、`ELEVENLABS_API_KEY` 已在环境变量中设置。代码里不要写入 key。

---

## 1. 图像理解（VLM）✅/⚠️

多模态模型直接读图，不需要先转成文本。代码直接粘贴在下方。

### 1a. Gemini ⚠️

```python
import base64
from google import genai

client = genai.Client()  # 读取环境变量 GEMINI_API_KEY

with open("photo.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=[
        {"type": "text", "text": "描述这张图片中的主体、颜色和场景。列出能看清的文字。"},
        {"type": "image", "data": image_b64, "mime_type": "image/jpeg"},
    ],
)
print(interaction.output_text)
```

大于约 20 MB 的请求改用 `client.files.upload(file="photo.jpg")`，然后把返回的 `uri` 与 `mime_type` 放进 `input`。

### 1b. OpenAI ⚠️

```python
import base64
from openai import OpenAI

client = OpenAI()  # 读取 OPENAI_API_KEY

with open("photo.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

response = client.responses.create(
    model="gpt-6-astra",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "描述这张图片中的主体、颜色和场景。"},
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_b64}"},
        ],
    }],
)
print(response.output_text)
```

### 注意

- 模型给出的是**推断**，不是测量。计数、坐标、读数要在原图上核对。
- 需要精确位置时，让模型输出框坐标，再把框画回原图检查。
- 把结论连同原图路径一起保存，方便回查。
- 本机没有 VLM 的 API key，第 1 节的代码未实跑。

---

## 2. 文生图

### 2a. 本地 Diffusers ⚠️（需要 GPU，CPU 上极慢）

```python
import torch
from diffusers import AutoPipelineForText2Image

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=dtype,
    variant="fp16" if dtype == torch.float16 else None,
    use_safetensors=True,
).to(device)

generator = torch.Generator(device=device).manual_seed(42)  # 固定种子，便于复现
image = pipe(
    prompt="A watercolor painting of a lighthouse at sunset",
    negative_prompt="blurry, low quality",
    num_inference_steps=30,
    guidance_scale=7.0,
    generator=generator,
).images[0]
image.save("lighthouse.png")
```

### 2b. OpenAI 图像生成 ⚠️

```python
import base64
from openai import OpenAI

client = OpenAI()
result = client.images.generate(
    model="gpt-image-2.5-sunburst",   # 快速版：gpt-image-2.5-flare
    prompt="A cute otter holding a sign that says 'hello'",
)
with open("otter.png", "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))
```

### 2c. Gemini 图像生成 ⚠️

```python
import base64
from google import genai

client = genai.Client()
interaction = client.interactions.create(
    model="gemini-nano-banana-2.1",
    input="A nano banana dish in a fancy restaurant with a Gemini theme",
)
with open("generated_image.png", "wb") as f:
    f.write(base64.b64decode(interaction.output_image.data))
```

---

## 3. 文生视频

### 3a. Veo（Gemini API）⚠️

```python
import time
from google import genai

client = genai.Client()
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="A slow dolly shot through a rainy neon street at night",
)
while not operation.done:          # 生成需要数分钟，轮询
    time.sleep(10)
    operation = client.operations.get(operation)

video = operation.response.generated_videos[0]
client.files.download(file=video.video, destination="veo_out.mp4")
```

### 3b. 代码生成视频 ✅

不用生成模型：分镜 JSON → Pillow 逐帧绘制 → FFmpeg 编码 H.264，可混入音轨。适合讲解、数据动画、片头字幕这类需要内容精确的视频。

```bash
python skills/signal-codec/examples/video_code_render.py storyboard.json out.mp4 \
  --audio melody.wav \
  --font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
  --font /usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf
```

本机结果：240 帧，8.01 秒，1280×720，30 fps，H.264 + AAC。4.5 秒的音频用静音补齐，没有截断视频。用抽帧拼图检查过：标题淡入淡出、波形滚动、柱状图增长，中英混排都正常。CPU 上渲染耗时约 4.6 秒。分镜格式和其他代码视频工具（Manim、matplotlib animation、MoviePy、Remotion）见 [encode/visual](encode/visual.md)。

### 3c. Sora ⚠️ 已停用

官方文档注明 Sora 2 模型与 Videos API 已于 2026-09-24 下线，**没有一对一的替代 API**。不要按旧示例调用。需要视频生成时，改用 3a 或其他仍在服务中的模型。

---

## 4. 语音合成（TTS）

### 4a. 本地 Piper ✅

已跑通，见 `examples/tts_asr_roundtrip.py`。

先下载音色（约 60 MB）：

```python
from huggingface_hub import hf_hub_download
for name in ["en_US-lessac-medium.onnx", "en_US-lessac-medium.onnx.json"]:
    hf_hub_download("rhasspy/piper-voices", f"en/en_US/lessac/medium/{name}", local_dir="voices")
```

```python
import wave
from piper import PiperVoice

voice = PiperVoice.load("voices/en/en_US/lessac/medium/en_US-lessac-medium.onnx")
with wave.open("out.wav", "wb") as wav:
    voice.synthesize_wav("Hello from a local voice.", wav)
```

### 4b. OpenAI TTS ⚠️

```python
from pathlib import Path
from openai import OpenAI

client = OpenAI()
with client.audio.speech.with_streaming_response.create(
    model="gpt-4o-mini-tts",
    voice="coral",             # 也可用 marin、cedar 等
    input="Today is a wonderful day to build something people love!",
    instructions="Speak in a cheerful and positive tone.",
) as response:
    response.stream_to_file(Path("speech.mp3"))
```

`response_format` 可选 `mp3`（默认）、`wav`、`pcm`、`flac`、`opus`、`aac`。

### 4c. ElevenLabs ⚠️（REST，无需额外 SDK）

```python
import os
import requests

voice_id = "JBFqnCBsd6RMkjVDRZzb"  # 从 GET /v1/voices 获取可用音色
resp = requests.post(
    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
    headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"},
    params={"output_format": "mp3_44100_128"},
    json={"text": "The first move is what sets everything in motion.",
          "model_id": "eleven_multilingual_v2"},
    timeout=120,
)
resp.raise_for_status()
with open("elevenlabs.mp3", "wb") as f:
    f.write(resp.content)
```

---

## 5. 音乐生成

### 5a. 程序合成 ✅

无模型、无网络，把乐谱文本渲染成 WAV：

```bash
python skills/signal-codec/examples/audio_code_synth.py melody.wav \
  "K:1 C4:1 E4:1 G4:1 S:1 C4+E4+G4:2 R:1 F#4:1" --bpm 120
```

本机已验证：C4 段主频 262.9 Hz，理论值 261.6 Hz，差值在 FFT 分辨率（约 2.5 Hz）以内。

### 5b. 代码作曲流水线 ✅

参考 [komiyoo/musician](https://github.com/komiyoo/musician)：乐谱 JSON → 分轨 MIDI → 每轨渲染 → 每轨响度对齐 → pedalboard 效果 → 母带 LUFS + 峰值限幅。乐谱格式与设计说明见 [encode/audio](encode/audio.md)。

```bash
pip install numpy scipy soundfile mido pyloudnorm pedalboard
python skills/signal-codec/examples/music_pipeline.py render spec.json out/
python skills/signal-codec/examples/music_pipeline.py sonify sensor.csv out_s/ --column value --bars 8
```

本机结果（numpy 兜底引擎；没装 FluidSynth，`--soundfont` 分支未跑）：

- 8 小节、5 个声部、22.2 秒。`full.mid` 有 5 轨，旋律 D5 段主频 587.8 Hz（理论 587.3 Hz）。
- 母带 −16.0 LUFS（目标 −16），峰值 −4.39 dBFS；`--narration` 模式峰值 −4.86 dBFS。
- 可听化：200 点数据压缩成 64 个八分音符，数据与音高相关系数 0.996。
- 测出并绕开一个问题：pedalboard `Limiter` 自带增益补偿，会把母带抬到约 −12 LUFS，改用 numpy 前瞻限幅器。

### 5c. Gemini Lyria ⚠️

```python
import base64
from google import genai

client = genai.Client()
interaction = client.interactions.create(
    model="lyria-3-clip-preview",   # 固定 30 秒；全曲用 lyria-3.5
    input="A short instrumental acoustic guitar piece.",
)
if interaction.output_audio:
    with open("music.mp3", "wb") as f:
        f.write(base64.b64decode(interaction.output_audio.data))
```

### 5d. MusicGen（本地 Transformers）⚠️（未运行，模型较大）

```python
import scipy.io.wavfile as wavfile
from transformers import AutoProcessor, MusicgenForConditionalGeneration

processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
inputs = processor(text=["lo-fi hip hop beat, mellow piano"], padding=True, return_tensors="pt")
audio = model.generate(**inputs, max_new_tokens=256)   # 约 5 秒
rate = model.config.audio_encoder.sampling_rate        # 按模型自己的采样率保存
wavfile.write("musicgen.wav", rate, audio[0, 0].numpy())
```

---

## 6. 语音识别（ASR）

### 6a. 本地 faster-whisper ✅

已跑通，见 `examples/tts_asr_roundtrip.py`。注意 faster-whisper 的 `transcribe()` 直接读文件时依赖 PyAV，本机版本不兼容时，先用 soundfile 读入并 `librosa.resample` 到 16 kHz，再传数组。

### 6b. OpenAI 转写 ⚠️

```python
from openai import OpenAI

client = OpenAI()
with open("speech.mp3", "rb") as f:
    result = client.audio.transcriptions.create(model="gpt-4o-transcribe", file=f)
print(result.text)
```

---

## 7. 信号处理 SDK 示例

这些是领域库的端到端调用，结果保持原生对象，不套统一格式。下面三段均已在本机运行通过（pandas 3.0.6、SciPy、trimesh 5.1.1、Python 3.13）。

**7a. 时序：CSV → 时间检查 → Welch PSD** ✅

```python
import numpy as np, pandas as pd
from scipy import signal

raw = pd.read_csv('sensor.csv')
raw['timestamp'] = pd.to_datetime(raw['timestamp'], utc=True, errors='raise')
s = raw.set_index('timestamp')['value'].sort_index()
dt = s.index.to_series().diff().dt.total_seconds().dropna().to_numpy()
assert (dt > 0).all() and np.allclose(dt, np.median(dt), rtol=1e-3, atol=1e-9), '非规则采样'
fs = 1 / np.median(dt)
f, psd = signal.welch(s.to_numpy(float), fs=fs, nperseg=256)
print('fs', fs, 'peak Hz', f[psd.argmax()])
```

本机用 100 Hz、5 Hz 正弦加噪声生成的 2000 点 CSV 验证：fs 得到 100.0，峰值在 5.08 Hz（频率分辨率约 0.39 Hz）。

**7b. RF：SigMF 写入 → 校验 → 读回 → PSD** ✅

```python
import json, numpy as np
from scipy import signal

fs, fc, n = 1_000_000, 433_920_000, 200_000
t = np.arange(n) / fs
x = (0.5 * np.exp(2j * np.pi * 50_000 * t)).astype('<c8')    # 50 kHz 基带音
x.tofile('cap.sigmf-data')
meta = {"global": {"core:datatype": "cf32_le", "core:sample_rate": fs, "core:version": "1.0.0"},
        "captures": [{"core:sample_start": 0, "core:frequency": fc}], "annotations": []}
json.dump(meta, open('cap.sigmf-meta', 'w'), indent=2)

g = json.load(open('cap.sigmf-meta'))['global']
y = np.fromfile('cap.sigmf-data', dtype='<c8')
f, p = signal.welch(y, fs=g['core:sample_rate'], nperseg=4096, return_onesided=False)
print('peak offset Hz', f[p.argmax()], 'abs RF Hz', fc + f[p.argmax()])
```

本机结果：峰值偏移 50048.8 Hz（分辨率约 244 Hz），与 50 kHz 一致。这里的 `fc` 是记录的中心频率，只是元数据，不代表真实设备的调谐。

**7c. 3D：生成球体 → 导出 PLY → 回读检查** ✅

```python
import numpy as np, trimesh

sphere = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
sphere.export('sphere.ply')
r = trimesh.load_mesh('sphere.ply')
print('faces', len(r.faces), 'bounds', np.round(r.bounds, 3).tolist(), 'watertight', r.is_watertight)
```

本机结果：320 个面，包围盒 ±1，闭合。

**未运行**：EEG（MNE 读 EDF）需要 EDF 样本，本机没有，未验证。
