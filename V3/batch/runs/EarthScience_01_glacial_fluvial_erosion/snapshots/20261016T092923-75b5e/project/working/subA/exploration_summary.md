# Data Audit & Exploration Summary

## Glacial vs Nonglacial Erosion Rate Datasets

### Dataset Overview

| Property | Glacial | Nonglacial |
|----------|---------|------------|
| Total rows | 427 | 6288 |
| Columns | 24 | 26 |
| Missing rows (any col) | 427 | 6288 |
| Pct rows with any missing | 100.0% | 100.0% |

### Column Schema

#### glacial_erosion_Earth

| Column | Type | Missing | % Missing | Unique |
|--------|------|---------|-----------|--------|
| Compilation | str | 0 | 0.0% | 13 |
| Reference | str | 0 | 0.0% | 154 |
| Reference DOI | str | 60 | 14.05% | 120 |
| Locality | str | 0 | 0.0% | 123 |
| Glacier | str | 0 | 0.0% | 184 |
| Region | str | 0 | 0.0% | 13 |
| Latitude | float64 | 2 | 0.47% | 228 |
| Longitude | float64 | 2 | 0.47% | 226 |
| Elevation (m) | float64 | 412 | 96.49% | 14 |
| Precipitation (mm/yr) | float64 | 2 | 0.47% | 227 |
| Slope (m/km) | float64 | 2 | 0.47% | 227 |
| Type | str | 0 | 0.0% | 5 |
| Lithology | str | 131 | 30.68% | 16 |
| Methodology | str | 0 | 0.0% | 5 |
| Area (km2) | float64 | 35 | 8.2% | 200 |
| Time interval (yr) | float64 | 0 | 0.0% | 191 |
| Sediment flux (km3/yr) | float64 | 376 | 88.06% | 49 |
| Exhumation (m) | float64 | 346 | 81.03% | 77 |
| Exhumation min (m) | float64 | 389 | 91.1% | 32 |
| Exhumation max (m) | float64 | 392 | 91.8% | 33 |
| Erosion rate (mm/yr) | float64 | 0 | 0.0% | 238 |
| Erosion rate min | float64 | 222 | 51.99% | 126 |
| Erosion rate max | float64 | 230 | 53.86% | 144 |
| Comments | str | 240 | 56.21% | 128 |

#### nonglacial_erosion_Earth

| Column | Type | Missing | % Missing | Unique |
|--------|------|---------|-----------|--------|
| Compilation | str | 0 | 0.0% | 6 |
| Reference | str | 0 | 0.0% | 265 |
| Reference DOI | str | 375 | 5.96% | 251 |
| Locality | str | 0 | 0.0% | 1819 |
| Basin | str | 1217 | 19.35% | 2249 |
| Place | str | 0 | 0.0% | 122 |
| Region | str | 0 | 0.0% | 15 |
| Sample ID | str | 1119 | 17.8% | 4736 |
| Latitude | float64 | 0 | 0.0% | 4872 |
| Longitude | float64 | 0 | 0.0% | 4879 |
| Elevation (m) | float64 | 2611 | 41.52% | 3050 |
| Precipitation (mm/yr) | float64 | 0 | 0.0% | 4185 |
| Slope (m/km) | float64 | 0 | 0.0% | 4692 |
| Type | str | 0 | 0.0% | 2 |
| Lithology | str | 2607 | 41.46% | 17 |
| Methodology | str | 0 | 0.0% | 5 |
| Area (km2) | float64 | 68 | 1.08% | 3837 |
| Time interval (yr) | float64 | 160 | 2.54% | 3521 |
| Sediment flux (km3/yr) | float64 | 5231 | 83.19% | 898 |
| Exhumation (m) | float64 | 6277 | 99.83% | 11 |
| Exhumation min (m) | float64 | 6285 | 99.95% | 2 |
| Exhumation max (m) | float64 | 6286 | 99.97% | 2 |
| Erosion rate (mm/yr) | float64 | 0 | 0.0% | 5711 |
| Erosion rate min | float64 | 1529 | 24.32% | 4489 |
| Erosion rate max | float64 | 1529 | 24.32% | 4536 |
| Comments | str | 1538 | 24.46% | 22 |

#### slope_glacial

| Column | Type | Missing | % Missing | Unique |
|--------|------|---------|-----------|--------|
| 88.13203214695751 | float64 | 2 | 0.43% | 246 |

#### slope_nonglacial

| Column | Type | Missing | % Missing | Unique |
|--------|------|---------|-----------|--------|
| 416.31848852901487 | float64 | 0 | 0.0% | 4688 |

#### lithology_parsed

| Column | Type | Missing | % Missing | Unique |
|--------|------|---------|-----------|--------|
| Latitude | float64 | 1 | 0.44% | 228 |
| Longitude | float64 | 1 | 0.44% | 226 |
| Hash | str | 0 | 0.0% | 229 |
| Lithology | str | 46 | 20.09% | 18 |
| Age | float64 | 47 | 20.52% | 44 |
| Age Uncert | float64 | 58 | 25.33% | 40 |
| Unparsed Lithology | str | 0 | 0.0% | 51 |

#### lithology_parsed_nonglacial

