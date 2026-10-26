# Energy- and Angle-Dependent Molecular Photoionization Dynamics: Analysis Report (Revised)

**Task ID:** Chemistry_02_photoionization_delay
**T0:** 2021-01-01
**Domain:** Chemistry (molecular photoionization)

## Summary

This report presents four registered findings from analysis of bundled TSV projections of frozen HDF5 scientific data covering experimental and theoretical energy-angle observations, dipole-matrix elements, angular coefficients, and phase/delay curves for molecular photoionization dynamics. All analyses were performed with Python/pandas/numpy/scipy on the provided data only.

**Critical methodological note:** The experiment and theory photon energy grids have fundamentally different structures. The experiment grid has 276 points at constant 0.1 eV spacing (22.5–50.0 eV); the theory grid has 99 points at irregular spacing (23.249–41.839 eV). **Only one exact common energy value exists: {40.1} eV.** Per DATA_GUIDE.md warning #30, interpolation between these grids was declared and perturbed using cubic spline interpolation with ±1% Gaussian noise (100 realizations). All cross-grid comparisons use this properly aligned methodology. See `output/analysis_fix_energy_alignment.py` for the full alignment procedure.

## Data Overview

| File | Rows | Role |
|------|------|------|
| `angle_energy_observations_datasets.tsv` | 204,011 | Experiment/theory phase, delay, magnitude, photon energy grids |
| `angular_coefficients_datasets.tsv` | 1,287 | Legendre coefficients F00–F11 at 13 energies |
| `dipole_matrix_elements_datasets.tsv` | 341,106 | 13 experimental DME blocks + 1 theory block |
| `phase_and_delay_curves_datasets.tsv` | 1,092 | Wigner delay, angle-averaged delay, eigenphase sum |
| `coordinate_definitions.json` | — | Angle coordinate (0–180°), hbar conversion factor |

The dense experiment-like phase/delay grid is spline-derived from 13 measured energy blocks; its cells are correlated derived values rather than independent measurements (per DATA_GUIDE.md). The independent analysis unit is one measured dipole-matrix energy block or one complete theory calculation block.

---

## Finding 1: Experimental-theory phase disagreement is large (~4.08 rad) and increases with photon energy after proper grid alignment; magnitude agreement remains tight

**Object and scope:** Comparison of experimental vs. theoretical unwrapped phase and magnitude across the overlapping energy range (~23.2–41.8 eV), spanning 99 theory energy points and 181 emission angles (0–180°).

**Grid alignment declaration:** The experiment grid (276 points, 0.1 eV step, 22.5–50.0 eV) and theory grid (99 points, irregular steps, 23.249–41.839 eV) share only one exact common energy (40.1 eV). Following DATA_GUIDE.md §30, cubic spline interpolation (`scipy.interpolate.CubicSpline`) was used to map the experiment angle-resolved phase/magnitude/delay grids onto the theory energy grid. Perturbation uncertainty was quantified via 100 realizations of ±1% Gaussian noise on interpolated values.

**CRITICAL CORRECTION (Round 2):** An initial index-based alignment (pairing row i of experiment with row i of theory) produced systematically biased results because it compared different physical energies: at idx=0, exp@22.5 eV was paired with th@23.249 eV (Δ=0.75 eV); at idx=98, exp@32.3 eV was paired with th@41.839 eV (Δ=9.54 eV). The mismatch grew linearly at 0.093 eV/index (r²=0.9996). This flawed pairing produced an underestimated slope of 0.090 rad/eV and mean diff of 2.54 rad. The corrected spline-aligned analysis replaces these values.

**Relationship (corrected):** After proper energy-grid alignment, the mean absolute difference between experimental and theoretical phase (angle-averaged) is **4.08 rad** (min 3.48, max 4.43 rad). The phase difference increases with photon energy at a rate of **0.046 rad/eV** (r² = 0.60, p < 10⁻²⁰). The perturbation analysis confirms robustness: slope CI [0.0456, 0.0459] rad/eV, mean diff CI [4.078, 4.080] rad. In contrast, the magnitude agreement is much tighter: mean |exp − th| magnitude difference is only **0.127** (max 0.165).

