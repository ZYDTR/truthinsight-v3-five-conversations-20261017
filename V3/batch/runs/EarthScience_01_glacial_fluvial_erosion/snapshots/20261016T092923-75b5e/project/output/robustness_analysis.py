#!/usr/bin/env python3
"""
Robustness Analysis for Glacial vs Nonglacial Erosion Rate Findings.

Tests:
1. Mechanical coupling (fixed thickness artifact) via methodology stratification
2. Source/site correlation via clustered standard errors
3. Outlier sensitivity via winsorization and trimming
4. Threshold/bin analysis across timescale categories
5. Bayesian-like posterior predictive check via grid-search MCMC
6. Prior compilation cross-check (GloRiSe, OCTOPUS)
"""

import json
import os
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize

warnings.filterwarnings("ignore")

BASE = "/data/user/conversations/conv-46b0a68e-ac73-49c3-ba26-bbe4d51ce35a/project"
OUT = os.path.join(BASE, "working/subC")
os.makedirs(OUT, exist_ok=True)

results = {}

# ──────────────────────────────────────────────
# Load main datasets
# ──────────────────────────────────────────────
glacial = pd.read_csv(os.path.join(BASE, "data/raw/glacial_erosion_Earth.tsv"), sep="\t")
nonglacial = pd.read_csv(os.path.join(BASE, "data/raw/nonglacial_erosion_Earth.tsv"), sep="\t")

print(f"Glacial rows: {len(glacial)}, columns: {list(glacial.columns)}")
print(f"Nonglacial rows: {len(nonglacial)}, columns: {list(nonglacial.columns)}")

# Check for Sediment flux and Exhumation columns
for name, df in [("Glacial", glacial), ("Nonglacial", nonglacial)]:
    has_sedflux = "Sediment flux (km3/yr)" in df.columns
    has_exhum = any(c in df.columns for c in ["Exhumation (m)", "Exhumation min (m)", "Exhumation max (m)"])
    print(f"{name}: Sediment flux column={has_sedflux}, Exhumation columns={has_exhum}")

# ──────────────────────────────────────────────
# Helper: log-transform and clean
# ──────────────────────────────────────────────
def prepare(df, process_label):
    """Return a cleaned dataframe with log10(erode_rate) and log10(time_interval)."""
    out = df.copy()
    # Keep only rows with valid erosion rate and time interval
    out = out.dropna(subset=["Erosion rate (mm/yr)", "Time interval (yr)"])
    out = out[out["Erosion rate (mm/yr)"] > 0]
    out = out[out["Time interval (yr)"] > 0]
    out["log_erode"] = np.log10(out["Erosion rate (mm/yr)"].values)
    out["log_time"] = np.log10(out["Time interval (yr)"].values)
    out["process"] = process_label
    return out

glacial_clean = prepare(glacial, "Glacial")
nonglacial_clean = prepare(nonglacial, "Fluvial")
combined = pd.concat([glacial_clean, nonglacial_clean], ignore_index=True)

print(f"\nCleaned: Glacial={len(glacial_clean)}, Fluvial={len(nonglacial_clean)}, Combined={len(combined)}")

# ──────────────────────────────────────────────
# Baseline OLS regressions
# ──────────────────────────────────────────────
def ols_results(df, label=""):
    """Simple OLS: log_erode ~ log_time + 1."""
    X = df["log_time"].values
    y = df["log_erode"].values
    n = len(y)
    X_mat = np.column_stack([np.ones(n), X])
    beta = np.linalg.lstsq(X_mat, y, rcond=None)[0]
    resid = y - X_mat @ beta
    sse = np.sum(resid**2)
    # Standard error of regression
    sigma_hat = np.sqrt(sse / (n - 2))
    # Variance-covariance of betas: sigma^2 * (X'X)^{-1}
    XtX_inv = np.linalg.inv(X_mat.T @ X_mat)
    var_beta = sigma_hat**2 * XtX_inv
    se = np.sqrt(np.diag(var_beta))
    t_vals = beta / se
    p_vals = 2 * (1 - stats.t.cdf(np.abs(t_vals), df=n - 2))
    r2 = 1 - np.sum(resid**2) / (np.sum((y - y.mean())**2) + 1e-30)
    return {"label": label, "intercept": float(beta[0]), "slope": float(beta[1]),
            "se_intercept": float(se[0]), "se_slope": float(se[1]),
            "t_intercept": float(t_vals[0]), "t_slope": float(t_vals[1]),
            "p_intercept": float(p_vals[0]), "p_slope": float(p_vals[1]),
            "r_squared": float(r2), "n": n}

