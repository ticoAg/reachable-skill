---
name: signal-codec
description: Decode signals (audio, speech, music, images, video, time series, EEG/ECG, RF/IQ, point clouds, 3D) into forms an LLM or a person can understand, and encode text, parameters or other content into signals (speech, music, images, video, waveforms, IQ, 3D). Picks existing tools and community skills, keeps native outputs, no shared schema. Use for recordings, sensor data, captures, "what is in this file", text-to-speech/image/video/waveform, or choosing signal tools.
---

# Signal Codec

两类能力，各自独立选工具：

- **解码（decode）**：原始信号 → 人或 LLM 能读懂的东西（转写、统计、事件、图、描述）。
- **编码（encode）**：文本、参数或其他内容 → 信号（语音、音乐、图像、视频、波形、IQ、3D）。

两类能力不要求互为逆过程。能解码某种信号，不代表能生成它；反之亦然。

## 工作流程

1. **判断方向。** 用户要“看懂/分析”走解码；要“做出/合成/渲染”走编码；两者都要就分别执行。
2. **识别输入。** 运行 `python scripts/probe.py <file>`（仅标准库）得到格式、ffprobe 流信息和建议阅读的 reference。扩展名只是提示；采样率、单位、时钟要来自文件头或采集记录，缺失且影响结果时先问用户。
3. **读对应的 reference**，只读用到的那一个：

| 模态 | 解码 | 编码 |
|---|---|---|
| 音频、语音、音乐 | [decode/audio](references/decode/audio.md) | [encode/audio](references/encode/audio.md) |
| 图像、视频 | [decode/visual](references/decode/visual.md) | [encode/visual](references/encode/visual.md) |
| 表格、时序、IMU、振动 | [decode/timeseries](references/decode/timeseries.md) | [encode/timeseries](references/encode/timeseries.md) |
| EEG、ECG、EMG | [decode/biosignals](references/decode/biosignals.md) | [encode/biosignals](references/encode/biosignals.md) |
| RF、IQ、通信录波 | [decode/rf](references/decode/rf.md) | [encode/rf](references/encode/rf.md) |
| 点云、网格、深度、3D | [decode/spatial](references/decode/spatial.md) | [encode/spatial](references/encode/spatial.md) |

4. **需要完整调用链时**（VLM 看图、文生图/视频、TTS、音乐、ASR，或端到端的信号处理）读 [end-to-end](references/end-to-end.md)。其中标明“已实跑”的代码在本机验证过；标明“未实跑”的需要先配置 API key。
5. **先找现成的。** 互联网上已有的 skill、CLI 和模型优先于自己写。清单与取舍见 [external](references/external.md)。安装第三方 skill 前先读它的 `SKILL.md`，核对来源与许可。
6. **跨工具连接**（读数组布局、时间对齐、坐标变换等）见 [integration](references/integration.md)。只在相连的两个工具之间做局部适配。

## 解码的交付方式

让 LLM 或人理解信号，常用三种派生视图，按任务选，不必都做：

- **数值事实**：采样率、时长、峰值、缺失、事件时间等，直接引用工具输出。
- **可视图**：`python scripts/render_view.py in.wav out.png` 生成波形加频谱图，供人或多模态模型查看。视频用抽帧拼图（见 decode/visual）。
- **文本**：转写、OCR、描述、摘要。

区分三类内容：测量事实、模型推断、假设。把有损摘要交给 LLM 后，LLM 的回答不再是原始测量。不要直接把几十万个原始采样值塞进上下文。

## 编码的交付方式

脚本 `python scripts/synth_wave.py out.wav --kind chirp --freq 200 --freq-end 4000` 可生成测试用的正弦、方波、扫频、噪声（WAV、CSV 或裸 cf32 IQ）。语音、音乐、图像、视频等内容生成走 references 中的工具与外部 skill。生成后必须检查：格式能解码、时长/尺寸/采样率符合要求、没有削波，再检查内容是否符合意图。随机生成要记录种子与模型版本。

## 约定

- 保留工具原生输出（数组、DataFrame、MNE Raw、图像、点云、音频文件等），不引入统一 schema 或强制文本化。
- 保留原始输入；重采样、滤波、降采样等预处理会改变信息，要说明。
- 先在小片段上跑通，再扩展到全量。
- 生物信号只用于研究数据处理，不做诊断。RF 只做离线分析与基带生成；发射与硬件操作需用户明确授权并遵守当地法规。
- 示例是使用配方。`scripts/` 中的三个脚本已在合成数据上运行过；其余未声称在所有平台和版本上验证。
