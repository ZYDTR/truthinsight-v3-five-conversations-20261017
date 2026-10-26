"""
Calcium Response Analysis - Main Statistical Analysis (v2)
==========================================================
Analyzes calcium event amplitude, timing, width, prominence, frequency, and area
across regions and conditions, accounting for age, slice, and batch effects.

Data: cellular_calcium_response_summaries.tsv (819 cell observations)
Structure: 819 cells nested in 7 slices, 9 batches, 8 age values
Regions: region_1..4 (anonymous), Conditions: baseline, neural_activity_blocked, receptor_stimulated
Important design constraint: Region_3 only has receptor_stimulated; Region_4 only has baseline + neural_activity_blocked
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
import io

warnings.filterwarnings('ignore')

# ============================================================
# 0. SETUP
# ============================================================
OUTPUT_DIR = '/data/user/conversations/conv-4a42b09e-c6e8-4347-910d-86fe4c3da0c2/project/working/analysis_A'
DATA_PATH = '/data/user/conversations/conv-4a42b09e-c6e8-4347-910d-86fe4c3da0c2/project/data/cellular_calcium_response_summaries.tsv'

model_output_log = io.StringIO()
def log(msg):
    print(msg)
    model_output_log.write(msg + '\n')

log("=" * 80)
log("CALCIUM RESPONSE ANALYSIS - MAIN STATISTICAL ANALYSIS (v2)")
log("=" * 80)

# ============================================================
# 1. LOAD AND EXPLORE DATA
# ============================================================
log("\n" + "=" * 80)
log("SECTION 1: DATA LOADING AND EXPLORATORY ANALYSIS")
log("=" * 80)

df = pd.read_csv(DATA_PATH, sep='\t')
log(f"\nLoaded data: {df.shape[0]} observations, {df.shape[1]} columns")
log(f"Columns: {list(df.columns)}")

missing = df.isnull().sum()
log(f"\nMissing values: {'None found' if missing.sum() == 0 else str(missing[missing > 0].to_dict())}")

numeric_cols = ['mean_amplitude_dff0', 'mean_time_to_peak_s', 'mean_peak_width_s',
                'mean_peak_prominence_dff0', 'mean_peak_frequency_hz', 'mean_auc_au']

log("\n--- Summary Statistics ---")
log(df[numeric_cols].describe().to_string())

df['anatomical_region_id'] = df['anatomical_region_id'].astype('category')
df['condition'] = df['condition'].astype('category')
df['slice_id'] = df['slice_id'].astype('category')
df['recording_batch_id'] = df['recording_batch_id'].astype('category')

log(f"\nUnique regions: {df['anatomical_region_id'].cat.categories.tolist()}")
log(f"Unique conditions: {df['condition'].cat.categories.tolist()}")
log(f"Unique slices: {df['slice_id'].nunique()}")
log(f"Unique batches: {df['recording_batch_id'].nunique()}")
log(f"Age range: {df['animal_age_days'].min()} - {df['animal_age_days'].max()} days")
log(f"Unique ages: {sorted(df['animal_age_days'].unique())}")

log("\n--- Region x Condition Cross-tabulation (cell counts) ---")
ct = pd.crosstab(df['anatomical_region_id'], df['condition'])
log(ct.to_string())

for region in sorted(df['anatomical_region_id'].cat.categories):
    conds = df[df['anatomical_region_id'] == region]['condition'].unique()
    n_cells = len(df[df['anatomical_region_id'] == region])
    log(f"  {region}: conditions={sorted(conds)}, n_cells={n_cells}")

# ============================================================
# 2. EXPLORATORY DATA ANALYSIS
# ============================================================
log("\n" + "=" * 80)
log("SECTION 2: EXPLORATORY DATA ANALYSIS")
log("=" * 80)

log("\n--- Mean Values by Region x Condition ---")
for var in numeric_cols:
    log(f"\n{var}:")
    means = df.groupby(['anatomical_region_id', 'condition'])[var].mean()
    log(means.to_string())

log("\n--- Marginal Means by Region ---")
for var in numeric_cols:
    log(f"\n{var}:")
    means = df.groupby('anatomical_region_id')[var].agg(['mean', 'std', 'count'])
    log(means.to_string())

log("\n--- Marginal Means by Condition ---")
for var in numeric_cols:
    log(f"\n{var}:")
    means = df.groupby('condition')[var].agg(['mean', 'std', 'count'])
    log(means.to_string())

log("\n--- Batch-level Summary Statistics ---")
for var in numeric_cols[:3]:
    log(f"\n{var} by batch:")
    batch_stats = df.groupby('recording_batch_id')[var].agg(['mean', 'std', 'count'])
    log(batch_stats.to_string())

log("\n--- Age vs Response Variables (correlation) ---")
age_corr_results = {}
for var in numeric_cols:
    corr, pval = stats.pearsonr(df['animal_age_days'], df[var])
    age_corr_results[var] = (corr, pval)
    log(f"  {var}: Pearson r={corr:.4f}, p={pval:.4e}")

# ============================================================
# 3. LINEAR MIXED EFFECTS MODELS
# ============================================================
log("\n" + "=" * 80)
log("SECTION 3: LINEAR MIXED EFFECTS MODELING")
log("=" * 80)

# Design subsets
df_full_cond = df[df['anatomical_region_id'].isin(['region_1', 'region_2'])].copy()
df_baseline = df[df['condition'].isin(['baseline', 'neural_activity_blocked'])].copy()

log(f"\nSubset with all 3 conditions (regions 1+2): {len(df_full_cond)} cells")
log(f"Baseline subset (all regions): {len(df_baseline)} cells")

# Helper function to fit LMM and extract results
def fit_lmm(formula, data, group_col, model_label):
    """Fit a mixed linear model and return structured results."""
    log(f"\n--- {model_label} ---")
    try:
        model = smf.mixedlm(formula, data, groups=data[group_col])
        result = model.fit(reml=True, maxiter=200)

        converged = hasattr(result, 'converged') and result.converged
        # Also check via internal state
        if not converged:
            try:
                converged = result.mle_retvals.get('converged', False)
            except:
                pass

        log(f"Converged: {converged}")
        log(f"Iterations: {result.iterations if hasattr(result, 'iterations') else 'N/A'}")
        log(f"Log-likelihood: {result.llf:.2f}")
        log(f"AIC: {result.aic:.2f}, BIC: {result.bic:.2f}")

        # Random effect variance
        if hasattr(result, 'random_effects_cov') and result.random_effects_cov is not None:
            log(f"Random effect variance components:\n{result.random_effects_cov}")

        log("\nFixed Effects Summary:")
        log(str(result.summary()))

        return result, True
    except Exception as e:
        log(f"FAILED: {type(e).__name__}: {e}")
        return None, False

def extract_fe_params(result, prefix=""):
    """Extract fixed effect parameters into a list of dicts."""
    rows = []
    if result is None:
        return rows
    fe = result.fe_params
    be = result.bse
    for param in fe.index:
        coef = fe[param]
        se = be[param]
        z = coef / se if se != 0 and not np.isnan(se) else float('nan')
        p = 2 * (1 - stats.norm.cdf(abs(z))) if not np.isnan(z) else float('nan')
        ci_l = coef - 1.96 * se
        ci_u = coef + 1.96 * se
        rows.append({
            'param': param,
            'coef': coef,
            'se': se,
            'z': z,
            'p_value': p,
            'ci_lower': ci_l,
            'ci_upper': ci_u
        })
    return rows

# ---- Model 1a: Amplitude additive, all data ----
result_1a, ok_1a = fit_lmm(
    "mean_amplitude_dff0 ~ anatomical_region_id + condition + animal_age_days",
    df, 'recording_batch_id',
    "Model 1a: Amplitude ~ Region + Condition + Age (additive, all 819 cells)"
)

# ---- Model 1b: Amplitude interaction, regions 1+2 ----
# Use reduced formula to avoid singularity: main effects + interactions for estimable terms
result_1b, ok_1b = fit_lmm(
    "mean_amplitude_dff0 ~ anatomical_region_id * condition + animal_age_days",
    df_full_cond, 'recording_batch_id',
    "Model 1b: Amplitude ~ Region * Condition + Age (regions 1+2, 580 cells)"
)

# If full interaction fails, try without age interaction
if not ok_1b:
    log("\nTrying reduced interaction model...")
    result_1b, ok_1b = fit_lmm(
        "mean_amplitude_dff0 ~ anatomical_region_id + condition + anatomical_region_id:condition + animal_age_days",
        df_full_cond, 'recording_batch_id',
        "Model 1b-reduced: Amplitude ~ Region + Condition + Region:Condition + Age"
    )

# ---- Model 1c: Amplitude interaction, baseline conditions, all regions ----
result_1c, ok_1c = fit_lmm(
    "mean_amplitude_dff0 ~ anatomical_region_id * condition + animal_age_days",
    df_baseline, 'recording_batch_id',
    "Model 1c: Amplitude ~ Region * Condition + Age (baseline conditions, all regions)"
)

if not ok_1c:
    log("\nTrying reduced interaction model for baseline...")
    result_1c, ok_1c = fit_lmm(
        "mean_amplitude_dff0 ~ anatomical_region_id + condition + anatomical_region_id:condition + animal_age_days",
        df_baseline, 'recording_batch_id',
        "Model 1c-reduced: Amplitude ~ Region + Condition + Region:Condition + Age (baseline)"
    )

# ---- Model 2a: Time to peak additive, all data ----
result_2a, ok_2a = fit_lmm(
    "mean_time_to_peak_s ~ anatomical_region_id + condition + animal_age_days",
    df, 'recording_batch_id',
    "Model 2a: TimeToPeak ~ Region + Condition + Age (additive, all 819 cells)"
)

# ---- Model 2b: Time to peak interaction, regions 1+2 ----
result_2b, ok_2b = fit_lmm(
    "mean_time_to_peak_s ~ anatomical_region_id * condition + animal_age_days",
    df_full_cond, 'recording_batch_id',
    "Model 2b: TimeToPeak ~ Region * Condition + Age (regions 1+2)"
)

if not ok_2b:
    log("\nTrying reduced interaction model for time to peak...")
    result_2b, ok_2b = fit_lmm(
        "mean_time_to_peak_s ~ anatomical_region_id + condition + anatomical_region_id:condition + animal_age_days",
        df_full_cond, 'recording_batch_id',
        "Model 2b-reduced: TimeToPeak ~ Region + Condition + Region:Condition + Age"
    )

# ---- Models for remaining variables (additive, all data) ----
results_other = {}
for var_name in ['mean_peak_width_s', 'mean_peak_prominence_dff0', 'mean_peak_frequency_hz', 'mean_auc_au']:
    result, ok = fit_lmm(
        f"{var_name} ~ anatomical_region_id + condition + animal_age_days",
        df, 'recording_batch_id',
        f"Model 3: {var_name} ~ Region + Condition + Age (all 819 cells)"
    )
    results_other[var_name] = (result, ok)

# ============================================================
# 3D. BATCH EFFECT QUANTIFICATION
# ============================================================
log("\n" + "=" * 80)
log("SECTION 3D: BATCH EFFECT QUANTIFICATION")
log("=" * 80)

for var_name in ['mean_amplitude_dff0', 'mean_time_to_peak_s']:
    log(f"\n--- Batch Effect on {var_name} ---")

    # OLS (no random effect)
    ols_formula = f"{var_name} ~ anatomical_region_id + condition + animal_age_days"
    try:
        ols_model = smf.ols(ols_formula, df).fit()
        log(f"OLS (no batch RE): AIC={ols_model.aic:.2f}, BIC={ols_model.bic:.2f}, R²={ols_model.rsquared:.4f}")
    except Exception as e:
        log(f"OLS failed: {e}")
        continue

    # LMM with batch random effect
    try:
        lmm_model = smf.mixedlm(ols_formula, df, groups=df['recording_batch_id']).fit(reml=True, maxiter=200)
        log(f"LMM (batch RE): AIC={lmm_model.aic:.2f}, BIC={lmm_model.bic:.2f}, LogL={lmm_model.llf:.2f}")

        # Extract random effect variance
        if hasattr(lmm_model, 'random_effects_cov') and lmm_model.random_effects_cov is not None:
            log(f"  Batch variance component: {lmm_model.random_effects_cov.values[0][0] if hasattr(lmm_model.random_effects_cov, 'values') else 'N/A'}")

        # Likelihood ratio test
        ll_diff = 2 * (lmm_model.llf - ols_model.llf)
        n_batches = df['recording_batch_id'].nunique()
        df_diff = n_batches - 1
        p_val = 1 - stats.chi2.cdf(ll_diff, df_diff)
        log(f"  LRT statistic: {ll_diff:.4f}, df={df_diff}, p={p_val:.4e}")

        # Also compute ICC (intraclass correlation)
        residual_var = lmm_model.scale
        batch_var = 0
        if hasattr(lmm_model, 'random_effects_cov') and lmm_model.random_effects_cov is not None:
            try:
                batch_var = lmm_model.random_effects_cov.values[0][0]
            except:
                pass
        total_var = residual_var + batch_var
        icc = batch_var / total_var if total_var > 0 else 0
        log(f"  Residual variance: {residual_var:.4f}, Batch variance: {batch_var:.4f}, ICC: {icc:.4f}")

    except Exception as e:
        log(f"LMM failed: {e}")

# ============================================================
# 3E. AGE EFFECT
# ============================================================
log("\n" + "=" * 80)
log("SECTION 3E: AGE EFFECT ANALYSIS")
log("=" * 80)

for var_name in numeric_cols:
    log(f"\n--- Age effect on {var_name} ---")
    try:
        model = smf.mixedlm(f"{var_name} ~ animal_age_days", df,
                           groups=df['recording_batch_id']).fit(reml=True, maxiter=200)
        slope = model.fe_params['animal_age_days']
        se = model.bse['animal_age_days']
        z = slope / se
        p = 2 * (1 - stats.norm.cdf(abs(z)))
        log(f"  Slope: {slope:.6f} per day, SE={se:.6f}, z={z:.4f}, p={p:.4e}")
        log(f"  Converged: {model.converged if hasattr(model, 'converged') else 'N/A'}")
    except Exception as e:
        log(f"Failed: {e}")

# ============================================================
# 3F. SPECIFIC CONTRASTS (estimable comparisons)
# ============================================================
log("\n" + "=" * 80)
log("SECTION 3F: ESTIMABLE CONTRASTS")
log("=" * 80)

# Contrast 1: Condition effects in regions 1+2
log("\n--- Condition contrasts in regions 1+2 ---")
for var in numeric_cols:
    log(f"\n{var}:")
    for cond_pair in [('baseline', 'neural_activity_blocked'),
                       ('baseline', 'receptor_stimulated'),
                       ('neural_activity_blocked', 'receptor_stimulated')]:
        c1, c2 = cond_pair
        sub = df_full_cond[df_full_cond['condition'].isin([c1, c2])]
        g1 = sub[sub['condition'] == c1][var]
        g2 = sub[sub['condition'] == c2][var]
        t_stat, p_val = stats.ttest_ind(g1, g2)
        mean_c1 = g1.mean()
        mean_c2 = g2.mean()
        diff = mean_c1 - mean_c2
        log(f"  {c1} vs {c2}: diff={diff:.4f}, t={t_stat:.4f}, p={p_val:.4e}, "
            f"mean({c1})={mean_c1:.4f}, mean({c2})={mean_c2:.4f}")

# Contrast 2: Region effects under shared conditions (baseline + neural_activity_blocked)
log("\n--- Region contrasts under shared conditions (baseline + blocked) ---")
df_shared = df[df['condition'].isin(['baseline', 'neural_activity_blocked'])]
for var in numeric_cols:
    log(f"\n{var}:")
    for reg_pair in [('region_1', 'region_2'), ('region_1', 'region_3'), ('region_1', 'region_4'),
                      ('region_2', 'region_3'), ('region_2', 'region_4'), ('region_3', 'region_4')]:
        r1, r2 = reg_pair
        sub = df_shared[df_shared['anatomical_region_id'].isin([r1, r2])]
        g1 = sub[sub['anatomical_region_id'] == r1][var]
        g2 = sub[sub['anatomical_region_id'] == r2][var]
        if len(g1) > 1 and len(g2) > 1:
            t_stat, p_val = stats.ttest_ind(g1, g2)
            mean_r1 = g1.mean()
            mean_r2 = g2.mean()
            diff = mean_r1 - mean_r2
            log(f"  {r1} vs {r2}: diff={diff:.4f}, t={t_stat:.4f}, p={p_val:.4e}, "
                f"n1={len(g1)}, n2={len(g2)}")
        else:
            log(f"  {r1} vs {r2}: INSUFFICIENT DATA (n1={len(g1)}, n2={len(g2)})")

# ============================================================
# 4. MODEL DIAGNOSTICS
# ============================================================
log("\n" + "=" * 80)
log("SECTION 4: MODEL DIAGNOSTICS")
log("=" * 80)

# Diagnostics for Model 1a (amplitude additive)
if ok_1a and result_1a is not None:
    log("\n--- Diagnostics for Model 1a (Amplitude, additive, all data) ---")

    # Get residuals from fitted values
    fitted = result_1a.fittedvalues
    resid = result_1a.resid
    log(f"Residuals: mean={resid.mean():.6f}, std={resid.std():.6f}, min={resid.min():.4f}, max={resid.max():.4f}")

    # Normality check (Shapiro-Wilk limited to 5000)
    n_check = min(len(resid), 5000)
    w_stat, norm_p = stats.shapiro(resid[:n_check])
    log(f"Shapiro-Wilk normality test (n={n_check}): W={w_stat:.4f}, p={norm_p:.4e}")

    # Skewness and kurtosis
    log(f"Skewness: {stats.skew(resid):.4f}, Kurtosis: {stats.kurtosis(resid):.4f}")

    # VIF for collinearity
    try:
        design_matrix = result_1a.model.exog
        vif_values = []
        for i in range(design_matrix.shape[1]):
            X_other = np.delete(design_matrix, i, axis=1)
            beta = np.linalg.lstsq(X_other, design_matrix[:, i], rcond=None)[0]
            y_hat = X_other @ beta
            ss_res = np.sum((design_matrix[:, i] - y_hat)**2)
            ss_tot = np.sum((design_matrix[:, i] - np.mean(design_matrix[:, i]))**2)
            vif_i = ss_tot / ss_res if ss_res > 1e-10 else float('inf')
            vif_values.append(vif_i)

        max_vif = max(vif_values)
        avg_vif = np.mean(vif_values)
        log(f"VIF: max={max_vif:.2f}, mean={avg_vif:.2f}")
        for i, (param, vif) in enumerate(zip(result_1a.model.exog_names, vif_values)):
            log(f"  {param}: VIF={vif:.2f}")
        if max_vif > 10:
            log("  WARNING: High multicollinearity detected!")
        elif max_vif > 5:
            log("  CAUTION: Moderate multicollinearity present.")
        else:
            log("  OK: No concerning multicollinearity.")
    except Exception as e:
        log(f"VIF calculation failed: {e}")

# Heteroscedasticity check
if ok_1a and result_1a is not None:
    log("\n--- Heteroscedasticity Check (Model 1a) ---")
    try:
        resp = result_1a.model.endog
        exog = result_1a.model.exog
        bp_stat, bp_p, _, _ = het_breuschpagan(resp - exog @ result_1a.params, exog)
        log(f"Breusch-Pagan test: stat={bp_stat:.4f}, p={bp_p:.4e}")
        if bp_p < 0.05:
            log("  WARNING: Heteroscedasticity detected.")
        else:
            log("  OK: No significant heteroscedasticity.")
    except Exception as e:
        log(f"Heteroscedasticity check failed: {e}")

# ============================================================
# 5. GENERATE FIGURES
# ============================================================
log("\n" + "=" * 80)
log("SECTION 5: FIGURE GENERATION")
log("=" * 80)

colors = {'baseline': '#2196F3', 'neural_activity_blocked': '#FF9800', 'receptor_stimulated': '#4CAF50'}
region_colors_map = {'region_1': '#1a237e', 'region_2': '#006064', 'region_3': '#b71c1c', 'region_4': '#1b5e20'}

# Figure 1: Bar charts for all 6 variables
fig, axes = plt.subplots(3, 2, figsize=(16, 18))
fig.suptitle('Calcium Response: Region x Condition Means ± SEM', fontsize=14, fontweight='bold')

vars_titles = [
    ('mean_amplitude_dff0', 'Mean Amplitude (dF/F0)'),
    ('mean_time_to_peak_s', 'Mean Time to Peak (s)'),
    ('mean_peak_width_s', 'Mean Peak Width (s)'),
    ('mean_peak_prominence_dff0', 'Mean Peak Prominence (dF/F0)'),
    ('mean_peak_frequency_hz', 'Mean Peak Frequency (Hz)'),
    ('mean_auc_au', 'Mean AUC (AU)')
]

for idx, (var, title) in enumerate(vars_titles):
    row = idx // 2
    col = idx % 2
    ax = axes[row, col]

    grouped = df.groupby(['anatomical_region_id', 'condition'])[var].agg(['mean', 'sem'])

    x_pos = np.arange(4)
    width = 0.25

    for ci, cond in enumerate(['baseline', 'neural_activity_blocked', 'receptor_stimulated']):
        means = []
        errs = []
        for ri in range(4):
            region = f'region_{ri+1}'
            try:
                m = grouped.loc[region, cond]['mean']
                s = grouped.loc[region, cond]['sem']
                means.append(m)
                errs.append(s)
            except KeyError:
                means.append(np.nan)
                errs.append(np.nan)

        offset = (ci - 1) * width
        ax.bar(x_pos + offset, means, width, label=cond, color=colors[cond], alpha=0.8, edgecolor='black', linewidth=0.5)
        ax.errorbar(x_pos + offset, means, yerr=errs, fmt='none', c='black', capsize=3, linewidth=0.8)

    ax.set_title(title, fontsize=11)
    ax.set_xlabel('Region')
    ax.set_ylabel(var.replace('mean_', '').replace('_', ' ').title())
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['R1', 'R2', 'R3', 'R4'])
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
fig.savefig(f'{OUTPUT_DIR}/figures.png', dpi=150, bbox_inches='tight')
log(f"Bar chart figures saved to {OUTPUT_DIR}/figures.png")
plt.close(fig)

# Figure 2: Violin plots
fig2, axes2 = plt.subplots(2, 3, figsize=(18, 10))
fig2.suptitle('Distribution of Calcium Response Variables', fontsize=14, fontweight='bold')

for idx, (var, title) in enumerate(vars_titles):
    ax = axes2[idx // 3, idx % 3]

    data_by_group = []
    labels = []
    for region in sorted(df['anatomical_region_id'].cat.categories):
        for cond in df['condition'].cat.categories:
            subset = df[(df['anatomical_region_id'] == region) & (df['condition'] == cond)][var]
            if len(subset) > 0:
                data_by_group.append(subset.values)
                labels.append(f"{region}\n{cond.replace('_', ' ')}")
            else:
                data_by_group.append([])
                labels.append(f"{region}\n{cond.replace('_', ' ')}\n(n/a)")

    parts = ax.violinplot(data_by_group, showmeans=False, showmedians=True)
    for i, pc in enumerate(parts['bodies']):
        region_idx = i // 3
        region_name = sorted(df['anatomical_region_id'].cat.categories)[region_idx]
        pc.set_facecolor(region_colors_map.get(region_name, 'gray'))
        pc.set_alpha(0.6)

    for partname in ['cbars', 'cmins', 'cmaxes', 'cmedians']:
        if partname in parts:
            vp = parts[partname]
            if hasattr(vp, 'get_edgecolor'):
                vp.set_edgecolor('black')
                vp.set_linewidth(1)

    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=7)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(var.replace('mean_', '').replace('_', ' ').title())

    for i, group_data in enumerate(data_by_group):
        if len(group_data) > 0:
            ax.text(i + 1, ax.get_ylim()[1] * 0.95, f'n={len(group_data)}',
                   ha='center', va='top', fontsize=6, color='gray')

plt.tight_layout()
fig2.savefig(f'{OUTPUT_DIR}/figures_violin.png', dpi=150, bbox_inches='tight')
log(f"Violin figures saved to {OUTPUT_DIR}/figures_violin.png")
plt.close(fig2)

# Figure 3: Batch effect visualization
fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5))
fig3.suptitle('Batch Effect Analysis', fontsize=14, fontweight='bold')

batch_amp = df.groupby('recording_batch_id')['mean_amplitude_dff0'].agg(['mean', 'std', 'count'])
batch_amp = batch_amp.sort_index()
axes3[0].bar(range(len(batch_amp)), batch_amp['mean'], yerr=batch_amp['std'],
             color='steelblue', alpha=0.7, edgecolor='black')
axes3[0].set_xticks(range(len(batch_amp)))
axes3[0].set_xticklabels([f'B{i+1}' for i in range(len(batch_amp))], rotation=45)
axes3[0].set_ylabel('Mean Amplitude (dF/F0)')
axes3[0].set_title('Batch Means ± SD (Amplitude)')
axes3[0].grid(axis='y', alpha=0.3)

batch_ttp = df.groupby('recording_batch_id')['mean_time_to_peak_s'].agg(['mean', 'std', 'count'])
batch_ttp = batch_ttp.sort_index()
axes3[1].bar(range(len(batch_ttp)), batch_ttp['mean'], yerr=batch_ttp['std'],
             color='darkorange', alpha=0.7, edgecolor='black')
axes3[1].set_xticks(range(len(batch_ttp)))
axes3[1].set_xticklabels([f'B{i+1}' for i in range(len(batch_ttp))], rotation=45)
axes3[1].set_ylabel('Mean Time to Peak (s)')
axes3[1].set_title('Batch Means ± SD (Time to Peak)')
axes3[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
fig3.savefig(f'{OUTPUT_DIR}/figures_batch.png', dpi=150, bbox_inches='tight')
log(f"Batch effect figures saved to {OUTPUT_DIR}/figures_batch.png")
plt.close(fig3)

# ============================================================
# 6. RESULTS SUMMARY CSV
# ============================================================
log("\n" + "=" * 80)
log("SECTION 6: RESULTS SUMMARY")
log("=" * 80)

results_rows = []

def add_result(model_name, variable, contrast, effect_size, se, ci_lower, ci_upper, p_value, note=""):
    results_rows.append({
        'model': model_name,
        'variable': variable,
        'contrast': contrast,
        'effect_size': round(effect_size, 6),
        'SE': round(se, 6),
        'CI_lower': round(ci_lower, 6),
        'CI_upper': round(ci_upper, 6),
        'p_value': round(p_value, 10) if not np.isnan(p_value) and p_value > 0 else '<0.00000001',
        'note': note
    })

# From Model 1a (amplitude additive, all data)
if ok_1a and result_1a is not None:
    log("\nExtracting results from Model 1a (Amplitude additive, all data)...")
    for row_data in extract_fe_params(result_1a):
        param = row_data['param']
        if param == 'Intercept':
            continue
        add_result('1a-Amplitude-additive-all', 'amplitude', param,
                  row_data['coef'], row_data['se'], row_data['ci_lower'],
                  row_data['ci_upper'], row_data['p_value'], 'All 819 cells, additive model')

# From Model 1b (amplitude interaction, regions 1+2)
if ok_1b and result_1b is not None:
    log("Extracting results from Model 1b (Amplitude interaction, regions 1+2)...")
    for row_data in extract_fe_params(result_1b):
        param = row_data['param']
        if param == 'Intercept':
            continue
        add_result('1b-Amplitude-interaction-R12', 'amplitude', param,
                  row_data['coef'], row_data['se'], row_data['ci_lower'],
                  row_data['ci_upper'], row_data['p_value'], 'Regions 1+2 only')

# From Model 1c (amplitude interaction, baseline, all regions)
if ok_1c and result_1c is not None:
    log("Extracting results from Model 1c (Amplitude interaction, baseline, all regions)...")
    for row_data in extract_fe_params(result_1c):
        param = row_data['param']
        if param == 'Intercept':
            continue
        add_result('1c-Amplitude-interaction-baseline', 'amplitude', param,
                  row_data['coef'], row_data['se'], row_data['ci_lower'],
                  row_data['ci_upper'], row_data['p_value'], 'Baseline conditions, all regions')

# From Model 2a (time to peak additive)
if ok_2a and result_2a is not None:
    log("Extracting results from Model 2a (TimeToPeak additive, all data)...")
    for row_data in extract_fe_params(result_2a):
        param = row_data['param']
        if param == 'Intercept':
            continue
        add_result('2a-TimeToPeak-additive-all', 'time_to_peak', param,
                  row_data['coef'], row_data['se'], row_data['ci_lower'],
                  row_data['ci_upper'], row_data['p_value'], 'All 819 cells, additive model')

# From Model 2b (time to peak interaction, regions 1+2)
if ok_2b and result_2b is not None:
    log("Extracting results from Model 2b (TimeToPeak interaction, regions 1+2)...")
    for row_data in extract_fe_params(result_2b):
        param = row_data['param']
        if param == 'Intercept':
            continue
        add_result('2b-TimeToPeak-interaction-R12', 'time_to_peak', param,
                  row_data['coef'], row_data['se'], row_data['ci_lower'],
                  row_data['ci_upper'], row_data['p_value'], 'Regions 1+2 only')

# Pairwise contrasts for amplitude (regions 1+2)
log("\nPairwise condition contrasts (amplitude, regions 1+2):")
for cond_pair in [('baseline', 'neural_activity_blocked'),
                   ('baseline', 'receptor_stimulated'),
                   ('neural_activity_blocked', 'receptor_stimulated')]:
    c1, c2 = cond_pair
    sub = df_full_cond[df_full_cond['condition'].isin([c1, c2])]
    g1 = sub[sub['condition'] == c1]['mean_amplitude_dff0']
    g2 = sub[sub['condition'] == c2]['mean_amplitude_dff0']
    t_stat, p_val = stats.ttest_ind(g1, g2)
    diff = g1.mean() - g2.mean()
    se_diff = np.sqrt(g1.sem()**2 + g2.sem()**2)
    ci_l = diff - 1.96 * se_diff
    ci_u = diff + 1.96 * se_diff
    add_result('Pairwise-t-test', 'amplitude', f'{c1} vs {c2}',
              diff, se_diff, ci_l, ci_u, p_val, 'Regions 1+2')

# Pairwise contrasts for time to peak (regions 1+2)
log("Pairwise condition contrasts (time to peak, regions 1+2):")
for cond_pair in [('baseline', 'neural_activity_blocked'),
                   ('baseline', 'receptor_stimulated'),
                   ('neural_activity_blocked', 'receptor_stimulated')]:
    c1, c2 = cond_pair
    sub = df_full_cond[df_full_cond['condition'].isin([c1, c2])]
    g1 = sub[sub['condition'] == c1]['mean_time_to_peak_s']
    g2 = sub[sub['condition'] == c2]['mean_time_to_peak_s']
    t_stat, p_val = stats.ttest_ind(g1, g2)
    diff = g1.mean() - g2.mean()
    se_diff = np.sqrt(g1.sem()**2 + g2.sem()**2)
    ci_l = diff - 1.96 * se_diff
    ci_u = diff + 1.96 * se_diff
    add_result('Pairwise-t-test', 'time_to_peak', f'{c1} vs {c2}',
              diff, se_diff, ci_l, ci_u, p_val, 'Regions 1+2')

# Save results
results_df = pd.DataFrame(results_rows)
results_df.to_csv(f'{OUTPUT_DIR}/results_summary.csv', index=False)
log(f"\nResults summary saved to {OUTPUT_DIR}/results_summary.csv")
log(f"Total registered contrasts: {len(results_df)}")

# Print summary table
log("\n--- Results Summary Table ---")
log(results_df.to_string(index=False))

# ============================================================
# 7. DESIGN CONSTRAINTS DOCUMENTATION
# ============================================================
log("\n" + "=" * 80)
log("SECTION 7: DESIGN CONSTRAINTS AND ESTIMABILITY ANALYSIS")
log("=" * 80)

log("""
DESIGN CONSTRAINTS:
==================