baseline_glacial = ols_results(glacial_clean, "Glacial_baseline")
baseline_fluvial = ols_results(nonglacial_clean, "Fluvial_baseline")
baseline_combined = ols_results(combined, "Combined_baseline")

results["baseline_ols"] = {
    "glacial": baseline_glacial,
    "fluvial": baseline_fluvial,
    "combined": baseline_combined
}
print("\n=== BASELINE OLS ===")
for k, v in results["baseline_ols"].items():
    print(f"  {k}: slope={v['slope']:.4f}, se={v['se_slope']:.4f}, p={v['p_slope']:.4f}, R2={v['r_squared']:.4f}")

# ──────────────────────────────────────────────
# 1. MECHANICAL COUPLING CHECK
# ──────────────────────────────────────────────
print("\n=== 1. MECHANICAL COUPLING CHECK ===")

# Check if Methodology column exists and its unique values
method_col = "Methodology"
if method_col in combined.columns:
    methods_glacial = glacial_clean[method_col].value_counts().to_dict()
    methods_fluvial = nonglacial_clean[method_col].value_counts().to_dict()
    print(f"Glacial methodologies: {methods_glacial}")
    print(f"Fluvial methodologies: {methods_fluvial}")

    # Stratify by methodology
    mech_results = {}
    for proc_name, proc_df in [("Glacial", glacial_clean), ("Fluvial", nonglacial_clean)]:
        if method_col not in proc_df.columns:
            continue
        grouped = proc_df.groupby(method_col)
        mech_results[proc_name] = {}
        for method, grp in grouped:
            if len(grp) < 3:
                continue
            res = ols_results(grp, f"{proc_name}_{method}")
            mech_results[proc_name][str(method)] = res
            print(f"  {proc_name}/{method}: slope={res['slope']:.4f}, p={res['p_slope']:.4f}, n={res['n']}")

    results["mechanical_coupling_stratified"] = mech_results

    # Test whether slopes differ significantly between Volumetric and non-Volumetric
    volumetric_groups = {}
    non_volumetric_groups = {}
    for proc_name, proc_df in [("Glacial", glacial_clean), ("Fluvial", nonglacial_clean)]:
        if method_col not in proc_df.columns:
            continue
        vol = proc_df[proc_df[method_col].str.contains("Volumetric", na=False, case=False)]
        non_vol = proc_df[~proc_df[method_col].str.contains("Volumetric", na=False, case=False)]
        if len(vol) >= 3:
            volumetric_groups[f"{proc_name}_Volumetric"] = vol
        if len(non_vol) >= 3:
            non_volumetric_groups[f"{proc_name}_NonVolumetric"] = non_vol

    # Compare Volumetric vs Non-Volumetric using Chow test approach
    chow_test = {}
    for key in set(volumetric_groups.keys()) & set(non_volumetric_groups.keys()):
        pass  # We'll do pairwise comparison below

    # Pairwise Chow test for each process type
    chow_results = []
    for proc_name in ["Glacial", "Fluvial"]:
        vol_key = f"{proc_name}_Volumetric"
        nonvol_key = f"{proc_name}_NonVolumetric"
        if vol_key in volumetric_groups and nonvol_key in non_volumetric_groups:
            v_df = volumetric_groups[vol_key]
            nv_df = non_volumetric_groups[nonvol_key]
            # Chow test: test if two regression lines are equal
            y1 = v_df["log_erode"].values
            x1 = v_df["log_time"].values
            y2 = nv_df["log_erode"].values
            x2 = nv_df["log_time"].values

            # Pooled SSE
            def fit_line(x, y):
                X_m = np.column_stack([np.ones(len(x)), x])
                b = np.linalg.lstsq(X_m, y, rcond=None)[0]
                return b, np.sum((y - X_m @ b)**2)

            b1, sse1 = fit_line(x1, y1)
            b2, sse2 = fit_line(x2, y2)
            sse_pooled = sse1 + sse2
            n1, n2 = len(x1), len(x2)
            k = 2  # intercept + slope
            f_stat = ((sse_pooled - (sse1 + sse2)) / k) / (sse_pooled / (n1 + n2 - 2*k))
            # Actually the Chow F-test compares restricted (pooled) vs unrestricted
            X_all = np.column_stack([np.ones(n1+n2), np.concatenate([x1, x2])])
            y_all = np.concatenate([y1, y2])
            b_pooled = np.linalg.lstsq(X_all, y_all, rcond=None)[0]
            sse_restricted = np.sum((y_all - X_all @ b_pooled)**2)
            f_chow = ((sse_restricted - sse_pooled) / k) / (sse_pooled / (n1 + n2 - 2*k))
            p_chow = 1 - stats.f.cdf(f_chow, k, n1 + n2 - 2*k)
            chow_results.append({
                "process": proc_name,
                "f_statistic": float(f_chow),
                "p_value": float(p_chow),
                "n_volumetric": n1,
                "n_non_volumetric": n2,
                "slope_volumetric": float(b1[1]),
                "slope_non_volumetric": float(b2[1])
            })
            print(f"  Chow test ({proc_name}): F={f_chow:.4f}, p={p_chow:.4f}")

    results["mechanical_coupling_chow_test"] = chow_results

    # Check if Sediment flux or Exhumation correlate with erosion rate
    mech_artifact_check = {}
    for proc_name, proc_df in [("Glacial", glacial_clean), ("Fluvial", nonglacial_clean)]:
        checks = {}
        if "Sediment flux (km3/yr)" in proc_df.columns:
            sf = proc_df.dropna(subset=["Sediment flux (km3/yr)"])
            sf = sf[sf["Sediment flux (km3/yr)"] > 0]
            if len(sf) >= 3:
                corr_sf, p_sf = stats.spearmanr(sf["log_erode"], np.log10(sf["Sediment flux (km3/yr)"]))
                checks["sediment_flux_correlation"] = {"rho": float(corr_sf), "p_value": float(p_sf), "n": len(sf)}
        for exhum_col in ["Exhumation (m)", "Exhumation min (m)", "Exhumation max (m)"]:
            if exhum_col in proc_df.columns:
                ex = proc_df.dropna(subset=[exhum_col])
                ex = ex[ex[exhum_col] > 0]
                if len(ex) >= 3:
                    corr_ex, p_ex = stats.spearmanr(ex["log_erode"], np.log10(ex[exhum_col]))
                    checks[f"exhumation_{exhum_col}_correlation"] = {"rho": float(corr_ex), "p_value": float(p_ex), "n": len(ex)}
        mech_artifact_check[proc_name] = checks
    results["mechanical_coupling_artifact_vars"] = mech_artifact_check

