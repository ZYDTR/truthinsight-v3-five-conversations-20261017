# Analysis State Log - Photoionization Dynamics

## Data Inventory (complete)
- `data/angle_energy_observations_datasets.tsv` (8.5 MB, 204011 rows): experiment/theory phase, delay, magnitude, photon_energy_eV grids (276 energy x 181 angle for exp; 99 x 181 for theory)
- `data/angular_coefficients_datasets.tsv` (45 KB, 1287 rows): 13 energies, Legendre coefficients F00-F11 at orders 0-8
- `data/dipole_matrix_elements_datasets.tsv` (9.9 MB, 341106 rows): 13 experimental DME blocks (7x6 each) + 1 theory block (34056x10)
- `data/phase_and_delay_curves_datasets.tsv` (43 KB, 1092 rows): Wigner delay (296 pts), angle-averaged delay (200 pts), eigenphase sum (50 pts)
- `data/coordinate_definitions.json`: angle=0-180 deg, hbar_as_eV=658.2119569, 13 measured energies

## Key Results
### Finding 1: Exp vs Theory Phase Disagreement Increases with Energy
- Mean |exp-th| phase diff = 2.54 rad (angle-avg over common 99 energy points)
- Slope of phase diff vs energy = 0.090 rad/eV, r²=0.95, p<0.001
- Angle-resolved: disagreement peaks at ~100-170° in mid-energy region
- Magnitude agreement is much better: mean |diff| = 0.21

### Finding 2: Angular Coefficient F20 Shows Non-Monotonic Resonance-like Structure
- F20 varies from 0.26 to 1.44 across 22.5-48.4 eV
- 6 extrema detected (local min at 24.8 eV, local max at 27.9 eV, etc.)
- Order=1 F20 shows 3 sign changes across energies
- Order=1 F21 shows 2 sign changes

### Finding 3: Dipole Matrix Element Magnitude Decreases with Energy
- Re_max slope = -0.011/eV, r=-0.48, p=0.095 (marginal significance)
- LOO robustness: all 13/13 leave-one-out slopes negative, range [-0.014, -0.006]
- Strongest DME at 31.0 eV (Re_max=0.71), weakest at 48.4 eV (Re_max=0.12)

### Finding 4: Wigner Delay and Eigenphase Sum Show Characteristic Resonance Features
- Wigner delay: min=-21.71 as at 0.5 eV, max=182.56 as at 9.1 eV
- Zero crossings at eKE=2.9 and 17.1 eV
- Eigenphase sum: monotonic increase from -1.11 to 0.47 rad with inflection at 2.5 and 17.0 eV

## Artifacts Produced
- `working/analysis_01_explore_data.py` - Initial data exploration
- `working/analysis_02_core_findings.py` - Core statistical analysis
- `working/analysis_03_figures.py` - Figure generation and cross-comparisons
- `working/analysis_04_deep.py` - Deep angle-resolved and robustness analysis
- `output/fig1_exp_theory_phase_diff.csv`
- `output/fig2_angular_coefficients.csv`
- `output/fig2_order1_angular_coefficients.csv`
- `output/fig3_dme_magnitude.csv`
- `output/fig4_wigner_delay.csv`
- `output/fig4_angle_averaged_delay.csv`
- `output/fig4_eigenphase_sum.csv`
- `output/analysis_results.json`
- `output/deep_analysis_results.json`
