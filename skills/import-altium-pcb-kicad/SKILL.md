---
name: import-altium-pcb-kicad
description: Import a specific Altium PcbDoc revision into KiCad while freezing the input hash and checking the native import report. Use for the AD-to-KiCad step before 3D export, including revised silkscreen; does not regenerate component models, export STEP or modify a footprint library.
---

# 单步：AD PCB 导入 KiCad

适用：已有带模型的 AD `.PcbDoc`，需要在 KiCad 继续处理或导出3D。支持目标 KiCad 的 `pcb import --format altium` CLI；本案用10.0.7。不是 LCEDA 原文件直接转换器，也不把 `.PrjPcb` 文本当 PCB。

用户给出修正版路径时，读取该路径的最新文件，做本次输入快照并记录哈希/修改时间；不能继续用上次临时导入文件。运行 `scripts/import_pcb.py --source ... --kicad-cli ... --out 新目录`。脚本不覆盖旧目录和源文件，不启动 GUI，调用原生 KiCad 导入并保留 JSON 报告。

验收：实际目标文件存在、报告无错误、源哈希不变。对重要任务另核对元件/焊盘/过孔数量、接口和3D模型；报告无错误并不等于全部尺寸或视觉通过。用户只改丝印时，下游从本步骤重跑，不重建元件封装、不改库焊盘。

输出：`Source.PcbDoc`、`Board.kicad_pcb`、`import_report.json`、`input.json`。下一步按任务选择模型装配或直接导出；本技能不自动发布或提交文件。
