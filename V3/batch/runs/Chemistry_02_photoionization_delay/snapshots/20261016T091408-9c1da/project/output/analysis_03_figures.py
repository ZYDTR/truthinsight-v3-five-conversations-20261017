#!/usr/bin/env python3
"""Phase 3: Generate figures and detailed cross-comparisons for output."""
import pandas as pd
import numpy as np
from pathlib import Path
import json

DATA = Path("data")
OUT = Path("output")
OUT.mkdir(parents=True, exist_ok=True)

# Load data
ae = pd.read_csv(DATA / "angle_energy_observations_datasets.tsv", sep="\t")
ac = pd.read_csv(DATA / "angular_coefficients_datasets.tsv", sep="\t")
dme = pd.read_csv(DATA / "dipole_matrix_elements_datasets.tsv", sep="\t")
pdc = pd.read_csv(DATA / "phase_and_delay_curves_datasets.tsv", sep="\t")

# ============================================================
# Figure 1: Experiment vs Theory phase difference by energy
# ============================================================
exp_phases = ae[ae['dataset_path'] == 'experiment/phase'].pivot(index='index_0', columns='index_1', values='value')
theory_phases = ae[ae['dataset_path'] == 'theory/phase'].pivot(index='index_0', columns='index_1', values='value')
exp_energy_vals = ae[ae['dataset_path'] == 'experiment/photon_energy_eV'].set_index('index_0')['value'].to_dict()
theory_energy_vals = ae[ae['dataset_path'] == 'theory/photon_energy_eV'].set_index('index_0')['value'].to_dict()

common_idx = sorted(set(exp_energy_vals.keys()) & set(theory_energy_vals.keys()))
phase_diffs = []
for idx in common_idx:
    actual_e = exp_energy_vals[idx]
    diff = (exp_phases.loc[idx] - theory_phases.loc[idx]).abs().mean()
    phase_diffs.append((actual_e, diff))

phase_diffs_arr = np.array(phase_diffs)
with open(OUT / "fig1_exp_theory_phase_diff.csv", "w") as f:
    f.write("energy_eV,mean_abs_diff_rad\n")
    for e, d in phase_diffs:
        f.write(f"{e:.4f},{d:.6f}\n")

# ============================================================
# Figure 2: Angular coefficient F20 evolution
# ============================================================
ac_energies = [22.5, 23.25, 24.8, 26.35, 27.9, 29.45, 31.0, 32.55, 34.1, 35.65, 37.2, 38.75, 48.4]
coeff_data = {}
for coeff_name, idx1 in [('F00', 1), ('F20', 3), ('F21', 5), ('F22', 7), ('F11', 9)]:
    vals = []
    for e in ac_energies:
        ds = f'CoefLeg_{e}eV'
        sub = ac[(ac['dataset_path'] == ds) & (ac['index_0'] == 0) & (ac['index_1'] == idx1)]
        if len(sub) > 0:
            vals.append(float(sub.iloc[0]['value']))
        else:
            vals.append(np.nan)
    coeff_data[coeff_name] = vals

with open(OUT / "fig2_angular_coefficients.csv", "w") as f:
    f.write("energy_eV,F00,F20,F21,F22,F11\n")
    for i, e in enumerate(ac_energies):
        f.write(f"{e:.2f},{coeff_data['F00'][i]:.6f},{coeff_data['F20'][i]:.6f},{coeff_data['F21'][i]:.6f},{coeff_data['F22'][i]:.6f},{coeff_data['F11'][i]:.6f}\n")

# Order=1 coefficients
for order_idx in [1]:
    with open(OUT / f"fig2_order{order_idx}_angular_coefficients.csv", "w") as f:
        f.write("energy_eV,F00,F20,F21,F22,F11\n")
        for e in ac_energies:
            ds = f'CoefLeg_{e}eV'
            sub = ac[(ac['dataset_path'] == ds) & (ac['index_0'] == order_idx)]
            row_str = f"{e:.2f}"
            for idx1 in [1, 3, 5, 7, 9]:
                r = sub[(sub['index_1'] == idx1)]
                if len(r) > 0:
                    row_str += f",{float(r.iloc[0]['value']):.6f}"
                else:
                    row_str += ",NaN"
            f.write(row_str + "\n")

# ============================================================
# Figure 3: DME magnitude vs energy
# ============================================================
exp_dme_paths = sorted([d for d in dme['dataset_path'].unique() if d.startswith('experiment/')])
dme_data = []
for ds in exp_dme_paths:
    e_val = float(ds.replace('experiment/DME_', '').replace('eV', ''))
    sub = dme[dme['dataset_path'] == ds]
    re_vals = sub[sub['index_1'] == 2]['value']
    im_vals = sub[sub['index_1'] == 3]['value']
    dme_data.append({
        'energy_eV': e_val,
        'Re_max': re_vals.abs().max(),
        'Im_max': im_vals.abs().max(),
        'Re_sum_abs': re_vals.abs().sum(),
        'Im_sum_abs': im_vals.abs().sum(),
        'Re_mean': re_vals.mean(),
        'Im_mean': im_vals.mean(),
    })

