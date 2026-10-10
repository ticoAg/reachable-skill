# 解码：图像与视频

目标：让人或多模态 LLM 能读懂画面内容与时间结构。

## 读取与检查

安装 `opencv-python`（无 UI 服务用 `opencv-python-headless`，二者不要共装）；FFmpeg/FFprobe 单独安装。

```bash
ffprobe -v error -show_streams -show_format -of json input.mp4
```

```python
import cv2
image = cv2.imread('input.png', cv2.IMREAD_UNCHANGED)   # BGR 原生对象
if image is None:
    raise ValueError('图像读取失败')
if image.ndim == 3 and image.shape[2] == 3:              # 灰度、BGRA、16-bit 另行处理
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
```

检查 EXIF 方向和 alpha 通道；高位深图像不要默认缩成 8-bit。视频用 `cv2.VideoCapture`，检查 `isOpened()` 与每次 `read()` 的返回值，最后 `release()`。变帧率视频要精确同步时，用解码器的 PTS/time_base，不用 frame_index / 平均 FPS。

## 让人或 LLM 看懂

| 要什么 | 做法 |
|---|---|
| 图像内容 | 多模态模型直接读图；大图先缩小并记录缩放比例 |
| 图中文字 | OCR：Tesseract、PaddleOCR 或云端 API |
| 目标与位置 | 检测/分割模型，保留各自的框、mask |
| 视频概览 | 抽帧拼图（contact sheet），见下 |
| 视频里说了什么 | 抽出音轨，走 [decode/audio](audio.md) 的 ASR，保留时间戳 |
| 镜头切换 | PySceneDetect，或 FFmpeg 的 `select='gt(scene,0.4)'` |

抽帧拼图，每 5 秒一帧，排成 4 列（阈值与布局按任务调整）。该 filter 链已用 imageio-ffmpeg 自带的 FFmpeg 7.0.2 实跑；没有系统 FFmpeg 时可 `pip install imageio-ffmpeg`，用 `imageio_ffmpeg.get_ffmpeg_exe()` 取得路径：

```bash
ffmpeg -i input.mp4 -vf "fps=1/5,scale=320:-1,tile=4x4" -frames:v 1 sheet.png
```

采样可能漏掉短事件；必要时加密或结合事件检测。逐帧抽取：

```bash
mkdir -p frames && ffmpeg -i input.mp4 -vf fps=1 frames/frame_%06d.png
```

## 集成要点

记录 resize、padding、crop 的坐标变换，把框和 mask 映回原图。时间模型必须接收按时间排序的帧。音视频同步保留各流的起点和 PTS。大视频流式解码。模型的标签与置信度不是测量事实。

## 来源

- [FFprobe](https://ffmpeg.org/ffprobe.html)
- [FFmpeg](https://ffmpeg.org/ffmpeg.html)
- [OpenCV 视频](https://docs.opencv.org/4.11.0/dd/d43/tutorial_py_video_display.html)
- [OpenCV 颜色空间](https://docs.opencv.org/4.11.0/df/d9d/tutorial_py_colorspaces.html)
