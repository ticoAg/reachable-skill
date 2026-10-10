# EEG、ECG、EMG 与其他生理信号

## 工具选择与读取

EDF/BDF、通道与事件研究优先选择 MNE；WFDB 成组 header/dat/annotation 使用 WFDB；ECG/EDA/EMG 等处理与模拟可用 NeuroKit2。按任务在独立环境安装 `mne`、`wfdb` 或 `neurokit2`，不要强制一次安装全部。

```python
import mne
raw = mne.io.read_raw_edf('input.edf', preload=False)
print(raw.info['sfreq'], raw.ch_names)
print(raw.annotations)
# 只读有限时间片段；MNE get_data 采用 channels×samples。
sfreq = raw.info['sfreq']
x = raw.get_data(start=0, stop=min(raw.n_times, int(sfreq * 10)))
```

核对文件声明单位及 reader 的单位转换。MNE 数据通常使用 SI 单位；按具体通道类型核对，不要把所有通道都当电压。

```python
import wfdb
record = wfdb.rdrecord('records/100', sampfrom=0, sampto=3600)
x = record.p_signal
fs = record.fs
units = record.units
```

记录名不带 `.hea` 或 `.dat`；文件必须成组存在。核对 physical/digital 模式、每导联增益、单位和通道顺序。不要在没有说明的情况下把物理值再除以 ADC 增益。

## 分析流程

先检查掉线、平直、饱和、坏通道、工频和运动伪迹。按分析目标决定 reference、滤波、epoch 与事件标注策略；带通与重参考会改变波形。心电峰值检测需要核对采样率和异常片段，EEG 的坏通道与 ICA 选择不能仅凭默认参数。

NeuroKit2 示例，要求 `ecg` 已明确是合适的单导联、有限值数组，`fs` 是真实采样率：

```python
import neurokit2 as nk
signals, info = nk.ecg_process(ecg, sampling_rate=fs)
```

保留工具自己的 `signals` DataFrame 和 `info` 字典。检测到的峰与诊断结论不同；标注、仪器信息和人工核对可能影响解释。此 skill 处理研究数据，不提供自动诊断流程。

## 集成建议

从 MNE 导出到模型时，核对 channel order、单位、shape、窗口和 annotation 的时间基。仅传 ndarray 可能丢掉参考信息，必要时保留 MNE 对象或原文件及实验笔记。EDF 等导出存在量化或元信息限制，回读比较数值与标注。跨 ECG、EEG、视频同步按实际时钟而不是默认“同时开始”。

## 生成

NeuroKit2 有独立的参数化生理信号模拟器；不意味着任意原始记录都可逆向重建。

```python
import neurokit2 as nk
synthetic = nk.ecg_simulate(duration=10, sampling_rate=250,
                            heart_rate=70, random_state=42)
```

检查时长、峰间隔、波形、噪声和目标单位。模拟器返回数组不意味着它已具备真实设备的校准单位或病理真实性；不要把模拟数据作为患者真实记录。

## 官方来源

- [MNE reader](https://mne.tools/stable/api/reading_raw_data.html)
- [WFDB Python](https://physionet.org/content/wfdb-python/4.1.0/)
- [NeuroKit2 ECG API](https://neuropsychology.github.io/NeuroKit/functions/ecg.html)
- [NeuroKit2 模拟示例](https://neuropsychology.github.io/NeuroKit/examples/signal_simulation/signal_simulation.html)

示例是配方，实际结果需要数据质量与领域核对；未宣称临床验证。
