# Comparison V2 → V3 — Astronomy_02_gravity_spectral_structure

**Conclusion first.** V3 ended with a more verifiable final delivery than V2 on this task, but the improvement cannot be attributed to the revised Skill alone. V3's first autonomous round was structurally WORSE than V2's (zero native delegations vs two, shared Skill unread), and V3 needed 8 science rounds + 7 operator interventions to converge vs V2's 4 rounds + 3 interventions. V3's final state is strictly stronger on reproducibility (executed, hash-verified clean-directory reproduction vs none) and on claim-to-execution traceability (every headline number re-derived and propagated to artifacts), while scientific correctness remains unjudged in both (no scoring anywhere). All "improvements" below are confounded by deeper operator source-auditing in V3 and by two SDK context compactions; single-run, five-task design supports no statistical claims.

Gate: this comparison was written only after all five V3 `sealed.json` existed (verified 10:16:44Z: Chemistry_02 sealed last). Only this task's V2 evidence was read (`run.json`, `rounds/`, `reviews/verdict.json`, environment docs); no other task's V2/V3 scientific content was opened.

## 1. Consistency factors verified (both rounds)

| Factor | V2 | V3 | Same? |
|---|---|---|---|
| Backend | main `6d529489815362eb2d6cf717e736e44936de3afc` (control/backend-freeze.json) | same sha (docs/environment-verification.json passed) | ✅ |
| Main/child model | qwen3.7-flash verified from JSONL model fields; fallback empty | same (376 assistant msgs + 2 child JSONLs all `qwen3.7-flash`; ready.json fallback "") | ✅ |
| Worker resources | 1 CPU / 4g (run-spec L37–38) | 1 CPU / 4g (run-spec) | ✅ |
| Outer operator | GLM-5.3-Flash-W4A16-MTP | same (pinned per run-spec `observed_default`) | ✅ |
| Operators layout | 5 independent leaf operators, one conversation each | same | ✅ |
| Probe protocol | no separate probe conversation; child model from first real delegation | same | ✅ |
| First science message | original LaunchPrompt verbatim (sha 0f4caf…) | byte-identical (same sha) | ✅ |
| SDK/CLI | contract-pinned 0.2.154 / 2.1.274; V2 env-verification used a different schema (filelock 3.20.0, worker_import, prompt_exact) and did not restate SDK/CLI versions | V3 env-verification: SDK 0.2.154, CLI 2.1.274, `dependency_versions_identical: true` against V2 pins | ✅ attested by V3 verification; V2-side values not directly re-observed (noted as such) |
| **Subject Skill** | **scientific-evidence 2.0.0** (SKILL.md fa4b0f88…) | **3.1.0** (SKILL.md 6264b74f…) | ❌ — the experimental variable |

## 2. Dimension-by-dimension comparison

