# Comparison V2 → V3 · EarthScience_01_glacial_fluvial_erosion

写作时机：五题 V3 sealed.json 全部存在之后（2026-10-16 10:10:42Z 门槛满足）；仅阅读本题 V2 的 run.json、rounds/、snapshots/、reviews/、docs/execution-report.md、docs/comparison-v1-v2.md 与两环境 ready.json/versions.txt；未读其他题 V2/V3 科学内容；seal 后未再向任何被测会话发送反馈。不评分、不调用 judge。

## 结论前置

| 维度 | 判定 | 同口径证据 |
|---|---|---|
| 首轮科研自主表现（委派范围与时机） | **改善** | V2 R1 主体分析全部主侧单干（V2 报告 §1：L43–L128 单干、L136 唯一委派发生在主体分析与报告撰写之后、仅事后数值复核，自评"自主委派不足"基线）；V3 R1 未收任何提示即前置 3 个并行专项 general-purpose 委派（主 JSONL 行 94/100/102，Branch A 数据审计/B 核心分析/C 稳健性），核心分析由子承担、主侧仅整合（行 126–182） |
| 首轮共享上下文加载 | **改善（保留缺口）** | V2 R1 读 5/6 references＋缺根 CLAUDE.md 实读与 delivery.md（V2 报告 §1/§5）；V3 R1 读全部 6 references＋INDEX.md（主 reads 行 67/68/73/74/75/76），保留缺口：根 project/CLAUDE.md 全程无显式实读（两代相同，仅自动注入） |
| 匹配 V2 科研轮数（第 3 科研轮）时的状态 | **相当（收敛轮形态不同）** | 两者第 3 轮均为轻量收敛轮：V2 R3 归属证据链核验 ~209s、validator PASSED；V3 R3 单项数字修正 34.9s、validator 通过（0 errors/0 warnings）。两者均无新分析维度 |
| 最终公共交付格式 | **未变** | 两代均通过公共 validator（V2 4 findings；V3 3 findings——数量不做质量分，仅格式验收） |
| 干净目录复现 | **退化（被测自主复现缺失）** | V2 子 Agent clean_reproduction.py 独立重算核心结果（Results 1–3 <0.1% 一致，drop_first 根因双设定入稿）——被测自主复现；V3 被测 Agent 未执行任何 clean-target 复现（仅 validator），干净目录复现由操作者以 docker 一次性容器验证（3 脚本 rc=0、5 输出文件与快照 sha256 一致）——只证明确定性，不能记为被测能力 |
| 产物归属可追溯性 | **改善** | V2 存在主侧在子运行期间重跑三个子脚本的双执行（alternative_explanations.csv 最终字节为主侧重跑产物、source_audit.csv 归属歧义，verdict remaining 3 项中 2 项）；V3 无双执行：子产物直接复制进 output/（主 JSONL 行 189/195），归属清晰 |
| 核心方法已验证性 | **退化（新发现）** | V3 子 C 自写 cluster-robust SE 实现存在 sandwich 中间项缺陷（第 270 行 A_g 一维、第 271 行内积为标量广播进 2×2；正确应为外积）——root 后审发现、操作者亲读复核（docs/root-review-addendum.md）：Finding 3 与 Abstract 第 3 点依赖的 clustered SE/p 尚不能视为方法已验证；V2 verdict 无对应方法级未验证项（V2 该维度遗留为过程可追溯问题） |
| 总耗时 | **改善（运行时间）** | V2 科研运行 1232s（369+654+209）＋排队 23min；V3 872s（639.8+197.6+34.9）＋排队 ~15.7min（R1 前 8.7min＝08:50:16→08:59:00 POST、R2 前 ~7min＝09:15:37→09:22:34、R3 前 0min）。注：V3 报告 §6 "约 19 分钟"为观察到 RUNNING 的时刻差，准确排队时长以 process.log POST 时间戳为准，此处更正 |
| 科学正确性 | **无法判断** | 评分禁止；两代均未调用 judge；单次运行 |

上述判定均为单次运行观察；混杂未排除（见 §4），不构成统计结论，不能把变化全部归因于共享 Skill 3.1.0。

## 1. 首次科研自主表现（反馈前留证）

- **V2 R1**（run_39b1b62025ec4527，369s）：未收提示下读 INDEX/SKILL/delegation-contract/data-design/inference/verification＋context/delegation.md；主体分析（盘点、主统计、分箱、多变量、winsor、图表、报告）全部单干；唯一 Agent 调用（L136）为事后数值复核；子 Agent a51284ef 真实独立执行（32 行 JSONL）。SendMessage 空 content ×2 未恢复。
- **V3 R1**（run_4c18eaaee41340c6，639.8s）：未收提示下读 INDEX/SKILL/全部 6 references＋任务契约与数据文件；写 working/analysis-state.md（r1）登记 F1–F8 与三分支分工；前置 3 个并行 general-purpose 委派（4 上限内、run_in_background=true），子 A/B/C 各自真实执行（Bash 21/22/16 次；子 B 含 ~8 次调试迭代）；主侧等待后亲读子产物并整合（行 126–182）；轮内 validator 失败后自愈（行 198→208→211）。
- 同口径保留项：V3 R1 的交付也含当时未发现的方法与报告缺陷（§3 root 后审）；其"委派前置"改善指执行形态，不涉及科学质量。

## 2. 匹配 V2 科研轮数时（第 3 科研轮）

