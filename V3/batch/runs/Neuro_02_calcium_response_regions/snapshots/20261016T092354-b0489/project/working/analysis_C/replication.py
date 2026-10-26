#!/usr/bin/env python3
"""
Independent replication of core effect-size calculations for calcium response data.
Task: Neuro_02_calcium_response_regions

This script independently computes:
1. Region x Condition means, stds, n, and 95% CIs for all 6 variables
2. Simple-effect pairwise comparisons (t-tests) with Cohen's d / Hedges' g
3. Eta-squared (eta^2) from one-way ANOVA for each region-condition group
4. Explicitly identifies which contrasts are confounded/unestimable

Data is read directly from the TSV file; no imported analysis results are used.
"""

import pandas as pd
import numpy as np
from scipy import stats
from itertools import combinations
import csv
import os

# ── Paths ──────────────────────────────────────────────────────────────
DATA_PATH = "/data/user/conversations/conv-4a42b09e-c6e8-4347-910d-86fe4c3da0c2/project/data/cellular_calcium_response_summaries.tsv"
OUTPUT_DIR = "/data/user/conversations/conv-4a42b09e-c6e8-4347-910d-86fe4c3da0c2/project/working/analysis_C"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, sep="\t")
print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

VARIABLES = [
    "mean_amplitude_dff0",
    "mean_time_to_peak_s",
    "mean_peak_width_s",
    "mean_peak_prominence_dff0",
    "mean_peak_frequency_hz",
    "mean_auc_au",
]

CONDITIONS = ["baseline", "neural_activity_blocked", "receptor_stimulated"]
REGIONS = sorted(df["anatomical_region_id"].unique())

# ── Helper functions ───────────────────────────────────────────────────

def compute_group_stats(group):
    """Return n, mean, std, se, ci_lower, ci_upper for a pandas Series."""
    n = len(group)
    m = group.mean()
    s = group.std(ddof=1)
    se = s / np.sqrt(n) if n > 0 else np.nan
    ci = stats.t.interval(0.95, df=n - 1, loc=m, scale=se) if n > 1 else (np.nan, np.nan)
    return {"n": n, "mean": m, "std": s, "se": se, "ci_lower": ci[0], "ci_upper": ci[1]}


def cohens_d(x, y):
    """Cohen's d with pooled standard deviation."""
    n1, n2 = len(x), len(y)
    if n1 < 2 or n2 < 2:
        return np.nan
    var1 = x.var(ddof=1)
    var2 = y.var(ddof=1)
    pooled_se = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)) / np.sqrt(1.0 / n1 + 1.0 / n2)
    if pooled_se == 0:
        return np.nan
    return (x.mean() - y.mean()) / np.sqrt((var1 + var2) / 2)


def hedges_g(x, y):
    """Hedges' g (Cohen's d with small-sample correction)."""
    d = cohens_d(x, y)
    if np.isnan(d):
        return np.nan
    n1, n2 = len(x), len(y)
    j = stats.gamma.logpdf(0.5 * (n1 + n2) - 1, 0.5 * (n1 + n2) - 1) - stats.gamma.logpdf(0.5 * (n1 + n2) - 1.5, 0.5 * (n1 + n2) - 1)
    # Approximate correction factor using gamma function ratio
    from math import lgamma
    j_factor = 1 - 3 / (4 * (n1 + n2) - 9) if (n1 + n2) > 4 else 1.0
    return d * j_factor


def eta_squared_anova(*groups):
    """Eta-squared from one-way ANOVA: SS_between / SS_total."""
    all_data = np.concatenate(groups)
    grand_mean = all_data.mean()
    ss_total = sum(((v - grand_mean) ** 2) for g in groups for v in g)
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    if ss_total == 0:
        return 0.0
    return ss_between / ss_total


def welch_ttest_pval(x, y):
    """Two-sided p-value from Welch's t-test."""
    if len(x) < 2 or len(y) < 2:
        return np.nan
    t, p = stats.ttest_ind(x, y, equal_var=False)
    return p


# ── 1. Region x Condition summary statistics ──────────────────────────
print("\n" + "=" * 80)
print("SECTION 1: Region x Condition Summary Statistics")
print("=" * 80)

