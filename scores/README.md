# V3 已有评分

这份评分对应包内五个 V3 conversation 的最终封存提交。实际共享上下文版本为 3.1.0。此次仅归档，没有新评分调用。

Judge：`qwen3.8-max`，thinking 关闭，原版 TruthInsightBench V1.0 评分器。

[核验汇总](V3-completed/verified-summary.json) · [最终评分 JSON](V3-completed/work/final/final_scoring_result.json) · [初评到最终差异](V3-completed/work/final/base_to_final_comparison.json) · [原始调用](V3-completed/calls) · [评分与会话逐题绑定](../indexes/scoring-to-conversation-binding.json)

| 题目 | 最终分 / 100 |
|---|---:|
| 光电离延迟 | 52.1 |
| 时间延迟转变 | 60.9 |
| 引力谱结构 | 57.9 |
| 冰川与河流侵蚀 | 66.7 |
| 钙信号区域差异 | 53.1 |

平均分 **58.14**。这是含操作者反馈的最终提交评分；20 个发现中，数值复算覆盖 3 个，16 个完成检索、4 个使用冻结参考资料。`work/score/scoring_result.*` 是初评，请以 `work/final/final_scoring_result.json` 为准。

五题评分导出与对应会话的最终 output 逐文件哈希一致；原始请求、返回、失败重试、复核材料与评分器均完整保留。
