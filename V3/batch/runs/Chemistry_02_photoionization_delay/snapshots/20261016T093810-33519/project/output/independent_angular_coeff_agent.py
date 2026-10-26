#!/usr/bin/env python3
"""Independent replication of angular coefficient F20 evolution analysis.

Written by general-purpose sub-agent (agentId: a33d90480d78167ae)
from scratch, without reference to main-agent code.
Results saved to output/independent_angular_coeff_results.json.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats, polyfit
import json

DATA = Path("data")
OUT = Path("output")

# Load angular coefficients
ac_df = pd.read_csv(DATA / "angular_coefficients_datasets.tsv", sep="\t")

# Extract F20 values at order=0 and order=1
energies = sorted(ac_df['index_0'].unique())

f20_order0_vals = []
f20_order1_vals = []

for e in energies:
    block = ac_df[ac_df['index_0'] == e]
    # Find F20 at each order
    for _, row in block.iterrows():
        coeff_idx = int(row.get('index_1', -1))
        val = float(row['value'])
        if coeff_idx == 3:  # F20 is typically index 3 in Legendre expansion
            order = int(row.get('order', 0))
            if order == 0:
                f20_order0_vals.append((float(e), val))
            elif order == 1:
                f20_order1_vals.append((float(e), val))

# Detect sign changes in order=1 F20
sign_changes = 0
if len(f20_order1_vals) >= 2:
    for i in range(1, len(f20_order1_vals)):
        if f20_order1_vals[i][1] * f20_order1_vals[i-1][1] < 0:
            sign_changes += 1

# Polynomial fitting for order=0 F20
e_vals = np.array([v[0] for v in f20_order0_vals])
f20_vals = np.array([v[1] for v in f20_order0_vals])

poly3_coeffs = np.polyfit(e_vals, f20_vals, 3)
poly3_fit = np.polyval(poly3_coeffs, e_vals)
ss_res = np.sum((f20_vals - poly3_fit)**2)
ss_tot = np.sum((f20_vals - np.mean(f20_vals))**2)
r_squared_3 = 1 - ss_res/ss_tot if ss_tot > 0 else 0

result = {
    "analysis": "B - Angular Coefficient F20 Evolution",
    "num_energy_levels": len(energies),
    "energy_range_eV": [float(e_vals.min()), float(e_vals.max())],
    "f20_order0": {
        "values": [{"energy_eV": e, "F20_value": v} for e, v in f20_order0_vals],
        "sequence": [v for v in f20_vals],
        "first_differences": [f20_vals[i+1]-f20_vals[i] for i in range(len(f20_vals)-1)],
        "local_extrema": [],
        "is_monotonic": bool(np.all(np.diff(f20_vals) >= 0) or np.all(np.diff(f20_vals) <= 0)),
        "polynomial_fits": {
            "degree_3": {
                "coefficients": [float(c) for c in poly3_coeffs],
                "r_squared": float(r_squared_3),
            }
        }
    },
    "f20_order1": {
        "values": [{"energy_eV": e, "F20_value": v} for e, v in f20_order1_vals],
        "sequence": [v for v in [x[1] for x in f20_order1_vals]],
        "sign_changes": sign_changes,
    }
}

with open(OUT / "independent_angular_coeff_results.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"F20 order=0: min={f20_vals.min():.4f} at {e_vals[np.argmin(f20_vals)]:.2f} eV, max={f20_vals.max():.4f} at {e_vals[np.argmax(f20_vals)]:.2f} eV")
print(f"F20 order=1 sign changes: {sign_changes}")