summary_rows = []
for var in VARIABLES:
    print(f"\n--- {var} ---")
    for region in REGIONS:
        for cond in CONDITIONS:
            subset = df[(df["anatomical_region_id"] == region) & (df["condition"] == cond)]
            if len(subset) == 0:
                continue
            vals = subset[var].dropna()
            if len(vals) == 0:
                continue
            s = compute_group_stats(vals)
            row = {
                "variable": var,
                "region": region,
                "condition": cond,
                "n": s["n"],
                "mean": round(s["mean"], 6),
                "std": round(s["std"], 6),
                "se": round(s["se"], 6),
                "ci_lower": round(s["ci_lower"], 6),
                "ci_upper": round(s["ci_upper"], 6),
            }
            summary_rows.append(row)
            print(f"  {region} x {cond}: n={s['n']}, mean={s['mean']:.4f}, std={s['std']:.4f}, "
                  f"95% CI=[{s['ci_lower']:.4f}, {s['ci_upper']:.4f}]")

# Save summary CSV
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(os.path.join(OUTPUT_DIR, "replication_results.csv"), index=False)
print(f"\nSummary saved to {OUTPUT_DIR}/replication_results.csv ({len(summary_df)} rows)")

# ── 2. Identify estimable vs confounded contrasts ─────────────────────
print("\n" + "=" * 80)
print("SECTION 2: Estimability Analysis (Confounding Check)")
print("=" * 80)

# Build condition-region matrix
cr_matrix = {}
for region in REGIONS:
    for cond in CONDITIONS:
        key = (region, cond)
        cr_matrix[key] = len(df[(df["anatomical_region_id"] == region) & (df["condition"] == cond)])

print("\nCondition-Region cell counts:")
for (r, c), cnt in sorted(cr_matrix.items()):
    marker = " [EMPTY]" if cnt == 0 else ""
    print(f"  {r} x {c}: {cnt}{marker}")

# Define all possible pairwise contrasts between conditions
all_contrasts = list(combinations(CONDITIONS, 2))

estimable = []
confounded = []

for c1, c2 in all_contrasts:
    regions_with_both = []
    regions_missing = []
    for region in REGIONS:
        has_c1 = cr_matrix.get((region, c1), 0) > 0
        has_c2 = cr_matrix.get((region, c2), 0) > 0
        if has_c1 and has_c2:
            regions_with_both.append(region)
        elif not has_c1 and not has_c2:
            pass  # neither present
        else:
            missing = c1 if not has_c1 else c2
            regions_missing.append(f"{region}({missing})")

    if regions_with_both:
        estimable.append((c1, c2, regions_with_both, regions_missing))
        print(f"\n  ESTIMABLE: {c1} vs {c2}")
        print(f"    In regions: {', '.join(regions_with_both)}")
        if regions_missing:
            print(f"    Not jointly observed in: {', '.join(regions_missing)}")
    else:
        confounded.append((c1, c2, regions_missing))
        print(f"\n  CONFOUNDED (not estimable): {c1} vs {c2}")
        print(f"    No region has both conditions: {', '.join(regions_missing)}")

# ── 3. Simple-effect pairwise tests ───────────────────────────────────
print("\n" + "=" * 80)
print("SECTION 3: Simple-Effect Pairwise Comparisons")
print("=" * 80)

test_rows = []

for c1, c2, valid_regions, _miss in estimable:
    for region in valid_regions:
        sub1 = df[(df["anatomical_region_id"] == region) & (df["condition"] == c1)]
        sub2 = df[(df["anatomical_region_id"] == region) & (df["condition"] == c2)]

        for var in VARIABLES:
            v1 = sub1[var].dropna().values
            v2 = sub2[var].dropna().values

            if len(v1) < 2 or len(v2) < 2:
                continue

            p_val = welch_ttest_pval(v1, v2)
            d_val = cohens_d(v1, v2)
            g_val = hedges_g(v1, v2)

            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"

            row = {
                "contrast": f"{c1} vs {c2}",
                "region": region,
                "variable": var,
                "n1": len(v1),
                "n2": len(v2),
                "mean1": round(v1.mean(), 6),
                "mean2": round(v2.mean(), 6),
                "diff": round(v1.mean() - v2.mean(), 6),
                "cohens_d": round(d_val, 6),
                "hedges_g": round(g_val, 6),
                "p_value": round(p_val, 8),
                "significance": sig,
            }
            test_rows.append(row)

            if p_val < 0.05:
                print(f"  {region} | {c1} vs {c2} | {var}: d={d_val:.3f}, p={p_val:.4f} [{sig}]")

