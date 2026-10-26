# V3 终态科学结果审读：题目是否做得足够好

**结论：还不足以把五题终稿直接当作可靠的科研结论交付。** 五题都包含有价值的描述性结果，但仍有影响核心主张的实现错误、分析对象错配或证据强度过度解释。这里评价可验证主张的成立范围，不调用 benchmark judge、不读取隐藏答案、不产生分数或排名。

五题已于 2026-10-16 18:09:43（Asia/Shanghai）全部封存；共享资源清理收据时间18:09:56。本次 2026-10-17 审读使用各题 sealed.json 指向的最终快照，444 项 manifest 校验全部一致，原封存产物未改。Docker 以本轮名称前缀查询容器、网络、卷、镜像均无结果。未重开会话、派新操作者、发送科研消息或恢复定时任务。

审读范围：五份 ResearchObjective、DATA_GUIDE 与最终 Result.md，关键脚本和机器结果、必要原始表，既有执行报告与补录；V2 对比报告只作干预归因背景，不用作本轮正确答案。定向复核脚本及数值见 [diagnostics.py](diagnostics.py)、[diagnostics.json](diagnostics.json)。这些是 root 封存后的只读诊断，使用独立审读环境 Python3.12.14/NumPy2.3.5/pandas2.2.3，不是新模型实验或同栈 benchmark 重跑。没有全量重新求解五题。

## 逐题判断

| 题目 | 已有可保留内容 | 最影响结果质量的缺口 |
|---|---|---|
| 化学 | 能量网格对齐已纠正，曲线极值、非单调结构等有数据依据 | 核心相位差未排除2π分支；置信度使用密集派生网格；若干结论与实现/自身数值矛盾 |
| 物理 | buffer 增加伴随延迟减小、有限尺寸变化等描述有支持 | 把优化搜索下限解释为时间尺度饱和；模型比较不足以区分转变与平滑解释 |
| 天文 | 已供候选表内的相对排序、残差描述及模型间差异有支持 | 非等间隔采样直接做FFT；频率分辨率与Nyquist混用；LOO没有检验被宣称的谱结构 |
| 地学 | 方法分层及数学耦合风险的识别有价值 | 聚类方差实现错误；更正后非显著仍保留，但不能据此认定少数研究驱动；调整效应口径混写 |
| 神经 | 缺失设计单元、区域/条件混杂的识别有价值 | 核心统计仍未控制年龄/切片/批次；分组键作用域未查明；非显著被解释成效应很小 |

## 化学：核心相位差的科学含义尚未建立

题目要求联合研究能量、角度、相位、延迟、振幅和矩阵元之间的结构与实验/理论差异。当前终稿把约4.08 rad差异和随能量增长解释成可能缺失的理论物理，但没有先解决相位的周期性及参考约定。

