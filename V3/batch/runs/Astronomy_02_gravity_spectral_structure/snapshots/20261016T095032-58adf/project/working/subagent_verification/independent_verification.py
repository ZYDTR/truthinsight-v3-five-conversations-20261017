#!/usr/bin/env python3
"""
Independent verification of spectral ranking and cross-model correlation findings.
Blind re-computation from raw data files — no imported scripts executed.
"""

import json
import csv
import math
from collections import defaultdict

PROJECT_ROOT = "/data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project"
DATA_DIR = f"{PROJECT_ROOT}/data"
OUTPUT_DIR = f"{PROJECT_ROOT}/working/subagent_verification"

def read_tsv(filepath):
    """Read a TSV file and return list of dicts."""
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        return list(reader)

def pearson_r(x, y):
    """Compute Pearson correlation coefficient."""
    n = len(x)
    if n < 2:
        return None
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    den_x = math.sqrt(sum((xi - mean_x)**2 for xi in x))
    den_y = math.sqrt(sum((yi - mean_y)**2 for yi in y))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)

def mean_abs_diff(x, y):
    """Compute mean absolute difference between two lists."""
    return sum(abs(xi - yi) for xi, yi in zip(x, y)) / len(x)

# ============================================================
# SECTION 1: Spectral Ranking Verification
# ============================================================

print("=" * 60)
print("SECTION 1: SPECTRAL RANKING VERIFICATION")
print("=" * 60)

ranked = read_tsv(f"{DATA_DIR}/ranked_full_parameter_grid.tsv")
candidates = read_tsv(f"{DATA_DIR}/candidate_spectrum_comparison.tsv")
uniform_alt = read_tsv(f"{DATA_DIR}/uniform_alternative_comparison.tsv")

results = {}

# --- 1a: Verify delta_information_criterion ---
print("\n--- 1a: delta_IC verification ---")
# Rank 1 should have delta_IC = 0 by definition
assert ranked[0]['candidate_rank'] == '1'
assert float(ranked[0]['delta_information_criterion']) == 0.0
print(f"Rank 1 delta_IC = {ranked[0]['delta_information_criterion']} (expected 0)")

# Check if delta_IC = IC_rank1 - IC_current (i.e., rank 1 is best, higher IC = better)
# Or delta_IC = IC_current - IC_rank1 (difference from rank 1)
# Since rank 1 has delta=0 and values increase, it's likely: delta_IC = IC_current - IC_rank1
# where IC is negative log-likelihood based. Let's check the pattern.

# Extract all IC values from ranked table to see if there's an underlying IC column
# The ranked table only has delta_IC, not raw IC. But we can infer:
# If delta_IC = IC_best - IC_i, then IC_i = IC_best - delta_IC
# If delta_IC = IC_i - IC_best, then IC_i = IC_best + delta_IC
# We need to cross-reference with candidate_spectrum_comparison.tsv which has information_criterion

# Build lookup from candidates
candidates_by_params = {}
for row in candidates:
    key = (float(row['max_velocity_cm_s']), float(row['min_velocity_cm_s']),
           float(row['peak_frequency_microhz']), float(row['peak_width_microhz']))
    candidates_by_params[key] = float(row['information_criterion'])

# Find rank-1 params in ranked table
rank1_params = (
    float(ranked[0]['max_velocity_cm_s']),
    float(ranked[0]['min_velocity_cm_s']),
    float(ranked[0]['peak_frequency_microhz']),
    float(ranked[0]['frequency_width_microhz'])
)
print(f"Rank 1 params: v_max={rank1_params[0]}, v_min={rank1_params[1]}, f_peak={rank1_params[2]}, width={rank1_params[3]}")

# Check if these params exist in candidate_spectrum_comparison
if rank1_params in candidates_by_params:
    rank1_ic_in_candidates = candidates_by_params[rank1_params]
    print(f"Rank 1 params found in candidate_spectrum_comparison.tsv with IC = {rank1_ic_in_candidates}")
else:
    # Try with peak_width instead of frequency_width
    rank1_params_alt = (rank1_params[0], rank1_params[1], rank1_params[2], rank1_params[3])
    print(f"Trying alternate key...")
    # The columns are named differently: frequency_width_microhz vs peak_width_microhz
    # They should represent the same thing
    found = False
    for key, ic in candidates_by_params.items():
        if (key[0] == rank1_params[0] and key[1] == rank1_params[1] and
            key[2] == rank1_params[2] and abs(key[3] - rank1_params[3]) < 1e-6):
            print(f"Found match in candidates: params={key}, IC={ic}")
            found = True
            break
    if not found:
        print("Rank 1 params NOT found in candidate_spectrum_comparison.tsv")