| Column | Type | Missing | % Missing | Unique |
|--------|------|---------|-----------|--------|
| Latitude | float64 | 0 | 0.0% | 4872 |
| Longitude | float64 | 0 | 0.0% | 4879 |
| Hash | str | 0 | 0.0% | 4900 |
| Lithology | str | 516 | 10.53% | 39 |
| Age | float64 | 513 | 10.47% | 82 |
| Age Uncert | float64 | 1338 | 27.31% | 57 |
| Unparsed Lithology | str | 0 | 0.0% | 172 |

### Erosion Rate Distribution

| Statistic | Glacial | Nonglacial |
|-----------|---------|------------|
| min | 0.0004 | 0.0 |
| max | 1000.0 | 118.864 |
| mean | 7.698705409367682 | 0.35399940535305346 |
| median | 0.55 | 0.061094300000000004 |
| std | 60.74447060807744 | 1.9684545063809906 |

### Time Interval Distribution

| Statistic | Glacial | Nonglacial |
|-----------|---------|------------|
| min | 0.0191781 | 0.00274 |
| max | 250000000.0 | 20000000.0 |
| mean | 1741868.2784354386 | 53732.41845415796 |
| median | 1270.0 | 1201.185 |
| std | 12915843.251323644 | 467452.64533457026 |

### Log10 Erosion Rate Distribution

| Statistic | Glacial | Nonglacial |
|-----------|---------|------------|
| log10_min | -3.3979400086720375 | -5.0 |
| log10_max | 3.0 | 2.0750503410046206 |
| log10_mean | -0.29608290510655616 | -1.2608086539464742 |
| log10_median | -0.2596373105057561 | -1.2123426879756036 |

### Methodology Categories


#### glacial

| Methodology | Count |
|-------------|-------|
| Volumetric | 233 |
| Cosmogenic surface | 99 |
| Thermochronometric | 68 |
| Relief | 18 |
| Cosmogenic detrital | 9 |


#### nonglacial

| Methodology | Count |
|-------------|-------|
| Cosmogenic detrital | 3470 |
| Volumetric | 2583 |
| Cosmogenic surface | 224 |
| Relief | 7 |
| Thermochronometric | 4 |

### Region Distribution (Top 10)


#### glacial

| Region | Count |
|--------|-------|
| North American Cordillera | 114 |
| Fennoscandia | 73 |
| Alps | 73 |
| Greenland | 55 |
| Antarctica | 29 |
| Central Asia | 24 |
| South American Cordillera | 22 |
| Laurentide | 14 |
| Iceland | 13 |
| British Isles | 4 |


#### nonglacial

| Region | Count |
|--------|-------|
| North America | 1595 |
| Asia | 1334 |
| Europe | 1205 |
| South America | 1056 |
| Antarctica | 224 |
| Africa | 220 |
| Russia | 153 |
| Central America | 127 |
| Australia | 121 |
| Pacific | 115 |

### Outlier Detection


#### glacial

- Zero erosion rates: 0
- Negative erosion rates: 0
- NaN erosion rates: 0
- Zero time intervals: 0
- Negative time intervals: 0
- IQR outlier fences (erosion): [0.0, 6.3500000000000005]
- Extreme high erosion outliers: 37
- Extreme low erosion outliers: 0


#### nonglacial

- Zero erosion rates: 4
- Negative erosion rates: 0
- NaN erosion rates: 0
- Zero time intervals: 0
- Negative time intervals: 0
- IQR outlier fences (erosion): [0.0, 0.801823975]
- Extreme high erosion outliers: 539
- Extreme low erosion outliers: 0

### Prior Compilation Overlap

- GloRiSe_unique_localities: 408
- GloRiSe_unique_references: 33
- OCTOPUS_unique_references: 488
- OCTOPUS_unique_studies: 176
- Chen_et_al_unique_references: 29
- Chen_et_al_unique_locations: 1477
- GloRiSe_vs_OCTOPUS_overlap: 0
- GloRiSe_vs_Chen_overlap: 0
- OCTOPUS_vs_Chen_overlap: 0
- Main_table_compilations: {'glacial': ['Amantov et al., 2011', 'Anderson, 2005', 'Antoniazza and Lane, 2021', 'Balter-Kennedy et al., 2021', 'Bell and Laine, 1985', 'Björnsson, 1979', 'Burbank et al., 2000', 'Faleide et al., 1996', 'Geirsdóttir et al., 2007', 'Hallet et al., 1996', 'Lliboutry, 1994', 'Richardson and Holmlund, 1992', 'This study'], 'nonglacial': ['Burbank et al., 2000', 'Chen et al., 2022', 'GloRiSe', 'Marrero et al., 2018', 'OCTOPUS', 'This study']}
- Main_tables_contain_prior_compilations: {'nonglacial_contains_GloRiSe': True, 'nonglacial_contains_OCTOPUS': True, 'nonglacial_contains_Chen_2022': True}
- Glacial_ref_count: 161
- Nonglacial_ref_count: 270

### Key Questions Answered

**Unique localities/sources per dataset:** See locality_source_counts above.
**Methodology categories:** See methodology_categories above.
**Timescale range per type:** See timescale_ranges_by_type above.
**Zero or missing erosion rates:** See outlier_detection above.
**Lithologies represented:** See cross_tabulations -> Lithology_distribution above.

---
*Generated by data_audit.py*
