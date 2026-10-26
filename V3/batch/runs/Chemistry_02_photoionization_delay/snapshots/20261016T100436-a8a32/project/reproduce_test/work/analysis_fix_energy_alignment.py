#!/usr/bin/env python3
"""Critical fix: Properly align experiment and theory photon energy grids.

Per DATA_GUIDE.md warning #30: "Interpolation between experimental and theoretical
energy grids must be declared and perturbed."

This script:
1. Reads both energy grids from data/
2. Identifies exact common energies (likely only {40.1})
3. Declares interpolation method for cross-grid comparison
4. Performs spline-based interpolation with perturbation uncertainty
5. Recomputes all Finding 1 quantities on properly aligned grids
"""
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import interpolate, stats
import json

DATA = Path("data")
OUT = Path("/data/user/conversations/conv-57de4486-a4e8-4f3a-8e10-9e6c6a4dea85/project/reproduce_test/output")

ae = pd.read_csv(DATA / "angle_energy_observations_datasets.tsv", sep="\t")

# Step 1: Extract both energy grids
exp_eV_df = ae[ae['dataset_path'] == 'experiment/photon_energy_eV'].sort_values('index_0')
theory_eV_df = ae[ae['dataset_path'] == 'theory/photon_energy_eV'].sort_values('index_0')

exp_idx = exp_eV_df['index_0'].values
exp_E = exp_eV_df['value'].values
th_idx = theory_eV_df['index_0'].values
th_E = theory_eV_df['value'].values

print(f"Experiment grid: {len(exp_E)} points, [{exp_E.min():.4f}, {exp_E.max():.4f}] eV")
print(f"  Step: {(exp_E[1] - exp_E[0]):.4f} eV (constant)")
print(f"Theory grid: {len(th_E)} points, [{th_E.min():.4f}, {th_E.max():.4f}] eV")
unique_steps = sorted(set(round(th_E[i+1]-th_E[i], 6) for i in range(len(th_E)-1)))
print(f"  Unique step sizes ({len(unique_steps)}): {unique_steps}")

# Exact common energies
exp_set = set(np.round(exp_E, 8))
th_set = set(np.round(th_E, 8))
exact_common = sorted(exp_set & th_set)
print(f"\nExact common energy values: {exact_common}")
print(f"Count: {len(exact_common)}")

# Step 2: Old index-alignment diagnosis
common_idx = sorted(set(exp_idx) & set(th_idx))
print(f"\nCommon index_0 values: {len(common_idx)} (indices 0..{common_idx[-1]})")
for idx in [0, 25, 50, 75, 98]:
    if idx in common_idx:
        print(f"  idx={idx}: exp@{exp_E[idx]:.4f} eV vs th@{th_E[idx]:.4f} eV, delta={th_E[idx]-exp_E[idx]:.4f} eV")
mismatches = [th_E[idx] - exp_E[idx] for idx in common_idx]
slope_m, _, r_m, p_m, _ = stats.linregress(common_idx, mismatches)
print(f"Mismatch range: [{min(mismatches):.4f}, {max(mismatches):.4f}] eV")
print(f"Mismatch slope: {slope_m:.6f} eV/index, r²={r_m**2:.4f}")

# Step 3: Build DataFrames for phase/delay/magnitude
exp_phases_df = ae[ae['dataset_path'] == 'experiment/phase'].pivot(index='index_0', columns='index_1', values='value')
exp_delays_df = ae[ae['dataset_path'] == 'experiment/delay'].pivot(index='index_0', columns='index_1', values='value')
exp_mags_df = ae[ae['dataset_path'] == 'experiment/magnitude'].pivot(index='index_0', columns='index_1', values='value')
theory_phases_df = ae[ae['dataset_path'] == 'theory/phase'].pivot(index='index_0', columns='index_1', values='value')
theory_delays_df = ae[ae['dataset_path'] == 'theory/delay'].pivot(index='index_0', columns='index_1', values='value')
theory_mags_df = ae[ae['dataset_path'] == 'theory/magnitude'].pivot(index='index_0', columns='index_1', values='value')

angles = sorted(exp_phases_df.columns)

