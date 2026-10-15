# PCB 模块库的独立修改步骤

适用 LCEDA Pro→AD→KiCad STEP→已有 AD PcbLib，以及从匹配网表生成模块 SchLib 的工作。并非其他 EDA 格式的通用导入器，也不授权变更电气设计或发布用户库。

| 修改内容 | 从哪里重做 | 必须保留 |
| --- | --- | --- |
| 丝印或外层走线修订 | import-altium-pcb-kicad → 装配副本 → export-kicad-outer-3d → prepare-step-soldermask → attach-step-altium-footprint | 最新源哈希、已有封装焊盘/原点 |
| 只调整阻焊不透明度 | attach-step-altium-footprint 的 set_opacity.py | 所有 STEP 几何流 |
| 过孔是否显示或导出层选择 | export-kicad-outer-3d → 拆分 → 绑定 | 实际 PCB 过孔和焊盘 |
| 排针/排母及插合高度 | assemble-module-connectors-3d → 导出 → 拆分 → 绑定 | 目标库编号/孔位，模型基准面 |
| 原理图引脚 Name 修订 | build-altium-module-symbol，extract 后 mode=names | 引脚编号、位置、分部、已有封装链接 |
| 完整重建空白符号 | build-altium-module-symbol，mode=build | 其他库元件和字体表 |

2026-10-15 验证案例：Windows，KiCad10.0.7、AD25.8.1、cadquery-ocp8.x。实例接口为 U2/U9 各2×30、2.54 mm，偏移0/60；目标120个信号焊盘+4孔，符号7个分部；这些是实例常量，换板必须重新求出。原生 AD 读回确认120引脚、124焊盘、2个 Body，阻焊不透明度约0.7；二进制比较证实其他符号/封装不变。KiCad 完整外观预览已查看，原生 AD 3D 画面未人工复核；这些不构成生产插合验收。

脚本验证覆盖：实际 PcbDoc 导入、120焊盘配准、两类官方连接器模型规范化、装配副本、隐藏554过孔的外层 STEP 导出、上下阻焊拆分、Body原生生成、单封装合并与重复合并不增加模型数量、仅改透明度时几何流不变、最新 LCEDA 工程120引脚全名提取与原生 SchLib 保存/合并。输入板卡及模型不随公共技能发布。

已遇到的问题：

- XCAF 实例名可能只有 `=>[...]`，应同时检查引用的产品定义名，否则阻焊漏分。
- ASCII junction 用 Path.resolve() 后会暴露中文真实路径，原生脚本输出路径检查应基于用户选定的可用 ASCII 路径；源文件快照可用真实路径。
- SchLib 原 Header 同时含 UTF-8 和 MBCS 字段，查找目标 LibRef 时不要将所有字段统一 decode('utf8')。本脚本以 ASCII 目标名按字节匹配，不触碰其他元件的编码。
- AD 原生另存可能重写整库、排序和元数据；使用它生成指定记录，再合回原库以保留用户其他数据。压缩内嵌 STEP 与外部原始 STEP 不能重复全部纳入 Git 交付。
- 本案用原生 RemovePCBObject 移除旧 Body 后，另存仍出现同名旧记录。绑定准备改为在工作副本中按已验证的记录边界移除待替换 Body，之后原生只新增；最终合并再次检查每个名称恰有一个记录。原始库不会被这个准备动作修改。
