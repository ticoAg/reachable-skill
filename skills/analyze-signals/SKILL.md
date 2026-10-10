---
name: analyze-signals
description: Route raw heterogeneous signals and datasets to domain analysis tools and skills; plan preprocessing, native-output integration and optional generation. Use for unfamiliar modalities, multimodal inputs, selecting signal-processing software or connecting analysis pipelines without requiring a shared IR or result schema.
---

# Analyze Signals

## 工作流程

1. 识别任务：检查、分析、理解、变换、生成，或其组合。不要默认需要文本化或生成。
2. 用文件签名、header、领域 reader 或采集参数辨认输入；确认任务真正需要的单位、时间、采样与空间信息。缺失参数影响结果时先询问。
3. 根据下表选择已安装的领域 skill；没有安装时，根据 [工具与集成索引](references/integration.md) 使用官方工具文档。
4. 先做最小原生读取与质量检查，再选 DSP、专业软件、模型或组合。不要仅因能调用 LLM 就把原始数值信号直接转成文本。
5. 为每一条工具连接检查接收方所需的 dtype、layout、单位、时间、文件格式与边界。只做必要的局部转换。
6. 保留工具原生结果；按任务交付数组、表、图、领域对象、文件或说明。不要求字段一致，不引入统一 SIR，不要求所有任务生成语义。
7. 若涉及输出生成，单独匹配合成器、仿真器、渲染器或生成模型的条件，再用目标领域方法验证。

| 输入 | 已安装时调用 |
|---|---|
| 音频、语音、音乐 | `$audio-signals` |
| 图像、视频 | `$visual-signals` |
| 表格、时序、IMU、振动 | `$timeseries-signals` |
| EEG、ECG、EMG | `$biosignals` |
| RF、IQ、通信录波 | `$rf-signals` |
| 点云、网格、深度、3D | `$spatial-signals` |

遇到未覆盖的模态时先寻找该领域原生 reader 与专业分析工具，再按照本流程接入；不要声称已支持任何可能的信号。
