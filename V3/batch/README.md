# 共享科研上下文 V3 修订版

版本 3.1.0，用户已授权优化后完整重跑五题。已于 2026-10-16T08:47:31.299466+00:00 派发五个 OpenCode session，唯一绑定见批次 docs/dispatch.json；实际科研进度与结果以各题证据为准。原 3.0.0 的冻结和未运行记录保留。

- [共享 Skill](subject/project/.claude/skills/scientific-evidence/SKILL.md)、[系统提示词](subject/system_prompt.md)、[薄入口](subject/project/CLAUDE.md)。
- [改动依据与验收](docs/changes.md)、[冻结清单](context-manifest.json)、[工作记录](docs/working.md)。
- [五人共用操作者入口](batches/qwen3.7-flash-main-6d52948-20261016/control/operator-task.md)。

固定 V2 实测外层 GLM-5.3-Flash-W4A16-MTP、SAP 主子 qwen3.7-flash、fallback 空，后端 6d52948、SDK 0.2.154、CLI 2.1.274 和原预算。五个全新 OpenCode session 一人一题一新 Conversation，最多两题同时科研运行；不评分。原始数据与首科研输入本轮保留，Skill、系统提示词及薄路由修订。统一操作者补充源码有效性审读说明，比较时作为额外干预披露。

定时任务 tib-v3 继续暂停。操作者自主持续执行，root 仅启动核验和有界协调，不成为第二操作者。
