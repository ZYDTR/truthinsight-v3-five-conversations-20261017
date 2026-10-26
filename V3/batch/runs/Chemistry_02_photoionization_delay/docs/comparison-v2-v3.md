# Comparison V2 (sealed baseline) vs V3 (current round) · Chemistry_02_photoionization_delay

结论前置（先读这段）：同口径核实后，本题 V3 相对 V2 的**可归因差异集中在"复现证据与冲突/来源记录的完整性"**——V3 执行了 14/15 干净目录脚本重建 + 1 项有完整注记的 DIRECT_REBUILT，并保留了过时快照误判、产物字节丢失、失败委派等全部负面事实；V2 没有等价的干净目录重建执行证据。**首轮自主表现 V3 在委派维度不优于 V2（V2 轮 1 内自主完成真实委派，V3 轮 1 零委派尝试）**，不能声称 Skill 带来首轮提升。V3 的反馈与干预事件显著多于 V2（5 次操作者反馈 + 2 次 root 有界审读 vs V2 的 2 次反馈），是首要混杂因素——所有"改善"均不得归因于 Skill 单一变量。单题单次运行，无统计结论力。全程不评分。

## 1. 同口径前提核实（比较有效性）

| 维度 | V2 | V3 | 一致? |
|---|---|---|---|
| 后端 | main 6d529489815362eb2d6cf717e736e44936de3afc | 同 sha（run-spec backend_sha；environment.md 固定） | ✓ |
| 被测模型 | 主/子均 qwen3.7-flash，fallback 空（406 条 assistant 逐一核验） | 主/子均 qwen3.7-flash，fallback 空（388 条逐一核验） | ✓ |
| 外层操作者模型 | windows-glm/GLM-5.3-Flash-W4A16-MTP | 同（run-spec observed_default；本 session 实际沿用） | ✓ |
| 预算 | 500 turns / 40 rounds / 4子并发 / 2 科研槽 | 同 | ✓ |
| SDK/CLI/依赖 | 0.2.154 / 2.1.274 / 科学栈沿用 | 同（environment.md：沿用 V2，仅替换共享系统提示词常量） | ✓ |
| 操作者布局 | 5 个独立 leaf、一题一会话一 Conversation | 同 | ✓ |
| 探针协议 | 无独立探针会话；中性 warmup + 首委派后核子模型，合并进唯一 Conversation | 同（run-spec separate_probe=false） | ✓ |
| 首条科研消息 | 原 LaunchPrompt 逐字（sha 0f4cafd2…） | 同 sha、cmp 字节一致 | ✓ |
| 输入完整性 | 历次快照 input/shared 未变 | 同（11 快照） | ✓ |
| 公共 validator | 只检结构，不判科学 | 同 | ✓ |
| **共享 Skill** | V2 冻结版（3.0.0 代） | **V3 修订版 3.1.0 + 系统提示词常量替换（本轮唯一自变量）** | ✗（设计差异） |

比较有效；差异解释空间 = Skill/系统提示词修订 + 干预事件差异 + 运行间随机性。

## 2. 首次科研自主表现（轮 1，反馈前）——分项对照

| 项 | V2 轮 001 | V3 轮 001 | 判定 |
|---|---|---|---|
| 主体分析单干 | 是（首次 Bash L80→L188 才委派，100+ 行工具活动先于委派） | 是（L58–L224 全程零委派） | 同病 |
| 首轮自主委派 | **有**：L185 先用错工具（SendMessage→报错），自纠后 L188 真实 Agent 委派（general-purpose，后台，3174 字符有界 prompt）；子 a1934c5e 独立写码执行 8 轮修复后落盘；主侧 L253–L290 消费并修订 F1/2/3——全部发生在轮 1 内 | **无**：零委派、零错误工具尝试 | **V2 更强**（虽有"事后复核型"性质） |
| 共享上下文读取 | INDEX ✓ SKILL ✓ references 5/5 ✓；根 CLAUDE.md ✗（仅注入） | 仅 INDEX ✓（L21）；SKILL/references 无显式 Read；analysis-state.md 自建符合模块要求 | 口径不同：V2 系统提示词要求"实际读取"；V3 3.1.0 设计为 INDEX 路由+按需读取，但按 3.1.0 自身标准"委派前读取委派合同"也未达成（轮 2 委派前无 delegation-contract.md 读取记录，比较阶段新核事实） |
| 提前宣告完成 | L250 "Task Complete"（子返回前，本轮末自纠） | 无此行为 | V3 无此缺口 |
| 产物与格式 | Result.md 初稿+全量结果；validator passed | Result.md+4 脚本+10 机器产物；validator passed | 持平（结构） |
| 核心主张质量 | 未评分；V2 verdict 记录结构性缺口 | Finding 1 存在 index 对齐能量错位（违反 DATA_GUIDE §30）+双口径共存——**本轮证据内的实质性方法缺陷，V2 轮 1 未出现同类问题** | V3 更弱（该项） |
| 工具错误 | 46 | 20 | 不作质量分 |

## 3. 匹配 V2 科研轮数时（第 3 科研轮）的状态

