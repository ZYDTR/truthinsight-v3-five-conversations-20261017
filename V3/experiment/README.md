# 共享科研上下文 V3 修订版

版本 3.1.0，用户已授权优化后完整重跑五题。已于 2026-10-16T08:47:31.299466+00:00 派发五个 OpenCode session，唯一绑定见批次 docs/dispatch.json；实际科研进度与结果以各题证据为准。原 3.0.0 的冻结和未运行记录保留。

- [共享 Skill](subject/project/.claude/skills/scientific-evidence/SKILL.md)、[系统提示词](subject/system_prompt.md)、[薄入口](subject/project/CLAUDE.md)。
- [改动依据与验收](docs/changes.md)、[冻结清单](context-manifest.json)、[工作记录](docs/working.md)。
- [五人共用操作者入口](batches/qwen3.7-flash-main-6d52948-20261016/control/operator-task.md)。

固定 V2 实测外层 GLM-5.3-Flash-W4A16-MTP、SAP 主子 qwen3.7-flash、fallback 空，后端 6d52948、SDK 0.2.154、CLI 2.1.274 和原预算。五个全新 OpenCode session 一人一题一新 Conversation，最多两题同时科研运行；不评分。原始数据与首科研输入本轮保留，Skill、系统提示词及薄路由修订。统一操作者补充源码有效性审读说明，比较时作为额外干预披露。

定时任务 tib-v3 继续暂停。操作者自主持续执行，root 仅启动核验和有界协调，不成为第二操作者。

## 本轮结束与结果审读

五题已于2026-10-16 18:09（Asia/Shanghai）全部封存，独占运行资源已清理。2026-10-17 root 完成[终态科学结果审读](batches/qwen3.7-flash-main-6d52948-20261016/docs/result-quality-review-20261017/review.md)：存在影响核心结论的方法和推断缺口，不能因运行完成或格式通过而视为科学验收通过。定向只读诊断与原件索引同目录；没有评分、重开会话或修改冻结subject。

## 后置评分（2026-10-17 用户另行授权）

用户随后授权用 217 LiteLLM 的 `qwen3.8-max`、thinking 关闭，对本轮五份最终封存提交评分。未修改原版 V1.0 评分器或被测答案，未启动下一版解题。初评与最终复核于 2026-10-17 13:13（Asia/Shanghai）全部完成；[评分及完整性核验](../../evaluations/shared-context-v31-qwen38max-nothinking-20261017/verified-summary.json)记录五题最终分数与逐项原件入口，平均 58.14/100。

67 次评分请求中 66 次返回成功、1 次传输失败后已恢复；全部成功回复均为指定模型，所有请求显式关闭 thinking。20 条发现完成复核，16 条新增先例检索与4条冻结参考资料比较均完成；自动数值复算只覆盖3条发现。444 项封存原件及578个评分器/资产文件哈希保持一致。这里的分数属于含操作者反馈的最终提交，不代表首次自主作答表现，也不能直接与采用不同评分模型的历史分数比较。
