# TruthInsightBench V3 五题完整产物与评分

**本包包含 V3 的五个 SAP conversation 及其对应的已有正式评分。** 实际共享上下文版本为 3.1.0。全部轮次、全部快照、最终科研产物、原始主子 Agent JSONL、操作者会话、环境清理前运行目录与服务日志均收入。

此次仅离线归档，未新增科研运行或评分。历史过程报告中的“不评分”是当时操作者边界；最终分来自用户后来授权的独立后置评分。

## 从这里看

| 题目 | 全过程与 JSONL 索引 | 最终报告 | 已有分数 / 100 |
|---|---|---|---:|
| 光电离延迟 | [索引](indexes/Chemistry_02_photoionization_delay.md) | [Result.md](V3/batch/runs/Chemistry_02_photoionization_delay/snapshots/20261016T100943-539ca/project/output/Result.md) | 52.1 |
| 时间延迟转变 | [索引](indexes/Physics_04_temporal_delay_transition.md) | [Result.md](V3/batch/runs/Physics_04_temporal_delay_transition/snapshots/20261016T094435-cdafa/project/output/Result.md) | 60.9 |
| 引力谱结构 | [索引](indexes/Astronomy_02_gravity_spectral_structure.md) | [Result.md](V3/batch/runs/Astronomy_02_gravity_spectral_structure/snapshots/20261016T100423-97597/project/output/Result.md) | 57.9 |
| 冰川与河流侵蚀 | [索引](indexes/EarthScience_01_glacial_fluvial_erosion.md) | [Result.md](V3/batch/runs/EarthScience_01_glacial_fluvial_erosion/snapshots/20261016T093515-ca9ab/project/output/Result.md) | 66.7 |
| 钙信号区域差异 | [索引](indexes/Neuro_02_calcium_response_regions.md) | [Result.md](V3/batch/runs/Neuro_02_calcium_response_regions/snapshots/20261016T093148-64cf6/project/output/Result.md) | 53.1 |

[评分与原始调用](scores/README.md) · [全部文件清单](indexes/files.csv) · [JSONL 清单](indexes/jsonl-inventory.json) · [会话绑定](indexes/conversations.json)

## 目录

```text
V3/
  batch/runs/<task>/      全轮次、快照、科研文件、审读/比较报告、反馈与收据
  batch/docs/            批次进度、结果质量审读及完成记录
  batch/.local/          root 过程审查与派发回执
  experiment/subject/    当时冻结的 CLAUDE.md、Skill、系统提示词
  operators/<task>/      五个操作者的原生 JSONL、可读全文及引用上下文
  environment/           清理前运行目录、主子状态、服务日志与版本证据
    private/             脱敏后的数据库快照与环境资料
scores/V3-completed/     对应正式评分、原始调用、闭环材料与评分输入
scorer/                  当次评分器及其 578 个冻结资产
indexes/                 分题索引、文件清单、来源哈希、评分绑定与脱敏记录
MANIFEST.sha256          除自身外的逐文件 SHA-256
```

被测主子模型：`qwen3.7-flash`；外层操作者：`windows-glm/GLM-5.3-Flash-W4A16-MTP`。共享上下文 3.1.0 冻结于 `52fff1847bec1a2f82b1abd8e23caeda979dea21`；后端 `6d529489815362eb2d6cf717e736e44936de3afc`。

## 完整性与边界

五题封存清单的 444 个条目已重新核验。评分所用 output 与相应最终封存 output 逐文件一致，详见 [评分绑定核验](indexes/scoring-to-conversation-binding.json)。全部快照保留，重复文件未去重。JSONL 逐行检查见 [核验记录](indexes/source-verification.json)。

凭据只在打包副本中替换，原件保留。[脱敏清单](indexes/redactions.json) 与 [来源哈希](indexes/source-files.json) 可追溯变化。操作者 JSONL 完整保留消息与工具块，并附按哈希引用的上下文正文。

通用后端源码副本、外部账户凭据库和其他版本的运行批次未打包；本轮已有 V2/V3 比较报告仍保留。数据库是专用实验环境的清理前快照，其中可能含环境探测记录，不计作第六道题。历史文件内绝对路径保留，新建索引用包内相对路径。

解压后运行 `python3 tools/verify_archive.py` 验证逐文件哈希。ZIP 外另附压缩包 SHA-256 和核验回执。