# Now let's look at the global minimum IC in candidate_spectrum_comparison
min_ic_row = min(candidates, key=lambda r: float(r['information_criterion']))
min_ic_val = float(min_ic_row['information_criterion'])
min_ic_params = (
    float(min_ic_row['max_velocity_cm_s']),
    float(min_ic_row['min_velocity_cm_s']),
    float(min_ic_row['peak_frequency_microhz']),
    float(min_ic_row['peak_width_microhz'])
)
print(f"\nGlobal minimum IC in candidate_spectrum_comparison: {min_ic_val}")
print(f"  Params: v_max={min_ic_params[0]}, v_min={min_ic_params[1]}, f_peak={min_ic_params[2]}, width={min_ic_params[3]}")

# Compare with rank 1
print(f"\nRank 1 params: v_max={rank1_params[0]}, v_min={rank1_params[1]}, f_peak={rank1_params[2]}, width={rank1_params[3]}")
print(f"Match: {min_ic_params == rank1_params}")

# Check if delta_IC = IC_candidate - IC_rank1 (AIC/BIC style: lower is better)
# If rank 1 has the lowest IC, then delta_IC = IC_i - IC_rank1 >= 0
# This means IC_rank1 is the minimum IC value
# From candidate_spectrum_comparison, the minimum IC is 5066.3 (first row)
# Let's verify: does rank 1 correspond to IC=5066.3?

# Check first few rows of candidate_spectrum_comparison
print("\nFirst 10 rows of candidate_spectrum_comparison:")
for i, row in enumerate(candidates[:10]):
    print(f"  Row {i+1}: IC={row['information_criterion']}, "
          f"v_max={row['max_velocity_cm_s']}, v_min={row['min_velocity_cm_s']}, "
          f"f_peak={row['peak_frequency_microhz']}, width={row['peak_width_microhz']}")

# The first row has IC=5066.3 with params v_max=0.1, v_min=0, f_peak=1010, width=300
# Rank 1 has v_max=30, v_min=0.05, f_peak=1010, width=275
# These are DIFFERENT parameter sets! So the two tables may represent different pools.

# Let's find the row in candidates that matches rank 1 exactly
rank1_match_found = False
for row in candidates:
    if (float(row['max_velocity_cm_s']) == rank1_params[0] and
        float(row['min_velocity_cm_s']) == rank1_params[1] and
        float(row['peak_frequency_microhz']) == rank1_params[2] and
        abs(float(row['peak_width_microhz']) - rank1_params[3]) < 1e-6):
        print(f"\nRank 1 params MATCH in candidate_spectrum_comparison: IC={row['information_criterion']}")
        rank1_match_found = True
        break

if not rank1_match_found:
    print(f"\nRank 1 params NOT found in candidate_spectrum_comparison")
    # Maybe the column names differ but represent same concept
    # Check if frequency_width_microhz maps to peak_width_microhz
    # Rank 1: v_max=30, v_min=0.05, f_peak=1010, width=275
    # Let's search more broadly
    for row in candidates:
        if (float(row['max_velocity_cm_s']) == 30 and
            float(row['min_velocity_cm_s']) == 0.05 and
            float(row['peak_frequency_microhz']) == 1010):
            print(f"  Partial match (v_max=30, v_min=0.05, f_peak=1010): width={row['peak_width_microhz']}, IC={row['information_criterion']}")

# --- 1b: Count candidates within delta_IC thresholds ---
print("\n--- 1b: Candidate counts within delta_IC thresholds ---")
delta_values = [float(r['delta_information_criterion']) for r in ranked]
count_le_10 = sum(1 for d in delta_values if d <= 10)
count_le_20 = sum(1 for d in delta_values if d <= 20)
print(f"Total candidates: {len(ranked)}")
print(f"Candidates with delta_IC <= 10: {count_le_10}")
print(f"Candidates with delta_IC <= 20: {count_le_20}")

# List them
within_10 = [(int(r['candidate_rank']), float(r['delta_information_criterion']))
             for r in ranked if float(r['delta_information_criterion']) <= 10]