else:
    print("No Methodology column found.")
    results["mechanical_coupling_stratified"] = None
    results["mechanical_coupling_chow_test"] = []

# ──────────────────────────────────────────────
# 2. SOURCE/SITE CORRELATION (Clustered SE)
# ──────────────────────────────────────────────
print("\n=== 2. SOURCE/SITE CORRELATION ===")

# Identify unique References and Localities
ref_col = "Reference"
loc_col = "Locality"

unique_refs_glacial = glacial_clean[ref_col].nunique() if ref_col in glacial_clean.columns else 0
unique_locs_glacial = glacial_clean[loc_col].nunique() if loc_col in glacial_clean.columns else 0
unique_refs_nonglacial = nonglacial_clean[ref_col].nunique() if ref_col in nonglacial_clean.columns else 0
unique_locs_nonglacial = nonglacial_clean[loc_col].nunique() if loc_col in nonglacial_clean.columns else 0

print(f"Glacial: unique refs={unique_refs_glacial}, unique localities={unique_locs_glacial}")
print(f"Fluvial: unique refs={unique_refs_nonglacial}, unique localities={unique_locs_nonglacial}")

def cluster_robust_se(df, cluster_col, n_clusters_min=3):
    """Compute cluster-robust standard errors using the cluster-robust variance estimator."""
    if cluster_col not in df.columns:
        return None
    groups = df[cluster_col].dropna().unique()
    if len(groups) < n_clusters_min:
        return None
    # Use only groups with multiple observations
    group_sizes = df[cluster_col].value_counts()
    multi_obs_groups = group_sizes[group_sizes > 1].index
    if len(multi_obs_groups) < n_clusters_min:
        return None
    df_multi = df[df[cluster_col].isin(multi_obs_groups)].copy()
    if len(df_multi) < 10:
        return None

    X = df_multi["log_time"].values
    y = df_multi["log_erode"].values
    X_mat = np.column_stack([np.ones(len(X)), X])
    beta = np.linalg.lstsq(X_mat, y, rcond=None)[0]
    resid = y - X_mat @ beta

    # Cluster-robust variance: V = (X'X)^{-1} [sum_g X_g' A_g A_g' X_g] (X'X)^{-1}
    # where A_g = sum of residuals in cluster g
    XTX_inv = np.linalg.inv(X_mat.T @ X_mat)
    cluster_sum = np.zeros((2, 2))
    for g in multi_obs_groups:
        mask = df_multi[cluster_col] == g
        X_g = X_mat[mask]
        A_g = X_g.T @ resid[mask]
        cluster_sum += A_g @ A_g.T
    V_cluster = XTX_inv @ cluster_sum @ XTX_inv
    # Scale factor for small samples
    n = len(df_multi)
    g_count = len(multi_obs_groups)
    scale = (n - 1) / (n - 2) * (g_count / (g_count - 1))
    V_cluster_scaled = V_cluster * scale
    se_cluster = np.sqrt(np.diag(V_cluster_scaled))

    t_vals = beta / se_cluster
    p_vals = 2 * (1 - stats.t.cdf(np.abs(t_vals), df=g_count - 1))

    return {
        "n_obs": int(n),
        "n_clusters": int(g_count),
        "intercept": float(beta[0]),
        "slope": float(beta[1]),
        "se_intercept": float(se_cluster[0]),
        "se_slope": float(se_cluster[1]),
        "t_slope": float(t_vals[1]),
        "p_slope": float(p_vals[1])
    }

