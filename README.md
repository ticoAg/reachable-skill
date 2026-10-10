# Signal Skills

面向 AI Agent 的多类型数据与信号分析、工具使用、集成实践 skill 仓库。

从原始信号出发，调用领域程序、专业软件和模型完成分析；需要生成时，再选择合成器、仿真器或生成模型。中间处理方式开放。

**保留工具原生输出。没有统一 SIR、统一结果 schema、强制文本化，也不要求分析与生成互为逆过程。** 数组、DataFrame、MNE Raw、图像、点云、音频、工具原生文件、模型对象和自然语言都可以直接使用。接口适配只发生在确实需要连接的两个工具之间。

## Skills

| Skill | 数据与任务 | 起始工具 |
|---|---|---|
| `analyze-signals` | 识别输入、选路、跨工具集成 | 文件探测、原生 reader |
| `audio-signals` | 音频、语音、音乐、声学信号 | FFmpeg、SoundFile、librosa、SciPy |
| `visual-signals` | 图像、视频、帧与时间信息 | FFmpeg、OpenCV |
| `timeseries-signals` | 表格、时间序列、IMU、振动、传感器 | pandas、NumPy、SciPy |
| `biosignals` | EEG、ECG、EMG、EDF 等 | MNE、WFDB、NeuroKit2 |
| `rf-signals` | IQ、RF、频谱与通信录波 | SigMF、NumPy、SciPy、GNU Radio |
| `spatial-signals` | 点云、网格、深度、3D 几何 | Open3D、Trimesh、Blender |

## 安装

在支持 `SKILL.md` 的 Agent 中，把需要的 skill 文件夹复制到其 skill 搜索目录。Codex 示例（请先 clone 本仓库并进入仓库根目录）：

```bash
mkdir -p ~/.codex/skills
cp -R skills/analyze-signals ~/.codex/skills/
cp -R skills/audio-signals ~/.codex/skills/
```

也可以复制 `skills/` 中全部七个文件夹。重启或刷新客户端后，按客户端的发现机制加载。
路由 skill 不强制依赖其余 skill：只有安装了对应 skill 时才调用，否则按其索引中的工具文档执行。

各领域依赖相互独立；按任务安装，不安装一个“大而全”的环境。示例：

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install numpy scipy soundfile librosa
```

FFmpeg、GNU Radio、Blender 为独立软件。运行前核对具体版本、平台、编解码器和模型许可。仓库中的 Python 片段是使用配方，不是已对所有平台验证的封装 SDK。

## 用法

- “用 $audio-signals 分析录音中的节奏、频谱和削波，保留原始采样率。”
- “用 $rf-signals 分析这份 SigMF IQ 录波，输出 GNU Radio 可以继续处理的数据。”
- “用 $timeseries-signals 检查这份 IMU CSV 的时间戳、缺失值与异常，保留 DataFrame。”
- “用 $analyze-signals 为 EEG 和视频选择分析工具，并设计时间同步方式。”
- “把分析结果交给指定生成器；只做这个工具要求的局部适配。”

## 内容与状态

每个领域包含精简 `SKILL.md` 和按需读取的 `references/workflows.md`。
实践指南是作者整理的工程建议；示例没有被声称为生产验证案例。
基础工具文档核对日期：2026-10-10。运行时仍须检查已安装版本。
第一版不携带模型权重、用户数据、自动硬件采集或后台上传逻辑。

## 扩展

见 [CONTRIBUTING.md](CONTRIBUTING.md)。欢迎增加新模态、可复现案例、模型和专业软件的使用指南。统一的是指南的组织方式，不是数据或分析结果。
