# Analysis State - Astronomy_02_gravity_spectral_structure

## Facts Established
- 22 complete time-resolved passes, ~77 samples each (1698 total)
- 3 residual models: A, B, C (mm/s)
- Candidate spectrum: 507 rows across 2 families (frequency_amplitude_scan, minimum_velocity_scan)
- Ranked parameter grid: 250 candidates with delta IC
- Mode-frequency grid: 52 modes (l=2-8, n=0-7)
- Uniform alternative: 24 velocity values with IC

## Key Results
1. Best candidate: v_max=30, v_min=0.05, freq=1010 uHz, width=275, IC=43.9
2. Rank 2: v_max=20, v_min=0.05, freq=1060 uHz, width=300, delta_IC=2.0
3. Only 4 candidates within delta_IC<=10 of best
4. Best uniform: v=0.1 cm/s, IC=1522.1 (much worse than structured candidates)
5. Between-pass variance fraction: A=0.7%, B=0.01%, C=0.05% (mostly within-pass)
6. Cross-model correlations: MA-MB mean=0.57, MA-MC mean=0.81, MB-MC mean=0.78
7. Mean lag-1 autocorrelation: A=0.53, B=-0.28, C=0.16 (model-dependent)

## Decisions Made
- Primary evidence from ranked_full_parameter_grid.tsv for spectral structure claims
- Temporal analysis uses per-pass statistics (not pooled, as per DATA_GUIDE warning)
- Robustness via leave-one-pass-out and first-half/second-half splits

## Artifacts Produced
- output/analysis.py - main analysis script
- output/generate_artifacts.py - artifact generation
- output/analysis_results.json - full numerical results
- output/result_artifacts.json - machine-readable result artifacts

## Unresolved
- FFT periodicity: no clear consistent peak frequency across passes
- Model B shows negative autocorrelation while A is positive - structural difference unclear
