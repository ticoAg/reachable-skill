# 编码：文本与参数 → 图像与视频

| 要生成 | 路线 |
|---|---|
| 精确的图表、示意图、含文字的图 | 程序化：matplotlib、Pillow、SVG（再栅格化）。文字准确度要求高时不要用扩散模型 |
| 写实或艺术图像 | 扩散模型（Diffusers 的具体 pipeline）或云端 API。条件：文本、参考图、mask、控制图，各 pipeline 支持不同 |
| 代码式生成艺术 | Anthropic 的 `algorithmic-art`、`canvas-design` skill，见 [external](../external.md) |
| 动图 | Anthropic 的 `slack-gif-creator` skill；或 Pillow 逐帧保存 GIF |
| 讲解视频、数据动画、片头字幕（代码生成） | 见下节“代码生成视频” |
| 写实或创意视频（模型生成） | 云端模型 API（如 Veo，见 [end-to-end](../end-to-end.md) 第 3 节），或 varg-ai 等聚合 skill（需要 key，见 [external](../external.md)） |
| 3D 场景渲染成图/视频 | Blender，见 [encode/spatial](spatial.md) |
| 已有帧 → 视频 | FFmpeg |

固定并记录 pipeline、权重版本、scheduler 与种子。模型特定的条件接口不要当作通用协议。

## 程序化图像（OpenCV 示例）

```python
import numpy as np, cv2
img = np.zeros((240, 320, 3), np.uint8)
cv2.putText(img, 'hello', (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
cv2.imwrite('hello.png', img)
```

## 代码生成视频

LLM 写分镜或场景代码，程序逐帧绘制，再由 FFmpeg 编码。与模型生成相比，内容精确（文字、数字、坐标、时间点都可控）、可复现、可在 CPU 上运行、不需要 API key；代价是只能做程序能画出来的东西，做不出写实画面。

| 工具 | 适合 | 说明 |
|---|---|---|
| `examples/video_code_render.py` | 标题卡、波形、柱状图等简单动画，可带音轨 | Pillow 绘帧，管道送入 FFmpeg。✅ 已实跑 |
| Manim | 数学公式、几何、讲解动画 | Python；LaTeX 公式需要另装 TeX |
| matplotlib `animation` | 数据图表随时间变化 | `FuncAnimation` + `FFMpegWriter` |
| MoviePy | 剪辑、拼接、叠字幕、混音 | 底层调用 FFmpeg |
| Remotion / Motion Canvas | 用 React / TypeScript 写的动效视频 | Node 环境；Remotion 商用有许可条件，使用前核对 |
| Blender `bpy` | 3D 场景、相机运动 | 见 [encode/spatial](spatial.md) |

分镜示例（`storyboard.json`）：

```json
{"width": 1280, "height": 720, "fps": 30,
 "scenes": [
  {"type": "title", "text": "信号编码", "sub": "code → frames → mp4", "seconds": 2},
  {"type": "wave",  "text": "Sine 3 cycles", "freq": 3, "seconds": 3},
  {"type": "bars",  "text": "结果", "values": {"A": 3, "B": 7, "C": 5}, "seconds": 3}
 ]}
```

```bash
python skills/signal-codec/examples/video_code_render.py storyboard.json out.mp4 \
  --audio melody.wav \
  --font /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
  --font /usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf
```

要点：

- FFmpeg：优先用系统的 `ffmpeg`；没有时 `pip install imageio-ffmpeg`，它自带一个静态二进制，脚本会自动找到。
- 字体：不传 `--font` 只能显示拉丁字符。中英混排要用同时覆盖两者的字体（Noto Sans CJK、思源黑体），或者传两个 `--font`，脚本按字符依次回退。
- 音轨：音频比视频短时用 `apad` 补静音，以视频长度为准。配乐可以来自 `examples/audio_code_synth.py`，旁白可以来自 TTS。
- 宽高必须是偶数（yuv420p 的要求）。
- 新增场景类型：写一个 `draw_xxx(img, scene, progress, fonts)` 函数，注册到 `DRAW` 字典。

## PNG 序列 → 视频

等尺寸帧，帧率由任务指定：

```bash
ffmpeg -framerate 24 -i frames/frame_%06d.png -c:v libx264 -pix_fmt yuv420p output.mp4
```

需要带 libx264 的 FFmpeg；yuv420p 路径要求偶数宽高。

## 检查输出

生成的视频可以用 [decode/visual](../decode/visual.md) 的抽帧拼图命令转成一张图，交给人或 VLM 检查每个场景的画面。


用 `ffprobe` 确认能解码、帧数/时长/时间基正确；检查尺寸、色彩与坐标；再检查内容是否满足提示。扩散模型输出的文字、手指、数量常出错，要看图确认。注意生成内容的许可与真实人物肖像问题。

## 来源

- [FFmpeg](https://ffmpeg.org/ffmpeg.html)
- [Diffusers text-to-image](https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/text2img)
- [Manim Community](https://www.manim.community/)
