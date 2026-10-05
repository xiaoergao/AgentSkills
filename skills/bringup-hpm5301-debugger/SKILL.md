---
name: bringup-hpm5301-debugger
description: Bootstrap and diagnose an HPM5301IEG1 onboard debugger using CherryDAP HSLink-Lite, UART ROM ISP and CMSIS-DAP v2 JTAG. Use for matching custom-board pin mapping, USB2 not enumerating before firmware, unreliable TTL recovery, image-layout verification and repeated USB reconnect failures. Do not assume HSLink-Pro, EVK-Lite, UF2 bootloaders, other chip packages or target external-Flash algorithms share this configuration.
---

# HPM5301 板载调试器首次烧录与恢复

## 适用范围

- **已验证对象**：HPM6E8Y 自制板，U6=`HPM5301IEG1` QFN48，USB2 连接 U6，U3 为 HPM6E 主控。CherryDAP 中 HSLink-Lite 2.4.7，上游提交 `d95619bbdc8647e67283e4dd0e0deadf9d7decdb`，本板修订 `hpm6e8y-kit-r2-usb-reconnect-nrst`，HPM SDK 1.13.0。
- **适用任务**：首次 UART ISP、同板固件恢复、CMSIS-DAP v2 JTAG 连接、软件重连队列故障、版本/备份/读回证据整理。
- **排除范围**：其他封装、EVK-Lite/HSLink-Pro 的直接刷写；通用 USB ROM ISP 说明；UF2 拖拽更新；主控外部 Flash 算法；CDC 串口桥和任意高速 JTAG 的已验证承诺。
- **迁移要求**：以下地址、管脚、复位极性和电源顺序仅适用于该板及镜像。新板先核对 ROM、原理图、生产资料、已有启动器和固件布局，再选择实现。经验不是批量擦写授权。

## 工作流程

1. 区分三个对象：调试器 U6 的固件、主控 U3 的应用、主机上的调试工具。确认实际 USB 接口和芯片型号，不能把主控 USB1 的 HID/ROM 下载行为套用到 USB2。
2. 选择匹配的上游项目和本板 BSP。CherryDAP 是本案的源码仓库，HSLink-Lite 是其中项目，不是二选一的竞争协议。按 [逐项经验及过程](references/lessons-and-case.md) 核对引脚、供电级、NRST 和构建目标。
3. 烧写前确认任务已有目标板写入授权、镜像哈希、Flash 起始地址和该板自己的备份。未知布局先只读识别/备份，不拿另一块板的全 FF 备份代替。保留已验证固件与失败日志。
4. 本板首次 ROM ISP 使用 UART0。3.3 V TTL TX/RX 交叉并共地，不接 TTL VCC；先保证接触可靠。全供电断开后按住 SW5 给 USB2 上电，松开，再连接 TTL USB。详细映射见参考文档。
5. 本案使用默认 115200、小分包、帧间间隔；改变波特率需要 ROM 协议握手，不是只改 PC 串口设置。超时后先恢复电气连接与完整 ISP 状态，再重新建立通信。
6. 匹配镜像按确认后的地址写入，完整读回逐字节比较，再执行 ROM 冷复位。检查 USB 枚举和连续 CMSIS-DAP/JTAG 重开；一次枚举或一次连接成功不算重连验证。
7. 用主控自己的 ELF 测试 halt/PC/step/resume。恢复目标运行后结束会话。明确分开 RAM 加载、Flash 下载、物理冷启动、串口桥和长期稳定性，逐项报告已验证与未验证。

## 交付组织

对这种独立板载调试器，可在产品旁保留一个 `HPM5301_Debugger/`：`firmware/` 放已验收镜像和清单，`source/` 放来源版本/补丁，`scripts/` 放可重定位工作流，`docs/` 放接线和恢复步骤，`records/` 放该板备份与冻结记录，`logs/`/`build/` 放后续生成物。外部 SDK 路径由参数指定，不复制全局 SDK 或覆盖已验收发布包。

本文为经验技能，不附可直接烧写所有板卡的 BIN 或批量恢复脚本。首先读取 [各项陷阱、历史过程和验收边界](references/lessons-and-case.md)。
