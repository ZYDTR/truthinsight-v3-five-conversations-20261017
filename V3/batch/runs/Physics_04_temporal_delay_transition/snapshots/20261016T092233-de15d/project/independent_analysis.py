#!/usr/bin/env python3
"""Independent replication of Physics_04 temporal delay transition analysis."""

import json
import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar, curve_fit
import os

DATA_DIR = "/data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project/data/source_data"
OUTPUT_DIR = "/data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project/output/evidence_independent"

results = {}

# ============================================================
# Finding 1: V vs B relationship (linear + segmented regression)
# ============================================================
print("=" * 60)
print("FINDING 1: V vs B relationship")
print("=" * 60)

# --- Meanfield data ---
mf_data = np.loadtxt(os.path.join(DATA_DIR, "figures/fig2_critical_buffer/data/meanfield_data.csv"),
                     delimiter=',', skiprows=1)
B_mf = mf_data[:, 0]
V_mf = mf_data[:, 2]

# Full linear fit
slope_mf, intercept_mf, r_mf, p_mf, std_err_mf = stats.linregress(B_mf, V_mf)
print(f"\nMeanfield full linear fit:")
print(f"  slope={slope_mf:.6f}, intercept={intercept_mf:.6f}, R²={r_mf**2:.6f}, p={p_mf:.2e}")

# Segmented regression: find optimal breakpoint near where V drops sharply
# The data shows a sharp drop around B=3.5-4.0
best_breakpoint = None
best_seg_R2 = -np.inf
best_params = None

for bp in np.arange(2.0, 6.0, 0.05):
    mask1 = B_mf <= bp
    mask2 = B_mf > bp
    if mask1.sum() < 2 or mask2.sum() < 2:
        continue
    # Two separate linear fits
    s1, i1, r1, p1, _ = stats.linregress(B_mf[mask1], V_mf[mask1])
    s2, i2, r2, p2, _ = stats.linregress(B_mf[mask2], V_mf[mask2])
    # Compute combined R²
    y_pred = np.where(mask1, s1 * B_mf + i1, s2 * B_mf + i2)
    ss_res = np.sum((V_mf - y_pred)**2)
    ss_tot = np.sum((V_mf - np.mean(V_mf))**2)
    seg_r2 = 1 - ss_res / ss_tot
    if seg_r2 > best_seg_R2:
        best_seg_R2 = seg_r2
        best_breakpoint = bp
        best_params = (s1, i1, s2, i2)

print(f"\nMeanfield segmented regression:")
print(f"  breakpoint_Bc={best_breakpoint:.2f}")
print(f"  segment1: slope={best_params[0]:.6f}, intercept={best_params[1]:.6f}")
print(f"  segment2: slope={best_params[2]:.6f}, intercept={best_params[3]:.6f}")
print(f"  segmented R²={best_seg_R2:.6f}")

# --- Theory data ---
th_data = np.loadtxt(os.path.join(DATA_DIR, "figures/fig2_critical_buffer/data/theory_data.csv"),
                     delimiter=',', skiprows=1)
B_th = th_data[:, 0]
V_th = th_data[:, 2]

# Only fit the non-zero portion for theory (before V becomes exactly 0)
nonzero_mask = V_th > 0
B_th_nz = B_th[nonzero_mask]
V_th_nz = V_th[nonzero_mask]

slope_th, intercept_th, r_th, p_th, std_err_th = stats.linregress(B_th_nz, V_th_nz)
print(f"\nTheory (non-zero) linear fit:")
print(f"  slope={slope_th:.6f}, intercept={intercept_th:.6f}, R²={r_th**2:.6f}, p={p_th:.2e}")

# Segmented regression for theory
best_bp_th = None
best_seg_R2_th = -np.inf
best_params_th = None

for bp in np.arange(2.0, 6.0, 0.05):
    mask1 = B_th_nz <= bp
    mask2 = B_th_nz > bp
    if mask1.sum() < 2 or mask2.sum() < 2:
        continue
    s1, i1, r1, p1, _ = stats.linregress(B_th_nz[mask1], V_th_nz[mask1])
    s2, i2, r2, p2, _ = stats.linregress(B_th_nz[mask2], V_th_nz[mask2])
    y_pred = np.where(mask1, s1 * B_th_nz + i1, s2 * B_th_nz + i2)
    ss_res = np.sum((V_th_nz - y_pred)**2)
    ss_tot = np.sum((V_th_nz - np.mean(V_th_nz))**2)
    seg_r2 = 1 - ss_res / ss_tot
    if seg_r2 > best_seg_R2_th:
        best_seg_R2_th = seg_r2
        best_bp_th = bp
        best_params_th = (s1, i1, s2, i2)

