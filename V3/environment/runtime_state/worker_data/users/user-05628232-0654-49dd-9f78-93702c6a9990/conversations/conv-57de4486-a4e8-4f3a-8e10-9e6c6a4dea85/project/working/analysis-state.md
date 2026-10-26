# Analysis State Log - Photoionization Dynamics (Revised)

## Data Inventory (complete)
- `data/angle_energy_observations_datasets.tsv` (8.5 MB, 204011 rows): experiment/theory phase, delay, magnitude, photon energy grids
- `data/angular_coefficients_datasets.tsv` (45 KB, 1287 rows): Legendre coefficients F00-F11 at 13 energies
- `data/dipole_matrix_elements_datasets.tsv` (9.9 MB, 341106 rows): 13 experimental DME blocks + 1 theory block
- `data/phase_and_delay_curves_datasets.tsv` (43 KB, 1092 rows): Wigner delay, angle-averaged delay, eigenphase sum
- `data/coordinate_definitions.json`: angle=0-180 deg, hbar_as_eV=658.2119569, 13 measured energies

## Critical Grid Alignment Correction (Round 2)
- Experiment grid: 276 points, constant 0.1 eV step, 22.5–50.0 eV
- Theory grid: 99 points, irregular steps, 23.249–41.839 eV
- **Exact common energies: {40.1} only (count=1)**
- Old index-alignment had energy mismatches growing from 0.75 to 9.54 eV (slope=0.093 eV/index, r²=0.9996)
- Corrected method: cubic spline interpolation onto theory grid, ±1% Gaussian noise perturbation (100 realizations)

## Key Results (Corrected)
### Finding 1: Exp vs Theory Phase Disagreement (CORRECTED)
- OLD (flawed index-alignment): mean diff = 2.54 rad, slope = 0.090 rad/eV
- NEW (spline-aligned): mean diff = **4.08 rad**, slope = **0.046 rad/eV**, r² = 0.60, p < 10⁻²⁰
- Perturbation CI: slope [0.0456, 0.0459], mean [4.078, 4.080]
- Magnitude mean diff = 0.127 (tight agreement)

### Finding 2: Angular Coefficient F20 Non-Monotonicity
- F20 varies from 0.26 to 1.44 across 22.5–48.4 eV
- 6 extrema detected; order=1 F20 has 3 sign changes

### Finding 3: DME Energy Decrease
- Re_max slope = −0.011/eV, r = −0.48, p = 0.095
- LOO robustness: 13/13 same-sign slopes

### Finding 4: Wigner Delay Features
- Range: [−21.7, +182.6] as; zero crossings at 2.9 and 17.1 eV
- **CORRECTION (Round 3):** Eigenphase sum is NON-MONOTONIC. Direct computation from raw TSV: decreases 0.5→3.0 eV (min −1.113), increases 3.0→17.5 eV (max +0.466), decreases 17.5→30.0 eV. Code in analysis_02_core_findings.py lines 271–276 detects local extrema via `np.diff(np.sign(np.diff(phase)))` — first-derivative sign changes, NOT second-derivative inflection points. Old claim of "monotonic increase" and "inflection points at 2.5/17.0 eV" was incorrect. Second-derivative sign changes on raw data occur at ~9/24/25/26 eV but are grid-sensitive.

## Round 3 Corrections (Fact Feedback)
### Finding 4 eigenphase correction
- Problem: Result.md claimed "monotonically increasing" and "inflection points at 2.5/17.0 eV (second derivative)"
- Root cause: Code computes extrema (first-derivative sign changes), not inflection points; eigenphase is non-monotonic
- Evidence: Raw TSV direct computation confirms min at 3.0 eV (−1.113), max at 17.5 eV (+0.466); sub-agent JSON also says `monotonically_increasing: false`
- Fix: Rewrote Finding 4 to describe non-monotonic behavior, correct extremum locations, and code-method mismatch

### Finding 1 angle-resolved correction
- Problem: Stale numbers (0.13 rad at 90°, 6.7 rad at 100-170°) from index-aligned analysis_04_deep.py still in text
- Evidence: `deep_analysis_results.json.angle_resolved_phase_diff` is empty object; old numbers came from stale stdout
- Fix: Re-ran angle-resolved analysis on spline-aligned grids (`working/analysis_round3_angle_resolved.py`); new values: 90° ≈ 0.09 rad (low energy), wide angles ≈ 6.6 rad; saved to `output/fig1_angle_resolved_aligned.csv`

### Finding 1 Robustness section correction
- Problem: Sentence claiming sub-agent confirmed aligned-grid results for Finding 1
- Evidence: Sub-agent prompt only covered Findings 2/3/4 (DME, angular coeff, Wigner)
- Fix: Limited claim to actual sub-agent scope; explicitly noted Finding 1 was not independently replicated

### Dual-口径 correction
- Problem: `analysis_results.json` described as containing "2.54 rad"; actually contains 4.0137 (cell-averaged, old alignment)
- Evidence: `analysis_03_figures.py` line 153 writes phase_diff_mean_rad = 4.0137; 2.54 was from analysis_02_core_findings.py stdout (angle-average口径)
- Fix: Corrected description; noted that口径(b) has not been re-executed under spline alignment

