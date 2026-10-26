# TruthInsightBench 29-action semantic evaluation

> This is the intermediate semantic-stage report. Final scores are written by `finalize_scores.mjs` after prior-art and deterministic closure.

- Evaluator model: `qwen3.8-max`
- Evaluated runs: `5`
- Registered findings: `20`
- Atomic action judgments: `580`

## Cohort-complete task summary

| Rank | Agent | Mean | Minimum | Maximum |
|---:|---|---:|---:|---:|
| 1 | sap-shared-context-v3.1 | 57.70 | 50.40 | 69.10 |

## Complete task-by-Agent matrix

| Task | sap-shared-context-v3.1 |
|---|---:|
| Astronomy_02_gravity_spectral_structure | 53.10 |
| Chemistry_02_photoionization_delay | 50.40 |
| EarthScience_01_glacial_fluvial_erosion | 69.10 |
| Neuro_02_calcium_response_regions | 57.10 |
| Physics_04_temporal_delay_transition | 58.80 |

## Per-run decomposition

| Task | Agent | Cohort status | Score | Finding 1 | Finding 2 | Yield bonus | Target recovery |
|---|---|---|---:|---:|---:|---:|---:|
| Astronomy_02_gravity_spectral_structure | sap-shared-context-v3.1 | complete | 53.10 | 50.5 | 49.0 | 8 | 5.0 |
| Chemistry_02_photoionization_delay | sap-shared-context-v3.1 | complete | 50.40 | 55.5 | 45.5 | 8 | 0.0 |
| EarthScience_01_glacial_fluvial_erosion | sap-shared-context-v3.1 | complete | 69.10 | 72.0 | 64.5 | 8 | 5.0 |
| Neuro_02_calcium_response_regions | sap-shared-context-v3.1 | complete | 57.10 | 62.0 | 59.5 | 8 | 0.0 |
| Physics_04_temporal_delay_transition | sap-shared-context-v3.1 | complete | 58.80 | 59.0 | 54.5 | 10 | 2.5 |

## Interpretation boundary

- The semantic stage uses the frozen run receipt, submitted artifacts, and path-resolution evidence; it does not execute Agent-authored source code.
- Reference-card matches use frozen prior-art assets. Other claims receive their final prior-art decision during closure.
- Deterministic penalties apply only when a successful recomputation directly contradicts a claim retained in the authoritative report.

