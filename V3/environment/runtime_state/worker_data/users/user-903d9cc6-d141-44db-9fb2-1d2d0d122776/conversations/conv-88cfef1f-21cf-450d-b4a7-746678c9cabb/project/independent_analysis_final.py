#!/usr/bin/env python3
"""Final independent analysis - matching original methodology."""

import json
import numpy as np
from scipy import stats
import os

DATA_DIR = "/data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project/data/source_data"
OUTPUT_DIR = "/data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project/output/evidence_independent"

results = {}

# ============================================================
# Finding 1: V vs B relationship
# ============================================================
print("=" * 60)
print("FINDING 1: V vs B relationship")
print("=" * 60)

# --- Meanfield data ---
mf_data = np.loadtxt(os.path.join(DATA_DIR, "figures/fig2_critical_buffer/data/meanfield_data.csv"),
                     delimiter=',', skiprows=1)
B_mf = mf_data[:, 0]
V_mf = mf_data[:, 2]

# Full linear fit (all points, matching original)
slope_mf, intercept_mf, r_mf, p_mf, _ = stats.linregress(B_mf, V_mf)
print(f"\nMeanfield full linear fit:")
print(f"  slope={slope_mf:.6f}, intercept={intercept_mf:.6f}, R²={r_mf**2:.6f}, p={p_mf:.2e}")

# Segmented regression with finer grid
best_bp_mf = None
best_seg_R2_mf = -np.inf
best_params_mf = None
for bp in np.arange(1.0, 7.0, 0.01):
    mask1 = B_mf <= bp
    mask2 = B_mf > bp
    if mask1.sum() < 2 or mask2.sum() < 2:
        continue
    s1, i1, _, _, _ = stats.linregress(B_mf[mask1], V_mf[mask1])
    s2, i2, _, _, _ = stats.linregress(B_mf[mask2], V_mf[mask2])
    y_pred = np.where(mask1, s1 * B_mf + i1, s2 * B_mf + i2)
    ss_res = np.sum((V_mf - y_pred)**2)
    ss_tot = np.sum((V_mf - np.mean(V_mf))**2)
    seg_r2 = 1 - ss_res / ss_tot
    if seg_r2 > best_seg_R2_mf:
        best_seg_R2_mf = seg_r2
        best_bp_mf = bp
        best_params_mf = (s1, i1, s2, i2)

print(f"Meanfield segmented: Bc={best_bp_mf:.2f}, segR²={best_seg_R2_mf:.6f}")

# --- Theory data ---
th_data = np.loadtxt(os.path.join(DATA_DIR, "figures/fig2_critical_buffer/data/theory_data.csv"),
                     delimiter=',', skiprows=1)
B_th = th_data[:, 0]
V_th = th_data[:, 2]

# Full linear fit (ALL points including zeros, matching original methodology)
slope_th, intercept_th, r_th, p_th, _ = stats.linregress(B_th, V_th)
print(f"\nTheory full linear fit (all points):")
print(f"  slope={slope_th:.6f}, intercept={intercept_th:.6f}, R²={r_th**2:.6f}, p={p_th:.2e}")

# Segmented regression for theory
best_bp_th = None
best_seg_R2_th = -np.inf
best_params_th = None
for bp in np.arange(1.0, 7.0, 0.01):
    mask1 = B_th <= bp
    mask2 = B_th > bp
    if mask1.sum() < 2 or mask2.sum() < 2:
        continue
    s1, i1, _, _, _ = stats.linregress(B_th[mask1], V_th[mask1])
    s2, i2, _, _, _ = stats.linregress(B_th[mask2], V_th[mask2])
    y_pred = np.where(mask1, s1 * B_th + i1, s2 * B_th + i2)
    ss_res = np.sum((V_th - y_pred)**2)
    ss_tot = np.sum((V_th - np.mean(V_th))**2)
    seg_r2 = 1 - ss_res / ss_tot
    if seg_r2 > best_seg_R2_th:
        best_seg_R2_th = seg_r2
        best_bp_th = bp
        best_params_th = (s1, i1, s2, i2)

print(f"Theory segmented: Bc={best_bp_th:.2f}, segR²={best_seg_R2_th:.6f}")

