# 点云、网格、深度与 3D 数据

## 工具与原生读取

点云/配准选择 Open3D；网格属性和格式转换选择 Trimesh；场景、材质、渲染选择 Blender。分别安装 `open3d` 或 `trimesh`，Blender 用其独立应用和内置 Python。

```python
import open3d as o3d
import numpy as np
cloud = o3d.io.read_point_cloud('input.ply')
points = np.asarray(cloud.points)
if not len(points) or not np.isfinite(points).all():
    raise ValueError('空点云或非有限坐标')
bounds = cloud.get_axis_aligned_bounding_box()
```

保持 `cloud` 原生对象，颜色、法线与坐标有关联；只传 points 可能丢失属性。

```python
import trimesh
mesh = trimesh.load_mesh('input.stl')
print(mesh.bounds, mesh.is_watertight)
```

多对象 GLTF/GLB 场景需要考虑 `load_scene` 与节点变换；不要默认所有输入都可无损变成一张网格。STL 通常无法提供可靠的物理单位，单位需另外确认。

## 分析与集成

检查单位、坐标手性、axis、外参、有限值、法线和点密度；深度重建还需相机内参及深度尺度。体积/质量估计先检查闭合性、方向与密度条件。配准先考虑初值、重叠、尺度和外点，再选 ICP/其他方法；单看收敛标志不能证明配准正确。

降采样、去噪、补洞和网格重建会改变原始几何，保留原数据与变换。跨工具交换检查材质、纹理、单位和节点变换有没有丢失；导出后回读并比较 bounds、点/面数量和关键方向。

## 生成

Open3D/Trimesh 可程序化创建几何；Blender 根据场景和参数渲染；3D 生成模型需要单独核对其权重和支持的 text/image/geometry 条件。

```python
import trimesh
sphere = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
sphere.export('sphere.ply')
```

radius 的单位由当前场景决定，PLY 未必带单位定义。

已有 Blender 场景离线渲染：

```bash
blender --background scene.blend --render-output ./renders/frame_ --render-frame 1
```

Blender 命令参数按顺序执行，scene 应在覆盖输出参数之前载入，render 动作放最后。检查渲染相机、分辨率、色彩管理和帧范围；图像正确不代表 underlying geometry 满足工程约束。

## 官方来源

- [Open3D 点云读取](https://www.open3d.org/docs/latest/python_api/open3d.io.read_point_cloud.html)
- [Open3D 点云教程](https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html)
- [Trimesh quickstart](https://trimesh.org/quick_start.html)
- [Trimesh typed loaders](https://trimesh.org/trimesh.exchange.load.html)
- [Blender CLI 渲染](https://docs.blender.org/manual/en/latest/advanced/command_line/render.html)

以上是官方工具入口与工程建议，未声明对全部格式和渲染后端实测。
