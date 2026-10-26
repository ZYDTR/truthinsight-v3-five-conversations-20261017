# 唯一控制面命令

解释器 `/Users/zhengyidi/miniconda3/envs/ideagen_env/bin/python -B`；入口 `/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/scripts/runtime_test/control.py`。以下 ACTION 均替换为该完整 Python 命令后的参数，不传 task 或 session 参数；脚本从 `OPENCODE_SESSION_ID` 自动绑定自己。不得伪造该环境变量。

| ACTION | 用途 |
|---|---|
| `whoami` | 校验唯一题目/新Conversation/owner/运行目录 |
| `prepare` | 一次性建立自己的运行目录，保留原 LaunchPrompt |
| `warmup` | 启动一次中性预热作业；完成后自动复制原输入与冻结 subject 到实际 project，验真实主模型 |
| `send` | 首条科研消息，原 LaunchPrompt；发送前自动校验实际模型与输入/共享文件哈希 |
| `send --input <自己的run目录内反馈.md>` | 保存事实反馈后发送；不得提供科学答案 |
| `status` | 查看本题任务与发送作业，WAITING_FOR_SLOT 是正常资源排队 |
| `monitor` | 保存状态、project变化、原JSONL增长 |
| `observe --since N` | 脱敏定位实时工具/委派/错误；不能代替原文审读 |
| `collect` | 保存不可变快照和原JSONL，运行公共格式validator |
| `audit` | 基于最新快照生成JSONL索引，仍需亲读原件 |
| `seal` 或 `seal --blocked` | 停止后续发送，保存最终快照和哈希，回收本题worker；必须先写报告和review |
| `finish` | 只在五题均封存后清理共享环境；其他情况只报告等待 |

`warmup/send` 立即返回机械后台作业 PID 和日志路径，不是外层 Agent。它负责请求与SSE持续落盘，期间每240秒自动机械采样。你仍必须亲自审读过程和反馈，禁止只启动作业就结束。每60—240秒检查本题状态，不能固定长睡眠绕过观察。发现ERROR先读本题jobs/process.log、rounds和private HTTP错误；不能直接重发造成重复轮次。现有作业未完成时发送入口拒绝重复请求。不要调用底层 controller_impl.py 或私自绕过锁直接POST。

`prepare` 后核对 first-message.md 与原 LaunchPrompt 字节一致；warmup完成且项目已播种后才send。子模型从首次实际原生委派的JSONL核验，若不匹配应立即停止反馈并保存为阻塞，不可自行换模型。

每轮就近写 `docs/operator-log.md`，记录证据、决定、反馈文件和实际结果。各round目录、snapshot和已发input不可改写。公共validator只是格式验收，不等于科学正确。

封存必须先产出：
- `docs/execution-report.md`：首次自主、匹配V2轮数、最终表现分别记录；审读证据、当前限制、实际模型、上下文加载、原生委派、最终版本一致性、复现、反馈与工具问题。
- `docs/execution-index.json`：对应raw、快照、每轮、产物、反馈和验证路径。
- `reviews/verdict.json`：至少包含 `raw_jsonl_reviewed: true`、`raw_files: [{"path":"原JSONL绝对路径","sha256":"...","reviewed_lines":"1-N","findings":["事实与行号"]}]`、`scoring_performed: false`、`verdict: "REVIEWED_WITH_ISSUES或REVIEWED或BLOCKED"`、实际models、remaining_issues。

seal之后不能再发科研消息。等待 control/ownership.json 列出的五个 runs/<task>/sealed.json 都存在后，仅阅读自己题目 V2 的 `run.json`、`rounds/`、`snapshots/`、`reviews/` 及执行证据，在本题 `docs/comparison-v2-v3.md` 对比。不要读V2整批报告中的其他题答案。比较须核实后端、模型、依赖、预算、操作者布局和探针协议一致，单列 V2 中途干预与两轮反馈差异，且任何“改善”都要有同口径证据，不评分。最后调用finish，确认共享清理证明并在自己session汇报。

版本绑定：共用 operator-control-v2 原件保持不变；其中当前 V2 代指本轮 V3、基线 V1 代指已封存 V2，以本轮 run-spec 为准。五题 V3 全部封存前不得读取 V2 科学结果。所有五个操作者收到相同上下文；按冻结 Skill 的实际验收条件审读，不在首条科研消息中追加任何提示。
