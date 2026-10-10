# 音频、语音与音乐

## 选工具与读取

使用 FFprobe 确认容器、编码、采样率、声道和时长；SoundFile 适用于其 libsndfile 支持的格式，其他格式按安装能力用 FFmpeg 解码。

```bash
ffprobe -v error -show_streams -show_format -of json input.wav
```

先在独立环境安装 `numpy scipy soundfile librosa`。保留原采样率和声道：

```python
import soundfile as sf
import numpy as np
from scipy import signal
x, sr = sf.read('input.wav', dtype='float32', always_2d=True)
if len(x) < 2 or not np.isfinite(x).all():
    raise ValueError('空、过短信号或非有限数据')
f, psd = signal.welch(x, fs=sr, nperseg=min(2048, len(x)), axis=0)
```

`x` 是 frames×channels；`f` 与 `psd` 是原生数组。PSD 的量纲取决于输入幅度，未校准录音不能宣称测得声压级。

librosa 0.11 的 `load` 默认重采样并转 mono。需要保留时显式 `y, sr = librosa.load(path, sr=None, mono=False)`；核对所装版本。多声道 librosa 输入通常采用 channel×time，来自 SoundFile 的数据要按调用要求转置。

## 分析路线

- 质量：有限值、静音、峰值与削波、声道差异；归一化之前记录幅度情况。
- 声学：Welch PSD、STFT、包络、频带能量。明确窗口与 hop；峰频与音高不是同一概念。
- 音乐：librosa 的 onset、beat、chroma 等；先用一个片段检查，再推到全曲。节拍估计在变速或弱节奏音乐上可能失效。
- 语音：先核对 ASR 模型要求的声道、采样率与分段方式；保留时间戳和低置信片段。转录不是对全部声音内容的分析。

## 工具集成建议

把声道、时间轴和采样率显式传到下一工具。滤波或重采样之前决定是否需保持相位；离线零相位滤波不适合实时处理。chunk 间需要重叠或滤波状态，不能直接拼接独立处理结果。避免用 MP3 等有损中间文件传递精确测量波形。

## 生成路线

程序化音频：NumPy/SciPy 生成振荡器、包络和噪声，再用 SoundFile 写 WAV。音乐模型：AudioCraft/MusicGen 接收其版本支持的文本或旋律条件，返回音频张量；根据模型自己的采样率保存。两者不共享条件格式。

```python
import numpy as np
import soundfile as sf
sr = 48000
n = int(sr * 1.0)
t = np.arange(n) / sr
wave = 0.2 * np.sin(2 * np.pi * 440 * t)
sf.write('tone.wav', wave, sr, subtype='PCM_16')
```

检查输出时长、声道、编码、削波和边缘点击；音乐的风格、节奏需另行评价。不要把生成音频视为源录音的逆变换。

## 来源与状态

以下为官方文档支持的起始方法；配方是工程建议，运行时核对本地版本。

- [SoundFile 0.13.1](https://python-soundfile.readthedocs.io/en/0.13.1/)
- [librosa.load 0.11](https://librosa.org/doc/0.11.0/generated/librosa.load.html)
- [SciPy Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)
- [FFprobe](https://ffmpeg.org/ffprobe.html)
- [MusicGen 使用与依赖](https://github.com/facebookresearch/audiocraft/blob/main/docs/MUSICGEN.md)