# Append test results to CSV
if test_rows:
    test_df = pd.DataFrame(test_rows)
    test_df.to_csv(os.path.join(OUTPUT_DIR, "replication_results.csv"), mode="a", header=False, index=False)
    print(f"\nTest results appended to replication_results.csv ({len(test_df)} rows)")

# ── 4. Eta-squared for multi-group ANOVAs ─────────────────────────────
print("\n" + "=" * 80)
print("SECTION 4: Eta-Squared (ANOVA Effect Sizes)")
print("=" * 80)

eta_rows = []

# For each variable, run ANOVA across conditions within each region that has >= 3 conditions
for var in VARIABLES:
    for region in REGIONS:
        groups = []
        cond_names = []
        for cond in CONDITIONS:
            vals = df[(df["anatomical_region_id"] == region) & (df["condition"] == cond)][var].dropna()
            if len(vals) >= 2:
                groups.append(vals.values)
                cond_names.append(cond)

        if len(groups) >= 2:
            eta_sq = eta_squared_anova(*groups)
            f_stat, p_val = stats.f_oneway(*groups) if all(len(g) >= 2 for g in groups) else (np.nan, np.nan)

            row = {
                "variable": var,
                "region": region,
                "conditions_compared": "+".join(cond_names),
                "n_groups": len(groups),
                "total_n": sum(len(g) for g in groups),
                "eta_squared": round(eta_sq, 6),
                "f_statistic": round(f_stat, 6) if not np.isnan(f_stat) else np.nan,
                "p_value": round(p_val, 8) if not np.isnan(p_val) else np.nan,
            }
            eta_rows.append(row)
            print(f"  {region} | {var}: eta^2={eta_sq:.4f}, F={f_stat:.2f}, p={p_val:.4e}, k={len(groups)}")