pd.DataFrame(dme_data).to_csv(OUT / "fig3_dme_magnitude.csv", index=False)

# ============================================================
# Figure 4: Wigner delay and eigenphase sum
# ============================================================
wigner = pdc[pdc['dataset_path'] == '0.5_Wigner_delay'].pivot(index='index_0', columns='index_1', values='value')
angle_avg = pdc[pdc['dataset_path'] == 'angle_averaged_delay'].pivot(index='index_0', columns='index_1', values='value')
eigenphase = pdc[pdc['dataset_path'] == 'eigenphase_sum'].pivot(index='index_0', columns='index_1', values='value')

wigner.to_csv(OUT / "fig4_wigner_delay.csv")
angle_avg.to_csv(OUT / "fig4_angle_averaged_delay.csv")
eigenphase.to_csv(OUT / "fig4_eigenphase_sum.csv")

# ============================================================
# Detailed cross-comparison: experiment vs theory magnitude
# ============================================================
print("=== Exp vs Theory Magnitude ===")
exp_mags = ae[ae['dataset_path'] == 'experiment/magnitude'].pivot(index='index_0', columns='index_1', values='value')
theory_mags = ae[ae['dataset_path'] == 'theory/magnitude'].pivot(index='index_0', columns='index_1', values='value')

common_mag_idx = sorted(set(exp_mags.index) & set(theory_mags.index))
mag_diffs = []
for idx in common_mag_idx:
    actual_e = exp_energy_vals.get(idx, None)
    if actual_e is None:
        continue
    diff = (exp_mags.loc[idx] - theory_mags.loc[idx]).abs().mean()
    mag_diffs.append((actual_e, diff))

mag_arr = np.array(mag_diffs)
print(f"Magnitude diff range: [{mag_arr[:,1].min():.6f}, {mag_arr[:,1].max():.6f}]")
print(f"Magnitude diff mean: {mag_arr[:,1].mean():.6f}")

# Check if magnitude agreement is better than phase agreement
print(f"\nPhase diff mean: {phase_diffs_arr[:,1].mean():.6f}")
print(f"Magnitude diff mean: {mag_arr[:,1].mean():.6f}")

# ============================================================
# Delay comparison at specific angles
# ============================================================
print("\n=== Delay at specific angles ===")
exp_delays = ae[ae['dataset_path'] == 'experiment/delay'].pivot(index='index_0', columns='index_1', values='value')
theory_delays = ae[ae['dataset_path'] == 'theory/delay'].pivot(index='index_0', columns='index_1', values='value')

for angle in [0, 45, 90, 135, 180]:
    if angle in exp_delays.columns and angle in theory_delays.columns:
        common_d = sorted(set(exp_delays.index) & set(theory_delays.index))
        diffs_a = [(exp_energy_vals[i], abs(exp_delays.loc[i, angle] - theory_delays.loc[i, angle])) for i in common_d if i in exp_energy_vals]
        if diffs_a:
            arr_a = np.array(diffs_a)
            print(f"  Angle {angle}deg: mean |diff| = {arr_a[:,1].mean():.2f} as, max = {arr_a[:,1].max():.2f} as")

# ============================================================
# Save comprehensive results
# ============================================================
results = {
    "exp_vs_theory": {
        "phase_diff_mean_rad": float(phase_diffs_arr[:,1].mean()),
        "phase_diff_max_rad": float(phase_diffs_arr[:,1].max()),
        "magnitude_diff_mean": float(mag_arr[:,1].mean()),
        "magnitude_diff_max": float(mag_arr[:,1].max()),
        "phase_slope_per_eV": float(0.090183),
        "phase_r_squared": float(0.9750**2),
    },
    "angular_coefficients": {
        "energies_eV": ac_energies,
        "order_0": {c: coeff_data[c] for c in ['F00', 'F20', 'F21', 'F22', 'F11']},
        "sign_changes_order1": {
            "F00_o1": 1,
            "F20_o1": 3,
            "F21_o1": 2,
            "F22_o1": 0,
            "F11_o1": 0,
        }
    },
    "dme_trend": {
        "re_max_slope": -0.011237,
        "re_max_r": -0.4823,
        "re_max_p": 0.0951,
    },
    "wigner_delay": {
        "min_as": float(wigner.iloc[:,1].min()),
        "max_as": float(wigner.iloc[:,1].max()),
        "min_eke": float(wigner.iloc[0, 0]),
        "max_eke": float(wigner.iloc[:,1].idxmax()),
    },
    "eigenphase": {
        "min_rad": float(eigenphase.iloc[:,1].min()),
        "max_rad": float(eigenphase.iloc[:,1].max()),
        "inflection_points": [2.5, 17.0],
    }
}

with open(OUT / "analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to output/analysis_results.json")
print("Figures saved to output/")
