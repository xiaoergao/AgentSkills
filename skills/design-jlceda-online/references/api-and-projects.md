# 在线 API 与工程身份

适用：专业版在线编辑器已安装 API Gateway，并有用户启动的本机 Bridge。下列方法在 2026-11-01 的协作中使用过；迁移到其他插件/编辑器版本时先检查当前 API 文档和返回结构。不适用：直接操作云端数据库、未授权接管其他工程、把桌面客户端状态视为在线工程状态。

## 连接与选择

- 官方入口：[专业版 CLI 指南](https://prodocs.lceda.cn/cn/api/guide/cli.html)、[API Gateway 扩展](https://jlc-ext.com/item/oshwhub/run-api-gateway)。CLI 与第三方 Gateway/Bridge 是不同入口，不能混用参数或假设认证方式相同。
- 本次 Bridge 协议：`GET /eda-windows` 返回 `windows[]`；`POST /execute` 请求 `{windowId, code}`，响应 `{success,result,error}`。默认本机端口曾为 49620，脚本可配置，必须以当前实际启动信息为准。
- “Bridge 运行”与“EDA 窗口连接”分开检查。零窗口时由用户在目标工程执行插件重新连接；多窗口时分别只读查询文档身份，不再使用“必须只有一个窗口”的旧假设。
- Bridge 返回 `activeWindowId` 只是 UI 活动提示。真正的修改条件是工程 UUID、文档 UUID和类型符合任务；两个独立工程可能有相同文档 UUID。
- `dmt_Project.openProject(projectUuid)` 后重新读取当前工程；`dmt_EditorControl.openDocument(docUuid)` 后重新读取文档。不要把工程 UUID 当成 `openDocument` 的第二个参数。

最小身份读操作：

```javascript
return {
  doc: await eda.dmt_SelectControl.getCurrentDocumentInfo(),
  project: (await eda.dmt_Project.getCurrentProjectInfo())?.uuid
};
```

写脚本只使用明确的输入，避免硬编码历史工程 UUID。随附 Bridge 脚本注入 `assertTarget()`，长脚本在每个异步修改前可再次 `await assertTarget()`。执行期间用户切换图页仍可能造成竞争；出现切换立即停止，重新读回，不继续原批次。

工程身份一致仍不代表布局未变。布局批次同时比较样板/目标的坐标、旋转、层面及受影响线路；不在新的手工位置上继续执行旧坐标的布线计划。PCB 元件位置优先用 `pcb_PrimitiveComponent.modify`；避免把焊盘 getter 返回的整对象经 setter/done 回写。本次曾观察到焊盘圆形尺寸 getter 单位不一致及回写后的实例形状异常，几何测量应与库源交叉核对；不为改网名而无意改写焊盘几何。

该辅助脚本用于固定目标内的操作。需要切换工程/图页时，先通过当前可用 API 单独完成有明确目标的导航，再按新身份调用辅助脚本；不要把导航放进期望目标始终不变的写批次。

## 复制工程

案例使用过的 API 序列（先核对当前签名）：

1. `sys_FileManager.getProjectFileByProjectUuid(sourceUuid, fileName, undefined, "epro2")` 获取 `File`。
2. `sys_FileManager.importProjectByProjectFile(file, "JLCEDA Pro", importOptions, destination)`；目的操作为 `New Project`，团队、名称由当前可访问工程信息及用户要求确定。
3. 读取新工程 UUID、工程树和关联 Board/Schematic/PCB；激活副本并读回 `parentProjectUuid`。
4. 在副本改名、删页、放器件；每次修改都检查副本身份。读回原工程进行对象比较，确认其目标图页、元件/走线仍保留，再回到副本。

导入参数的已用形式（变量来自当前任务；不照抄示例工程或团队身份）：

```javascript
const file = await eda.sys_FileManager.getProjectFileByProjectUuid(
  sourceProjectUuid, backupName, undefined, 'epro2');
if (!file) throw Error('Project export failed');
const imported = await eda.sys_FileManager.importProjectByProjectFile(
  file, 'JLCEDA Pro',
  {importOption:'ImportDocument', associateFootprint:true, associate3DModel:true},
  {operation:'New Project', newProjectOwnerTeamUuid:targetTeamUuid,
   newProjectName:newSlug, newProjectFriendlyName:newDisplayName,
   newProjectDescription:description});
return imported; // 检查实际返回的新工程身份，再执行导航。
```

注意：以上流程中，源文件可以暂存在编辑器 JS 全局变量，但页面刷新后会丢失。保存本地备份更可靠。不得把“复制成功”解释为“内部所有图元 ID 都重新生成”；本次观察到文档 UUID 保留。

## 常用 API 的职责

| 操作 | 曾验证的入口 | 关键条件 |
| --- | --- | --- |
| 源数据备份/回写 | `sys_FileManager.getDocumentSource()` / `setDocumentSource(source)` | 全文回写前保存基线；只改目标记录，保留其他图元 |
| 元件实例 | `sch_PrimitiveComponent` / `pcb_PrimitiveComponent` 的 create/modify/getAllPinsByPrimitiveId | 符号引脚号与 PCB 焊盘号分别读取，不从截图猜编号 |
| 电源符号 | `sch_PrimitiveComponent.createNetFlag('Ground'或'Power', net, x, y, rotation, mirror)` | 使用已有 net；标识不得进入 BOM/PCB 实体器件列表 |
| 原理图保存与网表 | `sch_Document.save()`，`sch_ManufactureData.getNetlistFile(name,'JLCEDA')` | 保存后再导出，解析 `File.text()` |
| PCB 同步 | `pcb_Document.importChanges(schematicUuid, true)` | 第二个参数的无弹窗支持依版本核实；操作前后保存源，检查实例 ID、位置、3D、DNP |
| 检查/视图 | `pcb_Drc.check(false,false,true)`、`pcb_Document.zoomToBoardOutline()` | DRC 参数以当前版本解释；不能仅凭返回真值判断通过 |
| 原理图画面 | `sch_ManufactureData.getExportDocumentFile(name,'PNG', options,'Current Schematic Page')` | 将返回文件保存到本地查看，不在日志打印 base64 |

## 源数据与坐标

原生记录常为 `headerJSON||bodyJSON|`，最后一行可能没有尾部 `|`。`DOCHEAD`/`CANVAS` 等记录不一定都有 `id`。用 JSON 解析记录，不对整份源文件做无约束的字符串替换。

原理图 API 的引脚 Y 与原生源记录 Y 在本次观察中符号相反。例如 API 引脚 `(330,1300)` 对应源中的 `(330,-1300)`。这不是所有 API 的统一坐标契约：旋转、镜像和不同文档类型必须用一个已知元件及全部引脚读回验证。PCB API 常用 mil，`mm=mil×0.0254`；原理图坐标尺度不同，不能共用转换。底层镜像与旋转组合应核对至少三个不共线焊盘。

源数据中的 `PAD_NET` 记录 ID 可包含组件 ID、焊盘号和封装内部 pad ID。仅改变组件 ID而漏改关联属性或 PAD_NET 会制造悬空数据。PCB `BOARD` 记录顺序曾影响导入，进行结构变换时保持原有顺序，尤其不要把追加图元写到最终 BOARD 之后。

## 卡住时

一次超时不能证明操作失败。先只读检查目标组件数、ID、源数据和保存状态，防止重复放置。若同一绘图 API 连续卡住但读取仍可用，保存已完成内容并停止该写批次；再使用 computer-use 查看更新确认框、模态对话框或工程加载状态。只让用户完成确实需要手动的刷新/重新连接步骤。恢复后重新识别工程，不沿用过期 windowId、全局 File 或未确认的执行结果。

若桌面端更稳定且用户已允许切换，可在核对独立工程身份和数据同步后继续；不要因“桌面已安装”而自动编辑另一份本地旧工程。
