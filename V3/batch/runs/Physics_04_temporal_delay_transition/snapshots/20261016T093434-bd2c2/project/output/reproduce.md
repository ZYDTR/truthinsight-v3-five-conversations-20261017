# Reproduction Guide

## Overview

This document describes how to reproduce all results reported in `Result.md` for task Physics_04_temporal_delay_transition.

## Prerequisites

- Python 3.11+
- Packages: numpy, scipy, pandas (see `data/source_data/python_temp_criticality/requirents.txt` for full list)

## Step-by-step reproduction

### 1. Prepare working directory

```bash
cd /data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project
mkdir -p /tmp/repro_clean/output/evidence
cp output/analysis.py /tmp/repro_clean/
cp output/robustness.py /tmp/repro_clean/
cp -r data /tmp/repro_clean/data
cd /tmp/repro_clean
```

### 2. Run core analysis

```bash
python3 analysis.py
```

This produces:
- `output/evidence/finding1_V_vs_B.json` — V(B) linear and segmented fits
- `output/evidence/finding1_v_b_scatter.json` — scatter data for plotting
- `output/evidence/finding2_correlation_collapse.json` — pairwise collapse correlations
- `output/evidence/finding3_finite_size.json` — finite-size scaling parameters
- `output/evidence/finding4_real_networks.json` — real-network fit results
- `output/evidence/summary.json` — consolidated summary of all findings

### 3. Run robustness checks

```bash
python3 robustness.py
```

This produces:
- `output/evidence/robustness_checks.json` — LOO stability, spline collapse comparison, bootstrap CIs, alternative model fits

### 4. Verify outputs

All JSON files are self-contained and can be inspected directly. Key numeric values from the report:

| Finding | Key Value | Expected Range |
|---|---|---|
| F1: Theory Bc | 3.95 | [3.90, 4.00] |
| F1: Meanfield Bc | 3.60 | [3.50, 3.65] |
| F2: Pairs with R² > 0.999 | 7 of 10 | 7–8 of 10 |
| F3: Meanfield ν | 3.24 | [3.15, 3.35] |
| F3: Meanfield Bc∞ | 3.837 | [3.825, 3.849] |
| F4: Thiers13 linear R² | 0.877 | [0.85, 0.90] |

### 5. Clean-directory verification

A clean-directory reproduction was executed on 2026-10-16 at `/tmp/repro_clean/`. All 7 JSON artifacts were produced and verified identical to the originals (SHA-256 match confirmed). The reproduction evidence is retained at `/tmp/repro_clean/output/evidence/`.

### Data sources

All data is under `data/source_data/figures/`. No external data download is required. File hashes are verified against `data_manifest.json`.