- V2 第 3 轮即最终封存轮：validator passed、3 子产物整合、归属修正完成，终态=封存态。
- V3 第 3 轮（replication-integration）：能量对齐已修正、首次委派完成且子1 复算与主侧逐值一致、复算证据已入 F2/3/4——但当时仍带 2 个未纠正的文本缺口（Finding 1 Robustness 越界句、双口径对 analysis_results.json 的错误描述）与 1 个来源限制（主侧重建脚本替代已删除的子侧原始实现）。V3 在第 3 轮**未达终态**，其后又经 3 轮（F4 极值/拐点语义、对齐网格 angle-resolved 重算、干净目录重建与复现诚实性）。
- 同口径判定：匹配轮数时 V2 处于"可封存"状态，V3 处于"中途修正"状态——**不能据此判定退化**（V3 的 Skill 验收条件更严，要求干净目录重建与来源注记，V2 无此条件）；列为"口径不同导致不可直接比较"，证据如上。

## 4. 最终表现对照（各自封存态）

| 项 | V2 最终 | V3 最终 | 判定 |
|---|---|---|---|
| verdict | REVIEWED_WITH_ISSUES | REVIEWED_WITH_ISSUES | 持平 |
| validator | passed（0 err 0 warn） | passed（0 err 0 warn） | 持平 |
| 子委派 | 3 次全部真实独立执行落盘，全部被主侧消费 | 2 次真实（子1 成功且复算一致；子2 选错列失败，主侧直接重算恢复） | V2 委派成功率更高；V3 保留了失败事实 |
| 子证据改变主结论 | 有（Check 2 → F3 从 physical effect 降为 potentially localized artifact） | 有（子1 确认 F3/F4；eigenphase 非单调经子1+操作者复算推翻主侧原判） | 持平（机制均真实发生） |
| 复现证据 | reproduce.md 步骤+脚本在位；**无干净目录重建执行记录** | **14/15 干净目录脚本重建执行（命令/退出码/容差留痕）+ 1 项 DIRECT_REBUILT 完整注记** | **V3 更强（本题最主要差异）** |
| 冲突/来源记录 | 归属错误 1 处（轮 3 修复） | 过时快照误判、子产物字节丢失、失败委派、手改比较状态（root 指认后由被测 Agent 自行以执行结果取代）——全部保留并注记 | V3 记录更完整（部分源于其更严的 Skill 条款） |
| 输入树完整性 | 未变 | 未变 | 持平 |

## 5. 干预与反馈差异（混杂，单列）

- V2：2 次操作者事实反馈（#1 含用户口径引入的"主体工作委派/上下文分担"要求，明确标记为操作者干预；#2 仅结果归属）。无 root 中途审读。
- V3：5 次操作者事实反馈 + **2 次 root 有界审读**（第一次审读后 owner 补查并轮 6 前送出复现诚实性反馈；root followup 直接触发轮 6）。所有干预都发生在 run 之间，无运行中插话、无重复 POST。
- 结论：V3 获得的逐轮纠偏总量约为 V2 的 2.5–3.5 倍。**"最终交付更完整"不能归因于 Skill**——其中至少"复现证据诚实性"一项由 root followup 直接触发。
- 两轮反馈内容差异本身反映 Skill 验收条件不同（V3.1.0 新增：提前委派、独立复算整合、analysis-state、干净目录重建、来源注记），反馈粒度随之加细——这也是口径差异，不是同变量对比。

## 6. 随机性与外推限制

- 单题单次运行；五题各自独立操作者/会话/环境；被测模型采样随机性未被控制（无重复试验）。
- 首轮委派行为（V2 有/V3 无）在 n=1 下不能外推为"V3 Skill 削弱首轮自主性"或"V2 更优"；同理 V3 的能量错位缺口也可能为单次现象。
- 后端/依赖/模型/预算/协议一致但**环境实例、数据库、worker 均为 V3 新建**（不复用 V2 历史），实例级差异不可排除但已按合同最小化。
- root 审读与操作者反馈属于外部干预变量，已尽量在 §5 单列；仍无法从最终状态中完全剥离。

## 7. 改善 / 未变 / 退化 / 无法判断 清单（本题证据内）

- **改善（有同口径执行证据）**：干净目录复现验证从"无执行记录"→"14/15+1 留痕执行"；负面事实与来源限制的记录完整性。
- **未变**：validator 通过、输入完整性、角色边界（子不再派生、无越界读写）、verdict 等级（REVIEWED_WITH_ISSUES）、子证据真实改变主结论的机制。
- **不优于 V2（本题证据内）**：首轮自主委派（V2 轮 1 内真实发生，V3 为零）；首轮共享模块显式读取（V2 读 SKILL+5refs，V3 仅 INDEX——部分为 3.1.0 设计使然）。
- **无法判断**：整体质量优劣（不评分）；匹配轮数状态差异是否为 Skill 所致（验收条件与干预量不同）。
- **V3 特有新缺口（比较阶段新核）**：按 3.1.0 Skill"委派前读取委派合同"的要求，轮 2 委派前主 JSONL 无 delegation-contract.md 读取记录——本轮未就此发送过反馈，补记于此；已封存，仅记录不重开。
- **未解决问题遗留**：相位差 ~4 rad 的机制解释（约定偏移 vs 能量分歧）两轮均未定；errF 误差列两轮均未入检验。

## 8. 证据位置

- V3：本题 runs/Chemistry_02_photoionization_delay/{docs/execution-report.md, docs/execution-index.json, reviews/verdict.json, rounds/, snapshots/}；原始 JSONL 三份（主 838 行 + 子 77 + 子 44）行号级 findings 见 verdict.json。
- V2：shared-context-v2-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Chemistry_02_photoionization_delay/{run.json, rounds/(000-warmup,001,002,003), reviews/verdict.json, docs/execution-report.md, sealed.json}；仅读本题，未读其他题与整批报告。