print(f"\nTheory segmented regression:")
print(f"  breakpoint_Bc={best_bp_th:.2f}")
print(f"  segment1: slope={best_params_th[0]:.6f}, intercept={best_params_th[1]:.6f}")
print(f"  segment2: slope={best_params_th[2]:.6f}, intercept={best_params_th[3]:.6f}")
print(f"  segmented R²={best_seg_R2_th:.6f}")

results["finding1"] = {
    "meanfield": {
        "linear_fit": {
            "slope": float(slope_mf),
            "intercept": float(intercept_mf),
            "R_squared": float(r_mf**2),
            "p_value": float(p_mf)
        },
        "segmented_regression": {
            "breakpoint_Bc": float(best_breakpoint),
            "segment1_slope": float(best_params[0]),
            "segment1_intercept": float(best_params[1]),
            "segment2_slope": float(best_params[2]),
            "segment2_intercept": float(best_params[3]),
            "R_squared": float(best_seg_R2)
        }
    },
    "theory": {
        "linear_fit": {
            "slope": float(slope_th),
            "intercept": float(intercept_th),
            "R_squared": float(r_th**2),
            "p_value": float(p_th)
        },
        "segmented_regression": {
            "breakpoint_Bc": float(best_bp_th),
            "segment1_slope": float(best_params_th[0]),
            "segment1_intercept": float(best_params_th[1]),
            "segment2_slope": float(best_params_th[2]),
            "segment2_intercept": float(best_params_th[3]),
            "R_squared": float(best_seg_R2_th)
        }
    }
}

# ============================================================
# Finding 2: Correlation collapse - lag-rescaling factors
# ============================================================
print("\n" + "=" * 60)
print("FINDING 2: Correlation collapse")
print("=" * 60)

# Each corr.ave_k.txt has two columns: lag and correlation value
# We need to find optimal rescaling factor that maximizes correlation between pairs
# The idea: C_k(tau) should collapse when plotted against tau/scale_k
# So we try different scale factors and find which maximizes pairwise correlation

corr_files = []
for k in range(1, 6):
    fpath = os.path.join(DATA_DIR, f"figures/fig3a_correlation_collapse/data/corr.ave_{k}.txt")
    data = np.loadtxt(fpath)
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    if data.shape[1] >= 2:
        lags = data[:, 0]
        corrs = data[:, 1]
    else:
        lags = np.arange(len(data))
        corrs = data[:, 0]
    corr_files.append((k, lags, corrs))
    print(f"  ave_{k}: {len(lags)} points, lag range [{lags.min():.0f}, {lags.max():.0f}], corr range [{corrs.min():.4f}, {corrs.max():.4f}]")

# For correlation collapse, we want to find scale factors s_k such that
# C_k(tau) ~ C_ref(tau/s_k) for some reference
# Use ave_1 as reference (largest system, most data)
ref_k, ref_lags, ref_corrs = corr_files[0]

pairwise_results = {}
for i in range(1, 6):
    k_i, lags_i, corrs_i = corr_files[i-1]
    if i == 1:
        pairwise_results[f"ave_{k_i}"] = {
            "optimal_scale": 1.0,
            "self_correlation": 1.0,
            "note": "reference curve"
        }
        continue

    # Try to find optimal scale factor s that maximizes correlation between
    # ref_corrs and corrs_i at scaled lags
    # Interpolate ref curve at scaled lags of curve i
    best_s = None
    best_corr_val = -np.inf

    # Search over a range of scale factors
    for s in np.linspace(0.5, 5.0, 500):
        scaled_lags = lags_i / s
        # Interpolate reference curve at scaled lags
        ref_interp = np.interp(scaled_lags, ref_lags, ref_corrs)
        # Compute correlation (only where both are valid)
        valid = ~(np.isnan(ref_interp) | np.isnan(corrs_i))
        if valid.sum() < 10:
            continue
        c = np.corrcoef(corrs_i[valid], ref_interp[valid])[0, 1]
        if not np.isnan(c) and c > best_corr_val:
            best_corr_val = c
            best_s = s

    print(f"  ave_{k_i} vs ave_1: optimal_scale={best_s:.4f}, max_correlation={best_corr_val:.6f}")
    pairwise_results[f"ave_{k_i}"] = {
        "optimal_scale": float(best_s),
        "max_correlation_with_reference": float(best_corr_val)
    }

