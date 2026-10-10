# 编码：文本与参数 → 图像与视频

| 要生成 | 路线 |
|---|---|
| 精确的图表、示意图、含文字的图 | 程序化：matplotlib、Pillow、SVG（再栅格化）。文字准确度要求高时不要用扩散模型 |
| 写实或艺术图像 | 扩散模型（Diffusers 的具体 pipeline）或云端 API。条件：文本、参考图、mask、控制图，各 pipeline 支持不同 |
| 代码式生成艺术 | Anthropic 的 `algorithmic-art`、`canvas-design` skill，见 [external](../external.md) |
| 动图 | Anthropic 的 `slack-gif-creator` skill；或 Pillow 逐帧保存 GIF |
| 数学/讲解动画 | Manim |
| 文本 → 视频 | 云端模型 API，或 varg-ai 等聚合 skill（需要 key，见 [external](../external.md)） |
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

## PNG 序列 → 视频

等尺寸帧，帧率由任务指定：

```bash
ffmpeg -framerate 24 -i frames/frame_%06d.png -c:v libx264 -pix_fmt yuv420p output.mp4
```

需要带 libx264 的 FFmpeg；yuv420p 路径要求偶数宽高。

## 检查输出

用 `ffprobe` 确认能解码、帧数/时长/时间基正确；检查尺寸、色彩与坐标；再检查内容是否满足提示。扩散模型输出的文字、手指、数量常出错，要看图确认。注意生成内容的许可与真实人物肖像问题。

## 来源

- [FFmpeg](https://ffmpeg.org/ffmpeg.html)
- [Diffusers text-to-image](https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/text2img)
- [Manim Community](https://www.manim.community/)
