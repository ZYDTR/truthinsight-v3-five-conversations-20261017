#!/usr/bin/env python3
"""
Core statistical analysis: Glacial vs Nonglacial erosion rates.
Examines how erosion rate relates to observation timescale, process category,
and measurement method. Separates geological process, observation window,
and mathematical coupling.
"""

import json
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

warnings.filterwarnings('ignore')


def fit_ols_array(x, y):
    """Fit OLS on numpy arrays, return results as dict."""
    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    # When X is a plain ndarray, params/pvalues are also ndarrays
    if hasattr(model.params, 'index'):
        p = dict(zip(model.params.index, model.params))
        pv = dict(zip(model.pvalues.index, model.pvalues))
        ci = {str(k): list(v) for k, v in model.conf_int().items()}
    else:
        p = {"const": float(model.params[0]), "log_time": float(model.params[1])}
        pv = {"const": float(model.pvalues[0]), "log_time": float(model.pvalues[1])}
        ci = {"const": [float(model.conf_int()[0][0]), float(model.conf_int()[0][1])],
              "log_time": [float(model.conf_int()[1][0]), float(model.conf_int()[1][1])]}
    return {
        "model": model,
        "params": p,
        "pvalues": pv,
        "conf_int": ci,
        "rsquared": float(model.rsquared),
        "adj_rsquared": float(model.rsquared_adj),
        "aic": float(model.aic),
        "bic": float(model.bic),
        "nobs": int(model.nobs),
    }


# ============================================================
# 1. DATA PREPARATION
# ============================================================
print("=" * 70)
print("DATA PREPARATION")
print("=" * 70)

glacial = pd.read_csv(
    "/data/user/conversations/conv-46b0a68e-ac73-49c3-ba26-bbe4d51ce35a/project/data/raw/glacial_erosion_Earth.tsv",
    sep="\t"
)
nonglacial = pd.read_csv(
    "/data/user/conversations/conv-46b0a68e-ac73-49c3-ba26-bbe4d51ce35a/project/data/raw/nonglacial_erosion_Earth.tsv",
    sep="\t"
)

# Assign process category
glacial["process_category"] = "Glacial"
nonglacial["process_category"] = "Fluvial"

# Combine
df = pd.concat([glacial, nonglacial], ignore_index=True)

# Handle missing values for key columns
for col in ["Erosion rate (mm/yr)", "Time interval (yr)", "Methodology"]:
    print(f"\n{col} missing before handling:")
    print(f"  Total NaN: {df[col].isna().sum()}")

# For log analyses, exclude rows with erosion_rate <= 0 or time_interval <= 0
df_log = df.copy()
df_log["log_erode"] = np.where(
    df_log["Erosion rate (mm/yr)"] > 0,
    np.log10(df_log["Erosion rate (mm/yr)"]),
    np.nan
)
df_log["log_time"] = np.where(
    df_log["Time interval (yr)"] > 0,
    np.log10(df_log["Time interval (yr)"]),
    np.nan
)

valid_mask = (
    df_log["log_erode"].notna()
    & df_log["log_time"].notna()
    & np.isfinite(df_log["log_erode"])
    & np.isfinite(df_log["log_time"])
)
df_valid = df_log[valid_mask].copy()

print(f"\nTotal rows: {len(df)}")
print(f"Rows valid for log analysis: {len(df_valid)}")
print(f"Excluded (<=0 or NaN): {len(df) - len(df_valid)}")

# Methodology groupings
method_groups = {
    "Volumetric": "Volumetric",
    "Cosmogenic surface": "Cosmogenic",
    "Cosmogenic detrital": "Cosmogenic",
    "Thermochronometric": "Thermochronometric",
    "Relief": "Relief",
}
df_valid["method_group"] = df_valid["Methodology"].map(method_groups).fillna("Other")

print("\nMethodology groups distribution:")
print(df_valid.groupby(["process_category", "method_group"]).size().unstack(fill_value=0))

# ============================================================
# 2. PRIMARY ANALYSIS - Log erosion rate vs timescale
# ============================================================
print("\n" + "=" * 70)
print("PRIMARY ANALYSIS: Log Erosion Rate vs Timescale")
print("=" * 70)

