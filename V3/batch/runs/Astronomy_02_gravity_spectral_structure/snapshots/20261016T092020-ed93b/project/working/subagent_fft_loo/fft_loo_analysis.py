#!/usr/bin/env python3
"""
FFT Periodicity Analysis and Leave-One-Pass-Out Robustness for Gravity Residual Data.

Independent analysis: does not import or execute any existing scripts.
Reads raw TSV data, performs FFT and LOO computations from scratch.
"""

import json
import numpy as np
from collections import defaultdict


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

DATA_DIR = "/data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project/data"
OUTPUT_DIR = "/data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project/working/subagent_fft_loo"


def load_pass_residual_traces():
    """Load pass_residual_traces.tsv into a dict of {pass_id: {model: (times, residuals)}}."""
    filepath = f"{DATA_DIR}/pass_residual_traces.tsv"
    passes = {}
    with open(filepath, "r") as f:
        header = f.readline().strip().split("\t")
        # Header: pass_id, relative_time_min, residual_model_A_mm_s, residual_model_C_mm_s, residual_model_B_mm_s
        col_map = {h.strip(): i for i, h in enumerate(header)}
        pass_col = col_map["pass_id"]
        time_col = col_map["relative_time_min"]
        model_cols = {
            "A": col_map["residual_model_A_mm_s"],
            "B": col_map["residual_model_B_mm_s"],
            "C": col_map["residual_model_C_mm_s"],
        }

        current_pass = None
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            pid = parts[pass_col]
            if pid != current_pass:
                current_pass = pid
                passes[pid] = {"A": ([], []), "B": ([], []), "C": ([], [])}
            t = float(parts[time_col])
            for model, col_idx in model_cols.items():
                passes[pid][model][0].append(t)
                passes[pid][model][1].append(float(parts[col_idx]))

    # Convert lists to numpy arrays
    for pid in passes:
        for model in ["A", "B", "C"]:
            times = np.array(passes[pid][model][0])
            residuals = np.array(passes[pid][model][1])
            # Sort by time
            sort_idx = np.argsort(times)
            passes[pid][model] = (times[sort_idx], residuals[sort_idx])

    return passes


def load_ranked_candidates():
    """Load ranked_full_parameter_grid.tsv."""
    filepath = f"{DATA_DIR}/ranked_full_parameter_grid.tsv"
    candidates = []
    with open(filepath, "r") as f:
        header = f.readline().strip().split("\t")
        col_map = {h.strip(): i for i, h in enumerate(header)}
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            row = {
                "candidate_rank": int(parts[col_map["candidate_rank"]]),
                "max_velocity_cm_s": float(parts[col_map["max_velocity_cm_s"]]),
                "min_velocity_cm_s": float(parts[col_map["min_velocity_cm_s"]]),
                "peak_frequency_microhz": float(parts[col_map["peak_frequency_microhz"]]),
                "frequency_width_microhz": float(parts[col_map["frequency_width_microhz"]]),
                "delta_information_criterion": float(parts[col_map["delta_information_criterion"]]),
            }
            candidates.append(row)
    return candidates


def load_candidate_spectrum():
    """Load candidate_spectrum_comparison.tsv."""
    filepath = f"{DATA_DIR}/candidate_spectrum_comparison.tsv"
    rows = []
    with open(filepath, "r") as f:
        header = f.readline().strip().split("\t")
        col_map = {h.strip(): i for i, h in enumerate(header)}
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 6:
                continue
            row = {
                "candidate_family": parts[col_map["candidate_family"]],
                "max_velocity_cm_s": float(parts[col_map["max_velocity_cm_s"]]),
                "min_velocity_cm_s": float(parts[col_map["min_velocity_cm_s"]]),
                "peak_frequency_microhz": float(parts[col_map["peak_frequency_microhz"]]),
                "peak_width_microhz": float(parts[col_map["peak_width_microhz"]]),
                "information_criterion": float(parts[col_map["information_criterion"]]),
            }
            rows.append(row)
    return rows


# =============================================================================
# 1. FFT PERIODICITY ANALYSIS
# =============================================================================

