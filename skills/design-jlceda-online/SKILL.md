---
name: design-jlceda-online
description: 使用嘉立创 EDA 专业版在线编辑器及 API Gateway/本机 Bridge 创建、复制和修改工程，按用户样板整理实线连接的紧凑原理图、分区布局 PCB、匹配封装和 3D，并校验网表与变更边界。用于已有在线 EDA 联动或准备建立联动的设计任务；不替代固件、仿真、板级电气验收或 Altium/KiCad 导出专用流程。
---

# 在线嘉立创 EDA 协同设计

## 范围与工作方式

通过当前编辑器支持的交互 API 工作。先使用已连接的 API Gateway/Bridge；本机已安装客户端不等于在线编辑器已连接。用户允许时才切换桌面工程，并重新核对目标。浏览器沿用用户选择，本工作流优先 Chrome。API 连续卡住、弹窗或状态不明时再用可用的 computer-use 技能查看问题，不默认通过坐标点击绘图。

这些约定来自一次在线专业版工程协作，经过原理图/网表和局部 PCB 数据核对；不是已完成产品的通用电气方案。用户当前要求优先于本技能的布局偏好。

按任务读取：

- 连接、复制工程、API 调用及故障恢复：[api-and-projects.md](references/api-and-projects.md)。
- 原理图整理、用户样板复用、核心板符号：[schematic-style.md](references/schematic-style.md)。
- PCB 分区、连接器、器件选型和 3D：[pcb-and-components.md](references/pcb-and-components.md)。
- 重复通道紧凑布局、RS485/DI 样板及 DO 迁移：[compact-channel-layout.md](references/compact-channel-layout.md)。中心思想是优先减小单通道垂直占用，利用左右空间，在焊盘净距、本体和实际布线约束内缩小行距。
- 历史证据与不能外推的结论：[verified-lessons.md](references/verified-lessons.md)。

## 执行流程

1. **识别目标。** 读取连接窗口、`getCurrentDocumentInfo()` 和工程结构；记录工程 UUID、文档 UUID、类型和名称。复制工程可能保留文档 UUID，修改必须同时匹配 `parentProjectUuid` 与文档 UUID，不能只按标题、活动窗口或 PCB UUID 选择。
2. **保存基线。** 先读取当前源数据，保存原理图后导出关联板的网表；PCB 工作另存布局/焊盘/走线基线。备份和原始工程仅存任务本地，不随公共技能发布。
3. **遵守副本边界。** “复制一份再改”意味着创建独立工程，确认复制完成后再修改。原工程与副本的身份分别保留；以后只有用户明确要求才回到原工程修改指定内容。
4. **先做局部可核对变更。** 原理图按电路功能块连接；PCB 按实际信号流、连接器和结构约束布局。选型缺失时推进已确定部分，接口预留不能写成已完成采集电路。不要猜测 MCU 复用功能、连接器编号、器件耐压或核心板净空。
5. **保存、读回并验证。** 整理原理图后保存再导出网表；比较位号/引脚/网络，另外核对阻容值、DNP 和封装。PCB 修改后检查 DRC、实线/飞线和机械间距。既有错误与新增错误分开报告，数量相同不一定是相同错误。
6. **检查实际画面。** 优先 API 导出 PNG/SVG/PDF 查看；校验图框内排布、标签重叠、符号方向、3D 装配关系。API 返回成功不等于画面正确或电气设计完成。

## 原理图默认风格

采用用户手工确认的 CH1 式紧凑电路块：收发器在左，串联电阻、偏置/终端、保护器件沿总线依次排列；关联元件用实线连接。去耦贴近芯片，电源/接地短引线，偏置及终端电阻尽量纵向对齐，减少回折和空白。跨页、MCU 入口和集中端子可用网络标签，避免每个元件各挂一对标签。

GND 用专用接地符号；3.3V 用专用 Power/VCC 符号，但保持设计已有网络名。不要把多个不同电源域都改名为 `VCC`。重复通道先完成一个样板并核对，再迁移位置、朝向、连线和文字样式；保留目标通道的位号、Unique ID 和网络名称，以及用户样板本身。

## 可复用脚本

依赖 Python 3 标准库，无需第三方包。

```powershell
python scripts/bridge_client.py list
python scripts/bridge_client.py run --project PROJECT_UUID --document PAGE_UUID --code-file inspect.js --out snapshot.json
python scripts/eda_audit.py netlist before.json after.json
python scripts/eda_audit.py source before.json after.json --allow-id APPROVED_PRIMITIVE_ID
```

- `bridge_client.py` 按实际工程/文档筛选窗口，并在执行前后再次校验。它不是只读沙箱；`--code-file` 的内容必须在当前用户任务范围内。写操作超时后先读回，不自动重放。
- `eda_audit.py netlist` 比较完整组件集合及位号/引脚/网络，接受原始网表或 Bridge 返回的 `result.netlist`。
- `eda_audit.py source` 比较原生源记录，默认忽略文档头和画布状态，输出未经允许的图元变化。`--allow-id` 只用于事先列明的修改对象，不能把整批差异直接加入白名单。
- 脚本测试：`python -m unittest discover -s scripts/tests -v`。测试使用虚构源数据和本机模拟 Bridge，不修改 EDA 工程。

## 交付

说明具体修改了哪个工程/图页、保持了什么用户样板、网表/DRC/画面实际检查结果，以及仍未布线或待确认的设计部分。不要以“无新增 DRC”替代最终通过，也不要以同网名替代实际连通检查。