regression_results = {}

# Per-group OLS regressions
groups = df_valid.groupby(["process_category", "method_group"])
group_regressions = {}

for (proc, meth), grp in groups:
    if len(grp) < 3:
        continue
    x = grp["log_time"].values
    y = grp["log_erode"].values

    res = fit_ols_array(x, y)

    key = f"{proc}_{meth}"
    group_regressions[key] = {
        "process_category": proc,
        "method_group": meth,
        "n": int(len(grp)),
        "slope": float(res["params"].get("log_time", res["params"].get(1, np.nan))),
        "intercept": float(res["params"].get("const", res["params"].get(0, np.nan))),
        "R_squared": res["rsquared"],
        "adj_R_squared": res["adj_rsquared"],
        "p_value_slope": float(res["pvalues"].get("log_time", res["pvalues"].get(1, np.nan))),
        "ci_lower_slope": float(res["conf_int"].get("log_time", [np.nan, np.nan])[0]),
        "ci_upper_slope": float(res["conf_int"].get("log_time", [np.nan, np.nan])[1]),
        "AIC": res["aic"],
        "BIC": res["bic"],
    }

    slope_val = res["params"].get("log_time", res["params"].get(1, 0))
    p_val = res["pvalues"].get("log_time", res["pvalues"].get(1, 1))
    sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
    print(f"  {key}: slope={slope_val:.4f}, R²={res['rsquared']:.3f}, p={p_val:.2e} [{sig}] (n={len(grp)})")

regression_results["group_regressions"] = group_regressions

# Pooled model with interaction
print("\nPooled model with interactions:")
formula = "log_erode ~ log_time * process_category + log_time * method_group + process_category + method_group"
pooled_model = ols(formula, data=df_valid).fit()
print(pooled_model.summary().as_text())

pooled_summary = {
    "formula": formula,
    "n_obs": pooled_model.nobs,
    "R_squared": float(pooled_model.rsquared),
    "adj_R_squared": float(pooled_model.rsquared_adj),
    "AIC": float(pooled_model.aic),
    "BIC": float(pooled_model.bic),
    "parameters": {str(k): float(v) for k, v in pooled_model.params.items()},
    "p_values": {str(k): float(v) for k, v in pooled_model.pvalues.items()},
    "conf_int": {str(k): list(v) for k, v in pooled_model.conf_int().to_dict().items()},
}
regression_results["pooled_interaction_model"] = pooled_summary

# Also fit without method interaction (simpler pooled)
formula2 = "log_erode ~ log_time * process_category + method_group + process_category"
pooled_model2 = ols(formula2, data=df_valid).fit()
pooled_summary2 = {
    "formula": formula2,
    "n_obs": pooled_model2.nobs,
    "R_squared": float(pooled_model2.rsquared),
    "adj_R_squared": float(pooled_model2.rsquared_adj),
    "AIC": float(pooled_model2.aic),
    "BIC": float(pooled_model2.bic),
    "parameters": {str(k): float(v) for k, v in pooled_model2.params.items()},
    "p_values": {str(k): float(v) for k, v in pooled_model2.pvalues.items()},
    "conf_int": {str(k): list(v) for k, v in pooled_model2.conf_int().to_dict().items()},
}
regression_results["pooled_main_effect_model"] = pooled_summary2

# ANOVA comparing models
anova_table = anova_lm(pooled_model2, pooled_model)
anova_cols = anova_table.columns.tolist()
anova_dict = {}
for col in anova_cols:
    try:
        anova_dict[col] = anova_table[col].tolist()
    except Exception:
        anova_dict[col] = anova_table[col].values.tolist()
regression_results["anova_pooled_models"] = {
    "term": anova_table.index.tolist(),
    **anova_dict,
}

# ============================================================
# 3. PROCESS COMPARISON
# ============================================================
print("\n" + "=" * 70)
print("PROCESS COMPARISON: Glacial vs Fluvial")
print("=" * 70)

comparison_results = {}

