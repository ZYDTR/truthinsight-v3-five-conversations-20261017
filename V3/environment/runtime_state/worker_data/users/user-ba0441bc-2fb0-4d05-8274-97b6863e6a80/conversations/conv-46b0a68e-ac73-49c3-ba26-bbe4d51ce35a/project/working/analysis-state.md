# 当前分析状态
更新依据：Round 2 事实审读后修订；6 项缺口全部修正。当前交付版本：r3

## 已确认事实
| ID | 定义、单位与支持范围 | 证据路径及定位 | 已检查版本 |
|---|---|---|---|
| F1 | 主数据集: glacial_erosion_Earth.tsv (427行), nonglacial_erosion_Earth.tsv (6,288行) | data/raw/glacial_erosion_Earth.tsv, data/raw/nonglacial_erosion_Earth.tsv | r1 |
| F2 | 核心变量: Erosion rate (mm/yr), Time interval (yr), Methodology, Type | 两主表均含这些列 | r1 |
| F3 | Methodology分类: Volumetric, Cosmogenic surface, Thermochronometric, Relief, Cosmogenic detrital | 两主表 Methodology 列 | r1 |
| F4 | Glacial中值侵蚀率0.55 mm/yr; Fluvial中值0.061 mm/yr — 约10倍差异 | working/subA/exploration_summary.md | r1 |
| F5 | 时间跨度: Glacial 0.02-250M yr (中位1270); Fluvial 0.003-20M yr (中位1201) | working/subA/exploration_summary.md | r1 |
| F6 | 同源相关性严重: 154 Refs→427 glacial; 265 Refs→6288 fluvial (全行口径) | working/subA/exploration_summary.md | r1 |
| F7 | Timescale斜率因Methodology而异: Cosmogenic ~ -1.0(机械耦合); Volumetric Glacial -0.073, Fluvial +0.117 | working/subB/regression_results.json, working/subC/robustness_results.json | r2 |
| F8 | 聚类SE后timescale效应不显著: Glacial p=0.997, Fluvial p=0.279(按Reference) | working/subC/robustness_results.json | r2 |
| F9 | Glacial vs Fluvial log10差异+0.90 (t=20.5, p=1.4e-67); ANCOVA控制timescale和method后process effect仍显著(F=489.7, p=1.03e-104) | working/subB/comparison_results.json | r2 |
| F10 | 最佳模型: interaction model R²=0.587, AIC=10705; main-effects最佳R²=0.127 | working/subB/analysis_summary.md | r2 |
| F11 | Clustered回归过滤单观测cluster: glacial 427→324, fluvial 6128→6109 | working/subC/robustness_analysis.py (~L247-252) | r3 |
| F12 | Fluvial Time interval缺失160行(2.54%); 零侵蚀率4行; 有效样本6555 = 427+6128 | output/audit_results.json, output/robustness_results.json | r3 |

## 分工与未决问题
| 问题/分支 | 执行者与子任务 ID | 输入、独占输出路径 | 状态、依赖或阻点 |
|---|---|---|---|
| Branch A: Data audit & exploration | Sub-Agent A (general-purpose) | → working/subA/ | ✅ 已完成待审 |
| Branch B: Core analysis | Sub-Agent B (general-purpose) | → working/subB/ | ✅ 已完成待审 |
| Branch C: Robustness checks | Sub-Agent C (general-purpose) | → working/subC/ | ✅ 已完成待审 |
| Integration & report writing | Main Agent | → output/ | ✅ 已完成; Round 2 修订已应用 |

## 结论与权威产物
| 结论 ID | 当前源码/结果及版本 | 复核状态 | 采纳状态及报告位置 |
|---|---|---|---|
| Finding 1: Timescale-erosion relationship is method-dependent | working/subB/core_analysis.py, working/subC/robustness_analysis.py | ✅ 已交叉验证 | 采纳, 见 Result.md D1 |
| Finding 2: Glacial > Fluvial erosion rates after controlling for method/timescale | working/subB/comparison_results.json | ✅ 已交叉验证 | 采纳, 见 Result.md D2 (bin解释已修正) |
| Finding 3: Source correlation invalidates OLS significance of timescale slope | working/subC/robustness_results.json | ✅ 已交叉验证 | 采纳, 见 Result.md D3 (口径/样本披露已补充) |

## Round 2 修订记录
| 修订项 | 原问题 | 修正内容 |
|---|---|---|
| #1 Bin分析文字矛盾 | "except >10,000 yr gap narrows" 与实际数字不符 | 改为正确描述: 全部4个bin glacial均高于fluvial, 差距最小在100-10000yr(bin差0.05), 最大在>10000yr(bin差1.39) |
| #2 Reference口径混用 | 同一Finding内使用265/248/229三个不同口径的Reference计数 | 明确标注三种口径来源: (a)全行154/265, (b)complete cases 154/248, (c)clustered filtered 51/229 |
| #3 SE比较样本不同 | combined OLS SE(n=6555) vs fluvial clustered SE(n=6109)跨模型对比 | 改为同一样本下fluvial OLS SE=0.0041 vs clustered SE=0.0284 (≈7×), 并声明cross-model对比不适用 |
| #4 样本过滤未披露 | clustered回归剔除单观测cluster导致n缩小但未说明 | 新增Note段落披露过滤逻辑、n变化(427→324/6128→6109)、对Finding 3结论的影响评估 |
| #5 有效样本构成不完整 | 仅提4行零速率, 未提160行Time interval缺失 | Methods Data段补全: 160行缺失+4行零速率→6128 valid fluvial |
| #6 p值表述不精确 | "p<1.0×10⁻¹⁰⁴" 但实际为1.028×10⁻¹⁰⁴ | 改为 "p=1.03×10⁻¹⁰⁴" |
