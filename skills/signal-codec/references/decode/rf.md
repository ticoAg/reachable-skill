# 解码：射频、复数 IQ 与通信录波

只做离线分析。采集与发射硬件操作需用户明确授权，并遵守当地无线电法规。

## 读取

优先用 SigMF 的 metadata/data 配对文件或采集软件原生格式。SigMF 的 dtype 描述 real/complex、位宽与端序；捕获分段可以改变中心频率等参数。安装 `sigmf numpy scipy` 时核对版本。

对已确认的单通道 `cf32_le` 裸样本：

```python
import numpy as np
from scipy import signal
# 仅适用于连续、无 header/偏移/额外字节的 cf32_le payload
iq = np.memmap('capture.sigmf-data', dtype='<c8', mode='r')
fs = 1_000_000  # 示例值；必须从 metadata 或采集配置读取
if len(iq) < 2 or not np.isfinite(iq[:min(len(iq), 4096)]).all():
    raise ValueError('空、过短或非有限样本')
segment = np.asarray(iq[:min(len(iq), 1_000_000)])
f, psd = signal.welch(segment, fs=fs, nperseg=min(4096, len(segment)), return_onesided=False)
order = np.argsort(f)
f, psd = f[order], psd[order]
```

整数 IQ、Q/I 顺序、多通道、非零 payload offset、header 和不合规数据不能直接套用。合规复数 SigMF 样本中 I 与 Q 交错，I 在前。

## 让人或 LLM 看懂

- 频谱图：`python scripts/render_view.py` 面向实数信号。复数 IQ 要自己画双边谱，例如 `plt.specgram(segment, Fs=fs, NFFT=1024)`（matplotlib 对复数输入画双边谱，核对所装版本）。
- 数值摘要：采样率、中心频率、时长、DC 偏移、削波比例、占用带宽、突发起止时间。
- 先查 DC offset、削波、缺失/突变、I/Q 不平衡，再做 PSD、瀑布图、占用带宽、突发检测。
- `f` 是基带频率；要绝对 RF 频率，加上该捕获段的中心频率。未校准 PSD 不能标成 dBm。
- 解调前确认制式、符号率、频偏、滤波与帧同步；不要仅凭频谱形状断定调制类型。已知协议可用对应解码器（如 multimon-ng、dump1090 等，按协议选）。

## GNU Radio

GNU Radio Companion 可连 File Source → DSP blocks → GUI/File Sink。核对 block 的 item type、变速因子、tag 与 message 接口；stream 与 message 不能直接互连。

## 集成要点

保留 complex array、SigMF 配对文件或 flowgraph。交给 GNU Radio 的 complex File Source 前核对端序与格式。纯样本文件不携带中心频率和采样率，按下游工具需要另存配置。大录波分块时保留滤波、定时恢复和帧解析状态，并检查块边缘事件。

## 来源

- [SigMF 规范](https://sigmf.org/)
- [SigMF Python quickstart](https://sigmf.readthedocs.io/en/stable/quickstart.html)
- [GNU Radio Signal Source](https://wiki.gnuradio.org/index.php/Signal_Source)
- [SciPy Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)