def fft_periodicity_analysis(passes):
    """
    For each pass and each model:
    - Detrend (remove linear trend via polyfit)
    - Compute FFT, find top-5 peak frequencies (excluding DC)
    - Convert to muHz
    - Cross-pass consistency check
    """
    results = {}
    all_top_peaks = []  # list of (pass_id, model, freq_muHz)

    for pid in sorted(passes.keys()):
        pass_result = {}
        for model in ["A", "B", "C"]:
            times, residuals = passes[pid][model]
            dt = np.mean(np.diff(times))  # time step in minutes

            # Detrend
            coeffs = np.polyfit(times, residuals, 1)
            detrended = residuals - np.polyval(coeffs, times)

            # FFT
            n = len(detrended)
            fft_vals = np.fft.rfft(detrended)
            fft_freqs = np.fft.rfftfreq(n, d=dt)  # frequency in 1/min

            # Exclude DC component (index 0)
            fft_freqs = fft_freqs[1:]
            fft_mags = np.abs(fft_vals[1:])

            # Find top-5 peaks: use argpartition for efficiency, then verify
            if len(fft_mags) >= 5:
                top_indices = np.argpartition(fft_mags, -5)[-5:]
                top_indices = top_indices[np.argsort(fft_mags[top_indices])[::-1]]
            else:
                top_indices = np.argsort(fft_mags)[::-1][:len(fft_mags)]

            top_freqs_hz = fft_freqs[top_indices]
            top_freqs_muhz = top_freqs_hz * 1e6  # convert Hz to muHz
            top_mags = fft_mags[top_indices]

            pass_result[model] = {
                "top_5_frequencies_muhz": [float(f) for f in top_freqs_muhz],
                "top_5_magnitudes": [float(m) for m in top_mags],
                "n_samples": n,
                "dt_minutes": float(dt),
            }

            for freq in top_freqs_muhz:
                all_top_peaks.append((pid, model, float(freq)))

        # Mean of top peak across models
        top_peaks_by_model = {}
        for model in ["A", "B", "C"]:
            top_peaks_by_model[model] = pass_result[model]["top_5_frequencies_muhz"][0]
        mean_top_peak = np.mean(list(top_peaks_by_model.values()))

        pass_result["mean_top_peak_across_models_muhz"] = float(mean_top_peak)
        pass_result["top_peak_per_model_muhz"] = top_peaks_by_model

        results[pid] = pass_result

    # Cross-pass consistency: count how many times each frequency bin appears
    # Round to nearest 10 muHz for grouping
    freq_bins = defaultdict(int)
    for pid, model, freq in all_top_peaks:
        binned = round(freq / 10) * 10
        freq_bins[binned] += 1

    # Check if any frequency appears in more than half of the passes (>11)
    total_passes = len(passes)
    common_signals = []
    for freq_bin, count in sorted(freq_bins.items(), key=lambda x: -x[1]):
        if count > total_passes / 2:
            common_signals.append({
                "frequency_muhz": freq_bin,
                "appearances": count,
                "passes_fraction": f"{count}/{total_passes}",
            })

    # Also report the most common frequencies even if below threshold
    top_common = sorted(freq_bins.items(), key=lambda x: -x[1])[:10]

    cross_pass_summary = {
        "total_passes": total_passes,
        "total_top_peak_count": len(all_top_peaks),
        "common_signals_above_threshold": common_signals,
        "top_10_frequencies": [{"frequency_muhz": f, "count": c} for f, c in top_common],
        "has_consistent_signal": len(common_signals) > 0,
    }

    return results, cross_pass_summary


# =============================================================================
# 2. LEAVE-ONE-PASS-OUT ROBUSTNESS
# =============================================================================

