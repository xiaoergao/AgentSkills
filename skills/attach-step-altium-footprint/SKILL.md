---
name: attach-step-altium-footprint
description: Add or replace named embedded STEP bodies in one existing Altium PcbLib footprint without changing its pads, origin, other primitives or other footprints. Supports independent mask opacity edits and byte-preserving library merge after native AD authoring.
---

# 只更新一个封装的 3D

适用：Windows、可运行脚本的 Altium、Python 3 + olefile。原生写入在 AD25.8.1 验证；其他版本先小样。输入模型已按现有库原点、旋转和安装平面配准。此步骤不改焊盘、不补电气引脚、不修整板布局，也不负责 STEP 的装配配准。

1. 对库计算 SHA256 并保留原件。`prepare_bind.py --library EXISTING.PcbLib --footprint NAME --recipe bodies.json --out ASCII_NEW_DIR` 生成副本与原生 DelphiScript；recipe 为 `{"bodies":[{"file":"Main.step","opacity":1.0},{"file":"Soldermask.step","opacity":0.7,"color_bgr":2709778}]}`，模型路径相对 recipe。文件名是替换键，后续修改沿用同名。待替换的模型若旧库使用不同名称，应明确列入配方或另做迁移，不能自动删掉其他 Body。
2. 执行 `run-command.txt` 的原生 AD 命令；日志必须包含 `SAVED`，并核验 Authored.PcbLib 存在。使用 `DoFileSave('')` 保存 PcbLib。遇到脚本错误检查具体日志/错误，最多修复后重试两次；不结束用户 AD 会话。脚本只操作副本。
3. `merge_models.py --original ORIGINAL --authored Authored.PcbLib --footprint NAME --recipe bodies.json --out NEW.PcbLib` 仅替换同名 Body 和对应压缩模型流。保留所有其他 primitive 字节；仅当被替换的旧模型不再被任何 Body 使用时移除其内嵌数据，避免反复修改越变越大。
4. 原生 AD 读回确认焊盘数、Body 数和透明度；用 KiCad 导入或几何清单比较全部焊盘编号/位置/尺寸/孔径及原点。校验最终库大小。安装前再次核对用户原库 SHA，存在并发修改则重新合并。

只有透明度变化时，用 `set_opacity.py --library INPUT --footprint NAME --model-name Soldermask.step --opacity 0.7 --out NEW`，不重导 STEP。此脚本保留记录长度，遇到非固定三位小数格式会拒绝；这种情况用原生 API 更新。记录 opacity 是不透明度，不要把 30% 透明写为 0.3。

真实 PCB/库/STEP 不纳入公共技能仓库。交付报告写明原/新字节数、压缩模型数量、实际通过的数据检查及尚未完成的画面检查；不要把 API 读回当作人工 3D 画面验收。

原生接口依据：[Altium PCB API](https://www.altium.com/documentation/altium-dxp-developer/pcb-api-design-objects-interfaces-reference)。
