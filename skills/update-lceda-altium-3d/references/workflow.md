# 参数、坐标和执行细节

范围继承本技能：LCEDA Altium 导出 + 可识别位号的有色 STEP，Windows/AD 原生脚本。以下约定只用于所附脚本，不是所有 ECAD/MCAD 的通用坐标系；非平移配准、不同 Z 方向/底面约定需要扩展和小样复测。

## 运行依赖与输入

Python 3.11+；PCB/OLE 读写依赖 `olefile`；几何依赖 `cadquery-ocp` 8.x，导入模块是 `OCP`，不是同名 `ocp` 包。使用目标环境已有运行时或独立虚拟环境安装依赖；不要复制整套 SDK/运行时进交付包。Windows 写 OLE 使用系统 `ole32`，不依赖 Office。脚本不会启动 AD；运行命令由当前任务在已授权范围内执行。

`inspect_pcb.py`：识别 ZIP/epro2 并仅列出条目，不解压未知路径；支持 LCEDA 的 `|RECORD=Component|...` ASCII 和 `Components6/Data` 等 OLE PCB6 流。它不实现 epru→PCB 的电气转换，不从截图恢复走线，也不保证任意 Altium 新版本都采用该布局。对于其他导出格式，先获得匹配的 Altium 原生 PCB。

`prepare_models.py`：读 STEP 的唯一自由根装配，其直接子项名匹配位号，子项内部递归保留实体/表面颜色。共享模型按 PCB 的 `PATTERN` 分组，同封装选一个源模型（优先顶面），逆向放置变换得到规范形状。存在合法料号差异时先由任务决定是否统一；当前脚本不自动区分同封装变体。

## plan 示例

以下全部是字段示例，坐标及板厚必须替换为当前文件实测值。JSON 无注释；路径相对 plan 所在目录，`canonical_models` 的键必须是 PCB 中真实的完整封装名。

```json
{
  "source_origin_xy_mm": [0.0, 0.0],
  "source_bottom_z_mm": 0.0,
  "source_top_z_mm": 1.6,
  "target_board_thickness_mm": 1.6,
  "exclude_references": [],
  "canonical_models": {},
  "replace_existing_bodies": false
}
```

- `source_origin_xy_mm=[sx,sy]` 定义 `PCB_X=STEP_X+sx`、`PCB_Y=STEP_Y+sy`，单位 mm；要求源 STEP 和 PCB XY 轴方向相同。旋转/镜像导出不能只填一个偏移凑数。
- 用多个接近对称的电阻/焊盘锚点求 `sx,sy` 的中位数，再用远离锚点、带方向的接口核对。器件外壳中心不一定等于封装原点；多个值不一致时追查原点/方向，不能强制平均。
- `source_top_z_mm`/`source_bottom_z_mm` 是 STEP 的板体顶/底平面；`target_board_thickness_mm` 来自实际 AD 叠层，二者数值未必完全相同。正面悬空一个板厚时重点检查是否将源板厚又加了一次。
- `exclude_references` 必须逐项命中实际位号，用于确定不代表实际器件的安装孔等。不要默认忽略所有缺模。
- `canonical_models` 是 `{"实际封装名":"models/approved_part.step"}`。替换模型必须先变为：封装原点 XY、零度旋转、外壳贴装平面 Z=0、正常向上；穿板脚可以 Z<0。新排母必须同时核对孔排、间距、针脚编号、开口方向、壳体高度。只改当前已授权的位号；如仅替换同封装的部分实例，应先在副本中为这些实例设置明确的封装变体键，再映射，不能用 pattern 覆盖其他实例。
- `replace_existing_bodies=true` 会在工作副本中移除全部旧 3D Body，再按 manifest 添加。默认遇到旧 Body 停止，避免重复叠加；需要保留部分已有机械对象时先拆分处理。不会删除原文件或自动删除旧的空机械载体元件。

## 变换约定

令 `P` 为 PCB 元件位置，`S=P-[sx,sy]` 为其 STEP XY；原始旋转为 θ。顶面规范模型为 `Rz(-θ)·T(-Sx,-Sy,-source_top_z)·源几何`。底面为 `Rx(180)·Rz(-θ)·T(-Sx,-Sy,-source_bottom_z)·源几何`。该底面公式要求输入的 STEP 已处于真实装配状态。