within_20 = [(int(r['candidate_rank']), float(r['delta_information_criterion']))
             for r in ranked if float(r['delta_information_criterion']) <= 20]
print(f"\nWithin delta_IC <= 10:")
for rank, delta in within_10:
    print(f"  Rank {rank}: delta_IC={delta}")
print(f"\nWithin delta_IC <= 20 (additional beyond 10):")
for rank, delta in within_20:
    if delta > 10:
        print(f"  Rank {rank}: delta_IC={delta}")

# --- 1c: Relationship between the two data files ---
print("\n--- 1c: Relationship between ranked_full_parameter_grid.tsv and candidate_spectrum_comparison.tsv ---")

# Check column naming: frequency_width_microhz vs peak_width_microhz
# Both seem to represent the same physical quantity (spectral width)
# Let's check if the parameter grids overlap

# Get all unique parameter combinations from each file
ranked_combos = set()
for r in ranked:
    combo = (float(r['max_velocity_cm_s']), float(r['min_velocity_cm_s']),
             float(r['peak_frequency_microhz']), float(r['frequency_width_microhz']))
    ranked_combos.add(combo)

candidates_combos = set()
for c in candidates:
    combo = (float(c['max_velocity_cm_s']), float(c['min_velocity_cm_s']),
             float(c['peak_frequency_microhz']), float(c['peak_width_microhz']))
    candidates_combos.add(combo)

overlap = ranked_combos & candidates_combos
print(f"Unique combos in ranked_full_parameter_grid: {len(ranked_combos)}")
print(f"Unique combos in candidate_spectrum_comparison: {len(candidates_combos)}")
print(f"Overlap (same param combos): {len(overlap)}")

# Check families in candidate_spectrum_comparison
families = set(c['candidate_family'] for c in candidates)
print(f"Families in candidate_spectrum_comparison: {families}")

# Count per family
family_counts = defaultdict(int)
for c in candidates:
    family_counts[c['candidate_family']] += 1
print(f"Counts per family: {dict(family_counts)}")

# Check if ranked table is a subset of candidates
print(f"All ranked combos in candidates: {ranked_combos.issubset(candidates_combos)}")
print(f"All candidates in ranked: {candidates_combos.issubset(ranked_combos)}")

# Determine whether they represent the same pool
if ranked_combos == candidates_combos:
    print("CONCLUSION: Both files represent the EXACT SAME candidate pool")
elif ranked_combos.issubset(candidates_combos):
    print("CONCLUSION: ranked_full_parameter_grid is a SUBSET of candidate_spectrum_comparison")
elif candidates_combos.issubset(ranked_combos):
    print("CONCLUSION: candidate_spectrum_comparison is a SUBSET of ranked_full_parameter_grid")
else:
    print("CONCLUSION: The two files represent OVERLAPPING but DIFFERENT candidate pools")

# Check mapping: do both use the same IC scale?
# ranked uses delta_IC (relative), candidates use absolute IC
# If they share the same pool, we can compare

# For overlapping candidates, check if delta_IC corresponds to IC differences
overlap_with_delta = []
for r in ranked:
    combo = (float(r['max_velocity_cm_s']), float(r['min_velocity_cm_s']),
             float(r['peak_frequency_microhz']), float(r['frequency_width_microhz']))
    if combo in candidates_combos:
        delta = float(r['delta_information_criterion'])
        # Find the IC in candidates
        for c in candidates:
            if (float(c['max_velocity_cm_s']) == combo[0] and
                float(c['min_velocity_cm_s']) == combo[1] and
                float(c['peak_frequency_microhz']) == combo[2] and
                abs(float(c['peak_width_microhz']) - combo[3]) < 1e-6):
                ic = float(c['information_criterion'])
                overlap_with_delta.append((combo, delta, ic))
                break

if overlap_with_delta:
    # Check if delta = IC - IC_min (where IC_min is the minimum across ALL candidates)
    all_ic_values = [float(c['information_criterion']) for c in candidates]
    global_min_ic = min(all_ic_values)
    print(f"\nGlobal minimum IC across all candidates: {global_min_ic}")

    # Check consistency: delta should equal IC - global_min_ic if both use same baseline
    deltas_from_global = [(combo, delta, ic, ic - global_min_ic)
                          for combo, delta, ic in overlap_with_delta]

    # How many match exactly?
    exact_matches = sum(1 for _, d, ic, expected in deltas_from_global if abs(d - expected) < 1e-6)
    print(f"Overlap entries: {len(overlap_with_delta)}")
    print(f"Exact matches (delta == IC - global_min_ic): {exact_matches}")

    # Show some examples
    print("\nSample overlap entries (combo, delta, IC, IC-global_min):")
    for combo, d, ic, exp in deltas_from_global[:5]:
        print(f"  {combo}: delta={d:.4f}, IC={ic:.4f}, IC-min={exp:.4f}, diff={abs(d-exp):.6f}")

