---
name: assemble-module-connectors-3d
description: Register a module PCB against an existing footprint and prepare male headers on the module with matching female sockets on the motherboard in a KiCad copy. Use to correct module mating geometry or board spacing; does not move existing pads, assume connector procurement dimensions or export surface graphics.
---

# 单步：模块接口与母板插座装配

适用：已有 KiCad 模块 PCB、AD PcbLib 中已建好的模块封装、明确的接口位号/编号映射和模型。不会重排现有封装，也不默认把模块本体焊成排母。先明确：模块焊排针、母板焊排母，还是其他结构。

1. 用 KiCad 自带 Python 执行 `scripts/module_assembly.py register --pcb ... --library ... --footprint ... --connector U2:0 --connector U9:60 --output alignment.json`。`U9:60` 表示原引脚1对应模块焊盘61，是任务参数，不是通用编号。脚本以全部映射焊盘验证平移与孔径；不匹配时停止，不能挪焊盘来迁就模型。脚本当前只处理可由同一XY平移注册的几何。
2. 为指定接口准备方向正确、以原封装原点为原点的共享模型：模块排针向下，母板排母向上；标准 KiCad 直立双排模型可用 `scripts/normalize_connectors.py`。该辅助脚本限定其标准1/2/3脚坐标约定，其他供应商模型先核对方向和尺寸。模型文件与许可由任务取得，不随技能分发。
3. 用 `module_assembly.py assemble --plan alignment.json --male-model ... --female-model ... --male-housing-mm ... --female-housing-mm ... --output ...` 在新副本中替换指定接口的3D，并加无焊盘的模型载体。母板排母底部设为母板贴装面；模块板间距取已选壳体尺寸与插合关系，不虚构最终采购/实物验收。脚本的壳体相接关系是预览方案，有指定插合深度时先调整模型/高度参数。

验收所有映射引脚、排距、行距、Pin1、上下朝向及接合深度；源板和已有库不改变。只调整装配高度时从本步骤后半段继续，不重新导入AD或重建焊盘。辅助脚本对相同朝向和原点的双接口共用一对规范模型；不同朝向/不同封装键需要先扩展映射，不静默套用。
