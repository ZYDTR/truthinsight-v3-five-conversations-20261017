# Time-Resolved Gravity Residuals and Candidate Spectral Structure — Scientific Report

**Task ID:** Astronomy_02_gravity_spectral_structure  
**T0:** 2022-01-01  
**Analysis date:** 2026-10-16  

## Executive Summary

This report investigates whether reproducible temporal or spectral structure is supported in the data from an anonymous gravitating system. The dataset comprises 22 complete time-resolved passes (1,698 time samples total), a ranked grid of 250 candidate spectral parameter combinations, a mode-frequency grid with 52 entries, and a uniform-velocity alternative comparison. Analysis was conducted using per-pass statistics, cross-model correlation, variance decomposition, information-criterion landscape analysis, and robustness checks (leave-one-pass-out, first-half/second-half splits).

The data support two principal findings: (1) a well-localized spectral structure peak at ~1010–1060 μHz with narrow delta IC separation from alternatives, and (2) residual traces dominated by within-pass variance with negligible between-pass structure, indicating that temporal variation is pass-internal rather than systematic across passes. Model B exhibits a distinct autocorrelation sign pattern compared to Models A and C, suggesting model-dependent structural differences.

---

## Data Inventory

| File | Rows | Role |
|------|------|------|
| `data/pass_residual_traces.tsv` | 1,698 | 22 passes × ~77 time samples; 3 residual models (A, B, C) in mm/s |
| `data/candidate_spectrum_comparison.tsv` | 507 | Frequency amplitude scan (304 rows) + minimum velocity scan (203 rows) |
| `data/ranked_full_parameter_grid.tsv` | 250 | Ranked candidates with delta information criterion |
| `data/mode_frequency_grid.tsv` | 52 | Angular degree l=2–8, radial order n=0–7 |
| `data/uniform_alternative_comparison.tsv` | 24 | Uniform velocity alternatives from 0.001 to 500 cm/s |

Independent analysis unit: one complete time-resolved pass or one complete candidate spectral parameter combination (DATA_GUIDE warning: adjacent time samples are not independent replicates).

Analysis source code: `output/analysis.py`, `output/generate_artifacts.py`.  
Machine-readable results: `output/result_artifacts.json`.

---

## Methods

### Temporal analysis
Per-pass descriptive statistics (mean, std, skewness, kurtosis), lag-1 autocorrelation, detrended FFT for periodicity detection, and variance decomposition (between-pass vs. within-pass).

### Spectral analysis
Information-criterion landscape mapping across the candidate parameter grid, ranking-based gap analysis, and comparison against the uniform-velocity alternative.

### Cross-model agreement
Pearson correlation between each pair of residual models within each pass, and mean absolute difference between models.

### Robustness checks
Leave-one-pass-out consistency (recomputing summary statistics excluding each pass), first-half vs. second-half mean/std comparison within each pass, and variance decomposition sensitivity.

All analysis was executed with Python 3 using pandas and numpy. See `output/analysis.py` for the complete executable pipeline.

---

## Finding 1: A Narrow Spectral Peak at ~1010–1060 μHz Is Strongly Supported by the Information Criterion Landscape

**Object and scope:** The full candidate spectral parameter grid (250 ranked combinations, 507 raw evaluations across two scan families), evaluated on the complete set of 22 passes.

**Relationship and direction:** The information criterion (IC) landscape shows a sharply localized minimum near peak frequency = 1010 μHz with width = 275 μHz and max velocity = 30 cm/s, min velocity = 0.05 cm/s. This configuration achieves the global minimum IC of 43.9. The next-best candidate (rank 2) has IC = 45.9 (delta_IC = 2.0), differing in both peak frequency (1060 vs. 1010 μHz) and max velocity (20 vs. 30 cm/s). Only 4 of 250 candidates fall within delta_IC ≤ 10 of the best, and only 10 within delta_IC ≤ 20.

**Core quantitative result:** 
- Rank 1: v_max=30 cm/s, v_min=0.05 cm/s, f_peak=1010 μHz, width=275 μHz, IC=43.9
- Rank 2: v_max=20 cm/s, v_min=0.05 cm/s, f_peak=1060 μHz, width=300 μHz, delta_IC=2.0
- Rank 3: delta_IC=5.7; Rank 4: delta_IC=9.4
- Candidates within delta_IC ≤ 10: 4 out of 250 (1.6%)

