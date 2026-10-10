# 编码：参数 → 生理信号

模拟数据只用于算法测试、教学和演示，不能当作真实受试者记录，也不能暗示临床真实性。

## 参数化模拟

NeuroKit2 有独立的模拟器，可按心率、时长、噪声生成 ECG、PPG、EDA、EMG、呼吸等：

```python
import neurokit2 as nk
synthetic = nk.ecg_simulate(duration=10, sampling_rate=250, heart_rate=70, random_state=42)
```

这不表示任意真实记录都能反向重建。

## 写成标准文件

- EDF：可用 MNE 的导出功能（依赖 `edfio`，核对所装版本），注意量化与单位限制。
- WFDB：`wfdb.wrsamp` 写 header 与 dat。
- 导出后回读，比较采样率、通道名、单位、数值范围和标注。合成数据上的回读结果见 [end-to-end](../end-to-end.md) 第 7d 节：EDF 使用默认 `physical_range='auto'` 时，50 µV 正弦的回读误差小于 0.001 µV；同一次 WFDB 写出的是 32 位整数。

## 检查输出

时长、峰间隔、波形形态、噪声水平、单位。模拟器返回数组不代表带有真实设备的校准单位。未做临床验证。

## 来源

- [NeuroKit2 模拟示例](https://neuropsychology.github.io/NeuroKit/examples/signal_simulation/signal_simulation.html)
- [WFDB Python](https://physionet.org/content/wfdb-python/4.1.0/)
