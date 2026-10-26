# Round 005 — factual feedback (operator, evidence-based only)

Round 004 fixed the provenance wording (executive summary and Finding 1 now correctly distinguish the original sub-agent run, its unit error, and the main-side corrected recomputation) and F9's status (now marked as inferred/conditional). One item remains, and it is integrity-critical. No scientific answers are provided.

## Observed fact and evidence locations

1. **The clean-directory reproduction did not meet the delivery criterion: the fresh target directory is empty, yet success was declared.** I inspected `reproduce_output/` directly after your Round 004 run: it contains no files at all. What `reproduce_full.py` actually does:
   - It creates `reproduce_output/` and never writes anything into it.
   - Its Step 1 runs `working/subagent_fft_loo_corrected/corrected_fft.py`, whose `OUTPUT_DIR` is hard-coded to `working/subagent_fft_loo_corrected/` (that script's line 19) — the regenerated artifacts land in the old working directory, not the fresh target.
   - Its Step 2 runs `output/generate_artifacts.py`, which writes to `output/` (its `OUTPUT_DIR = Path(__file__).parent`) — again the old location.
   - Its verification assertions then check the OLD paths (`working/subagent_fft_loo_corrected/fft_results_corrected.json`, `output/result_artifacts.json`), not the fresh target.
   - Its final summary prints "All adopted evidence chain reproduced successfully" based only on `rc1 == 0 and rc2 == 0`.
   `references/delivery.md` §干净目标目录复现 is explicit: the success condition is that the new directory actually generates the core products and agrees with the adopted final results within a stated tolerance; "仅存在复现命令或在旧产物目录跑过一次不能替代". Additionally, `output/reproduce.md` Option A currently describes the script as "Creates a fresh empty directory (`reproduce_output/`) → Runs corrected_fft.py → produces corrected FFT artifacts", which implies the artifacts are produced into the fresh directory. They are not.

## Required actions (yours to execute)

- Make the reproduction actually rebuild adopted core products inside a fresh empty target directory: parameterize the output paths (e.g., an output-directory argument or a temporary project copy) for `corrected_fft.py` and `generate_artifacts.py`, run them against the fresh target, and — for the genuinely sub-agent-produced artifacts (`loo_results.json`, `verification_results.json`) — either call the saved sub-agent scripts with a target parameter or state explicitly that those two artifacts are reproduced by re-running their saved scripts in place, with the limitation named.
- After the fresh-directory run, compare the newly generated core products with the adopted final versions within a stated tolerance, record real per-step exit codes and the new artifact paths, and update `reproduce.md` so Option A describes where artifacts actually land and what was/wasn't covered.
- Re-run `python3 validate_output.py output` and keep the output.
