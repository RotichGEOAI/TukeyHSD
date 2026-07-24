#!/usr/bin/env python3
"""
Turkey HSD Analyzer v2.0 - Streamlit Application
=================================================
Fixed for production deployment:
- Syntax errors in try/except blocks resolved
- Bartlett test bug workaround for scipy>=1.15
- Robust error handling throughout

Author: Turkey HSD Analyzer Team
Version: 2.0.1
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from scipy import stats
import warnings
from datetime import datetime

from statistics import (
    perform_anova, perform_tukey_hsd, perform_two_way_anova,
    perform_mean_separation, compact_letter_display,
    simple_effects_analysis, interaction_plot, profile_plot,
    interpret_effect_size, _safe_bartlett
)

warnings.filterwarnings('ignore')

APP_NAME = "Turkey HSD Analyzer"
APP_VERSION = "2.0.1"
APP_ICON = "🔬"

st.set_page_config(
    page_title=f"{APP_NAME} v{APP_VERSION}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/turkey-hsd/analyzer/issues',
        'Report a bug': 'https://github.com/turkey-hsd/analyzer/issues',
        'About': f"**{APP_NAME} v{APP_VERSION}** — Advanced ANOVA & Mean Separation"
    }
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1f77b4; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.2rem; color: #666; margin-bottom: 2rem; }
    .metric-card { background-color: #f0f2f6; border-radius: 10px; padding: 1rem; border-left: 4px solid #1f77b4; }
    .success-box { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .info-box { background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .warning-box { background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .error-box { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .footer { text-align: center; color: #666; padding: 1rem; font-size: 0.9rem; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    defaults = {'data': None, 'cleaned_data': None, 'analysis_results': {}, 'last_analysis': None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


def clean_column_names(df):
    df = df.copy()
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(' ', '_', regex=False)
                  .str.replace('-', '_', regex=False)
                  .str.replace('[^a-z0-9_]', '', regex=True))
    return df


def detect_data_types(df):
    df = df.copy()
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='raise')
            continue
        except (ValueError, TypeError):
            pass
        try:
            df[col] = pd.to_datetime(df[col], errors='raise')
            continue
        except (ValueError, TypeError):
            pass
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio < 0.1 and df[col].nunique() < 50:
            df[col] = df[col].astype('category')
    return df


def handle_missing_values(df):
    df = df.copy()
    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col].fillna(df[col].median(), inplace=True)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col].fillna(method='ffill', inplace=True)
            df[col].fillna(method='bfill', inplace=True)
        else:
            mode_val = df[col].mode()
            if len(mode_val) > 0:
                df[col].fillna(mode_val[0], inplace=True)
            else:
                df[col].fillna('Unknown', inplace=True)
    return df


def render_sidebar():
    with st.sidebar:
        st.markdown(f"## {APP_ICON} {APP_NAME}")
        st.markdown(f"<p style='color: #666;'>v{APP_VERSION}</p>", unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("### 📁 Data Import")
        uploaded_file = st.file_uploader(
            "Upload your data file",
            type=['csv', 'txt', 'xlsx', 'xls'],
            help="Supported: CSV, TXT, Excel"
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)
                st.session_state.data = df
                st.success(f"✅ Loaded {len(df):,} rows x {len(df.columns)} columns")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

        st.markdown("---")
        st.markdown("### ⚙️ Analysis Type")
        analysis_type = st.selectbox(
            "Select Analysis",
            ["Auto-Detect", "One-Way ANOVA", "Two-Way ANOVA", "Mean Separation", "Descriptive Statistics"],
            help="Choose your statistical analysis method"
        )
        st.markdown("---")
        st.markdown("### 🎨 Visualization")
        plot_theme = st.selectbox("Plot Theme", ["whitegrid", "darkgrid", "white", "dark"], index=0)
        color_palette = st.selectbox("Color Palette", ["viridis", "plasma", "Set1", "Set2", "tab10", "husl"], index=4)
        sns.set_style(plot_theme)
        st.markdown("---")
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.clear()
            init_session_state()
            st.rerun()
        st.markdown("<div class='footer'>Built with Streamlit</div>", unsafe_allow_html=True)
    return analysis_type, color_palette


def render_welcome_screen():
    st.markdown(f'<p class="main-header">{APP_ICON} {APP_NAME}</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Advanced ANOVA & Mean Separation Analysis Platform</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class="metric-card"><h3>📊 One-Way ANOVA</h3><p>Compare means across multiple groups with automatic post-hoc testing using Tukey HSD.</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="metric-card"><h3>🔀 Two-Way ANOVA</h3><p>Analyze two factors simultaneously with interaction effects and simple effects analysis.</p></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="metric-card"><h3>🔤 Mean Separation</h3><p>Multiple comparison methods: Tukey, Duncan, Fisher LSD, SNK, Scheffe with CLD.</p></div>""", unsafe_allow_html=True)

    st.info("👈 Upload a data file to begin analysis, or generate sample data below.")
    st.markdown("### 🧪 Sample Data")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Agriculture Data", use_container_width=True):
            np.random.seed(42)
            df = pd.DataFrame({
                'fertilizer': np.repeat(['Control', 'NPK', 'Organic', 'Biochar'], 15),
                'yield_kg': np.concatenate([
                    np.random.normal(45, 3, 15), np.random.normal(52, 3, 15),
                    np.random.normal(48, 3, 15), np.random.normal(55, 3, 15)
                ]),
                'soil_type': np.random.choice(['Clay', 'Sandy', 'Loam'], 60),
                'replication': list(range(1, 16)) * 4
            })
            st.session_state.data = df
            st.rerun()
    with col2:
        if st.button("Generate Clinical Data", use_container_width=True):
            np.random.seed(42)
            df = pd.DataFrame({
                'treatment': np.repeat(['Placebo', 'Drug_A', 'Drug_B', 'Drug_C'], 20),
                'blood_pressure': np.concatenate([
                    np.random.normal(140, 8, 20), np.random.normal(128, 7, 20),
                    np.random.normal(125, 7, 20), np.random.normal(130, 7, 20)
                ]),
                'gender': np.random.choice(['Male', 'Female'], 80),
                'age_group': np.random.choice(['Young', 'Middle', 'Senior'], 80)
            })
            st.session_state.data = df
            st.rerun()