# --- 1d: Uniform alternative comparison ---
print("\n--- 1d: Uniform alternative comparison ---")
uniform_ics = [(float(r['uniform_velocity_cm_s']), float(r['information_criterion']))
               for r in uniform_alt]
best_uniform = min(uniform_ics, key=lambda x: x[1])
print(f"Best uniform velocity: {best_uniform[0]} cm/s")
print(f"Best uniform IC: {best_uniform[1]}")

# Best structured IC from candidate_spectrum_comparison
best_structured_ic = min_ic_val
print(f"Best structured IC: {best_structured_ic}")
print(f"IC difference (structured - uniform): {best_structured_ic - best_uniform[1]}")

# Are the IC values comparable?
# Both tables report information_criterion
# The uniform alternatives use different velocities but presumably same likelihood framework
# The structured model has additional parameters (v_max, v_min, f_peak, width)
# If they share the same baseline likelihood, the difference is meaningful
print(f"\nStructured IC range: [{min(all_ic_values):.1f}, {max(all_ic_values):.1f}]")
print(f"Uniform IC range: [{min(u[1] for u in uniform_ics):.1f}, {max(u[1] for u in uniform_ics):.1f}]")
print(f"Do ranges overlap? {max(u[1] for u in uniform_ics) >= min(all_ic_values)}")

# ============================================================
# SECTION 2: Cross-Model Correlation Verification
# ============================================================

print("\n" + "=" * 60)
print("SECTION 2: CROSS-MODEL CORRELATION VERIFICATION")
print("=" * 60)

traces = read_tsv(f"{DATA_DIR}/pass_residual_traces.tsv")

# Organize by pass_id
passes = defaultdict(lambda: {'time': [], 'A': [], 'B': [], 'C': []})
for row in traces:
    pid = row['pass_id']
    passes[pid]['time'].append(float(row['relative_time_min']))
    passes[pid]['A'].append(float(row['residual_model_A_mm_s']))
    passes[pid]['B'].append(float(row['residual_model_B_mm_s']))
    passes[pid]['C'].append(float(row['residual_model_C_mm_s']))

pass_ids = sorted(passes.keys())
num_passes = len(pass_ids)
print(f"Number of passes: {num_passes}")
print(f"Pass IDs: {pass_ids[:5]}...{pass_ids[-3:]}")

# Compute pairwise correlations
pairs = [('A', 'B'), ('A', 'C'), ('B', 'C')]
pair_corrs = {pair: [] for pair in pairs}
pair_mad = {pair: [] for pair in pairs}  # mean absolute difference

for pid in pass_ids:
    p = passes[pid]
    for m1, m2 in pairs:
        r = pearson_r(p[m1], p[m2])
        mad = mean_abs_diff(p[m1], p[m2])
        pair_corrs[(m1, m2)].append(r)
        pair_mad[(m1, m2)].append(mad)

# Summary statistics
def summary_stats(values):
    n = len(values)
    m = sum(values) / n
    var = sum((v - m)**2 for v in values) / (n - 1)  # sample variance
    std = math.sqrt(var)
    return {
        'mean': m,
        'std': std,
        'min': min(values),
        'max': max(values),
        'count': n
    }

correlation_summary = {}
mad_summary = {}
for pair in pairs:
    corrs = pair_corrs[pair]
    mads = pair_mad[pair]
    correlation_summary[f'{pair[0]}-{pair[1]}'] = summary_stats(corrs)
    mad_summary[f'{pair[0]}-{pair[1]}'] = summary_stats(mads)

print("\n--- Pairwise Pearson r summary ---")
for pair in pairs:
    s = correlation_summary[f'{pair[0]}-{pair[1]}']
    print(f"  {pair[0]}-{pair[1]}: mean={s['mean']:.6f}, std={s['std']:.6f}, "
          f"min={s['min']:.6f}, max={s['max']:.6f}")

