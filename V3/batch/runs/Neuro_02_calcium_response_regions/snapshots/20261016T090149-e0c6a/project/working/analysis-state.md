# 当前分析状态
更新依据：所有子Agent完成 + 主侧独立复算；当前交付版本：r2

## 已确认事实
| ID | 定义、单位与支持范围 | 证据路径及定位 | 已检查版本 |
|---|---|---|---|
| F1 | 数据文件 `data/cellular_calcium_response_summaries.tsv`，819行观测，SHA256与manifest一致 | data/cellular_calcium_response_summaries.tsv | r1 |
| F2 | 4区域×3条件结构严重混杂：R3仅receptor_stimulated，R4仅baseline+blocked | working/main_analysis.py 输出 | r1 |
| F3 | ANOVA (R1+2)：Region×Condition交互对所有变量显著(p<0.05)，除AUC外 | working/main_analysis.py line ~ANOVA结果 | r1 |
| F4 | Batch效应强：amplitude η²=0.327, prominence η²=0.386, width η²=0.168 | working/analysis_B/batch_effects.csv, main_analysis.py | r1 |
| F5 | Receptor_stimulated vs baseline在R1+2中：振幅↑(d=-0.66), AUC↑(d=-1.89), 宽度↑(d=-1.51), TTP↓(d=0.43) | working/analysis_C/replication_results.csv, output/contrasts_regions12.csv | r1 |
| F6 | Baseline vs neural_activity_blocked在R1+2中：多数对比不显著，仅TTP和width有中等效应 | output/contrasts_regions12.csv rows 0-2 | r1 |
| F7 | LOO稳健性：排除任一批次后receptor_stimulated效应方向100%保持(26/26次p<0.001) | output/robustness_lobo.csv | r1 |
| F8 | 切片级聚合时显著对比从23/54降至7/54，细胞内非独立性影响推断 | working/analysis_B/robustness_results.csv | r1 |
| F9 | Age与amplitude(r=0.18,p<1e-7)、prominence(r=0.21,p<1e-9)弱相关 | working/main_analysis.py age_correlations | r1 |

## 分工与产物
| 问题/分支 | 执行者 | 输入、独占输出路径 | 状态 |
|---|---|---|---|
| 主分析(LMM+探索) | Agent A (general-purpose) | working/analysis_A/ | 已完成待审 |
| 稳健性检验+批次效应 | Agent B (general-purpose) | working/analysis_B/ | 已完成待审 |
| 独立复核(replication) | Agent C (general-purpose) | working/analysis_C/ | 已完成待审 |
| 主侧独立复算 | 主Agent亲自 | working/main_analysis.py → output/ | 已完成采纳 |

## 结论与权威产物
| 结论ID | 当前源码/结果及版本 | 复核状态 | 采纳状态及报告位置 |
|---|---|---|---|
| D1: Receptor stimulation increases amplitude/AUC/width | output/contrasts_regions12.csv, main_analysis.py | Agent C一致, LOO稳健 | 采纳, Result.md Finding 1 |
| D2: Region×Condition interaction is significant but confounded | output/contrasts_regions12.csv ANOVA, model_output.txt | 设计约束明确 | 采纳, Result.md Finding 2 |
| D3: Batch effects are substantial for amplitude/prominence | batch_effects.csv, figures_batch_effect.png | Agent B一致 | 采纳, Result.md Finding 3 |
| D4: Baseline vs blocked mostly null effect | output/contrasts_regions12.csv rows 0-2 | Agent C一致 | 采纳, Result.md Finding 4 |
