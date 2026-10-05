---
name: bringup-hpm6e-network
description: Bring up or diagnose HPM6E00 TSW Ethernet with RTL8211F, FreeRTOS and lwIP, including concurrent USB RNDIS management, switch-only receive stalls, DMA completion handling, gigabit negotiation and multi-board network identity. Use for matching custom-board firmware and evidence-based network regression. Do not apply its registers, buffer counts, priorities or filters to other MACs, PHYs or stacks; it does not implement EtherCAT motion or production provisioning.
---

# HPM6E 网络联调

## 适用范围

- **实测配置**：自制 HPM6E8Y 板、HPM6E00 TSW 端口 3、RTL8211F RGMII、HPM SDK 1.13.0、CPU0 300 MHz、FreeRTOS、单 lwIP 双 netif、USB RNDIS、Windows 主机。案例日期 2026-10-05，最终固件 `0.2.3-net`，仅 RAM 运行。
- **可迁移的方法**：逐层计数、单变量对照、生产/消费队列预算、网络身份分层、固件与证据绑定。迁移到其他平台必须重新确认硬件模型和 API。
- **排除范围**：其他 HPM ENET 控制器、其他 PHY 的寄存器配置；EtherCAT 周期/运动控制；生产级安全、Flash 自启动和多板配置分配。没有验证千兆满线速。
- **版本边界**：本技能记录一个已验证基线，不要求把新 SDK 降级到 1.13.0；升级或改板后按目标源码、手册重新核对。

## 工作流程

1. 读取目标项目规则、原始网表、封装引脚表、SDK pinmux 和构建脚本。确认 USB、ETH、调试器分别属于哪个芯片及控制器。不要从同系列 EVK 推导本板引脚。
2. 记录固件版本/哈希、启动模式、PHY ID/地址、IP/掩码、主机源网卡、链路速度、交换机接线。用明确的源地址测试；不要同时更换子网、网卡和固件后只归因于交换机。
3. 在改代码前建立故障快照：PHY、MAC 正常/错误帧、TSW CPU 出口溢出、DMA 命令/响应 FIFO、软件 RX/TX、pbuf/入站消息池/邮箱失败、任务进度和启动计数。硬件监控未启用时，零计数不能证明正常。优先通过仍正常的 USB 读取诊断。
4. 按 [经验清单](references/lessons.md) 定位停止推进的层。ISR 只通知任务；完成队列状态决定待处理工作量，中断通知不是报文计数。检查 DMA 内存一致性、描述符所有权、长度和帧尾处理，再调整缓冲或调度。
5. 做单变量对照并保留失败结果。不要默认把停滞命名为“丢中断”，不要以周期复位或关闭千兆掩盖故障。是否采用某个缓冲数/过滤策略必须结合服务范围和资源预算。
6. 千兆要求同时满足 PHY 能力宣告、真实协商结果与 MAC 配置。实际链路速度从 PHY 读取；读取网页上的常量不是验收。保留支持能力，不因一次超时偷偷禁用千兆。
7. 同时回归 USB 与 ETH：页面/API、错误请求、有界并发、错误计数增量、无意外重启、启动重复性和空闲恢复。下载、复位会中断应用，只在当前任务已授权的目标板上操作；技能本身不授权设备写入。
8. 将源码、构建参数、BIN/ELF 哈希和原始报告绑定到不可覆盖的版本目录。明确区分“协商成功”“功能回归”“吞吐量”“长期稳定”“多板同时运行”和“运动验收”。

## 阅读入口

- [逐项经验与适用范围](references/lessons.md)：板级映射、DMA、协议栈资源、抓包、多板 MAC/IP、USB 隔离、工程归档。
- [2026-10-05 调试过程与验收边界](references/case-study.md)：失败对照、百兆修复、千兆调优及可追溯证据。
- [板载 HPM5301 调试器技能](../bringup-hpm5301-debugger/SKILL.md)：仅在排查 USB2 调试器首次烧录或重连时使用。

## 输出要求

交付实际修改和验证结果；对每个判断注明适用条件与证据，保留未验证项。这里的案例地址、资源数、优先级和文件布局都是局部配置，不能作为其他板卡的默认值。
