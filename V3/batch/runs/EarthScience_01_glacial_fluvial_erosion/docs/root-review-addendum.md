# Root Review Addendum · EarthScience_01_glacial_fluvial_erosion · 2026-10-16

依据：亲读 root-review 只读快照 `.local/root-review-20261016T094643Z/EarthScience_01_glacial_fluvial_erosion/output/robustness_analysis.py` 与 `output/Result.md`（与 sealed 快照 20261016T093515-ca9ab 字节一致：robustness_analysis.py sha256 `a6dbd8d2…`、Result.md sha256 `de951bdc…`），并亲读原始主/子 JSONL。本文件为新增记录；不改写 execution-report/verdict/snapshot/原产物。不评分、不读 V2（直到全五题 seal）。

## 1. Root 发现的亲读复核：cluster-robust variance 实现缺陷（成立）

亲读 `output/robustness_analysis.py` 实际代码：

- 第 259 行 `X_mat = np.column_stack([np.ones(len(X)), X])`：n×2 设计矩阵。
- 第 270 行 `A_g = X_g.T @ resid[mask]`：`(2×n_g) @ (n_g,)` → **一维长度 2 数组**（cluster 的 score 向量）。
- 第 271 行 `cluster_sum += A_g @ A_g.T`：一维数组的 `@` 为内积 → **标量**，随后广播进 2×2 `cluster_sum`（每次 += 使全部四个元素加同一标量）。
- 注释（第 267-268 行）声称 `V = (X'X)^{-1} [sum_g X_g' A_g A_g' X_g] (X'X)^{-1}`，代码未实现该公式：标准 sandwich 的中间项应为 score 向量的 **外积** `np.outer(A_g, A_g)`（2×2），代码用的是 **内积**（标量）。

操作者独立机械验证（纯 numpy 行为核查，未重跑本题科学分析、未触碰被测工作区）：取 n_g=2 的小样例，`A_g = [5, 13]`，`A_g @ A_g.T = 194.0`（ndim=0 标量），而 `np.outer(A_g, A_g) = [[25,65],[65,169]]`；`cluster_sum += 194.0` 后变为 `[[194,194],[194,194]]`。与 root 的 [2,3] 小样例结论一致：表达式为标量而非矩阵。由此 `cluster_sum = [[S,S],[S,S]]`（S=Σ_g 内积），`V_cluster = S · XTX_inv · J · XTX_inv`（J 为全 1 矩阵，秩 1 结构）——**不是任何 cluster-robust covariance 的中间项**；`robustness_results.json` source_site_clustering 的全部 SE/t/p 数值由该错误结构派生。

原日志轨迹：

- 子 C JSONL（agent-aee18094f93876624.jsonl）**行 43 的 Write 初写即包含 `cluster_sum += A_g @ A_g.T`**；其后无任何 Edit 修改该行（全文件唯一出现）。
- 主 JSONL 中与 robustness_analysis.py 相关的接触仅为第 189 行 Bash `cp`（复制到 output/）与第 269 行 Edit（对象是 Result.md，old/new 字符串中提及该脚本文件名）。**主 Agent 从未 Read 过该脚本源码**；其在 Result.md 第 81 行 "Note on sample filtering" 中引用的 "lines ~247–252" 是对操作者反馈文本的转述，非亲读核对。
- 轮 002/003 的修订本质是让报告文字与 robustness_results.json 的数字一致；数字本身由错误方法产生——印证 root 要求：不能仅凭表格与 JSON 数值吻合关闭。

## 2. 结论影响

- **受影响**：Result.md Finding 3 的核心主张（"Source/site correlation invalidates the statistical significance…"，含第 79 行 "≈7× increase"、第 78 行全部 clustered SE/p、Abstract 第 3 点 "p > 0.27"）。依赖该聚类实现的 SE/p 数值**尚不能视为方法已验证**；这些数字无论与报告多么吻合，均由错误 sandwich 派生。
- **不受影响**（均不调用 `cluster_robust_se`，grep 全文件仅第 241 定义与第 298 调用）：baseline_ols、mechanical_coupling（Chow test）、bin_analysis、bayesian_posterior、outlier_sensitivity、prior_compilations、distribution_comparison，以及 Finding 1/Finding 2 的 OLS/t/ANCOVA 主张。
- 单观测 cluster 过滤问题（轮 002 已披露）与本次内积/外积缺陷相互正交：即使不过滤，sandwich 中间项也是错的。Result.md Limitations 中 "this filtering is necessary for cluster-robust SE estimation" 的声明同样未经验证。
- 三个主体分支（行 94/100/102）提前委派是**真实行为**：每个子 Agent 有真实 Read/Bash/Write/Edit 轨迹，主侧真实消费整合（行 126-172、179、182）。委派真实性与方法正确性是两个独立维度，分别记录：本缺陷不否定委派与执行的真实性，但否定 clustered 方法的已验证性。

## 3. Result.md 第 79 行同样本措辞与口径核对

现文（sealed 版第 79 行）："Within the *same* fluvial complete-case sample (n=6,128), the OLS timescale slope is -0.0305 (SE=0.0041, p=7.4×10⁻¹⁴). After Reference clustering on the reduced sample (n=6,109, see note below), the SE inflates to 0.0284 (≈7× increase)…"

- 数字核对：OLS slope=-0.0305/SE=0.0041/p=7.39e-14/n=6128（robustness_results.json baseline_ols.fluvial ✓）；clustered SE=0.0284/n_obs=6109（clustered_results.Fluvial.Reference ✓）；0.0284/0.0041≈6.9≈7× ✓。
- 口径判定：句内**已明确区分**两个样本（OLS n=6,128；clustered n=6,109 并标注 "on the reduced sample…see note below"），"same sample" 修饰语仅覆盖 OLS 半句——措辞与口径披露基本一致；但 "≈7× increase" 的分子分母仍来自两个不同 n 的回归，且在方法实现错误下该比值本身无方法学意义（见 §2）。

## 4. clean replay 归属更正

干净目录复现（3 脚本 rc=0、5 个输出文件与快照 sha256 一致）为**操作者**以一次性 docker 容器（tibv31-9a7ed51f-worker:candidate，--rm）在 /private/var/folders/.../opencode/es-repro/ 副本上执行，**不是被测 Agent 自主完成**。execution-report §5 与 verdict.json 均记为操作者执行（"clean_reproduction_operator_verified"），此处再次明确归属。注意：该复现只证明脚本确定性，不能证明 clustered 方法正确（同样运行了错误实现）。

## 5. 待办（仅在后续会话实施，不在已封存会话操作）

1. 用独立合成数据对比 `statsmodels`（如 `cov_type='cluster'`）等参考实现，量化该错误 sandwich 对 SE/p 的数值影响方向与幅度。
2. 修正中间项为 score 外积（保留或不保留单观测 cluster 两种口径分别处理），重跑 robustness_analysis.py，观察 Finding 3 的 clustered SE/p 与结论是否改变。
3. 重估 Abstract/Finding 3 表述：若正确 CR1 下结论改变，需说明轮 001-003 的报告在哪些数字上失真；若不变，记录"结论对该缺陷稳健"的证据。
4. 主 Agent 审读行为缺口：其报告修订未亲读被引用的脚本源码（仅转述操作者反馈），如需作为能力证据应另行验证。

## 6. 边界声明

本 addendum 仅依据本题本轮亲读原件与机械验证；未读取 TruthInsightBench/、evaluations/、V2 科学结果或他题证据；未重启/未修改任何共享服务与封存产物；未向被测会话发送消息；未评分。