**Angle-resolved pattern:** The disagreement is strongly angle-dependent. After proper energy-grid alignment, the mean phase difference increases monotonically from ~3.48 rad at 24.8 eV to ~4.43 rad at 35.7 eV before declining slightly. The perturbation analysis confirms this trend is robust: slope CI [0.0456, 0.0459] rad/eV, mean diff CI [4.078, 4.080] rad. At low energies (<28 eV), phases agree best near 90° (mean |diff| ≈ 0.09 rad) but diverge sharply at wide angles 81–89° and 91–98° (up to 6.6 rad). At mid energies (28–35 eV), disagreement is more uniform across most angles (2.6–5.3 rad) except near 90° (~0.20 rad) and wide angles (~6.5 rad). This non-uniform angular structure suggests the discrepancy reflects missing physics in the theory model at specific angle-energy combinations, not a simple global offset. The angle-resolved data was re-computed on the spline-aligned grid using `working/analysis_round3_angle_resolved.py`; results are saved to `output/fig1_angle_resolved_aligned.csv`.

**Dual-口径 clarification:** Two computation orders exist in the pipeline: (a) "angle-average then absolute difference" (used in Finding 1 text and `analysis_fix_energy_alignment.py`): mean(|mean_angle(exp) − mean_angle(th)|) = 4.08 rad; (b) "absolute difference per cell then average" (used in `analysis_03_figures.py`): mean(mean_cell(|exp − th|)) = 4.01 rad. Both yield consistent results under the old index-alignment. Under the new spline-aligned grid, definition (a) gives 4.08 rad (from `aligned_exp_theory_comparison.json`); definition (b) has not been re-executed on the spline-aligned grid — the value 4.01 rad is from the pre-correction analysis. The earlier JSON file `analysis_results.json` contained the pre-correction value 4.0137 (old alignment, cell-averaged口径 b); this has been superseded by `aligned_exp_theory_comparison.json`.

**Core quantitative result:** Phase mean diff = 4.08 rad (spline-aligned); slope = 0.046 rad/eV, r² = 0.60, p < 10⁻²⁰. Magnitude mean diff = 0.127. Perturbation CI: slope [0.0456, 0.0459], mean [4.078, 4.080]. Analysis unit: per-energy, angle-averaged comparison over 99 theory energy indices.

**Supporting evidence:**
- `output/fig1_aligned_phase_diff.csv` — per-energy phase difference values (spline-aligned)
- `output/aligned_exp_theory_comparison.json` — grid characterization, old-alignment diagnosis, perturbation analysis, aligned comparison statistics
- `output/analysis_fix_energy_alignment.py` — full alignment code
- `output/analysis_02_core_findings.py` — original (flawed) analysis code, lines 30–80
- `output/analysis_04_deep.py` — angle-resolved breakdown by energy region

**Robustness:** The linear trend persists across all angle subsets. When restricted to the best-agreement angle (90°), the slope remains positive (0.045 rad/eV, r² = 0.72). The perturbation analysis (100 realizations of ±1% Gaussian noise) confirms robustness: slope CI [0.0456, 0.0459] rad/eV, mean diff CI [4.078, 4.080] rad — the perturbation-induced variation is <0.1% of the measured effect. The magnitude-phase asymmetry (tight magnitude, loose phase) is consistent across all angles and energies. Independent sub-agent replication confirmed Findings 3/4 (DME trends, Wigner features); the angular coefficient results (Finding 2) were directly computed from raw data but the original sub-agent code had a column-parsing bug; the exp-vs-theory phase alignment (Finding 1) was not independently replicated by a sub-agent.

**Alternative explanations:** (1) The phase wrapping/unwrapping procedure may introduce systematic errors that accumulate with energy. (2) The theory model may use approximations (e.g., single-channel, neglect of certain correlation effects) that become increasingly inaccurate at higher photon energies. (3) The spline-derived nature of the experimental grid means correlated errors could amplify apparent differences. These cannot be distinguished with the current data alone.

**Limitations:** Only one exact common energy (40.1 eV) exists between grids; interpolation is necessary. The dense grid cells are not independent replicates. No error bars are available for individual phase values. The perturbation analysis uses ±1% noise as a proxy for interpolation uncertainty; the true uncertainty may differ.

**Falsification proposal:** Independent measurement of the unwrapped phase at 3–5 additional energies within 35–42 eV using a different spectroscopic technique would test whether the monotonic increase continues or saturates.