results["finding1"] = {
    "meanfield": {
        "linear_fit": {"slope": float(slope_mf), "intercept": float(intercept_mf),
                       "R_squared": float(r_mf**2), "p_value": float(p_mf)},
        "segmented_regression": {
            "breakpoint_Bc": float(best_bp_mf),
            "segment1_slope": float(best_params_mf[0]), "segment1_intercept": float(best_params_mf[1]),
            "segment2_slope": float(best_params_mf[2]), "segment2_intercept": float(best_params_mf[3]),
            "R_squared": float(best_seg_R2_mf)
        }
    },
    "theory": {
        "linear_fit": {"slope": float(slope_th), "intercept": float(intercept_th),
                       "R_squared": float(r_th**2), "p_value": float(p_th)},
        "segmented_regression": {
            "breakpoint_Bc": float(best_bp_th),
            "segment1_slope": float(best_params_th[0]), "segment1_intercept": float(best_params_th[1]),
            "segment2_slope": float(best_params_th[2]), "segment2_intercept": float(best_params_th[3]),
            "R_squared": float(best_seg_R2_th)
        }
    }
}

# ============================================================
# Finding 2: Correlation collapse
# ============================================================
print("\n" + "=" * 60)
print("FINDING 2: Correlation collapse")
print("=" * 60)

corr_files = []
for k in range(1, 6):
    fpath = os.path.join(DATA_DIR, f"figures/fig3a_correlation_collapse/data/corr.ave_{k}.txt")
    data = np.loadtxt(fpath)
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    lags = data[:, 0]
    corrs = data[:, 1]
    corr_files.append((k, lags, corrs))

ref_k, ref_lags, ref_corrs = corr_files[0]

# Decay scale estimation
def get_decay_scale(lags, corrs):
    c0 = corrs[0]
    target = c0 / np.e
    below = corrs < target
    if below.sum() > 0:
        idx = below.argmax()
        return lags[idx]
    return lags[-1]

decay_scales = {}
for k, lags, corrs in corr_files:
    decay_scales[k] = get_decay_scale(lags, corrs)

pairwise_results = {}
all_pairwise = {}

for i in range(1, 6):
    k_i, lags_i, corrs_i = corr_files[i-1]
    if i == 1:
        pairwise_results[f"ave_{k_i}"] = {"optimal_scale": 1.0, "self_correlation": 1.0, "note": "reference"}
        continue

    best_s = None
    best_corr_val = -np.inf
    for s in np.linspace(0.1, 10.0, 1000):
        scaled_lags = lags_i / s
        ref_interp = np.interp(scaled_lags, ref_lags, ref_corrs)
        valid = ~(np.isnan(ref_interp) | np.isnan(corrs_i))
        if valid.sum() < 10:
            continue
        c = np.corrcoef(corrs_i[valid], ref_interp[valid])[0, 1]
        if not np.isnan(c) and c > best_corr_val:
            best_corr_val = c
            best_s = s

    print(f"  ave_{k_i}: scale={best_s:.4f}, corr={best_corr_val:.6f}")
    pairwise_results[f"ave_{k_i}"] = {"optimal_scale": float(best_s), "max_correlation_with_reference": float(best_corr_val)}

for i in range(1, 6):
    for j in range(i+1, 6):
        k_i, lags_i, corrs_i = corr_files[i-1]
        k_j, lags_j, corrs_j = corr_files[j-1]
        best_s_ij = None
        best_corr_ij = -np.inf
        for s in np.linspace(0.1, 10.0, 1000):
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
        all_pairwise[key] = {"optimal_scale": float(best_s_ij), "correlation": float(best_corr_ij)}

results["finding2"] = {
    "pairwise_optimal_scales": pairwise_results,
    "all_pairwise_correlations": all_pairwise,
    "decay_scales": {str(k): float(v) for k, v in decay_scales.items()}
}

# ============================================================
# Finding 3: Finite-size scaling
# ============================================================
print("\n" + "=" * 60)
print("FINDING 3: Finite-size scaling")
print("=" * 60)

N_values = np.loadtxt(os.path.join(DATA_DIR, "figures/SI.2_finite_size/data/N_values.csv"))
meanfield_Bc = np.loadtxt(os.path.join(DATA_DIR, "figures/SI.2_finite_size/data/meanfield_Bc.csv"))
tempnet_Bc = np.loadtxt(os.path.join(DATA_DIR, "figures/SI.2_finite_size/data/tempnet_Bc.csv"))