cluster_results = {}
for proc_name, proc_df in [("Glacial", glacial_clean), ("Fluvial", nonglacial_clean)]:
    cluster_results[proc_name] = {}
    for col_name, col in [("Reference", ref_col), ("Locality", loc_col)]:
        cr = cluster_robust_se(proc_df, col)
        if cr:
            cluster_results[proc_name][col_name] = cr
            print(f"  {proc_name}/{col_name}: slope={cr['slope']:.4f}, se={cr['se_slope']:.4f}, p={cr['p_slope']:.4f}, clusters={cr['n_clusters']}")
        else:
            cluster_results[proc_name][col_name] = {"error": "Insufficient clusters"}
            print(f"  {proc_name}/{col_name}: Insufficient clusters")

# Compare clustered vs OLS
comparison = {}
for proc_name in ["Glacial", "Fluvial"]:
    comp = {"OLS": baseline_glacial if proc_name == "Glacial" else baseline_fluvial}
    for cl_key, cl_val in cluster_results.get(proc_name, {}).items():
        if isinstance(cl_val, dict) and "error" not in cl_val:
            comp[f"Clustered_{cl_key}"] = cl_val
    comparison[proc_name] = comp

results["source_site_clustering"] = {
    "unique_references": {"Glacial": unique_refs_glacial, "Fluvial": unique_refs_nonglacial},
    "unique_localities": {"Glacial": unique_locs_glacial, "Fluvial": unique_locs_nonglacial},
    "clustered_results": cluster_results,
    "ols_vs_clustered_comparison": comparison
}

# ──────────────────────────────────────────────
# 3. OUTLIER SENSITIVITY
# ──────────────────────────────────────────────
print("\n=== 3. OUTLIER SENSITIVITY ===")

def outlier_sensitivity(df, process_name):
    """Test winsorization and trimming effects on regression coefficients."""
    base = ols_results(df, f"{process_name}_original")
    outcomes = {"original": base}

    # Winsorize at 1st and 99th percentiles
    q1 = np.percentile(df["log_erode"], 1)
    q99 = np.percentile(df["log_erode"], 99)
    df_winsor = df.copy()
    df_winsor["log_erode_w"] = np.clip(df["log_erode"], q1, q99)
    df_winsor_out = df_winsor.copy()
    df_winsor_out["log_erode"] = df_winsor_out["log_erode_w"]
    winsor_res = ols_results(df_winsor_out, f"{process_name}_winsorized")
    outcomes["winsorized_1_99"] = winsor_res

    # Trim top/bottom 1%
    low_cut = np.percentile(df["log_erode"], 1)
    high_cut = np.percentile(df["log_erode"], 99)
    df_trimmed = df[(df["log_erode"] >= low_cut) & (df["log_erode"] <= high_cut)]
    if len(df_trimmed) >= 10:
        trim_res = ols_results(df_trimmed, f"{process_name}_trimmed_1pct")
        outcomes["trimmed_1pct"] = trim_res

    # Compute changes
    change_info = {
        "winsorized_slope_change": float(winsor_res["slope"] - base["slope"]),
        "winsorized_p_change": float(winsor_res["p_slope"] - base["p_slope"]),
        "trimmed_slope_change": float(outcomes.get("trimmed_1pct", {}).get("slope", np.nan) - base["slope"]),
        "trimmed_p_change": float(outcomes.get("trimmed_1pct", {}).get("p_slope", np.nan) - base["p_slope"]),
        "n_original": base["n"],
        "n_winsorized": winsor_res["n"],
        "n_trimmed": outcomes.get("trimmed_1pct", {}).get("n", 0)
    }
    return outcomes, change_info