# Specific counts
ab_below_50 = sum(1 for r in pair_corrs[('A', 'B')] if r < 0.50)
ac_above_80 = sum(1 for r in pair_corrs[('A', 'C')] if r > 0.80)
bc_range = (min(pair_corrs[('B', 'C')]), max(pair_corrs[('B', 'C')]))

print(f"\n--- Specific counts ---")
print(f"Passes where A-B r < 0.50: {ab_below_50}")
print(f"Passes where A-C r > 0.80: {ac_above_80}")
print(f"B-C r range: [{bc_range[0]:.6f}, {bc_range[1]:.6f}]")

print("\n--- Mean absolute difference summary ---")
for pair in pairs:
    s = mad_summary[f'{pair[0]}-{pair[1]}']
    print(f"  {pair[0]}-{pair[1]}: mean={s['mean']:.6f}, std={s['std']:.6f}, "
          f"min={s['min']:.6f}, max={s['max']:.6f}")

# Per-pass details
print("\n--- Per-pass correlation details ---")
for pid in pass_ids:
    p = passes[pid]
    ab_r = pearson_r(p['A'], p['B'])
    ac_r = pearson_r(p['A'], p['C'])
    bc_r = pearson_r(p['B'], p['C'])
    print(f"  {pid}: A-B={ab_r:.6f}, A-C={ac_r:.6f}, B-C={bc_r:.6f}")

# ============================================================
# SECTION 3: Mode-Frequency Grid Verification
# ============================================================

print("\n" + "=" * 60)
print("SECTION 3: MODE-FREQUENCY GRID VERIFICATION")
print("=" * 60)

mode_grid = read_tsv(f"{DATA_DIR}/mode_frequency_grid.tsv")

# Filter for l=2
l2_rows = [r for r in mode_grid if int(r['angular_degree']) == 2]
print(f"Total rows for l=2: {len(l2_rows)}")

# Sort by radial order
l2_sorted = sorted(l2_rows, key=lambda r: int(r['radial_order']))

# --- 3a: Coupling coefficients by radial order n=0..7 ---
print("\n--- 3a: Coupling coefficients for l=2 by radial order ---")
coupling_by_n = {}
for row in l2_sorted:
    n = int(row['radial_order'])
    cc = float(row['coupling_coefficient'])
    freq = float(row['mode_frequency_microhz'])
    sv = float(row['surface_velocity_cm_s'])
    coupling_by_n[n] = cc
    print(f"  n={n}: coupling={cc:.6e}, freq={freq:.2f} microHz, surface_v={sv:.2f} cm/s")

# --- 3b: Trend direction ---
print("\n--- 3b: Trend direction ---")
cc_values = [coupling_by_n[n] for n in range(8)]
increasing = all(cc_values[i] <= cc_values[i+1] for i in range(len(cc_values)-1))
decreasing = all(cc_values[i] >= cc_values[i+1] for i in range(len(cc_values)-1))
if increasing:
    trend = "strictly increasing"
elif decreasing:
    trend = "strictly decreasing"
else:
    # Check non-monotonic
    changes = []
    for i in range(len(cc_values)-1):
        if cc_values[i] < cc_values[i+1]:
            changes.append('up')
        elif cc_values[i] > cc_values[i+1]:
            changes.append('down')
    trend = f"non-monotonic (changes: {changes})"
print(f"Trend: {trend}")

# --- 3c: Maximum coupling coefficient for l=2 ---
max_n = max(range(8), key=lambda n: coupling_by_n[n])
max_cc = coupling_by_n[max_n]
print(f"\n--- 3c: Maximum coupling coefficient ---")
print(f"Radial order with max coupling: n={max_n}")
print(f"Max coupling coefficient: {max_cc:.6e}")

# --- 3d: Modes in 900-1300 microHz range ---
print("\n--- 3d: Modes in 900-1300 microHz range ---")
in_range = [r for r in mode_grid
            if 900 <= float(r['mode_frequency_microhz']) <= 1300]
print(f"Count of modes in 900-1300 microHz: {len(in_range)}")
for r in sorted(in_range, key=lambda x: float(x['mode_frequency_microhz'])):
    print(f"  l={r['angular_degree']}, n={r['radial_order']}, "
          f"freq={float(r['mode_frequency_microhz']):.2f} microHz, "
          f"coupling={float(r['coupling_coefficient']):.6e}")

# ============================================================
# SAVE RESULTS
# ============================================================

print("\n" + "=" * 60)
print("SAVING RESULTS")
print("=" * 60)

