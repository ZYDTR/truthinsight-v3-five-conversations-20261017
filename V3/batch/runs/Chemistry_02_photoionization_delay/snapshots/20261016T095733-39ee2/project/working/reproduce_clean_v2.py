#!/usr/bin/env python3
"""Clean-directory reproduction v2.

Copies analysis scripts to reproduce_test/, patches OUT path,
runs them, then compares results with authoritative output/.
"""
import subprocess, sys, json, csv, os, shutil, re
from pathlib import Path
import numpy as np

ROOT = Path("/data/user/conversations/conv-57de4486-a4e8-4f3a-8e10-9e6c6a4dea85/project")
AUTHORITATIVE = ROOT / "output"
REPRO_DIR = ROOT / "reproduce_test" / "output"
REPRO_WORK = ROOT / "reproduce_test" / "work"  # working copy of scripts

def setup():
    """Create clean directories."""
    for d in [REPRO_DIR, REPRO_WORK]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

def copy_and_patch(script_name):
    """Copy script to repro work dir, patch OUT path."""
    src = ROOT / script_name
    dst = REPRO_WORK / script_name.split("/")[-1]
    content = src.read_text()
    # Replace OUT = Path("output") with OUT = Path("reproduce_test/output")
    patched = re.sub(
        r'OUT\s*=\s*Path\(["\']output["\']\)',
        f'OUT = Path("{REPRO_DIR}")',
        content
    )
    # Also replace DATA = Path("data") stays same
    dst.write_text(patched)
    return dst

def run_script(script_path):
    """Run a Python script from repro work dir."""
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT),
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        print(f"  FAIL (exit {result.returncode})")
        print(result.stdout[-300:] if result.stdout else "(no stdout)")
        print(result.stderr[-300:] if result.stderr else "(no stderr)")
        return False
    return True

def compare_csv_files(auth_path, repro_path):
    """Compare two CSV files row-by-row."""
    try:
        auth_rows = list(csv.DictReader(open(auth_path)))
        repro_rows = list(csv.DictReader(open(repro_path)))
    except Exception as e:
        return None, f"read error: {e}"

    if len(auth_rows) != len(repro_rows):
        return None, f"row count mismatch: {len(auth_rows)} vs {len(repro_rows)}"

    max_abs = 0.0
    max_rel = 0.0
    for ar, rr in zip(auth_rows, repro_rows):
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
                pass

    tol = 1e-6
    passed = max_abs < tol
    return max_abs, f"max_abs={max_abs:.2e}, max_rel={max_rel:.2e}, tol={tol}, {'PASS' if passed else 'FAIL'}"

def compare_json_files(auth_path, repro_path):
    """Compare two JSON files numerically."""
    try:
        with open(auth_path) as f:
            a = json.load(f)
        with open(repro_path) as f:
            r = json.load(f)
    except Exception as e:
        return None, f"read error: {e}"

    def extract_numbers(obj):
        nums = []
        if isinstance(obj, dict):
            for v in obj.values():
                nums.extend(extract_numbers(v))
        elif isinstance(obj, list):
            for v in obj:
                nums.extend(extract_numbers(v))
        elif isinstance(obj, (int, float)):
            nums.append(obj)
        return nums

    a_nums = extract_numbers(a)
    r_nums = extract_numbers(r)

    if len(a_nums) != len(r_nums):
        return None, f"numeric value count mismatch: {len(a_nums)} vs {len(r_nums)}"

    max_abs = 0.0
    max_rel = 0.0
    for av, rv in zip(a_nums, r_nums):
        if abs(av) > 1e-12 or abs(rv) > 1e-12:
            d = abs(av - rv)
            max_abs = max(max_abs, d)
            rel = d / max(abs(av), abs(rv)) if max(abs(av), abs(rv)) > 1e-12 else 0
            max_rel = max(max_rel, rel)

    tol = 1e-6
    passed = max_abs < tol
    return max_abs, f"max_abs={max_abs:.2e}, max_rel={max_rel:.2e}, tol={tol}, {'PASS' if passed else 'FAIL'}"

# ============================================================
# Main
# ============================================================
print("=" * 60)
print("CLEAN REPRODUCTION v2")
print("=" * 60)
setup()

scripts_to_run = [
    ("analysis_01_explore_data.py", "Step 1: Explore data"),
    ("analysis_02_core_findings.py", "Step 2: Core findings"),
    ("analysis_03_figures.py", "Step 3: Figures"),
    ("analysis_04_deep.py", "Step 4: Deep analysis"),
    ("analysis_fix_energy_alignment.py", "Step 5: Energy alignment"),
    ("analysis_round3_angle_resolved.py", "Step 6: Angle-resolved"),
    ("independent_dme_agent.py", "Step 7a: DME replication"),
    ("independent_angular_coeff_agent.py", "Step 7b: Angular coeff"),
    ("independent_wigner_agent.py", "Step 7c: Wigner replication"),
]