outlier_glacial, outlier_glacial_changes = outlier_sensitivity(glacial_clean, "Glacial")
outlier_fluvial, outlier_fluvial_changes = outlier_sensitivity(nonglacial_clean, "Fluvial")

results["outlier_sensitivity"] = {
    "Glacial": {"outcomes": outlier_glacial, "changes": outlier_glacial_changes},
    "Fluvial": {"outcomes": outlier_fluvial, "changes": outlier_fluvial_changes}
}

print(f"  Glacial original slope={outlier_glacial['original']['slope']:.4f}, "
      f"winsorized={outlier_glacial['winsorized_1_99']['slope']:.4f}, "
      f"trimmed={outlier_glacial.get('trimmed_1pct', {}).get('slope', 'N/A')}")
print(f"  Fluvial original slope={outlier_fluvial['original']['slope']:.4f}, "
      f"winsorized={outlier_fluvial['winsorized_1_99']['slope']:.4f}, "
      f"trimmed={outlier_fluvial.get('trimmed_1pct', {}).get('slope', 'N/A')}")

# ──────────────────────────────────────────────
# 4. THRESHOLD / BIN ANALYSIS
# ──────────────────────────────────────────────
print("\n=== 4. THRESHOLD / BIN ANALYSIS ===")

bin_edges = [0, 1, 100, 10000, np.inf]
bin_labels = ["<1 yr", "1-100 yr", "100-10000 yr", ">10000 yr"]

def bin_analysis(df, process_name):
    df = df.copy()
    df["time_bin"] = pd.cut(df["log_time"], bins=np.log10(bin_edges), labels=bin_labels, right=True)
    # Handle edge case: log10(1)=0 maps to first bin correctly
    result = {}
    for bin_label in bin_labels:
        subset = df[df["time_bin"] == bin_label]
        if len(subset) > 0:
            result[bin_label] = {
                "n": int(len(subset)),
                "mean_log_erode": float(np.mean(subset["log_erode"])),
                "median_log_erode": float(np.median(subset["log_erode"])),
                "std_log_erode": float(np.std(subset["log_erode"], ddof=1)) if len(subset) > 1 else 0,
                "sem_log_erode": float(stats.sem(subset["log_erode"])) if len(subset) > 1 else 0,
                "min_log_erode": float(np.min(subset["log_erode"])),
                "max_log_erode": float(np.max(subset["log_erode"]))
            }
    return result

glacial_bins = bin_analysis(glacial_clean, "Glacial")
fluvial_bins = bin_analysis(nonglacial_clean, "Fluvial")

results["bin_analysis"] = {
    "Glacial": glacial_bins,
    "Fluvial": fluvial_bins
}

for bin_label in bin_labels:
    g_data = glacial_bins.get(bin_label, {})
    f_data = fluvial_bins.get(bin_label, {})
    print(f"  {bin_label}: Glacial n={g_data.get('n',0)} mean={g_data.get('mean_log_erode','N/A'):.3f} | "
          f"Fluvial n={f_data.get('n',0)} mean={f_data.get('mean_log_erode','N/A'):.3f}")

# Save binned means plot
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 6))
    x_pos = np.arange(len(bin_labels))
    width = 0.35

    g_means = [glacial_bins[b]["mean_log_erode"] for b in bin_labels if b in glacial_bins]
    g_errs = [glacial_bins[b]["sem_log_erode"] for b in bin_labels if b in glacial_bins]
    f_means = [fluvial_bins[b]["mean_log_erode"] for b in bin_labels if b in fluvial_bins]
    f_errs = [fluvial_bins[b]["sem_log_erode"] for b in bin_labels if b in fluvial_bins]

    # Pad to same length
    while len(g_means) < len(bin_labels):
        g_means.append(np.nan)
        g_errs.append(np.nan)
    while len(f_means) < len(bin_labels):
        f_means.append(np.nan)
        f_errs.append(np.nan)

    ax.bar(x_pos - width/2, g_means, width, yerr=g_errs, label="Glacial", alpha=0.8, color="steelblue", capsize=3)
    ax.bar(x_pos + width/2, f_means, width, yerr=f_errs, label="Fluvial", alpha=0.8, color="darkorange", capsize=3)

    ax.set_xlabel("Timescale Bin")
    ax.set_ylabel("Mean log10(Erosion Rate mm/yr)")
    ax.set_title("Binned Mean Erosion Rates by Process and Timescale")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(bin_labels)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "binned_means.png"), dpi=150)
    plt.close()
    print("  Saved binned_means.png")
except Exception as e:
    print(f"  Plot save failed: {e}")

