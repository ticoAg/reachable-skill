# 解码：EEG、ECG、EMG 与其他生理信号

本指南处理研究数据，不提供诊断流程。

## 工具与读取

EDF/BDF、通道与事件研究用 MNE；WFDB 成组 header/dat/annotation 用 WFDB；ECG/EDA/EMG 等处理用 NeuroKit2。按任务在独立环境安装 `mne`、`wfdb` 或 `neurokit2`。

```python
import mne
raw = mne.io.read_raw_edf('input.edf', preload=False)
print(raw.info['sfreq'], raw.ch_names)
print(raw.annotations)
sfreq = raw.info['sfreq']
x = raw.get_data(start=0, stop=min(raw.n_times, int(sfreq * 10)))   # channels × samples
```

核对文件声明单位与 reader 的单位转换。MNE 通常用 SI 单位，按通道类型核对，不要把所有通道都当电压。

```python
import wfdb
record = wfdb.rdrecord('records/100', sampfrom=0, sampto=3600)
x, fs, units = record.p_signal, record.fs, record.units
```

记录名不带 `.hea` 或 `.dat`，文件必须成组存在。核对 physical/digital 模式、增益、单位和通道顺序，不要把物理值再除以 ADC 增益。

## 让人或 LLM 看懂

- 概览图：MNE 的 `raw.plot()`、`raw.compute_psd().plot()`，保存为 PNG 交给人或多模态模型。
- 数值摘要：通道名、采样率、时长、事件列表、坏通道、各通道幅度范围。
- 单导联时序可用 `python scripts/render_view.py` 画波形与频谱图（需先导出为 `.npy` 并指定 `--fs`）。
- 事件与节律：峰值检测结果、心率、频带功率，注明方法与参数。检测到的峰不等于诊断结论。

## 分析要点

先查掉线、平直、饱和、坏通道、工频和运动伪迹。reference、滤波、epoch 与事件策略由分析目标决定；带通与重参考会改变波形。ECG 峰值检测要核对采样率和异常片段；EEG 的坏通道与 ICA 选择不能只靠默认参数。

```python
import neurokit2 as nk
signals, info = nk.ecg_process(ecg, sampling_rate=fs)   # ecg: 单导联、有限值；fs: 真实采样率
```

保留工具自己的 `signals` DataFrame 与 `info` 字典。

## 集成要点

导出给模型时核对 channel order、单位、shape、窗口和 annotation 时间基。只传 ndarray 会丢参考信息，必要时保留 MNE 对象或原文件。EDF 导出有量化与元信息限制，回读比较数值与标注。多模态同步按实际时钟，不默认“同时开始”。

## 来源

- [MNE reader](https://mne.tools/stable/api/reading_raw_data.html)
- [WFDB Python](https://physionet.org/content/wfdb-python/4.1.0/)
- [NeuroKit2 ECG API](https://neuropsychology.github.io/NeuroKit/functions/ecg.html)
