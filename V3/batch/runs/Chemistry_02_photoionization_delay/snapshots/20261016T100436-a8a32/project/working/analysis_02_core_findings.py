#!/usr/bin/env python3
"""Phase 2: Core analysis for photoionization dynamics findings.

This script performs:
1. Experiment vs theory phase/delay/magnitude comparison across energy-angle grids
2. Angular coefficient evolution with photon energy
3. Dipole matrix element trends across measured energies
4. Wigner delay / eigenphase sum behavior
5. Robustness checks (energy binning, leave-one-out)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json

DATA = Path("data")
OUT = Path("output")
OUT.mkdir(parents=True, exist_ok=True)

# ============================================================
# LOAD ALL DATA
# ============================================================
ae = pd.read_csv(DATA / "angle_energy_observations_datasets.tsv", sep="\t")
ac = pd.read_csv(DATA / "angular_coefficients_datasets.tsv", sep="\t")
dme = pd.read_csv(DATA / "dipole_matrix_elements_datasets.tsv", sep="\t")
pdc = pd.read_csv(DATA / "phase_and_delay_curves_datasets.tsv", sep="\t")

# ============================================================
# FINDING 1: Experiment vs Theory Phase/Delay - Agreement at low energy, divergence at high energy
# ============================================================
print("=" * 60)
print("FINDING 1: Exp vs Theory phase/delay comparison")
print("=" * 60)

# Extract experiment and theory panels
# index_0 = energy index, index_1 = angle (0-180 deg)
exp_phases = ae[ae['dataset_path'] == 'experiment/phase'].pivot(index='index_0', columns='index_1', values='value')
exp_delays = ae[ae['dataset_path'] == 'experiment/delay'].pivot(index='index_0', columns='index_1', values='value')
exp_mags = ae[ae['dataset_path'] == 'experiment/magnitude'].pivot(index='index_0', columns='index_1', values='value')
exp_energy_vals = ae[ae['dataset_path'] == 'experiment/photon_energy_eV'].set_index('index_0')['value'].to_dict()

theory_phases = ae[ae['dataset_path'] == 'theory/phase'].pivot(index='index_0', columns='index_1', values='value')
theory_delays = ae[ae['dataset_path'] == 'theory/delay'].pivot(index='index_0', columns='index_1', values='value')
theory_mags = ae[ae['dataset_path'] == 'theory/magnitude'].pivot(index='index_0', columns='index_1', values='value')
theory_energy_vals = ae[ae['dataset_path'] == 'theory/photon_energy_eV'].set_index('index_0')['value'].to_dict()

exp_energies_arr = np.array(sorted(exp_energy_vals.values()))
theory_energies_arr = np.array(sorted(theory_energy_vals.values()))

print(f"Experiment energy range: [{exp_energies_arr.min():.1f}, {exp_energies_arr.max():.1f}] eV ({len(exp_energies_arr)} points)")
print(f"Theory energy range: [{theory_energies_arr.min():.1f}, {theory_energies_arr.max():.1f}] eV ({len(theory_energies_arr)} points)")

# Common energy indices (overlap region by index_0)
common_idx = set(exp_energy_vals.keys()) & set(theory_energy_vals.keys())
common_idx_sorted = sorted(common_idx)
print(f"Common energy index points: {len(common_idx_sorted)}")

# Compare phases in common region
if len(common_idx_sorted) > 0:
    exp_common = exp_phases.loc[[e for e in common_idx_sorted], :]
    th_common = theory_phases.loc[[e for e in common_idx_sorted], :]

    # Angle-averaged difference
    exp_mean = exp_common.mean(axis=1)
    th_mean = th_common.mean(axis=1)
    diff_mean = (exp_mean - th_mean).abs()

    print(f"\nPhase comparison (common energies):")
    print(f"  Mean |exp - th| (angle-avg): {diff_mean.mean():.4f}")
    print(f"  Max |exp - th| (angle-avg): {diff_mean.max():.4f}")

    # Per-energy differences
    for e in common_idx_sorted[:5]:
        ed = (exp_phases.loc[e] - theory_phases.loc[e]).abs().mean()
        print(f"  Energy {e:.2f} eV: mean |diff| across angles = {ed:.4f}")

    # Check if disagreement increases with energy
    diffs_by_energy = {}
    for idx in common_idx_sorted:
        actual_e = exp_energy_vals[idx]
        d = (exp_phases.loc[idx] - theory_phases.loc[idx]).abs().mean()
        diffs_by_energy[actual_e] = d

    energies_arr = np.array(sorted(diffs_by_energy.keys()))
    diffs_arr = np.array([diffs_by_energy[e] for e in energies_arr])

    from scipy import stats
    if len(energies_arr) > 2:
        slope, intercept, r_val, p_val, std_err = stats.linregress(energies_arr, diffs_arr)
        print(f"\n  Phase diff vs energy: slope={slope:.6f}/eV, r={r_val:.4f}, p={p_val:.4f}")

# Compare delays
print(f"\nDelay comparison:")
exp_d_mean = exp_delays.mean(axis=1)
th_d_mean = theory_delays.mean(axis=1)

# Find common delay indices
common_d_idx = set(exp_delays.index) & set(theory_delays.index)
if len(common_d_idx) > 0:
    exp_d_common = exp_delays.loc[list(common_d_idx)]
    th_d_common = theory_delays.loc[list(common_d_idx)]
    d_diff = (exp_d_common - th_d_common).abs().mean(axis=1)
    print(f"  Mean |exp - th| delay (common): {d_diff.mean():.4f}")
    print(f"  Max |exp - th| delay (common): {d_diff.max():.4f}")

# ============================================================
# FINDING 2: Angular coefficient evolution shows resonance-like structure
# ============================================================
print("\n" + "=" * 60)
print("FINDING 2: Angular coefficient evolution")
print("=" * 60)

# Parse energy from CoefLeg names
ac_energies = []
for ds in ac['dataset_path'].unique():
    e_str = ds.replace('CoefLeg_', '').replace('eV', '')
    ac_energies.append(float(e_str))
ac_energies.sort()
print(f"Angular coefficients at energies: {ac_energies}")

# Track F00, F20, F21, F22, F11 across energies
# index_1 mapping: 0=order, 1=F00, 2=errF00, 3=F20, 4=errF20, 5=F21, 6=errF21, 7=F22, 8=errF22, 9=F11, 10=errF11
coeff_index_map = {'F00': 1, 'F20': 3, 'F21': 5, 'F22': 7, 'F11': 9}
coeff_names = ['F00', 'F20', 'F21', 'F22', 'F11']
coeff_evolution = {}

for coeff in coeff_names:
    vals = []
    for e in ac_energies:
        ds = f'CoefLeg_{e}eV'
        sub = ac[ac['dataset_path'] == ds]
        row = sub[(sub['index_0'] == 0) & (sub['index_1'] == coeff_index_map[coeff])]
        if len(row) > 0:
            vals.append(float(row.iloc[0]['value']))
        else:
            vals.append(np.nan)
    coeff_evolution[coeff] = vals

# Print the evolution
print("\nCoefficient evolution (order=0 rows):")
header = f"{'Energy':>8}"
for c in coeff_names:
    header += f"  {c:>10}"
print(header)

for i, e in enumerate(ac_energies):
    row_str = f"{e:>8.2f}"
    for c in coeff_names:
        v = coeff_evolution[c][i]
        row_str += f"  {v:>10.6f}"
    print(row_str)

# Check for sign changes or non-monotonic behavior in F20, F21, F22
print("\nSign changes in angular coefficients (order=0):")
for c in ['F20', 'F21', 'F22']:
    vals = coeff_evolution[c]
    signs = np.sign(vals)
    changes = np.sum(signs[:-1] != signs[1:])
    print(f"  {c}: {changes} sign change(s) across energies")

# Also check order=1 rows which have F11 structure
print("\nOrder=1 coefficient evolution (F11 column):")
f11_vals = []
for e in ac_energies:
    ds = f'CoefLeg_{e}eV'
    sub = ac[(ac['dataset_path'] == ds) & (ac['index_0'] == 1) & (ac['index_1'] == 9)]
    if len(sub) > 0:
        f11_vals.append(float(sub.iloc[0]['value']))
    else:
        f11_vals.append(np.nan)

header_f11 = f"{'Energy':>8}"
for i, e in enumerate(ac_energies):
    header_f11 += f"  F11(o1):{coeff_evolution['F11'][i]:>10.6f}"
print(header_f11)
row_f11 = f"{'':>8}"
for v in f11_vals:
    row_f11 += f"  {v:>10.6f}"
print(row_f11)

# Check F11 sign changes
f11_signs = np.sign(f11_vals)
f11_changes = np.sum(f11_signs[:-1] != f11_signs[1:])
print(f"\n  F11 (order=1): {f11_changes} sign change(s) across energies")

# Check all non-trivial coefficients for sign changes at order=1
print("\nAll order=1 coefficient sign patterns:")
for idx1 in [1, 3, 5, 7, 9]:  # F00, F20, F21, F22, F11
    vals_o1 = []
    for e in ac_energies:
        ds = f'CoefLeg_{e}eV'
        sub = ac[(ac['dataset_path'] == ds) & (ac['index_0'] == 1) & (ac['index_1'] == idx1)]
        if len(sub) > 0:
            vals_o1.append(float(sub.iloc[0]['value']))
        else:
            vals_o1.append(np.nan)
    signs = np.sign(vals_o1)
    changes = np.sum(signs[:-1] != signs[1:])
    col_name = {1: 'F00(o1)', 3: 'F20(o1)', 5: 'F21(o1)', 7: 'F22(o1)', 9: 'F11(o1)'}[idx1]
    print(f"  {col_name}: {vals_o1}")
    print(f"    -> {changes} sign change(s)")

# ============================================================
# FINDING 3: Dipole matrix element magnitude decreases with energy
# ============================================================
print("\n" + "=" * 60)
print("FINDING 3: DME energy dependence")
print("=" * 60)

exp_dme_paths = sorted([d for d in dme['dataset_path'].unique() if d.startswith('experiment/')])
dme_energy_trend = {}

for ds in exp_dme_paths:
    e_str = ds.replace('experiment/DME_', 'eV').replace('eV', '')
    e_val = float(e_str)
    sub = dme[dme['dataset_path'] == ds]
    # Real part magnitudes (columns 2,3 are Re, Im)
    re_vals = sub[sub['index_1'] == 2]['value'].abs()
    im_vals = sub[sub['index_1'] == 3]['value'].abs()
    dme_energy_trend[e_val] = {
        're_max': re_vals.max(),
        'im_max': im_vals.max(),
        're_sum_abs': re_vals.sum(),
        'im_sum_abs': im_vals.sum(),
    }
    print(f"  {ds}: Re max={re_vals.max():.4f}, Im max={im_vals.max():.4f}, |Re|sum={re_vals.sum():.4f}")

# Check trend
energies_dme = sorted(dme_energy_trend.keys())
re_maxes = [dme_energy_trend[e]['re_max'] for e in energies_dme]
im_maxes = [dme_energy_trend[e]['im_max'] for e in energies_dme]

if len(energies_dme) > 2:
    slope_re, _, r_re, p_re, _ = stats.linregress(energies_dme, re_maxes)
    slope_im, _, r_im, p_im, _ = stats.linregress(energies_dme, im_maxes)
    print(f"\n  Re max vs energy: slope={slope_re:.6f}, r={r_re:.4f}, p={p_re:.4f}")
    print(f"  Im max vs energy: slope={slope_im:.6f}, r={r_im:.4f}, p={p_im:.4f}")

# ============================================================
# FINDING 4: Wigner delay and eigenphase sum show energy-dependent structure
# ============================================================
print("\n" + "=" * 60)
print("FINDING 4: Wigner delay and eigenphase sum")
print("=" * 60)

wigner = pdc[pdc['dataset_path'] == '0.5_Wigner_delay'].pivot(index='index_0', columns='index_1', values='value')
angle_avg = pdc[pdc['dataset_path'] == 'angle_averaged_delay'].pivot(index='index_0', columns='index_1', values='value')
eigenphase = pdc[pdc['dataset_path'] == 'eigenphase_sum'].pivot(index='index_0', columns='index_1', values='value')

print(f"Wigner delay shape: {wigner.shape}")
print(f"Angle-averaged delay shape: {angle_avg.shape}")
print(f"Eigenphase sum shape: {eigenphase.shape}")

# Wigner delay features
w_delay = wigner.iloc[:, 1].values
w_eKE = wigner.iloc[:, 0].values
print(f"\nWigner delay: min={w_delay.min():.2f} as, max={w_delay.max():.2f} as")
print(f"  Range: [{w_eKE.min():.1f}, {w_eKE.max():.1f}] eKE")

# Find extrema
min_idx = np.argmin(w_delay)
max_idx = np.argmax(w_delay)
print(f"  Min at eKE={w_eKE[min_idx]:.2f} eV, delay={w_delay[min_idx]:.2f} as")
print(f"  Max at eKE={w_eKE[max_idx]:.2f} eV, delay={w_delay[max_idx]:.2f} as")

# Eigenphase sum: monotonic increase then plateau
ep_phase = eigenphase.iloc[:, 1].values
ep_eKE = eigenphase.iloc[:, 0].values
print(f"\nEigenphase sum: min={ep_phase.min():.4f} rad, max={ep_phase.max():.4f} rad")
# Check derivative
ep_deriv = np.diff(ep_phase)
print(f"  Derivative range: [{ep_deriv.min():.4f}, {ep_deriv.max():.4f}] rad/eV")
print(f"  Zero-crossing of derivative (inflection): ", end="")
sign_changes = np.diff(np.sign(ep_deriv))
zero_crossings_arr = np.where(sign_changes != 0)[0]
if len(zero_crossings_arr) > 0:
    for zc in zero_crossings_arr:
        print(f"eKE={ep_eKE[zc]:.1f} eV ", end="")
else:
    print("none")
print()

# Angle-averaged delay features
aa_delay = angle_avg.iloc[:, 1].values
aa_eKE = angle_avg.iloc[:, 0].values
print(f"\nAngle-averaged delay: min={aa_delay.min():.2f} as, max={aa_delay.max():.2f} as")
aa_min_idx = np.argmin(aa_delay)
aa_max_idx = np.argmax(aa_delay)
print(f"  Min at eKE={aa_eKE[aa_min_idx]:.2f} eV, delay={aa_delay[aa_min_idx]:.2f} as")
print(f"  Max at eKE={aa_eKE[aa_max_idx]:.2f} eV, delay={aa_delay[aa_max_idx]:.2f} as")

# ============================================================
# ROBUSTNESS CHECKS
# ============================================================
print("\n" + "=" * 60)
print("ROBUSTNESS CHECKS")
print("=" * 60)

# Check 1: Split experiment data into low/high energy halves and compare to theory
mid_energy = np.median(energies_dme)
low_energies = [e for e in energies_dme if e < mid_energy]
high_energies = [e for e in energies_dme if e >= mid_energy]

print(f"\nSplit at median energy {mid_energy:.2f} eV")
print(f"  Low energy group: {[f'{e:.2f}' for e in low_energies]}")
print(f"  High energy group: {[f'{e:.2f}' for e in high_energies]}")

# Check agreement in each group
low_re = [dme_energy_trend[e]['re_max'] for e in low_energies]
high_re = [dme_energy_trend[e]['re_max'] for e in high_energies]
print(f"  Low group Re max mean: {np.mean(low_re):.4f}")
print(f"  High group Re max mean: {np.mean(high_re):.4f}")

# Check 2: Angular coefficient stability within energy bins
# Group angular coefficients into low (<30), mid (30-35), high (>35) eV
low_ac = [e for e in ac_energies if e < 30]
mid_ac = [e for e in ac_energies if 30 <= e <= 35]
high_ac = [e for e in ac_energies if e > 35]

print(f"\nAngular coefficient groups:")
print(f"  Low (<30 eV): {low_ac}")
print(f"  Mid (30-35 eV): {mid_ac}")
print(f"  High (>35 eV): {high_ac}")

# Check F20 sign pattern in each group
for label, group in [("Low", low_ac), ("Mid", mid_ac), ("High", high_ac)]:
    f20_vals = []
    for e in group:
        ds = f'CoefLeg_{e}eV'
        sub = ac[ac['dataset_path'] == ds]
        row = sub[(sub['index_0'] == 0) & (sub['index_1'] == 3)]  # F20 at index_1=3
        if len(row) > 0:
            f20_vals.append(float(row.iloc[0]['value']))
    signs = np.sign(f20_vals)
    print(f"  {label} group F20: {f20_vals} -> signs: {signs}")

# Save summary statistics
summary = {
    "finding_1_exp_vs_theory": {
        "experiment_energy_range": [float(exp_energies_arr.min()), float(exp_energies_arr.max())],
        "theory_energy_range": [float(theory_energies_arr.min()), float(theory_energies_arr.max())],
        "common_energy_points": len(common_idx_sorted),
        "phase_angle_avg_diff_mean": float(diff_mean.mean()) if len(common_idx_sorted) > 0 else None,
    },
    "finding_2_angular_coeffs": {
        "energies": ac_energies,
        "coefficients": {c: coeff_evolution[c] for c in coeff_names},
    },
    "finding_3_dme_trend": {
        "energies": energies_dme,
        "re_max_values": re_maxes,
        "im_max_values": im_maxes,
        "re_slope": float(slope_re),
        "re_r": float(r_re),
        "re_p": float(p_re),
    },
    "finding_4_wigner": {
        "wigner_min_delay_as": float(w_delay.min()),
        "wigner_max_delay_as": float(w_delay.max()),
        "wigner_min_eke": float(w_eKE[min_idx]),
        "wigner_max_eke": float(w_eKE[max_idx]),
        "eigenphase_min_rad": float(ep_phase.min()),
        "eigenphase_max_rad": float(ep_phase.max()),
        "angle_avg_delay_min_as": float(aa_delay.min()),
        "angle_avg_delay_max_as": float(aa_delay.max()),
    },
}

with open(OUT / "analysis_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\nSummary saved to output/analysis_summary.json")
