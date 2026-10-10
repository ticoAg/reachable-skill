---
name: timeseries-signals
description: Analyze tabular data, time series, IMU, vibration and sensor streams; use pandas, NumPy and SciPy for quality checks and statistical or spectral analysis, with native DataFrame and array outputs and local tool adapters.
---

# Time Series Signals

核对列含义、时区、时钟、单位、采样间隔与缺失值。对不规则时间序列先决定采样策略，再做频谱或时序建模。

## 执行约定

1. 先确认任务和输入的实际格式、单位、采样或坐标信息；不依据扩展名猜测全部参数。
2. 按当前环境选择工具，核对安装版本与官方 API；先运行小片段，再扩展到全数据。
3. 保留输入，明确预处理带来的信息变化；区分测量事实、模型推断和假设。
4. 直接使用领域原生输出。仅在下一工具需要时转换布局、类型、单位或文件编码；不套统一结果 schema，不强制生成文本或语义标签。
5. 按任务检查数据与输出质量，用原生文件、日志或附属笔记记录参数和版本。记录形式按工具与任务决定。
6. 需要生成时，单独选择生成器并验证输出，不假设分析方法可逆。

读取 [领域配方](references/workflows.md) 获取工具示例、集成建议与检查方法。
