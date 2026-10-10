# 图像与视频

## 读取与检查

安装 `opencv-python`（无 UI 服务使用 `opencv-python-headless`，二者不要共装）；FFmpeg/FFprobe 单独安装。

```bash
ffprobe -v error -show_streams -show_format -of json input.mp4
```

读取单张图像并保留 BGR 原生对象，只有消费者需要 RGB 时再转换：

```python
import cv2
image = cv2.imread('input.png', cv2.IMREAD_UNCHANGED)
if image is None:
    raise ValueError('图像读取失败')
# 下面转换仅适用于三通道 BGR；灰度、BGRA、16-bit 图另行处理。
if image.ndim == 3 and image.shape[2] == 3:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
```

视频用 `cv2.VideoCapture`；检查 `isOpened()`，逐次判断 `read()` 的成功标记，最后 `release()`。OpenCV 的属性读取受后端影响；变帧率视频精确同步用解码器 PTS/time_base，不能用 frame_index / 平均 FPS 替代真实时间戳。

## 分析路线

质量：分辨率、像素深度、曝光、模糊、压缩伪影。结构：轮廓、分割、几何与光流。语义：按任务选择 OCR、检测器或多模态模型；它们的结果可以保留为各自的框、mask、对象或文本。

抽帧示例（只适合预览，不保留完整帧时间语义）：

```bash
mkdir -p frames
ffmpeg -i input.mp4 -vf fps=1 frames/frame_%06d.png
```

采样可能漏掉短事件，必要时增加密度或结合事件检测。高位深图像避免默认缩成 8-bit；检查 EXIF 方向和 alpha 通道。

## 集成建议

记录 resize、padding、crop 的坐标变换，把检测框/mask 映回原图。时间模型必须接收按时间排序的帧。音视频同步保留流各自的起点和 PTS，不只用文件时长。大型视频流式解码，避免一次性装入所有帧。模型的标签、置信度不可直接当作测量事实。

## 生成与变换

FFmpeg 编码已有帧，OpenCV 程序化生成图像，Blender 渲染场景，Diffusers 的具体 pipeline 进行条件图像生成。选择和固定 pipeline、权重、scheduler 与种子；确认模型支持文本、参考图、mask 或控制图中的哪一种条件。不要将模型特定的条件接口升级成全仓库协议。

已有等尺寸 PNG 序列编码为视频（帧率由任务明确指定）：

```bash
ffmpeg -framerate 24 -i frames/frame_%06d.png -c:v libx264 -pix_fmt yuv420p output.mp4
```

需要安装支持 libx264 的 FFmpeg；常见 yuv420p 路径要求偶数宽高。验证输出可解码、帧数/时长/时间基、色彩与坐标一致性，再检查任务所需内容。

## 官方来源

- [FFprobe](https://ffmpeg.org/ffprobe.html)
- [FFmpeg](https://ffmpeg.org/ffmpeg.html)
- [OpenCV 视频](https://docs.opencv.org/4.11.0/dd/d43/tutorial_py_video_display.html)
- [OpenCV 颜色空间](https://docs.opencv.org/4.11.0/df/d9d/tutorial_py_colorspaces.html)
- [Diffusers 条件与原生返回值](https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion/text2img)

这些示例是使用配方，未声明在所有编解码后端或模型上实测。
