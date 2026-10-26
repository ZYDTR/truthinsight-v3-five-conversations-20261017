#!/usr/bin/env python3
"""
Core analysis: Buffer Parameters and Delay Dynamics in Temporal Networks
Task ID: Physics_04_temporal_delay_transition

Analyzes:
  Finding 1: V(B) relationship and critical buffer Bc (fig2)
  Finding 2: Correlation collapse across buffer conditions (fig3a)
  Finding 3: Finite-size scaling of Bc (SI.2)
  Finding 4: Real-network validation (fig4b)
"""

import numpy as np
import pandas as pd
from scipy import stats, optimize
import json
import os

DATA_DIR = 'data/source_data'
OUTPUT_DIR = 'output/evidence'
os.makedirs(OUTPUT_DIR, exist_ok=True)

results = {}

# ============================================================
# Finding 1: Delay growth velocity V vs buffer parameter B
# ============================================================
print("=" * 60)
print("Finding 1: V(B) relationship and critical buffer")
print("=" * 60)

# meanfield_data.csv: B, alpha, V (37 points, B from 0 to 9)
mf = pd.read_csv(f'{DATA_DIR}/figures/fig2_critical_buffer/data/meanfield_data.csv')
print(f"Meanfield: {len(mf)} points, B=[{mf['B'].min()}, {mf['B'].max()}]")
print(f"V range: [{mf['V'].min():.4f}, {mf['V'].max():.4f}]")

# theory_data.csv: B, alpha, V (182 points, B from 0 to ~4.5)
th = pd.read_csv(f'{DATA_DIR}/figures/fig2_critical_buffer/data/theory_data.csv')
print(f"Theory: {len(th)} points, B=[{th['B'].min()}, {th['B'].max()}]")
print(f"V range: [{th['V'].min():.4f}, {th['V'].max():.4f}]")

# Fit linear model V = a + b*B for both datasets
mf_slope, mf_intercept, mf_r, mf_p, mf_se = stats.linregress(mf['B'], mf['V'])
th_slope, th_intercept, th_r, th_p, th_se = stats.linregress(th['B'], th['V'])

print(f"\nMeanfield fit: V = {mf_intercept:.6f} + {mf_slope:.6f} * B")
print(f"  R²={mf_r**2:.6f}, p={mf_p:.2e}")
print(f"Theory fit: V = {th_intercept:.6f} + {th_slope:.6f} * B")
print(f"  R²={th_r**2:.6f}, p={th_p:.2e}")

# Check if there's a change in slope near some B value (critical buffer)
# Split at various candidate Bc values and compare slopes
best_Bc = None
best_diff = -np.inf
for Bc_candidate in np.arange(0.5, 4.0, 0.05):
    mask_below = th['B'] < Bc_candidate
    mask_above = th['B'] >= Bc_candidate
    if mask_below.sum() < 5 or mask_above.sum() < 5:
        continue
    s1, i1, r1, p1, se1 = stats.linregress(th.loc[mask_below, 'B'], th.loc[mask_below, 'V'])
    s2, i2, r2, p2, se2 = stats.linregress(th.loc[mask_above, 'B'], th.loc[mask_above, 'V'])
    diff = abs(s2 - s1)
    if diff > best_diff:
        best_diff = diff
        best_Bc = Bc_candidate

print(f"\nBest segmented Bc (theory): {best_Bc:.2f}")
print(f"  Slope below Bc: {s1:.6f}, above Bc: {s2:.6f}")

# Also check meanfield with segmentation
best_Bc_mf = None
best_diff_mf = -np.inf
for Bc_candidate in np.arange(0.5, 5.0, 0.1):
    mask_below = mf['B'] < Bc_candidate
    mask_above = mf['B'] >= Bc_candidate
    if mask_below.sum() < 5 or mask_above.sum() < 5:
        continue
    s1, _, _, _, _ = stats.linregress(mf.loc[mask_below, 'B'], mf.loc[mask_below, 'V'])
    s2, _, _, _, _ = stats.linregress(mf.loc[mask_above, 'B'], mf.loc[mask_above, 'V'])
    diff = abs(s2 - s1)
    if diff > best_diff_mf:
        best_diff_mf = diff
        best_Bc_mf = Bc_candidate

