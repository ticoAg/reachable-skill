# 现成的 skill、工具与模型

核对日期：2026-10-10。清单来自仓库目录页和搜索结果，**未逐个安装测试**。安装前读对方的 `SKILL.md`，核对来源、许可、是否需要 API key、会不会把数据上传到云端。含隐私或受限的数据不要交给云端 API。

## 现成的 Agent Skill

| Skill | 能力 | 方向 | 备注 |
|---|---|---|---|
| [openai/skills](https://github.com/openai/skills/tree/main/skills/.curated) 的 `transcribe` | 音频转写，含说话人标注 | 解码 | 目录页只列出名称；细节读其 SKILL.md。通常需要 OpenAI key |
| 同上 `speech` | 文本转语音（OpenAI Audio API） | 编码 | 需要 `OPENAI_API_KEY`，不含自定义声音创建 |
| [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills) 的 `algorithmic-art`、`canvas-design` | 代码式生成艺术、画布设计 | 编码 | 输出图像/HTML |
| 同上 `slack-gif-creator` | 生成 GIF 动图 | 编码 | |
| 同上 `pdf`、`docx`、`pptx`、`xlsx` | 读写文档类文件 | 解码/编码 | 文档不是本仓库核心，仅在输入输出是这些格式时使用 |
| [vargHQ/skills](https://github.com/vargHQ/skills)（`varg-ai`） | 聚合 AI 视频、图像、语音、音乐生成 | 编码 | MIT；需要 `VARG_API_KEY`；本地模式需要 bun 和 ffmpeg |
| 社区：VoiceClaw（openclaw/skills） | 本地 whisper.cpp 转写 + Piper 语音回复 | 双向 | 来自聚合站，使用前读源码 |
| 社区：edge-tts（sundial-org/awesome-openclaw-skills） | 无需 key 的 TTS | 编码 | 依赖微软在线服务，文本会发送到云端 |

聚合站与目录（用来找更多 skill）：[skills.sh](https://www.skills.sh/anthropics)、[agentskills.so 媒体分类](https://agentskills.so/skills/categories/media)、[agentskill.sh](https://agentskill.sh/)。聚合站内容质量不一，不能代替审阅。

## 本地工具与模型

| 任务 | 工具 |
|---|---|
| 容器、编解码、抽帧、拼接 | FFmpeg / FFprobe |
| 语音识别 | faster-whisper、whisper.cpp、openai/whisper |
| 说话人分离 | pyannote.audio |
| 语音合成 | Piper、Kokoro、edge-tts |
| 音乐生成 | AudioCraft（MusicGen） |
| 音频分析 | librosa、SoundFile、SciPy |
| OCR | Tesseract、PaddleOCR |
| 视频镜头切分 | PySceneDetect |
| 图像生成 | Diffusers |
| 生理信号 | MNE、WFDB、NeuroKit2 |
| 射频 | SigMF、GNU Radio |
| 3D | Open3D、Trimesh、Blender |

模型权重与服务各有许可和使用条款，使用前核对。

## 选用顺序

1. 本机已安装的 skill 或 CLI 已覆盖任务 → 直接用。
2. 有可信来源的 skill（官方或维护者明确）→ 读 SKILL.md 后安装。
3. 只有聚合站条目 → 先读源码和脚本，再决定。
4. 都没有 → 用 references 里的库写最小脚本，并把脚本留在工作目录，不改动仓库。

## 贡献新条目

加入清单时写明：来源链接、核对日期、是否实测、需要的 key 与依赖、数据是否上传。未运行过的条目写“未实测”。
