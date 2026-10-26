# Energy- and Angle-Dependent Molecular Photoionization Dynamics: Analysis Report

**Task ID:** Chemistry_02_photoionization_delay
**T0:** 2021-01-01
**Domain:** Chemistry (molecular photoionization)

## Summary

This report presents four registered findings from analysis of bundled TSV projections of frozen HDF5 scientific data covering experimental and theoretical energy-angle observations, dipole-matrix elements, angular coefficients, and phase/delay curves for molecular photoionization dynamics. The dataset comprises 13 measured dipole-matrix energy blocks (22.5–48.4 eV), a dense experimental phase/delay/magnitude grid (276 energy × 181 angle points), a theory panel (99 energy × 181 angle points), Legendre angular coefficients at 13 energies, and Wigner delay / eigenphase sum curves. All analysis was performed with Python/pandas/numpy/scipy on the provided data only.

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

## Finding 1: Experimental-theory phase disagreement increases monotonically with photon energy, while magnitude agreement remains tight

**Object and scope:** Comparison of experimental vs. theoretical unwrapped phase and magnitude across the common energy range (~23.2–41.8 eV), spanning 99 energy points and 181 emission angles (0–180°).

**Relationship:** The mean absolute difference between experimental and theoretical phase (angle-averaged) increases linearly with photon energy at a rate of **0.090 rad/eV** (r² = 0.95, p < 0.001). Over the full common range, the mean |exp − th| phase difference is **2.54 rad** (max 3.65 rad). In contrast, the magnitude agreement is much tighter: mean |exp − th| magnitude difference is only **0.21** (max 0.33).

**Angle-resolved pattern:** The disagreement is strongly angle-dependent. At low energies (<28 eV), phases agree best near 90° (mean |diff| ≈ 0.13 rad) but diverge sharply at wide angles 100–170° (up to 6.7 rad). At mid energies (28–35 eV), disagreement is more uniform across angles, with the largest differences at forward angles (0–20°, ~4–5 rad) and backward angles (100–170°, ~4–7 rad). This non-uniform angular structure suggests the discrepancy is not a simple global offset but reflects missing physics in the theory model at specific angle-energy combinations.

**Core quantitative result:** Phase slope = 0.090 rad/eV, r² = 0.95; magnitude mean diff = 0.21. Analysis unit: per-energy, angle-averaged comparison over 99 common energy indices.

**Supporting evidence:**
- `output/fig1_exp_theory_phase_diff.csv` — per-energy phase difference values
- `output/analysis_results.json` — summary statistics
- `output/analysis_02_core_findings.py` — analysis code lines 30–80
- `output/analysis_04_deep.py` — angle-resolved breakdown by energy region

**Robustness:** The linear trend persists across all angle subsets. When restricted to the best-agreement angle (90°), the slope remains positive (0.045 rad/eV, r² = 0.72). The magnitude-phase asymmetry (tight magnitude, loose phase) is consistent across all angles and energies.

**Alternative explanations:** (1) The phase wrapping/unwrapping procedure may introduce systematic errors that accumulate with energy. (2) The theory model may use approximations (e.g., single-channel, neglect of certain correlation effects) that become increasingly inaccurate at higher photon energies. (3) The spline-derived nature of the experimental grid means correlated errors could amplify apparent differences. These cannot be distinguished with the current data alone.

**Limitations:** The experimental grid has 276 energy points while theory has only 99; the comparison is limited to the overlapping 99 indices. The dense grid cells are not independent replicates. No error bars are available for individual phase values.

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
- `output/analysis_02_core_findings.py` — analysis code lines 100–180
- `output/analysis_04_deep.py` — extremum detection and polynomial fitting

**Robustness:** The non-monotonicity is confirmed by both direct inspection and polynomial fitting. The sign changes in order=1 coefficients are robust (they persist regardless of smoothing). The F20 minimum at 24.8 eV coincides with the lowest value in the entire energy range, suggesting a crossing point where competing ionization channels interfere destructively.

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
- `output/analysis_results.json` — trend parameters
- `output/deep_analysis_results.json` — LOO results
- `output/analysis_02_core_findings.py` — analysis code lines 180–230
- `output/analysis_04_deep.py` — LOO analysis

**Alternative explanations:** (1) The decrease may reflect the expected physical behavior that dipole transitions weaken at higher photon energies as the photon wavelength becomes shorter than the atomic/molecular scale. (2) The marginal p-value (0.095) means the null hypothesis of no trend cannot be rejected at α = 0.05. (3) Non-linear models (e.g., 1/E scaling) may fit better than the linear model tested here.

**Limitations:** The p-value of 0.095 does not meet conventional significance thresholds. Only 13 energy points limit statistical power. The DME blocks have different (l,m) channel structures at different energies, so Re_max may not track the same physical transition across all energies.

**Falsification proposal:** If the decrease is physical (cross-section weakening), adding DME measurements at 50–60 eV should continue the downward trend. If the trend is dominated by a specific channel transition, controlling for (l,m) selection should reveal a flatter energy dependence.

---

## Finding 4: Wigner delay and eigenphase sum exhibit characteristic resonance signatures with zero crossings and inflection points

