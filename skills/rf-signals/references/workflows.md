# 射频、复数 IQ 与通信录波

## 读取

优先使用 SigMF metadata/data 配对文件或采集软件的原生格式。SigMF 的 dtype 描述 real/complex、位宽和端序；metadata 的捕获分段可以改变频率等参数。安装 `sigmf numpy scipy` 时核对具体版本。

对已确认的单通道 `cf32_le` 裸样本可以使用：

```python
import numpy as np
from scipy import signal
# 仅适用于连续、无 header/偏移/额外字节的 cf32_le payload。
iq = np.memmap('capture.sigmf-data', dtype='<c8', mode='r')
fs = 1_000_000  # 示例假定值；实际必须从 metadata 或采集配置读取
if len(iq) < 2 or not np.isfinite(iq[:min(len(iq), 4096)]).all():
    raise ValueError('空、过短或非有限样本')
segment = np.asarray(iq[:min(len(iq), 1_000_000)])
f, psd = signal.welch(segment, fs=fs, nperseg=min(4096, len(segment)),
                      return_onesided=False)
order = np.argsort(f)
f, psd = f[order], psd[order]
```

`fs` 的例值不是默认设备采样率。整数 IQ、Q/I 顺序、多通道、非零 payload offset、header 和 non-conforming 数据不能直接套此 reader。对于符合规范的复数 SigMF 样本，I 与 Q 交错且 I 在前。

## 分析

先查 DC offset、削波、缺失/突变和 I/Q 不平衡，再做两侧 PSD、瀑布图、占用带宽与突发检测。`f` 为基带频率，若要绝对 RF 频率，使用对应捕获段的中心频率；PSD 未校准时不能标成 dBm。解调前确认制式、符号率、频偏、滤波与帧同步；不要从频谱形状直接声称确定调制类型。

GNU Radio Companion 可以连接 File Source → DSP blocks → GUI/File Sink。block 的 item type、rate-changing factor、tag 和 message 接口分别核对；stream 与 message 不能直接当同一种连接。离线分析不等于硬件采集或发射授权。

## 集成建议

保留 complex array、SigMF 配对文件或 flowgraph。将 complex64 文件交给 GNU Radio 的 complex File Source 之前核对端序与该平台格式。导出文件的中心频率、采样率不会自动随纯样本传递，按该工具需要保存配置。大录波分块时保留滤波、定时恢复和帧解析状态，检测块边缘事件。

## 生成

先用 NumPy 生成基带测试 IQ，或用 GNU Radio Signal Source 与调制/信道 blocks 产生离线样本。参数条件是频率、振幅、调制、符号率、噪声与信道等，不要求文本。

```python
rng = np.random.default_rng(7)
fs = 1_000_000
t = np.arange(100_000) / fs
wave = 0.2 * np.exp(2j * np.pi * 100_000 * t)
wave += 0.01 * (rng.standard_normal(len(t)) + 1j * rng.standard_normal(len(t)))
wave.astype('<c8').tofile('synthetic.cf32')
```

此文件是裸 cf32 payload，不是完整 SigMF 记录；要用 SigMF 时另按其规范写 metadata。检查复数类型、采样率、频率是否在 Nyquist 范围、功率、频偏和频谱。硬件 sink 需要另行确认设备配置与用户任务。

## 官方来源

- [SigMF 规范](https://sigmf.org/)
- [SigMF Python quickstart](https://sigmf.readthedocs.io/en/stable/quickstart.html)
- [GNU Radio Signal Source](https://wiki.gnuradio.org/index.php/Signal_Source)
- [SciPy Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)

以上为读取与集成配方，未声明已在具体射频硬件上运行。
