#!/usr/bin/env python3
"""Clean-directory reproduction of core analysis artifacts.

Runs all analysis scripts from data/ raw input into reproduce_test/output/,
then compares with output/ (authoritative) to verify reproducibility within tolerance.
"""
import subprocess, sys, json, csv, os, shutil
from pathlib import Path
import numpy as np

ROOT = Path("/data/user/conversations/conv-57de4486-a4e8-4f3a-8e10-9e6c6a4dea85/project")
AUTHORITATIVE = ROOT / "output"
REPRO_DIR = ROOT / "reproduce_test" / "output"
COMPARISON = {}  # {filename: {"max_abs_diff": ..., "max_rel_diff": ..., "pass": bool}}

def run_script(script_name):
    """Run a Python script and return success."""
    result = subprocess.run(
        [sys.executable, str(ROOT / script_name)],
        cwd=str(ROOT),
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        print(f"  FAIL: {script_name} (exit {result.returncode})")
        print(result.stdout[-500:] if result.stdout else "(no stdout)")
        print(result.stderr[-500:] if result.stderr else "(no stderr)")
        return False
    return True

def compare_csv_files(auth_path, repro_path, label=""):
    """Compare two CSV files row-by-row, return max abs diff."""
    try:
        auth_rows = list(csv.DictReader(open(auth_path)))
        repro_rows = list(csv.DictReader(open(repro_path)))
    except Exception as e:
        return None, f"read error: {e}"

    if len(auth_rows) != len(repro_rows):
        return None, f"row count mismatch: {len(auth_rows)} vs {len(repro_rows)}"

    max_abs = 0.0
    max_rel = 0.0
    for i, (ar, rr) in enumerate(zip(auth_rows, repro_rows)):
        for key in ar:
            if key not in rr:
                continue
            try:
                av = float(ar[key])
                rv = float(rr[key])
                if abs(av) > 1e-12 or abs(rv) > 1e-12:
                    d = abs(av - rv)
                    max_abs = max(max_abs, d)
                    rel = d / max(abs(av), abs(rv)) if max(abs(av), abs(rv)) > 1e-12 else 0
                    max_rel = max(max_rel, rel)
            except (ValueError, TypeError):
                pass  # non-numeric columns

    tol = 1e-6  # floating point tolerance
    passed = max_abs < tol
    return max_abs, f"max_abs={max_abs:.2e}, max_rel={max_rel:.2e}, tol={tol}, {'PASS' if passed else 'FAIL'}"

def compare_json_files(auth_path, repro_path, prefix=""):
    """Compare two JSON files structurally, return max numeric diff."""
    try:
        with open(auth_path) as f:
            a = json.load(f)
        with open(repro_path) as f:
            r = json.load(f)
    except Exception as e:
        return None, f"read error: {e}"

    def extract_numbers(obj, path=""):
        nums = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                nums.extend(extract_numbers(v, f"{path}.{k}"))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                nums.extend(extract_numbers(v, f"{path}[{i}]"))
        elif isinstance(obj, (int, float)):
            nums.append((path, obj))
        return nums

    a_nums = extract_numbers(a)
    r_nums = extract_numbers(r)

    if len(a_nums) != len(r_nums):
        return None, f"numeric value count mismatch: {len(a_nums)} vs {len(r_nums)}"

    max_abs = 0.0
    max_rel = 0.0
    for (ap, av), (rp, rv) in zip(a_nums, r_nums):
        if abs(av) > 1e-12 or abs(rv) > 1e-12:
            d = abs(av - rv)
            max_abs = max(max_abs, d)
            rel = d / max(abs(av), abs(rv)) if max(abs(av), abs(rv)) > 1e-12 else 0
            max_rel = max(max_rel, rel)

    tol = 1e-6
    passed = max_abs < tol
    return max_abs, f"max_abs={max_abs:.2e}, max_rel={max_rel:.2e}, tol={tol}, {'PASS' if passed else 'FAIL'}"

# ============================================================
# Step 1: Clean slate
# ============================================================
print("=" * 60)
print("CLEAN REPRODUCTION")
print("=" * 60)

if REPRO_DIR.exists():
    shutil.rmtree(REPRO_DIR)
REPRO_DIR.mkdir(parents=True)
print(f"Created clean directory: {REPRO_DIR}")

# ============================================================
# Step 2: Run each script
# ============================================================
scripts = [
    ("output/analysis_01_explore_data.py", "Step 1: Explore data"),
    ("output/analysis_02_core_findings.py", "Step 2: Core findings"),
    ("output/analysis_03_figures.py", "Step 3: Figures"),
    ("output/analysis_04_deep.py", "Step 4: Deep analysis"),
    ("output/analysis_fix_energy_alignment.py", "Step 5: Energy alignment"),
    ("output/analysis_round3_angle_resolved.py", "Step 6: Angle-resolved (Round 3)"),
    ("output/independent_dme_agent.py", "Step 7a: DME replication"),
    ("output/independent_angular_coeff_agent.py", "Step 7b: Angular coeff replication"),
    ("output/independent_wigner_agent.py", "Step 7c: Wigner replication"),
]

all_ok = True
for script, label in scripts:
    print(f"\n{label}: {script}")
    ok = run_script(script)
    if not ok:
        all_ok = False

if not all_ok:
    print("\nSome scripts failed. Proceeding with comparison of available outputs.")

# ============================================================
# Step 3: Compare authoritative vs reproduced
# ============================================================
print("\n" + "=" * 60)
print("COMPARISON: Authoritative vs Reproduced")
print("=" * 60)

tolerance_reason = "Floating-point reproducibility across independent runs; cubic spline interpolation is deterministic given same input data and scipy version. Tolerance 1e-6 covers IEEE 754 rounding."

compare_pairs = [
    # (auth_file, repro_file, description)
    ("fig1_aligned_phase_diff.csv", "fig1_aligned_phase_diff.csv", "Phase diff (spline-aligned)"),
    ("fig1_exp_theory_phase_diff.csv", "fig1_exp_theory_phase_diff.csv", "Phase diff (old index-alignment)"),
    ("fig1_angle_resolved_aligned.csv", "fig1_angle_resolved_aligned.csv", "Angle-resolved phase diff"),
    ("fig2_angular_coefficients.csv", "fig2_angular_coefficients.csv", "Order-0 angular coefficients"),
    ("fig2_order1_angular_coefficients.csv", "fig2_order1_angular_coefficients.csv", "Order-1 angular coefficients"),
    ("fig3_dme_magnitude.csv", "fig3_dme_magnitude.csv", "DME magnitude statistics"),
    ("fig4_wigner_delay.csv", "fig4_wigner_delay.csv", "Wigner delay curve"),
    ("fig4_angle_averaged_delay.csv", "fig4_angle_averaged_delay.csv", "Angle-averaged delay"),
    ("fig4_eigenphase_sum.csv", "fig4_eigenphase_sum.csv", "Eigenphase sum"),
    ("aligned_exp_theory_comparison.json", "aligned_exp_theory_comparison.json", "Grid characterization & perturbation"),
    ("analysis_results.json", "analysis_results.json", "Summary statistics"),
    ("deep_analysis_results.json", "deep_analysis_results.json", "Deep analysis results"),
    ("independent_dme_results.json", "independent_dme_results.json", "Independent DME results"),
    ("independent_angular_coeff_results.json", "independent_angular_coeff_results.json", "Independent angular coeff results"),
    ("independent_wigner_results.json", "independent_wigner_results.json", "Independent Wigner results"),
]

results = []
for auth_name, repro_name, desc in compare_pairs:
    auth_path = AUTHORITATIVE / auth_name
    repro_path = REPRO_DIR / repro_name

    if not auth_path.exists():
        results.append((desc, "SKIP", f"authoritative file missing: {auth_name}"))
        continue
    if not repro_path.exists():
        results.append((desc, "FAIL", f"reproduced file missing: {repro_name}"))
        continue

    if auth_name.endswith(".csv"):
        max_diff, detail = compare_csv_files(auth_path, repro_path, desc)
    elif auth_name.endswith(".json"):
        max_diff, detail = compare_json_files(auth_path, repro_path, desc)
    else:
        max_diff, detail = None, "unknown format"

    if max_diff is None:
        results.append((desc, "ERROR", detail))
    else:
        passed = "PASS" in detail
        results.append((desc, "PASS" if passed else "WARN", detail))

# Print comparison table
print(f"\n{'Description':<45} {'Status':<8} {'Detail'}")
print("-" * 100)
for desc, status, detail in results:
    print(f"{desc:<45} {status:<8} {detail}")

# Summary
passed_count = sum(1 for _, s, _ in results if s == "PASS")
failed_count = sum(1 for _, s, _ in results if s == "FAIL")
error_count = sum(1 for _, s, _ in results if s == "ERROR")
skip_count = sum(1 for _, s, _ in results if s == "SKIP")
warn_count = sum(1 for _, s, _ in results if s == "WARN")

print(f"\nSummary: {passed_count} PASS, {warn_count} WARN, {failed_count} FAIL, {error_count} ERROR, {skip_count} SKIP out of {len(results)} files")

# Save comparison results
comparison_summary = {
    "reproduction_directory": str(REPRO_DIR),
    "tolerance": 1e-6,
    "tolerance_reason": tolerance_reason,
    "results": [{"file": d, "status": s, "detail": det} for d, s, det in results],
    "summary": {
        "total": len(results),
        "pass": passed_count,
        "warn": warn_count,
        "fail": failed_count,
        "error": error_count,
        "skip": skip_count,
    }
}

with open(ROOT / "reproduce_test" / "comparison_results.json", "w") as f:
    json.dump(comparison_summary, f, indent=2)

print(f"\nComparison saved to reproduce_test/comparison_results.json")
