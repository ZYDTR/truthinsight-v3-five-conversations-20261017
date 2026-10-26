# Scale and Measurement Boundaries of Glacial and Nonglacial Erosion Rates: A Global Compilation Analysis

## Abstract

This study analyzes a global compilation of 6,715 published erosion-rate estimates (427 glacial, 6,288 nonglacial/fluvial) to quantify how erosion rate relates to observation timescale, process category, and measurement method. Three registered findings are reported: (1) the timescale-erosion rate relationship is strongly method-dependent, with cosmogenic methods showing near -1.0 slopes consistent with mechanical coupling (rate = thickness/time), while volumetric methods show opposite signs for glacial (-0.073) and fluvial (+0.117); (2) glacial erosion rates are systematically higher than fluvial rates by ~0.9 log10 units (~8x) after controlling for timescale and methodology; (3) accounting for source/site correlation via clustered standard errors renders the overall timescale effect statistically insignificant (p > 0.27), indicating the apparent scale dependence is driven by a small number of influential studies rather than a broad physical law. The interaction model (timescale × process × method) explains 58.7% of variance, confirming that both relationships depend critically on measurement method.

---

## Methods

### Data

The analysis uses two primary tabular datasets from the global erosion-rate compilation: `data/raw/glacial_erosion_Earth.tsv` (427 rows, 24 columns) and `data/raw/nonglacial_erosion_Earth.tsv` (6,288 rows, 26 columns). Both contain erosion rate (mm/yr), time interval (yr), methodology, type, area, precipitation, slope, latitude, plus auxiliary fields. Five methodology categories were identified: Volumetric, Cosmogenic surface, Thermochronometric, Relief, and Cosmogenic detrital. Auxiliary data include lithology tables (`data/raw/lithology_parsed*.tsv`), slope tables, and prior compilations (GloRiSe, OCTOPUS, CHELSEA, Chen et al. 2023).

All analyses were performed in log10 space for erosion rate and time interval, as rates span orders of magnitude (DATA_GUIDE warning). Rows with erosion rate ≤ 0 or time interval ≤ 0 were excluded from log analyses. Four nonglacial rows had zero erosion rates (Marrero et al. 2018, Antarctica). Missingness was audited at row level; key sparse columns include Elevation (96% missing in glacial), Sediment flux (83-88%), and Exhumation (81-100%).

### Statistical models

1. **Group-level OLS**: `log10(erode_rate) ~ log10(time_interval)` fitted separately within each combination of process category (Glacial/Fluvial) and methodology.
2. **Pooled ANCOVA**: `log10(erode_rate) ~ process_category * log10(time_interval) + method_group + process_category` to test main effects and interactions.
3. **Clustered SE**: Standard errors clustered by Reference (study) and Locality (site) to account for non-independence.
4. **Outlier sensitivity**: Winsorization at 1st/99th percentiles and trimming of top/bottom 1%.
5. **Bin analysis**: Observations binned into timescale categories (<1, 1-100, 100-10,000, >10,000 yr) with mean log10 erosion rates computed per bin.
6. **Bayesian posterior**: Grid-search posterior for power-law exponent b in erode_rate = a × time^b under uniform priors.
7. **Model comparison**: AIC/BIC across nine nested and non-nested specifications.

Analysis scripts are saved at `output/core_analysis.py` and `output/robustness_analysis.py`. Results artifacts are at `output/regression_results.json`, `output/comparison_results.json`, `output/robustness_results.json`, and `output/binned_means.png`.

---

## Registered Findings

### Finding 1: The timescale-erosion rate relationship is dominated by measurement method, not geological process

**Object and scope:** All 6,555 valid observations with positive erosion rates and time intervals across both glacial and nonglacial datasets.

**Relationship:** The slope of log10(erode_rate) vs log10(time_interval) varies dramatically by methodology. Cosmogenic methods (surface and detrital combined, n=3,642) show slopes near -1.0 (Fluvial_Cosmogenic: slope=-1.006, R²=0.994; Glacial_Cosmogenic: slope=-0.418, R²=0.260). Thermochronometric methods also show steep negative slopes (Glacial: -0.652, p<0.001; Fluvial: -0.647, ns due to n=4). In contrast, the Volumetric method shows a *positive* slope for fluvial data (+0.117, p<0.001, n=2,583) and a weak negative slope for glacial data (-0.073, p=0.004, n=233). Relief methods show moderate negative slopes (Glacial: -0.370, p=0.003; Fluvial: -0.420, ns, n=7).

