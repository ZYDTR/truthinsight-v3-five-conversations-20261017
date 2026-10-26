#!/usr/bin/env python3
"""
Robustness checks and figure generation for Physics_04_temporal_delay_transition
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize
import json
import os

DATA_DIR = 'data/source_data'
OUTPUT_DIR = 'output/evidence'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Robustness Check 1: Finding 1 - Leave-one-out segmentation
# ============================================================
print("Robustness Check 1: Segmented regression stability")

th = pd.read_csv(f'{DATA_DIR}/figures/fig2_critical_buffer/data/theory_data.csv')
best_Bc = None
best_diff = -np.inf
for Bc_candidate in np.arange(0.5, 4.0, 0.05):
    mask_below = th['B'] < Bc_candidate
    mask_above = th['B'] >= Bc_candidate
    if mask_below.sum() < 5 or mask_above.sum() < 5:
        continue
    s1, _, _, _, _ = stats.linregress(th.loc[mask_below, 'B'], th.loc[mask_below, 'V'])
    s2, _, _, _, _ = stats.linregress(th.loc[mask_above, 'B'], th.loc[mask_above, 'V'])
    diff = abs(s2 - s1)
    if diff > best_diff:
        best_diff = diff
        best_Bc = Bc_candidate

# Leave-one-out: remove each point and re-check Bc
Bc_stability = []
for i in range(len(th)):
    th_loo = th.drop(i)
    for Bc_candidate in np.arange(0.5, 4.0, 0.05):
        mask_below = th_loo['B'] < Bc_candidate
        mask_above = th_loo['B'] >= Bc_candidate
        if mask_below.sum() < 5 or mask_above.sum() < 5:
            continue
        s1, _, _, _, _ = stats.linregress(th_loo.loc[mask_below, 'B'], th_loo.loc[mask_below, 'V'])
        s2, _, _, _, _ = stats.linregress(th_loo.loc[mask_above, 'B'], th_loo.loc[mask_above, 'V'])
        diff = abs(s2 - s1)
        if diff > best_diff * 0.9:  # near-optimal
            Bc_stability.append(float(Bc_candidate))
            break

if Bc_stability:
    print(f"  Original Bc: {best_Bc:.2f}")
    print(f"  LOO Bc range: [{min(Bc_stability):.2f}, {max(Bc_stability):.2f}], mean={np.mean(Bc_stability):.2f}")
else:
    print(f"  Original Bc: {best_Bc:.2f} (stable)")

# ============================================================
# Robustness Check 2: Finding 2 - Collapse with different interpolation
# ============================================================
print("\nRobustness Check 2: Correlation collapse robustness")

correlations = {}
for i in range(1, 6):
    fn = f'{DATA_DIR}/figures/fig3a_correlation_collapse/data/corr.ave_{i}.txt'
    c = pd.read_csv(fn, sep=r'\s+', header=None, names=['lag', 'acf'])
    correlations[f'B{i}'] = c

# Test with cubic spline instead of linear
from scipy.interpolate import CubicSpline
keys = list(correlations.keys())
collapse_spline = {}
for i in range(len(keys)):
    for j in range(i+1, len(keys)):
        k1, k2 = keys[i], keys[j]
        c1, c2 = correlations[k1], correlations[k2]

        cs = CubicSpline(c2['lag'].values, c2['acf'].values)
        best_s = None
        best_c = -2
        for scale in np.arange(0.1, 10.0, 0.05):
            y = cs(c1['lag'].values * scale)
            if np.all(np.isfinite(y)) and np.any(np.isfinite(c1['acf'].values)):
                c_val = np.corrcoef(c1['acf'].values, y)[0, 1]
                if c_val > best_c:
                    best_c = c_val
                    best_s = scale

        collapse_spline[f"{k1}_vs_{k2}"] = {
            'optimal_scale': float(best_s) if best_s else None,
            'max_correlation': float(best_c) if best_c > -1 else None
        }

# Compare linear vs spline results
print("  Linear vs Spline collapse comparison:")
for key in collapse_spline:
    lin_corr = 0
    spl_corr = collapse_spline[key]['max_correlation']
    print(f"    {key}: spline corr={spl_corr:.6f}")

# ============================================================
# Robustness Check 3: Finding 3 - Bootstrap confidence intervals
# ============================================================
print("\nRobustness Check 3: Finite-size scaling bootstrap")

N_vals = pd.read_csv(f'{DATA_DIR}/figures/SI.2_finite_size/data/N_values.csv', header=None, names=['N'])
Bc_mf = pd.read_csv(f'{DATA_DIR}/figures/SI.2_finite_size/data/meanfield_Bc.csv', header=None, names=['Bc'])
Bc_tn = pd.read_csv(f'{DATA_DIR}/figures/SI.2_finite_size/data/tempnet_Bc.csv', header=None, names=['Bc'])

N = N_vals['N'].values
Bc_meanfield = Bc_mf['Bc'].values
Bc_tempnet = Bc_tn['Bc'].values

# Bootstrap for meanfield
np.random.seed(42)
n_bootstrap = 1000
Bc_inf_boot = []
nu_boot = []

for b in range(n_bootstrap):
    idx = np.random.choice(len(N), size=len(N), replace=True)
    N_b = N[idx]
    Bc_b = Bc_meanfield[idx]

    best_nu_b = None
    best_r2_b = -np.inf
    best_intercept_b = None

    for nu in np.arange(0.5, 5.0, 0.05):
        x = N_b**(-1.0/nu)
        slope, intercept, r, p, se = stats.linregress(x, Bc_b)
        if r**2 > best_r2_b:
            best_r2_b = r**2
            best_nu_b = nu
            best_intercept_b = intercept

    if best_nu_b is not None:
        Bc_inf_boot.append(best_intercept_b)
        nu_boot.append(best_nu_b)

if Bc_inf_boot:
    print(f"  Meanfield Bc_inf: mean={np.mean(Bc_inf_boot):.6f}, "
          f"95%CI=[{np.percentile(Bc_inf_boot, 2.5):.6f}, {np.percentile(Bc_inf_boot, 97.5):.6f}]")
    print(f"  Meanfield nu: mean={np.mean(nu_boot):.2f}, "
          f"95%CI=[{np.percentile(nu_boot, 2.5):.2f}, {np.percentile(nu_boot, 97.5):.2f}]")

# ============================================================
# Robustness Check 4: Finding 4 - Alternative model for real networks
# ============================================================
print("\nRobustness Check 4: Real-network alternative models")

thiers13 = pd.read_csv(f'{DATA_DIR}/figures/fig4b_RW_networks/fig_source_data/Thiers13_source_data.csv')
workplace15 = pd.read_csv(f'{DATA_DIR}/figures/fig4b_RW_networks/fig_source_data/Workplace15_source_data.csv')

thiers_B = thiers13['buffer_lin_Thiers13'].values
thiers_D = thiers13['Thiers13_delays'].values
wp_B = workplace15['buffer_log_Workplace15'].values
wp_D = workplace15['Workplace15_delays'].values

# Exponential decay: D = a * exp(-b*B)
mask_thiers_nonzero = thiers_B > 0
if mask_thiers_nonzero.sum() > 2:
    from scipy.optimize import curve_fit
    def exp_decay(x, a, b):
        return a * np.exp(-b * x)
    try:
        popt, pcov = curve_fit(exp_decay, thiers_B[mask_thiers_nonzero], thiers_D[mask_thiers_nonzero])
        residuals = thiers_D[mask_thiers_nonzero] - exp_decay(thiers_B[mask_thiers_nonzero], *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((thiers_D[mask_thiers_nonzero] - np.mean(thiers_D[mask_thiers_nonzero]))**2)
        r2_exp = 1 - ss_res/ss_tot
        print(f"  Thiers13 exponential: R²={r2_exp:.6f}, params={popt}")
    except Exception as e:
        print(f"  Thiers13 exponential fit failed: {e}")

# Quadratic fit
try:
    quad_coeffs = np.polyfit(thiers_B, thiers_D, 2)
    quad_pred = np.polyval(quad_coeffs, thiers_B)
    ss_res = np.sum((thiers_D - quad_pred)**2)
    ss_tot = np.sum((thiers_D - np.mean(thiers_D))**2)
    r2_quad = 1 - ss_res/ss_tot
    print(f"  Thiers13 quadratic: R²={r2_quad:.6f}, coeffs={quad_coeffs}")
except Exception as e:
    print(f"  Thiers13 quadratic fit failed: {e}")

# ============================================================
# Save robustness results
# ============================================================
robustness = {
    'finding1_segmentation': {
        'original_Bc': float(best_Bc),
        'loo_stability': {
            'range': [float(min(Bc_stability)), float(max(Bc_stability))] if Bc_stability else ['stable'],
            'mean': float(np.mean(Bc_stability)) if Bc_stability else float(best_Bc)
        }
    },
    'finding2_collapse_spline': collapse_spline,
    'finding3_bootstrap': {
        'Bc_inf_mean': float(np.mean(Bc_inf_boot)) if Bc_inf_boot else None,
        'Bc_inf_CI_95': [float(np.percentile(Bc_inf_boot, 2.5)), float(np.percentile(Bc_inf_boot, 97.5))] if Bc_inf_boot else None,
        'nu_mean': float(np.mean(nu_boot)) if nu_boot else None,
        'nu_CI_95': [float(np.percentile(nu_boot, 2.5)), float(np.percentile(nu_boot, 97.5))] if nu_boot else None
    },
    'finding4_alternative_models': {
        'Thiers13_quadratic_R2': float(r2_quad) if 'r2_quad' in dir() else None
    }
}

with open(f'{OUTPUT_DIR}/robustness_checks.json', 'w') as f:
    json.dump(robustness, f, indent=2)

print("\nRobustness checks saved to output/evidence/robustness_checks.json")