eta_df = pd.DataFrame(eta_rows)
eta_df.to_csv(os.path.join(OUTPUT_DIR, "eta_squared_results.csv", ) if False else None, index=False)
# Write eta squared separately
with open(os.path.join(OUTPUT_DIR, "eta_squared_results.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=eta_rows[0].keys() if eta_rows else [])
    writer.writeheader()
    writer.writerows(eta_rows)
print(f"\nEta-squared results saved to {OUTPUT_DIR}/eta_squared_results.csv")

# ── 5. Confounded contrast report ─────────────────────────────────────
print("\n" + "=" * 80)
print("SECTION 5: Confounded / Unestimable Contrasts")
print("=" * 80)

for c1, c2, miss_list in confounded:
    print(f"  NOT ESTIMABLE: {c1} vs {c2}")
    print(f"    Reason: {', '.join(miss_list)}")
    print(f"    These conditions never co-occur in any region.")

# Also note partial confounding
print("\nPartial confounding notes:")
for region in REGIONS:
    conds_present = [c for c in CONDITIONS if cr_matrix.get((region, c), 0) > 0]
    if len(conds_present) < 3:
        missing_conds = [c for c in CONDITIONS if c not in conds_present]
        print(f"  {region}: only {conds_present} observed; cannot estimate {missing_conds}")

# ── 6. Comparison with main analysis ──────────────────────────────────
print("\n" + "=" * 80)
print("SECTION 6: Replication Notes")
print("=" * 80)
print("""
Key design features identified:
1. Region-Condition Confounding:
   - region_1: baseline, neural_activity_blocked, receptor_stimulated (all 3)
   - region_2: baseline, neural_activity_blocked, receptor_stimulated (all 3)
   - region_3: receptor_stimulated ONLY (no baseline or blocked)
   - region_4: baseline, neural_activity_blocked ONLY (no receptor_stimulated)

2. Therefore:
   - 'receptor_stimulated vs baseline': estimable in region_1, region_2;
     NOT estimable in region_3 (no baseline), region_4 (no receptor_stimulated)
   - 'receptor_stimulated vs neural_activity_blocked': estimable in region_1, region_2;
     NOT estimable in region_3 (no blocked), region_4 (no receptor_stimulated)
   - 'baseline vs neural_activity_blocked': estimable in region_1, region_2, region_4;
     NOT estimable in region_3 (neither present)

3. Nested structure: cells are nested within slices, which are nested within batches.
   Simple t-tests treat cells as independent, which may underestimate SE.
   A mixed-effects model would be more appropriate but is beyond scope of this replication.

4. Sample sizes vary dramatically:
   - receptor_stimulated has many more observations (226+199+189=614) than baseline (22+43+0+21=86) or blocked (44+46+0+29=119)
   - This imbalance affects power and variance estimates

5. All analyses use Welch's t-test (unequal variances) for pairwise comparisons.
   Hedges' g is reported for bias-corrected effect sizes.
""")

# ── Write comparison text ─────────────────────────────────────────────
comparison_text = f"""INDEPENDENT REPLICATION RESULTS - COMPARISON NOTES
==================================================
Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Data: {DATA_PATH}
Total observations: {len(df)}

DESIGN ANALYSIS
---------------
The data exhibits strong region-condition confounding:
- region_1: all 3 conditions (baseline={cr_matrix.get(('region_1','baseline'),0)}, blocked={cr_matrix.get(('region_1','neural_activity_blocked'),0)}, stimulated={cr_matrix.get(('region_1','receptor_stimulated'),0)})
- region_2: all 3 conditions (baseline={cr_matrix.get(('region_2','baseline'),0)}, blocked={cr_matrix.get(('region_2','neural_activity_blocked'),0)}, stimulated={cr_matrix.get(('region_2','receptor_stimulated'),0)})
- region_3: receptor_stimulated only (stimulated={cr_matrix.get(('region_3','receptor_stimulated'),0)})
- region_4: baseline + blocked only (baseline={cr_matrix.get(('region_4','baseline'),0)}, blocked={cr_matrix.get(('region_4','neural_activity_blocked'),0)})

CONTRAST ESTIMABILITY
---------------------
ESTIMABLE CONTRASTS:
"""

for c1, c2, regions, _ in estimable:
    comparison_text += f"  - {c1} vs {c2}: in {', '.join(regions)}\n"

comparison_text += "\nNOT ESTIMABLE (confounded):\n"
for c1, c2, miss in confounded:
    comparison_text += f"  - {c1} vs {c2}: {', '.join(miss)}\n"

comparison_text += f"""
STATISTICAL METHODS
-------------------
- Group statistics: mean, std, SE, 95% CI (t-distribution)
- Pairwise tests: Welch's two-sample t-test (unequal variances assumed)
- Effect sizes: Cohen's d and Hedges' g (small-sample corrected)
- ANOVA effect size: eta-squared (SS_between / SS_total)
- Significance thresholds: *** p<0.001, ** p<0.01, * p<0.05, ns p>=0.05

LIMITATIONS
-----------
1. Cells within slices are not independent; simple t-tests ignore nesting.
   A mixed-effects model with random intercepts for slice/batch would be preferred.
2. Large sample size imbalance (receptor_stimulated >> baseline/blocked).
3. region_3 and region_4 have limited condition coverage, preventing full factorial analysis.
4. Multiple comparisons across 6 variables and many contrasts increase Type I error risk.
   Bonferroni or FDR corrections were not applied (exploratory analysis).

FILES GENERATED
---------------
- replication_results.csv: Summary stats + pairwise test results
- eta_squared_results.csv: ANOVA eta-squared values
- This file: methodological notes and contrast estimability

"""

with open(os.path.join(OUTPUT_DIR, "comparison_with_main.txt"), "w") as f:
    f.write(comparison_text)

print(f"\nComparison notes saved to {OUTPUT_DIR}/comparison_with_main.txt")
print("\nReplication complete.")
