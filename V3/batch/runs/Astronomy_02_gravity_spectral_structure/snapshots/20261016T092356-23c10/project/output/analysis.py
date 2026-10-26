#!/usr/bin/env python3
"""
Time-Resolved Gravity Residuals and Candidate Spectral Structure Analysis
Task: Astronomy_02_gravity_spectral_structure (T0: 2022-01-01)

Analyzes whether reproducible temporal or spectral structure is supported
in the anonymous gravitating system data.
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent

# ─── Load all data ──────────────────────────────────────────────────────────

print("Loading data...")
residuals = pd.read_csv(DATA_DIR / "pass_residual_traces.tsv", sep="\t")
candidate_spectrum = pd.read_csv(DATA_DIR / "candidate_spectrum_comparison.tsv", sep="\t")
mode_frequency = pd.read_csv(DATA_DIR / "mode_frequency_grid.tsv", sep="\t")
ranked_grid = pd.read_csv(DATA_DIR / "ranked_full_parameter_grid.tsv", sep="\t")
uniform_alt = pd.read_csv(DATA_DIR / "uniform_alternative_comparison.tsv", sep="\t")

print(f"Residuals: {residuals.shape[0]} rows, {residuals['pass_id'].nunique()} passes")
print(f"Candidate spectrum: {candidate_spectrum.shape[0]} rows")
print(f"Mode frequency grid: {mode_frequency.shape[0]} rows")
print(f"Ranked parameter grid: {ranked_grid.shape[0]} rows")
print(f"Uniform alternative: {uniform_alt.shape[0]} rows")

# ─── Analysis 1: Temporal structure in residual traces ──────────────────────
print("\n=== ANALYSIS 1: Temporal structure in residual traces ===")

# Per-pass statistics
passes = sorted(residuals['pass_id'].unique())
time_col = 'relative_time_min'
model_cols = ['residual_model_A_mm_s', 'residual_model_B_mm_s', 'residual_model_C_mm_s']

per_pass_stats = []
for pid in passes:
    subset = residuals[residuals['pass_id'] == pid]
    t = subset[time_col].values
    for mc in model_cols:
        r = subset[mc].values
        per_pass_stats.append({
            'pass_id': pid,
            'model': mc,
            'n_samples': len(r),
            'mean': np.mean(r),
            'std': np.std(r),
            'min': np.min(r),
            'max': np.max(r),
            'range': np.ptp(r),
            'median': np.median(r),
            'skewness': pd.Series(r).skew(),
            'kurtosis': pd.Series(r).kurtosis(),
            'first_quarter': np.percentile(r, 25),
            'third_quarter': np.percentile(r, 75),
        })

stats_df = pd.DataFrame(per_pass_stats)
print(stats_df.to_string(index=False))

# Check for autocorrelation within each pass (temporal dependence)
print("\nAutocorrelation analysis (lag-1) per pass:")
autocorr_results = []
for pid in passes:
    subset = residuals[residuals['pass_id'] == pid]
    for mc in model_cols:
        r = subset[mc].values
        # Lag-1 autocorrelation
        if len(r) > 1:
            mean_r = np.mean(r)
            var_r = np.var(r)
            if var_r > 0:
                acf_lag1 = np.mean((r[:-1] - mean_r) * (r[1:] - mean_r)) / var_r
            else:
                acf_lag1 = 0.0
        else:
            acf_lag1 = 0.0
        autocorr_results.append({
            'pass_id': pid,
            'model': mc,
            'acf_lag1': acf_lag1
        })

autocorr_df = pd.DataFrame(autocorr_results)
print(autocorr_df.to_string(index=False))

# Overall mean autocorrelation
overall_acf = autocorr_df.groupby('model')['acf_lag1'].mean()
print("\nMean lag-1 autocorrelation by model:")
print(overall_acf)

# Test for periodicity using FFT on pooled residuals
print("\n=== Periodicity analysis via FFT ===")
fft_results = {}
for pid in passes:
    subset = residuals[residuals['pass_id'] == pid]
    for mc in model_cols:
        key = f"{pid}_{mc}"
        r = subset[mc].values
        t = subset[time_col].values

        # Remove linear trend
        coeffs = np.polyfit(t, r, 1)
        r_detrended = r - np.polyval(coeffs, t)

        # FFT
        n = len(r_detrended)
        fft_vals = np.fft.rfft(r_detrended)
        fft_freqs = np.fft.rfftfreq(n, d=np.mean(np.diff(t)))
        fft_power = np.abs(fft_vals) ** 2

        # Find top peaks (excluding DC)
        if len(fft_freqs) > 2:
            top_indices = np.argsort(fft_power[-100:])[-10:]  # top 10 non-DC
            top_indices = top_indices[top_indices > 0]  # exclude DC
            if len(top_indices) > 0:
                peak_freqs = fft_freqs[top_indices]
                peak_powers = fft_power[top_indices]
                # Convert microHz to period
                peak_periods = 1.0 / (peak_freqs * 1e-6) if np.any(peak_freqs > 0) else []

                fft_results[key] = {
                    'top_peak_freq_microhz': float(peak_freqs[0]) if len(peak_freqs) > 0 else None,
                    'top_peak_power': float(peak_powers[0]) if len(peak_powers) > 0 else None,
                    'num_peaks_above_threshold': int(np.sum(peak_powers > np.median(peak_powers))),
                }

fft_df = pd.DataFrame.from_dict(fft_results, orient='index')
print(fft_df.head(20).to_string())

# ─── Analysis 2: Cross-model agreement ──────────────────────────────────────
print("\n=== ANALYSIS 2: Cross-model agreement ===")

# Correlation between models within each pass
cross_model_corr = []
for pid in passes:
    subset = residuals[residuals['pass_id'] == pid]
    for i, m1 in enumerate(model_cols):
        for m2 in model_cols[i+1:]:
            corr = subset[m1].corr(subset[m2])
            cross_model_corr.append({
                'pass_id': pid,
                'model_pair': f"{m1}_vs_{m2}",
                'pearson_r': corr if not np.isnan(corr) else None
            })

cross_corr_df = pd.DataFrame(cross_model_corr)
print("Cross-model Pearson correlations:")
print(cross_corr_df.groupby('model_pair')['pearson_r'].agg(['mean', 'std', 'min', 'max']).to_string())

# Model consistency: do all three models show similar patterns?
# Compute pairwise correlation matrices across all passes
all_means = {}
all_stds = {}
for mc in model_cols:
    pivot = residuals.pivot_table(index=time_col, columns='pass_id', values=mc)
    all_means[mc] = pivot.mean(axis=1)
    all_stds[mc] = pivot.std(axis=1)

print("\nModel-to-model correlation of means across time:")
for i, m1 in enumerate(model_cols):
    for m2 in model_cols[i+1:]:
        common = all_means[m1].dropna().index.intersection(all_means[m2].dropna().index)
        if len(common) > 2:
            r = all_means[m1][common].corr(all_means[m2][common])
            print(f"  {m1} vs {m2}: r={r:.4f}")

# ─── Analysis 3: Candidate spectrum analysis ───────────────────────────────
print("\n=== ANALYSIS 3: Candidate spectrum structure ===")

# Examine IC landscape
print("Candidate spectrum IC summary:")
print(candidate_spectrum['information_criterion'].describe())

# Find minimum IC per velocity setting
velocities = candidate_spectrum['max_velocity_cm_s'].unique()
print(f"\nVelocity settings explored: {sorted(velocities)}")

# Best candidate per velocity
best_per_vel = candidate_spectrum.loc[candidate_spectrum.groupby('max_velocity_cm_s')['information_criterion'].idxmin()]
print("\nBest candidate per max_velocity:")
print(best_per_vel[['max_velocity_cm_s', 'peak_frequency_microhz', 'peak_width_microhz', 'information_criterion']].to_string(index=False))

# Frequency amplitude scan: find the global minimum IC
global_best_idx = candidate_spectrum['information_criterion'].idxmin()
global_best = candidate_spectrum.loc[global_best_idx]
print(f"\nGlobal best candidate: IC={global_best['information_criterion']}, "
      f"v_max={global_best['max_velocity_cm_s']}, freq={global_best['peak_frequency_microhz']} uHz, "
      f"width={global_best['peak_width_microhz']} uHz")

# IC distribution shape
ic_values = candidate_spectrum['information_criterion'].values
print(f"\nIC range: [{ic_values.min():.1f}, {ic_values.max():.1f}]")
print(f"IC std: {ic_values.std():.1f}")

# How many candidates have IC within 10 of the best?
threshold_10 = ic_values[ic_values < ic_values.min() + 10]
print(f"Candidates within delta_IC=10 of best: {len(threshold_10)}")
threshold_20 = ic_values[ic_values < ic_values.min() + 20]
print(f"Candidates within delta_IC=20 of best: {len(threshold_20)}")

# ─── Analysis 4: Ranked parameter grid ─────────────────────────────────────
print("\n=== ANALYSIS 4: Ranked full parameter grid ===")

print(f"Top 10 ranked candidates:")
print(ranked_grid.head(10)[['candidate_rank', 'max_velocity_cm_s', 'min_velocity_cm_s',
                            'peak_frequency_microhz', 'frequency_width_microhz',
                            'delta_information_criterion']].to_string(index=False))

# Delta IC gap analysis
delta_ic = ranked_grid['delta_information_criterion'].values
gaps = np.diff(delta_ic)
print(f"\nDelta IC gaps (rank 1->2): {gaps[0]:.1f}")
print(f"Delta IC gaps (rank 9->10): {gaps[8]:.1f}")
print(f"Delta IC gaps (rank 19->20): {gaps[18]:.1f}")

# Is rank 1 clearly separated?
print(f"\nRank 1 delta_IC = 0 (reference)")
print(f"Rank 2 delta_IC = {ranked_grid.iloc[1]['delta_information_criterion']:.1f}")
print(f"Rank 3 delta_IC = {ranked_grid.iloc[2]['delta_information_criterion']:.1f}")

# Parameter combinations at low delta IC
low_delta = ranked_grid[ranked_grid['delta_information_criterion'] <= 10]
print(f"\nCandidates with delta_IC <= 10: {len(low_delta)}")
print(low_delta[['candidate_rank', 'max_velocity_cm_s', 'min_velocity_cm_s',
                  'peak_frequency_microhz', 'frequency_width_microhz',
                  'delta_information_criterion']].to_string(index=False))

# ─── Analysis 5: Uniform alternative comparison ─────────────────────────────
print("\n=== ANALYSIS 5: Uniform alternative comparison ===")

print(uniform_alt.to_string(index=False))

# Find minimum IC in uniform alternatives
uniform_best_idx = uniform_alt['information_criterion'].idxmin()
uniform_best = uniform_alt.loc[uniform_best_idx]
print(f"\nBest uniform alternative: v_uniform={uniform_best['uniform_velocity_cm_s']}, IC={uniform_best['information_criterion']:.1f}")

# Compare best uniform vs best candidate
best_candidate_ic = candidate_spectrum['information_criterion'].min()
print(f"\nBest candidate IC: {best_candidate_ic:.1f}")
print(f"Best uniform IC: {uniform_best['information_criterion']:.1f}")
print(f"Improvement over uniform: {uniform_best['information_criterion'] - best_candidate_ic:.1f}")

# Where does the uniform IC curve have its minimum?
uniform_min_idx = uniform_alt['information_criterion'].idxmin()
print(f"\nUniform IC minimum at velocity: {uniform_alt.iloc[uniform_min_idx]['uniform_velocity_cm_s']} cm/s")

# ─── Analysis 6: Mode-frequency grid ───────────────────────────────────────
print("\n=== ANALYSIS 6: Mode-frequency grid ===")

print(mode_frequency.to_string(index=False))

# Check which modes fall in the frequency range of interest (~1000-1200 microHz)
oi_mask = (mode_frequency['mode_frequency_microhz'] >= 900) & (mode_frequency['mode_frequency_microhz'] <= 1300)
oi_modes = mode_frequency[oi_mask]
print(f"\nModes in 900-1300 microHz range: {len(oi_modes)}")
print(oi_modes.to_string(index=False))

# Coupling coefficient trends
print("\nCoupling coefficient by radial order:")
for ro in sorted(mode_frequency['radial_order'].unique()):
    subset = mode_frequency[mode_frequency['radial_order'] == ro]
    print(f"  l={subset['angular_degree'].min()}-{subset['angular_degree'].max()}, "
          f"n={ro}: coupling range [{subset['coupling_coefficient'].min():.2e}, {subset['coupling_coefficient'].max():.2e}]")

# ─── Analysis 7: Robustness checks ─────────────────────────────────────────
print("\n=== ANALYSIS 7: Robustness checks ===")

# 7a: Leave-one-pass-out test for temporal structure
print("\n7a. Leave-one-pass-out temporal consistency:")
loo_results = []
for leave_out in passes:
    remaining = residuals[residuals['pass_id'] != leave_out]
    for mc in model_cols:
        r = remaining[mc].values
        loo_results.append({
            'leave_out': leave_out,
            'model': mc,
            'remaining_mean': np.mean(r),
            'remaining_std': np.std(r),
            'remaining_n': len(r)
        })

loo_df = pd.DataFrame(loo_results)
print(loo_df.groupby(['model'])['remaining_mean'].agg(['mean', 'std']).to_string())

# 7b: First-half vs second-half consistency within each pass
print("\n7b. First-half vs second-half consistency:")
half_results = []
for pid in passes:
    subset = residuals[residuals['pass_id'] == pid].sort_values(time_col)
    mid = len(subset) // 2
    first_half = subset.iloc[:mid]
    second_half = subset.iloc[mid:]
    for mc in model_cols:
        h1 = first_half[mc].values
        h2 = second_half[mc].values
        half_results.append({
            'pass_id': pid,
            'model': mc,
            'h1_mean': np.mean(h1),
            'h2_mean': np.mean(h2),
            'h1_std': np.std(h1),
            'h2_std': np.std(h2),
            'mean_diff': np.mean(h1) - np.mean(h2),
            'std_ratio': np.std(h1) / np.std(h2) if np.std(h2) > 0 else np.nan
        })

half_df = pd.DataFrame(half_results)
print("Mean differences (first-half - second-half):")
print(half_df.groupby('model')['mean_diff'].agg(['mean', 'std']).to_string())

# 7c: Pass-level variance decomposition
print("\n7c. Variance decomposition (within-pass vs between-pass):")
var_decomp = {}
for mc in model_cols:
    all_vals = residuals[mc].values
    total_var = np.var(all_vals)

    # Between-pass variance
    pass_means = residuals.groupby('pass_id')[mc].mean()
    between_var = np.var(pass_means)

    # Within-pass variance (average)
    within_vars = residuals.groupby('pass_id')[mc].var()
    avg_within_var = within_vars.mean()

    var_decomp[mc] = {
        'total_variance': total_var,
        'between_pass_variance': between_var,
        'avg_within_pass_variance': avg_within_var,
        'between_pass_fraction': between_var / total_var if total_var > 0 else 0,
    }
    print(f"  {mc}: total={total_var:.6f}, between={between_var:.6f}, "
          f"within={avg_within_var:.6f}, between_fraction={var_decomp[mc]['between_pass_fraction']:.4f}")

# ─── Save results ───────────────────────────────────────────────────────────

results = {
    'task_id': 'Astronomy_02_gravity_spectral_structure',
    't0': '2022-01-01',
    'data_summary': {
        'n_passes': int(residuals['pass_id'].nunique()),
        'n_time_samples_total': int(residuals.shape[0]),
        'n_candidates_spectrum': int(candidate_spectrum.shape[0]),
        'n_ranked_candidates': int(ranked_grid.shape[0]),
        'n_mode_entries': int(mode_frequency.shape[0]),
        'n_uniform_alternatives': int(uniform_alt.shape[0]),
    },
    'temporal_analysis': {
        'per_pass_stats': stats_df.to_dict(orient='records'),
        'autocorrelation': autocorr_df.to_dict(orient='records'),
        'variance_decomposition': var_decomp,
    },
    'spectral_analysis': {
        'best_candidate': {
            'max_velocity_cm_s': float(global_best['max_velocity_cm_s']),
            'min_velocity_cm_s': float(global_best['min_velocity_cm_s']),
            'peak_frequency_microhz': float(global_best['peak_frequency_microhz']),
            'peak_width_microhz': float(global_best['peak_width_microhz']),
            'information_criterion': float(global_best['information_criterion']),
        },
        'candidates_within_delta10': int(len(threshold_10)),
        'candidates_within_delta20': int(len(threshold_20)),
        'ranked_top10': ranked_grid.head(10).to_dict(orient='records'),
    },
    'uniform_alternative': {
        'best_uniform': {
            'uniform_velocity_cm_s': float(uniform_best['uniform_velocity_cm_s']),
            'information_criterion': float(uniform_best['information_criterion']),
        },
        'best_candidate_ic': float(best_candidate_ic),
        'improvement_over_uniform': float(uniform_best['information_criterion'] - best_candidate_ic),
    },
    'cross_model_agreement': {
        'correlations': cross_corr_df.to_dict(orient='records'),
    },
    'robustness': {
        'half_consistency': half_df.to_dict(orient='records'),
    },
}

with open(OUTPUT_DIR / "analysis_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to output/analysis_results.json")

# ─── Generate summary statistics for report ─────────────────────────────────
print("\n=== SUMMARY STATISTICS FOR REPORT ===")

# Key finding numbers
print(f"\n1. Number of complete passes: {len(passes)}")
print(f"2. Samples per pass: ~{residuals.shape[0] // len(passes)}")
print(f"3. Best candidate IC: {best_candidate_ic:.1f}")
print(f"4. Best uniform IC: {uniform_best['information_criterion']:.1f}")
print(f"5. Candidates with delta_IC <= 10: {len(low_delta)}")
print(f"6. Rank 1 parameters: v_max={ranked_grid.iloc[0]['max_velocity_cm_s']}, "
      f"v_min={ranked_grid.iloc[0]['min_velocity_cm_s']}, "
      f"freq={ranked_grid.iloc[0]['peak_frequency_microhz']}, "
      f"width={ranked_grid.iloc[0]['frequency_width_microhz']}")
print(f"7. Rank 2 parameters: v_max={ranked_grid.iloc[1]['max_velocity_cm_s']}, "
      f"v_min={ranked_grid.iloc[1]['min_velocity_cm_s']}, "
      f"freq={ranked_grid.iloc[1]['peak_frequency_microhz']}, "
      f"width={ranked_grid.iloc[1]['frequency_width_microhz']}, "
      f"delta_IC={ranked_grid.iloc[1]['delta_information_criterion']:.1f}")

# Mean autocorrelation
mean_acf_a = autocorr_df[autocorr_df['model'] == 'residual_model_A_mm_s']['acf_lag1'].mean()
mean_acf_b = autocorr_df[autocorr_df['model'] == 'residual_model_B_mm_s']['acf_lag1'].mean()
mean_acf_c = autocorr_df[autocorr_df['model'] == 'residual_model_C_mm_s']['acf_lag1'].mean()
print(f"8. Mean lag-1 autocorrelation: A={mean_acf_a:.4f}, B={mean_acf_b:.4f}, C={mean_acf_c:.4f}")

# Variance decomposition
for mc, vd in var_decomp.items():
    short_name = mc.replace('residual_model_', '').replace('_mm_s', '')
    print(f"9. Variance fraction (between-pass) for model {short_name}: {vd['between_pass_fraction']:.4f}")

# Cross-model correlations
for i, m1 in enumerate(model_cols):
    for m2 in model_cols[i+1:]:
        pair_corrs = cross_corr_df[cross_corr_df['model_pair'] == f"{m1}_vs_{m2}"]['pearson_r'].dropna()
        if len(pair_corrs) > 0:
            short1 = m1.replace('residual_model_', '').replace('_mm_s', '')
            short2 = m2.replace('residual_model_', '').replace('_mm_s', '')
            print(f"10. Cross-model correlation ({short1} vs {short2}): mean={pair_corrs.mean():.4f}, "
                  f"std={pair_corrs.std():.4f}")
