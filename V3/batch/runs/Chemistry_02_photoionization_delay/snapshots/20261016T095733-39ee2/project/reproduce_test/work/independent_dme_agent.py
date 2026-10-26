#!/usr/bin/env python3
"""Independent replication of DME energy trend analysis.

Written by general-purpose sub-agent (agentId: a33d90480d78167ae)
from scratch, without reference to main-agent code.
Results saved to output/independent_dme_results.json.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import json

DATA = Path("data")
OUT = Path("/data/user/conversations/conv-57de4486-a4e8-4f3a-8e10-9e6c6a4dea85/project/reproduce_test/output")

# Load DME data
dme_df = pd.read_csv(DATA / "dipole_matrix_elements_datasets.tsv", sep="\t")

# Extract per-energy statistics
energies = sorted(dme_df['index_0'].unique())
per_energy = {}

for e in energies:
    block = dme_df[dme_df['index_0'] == e]
    channels = []
    for _, row in block.iterrows():
        l_val = float(row.get('l', row.get('index_1', 0)))
        m_val = float(row.get('m', 0))
        re_val = float(row.get('value', 0))
        # value column contains Re; Im would be in a separate dataset or interleaved
        channels.append({"channel": int(row.get('index_1', 0)), "l": l_val, "m": m_val, "real": re_val})

    if channels:
        re_vals = [ch["real"] for ch in channels]
        per_energy[float(e)] = {
            "max_abs_real": max(abs(v) for v in re_vals),
            "sum_abs_real": sum(abs(v) for v in re_vals),
            "num_channels": len(channels),
        }

# Linear regression on Re_max
energies_arr = np.array(list(per_energy.keys()))
re_max_vals = np.array([per_energy[e]["max_abs_real"] for e in energies_arr])

slope, intercept, r_value, p_value, std_err = stats.linregress(energies_arr, re_max_vals)

# Leave-one-out robustness
loo_slopes = []
for i in range(len(energies_arr)):
    mask = np.arange(len(energies_arr)) != i
    if mask.sum() >= 2:
        s, _, _, _, _ = stats.linregress(energies_arr[mask], re_max_vals[mask])
        loo_slopes.append(s)

result = {
    "analysis": "A - Dipole Matrix Element Energy Trend",
    "num_energy_levels": len(energies),
    "energy_range_eV": [float(energies_arr.min()), float(energies_arr.max())],
    "per_energy_stats": {str(e): per_energy[e] for e in per_energy},
    "linear_regression_Re_max": {
        "slope_per_eV": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_value**2),
        "p_value": float(p_value),
        "standard_error": float(std_err),
        "num_points": len(energies),
    },
    "leave_one_out_robustness": {
        "full_slope_Re_max": float(slope),
        "loo_mean_slope_Re_max": float(np.mean(loo_slopes)),
        "loo_std_slope_Re_max": float(np.std(loo_slopes)),
        "loo_min_slope_Re_max": float(min(loo_slopes)),
        "loo_max_slope_Re_max": float(max(loo_slopes)),
        "loo_slopes_Re_max": [float(s) for s in loo_slopes],
    }
}

with open(OUT / "independent_dme_results.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"DME analysis complete: slope={slope:.6f}/eV, r²={r_value**2:.4f}, p={p_value:.4f}")
print(f"LOO slopes: mean={np.mean(loo_slopes):.6f}, std={np.std(loo_slopes):.6f}")
print(f"Same-sign LOO: {sum(1 for s in loo_slopes if s < 0)}/{len(loo_slopes)}")
