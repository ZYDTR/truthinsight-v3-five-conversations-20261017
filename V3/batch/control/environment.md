# V3 环境合同

本轮为用户重新授权的 V3 修订版 3.1.0；V2 已全体封存、比较和清理，启动时重新核验。原 V3 3.0.0 保留且不复用其已停止环境。
后端固定 6d529489815362eb2d6cf717e736e44936de3afc，SDK 0.2.154、CLI 2.1.274 与科学依赖沿用 V2；原始输入、公共校验器、模型路由及预算不变。API/worker 仅替换共享系统提示词常量。新 RUN_ID、独立用户、数据库、运行目录和五个新 Conversation，不复用 V2 历史。

实际环境位置读取本批次 `.local/active.json`；API 地址、镜像与实际就绪证明读取该环境 `ready.json`。原件可能含私有配置，不回显凭据。

一题一个全新 OpenCode 操作者，固定沿用 V2 实测 GLM-5.3-Flash-W4A16-MTP，主子均 qwen3.7-flash，fallback 空，4 子并发上限/2 科研运行槽/500 turns/40 rounds/1 CPU/4 GiB。首科研消息逐字原 LaunchPrompt；中性 warmup 与实际主子型号核验沿用 V2，禁止另开探针 Conversation。

后台由唯一 control.py 驱动；环境准备和启动由主线程负责，五题完成后由最后 seal/finish 负责证据备份和清理。所有冻结文件在 operator-bundle/manifest.json；操作者不得修改。
