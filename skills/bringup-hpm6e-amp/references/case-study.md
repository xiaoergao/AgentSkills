# 双核升级过程与证据索引

## 适用范围

仅 [本技能配置](../SKILL.md) 的2026-10-12记录。数字、源码路径和现场结论用于说明决策过程，不构成其他芯片的启动处方。原项目`HPM6E_MotionController`的身份/Flash备份和SDK不随本仓库发布。

## 过程

1. 用户要求先提交/打tag：基线`a4f272fc`、`v0.24.1-multi-pre-amp-20261012`，保留原0.24.1单核回退包。
2. 0.25.0完成CPU角色拆分、带界限IPC、Flash次核容器、300/480MHz构建；41项host回归通过，但只有离线证据。
3. 初次实板写后verify成功而HTTP不可用；通过异常CSR和两处相同的指令字证明本地ILM访问别名，修正CPU0复制系统窗口。初版明确废弃，旧包留作证据。
4. 改善快照复制及冲突时的有效值/年龄保留；在晚启动CPU1下补JOG种子重试。重复运动不参与初始化重试。
5. 先300再480，对两轴空载定位/反向接管/多轴共同周期/JOG做回归；临时UDP只应用RAM，测试后恢复。
6. 480另测动态限扭、Touch/TouchNow惯性触发偏移、四种V3状态、SDO正常/abort。真实触碰、压力或回零接线不在该验收中。
7. 对照前后256KiB配置，逐字节一致；最后两核480、ready、两轴取消使能且无报警。只完成短时验收，USB2链可靠性和长期电气仍留项。
8. 扩大性能轮次先受USB2打开失败阻碍，仅重插USB2未恢复，完整板卡断电重连后恢复。依次重刷单核300/双核300/双核480，全部写后校验成功；同一脚本共288批次、576个规划计时、34287个有效HTR2样本，保留不利的尾延迟对照。
9. ELF符号证实replan从单核AXI迁到CPU1 ILM，收益不能纯归因核数。最终双接口核验480/ready、绑定有效、两轴空闲取消使能；RAM UDP恢复，配置代次未变。本轮未再次halt读取全配置分区，不把第7项旧哈希证据冒充新读取。

## 原项目证据位置

这些是原工程相对路径索引，**不是本仓库可下载附件**。不同用户不一定有该工程，复用时要重新采集自己的证据。

| 内容 | 原工程索引 |
| --- | --- |
| 初版离线基线及未覆盖项 | `docs/validation/0.25.0双核软件升级与离线验收_2026-10-12.txt` |
| 修正、实板回归与边界 | `docs/validation/0.25.1双核下载与两轴空载验证_2026-10-12.txt` |
| 异常CSR和别名对照 | `out/validation/amp-hardware-20261012-1530/boot-debug-core0.log`、`local-alias-evidence.log` |
| 播种、快照、RPC真实C验证 | `tests/host/amp_client_native.c`、`test_amp_native.py`及该目录回归日志 |
| 镜像与物理复制映射 | `firmware/modules/amp/amp_client.c`、`amp_image_address.h` |
| 四格式、SDO、持续观察 | `tests/hardware/verify_amp_extra.py`、该目录`extra-480-repeat.json`；第一次恢复失败记录为`extra-480.json` |
| 动态限扭、惯性触发偏移 | `tests/hardware/verify_amp_contact.py`、该目录`contact-480.json` |
| 同板性能对照 | `tests/hardware/benchmark_amp.py`、`out/validation/amp-performance-20261012` |

## 尚未覆盖

真实芯片电压低谷和温升、仪器测频、长期老化、八轴/多品牌实物、机械带载、物理断电引导、真实报警联停、最坏延迟/运行栈、Flash保存掉电中断、TouchNow下一PDO目标冻结的专项逐帧核验。不要把host八轴测试或1kHz短时零丢样写成以上项目已通过。