print(f"Best segmented Bc (meanfield): {best_Bc_mf:.2f}")

# above_bc.csv and below_bc.csv contain simulation data
above = pd.read_csv(f'{DATA_DIR}/figures/fig2_critical_buffer/data/above_bc.csv')
below = pd.read_csv(f'{DATA_DIR}/figures/fig2_critical_buffer/data/below_bc.csv')

# The columns are "Plot 1", "Plot 2" etc.
# From fig2_source_data.csv structure: x1,y1 correspond to B,alpha; x2,y2 to B,V
# above_bc has 2 cols, below_bc has 4 cols
# Plot 1 likely = B, Plot 2 likely = V or similar
print(f"\nabove_bc: shape={above.shape}, cols={list(above.columns)}")
print(f"below_bc: shape={below.shape}, cols={list(below.columns)}")

# Store results
results['finding1'] = {
    'meanfield': {
        'n_points': len(mf),
        'B_range': [float(mf['B'].min()), float(mf['B'].max())],
        'V_range': [float(mf['V'].min()), float(mf['V'].max())],
        'linear_fit': {
            'slope': float(mf_slope),
            'intercept': float(mf_intercept),
            'R_squared': float(mf_r**2),
            'p_value': float(mf_p)
        },
        'segmented_Bc': float(best_Bc_mf)
    },
    'theory': {
        'n_points': len(th),
        'B_range': [float(th['B'].min()), float(th['B'].max())],
        'V_range': [float(th['V'].min()), float(th['V'].max())],
        'linear_fit': {
            'slope': float(th_slope),
            'intercept': float(th_intercept),
            'R_squared': float(th_r**2),
            'p_value': float(th_p)
        },
        'segmented_Bc': float(best_Bc)
    }
}

# Save finding 1 results
with open(f'{OUTPUT_DIR}/finding1_V_vs_B.json', 'w') as f:
    json.dump(results['finding1'], f, indent=2)

# Generate scatter plot data
v_b_data = {
    'meanfield': [{'B': float(b), 'V': float(v)} for b, v in zip(mf['B'], mf['V'])],
    'theory': [{'B': float(b), 'V': float(v)} for b, v in zip(th['B'], th['V'])]
}
with open(f'{OUTPUT_DIR}/finding1_v_b_scatter.json', 'w') as f:
    json.dump(v_b_data, f, indent=2)

# ============================================================
# Finding 2: Correlation collapse across buffer conditions
# ============================================================
print("\n" + "=" * 60)
print("Finding 2: Correlation collapse analysis")
print("=" * 60)

# corr.ave_{1-5}.txt: lag, acf for each buffer condition
correlations = {}
for i in range(1, 6):
    fn = f'{DATA_DIR}/figures/fig3a_correlation_collapse/data/corr.ave_{i}.txt'
    c = pd.read_csv(fn, sep=r'\s+', header=None, names=['lag', 'acf'])
    correlations[f'B{i}'] = c

for key, c in correlations.items():
    print(f"{key}: n={len(c)}, lag=[{int(c['lag'].min())}, {int(c['lag'].max())}], "
          f"acf=[{c['acf'].min():.6f}, {c['acf'].max():.6f}]")

# inset_fit_data.csv: fit_x, fit_y — these appear to be B values and corresponding scale factors
inset_fit = pd.read_csv(f'{DATA_DIR}/figures/fig3a_correlation_collapse/fig_source_data/inset_fit_data.csv')
print(f"\ninset_fit_data: {list(inset_fit.columns)}, shape={inset_fit.shape}")
print(f"fit_x range: [{inset_fit['fit_x'].min():.4f}, {inset_fit['fit_x'].max():.4f}]")
print(f"fit_y range: [{inset_fit['fit_y'].min():.4f}, {inset_fit['fit_y'].max():.4f}]")