# Also compute pairwise correlations between all pairs
all_pairwise = {}
for i in range(1, 6):
    for j in range(i+1, 6):
        k_i, lags_i, corrs_i = corr_files[i-1]
        k_j, lags_j, corrs_j = corr_files[j-1]

        # Find optimal scale for j relative to i
        best_s_ij = None
        best_corr_ij = -np.inf
        for s in np.linspace(0.5, 5.0, 500):
            scaled_lags = lags_j / s
            ref_interp = np.interp(scaled_lags, lags_i, corrs_i)
            valid = ~(np.isnan(ref_interp) | np.isnan(corrs_j))
            if valid.sum() < 10:
                continue
            c = np.corrcoef(corrs_j[valid], ref_interp[valid])[0, 1]
            if not np.isnan(c) and c > best_corr_ij:
                best_corr_ij = c
                best_s_ij = s

        key = f"ave_{k_i}_vs_ave_{k_j}"
        all_pairwise[key] = {
            "optimal_scale": float(best_s_ij),
            "correlation": float(best_corr_ij)
        }
        print(f"  ave_{k_i} vs ave_{k_j}: scale={best_s_ij:.4f}, corr={best_corr_ij:.6f}")

results["finding2"] = {
    "pairwise_optimal_scales": pairwise_results,
    "all_pairwise_correlations": all_pairwise
}

# ============================================================
# Finding 3: Finite-size scaling
# ============================================================
print("\n" + "=" * 60)
print("FINDING 3: Finite-size scaling")
print("=" * 60)

# Read N_values and Bc values
N_values = np.loadtxt(os.path.join(DATA_DIR, "figures/SI.2_finite_size/data/N_values.csv"))
meanfield_Bc = np.loadtxt(os.path.join(DATA_DIR, "figures/SI.2_finite_size/data/meanfield_Bc.csv"))
tempnet_Bc = np.loadtxt(os.path.join(DATA_DIR, "figures/SI.2_finite_size/data/tempnet_Bc.csv"))

print(f"N_values: {N_values[:5]} ... ({len(N_values)} points)")
print(f"meanfield_Bc: {meanfield_Bc[:5]} ... ({len(meanfield_Bc)} points)")
print(f"tempnet_Bc: {tempnet_Bc[:5]} ... ({len(tempnet_Bc)} points)")

def finite_size_scaling(N, Bc_inf, a, nu):
    """Bc(N) = Bc_inf + a * N^(-1/nu)"""
    return Bc_inf + a * N**(-1.0/nu)

def fit_fss(N, Bc_vals, nu):
    """Fit Bc(N) = Bc_inf + a*N^(-1/nu) for fixed nu, return Bc_inf, a, R²"""
    x = N**(-1.0/nu)
    slope, intercept, r, p, se = stats.linregress(x, Bc_vals)
    y_pred = intercept + slope * x
    ss_res = np.sum((Bc_vals - y_pred)**2)
    ss_tot = np.sum((Bc_vals - np.mean(Bc_vals))**2)
    R2 = 1 - ss_res / ss_tot
    return intercept, slope, R2

# Scan nu values
nu_range = np.linspace(0.5, 5.0, 1000)

# Meanfield
best_R2_mf = -np.inf
best_nu_mf = None
best_params_mf = None
for nu in nu_range:
    Bc_inf, a, R2 = fit_fss(N_values, meanfield_Bc, nu)
    if R2 > best_R2_mf:
        best_R2_mf = R2
        best_nu_mf = nu
        best_params_mf = (Bc_inf, a)

