# 当前分析状态
更新依据：三个子代理完成；结果已审阅并整合。当前交付版本：r2

## 已确认事实
| ID | 定义、单位与支持范围 | 证据路径及定位 | 已检查版本 |
|---|---|---|---|
| F1 | 主数据集: glacial_erosion_Earth.tsv (427行), nonglacial_erosion_Earth.tsv (6288行) | data/raw/glacial_erosion_Earth.tsv, data/raw/nonglacial_erosion_Earth.tsv | r1 |
| F2 | 核心变量: Erosion rate (mm/yr), Time interval (yr), Methodology, Type | 两主表均含这些列 | r1 |
| F3 | Methodology分类: Volumetric, Cosmogenic surface, Thermochronometric, Relief, Cosmogenic detrital | 两主表 Methodology 列 | r1 |
| F4 | Glacial中值侵蚀率0.55 mm/yr; Fluvial中值0.061 mm/yr — 约10倍差异 | working/subA/exploration_summary.md | r1 |
| F5 | 时间跨度: Glacial 0.02-250M yr (中位1270); Fluvial 0.003-20M yr (中位1201) | working/subA/exploration_summary.md | r1 |
| F6 | 同源相关性严重: 427条glacial观测来自154个Reference; 6288条fluvial来自265个Reference | working/subA/exploration_summary.md | r1 |
| F7 | Timescale斜率因Methodology而异: Cosmogenic ~ -1.0(机械耦合); Volumetric Glacial -0.073, Fluvial +0.117 | working/subB/regression_results.json, working/subC/robustness_results.json | r2 |
| F8 | 聚类SE后timescale效应不显著: Glacial p=0.997, Fluvial p=0.279(按Reference) | working/subC/robustness_results.json | r2 |
| F9 | Glacial vs Fluvial log10差异+0.90 (t=20.5, p<1e-67); ANCOVA控制timescale和method后process effect仍显著(F=489.7, p<1e-104) | working/subB/comparison_results.json | r2 |
| F10 | 最佳模型: interaction model R²=0.587, AIC=10705; main-effects最佳R²=0.127 | working/subB/analysis_summary.md | r2 |

## 分工与未决问题
| 问题/分支 | 执行者与子任务 ID | 输入、独占输出路径 | 状态、依赖或阻点 |
|---|---|---|---|
| Branch A: Data audit & exploration | Sub-Agent A (general-purpose) | → working/subA/ | ✅ 已完成待审 |
| Branch B: Core analysis | Sub-Agent B (general-purpose) | → working/subB/ | ✅ 已完成待审 |
| Branch C: Robustness checks | Sub-Agent C (general-purpose) | → working/subC/ | ✅ 已完成待审 |
| Integration & report writing | Main Agent | → output/ | 进行中 |

## 结论与权威产物
| 结论 ID | 当前源码/结果及版本 | 复核状态 | 采纳状态及报告位置 |
|---|---|---|---|
| Finding 1: Timescale-erosion relationship is method-dependent | working/subB/core_analysis.py, working/subC/robustness_analysis.py | ✅ 已交叉验证 | 采纳, 见 Result.md D1 |
| Finding 2: Glacial > Fluvial erosion rates after controlling for method/timescale | working/subB/comparison_results.json | ✅ 已交叉验证 | 采纳, 见 Result.md D2 |
| Finding 3: Source correlation invalidates OLS significance of timescale slope | working/subC/robustness_results.json | ✅ 已交叉验证 | 采纳, 见 Result.md D3 |

## 受影响的旧证据
(无旧版本)