### Sub-agent eigenphase discrepancy resolution
- Problem: analysis-state.md marked sub-agent eigenphase result as "CONSISTENT" with main-agent's wrong claim
- Evidence: Sub-agent says `monotonically_increasing: false`; main-agent said monotonic
- Fix: Removed CONSISTENT label; documented the substantive disagreement and its resolution in Finding 4

## Artifacts Produced
- `output/analysis_0{1-4}_*.py` — original analysis scripts
- `output/analysis_fix_energy_alignment.py` — corrected grid alignment
- `output/fig1_exp_theory_phase_diff.csv` — old (flawed) per-energy phase diff
- `output/fig1_aligned_phase_diff.csv` — corrected per-energy phase diff
- `output/fig2_angular_coefficients.csv` — order=0 coefficients
- `output/fig2_order1_angular_coefficients.csv` — order=1 coefficients
- `output/fig3_dme_magnitude.csv` — DME statistics
- `output/fig4_wigner_delay.csv`, `fig4_angle_averaged_delay.csv`, `fig4_eigenphase_sum.csv`
- `output/analysis_results.json` — superseded by aligned version
- `output/deep_analysis_results.json` — deep analysis results
- `output/aligned_exp_theory_comparison.json` — corrected comparison with grid characterization

## Sub-Agent Delegation (Round 2)
- Delegated independent replication of DME trend, angular coefficient evolution, and Wigner delay features to general-purpose sub-agent (agentId: a33d90480d78167ae)
- Sub-agent writes own code from scratch, executes, saves to output/
- **Adoption Status (Round 3):** All three sub-agent results incorporated into Result.md findings:
  - `independent_dme_results.json`: Re_max slope = −0.0112/eV, r² = 0.23, p = 0.095 — CONSISTENT with Finding 3 (slope −0.011/eV). LOO 13/13 same-sign confirmed. max_abs_real at 22.5 eV = 0.456 (not 3.0 as in stale snapshot).
  - `independent_angular_coeff_results.json`: F20 order=0 min=0.346 at 24.8 eV, max=1.435 at 27.9 eV — CONSISTENT with Finding 2. Order=1 F20 sign changes = 3 — CONSISTENT.
  - `independent_wigner_results.json`: Wigner delay peak=182.56 at 9.1 eV, zero crossings at 2.96 and 17.20 eV — CONSISTENT with Finding 4. Eigenphase: sub-agent says `monotonically_increasing: false` with inflection candidates at ~9.5/25/26/27 eV; this DISAGREES with earlier main-agent claim of monotonic increase. Resolution: Finding 4 rewritten to reflect non-monotonic behavior (see Round 3 corrections above).
- Sub-agent code was deleted after execution (per leaf-agent constraint); results preserved in JSON files only.

## Round 4: Clean-directory reproduction verification
- Executed `working/reproduce_clean_v2.py` to rebuild all artifacts from raw data into `reproduce_test/output/`
- Procedure: copy each script → patch OUT path → run sequentially from `data/` only → compare with authoritative `output/`
- Tolerance: 1e-6 absolute difference (deterministic algorithms: cubic spline, linregress, seeded noise)
- **Initial Result: 15/15 PASS** — but this was misleading because `independent_angular_coeff_results.json` in authoritative `output/` contained stale sub-agent output with wrong column mapping (index_1=2 instead of index_1=3 for F20). The clean-directory reproduction compared the same wrong file against itself.
- Full comparison: `reproduce_test/comparison_results.json`
- Caveat: `independent_angular_coeff_agent.py` has a column-parsing bug (reads wrong index_1 values); the authoritative result was copied from the incorrect Round 2 sub-agent output.

## Round 5: Angular coefficient reproducibility gap resolved
- **Problem:** The authoritative `output/independent_angular_coeff_results.json` contained incorrect data from the original sub-agent (wrong column mapping: index_1=2 instead of index_1=3 for F20). The clean-directory "15/15 PASS" claim was false — it compared the wrong authoritative file against a reproduced version of the same wrong file.
- **Investigation:** Delegated sub-agent (a85d91b2fb09d939a) to rebuild from scratch. Sub-agent also selected index_1=2, producing wrong F20 values (0.003–0.005 range vs correct 0.26–1.44 range). Both the main-agent's representative reconstruction (`independent_angular_coeff_agent.py`) AND the sub-agent have the same column-parsing bug.
- **Resolution:** Main agent directly computed the correct results from raw data using proper column mapping (index_1=3 for F20 at both order=0 and order=1). Results written to both `output/independent_angular_coeff_results.json` and `reproduce_test/output/independent_angular_coeff_results.json`.
- **Corrected F20 values:** min=0.262@48.4 eV, max=1.435@27.9 eV, 6 extrema, order=1 sign changes=3.
- **Reproduction status:** 14/15 artifacts independently rebuilt via scripts and match within tolerance. 1 artifact (`independent_angular_coeff_results.json`) DIRECT_REBUILT — numerically identical but not independently rebuilt through a separate script.
- **Result.md updated:** Removed false "All 15 core artifacts reproduce identically" statement; added NOT_REBUILT/DIRECT_REBUILT entry with honest documentation of the column-parsing bug and its impact.
- **Validator passes:** 4 findings, 0 errors, 0 warnings.
