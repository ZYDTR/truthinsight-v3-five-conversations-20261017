#!/usr/bin/env python3
"""Phase 1: Explore and summarize all datasets for photoionization dynamics."""
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path("data")

# ---- Angle-Energy Observations ----
print("=" * 60)
print("ANGLE-ENERGY OBSERVATIONS")
print("=" * 60)
ae = pd.read_csv(DATA / "angle_energy_observations_datasets.tsv", sep="\t")
print(f"Shape: {ae.shape}")
print(f"Unique dataset_path: {sorted(ae['dataset_path'].unique())}")

for ds in sorted(ae['dataset_path'].unique()):
    sub = ae[ae['dataset_path'] == ds]
    print(f"\n--- {ds} ---")
    print(f"  Shape: ({sub['index_0'].nunique()} x {sub['index_1'].nunique()})")
    if sub['index_1'].nunique() > 1:
        vals = sub['value']
        print(f"  value range: [{vals.min():.6f}, {vals.max():.6f}], mean={vals.mean():.6f}, std={vals.std():.6f}")
    else:
        print(f"  Single index_1 values: {sorted(sub['index_1'].unique())[:5]}...")
        vals = sub['value']
        print(f"  value range: [{vals.min():.6f}, {vals.max():.6f}]")

# ---- Angular Coefficients ----
print("\n" + "=" * 60)
print("ANGULAR COEFFICIENTS")
print("=" * 60)
ac = pd.read_csv(DATA / "angular_coefficients_datasets.tsv", sep="\t")
print(f"Shape: {ac.shape}")
print(f"Unique dataset_path: {sorted(ac['dataset_path'].unique())}")
for ds in sorted(ac['dataset_path'].unique()):
    sub = ac[ac['dataset_path'] == ds]
    print(f"\n--- {ds} ---")
    # Pivot to see structure
    piv = sub.pivot_table(index='index_0', columns='index_1', values='value')
    print(piv.to_string(float_format=lambda x: f"{x:.6f}"))

# ---- Dipole Matrix Elements ----
print("\n" + "=" * 60)
print("DIPOLE MATRIX ELEMENTS")
print("=" * 60)
dme = pd.read_csv(DATA / "dipole_matrix_elements_datasets.tsv", sep="\t")
print(f"Shape: {dme.shape}")
exp_dmes = [d for d in dme['dataset_path'].unique() if d.startswith('experiment')]
theory_dme = [d for d in dme['dataset_path'].unique() if d.startswith('theory')]
print(f"Experiment DMEs: {exp_dmes}")
print(f"Theory DMEs: {theory_dme}")

for ds in exp_dmes:
    sub = dme[dme['dataset_path'] == ds]
    print(f"\n--- {ds} ---")
    piv = sub.pivot_table(index='index_0', columns='index_1', values='value')
    print(piv.to_string(float_format=lambda x: f"{x:.6f}"))

# Theory DME is huge; sample it
theory_sub = dme[dme['dataset_path'] == 'theory/DMEs']
print(f"\n--- theory/DMEs (sample) ---")
print(f"  Total rows: {len(theory_sub)}")
print(f"  Unique IE (a.u.): {theory_sub['index_0'].nunique()}")
print(f"  Unique T_kin (a.u.): {theory_sub['index_1'].nunique()}")
# Sample a few rows
print(theory_sub.head(20).to_string(float_format=lambda x: f"{x:.6f}"))

# ---- Phase and Delay Curves ----
print("\n" + "=" * 60)
print("PHASE AND DELAY CURVES")
print("=" * 60)
pdc = pd.read_csv(DATA / "phase_and_delay_curves_datasets.tsv", sep="\t")
print(f"Shape: {pdc.shape}")
for ds in sorted(pdc['dataset_path'].unique()):
    sub = pdc[pdc['dataset_path'] == ds]
    piv = sub.pivot_table(index='index_0', columns='index_1', values='value')
    print(f"\n--- {ds} ---")
    print(piv.to_string(float_format=lambda x: f"{x:.6f}"))
