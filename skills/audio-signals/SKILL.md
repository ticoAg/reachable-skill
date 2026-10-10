---
name: audio-signals
description: Analyze audio, speech, music and acoustic recordings; choose DSP and audio tools, preserve native waveforms and features, integrate downstream analysis or synthesis without a shared output schema. Use for recordings, WAV/FLAC/MP3, spectrum, rhythm and audio tool integration.
---

# Audio Signals

核对采样率、声道、编码与幅度单位。先检查削波、静音和解码质量，再按任务选择频谱、节奏、语音或音乐模型。

## 执行约定

1. 先确认任务和输入的实际格式、单位、采样或坐标信息；不依据扩展名猜测全部参数。
2. 按当前环境选择工具，核对安装版本与官方 API；先运行小片段，再扩展到全数据。
3. 保留输入，明确预处理带来的信息变化；区分测量事实、模型推断和假设。
4. 直接使用领域原生输出。仅在下一工具需要时转换布局、类型、单位或文件编码；不套统一结果 schema，不强制生成文本或语义标签。
5. 按任务检查数据与输出质量，用原生文件、日志或附属笔记记录参数和版本。记录形式按工具与任务决定。
6. 需要生成时，单独选择生成器并验证输出，不假设分析方法可逆。

读取 [领域配方](references/workflows.md) 获取工具示例、集成建议与检查方法。