# Simple mean comparison
glacial_rates = df_valid[df_valid["process_category"] == "Glacial"]["log_erode"]
fluvial_rates = df_valid[df_valid["process_category"] == "Fluvial"]["log_erode"]

t_stat, t_pval = stats.ttest_ind(glacial_rates, fluvial_rates, equal_var=False)
mw_stat, mw_pval = stats.mannwhitneyu(fluvial_rates, glacial_rates, alternative="two-sided")

comparison_results["simple_mean_comparison"] = {
    "glacial_n": int(len(glacial_rates)),
    "glacial_mean_log": float(glacial_rates.mean()),
    "glacial_median_log": float(glacial_rates.median()),
    "glacial_std_log": float(glacial_rates.std()),
    "fluvial_n": int(len(fluvial_rates)),
    "fluvial_mean_log": float(fluvial_rates.mean()),
    "fluvial_median_log": float(fluvial_rates.median()),
    "fluvial_std_log": float(fluvial_rates.std()),
    "mean_difference": float(glacial_rates.mean() - fluvial_rates.mean()),
    "welch_ttest": {"t_stat": float(t_stat), "p_value": float(t_pval)},
    "mann_whitney": {"U_stat": float(mw_stat), "p_value": float(mw_pval)},
}

print(f"  Welch t-test: t={t_stat:.4f}, p={t_pval:.2e}")
print(f"  Mann-Whitney: U={mw_stat:.0f}, p={mw_pval:.2e}")
print(f"  Mean difference (G-F): {glacial_rates.mean() - fluvial_rates.mean():.4f}")

# ANCOVA controlling for log10(time_interval)
ancova_formula = "log_erode ~ process_category + log_time"
ancova_model = ols(ancova_formula, data=df_valid).fit()
ancova_table = anova_lm(ancova_model)
print("\n  ANCOVA table:")
print(ancova_table.to_string())

comparison_results["ancova"] = {
    "formula": ancova_formula,
    "n_obs": int(ancova_model.nobs),
    "R_squared": float(ancova_model.rsquared),
    "ANOVA": {
        "term": ancova_table.index.tolist(),
        "df": ancova_table["df"].tolist(),
        "sum_sq": ancova_table["sum_sq"].tolist(),
        "mean_sq": ancova_table["mean_sq"].tolist(),
        "F": ancova_table["F"].tolist(),
        "PR_gt_F": ancova_table["PR(>F)"].tolist(),
    },
    "coefficients": {str(k): float(v) for k, v in ancova_model.params.items()},
    "ci": {str(k): list(v) for k, v in ancova_model.conf_int().to_dict().items()},
}

# ANCOVA also with method_group as covariate
ancova2_formula = "log_erode ~ process_category + log_time + method_group"
ancova2_model = ols(ancova2_formula, data=df_valid).fit()
ancova2_table = anova_lm(ancova2_model)
comparison_results["ancova_with_method"] = {
    "formula": ancova2_formula,
    "n_obs": int(ancova2_model.nobs),
    "R_squared": float(ancova2_model.rsquared),
    "ANOVA": {
        "term": ancova2_table.index.tolist(),
        "df": ancova2_table["df"].tolist(),
        "sum_sq": ancova2_table["sum_sq"].tolist(),
        "mean_sq": ancova2_table["mean_sq"].tolist(),
        "F": ancova2_table["F"].tolist(),
        "PR_gt_F": ancova2_table["PR(>F)"].tolist(),
    },
    "coefficients": {str(k): float(v) for k, v in ancova2_model.params.items()},
    "ci": {str(k): list(v) for k, v in ancova2_model.conf_int().to_dict().items()},
}

# ============================================================
# 4. METHOD STRATIFICATION
# ============================================================
print("\n" + "=" * 70)
print("METHOD STRATIFICATION")
print("=" * 70)

method_stats = {}
min_n = 10

# Count observations per method across both datasets
method_counts = df_valid.groupby("method_group").size()
eligible_methods = method_counts[method_counts >= min_n].index.tolist()
print(f"Methods with >= {min_n} observations: {eligible_methods}")