print(f"\nMeanfield FSS:")
print(f"  best nu = {best_nu_mf:.4f}")
print(f"  Bc_inf = {best_params_mf[0]:.6f}")
print(f"  a = {best_params_mf[1]:.6f}")
print(f"  R² = {best_R2_mf:.6f}")

# Tempnet
best_R2_tn = -np.inf
best_nu_tn = None
best_params_tn = None
for nu in nu_range:
    Bc_inf, a, R2 = fit_fss(N_values, tempnet_Bc, nu)
    if R2 > best_R2_tn:
        best_R2_tn = R2
        best_nu_tn = nu
        best_params_tn = (Bc_inf, a)

print(f"\nTempnet FSS:")
print(f"  best nu = {best_nu_tn:.4f}")
print(f"  Bc_inf = {best_params_tn[0]:.6f}")
print(f"  a = {best_params_tn[1]:.6f}")
print(f"  R² = {best_R2_tn:.6f}")

# Also try power-law model: Bc(N) = Bc_inf + a*N^(-alpha) with alpha free
def fit_powerlaw(N, Bc_vals):
    """Free exponent fit using nonlinear least squares"""
    def model(N, Bc_inf, a, alpha):
        return Bc_inf + a * N**(-alpha)
    p0 = [3.0, 0.5, 0.5]
    try:
        popt, pcov = curve_fit(model, N, Bc_vals, p0=p0, maxfev=10000)
        y_pred = model(N, *popt)
        ss_res = np.sum((Bc_vals - y_pred)**2)
        ss_tot = np.sum((Bc_vals - np.mean(Bc_vals))**2)
        R2 = 1 - ss_res / ss_tot
        return popt[0], popt[1], popt[2], R2
    except:
        return None, None, None, -np.inf

Bc_inf_mf_pl, a_mf_pl, alpha_mf_pl, R2_mf_pl = fit_powerlaw(N_values, meanfield_Bc)
Bc_inf_tn_pl, a_tn_pl, alpha_tn_pl, R2_tn_pl = fit_powerlaw(N_values, tempnet_Bc)

print(f"\nMeanfield power-law fit: Bc_inf={Bc_inf_mf_pl:.6f}, a={a_mf_pl:.6f}, alpha={alpha_mf_pl:.6f}, R²={R2_mf_pl:.6f}")
print(f"Tempnet power-law fit: Bc_inf={Bc_inf_tn_pl:.6f}, a={a_tn_pl:.6f}, alpha={alpha_tn_pl:.6f}, R²={R2_tn_pl:.6f}")

results["finding3"] = {
    "meanfield": {
        "scanning_method": {
            "best_nu": float(best_nu_mf),
            "Bc_inf": float(best_params_mf[0]),
            "amplitude_a": float(best_params_mf[1]),
            "R_squared": float(best_R2_mf)
        },
        "power_law_fit": {
            "Bc_inf": float(Bc_inf_mf_pl),
            "amplitude_a": float(a_mf_pl),
            "exponent_alpha": float(alpha_mf_pl),
            "R_squared": float(R2_mf_pl)
        }
    },
    "tempnet": {
        "scanning_method": {
            "best_nu": float(best_nu_tn),
            "Bc_inf": float(best_params_tn[0]),
            "amplitude_a": float(best_params_tn[1]),
            "R_squared": float(best_R2_tn)
        },
        "power_law_fit": {
            "Bc_inf": float(Bc_inf_tn_pl),
            "amplitude_a": float(a_tn_pl),
            "exponent_alpha": float(alpha_tn_pl),
            "R_squared": float(R2_tn_pl)
        }
    }
}

# ============================================================
# Finding 4: Real-network validation
# ============================================================
print("\n" + "=" * 60)
print("FINDING 4: Real-network validation")
print("=" * 60)

# Thiers13
thiers_data = np.loadtxt(os.path.join(DATA_DIR, "figures/fig4b_RW_networks/fig_source_data/Thiers13_source_data.csv"),
                         delimiter=',', skiprows=1)
buffer_t = thiers_data[:, 0]
delay_t = thiers_data[:, 1]

# Linear model: delay = a + b * buffer
sl_t, int_t, r_t, p_t, se_t = stats.linregress(buffer_t, delay_t)
y_pred_lin_t = int_t + sl_t * buffer_t
ss_res_t = np.sum((delay_t - y_pred_lin_t)**2)
ss_tot_t = np.sum((delay_t - np.mean(delay_t))**2)
R2_lin_t = 1 - ss_res_t / ss_tot_t