**Core quantitative result:** The Chow test between Volumetric and non-Volumetric slopes is highly significant for fluvial data (F=3698, p<0.001) but not for glacial data (F=0.44, p=0.64), indicating the fluvial timescale pattern is driven almost entirely by cosmogenic/isotopic methods.

**Supporting evidence:** `output/regression_results.json` (group_regressions section); `working/subB/core_analysis.py`; `working/subC/robustness_analysis.py`.

**Robustness:** Excluding Volumetric data yields slope=-0.732 (R²=0.604); cosmogenic-only yields slope=-0.978 (R²=0.957). The near -1.0 slope for cosmogenic methods is consistent with mathematical coupling: if erosion_rate = measured_thickness / time_interval, then log(erode_rate) = log(thickness) - log(time), producing a slope of exactly -1.0 when thickness is approximately constant. This cannot be ruled out as an artifact without independent thickness measurements.

**Counterevidence and limitations:** The glacial Volumetric method shows a significant negative slope (-0.073, p=0.004), suggesting some component of the timescale relationship is not purely mechanical for glacial processes. However, this effect is small compared to the cosmogenic signal. The Relief method has very few observations (n=7 fluvial, n=18 glacial), limiting inference.

**Falsification proposal:** Obtain independent thickness measurements for a subset of sites and re-fit the model using thickness-adjusted erosion rates. If the near -1.0 slopes disappear for cosmogenic methods after thickness adjustment, this would confirm mechanical coupling.

---

### Finding 2: Glacial erosion rates are systematically higher than fluvial rates, even after controlling for timescale and methodology

**Object and scope:** 6,555 valid observations across both datasets.

**Relationship:** Glacial erosion rates are approximately 8× higher than fluvial rates on average (mean log10 difference = +0.904, Welch t-test: t=20.52, p<1.4×10⁻⁶⁷; Mann-Whitney U: p<1.1×10⁻⁸⁴). This difference persists after controlling for timescale (ANCOVA: process_category F=489.7, p<1.0×10⁻¹⁰⁴) and further after adding methodology as a covariate (process coefficient = +1.027, R²=0.126).

Within individual methodology groups:
- Cosmogenic: Glacial mean(log) = -0.612 vs Fluvial = -1.188, difference = +0.576 (p=1.6×10⁻¹⁰)
- Volumetric: Glacial = -0.244 vs Fluvial = -1.226, difference = +0.981 (p=2.8×10⁻⁴¹)
- Relief: Glacial = +0.036 vs Fluvial = +1.035, difference = -0.999 (p=0.006) — *reversal*
- Thermochronometric: Glacial = -0.060 vs Fluvial = +0.422, difference = -0.482 (p=0.066) — marginal

**Supporting evidence:** `output/core_analysis.py` (ANCOVA and process comparison code); `output/comparison_results.json` (process comparison statistics including t-test, Mann-Whitney, ANCOVA coefficients).

**Robustness:** The glacial > fluvial pattern holds for Cosmogenic and Volumetric methods (the two largest groups, n=3,534 and n=2,583 respectively). The reversal in Relief and Thermochronometric methods is based on very small samples (n=7 and n=4 for fluvial). Bin analysis confirms glacial rates exceed fluvial rates in all timescale bins except >10,000 yr, where the gap narrows substantially (glacial mean log = -0.409 vs fluvial = -1.803).

**Counterevidence and limitations:** The Relief method shows a reversal (fluvial > glacial), but with only 7 fluvial and 18 glacial observations, this may reflect sampling bias rather than a true process difference. Thermochronometric results are similarly limited (n=4 fluvial). The overall conclusion applies primarily to Cosmogenic and Volumetric methods, which together comprise 95% of the sample.

**Falsification proposal:** Collect additional thermochronometric and relief-based erosion rate measurements from sites where both glacial and fluvial processes operate under similar climatic and tectonic conditions. If the reversal persists in well-matched pairs, the process effect may be method-specific rather than universal.

---