def render_data_cleaning(raw_data):
    st.markdown("---")
    st.markdown("## Phase 1: Data Import & Cleaning")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rows", f"{len(raw_data):,}")
    col2.metric("Total Columns", len(raw_data.columns))
    col3.metric("Missing Values", f"{raw_data.isnull().sum().sum():,}")
    col4.metric("Duplicate Rows", raw_data.duplicated().sum())

    with st.expander("🔍 Raw Data Preview", expanded=False):
        st.dataframe(raw_data.head(20), use_container_width=True)

    with st.spinner("🧹 Cleaning data..."):
        cleaned_data = raw_data.copy()
        cleaned_data = clean_column_names(cleaned_data)
        cleaned_data = detect_data_types(cleaned_data)
        cleaned_data = cleaned_data.drop_duplicates()
        cleaned_data = handle_missing_values(cleaned_data)
        st.session_state.cleaned_data = cleaned_data
    st.markdown('<div class="success-box">✅ Data cleaning complete!</div>', unsafe_allow_html=True)
    return cleaned_data


def render_data_profiling(cleaned_data, numeric_cols, categorical_cols, color_palette):
    st.markdown("---")
    st.markdown("## Phase 2: Data Profiling")
    tab1, tab2, tab3 = st.tabs(["📋 Overview", "📊 Distributions", "🔗 Correlations"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Variable Types")
            datetime_cols = cleaned_data.select_dtypes(include=['datetime64']).columns.tolist()
            type_df = pd.DataFrame({
                'Type': ['Numeric', 'Categorical', 'Datetime'],
                'Count': [len(numeric_cols), len(categorical_cols), len(datetime_cols)]
            })
            st.dataframe(type_df, use_container_width=True, hide_index=True)
            if numeric_cols:
                st.markdown("### Numeric Summary")
                st.dataframe(cleaned_data[numeric_cols].describe().T, use_container_width=True)
        with col2:
            if categorical_cols:
                st.markdown("### Categorical Summary")
                for col in categorical_cols[:5]:
                    st.markdown(f"**{col}**")
                    st.bar_chart(cleaned_data[col].value_counts().head(5))

    with tab2:
        if numeric_cols:
            selected = st.selectbox("Select variable", numeric_cols)
            col1, col2 = st.columns(2)
            with col1:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.histplot(cleaned_data[selected], kde=True, color='steelblue', ax=ax)
                ax.set_title(f'Distribution of {selected}')
                st.pyplot(fig)
            with col2:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.boxplot(y=cleaned_data[selected], color='lightcoral', ax=ax)
                ax.set_title(f'Box Plot of {selected}')
                st.pyplot(fig)
            sample = cleaned_data[selected].dropna()
            if len(sample) > 5000:
                sample = sample.sample(5000, random_state=42)
            stat, p = stats.shapiro(sample)
            dist_type = 'Normal' if p > 0.05 else 'Non-normal'
            st.info(f"**Shapiro-Wilk**: Statistic={stat:.4f}, p={p:.4f} ({dist_type})")

    with tab3:
        if len(numeric_cols) >= 2:
            corr = cleaned_data[numeric_cols].corr()
            fig, ax = plt.subplots(figsize=(12, 10))
            mask = np.triu(np.ones_like(corr, dtype=bool))
            sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap=color_palette, center=0, square=True, ax=ax)
            st.pyplot(fig)


def render_one_way_anova(cleaned_data, numeric_cols, categorical_cols, color_palette):
    st.markdown("---")
    st.markdown("## Phase 3: One-Way ANOVA & Tukey HSD")

    col1, col2 = st.columns(2)
    with col1:
        dep_var = st.selectbox("Dependent Variable", numeric_cols, index=0)
        all_grouping = categorical_cols + [c for c in numeric_cols if c != dep_var]
        ind_var = st.selectbox("Grouping Variable", all_grouping, index=0 if all_grouping else None)
    with col2:
        alpha = st.slider("Significance Level (α)", 0.01, 0.10, 0.05, 0.01)
        show_cld = st.checkbox("Show Compact Letter Display", value=True)
        show_interpretation = st.checkbox("Show Interpretation", value=True)

    if st.button("🚀 Run One-Way ANOVA", type="primary", use_container_width=True):
        with st.spinner("🔬 Running ANOVA and Tukey HSD..."):
            try:
                anova_results = perform_anova(cleaned_data, dep_var, ind_var)
                tukey_results = perform_tukey_hsd(cleaned_data, dep_var, ind_var, alpha)
                st.session_state.analysis_results['one_way'] = {'anova': anova_results, 'tukey': tukey_results}

                # ANOVA Results
                st.markdown("### 1️⃣ ANOVA Results")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("F-Statistic", f"{anova_results['f_statistic']:.4f}")
                c2.metric("P-Value", f"{anova_results['p_value']:.4f}",
                         delta="Significant" if anova_results['significant'] else "Not Significant",
                         delta_color="normal" if anova_results['significant'] else "inverse")
                c3.metric("η²", f"{anova_results['eta_squared']:.4f}")
                c4.metric("ω²", f"{anova_results['omega_squared']:.4f}")
                c5.metric("Groups", anova_results['n_groups'])

                st.markdown("#### ANOVA Table")
                anova_table = pd.DataFrame({
                    'Source': ['Between Groups', 'Within Groups', 'Total'],
                    'SS': [f"{anova_results['ss_between']:.4f}", f"{anova_results['ss_within']:.4f}", f"{anova_results['ss_total']:.4f}"],
                    'df': [anova_results['df_between'], anova_results['df_within'], anova_results['df_total']],
                    'MS': [f"{anova_results['ms_between']:.4f}", f"{anova_results['ms_within']:.4f}", '-'],
                    'F': [f"{anova_results['f_statistic']:.4f}", '-', '-'],
                    'p-value': [f"{anova_results['p_value']:.6f}", '-', '-']
                })
                st.dataframe(anova_table, use_container_width=True, hide_index=True)

                effect_label, effect_desc = interpret_effect_size(anova_results['eta_squared'])
                st.markdown(f'<div class="info-box"><strong>Effect Size:</strong> η² = {anova_results["eta_squared"]:.4f} ({effect_label}) — {effect_desc}</div>', unsafe_allow_html=True)

                if anova_results['significant']:
                    st.markdown('<div class="success-box"><strong>✅ Significant:</strong> At least one group mean differs. Tukey HSD follows.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="warning-box"><strong>⚠️ Not Significant:</strong> No significant differences between group means.</div>', unsafe_allow_html=True)

                # Tukey HSD
                st.markdown("---")
                st.markdown("### 2️⃣ Tukey HSD Post-Hoc Test")
                st.info("Tukey's HSD compares all pairs of group means while controlling family-wise error rate.")

                tukey_df = tukey_results['tukey_table']
                st.dataframe(tukey_df, use_container_width=True)

                sig_pairs = tukey_df[tukey_df['reject'] == True]
                if not sig_pairs.empty:
                    st.markdown("#### 🔍 Significant Pairwise Differences")
                    for _, row in sig_pairs.iterrows():
                        st.markdown(f"- **{row['group1']}** vs **{row['group2']}**: Diff = {row['meandiff']:.4f}, p-adj = {row['p-adj']:.4f}")

                # CLD
                if show_cld:
                    st.markdown("---")
                    st.markdown("### 3️⃣ Compact Letter Display (CLD)")
                    st.info("Groups sharing a letter are NOT significantly different. Groups with different letters ARE significantly different.")
                    cld_df = tukey_results['cld']

                    fig, ax = plt.subplots(figsize=(10, max(4, len(cld_df) * 0.6)))
                    ax.axis('off')
                    table_data = [['Group', 'Mean', 'Letters']]
                    for _, row in cld_df.iterrows():
                        table_data.append([str(row['group']), f"{row['mean']:.4f}", row['letters']])
                    table = ax.table(cellText=table_data, cellLoc='center', loc='center', colWidths=[0.4, 0.3, 0.3])
                    table.auto_set_font_size(False)
                    table.set_fontsize(12)
                    table.scale(1, 2)
                    for i in range(3):
                        table[(0, i)].set_facecolor('#1f77b4')
                        table[(0, i)].set_text_props(weight='bold', color='white')
                    for i in range(1, len(table_data)):
                        table[(i, 2)].set_text_props(weight='bold', color='#d62728')
                    st.pyplot(fig)
                    st.dataframe(cld_df, use_container_width=True, hide_index=True)

                # Visualizations
                st.markdown("---")
                st.markdown("### 📊 Visualizations")
                tab1, tab2, tab3 = st.tabs(["Group Means", "Box Plot", "Tukey Intervals"])

                with tab1:
                    fig, ax = plt.subplots(figsize=(12, 7))
                    group_means = cleaned_data.groupby(anova_results['independent_var'])[dep_var].mean().sort_values(ascending=False)
                    colors = ['#2ecc71' if anova_results['significant'] else '#95a5a6'] * len(group_means)
                    bars = ax.bar(range(len(group_means)), group_means.values, color=colors, alpha=0.8, edgecolor='black')
                    ax.set_xticks(range(len(group_means)))
                    ax.set_xticklabels(group_means.index, rotation=45, ha='right')
                    ax.set_ylabel(f'Mean {dep_var}')
                    ax.set_title(f'Mean {dep_var} by {anova_results["independent_var"]}')
                    ax.grid(axis='y', alpha=0.3)
                    for bar, val in zip(bars, group_means.values):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01*max(group_means.values),
                               f'{val:.2f}', ha='center', va='bottom', fontweight='bold')
                    st.pyplot(fig)

                with tab2:
                    fig, ax = plt.subplots(figsize=(12, 7))
                    sns.boxplot(data=cleaned_data, x=anova_results['independent_var'], y=dep_var, palette=color_palette, ax=ax)
                    ax.set_title(f'{dep_var} Distribution by {anova_results["independent_var"]}')
                    ax.tick_params(axis='x', rotation=45)
                    st.pyplot(fig)

                with tab3:
                    fig, ax = plt.subplots(figsize=(12, 7))
                    tukey_results['tukey_results'].plot_simultaneous(ax=ax)
                    ax.set_title("Tukey HSD Simultaneous Confidence Intervals")
                    ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
                    st.pyplot(fig)

                if show_interpretation:
                    st.markdown("---")
                    st.markdown("### 📝 Interpretation")
                    if anova_results['significant']:
                        st.markdown(f"The One-Way ANOVA revealed a significant effect of **{anova_results['independent_var']}** on **{dep_var}** (F({anova_results['df_between']}, {anova_results['df_within']}) = {anova_results['f_statistic']:.2f}, p = {anova_results['p_value']:.4f}, η² = {anova_results['eta_squared']:.4f}). Post-hoc Tukey HSD identified {len(sig_pairs)} significant pairwise difference(s).")
                    else:
                        st.markdown(f"The One-Way ANOVA found no significant effect of **{anova_results['independent_var']}** on **{dep_var}** (F({anova_results['df_between']}, {anova_results['df_within']}) = {anova_results['f_statistic']:.2f}, p = {anova_results['p_value']:.4f}).")

            except Exception as e:
                st.error(f"❌ Analysis error: {str(e)}")
                st.markdown(f'<div class="error-box"><strong>Error:</strong> {str(e)}</div>', unsafe_allow_html=True)


