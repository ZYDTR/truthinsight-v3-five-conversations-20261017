# Reproduction Document

## Overview

This document describes how to reproduce all analyses and results reported in `Result.md` for the task **Astronomy_02_gravity_spectral_structure** (T0: 2022-01-01).

## Prerequisites

- Python 3.8+
- pandas, numpy

No external data or software beyond the bundled dataset is required.

## Step-by-step reproduction

### 1. Run the main analysis pipeline

```bash
cd output
python3 analysis.py
```

This produces:
- Console output with per-pass statistics, autocorrelation values, variance decomposition, candidate spectrum analysis, uniform alternative comparison, and summary statistics
- `output/analysis_results.json` — full numerical results

### 2. Generate machine-readable result artifacts

```bash
cd output
python3 generate_artifacts.py
```

This produces:
- `output/result_artifacts.json` — structured JSON with all key findings, per-pass statistics, cross-model correlations, spectral analysis results, and mode-frequency summaries

### 3. Verify semantic delivery contract

```bash
python3 validate_output.py output
```

Expected: validation passes with 5 registered findings, traceable to analysis sources and result artifacts.

## Data files used (read-only)

All data files are under `data/`:
- `pass_residual_traces.tsv` — 1,698 rows, 22 passes × ~77 time samples
- `candidate_spectrum_comparison.tsv` — 507 rows, two scan families
- `ranked_full_parameter_grid.tsv` — 250 ranked candidates
- `mode_frequency_grid.tsv` — 52 mode entries
- `uniform_alternative_comparison.tsv` — 24 uniform alternatives

## Key analytical steps

1. **Per-pass statistics:** For each of 22 passes and 3 models, compute mean, std, skewness, kurtosis, min, max, median, lag-1 autocorrelation, and FFT peak frequency.

2. **Variance decomposition:** Compute total, between-pass, and within-pass variance for each model. Between-pass fraction = between_pass_variance / total_variance.

3. **Cross-model correlation:** For each pass, compute Pearson r between each pair of models (A-B, A-C, B-C).

4. **Candidate spectrum analysis:** Find global minimum IC, best IC per velocity setting, count candidates within delta_IC thresholds.

5. **Ranked grid analysis:** Examine top 10 candidates, compute delta_IC gaps between consecutive ranks.

6. **Uniform alternative comparison:** Find minimum IC in uniform curve, compare against best structured candidate.

7. **Robustness:** Leave-one-pass-out recomputation; first-half vs. second-half consistency within each pass.

## Determinism

All computations are deterministic given the frozen dataset. No random seeds are used. Results will be identical on re-run.
