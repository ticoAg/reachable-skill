# 编码：参数与文本 → 基带 IQ

只生成离线基带样本。把样本送到硬件发射机需要用户明确授权、合规的频段与功率，不在本指南范围内。

## 路线

- 测试信号：`python scripts/synth_wave.py iq.cf32 --kind complex --freq 100000 --fs 1000000 --noise 0.01`。输出是裸 little-endian complex64，无 header。
- 调制链：GNU Radio 的 Signal Source、调制和信道 blocks 离线生成。
- 数字调制：用 NumPy 写 BPSK/QPSK 等，或用 `commpy` 等库。

## 文本 → BPSK 基带（最小示例，演示用）

无同步头、无纠错、矩形脉冲，只能被同参数接收方读回：

```python
import numpy as np
sps = 8                                    # 每符号采样数
bits = np.unpackbits(np.frombuffer('hello'.encode(), dtype=np.uint8))
iq = np.repeat((2.0 * bits - 1.0), sps).astype('<c8')   # 0→-1，1→+1
iq.tofile('bpsk.cf32')
# 读回
rx = np.fromfile('bpsk.cf32', dtype='<c8').reshape(-1, sps).mean(axis=1)
print(np.packbits((rx.real > 0).astype(np.uint8)).tobytes().decode())
```

## 写成 SigMF

裸 cf32 不是完整 SigMF 记录。需要时按规范写 `.sigmf-meta`，至少包含 `core:datatype`（如 `cf32_le`）、`core:sample_rate`、`core:version`，捕获段里写 `core:frequency`。字段细节以 SigMF 规范为准。

## 检查输出

复数类型、采样率、频率是否在 Nyquist 内、功率、频偏、频谱形状。回读比较样本数与数值。

## 来源

- [SigMF 规范](https://sigmf.org/)
- [GNU Radio Signal Source](https://wiki.gnuradio.org/index.php/Signal_Source)
