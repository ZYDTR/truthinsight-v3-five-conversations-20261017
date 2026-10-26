#!/usr/bin/env python3
"""Independent replication v2 - fixes for finding1 comparison, finding2 scaling, finding4 power-law."""

import json
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
import os

DATA_DIR = "/data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project/data/source_data"
OUTPUT_DIR = "/data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project/output/evidence_independent"

# ============================================================
# Finding 2 revisited: Correlation collapse with better scaling
# ============================================================
print("=" * 60)
print("FINDING 2 REVISITED: Correlation collapse")
print("=" * 60)

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

# The key insight: these are time-lag correlation functions C(tau).
# For correlation collapse, we rescale tau -> tau/s_k where s_k is a system-size dependent scale.
# We should compare curves by interpolating one onto the lag grid of another.
# Use ave_1 as reference.

ref_k, ref_lags, ref_corrs = corr_files[0]

# Better approach: find optimal scale by matching the decay rate
# Compute the characteristic decay length (where correlation drops to 1/e or similar)
def get_decay_scale(lags, corrs):
    """Find the lag at which correlation drops to 1/e of initial value."""
    c0 = corrs[0]
    target = c0 / np.e
    # Find first index where corr < target
    below = corrs < target
    if below.sum() > 0:
        idx = below.argmax()
        return lags[idx]
    return lags[-1]

decay_scales = {}
for k, lags, corrs in corr_files:
    ds = get_decay_scale(lags, corrs)
    decay_scales[k] = ds
    print(f"  ave_{k}: decay_scale={ds:.1f}")

# Optimal scale factor relative to reference
pairwise_results = {}
all_pairwise = {}

for i in range(1, 6):
    k_i, lags_i, corrs_i = corr_files[i-1]
    if i == 1:
        pairwise_results[f"ave_{k_i}"] = {
            "optimal_scale": 1.0,
            "self_correlation": 1.0,
            "note": "reference curve"
        }
        continue

    # Scale factor from decay ratio
    s_from_decay = decay_scales[k_i] / decay_scales[1]

    # Also verify by direct optimization
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

    print(f"  ave_{k_i} vs ave_1: optimal_scale={best_s:.4f}, max_correlation={best_corr_val:.6f}, decay_ratio={s_from_decay:.4f}")
    pairwise_results[f"ave_{k_i}"] = {
        "optimal_scale": float(best_s),
        "max_correlation_with_reference": float(best_corr_val),
        "decay_scale_ratio": float(s_from_decay)
    }

# All pairwise
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
        all_pairwise[key] = {
            "optimal_scale": float(best_s_ij),
            "correlation": float(best_corr_ij)
        }
        print(f"  ave_{k_i} vs ave_{k_j}: scale={best_s_ij:.4f}, corr={best_corr_ij:.6f}")

# ============================================================
# Finding 4 revisited: Real-network validation with proper power-law
# ============================================================
print("\n" + "=" * 60)
print("FINDING 4 REVISITED: Real-network validation")
print("=" * 60)

# Thiers13
thiers_data = np.loadtxt(os.path.join(DATA_DIR, "figures/fig4b_RW_networks/fig_source_data/Thiers13_source_data.csv"),
                         delimiter=',', skiprows=1)
buffer_t = thiers_data[:, 0]
delay_t = thiers_data[:, 1]

# Linear model
sl_t, int_t, r_t, p_t, se_t = stats.linregress(buffer_t, delay_t)
y_pred_lin_t = int_t + sl_t * buffer_t
ss_res_t = np.sum((delay_t - y_pred_lin_t)**2)
ss_tot_t = np.sum((delay_t - np.mean(delay_t))**2)
R2_lin_t = 1 - ss_res_t / ss_tot_t

