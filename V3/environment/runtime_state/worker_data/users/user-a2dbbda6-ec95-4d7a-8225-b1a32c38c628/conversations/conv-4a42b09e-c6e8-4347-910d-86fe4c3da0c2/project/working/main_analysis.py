#!/usr/bin/env python3
"""Main calcium response analysis - independent execution for final report."""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import warnings
warnings.filterwarnings('ignore')

# Load data
df = pd.read_csv('data/cellular_calcium_response_summaries.tsv', sep='\t')
print(f"Loaded {len(df)} observations, {len(df.columns)} columns")

numeric_cols = ['mean_amplitude_dff0', 'mean_time_to_peak_s', 'mean_peak_width_s',
                'mean_peak_prominence_dff0', 'mean_peak_frequency_hz', 'mean_auc_au']
col_labels = {'mean_amplitude_dff0': 'Amplitude (dF/F0)',
              'mean_time_to_peak_s': 'Time-to-Peak (s)',
              'mean_peak_width_s': 'Peak Width (s)',
              'mean_peak_prominence_dff0': 'Prominence (dF/F0)',
              'mean_peak_frequency_hz': 'Frequency (Hz)',
              'mean_auc_au': 'AUC (AU)'}

# ============================================================
# 1. Region x Condition structure
# ============================================================
print("\n=== Region x Condition Structure ===")
cross = pd.crosstab(df['anatomical_region_id'], df['condition'])
print(cross)

# ============================================================
# 2. Summary statistics by region x condition
# ============================================================
print("\n=== Summary Statistics by Region x Condition ===")
summary = df.groupby(['anatomical_region_id', 'condition'])[numeric_cols].agg(
    ['count', 'mean', 'std', 'sem']
).round(4)
print(summary.to_string())

# ============================================================
# 3. ANOVA on regions 1+2 (where all conditions exist)
# ============================================================
print("\n=== ANOVA: Regions 1+2 ===")
r12 = df[df['anatomical_region_id'].isin(['region_1', 'region_2'])].copy()
results_anova = {}
for col in numeric_cols:
    formula = f'{col} ~ C(anatomical_region_id) * C(condition)'
    try:
        model = ols(formula, data=r12).fit()
        anova_table = anova_lm(model, typ=2)
        results_anova[col] = anova_table
        print(f"\n{col}:")
        print(anova_table.to_string())
    except Exception as e:
        print(f"{col}: FAILED - {e}")

# ============================================================
# 4. Pairwise contrasts in regions 1+2 (Welch's t-test)
# ============================================================
print("\n=== Pairwise Contrasts (Regions 1+2) ===")
contrasts_results = []
conditions = ['baseline', 'neural_activity_blocked', 'receptor_stimulated']
for col in numeric_cols:
    for c1, c2 in [('baseline', 'neural_activity_blocked'),
                    ('baseline', 'receptor_stimulated'),
                    ('neural_activity_blocked', 'receptor_stimulated')]:
        d1 = r12[r12['condition'] == c1][col]
        d2 = r12[r12['condition'] == c2][col]
        t_stat, p_val = stats.ttest_ind(d1, d2, equal_var=False)
        # Cohen's d
        pooled_std = np.sqrt((d1.var() + d2.var()) / 2)
        cohens_d = (d1.mean() - d2.mean()) / pooled_std if pooled_std > 0 else 0
        # Hedges' g (small sample correction)
        n1, n2 = len(d1), len(d2)
        j = 1 - (3 - 1/(n1+n2-2)) / (4*(n1+n2-2) - 1) if (n1+n2-2) > 0 else 1
        hedges_g = cohens_d * j
        contrasts_results.append({
            'variable': col,
            'label': col_labels[col],
            'contrast': f'{c1} vs {c2}',
            'n1': n1, 'n2': n2,
            'mean1': d1.mean(), 'mean2': d2.mean(),
            'diff': d1.mean() - d2.mean(),
            't_stat': t_stat, 'p_value': p_val,
            'cohens_d': cohens_d, 'hedges_g': hedges_g,
            'regions': '1+2'
        })

contrasts_df = pd.DataFrame(contrasts_results)
print(contrasts_df[['label', 'contrast', 'n1', 'n2', 'mean1', 'mean2', 'diff',
                     't_stat', 'p_value', 'cohens_d', 'hedges_g']].to_string())

# ============================================================
# 5. Baseline-only contrasts across all regions
# ============================================================
print("\n=== Baseline Comparisons Across Regions ===")
baseline_df = df[df['condition'] == 'baseline'].copy()
for col in numeric_cols:
    groups = baseline_df.groupby('anatomical_region_id')[col]
    print(f"\n{col_labels[col]}:")
    for region, grp in groups:
        print(f"  {region}: n={len(grp)}, mean={grp.mean():.4f}, sem={grp.sem():.4f}")
    # ANOVA across regions
    group_data = [baseline_df[baseline_df['anatomical_region_id'] == r][col].values
                  for r in ['region_1', 'region_2', 'region_4']]
    f_stat, p_val = stats.f_oneway(*group_data)
    print(f"  F={f_stat:.4f}, p={p_val:.6f}")