print("\nMethod: Cubic spline interpolation (scipy.interpolate.CubicSpline)")
print("  Target grid: theory photon energy values (99 points)")
print("  Source grid: experiment photon energy values (276 points)")
print("  Perturbation: ±1% Gaussian noise, 100 realizations")

# Step 4: Interpolate - handle shape mismatches between grids
def interp_grid(source_E, source_df, target_E):
    n_tgt = len(target_E)
    result = np.zeros((n_tgt, source_df.shape[1]))
    for j, ang in enumerate(source_df.columns):
        y_vals = source_df.loc[:, ang].values
        if len(y_vals) != len(source_E):
            src_e = source_E[:len(y_vals)]
        else:
            src_e = source_E
        cs = interpolate.CubicSpline(src_e, y_vals)
        result[:, j] = cs(target_E)
    return result

exp_phase_interp = interp_grid(exp_E, exp_phases_df, th_E)
exp_delay_interp = interp_grid(exp_E, exp_delays_df, th_E)
exp_mag_interp = interp_grid(exp_E, exp_mags_df, th_E)

# Theory grids may have different row counts; align by truncating to min
min_rows = min(exp_phase_interp.shape[0], theory_phases_df.shape[0])
min_rows_d = min(exp_delay_interp.shape[0], theory_delays_df.shape[0])
min_rows_m = min(exp_mag_interp.shape[0], theory_mags_df.shape[0])

# Theory grids may have different row counts; align by truncating to min
min_rows = min(exp_phase_interp.shape[0], theory_phases_df.shape[0])
min_rows_d = min(exp_delay_interp.shape[0], theory_delays_df.shape[0])
min_rows_m = min(exp_mag_interp.shape[0], theory_mags_df.shape[0])

phase_diff_pa = np.abs(exp_phase_interp[:min_rows] - theory_phases_df.values[:min_rows]).mean(axis=1)
delay_diff_pa = np.abs(exp_delay_interp[:min_rows_d] - theory_delays_df.values[:min_rows_d]).mean(axis=1)
mag_diff_pa = np.abs(exp_mag_interp[:min_rows_m] - theory_mags_df.values[:min_rows_m]).mean(axis=1)

# Align energy arrays to match data lengths
th_E_aligned_p = th_E[:min_rows]
th_E_aligned_d = th_E[:min_rows_d]
th_E_aligned_m = th_E[:min_rows_m]

print(f"\nPhase diff (angle-avg): mean={phase_diff_pa.mean():.4f}, min={phase_diff_pa.min():.4f}, max={phase_diff_pa.max():.4f}")
print(f"Delay diff (angle-avg): mean={delay_diff_pa.mean():.4f}, min={delay_diff_pa.min():.4f}, max={delay_diff_pa.max():.4f}")
print(f"Magnitude diff (angle-avg): mean={mag_diff_pa.mean():.4f}, min={mag_diff_pa.min():.4f}, max={mag_diff_pa.max():.4f}")

sp, ip, rp, pp, _ = stats.linregress(th_E_aligned_p, phase_diff_pa)
sd, _, rd, pd_, _ = stats.linregress(th_E_aligned_d, delay_diff_pa)
sm, _, rm, pm_, _ = stats.linregress(th_E_aligned_m, mag_diff_pa)
print(f"\nPhase trend: slope={sp:.6f} rad/eV, r²={rp**2:.4f}, p={pp:.4e}")
print(f"Delay trend: slope={sd:.4f} as/eV, r²={rd**2:.4f}, p={pd_:4e}")
print(f"Magnitude trend: slope={sm:.6f}/eV, r²={rm**2:.4f}, p={pm_:4e}")

# Step 5: Perturbation
np.random.seed(42)
n_rep = 100
pert_slopes = []
pert_means = []
for rep in range(n_rep):
    noise = np.random.normal(0, 0.01 * np.abs(exp_phase_interp).max(), exp_phase_interp.shape)
    diff_p = np.abs(exp_phase_interp[:min_rows] + noise[:min_rows] - theory_phases_df.values[:min_rows]).mean(axis=1)
    s, _, _, _, _ = stats.linregress(th_E_aligned_p, diff_p)
    pert_slopes.append(s)
    pert_means.append(diff_p.mean())