# Power-law: fit log-log only for positive values
pos_mask_t = (buffer_t > 0) & (delay_t > 0)
if pos_mask_t.sum() > 2:
    log_b_t = np.log(buffer_t[pos_mask_t])
    log_d_t = np.log(delay_t[pos_mask_t])
    sl_log_t, int_log_t, r_log_t, p_log_t, se_log_t = stats.linregress(log_b_t, log_d_t)
    a_pow_t = np.exp(int_log_t)
    b_pow_t = sl_log_t
    # R² on original scale using predicted values
    y_pred_pow_t = a_pow_t * np.maximum(buffer_t, 1e-15)**b_pow_t
    ss_res_pow_t = np.sum((delay_t - y_pred_pow_t)**2)
    R2_pow_t = 1 - ss_res_pow_t / ss_tot_t
else:
    a_pow_t, b_pow_t, R2_pow_t, p_log_t = None, None, None, None

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

pos_mask_w = (buffer_w > 0) & (delay_w > 0)
if pos_mask_w.sum() > 2:
    log_b_w = np.log(buffer_w[pos_mask_w])
    log_d_w = np.log(delay_w[pos_mask_w])
    sl_log_w, int_log_w, r_log_w, p_log_w, se_log_w = stats.linregress(log_b_w, log_d_w)
    a_pow_w = np.exp(int_log_w)
    b_pow_w = sl_log_w
    y_pred_pow_w = a_pow_w * np.maximum(buffer_w, 1e-15)**b_pow_w
    ss_res_pow_w = np.sum((delay_w - y_pred_pow_w)**2)
    R2_pow_w = 1 - ss_res_pow_w / ss_tot_w
else:
    a_pow_w, b_pow_w, R2_pow_w, p_log_w = None, None, None, None

print(f"\nWorkplace15:")
print(f"  Linear: slope={sl_w:.6f}, intercept={int_w:.6f}, R²={R2_lin_w:.6f}, p={p_w:.2e}")
if a_pow_w is not None:
    print(f"  Power-law: a={a_pow_w:.6f}, b={b_pow_w:.6f}, R²={R2_pow_w:.6f}, p={p_log_w:.2e}")

# ============================================================
# Load existing results and update findings 2 and 4
# ============================================================
with open(os.path.join(OUTPUT_DIR, "results.json")) as f:
    results = json.load(f)

# Update finding2
results["finding2"] = {
    "pairwise_optimal_scales": pairwise_results,
    "all_pairwise_correlations": all_pairwise,
    "decay_scales": {str(k): float(v) for k, v in decay_scales.items()}
}

# Update finding4
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

# Save updated results
output_path = os.path.join(OUTPUT_DIR, "results.json")
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nUpdated results saved to {output_path}")

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
    # Original structure: top-level keys are "meanfield" and "theory", each with linear_fit dict
    orig_mf = original.get("meanfield", {})
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

    orig_th = original.get("theory", {})
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
            print(f"  NOTE: finding1 meanfield segmented_Bc: orig={orig_bp_mf}, mine={my_bp_mf}, diff={pct_diff:.2f}%")

    orig_bp_th = original.get("theory", {}).get("segmented_Bc", None)
    my_bp_th = results["finding1"]["theory"]["segmented_regression"]["breakpoint_Bc"]
    if orig_bp_th is not None:
        if abs(orig_bp_th) > 1e-10:
            pct_diff = abs(my_bp_th - orig_bp_th) / abs(orig_bp_th) * 100
        else:
            pct_diff = abs(my_bp_th - orig_bp_th) * 100
        diffs["finding1_theory_segmented_Bc"] = {"original": orig_bp_th, "independent": my_bp_th, "pct_diff": pct_diff}
        if pct_diff > 1.0:
            print(f"  NOTE: finding1 theory segmented_Bc: orig={orig_bp_th}, mine={my_bp_th}, diff={pct_diff:.2f}%")

    if diffs:
        print(f"\nDifferences found: {len(diffs)} comparisons")
        for k, v in diffs.items():
            print(f"  {k}: orig={v['original']}, independent={v['independent']}, diff={v['pct_diff']:.2f}%")
    else:
        print("No differences found.")

except FileNotFoundError:
    print(f"Original results file not found at {original_path}")

print("\nDone!")
