# Reproduction Guide

## Overview

This document describes how to reproduce all results reported in `Result.md` for task Physics_04_temporal_delay_transition.

## Prerequisites

- Python 3.11+
- Packages: numpy, scipy, pandas (see `data/source_data/python_temp_criticality/requirents.txt` for full list)

## Step-by-step reproduction

### 1. Run core analysis

```bash
cd /data/user/conversations/conv-88cfef1f-21cf-450d-b4a7-746678c9cabb/project
python3 output/analysis.py
```

This produces:
- `output/evidence/finding1_V_vs_B.json` — V(B) linear and segmented fits
- `output/evidence/finding1_v_b_scatter.json` — scatter data for plotting
- `output/evidence/finding2_correlation_collapse.json` — pairwise collapse correlations
- `output/evidence/finding3_finite_size.json` — finite-size scaling parameters
- `output/evidence/finding4_real_networks.json` — real-network fit results
- `output/evidence/summary.json` — consolidated summary of all findings

### 2. Run robustness checks

```bash
python3 output/robustness.py
```

This produces:
- `output/evidence/robustness_checks.json` — LOO stability, spline collapse comparison, bootstrap CIs, alternative model fits

### 3. Verify outputs

All JSON files are self-contained and can be inspected directly. Key numeric values from the report:

| Finding | Key Value | Expected Range |
|---|---|---|
| F1: Theory Bc | 3.95 | [3.70, 4.20] |
| F1: Meanfield Bc | 3.60 | [3.40, 3.80] |
| F2: Best collapse R² | 0.999985 | > 0.999 |
| F3: Meanfield ν | 3.24 | [3.15, 3.35] |
| F3: Meanfield Bc∞ | 3.837 | [3.825, 3.849] |
| F4: Thiers13 linear R² | 0.877 | [0.85, 0.90] |

### 4. Data sources

All data is under `data/source_data/figures/`. No external data download is required. File hashes are verified against `data_manifest.json`.
