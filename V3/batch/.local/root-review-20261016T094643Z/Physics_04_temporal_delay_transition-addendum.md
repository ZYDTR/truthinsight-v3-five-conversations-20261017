# Root Review Addendum · Physics_04_temporal_delay_transition · 2026-10-16

依据 root 对原 JSONL 时间线的核对与本方对封存快照（snapshots/20261016T094435-cdafa）的补充核验。本文件仅为事实补充，不修改已 seal 的报告、verdict、快照或 rounds；不评分；全五题 V3 封存前不读 V2 科学结果。root 审读只读快照：`.local/root-review-20261016T094643Z/Physics_04_temporal_delay_transition`；root 进度说明存于批次 `docs/root-progress-review-20261016/Physics_04_temporal_delay_transition-owner-note.md`。

## 1. 委派时间线的准确表述（修正 execution-report 的措辞）

原 JSONL（main，379 行，sha256=510ab465b32fc7301e0d7299ad121ffdf223b9496f35d844fcddb8765ce7f247）：

- 第 119 行，09:16:48Z：Write `working/analysis.py`（主体实现写完）。
- 第 126 行，09:16:58Z：调用唯一原生 Agent（general-purpose，后台，"Independent replication of core analysis"）。
- 第 133 行，09:17:03Z：首次执行 `python3 working/analysis.py`。

准确表述：**主体实现写完后、首次执行前，派独立复核**。既不是"提前将主体分析交出去"（冻结 Skill 要求的主体管线开工前实质分担），也不是"主分析执行之后才派"。执行报告原文"主侧先写完并执行了自己的完整管线，之后才委派"在时序上不精确，以此为准修正；verdict 的 REVIEWED_WITH_ISSUES 结论与"早委派条件未满足"的过程判定不变，仅表述精确化。

首轮平台 `conversation_content_save_failed`（round 001，run_7cc5bd3642cb44b8，events.sse id=130）与 rounds 002–004 的反馈驱动恢复是两类独立事实：前者为后端故障，后者为审读发现后的修复过程，不能合并表述。

## 2. 复现入口的实际覆盖范围（新增未满足项）

对封存快照核验：

- `output/reproduce.md` 第 14–48 行声明的干净目录入口只复制 `output/analysis.py`、`output/robustness.py` 与 `data/`，重跑两个脚本，产物为 7 个核心 JSON（finding1_V_vs_B、finding1_v_b_scatter、finding2_correlation_collapse、finding3_finite_size、finding4_real_networks、robustness_checks、summary）。
- `output/repro_evidence/` 实际只含上述 7 个文件（逐文件 sha256 与 `output/evidence/` 一致，已亲验）。
- 终稿采纳的 `output/evidence_independent/results.json` **不在**该复现入口覆盖内：入口未重跑独立脚本，独立脚本（`independent_analysis.py`、`independent_analysis_v2.py`、`independent_analysis_final.py`）位于 project 根而非 output/，reproduce.md 全文无 "independent" 字样。
- Result.md §Reproduction 称 "To reproduce all results in a clean directory"，相对实际入口覆盖范围属过度声明。

据此记录：**核心链复现已完成；独立复核支链未纳入复现入口**。冻结 Skill 复现标准（"复现覆盖终稿所依赖的完整证据链，包括……关键复核"）在该支链上未满足。本题科学验收条件不应表述为全部满足；verdict 的 remaining_issues 以本条补充。

## 3. 归响与边界

- 本补充不改变 sealed.json、已发消息、快照与 verdict 的任何内容；后续对比报告（comparison-v2-v3.md）将把上述两点列入 V3 侧事实。
- 全五题封存前不读 V2；比较时区分：root 本次审读为额外干预，须与 Skill 作用、操作者反馈轮分别归因。
