# AgentSkills

按项目架构和任务选择规则与 Skills。这里的规则是工程行为约定，不是命令权限文件；不要把所有规则直接合并到每个项目的 `AGENTS.md`。

本仓库保存可复用技能、工程规则和有证据的调试经验。**每一个技能、注意事项和经验都必须说明自己的适用范围；一次项目成功不能自动升级为通用规则。** 仓库维护约定见 [AGENTS.md](AGENTS.md)。

## 选择索引

| 项目或任务 | 选择 | 适用边界 |
| --- | --- | --- |
| AD PCB 修订后重新导入 KiCad | [import-altium-pcb-kicad](skills/import-altium-pcb-kicad/SKILL.md) | 单个 PcbDoc 快照、原生导入与错误报告；不重建封装 |
| 从 KiCad 导出上下丝印、外层走线/焊盘、阻焊，隐藏过孔 | [export-kicad-outer-3d](skills/export-kicad-outer-3d/SKILL.md) | 只改导出副本；不包含内层铜，不在本步骤应用透明度 |
| 模块排针向下、底板排母向上，配准已有库焊盘 | [assemble-module-connectors-3d](skills/assemble-module-connectors-3d/SKILL.md) | 已核对双排连接器编号/尺寸，按多个焊盘求共同原点；不改实际生产 PCB |
| 仅阻焊半透明，其余器件不透明 | [prepare-step-soldermask](skills/prepare-step-soldermask/SKILL.md) | 命名 XCAF STEP 拆主总成与上下阻焊，使用实测安装 Z |
| 仅给已有 PcbLib 封装添加/替换 3D 或调整阻焊透明度 | [attach-step-altium-footprint](skills/attach-step-altium-footprint/SKILL.md) | 原生 AD 创建记录、逐流合并；焊盘、原点和其他封装不变 |
| 模块原理图引脚 Name 与主芯片完整复用功能名称一致 | [build-altium-module-symbol](skills/build-altium-module-symbol/SKILL.md) | LCEDA 符号+网表追溯；模块焊盘编号保留；支持空白草稿构建及后续只改 Name |
| 立创 PCB/Altium 导出缺少 3D、正面元件悬空、整板模型无法逐件编辑、模型体积过大 | [update-lceda-altium-3d](skills/update-lceda-altium-3d/SKILL.md)、[坐标与脚本](skills/update-lceda-altium-3d/references/workflow.md)、[案例与限制](skills/update-lceda-altium-3d/references/case-study.md) | 匹配的 LCEDA Altium PcbDoc 和可按位号识别的 STEP；Windows/AD 原生绑定，按封装共享几何；不从截图恢复电气设计，不强制 KiCad 转换，预览高度及最终画面需分别确认 |
| SDK 风格 .NET 应用的构建、测试、发布 | [构建发布规则](rules/dotnet-build-publish.md)、[build-publish-dotnet-app](skills/build-publish-dotnet-app/SKILL.md) | WPF、WinForms、控制台、Worker、ASP.NET；不适用于非 .NET 工程或 NuGet 包发布 |
| Windows WPF/WebView2 桌面内嵌 ASP.NET Core，Web 前端，SQLite；整理源码、临时目录及可复制 APP | [organize-windows-desktop-web](skills/organize-windows-desktop-web/SKILL.md)、[专用工程规则](skills/organize-windows-desktop-web/references/project-rules.md) | 整体文件夹交付的单机桌面架构；不是独立服务器或所有 .NET 项目的默认布局 |
| WPF 原生界面的字体、布局及 DPI | [WPF 规则](rules/wpf-ui-font-dpi.md)、[build-wpf-dpi-ui](skills/build-wpf-dpi-ui/SKILL.md) | WPF 控件及其渲染边界；不把 WPF DIP 规则套用到 WebView2 的 CSS/DOM |
| WPF 中使用 ScottPlot | [build-scottplot-wpf](skills/build-scottplot-wpf/SKILL.md) | 按 Skill 所支持的 ScottPlot 版本选择；不自动用于其他图表库 |
| HPM6E00 TSW + RTL8211F，USB RNDIS/ETH 双接口，交换机停滞、千兆协商与多板身份 | [bringup-hpm6e-network](skills/bringup-hpm6e-network/SKILL.md)、[逐项经验](skills/bringup-hpm6e-network/references/lessons.md)、[调试过程](skills/bringup-hpm6e-network/references/case-study.md) | 实测为 HPM6E8Y 自制板、SDK 1.13.0、FreeRTOS/lwIP、RAM 固件；不是其他 MAC/PHY 的寄存器模板，也不代表 EtherCAT 或千兆吞吐量验收 |
| HPM5301IEG1 板载调试器，UART ISP、HSLink-Lite 适配和 USB 重连 | [bringup-hpm5301-debugger](skills/bringup-hpm5301-debugger/SKILL.md)、[陷阱及过程](skills/bringup-hpm5301-debugger/references/lessons-and-case.md) | 实测为该自制板、HSLink-Lite 2.4.7 本板 r2；不直接用于其他板型、UF2 或主控外部 Flash |
| HPM6E80 独立FreeRTOS双核AMP、CPU1运动/PDO和CPU0网络、次核装载与性能对照 | [bringup-hpm6e-amp](skills/bringup-hpm6e-amp/SKILL.md)、[双核踩坑提醒](skills/bringup-hpm6e-amp/references/lessons.md)、[性能与边界](skills/bringup-hpm6e-amp/references/performance.md)、[可选规则](rules/hpm6e-amp-release.md) | 实测HPM6E8Y/SDK1.13.0、0.25.1-amp、两台SV660N；地址仅本型号，不能推广SMP/其他SoC或八轴/带载/长期稳定结论；三版本同脚本两轴实测已完成，局部规划中位数快1.95～2.23倍；不等于UDP吞吐或全局最坏实时性同比提高 |
| Go 后端、Electron/Tauri、纯 Web、云端数据库、容器、嵌入式固件等 | 当前没有对应的工程组织规则 | 保留项目原约定；不要套用 Windows 桌面 APP 目录和 SQLite 便携规则 |

