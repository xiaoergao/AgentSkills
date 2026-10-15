---
name: build-altium-module-symbol
description: Build or rename an Altium module schematic symbol from a verified LCEDA MCU symbol and module connector netlist. Preserve complete MCU multiplexed pin Names while using module pad Designators and linking the existing PCB footprint.
---

# 模块符号与主控引脚同名

适用：LCEDA Pro `.epro2` ZIP 内含 `.epru` 的 SYMBOL 记录、匹配修订的 PADS 风格 `.tel` 网表、已有同名空白 SchLib 元件，以及经核对的接口→模块焊盘偏移。Windows/Altium 原生脚本在25.8.1验证。当前生成器要求元件名和引脚文字为 ASCII；其他字符需显式处理脚本编码。不是截图识别、电气自动设计或任意格式原理图转换器。

1. `extract_pin_names.py --epro PROJECT --netlist TEL --symbol-uuid MCU_SYMBOL_UUID --mcu U3 --connector U2:0 --connector U9:60 --rail GND --rail +5V --rail +3.3V --out NEW.json`。接口偏移是用户当前库的编号规则，不是任意模块默认规则。脚本通过实际网络追溯 MCU 球号，从该球号原始 `Pin Name` 复制完整名称，包含 GPIO 和所有复用功能；不能仅用 `OLED_SDA` 等板级网络名替代。Designator 仍用模块焊盘号，不能换成 MCU BGA 球号。
2. 对滤波器/串阻导致的跨网连接，必须核对原理图通道后显式传 `--through-net OUTSIDE:MCU_NET`；脚本不猜器件内部连接。保留模块电源轨命名，不把共享电源网络随机对应某颗 MCU 电源脚。任何未解析或多个 MCU 球号歧义都会停止。
3. `prepare_symbol.py --library SOURCE.SchLib --name MODULE --footprint FOOTPRINT --pins NEW.json --mode build --out ASCII_NEW_DIR` 生成副本与脚本。build 只接受零引脚草稿，按 PA～PF 分组并加电源/其他单元，所有引脚可见；完整长 Name 不截短。非 GPIO 保守设 Passive，电源设 Power，GPIO 设 IO，不猜动态复用方向。执行 run-command.txt 后确认日志 SAVED。
4. 下次只改 Name 时用 `--mode names`，按 Designator 匹配，保持引脚位置、分部和已有模型链接，出现缺失或多余编号则停止。不因名称变化重建用户已排版的符号。
5. `merge_symbol.py --original SOURCE.SchLib --authored Authored.SchLib --name MODULE --pins NEW.json --out NEW.SchLib` 仅合并该元件 Data，更新该元件 PartCount 及全库 Weight；其他符号与全局字体表字节保持不变。此工具面向没有额外 PinTextData 等辅助流的本技能输出，遇到这种流停止，改用专门兼容处理。

验收：源工程/网表哈希、每个模块编号唯一且匹配现有 PCB、全部 Name 与选定 MCU 源符号一致、显式电源例外和滤波通道有据可查；原生 AD 重新打开核对实际120等本案计数及模型链接。数字120、接口位号、UUID和端口数量只属于本次实例，应从当前输入重新计算。布局画面应另行检查，不能以日志替代视觉验收。

原生接口依据：[Altium Schematic API](https://www.altium.com/documentation/altium-dxp-developer/schematic-api-design-objects-interfaces-reference)。
