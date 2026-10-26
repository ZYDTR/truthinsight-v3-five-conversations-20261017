#!/usr/bin/env python3
"""Phase 4: Deep analysis - angle-resolved comparisons, energy binning, robustness."""
import pandas as pd
import numpy as np
from pathlib import Path
import json
from scipy import stats

DATA = Path("data")
OUT = Path("/data/user/conversations/conv-57de4486-a4e8-4f3a-8e10-9e6c6a4dea85/project/reproduce_test/output")

ae = pd.read_csv(DATA / "angle_energy_observations_datasets.tsv", sep="\t")
ac = pd.read_csv(DATA / "angular_coefficients_datasets.tsv", sep="\t")
dme = pd.read_csv(DATA / "dipole_matrix_elements_datasets.tsv", sep="\t")
pdc = pd.read_csv(DATA / "phase_and_delay_curves_datasets.tsv", sep="\t")

exp_energy_vals = ae[ae['dataset_path'] == 'experiment/photon_energy_eV'].set_index('index_0')['value'].to_dict()
theory_energy_vals = ae[ae['dataset_path'] == 'theory/photon_energy_eV'].set_index('index_0')['value'].to_dict()

exp_phases = ae[ae['dataset_path'] == 'experiment/phase'].pivot(index='index_0', columns='index_1', values='value')
theory_phases = ae[ae['dataset_path'] == 'theory/phase'].pivot(index='index_0', columns='index_1', values='value')
exp_delays = ae[ae['dataset_path'] == 'experiment/delay'].pivot(index='index_0', columns='index_1', values='value')
theory_delays = ae[ae['dataset_path'] == 'theory/delay'].pivot(index='index_0', columns='index_1', values='value')
exp_mags = ae[ae['dataset_path'] == 'experiment/magnitude'].pivot(index='index_0', columns='index_1', values='value')
theory_mags = ae[ae['dataset_path'] == 'theory/magnitude'].pivot(index='index_0', columns='index_1', values='value')

common_idx = sorted(set(exp_energy_vals.keys()) & set(theory_energy_vals.keys()))

# ============================================================
# Angle-resolved phase difference by energy region
# ============================================================
print("=" * 60)
print("ANGLE-RESOLVED PHASE DIFFERENCES BY ENERGY REGION")
print("=" * 60)

# Split common energies into low, mid, high
common_energies = [exp_energy_vals[i] for i in common_idx]
low_mask = np.array(common_energies) < 28
mid_mask = (np.array(common_energies) >= 28) & (np.array(common_energies) < 35)
high_mask = np.array(common_energies) >= 35

angles = range(0, 181, 10)  # Check every 10 degrees

for label, mask in [("Low (<28 eV)", low_mask), ("Mid (28-35 eV)", mid_mask), ("High (>=35 eV)", high_mask)]:
    idxs = [common_idx[i] for i in range(len(common_idx)) if mask[i]]
    if not idxs:
        continue
    diffs_by_angle = {}
    for idx in idxs:
        d = (exp_phases.loc[idx] - theory_phases.loc[idx]).abs()
        for ang in d.index:
            diffs_by_angle.setdefault(ang, []).append(d.loc[ang])
    avg_diff = {ang: np.mean(vals) for ang, vals in diffs_by_angle.items()}

    print(f"\n{label} ({len(idxs)} energy points):")
    for ang in angles:
        if ang in avg_diff:
            print(f"  Angle {ang:3d}deg: mean |phase diff| = {avg_diff[ang]:.4f} rad")

# ============================================================
# Angular coefficient F20 non-monotonicity analysis
# ============================================================
print("\n" + "=" * 60)
print("F20 NON-MONOTONICITY DETAIL")
print("=" * 60)

ac_energies = [22.5, 23.25, 24.8, 26.35, 27.9, 29.45, 31.0, 32.55, 34.1, 35.65, 37.2, 38.75, 48.4]
f20_vals = []
for e in ac_energies:
    ds = f'CoefLeg_{e}eV'
    sub = ac[(ac['dataset_path'] == ds) & (ac['index_0'] == 0) & (ac['index_1'] == 3)]
    f20_vals.append(float(sub.iloc[0]['value']))

