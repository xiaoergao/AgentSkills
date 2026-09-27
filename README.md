# AgentSkills

按项目架构和任务选择规则与 Skills。这里的规则是工程行为约定，不是命令权限文件；不要把所有规则直接合并到每个项目的 `AGENTS.md`。

## 选择索引

| 项目或任务 | 选择 | 适用边界 |
| --- | --- | --- |
| SDK 风格 .NET 应用的构建、测试、发布 | [构建发布规则](rules/dotnet-build-publish.md)、[build-publish-dotnet-app](skills/build-publish-dotnet-app/SKILL.md) | WPF、WinForms、控制台、Worker、ASP.NET；不适用于非 .NET 工程或 NuGet 包发布 |
| Windows WPF/WebView2 桌面内嵌 ASP.NET Core，Web 前端，SQLite；整理源码、临时目录及可复制 APP | [organize-windows-desktop-web](skills/organize-windows-desktop-web/SKILL.md)、[专用工程规则](skills/organize-windows-desktop-web/references/project-rules.md) | 整体文件夹交付的单机桌面架构；不是独立服务器或所有 .NET 项目的默认布局 |
| WPF 原生界面的字体、布局及 DPI | [WPF 规则](rules/wpf-ui-font-dpi.md)、[build-wpf-dpi-ui](skills/build-wpf-dpi-ui/SKILL.md) | WPF 控件及其渲染边界；不把 WPF DIP 规则套用到 WebView2 的 CSS/DOM |
| WPF 中使用 ScottPlot | [build-scottplot-wpf](skills/build-scottplot-wpf/SKILL.md) | 按 Skill 所支持的 ScottPlot 版本选择；不自动用于其他图表库 |
| Go 后端、Electron/Tauri、纯 Web、云端数据库、容器、嵌入式固件等 | 当前没有对应的工程组织规则 | 保留项目原约定；不要套用 Windows 桌面 APP 目录和 SQLite 便携规则 |

## 组合与优先级

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