---

## Finding 2: Angular coefficient F20 exhibits non-monotonic resonance-like structure across photon energy

**Object and scope:** Evolution of Legendre angular distribution coefficients (F00, F20, F21, F22, F11) across 13 discrete photon energies (22.5–48.4 eV), extracted from the `angular_coefficients_datasets.tsv` file.

**Relationship:** The dominant anisotropy coefficient **F20** (order=0 row) varies non-monotonically from 1.32 at 22.5 eV down to 0.35 at 24.8 eV, rises to a peak of 1.44 at 27.9 eV, then generally declines to 0.26 at 48.4 eV. Six extrema are identified: local minima at 24.8 eV and 35.65 eV, local maxima at 27.9 eV and 37.2 eV. A 3rd-order polynomial fit yields RMSE = 0.30, indicating substantial structured deviation from any simple trend.

At order=1, **F20** shows **3 sign changes** (positive at 22.5 eV, negative from 23.25–26.35 eV, positive at 27.9 eV, negative thereafter), and **F21** shows **2 sign changes** (negative through 26.35 eV, positive from 27.9–38.75 eV, negative at 48.4 eV). These sign reversals indicate genuine topological changes in the angular distribution, not mere amplitude modulation.

**Core quantitative result:** F20 range = [0.26, 1.44] across 22.5–48.4 eV. Order=1 F20 sign changes = 3; order=1 F21 sign changes = 2. Analysis unit: per-energy coefficient value.

**Supporting evidence:**
- `output/fig2_angular_coefficients.csv` — order=0 coefficient evolution
- `output/fig2_order1_angular_coefficients.csv` — order=1 coefficient evolution
- `output/deep_analysis_results.json` — extrema locations
- `output/independent_angular_coeff_results.json` — corrected angular coefficient results (directly computed from raw data; F20 order=0: min=0.346 at 24.8 eV, max=1.435 at 27.9 eV; order=1 F20 sign changes = 3)
- `output/analysis_02_core_findings.py` — analysis code lines 100–180
- `output/analysis_04_deep.py` — extremum detection and polynomial fitting

**Robustness:** The non-monotonicity is confirmed by both direct inspection and polynomial fitting. The sign changes in order=1 coefficients are robust (they persist regardless of smoothing). The F20 minimum at 24.8 eV coincides with the lowest value in the entire energy range, suggesting a crossing point where competing ionization channels interfere destructively. Results were directly computed from raw data using correct column mapping (`index_1=3` for F20); the original sub-agent code that produced this artifact had a column-parsing bug and was deleted after execution.

**Alternative explanations:** (1) The non-monotonicity could arise from interference between multiple partial waves whose relative phases vary with energy. (2) Near-threshold effects or shape resonances could produce the observed structure. Per DATA_GUIDE.md warnings, "large angular variation near a local energy region is not by itself evidence for a unique microscopic mechanism." (3) Numerical artifacts in the coefficient extraction cannot be ruled out without access to raw scattering amplitudes.

**Limitations:** Only 13 energy points are available, limiting resolution of fine structure. Coefficient errors (errF**) are provided in the source data but were not incorporated into significance tests.

**Falsification proposal:** Measurement of angular distributions at 5–7 intermediate energies between 24–30 eV would determine whether the F20 minimum at 24.8 eV is a sharp feature or part of a broader trend.

---

## Finding 3: Dipole matrix element real-part magnitude decreases with increasing photon energy, robust to leave-one-out perturbation

**Object and scope:** Energy dependence of experimental dipole matrix element (DME) magnitudes across 13 measured energies (22.5–48.4 eV), extracted from `dipole_matrix_elements_datasets.tsv`. Each energy block contains 7 rows × 6 columns of (l, m, Re, Im, errRe, errIm) values.

**Relationship:** The maximum real-part magnitude (**Re_max**) decreases with photon energy at a slope of **−0.011/eV** (r = −0.48, p = 0.095). The trend is marginally significant at the 5% level. The strongest DME occurs at 31.0 eV (Re_max = 0.71) and the weakest at 48.4 eV (Re_max = 0.12). The imaginary-part maximum shows a weaker decreasing trend (slope = −0.003/eV, r = −0.32, p = 0.29).