# ============================================================
# 6. Batch effect quantification (ANOVA SS decomposition)
# ============================================================
print("\n=== Batch Effect Quantification ===")
batch_results = []
for col in numeric_cols:
    y = df[col].values
    ss_total = np.sum((y - y.mean())**2)
    batch_means = df.groupby('recording_batch_id')[col].mean().values
    batch_counts = df.groupby('recording_batch_id')[col].count().values
    ss_between = np.sum(batch_counts * (batch_means - y.mean())**2)
    ss_within = ss_total - ss_between
    eta_sq = ss_between / ss_total if ss_total > 0 else 0

    # One-way ANOVA F-test
    groups = [df[df['recording_batch_id'] == b][col].values
              for b in sorted(df['recording_batch_id'].unique())]
    f_stat, p_val = stats.f_oneway(*groups)

    batch_results.append({
        'variable': col,
        'label': col_labels[col],
        'ss_total': ss_total,
        'ss_between': ss_between,
        'ss_within': ss_within,
        'eta_squared': eta_sq,
        'f_statistic': f_stat,
        'p_value': p_val,
        'n_batches': len(groups)
    })
    print(f"{col_labels[col]}: η²={eta_sq:.4f}, F={f_stat:.4f}, p={p_val:.2e}")

batch_df = pd.DataFrame(batch_results)

# ============================================================
# 7. Slice-level aggregation (cells within slice not independent)
# ============================================================
print("\n=== Slice-Level Aggregation ===")
slice_agg = df.groupby(['slice_id', 'anatomical_region_id', 'condition']).agg(
    n_cells=('observation_id', 'count'),
    mean_amplitude=('mean_amplitude_dff0', 'mean'),
    mean_auc=('mean_auc_au', 'mean'),
    mean_width=('mean_peak_width_s', 'mean'),
    mean_ttp=('mean_time_to_peak_s', 'mean')
).reset_index()

print(slice_agg.to_string())

# ============================================================
# 8. Robustness: leave-one-batch-out for receptor_stimulated vs baseline
# ============================================================
print("\n=== Robustness: Leave-One-Batch-Out ===")
lobo_results = []
batches = sorted(df['recording_batch_id'].unique())
for batch_out in batches:
    df_subset = df[~(df['recording_batch_id'] == batch_out)].copy()
    # Only look at regions 1+2 where both conditions exist
    r12_sub = df_subset[df_subset['anatomical_region_id'].isin(['region_1', 'region_2'])]
    bl = r12_sub[r12_sub['condition'] == 'baseline']
    rs = r12_sub[r12_sub['condition'] == 'receptor_stimulated']

    for col in ['mean_amplitude_dff0', 'mean_auc_au', 'mean_peak_width_s']:
        d_bl = bl[col]
        d_rs = rs[col]
        t_stat, p_val = stats.ttest_ind(d_bl, d_rs, equal_var=False)
        diff = d_bl.mean() - d_rs.mean()
        lobo_results.append({
            'batch_excluded': batch_out,
            'variable': col_labels[col],
            'diff': diff, 't_stat': t_stat, 'p_value': p_val,
            'n_baseline': len(d_bl), 'n_stimulated': len(d_rs)
        })

lobo_df = pd.DataFrame(lobo_results)
print(lobo_df.to_string())

# ============================================================
# 9. Age correlation
# ============================================================
print("\n=== Age Correlations ===")
for col in numeric_cols:
    r, p = stats.pearsonr(df['animal_age_days'], df[col])
    print(f"  {col_labels[col]}: r={r:.4f}, p={p:.2e}")

# ============================================================
# 10. Figures
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
axes = axes.flatten()

for i, col in enumerate(numeric_cols):
    ax = axes[i]
    pivot = df.pivot_table(values=col, index='anatomical_region_id',
                           columns='condition', aggfunc='mean')
    pivot.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title(col_labels[col], fontsize=10)
    ax.set_xlabel('Region')
    ax.set_ylabel('Mean Value')
    ax.legend(title='Condition')
    ax.tick_params(axis='x', rotation=0)

plt.tight_layout()
plt.savefig('output/figures_main.png', dpi=150, bbox_inches='tight')
plt.close()

# Violin plot for amplitude by region x condition
fig, ax = plt.subplots(figsize=(10, 6))
sns.violinplot(data=df, x='anatomical_region_id', y='mean_amplitude_dff0',
               hue='condition', split=False, inner='quartile')
ax.set_title('Calcium Amplitude by Region and Condition')
ax.set_xlabel('Anatomical Region')
ax.set_ylabel('Mean Amplitude (dF/F0)')
plt.tight_layout()
plt.savefig('output/figures_violin_amplitude.png', dpi=150, bbox_inches='tight')
plt.close()

# Batch effect bar chart
fig, ax = plt.subplots(figsize=(10, 6))
batch_summary = df.groupby('recording_batch_id')['mean_amplitude_dff0'].agg(['mean', 'sem'])
ax.bar(range(len(batch_summary)), batch_summary['mean'], yerr=batch_summary['sem'],
       capsize=3, color='steelblue')
ax.set_xticks(range(len(batch_summary)))
ax.set_xticklabels(sorted(df['recording_batch_id'].unique()), rotation=45, ha='right')
ax.set_title('Batch Effect on Calcium Amplitude')
ax.set_xlabel('Recording Batch')
ax.set_ylabel('Mean Amplitude (dF/F0)')
plt.tight_layout()
plt.savefig('output/figures_batch_effect.png', dpi=150, bbox_inches='tight')
plt.close()

# Save all results
contrasts_df.to_csv('output/contrasts_regions12.csv', index=False)
batch_df.to_csv('output/batch_effects.csv', index=False)
lobo_df.to_csv('output/robustness_lobo.csv', index=False)

# Save summary table
summary.to_csv('output/summary_stats.csv', float_format='%.4f')

print("\n=== All output files saved to output/ ===")
print("Files: figures_main.png, figures_violin_amplitude.png, figures_batch_effect.png")
print("       contrasts_regions12.csv, batch_effects.csv, robustness_lobo.csv, summary_stats.csv")