**Supporting evidence:**
- `data/ranked_full_parameter_grid.tsv` — full ranking with delta IC values
- `data/candidate_spectrum_comparison.tsv` — raw IC landscape showing the sharp minimum
- `output/result_artifacts.json` — machine-readable spectral analysis results
- `output/analysis.py` lines 100–140 — candidate spectrum analysis code

**Robustness:** The ranked grid is derived from the complete candidate evaluation; the delta_IC gaps are monotonic and the top-4 cluster is separated from rank 5 (delta_IC=11.9) by a gap of 2.5, which is comparable to the spread among ranks 2–4. The minimum velocity scan independently confirms that the lowest IC values occur at v_min ∈ {0.01, 0.02, 0.03} cm/s with v_max ≥ 30 cm/s, but these are evaluated under a different scan family and use absolute IC (not delta relative to the same reference), so they cannot be directly merged with the ranked grid without knowing the shared baseline.

**Counterevidence and limitations:** The delta_IC gap between rank 1 and rank 2 is only 2.0, which is modest. While only 4 candidates lie within delta_IC ≤ 10, this does not prove physical uniqueness — the DATA_GUIDE explicitly states that "a lower information criterion supports a relative comparison within the supplied candidate family, not proof that the family is physically unique." The frequency_amplitude_scan family (304 rows) dominates the low-IC region, while the minimum_velocity_scan family (203 rows) contributes fewer low-IC candidates.

**Alternative explanations:** The sharp IC minimum could reflect overfitting if the candidate family is flexible enough to absorb noise. However, the consistent preference for frequencies near 1010–1060 μHz across multiple velocity settings argues against pure noise fitting. The narrow width (275 μHz) at rank 1 versus broader widths (300–325 μHz) at other ranks suggests the data prefer a relatively narrow spectral feature.

**Falsification proposal:** Acquire additional passes under identical observational conditions. If the spectral structure is real, the re-ranked candidate grid should continue to place a candidate near 1010 μHz at or near rank 1, with delta_IC to rank 2 remaining small (< 5). If the current ranking is driven by pass-specific noise, adding data should increase the delta_IC gap or shift the preferred frequency.

---

## Finding 2: Residual Variance Is Dominated by Within-Pass Structure With Negligible Between-Pass Coherence

**Object and scope:** All 22 time-resolved passes, three residual models (A, B, C), 1,698 time samples total.

**Relationship and direction:** Variance decomposition reveals that between-pass variance accounts for only 0.7% (Model A), 0.01% (Model B), and 0.05% (Model C) of total variance. Over 99% of the variance resides within individual passes. This means the residuals exhibit rich temporal structure within each pass, but there is no coherent signal shared across passes at the level of pass-mean offsets.

**Core quantitative result:**
| Model | Total Variance | Between-Pass Fraction | Mean Lag-1 Autocorrelation |
|-------|---------------|----------------------|---------------------------|
| A | 0.001615 | 0.0072 | 0.5345 |
| B | 0.000920 | 0.0001 | −0.2776 |
| C | 0.001148 | 0.0005 | 0.1570 |

**Supporting evidence:**
- `data/pass_residual_traces.tsv` — raw residual traces
- `output/result_artifacts.json` — temporal analysis section with per-pass statistics and variance decomposition
- `output/analysis.py` lines 50–90 — autocorrelation and variance decomposition code

**Robustness:** Leave-one-pass-out recomputation of mean and standard deviation shows negligible change (remaining mean shifts < 0.0002, std changes < 0.0002), confirming that no single pass drives the aggregate statistics. First-half vs. second-half comparisons show mean differences centered near zero (A: −0.0015, B: +0.0001, C: −0.0005) with small standard deviations, consistent with stationarity within passes.

**Counterevidence and limitations:** The extremely low between-pass fractions could indicate that the residual models have been normalized or differ primarily in their internal parameterization rather than capturing fundamentally different physics. Model B's negative mean autocorrelation (−0.28) contrasts sharply with Model A's positive value (0.53), suggesting that the three models encode different temporal assumptions. This model-dependence limits generalizability of any single-model finding.

**Alternative explanations:** The lack of between-pass coherence could arise because: (a) each pass observes a different realization of stochastic processes, (b) the residual computation removes any common-mode signal, or (c) the system's intrinsic variability is much faster than the pass-to-pass timescale. Without external timing information linking the passes, these alternatives cannot be distinguished.