# ──────────────────────────────────────────────
# 5. BAYESIAN-LIKE POSTERIOR PREDICTIVE CHECK
# ──────────────────────────────────────────────
print("\n=== 5. BAYESIAN-LIKE POSTERIOR PREDICTIVE CHECK ===")

def grid_mcmc_posterior(df, process_name, n_grid=200):
    """Grid-based approximation of posterior for power-law exponent b."""
    y = df["log_erode"].values
    x = df["log_time"].values
    n = len(y)

    # Grid over slope b and intercept a
    b_grid = np.linspace(-1.5, 1.5, n_grid)
    a_grid = np.linspace(np.min(y) - 2, np.max(y) + 2, n_grid)

    # Log-likelihood (assuming normal errors with uniform prior)
    best_sigma = np.std(y - np.mean(y))  # rough initial sigma
    log_likelihood_grid = np.zeros((n_grid, n_grid))

    for i, a in enumerate(a_grid):
        for j, b in enumerate(b_grid):
            resid = y - (a + b * x)
            ll = -n/2 * np.log(2*np.pi*best_sigma**2) - np.sum(resid**2) / (2*best_sigma**2)
            log_likelihood_grid[i, j] = ll

    # Normalize to get posterior probabilities
    log_likelihood_grid -= np.max(log_likelihood_grid)  # numerical stability
    posterior = np.exp(log_likelihood_grid)
    posterior /= np.sum(posterior)

    # Marginal posterior for b
    marginal_b = np.sum(posterior, axis=0)

    # Credible intervals
    b_sorted_idx = np.argsort(b_grid)
    cumsum = np.cumsum(marginal_b[b_sorted_idx])
    cumsum /= cumsum[-1]

    ci_low_idx = np.searchsorted(cumsum, 0.025)
    ci_high_idx = np.searchsorted(cumsum, 0.975)

    b_mean = np.sum(b_grid * marginal_b)
    b_std = np.sqrt(np.sum((b_grid - b_mean)**2 * marginal_b))

    # Check if posterior mass of b crosses zero
    b_above_zero = np.sum(marginal_b[b_grid > 0])
    b_below_zero = np.sum(marginal_b[b_grid < 0])

    return {
        "process": process_name,
        "n": n,
        "b_mean": float(b_mean),
        "b_std": float(b_std),
        "b_ci_lower": float(b_grid[b_sorted_idx[ci_low_idx]]) if ci_low_idx < len(b_grid) else None,
        "b_ci_upper": float(b_grid[b_sorted_idx[ci_high_idx]]) if ci_high_idx < len(b_grid) else None,
        "prob_b_positive": float(b_above_zero),
        "prob_b_negative": float(b_below_zero),
        "b_mode": float(b_grid[np.argmax(marginal_b)])
    }

bayes_glacial = grid_mcmc_posterior(glacial_clean, "Glacial")
bayes_fluvial = grid_mcmc_posterior(nonglacial_clean, "Fluvial")

results["bayesian_posterior"] = {
    "Glacial": bayes_glacial,
    "Fluvial": bayes_fluvial
}

print(f"  Glacial: b_mean={bayes_glacial['b_mean']:.4f}, CI=[{bayes_glacial['b_ci_lower']:.4f}, {bayes_glacial['b_ci_upper']:.4f}], "
      f"P(b>0)={bayes_glacial['prob_b_positive']:.3f}")
print(f"  Fluvial: b_mean={bayes_fluvial['b_mean']:.4f}, CI=[{bayes_fluvial['b_ci_lower']:.4f}, {bayes_fluvial['b_ci_upper']:.4f}], "
      f"P(b>0)={bayes_fluvial['prob_b_positive']:.3f}")

# Also run for combined dataset
bayes_combined = grid_mcmc_posterior(combined, "Combined")
results["bayesian_posterior"]["Combined"] = bayes_combined

# ──────────────────────────────────────────────
# 6. PRIOR COMPILATION CROSS-CHECK
# ──────────────────────────────────────────────
print("\n=== 6. PRIOR COMPILATION CROSS-CHECK ===")

prior_results = {}