def render_two_way_anova(cleaned_data, numeric_cols, categorical_cols, color_palette):
    st.markdown("---")
    st.markdown("## Phase 3: Two-Way ANOVA")

    col1, col2 = st.columns(2)
    with col1:
        dep_var = st.selectbox("Dependent Variable", numeric_cols, index=0, key='tw_dep')
        all_factors = categorical_cols + [c for c in numeric_cols if c != dep_var]
        factor_a = st.selectbox("Factor A", all_factors, index=0, key='tw_fa')
    with col2:
        factor_b = st.selectbox("Factor B", [c for c in all_factors if c != factor_a], index=0 if len(all_factors) > 1 else None, key='tw_fb')
        alpha = st.slider("Significance Level (α)", 0.01, 0.10, 0.05, 0.01, key='tw_alpha')
        show_simple_effects = st.checkbox("Show Simple Effects Analysis", value=True)
        show_interpretation = st.checkbox("Show Interpretation", value=True)

    if st.button("🚀 Run Two-Way ANOVA", type="primary", use_container_width=True):
        with st.spinner("🔬 Running Two-Way ANOVA..."):
            try:
                tw_results = perform_two_way_anova(cleaned_data, dep_var, factor_a, factor_b)

                if show_simple_effects and tw_results.get('interaction', {}).get('significant', False):
                    simple_results = simple_effects_analysis(cleaned_data, dep_var, factor_a, factor_b, alpha)
                else:
                    simple_results = None

                st.session_state.analysis_results['two_way'] = {'anova': tw_results, 'simple_effects': simple_results}

                # ANOVA Table
                st.markdown("### 1️⃣ Two-Way ANOVA Table")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("R²", f"{tw_results['r_squared']:.4f}")
                c2.metric("Adj. R²", f"{tw_results['adj_r_squared']:.4f}")
                c3.metric("Model F", f"{tw_results['fvalue']:.4f}")
                c4.metric("Model p", f"{tw_results['f_pvalue']:.4f}")

                anova_df = tw_results['anova_table'].reset_index()
                anova_df.columns = ['Source', 'Sum of Squares', 'df', 'Mean Square', 'F', 'p-value']
                anova_df['Significant'] = anova_df['p-value'].apply(lambda x: '✅ Yes' if x < 0.05 else '❌ No')
                st.dataframe(anova_df, use_container_width=True, hide_index=True)

                # Effects Summary
                st.markdown("---")
                st.markdown("### 2️⃣ Effects Summary")

                if 'factor_a' in tw_results:
                    fa = tw_results['factor_a']
                    color = "success-box" if fa['significant'] else "warning-box"
                    st.markdown(f'<div class="{color}"><strong>Factor A ({fa["name"]}):</strong> F = {fa["f_statistic"]:.4f}, p = {fa["p_value"]:.4f} ({"Significant" if fa["significant"] else "Not Significant"})</div>', unsafe_allow_html=True)

                if 'factor_b' in tw_results:
                    fb = tw_results['factor_b']
                    color = "success-box" if fb['significant'] else "warning-box"
                    st.markdown(f'<div class="{color}"><strong>Factor B ({fb["name"]}):</strong> F = {fb["f_statistic"]:.4f}, p = {fb["p_value"]:.4f} ({"Significant" if fb["significant"] else "Not Significant"})</div>', unsafe_allow_html=True)

                if 'interaction' in tw_results:
                    inter = tw_results['interaction']
                    if inter['significant']:
                        st.markdown(f'<div class="success-box"><strong>⚡ Interaction Effect ({factor_a} × {factor_b}):</strong> F = {inter["f_statistic"]:.4f}, p = {inter["p_value"]:.4f} (SIGNIFICANT — Simple effects analysis recommended)</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="info-box"><strong>Interaction Effect ({factor_a} × {factor_b}):</strong> F = {inter["f_statistic"]:.4f}, p = {inter["p_value"]:.4f} (Not significant — Main effects can be interpreted independently)</div>', unsafe_allow_html=True)

                # Marginal Means
                st.markdown("---")
                st.markdown("### 3️⃣ Marginal Means")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**{factor_a} Marginal Means**")
                    st.dataframe(tw_results['marginal_a'], use_container_width=True, hide_index=True)
                with col2:
                    st.markdown(f"**{factor_b} Marginal Means**")
                    st.dataframe(tw_results['marginal_b'], use_container_width=True, hide_index=True)

                st.markdown("#### Cell Means (Factor A × Factor B)")
                st.dataframe(tw_results['cell_means'], use_container_width=True, hide_index=True)

                # Simple Effects
                if simple_results is not None:
                    st.markdown("---")
                    st.markdown("### 4️⃣ Simple Effects Analysis")
                    st.info("Simple effects examine the effect of one factor at each level of the other factor. This is necessary when the interaction effect is significant.")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Effect of {factor_a} within each level of {factor_b}**")
                        st.dataframe(simple_results['simple_effects_a'], use_container_width=True, hide_index=True)
                    with col2:
                        st.markdown(f"**Effect of {factor_b} within each level of {factor_a}**")
                        st.dataframe(simple_results['simple_effects_b'], use_container_width=True, hide_index=True)

                # Visualizations
                st.markdown("---")
                st.markdown("### 📊 Visualizations")
                tab1, tab2, tab3 = st.tabs(["Interaction Plot", "Profile Plot", "Cell Means Heatmap"])

                with tab1:
                    plot_data = interaction_plot(cleaned_data, dep_var, factor_a, factor_b)
                    fig = px.line(plot_data, x=factor_a, y='mean', color=factor_b,
                                 error_y='se', markers=True,
                                 title=f'Interaction Plot: {dep_var} by {factor_a} and {factor_b}',
                                 labels={'mean': f'Mean {dep_var}', 'se': 'Standard Error'})
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    plot_data = profile_plot(cleaned_data, dep_var, factor_b, factor_a)
                    fig = px.line(plot_data, x=factor_b, y='mean', color=factor_a,
                                 error_y='se', markers=True,
                                 title=f'Profile Plot: {dep_var} by {factor_b} and {factor_a}',
                                 labels={'mean': f'Mean {dep_var}', 'se': 'Standard Error'})
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)

                with tab3:
                    pivot = tw_results['cell_means'].pivot(index=factor_a, columns=factor_b, values='mean')
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.heatmap(pivot, annot=True, fmt='.2f', cmap=color_palette, ax=ax, cbar_kws={'label': f'Mean {dep_var}'})
                    ax.set_title(f'Cell Means Heatmap: {dep_var}')
                    st.pyplot(fig)

                if show_interpretation:
                    st.markdown("---")
                    st.markdown("### 📝 Interpretation")
                    inter_sig = tw_results.get('interaction', {}).get('significant', False)
                    fa_sig = tw_results.get('factor_a', {}).get('significant', False)
                    fb_sig = tw_results.get('factor_b', {}).get('significant', False)

                    if inter_sig:
                        st.markdown(f"The Two-Way ANOVA revealed a **significant interaction effect** between **{factor_a}** and **{factor_b}** (F = {tw_results['interaction']['f_statistic']:.2f}, p = {tw_results['interaction']['p_value']:.4f}). This means the effect of one factor depends on the level of the other factor. Simple effects analysis shows how each factor behaves within levels of the other.")
                    else:
                        parts = []
                        if fa_sig:
                            parts.append(f"**{factor_a}** has a significant main effect")
                        if fb_sig:
                            parts.append(f"**{factor_b}** has a significant main effect")
                        if parts:
                            st.markdown(f"The Two-Way ANOVA found {', and '.join(parts)} on **{dep_var}**, with no significant interaction. The effects can be interpreted independently.")
                        else:
                            st.markdown(f"The Two-Way ANOVA found no significant main effects or interaction on **{dep_var}**.")

            except Exception as e:
                st.error(f"❌ Analysis error: {str(e)}")
                st.markdown(f'<div class="error-box"><strong>Error:</strong> {str(e)}</div>', unsafe_allow_html=True)


