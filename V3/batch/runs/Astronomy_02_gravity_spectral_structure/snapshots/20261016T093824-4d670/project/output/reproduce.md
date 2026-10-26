# Reproduction Document

## Overview

This document describes how to reproduce all analyses and results reported in `Result.md` for the task **Astronomy_02_gravity_spectral_structure** (T0: 2022-01-01).

## Prerequisites

- Python 3.8+
- pandas, numpy

No external data or software beyond the bundled dataset is required.

## Full Evidence Chain (adopted products)

The final report adopts evidence from three sources:
1. Main-side analysis: `output/analysis.py`, `output/generate_artifacts.py`
2. Sub-agent verification: `working/subagent_verification/independent_verification.py` → `verification_results.json`
3. Corrected FFT (main-side self-check after sub-agent unit error): `working/subagent_fft_loo_corrected/corrected_fft.py` → `fft_results_corrected.json`, `consistency_results_corrected.json`
4. Original LOO (sub-agent): `working/subagent_fft_loo/loo_results.json`

## Step-by-step reproduction

### Option A: Single-command reproduction

```bash
cd /data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project
python3 reproduce_full.py
```

This script:
1. Creates a fresh empty directory (`reproduce_output/`)
2. Runs `corrected_fft.py` → produces corrected FFT artifacts
3. Runs `generate_artifacts.py` → produces result_artifacts.json
4. Runs `validate_output.py output` → validates semantic delivery contract

### Option B: Manual step-by-step

```bash
cd /data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project

# Step 1: Run corrected FFT analysis
python3 working/subagent_fft_loo_corrected/corrected_fft.py

# Step 2: Generate result artifacts
python3 output/generate_artifacts.py

# Step 3: Validate semantic delivery contract
python3 validate_output.py output
```

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
7. **Corrected FFT periodicity:** Detrend residuals, compute FFT using dt in seconds for correct Hz output, convert to μHz. Check cross-pass consistency.
8. **LOO robustness:** Leave-one-pass-out recomputation of mean and standard deviation.
9. **Spectral ranking verification:** Independent re-computation of delta_IC thresholds, cross-model correlations, and mode-frequency grid analysis.

## Determinism

All computations are deterministic given the frozen dataset. No random seeds are used. Results will be identical on re-run.

## Validation

The semantic validator confirms:
- 5 registered findings (consecutive from 1)
- All findings have resolvable analysis sources and result evidence
- Reproduction mode: companion markdown + executed scripts
- Zero errors, zero warnings