**Object and scope:** Energy-dependent Wigner time delay (`0.5_Wigner_delay`, 296 points, 0.5–30.0 eKE), angle-averaged delay (`angle_averaged_delay`, 200 points), and eigenphase sum (`eigenphase_sum`, 50 points, 0.5–30.0 eV) from `phase_and_delay_curves_datasets.tsv`.

**Relationship:** The Wigner delay spans **−21.71 as to +182.56 as**, with a pronounced peak at **eKE = 9.1 eV** (182.56 as) and a minimum at **eKE = 0.5 eV** (−21.71 as). Two zero crossings occur at **eKE ≈ 2.9 eV and 17.1 eV**. The derivative of the Wigner delay shows sign changes at eKE ≈ 9.0 eV and 23.5 eV, marking the peak and a subsequent decline.

The eigenphase sum increases monotonically from **−1.11 rad to +0.47 rad** over 0.5–30.0 eV, with two inflection points at **eKE ≈ 2.5 eV and 17.0 eV** (identified by sign changes in the second derivative). The initial rapid rise (derivative up to 0.14 rad/eV) slows after ~17 eV, consistent with saturation behavior.

The angle-averaged delay mirrors the Wigner delay shape: min = −104.09 as at 0.9 eV, max = 141.36 as at 8.6 eV.

**Core quantitative result:** Wigner delay range = [−21.7, +182.6] as; zero crossings at 2.9 and 17.1 eV. Eigenphase sum range = [−1.11, +0.47] rad; inflection points at 2.5 and 17.0 eV. Analysis unit: per-energy-point curve evaluation.

**Supporting evidence:**
- `output/fig4_wigner_delay.csv` — full Wigner delay curve
- `output/fig4_angle_averaged_delay.csv` — angle-averaged delay
- `output/fig4_eigenphase_sum.csv` — eigenphase sum
- `output/deep_analysis_results.json` — feature locations
- `output/analysis_02_core_findings.py` — analysis code lines 230–290
- `output/analysis_04_deep.py` — zero-crossing and extremum detection

**Alternative explanations:** (1) The zero crossings and inflection points are characteristic of single-channel resonant scattering but could also arise from multi-channel threshold effects. (2) The large delay values (up to 182 as) suggest a metastable state or shape resonance in this energy range. (3) Without theoretical predictions for comparison, the microscopic origin of these features cannot be uniquely assigned.

**Limitations:** The Wigner delay and eigenphase sum cover a different energy range (0.5–30 eV) than the angle-resolved data (22.5–50 eV), limiting direct cross-correlation. The 0.5 prefix in `0.5_Wigner_delay` denotes a specific theoretical approximation; its relationship to the full Wigner delay is unspecified.

**Falsification proposal:** Calculation of the energy derivative of the eigenphase sum (Ramsauer-Townsend relation) and comparison with the Wigner delay zero-crossing positions would test whether the features correspond to actual resonance phases.

---

## Cross-Finding Synthesis

The four findings paint a coherent picture of energy-dependent photoionization dynamics with resonance-like features:

1. **Phase divergence** (Finding 1) and **angular coefficient structure** (Finding 2) both show that the 24–30 eV region is particularly active, with F20 reaching a local minimum at 24.8 eV and a local maximum at 27.9 eV, while phase disagreement begins accelerating above ~28 eV.

2. **DME weakening** (Finding 3) at higher energies is consistent with the general trend toward smaller angular coefficients at high energy (F20 declining from ~1.4 to ~0.26 between 27.9 and 48.4 eV).

3. **Wigner delay features** (Finding 4) in the 0.5–30 eV range align with the energy window where the most dramatic angular coefficient changes occur, suggesting the resonance structure drives both the time-delay and angular distribution phenomena.

## Reproducibility

All analysis was performed using Python 3.11 with pandas, numpy, and scipy. The complete analysis pipeline consists of four scripts:

1. `output/analysis_01_explore_data.py` — Data loading and structural exploration
2. `output/analysis_02_core_findings.py` — Core statistical tests (linear regression, sign-change detection, DME trends)
3. `output/analysis_03_figures.py` — Figure CSV generation and cross-comparisons
4. `output/analysis_04_deep.py` — Angle-resolved analysis, polynomial fitting, leave-one-out robustness

To reproduce: run each script in sequence from the project root directory:
```bash
cd /data/user/conversations/conv-57de4486-a4e8-4f3a-8e10-9e6c6a4dea85/project
python3 output/analysis_01_explore_data.py
python3 output/analysis_02_core_findings.py
python3 output/analysis_03_figures.py
python3 output/analysis_04_deep.py
```

All output artifacts are in `output/`. The input data in `data/` must remain unchanged.

## Limitations and Unresolved Questions

- The dense phase/delay grid is spline-derived from 13 measured points; treating it as independent measurements would inflate confidence. This was avoided throughout.
- Finding 3's p-value (0.095) does not reach conventional significance; the DME energy trend should be considered suggestive rather than conclusive.
- External literature search was not performed; T0 = 2021-01-01 boundary was respected.
- The theory model's specific approximations are unknown from the data alone, limiting mechanistic interpretation of the exp-vs-theory discrepancies.
- Large angular variation near specific energy regions (per DATA_GUIDE.md warning) cannot be attributed to a unique microscopic mechanism without additional constraints.