output = {
    "section_1_spectral_ranking": {
        "delta_ic_verification": {
            "rank_1_delta_ic": 0.0,
            "delta_ic_definition": "delta_IC = IC_candidate - IC_best (where IC is the information criterion)",
            "rank_1_params": {
                "v_max": rank1_params[0],
                "v_min": rank1_params[1],
                "f_peak": rank1_params[2],
                "width": rank1_params[3]
            },
            "rank_1_found_in_candidates": rank1_match_found
        },
        "threshold_counts": {
            "total_candidates": len(ranked),
            "delta_ic_le_10": count_le_10,
            "delta_ic_le_20": count_le_20,
            "candidates_within_10": [{"rank": r, "delta_ic": d} for r, d in within_10],
            "candidates_within_20_beyond_10": [{"rank": r, "delta_ic": d} for r, d in within_20 if d > 10]
        },
        "file_relationship": {
            "unique_ranked_combos": len(ranked_combos),
            "unique_candidates_combos": len(candidates_combos),
            "overlap_count": len(overlap),
            "families": list(families),
            "family_counts": dict(family_counts),
            "ranked_is_subset_of_candidates": ranked_combos.issubset(candidates_combos),
            "candidates_is_subset_of_ranked": candidates_combos.issubset(ranked_combos),
            "conclusion": ("SAME_POOL" if ranked_combos == candidates_combos else
                          "OVERLAPPING_DIFFERENT" if overlap else "NO_OVERLAP"),
            "global_min_ic_in_candidates": global_min_ic,
            "best_structured_ic": best_structured_ic,
            "best_structured_params": {
                "v_max": min_ic_params[0],
                "v_min": min_ic_params[1],
                "f_peak": min_ic_params[2],
                "width": min_ic_params[3]
            }
        },
        "uniform_alternative": {
            "best_uniform_velocity": best_uniform[0],
            "best_uniform_ic": best_uniform[1],
            "best_structured_ic": best_structured_ic,
            "ic_difference": best_structured_ic - best_uniform[1],
            "structured_ic_range": [min(all_ic_values), max(all_ic_values)],
            "uniform_ic_range": [min(u[1] for u in uniform_ics), max(u[1] for u in uniform_ics)],
            "ranges_overlap": max(u[1] for u in uniform_ics) >= min(all_ic_values)
        }
    },
    "section_2_cross_model_correlation": {
        "num_passes": num_passes,
        "pairwise_pearson_r": {},
        "pairwise_mean_abs_diff": {},
        "specific_counts": {
            "ab_below_0.50": ab_below_50,
            "ac_above_0.80": ac_above_80,
            "bc_range": [bc_range[0], bc_range[1]]
        },
        "per_pass_correlations": {}
    },
    "section_3_mode_frequency_grid": {
        "l2_coupling_by_radial_order": {f"n{n}": coupling_by_n[n] for n in range(8)},
        "trend_direction": trend,
        "max_coupling": {
            "radial_order": max_n,
            "coefficient": max_cc
        },
        "modes_900_1300_microhz": {
            "count": len(in_range),
            "details": [{
                "l": int(r['angular_degree']),
                "n": int(r['radial_order']),
                "frequency_microhz": float(r['mode_frequency_microhz']),
                "coupling_coefficient": float(r['coupling_coefficient'])
            } for r in sorted(in_range, key=lambda x: float(x['mode_frequency_microhz']))]
        }
    }
}

# Fill in detailed correlation stats
for pair in pairs:
    corrs = pair_corrs[pair]
    output["section_2_cross_model_correlation"]["pairwise_pearson_r"][f"{pair[0]}-{pair[1]}"] = {
        "values": corrs,
        **summary_stats(corrs)
    }
    output["section_2_cross_model_correlation"]["pairwise_mean_abs_diff"][f"{pair[0]}-{pair[1]}"] = {
        "values": pair_mad[pair],
        **summary_stats(pair_mad[pair])
    }

for pid in pass_ids:
    p = passes[pid]
    output["section_2_cross_model_correlation"]["per_pass_correlations"][pid] = {
        "A-B": pearson_r(p['A'], p['B']),
        "A-C": pearson_r(p['A'], p['C']),
        "B-C": pearson_r(p['B'], p['C'])
    }

# Save
output_path = f"{OUTPUT_DIR}/verification_results.json"
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nResults saved to: {output_path}")
print("Verification complete.")
