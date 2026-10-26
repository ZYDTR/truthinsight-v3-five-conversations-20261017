#!/usr/bin/env python3
"""
Generate result artifacts for the gravity spectral structure analysis.
Produces: result_artifacts.json (machine-readable), summary statistics, and key comparisons.
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
import json

DATA_DIR = Path(__file__).parent.parent / "data"
_DEFAULT_OUTPUT_DIR = Path(__file__).parent

# Accept --output-dir <path> as first CLI argument for clean-directory reproduction
if len(sys.argv) > 1 and sys.argv[1] == "--output-dir" and len(sys.argv) > 2:
    OUTPUT_DIR = Path(sys.argv[2])
else:
    OUTPUT_DIR = _DEFAULT_OUTPUT_DIR

# ─── Paths to adopted sub-side artifacts (read-only, embedded into result_artifacts.json) ───
PROJECT_ROOT = Path(__file__).parent.parent
CORRECTED_FFT_PATH = PROJECT_ROOT / "working/subagent_fft_loo_corrected/fft_results_corrected.json"
CORRECTED_CONSISTENCY_PATH = PROJECT_ROOT / "working/subagent_fft_loo_corrected/consistency_results_corrected.json"
LOO_PATH = PROJECT_ROOT / "working/subagent_fft_loo/loo_results.json"
VERIFICATION_PATH = PROJECT_ROOT / "working/subagent_verification/verification_results.json"

# Load data
residuals = pd.read_csv(DATA_DIR / "pass_residual_traces.tsv", sep="\t")
candidate_spectrum = pd.read_csv(DATA_DIR / "candidate_spectrum_comparison.tsv", sep="\t")
mode_frequency = pd.read_csv(DATA_DIR / "mode_frequency_grid.tsv", sep="\t")
ranked_grid = pd.read_csv(DATA_DIR / "ranked_full_parameter_grid.tsv", sep="\t")
uniform_alt = pd.read_csv(DATA_DIR / "uniform_alternative_comparison.tsv", sep="\t")

models = ['residual_model_A_mm_s', 'residual_model_B_mm_s', 'residual_model_C_mm_s']
passes = sorted(residuals['pass_id'].unique())

# ─── 1. Per-pass residual statistics ────────────────────────────────────────
per_pass = []
for pid in passes:
    sub = residuals[residuals['pass_id'] == pid]
    t = sub['relative_time_min'].values
    for mc in models:
        r = sub[mc].values
        # Lag-1 autocorrelation
        if len(r) > 1:
            mean_r = np.mean(r)
            var_r = np.var(r)
            acf_lag1 = np.mean((r[:-1] - mean_r) * (r[1:] - mean_r)) / var_r if var_r > 0 else 0.0
        else:
            acf_lag1 = 0.0

        # Detrended FFT peak frequency
        coeffs = np.polyfit(t, r, 1)
        r_det = r - np.polyval(coeffs, t)
        n = len(r_det)
        fft_vals = np.fft.rfft(r_det)
        fft_freqs = np.fft.rfftfreq(n, d=np.mean(np.diff(t)))
        fft_power = np.abs(fft_vals) ** 2

        # Top non-DC peak
        if len(fft_freqs) > 2:
            top_idx = np.argmax(fft_power[1:]) + 1  # skip DC
            peak_freq_hz = fft_freqs[top_idx]
            peak_freq_uz = peak_freq_hz * 1e6
            peak_power_val = float(fft_power[top_idx])
        else:
            peak_freq_uz = None
            peak_power_val = 0.0

        per_pass.append({
            'pass_id': pid,
            'model': mc,
            'n_samples': int(len(r)),
            'mean': float(np.mean(r)),
            'std': float(np.std(r)),
            'median': float(np.median(r)),
            'min': float(np.min(r)),
            'max': float(np.max(r)),
            'acf_lag1': float(acf_lag1),
            'top_fft_peak_microhz': float(peak_freq_uz) if peak_freq_uz is not None else None,
            'top_fft_power': float(peak_power_val),
        })

per_pass_df = pd.DataFrame(per_pass)

# ─── 2. Cross-model correlations ────────────────────────────────────────────
cross_corr = []
for pid in passes:
    sub = residuals[residuals['pass_id'] == pid]
    for i, m1 in enumerate(models):
        for m2 in models[i+1:]:
            r = sub[m1].corr(sub[m2])
            cross_corr.append({
                'pass_id': pid,
                'model_pair': f"{m1}_vs_{m2}",
                'pearson_r': float(r) if not np.isnan(r) else None,
            })
cross_corr_df = pd.DataFrame(cross_corr)

# ─── 3. Variance decomposition ──────────────────────────────────────────────
var_decomp = {}
for mc in models:
    all_vals = residuals[mc].values
    total_var = float(np.var(all_vals))
    pass_means = residuals.groupby('pass_id')[mc].mean()
    between_var = float(np.var(pass_means))
    within_vars = residuals.groupby('pass_id')[mc].var()
    avg_within = float(within_vars.mean())
    var_decomp[mc] = {
        'total_variance': total_var,
        'between_pass_variance': between_var,
        'avg_within_pass_variance': avg_within,
        'between_pass_fraction': between_var / total_var if total_var > 0 else 0.0,
    }

# ─── 4. Candidate spectrum best candidates ──────────────────────────────────
global_best_idx = candidate_spectrum['information_criterion'].idxmin()
global_best = candidate_spectrum.loc[global_best_idx]

# Best per velocity setting
best_per_vel = []
for v in sorted(candidate_spectrum['max_velocity_cm_s'].unique()):
    sub = candidate_spectrum[candidate_spectrum['max_velocity_cm_s'] == v]
    idx = sub['information_criterion'].idxmin()
    row = sub.loc[idx]
    best_per_vel.append({
        'max_velocity_cm_s': float(row['max_velocity_cm_s']),
        'min_velocity_cm_s': float(row['min_velocity_cm_s']),
        'peak_frequency_microhz': float(row['peak_frequency_microhz']),
        'peak_width_microhz': float(row['peak_width_microhz']),
        'information_criterion': float(row['information_criterion']),
    })

# Ranked grid top entries
top_ranked = ranked_grid.head(10).to_dict(orient='records')

# Delta IC gaps
delta_ic_gaps = []
for i in range(min(20, len(ranked_grid) - 1)):
    delta_ic_gaps.append({
        'from_rank': int(ranked_grid.iloc[i]['candidate_rank']),
        'to_rank': int(ranked_grid.iloc[i+1]['candidate_rank']),
        'gap': float(ranked_grid.iloc[i+1]['delta_information_criterion'] - ranked_grid.iloc[i]['delta_information_criterion']),
    })

# ─── 5. Uniform alternative ─────────────────────────────────────────────────
uniform_best_idx = uniform_alt['information_criterion'].idxmin()
uniform_best = uniform_alt.loc[uniform_best_idx]

# ─── 6. Mode-frequency grid summary ─────────────────────────────────────────
modes_in_range = mode_frequency[
    (mode_frequency['mode_frequency_microhz'] >= 900) &
    (mode_frequency['mode_frequency_microhz'] <= 1300)
]

mode_summary = []
for _, row in modes_in_range.iterrows():
    mode_summary.append({
        'angular_degree': int(row['angular_degree']),
        'radial_order': int(row['radial_order']),
        'mode_frequency_microhz': float(row['mode_frequency_microhz']),
        'surface_velocity_cm_s': float(row['surface_velocity_cm_s']),
        'coupling_coefficient': float(row['coupling_coefficient']),
    })

# ─── 7. First-half vs second-half consistency ───────────────────────────────
half_results = []
for pid in passes:
    sub = residuals[residuals['pass_id'] == pid].sort_values('relative_time_min')
    mid = len(sub) // 2
    h1 = sub.iloc[:mid]
    h2 = sub.iloc[mid:]
    for mc in models:
        half_results.append({
            'pass_id': pid,
            'model': mc,
            'h1_mean': float(np.mean(h1[mc].values)),
            'h2_mean': float(np.mean(h2[mc].values)),
            'h1_std': float(np.std(h1[mc].values)),
            'h2_std': float(np.std(h2[mc].values)),
            'mean_diff': float(np.mean(h1[mc].values) - np.mean(h2[mc].values)),
        })
half_df = pd.DataFrame(half_results)

# ─── 8. Embed corrected FFT results (main-side self-check, unit-corrected) ───
corrected_fft_data = None
if CORRECTED_FFT_PATH.exists():
    with open(CORRECTED_FFT_PATH, "r") as f:
        corrected_fft_data = json.load(f)

# ─── 9. Embed corrected consistency analysis ────────────────────────────
corrected_consistency_data = None
if CORRECTED_CONSISTENCY_PATH.exists():
    with open(CORRECTED_CONSISTENCY_PATH, "r") as f:
        corrected_consistency_data = json.load(f)

# ─── 10. Embed LOO robustness results ──────────────────────────────────
loo_data = None
if LOO_PATH.exists():
    with open(LOO_PATH, "r") as f:
        loo_data = json.load(f)

# ─── 11. Embed independent verification results ────────────────────────
verification_data = None
if VERIFICATION_PATH.exists():
    with open(VERIFICATION_PATH, "r") as f:
        verification_data = json.load(f)

# ─── Assemble and save ──────────────────────────────────────────────────────
artifacts = {
    'task_id': 'Astronomy_02_gravity_spectral_structure',
    't0': '2022-01-01',
    'data_dimensions': {
        'n_passes': len(passes),
        'n_time_samples_total': int(residuals.shape[0]),
        'samples_per_pass': [int(len(residuals[residuals['pass_id'] == p])) for p in passes],
        'n_candidate_spectrum_rows': int(candidate_spectrum.shape[0]),
        'n_ranked_candidates': int(ranked_grid.shape[0]),
        'n_mode_entries': int(mode_frequency.shape[0]),
        'n_uniform_alternatives': int(uniform_alt.shape[0]),
    },
    'temporal_analysis': {
        'per_pass_statistics': per_pass_df.to_dict(orient='records'),
        'mean_autocorrelation_by_model': {
            mc: float(per_pass_df[per_pass_df['model'] == mc]['acf_lag1'].mean())
            for mc in models
        },
        'variance_decomposition': var_decomp,
        'first_half_vs_second_half': half_df.to_dict(orient='records'),
    },
    'cross_model_agreement': {
        'per_pass_correlations': cross_corr_df.to_dict(orient='records'),
        'mean_correlation': {
            pair: float(cross_corr_df[cross_corr_df['model_pair'] == pair]['pearson_r'].mean())
            for pair in cross_corr_df['model_pair'].unique()
        },
    },
    'spectral_analysis': {
        'global_best_candidate': {
            'max_velocity_cm_s': float(global_best['max_velocity_cm_s']),
            'min_velocity_cm_s': float(global_best['min_velocity_cm_s']),
            'peak_frequency_microhz': float(global_best['peak_frequency_microhz']),
            'peak_width_microhz': float(global_best['peak_width_microhz']),
            'information_criterion': float(global_best['information_criterion']),
        },
        'best_per_velocity_setting': best_per_vel,
        'top_10_ranked_candidates': top_ranked,
        'delta_ic_gaps_top20': delta_ic_gaps,
        'candidates_within_delta10': int(len(ranked_grid[ranked_grid['delta_information_criterion'] <= 10])),
        'candidates_within_delta20': int(len(ranked_grid[ranked_grid['delta_information_criterion'] <= 20])),
    },
    'uniform_alternative': {
        'best_uniform': {
            'uniform_velocity_cm_s': float(uniform_best['uniform_velocity_cm_s']),
            'information_criterion': float(uniform_best['information_criterion']),
        },
        'improvement_over_best_uniform': float(uniform_best['information_criterion'] - global_best['information_criterion']),
        'uniform_curve': uniform_alt.to_dict(orient='records'),
    },
    'mode_frequency': {
        'total_modes': int(mode_frequency.shape[0]),
        'modes_in_900_1300_microhz': len(mode_summary),
        'modes_in_range': mode_summary,
    },
    # ─── Embedded sub-side / corrected analysis artifacts ────────────────
    'corrected_fft_periodicity': corrected_fft_data,
    'corrected_consistency_analysis': corrected_consistency_data,
    'loo_robustness': loo_data,
    'independent_verification': verification_data,
}

with open(OUTPUT_DIR / "result_artifacts.json", "w") as f:
    json.dump(artifacts, f, indent=2)

print("Result artifacts saved to output/result_artifacts.json")
print(f"Total artifact size: {Path(OUTPUT_DIR / 'result_artifacts.json').stat().st_size} bytes")