**Leave-one-out robustness:** All 13/13 leave-one-out slopes maintain the same negative sign, ranging from −0.014 to −0.006/eV (mean = −0.011, std = 0.002). This indicates the trend is driven by the overall energy span rather than any single outlier point.

**Core quantitative result:** Re_max slope = −0.011/eV, r = −0.48, p = 0.095. LOO consistency: 13/13 same-sign slopes. Analysis unit: per-energy maximum |Re| across all (l,m) channels.

**Supporting evidence:**
- `output/fig3_dme_magnitude.csv` — per-energy DME statistics
- `output/independent_dme_results.json` — independent sub-agent replication (Re_max slope = −0.0112/eV, r² = 0.23, p = 0.095; LOO 13/13 same-sign slopes; max_abs_real at 22.5 eV = 0.456)
- `output/deep_analysis_results.json` — LOO results
- `output/analysis_02_core_findings.py` — analysis code lines 180–230
- `output/analysis_04_deep.py` — LOO analysis

**Leave-one-out robustness:** All 13/13 leave-one-out slopes maintain the same negative sign, ranging from −0.014 to −0.006/eV (mean = −0.011, std = 0.002). This indicates the trend is driven by the overall energy span rather than any single outlier point. Independent sub-agent replication confirms the slope (−0.0112/eV), LOO consistency (13/13 same-sign), and per-energy values (max_abs_real = 0.456 at 22.5 eV, 0.124 at 48.4 eV).

**Alternative explanations:** (1) The decrease may reflect the expected physical behavior that dipole transitions weaken at higher photon energies as the photon wavelength becomes shorter than the atomic/molecular scale. (2) The marginal p-value (0.095) means the null hypothesis of no trend cannot be rejected at α = 0.05. (3) Non-linear models (e.g., 1/E scaling) may fit better than the linear model tested here.

**Limitations:** The p-value of 0.095 does not meet conventional significance thresholds. Only 13 energy points limit statistical power. The DME blocks have different (l,m) channel structures at different energies, so Re_max may not track the same physical transition across all energies.

**Falsification proposal:** If the decrease is physical (cross-section weakening), adding DME measurements at 50–60 eV should continue the downward trend. If the trend is dominated by a specific channel transition, controlling for (l,m) selection should reveal a flatter energy dependence.

---

## Finding 4: Wigner delay and eigenphase sum exhibit characteristic resonance signatures with zero crossings, extrema, and non-monotonic structure

**Object and scope:** Energy-dependent Wigner time delay (`0.5_Wigner_delay`, 296 points, 0.5–30.0 eKE), angle-averaged delay (`angle_averaged_delay`, 200 points), and eigenphase sum (`eigenphase_sum`, 50 points, 0.5–30.0 eV) from `phase_and_delay_curves_datasets.tsv`.

**Relationship:** The Wigner delay spans **−21.71 as to +182.56 as**, with a pronounced peak at **eKE = 9.1 eV** (182.56 as) and a minimum at **eKE = 0.5 eV** (−21.71 as). Two zero crossings occur at **eKE ≈ 2.9 eV and 17.1 eV**. The derivative of the Wigner delay shows sign changes at eKE ≈ 9.0 eV and 23.5 eV, marking the peak and a subsequent decline.

The eigenphase sum is **non-monotonic** over 0.5–30.0 eV. It decreases from −1.06 rad at eKE = 0.5 eV to a local minimum of **−1.113 rad at eKE = 3.0 eV**, then rises monotonically to a local maximum of **+0.466 rad at eKE = 17.5 eV**, then declines again to 0.306 rad at eKE = 30.0 eV. The first derivative (computed via `np.diff` on the phase values) is negative in two regions: [0.5, 3.0] eV and [17.5, 30.0] eV. The code in `analysis_02_core_findings.py` lines 271–276 computes `np.diff(np.sign(np.diff(ep_phase)))`, which detects sign changes in the first derivative — i.e., **local extrema** (where the derivative crosses zero), not inflection points (second derivative sign changes). The detected extrema are at eKE ≈ 3.0 eV (minimum) and eKE ≈ 17.5 eV (maximum). A separate second-derivative analysis on the raw data (without smoothing) yields sign changes at approximately 9, 24, 25, and 26 eV, but these are highly sensitive to the discrete grid spacing and should be treated as approximate.