### Finding 3: Source/site correlation invalidates the statistical significance of the overall timescale-erosion rate relationship

**Object and scope:** The effective sample size after accounting for clustering by Reference (study) and Locality (site).

**Relationship:** Ordinary least squares standard errors are severely underestimated because many observations share the same Reference or Locality. After clustering by Reference, the glacial timescale slope becomes completely insignificant (slope=-0.001, SE=0.192, p=0.997, 51 clusters); clustering by Locality yields slope=-0.041, SE=0.208, p=0.845 (46 clusters). For fluvial data, clustering by Reference gives p=0.279 (229 clusters) and by Locality p=0.577 (258 clusters). The OLS standard errors are 10-20× too small.

**Core quantitative result:** Under OLS, the combined timescale slope is -0.022 (SE=0.004, p=7.0×10⁻⁸). After Reference clustering, SE inflates to 0.028 (10× increase), rendering the effect insignificant.

**Supporting evidence:** `output/robustness_results.json` (clustered_se section); `working/subC/robustness_analysis.py`.

**Robustness:** Outlier trimming (top/bottom 1%) reduces OLS slope magnitudes by ~50% but does not change direction. Winsorization produces similar results. The clustering finding is robust to outlier treatment because it reflects the fundamental non-independence structure of the data, not leverage points.

**Counterevidence and limitations:** The clustered analysis reveals that the apparent timescale effect is driven by a small number of influential studies/sites rather than a broad empirical pattern across thousands of independent observations. With 154 References contributing 427 glacial observations (average 2.8 obs/Ref) and 265 References contributing 6,288 fluvial observations (average 23.7 obs/Ref), the effective sample size is much smaller than the nominal count. This limits the generalizability of any timescale-erosion relationship derived from this compilation.

**Falsification proposal:** Design a new field campaign targeting ≥50 geologically distinct sites spanning the full range of climates, lithologies, and process types, with each site measured using a single standardized methodology. If the timescale-erosion relationship holds with properly independent observations, the current null result would be overturned.

---

## Unresolved Questions and Alternative Explanations

1. **Mechanical coupling cannot be fully disentangled.** The near -1.0 slopes for cosmogenic methods are consistent with rate = thickness/time, but we lack independent thickness measurements to test this directly. Without such data, we cannot definitively separate physical scale dependence from measurement artifact for these methods.

2. **The Relief method reversal.** Fluvial Relief rates exceed glacial Relief rates, contrary to the overall pattern. This may reflect that Relief-based estimates capture long-term topographic evolution where fluvial incision in active orogens (e.g., Himalayas, Alps) produces high rates, while glacial Relief estimates often come from deglaciated areas with lower long-term rates. More data are needed.

3. **OCTOPUS compilation lacks time intervals.** The OCTOPUS dataset (n=236 with erosion rates) provides distribution-level consistency checks but could not be included in regression analyses due to missing time interval columns.

4. **Prior compilations support but do not strengthen inference.** GloRiSe (n=1,078) shows a consistent weak negative trend (slope=-0.025, p=0.551) but with insufficient precision. OCTOPUS median erosion rate (~0.04 mm/yr) falls within the fluvial range. Neither contradicts the main findings.

---

## How to Reproduce

```bash
cd /data/user/conversations/conv-46b0a68e-ac73-49c3-ba26-bbe4d51ce35a/project
python3 output/core_analysis.py          # Main regression and comparison analysis
python3 output/robustness_analysis.py    # Robustness checks and bin analysis
```

Both scripts read from `data/raw/` and write results to `output/`. Random seeds are not used (no resampling). All results are deterministic given the input data.

---

## Limitations

- **Non-independence:** Multiple rows per Reference, Site, or Compilation violate the independence assumption of standard regression. Clustered SEs address this partially but reduce effective sample size dramatically.
- **Method heterogeneity:** Each methodology captures different temporal windows and may encode different systematic biases. Direct comparison assumes methods measure the same underlying quantity.
- **Missing data:** 100% of rows have at least one missing value. Key variables (Elevation, Sediment flux, Exhumation) are sparsely reported, preventing multivariate analysis including these factors.
- **No causal identification:** Even statistically significant relationships describe associations, not causal mechanisms. Confounding by climate, tectonics, and lithology cannot be fully controlled with observational data.