1. **主张对相位分支高度敏感。** 按原数据和同一 not-a-knot 三次样条对齐，root 精确复现 mean(abs(exp−theory))=4.0781000658 rad，与已存 JSON 差为0。相同对齐数据的圆周距离 mean(abs(angle(exp(iΔφ))))=0.4647860890 rad；85°处直接绝对差均值6.38475 rad，圆周距离仅0.10157 rad。63.54%的网格差超过π。即使每个角度只选一个在整段能量上保持常数的整数2π分支校正，平均绝对差也降至0.87137 rad。**这些是表示方式敏感性检查，不是宣告0.465或0.871为正确科研答案。** 必须证明相位约定一致，并检查延迟/能量导数等更贴近题目目标的量，才能把大绝对差解释成物理差异。相位的2π周期及unwrap的作用见 [NumPy 官方说明](https://numpy.org/doc/2.3/reference/generated/numpy.unwrap.html)。
2. **报告所说的计算顺序仍然错误。** [终稿双口径段](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Chemistry_02_photoionization_delay/snapshots/20261016T100943-539ca/project/output/Result.md:39)称4.08来自先平均角度再取绝对差；[实际代码](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Chemistry_02_photoionization_delay/snapshots/20261016T100943-539ca/project/output/analysis_fix_energy_alignment.py:101)做的是先逐格取绝对差再平均。前一种定义在相同数据上是2.6690264014 rad。这是方法描述与计算对象的直接错配。
3. **不确定性没有落到真实独立单位。** 数据指南明确密集网格来自13个测量能量块，终稿却把99个理论能量索引的回归p值当成很强证据。[扰动代码](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Chemistry_02_photoionization_delay/snapshots/20261016T100943-539ca/project/output/analysis_fix_energy_alignment.py:127)对插值后的格点添加独立噪声，标准差为整体相位最大绝对值的1%；这只能检验该人为噪声设定，不能提供实验不确定性或原始13块的置信区间。正文虽然写了相关性限制，核心p值/窄CI的解释没有相应收缩。
4. **简单事实矛盾仍在终稿。** [F20段](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Chemistry_02_photoionization_delay/snapshots/20261016T100943-539ca/project/output/Result.md:78)称24.8eV是全能区最低值；原始F20 order0在48.4eV为0.26214，比24.8eV的0.346347更小。[DME段](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Chemistry_02_photoionization_delay/snapshots/20261016T100943-539ca/project/output/Result.md:92)把p=0.095写成在5%水平边缘显著，后文又写未达到0.05。最新复现声明已从15/15改为14/15加直接重建，这一诚实性改进应保留，但它并未解决上述科学问题。

因此，可保留部分曲线描述和特征定位；实验/理论物理差异的大小、证据强度及跨表机制整合还不够可靠。

## 物理：优化边界被写成物理现象

题目明确要求比较平滑、分段、非线性、无可辨边界及有限尺寸解释，并做窗口、条件留出和方法敏感性。当前报告对这些比较的覆盖仍不充分。

1. **所谓时间尺度饱和是搜索下限假象。** [终稿](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Physics_04_temporal_delay_transition/snapshots/20261016T094435-cdafa/project/output/Result.md:44)把B4/B5相对B1的缩放因子都为0.1解释成饱和或floor effect。但[实际搜索](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Physics_04_temporal_delay_transition/snapshots/20261016T094435-cdafa/project/output/analysis.py:235)只允许scale≥0.1。root保留同一数据、同一相关系数目标及线性插值/外推，仅把搜索拓展到0.001–0.0999，B1/B4的最优值变为0.0644，相关系数从0.98616升至0.99991；B1/B5变为0.0302，从0.92426升至0.99979。两条曲线的绝对RMSE也分别从0.0681/0.1592降到0.00790/0.01189。故“二者同尺度/饱和”这一解释没有依据。
2. **外推污染了所谓collapse质量。** 原B1/B5最优值0.1时，72.67%的比较点处于B5观测区间之外。拓展下限后仍有约9.66%外推，因此新数值只是定位原错误的诊断，不是完整修复。最终科学比较仍需共同可观测区间、幅值误差与跨条件一致的缩放规则，不能仅优化Pearson相关。
3. **转变与竞争模型未被真正裁决。** [分段搜索](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Physics_04_temporal_delay_transition/snapshots/20261016T094435-cdafa/project/output/analysis.py:51)最大化两段斜率差，没有构成与平滑候选同口径的预测误差或复杂度控制比较；LOO重点检验已供理论曲线上的阈值。[有限尺寸段](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Physics_04_temporal_delay_transition/snapshots/20261016T094435-cdafa/project/output/Result.md:75)甚至用R²>0.999声称其他函数形式几乎无空间，这不能代替候选模型比较。把这些未完成的现有数据检验全部留作将来采新数据，也未充分完成题目。

可保留下降趋势及候选有限尺寸拟合；时间尺度饱和、普适曲线与排他性转变解释需要重新论证。

## 天文：有候选偏好，尚未建立稳健谱结构

1. **七个pass并非等间隔采样。** 原始时间轴中pass02/03/09/10/15/18/19有不等间隔，[FFT代码](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Astronomy_02_gravity_spectral_structure/snapshots/20261016T100423-97597/project/working/subagent_fft_loo_corrected/corrected_fft.py:93)却取mean(diff(t))后直接rFFT。时间缺口未重采样，也未使用适用于不等间隔的估计。SciPy 对等间隔DFT及不等间隔Lomb–Scargle的边界有明确区分，见[官方频谱说明](https://docs.scipy.org/doc/scipy/tutorial/signal.html)。这会影响把频率格点出现次数当成重复谱峰的解释。
2. **Nyquist足够不等于窄谱峰定位充分。** 实际窗口60–79分钟，原FFT格点间距约208–273 μHz；1010与1060 μHz仅相差50 μHz。当前普通FFT的top5格点计数不能独立确认如此窄的定位或峰宽。模型化的亚格点估计原则上可能，但本轮没有实现或验证它。报告把所有pass写成79分钟也不符合原始表。
3. **稳健性检验没有针对核心对象。** [LOO产物](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Astronomy_02_gravity_spectral_structure/snapshots/20261016T100423-97597/project/working/subagent_fft_loo/loo_results.json:1)只给每次删pass后的残差均值、标准差和变化比例，没有重估谱峰、宽度或候选排序。因pass01影响总体std，就推测IC排序被它驱动，不能满足“首选候选是否通过整pass/整窗口扰动”的题目目标。top5出现13/22本身也没有无结构或相关噪声基线。
4. **条件性限定没有覆盖核心标题。** 最后第8轮已把跨表IC比较改为条件性，这比前稿准确；但[Finding4标题](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Astronomy_02_gravity_spectral_structure/snapshots/20261016T100423-97597/project/output/Result.md:146)仍无条件称结构模型dramatically outperforms。共享候选子集的数字一致只能核对那两个表，不能独立证明第三张uniform表的定义/归一化相同。

候选表内部的偏好是可报告结果；“真实窄谱结构获得独立FFT与跨pass支持”则证据不足。部分描述和排序本身可用，不能由此推出物理唯一性。

## 地学：实现错误需要更正，但不能夸大更正的影响

主体按方法分层、指出rate与time数学耦合的风险，确实切中了题目。问题集中在聚类和效应解释。

1. **聚类SE算法有确定错误。** [实现](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/EarthScience_01_glacial_fluvial_erosion/snapshots/20261016T093515-ca9ab/project/output/robustness_analysis.py:270)对长度2的一维score向量使用内积，得到标量并广播入2×2矩阵。标准cluster sandwich使用每个group score的外积，见[statsmodels源码](https://www.statsmodels.org/dev/_modules/statsmodels/stats/sandwich_covariance.html)。root在完全相同原始筛选和小样本修正下单独计算CR1：glacial/Reference的SE从错误的0.191575变为0.047603，fluvial/Reference从0.028370变为0.023481。
2. **修正后的总体非显著结论仍保留。** 同原过滤样本，Reference聚类p约为0.987（glacial）和0.191（fluvial）；保留单观测cluster时约为0.150和0.193。不能说修复该代码就证明总体趋势显著。原数字需要纠正，而“未发现稳定总体斜率”的谨慎表述仍有支持。
3. **非显著不能证明少数研究驱动。** [终稿](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/EarthScience_01_glacial_fluvial_erosion/snapshots/20261016T093515-ca9ab/project/output/Result.md:87)把聚类后的非显著解释成少数研究造成的假象；这需要具体的study influence或leave-study-out证据。原全样本glacial斜率−0.05666，删单观测cluster后变为−0.000758，点估计的变化也不能归因于只改变SE。对同一样本比较与保留单观测cluster的诊断需分开。
4. **调整与未调整的效应量混用。** 摘要把约0.904 log10、约8倍写成控制timescale和method之后的差异，实际0.904来自简单组均值差；加入协变量的代码和结果给出过程系数1.027。可保留关联方向，不能把未经调整的数量级当作调整估计，更不能自动作因果解释。

本题有价值的科学框架已经形成，但终稿中方法依赖的数值和机制归因仍不足以直接采用。

## 神经：识别了混杂，主分析却没有真正处理

1. **题目要求的调整未进入核心估计。** [交互模型](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Neuro_02_calcium_response_regions/snapshots/20261016T093148-64cf6/project/output/main_analysis.py:53)只有region×condition，[两两比较](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Neuro_02_calcium_response_regions/snapshots/20261016T093148-64cf6/project/output/main_analysis.py:73)是细胞级Welch，[批次比例](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Neuro_02_calcium_response_regions/snapshots/20261016T093148-64cf6/project/output/main_analysis.py:120)是单因素batch平方和。主张已accounting for age/slice/batch，以及batch在控制region/condition后仍解释某比例，强于实际执行。leave-one-batch-out重复保留细胞上的同一检验，只能检查单批次敏感性，不能替代对切片依赖、年龄和批次的处理，也不是在被留出批次验证预测。
2. **切片键的作用域没有查清。** 数据有7个slice标签，但它们跨9个batch重复，组合成41个(batch,slice)对。当前按(slice_id,region,condition)聚合得到50组，按(batch,slice_id,region,condition)则为99组。代码确实把来自不同batch、不同年龄的同名slice记录合并了。是否属于同一物理切片需要元信息；在确认前，50组不能直接代表有效独立重复数。
3. **拟合后API报错被写成收敛失败。** fit已返回且打印LogL，随后访问`.values[0][0]`报错；其他模型摘要显示Converged=True。这个已被原操作者补录确认，终稿本身仍保留错误说明。无法运行部分模型应限制对应主张，不能以失败标签绕过更合适的分析。
4. **阴性解释过强。** [R4效应](/Users/zhengyidi/yage/context-infrastructure/adhoc_jobs/truthinsight_bench_harness/experiments/shared-context-v3.1-20261016/batches/qwen3.7-flash-main-6d52948-20261016/runs/Neuro_02_calcium_response_regions/snapshots/20261016T093148-64cf6/project/output/Result.md:128)含d≈0.56/0.52等数值，且样本较少，终稿却概括成minimal changes。没有等效性界限或足够精度，未显著只意味着本次证据不足。题目允许unresolved解释，应该在核心结论中保留，而不是只放在limitations。

缺失设计单元、R3/R4不可估计对比的分析可保留。刺激效应的量级、区域交互与batch解释必须以正确层级和实际调整后的证据重写。

## 对下一轮 Harness 优化的含义

本次不修改冻结Skill或系统提示词，不启动V4。应优先讨论以下可迁移结果标准，而不是为五题写预置科学答案：

- 核心主张需要通过一次足以区分竞争解释的检验。相位分支、搜索边界、采样假设、聚类实现等都有可定位的反例；不能把“限制已经列出”当成问题已解决。
- 验收要核对“检验的对象是否就是主张对象”。总体标准差稳定不等于谱峰稳定，相关很高不等于曲线重合，删批次后p仍小不等于已控制层级混杂。
- 关键自写统计实现需要参考实现或独立等价计算；边界最优、异常处理、分组键作用域要有实际诊断。只复算同一公式的数字可能复制同一错误。
- 反证必须改变标题、摘要和机器结果的结论强度。对目前数据做得出的结论，允许明确停在“描述性支持/条件性支持/尚不能区分”，并解释剩余不确定性。

**操作者口径也需要澄清。** 地学比较报告把“科学正确性无法判断”直接关联到评分禁止，神经报告有同类措辞，天文报告也称没有作quality judgment。不评分禁止的是数值打分、隐藏标准和judge调用；它不应阻止检查科学主张、计算方法及题目覆盖。本次审读正是在该边界内完成。此前数值与文件一致性的纠错有价值，但不能替代结果有效性审读。

这些五题各一次、且反馈次数不一致的运行，也不足以证明V3 Skill相对V2造成了科学质量提升。当前最可信的结论是：过程可追溯性有所增加，但核心主张的有效性仍是主要缺口。