## 组合与优先级

PCB 库增量修改按 [独立步骤与验证边界](rules/pcb-library-incremental-workflow.md) 选择：改丝印从导入开始；只改透明度直接改 Body；只改引脚 Name 保留符号位置；只换模型保留所有焊盘。每一步都有单独脚本与新输出，不必重做整条流程。

1. 先读目标项目的 `AGENTS.md`、构建脚本和发布约定，确认实际架构及用户要求。
2. 通用 .NET 构建 Skill 可以与架构专用组织 Skill 组合。专用配置采用 `src` / `scripts` / `temp` / `artifacts/app` 时，通用规则中的“生成物树”表示这些受忽略的指定输出位置，不要求把临时目录重新放回 `artifacts`。
3. WPF 原生壳和网页界面分别处理字体、尺寸与缩放；只有实际使用 ScottPlot 时才追加对应 Skill。
4. 更具体的项目要求及用户明确选择优先。目录整理不隐含更换数据库、升级框架、修改登录方式、开启设备写入或改变部署模式的授权。
5. 一个仓库有多个产品时，在各产品边界分别选用；不要因为某个产品使用 WPF 而改动其他架构的目录。

桌面内嵌后端配置的 APP 内部采用并列的 `runtime`（运行资源）、`config`（配置）和 `database`（SQLite、附件及备份），不嵌套第二层 `artifacts`；迁移旧路径必须保留历史数据与备份的可用性。

## 使用方式

- 规则：将所需规则的适用范围和约定合入目标项目的 `AGENTS.md`，先调整项目自己的路径与运行要求。
- Skill：将所选 `skills/<名称>` 完整目录安装到工具支持的 Skills 目录；保留其 `references` 和已有 `agents` 文件。
- 新增架构时使用独立目录，明确触发条件、排除范围和与已有规则的关系，再更新本索引。

本次新增的桌面工程组织 Skill 同时借鉴 UTF-8 文件处理和窄范围 Git 提交实践，但这些通用实践不决定项目架构，也不授权自动推送其他仓库。

## 每条知识的适用范围要求

适用于本仓库全部 `skills/`、`rules/` 及经验参考文档，不限制目标产品必须采用某种架构。

1. **对象与触发条件**：写清要解决的现象，硬件/封装/板型、软件栈、操作系统、依赖版本等必要前提；不相关的字段可省略。
2. **排除条件**：明确哪些相似场景不能直接用，以及哪些改动会使经验失效，如 PHY、SDK、启动器、图表版本或线程模型变化。
3. **经验粒度**：独立文件必须有范围说明。同一文档内共享同一范围的条目可显式继承文档范围；混合通用方法、板级参数和单次观察时，每条经验再单独标明差异，不能只靠 README 的总免责声明。
4. **证据与结论**：区分源码/手册事实、实测结果、实现选择和待验证推断。记录日期、版本、失败对照、验收标准、未验证项；历史验收不是本次重新执行的结果。
5. **迁移条件**：列出复用前应核对的项目和复测要求。示例 IP、缓冲数、优先级、Flash 地址、目录、字体大小等不能作为任意项目的默认值。
6. **变更边界**：经验不授予擦写、OTP、运动使能、生产配置修改或跨仓库发布权限；使用当前用户已给的任务授权，不重复索要已经明确的许可。

新增条目的最小表达方式（可按内容合并，避免机械堆叠标题）：

```text
经验：具体问题或决策
适用：对象、版本、触发条件；共用范围可明确引用所在文档
不适用：相似但不满足条件的场景
现象与证据：日期、源码/手册/测试来源，事实与推断分开
处理：有效方案，以及值得保留的失败尝试
验收与限制：实际通过什么，未测试什么，迁移后如何复核
```

## 目录与提交检查

```text
skills/<名称>/SKILL.md       触发条件、范围和可执行工作流
skills/<名称>/references/   按需读取的细节、经验、过程和证据索引
skills/<名称>/agents/       可选的工具显示配置
rules/                     可选用的目标项目行为规则
```

- 案例文档放在所属技能的 `references/`，入口提供链接，不把整段调试历史塞进技能描述。
- 新增或修改范围后同步选择索引；检查 SKILL frontmatter、相对链接及示例与范围是否一致。
- 记录最终通过和失败对照，不删除失败来制造全通过。没有实测就写未验证，文档改动不要求重新操作现场硬件。
- 发布的是可复用知识；上传前移除凭据、真实设备身份台账、第三方业务报文和不必要的原始抓包。证据未随仓库发布时明确写原项目索引，不能提供伪装成可访问附件的链接。
- 本次 HPM 两项技能已补充各经验自己的范围；既有四项技能和参考资料也补充或保留了范围边界。它们的既有技术内容未因此获得新的实测认证。
