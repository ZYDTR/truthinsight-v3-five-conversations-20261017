# Core Analysis Summary: Glacial vs Nonglacial Erosion Rates

## Data Overview

- **Total observations**: 6715
- **Valid for log analysis**: 6555
- **Glacial**: 427 | **Fluvial**: 6128
- **Missing erosion rate (nonglacial)**: 4
- **Missing time interval (nonglacial)**: 160

## Key Finding 1: Timescale-Erosion Relationship

The relationship between log10(errosion rate) and log10(timescale) was tested across all methodology groups.

| Group | n | Slope | R² | p-value | Significance |
|-------|---|-------|-----|---------|-------------|
| Fluvial_Cosmogenic | 3534 | -1.0062 | 0.994 | 0.00e+00 | *** |
| Fluvial_Relief | 7 | -0.4203 | 0.218 | 2.91e-01 | ns |
| Fluvial_Thermochronometric | 4 | -0.6466 | 0.395 | 3.71e-01 | ns |
| Fluvial_Volumetric | 2583 | 0.1174 | 0.053 | 3.32e-32 | *** |
| Glacial_Cosmogenic | 108 | -0.4183 | 0.260 | 1.74e-08 | *** |
| Glacial_Relief | 18 | -0.3699 | 0.432 | 3.03e-03 | ** |
| Glacial_Thermochronometric | 68 | -0.6516 | 0.331 | 2.90e-07 | *** |
| Glacial_Volumetric | 233 | -0.0729 | 0.035 | 4.41e-03 | ** |

### Overall timescale effect (pooled, no method interaction)

- Formula: `log_erode ~ log_time * process_category + method_group + process_category`
- R² = 0.1274
- Timescale coefficient: -0.14156495398838065
- Timescale p-value: 4.744318351886586e-71

## Key Finding 2: Glacial vs Fluvial Comparison

- **Mean log10 rate (Glacial)**: -0.2961 (n=427)
- **Mean log10 rate (Fluvial)**: -1.2004 (n=6128)
- **Mean difference (G-F)**: 0.9043
- **Welch t-test**: t=20.5211, p=1.42e-67
- **Mann-Whitney**: U=571071, p=1.12e-84

### ANCOVA (controlling for timescale)

- Formula: `log_erode ~ process_category + log_time`
- R² = 0.0781
- Process category F-statistic: 489.7444, p=1.03e-104
- Timescale F-statistic: 65.0052, p=8.81e-16

### ANCOVA with method control

- Formula: `log_erode ~ process_category + log_time + method_group`
- R² = 0.1260
- Process category coefficient: 1.026511858220885
- Process category CI: N/A

## Key Finding 3: Method Stratification

Erosion rate differences between Glacial and Fluvial within each methodology:

| Method | n(G/F) | G mean(log) | F mean(log) | Difference | t-test p |
|--------|--------|-------------|-------------|------------|----------|
| Cosmogenic | 108/3534 | -0.612 | -1.188 | 0.576 | 1.6314054817912648e-10 |
| Relief | 18/7 | 0.036 | 1.035 | -0.999 | 0.005699269863182483 |
| Thermochronometric | 68/4 | -0.060 | 0.422 | -0.482 | 0.06648925859587448 |
| Volumetric | 233/2583 | -0.244 | -1.226 | 0.981 | 2.775202779119402e-41 |

## Key Finding 4: Model Comparison

Models ranked by AIC (lower is better):

| Rank | Model | AIC | BIC | R² |
|------|-------|-----|-----|-----|
| 1 | pooled_interaction | 10704.7 | 10772.6 | 0.5865 |
| 2 | pooled_main | 15594.3 | 15641.9 | 0.1274 |
| 3 | full_main_effects | 15603.2 | 15643.9 | 0.1260 |
| 4 | timescale_plus_process | 15947.0 | 15967.3 | 0.0781 |
| 5 | process_only | 16009.7 | 16023.3 | 0.0689 |
| 6 | timescale_plus_method | 16093.8 | 16127.7 | 0.0578 |
| 7 | method_only | 16278.2 | 16305.4 | 0.0306 |
| 8 | timescale_only | 16448.7 | 16462.2 | 0.0044 |
| 9 | intercept_only | 16475.7 | 16482.5 | 0.0000 |

## Robustness Checks

- **Without Volumetric** (n=3739): slope=-0.7315, p=0.00e+00, R²=0.6041
- **Cosmogenic only** (n=3642): slope=-0.9781, p=0.00e+00, R²=0.9570

## Interpretation Notes

- **Timescale coupling**: A non-zero slope in the log-log relationship may reflect mathematical coupling (rate = thickness / time) rather than a true physical dependence.
- **Method stratification**: Different methodologies capture different temporal windows and may introduce systematic biases.
- **Process effect**: After controlling for timescale and methodology, the residual difference between glacial and fluvial rates represents the pure process effect.
- **Best model**: The model with lowest AIC provides the best trade-off between fit and complexity.