1. **First substantive delegation vs first main implementation** — V2: round 1 had 2 autonomous general-purpose delegations, but only AFTER main wrote and ran a monolithic analysis.py single-handed (~7 min, 13 tool events, 2 failed runs); core Findings 1–5 computation was never delegated. V3: round 1 had ZERO delegations — main wrote analysis.py, generated artifacts, and wrote the full report solo. **Unchanged in kind (both violate "delegate before main pipeline"), worse in degree in V3's first round; V2 at least produced autonomous delegations within round 1.**
2. **Assigned analytic scope vs late verification only** — V2: round-1 children did verification + additional analysis; round-4's PSD/competing-explanations/delta-IC children were operator-prompted (feedback-004). V3: children carried a core-supporting analysis branch (FFT periodicity + LOO robustness) and a blind independent verification — but only after operator feedback in round 002. **Improved in scope (core-supporting branch delegated), not attributable to Skill alone (intervention-required in both).**
3. **Child actual execution vs main duplicate analysis** — V2: children executed (24/20/30/23 tool_use in child JSONLs). V3: children executed (45/29 assistant msgs with own-code writes and runs). V3 main partially duplicated the child branch by writing `corrected_fft.py` itself after the child's 60× unit error — honestly labeled self-check in analysis-state and report. **Comparable child execution; V3 adds an attribution-clean self-check episode caused by child defects.**
4. **Reported single-request input tokens (main/child)** — 缺测 in both (V2 verdict: not reported; V3 audit has only dedup usage sums: input 15,269,964 / output 104,415 tokens across the conversation — not single-request). **Unchanged (both missing).**
5. **Analysis-state vs evidence; adopted results; report anchors; revision invalidation** — V3: `working/analysis-state.md` maintained through r8 with confirmed-facts table (F1–F13), executor/task ledger, adoption states, and an affected-evidence ledger (items 4–12) driving propagation; stale rows were themselves caught and fixed (item 11). V2: verdict records artifact-naming/reference gaps and a file rewrite (`rm leave_one_pass_out.csv && mv …`) in round 3. **Improved in V3 (ledger-driven revision), operator-audit-assisted.**
6. **Claim vs executed analysis definition and units** — V2: pass_01 lag-1 autocorrelation reported-vs-computed discrepancy (0.52 vs 0.178) reconciled with children. V3: IC mis-join across files (43.9 attached to a nonexistent row), cycles/min→μHz 60× error, 3600× period error, pass-vs-series counting unit (17/22 → 13/22 passes = 17/66) — each caught by operator audit of current source, each fixed with JSON/artifact/report/state propagation, and finally re-derived by the subject itself (round-007 subject note: corrected counts match operator recount). **Both rounds had unit/definition defects; V3 had more, all fixed with full propagation; not a quality score.**
7. **Method objections / counterevidence change headline claims** — V3: corrected FFT overturned the "no consistent signal" null twice-removed (headline: "Indicated … Not Confirmed" → "Supported by Both", strength weakened to "slight majority" at 59%); Finding 4 headline ratio framing → conditional IC-difference. V2: Competing Explanations section added; PSD integrated into Finding 3. **Improved in V3 (headline actually changed with evidence), audit-assisted.**
8. **Valid model comparison + complete clean-target reproduction** — V2: **clean-directory reproduction NOT executed** (explicit remaining issue). V3: executed via `reproduce_clean.py` (fresh `reproduce_output/`, `--output-dir` parameterization, adopted-hash capture before regeneration, final all-match; operator independently re-verified SHA-256 c85bf408…/1aec316b…). Scope limit honestly disclosed: standalone sub-agent artifacts (`loo_results.json`, `verification_results.json`) are NOT rebuilt — embedded copies are read from adopted old files; partial-chain verified, not full-chain. **Improved (executed + verified > absent), with named limit.**
9. **Public criteria / validator** — same public contract bytes both rounds; validator failures: V2 ×1 (recovered same round), V3 ×4 (recovered each time; one reproduction MISMATCH self-diagnosed by subject). Format-only scope in both. **Unchanged.**
10. **Feedback rounds / categories** — V2: 3 (artifact internal consistency + integration; protocol actual-read gap; delegation pattern + PSD + unused modules). V3: 7 (no-delegation + Skill-unread + late state + IC mis-join + counts/trend + unsaved robustness/FFT + IC-ratio framing; FFT 60× + period 3600× + child-source-unread; provenance + reproduction-integrity + F9; empty-reproduce_output; silent artifact reversion; pass/series unit [operator-proactive]; IC comparability basis). **More interventions in V3; partly reflects deeper operator auditing this round (source-level vs artifact-level), a confounder.**
11. **Tool faults & recovery** — V2: 2 failed analysis runs, 4 edit errors, 1 validator failure, ~19 min WAITING_FOR_SLOT. V3: 2 analysis NameErrors, 3 SendMessage empty-message errors, 1 blocked sleep, 4 validator failures, 1 reproduction MISMATCH, 2 SDK compactions; all recovered, all preserved (17 tool errors in final audit). **Comparable recovery discipline; more fault volume in V3.**

## 3. Separately stated intervention history (attribution limits)

- **V2 mid-run operator interventions**: feedback-002 (internal consistency), feedback-003 (protocol actual-read), feedback-004 — the latter introduced the bounded-division delegation requirement as an explicit operator intervention; V2's round-4 delegations were operator-prompted and its verdict says so.
- **V3 interventions**: rounds 002–008 factual feedbacks; round-007's pass/series recount was operator-proactive (independently written before root's reminder; root follow-up recorded this attribution). V3's operator also performed source-level audits (reading current `corrected_fft.py`, `reproduce_full.py`, JSON artifacts) — a deeper audit behavior than V2's, which changes what defects become visible.
- **Two-round feedback differences**: V3's 7 vs V2's 3 interventions mean V3 had more opportunities for correction; convergence-depth comparisons are confounded and cannot be scored.
- **Randomness/limitation**: single run per task, one shared backend instance per round, five independent outer operators; queue waits varied (V2 ~19 min vs V3 minutes). No significance claims; changes cannot be attributed solely to the Skill revision.

## 4. Improvements / unchanged / regressed / undeterminable

- **Improved (evidence-backed, audit-assisted)**: executed+verified clean-directory reproduction (vs none); ledger-driven revision propagation; headline claims actually revised with corrected computations; conditional-baseline discipline (F9/F13); child-branch scope (core-supporting FFT/LOO).
- **Unchanged**: autonomous first-round delegation deficit (both require intervention to delegate); validator scope (format-only); scientific-correctness unjudged (no scoring); single-request token reporting missing.
- **Regressed (first autonomous round only)**: V3 round 1 made zero delegations and skipped the shared Skill entirely (V2 round 1: 2 autonomous delegations, Skill read at L62) — however V2's own delegations were late-verification-only, so neither round satisfies the frozen criterion autonomously.
- **Undeterminable**: whether V3's Skill revision (2.0.0→3.1.0) causes any reproducible improvement across tasks — requires the controlled design this harness explicitly disclaims; deeper operator auditing and platform compaction events are additional confounders.

## 5. Unresolved issues carried forward

1. Main-body analysis delegation remains intervention-dependent in both versions.
2. Sub-agent verification branches can themselves contain systematic errors (60×, 3600×, counting-unit) — main-side source audit before integration is essential and was only enforced via operator feedback in both rounds.
3. Reproduction of sub-agent-produced artifacts remains non-automated (read-from-adopted only).
4. IC definition/normalization unprovable from supplied files; Finding 4 stays conditional.
5. Sampling-grid-artifact alternative for 620/830/1040 μHz common peaks stays unresolved on supplied data.
6. No scoring performed in either round; nothing above is a quality judgment.