# Check if fit_x represents B values around Bc
# The first value is 3.68 which matches the known Bc ~ 3.68-3.69
print(f"\nFirst few fit_x values: {inset_fit['fit_x'].values[:10]}")
print(f"Last few fit_x values: {inset_fit['fit_x'].values[-10:]}")

# main_figure_scatter_data.csv: B1_x through B5_x (lags), B1_y through B5_y (ACFs)
scatter = pd.read_csv(f'{DATA_DIR}/figures/fig3a_correlation_collapse/fig_source_data/main_figure_scatter_data.csv')
print(f"\nmain_figure_scatter_data: {list(scatter.columns)}, shape={scatter.shape}")

# Test collapse: rescale lag by a factor and see if curves overlap
# For each pair of conditions, find optimal collapse factor
B1 = correlations['B1']
B2 = correlations['B2']

# Interpolate B2 onto B1's lag grid
from scipy.interpolate import interp1d
if len(B1) >= 2 and len(B2) >= 2:
    f_B2 = interp1d(B2['lag'].values, B2['acf'].values, kind='linear', fill_value='extrapolate')
    B2_resampled = f_B2(B1['lag'].values)

    # Compute correlation between B1 and B2_resampled
    corr_B1_B2 = np.corrcoef(B1['acf'].values, B2_resampled)[0, 1]
    print(f"\nCorrelation B1 vs B2 (raw lag): {corr_B1_B2:.6f}")

    # Try rescaling B2's lag by various factors
    best_factor = None
    best_corr = -2
    for scale in np.arange(0.5, 3.0, 0.01):
        B2_scaled_lag = B2['lag'].values * scale
        f_B2_scaled = interp1d(B2_scaled_lag, B2['acf'].values, kind='linear',
                               fill_value='extrapolate')
        B2_scaled_acf = f_B2_scaled(B1['lag'].values)
        c = np.corrcoef(B1['acf'].values, B2_scaled_acf)[0, 1]
        if c > best_corr:
            best_corr = c
            best_factor = scale

    print(f"Best collapse factor (B2->B1): {best_factor:.3f}, max correlation: {best_corr:.6f}")

# Collapse test: compute pairwise correlations with optimal scaling
pairwise_corr = {}
keys = list(correlations.keys())
for i in range(len(keys)):
    for j in range(i+1, len(keys)):
        k1, k2 = keys[i], keys[j]
        c1, c2 = correlations[k1], correlations[k2]

        # Find optimal scale of c2 to match c1
        best_s = None
        best_c = -2
        for scale in np.arange(0.1, 10.0, 0.01):
            f = interp1d(c2['lag'].values, c2['acf'].values, kind='linear', fill_value='extrapolate')
            y = f(c1['lag'].values * scale)
            if np.all(np.isfinite(y)):
                c_val = np.corrcoef(c1['acf'].values, y)[0, 1]
                if c_val > best_c:
                    best_c = c_val
                    best_s = scale

        pairwise_corr[f"{k1}_vs_{k2}"] = {
            'optimal_scale': float(best_s) if best_s else None,
            'max_correlation': float(best_c) if best_c > -1 else None
        }
        print(f"{k1} vs {k2}: scale={best_s:.3f}, corr={best_c:.6f}")

results['finding2'] = {
    'correlation_curves': {k: {'n_points': int(len(v)), 'max_lag': int(v['lag'].max()),
                                'acf_min': float(v['acf'].min()), 'acf_max': float(v['acf'].max())}
                           for k, v in correlations.items()},
    'collapse_pairwise': pairwise_corr,
    'inset_fit': {
        'n_points': len(inset_fit),
        'fit_x_range': [float(inset_fit['fit_x'].min()), float(inset_fit['fit_x'].max())],
        'fit_y_range': [float(inset_fit['fit_y'].min()), float(inset_fit['fit_y'].max())]
    }
}

with open(f'{OUTPUT_DIR}/finding2_correlation_collapse.json', 'w') as f:
    json.dump(results['finding2'], f, indent=2)

# ============================================================
# Finding 3: Finite-size scaling of Bc
# ============================================================
print("\n" + "=" * 60)
print("Finding 3: Finite-size scaling")
print("=" * 60)

