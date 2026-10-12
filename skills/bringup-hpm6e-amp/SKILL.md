---
name: bringup-hpm6e-amp
description: Implement or diagnose HPM6E80 dual-core AMP motion firmware with CPU1 EtherCAT/PDO and CPU0 FreeRTOS/lwIP management, including secondary-image loading, shared-memory ownership, startup readiness and reproducible hardware performance comparisons. Use for matching HPM6E projects; verify address maps and SDK behavior before migration. Does not authorize flashing or motion, apply to SMP, or certify electrical stability and machine safety.
---

# HPM6E 双核 AMP 与运动性能验证

## 适用范围

- 实测案例：自制 HPM6E8Y、HPM SDK 1.13.0、独立 FreeRTOS 内核、CPU1 CherryECAT/TSW/PDO/轨迹，CPU0 lwIP/USB RNDIS/UDP/HTTP/WS，两个 SV660N，Windows 主机，Debug/O0，软件 double。日期 2026-10-12，修正版 0.25.1-amp。
- 可迁移方法：镜像与执行地址区分、跨核所有权、启动握手、故障证据、单变量频率对照及验收分层。具体地址、任务优先级、槽容量和主频必须重新确认。
- 不适用：直接作为其他 HPM 系列、SMP、其他 EtherCAT 栈的寄存器/链接脚本模板。两轴空载不代表八轴、真实压机、长期稳定或电压温升验收。
- 现场动作须由当前用户授权。本技能不提供通用可烧写镜像，不要求为了阅读经验重启实板。

## 工作流程

1. 核对板型、电源、SDK、启动器、当前源码与冻结包。先读目标规则和 [双核经验](references/lessons.md)，建立可回退基线；保留现有未提交修改和旧包。
2. 分清执行地址、CPU 普通访问地址、DMA/ROM/API 的地址语义。用源码/手册核对，再做最小实板装载验证。链接成功和同名转换函数存在都不能证明跨核普通 `memcpy` 正确。
3. 明确每个外设、IRQ、DMA描述符、邮箱、配置Flash和运行状态的唯一所有者。IPC传值/偏移，不传本地指针、RTOS句柄或跨核可执行字符串地址；以两核独立编译的布局描述核对ABI。
4. 区分“次核已启动”“桥接ready”“完成扫描/绑定”“首次有效PDO”“可以运动”。启动期间的幂等初始化允许有限重试，不能类推为运动命令自动重发。
5. 按 [案例与证据索引](references/case-study.md) 保留成功与失败：两核寄存器、镜像字节、IRQ所有权、发布序号、反馈年龄、CRC与配置读回。故障定位后恢复设备运行；调试暂停不能混入运行态PDO性能统计。
6. 性能使用 [对照方法与结果](references/performance.md)：同板/轴/轨迹/编译参数/客户端负载，至少区分单核300、双核300、双核480。报告板内规划耗时、端到端延迟、实际负载和PDO周期分布，不用总MHz冒充实际加速。
7. 分别记录编译/host回归、下载读回、软件复位、物理断电、两轴空载、混合/八轴实物、机械带载与长期电气稳定。将源码、两核ELF、资源、Flash布局及证据绑定，按范围给出开发基准建议。

项目需要采用发布约定时，按实际目标调整 [可选规则](../../rules/hpm6e-amp-release.md)，不要复制成所有嵌入式工程的硬性策略。
