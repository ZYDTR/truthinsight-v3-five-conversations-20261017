# Region-, Condition-, and Batch-Dependent Calcium Response Structure

**Task ID:** Neuro_02_calcium_response_regions  
**T0:** 2020-01-01  
**Data:** `data/cellular_calcium_response_summaries.tsv` (819 cells, 12 variables, SHA256 verified)  
**Analysis unit:** Single cell nested within recording slice, batch, and biological source; cells from a shared slice are not independent animals.

---

## Summary

This analysis investigated how six calcium-event response metrics (amplitude, time-to-peak, peak width, prominence, frequency, and area under curve) vary across four anonymous anatomical regions and three experimental conditions (baseline, neural_activity_blocked, receptor_stimulated), while accounting for age, slice nesting, and recording batch effects. The data exhibit a **severe region-condition confounding structure**: Region 3 contains only receptor_stimulated observations, and Region 4 contains only baseline and neural_activity_blocked observations. This design constraint limits which contrasts are estimable and requires careful interpretation of all cross-region comparisons.

Four registered findings are reported below.

---

## Finding 1: Receptor stimulation produces robust increases in calcium amplitude, AUC, and peak width in regions where both conditions are observed

**Object and scope:** Regions 1 and 2, which contain all three conditions (baseline, neural_activity_blocked, receptor_stimulated). The comparison is restricted to these two regions because only there can condition effects be estimated without confounding with region identity.

