# 解码：表格、时间序列、IMU 与传感器

## 读取与时间检查

安装 `pandas numpy scipy`。先读表头和少量数据，确认分隔符、类型、时区、单位、设备时钟和缺失值编码。没有时间字段的表格先做表格分析，不能凭行顺序声称是规则采样。

下例假定 timestamp 自带 UTC offset，value 是已确认单位的数值：

```python
import pandas as pd
import numpy as np
from scipy import signal
raw = pd.read_csv('input.csv')
raw['timestamp'] = pd.to_datetime(raw['timestamp'], utc=True, errors='raise')
s = raw.set_index('timestamp')['value'].sort_index()
if s.index.has_duplicates or len(s) < 3:
    raise ValueError('先处理重复时间戳或过短输入')
if not np.isfinite(s.to_numpy(dtype=float)).all():
    raise ValueError('先决定缺失值和非有限值处理策略')
dt = s.index.to_series().diff().dt.total_seconds().dropna().to_numpy()  # 不用 asi8：其单位随 pandas 版本变化（pandas 3 为微秒）
if (dt <= 0).any() or not np.allclose(dt, np.median(dt), rtol=1e-3, atol=1e-9):
    raise ValueError('非规则时间，不能直接按规则采样计算 PSD')
fs = 1 / np.median(dt)
f, psd = signal.welch(s.to_numpy(dtype=float), fs=fs, nperseg=min(256, len(s)))
```

无时区时间戳先确认本地时区再 localize，不能一律当 UTC。采样 jitter 的容许值由任务决定，示例阈值不是标准。

## 让人或 LLM 看懂

- 摘要统计：`s.describe()`、缺失与重复计数、采样间隔分布。几行统计比贴原始数据更适合放进上下文。
- 图：`python scripts/render_view.py input.csv view.png --fs 100 --column value` 画波形加频谱图（规则采样才有意义）。
- 事件：`scipy.signal.find_peaks`；变化点可用 ruptures；异常按任务选方法。
- 文字结论里附上时间范围和采样率，让读者能回到原数据核对。

## 分析要点

表格：分布、重复、缺失、关联、异常，按实际字段选方法。时间序列：趋势、周期、变化点、滞后、频谱；缺失、漂移和设备重启分开处理。IMU：检查每轴量纲、坐标系、重力和校准，姿态融合需要特定模型。

`resample` 是分组加聚合，mean、sum、last 依物理意义选。插值可能制造频谱特征；长断档保留并单独报告。非规则采样可用 Lomb–Scargle，不能直接套均匀 FFT。

## 集成要点

保留 DataFrame、Series、NumPy 数组或原文件。进入模型前核对 feature 顺序、scaler 和窗口；按时间切分训练与评价，避免未来泄漏。大 CSV 分块读取，滚动统计和滤波保留跨块状态。跨传感器拼接前先校正时钟偏移与漂移。

## 来源

- [pandas 时间序列](https://pandas.pydata.org/docs/user_guide/timeseries.html)
- [pandas resample](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html)
- [SciPy 信号处理](https://docs.scipy.org/doc/scipy/reference/signal.html)
