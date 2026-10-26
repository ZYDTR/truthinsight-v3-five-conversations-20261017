"""
Robustness checks and batch-effect analysis for calcium response data.
Task: Neuro_02_calcium_response_regions
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# ── Load data ───────────────────────────────────────────────────────────────
DATA_PATH = "/data/user/conversations/conv-4a42b09e-c6e8-4347-910d-86fe4c3da0c2/project/data/cellular_calcium_response_summaries.tsv"
OUT_DIR   = "/data/user/conversations/conv-4a42b09e-c6e8-4347-910d-86fe4c3da0c2/project/working/analysis_B"

df = pd.read_csv(DATA_PATH, sep='\t')
print(f"Data shape: {df.shape}")
print(f"Batches: {sorted(df['recording_batch_id'].unique())}")
print(f"Regions: {sorted(df['anatomical_region_id'].unique())}")
print(f"Conditions: {sorted(df['condition'].unique())}")
print(f"Slices: {sorted(df['slice_id'].unique())}")
print(f"Age range: {df['animal_age_days'].min()} - {df['animal_age_days'].max()}")

# Response variables to analyze
RESP_VARS = [
    'mean_amplitude_dff0',
    'mean_time_to_peak_s',
    'mean_peak_width_s',
    'mean_peak_prominence_dff0',
    'mean_peak_frequency_hz',
    'mean_auc_au',
]

# ── 1. Batch-effect quantification via ANOVA SS decomposition ───────────────
print("\n=== BATCH-EFFECT QUANTIFICATION ===")

batch_results = []
for var in RESP_VARS:
    # One-way ANOVA across batches
    groups = df.groupby('recording_batch_id')[var].apply(list)
    group_lists = [v for v in groups.values if len(v) > 1]
    f_stat, p_val = stats.f_oneway(*group_lists)

    # Total SS
    total_ss = ((df[var] - df[var].mean()) ** 2).sum()
    # Between-batch SS
    between_ss = sum(len(g) * (np.mean(g) - df[var].mean())**2 for g in group_lists)
    # Within-batch SS
    within_ss = total_ss - between_ss

    eta_sq = between_ss / total_ss if total_ss > 0 else 0
    partial_eta_sq = between_ss / (between_ss + within_ss) if (between_ss + within_ss) > 0 else 0

    n_batches = df['recording_batch_id'].nunique()
    n_total = len(df)

    batch_results.append({
        'response_variable': var,
        'f_statistic': f_stat,
        'p_value': p_val,
        'total_ss': total_ss,
        'between_batch_ss': between_ss,
        'within_batch_ss': within_ss,
        'eta_squared': eta_sq,
        'partial_eta_squared': partial_eta_sq,
        'n_batches': n_batches,
        'n_observations': n_total,
    })

batch_df = pd.DataFrame(batch_results)
batch_df.to_csv(f"{OUT_DIR}/batch_effects.csv", index=False)
print("Batch effects saved to batch_effects.csv")
print(batch_df[['response_variable', 'eta_squared', 'partial_eta_squared', 'p_value']].to_string(index=False))

# ── 2. Region × Condition confounding map ──────────────────────────────────
print("\n=== REGION × CONDITION COVERAGE ===")
coverage = df.groupby(['anatomical_region_id', 'condition']).size().unstack(fill_value=0)
print(coverage)

# Identify which region-condition combos are missing
missing = []
for r in df['anatomical_region_id'].unique():
    for c in df['condition'].unique():
        count = coverage.loc[r, c] if r in coverage.index and c in coverage.columns else 0
        if count == 0:
            missing.append((r, c))
print(f"\nMissing region-condition combinations: {missing}")

# ── 3. Batch leave-one-out robustness ──────────────────────────────────────
print("\n=== BATCH LEAVE-ONE-OUT ROBUSTNESS ===")

# Get all region pairs that share at least one condition
regions = sorted(df['anatomical_region_id'].unique())
conditions = sorted(df['condition'].unique())

robustness_rows = []

for var in RESP_VARS:
    # Full-data region x condition means
    full_means = df.groupby(['anatomical_region_id', 'condition'])[var].mean()

    # For each batch, leave it out and recompute
    batches = sorted(df['recording_batch_id'].unique())
    for batch in batches:
        df_sub = df[df['recording_batch_id'] != batch]
        sub_means = df_sub.groupby(['anatomical_region_id', 'condition'])[var].mean()

        # Compare region pairs for shared conditions
        for cond in conditions:
            for r1, r2 in combinations(regions, 2):
                key1 = (r1, cond)
                key2 = (r2, cond)
                # Check if both keys exist in full data AND in the leave-one-out subset
                if key1 in full_means.index and key2 in full_means.index:
                    if key1 in sub_means.index and key2 in sub_means.index:
                        full_diff = full_means[key1] - full_means[key2]
                        sub_diff = sub_means[key1] - sub_means[key2]
                        sign_match = int(np.sign(full_diff) == np.sign(sub_diff))
                        diff_change = abs(full_diff - sub_diff)

                        robustness_rows.append({
                            'response_variable': var,
                            'region_pair': f"{r1}_vs_{r2}",
                            'condition': cond,
                            'full_data_diff': full_diff,
                            'leave_out_batch': batch,
                            'remaining_diff': sub_diff,
                            'sign_matches': sign_match,
                            'diff_change': diff_change,
                        })

robust_df = pd.DataFrame(robustness_rows)
robust_df.to_csv(f"{OUT_DIR}/robustness_results.csv", index=False)
print(f"Robustness results saved ({len(robust_df)} rows)")

# Summarize: what fraction of comparisons maintain sign?
summary = robust_df.groupby(['response_variable', 'region_pair', 'condition']).agg(
    n_comparisons=('sign_matches', 'count'),
    sign_match_count=('sign_matches', 'sum'),
    mean_diff_change=('diff_change', 'mean'),
    full_data_mean_diff=('full_data_diff', 'first'),
).reset_index()
summary['sign_match_rate'] = summary['sign_match_count'] / summary['n_comparisons']
print("\nSign match rates by variable and region pair:")
print(summary[['response_variable', 'region_pair', 'condition', 'sign_match_rate', 'mean_diff_change']].to_string(index=False))

# ── 4. Slice-level aggregation ─────────────────────────────────────────────
print("\n=== SLICE-LEVEL AGGREGATION ===")

# Compute mean per slice-region-condition group for each response variable
# Then compare region pairs at the slice level
slice_robustness = []
for var in RESP_VARS:
    # Aggregate to slice level: mean of each cell's value within each slice-region-condition
    slice_agg = df.groupby(['slice_id', 'anatomical_region_id', 'condition'])[var].mean().reset_index()
    slice_agg.columns = ['slice_id', 'anatomical_region_id', 'condition', 'slice_mean']

    for cond in conditions:
        for r1, r2 in combinations(regions, 2):
            m1 = slice_agg[(slice_agg['anatomical_region_id'] == r1) & (slice_agg['condition'] == cond)]['slice_mean']
            m2 = slice_agg[(slice_agg['anatomical_region_id'] == r2) & (slice_agg['condition'] == cond)]['slice_mean']

            if len(m1) >= 2 and len(m2) >= 2:
                t_stat, p_val = stats.ttest_ind(m1, m2, equal_var=False)
                cohens_d = (m1.mean() - m2.mean()) / np.sqrt(((m1.std(ddof=1)**2 + m2.std(ddof=1)**2) / 2)) if len(m1)+len(m2) > 2 else 0

                # Also get cell-level result for comparison
                cell_m1 = df[(df['anatomical_region_id'] == r1) & (df['condition'] == cond)][var]
                cell_m2 = df[(df['anatomical_region_id'] == r2) & (df['condition'] == cond)][var]
                cell_t, cell_p = stats.ttest_ind(cell_m1, cell_m2, equal_var=False) if len(cell_m1)>=2 and len(cell_m2)>=2 else (0, 1)

                slice_robustness.append({
                    'response_variable': var,
                    'region_pair': f"{r1}_vs_{r2}",
                    'condition': cond,
                    'n_slices_r1': len(m1),
                    'n_slices_r2': len(m2),
                    'slice_mean_diff': m1.mean() - m2.mean(),
                    'slice_t_stat': t_stat,
                    'slice_p_value': p_val,
                    'cohens_d': cohens_d,
                    'cell_mean_diff': cell_m1.mean() - cell_m2.mean(),
                    'cell_t_stat': cell_t,
                    'cell_p_value': cell_p,
                })

slice_df = pd.DataFrame(slice_robustness)
print("Slice-level vs cell-level comparisons:")
print(slice_df[['response_variable', 'region_pair', 'condition',
                 'slice_p_value', 'cell_p_value', 'slice_mean_diff', 'cell_mean_diff']].to_string(index=False))

# ── 5. Age stratification ─────────────────────────────────────────────────
print("\n=== AGE STRATIFICATION ===")

# Check if age is confounded with region, condition, or batch
age_by_region = df.groupby('anatomical_region_id')['animal_age_days'].agg(['mean', 'std', 'min', 'max', 'count'])
print("Age by region:")
print(age_by_region)

age_by_condition = df.groupby('condition')['animal_age_days'].agg(['mean', 'std', 'min', 'max', 'count'])
print("\nAge by condition:")
print(age_by_condition)

# Split into young/middle/old
age_bins = [0, 50, 60, 100]
age_labels = ['young_40-50', 'middle_50-60', 'old_60+']
df['age_group'] = pd.cut(df['animal_age_days'], bins=age_bins, labels=age_labels)

age_strat_results = []
for var in RESP_VARS:
    for cond in conditions:
        for r1, r2 in combinations(regions, 2):
            for ag in age_labels:
                sub1 = df[(df['anatomical_region_id'] == r1) & (df['condition'] == cond) & (df['age_group'] == ag)][var]
                sub2 = df[(df['anatomical_region_id'] == r2) & (df['condition'] == cond) & (df['age_group'] == ag)][var]
                if len(sub1) >= 2 and len(sub2) >= 2:
                    t_stat, p_val = stats.ttest_ind(sub1, sub2, equal_var=False)
                    age_strat_results.append({
                        'response_variable': var,
                        'region_pair': f"{r1}_vs_{r2}",
                        'condition': cond,
                        'age_group': ag,
                        'n_cells_r1': len(sub1),
                        'n_cells_r2': len(sub2),
                        'mean_diff': sub1.mean() - sub2.mean(),
                        't_stat': t_stat,
                        'p_value': p_val,
                    })

age_strat_df = pd.DataFrame(age_strat_results)
print(f"\nAge-stratified comparisons: {len(age_strat_df)}")
if len(age_strat_df) > 0:
    print(age_strat_df[['response_variable', 'region_pair', 'condition', 'age_group', 'n_cells_r1', 'n_cells_r2', 'p_value']].head(20).to_string(index=False))

# ── 6. Alternative explanation checks ──────────────────────────────────────
print("\n=== ALTERNATIVE EXPLANATION CHECKS ===")

# Region_3 only has receptor_stimulated -> region effect and condition effect are confounded
r3_conditions = df[df['anatomical_region_id'] == 'region_3']['condition'].unique()
r4_conditions = df[df['anatomical_region_id'] == 'region_4']['condition'].unique()
print(f"Region_3 conditions: {r3_conditions}")
print(f"Region_4 conditions: {r4_conditions}")

# Region_2 vs Region_3 comparison for receptor_stimulated:
# Any observed difference could be due to region OR condition (receptor_stimulated vs baseline/neural_activity_blocked)
# These are completely confounded
print("\n--- Unidentifiable comparisons ---")
print("Region_2 vs Region_3 (receptor_stimulated only):")
print("  Region effect and condition effect are COMPLETELY CONFOUNDED.")
print("  Cannot separate whether differences are due to anatomical region or stimulation type.")

print("\nRegion_4 has NO receptor_stimulated data:")
print("  Any baseline/neural_activity_blocked comparison in Region_4 cannot be generalized")
print("  to receptor_stimulated responses across all regions.")

# Show the actual data counts
for r in sorted(df['anatomical_region_id'].unique()):
    for c in sorted(df['condition'].unique()):
        cnt = len(df[(df['anatomical_region_id'] == r) & (df['condition'] == c)])
        print(f"  {r} x {c}: {cnt} cells")

# ── 7. Visualizations ─────────────────────────────────────────────────────
print("\n=== GENERATING FIGURES ===")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Batch Effects and Robustness Checks', fontsize=14, fontweight='bold')

# Panel 1: Eta-squared by response variable (batch effect size)
ax = axes[0, 0]
bp = ax.barh(range(len(batch_df)), batch_df['eta_squared'], color='#2196F3')
ax.set_yticks(range(len(batch_df)))
ax.set_yticklabels([v.replace('mean_', '').replace('_dff0', '').replace('_s', '').replace('_hz', '').replace('_au', '') for v in batch_df['response_variable']], fontsize=8)
ax.set_xlabel('Eta-squared (batch variance proportion)')
ax.set_title('Batch Effect Size (η²)')
ax.axvline(x=0.1, color='red', linestyle='--', label='η²=0.1 (large)')
ax.legend(fontsize=8)

# Panel 2: Batch means heatmap for amplitude
ax = axes[0, 1]
batch_means_amp = df.groupby(['recording_batch_id', 'anatomical_region_id'])['mean_amplitude_dff0'].mean().unstack(fill_value=np.nan)
sns.heatmap(batch_means_amp, annot=True, fmt='.2f', cmap='RdBu_r', ax=ax,
            xticklabels=[r.replace('region_', '') for r in batch_means_amp.columns])
ax.set_title('Mean Amplitude by Batch × Region')
ax.set_xlabel('Region')
ax.set_ylabel('Batch')

# Panel 3: Distribution of values by region (amplitude)
ax = axes[0, 2]
sns.boxplot(data=df, x='anatomical_region_id', y='mean_amplitude_dff0', ax=ax, palette='Set2')
ax.set_title('Amplitude Distribution by Region')
ax.set_xlabel('Region')
ax.set_ylabel('Mean Amplitude (ΔF/F₀)')

# Panel 4: Batch leave-one-out stability (amplitude, region_1 vs region_2)
ax = axes[1, 0]
amp_var = 'mean_amplitude_dff0'
full_means_amp = df.groupby(['anatomical_region_id', 'condition'])[amp_var].mean()
loo_diffs = []
loo_batches = []
for batch in sorted(df['recording_batch_id'].unique()):
    df_sub = df[df['recording_batch_id'] != batch]
    sub_means_amp = df_sub.groupby(['anatomical_region_id', 'condition'])[amp_var].mean()
    for cond in conditions:
        if ('region_1', cond) in sub_means_amp.index and ('region_2', cond) in sub_means_amp.index:
            if ('region_1', cond) in full_means_amp.index and ('region_2', cond) in full_means_amp.index:
                full_d = full_means_amp[('region_1', cond)] - full_means_amp[('region_2', cond)]
                sub_d = sub_means_amp[('region_1', cond)] - sub_means_amp[('region_2', cond)]
                loo_diffs.append(sub_d)
                loo_batches.append(batch)

if loo_diffs:
    # Plot per-condition LOO
    for i, cond in enumerate(conditions):
        indices = [j for j in range(len(loo_diffs)) if j % len(conditions) == i]
        vals = [loo_diffs[j] for j in indices]
        if vals:
            ax.plot(indices, vals, 'o-', label=f'{cond}', markersize=4)
    # Full data reference lines
    for i, cond in enumerate(conditions):
        val = full_means_amp[('region_1', cond)] - full_means_amp[('region_2', cond)]
        ax.axhline(y=val, linestyle=':', alpha=0.5)
    ax.set_xlabel('Batch Leave-Out Order')
    ax.set_ylabel(f'Mean Diff (Region1 - Region2)\n{amp_var}')
    ax.set_title('LOO Stability: Region1 vs Region2')
    ax.legend(fontsize=7)

# Panel 5: Slice-level vs cell-level p-values (amplitude)
ax = axes[1, 1]
amp_slice = slice_df[slice_df['response_variable'] == 'mean_amplitude_dff0']
if len(amp_slice) > 0:
    x_pos = np.arange(len(amp_slice))
    width = 0.35
    ax.bar(x_pos - width/2, -np.log10(amp_slice['slice_p_value']), width, label='Slice-level', color='green')
    ax.bar(x_pos + width/2, -np.log10(amp_slice['cell_p_value']), width, label='Cell-level', color='blue')
    ax.axhline(y=-np.log10(0.05), color='red', linestyle='--', label='p=0.05')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{rp.split('_vs_')[0][-1]}-{rp.split('_vs_')[1][-1]}\n{c}" for rp, c in zip(amp_slice['region_pair'], amp_slice['condition'])], rotation=45, ha='right', fontsize=7)
    ax.set_ylabel('-log10(p-value)')
    ax.set_title('Amplitude: Slice vs Cell p-values')
    ax.legend(fontsize=8)

# Panel 6: Age distribution by region
ax = axes[1, 2]
sns.violinplot(data=df, x='anatomical_region_id', y='animal_age_days', inner='quartile', ax=ax, palette='Set2')
ax.set_title('Age Distribution by Region')
ax.set_xlabel('Region')
ax.set_ylabel('Animal Age (days)')

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/figures.png", dpi=150, bbox_inches='tight')
print(f"Figures saved to figures.png")

# ── Summary report ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY OF FINDINGS")
print("="*60)

# Key batch effect findings
strong_batch = batch_df[batch_df['eta_squared'] > 0.05]
if len(strong_batch) > 0:
    print(f"\n1. BATCH EFFECTS: {len(strong_batch)} variable(s) show η² > 0.05:")
    for _, row in strong_batch.iterrows():
        print(f"   {row['response_variable']}: η² = {row['eta_squared']:.4f}, p = {row['p_value']:.6f}")
else:
    print("\n1. BATCH EFFECTS: No variable shows η² > 0.05 (weak batch effects)")
    for _, row in batch_df.iterrows():
        print(f"   {row['response_variable']}: η² = {row['eta_squared']:.4f}, p = {row['p_value']:.6f}")

# Sign match rates
if len(summary) > 0:
    avg_match = summary['sign_match_rate'].mean()
    print(f"\n2. LOO ROBUSTNESS: Average sign match rate = {avg_match:.2%}")
    low_match = summary[summary['sign_match_rate'] < 0.8]
    if len(low_match) > 0:
        print(f"   WARNING: {len(low_match)} comparisons have <80% sign match rate:")
        for _, row in low_match.iterrows():
            print(f"     {row['response_variable']} | {row['region_pair']} | {row['condition']}: {row['sign_match_rate']:.2%}")

# Confounding
print(f"\n3. CONFUNDING STRUCTURE:")
print(f"   Region_3: only {list(r3_conditions)} -> region and condition confounded")
print(f"   Region_4: only {list(r4_conditions)} -> no receptor_stimulated data")
print(f"   This means region×condition interactions are NOT identifiable for these regions.")

# Slice-level results
if len(slice_df) > 0:
    sig_slice = slice_df[slice_df['slice_p_value'] < 0.05]
    sig_cell = slice_df[slice_df['cell_p_value'] < 0.05]
    print(f"\n4. SLICE-LEVEL RESULTS:")
    print(f"   Significant at slice level (p<0.05): {len(sig_slice)}/{len(slice_df)}")
    print(f"   Significant at cell level (p<0.05): {len(sig_cell)}/{len(slice_df)}")

# Age stratification
if len(age_strat_df) > 0:
    print(f"\n5. AGE STRATIFICATION: {len(age_strat_df)} comparisons possible")
    print(f"   Many comparisons have very small sample sizes in age strata.")

print("\n" + "="*60)
print("FILES SAVED:")
print(f"  {OUT_DIR}/batch_effects.csv")
print(f"  {OUT_DIR}/robustness_results.csv")
print(f"  {OUT_DIR}/figures.png")
print("="*60)