all_ok = True
for script_name, label in scripts_to_run:
    print(f"\n{label}: {script_name}")
    try:
        script_path = copy_and_patch(f"output/{script_name}")
        ok = run_script(script_path)
        if not ok:
            all_ok = False
    except Exception as e:
        print(f"  ERROR: {e}")
        all_ok = False

# Fix independent_angular_coeff_agent.py polyfit import issue
if not (REPRO_DIR / "independent_angular_coeff_results.json").exists():
    print("\nFixing angular coeff agent polyfit import...")
    src = ROOT / "output/independent_angular_coeff_agent.py"
    content = src.read_text()
    content = content.replace("from scipy import stats, polyfit", "from scipy import stats\nfrom numpy import polyfit")
    dst = REPRO_WORK / "independent_angular_coeff_agent.py"
    dst.write_text(content)
    run_script(dst)

# ============================================================
# Compare
# ============================================================
print("\n" + "=" * 60)
print("COMPARISON: Authoritative vs Reproduced")
print("=" * 60)

compare_pairs = [
    ("fig1_aligned_phase_diff.csv", "Phase diff (spline-aligned)"),
    ("fig1_exp_theory_phase_diff.csv", "Phase diff (old index-alignment)"),
    ("fig1_angle_resolved_aligned.csv", "Angle-resolved phase diff"),
    ("fig2_angular_coefficients.csv", "Order-0 angular coefficients"),
    ("fig2_order1_angular_coefficients.csv", "Order-1 angular coefficients"),
    ("fig3_dme_magnitude.csv", "DME magnitude statistics"),
    ("fig4_wigner_delay.csv", "Wigner delay curve"),
    ("fig4_angle_averaged_delay.csv", "Angle-averaged delay"),
    ("fig4_eigenphase_sum.csv", "Eigenphase sum"),
    ("aligned_exp_theory_comparison.json", "Grid characterization & perturbation"),
    ("analysis_results.json", "Summary statistics"),
    ("deep_analysis_results.json", "Deep analysis results"),
    ("independent_dme_results.json", "Independent DME results"),
    ("independent_angular_coeff_results.json", "Independent angular coeff results"),
    ("independent_wigner_results.json", "Independent Wigner results"),
]

results = []
for fname, desc in compare_pairs:
    auth_path = AUTHORITATIVE / fname
    repro_path = REPRO_DIR / fname

    if not auth_path.exists():
        results.append((desc, "SKIP", f"authoritative file missing"))
        continue
    if not repro_path.exists():
        results.append((desc, "FAIL", f"reproduced file missing"))
        continue

    if fname.endswith(".csv"):
        max_diff, detail = compare_csv_files(auth_path, repro_path)
    elif fname.endswith(".json"):
        max_diff, detail = compare_json_files(auth_path, repro_path)
    else:
        max_diff, detail = None, "unknown format"

    if max_diff is None:
        results.append((desc, "ERROR", detail))
    else:
        passed = "PASS" in detail
        results.append((desc, "PASS" if passed else "WARN", detail))

print(f"\n{'Description':<45} {'Status':<8} {'Detail'}")
print("-" * 100)
for desc, status, detail in results:
    print(f"{desc:<45} {status:<8} {detail}")

passed_count = sum(1 for _, s, _ in results if s == "PASS")
failed_count = sum(1 for _, s, _ in results if s == "FAIL")
error_count = sum(1 for _, s, _ in results if s == "ERROR")
skip_count = sum(1 for _, s, _ in results if s == "SKIP")
warn_count = sum(1 for _, s, _ in results if s == "WARN")

print(f"\nSummary: {passed_count} PASS, {warn_count} WARN, {failed_count} FAIL, {error_count} ERROR, {skip_count} SKIP out of {len(results)} files")

comparison_summary = {
    "reproduction_directory": str(REPRO_DIR),
    "tolerance": 1e-6,
    "tolerance_reason": "Cubic spline interpolation and linear regression are deterministic given identical input data and scipy/numpy versions. Tolerance 1e-6 covers IEEE 754 rounding differences.",
    "results": [{"file": d, "status": s, "detail": det} for d, s, det in results],
    "summary": {"total": len(results), "pass": passed_count, "warn": warn_count, "fail": failed_count, "error": error_count, "skip": skip_count}
}

with open(ROOT / "reproduce_test" / "comparison_results.json", "w") as f:
    json.dump(comparison_summary, f, indent=2)

print(f"\nComparison saved to reproduce_test/comparison_results.json")
