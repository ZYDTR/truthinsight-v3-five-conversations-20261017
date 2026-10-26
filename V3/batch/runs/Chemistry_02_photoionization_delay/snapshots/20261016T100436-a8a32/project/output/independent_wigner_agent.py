#!/usr/bin/env python3
"""Independent replication of Wigner delay feature analysis.

Written by general-purpose sub-agent (agentId: a33d90480d78167ae)
from scratch, without reference to main-agent code.
Results saved to output/independent_wigner_results.json.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import json

DATA = Path("data")
OUT = Path("output")

# Load phase and delay curves
pdc_df = pd.read_csv(DATA / "phase_and_delay_curves_datasets.tsv", sep="\t")

result = {"analysis": "C - Wigner Delay Features", "available_curves": []}

for curve_name in ["0.5_Wigner_delay", "angle_averaged_delay", "eigenphase_sum"]:
    curve_data = pdc_df[pdc_df['dataset_path'] == curve_name].sort_values('index_0')
    if curve_data.empty:
        continue

    result["available_curves"].append(curve_name)

    energies = curve_data['index_0'].values.astype(float)
    values = curve_data['value'].values.astype(float)

    n_points = len(energies)
    min_idx = np.argmin(values)
    max_idx = np.argmax(values)

    # Zero crossings
    zero_crossings = []
    for i in range(1, len(values)):
        if values[i] * values[i-1] < 0:
            # Linear interpolation for crossing point
            frac = abs(values[i-1]) / (abs(values[i-1]) + abs(values[i]))
            zc_energy = energies[i-1] + frac * (energies[i] - energies[i-1])
            zero_crossings.append(float(zc_energy))

    # First derivative sign changes
    first_deriv = np.diff(values) / np.diff(energies)
    deriv_sign_changes = []
    for i in range(1, len(first_deriv)):
        if first_deriv[i] * first_deriv[i-1] < 0:
            deriv_sign_changes.append({
                "index": int(i),
                "energy_eV": float(energies[i]),
                "prev_deriv": float(first_deriv[i-1]),
                "curr_deriv": float(first_deriv[i]),
            })

    curve_result = {
        "curve": curve_name,
        "n_points": int(n_points),
        "energy_range_eV": [float(energies.min()), float(energies.max())],
        "min_value": float(values[min_idx]),
        "min_energy_eV": float(energies[min_idx]),
        "max_value": float(values[max_idx]),
        "max_energy_eV": float(energies[max_idx]),
        "zero_crossings_eV": zero_crossings,
        "derivative_sign_changes": deriv_sign_changes,
    }

    result[curve_name.replace(".", "_")] = curve_result

with open(OUT / "independent_wigner_results.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"Wigner analysis complete for {len(result['available_curves'])} curves")
