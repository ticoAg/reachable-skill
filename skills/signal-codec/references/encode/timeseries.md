# 编码：参数与文本 → 时间序列

## 参数化仿真

用趋势、周期、噪声和状态模型生成可控的合成序列：

```python
import numpy as np, pandas as pd
rng = np.random.default_rng(7)
t = np.arange(1000) / 100
values = np.sin(2 * np.pi * 3 * t) + rng.normal(0, 0.05, len(t))
generated = pd.Series(values, index=pd.to_timedelta(t, unit='s'), name='amplitude')
```

命令行版本：`python scripts/synth_wave.py sensor.csv --kind sine --freq 3 --fs 100 --noise 0.05 --seed 7`，输出 `time_s,value` 两列 CSV。

## 其他路线

- 多轴、有状态的数据（IMU、设备日志）：按设备模型写仿真，或用领域仿真器。
- 从自然语言描述生成序列：让 LLM 写出参数（频率、幅度、噪声、事件时刻），再由代码生成数值。不要让 LLM 直接输出成千上万个采样值。
- 条件时序生成模型（如扩散或自回归）需要核对其训练领域与输入窗口。

## 检查输出

采样率、单位、范围、分布、频谱、多轴相关性。只匹配均值与方差不能证明保留了真实动态结构。合成数据要在文件名或附注中标明是合成的，不要混入真实记录。

## 来源

- [pandas 时间序列](https://pandas.pydata.org/docs/user_guide/timeseries.html)
- [NumPy random Generator](https://numpy.org/doc/stable/reference/random/generator.html)