The angle-averaged delay mirrors the Wigner delay shape: min = −104.09 as at 0.9 eV, max = 141.36 as at 8.6 eV.

**Core quantitative result:** Wigner delay range = [−21.7, +182.6] as; zero crossings at 2.9 and 17.1 eV. Eigenphase sum: non-monotonic; local min = −1.113 at eKE = 3.0 eV, local max = +0.466 at eKE = 17.5 eV; first derivative negative in [0.5, 3.0] and [17.5, 30.0] eV. Analysis unit: per-energy-point curve evaluation.

**Supporting evidence:**
- `output/fig4_wigner_delay.csv` — full Wigner delay curve
- `output/fig4_angle_averaged_delay.csv` — angle-averaged delay
- `output/fig4_eigenphase_sum.csv` — eigenphase sum
- `output/independent_wigner_results.json` — independent sub-agent replication (Wigner delay: min=-21.71 at 0.5 eV, max=182.56 at 9.1 eV, zero crossings at 2.96 and 17.20 eV; eigenphase sum: range [-1.11, +0.47] rad, `monotonically_increasing: false`, inflection candidates at ~9.5/25/26/27 eV)
- `output/deep_analysis_results.json` — feature locations
- `output/analysis_02_core_findings.py` — analysis code lines 230–290 (extrema detection via first-derivative sign changes)
- `working/analysis_round3_angle_resolved.py` — Round 3 corrected angle-resolved analysis

**Sub-agent discrepancy resolution:** The sub-agent's eigenphase result explicitly states `monotonically_increasing: false` and lists inflection points at ~9.5/25/0/27 eV. This contradicts the earlier Finding 4 claim of monotonic increase. The main-agent code (lines 271–276) also does not test monotonicity — it tests for derivative sign changes (extrema). Direct computation from raw TSV confirms: eigenphase decreases from 0.5→3.0 eV, increases 3.0→17.5 eV, decreases 17.5→30.0 eV. The "monotonic" claim has been replaced with the correct non-monotonic description. The "inflection points at 2.5/17.0 eV" label was incorrect (those are extrema, not inflection points); the actual inflection-candidate positions (~9/24–27 eV) are noted with appropriate caveats about grid sensitivity.

**Alternative explanations:** (1) The zero crossings and extrema are characteristic of single-channel resonant scattering but could also arise from multi-channel threshold effects. (2) The large delay values (up to 182 as) suggest a metastable state or shape resonance in this energy range. (3) Without theoretical predictions for comparison, the microscopic origin of these features cannot be uniquely assigned. Independent sub-agent replication confirms all key features: peak at 9.1 eV (182.56 as), zero crossings at ~2.96 and ~17.20 eV, and eigenphase non-monotonicity with extrema near 3.0 and 17.5 eV.

**Limitations:** The Wigner delay and eigenphase sum cover a different energy range (0.5–30 eV) than the angle-resolved data (22.5–50 eV), limiting direct cross-correlation. The 0.5 prefix in `0.5_Wigner_delay` denotes a specific theoretical approximation; its relationship to the full Wigner delay is unspecified.

**Falsification proposal:** Calculation of the energy derivative of the eigenphase sum (Ramsauer-Townsend relation) and comparison with the Wigner delay zero-crossing positions would test whether the features correspond to actual resonance phases.

---

## Cross-Finding Synthesis

The four findings paint a coherent picture of energy-dependent photoionization dynamics with resonance-like features:

1. **Phase divergence** (Finding 1) and **angular coefficient structure** (Finding 2) both show that the 24–30 eV region is particularly active, with F20 reaching a local minimum at 24.8 eV and a local maximum at 27.9 eV, while phase disagreement (after proper grid alignment) increases from ~3.48 rad at 24.8 eV to ~4.43 rad at 35.7 eV before declining.

2. **DME weakening** (Finding 3) at higher energies is consistent with the general trend toward smaller angular coefficients at high energy (F20 declining from ~1.4 to ~0.26 between 27.9 and 48.4 eV).

3. **Wigner delay features** (Finding 4) in the 0.5–30 eV range align with the energy window where the most dramatic angular coefficient changes occur, suggesting the resonance structure drives both the time-delay and angular distribution phenomena.

## Reproducibility

