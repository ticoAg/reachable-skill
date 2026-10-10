# 解码：音频、语音与音乐

目标：把录音变成可检查的数值、可看的图和可读的文本。

## 读取与检查

FFprobe 确认容器、编码、采样率、声道和时长；SoundFile 读 libsndfile 支持的格式，其他格式用 FFmpeg 解码。

```bash
ffprobe -v error -show_streams -show_format -of json input.wav
```

```python
import soundfile as sf
import numpy as np
from scipy import signal
x, sr = sf.read('input.wav', dtype='float32', always_2d=True)   # frames × channels
if len(x) < 2 or not np.isfinite(x).all():
    raise ValueError('空、过短信号或非有限数据')
f, psd = signal.welch(x, fs=sr, nperseg=min(2048, len(x)), axis=0)
```

PSD 的量纲取决于输入幅度；未校准录音不能宣称测得声压级。librosa 0.11 的 `load` 默认重采样并转 mono，需要保留时写 `librosa.load(path, sr=None, mono=False)`；多声道为 channel×time，与 SoundFile 的布局相反。

## 让人或 LLM 看懂

| 要什么 | 做法 |
|---|---|
| 一眼看全貌 | `python scripts/render_view.py input.wav view.png`：波形加频谱图。多模态模型可直接读该 PNG。长录音用 `--start`、`--duration` 分段 |
| 说了什么 | ASR：faster-whisper、whisper.cpp、OpenAI Whisper 或云端 API。保留时间戳和低置信片段 |
| 谁在说 | 说话人分离，如 pyannote.audio（模型有使用条款，需核对） |
| 音乐结构 | librosa 的 onset、beat、chroma；先试一个片段 |
| 质量问题 | 有限值、静音、峰值与削波、声道差异；归一化之前先记录 |

转录不是对全部声音内容的分析：背景声、音乐、环境事件需要另外的方法。节拍估计在变速或弱节奏音乐上可能失效。峰频与音高不是同一概念。

已有现成 skill：OpenAI 的 `transcribe`（转写与说话人标注）见 [external](../external.md)。

## 集成要点

声道、时间轴、采样率要显式传给下一工具。滤波或重采样前决定是否保持相位；离线零相位滤波不适合实时。分块处理需要重叠或滤波状态。不要用 MP3 等有损中间文件传递精确测量波形。

## 来源

- [SoundFile](https://python-soundfile.readthedocs.io/en/0.13.1/)
- [librosa.load](https://librosa.org/doc/0.11.0/generated/librosa.load.html)
- [SciPy Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)
- [FFprobe](https://ffmpeg.org/ffprobe.html)
