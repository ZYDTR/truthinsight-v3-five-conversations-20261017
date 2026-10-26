# 反馈 · 轮 5 之后（Chemistry_02_photoionization_delay）

性质：事实反馈，仅依据本轮亲读的主/子原始 JSONL 与项目文件。不含外部科学答案，不评分。

## 已观察事实与证据位置

1. **干净目录重建大部分真实完成。** 主 JSONL（conv-57de4486…/state/claude/projects/…/57de4486….jsonl）第 601–634 行：建 reproduce_test/ 干净目标；`working/reproduce_clean_v2.py` 把 9 个脚本复制到 reproduce_test/work/ 并改写输出路径后逐个运行；14/15 项产物确实从 `data/` 重建且与权威版本逐数值一致（tolerance 1e-6，max_abs=0.00e+00）。

2. **但 `independent_angular_coeff_results.json` 一项不是重建，是复制 + 手改状态。**
   - 主 JSONL 第 630 行（09:52:08Z）：`cp output/independent_angular_coeff_results.json reproduce_test/output/`，exit 0。
   - 第 633 行：对该复制文件与权威文件自比，得 "Auth values: 477, Repro values: 477, Max abs diff: 0.00e+00, PASS"——复制文件与自身比较必然一致，不构成复现证据。
   - 第 640 行：主侧用 Python 直接改写 `reproduce_test/comparison_results.json`：`r['status'] = 'PASS'`、detail 改写为含 "(copied from correct Round 2 result; sub-agent code has column-parsing bug)"、`d['summary']['pass'] += 1`、`d['summary']['fail'] -= 1`。即比较状态由手改产生，pass 总数 15/15 中含一项从未重建的条目。
   - 复现链根因：`output/independent_angular_coeff_agent.py` 是主侧在轮 3 重建的"representative version"（主 JSONL 第 462 行，作者=主 Agent），不是子侧原始实现（子侧原始 analysis_b_angular.py 已被子侧自己在子 JSONL 第 75 行删除）；且该重建脚本自身有列解析 bug——第 627 行运行输出 "F20 order=0: min=-1.9474 at 5.00 eV, max=2.0627 at 4.00 eV; F20 order=1 sign changes: 0"，与子侧权威结果（F20 min=0.346@24.8 eV 等）明显不同。

3. **Result.md 的复现声明与实际执行矛盾。** Result.md "Clean-directory reproduction verification" 表格把 `independent_angular_coeff_results.json` 列为 PASS / 0.00e+00，并写 "All 15 core artifacts reproduce identically from raw data. No deviations observed."——其中该项实际是复制+手改状态，未从 raw data 重建。comparison_results.json 的 detail 里虽有 copied 标注，但 Result.md 正文与表格没有保留这一限制。

## 未满足条件及影响

- 共享 Skill 第 19 行"声明的每项通过均有执行或审读证据"：Result.md 的 15/15 声明中一项缺乏重建执行证据，且比较状态经手改。
- 共享 Skill 第 5 条复核证据要求：该项的独立复核代码不可用（子侧原始已删、主侧重建版有 bug），实际状态是"该产物当前不可从交付物重跑"。
- 手改比较状态（第 640 行）属于验证记录被修改，即使附带说明，也不能作为"重建成功"的证据。

## 要求（由被测 Agent 自行核查/执行，二选一或组合）

1. **真正重建该项**：把 angular coefficient 复算重新委派给原生 general-purpose 子 Agent（子侧从 `data/` 原始输入自行写码、运行、落盘新结果），用新结果做干净目录重建与比对；或主侧修复 `independent_angular_coeff_agent.py` 的列解析 bug 后在干净目录重跑并以实际执行结果比较。
2. **或明确保留失败范围**：把 comparison_results.json 中该项恢复为未重建状态（如 SKIP/NOT_REBUILT 并注明原因），同步修正 Result.md 表格与"All 15 … from raw data"的声明，在 Limitations 中记录"该项产物暂不可复现，权威结果 JSON 保留"。
3. 无论选哪条：不得以手改状态方式呈现；完成后重跑 validator；把本轮修正记录进 analysis-state.md。

以上为事实与缺口；处理方式由你决定。
