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
