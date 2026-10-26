#!/usr/bin/env python3
"""
Baseline comparability check for Finding 4.

Compare how ranked_full_parameter_grid.tsv and candidate_spectrum_comparison.tsv
score the same 29 parameter combinations that appear in both files.

- ranked_full_parameter_grid.tsv uses delta_information_criterion (relative to its own rank 1)
- candidate_spectrum_comparison.tsv uses absolute information_criterion

If the two tables share the same likelihood normalization, then:
  IC_candidate = constant + delta_IC_ranked  (for shared combos)
meaning the ordering of shared combos should be consistent between the two tables,
and the delta_IC gaps should correspond to fixed offsets in absolute IC.

This does NOT prove definitional identity — only whether the two tables' scores
are linearly related on the shared subset.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("/data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project/data")

# Load ranked grid
ranked = pd.read_csv(DATA_DIR / "ranked_full_parameter_grid.tsv", sep="\t")
# Load candidate spectrum
spectrum = pd.read_csv(DATA_DIR / "candidate_spectrum_comparison.tsv", sep="\t")

# Normalize column names for matching
# ranked columns: max_velocity_cm_s, min_velocity_cm_s, peak_frequency_microhz, frequency_width_microhz
# spectrum columns: max_velocity_cm_s, min_velocity_cm_s, peak_frequency_microhz, peak_width_microhz
# Only difference: frequency_width_microhz vs peak_width_microhz

# Create a common key for matching
ranked_key = ranked[['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz']].copy()
ranked_key['source'] = 'ranked'

spectrum_key = spectrum[['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'peak_width_microhz']].copy()
spectrum_key.columns = ['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz']
spectrum_key['source'] = 'spectrum'

# Merge on all four parameters
merged = ranked_key.merge(spectrum_key, on=['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz'], how='inner')

print(f"Total ranked candidates: {len(ranked)}")
print(f"Total spectrum rows: {len(spectrum)}")
print(f"Overlapping parameter combinations: {len(merged)}")
print()

if len(merged) == 0:
    print("No overlap found. Cannot perform comparability check.")
else:
    # Get delta_IC from ranked side
    ranked_delta = merged[['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz']].merge(
        ranked[['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz', 'delta_information_criterion', 'candidate_rank']],
        on=['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz'],
        suffixes=('', '_ranked')
    )

    # Get IC from spectrum side
    spec_ic = merged[['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz']].merge(
        spectrum[['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'peak_width_microhz', 'information_criterion', 'candidate_family']],
        left_on=['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz'],
        right_on=['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'peak_width_microhz'],
        suffixes=('', '_spec')
    )

    # Join them
    comparison = ranked_delta.merge(spec_ic[['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz', 'information_criterion', 'candidate_family']],
                                     on=['max_velocity_cm_s', 'min_velocity_cm_s', 'peak_frequency_microhz', 'frequency_width_microhz'])

    print(f"\nComparison on {len(comparison)} shared parameter combinations:")
    print()

    # Show top entries by delta_IC
    comparison_sorted = comparison.sort_values('delta_information_criterion')

    print("Top 10 shared combos by delta_IC (ranked):")
    print(f"{'Rank':>6} {'v_max':>6} {'v_min':>6} {'f_peak':>8} {'width':>7} {'delta_IC':>10} {'IC_spec':>10} {'family':>25}")
    for _, row in comparison_sorted.head(10).iterrows():
        print(f"{int(row['candidate_rank']):>6} {row['max_velocity_cm_s']:>6.2f} {row['min_velocity_cm_s']:>6.2f} {row['peak_frequency_microhz']:>8.1f} {row['frequency_width_microhz']:>7.1f} {row['delta_information_criterion']:>10.2f} {row['information_criterion']:>10.2f} {row['candidate_family'][:24]:>25}")

    print()

    # Check consistency: is there a linear relationship?
    deltas = comparison['delta_information_criterion'].values
    ic_vals = comparison['information_criterion'].values

    # Pearson correlation between delta_IC and absolute IC
    corr = np.corrcoef(deltas, ic_vals)[0, 1]

    # Linear regression: IC = a + b * delta_IC
    if len(deltas) > 1:
        slope, intercept = np.polyfit(deltas, ic_vals, 1)
        residuals = ic_vals - (intercept + slope * deltas)
        rmse = np.sqrt(np.mean(residuals**2))
        r_squared = 1 - np.sum(residuals**2) / np.sum((ic_vals - np.mean(ic_vals))**2)
    else:
        slope = intercept = rmse = r_squared = float('nan')

    print(f"\nLinear relationship check:")
    print(f"  Pearson correlation (delta_IC vs IC): {corr:.4f}")
    print(f"  Linear fit: IC = {intercept:.2f} + {slope:.4f} * delta_IC")
    print(f"  R² = {r_squared:.6f}")
    print(f"  RMSE = {rmse:.4f}")
    print(f"  Mean IC = {np.mean(ic_vals):.2f}, Range = [{np.min(ic_vals):.2f}, {np.max(ic_vals):.2f}]")
    print(f"  Mean delta_IC = {np.mean(deltas):.4f}, Range = [{np.min(deltas):.4f}, {np.max(deltas):.4f}]")

    print()

    # Check if the offset is approximately constant
    # If IC = constant + delta_IC, then slope ≈ 1 and residuals should be small
    print(f"Interpretation:")
    if abs(slope - 1.0) < 0.01:
        print(f"  Slope ≈ 1.0: The two tables use the SAME scale for IC values.")
        print(f"  Offset (constant term) = {intercept:.2f}: This is the baseline shift between tables.")
    elif abs(slope) < 0.1:
        print(f"  Slope ≈ 0: No relationship between delta_IC and absolute IC on shared combos.")
    else:
        print(f"  Slope = {slope:.4f}: The tables use DIFFERENT scales or formulas for IC.")

    if r_squared > 0.99:
        print(f"  R² > 0.99: Near-perfect linear relationship. Strong evidence for shared normalization.")
    elif r_squared > 0.95:
        print(f"  R² > 0.95: Strong linear relationship. Likely shared normalization with minor differences.")
    elif r_squared > 0.80:
        print(f"  R² > 0.80: Moderate linear relationship. Partial evidence for shared normalization.")
    else:
        print(f"  R² < 0.80: Weak linear relationship. Insufficient evidence for shared normalization.")

    # Print all shared combos for reference
    print(f"\nAll {len(comparison)} shared parameter combinations:")
    print(f"{'Rank':>6} {'v_max':>6} {'v_min':>6} {'f_peak':>8} {'width':>7} {'delta_IC':>10} {'IC_spec':>10} {'family':>25}")
    for _, row in comparison_sorted.iterrows():
        print(f"{int(row['candidate_rank']):>6} {row['max_velocity_cm_s']:>6.2f} {row['min_velocity_cm_s']:>6.2f} {row['peak_frequency_microhz']:>8.1f} {row['frequency_width_microhz']:>7.1f} {row['delta_information_criterion']:>10.4f} {row['information_criterion']:>10.2f} {row['candidate_family'][:24]:>25}")

    # Save results
    results = {
        'n_shared_combinations': int(len(comparison)),
        'pearson_correlation': float(corr),
        'linear_fit_slope': float(slope),
        'linear_fit_intercept': float(intercept),
        'r_squared': float(r_squared),
        'rmse': float(rmse),
        'mean_ic': float(np.mean(ic_vals)),
        'ic_range': [float(np.min(ic_vals)), float(np.max(ic_vals))],
        'mean_delta_ic': float(np.mean(deltas)),
        'delta_ic_range': [float(np.min(deltas)), float(np.max(deltas))],
        'shared_combinations': comparison_sorted.to_dict(orient='records'),
    }

    import json
    output_path = Path("/data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project/working/baseline_comparability_check.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")
