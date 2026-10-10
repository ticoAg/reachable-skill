# 编码：参数与文本 → 3D 几何与渲染

| 要生成 | 路线 |
|---|---|
| 基本几何、参数化模型 | Trimesh `creation`、Open3D `create_*`，或 CadQuery / OpenSCAD（可写成代码再导出） |
| 场景、材质、动画、渲染 | Blender 的 Python（`bpy`）或命令行 |
| 文本/图像 → 3D | 3D 生成模型，需单独核对权重许可、支持的条件（文本、单图、多视角）与输出格式 |
| 深度图 → 点云 | 用相机内参反投影（Open3D `create_from_depth_image`） |

让 LLM 写参数或建模脚本，再由几何库生成；不要让 LLM 直接输出网格顶点列表。

```python
import trimesh
sphere = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
sphere.export('sphere.ply')
```

`radius` 的单位由场景约定，PLY 未必带单位。

## 渲染

已有 Blender 场景离线渲染：

```bash
blender --background scene.blend --render-output ./renders/frame_ --render-frame 1
```

参数按顺序执行：先载入 scene，再设置输出，render 动作放最后。检查相机、分辨率、色彩管理和帧范围。图像正确不代表几何满足工程约束。

## 检查输出

回读 bounds、点/面数量、是否闭合、法线方向、单位；渲染结果看图确认。3D 打印或仿真用途要用对应软件验证。

## 来源

- [Trimesh quickstart](https://trimesh.org/quick_start.html)
- [Open3D 点云教程](https://www.open3d.org/docs/release/tutorial/geometry/pointcloud.html)
- [Blender CLI 渲染](https://docs.blender.org/manual/en/latest/advanced/command_line/render.html)
