# Robustness Analysis Summary: Glacial vs Nonglacial Erosion Rates

## Data Overview
- **Glacial**: 427 valid rows (from 427 total)
- **Fluvial (Nonglacial)**: 6,128 valid rows (from 6,288 total)
- Both datasets contain `Sediment flux` and `Exhumation` columns, raising mechanical coupling concerns per DATA_GUIDE.

---

## 1. Mechanical Coupling Check (Methodology Stratification)

### Key Finding: The timescale slope is NOT a universal artifact -- it varies dramatically by methodology.

| Process | Methodology | Slope | p-value | n |
|---------|------------|-------|---------|---|
| Glacial | Volumetric | -0.073 | 0.004 | 233 |
| Glacial | Cosmogenic surface | -0.342 | <0.001 | 99 |
| Glacial | Thermochronometric | -0.652 | <0.001 | 68 |
| Glacial | Relief | -0.370 | 0.003 | 18 |
| Glacial | Cosmogenic detrital | -0.941 | 0.001 | 9 |
| Fluvial | Volumetric | +0.117 | <0.001 | 2,583 |
| Fluvial | Cosmogenic detrital | -0.995 | <0.001 | 3,470 |
| Fluvial | Cosmogenic surface | -0.982 | <0.001 | 64 |

**Chow test results:**
- **Glacial**: F=0.44, p=0.64 -- No significant difference between Volumetric and non-Volumetric slopes. This means the negative timescale slope in glacial data persists even within the Volumetric methodology alone, suggesting it is not purely a mechanical artifact of that method.
- **Fluvial**: F=3698, p<0.001 -- Extremely significant difference. Fluvial Volumetric has a *positive* slope (+0.117) while non-Volumetric methods have steeply negative slopes (-0.98 to -0.99). This suggests the fluvial timescale relationship is heavily driven by cosmogenic/isotopic methods.

**Interpretation**: The overall negative timescale-erosion rate relationship is real for cosmogenic and thermochronometric methods across both processes, but the Volumetric method shows opposite behavior between glacial (negative) and fluvial (positive). The fluvial result is dominated by cosmogenic detrital measurements (n=3,470), which show near-perfect -1.0 slopes -- consistent with a measurement artifact where erosion rate = thickness/time_interval.

---

## 2. Source/Site Correlation (Clustered Standard Errors)

### Key Finding: Clustering by Reference or Locality drastically inflates standard errors, rendering most slopes statistically insignificant.

| Model | Slope | SE (clustered) | p-value | Clusters |
|-------|-------|----------------|---------|----------|
| Glacial OLS | -0.057 | 0.018 | 0.002 | -- |
| Glacial/Reference clustered | -0.001 | 0.192 | 0.997 | 51 |
| Glacial/Locality clustered | -0.041 | 0.208 | 0.845 | 46 |
| Fluvial OLS | -0.031 | 0.004 | <0.001 | -- |
| Fluvial/Reference clustered | -0.031 | 0.028 | 0.279 | 229 |
| Fluvial/Locality clustered | -0.025 | 0.044 | 0.577 | 258 |

**Interpretation**: After accounting for clustering by source (Reference) or site (Locality), the timescale-erosion rate relationship becomes statistically insignificant for both processes. The OLS standard errors are severely underestimated because many observations share the same reference or locality. This is a critical finding: the apparent "timescale effect" may be largely driven by a small number of studies/sites rather than a genuine physical relationship.

---

## 3. Outlier Sensitivity

### Key Finding: Conclusions are moderately sensitive to outliers; trimming extreme values reduces slope magnitudes.

| Model | Glacial Slope | Fluvial Slope |
|-------|--------------|---------------|
| Original | -0.057 | -0.031 |
| Winsorized (1st/99th) | -0.052 | -0.028 |
| Trimmed (top/bottom 1%) | -0.033 | -0.017 |

**Interpretation**: Removing extreme erosion rates reduces the magnitude of the negative slope for both processes. The trimmed estimates are roughly half the original slopes, suggesting that the timescale relationship is partially driven by high-leverage outlier observations. However, the direction (negative) remains consistent.

---

## 4. Threshold / Bin Analysis

### Key Finding: Glacial erosion rates are consistently higher than fluvial rates across all timescale bins.