**Falsification proposal:** If the passes can be ordered temporally (e.g., by observation date) and correlated with an independent time-varying parameter (e.g., orbital phase, stellar activity cycle), then between-pass variance should become significant when conditioned on that parameter. Failure to find such conditioning would support the null interpretation.

---

## Finding 3: Residual Models A and C Show Substantially Higher Cross-Model Agreement Than Model B

**Object and scope:** Pairwise correlations between Models A, B, and C within each of the 22 passes.

**Relationship and direction:** Model A and Model C agree most strongly (mean Pearson r = 0.81), followed by B and C (r = 0.78), while A and B show the weakest agreement (r = 0.57). In 10 of 22 passes, the A–B correlation falls below 0.50, whereas the A–C correlation exceeds 0.80 in 14 of 22 passes. This asymmetry suggests that Model C shares more structural features with Model A than Model B does.

**Core quantitative result:**
- MA vs MB: mean r = 0.573, std = 0.184, range [0.253, 0.994]
- MA vs MC: mean r = 0.810, std = 0.115, range [0.575, 0.997]
- MB vs MC: mean r = 0.783, std = 0.132, range [0.489, 0.936]

**Supporting evidence:**
- `data/pass_residual_traces.tsv` — raw residual traces
- `output/result_artifacts.json` — cross-model agreement section
- `output/analysis.py` lines 92–100 — cross-model correlation code

**Robustness:** The correlation pattern is stable across leave-one-pass-out tests. The A–C superiority holds regardless of which pass is excluded.

**Counterevidence and limitations:** High correlation does not imply the models capture the same physics; it may reflect shared numerical properties or similar baseline assumptions. The mean absolute differences between models are small (typically 0.005–0.02 mm/s), meaning all three models produce numerically close outputs despite their structural differences.

**Alternative explanations:** Model B may implement a different regularization scheme, noise model, or physical approximation that produces systematically different temporal patterns while maintaining similar overall magnitude. The negative autocorrelation in Model B (Finding 2) is consistent with this interpretation.

**Falsification proposal:** If Models A and C truly share a deeper structural similarity, then leaving out Model C should degrade fit quality more than leaving out Model B, when evaluated on held-out time segments within each pass. Testing this requires access to the underlying fitting procedure.

---

## Finding 4: The Structured Candidate Family Dramatically Outperforms the Uniform-Velocity Alternative

**Object and scope:** Comparison of the best structured candidate (IC = 43.9) against the entire uniform-velocity alternative curve (24 points, velocities from 0.001 to 500 cm/s).

**Relationship and direction:** The best uniform-velocity model achieves IC = 1522.1 at v = 0.1 cm/s, which is 1,478.2 IC units worse than the best structured candidate (IC = 43.9). The uniform IC curve is U-shaped with a clear minimum at v = 0.1 cm/s and rises monotonically on both sides, reaching IC > 13,500 at v = 500 cm/s. No uniform velocity comes within 1% of the structured candidate's IC.

**Core quantitative result:**
- Best structured candidate IC: 43.9
- Best uniform alternative IC: 1522.1 (at v_uniform = 0.1 cm/s)
- Improvement factor: 1522.1 / 43.9 ≈ 34.7× better IC for structured model
- Uniform IC at v = 0.1 cm/s is itself the minimum of the uniform curve; all other uniform velocities yield higher IC

**Supporting evidence:**
- `data/uniform_alternative_comparison.tsv` — uniform velocity IC curve
- `data/ranked_full_parameter_grid.tsv` — best structured candidate
- `output/generate_artifacts.py` — uniform alternative comparison code (lines 90–110)
- `output/result_artifacts.json` — uniform alternative section

**Robustness:** The uniform IC curve is smooth and unimodal, with the minimum clearly at v = 0.1 cm/s. The structured candidate's IC of 43.9 is far outside the range spanned by the uniform curve (1522–13553), making the conclusion insensitive to the exact placement of the uniform minimum.

**Counterevidence and limitations:** The IC comparison is valid only within the supplied candidate family. The DATA_GUIDE warns that "a lower information criterion supports a relative comparison within the supplied candidate family, not proof that the family is physically unique." Other parametric families not explored here might achieve even lower IC. Additionally, the uniform alternative uses a single velocity parameter while the structured candidates use four (v_max, v_min, f_peak, width), so the comparison partially reflects model complexity.

**Alternative explanations:** The structured candidate's superior IC could reflect the ability to fit a narrow spectral feature that the uniform model cannot represent, rather than evidence for a real physical spectral line. If the true signal is broad-band, the structured model might overfit.

