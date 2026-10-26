本次 root 原件审读发现新问题，请在你现有唯一 owner session 内核查；不评分，不读 V2 答案，不开新 session。root 不向 SAP 发消息。
1. 审读快照 working/subagent_fft_loo_corrected/corrected_fft.py 89–158 行把各 pass 的 A/B/C 模型 top5 峰全部加入后按频率累计，144–158 行计数并未按 pass ID 去重。原 JSON 的 620 μHz 桶甚至是 23/22；1040 μHz 桶的 17 条记录来自 13 个不同 pass。Result.md 第 11、58、67、80 行却将它写成 17/22 独立 pass（77%）。这是统计单位与文字不一致，请亲读当前代码、原 JSON 和终稿，确认本轮是否已修；若未修，按控制面将事实性反馈落盘后让本题 Agent 自行核查，并核对修改是否传递到状态、权威结果、生成器和复现。不要把 root 的计数当作免审读答案。
2. Result.md 152 行用 IC 数值范围重叠推断 likelihood normalization 相同并直接可比；analysis-state 的 F9 却将其记为条件性推断。请核实依据与措辞一致，不能用数值重叠代替定义依据。
3. 当前 reproduce.md 所示 clean replay 只运行 FFT 和 generate_artifacts，是否真正重建所有采纳的 LOO/independent verification 数据，还是读旧结果，需亲验并标明覆盖范围。
若收到时已经 seal，则严禁重开、再发 SAP 或修改封存产物；仅在 docs/root-review-addendum.md 追加这次原件核查及尚未解决的限制。
