# 解码：点云、网格、深度与 3D 数据

## 工具与读取

点云与配准用 Open3D；网格属性与格式转换用 Trimesh；场景、材质、渲染用 Blender。分别安装 `open3d` 或 `trimesh`；Blender 用其独立应用和内置 Python。

```python
import open3d as o3d
import numpy as np
cloud = o3d.io.read_point_cloud('input.ply')
points = np.asarray(cloud.points)
if not len(points) or not np.isfinite(points).all():
    raise ValueError('空点云或非有限坐标')
bounds = cloud.get_axis_aligned_bounding_box()
```

保留 `cloud` 原生对象；颜色、法线与坐标有关联，只传 points 会丢属性。

```python
import trimesh
mesh = trimesh.load_mesh('input.stl')
print(mesh.bounds, mesh.is_watertight)
```

多对象 GLTF/GLB 用 `load_scene` 并考虑节点变换，不要默认能无损合成一张网格。STL 没有可靠的物理单位，需另行确认。

## 让人或 LLM 看懂

- 数值摘要：点/面数量、包围盒尺寸、单位假设、是否闭合、法线与颜色是否存在、点密度。
- 图：用 Open3D 离屏渲染或 matplotlib 画多视角截图（正视、侧视、俯视）并保存为 PNG，再交给多模态模型。截图要标注坐标轴方向。
- 在无显示环境，Open3D 的可视化可能需要 headless 渲染配置，先在小文件上试。
- 体积、质量估计先检查闭合性、方向与密度条件。

## 分析要点

检查单位、坐标手性、轴向、外参、有限值、法线和点密度；深度图重建还需相机内参和深度尺度。配准先考虑初值、重叠、尺度和外点，再选 ICP 等；收敛标志不能证明配准正确。降采样、去噪、补洞与网格重建会改变原始几何，保留原数据与变换。

## 集成要点

跨工具交换检查材质、纹理、单位和节点变换是否丢失；导出后回读，比较 bounds、点/面数量和关键方向。

## 来源

- [Open3D 点云读取](https://www.open3d.org/docs/latest/python_api/open3d.io.read_point_cloud.html)
- [Open3D 点云教程](https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html)
- [Trimesh quickstart](https://trimesh.org/quick_start.html)
- [Trimesh typed loaders](https://trimesh.org/trimesh.exchange.load.html)