def render_mean_separation(cleaned_data, numeric_cols, categorical_cols, color_palette):
    st.markdown("---")
    st.markdown("## Phase 3: Mean Separation Analysis")

    st.info("""
    **Mean Separation Analysis** provides multiple methods for comparing group means after ANOVA.
    - **Tukey HSD**: Conservative, controls family-wise error for ALL pairwise comparisons
    - **Duncan's MRT**: Less conservative, step-down procedure
    - **Fisher's LSD**: Most liberal, equivalent to multiple t-tests (use only after significant ANOVA)
    - **SNK Test**: Middle ground between Tukey and Duncan
    - **Scheffe's Test**: Most conservative, valid for ALL possible contrasts
    """)

    col1, col2 = st.columns(2)
    with col1:
        dep_var = st.selectbox("Dependent Variable", numeric_cols, index=0, key='ms_dep')
        all_grouping = categorical_cols + [c for c in numeric_cols if c != dep_var]
        ind_var = st.selectbox("Grouping Variable", all_grouping, index=0, key='ms_ind')
    with col2:
        method = st.selectbox(
            "Separation Method",
            ['tukey', 'duncan', 'lsd', 'snk', 'scheffe'],
            format_func=lambda x: {
                'tukey': 'Tukey HSD (Conservative)',
                'duncan': "Duncan's MRT (Moderate)",
                'lsd': "Fisher's LSD (Liberal)",
                'snk': 'Student-Newman-Keuls (Moderate)',
                'scheffe': "Scheffe's Test (Most Conservative)"
            }[x]
        )
        alpha = st.slider("Significance Level (α)", 0.01, 0.10, 0.05, 0.01, key='ms_alpha')
        show_cld = st.checkbox("Show Compact Letter Display", value=True)

    if st.button("🚀 Run Mean Separation", type="primary", use_container_width=True):
        with st.spinner(f"🔬 Running {method.upper()} mean separation..."):
            try:
                results = perform_mean_separation(cleaned_data, dep_var, ind_var, method, alpha)
                st.session_state.analysis_results['mean_sep'] = results

                method_info = {
                    'tukey': ('Tukey HSD', 'Controls family-wise error rate for all pairwise comparisons. Best for balanced designs.'),
                    'duncan': ("Duncan's MRT", 'Step-down test with decreasing critical values. More powerful but less conservative than Tukey.'),
                    'lsd': ("Fisher's LSD", 'Least Significant Difference. Most powerful but does NOT control family-wise error. Only use after significant ANOVA.'),
                    'snk': ('SNK Test', 'Student-Newman-Keuls step-down procedure. Middle ground between Tukey and Duncan.'),
                    'scheffe': ("Scheffe's Test", 'Most conservative. Controls error rate for ALL possible contrasts, not just pairwise.')
                }
                name, desc = method_info[method]
                st.markdown(f'<div class="info-box"><strong>{name}</strong><br>{desc}</div>', unsafe_allow_html=True)

                # Pairwise Comparisons
                st.markdown("### 1️⃣ Pairwise Comparisons")
                pairwise_df = results['pairwise_table']
                st.dataframe(pairwise_df, use_container_width=True)

                if method == 'tukey':
                    sig_count = len(pairwise_df[pairwise_df['reject'] == True])
                else:
                    sig_count = len(pairwise_df[pairwise_df['significant'] == 'Yes'])
                st.markdown(f"**Significant pairs: {sig_count} / {len(pairwise_df)}**")

                # CLD
                if show_cld:
                    st.markdown("---")
                    st.markdown("### 2️⃣ Compact Letter Display (CLD)")
                    st.info("Groups sharing a letter are NOT significantly different (p > α). Groups with different letters ARE significantly different.")
                    cld_df = results['cld']

                    fig, ax = plt.subplots(figsize=(10, max(4, len(cld_df) * 0.6)))
                    ax.axis('off')
                    table_data = [['Rank', 'Group', 'Mean', 'Letters']]
                    for rank, (_, row) in enumerate(cld_df.iterrows(), 1):
                        table_data.append([str(rank), str(row['group']), f"{row['mean']:.4f}", row['letters']])
                    table = ax.table(cellText=table_data, cellLoc='center', loc='center', colWidths=[0.1, 0.35, 0.25, 0.3])
                    table.auto_set_font_size(False)
                    table.set_fontsize(11)
                    table.scale(1, 2)
                    for i in range(4):
                        table[(0, i)].set_facecolor('#1f77b4')
                        table[(0, i)].set_text_props(weight='bold', color='white')
                    for i in range(1, len(table_data)):
                        table[(i, 3)].set_text_props(weight='bold', color='#d62728', fontsize=12)
                    st.pyplot(fig)
                    st.dataframe(cld_df, use_container_width=True, hide_index=True)

                # Visualization
                st.markdown("---")
                st.markdown("### 📊 Mean Separation Plot")
                fig, ax = plt.subplots(figsize=(12, 7))
                cld = results['cld']
                means = cld['mean'].values
                groups = cld['group'].values
                letters = cld['letters'].values
                x_pos = np.arange(len(groups))
                bars = ax.bar(x_pos, means, color='steelblue', alpha=0.8, edgecolor='black')
                for i, (bar, letter) in enumerate(zip(bars, letters)):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(means)*0.01,
                           letter, ha='center', va='bottom', fontweight='bold', fontsize=14, color='#d62728')
                ax.set_xticks(x_pos)
                ax.set_xticklabels(groups, rotation=45, ha='right')
                ax.set_ylabel(f'Mean {dep_var}')
                ax.set_title(f'Mean Separation: {dep_var} by {ind_var} ({name})')
                ax.grid(axis='y', alpha=0.3)
                st.pyplot(fig)

            except Exception as e:
                st.error(f"❌ Analysis error: {str(e)}")
                st.markdown(f'<div class="error-box"><strong>Error:</strong> {str(e)}</div>', unsafe_allow_html=True)