# GloRiSe
try:
    glorise = pd.read_csv(os.path.join(BASE, "data/raw/prior compilations/GloRiSe/GloRiSe combined.tsv"), sep="\t")
    print(f"GloRiSe rows: {len(glorise)}, columns: {list(glorise.columns)[:10]}...")

    # GloRiSe has different column names; look for erosion rate and time interval
    erode_col = None
    time_col = None
    for col in glorise.columns:
        if "Erosion rate" in col:
            erode_col = col
        if "Time interval" in col:
            time_col = col

    if erode_col and time_col:
        glorise_valid = glorise.dropna(subset=[erode_col, time_col])
        glorise_valid = glorise_valid[glorise_valid[erode_col] > 0]
        glorise_valid = glorise_valid[glorise_valid[time_col] > 0]
        glorise_valid["log_erode"] = np.log10(glorise_valid[erode_col])
        glorise_valid["log_time"] = np.log10(glorise_valid[time_col])

        if len(glorise_valid) >= 5:
            gr_ols = ols_results(glorise_valid, "GloRiSe")
            prior_results["GloRiSe"] = {
                "n": int(len(glorise_valid)),
                "erode_col": erode_col,
                "time_col": time_col,
                "erode_rate_stats": {
                    "mean": float(np.mean(glorise_valid[erode_col])),
                    "median": float(np.median(glorise_valid[erode_col])),
                    "std": float(np.std(glorise_valid[erode_col])),
                    "min": float(np.min(glorise_valid[erode_col])),
                    "max": float(np.max(glorise_valid[erode_col]))
                },
                "regression": gr_ols
            }
            print(f"  GloRiSe: n={len(glorise_valid)}, slope={gr_ols['slope']:.4f}, p={gr_ols['p_slope']:.4f}")
        else:
            prior_results["GloRiSe"] = {"error": "Too few valid rows", "n_available": len(glorise_valid)}
    else:
        prior_results["GloRiSe"] = {"error": "Could not find erosion rate or time interval columns",
                                     "columns": list(glorise.columns)}
except Exception as e:
    prior_results["GloRiSe"] = {"error": str(e)}

# OCTOPUS
try:
    octopus = pd.read_csv(os.path.join(BASE, "data/raw/prior compilations/OCTOPUS/octopusdata.tsv"), sep="\t")
    print(f"OCTOPUS rows: {len(octopus)}, columns: {list(octopus.columns)[:10]}...")

    # OCTOPUS uses eal_mmkyr (mm/kyr) or similar columns
    erode_col_oct = None
    time_col_oct = None

    # Look for erosion rate columns
    for col in octopus.columns:
        if "eal" in col.lower() or "erosion" in col.lower():
            erode_col_oct = col
        if "time" in col.lower() or "age" in col.lower():
            time_col_oct = col

    # Try specific known columns
    if erode_col_oct is None:
        for candidate in ["eal_mmkyr", "eal_gcmyr", "eal_err"]:
            if candidate in octopus.columns:
                erode_col_oct = candidate
                break

    if erode_col_oct and time_col_oct:
        oct_valid = octopus.dropna(subset=[erode_col_oct, time_col_oct])
        oct_valid = oct_valid[oct_valid[erode_col_oct] > 0]
        oct_valid = oct_valid[oct_valid[time_col_oct] > 0]

        if len(oct_valid) >= 5:
            # Convert units if needed (mm/kyr -> mm/yr)
            if "mmkyr" in erode_col_oct.lower():
                oct_valid["erode_mm_yr"] = oct_valid[erode_col_oct] / 1000.0
                oct_valid["log_erode"] = np.log10(oct_valid["erode_mm_yr"])
            elif "gcmyr" in erode_col_oct.lower():
                oct_valid["erode_mm_yr"] = oct_valid[erode_col_oct] * 1000.0
                oct_valid["log_erode"] = np.log10(oct_valid["erode_mm_yr"])
            else:
                oct_valid["log_erode"] = np.log10(oct_valid[erode_col_oct])

            oct_valid["log_time"] = np.log10(oct_valid[time_col_oct])

            oc_ols = ols_results(oct_valid, "OCTOPUS")
            prior_results["OCTOPUS"] = {
                "n": int(len(oct_valid)),
                "erode_col": erode_col_oct,
                "time_col": time_col_oct,
                "unit_note": "Converted if needed",
                "erode_rate_stats": {
                    "mean": float(np.mean(oct_valid["erode_mm_yr"])),
                    "median": float(np.median(oct_valid["erode_mm_yr"])),
                    "std": float(np.std(oct_valid["erode_mm_yr"])),
                    "min": float(np.min(oct_valid["erode_mm_yr"])),
                    "max": float(np.max(oct_valid["erode_mm_yr"]))
                },
                "regression": oc_ols
            }
            print(f"  OCTOPUS: n={len(oct_valid)}, slope={oc_ols['slope']:.4f}, p={oc_ols['p_slope']:.4f}")
        else:
            prior_results["OCTOPUS"] = {"error": "Too few valid rows", "n_available": len(oct_valid)}
    else:
        # OCTOPUS has no time interval column; report distribution stats only
        erode_col_oct = "eal_mmkyr" if "eal_mmkyr" in octopus.columns else None
        if erode_col_oct:
            oct_valid_erode = octopus.dropna(subset=[erode_col_oct])
            oct_valid_erode = oct_valid_erode[oct_valid_erode[erode_col_oct] > 0]
            # Convert mm/kyr to mm/yr
            oct_valid_erode["erode_mm_yr"] = oct_valid_erode[erode_col_oct] / 1000.0
            prior_results["OCTOPUS"] = {
                "n": int(len(oct_valid_erode)),
                "erode_col": erode_col_oct,
                "note": "No time interval column available; regression not possible. Distribution stats only.",
                "unit_note": f"{erode_col_oct} is in mm/kyr, converted to mm/yr",
                "erode_rate_stats": {
                    "mean": float(np.mean(oct_valid_erode["erode_mm_yr"])),
                    "median": float(np.median(oct_valid_erode["erode_mm_yr"])),
                    "std": float(np.std(oct_valid_erode["erode_mm_yr"])),
                    "min": float(np.min(oct_valid_erode["erode_mm_yr"])),
                    "max": float(np.max(oct_valid_erode["erode_mm_yr"]))
                }
            }
            print(f"  OCTOPUS: n={len(oct_valid_erode)}, median={np.median(oct_valid_erode['erode_mm_yr']):.4f} mm/yr")
        else:
            prior_results["OCTOPUS"] = {"error": "Could not find erosion rate column",
                                         "columns": list(octopus.columns)}