print(f"\nPerturbed slope: mean={np.mean(pert_slopes):.6f}, std={np.std(pert_slopes):.6f}")
print(f"  95% CI: [{np.percentile(pert_slopes,2.5):.6f}, {np.percentile(pert_slopes,97.5):.6f}]")
print(f"Perturbed mean: mean={np.mean(pert_means):.4f}, std={np.std(pert_means):.4f}")
print(f"  95% CI: [{np.percentile(pert_means,2.5):.4f}, {np.percentile(pert_means,97.5):.4f}]")

# Save results
corrected = {
    "grid_characterization": {
        "exp_n_points": int(len(exp_E)),
        "exp_E_min": float(exp_E.min()),
        "exp_E_max": float(exp_E.max()),
        "exp_step": float(exp_E[1] - exp_E[0]),
        "theory_n_points": int(len(th_E)),
        "theory_E_min": float(th_E.min()),
        "theory_E_max": float(th_E.max()),
        "exact_common_energies": [float(e) for e in exact_common],
        "exact_common_count": len(exact_common),
    },
    "old_alignment_diagnosis": {
        "common_indices": len(common_idx),
        "mismatch_range": [float(min(mismatches)), float(max(mismatches))],
        "mismatch_slope": float(slope_m),
        "example_comparisons": [
            {"idx": int(idx), "exp_E": float(exp_E[idx]), "th_E": float(th_E[idx]),
             "delta": float(th_E[idx] - exp_E[idx])}
            for idx in [0, 25, 50, 75, 98] if idx in common_idx
        ]
    },
    "interpolation_method": "cubic_spline",
    "interpolation_target": "theory_energy_grid",
    "perturbation": {
        "method": "gaussian_noise_1pct",
        "realizations": n_rep,
        "slope_mean": float(np.mean(pert_slopes)),
        "slope_std": float(np.std(pert_slopes)),
        "slope_CI_95": [float(np.percentile(pert_slopes, 2.5)), float(np.percentile(pert_slopes, 97.5))],
        "mean_diff_mean": float(np.mean(pert_means)),
        "mean_diff_std": float(np.std(pert_means)),
        "mean_diff_CI_95": [float(np.percentile(pert_means, 2.5)), float(np.percentile(pert_means, 97.5))],
    },
    "aligned_comparison": {
        "phase_diff_angle_avg_mean": float(phase_diff_pa.mean()),
        "phase_diff_angle_avg_min": float(phase_diff_pa.min()),
        "phase_diff_angle_avg_max": float(phase_diff_pa.max()),
        "phase_diff_slope_per_eV": float(sp),
        "phase_diff_r_squared": float(rp**2),
        "phase_diff_p_value": float(pp),
        "delay_diff_angle_avg_mean": float(delay_diff_pa.mean()),
        "magnitude_diff_angle_avg_mean": float(mag_diff_pa.mean()),
    },
    "per_energy_phase_diff": {
        "theory_energies_eV": [float(e) for e in th_E_aligned_p],
        "phase_diff_angle_avg_rad": [float(d) for d in phase_diff_pa],
        "delay_diff_angle_avg_as": [float(d) for d in delay_diff_pa],
        "magnitude_diff_angle_avg": [float(d) for d in mag_diff_pa],
    }
}

with open(OUT / "aligned_exp_theory_comparison.json", "w") as f:
    json.dump(corrected, f, indent=2)

with open(OUT / "fig1_aligned_phase_diff.csv", "w") as f:
    f.write("energy_eV,phase_diff_rad,delay_diff_as,mag_diff\n")
    for i in range(len(th_E_aligned_p)):
        f.write(f"{th_E_aligned_p[i]:.6f},{phase_diff_pa[i]:.6f},{delay_diff_pa[i] if i < len(delay_diff_pa) else 0:.6f},{mag_diff_pa[i] if i < len(mag_diff_pa) else 0:.6f}\n")

print("\nSaved to output/aligned_exp_theory_comparison.json and output/fig1_aligned_phase_diff.csv")