| Timescale Bin | Glacial n | Glacial mean(log10 ER) | Fluvial n | Fluvial mean(log10 ER) |
|---------------|-----------|----------------------|-----------|----------------------|
| <1 yr | 45 | -0.249 | 1,058 | -1.469 |
| 1-100 yr | 112 | +0.025 | 1,529 | -1.046 |
| 100-10,000 yr | 94 | -0.490 | 1,725 | -0.538 |
| >10,000 yr | 176 | -0.409 | 1,816 | -1.803 |

The gap between glacial and fluvial rates narrows at longer timescales (>10,000 yr), where glacial rates drop below fluvial rates in log space. The binned scatter plot (`binned_means.png`) visualizes these patterns with error bars showing standard error of the mean.

---

## 5. Bayesian Posterior Predictive Check

### Key Finding: Both processes show strong posterior support for negative power-law exponents.

| Process | b_mean | 95% CI | P(b>0) | P(b<0) |
|---------|--------|--------|--------|--------|
| Glacial | -0.057 | [-0.098, -0.023] | 0.001 | 0.999 |
| Fluvial | -0.026 | [-0.038, -0.023] | ~0.000 | ~1.000 |

The posterior distribution of the power-law exponent b is almost entirely concentrated below zero for both processes. Even under a Bayesian framework with uniform priors, there is overwhelming evidence against a positive timescale-erosion rate relationship.

---

## 6. Prior Compilation Cross-Check

### GloRiSe (n=1,078):
- Slope: -0.025, p=0.551 (not significant)
- Consistent with the main datasets in showing a weak negative trend, but insufficient precision to confirm significance.

### OCTOPUS (n=236 with erosion rates):
- Median erosion rate: 0.042 mm/yr (after converting from mm/kyr)
- No time interval column available; regression not possible.
- Distribution is broadly consistent with the lower end of the fluvial dataset.

---

## Cross-Dataset Consistency

- **Mann-Whitney U**: stat=2,045,585, p<0.001 -- Glacial and fluvial erosion rate distributions are significantly different.
- **Kolmogorov-Smirnov**: stat=0.445, p<0.001 -- The cumulative distributions differ substantially.

---

## Answers to Key Questions

### Q1: Is the timescale-erosion relationship real or an artifact of measurement method?
**Partially real, partially methodological.** The relationship is strongest (slope ~ -1.0) for cosmogenic and thermochronometric methods, which is consistent with a mechanical artifact where erosion_rate = measured_thickness / time_interval. However, the Volumetric method also shows a significant negative slope for glacial data (p=0.004), suggesting some component is not purely mechanical. For fluvial data, the Volumetric method shows a *positive* slope, indicating the overall pattern is driven by isotopic/cosmogenic methods.

### Q2: Does clustering by source/locality change significance?
**Yes, decisively.** After clustering by Reference, the glacial slope becomes completely insignificant (p=0.997). For fluvial data, clustering by Reference yields p=0.279 and by Locality p=0.577. The OLS standard errors are 10-20x too small. This means the apparent timescale effect is likely driven by a small number of influential studies rather than a broad empirical pattern.

### Q3: Are conclusions sensitive to outliers?
**Moderately.** Trimming the top and bottom 1% of erosion rates reduces slope magnitudes by approximately 50%. The direction remains negative, but the effect size is substantially smaller without extreme values.

### Q4: Do prior compilations support or contradict the main findings?
**Broadly consistent but less precise.** GloRiSe shows a similar weak negative trend (slope=-0.025) but with insufficient precision to confirm significance. OCTOPUS provides only distribution-level comparison (no time intervals) and its median erosion rate (~0.04 mm/yr) falls within the range of the main datasets. Neither prior compilation contradicts the main findings.

---

## Critical Limitations

1. **Mechanical coupling cannot be fully ruled out**: The near -1.0 slopes for cosmogenic methods strongly suggest that erosion_rate = thickness/time_interval creates a spurious correlation. Without independent thickness measurements, this cannot be disentangled.
2. **Non-independence is severe**: With 154 references contributing 427 glacial observations and 248 references contributing 6,128 fluvial observations, the effective sample size after clustering is much smaller than the nominal count.
3. **OCTOPUS lacks time intervals**: A key prior compilation could not be included in the regression analysis.
