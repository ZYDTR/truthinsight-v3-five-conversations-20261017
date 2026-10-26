#!/usr/bin/env python3
"""Round 3 correction: Angle-resolved phase diff on spline-aligned grids.

Replaces stale angle-resolved numbers from index-based alignment.
Produces output/fig1_angle_resolved_aligned.csv and updates deep_analysis_results.json.
"""
import pandas as pd
import numpy as np
from scipy import interpolate
import json
from pathlib import Path

DATA = Path("data")
OUT = Path("output")

ae = pd.read_csv(DATA / "angle_energy_observations_datasets.tsv", sep="\t")

# Extract grids
exp_eV_df = ae[ae['dataset_path'] == 'experiment/photon_energy_eV'].sort_values('index_0')
theory_eV_df = ae[ae['dataset_path'] == 'theory/photon_energy_eV'].sort_values('index_0')
exp_E = exp_eV_df['value'].values
th_E = theory_eV_df['value'].values

# Build phase DataFrames
exp_phases = ae[ae['dataset_path'] == 'experiment/phase'].pivot(index='index_0', columns='index_1', values='value')
theory_phases = ae[ae['dataset_path'] == 'theory/phase'].pivot(index='index_0', columns='index_1', values='value')

def interp_grid(source_E, source_df, target_E):
    n_tgt = len(target_E)
    result = np.zeros((n_tgt, source_df.shape[1]))
    for j, ang in enumerate(source_df.columns):
        y_vals = source_df.loc[:, ang].values
        src_e = source_E[:len(y_vals)] if len(y_vals) != len(source_E) else source_E
        cs = interpolate.CubicSpline(src_e, y_vals)
        result[:, j] = cs(target_E)
    return result

exp_phase_interp = interp_grid(exp_E, exp_phases, th_E)
min_rows = min(exp_phase_interp.shape[0], theory_phases.shape[0])

angles = sorted(exp_phases.columns)

# Angle-resolved by energy region using spline-aligned grids
results = {}
csv_lines = ["energy_region,angle_deg,mean_diff_rad,n_points"]

for label, mask in [("low_<28eV", th_E < 28), ("mid_28-35eV", (th_E >= 28) & (th_E < 35)), ("high_>=35eV", th_E >= 35)]:
    idxs = np.where(mask)[0]
    if len(idxs) == 0:
        continue

    diffs_by_angle = {}
    for i in idxs:
        d = np.abs(exp_phase_interp[i, :min_rows] - theory_phases.values[i, :min_rows])
        n_cols = min(len(d), len(angles))
        for j in range(n_cols):
            diffs_by_angle.setdefault(angles[j], []).append(d[j])

    avg_diff = {ang: float(np.mean(vals)) for ang, vals in diffs_by_angle.items()}
    results[label] = avg_diff

    for ang, val in avg_diff.items():
        csv_lines.append(f"{label},{ang},{val:.6f},{len(diffs_by_angle[ang])}")

with open(OUT / "fig1_angle_resolved_aligned.csv", "w") as f:
    f.write("\n".join(csv_lines) + "\n")

with open(OUT / "deep_analysis_results.json", "r") as f:
    deep = json.load(f)
deep["angle_resolved_phase_diff_spline_aligned"] = results
with open(OUT / "deep_analysis_results.json", "w") as f:
    json.dump(deep, f, indent=2)

print("Angle-resolved (spline-aligned) saved to output/fig1_angle_resolved_aligned.csv")
print(json.dumps(results, indent=2))