for meth in eligible_methods:
    meth_data = df_valid[df_valid["method_group"] == meth]
    gl_meth = meth_data[meth_data["process_category"] == "Glacial"]["log_erode"]
    flu_meth = meth_data[meth_data["process_category"] == "Fluvial"]["log_erode"]

    stats_dict = {
        "n_total": int(len(meth_data)),
        "glacial_n": int(len(gl_meth)),
        "fluvial_n": int(len(flu_meth)),
        "all_mean_log": float(meth_data["log_erode"].mean()),
        "all_median_log": float(meth_data["log_erode"].median()),
        "all_std_log": float(meth_data["log_erode"].std()),
        "glacial_mean_log": float(gl_meth.mean()) if len(gl_meth) > 0 else None,
        "glacial_median_log": float(gl_meth.median()) if len(gl_meth) > 0 else None,
        "glacial_std_log": float(gl_meth.std()) if len(gl_meth) > 0 else None,
        "fluvial_mean_log": float(flu_meth.mean()) if len(flu_meth) > 0 else None,
        "fluvial_median_log": float(flu_meth.median()) if len(flu_meth) > 0 else None,
        "fluvial_std_log": float(flu_meth.std()) if len(flu_meth) > 0 else None,
    }

    # Test difference between glacial and fluvial within this method
    if len(gl_meth) >= 3 and len(flu_meth) >= 3:
        t_s, t_p = stats.ttest_ind(gl_meth, flu_meth, equal_var=False)
        mw_s, mw_p = stats.mannwhitneyu(flu_meth, gl_meth, alternative="two-sided")
        stats_dict["welch_ttest"] = {"t_stat": float(t_s), "p_value": float(t_p)}
        stats_dict["mann_whitney"] = {"U_stat": float(mw_s), "p_value": float(mw_p)}
    else:
        stats_dict["note"] = "Insufficient sample for statistical test"

    method_stats[meth] = stats_dict
    print(f"\n  {meth}:")
    print(f"    Total n={stats_dict['n_total']}, Glacial n={stats_dict['glacial_n']}, Fluvial n={stats_dict['fluvial_n']}")
    print(f"    All mean(log10 rate)={stats_dict['all_mean_log']:.3f}")
    if 'welch_ttest' in stats_dict:
        print(f"    Welch t-test: t={stats_dict['welch_ttest']['t_stat']:.4f}, p={stats_dict['welch_ttest']['p_value']:.2e}")

comparison_results["method_stratification"] = method_stats

# ============================================================
# 5. NULL BASELINE MODELS
# ============================================================
print("\n" + "=" * 70)
print("NULL BASELINE MODELS")
print("=" * 70)

null_models = {}

# Model 1: Intercept-only (grand mean)
null1 = ols("log_erode ~ 1", data=df_valid).fit()
null_models["intercept_only"] = {
    "formula": "log_erode ~ 1",
    "n_obs": null1.nobs,
    "R_squared": float(null1.rsquared),
    "adj_R_squared": float(null1.rsquared_adj),
    "AIC": float(null1.aic),
    "BIC": float(null1.bic),
    "intercept": float(null1.params["Intercept"]),
}
print(f"  Intercept-only: AIC={null1.aic:.1f}, BIC={null1.bic:.1f}, intercept={null1.params['Intercept']:.4f}")

# Model 2: Process-category only
null2 = ols("log_erode ~ process_category", data=df_valid).fit()
null_models["process_only"] = {
    "formula": "log_erode ~ process_category",
    "n_obs": null2.nobs,
    "R_squared": float(null2.rsquared),
    "adj_R_squared": float(null2.rsquared_adj),
    "AIC": float(null2.aic),
    "BIC": float(null2.bic),
    "parameters": {str(k): float(v) for k, v in null2.params.items()},
    "p_values": {str(k): float(v) for k, v in null2.pvalues.items()},
}
print(f"  Process-only: AIC={null2.aic:.1f}, BIC={null2.bic:.1f}, R²={null2.rsquared:.4f}")

