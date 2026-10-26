# Comparison V2 → V3 · Physics_04_temporal_delay_transition

门槛确认：五题 V3 sealed.json 全部存在（Chemistry_02、Physics_04、Astronomy_02、EarthScience_01、Neuro_02）后才读取 V2；仅读本题 V2 的 `run.json`、`rounds/`、`snapshots/`、`reviews/` 与执行证据（execution-report、operator 日志、反馈原文），未读整批报告与其他题答案。全程不评分，不调用 judge。root 审读为额外干预（见 §5）。

## 结论（前置）

| 维度 | 判定 | 同口径证据 |
|---|---|---|
| 干净目录复现完成度 | **改善**（有限定） | V3：空目录 /tmp/repro_clean 重建 7 个核心 JSON，逐文件 sha256 与终稿一致（操作者亲验 MATCH×7），证据保留于 `output/repro_evidence/`；但复现入口不含独立复核支链（root addendum §2）。V2：`reproduction_run/` 重建 panel1–4 JSON/PNG，为可配置输出副本（analysis_repro.py），操作者抽验共同键 0 差异、原稿多 3 补充字段，未保留于 output/。两版均非"未改动源码逐字节重建"。 |
| 报告-产物数字一致性 | **无法判断孰优**（审读深度不同） | V3 本方审读发现 5 处主张-产物不一致并全部在轮内修复（LOO 范围、8/10 计数、几何级数主张、Thiers13 p、指数拟合未持久化）。V2 本题操作者抽验未发现数字不一致（panel1 共同键 0 diff），但审读深度与项目不同，不能据此断言 V2 更差或更好。 |
| 委派分担（冻结 Skill 过程条件） | **未变（两版均未满足"开工前"条件）** | V2：主体分析在 round 002 单干完成（777.4s，零委派），round 003 操作者指令后才并行 3 子（A=F1 复算、B=全项方法审查、C=F3 复算），round 004 自主追加 D/E；共 5 子，各占独占目录。V3：主体实现 09:16:48Z 写完、09:16:58Z 委派唯一子（全四项复算）、09:17:03Z 首次执行主分析；共 1 子，脚本在 project 根、产物在 `output/evidence_independent/`。两版首次实质委派都晚于主体实现落笔；V2 的子侧独占目录纪律更好，V3 的子侧覆盖全部四项复算但并行度与独占性弱。 |
| 首次科研自主轮 | **未变**（同平台错误截断） | V2 round 001：56.0s，24 Read+2 Glob 清点，零写/零委派，被 `conversation_content_save_failed` 中断。V3 round 001：83.8s，契约五件套+共享上下文+SKILL 读取与 data/ 盘点，mkdir 被同一 `conversation_content_save_failed` 中断。两版首轮均无管线、无委派；自主表现证据都被平台故障截断。 |
| 匹配 V2 轮数时表现 | **结构未变，内容类别不同** | 两版均为 warmup+4 科研轮，002 均为平台故障恢复轮，003/004 均由操作者反馈推进。V2 003=分工指令+CLAUDE.md 补读、004=复现与如实标记指令；V3 003=8 条源码-主张审计、004=4 条追溯性/精度审计。轮数相同不等于内容可比（§4）。 |
| 最终 verdict 类别 | **未变** | V2=REVIEWED_WITH_ISSUES；V3=REVIEWED_WITH_ISSUES。 |
| 聚合 token（口径：报告 usage 去重和） | **V3 低于 V2**（非质量分） | V2 input≈12.83M/output≈119K tok、198 unique API messages、tool_errors 23（raw-audit-index.json）。V3 input 9,734,749/output 69,284 tok、115 unique messages、tool_errors 14（control.py audit）。单条请求峰值输入未提取，缺测。 |

## 1. 一致性核查（对比前提）

| 项 | V2 | V3 | 一致 |
|---|---|---|---|
| 后端 | origin/main 6d529489815362eb2d6cf717e736e44936de3afc | 同（environment-verification.json） | ✓ |
| 主/子模型 | qwen3.7-flash ×5 子全同 | qwen3.7-flash（主+1 子） | ✓ |
| fallback | 空 | 空 | ✓ |
| 外层操作者模型 | windows-glm/GLM-5.3-Flash-W4A16-MTP | 同 | ✓ |
| SDK/CLI | 0.2.154 / 2.1.274 | 同 | ✓ |
| 预算 | max_turns 500、40 轮、4 子、2 槽 | 同 | ✓ |
| 操作者布局 | 5 独立 session，一人一题一 Conversation | 同 | ✓ |
| 探针协议 | 无额外探针会话，中性 warmup | 同 | ✓ |
| 原始输入 | LaunchPrompt sha256 0f4cafd2…68da3a，144 文件 | 同 | ✓ |
| 公共校验器 | validate_output.py 同哈希（run.json input_hashes） | 同 | ✓ |