def render_descriptive_statistics(cleaned_data, numeric_cols, categorical_cols):
    st.markdown("---")
    st.markdown("## Phase 3: Descriptive Statistics")
    if numeric_cols:
        desc = cleaned_data[numeric_cols].describe().T
        desc['skewness'] = cleaned_data[numeric_cols].skew()
        desc['kurtosis'] = cleaned_data[numeric_cols].kurtosis()
        desc['missing'] = cleaned_data[numeric_cols].isnull().sum()
        desc['missing_pct'] = (desc['missing'] / len(cleaned_data)) * 100
        st.dataframe(desc, use_container_width=True)
    if categorical_cols:
        st.markdown("### Categorical Variables")
        for col in categorical_cols:
            st.markdown(f"**{col}**")
            st.dataframe(cleaned_data[col].value_counts().head(10), use_container_width=True)


def render_export(cleaned_data, numeric_cols, categorical_cols):
    st.markdown("---")
    st.markdown("## Phase 4: Export & Reporting")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💾 Download Data")
        csv = cleaned_data.to_csv(index=False)
        st.download_button("📥 Cleaned CSV", csv, "cleaned_data.csv", "text/csv", use_container_width=True)
    with col2:
        st.markdown("### 📄 Reports")
        if st.button("📝 Generate Summary Report", use_container_width=True):
            report = f"""
AUTOMATED ANALYTICAL REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DATA OVERVIEW
- Total Observations: {len(cleaned_data):,}
- Total Variables: {len(cleaned_data.columns)}
- Numeric Variables: {len(numeric_cols)}
- Categorical Variables: {len(categorical_cols)}

NUMERIC SUMMARY
{cleaned_data[numeric_cols].describe().to_string() if numeric_cols else 'No numeric variables'}
"""
            st.text_area("Report", report, height=300)
            st.download_button("📥 Download Report", report, "report.txt", "text/plain", use_container_width=True)


