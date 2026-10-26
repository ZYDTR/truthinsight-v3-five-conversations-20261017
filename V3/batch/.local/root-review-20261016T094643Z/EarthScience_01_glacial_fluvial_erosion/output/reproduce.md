# Reproduction Guide

## Overview

This document describes how to reproduce all results reported in `Result.md` from the raw data. All scripts are self-contained and read directly from `data/raw/`.

## Prerequisites

- Python 3.10+
- pandas, numpy, scipy, statsmodels, matplotlib

```bash
pip install pandas numpy scipy statsmodels matplotlib
```

## Step-by-step reproduction

### Step 1: Data audit (optional, for verification)

```bash
python3 output/data_audit.py
```

Produces `output/audit_results.json` with column-level statistics, distributions, and missingness audit.

### Step 2: Core analysis

```bash
python3 output/core_analysis.py
```

This script:
1. Loads `data/raw/glacial_erosion_Earth.tsv` and `data/raw/nonglacial_erosion_Earth.tsv`
2. Creates log10-transformed variables
3. Fits group-level OLS regressions by process × methodology
4. Fits pooled ANCOVA models
5. Performs process comparisons (t-test, Mann-Whitney, ANCOVA)
6. Compares model AIC/BIC across 9 specifications

Outputs: `output/regression_results.json`, `output/comparison_results.json`

### Step 3: Robustness checks

```bash
python3 output/robustness_analysis.py
```

This script:
1. Stratifies by methodology and tests mechanical coupling (Chow test)
2. Computes clustered standard errors by Reference and Locality
3. Performs outlier sensitivity analysis (winsorization, trimming)
4. Produces binned scatter plot with error bars
5. Runs Bayesian posterior grid search for power-law exponent
6. Cross-checks GloRiSe and OCTOPUS prior compilations

Outputs: `output/robustness_results.json`, `output/binned_means.png`

## Determinism

No random seeds are used. All analyses are deterministic given the input data. Re-running the scripts will produce identical outputs.

## Verification

Run the semantic validator:

```bash
python3 validate_output.py output
```

Expected: all five semantic delivery roles satisfied (authoritative report, analysis source, result evidence, reproduction trace, finding-to-evidence traceability).