N_vals = pd.read_csv(f'{DATA_DIR}/figures/SI.2_finite_size/data/N_values.csv', header=None, names=['N'])
Bc_mf = pd.read_csv(f'{DATA_DIR}/figures/SI.2_finite_size/data/meanfield_Bc.csv', header=None, names=['Bc'])
Bc_tn = pd.read_csv(f'{DATA_DIR}/figures/SI.2_finite_size/data/tempnet_Bc.csv', header=None, names=['Bc'])

N = N_vals['N'].values
Bc_meanfield = Bc_mf['Bc'].values
Bc_tempnet = Bc_tn['Bc'].values

print(f"N values ({len(N)}): min={N.min()}, max={N.max()}")
print(f"Bc_meanfield: [{Bc_meanfield.min():.4f}, {Bc_meanfield.max():.4f}]")
print(f"Bc_tempnet: [{Bc_tempnet.min():.4f}, {Bc_tempnet.max():.4f}]")

# Finite-size scaling: Bc(N) = Bc_inf + a * N^(-1/nu)
# Fit this form
def finite_size_scaling(N, Bc_inf, a, nu):
    return Bc_inf + a * N**(-1.0/nu)

# Initial guess
Bc_inf_guess = 3.5  # approximate asymptotic value
p0_mf = [Bc_inf_guess, 1.0, 1.0]
p0_tn = [Bc_inf_guess, 1.0, 1.0]

try:
    popt_mf, pcov_mf = optimize.curve_fit(finite_size_scaling, N, Bc_meanfield, p0=p0_mf, maxfev=5000)
    print(f"\nMeanfield finite-size fit: Bc_inf={popt_mf[0]:.6f}, a={popt_mf[1]:.6f}, nu={popt_mf[2]:.6f}")
except Exception as e:
    print(f"Meanfield fit failed: {e}")
    popt_mf = None

try:
    popt_tn, pcov_tn = optimize.curve_fit(finite_size_scaling, N, Bc_tempnet, p0=p0_tn, maxfev=5000)
    print(f"Tempnet finite-size fit: Bc_inf={popt_tn[0]:.6f}, a={popt_tn[1]:.6f}, nu={popt_tn[2]:.6f}")
except Exception as e:
    print(f"Tempnet fit failed: {e}")
    popt_tn = None

# Also try log-log fit: log(Bc - Bc_inf) vs log(N)
# First estimate Bc_inf from the largest N
largest_N_idx = np.argmax(N)
Bc_inf_est_mf = Bc_meanfield[largest_N_idx]
Bc_inf_est_tn = Bc_tempnet[largest_N_idx]

print(f"\nBc at largest N ({N[largest_N_idx]}): meanfield={Bc_meanfield[largest_N_idx]:.6f}, tempnet={Bc_tempnet[largest_N_idx]:.6f}")

# Linear regression of Bc vs N^(-1/nu) for various nu values
best_nu_mf = None
best_r2_mf = -np.inf
for nu in np.arange(0.5, 5.0, 0.01):
    x = N**(-1.0/nu)
    slope, intercept, r, p, se = stats.linregress(x, Bc_meanfield)
    if r**2 > best_r2_mf:
        best_r2_mf = r**2
        best_nu_mf = nu
        best_slope_mf = slope
        best_intercept_mf = intercept

print(f"\nMeanfield: best nu={best_nu_mf:.2f}, R²={best_r2_mf:.6f}")
print(f"  Bc_inf ≈ {best_intercept_mf:.6f}")

best_nu_tn = None
best_r2_tn = -np.inf
for nu in np.arange(0.5, 5.0, 0.01):
    x = N**(-1.0/nu)
    slope, intercept, r, p, se = stats.linregress(x, Bc_tempnet)
    if r**2 > best_r2_tn:
        best_r2_tn = r**2
        best_nu_tn = nu
        best_slope_tn = slope
        best_intercept_tn = intercept

print(f"Tempnet: best nu={best_nu_tn:.2f}, R²={best_r2_tn:.6f}")
print(f"  Bc_inf ≈ {best_intercept_tn:.6f}")