class StreamlitApp:
    def run(self):
        analysis_type, color_palette = render_sidebar()

        if st.session_state.data is None:
            render_welcome_screen()
            return

        cleaned_data = render_data_cleaning(st.session_state.data)
        numeric_cols = cleaned_data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = cleaned_data.select_dtypes(include=['category', 'object']).columns.tolist()

        render_data_profiling(cleaned_data, numeric_cols, categorical_cols, color_palette)

        if analysis_type == "Auto-Detect":
            st.info("🤖 Auto-detecting analysis type...")
            if len(categorical_cols) >= 2 and len(numeric_cols) >= 1:
                analysis_type = "Two-Way ANOVA"
                st.success(f"Detected multiple factors. Recommended: **{analysis_type}**")
            elif len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                analysis_type = "One-Way ANOVA"
                st.success(f"Detected grouping variable. Recommended: **{analysis_type}**")
            else:
                analysis_type = "Descriptive Statistics"
                st.success(f"Recommended: **{analysis_type}**")

        if analysis_type == "One-Way ANOVA":
            render_one_way_anova(cleaned_data, numeric_cols, categorical_cols, color_palette)
        elif analysis_type == "Two-Way ANOVA":
            render_two_way_anova(cleaned_data, numeric_cols, categorical_cols, color_palette)
        elif analysis_type == "Mean Separation":
            render_mean_separation(cleaned_data, numeric_cols, categorical_cols, color_palette)
        elif analysis_type == "Descriptive Statistics":
            render_descriptive_statistics(cleaned_data, numeric_cols, categorical_cols)

        render_export(cleaned_data, numeric_cols, categorical_cols)

        st.markdown("---")
        st.markdown("<div class='footer'><p>🔬 <strong>Turkey HSD Analyzer v2.0</strong> | Advanced ANOVA & Mean Separation | Built with Streamlit</p></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    app = StreamlitApp()
    app.run()
