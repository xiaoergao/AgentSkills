---
name: export-kicad-outer-3d
description: Export a prepared KiCad PCB as STEP with selected outer copper, pads, top/bottom silkscreen and optional soldermask, hiding vias only in an export copy when requested. Use for surface-detail changes and 3D re-export; does not alter the source PCB, mate connectors or update an Altium library.
---

# 单步：按图层导出 KiCad 3D

适用 KiCad 原生PCB和支持 `--include-tracks --include-pads --include-silkscreen --include-soldermask` 的 CLI，本案10.0.7；其他版本先查 CLI help。输入已有正确器件装配，不负责修正机械结构或原理图。

按用户要求选择导出内容。顶底走线使用 `--include-tracks`，不要加 `--include-inner-copper`。焊盘用 `--include-pads`，丝印用 `--include-silkscreen`；盖油几何用 `--include-soldermask`。铜皮/铺铜不是走线的同义词，只有要求时加 `--include-zones`。STEP 中颜色/几何不能保证达到渲染器的所有纹理效果。

用户要求不显示过孔时，在专用导出副本中移除 VIA，再导出；源 PCB 的过孔和布线不变。仅关闭 `--cut-vias-in-body` 不会移除 `--include-tracks` 带出的过孔铜体。

运行 `scripts/export_outer_step.py --pcb ... --kicad-cli ... --kicad-python ... --out 新目录 --origin XxYmm [--hide-vias] [--soldermask]`。origin 来自当前模块与封装的配准，不是每块板默认0；不确定时先完成对齐。

验收源哈希未变、输出存在、日志成功；有盖油时分别识别两个面并检查丝印与铜的Z层次。透明度属于后续材质/Body设置，不能把“导出了阻焊”称作“已70%不透明”。输出 `Export.step` 与清单，后续只改外观时可从这里重跑，不重新导入/绑定未改变的元件。