def loo_robustness_analysis(passes):
    """
    For each pass left out:
    - Compute summary stats of remaining residuals per model
    - Check if std changes >10% relative to full-data std
    - Specifically flag high-variance passes
    """
    # First compute full-data statistics
    full_stats = {}
    for model in ["A", "B", "C"]:
        all_residuals = []
        for pid in passes:
            _, res = passes[pid][model]
            all_residuals.extend(res.tolist())
        arr = np.array(all_residuals)
        full_stats[model] = {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "n_samples": len(arr),
        }

    loo_results = {}
    significant_changes = []

    for leave_out_pass in sorted(passes.keys()):
        exclusion_result = {"leave_out_pass": leave_out_pass}
        for model in ["A", "B", "C"]:
            remaining_residuals = []
            for pid in passes:
                if pid == leave_out_pass:
                    continue
                _, res = passes[pid][model]
                remaining_residuals.extend(res.tolist())
            arr = np.array(remaining_residuals)

            new_std = float(np.std(arr))
            old_std = full_stats[model]["std"]
            rel_change = (new_std - old_std) / old_std if old_std != 0 else float("nan")

            exclusion_result[model] = {
                "mean": float(np.mean(arr)),
                "std": new_std,
                "n_samples": len(arr),
                "relative_std_change": float(rel_change),
                "exceeds_10pct_threshold": abs(rel_change) > 0.10,
            }

            if abs(rel_change) > 0.10:
                significant_changes.append({
                    "leave_out_pass": leave_out_pass,
                    "model": model,
                    "full_std": old_std,
                    "loo_std": new_std,
                    "relative_change": float(rel_change),
                })

        loo_results[leave_out_pass] = exclusion_result

    # Analyze specific high-variance passes
    high_var_passes = {}
    for pid in sorted(passes.keys()):
        for model in ["A", "B", "C"]:
            _, res = passes[pid][model]
            high_var_passes[f"{pid}_{model}"] = {
                "mean": float(np.mean(res)),
                "std": float(np.std(res)),
                "n_samples": len(res),
            }

    # Identify which passes have highest variance
    var_by_pass = {}
    for pid in sorted(passes.keys()):
        model_stds = []
        for model in ["A", "B", "C"]:
            _, res = passes[pid][model]
            model_stds.append(np.std(res))
        var_by_pass[pid] = {
            "mean_std_across_models": float(np.mean(model_stds)),
            "std_per_model": {m: float(np.std(passes[pid][m][1])) for m in ["A", "B", "C"]},
        }

    # Sort by variance
    sorted_by_var = sorted(var_by_pass.items(), key=lambda x: -x[1]["mean_std_across_models"])

    loo_summary = {
        "full_data_stats": full_stats,
        "per_pass_exclusion": loo_results,
        "significant_changes_over_10pct": significant_changes,
        "high_variance_passes": {
            pid: var_by_pass[pid] for pid, _ in sorted_by_var[:5]
        },
        "all_pass_variances": var_by_pass,
        "loo_stability_holds": len(significant_changes) == 0,
        "num_significant_changes": len(significant_changes),
    }

    return loo_summary


# =============================================================================
# 3. CANDIDATE SPECTRUM CROSS-PASS CONSISTENCY
# =============================================================================

