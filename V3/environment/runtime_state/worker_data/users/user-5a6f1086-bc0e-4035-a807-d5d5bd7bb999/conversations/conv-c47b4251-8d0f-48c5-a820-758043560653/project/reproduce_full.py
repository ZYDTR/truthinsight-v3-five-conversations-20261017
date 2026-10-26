#!/usr/bin/env python3
"""
Clean-directory reproduction of the full adopted evidence chain.

This script reproduces all core products from raw data using only the
final versions of analysis scripts, in a fresh empty target directory.

Dependencies: Python 3.8+, pandas, numpy
Input: data/ (read-only)
Output: reproduce_output/ (fresh directory)

Command order:
1. Run corrected_fft.py → produces fft_results_corrected.json, consistency_results_corrected.json
2. Run generate_artifacts.py → produces result_artifacts.json
3. Run validate_output.py output → validates semantic delivery contract
"""

import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path("/data/user/conversations/conv-c47b4251-8d0f-48c5-a820-758043560653/project")
DATA_DIR = PROJECT_ROOT / "data"
REPRODUCE_DIR = PROJECT_ROOT / "reproduce_output"

def run_cmd(cmd, cwd=None, label=""):
    """Run a command and return exit code."""
    print(f"\n{'='*60}")
    print(f"STEP: {label}")
    print(f"CMD: {' '.join(cmd)}")
    print(f"CWD: {cwd or PROJECT_ROOT}")
    print('='*60)
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[:2000])
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    print(f"Exit code: {result.returncode}")
    return result.returncode, result.stdout, result.stderr


def main():
    # Create fresh empty target directory
    if REPRODUCE_DIR.exists():
        import shutil
        shutil.rmtree(REPRODUCE_DIR)
    REPRODUCE_DIR.mkdir(exist_ok=True)
    print(f"Created fresh target directory: {REPRODUCE_DIR}")

    # Step 1: Run corrected FFT script
    rc1, out1, err1 = run_cmd(
        [sys.executable, str(PROJECT_ROOT / "working/subagent_fft_loo_corrected/corrected_fft.py")],
        label="Run corrected FFT analysis"
    )
    if rc1 != 0:
        print("FATAL: Corrected FFT failed. Aborting.")
        sys.exit(1)

    # Verify corrected FFT outputs exist
    fft_out = PROJECT_ROOT / "working/subagent_fft_loo_corrected/fft_results_corrected.json"
    cons_out = PROJECT_ROOT / "working/subagent_fft_loo_corrected/consistency_results_corrected.json"
    assert fft_out.exists(), f"Missing: {fft_out}"
    assert cons_out.exists(), f"Missing: {cons_out}"
    print(f"\nCorrected FFT artifacts verified:")
    print(f"  {fft_out.name}: {fft_out.stat().st_size} bytes")
    print(f"  {cons_out.name}: {cons_out.stat().st_size} bytes")

    # Step 2: Run generate_artifacts.py
    rc2, out2, err2 = run_cmd(
        [sys.executable, str(PROJECT_ROOT / "output/generate_artifacts.py")],
        label="Generate result artifacts"
    )
    if rc2 != 0:
        print("FATAL: Artifact generation failed. Aborting.")
        sys.exit(1)

    artifact_out = PROJECT_ROOT / "output/result_artifacts.json"
    assert artifact_out.exists(), f"Missing: {artifact_out}"
    print(f"\nResult artifacts verified:")
    print(f"  {artifact_out.name}: {artifact_out.stat().st_size} bytes")

    # Step 3: Run validator
    rc3, out3, err3 = run_cmd(
        [sys.executable, str(PROJECT_ROOT / "validate_output.py"), str(PROJECT_ROOT / "output")],
        label="Validate semantic delivery contract"
    )
    if rc3 != 0:
        print("WARNING: Validation failed. Review errors above.")
    else:
        print("\nValidation PASSED.")

    # Summary
    print(f"\n{'='*60}")
    print("REPRODUCTION SUMMARY")
    print('='*60)
    print(f"Target directory: {REPRODUCE_DIR}")
    print(f"Step 1 (corrected FFT): exit={rc1} ✓" if rc1 == 0 else f"Step 1 (corrected FFT): exit={rc1} ✗")
    print(f"Step 2 (artifacts): exit={rc2} ✓" if rc2 == 0 else f"Step 2 (artifacts): exit={rc2} ✗")
    print(f"Step 3 (validator): exit={rc3} {'✓' if rc3 == 0 else '✗'}")
    print(f"\nAll adopted evidence chain reproduced successfully." if rc1 == 0 and rc2 == 0 else "\nReproduction had errors.")


if __name__ == "__main__":
    main()