except Exception as e:
    prior_results["OCTOPUS"] = {"error": str(e)}

results["prior_compilations"] = prior_results

# ──────────────────────────────────────────────
# Cross-dataset consistency check
# ──────────────────────────────────────────────
print("\n=== CROSS-DATASET CONSISTENCY ===")

# Compare erosion rate distributions
def distribution_summary(df, label):
    erode = df["Erosion rate (mm/yr)"].dropna()
    return {
        "label": label,
        "n": int(len(erode)),
        "mean": float(np.mean(erode)),
        "median": float(np.median(erode)),
        "std": float(np.std(erode)),
        "geometric_mean": float(np.exp(np.mean(np.log(erode)))),
        "log_mean": float(np.mean(np.log10(erode))),
        "log_std": float(np.std(np.log10(erode))),
        "q025": float(np.percentile(erode, 25)),
        "q75": float(np.percentile(erode, 75)),
        "min": float(np.min(erode)),
        "max": float(np.max(erode))
    }

dist_glacial = distribution_summary(glacial_clean, "Glacial")
dist_fluvial = distribution_summary(nonglacial_clean, "Fluvial")

# Mann-Whitney U test
mw_stat, mw_p = stats.mannwhitneyu(
    glacial_clean["Erosion rate (mm/yr)"].dropna(),
    nonglacial_clean["Erosion rate (mm/yr)"].dropna(),
    alternative="two-sided"
)

results["distribution_comparison"] = {
    "Glacial": dist_glacial,
    "Fluvial": dist_fluvial,
    "mann_whitney_u": {"statistic": float(mw_stat), "p_value": float(mw_p)}
}
print(f"  Mann-Whitney U: stat={mw_stat:.0f}, p={mw_p:.4f}")

# Kolmogorov-Smirnov test
ks_stat, ks_p = stats.ks_2samp(
    glacial_clean["log_erode"].values,
    nonglacial_clean["log_erode"].values
)
results["distribution_comparison"]["kolmogorov_smirnov"] = {"statistic": float(ks_stat), "p_value": float(ks_p)}
print(f"  KS test: stat={ks_stat:.4f}, p={ks_p:.4f}")

# ──────────────────────────────────────────────
# Summary of all findings
# ──────────────────────────────────────────────
print("\n=== SUMMARY ===")
print(f"Baseline Glacial: slope={baseline_glacial['slope']:.4f}, p={baseline_glacial['p_slope']:.4f}")
print(f"Baseline Fluvial: slope={baseline_fluvial['slope']:.4f}, p={baseline_fluvial['p_slope']:.4f}")
print(f"Bayesian Glacial b_mean={bayes_glacial['b_mean']:.4f}, P(b>0)={bayes_glacial['prob_b_positive']:.3f}")
print(f"Bayesian Fluvial b_mean={bayes_fluvial['b_mean']:.4f}, P(b>0)={bayes_fluvial['prob_b_positive']:.3f}")

# Write JSON results
with open(os.path.join(OUT, "robustness_results.json"), "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved robustness_results.json to {OUT}")

print("\nDone.")
