#!/usr/bin/env python3
"""
Corrected FFT Periodicity Analysis for Gravity Residual Data.

Fixes unit conversion errors from original fft_loo_analysis.py:
- Original line 147: dt in minutes -> fft_freqs in cycles/minute
- Original line 161: multiplied by 1e6 (treating cycles/min as Hz)
- CORRECT: cycles/minute * (1e6 / 60) = muHz
- Also fixes period formula at original line 346

Independent re-computation from raw data files.
"""

import json
import sys
import numpy as np
from collections import defaultdict

DATA_DIR = "/data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project/data"
_DEFAULT_OUTPUT_DIR = "/data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project/working/subagent_fft_loo_corrected"

# Accept --output-dir <path> as first CLI argument for clean-directory reproduction
if len(sys.argv) > 1 and sys.argv[1] == "--output-dir" and len(sys.argv) > 2:
    OUTPUT_DIR = sys.argv[2]
else:
    OUTPUT_DIR = _DEFAULT_OUTPUT_DIR

class NumpyEncoder(json.JSONEncoder):
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


def load_pass_residual_traces():
    filepath = f"{DATA_DIR}/pass_residual_traces.tsv"
    passes = {}
    with open(filepath, "r") as f:
        header = f.readline().strip().split("\t")
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

    for pid in passes:
        for model in ["A", "B", "C"]:
            times = np.array(passes[pid][model][0])
            residuals = np.array(passes[pid][model][1])
            sort_idx = np.argsort(times)
            passes[pid][model] = (times[sort_idx], residuals[sort_idx])

    return passes