def fit_fss(N, Bc_vals, nu):
    x = N**(-1.0/nu)
    slope, intercept, r, p, se = stats.linregress(x, Bc_vals)
    y_pred = intercept + slope * x
    ss_res = np.sum((Bc_vals - y_pred)**2)
    ss_tot = np.sum((Bc_vals - np.mean(Bc_vals))**2)
    R2 = 1 - ss_res / ss_tot
    return intercept, slope, R2

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

print(f"Meanfield: nu={best_nu_mf:.4f}, Bc_inf={best_params_mf[0]:.6f}, R²={best_R2_mf:.6f}")
print(f"Tempnet: nu={best_nu_tn:.4f}, Bc_inf={best_params_tn[0]:.6f}, R²={best_R2_tn:.6f}")

results["finding3"] = {
    "meanfield": {
        "scanning_method": {"best_nu": float(best_nu_mf), "Bc_inf": float(best_params_mf[0]),
                            "amplitude_a": float(best_params_mf[1]), "R_squared": float(best_R2_mf)}
    },
    "tempnet": {
        "scanning_method": {"best_nu": float(best_nu_tn), "Bc_inf": float(best_params_tn[0]),
                            "amplitude_a": float(best_params_tn[1]), "R_squared": float(best_R2_tn)}
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

sl_t, int_t, r_t, p_t, _ = stats.linregress(buffer_t, delay_t)
y_pred_lin_t = int_t + sl_t * buffer_t
ss_res_t = np.sum((delay_t - y_pred_lin_t)**2)
ss_tot_t = np.sum((delay_t - np.mean(delay_t))**2)
R2_lin_t = 1 - ss_res_t / ss_tot_t

# Power-law on log-log (positive values only)
pos_mask_t = (buffer_t > 0) & (delay_t > 0)
if pos_mask_t.sum() > 2:
    log_b_t = np.log(buffer_t[pos_mask_t])
    log_d_t = np.log(delay_t[pos_mask_t])
    sl_log_t, int_log_t, r_log_t, p_log_t, _ = stats.linregress(log_b_t, log_d_t)
    a_pow_t = np.exp(int_log_t)
    b_pow_t = sl_log_t
    # R² on log-log scale
    y_pred_log_t = int_log_t + sl_log_t * log_b_t
    ss_res_log_t = np.sum((log_d_t - y_pred_log_t)**2)
    ss_tot_log_t = np.sum((log_d_t - np.mean(log_d_t))**2)
    R2_pow_t = 1 - ss_res_log_t / ss_tot_log_t
else:
    a_pow_t, b_pow_t, R2_pow_t, p_log_t = None, None, None, None

print(f"Thiers13: Linear R²={R2_lin_t:.6f}, Power-law R²={R2_pow_t}")

# Workplace15
wp_data = np.loadtxt(os.path.join(DATA_DIR, "figures/fig4b_RW_networks/fig_source_data/Workplace15_source_data.csv"),
                     delimiter=',', skiprows=1)
buffer_w = wp_data[:, 0]
delay_w = wp_data[:, 1]

sl_w, int_w, r_w, p_w, _ = stats.linregress(buffer_w, delay_w)
y_pred_lin_w = int_w + sl_w * buffer_w
ss_res_w = np.sum((delay_w - y_pred_lin_w)**2)
ss_tot_w = np.sum((delay_w - np.mean(delay_w))**2)
R2_lin_w = 1 - ss_res_w / ss_tot_w

pos_mask_w = (buffer_w > 0) & (delay_w > 0)
if pos_mask_w.sum() > 2:
    log_b_w = np.log(buffer_w[pos_mask_w])
    log_d_w = np.log(delay_w[pos_mask_w])
    sl_log_w, int_log_w, r_log_w, p_log_w, _ = stats.linregress(log_b_w, log_d_w)
    a_pow_w = np.exp(int_log_w)
    b_pow_w = sl_log_w
    y_pred_log_w = int_log_w + sl_log_w * log_b_w
    ss_res_log_w = np.sum((log_d_w - y_pred_log_w)**2)
    ss_tot_log_w = np.sum((log_d_w - np.mean(log_d_w))**2)
    R2_pow_w = 1 - ss_res_log_w / ss_tot_log_w
else:
    a_pow_w, b_pow_w, R2_pow_w, p_log_w = None, None, None, None

print(f"Workplace15: Linear R²={R2_lin_w:.6f}, Power-law R²={R2_pow_w}")

results["finding4"] = {
    "Thiers13": {
        "linear_model": {"slope": float(sl_t), "intercept": float(int_t),
                         "R_squared": float(R2_lin_t), "p_value": float(p_t)},
        "power_law_model": {
            "coefficient_a": float(a_pow_t) if a_pow_t else None,
            "exponent_b": float(b_pow_t) if b_pow_t else None,
            "R_squared": float(R2_pow_t) if R2_pow_t else None,
            "p_value": float(p_log_t) if p_log_t else None
        }
    },
    "Workplace15": {
        "linear_model": {"slope": float(sl_w), "intercept": float(int_w),
                         "R_squared": float(R2_lin_w), "p_value": float(p_w)},
        "power_law_model": {
            "coefficient_a": float(a_pow_w) if a_pow_w else None,
            "exponent_b": float(b_pow_w) if b_pow_w else None,
            "R_squared": float(R2_pow_w) if R2_pow_w else None,
            "p_value": float(p_log_w) if p_log_w else None
        }
    }
}

# Save results
output_path = os.path.join(OUTPUT_DIR, "results.json")
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {output_path}")

# ============================================================
# Compare with original
# ============================================================
print("\n" + "=" * 60)
print("COMPARISON WITH ORIGINAL RESULTS")
print("=" * 60)

original_path = os.path.join("/data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project/output/evidence", "finding1_V_vs_B.json")
with open(original_path) as f:
    original = json.load(f)

diffs = {}
orig_mf = original.get("meanfield", {}).get("linear_fit", {})
my_mf = results["finding1"]["meanfield"]["linear_fit"]
for key in ["slope", "intercept", "R_squared", "p_value"]:
    if key in orig_mf and key in my_mf:
        ov, mv = orig_mf[key], my_mf[key]
        pct_diff = abs(mv - ov) / abs(ov) * 100 if abs(ov) > 1e-10 else abs(mv - ov) * 100
        diffs[f"mf_{key}"] = {"orig": ov, "mine": mv, "pct": pct_diff}
        status = "OK" if pct_diff <= 1.0 else "DIFF"
        print(f"  [{status}] mf {key}: orig={ov}, mine={mv}, diff={pct_diff:.4f}%")

orig_th = original.get("theory", {}).get("linear_fit", {})
my_th = results["finding1"]["theory"]["linear_fit"]
for key in ["slope", "intercept", "R_squared", "p_value"]:
    if key in orig_th and key in my_th:
        ov, mv = orig_th[key], my_th[key]
        pct_diff = abs(mv - ov) / abs(ov) * 100 if abs(ov) > 1e-10 else abs(mv - ov) * 100
        diffs[f"th_{key}"] = {"orig": ov, "mine": mv, "pct": pct_diff}
        status = "OK" if pct_diff <= 1.0 else "DIFF"
        print(f"  [{status}] th {key}: orig={ov}, mine={mv}, diff={pct_diff:.4f}%")

# Segmented Bc
for name, orig_bp, my_bp in [("mf_seg_Bc", original["meanfield"]["segmented_Bc"], results["finding1"]["meanfield"]["segmented_regression"]["breakpoint_Bc"]),
                               ("th_seg_Bc", original["theory"]["segmented_Bc"], results["finding1"]["theory"]["segmented_regression"]["breakpoint_Bc"])]:
    pct_diff = abs(my_bp - orig_bp) / abs(orig_bp) * 100 if abs(orig_bp) > 1e-10 else abs(my_bp - orig_bp) * 100
    diffs[name] = {"orig": orig_bp, "mine": my_bp, "pct": pct_diff}
    status = "OK" if pct_diff <= 1.0 else "DIFF"
    print(f"  [{status}] {name}: orig={orig_bp}, mine={my_bp}, diff={pct_diff:.2f}%")

print(f"\nTotal: {len(diffs)} comparisons, {sum(1 for v in diffs.values() if v['pct'] > 1.0)} exceed 1%")