AD Body 用 `MoveByXY(C.X,C.Y)`，顶面 `Model.SetState(0,0,θ,0)`，底面 `Model.SetState(180,0,θ,-target_thickness)`。最后一个参数为 AD 内部坐标整数，`1 mil = 10000` 单位；脚本显式由 mm 换算，避免把 mm 直接传成内部坐标。所有 Body 的投影保持工厂默认顶面，以显式模型变换表示底部位置；不要再设 Bottom projection 加一次翻转。改用 Altium 的面投影/机械层配对策略时，应重新验证底面几何与后续翻面行为。

此模型基准用于当前实例独立编辑。首次迁移至少检查一个方向不对称器件、90°旋转、底面器件和一组穿孔接口；有 45°/225°器件也要检查。不能用只看轴对齐包围盒代替所有形状方向核验。

## 原生 AD 脚本

`prepare_models.py` 输出目录必须不存在且为 ASCII 路径，防止覆盖已有成果/路径乱码。若有中文工作目录，可先选独立 ASCII 暂存目录，再完成文件交付。复制 PCB 后的全部操作仅在此副本执行。

生成的 DelphiScript 沿用本案实测核心调用：

```pascal
Body := PCBServer.PCBObjectFactory(eComponentBodyObject,eNoDimension,eCreate_Default);
M := Body.ModelFactory_FromFilename(StepPath,False);
M.SetState(RX,0,RZ,DZ);
Body.SetState_FromModel;
Body.Model := M;
Body.MoveByXY(C.X,C.Y);
B.AddPCBObject(Body);
C.AddPCBObject(Body);
PCBServer.SendMessageToRobots(C.I_ObjectAddress,c_Broadcast,PCBM_BoardRegisteration,Body.I_ObjectAddress);
```

在 PreProcess/PostProcess 之间进行数据库变更；迭代器在变更前销毁。只有 `C.AddPCBObject` 曾出现内存里有对象、保存后未持久化的情况；PCB 同时注册到 Board 和 Component。生成器逐位号匹配，不改变元件电气位置。新加入的旧 Body 清理分支属于复用代码，需在副本小样验证；不能借核心绑定历史通过声称该分支所有版本已原生测试。

保存 PCB 使用 `D.DoFileSave('PCB Binary')`；返回 True 且日志含 `SAVED` 后再检查实际文件。`.PcbLib` 若另外制作，是不同文档类型，本案使用 `DoFileSave('')`，不能把 `'PcbLib'` 当成已验证的格式 ID。生成器不包含库流程。

命令示例为已安装 `X2.EXE` 的路径加：

```text
-RScriptingSystem:RunScript(ProjectName=C:\cad_work\job\BuildModels.PrjScr|ProcName=BuildModels)
```

使用结构化参数或正确 shell 引号保留 `|`；路径有空格时引用整个参数。打开文件/生成脚本不代表运行完成。轮询本任务日志，及时报进展；错误后查编译行、日志或已出现的对话框。发生许可/登录阻塞交给用户处理；不杀用户 AD 进程、不无限重启。

## OLE 压缩边界

`compact_models.py` 适用 AD PCB6 的 `Models/{Header,Data,0..N}` 与 `ComponentBodies6/Data`，仅处理嵌入 STEP。需在 Windows 执行；对不同版本/外部链接或其他模型布局先盘点，不直接改二进制猜结构。

脚本以模型 NAME 分组并要求压缩 payload 字节相同，Body 的 `MODELID` 改为该组唯一 ID；局部 `MODEL.2D.*` 和 `MODEL.3D.*` 保留。重建标准 OLE v3，复制其他流和存储类 ID，验证写入内容与未修改输入哈希。不做曲面抽稀或把所有器件合成一个总成。目标必须是新文件，不能原地覆盖。

最后同时报告外部模型数、实际嵌入模型数、Body 数和字节数。AD18重新保存小样曾把共享模型再按 Body 重复写入；应在最终保存后压缩、重新打开检查。若二进制压缩不兼容，保留原生 AD 保存版本及外部共享模型，准确说明大小与限制。

## 原始资料

- [Altium PCB API objects](https://www.altium.com/documentation/altium-dxp-developer/pcb-api-design-objects-interfaces-reference)：Board/Component/Primitive 对象与登记语义。
- [Running Scripts](https://www.altium.com/documentation/altium-designer/scripting/running-scripts)：原生 RunScript 与脚本停止方式。
- [Working with 3D Bodies](https://www.altium.com/documentation/altium-designer/pcb/3d-bodies)：3D Body 的高度、旋转与来源设置。

官方文档不等于每个版本的隐藏 3D 模型接口承诺；本案调用与二进制布局另有实测边界。第三方模型由当前任务获取并保留其许可，本技能不分发 KiCad 或供应商 STEP。