def fft_periodicity_analysis_corrected(passes):
    """
    For each pass and each model:
    - Detrend (remove linear trend via polyfit)
    - Compute FFT, find top-5 peak frequencies (excluding DC)
    - CORRECT conversion: cycles/minute * (1e6/60) = muHz
    - Cross-pass consistency check
    """
    results = {}
    all_top_peaks = []

    for pid in sorted(passes.keys()):
        pass_result = {}
        for model in ["A", "B", "C"]:
            times, residuals = passes[pid][model]
            dt_minutes = np.mean(np.diff(times))  # time step in minutes
            dt_seconds = dt_minutes * 60.0  # convert to seconds for Hz

            # Detrend
            coeffs = np.polyfit(times, residuals, 1)
            detrended = residuals - np.polyval(coeffs, times)

            # FFT - use dt in seconds to get frequencies in Hz directly
            n = len(detrended)
            fft_vals = np.fft.rfft(detrended)
            fft_freqs_hz = np.fft.rfftfreq(n, d=dt_seconds)  # frequency in Hz

            # Exclude DC component (index 0)
            fft_freqs_hz = fft_freqs_hz[1:]
            fft_mags = np.abs(fft_vals[1:])

            # Find top-5 peaks
            if len(fft_mags) >= 5:
                top_indices = np.argpartition(fft_mags, -5)[-5:]
                top_indices = top_indices[np.argsort(fft_mags[top_indices])[::-1]]
            else:
                top_indices = np.argsort(fft_mags)[::-1][:len(fft_mags)]

            top_freqs_hz = fft_freqs_hz[top_indices]
            # Convert Hz to muHz: 1 Hz = 1e6 muHz
            top_freqs_muhz = top_freqs_hz * 1e6
            top_mags = fft_mags[top_indices]

            pass_result[model] = {
                "top_5_frequencies_muhz": [float(f) for f in top_freqs_muhz],
                "top_5_magnitudes": [float(m) for m in top_mags],
                "n_samples": n,
                "dt_minutes": float(dt_minutes),
                "dt_seconds": float(dt_seconds),
                "nyquist_muhz": float(1.0 / (2.0 * dt_seconds) * 1e6),
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

    # Cross-pass consistency
    # Count both series-level (pass×model) and pass-level (unique passes) appearances
    # freq_bins_series: raw count of (pid, model) tuples at each frequency bin
    # freq_bins_passes: set of unique pass IDs that have this frequency in any model
    freq_bins_series = defaultdict(int)
    freq_bins_passes = defaultdict(set)
    for pid, model, freq in all_top_peaks:
        binned = round(freq / 10) * 10
        freq_bins_series[binned] += 1
        freq_bins_passes[binned].add(pid)

    total_passes = len(passes)
    common_signals = []
    for freq_bin, pass_set in sorted(freq_bins_passes.items(), key=lambda x: -len(x[1])):
        n_passes = len(pass_set)
        n_series = freq_bins_series[freq_bin]
        if n_passes > total_passes / 2:
            common_signals.append({
                "frequency_muhz": freq_bin,
                "appearances_pass_level": n_passes,
                "appearances_series_level": n_series,
                "passes_fraction": f"{n_passes}/{total_passes}",
                "series_fraction": f"{n_series}/{total_passes * 3}",
            })

    top_common = sorted(freq_bins_series.items(), key=lambda x: -x[1])[:10]

    cross_pass_summary = {
        "total_passes": total_passes,
        "total_top_peak_count": len(all_top_peaks),
        "common_signals_above_threshold": common_signals,
        "top_10_frequencies": [{"frequency_muhz": f, "count": c} for f, c in top_common],
        "has_consistent_signal": len(common_signals) > 0,
    }

    return results, cross_pass_summary


def candidate_spectrum_consistency_corrected(passes, ranked_candidates, spectrum_rows):
    """
    Analyze whether residual traces contain features consistent with rank-1 parameters.
    Rank-1: v_max=30, v_min=0.05, f_peak=1010 muHz, width=275 muHz
    """
    rank1 = ranked_candidates[0]

    # Check spectrum comparison for rank-1 parameter combination
    rank1_spectrum_matches = []
    for row in spectrum_rows:
        if (abs(row["peak_frequency_microhz"] - rank1["peak_frequency_microhz"]) < 1 and
            abs(row["max_velocity_cm_s"] - rank1["max_velocity_cm_s"]) < 0.01 and
            abs(row["min_velocity_cm_s"] - rank1["min_velocity_cm_s"]) < 0.01 and
            abs(row["peak_width_microhz"] - rank1["frequency_width_microhz"]) < 1):
            rank1_spectrum_matches.append(row)

    # CORRECTED period calculation:
    # target_freq_muhz = 1010
    # target_freq_Hz = 1010e-6 = 0.001010 Hz
    # target_period_seconds = 1 / 0.001010 = 990.1 seconds
    # target_period_minutes = 990.1 / 60 = 16.5 minutes
    target_freq_muhz = rank1["peak_frequency_microhz"]
    target_freq_hz = target_freq_muhz * 1e-6
    target_period_seconds = 1.0 / target_freq_hz
    target_period_minutes = target_period_seconds / 60.0

    # Check if each pass has sufficient temporal resolution
    pass_resolution_info = {}
    for pid in sorted(passes.keys()):
        times, _ = passes[pid]["A"]
        time_span_min = float(np.max(times) - np.min(times))
        time_span_seconds = time_span_min * 60.0
        n_samples = len(times)
        dt_minutes = np.mean(np.diff(times))
        dt_seconds = dt_minutes * 60.0
        nyquist_muhz = 1.0 / (2.0 * dt_seconds) * 1e6
        resolution_muhz = 1.0 / (time_span_seconds) * 1e6

        pass_resolution_info[pid] = {
            "time_span_minutes": time_span_min,
            "time_span_seconds": time_span_seconds,
            "n_samples": n_samples,
            "dt_minutes": float(dt_minutes),
            "dt_seconds": float(dt_seconds),
            "nyquist_muhz": float(nyquist_muhz),
            "frequency_resolution_muhz": float(resolution_muhz),
            "can_resolve_target_freq": nyquist_muhz > target_freq_muhz,
            "target_freq_within_window": target_freq_muhz <= nyquist_muhz and target_freq_muhz >= resolution_muhz,
        }

    resolvable_count = sum(1 for p in pass_resolution_info.values() if bool(p["can_resolve_target_freq"]))
    within_window_count = sum(1 for p in pass_resolution_info.values() if bool(p["target_freq_within_window"]))

    best_ic_rows = sorted(spectrum_rows, key=lambda x: x["information_criterion"])[:10]

    rank1_in_spectrum = False
    for row in spectrum_rows:
        if (row["peak_frequency_microhz"] == rank1["peak_frequency_microhz"] and
            row["max_velocity_cm_s"] == rank1["max_velocity_cm_s"] and
            row["min_velocity_cm_s"] == rank1["min_velocity_cm_s"]):
            rank1_in_spectrum = True
            break

    consistency_summary = {
        "rank1_parameters": rank1,
        "rank1_in_spectrum": bool(rank1_in_spectrum),
        "rank1_spectrum_matches": rank1_spectrum_matches,
        "best_10_spectrum_rows": best_ic_rows,
        "target_frequency_muhz": float(target_freq_muhz),
        "target_frequency_hz": float(target_freq_hz),
        "target_period_seconds": float(target_period_seconds),
        "target_period_minutes": float(target_period_minutes),
        "pass_resolution_info": pass_resolution_info,
        "passes_can_resolve_target": int(resolvable_count),
        "passes_with_target_in_window": int(within_window_count),
        "total_passes": len(passes),
        "limitation_note": (
            "The candidate_spectrum_comparison.tsv provides IC values computed over ALL passes combined. "
            "There is no per-pass candidate evaluation available in the data. "
            "This analysis checks whether the residual traces have sufficient temporal "
            "resolution to detect the rank-1 frequency (1010 muHz)."
        ),
    }

    return consistency_summary


def main():
    print("=" * 60)
    print("CORRECTED FFT Periodicity & LOO Robustness Analysis")
    print("=" * 60)

    # Load data
    print("\nLoading pass_residual_traces.tsv...")
    passes = load_pass_residual_traces()
    print(f"  Loaded {len(passes)} passes")

    # Load ranked candidates
    ranked_path = f"{DATA_DIR}/ranked_full_parameter_grid.tsv"
    ranked = []
    with open(ranked_path, "r") as f:
        header = f.readline().strip().split("\t")
        col_map = {h.strip(): i for i, h in enumerate(header)}
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 6:
                continue
            ranked.append({
                "candidate_rank": int(parts[col_map["candidate_rank"]]),
                "max_velocity_cm_s": float(parts[col_map["max_velocity_cm_s"]]),
                "min_velocity_cm_s": float(parts[col_map["min_velocity_cm_s"]]),
                "peak_frequency_microhz": float(parts[col_map["peak_frequency_microhz"]]),
                "frequency_width_microhz": float(parts[col_map["frequency_width_microhz"]]),
                "delta_information_criterion": float(parts[col_map["delta_information_criterion"]]),
            })

    # Load spectrum comparison
    spec_path = f"{DATA_DIR}/candidate_spectrum_comparison.tsv"
    spectrum = []
    with open(spec_path, "r") as f:
        header = f.readline().strip().split("\t")
        col_map = {h.strip(): i for i, h in enumerate(header)}
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 6:
                continue
            spectrum.append({
                "candidate_family": parts[col_map["candidate_family"]],
                "max_velocity_cm_s": float(parts[col_map["max_velocity_cm_s"]]),
                "min_velocity_cm_s": float(parts[col_map["min_velocity_cm_s"]]),
                "peak_frequency_microhz": float(parts[col_map["peak_frequency_microhz"]]),
                "peak_width_microhz": float(parts[col_map["peak_width_microhz"]]),
                "information_criterion": float(parts[col_map["information_criterion"]]),
            })

    # 1. FFT Analysis (corrected)
    print("\n" + "=" * 60)
    print("1. CORRECTED FFT PERIODICITY ANALYSIS")
    print("=" * 60)
    fft_results, fft_cross_pass = fft_periodicity_analysis_corrected(passes)

    for pid in sorted(fft_results.keys()):
        pr = fft_results[pid]
        print(f"\n{pid}:")
        for model in ["A", "B", "C"]:
            top5 = pr[model]["top_5_frequencies_muhz"]
            nyq = pr[model]["nyquist_muhz"]
            print(f"  Model {model}: top-5 freqs (muHz) = {[round(f, 1) for f in top5]}, Nyquist={nyq:.1f}")
        print(f"  Mean top peak across models: {pr['mean_top_peak_across_models_muhz']:.1f} muHz")

    print(f"\nCross-pass consistency:")
    print(f"  Total passes: {fft_cross_pass['total_passes']}")
    print(f"  Has consistent signal (>half passes): {fft_cross_pass['has_consistent_signal']}")
    print(f"  Top 10 frequencies across all passes:")
    for item in fft_cross_pass["top_10_frequencies"]:
        print(f"    {item['frequency_muhz']} muHz: {item['count']} appearances")

    # 2. Candidate Spectrum Consistency (corrected)
    print("\n" + "=" * 60)
    print("2. CANDIDATE SPECTRUM CONSISTENCY (CORRECTED)")
    print("=" * 60)
    consistency = candidate_spectrum_consistency_corrected(passes, ranked, spectrum)

    print(f"\nRank-1 parameters: {consistency['rank1_parameters']}")
    print(f"Rank-1 in spectrum comparison: {consistency['rank1_in_spectrum']}")
    print(f"Target frequency: {consistency['target_frequency_muhz']} muHz = {consistency['target_frequency_hz']} Hz")
    print(f"Target period: {consistency['target_period_seconds']:.1f} seconds = {consistency['target_period_minutes']:.1f} minutes")
    print(f"Passes that can resolve target freq: {consistency['passes_can_resolve_target']}/{consistency['total_passes']}")
    print(f"Passes with target freq within window: {consistency['passes_with_target_in_window']}/{consistency['total_passes']}")

    # Print per-pass resolution info for key passes
    for pid in ["pass_01", "pass_02", "pass_22"]:
        info = consistency["pass_resolution_info"].get(pid, {})
        print(f"  {pid}: span={info.get('time_span_minutes', 'N/A')} min, "
              f"nyquist={info.get('nyquist_muhz', 'N/A'):.1f} muHz, "
              f"can_resolve={info.get('can_resolve_target_freq', 'N/A')}, "
              f"in_window={info.get('target_freq_within_window', 'N/A')}")

    # Save corrected results
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fft_output = {
        "per_pass_results": fft_results,
        "cross_pass_summary": fft_cross_pass,
    }
    with open(f"{OUTPUT_DIR}/fft_results_corrected.json", "w") as f:
        json.dump(fft_output, f, indent=2, cls=NumpyEncoder)

    cons_output = consistency
    with open(f"{OUTPUT_DIR}/consistency_results_corrected.json", "w") as f:
        json.dump(cons_output, f, indent=2, cls=NumpyEncoder)

    print(f"\nSaved corrected FFT results to {OUTPUT_DIR}/fft_results_corrected.json")
    print(f"Saved corrected consistency results to {OUTPUT_DIR}/consistency_results_corrected.json")

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Number of passes analyzed: {len(passes)}")
    print(f"Consistent FFT peak found: {fft_cross_pass['has_consistent_signal']}")
    if fft_cross_pass["common_signals_above_threshold"]:
        for sig in fft_cross_pass["common_signals_above_threshold"]:
            frac = sig['passes_fraction']
            sfrac = sig['series_fraction']
            print(f"  Common signal at {sig['frequency_muhz']} muHz ({frac} passes, {sfrac} series)")
    else:
        print("  No single frequency appeared in >half of passes.")
        if fft_cross_pass["top_10_frequencies"]:
            print(f"  Most common: {fft_cross_pass['top_10_frequencies'][0]['frequency_muhz']} muHz "
                  f"({fft_cross_pass['top_10_frequencies'][0]['count']} appearances)")
    print(f"Target period for 1010 muHz: {consistency['target_period_minutes']:.1f} minutes")
    print(f"Passes with target freq resolvable: {consistency['passes_can_resolve_target']}/{consistency['total_passes']}")
    print(f"Passes with target freq within analysis window: {consistency['passes_with_target_in_window']}/{consistency['total_passes']}")


if __name__ == "__main__":
    main()