# Model 3: Method-group only
null3 = ols("log_erode ~ method_group", data=df_valid).fit()
null_models["method_only"] = {
    "formula": "log_erode ~ method_group",
    "n_obs": null3.nobs,
    "R_squared": float(null3.rsquared),
    "adj_R_squared": float(null3.rsquared_adj),
    "AIC": float(null3.aic),
    "BIC": float(null3.bic),
    "parameters": {str(k): float(v) for k, v in null3.params.items()},
    "p_values": {str(k): float(v) for k, v in null3.pvalues.items()},
}
print(f"  Method-only: AIC={null3.aic:.1f}, BIC={null3.bic:.1f}, R²={null3.rsquared:.4f}")

# Model 4: Timescale only
null4 = ols("log_erode ~ log_time", data=df_valid).fit()
null_models["timescale_only"] = {
    "formula": "log_erode ~ log_time",
    "n_obs": null4.nobs,
    "R_squared": float(null4.rsquared),
    "adj_R_squared": float(null4.rsquared_adj),
    "AIC": float(null4.aic),
    "BIC": float(null4.bic),
    "parameters": {str(k): float(v) for k, v in null4.params.items()},
    "p_values": {str(k): float(v) for k, v in null4.pvalues.items()},
}
print(f"  Timescale-only: AIC={null4.aic:.1f}, BIC={null4.bic:.1f}, R²={null4.rsquared:.4f}")

# Model 5: Timescale + Process (main effects)
null5 = ols("log_erode ~ log_time + process_category", data=df_valid).fit()
null_models["timescale_plus_process"] = {
    "formula": "log_erode ~ log_time + process_category",
    "n_obs": null5.nobs,
    "R_squared": float(null5.rsquared),
    "adj_R_squared": float(null5.rsquared_adj),
    "AIC": float(null5.aic),
    "BIC": float(null5.bic),
    "parameters": {str(k): float(v) for k, v in null5.params.items()},
    "p_values": {str(k): float(v) for k, v in null5.pvalues.items()},
}
print(f"  Timescale+Process: AIC={null5.aic:.1f}, BIC={null5.bic:.1f}, R²={null5.rsquared:.4f}")

# Model 6: Timescale + Method (main effects)
null6 = ols("log_erode ~ log_time + method_group", data=df_valid).fit()
null_models["timescale_plus_method"] = {
    "formula": "log_erode ~ log_time + method_group",
    "n_obs": null6.nobs,
    "R_squared": float(null6.rsquared),
    "adj_R_squared": float(null6.rsquared_adj),
    "AIC": float(null6.aic),
    "BIC": float(null6.bic),
    "parameters": {str(k): float(v) for k, v in null6.params.items()},
    "p_values": {str(k): float(v) for k, v in null6.pvalues.items()},
}
print(f"  Timescale+Method: AIC={null6.aic:.1f}, BIC={null6.bic:.1f}, R²={null6.rsquared:.4f}")

# Model 7: Full main effects (Timescale + Process + Method)
null7 = ols("log_erode ~ log_time + process_category + method_group", data=df_valid).fit()
null_models["full_main_effects"] = {
    "formula": "log_erode ~ log_time + process_category + method_group",
    "n_obs": null7.nobs,
    "R_squared": float(null7.rsquared),
    "adj_R_squared": float(null7.rsquared_adj),
    "AIC": float(null7.aic),
    "BIC": float(null7.bic),
    "parameters": {str(k): float(v) for k, v in null7.params.items()},
    "p_values": {str(k): float(v) for k, v in null7.pvalues.items()},
}
print(f"  Full main effects: AIC={null7.aic:.1f}, BIC={null7.bic:.1f}, R²={null7.rsquared:.4f}")

# Model comparison table
model_comparison = []
for name, m in null_models.items():
    model_comparison.append({
        "model": name,
        "formula": m["formula"],
        "n": m["n_obs"],
        "R²": m["R_squared"],
        "adj_R²": m["adj_R_squared"],
        "AIC": m["AIC"],
        "BIC": m["BIC"],
    })
