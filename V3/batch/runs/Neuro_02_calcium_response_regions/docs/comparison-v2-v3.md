# Comparison V2→V3 · Neuro_02_calcium_response_regions（不评分，仅执行事实）

前置门槛确认：五题 V3 sealed.json 全部存在（Chemistry_02 / Physics_04 / Astronomy_02 / EarthScience_01 / Neuro_02，均 SEALED）后才读取本题 V2 证据；仅读了自己题目 V2 的 run.json、rounds/、snapshots/、reviews/、docs/。未读任何别题科学结果，未调用 judge/评分器。

## 结论前置

- **改善（同口径证据）**：首次科研轮的委派时点与范围——V2 首轮主体分析 solo、唯一委派是末端算术复核（V2 报告 §3：委派发生在主体分析完成之后，"仅为对已算数字的末端复核"）；V3 首轮在主体管线开工前并行委派 3 个 general-purpose 子 Agent 承担实质分析范围（V3 主 JSONL 行89/92/95 先于行174 主侧管线；子侧各自实现/执行/自修复）。判据在两轮报告中口径相同（"首条科研消息后、任何反馈前"）。
- **未变**：交付结构（4 registered findings、图、表、机器结果、validator passed）、主/子模型真实性核验结论、错误全部自恢复（无未恢复故障）、全程不评分。
- **退化（有证据）**：干净目录复现——V2 有子 4 的干净目录重放实例（两-way ANOVA 与 Cohen's d 从原始 TSV 重算，SS 分解差异如实披露）；V3 终稿未执行任何子任务被采纳结果的干净重建，且 Reproducibility 段"generates all figures and result tables"与 main_analysis.py 实际 7 项输出不符（root addendum §3）。
- **无法判断**：科学结论质量与正确性（两轮均不评分）；V3 首轮报告事实错误更多（5 类标签/引用/计数错误 vs V2 首轮未报出同类错误），但这属于单次运行观察，无法区分是 Skill 路由差异、自然变异还是首轮产出更激进所致——不构成质量分。

## 一致性核实（两轮同基线）

| 维度 | V2 | V3 | 一致 |
|---|---|---|---|
| 后端 | main 6d529489815362eb2d6cf717e736e44936de3afc（批次名同） | 同 sha（run-spec backend_sha） | ✓ |
| 主/子模型 | qwen3.7-flash / qwen3.7-flash，fallback ''（ready.json tibv2m-c5173220 核验） | 同（ready.json tibv31-9a7ed51f 核验） | ✓ |
| 外层操作者模型 | windows-glm/GLM-5.3-Flash-W4A16-MTP（V2 报告 §8.2） | 同（run-spec 冻结沿用） | ✓ |
| SDK/CLI | 0.2.154 / 2.1.274 | 同 | ✓ |
| 预算 | 500 turns / 40 rounds / 2 科研槽 / 4 子并发 | 同 | ✓ |
| 操作者布局 | 5 session 一题一会话，无第二操作者 | 同 | ✓ |
| 探针协议 | 中性 warmup 于唯一会话；子模型自首次委派核验；无额外探针会话（run-spec probe_policy 逐字相同） | 同 | ✓ |
| 原始输入 | 同一 144 原文件与原 LaunchPrompt（first-message sha 同源 0f4cafd2…） | 同 | ✓ |
| 公共 validator | 同一格式校验器，均 passed | 同 | ✓ |

## 首次科研轮自主表现对比（同口径：首条消息后、反馈前）

