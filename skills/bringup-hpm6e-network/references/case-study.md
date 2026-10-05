# HPM6E8Y：从网络停滞到千兆功能回归

## 范围与证据等级

2026-10-05，本项目单块 HPM6E8Y + RTL8211F，HPM SDK 1.13.0、CPU0 300 MHz、FreeRTOS/lwIP、Windows 主机和用户水星交换机。交换机具体型号/镜像配置未确认。本文是既有记录的归纳，本次整理没有重新下载或重新执行硬件压力测试。

“已观测”指日志/抓包/寄存器或报告；“实现选择”指当前源码；“推断”仅表示有效排查方向。USB1 是应用虚拟网卡，USB2 是板载调试器，ETH0 是管理网络。另两个口的 EtherCAT/预留功能未完成，SV660N 未接入。

## 调试时间线

| 阶段 | 操作及范围 | 观察/结果 | 可以得出的结论 |
| --- | --- | --- | --- |
| 板级移植 | 核对原始网表、封装与 pinmux | ETH0 更正为 PF02–PF13、TSW 端口 3 | EVK 的可选引脚不可直接套用 |
| USB 管理 | RNDIS + USB 专属 DHCP + 只读网页，独立 ETH netif | USB 可用于观察 ETH 停滞时的诊断 | 不等于桥接或可写配置完成 |
| 多板身份 | UUID 地址块和接口角色、登记冲突检查 | 算法及单板稳定性验证 | 多板实体和 IP 分配仍未验证 |
| 直连基线 | 独立 USB 网卡、另一个子网 | 直连可用 | 网卡/子网/固件变量不同，不能只归因交换机 |
| LAN 故障 | 改回 LAN 地址并绑定主机源网卡 | 同期 ETH 30 次超时，USB 30 次成功；软件 RX 停在 17 | 故障集中于 ETH 接收路径，不能说整个系统死机 |
| 硬件快照 | 短暂 JTAG halt/read/resume；启用硬件监控 | DMA RUN，完成 FIFO 空、剩余命令 7；MAC 正常帧增长、CPU 出口溢出增长 | 不是已证实的“队列满却漏掉中断”；软件零错误没有覆盖硬件丢包 |
| 对照 1 | 只增加 ingress store-and-forward | RX 停在 673，8/8 HTTP 超时 | 单独修改无效，撤回 |
| 对照 2 | 只将 DMA 总线最大突发由 255 改为 15 | RX 停在 156，8/8 超时 | 单独修改无效，撤回 |
| 对照 3 | 保留轮询，按响应 FIFO 而非 IRQ 标志取包 | 仍停滞，未见“响应存在却无 IRQ” | FIFO 判定合理但不是充分修复，不能宣称证实丢中断 |
| 对照 4 | 中断通知任务 + 16 缓冲 | ETH/USB 分别 1000 请求通过 | 接收及时性与容量方向有效 |
| 对照 5 | 中断通知任务 + 8 缓冲 | ETH 1000 请求完成，但 USB drop +1、ETH queue-full +14 | 最终判失败；不把请求完成率当唯一验收 |
| `0.2.2-net` | 16 缓冲 + 中断通知 + FIFO 判定 + IPv4 管理过滤 | 100M 下双接口并行各 1000、3 次 RAM 重载、60 秒应用空闲恢复通过 | 百兆单板环境修复基线；精确硬件触发原因仍未知 |
| 千兆初测 | 同时宣告 100/1000FD、MAC 跟随实际速率 | 已协商 1000；一次启动有 28 次软件入队失败 | 千兆链路建立不等于资源预算充分 |
| 千兆扩池 | 消息池 8 → 24，mailbox → 32 | queue-full 消除，但一次 pbuf 耗尽 20 | 扩容不是调度问题的完整解决方案 |
| `0.2.3-net` | tcpip 优先级 4，高于 ETH 生产任务 3 | 最终千兆并行、启动、空闲恢复通过 | 本负载下接收链资源与调度改善；不是所有场景的参数处方 |

## 最终验收快照

适用范围：仅 `0.2.3-net` RAM 镜像、上述单板/交换机和测试负载。

| 检查 | 历史记录结果 |
| --- | --- |
| PHY 实际协商 | 1000 Mbps，USB/ETH 两侧状态读取一致 |
| ETH0 HTTP | 1000 请求，2 并发，8.938 s；P99 32 ms，最大 47 ms |
| USB HTTP（同时启动） | 1000 请求，1 并发，19.329 s；P99/最大 32 ms |
| 完整断言 | 页面逐字节与源码一致；错误请求；无意外重启；软件丢包/USB 超时/硬件出口溢出/帧错误未增长 |
| RAM 重新下载启动 | 连续 3 轮协商 1000，双接口与各轮 10 秒应用空闲恢复通过，错误/丢包为 0 |
| ETH HTTP 空闲恢复 | 60 秒不发 ETH HTTP、仅用 USB 观察后恢复成功；LAN 背景流量仍存在 |

**未验证**：千兆满线速/iperf、长时间负载、其他交换机、新版仅百兆对端及物理速率切换、多块板同时连接、Flash 掉电自启动、持久化配置、EtherCAT 周期与实际伺服。测试通过支持修复方向，不证明某个 PHY/TSW 硅片缺陷，也不能保证所有 LAN 负载无丢包。

## 可追溯来源

本仓库只发布归纳后的过程和结论。以下是原项目相对路径索引，**不是本仓库可下载附件**；不上传原始 LAN 报文、板卡 UUID/MAC 台账、整份 SDK 或第三方源码。

原项目 `HPM6E_MotionController/`：

- `docs/decisions/网络接口实现.txt`、`多板卡网络身份.txt`：实现边界。
- `docs/validation/交换机抓包排查.txt`、`交换机修复验证.txt`、`千兆自动协商验证.txt`：对照过程。
- `docs/validation/千兆基线/`：`gigabit-eth0.json`、`gigabit-usb.json`、`network-ram-restart.json`、`switch-idle.json`、构建/下载日志、源文件及镜像哈希清单。
- `out/reports/gigabit-pre-tuning/`：失败记录，与最终验收分开。
- `firmware/modules/ethernet/ethernet.c`、`firmware/apps/usb_web/lwipopts.h`、`firmware/modules/usb_net/`：实现依据。
- `tests/hardware/verify_usb_web.py`、`verify_ram_restart.py`、`verify_switch_idle.py`：原项目复测入口；重载脚本会中断板卡，不能不核对目标就执行。

最终 BIN SHA256：`cdb7b0153c2a22d4f879fd1fc8b57f2aebcd43aa449639d0b62ee2cb325fc103`。整理时再次计算本地发布 BIN，匹配清单；这不代表再次执行实板回归。

硬件模型参考：[HPM6E00 用户手册 Rev0.7](https://www.hpmicro.com/Public/Uploads/uploadfile/files/20250414/HPM6E00UMV07.pdf)，第 68 章，特别是 68.3.10 DMA；[HPM SDK v1.13.0](https://github.com/hpmicro/hpm_sdk/tree/v1.13.0)。本板级改动没有写入全局 SDK。