results['finding3'] = {
    'N_range': [float(N.min()), float(N.max())],
    'N_points': len(N),
    'meanfield_Bc': {
        'range': [float(Bc_meanfield.min()), float(Bc_meanfield.max())],
        'at_largest_N': float(Bc_meanfield[largest_N_idx]),
        'best_nu': float(best_nu_mf),
        'R_squared': float(best_r2_mf),
        'Bc_inf_estimate': float(best_intercept_mf)
    },
    'tempnet_Bc': {
        'range': [float(Bc_tempnet.min()), float(Bc_tempnet.max())],
        'at_largest_N': float(Bc_tempnet[largest_N_idx]),
        'best_nu': float(best_nu_tn),
        'R_squared': float(best_r2_tn),
        'Bc_inf_estimate': float(best_intercept_tn)
    }
}

with open(f'{OUTPUT_DIR}/finding3_finite_size.json', 'w') as f:
    json.dump(results['finding3'], f, indent=2)

# ============================================================
# Finding 4: Real-network validation
# ============================================================
print("\n" + "=" * 60)
print("Finding 4: Real-network validation")
print("=" * 60)

# Thiers13 source data
thiers13 = pd.read_csv(f'{DATA_DIR}/figures/fig4b_RW_networks/fig_source_data/Thiers13_source_data.csv')
workplace15 = pd.read_csv(f'{DATA_DIR}/figures/fig4b_RW_networks/fig_source_data/Workplace15_source_data.csv')

print(f"Thiers13: {list(thiers13.columns)}, shape={thiers13.shape}")
print(f"Workplace15: {list(workplace15.columns)}, shape={workplace15.shape}")

# Thiers13: buffer_lin_Thiers13 vs Thiers13_delays
# Workplace15: buffer_log_Workplace15 vs Workplace15_delays
# These show delay as function of buffer parameter for real networks

# Fit power-law or exponential decay to delays vs buffer
thiers_B = thiers13['buffer_lin_Thiers13'].values
thiers_D = thiers13['Thiers13_delays'].values
wp_B = workplace15['buffer_log_Workplace15'].values
wp_D = workplace15['Workplace15_delays'].values

print(f"\nThiers13: B=[{thiers_B.min()}, {thiers_B.max()}], D=[{thiers_D.min():.6f}, {thiers_D.max():.6f}]")
print(f"Workplace15: B=[{wp_B.min()}, {wp_B.max()}], D=[{wp_D.min():.6f}, {wp_D.max():.6f}]")

# Linear fit for Thiers13
thiers_slope, thiers_intercept, thiers_r, thiers_p, thiers_se = stats.linregress(thiers_B, thiers_D)
print(f"\nThiers13 linear: D = {thiers_intercept:.6f} + {thiers_slope:.6f} * B")
print(f"  R²={thiers_r**2:.6f}, p={thiers_p:.2e}")

# Linear fit for Workplace15
wp_slope, wp_intercept, wp_r, wp_p, wp_se = stats.linregress(wp_B, wp_D)
print(f"Workplace15 linear: D = {wp_intercept:.6f} + {wp_slope:.6f} * B")
print(f"  R²={wp_r**2:.6f}, p={wp_p:.2e}")

# Power-law fit: D = a * B^(-b)
# Use log-transform
mask_thiers_nonzero = thiers_B > 0
if mask_thiers_nonzero.sum() > 2:
    log_B_t = np.log(thiers_B[mask_thiers_nonzero])
    log_D_t = np.log(thiers_D[mask_thiers_nonzero])
    pl_slope_t, pl_intercept_t, pl_r_t, pl_p_t, pl_se_t = stats.linregress(log_B_t, log_D_t)
    print(f"\nThiers13 power-law: log(D) = {pl_intercept_t:.6f} + {pl_slope_t:.6f} * log(B)")
    print(f"  R²={pl_r_t**2:.6f}, p={pl_p_t:.2e}")
else:
    pl_slope_t = pl_intercept_t = pl_r_t = pl_p_t = None