- V2 R3（~209s）：响应归属核验反馈，自建 CSV 哈希/mtime/时间轴证据链并逐 CSV 归属表入稿。
- V3 R3（34.9s）：响应单项数字错误反馈（glacial(b) 248→154），修正并标注来源，validator 通过。
- 两者第 3 轮都在"操作者事实反馈→被测自行核查→文档同步"机制下收敛，均无新分析维度。判定相当。

## 3. 最终表现与剩余限制

- **V2 终态**：12+ 文件（Result.md 19614B、8 CSV、2 figures、7 脚本）；validator passed；verdict REVIEWED_WITH_ISSUES，remaining：source_audit.csv 双执行归属歧义、alternative_explanations.csv 主侧重跑覆盖、SendMessage 修复未实测。
- **V3 终态**：10 文件（Result.md、3 脚本、5 结果工件、reproduce.md）；validator passed（0 errors/0 warnings）；verdict REVIEWED_WITH_ISSUES，remaining：binned_means.png 未目验、单观测 cluster 过滤必要性声明未独立验证；root 后审新增：clustered SE 方法未验证（root-review-addendum.md §1–2）。
- 报告-机器数字一致性：V3 终稿经操作者逐项核对与两轮反馈后与 JSON 一致（gap 1.22/1.07/0.05/1.39、t=20.52、F=489.7、Chow 3698/0.44、clustered 表内数字、三口径 265/248/229 各自标注）；但其中 clustered 列的方法实现未验证——数字吻合≠方法正确。
- 反馈轮数/类别：V2 两轮（R2=上下文加载+委派分工——行为塑造类；R3=产物归属——过程追溯类）；V3 两轮（R2=六项报告-机器一致性与披露——审计类；R3=单项数字转写——审计类）。类别不同：V2 反馈改变执行形态，V3 反馈仅修订报告与披露，故两代"反馈后改进"不可直接互比幅度。
- 主/子模型：两代实际均 qwen3.7-flash（V2 336 条、V3 283 条 assistant 消息＋各 1 条 warmup \<synthetic\> 占位）；fallback 均为空。
- 单请求 input tokens：V3 主最大 86,004、子 41,959–56,954（audit unique_api_messages=145，dedup input 7,198,270/output 84,390）；V2 题级仅 usage 汇总、逐子明细缺测（V2 comparison §3 已记缺测）——token 维度无法同口径比较，缺测如实标注。

## 4. 一致性核实与混杂因素

**一致性核实（两代相同项）**：后端 6d529489815362eb2d6cf717e736e44936de3afc（V2 报告 L4；V3 run-spec）；主/子模型 qwen3.7-flash＋fallback 空（两代 ready.json 与原始 JSONL 核验）；SDK 0.2.154、CLI 2.1.274 及全部科学依赖版本（numpy 2.4.6/pandas 3.0.3/scipy 1.17.1/sklearn 1.9.1/statsmodels 0.15.0/matplotlib 3.11.1/seaborn 0.13.2/openpyxl 3.1.5/h5py 3.16.0，两环境 versions.txt 逐项相同）；预算 max_turns 500/rounds 40/4 子并发/2 运行槽；原始输入（LaunchPrompt sha256 0f4cafd2…、28 个输入文件哈希逐项相同）；操作者布局（五独立操作者、一人一 Conversation、无额外探针会话）；外层操作者模型 GLM-5.3-Flash-W4A16-MTP（V2 实测默认沿用，未迁移）。

**差异与混杂（必须注明）**：
1. **Subject 同时变更**：V2 subject a25e2d2 → V3 subject 3.1.0（Skill、系统提示词、薄入口同时修订）；提示词与 Skill 效应在本设计内不可分离。
2. **Worker 镜像重建**：V3 image sha 06f5037e…/digest 89ff1e3e… ≠ V2 c9e44c5d…/df13c738…——依赖版本清单一致但镜像字节不同，平台层非严格同镜像。
3. **操作者实例独立**：外层模型同款但为两个独立 session 实例，审读风格与反馈粒度不同（V2 行为塑造 vs V3 源码审计）——root 进度审读（root-review-addendum）在 V3 是额外干预层，任何 V3 优势的归因必须保留此限制。
4. **V2 中途操作者干预单列**：V2 R2 反馈实质性地把执行形态从单干改为有界分工（V2 报告 L45 自认"第 2、3 轮的分工改进不能记为自主表现"）；V3 R1 的前置委派发生在任何操作者反馈之前，两代首轮自主性的对比因此成立，但 V2 的对比基线是"被反馈重塑后"的第 2 代终态。
5. **两轮反馈差异**：见 §3；反馈内容本身即干预，无法标准化。
6. **随机性限制**：每代单次运行、每题一观察；会话级随机性（温度、采样、排队顺序）不可控；所有"改善/退化"仅为本题单次观察，无统计效力，不排除会话间方差。

## 5. 未解决问题（带入后续，不再向任何被测会话反馈）

1. V3 clustered SE 的 sandwich 缺陷需待办实验验证（修正为外积、对比参考实现、重估 Finding 3）——仅列待办，不在已封存会话实施（见 root-review-addendum §5）。
2. 根 project/CLAUDE.md 显式实读两代均缺失（V3 全程；V2 靠 R2 补读）——薄入口设计下其必要性存疑，但口径差异应保留。
3. V2 的 source_audit.csv 归属歧义未重建；两代严格空目录冷复现均未由被测自主完成（V2 为子 Agent 同目录重算；V3 为操作者干净副本验证）。
4. 科学正确性两代均未评判；Skill 3.1.0/系统提示词/后端 main 的效应不可分离。
