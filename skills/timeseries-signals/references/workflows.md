# 表格、时序、IMU 与传感器

## 读取与时间检查

安装 `pandas numpy scipy`。先读取表头和少量数据，确认分隔符、类型、时区、单位、设备时钟和缺失值编码。没有时间字段的表格先做表格分析，不能凭行顺序声称是规则采样。

下面示例假定 timestamp 自带 UTC offset，value 是已确认单位的数值：

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
dt = np.diff(s.index.asi8) / 1e9
if (dt <= 0).any() or not np.allclose(dt, np.median(dt), rtol=1e-3, atol=1e-9):
    raise ValueError('非规则时间，不能直接按规则采样计算 PSD')
fs = 1 / np.median(dt)
f, psd = signal.welch(s.to_numpy(dtype=float), fs=fs,
                      nperseg=min(256, len(s)))
```

无时区时间戳应先确认本地时区再 localize；不能一律当 UTC。容许的采样 jitter 应由任务决定，示例中的阈值不是全局标准。

## 分析路线

表格：统计分布、重复、缺失、关联与异常；按实际字段选择方法。时间序列：趋势、周期、变化点、滞后与频谱；分开处理缺失、漂移和设备重启。IMU：检查每轴量纲、坐标系、重力和校准；姿态融合还需要特定模型和传感器条件。

`resample` 是时间分组加聚合；选 mean、sum、last 应依变量的物理意义。插值可能制造频谱特征；长断档保留并单独报告。非规则采样可按任务选 Lomb–Scargle 或保留原时间做模型，不能直接套均匀 FFT。

## 集成建议

保留 DataFrame、Series、NumPy 数组或原存储文件。进入模型前核对 feature 顺序、scaler 和窗口；训练/评价按时间分割，避免未来泄漏。大 CSV 分块读取；滚动统计和滤波保留跨块状态。跨传感器拼接之前先校正时钟偏移与漂移。

## 生成

用参数化趋势、周期、噪声和状态模型产生可控仿真时序，或用领域条件生成器。示例只生成一个合成传感器 Series，不模拟真实设备全部性质：

```python
rng = np.random.default_rng(7)
t = np.arange(1000) / 100
values = np.sin(2 * np.pi * 3 * t) + rng.normal(0, 0.05, len(t))
generated = pd.Series(values, index=pd.to_timedelta(t, unit='s'), name='amplitude')
```

检查采样、单位、范围、分布、频谱及多轴相关性；只匹配均值方差不能证明生成数据保留了真实动态结构。

## 官方来源

- [pandas 时间序列](https://pandas.pydata.org/docs/user_guide/timeseries.html)
- [pandas resample](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html)
- [SciPy 信号处理](https://docs.scipy.org/doc/scipy/reference/signal.html)

这些是工具文档与工程建议；插值和规则采样阈值须按实际任务验证。