# Add pooled models
for label, m in [("pooled_interaction", pooled_summary), ("pooled_main", pooled_summary2)]:
    model_comparison.append({
        "model": label,
        "formula": m["formula"],
        "n": m["n_obs"],
        "R²": m["R_squared"],
        "adj_R²": m["adj_R_squared"],
        "AIC": m["AIC"],
        "BIC": m["BIC"],
    })

model_comparison.sort(key=lambda x: x["AIC"])
print("\nModel ranking by AIC:")
for i, mc in enumerate(model_comparison):
    print(f"  {i+1}. {mc['model']:25s} AIC={mc['AIC']:10.1f}  BIC={mc['BIC']:10.1f}  R²={mc['R²']:.4f}")

regression_results["null_models"] = null_models
regression_results["model_comparison"] = model_comparison

# ============================================================
# 6. ROBUSTNESS CHECK: Exclude potential mechanical coupling
# ============================================================
print("\n" + "=" * 70)
print("ROBUSTNESS: Volumetric method (potential mechanical coupling)")
print("=" * 70)

# Volumetric methods may have mechanical coupling between rate and timescale
# (fixed thickness assumption). Check if the timescale slope persists
# after excluding volumetric methods.
df_no_volumetric = df_valid[df_valid["method_group"] != "Volumetric"].copy()
print(f"  Rows after removing Volumetric: {len(df_no_volumetric)}")

if len(df_no_volumetric) > 10:
    res_nv = fit_ols_array(df_no_volumetric["log_time"].values, df_no_volumetric["log_erode"].values)
    slope_nv = res_nv["params"].get("log_time", res_nv["params"].get(1, np.nan))
    p_nv = res_nv["pvalues"].get("log_time", res_nv["pvalues"].get(1, 1))
    print(f"  Non-volumetric timescale slope: {slope_nv:.4f} (p={p_nv:.2e})")
    print(f"  Non-volumetric R²: {res_nv['rsquared']:.4f}")

    regression_results["robustness_no_volumetric"] = {
        "n": len(df_no_volumetric),
        "slope": float(slope_nv),
        "p_value": float(p_nv),
        "R_squared": res_nv["rsquared"],
        "intercept": float(res_nv["params"].get("const", res_nv["params"].get(0, np.nan))),
    }

# Also check cosmogenic-only
df_cosmo = df_valid[df_valid["method_group"] == "Cosmogenic"].copy()
if len(df_cosmo) > 10:
    res_c = fit_ols_array(df_cosmo["log_time"].values, df_cosmo["log_erode"].values)
    slope_c = res_c["params"].get("log_time", res_c["params"].get(1, np.nan))
    p_c = res_c["pvalues"].get("log_time", res_c["pvalues"].get(1, 1))
    print(f"  Cosmogenic timescale slope: {slope_c:.4f} (p={p_c:.2e})")
    print(f"  Cosmogenic R²: {res_c['rsquared']:.4f}")

    regression_results["robustness_cosmogenic_only"] = {
        "n": len(df_cosmo),
        "slope": float(slope_c),
        "p_value": float(p_c),
        "R_squared": res_c["rsquared"],
        "intercept": float(res_c["params"].get("const", res_c["params"].get(0, np.nan))),
    }

# ============================================================
# 7. TIMESCALE DISTRIBUTION BY PROCESS
# ============================================================
print("\n" + "=" * 70)
print("TIMESCALE DISTRIBUTION")
print("=" * 70)

for proc in ["Glacial", "Fluvial"]:
    pdata = df_valid[df_valid["process_category"] == proc]
    print(f"\n  {proc}:")
    print(f"    n = {len(pdata)}")
    print(f"    Time interval: median={pdata['Time interval (yr)'].median():.1f}, "
          f"mean={pdata['Time interval (yr)'].mean():.1f}, "
          f"range=[{pdata['Time interval (yr)'].min():.1f}, {pdata['Time interval (yr)'].max():.1f}]")
    print(f"    log10(time): mean={pdata['log_time'].mean():.3f}, std={pdata['log_time'].std():.3f}")
    print(f"    Erosion rate: median={pdata['Erosion rate (mm/yr)'].median():.4f}, "
          f"mean={pdata['Erosion rate (mm/yr)'].mean():.4f}")
    print(f"    log10(rate): mean={pdata['log_erode'].mean():.3f}, std={pdata['log_erode'].std():.3f}")

