# V3 修订版接续

用户已重新授权本轮优化及启动；原 V3 3.0.0 的暂停记录仅属于旧版。定时任务 tib-v3 仍暂停，不可恢复旧 prompt。

root 使用 scripts/activate.py gate/up 检查前轮完成、启动和验证独立环境，再 scripts/dispatch.py start 仅执行一次。若 .local/opencode/dispatch-claim.json 或 control/ownership.json 存在，恢复同一组收据，禁止重开五个。scripts/dispatch.py status 供一次启动实际外层模型和防嵌套检查。控制面科学发送仅由对应 OPENCODE_SESSION_ID 的操作者执行，root 不代发。

五题封存后亲读 execution-report、comparison-v2-v3、verdict 与关键原始证据，核对单位/实际分析/反证整合/完整复现、委派时机和状态更新，区分首次自主与反馈后表现，保留额外操作者审读说明及 V2 干预的归因限制。清理以 docs/cleanup.json 和实际零残留为准，全程不评分。