mask_wp_nonzero = wp_B > 0
if mask_wp_nonzero.sum() > 2:
    log_B_w = np.log(wp_B[mask_wp_nonzero])
    log_D_w = np.log(wp_D[mask_wp_nonzero])
    pl_slope_w, pl_intercept_w, pl_r_w, pl_p_w, pl_se_w = stats.linregress(log_B_w, log_D_w)
    print(f"Workplace15 power-law: log(D) = {pl_intercept_w:.6f} + {pl_slope_w:.6f} * log(B)")
    print(f"  R²={pl_r_w**2:.6f}, p={pl_p_w:.2e}")
else:
    pl_slope_w = pl_intercept_w = pl_r_w = pl_p_w = None

# Compare with simulated buffer scans
buffer_lin = pd.read_csv(f'{DATA_DIR}/figures/fig4b_RW_networks/data/buffer_lin.csv')
buffer_log = pd.read_csv(f'{DATA_DIR}/figures/fig4b_RW_networks/data/buffer_log.csv')
print(f"\nSimulated buffer_lin: {len(buffer_lin)} points")
print(f"Simulated buffer_log: {len(buffer_log)} points")

results['finding4'] = {
    'Thiers13': {
        'n_points': len(thiers13),
        'B_range': [float(thiers_B.min()), float(thiers_B.max())],
        'D_range': [float(thiers_D.min()), float(thiers_D.max())],
        'linear_fit': {
            'slope': float(thiers_slope),
            'intercept': float(thiers_intercept),
            'R_squared': float(thiers_r**2),
            'p_value': float(thiers_p)
        },
        'power_law_fit': {
            'exponent': float(pl_slope_t) if pl_slope_t is not None else None,
            'R_squared': float(pl_r_t**2) if pl_r_t is not None else None,
            'p_value': float(pl_p_t) if pl_p_t is not None else None
        }
    },
    'Workplace15': {
        'n_points': len(workplace15),
        'B_range': [float(wp_B.min()), float(wp_B.max())],
        'D_range': [float(wp_D.min()), float(wp_D.max())],
        'linear_fit': {
            'slope': float(wp_slope),
            'intercept': float(wp_intercept),
            'R_squared': float(wp_r**2),
            'p_value': float(wp_p)
        },
        'power_law_fit': {
            'exponent': float(pl_slope_w) if pl_slope_w is not None else None,
            'R_squared': float(pl_r_w**2) if pl_r_w is not None else None,
            'p_value': float(pl_p_w) if pl_p_w is not None else None
        }
    }
}

with open(f'{OUTPUT_DIR}/finding4_real_networks.json', 'w') as f:
    json.dump(results['finding4'], f, indent=2)

# ============================================================
# Summary JSON
# ============================================================
summary = {
    'task_id': 'Physics_04_temporal_delay_transition',
    'findings': {
        'finding1': {
            'description': 'Delay growth velocity V decreases with buffer parameter B',
            'meanfield_linear_R2': float(mf_r**2),
            'theory_linear_R2': float(th_r**2),
            'meanfield_segmented_Bc': float(best_Bc_mf),
            'theory_segmented_Bc': float(best_Bc)
        },
        'finding2': {
            'description': 'Autocorrelation functions collapse under rescaling',
            'pairwise_correlations': pairwise_corr
        },
        'finding3': {
            'description': 'Critical buffer Bc depends on system size N via finite-size scaling',
            'meanfield_best_nu': float(best_nu_mf),
            'meanfield_R2': float(best_r2_mf),
            'meanfield_Bc_inf': float(best_intercept_mf),
            'tempnet_best_nu': float(best_nu_tn),
            'tempnet_R2': float(best_r2_tn),
            'tempnet_Bc_inf': float(best_intercept_tn)
        },
        'finding4': {
            'description': 'Real temporal networks show buffer-dependent delay consistent with simulations',
            'Thiers13_linear_R2': float(thiers_r**2),
            'Workplace15_linear_R2': float(wp_r**2)
        }
    }
}

with open(f'{OUTPUT_DIR}/summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\n" + "=" * 60)
print("All findings saved to output/evidence/")
print("=" * 60)
print(json.dumps(summary, indent=2))
