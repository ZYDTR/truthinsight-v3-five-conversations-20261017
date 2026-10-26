本题已经 seal。严格保留封存边界：不重开、不发 SAP 科研消息、不改写 execution-report/verdict/snapshot/原产物。请仅亲读自己题目的原件并新增 docs/root-review-addendum.md，记录如下新发现及其结论影响；不评分、不读 V2（直到全五题 seal）。
root 发现 output/robustness_analysis.py 第 259 行 X_mat 为 n×2，第 270 行 A_g=X_g.T @ resid[mask] 为一维长度 2 数组，第 271 行 A_g @ A_g.T 因而是标量，随后广播进 2×2 cluster_sum。这不是声明的 cluster covariance 中间矩阵。root 仅用 [2,3] 的独立维度小样例验证：此表达式为标量 13，非矩阵；没有重跑本题科学分析。请亲查实际代码与原日志，标注依赖该聚类 SE/p 的核心结论尚不能视为方法已验证，不能仅凭表格与 JSON 数值吻合关闭。
另请准确记录：Result.md 79 行的同样本措辞与 n=6128/6109 两种样本口径是否一致；clean replay 是操作者执行，不能记成被测 Agent 自主完成。提前三个主体分支委派是真实行为，与以上限制分别记录。需要进一步实验验证的内容只列待办，不在已封存会话实施。
