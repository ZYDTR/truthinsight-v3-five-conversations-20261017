# Root Review Addendum · Neuro_02_calcium_response_regions（封存后事实补充审读）

依据：root 进度审读消息（落盘 `batches/…/docs/root-progress-review-20261016/Neuro_02_calcium_response_regions-owner-note.md`）+ 操作者对只读审读快照 `.local/root-review-20261016T094643Z/Neuro_02_calcium_response_regions` 原件的亲读核实。本题已 SEALED；本文件仅补充事实，不改动已封存报告/verdict/产物，不评分，不读 V2（五题未全封存）。

## 1. "LMM failed" 的真实错误阶段：拟合后提取错误，非不收敛（root 声称属实）

- `output/analysis_A.py`（快照原件，行285-312 亲读）：`smf.mixedlm(...).fit(reml=True, maxiter=200)` 之后**立即成功打印** `LMM (batch RE): AIC=…, BIC=…, LogL={lmm_model.llf:.2f}`；随后第 290 行 `lmm_model.random_effects_cov.values[0][0]`——`random_effects_cov` 在该 statsmodels 版本是**方法**而非属性，`.values` 得到 builtin method，`[0][0]` 下标触发 `TypeError: 'builtin_function_or_method' object is not subscriptable`。该异常被 try 块末尾宽泛 `except Exception as e: log(f"LMM failed: {e}")` 捕获并写成 "LMM failed"。
- 由此：3D 节的 LRT 与 ICC 计算代码位于异常点**之后**，从未执行——"no LRT statistic is available" 的真实原因是拟合后提取 bug 中断了 try 块，不是模型不收敛，也不是拟合失败。`model_output_agentA.txt` 行544-545/550-551（快照行号 543-551）显示 LogL=-332.85 / -4291.94 均已打印、AIC/BIC=nan。
- 3D 节 batch-RE LMM 的收敛标志**从未打印**（该节无 Converged 字段），LogL 已产出仅证明 fit 返回；其收敛状态证据不足，既不能记为收敛失败，也不能反推有效。
- 对照：Section 3 各 LMM 摘要多处明确 `Converged: True`（行273/329/377/417/457/497/556-576）与 `Converged: Yes`（行296/352/400/440/480/520）——加法型（含 slice RE）LMM 实际收敛。交互型 LMM 的失败是 `LinAlgError: Singular matrix`（行313/318/321/326/336/369 等），属混杂导致的估计失败，与"不收敛"是不同阶段、不同性质。
- `mle_retvals` AttributeError（子 A JSONL 行62：`'MixedLMResults' object has no attribute 'mle_retvals'`）同样是 **API 属性在该版本（statsmodels 0.15.0）不可用**，发生在 fit+summary 已成功之后；子 A 行64 自行改为 `result.converged` 检查，行81 明确 "Additive models converged successfully…handled gracefully"。
- 终稿对应表述的核实结论：
  - Result.md 行105 "LMM fitting with batch as random effect **failed**" —— 不准确：fit 已返回并打印 LogL，失败发生在拟合后 `random_effects_cov` 提取，且正是该异常阻断了 LRT 计算。
  - Result.md Limitations #6 "**LMM convergence**: Mixed-effects models with random intercepts for slice/batch encountered computational issues" —— 口径混淆：把提取 bug 与交互模型 singular matrix 归入"收敛"问题；slice-RE 加法模型实际收敛（Converged: True/Yes）。
  - Result.md Finding 3 counterevidence 行110 "encountered **convergence issues** … (AttributeError on `mle_retvals`)" —— 同样混淆：该 AttributeError 是版本 API 缺失，非收敛问题。
  - 操作者自查：本操作者在 round 001-004 反馈中指出 LRT=263.79 无机器来源（属实）并核验了 OLS R² 引用，但未深挖 "failed" 背后的错误阶段，先前的执行报告沿用了终稿的 convergence 框架而未按原件区分——此为操作者审读遗漏，在本补录中更正。

## 2. 层级独立性与核心交互推断的口径对齐

- 终稿 Finding 2 的 headline 与 Relationship 全部 p 值/η² 来自主侧 `main_analysis.py` 的**普通 cell-level 两因素 ANOVA**（statsmodels typ=2，df=574，cells 视为独立）；混合模型仅存在于子 A 的 Section 3（加法型收敛、交互型 singular matrix），未进入 Finding 2 的效应量或推断。
- 报告自身证据（F8；子 B JSONL 行88/92；robustness_results.csv 486 行）显示 slice 级聚合后显著率 23/54→7/54——即 cell-level 推断在该数据上系统性放大显著性。
- 对齐事实：层级非独立的披露存在于 Limitations #2 与 Finding 1 的 robustness 段；Finding 2 的 headline/relationship 段**未携带该不确定性行内限定**，其"statistically significant"的适用范围（cell-level 推断）只在 Methods/Limitations 交代。方法（cell-level ANOVA）、headline（显著性结论）、不确定性（切片聚合证据）三者部分对齐：披露存在但未落在核心主张处。

## 3. 完整复现尚无证据（root 声称属实）

- `main_analysis.py` 实际只写出 7 个产物：figures_main.png、figures_violin_amplitude.png、figures_batch_effect.png、contrasts_regions12.csv、batch_effects.csv、robustness_lobo.csv、summary_stats.csv（行217-251）。
- 被采纳的子任务结果 `replication_results.csv`、`eta_squared_results.csv`、`batch_effects_subagent.csv`、`results_summary_agentA.csv`、`model_output_agentA.txt`、`robustness_results.csv` 均来自 working/ 子任务执行后**复制**进 output/，无任何从干净目录重建的执行记录。
- 因此 Result.md Reproducibility 段 "generates **all** figures and result tables in `output/`" 言过其实：文档化入口只能重建主侧产物，完整被采纳证据集的干净复现无证据。操作者先前执行报告中"核心产物为实际重建"仅对主侧 7 项成立，此处按更窄口径更正。

## 4. 委派卸载程度与状态文件缺陷

- 主 JSONL 行174 的 `main_analysis.py` 含完整 ANOVA/两两对比/批次分解/LOBO/绘图管线，与三个子任务（A: LMM+探索；B: 稳健性+批次；C: 复算）实质重叠。早期三分支委派属实（行89/92/95，general-purpose、spawnDepth=1），但"3 个子任务"这一计数本身不能证明主体分析已卸载——主侧实际自建并执行了同等覆盖的管线。
- `working/analysis-state.md`（快照原件亲读）：分工表 A/B/C 三行状态停留在"**已完成待审**"，而结论表 D1-D4 已写"Agent C一致/Agent B一致…采纳"——状态表与采纳事实不同步、未闭环。
- D2 行证据引用 "**model_output.txt**"——该文件不存在（实际为 `model_output_agentA.txt`）。终稿 Result.md 行72 引用的 "Section 7" 经核存在（model_output_agentA.txt 行727 SECTION 7: DESIGN CONSTRAINTS AND ESTIMABILITY ANALYSIS），该引用有效。

## 补充审读结论

root 四项声称全部经原件核实成立。归纳为未解决问题（不评分）：(a) 终稿将 API 提取错误与估计失败统一表述为 LMM convergence 问题，错误阶段混淆；(b) 核心交互显著性为 cell-level 推断、行内未限定适用范围；(c) 文档化复现入口不能重建全部被采纳产物；(d) analysis-state 存在未闭环状态行与一处失效文件引用。本题 verdict（REVIEWED_WITH_ISSUES）与此补录一致，无需变更；剩余限制以本文件为准叠加。