# ============================================================
# SAVE RESULTS
# ============================================================
print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

# Save regression results
with open("/data/user/conversations/conv-46b0a68e-ac73-49c3-ba26-bbe4d51ce35a/project/working/subB/regression_results.json", "w") as f:
    json.dump(regression_results, f, indent=2, default=str)
print("Saved: working/subB/regression_results.json")

# Save comparison results
with open("/data/user/conversations/conv-46b0a68e-ac73-49c3-ba26-bbe4d51ce35a/project/working/subB/comparison_results.json", "w") as f:
    json.dump(comparison_results, f, indent=2, default=str)
print("Saved: working/subB/comparison_results.json")

# Generate summary markdown
summary_lines = []
summary_lines.append("# Core Analysis Summary: Glacial vs Nonglacial Erosion Rates\n")
summary_lines.append("## Data Overview\n")
summary_lines.append(f"- **Total observations**: {len(df)}")
summary_lines.append(f"- **Valid for log analysis**: {len(df_valid)}")
summary_lines.append(f"- **Glacial**: {len(glacial_rates)} | **Fluvial**: {len(fluvial_rates)}")
summary_lines.append(f"- **Missing erosion rate (nonglacial)**: {(df['Erosion rate (mm/yr)']==0).sum()}")
summary_lines.append(f"- **Missing time interval (nonglacial)**: {df['Time interval (yr)'].isna().sum()}")

summary_lines.append("\n## Key Finding 1: Timescale-Erosion Relationship\n")
summary_lines.append("The relationship between log10(errosion rate) and log10(timescale) was tested across all methodology groups.\n")
summary_lines.append("| Group | n | Slope | R² | p-value | Significance |")
summary_lines.append("|-------|---|-------|-----|---------|-------------|")
for key, reg in sorted(group_regressions.items()):
    p = reg["p_value_slope"]
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
    summary_lines.append(f"| {key} | {reg['n']} | {reg['slope']:.4f} | {reg['R_squared']:.3f} | {p:.2e} | {sig} |")

summary_lines.append("\n### Overall timescale effect (pooled, no method interaction)\n")
summary_lines.append(f"- Formula: `{pooled_summary2['formula']}`")
summary_lines.append(f"- R² = {pooled_summary2['R_squared']:.4f}")
lt_key = [k for k in pooled_summary2['parameters'] if 'log_time' in str(k) and '*' not in str(k)][0]
summary_lines.append(f"- Timescale coefficient: {pooled_summary2['parameters'].get(lt_key, 'N/A')}")
summary_lines.append(f"- Timescale p-value: {pooled_summary2['p_values'].get(lt_key, 'N/A')}")

summary_lines.append("\n## Key Finding 2: Glacial vs Fluvial Comparison\n")
sc = comparison_results["simple_mean_comparison"]
summary_lines.append(f"- **Mean log10 rate (Glacial)**: {sc['glacial_mean_log']:.4f} (n={sc['glacial_n']})")
summary_lines.append(f"- **Mean log10 rate (Fluvial)**: {sc['fluvial_mean_log']:.4f} (n={sc['fluvial_n']})")
summary_lines.append(f"- **Mean difference (G-F)**: {sc['mean_difference']:.4f}")
summary_lines.append(f"- **Welch t-test**: t={sc['welch_ttest']['t_stat']:.4f}, p={sc['welch_ttest']['p_value']:.2e}")
summary_lines.append(f"- **Mann-Whitney**: U={sc['mann_whitney']['U_stat']:.0f}, p={sc['mann_whitney']['p_value']:.2e}")