- V2（~16 分钟）：solo 完成探索→深分析→稳健性→图→表→Result.md→复现文档→validator 通过；1 次委派（算术复核、背景运行、主体工作之后）。缺口：CLAUDE.md/delegation.md 首轮未显式 Read（仅注入）。
- V3（~13 分钟）：先读全部上下文（含 SKILL.md + 7 references，无缺读）→ 写 analysis-state → **先委派 3 子**（主分析/稳健性/复算）→ 等待期间检查包依赖 → 消费子产物 → 主侧独立复算并直接重建 output/ 主侧产物 → validator 通过。
- V3 首轮终稿存在 5 类可定位事实错误（检验标签误标、slice 级对比误归属 p=0.021、错误 CSV 引用、不存在的 LRT=263.79、计数 26/27 与 30/50 等）；V2 首轮报告未报出同类错误但委派结构不足。两轮首轮各有结构性强弱，不支持单向质量结论。

## 匹配 V2 科研轮数时（第 3 条科研消息末）状态

- V2 第 3 轮（干预后形态）：并行 3 子审计（slice ICC、region×batch 混杂、干净复现）+ 主侧整合 Methodological Audit 段 + validator passed。
- V3 第 3 轮：r1 自主管线 + 两轮事实反馈修复（5 项→全修复、2 残留→修复）；第 3 轮末 validator passed，analysis-state r3，残留 η² 公式标签与 bullet 口径问题（第 4 轮关闭）。
- 轮数对齐时的内容不同：V2 是审计扩张，V3 是事实订正收敛。均为执行事实，非质量分。

## 最终反馈后表现

- V2：2 条反馈后停手；遗留①正确推断单位（slice 级/混合模型）已披露但 findings 正文未重写框架，②F_region 59.89 vs 67.43 SS 分解差异并存未裁定。
- V3：4 条科研消息（3 条反馈）后停手；本轮所有反馈指出的数值/标签/引用错误全部修复并经操作者对机器产物逐项复核；遗留（root addendum）①LMM 错误阶段混淆（提取 bug/交互 singular matrix 被表述为 convergence 问题），②核心交互仍为 cell-level 推断且 Finding 2 行内无适用范围限定，③子任务被采纳结果无干净复现证据，④analysis-state 三行"已完成待审"未闭环 + D2 引用不存在的 model_output.txt。
- 两轮共同未解决：cell-level ANOVA 仍是核心显著性口径、层级非独立仅披露未重构；region_3/region_4 覆盖缺口为数据设计限制。

## V2 中途操作者干预与两轮反馈差异（单列，不得归因 Skill）

1. V2 round 3 的"委派结构要求"来自用户目标纠正（V2 报告 §6 明示"来源=用户 15:28 CST 目标纠正，非冻结 Skill"）——是外部目标干预，非操作者独立事实审计。
2. V2 round 2 反馈发送前按主线程补充指示合并了 CLAUDE.md/delegation.md 缺口（哈希 503209…→e03032…），也是中途干预。
3. V3 三条反馈均为操作者按冻结 Skill 验收条件独立亲读原件后的事实审计（rounds/feedback-round{2,3,4}.md），无用户追加提示；但 run-spec round_context_addendum 规定本轮统一加入"current-source validity audit"口径说明——这本身是相对 V2 的额外统一干预，两轮反馈生成条件不同。
4. 反馈轮数：V2=2，V3=3；排队时长：V2 单次 37 分钟，V3 两次 7-10 分钟——资源竞争状态不同，影响总时序但不影响轮内事实。
5. 外层模型相同（GLM-5.3-Flash-W4A16-MTP），但操作者是不同独立实例（ses_ebc8097affe… vs ses_ebc1ae3caff…），反馈行文与聚焦点存在实例差异。

## 随机性与归因限制

- 每版本单次运行、无重复抽样：以上全部"改善/退化"均为单样本观察，不支持统计显著结论，也不能把变化全部或部分归因于 Skill/系统提示词修订——后端相同但系统提示词常量、Skill 版本（3.0.0→3.1.0）、round addendum、操作者实例、排队状态均混杂。
- V2 的单次中途干预（用户目标纠正）是 V2 形态的一部分；V3 无等效干预。跨版本比较时干预维度不对齐，只能分列呈现（如上），不能合成总分。