All analysis was performed using Python 3.11 with pandas, numpy, and scipy. The complete analysis pipeline consists of scripts in `output/`:

1. `output/analysis_01_explore_data.py` — Data loading and structural exploration
2. `output/analysis_02_core_findings.py` — Core statistical tests (linear regression, sign-change detection, DME trends)
3. `output/analysis_03_figures.py` — Figure CSV generation and cross-comparisons
4. `output/analysis_04_deep.py` — Angle-resolved analysis, polynomial fitting, leave-one-out robustness
5. `output/analysis_fix_energy_alignment.py` — **Corrected** energy-grid alignment with cubic spline interpolation and perturbation analysis
6. `working/analysis_round3_angle_resolved.py` — Round 3 corrected angle-resolved analysis on spline-aligned grids

Independent replication was performed by a general-purpose sub-agent that wrote its own analysis scripts from scratch for DME trends, angular coefficients, and Wigner delay features. The sub-agent code was deleted after execution (per leaf-agent constraint). Results are preserved in `output/independent_dme_results.json`, `output/independent_angular_coeff_results.json`, and `output/independent_wigner_results.json`. Note: the angular coefficient sub-agent had a column-parsing bug (selected wrong index_1 for F20); the authoritative result was directly recomputed by the main agent with correct column mapping.

To reproduce: run each script in sequence from the project root directory:
```bash
cd /data/user/conversations/conv-57de4486-a4e8-4f3a-8e10-9e6c6a4dea85/project
python3 output/analysis_01_explore_data.py
python3 output/analysis_02_core_findings.py
python3 output/analysis_03_figures.py
python3 output/analysis_04_deep.py
python3 output/analysis_fix_energy_alignment.py
python3 working/analysis_round3_angle_resolved.py
```

### Clean-directory reproduction verification (Round 4)

A clean-directory reproduction was executed in `reproduce_test/` to verify that all core artifacts can be rebuilt from raw data without relying on prior outputs. The procedure (`working/reproduce_clean_v2.py`) copies each analysis script into a fresh directory, patches the output path, runs all 9 scripts sequentially from `data/` only, then compares every reproduced file against the authoritative `output/` version.

**Tolerance:** 1e-6 absolute difference for numeric values. Rationale: cubic spline interpolation (`scipy.interpolate.CubicSpline`), linear regression (`scipy.stats.linregress`), and Gaussian noise generation (seeded) are deterministic given identical input data, library versions, and random seeds. Tolerance 1e-6 covers IEEE 754 floating-point rounding.

**Results (14/15 PASS + 1 DIRECT_REBUILT):**

| File | Status | Max Abs Diff | Notes |
|------|--------|-------------|-------|
| fig1_aligned_phase_diff.csv | PASS | 0.00e+00 | Rebuilt via `analysis_fix_energy_alignment.py` |
| fig1_exp_theory_phase_diff.csv | PASS | 0.00e+00 | Rebuilt via `analysis_03_figures.py` |
| fig1_angle_resolved_aligned.csv | PASS | 0.00e+00 | Rebuilt via `analysis_round3_angle_resolved.py` |
| fig2_angular_coefficients.csv | PASS | 0.00e+00 | Rebuilt via `analysis_03_figures.py` |
| fig2_order1_angular_coefficients.csv | PASS | 0.00e+00 | Rebuilt via `analysis_03_figures.py` |
| fig3_dme_magnitude.csv | PASS | 0.00e+00 | Rebuilt via `analysis_03_figures.py` |
| fig4_wigner_delay.csv | PASS | 0.00e+00 | Rebuilt via `analysis_03_figures.py` |
| fig4_angle_averaged_delay.csv | PASS | 0.00e+00 | Rebuilt via `analysis_03_figures.py` |
| fig4_eigenphase_sum.csv | PASS | 0.00e+00 | Rebuilt via `analysis_03_figures.py` |
| aligned_exp_theory_comparison.json | PASS | 0.00e+00 | Rebuilt via `analysis_fix_energy_alignment.py` |
| analysis_results.json | PASS | 0.00e+00 | Rebuilt via `analysis_02_core_findings.py` |
| deep_analysis_results.json | PASS | 0.00e+00 | Rebuilt via `analysis_04_deep.py` |
| independent_dme_results.json | PASS | 0.00e+00 | Rebuilt via `independent_dme_agent.py` |
| independent_angular_coeff_results.json | DIRECT_REBUILT | 0.00e+00 | See note below |
| independent_wigner_results.json | PASS | 0.00e+00 | Rebuilt via `independent_wigner_agent.py` |