def candidate_spectrum_consistency(passes, ranked_candidates, spectrum_rows):
    """
    Analyze whether residual traces show features consistent with rank-1 parameters.
    Rank-1: v_max=30, v_min=0.05, f_peak=1010 muHz, width=275 muHz
    Acknowledge limitation: IC values are computed over all passes combined,
    so we cannot do true per-pass re-ranking.
    """
    rank1 = ranked_candidates[0]  # candidate_rank=1

    # Check spectrum comparison for the rank-1 parameter combination
    rank1_spectrum_matches = []
    for row in spectrum_rows:
        if (abs(row["peak_frequency_microhz"] - rank1["peak_frequency_microhz"]) < 1 and
            abs(row["max_velocity_cm_s"] - rank1["max_velocity_cm_s"]) < 0.01 and
            abs(row["min_velocity_cm_s"] - rank1["min_velocity_cm_s"]) < 0.01 and
            abs(row["peak_width_microhz"] - rank1["frequency_width_microhz"]) < 1):
            rank1_spectrum_matches.append(row)

    # Analyze whether the residual traces contain oscillatory features near 1010 muHz
    # 1010 muHz = 1010e-6 Hz = 0.00101 Hz
    # In terms of period: T = 1/f = 990 seconds ~ 16.5 minutes
    target_freq_muhz = rank1["peak_frequency_microhz"]
    target_period_min = 60.0 / (target_freq_muhz * 1e-6)  # period in minutes

    # Check if the time span of each pass is long enough to resolve this frequency
    pass_resolution_info = {}
    for pid in sorted(passes.keys()):
        times, _ = passes[pid]["A"]
        time_span_min = float(np.max(times) - np.min(times))
        n_samples = len(times)
        dt = np.mean(np.diff(times))
        nyquist_muhz = 1.0 / (2.0 * dt) * 1e6  # Nyquist in muHz
        resolution_muhz = 1.0 / (time_span_min) * 1e6  # frequency resolution in muHz

        pass_resolution_info[pid] = {
            "time_span_minutes": time_span_min,
            "n_samples": n_samples,
            "dt_minutes": float(dt),
            "nyquist_muhz": float(nyquist_muhz),
            "frequency_resolution_muhz": float(resolution_muhz),
            "can_resolve_target_freq": nyquist_muhz > target_freq_muhz,
        }

    # Check if the rank-1 frequency falls within the resolvable range for each pass
    resolvable_count = sum(1 for p in pass_resolution_info.values() if bool(p["can_resolve_target_freq"]))

    # Examine the spectrum comparison data for the best IC values
    best_ic_rows = sorted(spectrum_rows, key=lambda x: x["information_criterion"])[:10]

    # Check if the rank-1 parameters appear in the spectrum comparison
    rank1_in_spectrum = False
    for row in spectrum_rows:
        if (row["peak_frequency_microhz"] == rank1["peak_frequency_microhz"] and
            row["max_velocity_cm_s"] == rank1["max_velocity_cm_s"] and
            row["min_velocity_cm_s"] == rank1["min_velocity_cm_s"]):
            rank1_in_spectrum = True
            break

    # Convert numpy types for JSON serialization
    resolution_info_serializable = {}
    for pid, info in pass_resolution_info.items():
        resolution_info_serializable[pid] = {k: float(v) if isinstance(v, (np.floating, np.integer)) else v for k, v in info.items()}

    consistency_summary = {
        "rank1_parameters": rank1,
        "rank1_in_spectrum": bool(rank1_in_spectrum),
        "rank1_spectrum_matches": rank1_spectrum_matches,
        "best_10_spectrum_rows": best_ic_rows,
        "target_frequency_muhz": float(target_freq_muhz),
        "target_period_minutes": float(target_period_min),
        "pass_resolution_info": resolution_info_serializable,
        "passes_can_resolve_target": int(resolvable_count),
        "total_passes": len(passes),
        "limitation_note": (
            "The candidate_spectrum_comparison.tsv provides IC values computed over ALL passes combined. "
            "There is no per-pass candidate evaluation available in the data. "
            "Therefore, true per-pass candidate re-ranking cannot be performed. "
            "This analysis checks whether the residual traces have sufficient temporal "
            "resolution to detect the rank-1 frequency (1010 muHz)."
        ),
    }

    return consistency_summary


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("FFT Periodicity & LOO Robustness Analysis")
    print("=" * 60)

    # Load data
    print("\nLoading pass_residual_traces.tsv...")
    passes = load_pass_residual_traces()
    print(f"  Loaded {len(passes)} passes")
    for pid in sorted(passes.keys())[:3]:
        _, res = passes[pid]["A"]
        print(f"  {pid}: {len(res)} samples, std={np.std(res):.6f}")

    print("\nLoading ranked_full_parameter_grid.tsv...")
    ranked = load_ranked_candidates()
    print(f"  Loaded {len(ranked)} candidates")
    print(f"  Rank-1: {ranked[0]}")

    print("\nLoading candidate_spectrum_comparison.tsv...")
    spectrum = load_candidate_spectrum()
    print(f"  Loaded {len(spectrum)} spectrum rows")

    # 1. FFT Analysis
    print("\n" + "=" * 60)
    print("1. FFT PERIODICITY ANALYSIS")
    print("=" * 60)
    fft_results, fft_cross_pass = fft_periodicity_analysis(passes)

    for pid in sorted(fft_results.keys()):
        pr = fft_results[pid]
        print(f"\n{pid}:")
        for model in ["A", "B", "C"]:
            top5 = pr[model]["top_5_frequencies_muhz"]
            print(f"  Model {model}: top-5 freqs (muHz) = {[round(f, 1) for f in top5]}")
        print(f"  Mean top peak across models: {pr['mean_top_peak_across_models_muhz']:.1f} muHz")

    print(f"\nCross-pass consistency:")
    print(f"  Total passes: {fft_cross_pass['total_passes']}")
    print(f"  Has consistent signal (>half passes): {fft_cross_pass['has_consistent_signal']}")
    print(f"  Top 10 frequencies across all passes:")
    for item in fft_cross_pass["top_10_frequencies"]:
        print(f"    {item['frequency_muhz']} muHz: {item['count']} appearances")

    # Save FFT results
    fft_output = {
        "per_pass_results": fft_results,
        "cross_pass_summary": fft_cross_pass,
    }
    fft_path = f"{OUTPUT_DIR}/fft_results.json"
    with open(fft_path, "w") as f:
        json.dump(fft_output, f, indent=2, cls=NumpyEncoder)
    print(f"\nSaved FFT results to {fft_path}")

    # 2. LOO Robustness
    print("\n" + "=" * 60)
    print("2. LEAVE-ONE-PASS-OUT ROBUSTNESS")
    print("=" * 60)
    loo_summary = loo_robustness_analysis(passes)

    print(f"\nFull data stats:")
    for model, stats in loo_summary["full_data_stats"].items():
        print(f"  Model {model}: mean={stats['mean']:.6f}, std={stats['std']:.6f}, n={stats['n_samples']}")

    print(f"\nSignificant changes (>10% relative std change): {loo_summary['num_significant_changes']}")
    for sc in loo_summary["significant_changes_over_10pct"]:
        print(f"  Leave out {sc['leave_out_pass']}, model {sc['model']}: "
              f"full_std={sc['full_std']:.6f} -> loo_std={sc['loo_std']:.6f} "
              f"(change={sc['relative_change']:+.2%})")

    print(f"\nHighest variance passes:")
    for pid in ["pass_01", "pass_09", "pass_22"]:
        if pid in loo_summary["all_pass_variances"]:
            v = loo_summary["all_pass_variances"][pid]
            print(f"  {pid}: mean_std={v['mean_std_across_models']:.6f}, "
                  f"per_model={v['std_per_model']}")

    loo_path = f"{OUTPUT_DIR}/loo_results.json"
    with open(loo_path, "w") as f:
        json.dump(loo_summary, f, indent=2, cls=NumpyEncoder)
    print(f"\nSaved LOO results to {loo_path}")

    # 3. Candidate Spectrum Consistency
    print("\n" + "=" * 60)
    print("3. CANDIDATE SPECTRUM CROSS-PASS CONSISTENCY")
    print("=" * 60)
    consistency = candidate_spectrum_consistency(passes, ranked, spectrum)

    print(f"\nRank-1 parameters: {consistency['rank1_parameters']}")
    print(f"Rank-1 in spectrum comparison: {consistency['rank1_in_spectrum']}")
    print(f"Target frequency: {consistency['target_frequency_muhz']} muHz")
    print(f"Target period: {consistency['target_period_minutes']:.1f} minutes")
    print(f"Passes that can resolve target freq: {consistency['passes_can_resolve_target']}/{consistency['total_passes']}")
    print(f"\nLimitation: {consistency['limitation_note']}")

    # Save consistency results
    cons_path = f"{OUTPUT_DIR}/consistency_results.json"
    with open(cons_path, "w") as f:
        json.dump(consistency, f, indent=2, cls=NumpyEncoder)
    print(f"\nSaved consistency results to {cons_path}")

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Number of passes analyzed: {len(passes)}")
    print(f"Consistent FFT peak found: {fft_cross_pass['has_consistent_signal']}")
    if fft_cross_pass["common_signals_above_threshold"]:
        for sig in fft_cross_pass["common_signals_above_threshold"]:
            print(f"  Common signal at {sig['frequency_muhz']} muHz ({sig['appearances']} passes)")
    else:
        print("  No single frequency appeared in >half of passes.")
        print(f"  Most common: {fft_cross_pass['top_10_frequencies'][0]['frequency_muhz']} muHz "
              f"({fft_cross_pass['top_10_frequencies'][0]['count']} appearances)")
    print(f"LOO stability holds: {loo_summary['loo_stability_holds']}")
    print(f"  Significant changes: {loo_summary['num_significant_changes']}")
    print(f"Artifacts saved to: {OUTPUT_DIR}/")
    print(f"  - fft_results.json")
    print(f"  - loo_results.json")
    print(f"  - consistency_results.json")


if __name__ == "__main__":
    main()
