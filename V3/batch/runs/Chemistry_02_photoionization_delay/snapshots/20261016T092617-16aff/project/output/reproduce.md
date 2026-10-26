# Reproduction Guide

## How to Reproduce the Analysis

All scripts must be run from the project root directory. The `data/` directory must remain unmodified.

### Prerequisites
- Python 3.11+
- pandas, numpy, scipy

### Step-by-step

```bash
cd /data/user/conversations/conv-57de4486-a4e8-4f3a-8e10-9e6c6a4dea85/project

# Step 1: Explore data structure
python3 output/analysis_01_explore_data.py

# Step 2: Run core statistical analysis (produces output/analysis_summary.json)
python3 output/analysis_02_core_findings.py

# Step 3: Generate figure CSVs and cross-comparisons (produces output/fig*.csv, output/analysis_results.json)
python3 output/analysis_03_figures.py

# Step 4: Deep angle-resolved and robustness analysis (produces output/deep_analysis_results.json)
python3 output/analysis_04_deep.py

# Step 5: CORRECTED energy-grid alignment with interpolation and perturbation
python3 output/analysis_fix_energy_alignment.py

# Step 6: Independent replication (sub-agent code restored for reproducibility)
python3 output/independent_dme_agent.py
python3 output/independent_angular_coeff_agent.py
python3 output/independent_wigner_agent.py
```

### Expected outputs in `output/`
| File | Description |
|------|-------------|
| `Result.md` | Authoritative findings report (4 registered findings) |
| `fig1_aligned_phase_diff.csv` | Per-energy phase difference (spline-aligned) |
| `fig1_exp_theory_phase_diff.csv` | Per-energy phase difference (old flawed version) |
| `fig2_angular_coefficients.csv` | Order-0 Legendre coefficients at 13 energies |
| `fig2_order1_angular_coefficients.csv` | Order-1 Legendre coefficients at 13 energies |
| `fig3_dme_magnitude.csv` | DME magnitude statistics at 13 energies |
| `fig4_wigner_delay.csv` | Full Wigner delay curve (296 points) |
| `fig4_angle_averaged_delay.csv` | Angle-averaged delay curve (200 points) |
| `fig4_eigenphase_sum.csv` | Eigenphase sum curve (50 points) |
| `aligned_exp_theory_comparison.json` | Grid characterization, old-alignment diagnosis, perturbation analysis |
| `analysis_results.json` | Summary statistics (superseded by aligned version) |
| `deep_analysis_results.json` | Angle-resolved and LOO robustness results |
| `independent_dme_results.json` | Independent sub-agent DME replication |
| `independent_angular_coeff_results.json` | Independent sub-agent angular coefficient replication |
| `independent_wigner_results.json` | Independent sub-agent Wigner delay replication |

### Validation
Run the validation script:
```bash
python3 validate_output.py output
```