# Power-law model: delay = a * buffer^b (fit in log space)
# Only use positive buffer values
pos_mask_t = buffer_t > 0
if pos_mask_t.sum() > 2:
    log_b_t = np.log(buffer_t[pos_mask_t])
    log_d_t = np.log(delay_t[pos_mask_t])
    sl_log_t, int_log_t, r_log_t, p_log_t, se_log_t = stats.linregress(log_b_t, log_d_t)
    a_pow_t = np.exp(int_log_t)
    b_pow_t = sl_log_t
    y_pred_pow_t = a_pow_t * buffer_t**b_pow_t
    ss_res_pow_t = np.sum((delay_t - y_pred_pow_t)**2)
    R2_pow_t = 1 - ss_res_pow_t / ss_tot_t
else:
    a_pow_t, b_pow_t, R2_pow_t = None, None, None

print(f"\nThiers13:")
print(f"  Linear: slope={sl_t:.6f}, intercept={int_t:.6f}, R²={R2_lin_t:.6f}, p={p_t:.2e}")
if a_pow_t is not None:
    print(f"  Power-law: a={a_pow_t:.6f}, b={b_pow_t:.6f}, R²={R2_pow_t:.6f}, p={p_log_t:.2e}")

# Workplace15
wp_data = np.loadtxt(os.path.join(DATA_DIR, "figures/fig4b_RW_networks/fig_source_data/Workplace15_source_data.csv"),
                     delimiter=',', skiprows=1)
buffer_w = wp_data[:, 0]
delay_w = wp_data[:, 1]

sl_w, int_w, r_w, p_w, se_w = stats.linregress(buffer_w, delay_w)
y_pred_lin_w = int_w + sl_w * buffer_w
ss_res_w = np.sum((delay_w - y_pred_lin_w)**2)
ss_tot_w = np.sum((delay_w - np.mean(delay_w))**2)
R2_lin_w = 1 - ss_res_w / ss_tot_w

pos_mask_w = buffer_w > 0
if pos_mask_w.sum() > 2:
    log_b_w = np.log(buffer_w[pos_mask_w])
    log_d_w = np.log(delay_w[pos_mask_w])
    sl_log_w, int_log_w, r_log_w, p_log_w, se_log_w = stats.linregress(log_b_w, log_d_w)
    a_pow_w = np.exp(int_log_w)
    b_pow_w = sl_log_w
    y_pred_pow_w = a_pow_w * buffer_w**b_pow_w
    ss_res_pow_w = np.sum((delay_w - y_pred_pow_w)**2)
    R2_pow_w = 1 - ss_res_pow_w / ss_tot_w
else:
    a_pow_w, b_pow_w, R2_pow_w = None, None, None

print(f"\nWorkplace15:")
print(f"  Linear: slope={sl_w:.6f}, intercept={int_w:.6f}, R²={R2_lin_w:.6f}, p={p_w:.2e}")
if a_pow_w is not None:
    print(f"  Power-law: a={a_pow_w:.6f}, b={b_pow_w:.6f}, R²={R2_pow_w:.6f}, p={p_log_w:.2e}")

results["finding4"] = {
    "Thiers13": {
        "linear_model": {
            "slope": float(sl_t),
            "intercept": float(int_t),
            "R_squared": float(R2_lin_t),
            "p_value": float(p_t)
        },
        "power_law_model": {
            "coefficient_a": float(a_pow_t) if a_pow_t is not None else None,
            "exponent_b": float(b_pow_t) if b_pow_t is not None else None,
            "R_squared": float(R2_pow_t) if R2_pow_t is not None else None,
            "p_value": float(p_log_t) if p_log_t is not None else None
        }
    },
    "Workplace15": {
        "linear_model": {
            "slope": float(sl_w),
            "intercept": float(int_w),
            "R_squared": float(R2_lin_w),
            "p_value": float(p_w)
        },
        "power_law_model": {
            "coefficient_a": float(a_pow_w) if a_pow_w is not None else None,
            "exponent_b": float(b_pow_w) if b_pow_w is not None else None,
            "R_squared": float(R2_pow_w) if R2_pow_w is not None else None,
            "p_value": float(p_log_w) if p_log_w is not None else None
        }
    }
}