summary_lines.append("\n### ANCOVA (controlling for timescale)\n")
ac = comparison_results["ancova"]
summary_lines.append(f"- Formula: `{ac['formula']}`")
summary_lines.append(f"- R² = {ac['R_squared']:.4f}")
proc_f_idx = ac['ANOVA']['term'].index('process_category[T.Glacial]') if 'process_category[T.Glacial]' in ac['ANOVA']['term'] else 0
time_f_idx = ac['ANOVA']['term'].index('log_time') if 'log_time' in ac['ANOVA']['term'] else 1
summary_lines.append(f"- Process category F-statistic: {ac['ANOVA']['F'][proc_f_idx]:.4f}, p={ac['ANOVA']['PR_gt_F'][proc_f_idx]:.2e}")
summary_lines.append(f"- Timescale F-statistic: {ac['ANOVA']['F'][time_f_idx]:.4f}, p={ac['ANOVA']['PR_gt_F'][time_f_idx]:.2e}")

summary_lines.append("\n### ANCOVA with method control\n")
ac2 = comparison_results["ancova_with_method"]
summary_lines.append(f"- Formula: `{ac2['formula']}`")
summary_lines.append(f"- R² = {ac2['R_squared']:.4f}")
proc_key = 'process_category[T.Glacial]'
summary_lines.append(f"- Process category coefficient: {ac2['coefficients'].get(proc_key, 'N/A')}")
summary_lines.append(f"- Process category CI: {ac2['ci'].get(proc_key, 'N/A')}")

summary_lines.append("\n## Key Finding 3: Method Stratification\n")
summary_lines.append("Erosion rate differences between Glacial and Fluvial within each methodology:\n")
summary_lines.append("| Method | n(G/F) | G mean(log) | F mean(log) | Difference | t-test p |")
summary_lines.append("|--------|--------|-------------|-------------|------------|----------|")
for meth, ms in sorted(method_stats.items()):
    g_mean = ms.get('glacial_mean_log', 0) or 0
    f_mean = ms.get('fluvial_mean_log', 0) or 0
    diff = g_mean - f_mean
    tp = ms.get('welch_ttest', {}).get('p_value', 'N/A')
    summary_lines.append(f"| {meth} | {ms['glacial_n']}/{ms['fluvial_n']} | {g_mean:.3f} | {f_mean:.3f} | {diff:.3f} | {tp} |")

summary_lines.append("\n## Key Finding 4: Model Comparison\n")
summary_lines.append("Models ranked by AIC (lower is better):\n")
summary_lines.append("| Rank | Model | AIC | BIC | R² |")
summary_lines.append("|------|-------|-----|-----|-----|")
for i, mc in enumerate(model_comparison):
    summary_lines.append(f"| {i+1} | {mc['model']} | {mc['AIC']:.1f} | {mc['BIC']:.1f} | {mc['R²']:.4f} |")

summary_lines.append("\n## Robustness Checks\n")
if "robustness_no_volumetric" in regression_results:
    rv = regression_results["robustness_no_volumetric"]
    summary_lines.append(f"- **Without Volumetric** (n={rv['n']}): slope={rv['slope']:.4f}, p={rv['p_value']:.2e}, R²={rv['R_squared']:.4f}")
if "robustness_cosmogenic_only" in regression_results:
    rc = regression_results["robustness_cosmogenic_only"]
    summary_lines.append(f"- **Cosmogenic only** (n={rc['n']}): slope={rc['slope']:.4f}, p={rc['p_value']:.2e}, R²={rc['R_squared']:.4f}")

summary_lines.append("\n## Interpretation Notes\n")
summary_lines.append("- **Timescale coupling**: A non-zero slope in the log-log relationship may reflect mathematical coupling (rate = thickness / time) rather than a true physical dependence.")
summary_lines.append("- **Method stratification**: Different methodologies capture different temporal windows and may introduce systematic biases.")
summary_lines.append("- **Process effect**: After controlling for timescale and methodology, the residual difference between glacial and fluvial rates represents the pure process effect.")
summary_lines.append("- **Best model**: The model with lowest AIC provides the best trade-off between fit and complexity.")

with open("/data/user/conversations/conv-46b0a68e-ac73-49c3-ba26-bbe4d51ce35a/project/working/subB/analysis_summary.md", "w") as f:
    f.write("\n".join(summary_lines))
print("Saved: working/subB/analysis_summary.md")

print("\nDone.")
