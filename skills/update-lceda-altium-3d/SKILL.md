---
name: update-lceda-altium-3d
description: Update an EasyEDA/LCEDA PCB's exported Altium PcbDoc with independently editable per-component STEP bodies, shared by footprint, corrected mounting heights, and compact embedded geometry. Use when LCEDA exports lack 3D, parts float above the board, a whole-board STEP prevents individual editing, or embedded models bloat the file. Requires an Altium PCB export and identifiable component models; does not infer an electrical design from a screenshot or require KiCad conversion.
---

# 立创 PCB 补全 Altium 独立 3D

## 范围与交付

输入为立创 PCB/工程文件、其 Altium 导出 `.PcbDoc`（也可能在 ZIP 内）、对应 STEP。输出为保持原焊盘、网络和布局的 Altium PCB：每个实际器件有自己的 3D Body，相同封装共享规范化模型，单件高度和旋转可以分别修改。默认只交付用户要求的 Altium 文件；封装库、整板机械总成及 KiCad 转换按需另做。

脚本面向 Windows、Python 3、`olefile`、`cadquery-ocp` 8.x 和带有效许可的 Altium；绑定调用在 AD18.1.7 的历史案例中执行过。其他 AD/OCP 版本应先小样验证。未命名/无法识别零件的扁平 STEP、非 STEP 模型或不匹配版本的导出需要先配准/补模型，不能承诺无条件一键成功。

## 操作

1. **盘点而不覆盖。** 对用户文件计算哈希，识别 ZIP/`.epro2` 容器、ASCII/二进制 PcbDoc、STEP 层级和原有 3D。先用 `scripts/inspect_pcb.py`；`.epro2` 是 ZIP 的情况应查看 `project2.json` 与内嵌 PCB 记录，不能将文件后缀当作格式或把它当成已转换的 PcbDoc。对照器件数、位号、板框及接口确认输入属于同一修订。
2. **明确模型粒度。** 先列出实际器件、安装孔、缺失模型和每种封装的实例。相同封装优先共用一个模型；如料号有实际不同高度/几何，说明统一预览的取舍或采用明确的变体键，不能悄悄损失必要机械差异。孔不补成未经指定的螺丝。替换排针/排母仅限已指定的位号，沿用引脚号、孔位和网络。
3. **校准坐标和贴装面。** 阅读 [坐标、数据及自动化细节](references/workflow.md)。从多个已知器件/焊盘求 STEP→PCB 的 XY 配准，核对旋转、底面镜像和板框；从实际板体求源顶/底 Z，从 AD 叠层求目标板厚。不要把案例的原点或板厚当默认修复值；穿板引脚允许负 Z，不能简单用整个模型最低点作为外壳贴装面。
4. **按封装导出规范化 STEP，再绑定实例。** 将配准结果写入 plan；使用 `scripts/prepare_models.py --pcb ... --step ... --plan ... --out ...`，生成共享模型、逐位号 manifest、ASCII 路径的 DelphiScript 工程及待运行命令。支持有位号子装配的 STEP；缺失模型会列明并停止，不自动拿整板代替。经选型/确认的替换或预览模型通过 `canonical_models` 指定；它必须事先对准封装原点、零度方向和贴装平面。
5. **调用原生 Altium。** 使用生成的 `run-command.txt`，或在 AD 中 File → Run Script 执行 `BuildModels`。优先 CLI/应用 API；仅需要画面操作时才使用当前环境的 Windows computer-use 技能。不操作登录/许可窗口、不结束用户已有 AD 会话。日志正常完成后用 `scripts/inspect_pcb.py` 验证实际二进制文件，不能把“脚本已生成/进程退出”当作 PCB 已生成。执行停滞时检查日志/错误状态，修复具体问题再重试，最多自动重试两次；保留成果并报告仍缺的步骤。
6. **控制内嵌体积。** 外部 STEP 去重不等于 PCB 内嵌去重。对实际保存文件运行 `scripts/compact_models.py INPUT OUTPUT`；仅合并同名且压缩几何字节完全相同的模型，保留每个 Body 的位置/角度/高度。不同几何同名时拒绝合并。脚本生成新文件并核验其他对象流未变。AD18 后续保存可能重新重复内嵌，应重新盘点/压缩，不能保证只压一次永久不膨胀。
7. **分层验收。** 原始文件哈希不变；元件/焊盘/网络/过孔数与允许的修改一致；每个实际器件有独立 Body；安装孔/缺模不被隐瞒；每种规范封装只对应一个几何模型；抽查不同旋转及上下两面，核对坐标、穿板脚、贴装面和引脚1。原生 AD 重新打开并从低角度看顶/底高度、对齐及颜色；另存副本后检查编辑性与体积。数据检查通过不等于画面验收或制造验收。
8. **轻量交付。** 给出 PcbDoc/可选 PrjPcb、模型映射、实际字节数与 ZIP 大小、预览参数和未验证项。模型已嵌入时，外部 STEP 可单独作为可选附件；不要将运行时、安装包、全部过程 STEP 或原始工程重复打包。若用户停止界面操作，停止 UI，准确报告画面未复核，不能标记全通过。

## 工具入口

```powershell
python scripts/inspect_pcb.py exported.PcbDoc --output before.json
python scripts/prepare_models.py --pcb exported.PcbDoc --step assembly.step --plan plan.json --out C:\cad_work\job
# 按 job/run-command.txt 执行原生 AD；完成日志必须有 SAVED。
python scripts/compact_models.py C:\cad_work\job\Board3D_Raw.PcbDoc C:\cad_work\job\Board3D.PcbDoc
python scripts/inspect_pcb.py C:\cad_work\job\Board3D.PcbDoc --output after.json
```

相对路径均相对 plan 所在目录；输出/运行路径使用可写 ASCII 目录，避免 AD18 脚本中的中文路径编码问题。不要复制本机绝对路径或令牌到技能仓库。参数格式、依赖和异常边界见 [workflow.md](references/workflow.md)；历史失败对照与证据边界见 [case-study.md](references/case-study.md)。
