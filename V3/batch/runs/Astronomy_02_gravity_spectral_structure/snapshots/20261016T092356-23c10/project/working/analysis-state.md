# 当前分析状态 — Astronomy_02_gravity_spectral_structure
更新依据：Round 001 反馈 + 子 Agent 完成 + 事实修正；当前交付版本：r3

## 已确认事实
| ID | 定义、单位与支持范围 | 证据路径及定位 | 已检查版本 |
|----|---------------------|---------------|-----------|
| F1 | ranked_full_parameter_grid.tsv 仅有 delta_information_criterion，无 absolute IC | `data/ranked_full_parameter_grid.tsv` | r3 已核对 |
| F2 | candidate_spectrum_comparison.tsv 全局最小 IC=43.9 来自 (v_max=20, v_min=0, f=1010, width=300) | `data/candidate_spectrum_comparison.tsv` | r3 已核对 |
| F3 | rank-1 参数 (30, 0.05, 1010, 275) 不存在于 candidate_spectrum_comparison.tsv | 交叉验证两文件 | r3 已核对 |
| F4 | 两文件仅 29/250 重叠，代表不同候选池 | `working/subagent_verification/verification_results.json` | r3 已核对 |
| F5 | delta_IC ≤ 20 候选数 = 9 | `working/subagent_verification/verification_results.json` | r3 已核对 |
| F6 | A-B r < 0.50 → 9 passes; A-C r > 0.80 → 12 passes; B-C range [0.489, 0.998] | `working/subagent_verification/verification_results.json` | r3 已核对 |
| F7 | l=2 耦合系数非单调，峰值在 n=4 (8.61e-9) | `working/subagent_verification/verification_results.json` | r3 已核对 |
| F8 | FFT 未发现 1010 μHz 一致信号；top peaks 在 12,500–487,500 μHz | `working/subagent_fft_loo/fft_results.json` | r3 已核对 |
| F9 | LOO: pass_01 移除导致 std 变化 -21%~-42%；其他 pass <5% | `working/subagent_fft_loo/loo_results.json` | r3 已核对 |
| F10 | IC difference = 1478.2 (structured vs uniform)，可比性基于相同 likelihood 框架 | `working/subagent_verification/verification_results.json` | r3 已核对 |

## 分工与未决问题
| 问题/分支 | 执行者与子任务 ID | 输入、独占输出路径 | 状态、依赖或阻点 |
|-----------|-------------------|-------------------|-----------------|
| FFT周期性 + LOO稳健性 | subagent_fft_loo (a5ba94619161a7725) | data/pass_residual_traces.tsv → working/subagent_fft_loo/ | ✅ 已完成 |
| 光谱排名验证 + 跨模型相关 | subagent_verification (a66e0cc031968f8e9) | data/*.tsv → working/subagent_verification/ | ✅ 已完成 |
| Result.md 数值修正 + 冲突整合 | 主 Agent | 基于子Agent结果 | ✅ 已完成 (r3) |
| analysis-state.md 同步 | 主 Agent | 基于修正后结果 | ✅ 已完成 (r3) |

## 结论与权威产物
| 结论 ID | 当前源码/结果及版本 | 复核状态 | 采纳状态及报告位置 |
|---------|---------------------|---------|-------------------|
| C1: 光谱峰 ~1010-1060 μHz | IC ranking 支持但 FFT 未确认 | ✅ 独立复核完成 | Finding 1 — 标题改为 "Indicated by IC but Not Confirmed by FFT" |
| C2: 方差以 within-pass 为主 | variance decomposition + LOO | ✅ 独立复核完成 | Finding 2 — 加入 pass_01 outlier 说明 |
| C3: A-C 相关性高于 A-B | cross-model Pearson r | ✅ 独立复核完成 | Finding 3 — 数值已修正 |
| C4: 结构化候选优于均匀替代 | IC difference = 1478.2 | ✅ 独立复核完成 | Finding 4 — ratio→difference+可比性论证 |
| C5: 900-1300 μHz 有16个模态 | mode_frequency_grid.tsv | ✅ 独立复核完成 | Finding 5 — 趋势描述已修正 |

## 受影响的旧证据
| 变更依据 | 旧版本与替代路径 | 待重算/重核/同步的位置 |
|----------|-----------------|----------------------|
| Item 4: IC=43.9 归属错误 | r2 → r3: 明确区分两文件，IC=43.9 不属于 rank-1 参数 | Result.md Finding 1, analysis-state.md |
| Item 5: 计数错误 | r2 → r3: 9/12/0.998 修正 | Result.md Finding 1, Finding 3 |
| Item 6: 趋势方向错误 | r2 → r3: 非单调，峰值 n=4 | Result.md Finding 5 |
| Item 7: FFT/LOO artifact | r2 → r3: 已保存至 working/subagent_fft_loo/ | Result.md Finding 1, Finding 2 |
| Item 8: ratio表述不当 | r2 → r3: IC difference + 可比性论证 | Result.md Finding 4 |