1. Region_3 ONLY has receptor_stimulated condition.
   - CANNOT estimate: region_3 condition effects (no within-region comparison)
   - CANNOT estimate: region_3 x condition interaction
   - CAN estimate: receptor_stimulated effect in region_3 vs other regions (confounded with region)

2. Region_4 ONLY has baseline + neural_activity_blocked conditions.
   - CANNOT estimate: region_4 receptor_stimulated effect
   - CANNOT estimate: region_4 x receptor_stimulated interaction
   - CAN estimate: region_4 condition effects (baseline vs blocked)

3. Regions 1 and 2 have ALL THREE conditions.
   - CAN fully estimate: region_1 and region_2 x condition interactions
   - CAN estimate: all pairwise condition contrasts within regions 1 and 2
   - CAN estimate: region_1 vs region_2 differences within each condition

4. Overall condition effects are PARTIALLY confounded with region effects.
   - The receptor_stimulated condition appears ONLY in regions 1, 2, and 3
   - Any observed difference between receptor_stimulated and baseline could reflect:
     (a) True condition effect, OR
     (b) Region-specific baseline differences, OR
     (c) Region x condition interaction

5. Estimable contrasts:
   - Within regions 1+2: all 3 condition pairwise comparisons YES
   - Across all regions: baseline vs neural_activity_blocked YES
   - Region_1 vs Region_2 within each condition YES
   - Region_3 vs others: ONLY for receptor_stimulated (confounded) NO
   - Region_4 vs others: ONLY for baseline and neural_activity_blocked YES

6. Non-estimable contrasts:
   - Region_3 x condition interaction (no variation in condition within region_3)
   - Region_4 x receptor_stimulated interaction (no receptor_stimulated data in region_4)
   - Pure main effect of region (confounded with condition distribution)
   - Pure main effect of condition (confounded with region distribution)
""")

# ============================================================
# 8. WRITE FINAL OUTPUT FILES
# ============================================================
log("\n" + "=" * 80)
log("FINAL OUTPUT FILES")
log("=" * 80)

with open(f'{OUTPUT_DIR}/model_output.txt', 'w') as f:
    f.write(model_output_log.getvalue())

log(f"\nAll files written to {OUTPUT_DIR}/")
log("  - analysis.py (this script)")
log(f"  - results_summary.csv ({len(results_df)} contrast records)")
log(f"  - figures.png (6-panel bar chart)")
log(f"  - figures_violin.png (6-panel violin plot)")
log(f"  - figures_batch.png (batch effect diagnostics)")
log(f"  - model_output.txt (full model output log)")

log("\n" + "=" * 80)
log("ANALYSIS COMPLETE")
log("=" * 80)