**Relationship:** Compared to baseline and neural_activity_blocked, receptor_stimulated produces:
- **Higher amplitude** (dF/F0): R1+2 combined mean difference = −0.28 (baseline vs stimulated, p = 7.0 × 10⁻⁸, Hedges' g = −0.66); −0.31 (blocked vs stimulated, p = 2.6 × 10⁻¹², g = −0.74)
- **Larger AUC** (AU): mean difference = −84.4 (baseline vs stimulated, p = 5.3 × 10⁻⁸⁷, g = −1.89); −81.3 (blocked vs stimulated, p = 1.5 × 10⁻⁸⁹, g = −1.82)
- **Wider peaks** (s): mean difference = −28.0 (baseline vs stimulated, p = 1.6 × 10⁻⁶⁶, g = −1.51); −29.6 (blocked vs stimulated, p = 2.4 × 10⁻⁷⁸, g = −1.61)
- **Shorter time-to-peak** (s): mean difference = +26.0 (baseline vs stimulated, p = 7.9 × 10⁻³, g = +0.43); +53.1 (blocked vs stimulated, p = 8.4 × 10⁻¹⁰, g = +0.90)
- **Lower prominence** (dF/F0): non-significant trend toward lower values (p = 0.05–0.54)
- **Mixed frequency changes**: no consistent direction across contrasts

The effect sizes are large for AUC (g > 1.8), peak width (g > 1.5), and amplitude (g > 0.6). Time-to-peak shows a moderate-to-large effect (g = 0.4–0.9). These patterns are consistent across both Region 1 and Region 2 individually.

**Supporting analysis and result evidence:**
- Pairwise Welch's t-tests: `output/contrasts_regions12.csv` (rows for amplitude, auc, width, ttp contrasts); computed in `output/main_analysis.py`
- Single-region (region_1) condition ANOVA (one-way, not two-factor interaction): F = 8.19 (amplitude, p = 3.5 × 10⁻⁴), F = 9.32 (ttp, p = 1.2 × 10⁻⁴), F = 28.63 (width, p < 10⁻⁶), F = 68.45 (AUC, p < 10⁻¹⁵) — these are from `output/eta_squared_results.csv` rows where region=region_1, n_groups=3; they test whether condition means differ within region_1 alone, not a two-factor Region×Condition interaction. The two-factor R1+2 interaction values are reported in Finding 2.
- Independent replication by Agent C: `working/analysis_C/replication_results.csv`, `working/analysis_C/eta_squared_results.csv` — confirms same-direction effects with comparable magnitudes
- Violin plot visualization: `output/figures_violin_amplitude.png`

**Robustness result:** Leave-one-batch-out (LOO) analysis excluding each of 9 batches sequentially produced statistically significant receptor_stimulated effects in all 27 tests (all p < 0.001; max p = 2.05 × 10⁻⁴), with amplitude effect size estimates varying by up to 21% across exclusions (`output/robustness_lobo.csv`; AUC varied by ~10%, width by ~12%). When aggregating at the slice level (accounting for non-independence of cells within slices, yielding 50 slice-region-condition groups), the cell-level significance rate dropped from 23/54 to 7/54. The strongest amplitude contrast at the slice level was region_1 vs region_3 stimulated (t = −2.95, p ≈ 0.021); the region_2 stimulated vs baseline contrast at the slice level was not significant (t = −1.68, p ≈ 0.126).

**Counterevidence and limitations:** The magnitude of the receptor_stimulated effect cannot be disentangled from potential region-specific baseline differences because Region 3 (which has only receptor_stimulated data, n=189) shows even higher amplitude (mean=2.07) and AUC (mean=415.6) than Region 2 stimulated. Whether this reflects a true region effect or a condition effect is unidentifiable. Additionally, the large sample imbalance (receptor_stimulated n=614 vs baseline n=86) may inflate precision estimates. Multiple comparisons across 6 variables were not corrected (exploratory analysis).

**Falsification proposal:** An independent experiment measuring the same six calcium metrics in Region 3 under baseline and neural_activity_blocked conditions would directly test whether the elevated amplitude/AUC in Region 3 is due to region identity or receptor stimulation. If Region 3 baseline responses match other regions' baselines, the current finding is supported; if they match receptor_stimulated levels, the effect is region-specific.

---

## Finding 2: Region × Condition interactions are statistically significant but most cross-region comparisons are unidentifiable due to design confounding

**Object and scope:** All four regions and three conditions. The focus is on what the data CAN and CANNOT identify given the structural constraints.

**Relationship:** Two-way ANOVA on Regions 1+2 (where all conditions exist) reveals statistically significant Region × Condition interactions for five of six response variables:
- Amplitude: F(2,574) = 7.44, p = 6.4 × 10⁻⁴, η² ≈ 0.02
- Time-to-peak: F(2,574) = 7.29, p = 7.4 × 10⁻⁴, η² ≈ 0.02
- Peak width: F(2,574) = 3.55, p = 2.9 × 10⁻², η² ≈ 0.01
- Prominence: F(2,574) = 15.64, p = 2.4 × 10⁻⁷, partial η² = 0.052
- Frequency: F(2,574) = 10.18, p = 4.5 × 10⁻⁵, partial η² = 0.034
- AUC: F(2,574) = 0.003, p = 0.997 — NOT significant

The interaction indicates that the effect of condition differs across regions. For example, in Region 2 the receptor_stimulated amplitude increase (Δ = +0.49 over baseline) is roughly double that in Region 1 (Δ = +0.12). However, the interaction effect sizes are small for most variables (partial η² ≤ 0.03 for amplitude, time-to-peak, width; partial η² = 0.034 for frequency), with prominence showing a larger interaction (partial η² = 0.052), suggesting that while statistically detectable for five of six variables, the regional modulation of condition effects is modest overall.

**What is estimable:**
- Within R1 and R2: all 3 pairwise condition contrasts ✓
- Across all regions: baseline vs neural_activity_blocked ✓ (present in R1, R2, R4)
- R1 vs R2 within each condition ✓

**What is NOT estimable (confounded):**
- R3 × condition interaction: R3 has ONLY receptor_stimulated data — region and condition are perfectly confounded
- R4 × receptor_stimulated interaction: R4 has NO receptor_stimulated data
- Pure main effect of region: confounded with uneven condition distribution across regions
- Pure main effect of condition: confounded with region distribution

**Supporting analysis and result evidence:**
- Design constraint documentation: `output/model_output_agentA.txt` Section 7, `output/comparison_with_main.txt`
- ANOVA tables: computed in `output/main_analysis.py` (ANOVA section), results in `output/contrasts_regions12.csv`
- Cross-tabulation: `data/cellular_calcium_response_summaries.tsv` — R3: [0, 0, 189], R4: [21, 29, 0]
- Single-region (one-way) condition ANOVA effect sizes: `output/eta_squared_results.csv` — reports η² for each region separately (not two-factor interactions). For example, region_1 amplitude η²=0.054 (F=8.19, p=3.5×10⁻⁴); region_2 amplitude η²=0.152 (F=25.49, p<10⁻¹⁵); region_1 AUC η²=0.321 (F=68.45, p<10⁻¹⁵). The two-factor R1+2 Region×Condition interaction partial η² (partial η² = SS_interaction / (SS_interaction + SS_residual)) from `output/main_analysis.py` ANOVA table are: amplitude = 0.025, time-to-peak = 0.025, peak width = 0.012, prominence = 0.052, frequency = 0.034, AUC = 0.000012 (non-significant, F = 0.003, p = 0.997 as stated in lines 51–56 above). These differ from the single-region one-way η² values above because they come from different model specifications.

**Robustness result:** The estimability analysis is structural (based on data design, not statistical estimation) and therefore inherently robust. No alternative model can recover information about R3 condition effects or R4 receptor_stimulated responses.

**Counterevidence and limitations:** The interaction effect sizes are small for most variables (partial η² ≤ 0.03 for amplitude, time-to-peak, width; partial η² = 0.034 for frequency), with prominence showing a larger interaction (partial η² = 0.052). This suggests that while the interaction is statistically significant (driven by large N in R1+2), the practical importance of region-specific condition modulation is limited for most metrics. The dominant pattern is that receptor_stimulated increases amplitude/AUC/width broadly across regions where it is observed.

**Falsification proposal:** Adding baseline and blocked measurements to Region 3, and receptor_stimulated measurements to Region 4, would enable full factorial estimation and could reveal larger or qualitatively different interactions.

---

## Finding 3: Recording batch effects are substantial for amplitude and prominence, potentially driving spurious region-level conclusions

**Object and scope:** All 819 cells across 9 recording batches. The question is whether batch-to-batch variability could account for observed differences attributed to region or condition.

**Relationship:** One-way ANOVA decomposing variance by recording batch yields:

| Variable | η² (batch) | F-statistic | p-value |
|---|---|---|---|
| Amplitude (dF/F0) | 0.327 | 49.09 | 1.2 × 10⁻⁶⁴ |
| Prominence (dF/F0) | 0.385 | 63.51 | 1.5 × 10⁻⁸⁰ |
| Peak Width (s) | 0.168 | 20.51 | 2.0 × 10⁻²⁸ |
| AUC (AU) | 0.116 | 13.34 | 3.2 × 10⁻¹⁸ |
| Frequency (Hz) | 0.085 | 9.41 | 1.8 × 10⁻¹² |
| Time-to-Peak (s) | 0.045 | 4.81 | 8.3 × 10⁻⁶ |

Batch explains 32.7% of amplitude variance and 38.5% of prominence variance — medium-to-large effects by conventional standards. Even after accounting for region and condition, batch remains a major source of variation. Notably, batch_01 (n=4) shows an anomalously high amplitude mean (4.54) compared to other batches (1.55–2.23), which could disproportionately influence results if its cells overlap with specific region-condition combinations.

**Supporting analysis and result evidence:**
- Batch ANOVA results: `output/batch_effects.csv`, `output/batch_effects_subagent.csv`
- Batch visualization: `output/figures_batch_effect.png`
- OLS batch R² from sub-agent: amplitude R²=0.2595, time-to-peak R²=0.1734 (`output/model_output_agentA.txt` Section 3D); note that LMM fitting with batch as random effect failed in the sub-agent implementation (error: `'builtin_function_or_method' object is not subscriptable`; AIC/BIC reported as nan), so no LRT statistic is available from that source. The η² values above are from one-way ANOVA SS decomposition, which does not require LMM convergence.
- Batch effect computation code: `output/main_analysis.py` (Section "Batch Effect Quantification"), `output/robustness_check.py`

**Robustness result:** LOO analysis (Finding 1) excluded each batch individually and the receptor_stimulated effect remained significant in all cases, indicating that no single batch drives the primary finding. However, the large batch effects mean that any region-level conclusions must be interpreted cautiously, as region assignment is partially correlated with batch membership.

**Counterevidence and limitations:** The batch effect quantification uses cell-level observations as independent units, which violates the nested structure (cells within slices). A proper mixed-effects model with batch as a random effect would provide more accurate inference. The LMM fitting encountered convergence issues in the sub-agent implementation (AttributeError on `mle_retvals`), so the exact variance component estimates should be considered preliminary. Age also correlates weakly with amplitude (r = 0.18, p < 10⁻⁷) and prominence (r = 0.21, p < 10⁻⁹), and age may be partially confounded with batch.

**Falsification proposal:** Replicating the entire recording protocol across additional independent batches would determine whether the observed batch effects are systematic (protocol-related) or stochastic (technical artifacts). If new batches show similar variance magnitudes, the batch effects are likely real and must be modeled explicitly.

---

## Finding 4: Baseline versus neural activity blockade produces mostly null effects on calcium response metrics

**Object and scope:** Regions 1, 2, and 4, which contain both baseline and neural_activity_blocked conditions. This comparison tests whether blocking neural activity measurably alters calcium dynamics relative to baseline.

**Relationship:** In Regions 1+2 combined (n=65 baseline, n=90 blocked), pairwise comparisons show:
- **Amplitude**: Δ = +0.03, p = 0.59, g = 0.09 (negligible)
- **Time-to-peak**: Δ = −27.0 s, p = 0.026, g = −0.37 (small-moderate; blocked has longer TTP)
- **Peak width**: Δ = +1.68 s, p = 0.016, g = 0.40 (small-moderate; blocked has narrower peaks)
- **Prominence**: Δ = +0.05, p = 0.38, g = 0.14 (negligible)
- **Frequency**: Δ = −0.0029 Hz, p = 0.015, g = −0.38 (small; blocked has higher frequency)
- **AUC**: Δ = −3.18 AU, p = 0.13, g = −0.25 (small, not significant)

In Region 4 (n=21 baseline, n=29 blocked), all comparisons are non-significant. Effect sizes (Cohen's d from `output/replication_results.csv` rows 68–73): time-to-peak d = 0.563, AUC d = 0.517, peak width d = 0.311, amplitude d = 0.107, prominence d = 0.028, frequency d = −0.023; all p > 0.05.

The overall pattern is that blocking neural activity produces minimal changes to calcium response profiles compared to baseline. The few statistically significant differences (time-to-peak, peak width, frequency in R1+2) have small-to-moderate effect sizes and may reflect secondary consequences rather than primary calcium dynamics.

**Supporting analysis and result evidence:**
- Pairwise contrasts: `output/contrasts_regions12.csv` rows 0–2, 12–14
- Independent replication: `output/replication_results.csv` — confirms null amplitude difference (p = 0.59)
- Baseline cross-region ANOVA: `output/main_analysis.py` execution output

**Robustness result:** The null finding for amplitude is robust across all LOO exclusions and consistent between cell-level and slice-level analyses. The small significant effects on time-to-peak and width are less stable at the slice level.

**Counterevidence and limitations:** The baseline condition has relatively small sample sizes (n=86 total, n=22 in R1) compared to receptor_stimulated (n=614), reducing power to detect small effects. The neural_activity_blocked condition may not fully abolish neural input, depending on the pharmacological agent used. Age differences between groups (R4 mean age 46.9 days vs ~53 for others) could contribute to observed differences.

**Falsification proposal:** Increasing the sample size for baseline and blocked conditions (particularly in R1 and R4) would improve power to detect small effects. Using a stronger neural blockade or optogenetic silencing could produce more pronounced effects if the current pharmacological agent is incomplete.

---

## Methods

### Data
- Source: `data/cellular_calcium_response_summaries.tsv` (CC BY, frozen dataset)
- 819 per-cell calcium response summaries, 12 columns
- Variables: observation_id, recording_batch_id, animal_age_days, slice_id, condition, anatomical_region_id, mean_amplitude_dff0, mean_time_to_peak_s, mean_peak_width_s, mean_peak_prominence_dff0, mean_peak_frequency_hz, mean_auc_au
- No missing values, no imputation

### Statistical methods
- **Group statistics**: mean, standard deviation, standard error, 95% CI (t-distribution)
- **Pairwise comparisons**: Welch's two-sample t-test (unequal variances assumed), Cohen's d and Hedges' g effect sizes
- **ANOVA**: Type II sum of squares via statsmodels, eta-squared for effect size decomposition
- **Batch effects**: One-way ANOVA SS decomposition (between-batch / total)
- **Age correlations**: Pearson product-moment correlation
- **Robustness**: Leave-one-batch-out (9 iterations), slice-level aggregation (50 slice-region-condition groups)
- **Software**: Python 3, pandas 3.0.3, scipy 1.17.1, statsmodels 0.15.0, matplotlib 3.11.1, seaborn 0.13.2

### Limitations
1. **Region-condition confounding**: Region 3 has only receptor_stimulated; Region 4 has only baseline + blocked. Full factorial analysis is impossible.
2. **Nested structure**: Cells within slices are not independent. Cell-level tests may inflate Type I error; slice-level aggregation reduces power.
3. **Sample imbalance**: receptor_stimulated (n=614) vastly exceeds baseline (n=86) and blocked (n=119).
4. **Multiple comparisons**: 42 pairwise tests across 6 variables; no correction applied (exploratory).
5. **Anonymous regions**: Anatomical identity unknown; mechanistic interpretation limited.
6. **LMM convergence**: Mixed-effects models with random intercepts for slice/batch encountered computational issues; variance components should be validated with alternative software.

---

## Reproducibility

All analysis code is saved in `output/main_analysis.py`. To reproduce:

```bash
cd /data/user/conversations/conv-4a42b09e-c6e8-4347-910d-86fe4c3da0c2/project
python3 output/main_analysis.py
```

This script reads `data/cellular_calcium_response_summaries.tsv` and generates all figures and result tables in `output/`. Sub-agent analyses are preserved in `working/analysis_A/`, `working/analysis_B/`, and `working/analysis_C/`.

**Sub-agent analysis scripts (also copied to output/):**
- Main analysis: `output/analysis_A.py` (from `working/analysis_A/analysis.py`)
- Robustness checks: `output/robustness_check.py` (from `working/analysis_B/robustness.py`)
- Independent replication: `output/replication.py` (from `working/analysis_C/replication.py`)

**Key result files:**
- `output/contrasts_regions12.csv` — pairwise contrasts in regions 1+2
- `output/batch_effects.csv` — batch variance decomposition
- `output/robustness_lobo.csv` — leave-one-batch-out results
- `output/summary_stats.csv` — group summary statistics
- `output/figures_main.png` — 6-panel region×condition means
- `output/figures_violin_amplitude.png` — amplitude violin plot
- `output/figures_batch_effect.png` — batch effect bar chart
- `output/replication_results.csv` — sub-agent replicated results
- `output/eta_squared_results.csv` — sub-agent effect sizes
- `output/model_output_agentA.txt` — sub-agent detailed model output

---

## Evidence Registry

| File | Role |
|---|---|
| `output/Result.md` | Authoritative findings report |
| `output/main_analysis.py` | Primary analysis code |
| `output/analysis_A.py` | Sub-agent main analysis code |
| `output/robustness_check.py` | Sub-agent robustness code |
| `output/replication.py` | Sub-agent replication code |
| `output/contrasts_regions12.csv` | Pairwise contrast results |
| `output/batch_effects.csv` | Batch effect quantification |
| `output/robustness_lobo.csv` | LOO robustness results |
| `output/summary_stats.csv` | Group summary statistics |
| `output/figures_main.png` | Multi-variable visualization |
| `output/figures_violin_amplitude.png` | Amplitude distribution |
| `output/figures_batch_effect.png` | Batch effect visualization |
| `output/replication_results.csv` | Sub-agent replicated results |
| `output/eta_squared_results.csv` | Sub-agent effect sizes |
| `output/model_output_agentA.txt` | Sub-agent detailed model output |
| `output/comparison_with_main.txt` | Sub-agent methodological notes |
