#!/usr/bin/env python3
"""
Data audit and exploratory analysis for glacial vs nonglacial erosion rates.
Produces: audit_results.json, exploration_summary.md
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path("/data/user/conversations/conv-46b0a68e-ac73-49c3-ba26-bbe4d51ce35a/project")
RAW = BASE / "data" / "raw"
OUT = BASE / "working" / "subA"
OUT.mkdir(parents=True, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────

def read_tsv(path):
    """Read a TSV file; handle encoding issues."""
    try:
        df = pd.read_csv(path, sep="\t", encoding="utf-8")
        return df
    except UnicodeDecodeError:
        return pd.read_csv(path, sep="\t", encoding="latin-1")

def read_csv(path):
    try:
        return pd.read_csv(path, encoding="utf-8")
    except (UnicodeDecodeError, ParserError):
        return pd.read_csv(path, encoding="latin-1")

from pandas.errors import ParserError

def safe_percentiles(arr, pcts=[5, 25, 50, 75, 95]):
    """Compute percentiles on non-NaN values."""
    arr = np.asarray(arr, dtype=float)
    valid = arr[~np.isnan(arr)]
    if len(valid) == 0:
        return {f"p{p}": None for p in pcts}
    return {f"p{p}": float(np.percentile(valid, p)) for p in pcts}

def stats_1d(series, name):
    """Basic descriptive stats for a numeric series."""
    arr = np.asarray(series, dtype=float)
    valid = arr[~np.isnan(arr)]
    if len(valid) == 0:
        return {"name": name, "n_valid": 0, "min": None, "max": None,
                "mean": None, "median": None, "std": None,
                "percentiles": {}, "log10_stats": {}}
    stats = {
        "name": name,
        "n_valid": int(len(valid)),
        "min": float(np.min(valid)),
        "max": float(np.max(valid)),
        "mean": float(np.mean(valid)),
        "median": float(np.median(valid)),
        "std": float(np.std(valid, ddof=1)) if len(valid) > 1 else 0.0,
        "percentiles": safe_percentiles(valid),
    }
    # log10 stats (only positive values)
    pos = valid[valid > 0]
    if len(pos) > 0:
        log_vals = np.log10(pos)
        stats["log10_stats"] = {
            "n_positive": int(len(pos)),
            "log10_min": float(np.min(log_vals)),
            "log10_max": float(np.max(log_vals)),
            "log10_mean": float(np.mean(log_vals)),
            "log10_median": float(np.median(log_vals)),
            "log10_std": float(np.std(log_vals, ddof=1)) if len(pos) > 1 else 0.0,
            "log10_percentiles": safe_percentiles(log_vals),
        }
    else:
        stats["log10_stats"] = {"n_positive": 0}
    return stats

# ── load main tables ────────────────────────────────────────────────────

print("Loading glacial_erosion_Earth.tsv ...")
glacial = read_tsv(RAW / "glacial_erosion_Earth.tsv")
print(f"  shape: {glacial.shape}, columns: {list(glacial.columns)}")

print("Loading nonglacial_erosion_Earth.tsv ...")
nonglacial = read_tsv(RAW / "nonglacial_erosion_Earth.tsv")
print(f"  shape: {nonglacial.shape}, columns: {list(nonglacial.columns)}")

print("Loading slope_glacial.tsv ...")
slope_g = read_tsv(RAW / "slope_glacial.tsv")
print(f"  shape: {slope_g.shape}")

print("Loading slope_nonglacial.tsv ...")
slope_ng = read_tsv(RAW / "slope_nonglacial.tsv")
print(f"  shape: {slope_ng.shape}")

print("Loading lithology_parsed.tsv ...")
litho_g = read_tsv(RAW / "lithology_parsed.tsv")
print(f"  shape: {litho_g.shape}")

print("Loading lithology_parsed_nonglacial.tsv ...")
litho_ng = read_tsv(RAW / "lithology_parsed_nonglacial.tsv")
print(f"  shape: {litho_ng.shape}")

# Prior compilations
print("Loading GloRiSe combined.tsv ...")
glorise = read_tsv(RAW / "prior compilations/GloRiSe/GloRiSe combined.tsv")
print(f"  shape: {glorise.shape}")

print("Loading OCTOPUS octopusdata.tsv ...")
octo_data = read_tsv(RAW / "prior compilations/OCTOPUS/octopusdata.tsv")
print(f"  shape: {octo_data.shape}")

print("Loading OCTOPUS octopusages.tsv ...")
octo_ages = read_tsv(RAW / "prior compilations/OCTOPUS/octopusages.tsv")
print(f"  shape: {octo_ages.shape}")

print("Loading Chen et al. 2023 CSV ...")
chen = read_csv(RAW / "prior compilations/Chen et al. 2023/Chen_et_al_2021_short-term_erosion_rate_data.csv")
print(f"  shape: {chen.shape}")

print("Loading CHELSEA precipitation_glacial.tsv ...")
chel_g = read_tsv(RAW / "prior compilations/CHELSEA/precipitation_glacial.tsv")
print(f"  shape: {chel_g.shape}")

print("Loading CHELSEA precipitation_nonglacial.tsv ...")
chel_ng = read_tsv(RAW / "prior compilations/CHELSEA/precipitation_nonglacial.tsv")
print(f"  shape: {chel_ng.shape}")

results = {}

# ═══════════════════════════════════════════════════════════════════════
# 1. SCHEMA AUDIT
# ═══════════════════════════════════════════════════════════════════════
print("\n=== 1. SCHEMA AUDIT ===")

main_tables = {
    "glacial_erosion_Earth": glacial,
    "nonglacial_erosion_Earth": nonglacial,
    "slope_glacial": slope_g,
    "slope_nonglacial": slope_ng,
    "lithology_parsed": litho_g,
    "lithology_parsed_nonglacial": litho_ng,
}

schema_audit = {}
for tname, df in main_tables.items():
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        missing = int(df[col].isna().sum())
        total = len(df)
        pct_missing = round(missing / total * 100, 2) if total > 0 else 0.0
        sample_vals = df[col].dropna().unique()[:10].tolist()
        # Convert numpy types to Python native for JSON serialization
        sample_vals = [str(v) for v in sample_vals]
        unique_count = int(df[col].nunique())
        info = {
            "dtype": dtype,
            "total_rows": total,
            "missing_count": missing,
            "missing_pct": pct_missing,
            "unique_values": unique_count,
            "sample_unique_values": sample_vals,
        }
        col_info.append({"column": col, **info})
    schema_audit[tname] = col_info
    print(f"  {tname}: {len(df.columns)} columns, {len(df)} rows")

# Prior compilation schemas
prior_tables = {
    "GloRiSe_combined": glorise,
    "OCTOPUS_data": octo_data,
    "OCTOPUS_ages": octo_ages,
    "Chen_et_al_2023": chen,
    "CHELSEA_precip_glacial": chel_g,
    "CHELSEA_precip_nonglacial": chel_ng,
}

prior_schema = {}
for tname, df in prior_tables.items():
    col_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        missing = int(df[col].isna().sum())
        total = len(df)
        pct_missing = round(missing / total * 100, 2) if total > 0 else 0.0
        sample_vals = df[col].dropna().head(10).tolist()
        sample_vals = [str(v) for v in sample_vals]
        unique_count = int(df[col].nunique())
        info = {
            "dtype": dtype,
            "total_rows": total,
            "missing_count": missing,
            "missing_pct": pct_missing,
            "unique_values": unique_count,
            "sample_unique_values": sample_vals,
        }
        col_info.append({"column": col, **info})
    prior_schema[tname] = col_info
    print(f"  {tname}: {len(df.columns)} columns, {len(df)} rows")

results["schema_audit"] = {"main_tables": schema_audit, "prior_compilations": prior_schema}

# ═══════════════════════════════════════════════════════════════════════
# 2. DISTRIBUTION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════
print("\n=== 2. DISTRIBUTION ANALYSIS ===")

dist_analysis = {}
for label, df in [("glacial", glacial), ("nonglacial", nonglacial)]:
    dist_analysis[label] = {}
    for col in ["Erosion rate (mm/yr)", "Time interval (yr)"]:
        if col in df.columns:
            dist_analysis[label][col] = stats_1d(df[col], col)
    # Also log10 of erosion rate
    er_col = "Erosion rate (mm/yr)"
    if er_col in df.columns:
        er_arr = np.asarray(df[er_col], dtype=float)
        pos_mask = er_arr > 0
        if pos_mask.sum() > 0:
            log_er = np.log10(er_arr[pos_mask])
            dist_analysis[label]["Erosion rate (mm/yr)_log10"] = {
                "n_positive": int(pos_mask.sum()),
                "log10_min": float(np.min(log_er)),
                "log10_max": float(np.max(log_er)),
                "log10_mean": float(np.mean(log_er)),
                "log10_median": float(np.median(log_er)),
                "log10_std": float(np.std(log_er, ddof=1)) if len(log_er) > 1 else 0.0,
                "log10_percentiles": safe_percentiles(log_er),
            }
        else:
            dist_analysis[label]["Erosion rate (mm/yr)_log10"] = {"n_positive": 0}

results["distribution_analysis"] = dist_analysis

# ═══════════════════════════════════════════════════════════════════════
# 3. CROSS-TABULATIONS
# ═══════════════════════════════════════════════════════════════════════
print("\n=== 3. CROSS-TABULATIONS ===")

cross_tabs = {}
for label, df in [("glacial", glacial), ("nonglacial", nonglacial)]:
    cross_tabs[label] = {}
    # Methodology x Type
    if "Methodology" in df.columns and "Type" in df.columns:
        ct = pd.crosstab(df["Methodology"], df["Type"], margins=True, dropna=False)
        cross_tabs[label]["Methodology_x_Type"] = ct.to_dict()
        print(f"  {label} Methodology x Type:\n{ct}")

    # Region distribution
    if "Region" in df.columns:
        reg_dist = df["Region"].value_counts(dropna=False).to_dict()
        cross_tabs[label]["Region_distribution"] = {str(k): int(v) for k, v in reg_dist.items()}
        print(f"  {label} Region counts: {dict(reg_dist)}")

    # Lithology distribution
    if "Lithology" in df.columns:
        lit_dist = df["Lithology"].value_counts(dropna=False).to_dict()
        cross_tabs[label]["Lithology_distribution"] = {str(k): int(v) for k, v in lit_dist.items()}
        print(f"  {label} Lithology categories: {len(lit_dist)} unique")

results["cross_tabulations"] = cross_tabs

# ═══════════════════════════════════════════════════════════════════════
# 4. MISSINGNESS AUDIT
# ═══════════════════════════════════════════════════════════════════════
print("\n=== 4. MISSINGNESS AUDIT ===")

missingness = {}
for label, df in [("glacial", glacial), ("nonglacial", nonglacial)]:
    miss_info = {}
    miss_info["total_rows"] = len(df)
    miss_info["columns_with_missing"] = {}
    for col in df.columns:
        mc = int(df[col].isna().sum())
        if mc > 0:
            miss_info["columns_with_missing"][col] = {
                "missing_count": mc,
                "missing_pct": round(mc / len(df) * 100, 2),
            }

    # Rows with at least one missing value
    rows_any_missing = int(df.isna().any(axis=1).sum())
    miss_info["rows_with_at_least_one_missing"] = rows_any_missing
    miss_info["pct_rows_with_any_missing"] = round(rows_any_missing / len(df) * 100, 2) if len(df) > 0 else 0.0

    # Rows with NO missing values
    miss_info["rows_with_no_missing"] = len(df) - rows_any_missing

    # Check if missingness correlates with key variables
    key_cols = ["Erosion rate (mm/yr)", "Time interval (yr)", "Type", "Methodology"]
    corr_analysis = {}
    for kc in key_cols:
        if kc in df.columns:
            # Compare missing pattern in other cols between groups where kc is present vs absent
            has_kc = df[kc].notna()
            other_missing = {}
            for oc in df.columns:
                if oc != kc:
                    miss_when_kc_present = int(df.loc[has_kc, oc].isna().sum()) / max(has_kc.sum(), 1)
                    miss_when_kc_absent = int(df.loc[~has_kc, oc].isna().sum()) / max((~has_kc).sum(), 1)
                    other_missing[oc] = {
                        "missing_pct_when_kc_present": round(miss_when_kc_present * 100, 2),
                        "missing_pct_when_kc_absent": round(miss_when_kc_absent * 100, 2),
                    }
            corr_analysis[kc] = other_missing
    miss_info["missingness_correlation_with_key_vars"] = corr_analysis
    missingness[label] = miss_info
    print(f"  {label}: {rows_any_missing}/{len(df)} rows have at least one missing value ({miss_info['pct_rows_with_any_missing']}%)")

results["missingness_audit"] = missingness

# ═══════════════════════════════════════════════════════════════════════
# 5. OUTLIER DETECTION
# ═══════════════════════════════════════════════════════════════════════
print("\n=== 5. OUTLIER DETECTION ===")

outliers = {}
for label, df in [("glacial", glacial), ("nonglacial", nonglacial)]:
    out_info = {}
    er_col = "Erosion rate (mm/yr)"
    ti_col = "Time interval (yr)"

    # Zero or negative erosion rates
    if er_col in df.columns:
        er_arr = np.asarray(df[er_col], dtype=float)
        zero_mask = er_arr == 0
        neg_mask = er_arr < 0
        out_info["zero_erosion_rates"] = {
            "count": int(zero_mask.sum()),
            "indices": df.index[zero_mask].tolist() if len(zero_mask) > 0 else [],
        }
        out_info["negative_erosion_rates"] = {
            "count": int(neg_mask.sum()),
            "indices": df.index[neg_mask].tolist() if len(neg_mask) > 0 else [],
        }
        # Flag physically impossible values (negative erosion rate)
        out_info["physically_impossible_erosion"] = int(neg_mask.sum())

    # Zero or negative time intervals
    if ti_col in df.columns:
        ti_arr = np.asarray(df[ti_col], dtype=float)
        zero_ti = ti_arr == 0
        neg_ti = ti_arr < 0
        out_info["zero_time_intervals"] = {
            "count": int(zero_ti.sum()),
            "indices": df.index[zero_ti].tolist() if len(zero_ti) > 0 else [],
        }
        out_info["negative_time_intervals"] = {
            "count": int(neg_ti.sum()),
            "indices": df.index[neg_ti].tolist() if len(neg_ti) > 0 else [],
        }

    # Extreme values: IQR-based outlier detection
    if er_col in df.columns:
        er_valid = df[er_col].dropna()
        if len(er_valid) > 0:
            q1 = er_valid.quantile(0.25)
            q3 = er_valid.quantile(0.75)
            iqr = q3 - q1
            upper_fence = q3 + 3 * iqr
            lower_fence = max(0, q1 - 3 * iqr)  # erosion rate can't be negative
            extreme_high = int((er_valid > upper_fence).sum())
            extreme_low = int((er_valid < lower_fence).sum())
            out_info["iqr_outliers_erosion"] = {
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "upper_fence": float(upper_fence),
                "lower_fence": float(lower_fence),
                "extreme_high_count": extreme_high,
                "extreme_low_count": extreme_low,
            }

    if ti_col in df.columns:
        ti_valid = df[ti_col].dropna()
        if len(ti_valid) > 0:
            q1 = ti_valid.quantile(0.25)
            q3 = ti_valid.quantile(0.75)
            iqr = q3 - q1
            upper_fence = q3 + 3 * iqr
            extreme_high = int((ti_valid > upper_fence).sum())
            out_info["iqr_outliers_time_interval"] = {
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "upper_fence": float(upper_fence),
                "extreme_high_count": extreme_high,
            }

    # Flag rows with erosion rate = 0 or NaN
    if er_col in df.columns:
        er_arr = np.asarray(df[er_col], dtype=float)
        nan_er = int(np.isnan(er_arr).sum())
        out_info["nan_erosion_rates"] = {
            "count": nan_er,
        }

    outliers[label] = out_info
    print(f"  {label}: zero erosion={out_info.get('zero_erosion_rates',{}).get('count',0)}, "
          f"negative erosion={out_info.get('negative_erosion_rates',{}).get('count',0)}, "
          f"NaN erosion={out_info.get('nan_erosion_rates',{}).get('count',0)}")

results["outlier_detection"] = outliers

# ═══════════════════════════════════════════════════════════════════════
# 6. UNIQUE LOCALITIES/SOURCES
# ═══════════════════════════════════════════════════════════════════════
print("\n=== 6. UNIQUE LOCALITIES/SOURCES ===")

locality_info = {}
for label, df in [("glacial", glacial), ("nonglacial", nonglacial)]:
    loc_info = {}
    # Try different locality column names
    for col_name in ["Locality", "Location", "Basin", "Place", "Site"]:
        if col_name in df.columns:
            vals = df[col_name].dropna()
            loc_info[f"{col_name}_unique"] = int(vals.nunique())
            loc_info[f"{col_name}_total"] = len(vals)
            # Top 10 most common
            top10 = vals.value_counts().head(10).to_dict()
            loc_info[f"{col_name}_top10"] = {str(k): int(v) for k, v in top10.items()}
            break
    # Compilation source
    for col_name in ["Compilation", "Reference", "Source"]:
        if col_name in df.columns:
            vals = df[col_name].dropna()
            loc_info[f"{col_name}_unique_sources"] = int(vals.nunique())
            loc_info[f"{col_name}_total"] = len(vals)
            top10 = vals.value_counts().head(10).to_dict()
            loc_info[f"{col_name}_top10_sources"] = {str(k): int(v) for k, v in top10.items()}
            break
    locality_info[label] = loc_info
    print(f"  {label}: {loc_info}")

results["locality_source_counts"] = locality_info

# ═══════════════════════════════════════════════════════════════════════
# 7. PRIOR COMPILATION OVERLAP
# ═══════════════════════════════════════════════════════════════════════
print("\n=== 7. PRIOR COMPILATION OVERLAP ===")

overlap_info = {}

# Check overlap by locality/source identifiers across prior compilations
# GloRiSe uses Location_ID/Basin, OCTOPUS uses studyid/refid, Chen uses Reference (author names)
# Also check for shared Compilation names between main tables and prior compilations

# GloRiSe localities
glorise_locs = set()
if "Location_ID" in glorise.columns:
    glorise_locs = set(glorise["Location_ID"].dropna().astype(str))
if "Basin" in glorise.columns:
    glorise_locs.update(glorise["Basin"].dropna().astype(str))
if "Reference" in glorise.columns:
    glorise_refs = set(glorise["Reference"].dropna().astype(str))
else:
    glorise_refs = set()

# OCTOPUS data localities
octo_refs = set()
octo_studies = set()
for col in ["refid", "studyid", "refdoi"]:
    if col in octo_data.columns:
        vals = octo_data[col].dropna().astype(str)
        octo_refs.update(vals.unique())
        if col == "studyid":
            octo_studies.update(vals.unique())
if "basin" in octo_data.columns:
    octo_basins = set(octo_data["basin"].dropna().astype(str))
else:
    octo_basins = set()

# Chen references (author-year format)
chen_refs = set()
chen_locations = set()
if "Reference" in chen.columns:
    chen_refs = set(chen["Reference"].dropna().astype(str))
if "Location" in chen.columns:
    chen_locations = set(chen["Location"].dropna().astype(str))

# Main table references
glacial_refs = set()
nonglacial_refs = set()
glacial_compilations = set()
nonglacial_compilations = set()
for col in ["Compilation", "Reference"]:
    if col in glacial.columns:
        glacial_refs.update(glacial[col].dropna().astype(str).unique())
    if col in nonglacial.columns:
        nonglacial_refs.update(nonglacial[col].dropna().astype(str).unique())
if "Compilation" in glacial.columns:
    glacial_compilations = set(glacial["Compilation"].dropna().astype(str).unique())
if "Compilation" in nonglacial.columns:
    nonglacial_compilations = set(nonglacial["Compilation"].dropna().astype(str).unique())

# Check if OCTOPUS/GloRiSe/Chen appear as Compilation values in main tables
main_has_glorise = "GloRiSe" in nonglacial_compilations
main_has_octopus = "OCTOPUS" in nonglacial_compilations
main_has_chen = "Chen et al., 2022" in nonglacial_compilations

overlap_info["prior_compilation_overlap"] = {
    "GloRiSe_unique_localities": len(glorise_locs),
    "GloRiSe_unique_references": len(glorise_refs),
    "OCTOPUS_unique_references": len(octo_refs),
    "OCTOPUS_unique_studies": len(octo_studies),
    "Chen_et_al_unique_references": len(chen_refs),
    "Chen_et_al_unique_locations": len(chen_locations),
    "GloRiSe_vs_OCTOPUS_overlap": len(glorise_locs & octo_refs),
    "GloRiSe_vs_Chen_overlap": len(glorise_locs & chen_refs),
    "OCTOPUS_vs_Chen_overlap": len(octo_refs & chen_refs),
    "Main_table_compilations": {
        "glacial": sorted(list(glacial_compilations)),
        "nonglacial": sorted(list(nonglacial_compilations)),
    },
    "Main_tables_contain_prior_compilations": {
        "nonglacial_contains_GloRiSe": main_has_glorise,
        "nonglacial_contains_OCTOPUS": main_has_octopus,
        "nonglacial_contains_Chen_2022": main_has_chen,
    },
    "Glacial_ref_count": len(glacial_refs),
    "Nonglacial_ref_count": len(nonglacial_refs),
}

# Detailed overlap samples
overlap_detail = {}
if glorise_locs and octo_refs:
    overlap_detail["GloRiSe_OCTOPUS_common"] = list(glorise_locs & octo_refs)[:20]
if glorise_locs and chen_refs:
    overlap_detail["GloRiSe_Chen_common"] = list(glorise_locs & chen_refs)[:20]
if octo_refs and chen_refs:
    overlap_detail["OCTOPUS_Chen_common"] = list(octo_refs & chen_refs)[:20]

overlap_info["overlap_details"] = overlap_detail
results["prior_compilation_overlap"] = overlap_info

# ═══════════════════════════════════════════════════════════════════════
# 8. ADDITIONAL KEY QUESTIONS
# ═══════════════════════════════════════════════════════════════════════
print("\n=== 8. ADDITIONAL KEY QUESTIONS ===")

key_questions = {}

# Methodology categories and sample sizes
method_cats = {}
for label, df in [("glacial", glacial), ("nonglacial", nonglacial)]:
    if "Methodology" in df.columns:
        mc = df["Methodology"].value_counts(dropna=False).to_dict()
        method_cats[label] = {str(k): int(v) for k, v in mc.items()}
key_questions["methodology_categories"] = method_cats

# Timescale ranges per Type
timescale_ranges = {}
for label, df in [("glacial", glacial), ("nonglacial", nonglacial)]:
    type_timescales = {}
    if "Type" in df.columns and "Time interval (yr)" in df.columns:
        for t in df["Type"].dropna().unique():
            subset = df[df["Type"] == t]["Time interval (yr)"].dropna()
            if len(subset) > 0:
                type_timescales[str(t)] = {
                    "n": int(len(subset)),
                    "min": float(np.min(subset)),
                    "max": float(np.max(subset)),
                    "median": float(np.median(subset)),
                }
    timescale_ranges[label] = type_timescales
key_questions["timescale_ranges_by_type"] = timescale_ranges

# Summary statistics
key_questions["dataset_sizes"] = {
    "glacial_total_rows": len(glacial),
    "nonglacial_total_rows": len(nonglacial),
    "glacial_columns": len(glacial.columns),
    "nonglacial_columns": len(nonglacial.columns),
}

results["key_questions"] = key_questions

# ═══════════════════════════════════════════════════════════════════════
# SAVE RESULTS
# ═══════════════════════════════════════════════════════════════════════
print("\n=== SAVING RESULTS ===")

# Save JSON
json_path = OUT / "audit_results.json"
with open(json_path, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"Saved: {json_path}")

# Generate human-readable summary
summary_lines = []
summary_lines.append("# Data Audit & Exploration Summary\n")
summary_lines.append("## Glacial vs Nonglacial Erosion Rate Datasets\n")
summary_lines.append("### Dataset Overview\n")
summary_lines.append(f"| Property | Glacial | Nonglacial |")
summary_lines.append(f"|----------|---------|------------|")
summary_lines.append(f"| Total rows | {len(glacial)} | {len(nonglacial)} |")
summary_lines.append(f"| Columns | {len(glacial.columns)} | {len(nonglacial.columns)} |")
summary_lines.append(f"| Missing rows (any col) | {missingness['glacial']['rows_with_at_least_one_missing']} | {missingness['nonglacial']['rows_with_at_least_one_missing']} |")
summary_lines.append(f"| Pct rows with any missing | {missingness['glacial']['pct_rows_with_any_missing']}% | {missingness['nonglacial']['pct_rows_with_any_missing']}% |")
summary_lines.append("")

summary_lines.append("### Column Schema\n")
for tname, cols in schema_audit.items():
    summary_lines.append(f"#### {tname}\n")
    summary_lines.append("| Column | Type | Missing | % Missing | Unique |")
    summary_lines.append("|--------|------|---------|-----------|--------|")
    for c in cols:
        summary_lines.append(f"| {c['column']} | {c['dtype']} | {c['missing_count']} | {c['missing_pct']}% | {c['unique_values']} |")
    summary_lines.append("")

summary_lines.append("### Erosion Rate Distribution\n")
summary_lines.append("| Statistic | Glacial | Nonglacial |")
summary_lines.append("|-----------|---------|------------|")
for stat_name in ["min", "max", "mean", "median", "std"]:
    g_val = dist_analysis["glacial"]["Erosion rate (mm/yr)"].get(stat_name)
    ng_val = dist_analysis["nonglacial"]["Erosion rate (mm/yr)"].get(stat_name)
    summary_lines.append(f"| {stat_name} | {g_val} | {ng_val} |")
summary_lines.append("")

summary_lines.append("### Time Interval Distribution\n")
summary_lines.append("| Statistic | Glacial | Nonglacial |")
summary_lines.append("|-----------|---------|------------|")
for stat_name in ["min", "max", "mean", "median", "std"]:
    g_val = dist_analysis["glacial"]["Time interval (yr)"].get(stat_name)
    ng_val = dist_analysis["nonglacial"]["Time interval (yr)"].get(stat_name)
    summary_lines.append(f"| {stat_name} | {g_val} | {ng_val} |")
summary_lines.append("")

summary_lines.append("### Log10 Erosion Rate Distribution\n")
summary_lines.append("| Statistic | Glacial | Nonglacial |")
summary_lines.append("|-----------|---------|------------|")
for stat_name in ["log10_min", "log10_max", "log10_mean", "log10_median"]:
    g_val = dist_analysis["glacial"]["Erosion rate (mm/yr)_log10"].get(stat_name)
    ng_val = dist_analysis["nonglacial"]["Erosion rate (mm/yr)_log10"].get(stat_name)
    summary_lines.append(f"| {stat_name} | {g_val} | {ng_val} |")
summary_lines.append("")

summary_lines.append("### Methodology Categories\n")
for label, cats in method_cats.items():
    summary_lines.append(f"\n#### {label}\n")
    summary_lines.append("| Methodology | Count |")
    summary_lines.append("|-------------|-------|")
    for m, c in sorted(cats.items(), key=lambda x: -x[1]):
        summary_lines.append(f"| {m} | {c} |")
    summary_lines.append("")

summary_lines.append("### Region Distribution (Top 10)\n")
for label, tabs in cross_tabs.items():
    if "Region_distribution" in tabs:
        summary_lines.append(f"\n#### {label}\n")
        region_sorted = sorted(tabs["Region_distribution"].items(), key=lambda x: -x[1])[:10]
        summary_lines.append("| Region | Count |")
        summary_lines.append("|--------|-------|")
        for r, c in region_sorted:
            summary_lines.append(f"| {r} | {c} |")
        summary_lines.append("")

summary_lines.append("### Outlier Detection\n")
for label, oi in outliers.items():
    summary_lines.append(f"\n#### {label}\n")
    summary_lines.append(f"- Zero erosion rates: {oi.get('zero_erosion_rates', {}).get('count', 'N/A')}")
    summary_lines.append(f"- Negative erosion rates: {oi.get('negative_erosion_rates', {}).get('count', 'N/A')}")
    summary_lines.append(f"- NaN erosion rates: {oi.get('nan_erosion_rates', {}).get('count', 'N/A')}")
    summary_lines.append(f"- Zero time intervals: {oi.get('zero_time_intervals', {}).get('count', 'N/A')}")
    summary_lines.append(f"- Negative time intervals: {oi.get('negative_time_intervals', {}).get('count', 'N/A')}")
    iqr_info = oi.get("iqr_outliers_erosion", {})
    if iqr_info:
        summary_lines.append(f"- IQR outlier fences (erosion): [{iqr_info.get('lower_fence')}, {iqr_info.get('upper_fence')}]")
        summary_lines.append(f"- Extreme high erosion outliers: {iqr_info.get('extreme_high_count', 'N/A')}")
        summary_lines.append(f"- Extreme low erosion outliers: {iqr_info.get('extreme_low_count', 'N/A')}")
    summary_lines.append("")

summary_lines.append("### Prior Compilation Overlap\n")
for k, v in overlap_info.get("prior_compilation_overlap", {}).items():
    summary_lines.append(f"- {k}: {v}")
summary_lines.append("")

summary_lines.append("### Key Questions Answered\n")
summary_lines.append(f"**Unique localities/sources per dataset:** See locality_source_counts above.")
summary_lines.append(f"**Methodology categories:** See methodology_categories above.")
summary_lines.append(f"**Timescale range per type:** See timescale_ranges_by_type above.")
summary_lines.append(f"**Zero or missing erosion rates:** See outlier_detection above.")
summary_lines.append(f"**Lithologies represented:** See cross_tabulations -> Lithology_distribution above.")
summary_lines.append("")

summary_lines.append("---\n*Generated by data_audit.py*\n")

md_path = OUT / "exploration_summary.md"
with open(md_path, "w") as f:
    f.write("\n".join(summary_lines))
print(f"Saved: {md_path}")

print("\n=== DONE ===")