差异项：共享 Skill/系统提示词/CLAUDE.md 由 2.0.0 改为 3.1.0（本轮被测变量）；操作者反馈内容不同（§4）；V2 round 003 时长缺测。

## 2. 首次科研自主表现（反馈前留证，两版各自 round 001）

- 共同点：逐字 LaunchPrompt（同 sha256）；系统性上下文与数据清点真实完成；均被平台 `conversation_content_save_failed` 截断（V2 56.0s / V3 83.8s）；均未产出文件、未委派。
- 差异：V3 首轮读了 SKILL.md 与 context/INDEX.md（V3 系统提示词要求）；V2 首轮读了 context/delegation.md 与 SKILL.md（V2 清单），同样无显式根 CLAUDE.md 读取（V2 在 003 补读；V3 未被审读指出此缺口，因根 CLAUDE.md 自动 attachment 内容一致且两版系统提示词口径不同）。
- 限制：两版"首次自主表现"都只能评价到清点阶段，无法比较管线/委派能力。

## 3. 匹配 V2 轮数时（第 4 科研消息收束）与最终表现

- 第 4 科研消息（round 004）收束时——V2：四项发现各有专属复算子（F1=A、F2=D、F3=C、F4=E）+ B 定性方法审查；reproduction_run/ 重建并抽验；validate 通过；图像自报未目验。V3：四项发现由单子全量复算 + 本方 9 条审计全部修复；复现逐文件 sha256 匹配并入 output/；validate 通过；无图像交付。
- 最终交付：V2 产物更宽（9 面板、panel JSON/PNG、verification_results.json、五子产物树）；V3 更窄但每项主张与机器产物逐一对齐，且报告内含独立验证差异表（V2 的子差异仅在交付状态表中汇总）。宽度差异不构成质量分。
- 科学限制（各自自报、转述不背书）：V2——F1 alpha-B 混淆、F2 部分坍缩/B 映射无元数据、F3 Bc_inf 循环与 grid 病态、F4 power-law 未检验；V3——分割 vs 平滑未决、普适类未决、网络特异性未解释、复现不含独立支链。

## 4. V2 中途操作者干预与两轮反馈差异（单列，不并入 Skill 归因）

- V2 反馈（3 条）：002 平台故障事实通报+续行；003 用户指令型分工干预（要求委派+补读 CLAUDE.md）；004 用户指令型复现与如实标记干预。003/004 是外部引入的过程指令。
- V3 反馈（3 条）：002 平台故障事实通报+续行（附 Skill 委派要求指针）；003/004 为本方逐轮亲读源码与机器结果后的事实审计（LOO 阈值搜索缺陷、子结果差异表述、单位/轴与数字来源、复现范围与证据保留）。003/004 属证据驱动审读，不是外部科学指令，但仍是操作者干预。
- 两轮反馈差异使"轮数相同"失去过程等义性：V2 的 003/004 回应的是"该做而未做"的过程缺口；V3 的 003/004 回应的是"已做但与产物不符"的具体缺陷。任何跨版比较必须携带此差异。

## 5. 归因与随机性限制

1. Skill 修订（2.0.0→3.1.0）与操作者干预内容变化同时发生；root 本轮源码有效性审读为额外干预。单题单次运行无法把行为变化分解到 Skill、反馈内容、root 审读或被测随机性。
2. 两版 round 001/002 都遭遇同一平台错误，恢复轮结构相同——该部分与被测变量无关。
3. V3 round 002 主侧在子完成前写终稿（09:19:32 vs 09:22:24）是真实过程事实；V2 亦为先写后补（round 003 补读三子后修订）。模式相似，不能计为版本差异。
4. 聚合 token 差异（9.73M vs 12.83M 输入）与面板数、子数量、轮内容相关，不作效率或质量推断。
5. 未解决事项：V3 复现入口未覆盖独立复核支链（addendum §2）；V2 图像未目验遗留；两版首轮自主证据均被平台截断。

## 6. 证据指针

- V2：`runs/Physics_04_temporal_delay_transition/reviews/verdict.json`（sha256 见 V2 sealed.json e4474638…8cd15dd）、`docs/execution-report.md`、`rounds/00{2,3,4}-input-feedback*.md`、`raw-audit-index.json`。
- V3：本题 `docs/execution-report.md`、`docs/root-review-addendum.md`、`docs/execution-index.json`、`reviews/verdict.json`（review_sha256 56c6303e…8920c0）、`rounds/feedback-00{2,3,4}-source.md`、`snapshots/20261016T094435-cdafa`。