print("F20 values:", f20_vals)
# Find local extrema
f20_arr = np.array(f20_vals)
diffs_f20 = np.diff(f20_arr)
sign_changes_f20 = np.diff(np.sign(diffs_f20))
extrema = np.where(sign_changes_f20 != 0)[0]
print(f"F20 extrema at indices: {extrema}")
for ex in extrema:
    print(f"  Index {ex}: energy={ac_energies[ex]} eV, F20={f20_vals[ex]:.6f} -> energy={ac_energies[ex+1]} eV, F20={f20_vals[ex+1]:.6f}")

# Fit polynomial to F20
if len(ac_energies) > 3:
    coeffs_poly = np.polyfit(ac_energies, f20_vals, 3)
    fitted = np.polyval(coeffs_poly, ac_energies)
    residuals = f20_vals - fitted
    rmse = np.sqrt(np.mean(residuals**2))
    print(f"\n  3rd order poly fit RMSE: {rmse:.6f}")
    print(f"  Poly coefficients: {coeffs_poly}")

# ============================================================
# DME: leave-one-out trend check
# ============================================================
print("\n" + "=" * 60)
print("DME TREND ROBUSTNESS (leave-one-out)")
print("=" * 60)

exp_dme_paths = sorted([d for d in dme['dataset_path'].unique() if d.startswith('experiment/')])
energies_dme = []
re_maxes = []
for ds in exp_dme_paths:
    e_val = float(ds.replace('experiment/DME_', '').replace('eV', ''))
    sub = dme[dme['dataset_path'] == ds]
    re_vals = sub[sub['index_1'] == 2]['value'].abs()
    energies_dme.append(e_val)
    re_maxes.append(re_vals.max())

energies_dme = np.array(energies_dme)
re_maxes = np.array(re_maxes)

# Full trend
slope_full, _, r_full, p_full, _ = stats.linregress(energies_dme, re_maxes)
print(f"Full trend: slope={slope_full:.6f}, r={r_full:.4f}, p={p_full:.4f}")

# Leave-one-out
loo_slopes = []
for i in range(len(energies_dme)):
    mask = np.arange(len(energies_dme)) != i
    s, _, r, p, _ = stats.linregress(energies_dme[mask], re_maxes[mask])
    loo_slopes.append(s)

print(f"LOO slopes: mean={np.mean(loo_slopes):.6f}, std={np.std(loo_slopes):.6f}")
print(f"LOO slopes range: [{min(loo_slopes):.6f}, {max(loo_slopes):.6f}]")
# How many LOO slopes have same sign as full?
same_sign = sum(1 for s in loo_slopes if np.sign(s) == np.sign(slope_full))
print(f"Slopes with same sign as full: {same_sign}/{len(loo_slopes)}")

# ============================================================
# Wigner delay features summary
# ============================================================
print("\n" + "=" * 60)
print("WIGNER DELAY FEATURE SUMMARY")
print("=" * 60)

wigner = pdc[pdc['dataset_path'] == '0.5_Wigner_delay'].pivot(index='index_0', columns='index_1', values='value')
w_eKE = wigner.iloc[:, 0].values
w_delay = wigner.iloc[:, 1].values

# Find where delay crosses zero
zero_crossings_w = np.where(np.diff(np.sign(w_delay)))[0]
print(f"Wigner delay zero crossings at eKE: {[w_eKE[zc] for zc in zero_crossings_w]}")

# Derivative of Wigner delay
w_deriv = np.diff(w_delay)
w_deriv_extrema = np.where(np.diff(np.sign(w_deriv)))[0]
print(f"Wigner delay derivative sign changes at indices: {w_deriv_extrema}")
for de in w_deriv_extrema:
    print(f"  Index {de}: eKE={w_eKE[de]:.1f} eV")

# ============================================================
# Save deep results
# ============================================================
deep_results = {
    "angle_resolved_phase_diff": {},
    "f20_analysis": {
        "energies": ac_energies,
        "values": f20_vals,
        "extrema_indices": [int(x) for x in extrema],
    },
    "dme_loo": {
        "full_slope": float(slope_full),
        "loo_mean_slope": float(np.mean(loo_slopes)),
        "loo_std_slope": float(np.std(loo_slopes)),
        "same_sign_count": int(same_sign),
        "total_count": len(loo_slopes),
    },
    "wigner_features": {
        "zero_crossings_eke": [float(w_eKE[zc]) for zc in zero_crossings_w],
    }
}

with open(OUT / "deep_analysis_results.json", "w") as f:
    json.dump(deep_results, f, indent=2)

print("\nDeep results saved.")
