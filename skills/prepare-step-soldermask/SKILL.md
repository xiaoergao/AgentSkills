---
name: prepare-step-soldermask
description: Split a KiCad colored STEP export into opaque assembly and separate soldermask STEP bodies, with a measured mounting Z translation and an opacity recipe for Altium. Use after outer-layer export when the mask alone must be translucent.
---

# 独立准备阻焊与装配模型

适用：具有命名装配层级的 KiCad STEP，Python 3 + cadquery-ocp 8.x。只处理几何分组、颜色和给定安装平移；不改 PCB、电气对象或库焊盘，不从扁平匿名网格恢复层。

执行 `scripts/split_mask.py --step input.step --z-lift-mm MEASURED --opacity 0.7 --out NEW_DIRECTORY`。Z 必须从连接器安装基准、PCB 面及源 STEP 坐标实测求出，不能照抄案例高度；穿板引脚最低点不是外壳贴装面。

脚本同时检查实例名和引用的产品定义名。KiCad 实例可能叫 `=>[...]`，仅查实例名会漏掉 soldermask。至少找到上下两层阻焊才输出；保留 XCAF 引用、各零件颜色及共享几何。STEP 几何本身不等于已应用透明度；输出 `bodies.json` 中的 opacity 必须在后续 Altium Body 属性或 KiCad 模型实例上设置。0.7 表示 70% 不透明，主总成始终 1.0。

只有透明度修改时直接更新库中阻焊 Body 的属性即可，无需重导几何；丝印或走线改变时从导入/导出步骤重做，再替换两个模型。脚本不会覆盖输出目录。迁移到其他导出器/OCP 版本时先核对命名及顶底面范围。