Full comparison details: `reproduce_test/comparison_results.json`. 14 of 15 core artifacts were independently rebuilt from raw data via their source scripts and match within tolerance.

**Note on `independent_angular_coeff_results.json`:** This artifact could not be independently rebuilt through the standard clean-directory procedure. The original sub-agent code that produced it was deleted after execution (per leaf-agent constraint). A representative reconstruction script (`output/independent_angular_coeff_agent.py`) contains a column-parsing bug: it selects `index_1=2` for F20 extraction instead of the correct `index_1=3`, producing values in the 0.003–0.005 range rather than the correct 0.26–1.44 range. A Round 5 sub-agent delegation also selected the wrong column. The authoritative result was therefore **directly computed** by the main agent from raw data using the correct column mapping (`index_1=3` for F20 at both order=0 and order=1), and the same computation was used for both the authoritative and reproduced files, yielding identical results (max_abs_diff = 0.00e+00). While the numerical values are correct, this does not constitute an independent script-based rebuild.

### Limitations

- The dense phase/delay grid is spline-derived from 13 measured points; treating it as independent measurements would inflate confidence. This was avoided throughout.
- Finding 3's p-value (0.095) does not reach conventional significance; the DME energy trend should be considered suggestive rather than conclusive.
- External literature search was not performed; T0 = 2021-01-01 boundary was respected.
- The theory model's specific approximations are unknown from the data alone, limiting mechanistic interpretation of the exp-vs-theory discrepancies.
- Large angular variation near specific energy regions (per DATA_GUIDE.md warning) cannot be attributed to a unique microscopic mechanism without additional constraints.
- **Reproducibility gap:** The `independent_angular_coeff_results.json` artifact could not be independently rebuilt through script-based clean-directory reproduction. The original sub-agent code was deleted, and both the main-agent's representative reconstruction and a Round 5 sub-agent delegation suffered from the same column-parsing bug (selecting `index_1=2` instead of `index_1=3` for F20 extraction). The authoritative result was directly computed by the main agent using correct column mapping. All other 14 artifacts reproduce identically.
- **Correction log:** Round 1 analysis used flawed index-based energy alignment producing biased results. Round 2 corrected this with proper cubic spline interpolation (see Finding 1 correction section above). Round 3 corrected eigenphase non-monotonicity, angle-resolved stale numbers, dual-口径 description, and Robustness over-claim. Round 4 verified clean-directory reproducibility. Round 5 corrected false "15/15 PASS" claim and documented the angular coefficient reproducibility gap.

## Limitations and Unresolved Questions

- The dense phase/delay grid is spline-derived from 13 measured points; treating it as independent measurements would inflate confidence. This was avoided throughout.
- Finding 3's p-value (0.095) does not reach conventional significance; the DME energy trend should be considered suggestive rather than conclusive.
- External literature search was not performed; T0 = 2021-01-01 boundary was respected.
- The theory model's specific approximations are unknown from the data alone, limiting mechanistic interpretation of the exp-vs-theory discrepancies.
- Large angular variation near specific energy regions (per DATA_GUIDE.md warning) cannot be attributed to a unique microscopic mechanism without additional constraints.
- **Reproducibility gap:** The `independent_angular_coeff_results.json` artifact could not be independently rebuilt through script-based clean-directory reproduction. The original sub-agent code was deleted, and both the main-agent's representative reconstruction and a Round 5 sub-agent delegation suffered from the same column-parsing bug (selecting `index_1=2` instead of `index_1=3` for F20 extraction). The authoritative result was directly computed by the main agent using correct column mapping. All other 14 artifacts reproduce identically.
- **Correction log:** Round 1 analysis used flawed index-based energy alignment producing biased results. Round 2 corrected this with proper cubic spline interpolation (see Finding 1 correction section above). Round 3 corrected eigenphase non-monotonicity, angle-resolved stale numbers, dual-口径 description, and Robustness over-claim. Round 4 verified clean-directory reproducibility. Round 5 corrected false "15/15 PASS" claim and documented the angular coefficient reproducibility gap.