# ============================================================
# Save results
# ============================================================
output_path = os.path.join(OUTPUT_DIR, "results.json")
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {output_path}")

# ============================================================
# Compare with original results
# ============================================================
print("\n" + "=" * 60)
print("COMPARISON WITH ORIGINAL RESULTS")
print("=" * 60)

original_path = os.path.join("/data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project/output/evidence", "finding1_v_b_scatter.json")
try:
    with open(original_path) as f:
        original = json.load(f)

    diffs = {}
    # Compare finding1
    orig_mf = original.get("meanfield", {}).get("linear_fit", {})
    my_mf = results["finding1"]["meanfield"]["linear_fit"]
    for key in ["slope", "intercept", "R_squared", "p_value"]:
        if key in orig_mf and key in my_mf:
            ov = orig_mf[key]
            mv = my_mf[key]
            if abs(ov) > 1e-10:
                pct_diff = abs(mv - ov) / abs(ov) * 100
            else:
                pct_diff = abs(mv - ov) * 100
            diffs[f"finding1_meanfield_{key}"] = {"original": ov, "independent": mv, "pct_diff": pct_diff}
            if pct_diff > 1.0:
                print(f"  WARNING: finding1 meanfield {key}: orig={ov}, mine={mv}, diff={pct_diff:.2f}%")

    orig_th = original.get("theory", {}).get("linear_fit", {})
    my_th = results["finding1"]["theory"]["linear_fit"]
    for key in ["slope", "intercept", "R_squared", "p_value"]:
        if key in orig_th and key in my_th:
            ov = orig_th[key]
            mv = my_th[key]
            if abs(ov) > 1e-10:
                pct_diff = abs(mv - ov) / abs(ov) * 100
            else:
                pct_diff = abs(mv - ov) * 100
            diffs[f"finding1_theory_{key}"] = {"original": ov, "independent": mv, "pct_diff": pct_diff}
            if pct_diff > 1.0:
                print(f"  WARNING: finding1 theory {key}: orig={ov}, mine={mv}, diff={pct_diff:.2f}%")

    # Compare segmented Bc
    orig_bp_mf = original.get("meanfield", {}).get("segmented_Bc", None)
    my_bp_mf = results["finding1"]["meanfield"]["segmented_regression"]["breakpoint_Bc"]
    if orig_bp_mf is not None:
        if abs(orig_bp_mf) > 1e-10:
            pct_diff = abs(my_bp_mf - orig_bp_mf) / abs(orig_bp_mf) * 100
        else:
            pct_diff = abs(my_bp_mf - orig_bp_mf) * 100
        diffs["finding1_meanfield_segmented_Bc"] = {"original": orig_bp_mf, "independent": my_bp_mf, "pct_diff": pct_diff}
        if pct_diff > 1.0:
            print(f"  WARNING: finding1 meanfield segmented_Bc: orig={orig_bp_mf}, mine={my_bp_mf}, diff={pct_diff:.2f}%")

    orig_bp_th = original.get("theory", {}).get("segmented_Bc", None)
    my_bp_th = results["finding1"]["theory"]["segmented_regression"]["breakpoint_Bc"]
    if orig_bp_th is not None:
        if abs(orig_bp_th) > 1e-10:
            pct_diff = abs(my_bp_th - orig_bp_th) / abs(orig_bp_th) * 100
        else:
            pct_diff = abs(my_bp_th - orig_bp_th) * 100
        diffs["finding1_theory_segmented_Bc"] = {"original": orig_bp_th, "independent": my_bp_th, "pct_diff": pct_diff}
        if pct_diff > 1.0:
            print(f"  WARNING: finding1 theory segmented_Bc: orig={orig_bp_th}, mine={my_bp_th}, diff={pct_diff:.2f}%")

    if diffs:
        print(f"\nDifferences found: {len(diffs)} comparisons")
        for k, v in diffs.items():
            print(f"  {k}: orig={v['original']}, independent={v['independent']}, diff={v['pct_diff']:.2f}%")
    else:
        print("No differences found.")

except FileNotFoundError:
    print(f"Original results file not found at {original_path}")

print("\nDone!")