**Falsification proposal:** Test the structured candidate against additional uniform-like alternatives with different functional forms (e.g., Gaussian, Lorentzian, power-law) using the same IC metric. If these also achieve IC >> 100, the structured candidate's advantage is robust to alternative null models. If a simple alternative achieves IC < 50, the structured interpretation weakens.

---

## Finding 5: Mode Frequencies in the 900–1300 μHz Range Include 16 Stellar Oscillation Modes With Systematically Varying Coupling Coefficients

**Object and scope:** The mode-frequency grid (52 modes, angular degree l=2–8, radial order n=0–7), focusing on the frequency band overlapping with the spectral peak identified in Finding 1.

**Relationship and direction:** Sixteen modes fall within 900–1300 μHz, spanning radial orders n=3 through n=6 and angular degrees l=2 through l=8. Coupling coefficients decrease with increasing angular degree within each radial order (e.g., for n=4: l=2 has coupling 8.61×10⁻⁹, l=8 has 8.55×10⁻¹⁰), and increase with radial order for fixed l (e.g., for l=2: n=3 has 8.23×10⁻⁹, n=6 has 4.89×10⁻⁹). The surface velocities in this band range from 32.3 to 50.0 cm/s.

**Core quantitative result:**
- Modes in 900–1300 μHz: 16 out of 52 total
- Radial orders present: n=3 (l=5–8), n=4 (l=2–8), n=5 (l=2–5), n=6 (l=2)
- Coupling coefficient range: [8.55×10⁻¹⁰, 8.61×10⁻⁹]
- Surface velocity range: [32.3, 50.0] cm/s

**Supporting evidence:**
- `data/mode_frequency_grid.tsv` — complete mode-frequency grid
- `output/generate_artifacts.py` — mode-frequency grid analysis code (lines 112–130)
- `output/result_artifacts.json` — mode frequency section

**Robustness:** The mode-frequency grid is a fixed lookup table (not estimated from the data), so robustness checks are not applicable. The identification of modes in the relevant frequency band is deterministic.

**Counterevidence and limitations:** The mode-frequency grid provides theoretical mode properties but does not establish which modes are actually excited or detectable in the observations. The coupling coefficients are very small (10⁻⁹–10⁻⁸), suggesting weak mode coupling. Without observed mode amplitudes or linewidths, the connection between the spectral peak (Finding 1) and specific oscillation modes remains speculative.

**Alternative explanations:** The spectral peak at 1010–1060 μHz could correspond to multiple overlapping modes (e.g., n=4, l=4 at 1052 μHz and n=3, l=7 at 1017.5 μHz), making it difficult to attribute the peak to a single mode. Alternatively, the peak could arise from non-oscillatory processes not represented in the mode-frequency grid.

**Falsification proposal:** Obtain high-resolution spectra covering the 900–1300 μHz band with sufficient signal-to-noise to resolve individual mode amplitudes and linewidths. If the peak corresponds to specific modes, the observed mode pattern (relative amplitudes, frequency spacing) should match the theoretical mode-frequency grid predictions.

---

## Reproducibility

### How to reproduce the analysis

```bash
cd output
python3 analysis.py          # Main analysis pipeline
python3 generate_artifacts.py  # Generate result_artifacts.json
```

Both scripts read exclusively from `data/` and write to `output/`. The analysis is fully deterministic given the frozen dataset. Key outputs:
- `output/analysis_results.json` — full numerical results from analysis.py
- `output/result_artifacts.json` — machine-readable artifacts for validation

### Verification

Run the semantic validator:
```bash
python3 validate_output.py output
```

---

## Limitations

1. **Limited number of passes:** Only 22 complete passes are available. Claims about temporal structure must use blocked-time or whole-pass checks rather than treating time samples as replicates (DATA_GUIDE warning).
2. **IC family-bound:** Lower information criterion values support relative comparison within the supplied candidate family only, not proof of physical uniqueness (DATA_GUIDE warning).
3. **Model dependence:** The three residual models show different autocorrelation structures (especially Model B), limiting confidence in model-specific temporal claims.
4. **No direct mode identification:** The mode-frequency grid provides theoretical predictions but no observed mode amplitudes, preventing definitive attribution of the spectral peak to specific oscillation modes.
5. **Anonymous system:** The identity of the gravitating system is unknown, preventing comparison with known astrophysical objects or published results.
