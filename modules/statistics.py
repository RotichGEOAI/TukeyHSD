#!/usr/bin/env python3
"""
Turkey HSD Analyzer v2.0 - Core Statistical Functions
======================================================
Fixed for scipy 1.18.0 bartlett() NaN-to-integer bug.
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
import warnings

warnings.filterwarnings('ignore')


def _safe_bartlett(*groups):
    """Wrapper around scipy.stats.bartlett that handles the scipy>=1.15 int-dtype bug.

    The bug: scipy's bartlett() uses array-api-extra's at().set() which fails
    when trying to set NaN on an integer array. We convert all groups to float64.
    """
    float_groups = [np.asarray(g, dtype=np.float64) for g in groups]
    return stats.bartlett(*float_groups)


def perform_anova(df, dependent_var, independent_var):
    """Perform One-Way ANOVA."""
    df = df.copy()
    if pd.api.types.is_numeric_dtype(df[independent_var]) and df[independent_var].nunique() > 5:
        binned_name = f"{independent_var}_binned"
        df[binned_name] = pd.qcut(df[independent_var], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        independent_var = binned_name

    groups = [group[dependent_var].dropna().values for _, group in df.groupby(independent_var, observed=True)]
    if len(groups) < 2:
        raise ValueError(f"Need at least 2 groups for ANOVA. Found {len(groups)}.")

    f_stat, p_value = stats.f_oneway(*groups)
    grand_mean = np.mean(df[dependent_var].dropna())
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
    ss_within = sum(sum((x - np.mean(g)) ** 2 for x in g) for g in groups)
    ss_total = ss_between + ss_within
    df_between = len(groups) - 1
    df_within = len(df) - len(groups)
    ms_between = ss_between / df_between if df_between > 0 else 0
    ms_within = ss_within / df_within if df_within > 0 else 0
    eta_squared = ss_between / ss_total if ss_total > 0 else 0.0
    omega_squared = (ss_between - df_between * ms_within) / (ss_total + ms_within) if ss_total > 0 else 0.0

    group_stats = df.groupby(independent_var, observed=True)[dependent_var].agg(['count', 'mean', 'std', 'min', 'max']).reset_index()
    group_stats['se'] = group_stats['std'] / np.sqrt(group_stats['count'])
    group_stats['ci_lower'] = group_stats['mean'] - 1.96 * group_stats['se']
    group_stats['ci_upper'] = group_stats['mean'] + 1.96 * group_stats['se']

    return {
        'f_statistic': float(f_stat), 'p_value': float(p_value),
        'ss_between': float(ss_between), 'ss_within': float(ss_within), 'ss_total': float(ss_total),
        'df_between': int(df_between), 'df_within': int(df_within), 'df_total': int(len(df) - 1),
        'ms_between': float(ms_between), 'ms_within': float(ms_within),
        'eta_squared': float(eta_squared), 'omega_squared': float(omega_squared),
        'group_stats': group_stats, 'n_groups': len(groups), 'n_total': len(df),
        'significant': p_value < 0.05,
        'independent_var': independent_var, 'dependent_var': dependent_var,
        'groups': df[independent_var].unique()
    }


def perform_tukey_hsd(df, dependent_var, independent_var, alpha=0.05):
    """Perform Tukey's HSD post-hoc test."""
    df = df.copy()
    if pd.api.types.is_numeric_dtype(df[independent_var]) and df[independent_var].nunique() > 5:
        binned_name = f"{independent_var}_binned"
        df[binned_name] = pd.qcut(df[independent_var], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        independent_var = binned_name

    tukey = pairwise_tukeyhsd(endog=df[dependent_var].dropna(), groups=df[independent_var].dropna(), alpha=alpha)
    tukey_df = pd.DataFrame(data=tukey._results_table.data[1:], columns=tukey._results_table.data[0])
    tukey_df['significant'] = tukey_df['reject'].apply(lambda x: 'Yes' if x else 'No')
    cld_results = compact_letter_display(df, dependent_var, independent_var, alpha)

    return {
        'tukey_results': tukey, 'tukey_table': tukey_df, 'cld': cld_results,
        'alpha': alpha, 'independent_var': independent_var, 'dependent_var': dependent_var
    }


def compact_letter_display(df, dependent_var, independent_var, alpha=0.05):
    """Generate Compact Letter Display for mean separation."""
    df = df.copy()
    if pd.api.types.is_numeric_dtype(df[independent_var]) and df[independent_var].nunique() > 5:
        binned_name = f"{independent_var}_binned"
        df[binned_name] = pd.qcut(df[independent_var], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        independent_var = binned_name

    group_means = df.groupby(independent_var, observed=True)[dependent_var].mean().sort_values(ascending=False)
    groups = group_means.index.tolist()

    tukey = pairwise_tukeyhsd(endog=df[dependent_var].dropna(), groups=df[independent_var].dropna(), alpha=alpha)
    sig_matrix = pd.DataFrame(True, index=groups, columns=groups)
    for row in tukey._results_table.data[1:]:
        g1, g2 = row[0], row[1]
        if g1 in groups and g2 in groups:
            sig_matrix.loc[g1, g2] = row[6]
            sig_matrix.loc[g2, g1] = row[6]

    letters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    group_letters = {g: [] for g in groups}
    letter_idx = 0

    for i, g1 in enumerate(groups):
        if not group_letters[g1]:
            current_letter = letters[letter_idx]
            letter_idx += 1
            group_letters[g1].append(current_letter)
            for g2 in groups[i+1:]:
                if not sig_matrix.loc[g1, g2] and not group_letters[g2]:
                    can_assign = True
                    for g_check in groups:
                        if current_letter in group_letters.get(g_check, []):
                            if sig_matrix.loc[g2, g_check]:
                                can_assign = False
                                break
                    if can_assign:
                        group_letters[g2].append(current_letter)

    return pd.DataFrame({
        'group': groups,
        'mean': [group_means[g] for g in groups],
        'letters': [''.join(group_letters[g]) for g in groups]
    })


def _q_critical(alpha, k, df):
    """Studentized range critical value using scipy.studentized_range (scipy>=1.7)."""
    try:
        from scipy.stats import studentized_range
        return studentized_range.ppf(1 - alpha, k, df)
    except Exception:
        return stats.t.ppf(1 - alpha / (k * (k - 1)), df) * np.sqrt(2)


def duncans_mrt(df, dependent_var, independent_var, alpha=0.05):
    """Duncan's Multiple Range Test."""
    df = df.copy()
    if pd.api.types.is_numeric_dtype(df[independent_var]) and df[independent_var].nunique() > 5:
        binned_name = f"{independent_var}_binned"
        df[binned_name] = pd.qcut(df[independent_var], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        independent_var = binned_name

    groups_data = {name: group[dependent_var].dropna().values for name, group in df.groupby(independent_var, observed=True)}
    group_names = list(groups_data.keys())
    k = len(group_names)
    all_values = np.concatenate(list(groups_data.values()))
    n_total = len(all_values)
    ss_within = sum(np.sum((g - np.mean(g))**2) for g in groups_data.values())
    df_error = n_total - k
    mse = ss_within / df_error if df_error > 0 else 0
    group_means = {name: np.mean(values) for name, values in groups_data.items()}
    sorted_groups = sorted(group_means.items(), key=lambda x: x[1], reverse=True)

    results = []
    for i, (g1, mean1) in enumerate(sorted_groups):
        for j, (g2, mean2) in enumerate(sorted_groups[i+1:], start=i+1):
            rank_diff = j - i + 1
            n1 = len(groups_data[g1])
            n2 = len(groups_data[g2])
            se_diff = np.sqrt(mse * (1/n1 + 1/n2) / 2)
            try:
                q_crit = _q_critical(alpha, rank_diff, df_error) / np.sqrt(2)
            except:
                q_crit = stats.t.ppf(1 - alpha/2, df_error) * np.sqrt(2)
            critical_diff = q_crit * se_diff
            observed_diff = abs(mean1 - mean2)
            results.append({
                'group1': g1, 'group2': g2, 'mean1': mean1, 'mean2': mean2,
                'difference': observed_diff, 'critical_value': critical_diff,
                'significant': 'Yes' if observed_diff > critical_diff else 'No',
                'rank_difference': rank_diff
            })
    return pd.DataFrame(results)


def fishers_lsd(df, dependent_var, independent_var, alpha=0.05):
    """Fisher's Least Significant Difference test."""
    df = df.copy()
    if pd.api.types.is_numeric_dtype(df[independent_var]) and df[independent_var].nunique() > 5:
        binned_name = f"{independent_var}_binned"
        df[binned_name] = pd.qcut(df[independent_var], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        independent_var = binned_name

    groups_data = {name: group[dependent_var].dropna().values for name, group in df.groupby(independent_var, observed=True)}
    group_names = list(groups_data.keys())
    k = len(group_names)
    n_total = sum(len(v) for v in groups_data.values())
    ss_within = sum(np.sum((g - np.mean(g))**2) for g in groups_data.values())
    df_error = n_total - k
    mse = ss_within / df_error if df_error > 0 else 0
    group_means = {name: np.mean(values) for name, values in groups_data.items()}
    t_crit = stats.t.ppf(1 - alpha/2, df_error)

    results = []
    for i, (g1, mean1) in enumerate(group_means.items()):
        for g2, mean2 in list(group_means.items())[i+1:]:
            n1 = len(groups_data[g1])
            n2 = len(groups_data[g2])
            se_diff = np.sqrt(mse * (1/n1 + 1/n2))
            lsd = t_crit * se_diff
            diff = abs(mean1 - mean2)
            t_stat = diff / se_diff if se_diff > 0 else 0
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df_error))
            results.append({
                'group1': g1, 'group2': g2, 'mean1': mean1, 'mean2': mean2,
                'difference': diff, 'lsd_value': lsd, 't_statistic': t_stat,
                'p_value': p_value, 'significant': 'Yes' if diff > lsd else 'No', 'alpha': alpha
            })
    return pd.DataFrame(results)


def snk_test(df, dependent_var, independent_var, alpha=0.05):
    """Student-Newman-Keuls test."""
    df = df.copy()
    if pd.api.types.is_numeric_dtype(df[independent_var]) and df[independent_var].nunique() > 5:
        binned_name = f"{independent_var}_binned"
        df[binned_name] = pd.qcut(df[independent_var], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        independent_var = binned_name

    groups_data = {name: group[dependent_var].dropna().values for name, group in df.groupby(independent_var, observed=True)}
    group_names = list(groups_data.keys())
    k = len(group_names)
    n_total = sum(len(v) for v in groups_data.values())
    ss_within = sum(np.sum((g - np.mean(g))**2) for g in groups_data.values())
    df_error = n_total - k
    mse = ss_within / df_error if df_error > 0 else 0
    group_means = {name: np.mean(values) for name, values in groups_data.items()}
    sorted_groups = sorted(group_means.items(), key=lambda x: x[1], reverse=True)

    results = []
    for i, (g1, mean1) in enumerate(sorted_groups):
        for j, (g2, mean2) in enumerate(sorted_groups[i+1:], start=i+1):
            rank_diff = j - i + 1
            n1 = len(groups_data[g1])
            n2 = len(groups_data[g2])
            se_diff = np.sqrt(mse * (1/n1 + 1/n2) / 2)
            try:
                q_crit = _q_critical(alpha, rank_diff, df_error) / np.sqrt(2)
            except:
                q_crit = stats.t.ppf(1 - alpha/2, df_error)
            critical_diff = q_crit * se_diff
            observed_diff = abs(mean1 - mean2)
            results.append({
                'group1': g1, 'group2': g2, 'mean1': mean1, 'mean2': mean2,
                'difference': observed_diff, 'critical_value': critical_diff,
                'significant': 'Yes' if observed_diff > critical_diff else 'No',
                'rank_difference': rank_diff
            })
    return pd.DataFrame(results)


def scheffe_test(df, dependent_var, independent_var, alpha=0.05):
    """Scheffe's test for mean separation."""
    df = df.copy()
    if pd.api.types.is_numeric_dtype(df[independent_var]) and df[independent_var].nunique() > 5:
        binned_name = f"{independent_var}_binned"
        df[binned_name] = pd.qcut(df[independent_var], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        independent_var = binned_name

    groups_data = {name: group[dependent_var].dropna().values for name, group in df.groupby(independent_var, observed=True)}
    group_names = list(groups_data.keys())
    k = len(group_names)
    n_total = sum(len(v) for v in groups_data.values())
    ss_within = sum(np.sum((g - np.mean(g))**2) for g in groups_data.values())
    df_error = n_total - k
    mse = ss_within / df_error if df_error > 0 else 0
    group_means = {name: np.mean(values) for name, values in groups_data.items()}
    f_crit = stats.f.ppf(1 - alpha, k - 1, df_error)
    scheffe_crit = np.sqrt((k - 1) * f_crit)

    results = []
    for i, (g1, mean1) in enumerate(group_means.items()):
        for g2, mean2 in list(group_means.items())[i+1:]:
            n1 = len(groups_data[g1])
            n2 = len(groups_data[g2])
            se_diff = np.sqrt(mse * (1/n1 + 1/n2))
            critical_diff = scheffe_crit * se_diff
            observed_diff = abs(mean1 - mean2)
            f_stat = (observed_diff ** 2) / (se_diff ** 2) if se_diff > 0 else 0
            p_value = 1 - stats.f.cdf(f_stat, k - 1, df_error)
            results.append({
                'group1': g1, 'group2': g2, 'mean1': mean1, 'mean2': mean2,
                'difference': observed_diff, 'critical_value': critical_diff,
                'f_statistic': f_stat, 'p_value': p_value,
                'significant': 'Yes' if observed_diff > critical_diff else 'No'
            })
    return pd.DataFrame(results)


def perform_mean_separation(df, dependent_var, independent_var, method='tukey', alpha=0.05):
    """Perform mean separation using specified method."""
    methods = {
        'tukey': perform_tukey_hsd, 'duncan': duncans_mrt,
        'lsd': fishers_lsd, 'snk': snk_test, 'scheffe': scheffe_test
    }
    if method not in methods:
        raise ValueError(f"Unknown method: {method}")

    result = methods[method](df, dependent_var, independent_var, alpha)
    if method == 'tukey':
        cld = result['cld']
        pairwise_table = result['tukey_table']
    else:
        cld = compact_letter_display(df, dependent_var, independent_var, alpha)
        pairwise_table = result

    return {
        'method': method, 'alpha': alpha,
        'pairwise_table': pairwise_table, 'cld': cld,
        'dependent_var': dependent_var, 'independent_var': independent_var
    }


def perform_two_way_anova(df, dependent_var, factor_a, factor_b):
    """Perform Two-Way ANOVA with interaction effects."""
    df = df.copy()
    for factor in [factor_a, factor_b]:
        if pd.api.types.is_numeric_dtype(df[factor]) and df[factor].nunique() > 5:
            binned_name = f"{factor}_binned"
            df[binned_name] = pd.qcut(df[factor], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
            if factor == factor_a:
                factor_a = binned_name
            else:
                factor_b = binned_name

    formula = f"{dependent_var} ~ C({factor_a}) + C({factor_b}) + C({factor_a}):C({factor_b})"
    model = ols(formula, data=df).fit()
    anova_table = anova_lm(model, typ=2)

    results = {
        'anova_table': anova_table, 'model_summary': model.summary(),
        'r_squared': model.rsquared, 'adj_r_squared': model.rsquared_adj,
        'fvalue': model.fvalue, 'f_pvalue': model.f_pvalue,
        'dependent_var': dependent_var, 'factor_a': factor_a, 'factor_b': factor_b,
        'n_observations': int(model.nobs)
    }

    for key, label in [(f"C({factor_a})", 'factor_a'), (f"C({factor_b})", 'factor_b')]:
        if key in anova_table.index:
            row = anova_table.loc[key]
            results[label] = {
                'name': factor_a if label == 'factor_a' else factor_b,
                'f_statistic': row['F'], 'p_value': row['PR(>F)'],
                'significant': row['PR(>F)'] < 0.05,
                'sum_sq': row['sum_sq'], 'mean_sq': row['mean_sq'], 'df': row['df']
            }

    interaction_key = f"C({factor_a}):C({factor_b})"
    if interaction_key in anova_table.index:
        row = anova_table.loc[interaction_key]
        results['interaction'] = {
            'f_statistic': row['F'], 'p_value': row['PR(>F)'],
            'significant': row['PR(>F)'] < 0.05,
            'sum_sq': row['sum_sq'], 'mean_sq': row['mean_sq'], 'df': row['df']
        }

    if 'Residual' in anova_table.index:
        row = anova_table.loc['Residual']
        results['residual'] = {'sum_sq': row['sum_sq'], 'mean_sq': row['mean_sq'], 'df': row['df']}

    cell_means = df.groupby([factor_a, factor_b], observed=True)[dependent_var].agg(['mean', 'std', 'count']).reset_index()
    cell_means['se'] = cell_means['std'] / np.sqrt(cell_means['count'])
    marginal_a = df.groupby(factor_a, observed=True)[dependent_var].agg(['mean', 'std', 'count']).reset_index()
    marginal_a['se'] = marginal_a['std'] / np.sqrt(marginal_a['count'])
    marginal_b = df.groupby(factor_b, observed=True)[dependent_var].agg(['mean', 'std', 'count']).reset_index()
    marginal_b['se'] = marginal_b['std'] / np.sqrt(marginal_b['count'])

    results['cell_means'] = cell_means
    results['marginal_a'] = marginal_a
    results['marginal_b'] = marginal_b
    return results


def simple_effects_analysis(df, dependent_var, factor_a, factor_b, alpha=0.05):
    """Simple effects analysis for Two-Way ANOVA."""
    df = df.copy()
    for factor in [factor_a, factor_b]:
        if pd.api.types.is_numeric_dtype(df[factor]) and df[factor].nunique() > 5:
            binned_name = f"{factor}_binned"
            df[binned_name] = pd.qcut(df[factor], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
            if factor == factor_a:
                factor_a = binned_name
            else:
                factor_b = binned_name

    simple_a_results = []
    for level_b in df[factor_b].unique():
        subset = df[df[factor_b] == level_b]
        groups = [group[dependent_var].dropna().values for _, group in subset.groupby(factor_a, observed=True)]
        if len(groups) >= 2:
            f_stat, p_value = stats.f_oneway(*groups)
            simple_a_results.append({
                f'{factor_b}_level': level_b, 'f_statistic': f_stat,
                'p_value': p_value, 'significant': p_value < alpha, 'n': len(subset)
            })

    simple_b_results = []
    for level_a in df[factor_a].unique():
        subset = df[df[factor_a] == level_a]
        groups = [group[dependent_var].dropna().values for _, group in subset.groupby(factor_b, observed=True)]
        if len(groups) >= 2:
            f_stat, p_value = stats.f_oneway(*groups)
            simple_b_results.append({
                f'{factor_a}_level': level_a, 'f_statistic': f_stat,
                'p_value': p_value, 'significant': p_value < alpha, 'n': len(subset)
            })

    return {
        'simple_effects_a': pd.DataFrame(simple_a_results),
        'simple_effects_b': pd.DataFrame(simple_b_results),
        'factor_a': factor_a, 'factor_b': factor_b,
        'dependent_var': dependent_var, 'alpha': alpha
    }


def interaction_plot(df, dependent_var, factor_a, factor_b):
    """Generate data for interaction plot."""
    df = df.copy()
    for factor in [factor_a, factor_b]:
        if pd.api.types.is_numeric_dtype(df[factor]) and df[factor].nunique() > 5:
            binned_name = f"{factor}_binned"
            df[binned_name] = pd.qcut(df[factor], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
            if factor == factor_a:
                factor_a = binned_name
            else:
                factor_b = binned_name

    plot_data = df.groupby([factor_a, factor_b], observed=True)[dependent_var].agg(['mean', 'std', 'count']).reset_index()
    plot_data['se'] = plot_data['std'] / np.sqrt(plot_data['count'])
    plot_data['ci_lower'] = plot_data['mean'] - 1.96 * plot_data['se']
    plot_data['ci_upper'] = plot_data['mean'] + 1.96 * plot_data['se']
    return plot_data


def profile_plot(df, dependent_var, factor_a, factor_b):
    """Generate data for profile plot."""
    return interaction_plot(df, dependent_var, factor_a, factor_b)


def interpret_effect_size(eta_sq):
    """Interpret eta-squared effect size."""
    if eta_sq < 0.01:
        return "Negligible", "The effect is practically meaningless."
    elif eta_sq < 0.06:
        return "Small", "The effect is small but may be meaningful in large samples."
    elif eta_sq < 0.14:
        return "Medium", "The effect is moderate and likely meaningful."
    else:
        return "Large", "The effect is large and practically significant."
