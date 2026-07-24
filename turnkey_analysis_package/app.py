#!/usr/bin/env python3
"""
Turnkey Statistical Analysis Pipeline
=====================================
A production-ready Streamlit application for automated statistical analysis
with support for ANOVA, Tukey HSD post-hoc testing, regression, and descriptive
statistics.

Entry Point: app.py
Author: Turnkey Operations Team
License: MIT
Python: >=3.9
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

APP_NAME = "Turnkey Statistical Analysis"
APP_VERSION = "1.0.0"
APP_ICON = "📊"

st.set_page_config(
    page_title=f"{APP_NAME} v{APP_VERSION}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/turnkey-ops/turnkey-analysis',
        'Report a bug': 'https://github.com/turnkey-ops/turnkey-analysis/issues',
        'About': f"{APP_NAME} v{APP_VERSION} - Production-ready statistical analysis pipeline"
    }
)

# =============================================================================
# CUSTOM CSS
# =============================================================================

CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1.15rem;
        color: #666;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 12px;
        padding: 1.2rem;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #b1dfbb;
        color: #155724;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .info-box {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 1px solid #a8d5e2;
        color: #0c5460;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .warning-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border: 1px solid #ffe8a1;
        color: #856404;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .error-box {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f1b0b7;
        color: #721c24;
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 6px 6px 0px 0px;
        gap: 1px;
        padding: 10px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1f77b4;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #666;
    }
    .footer {
        text-align: center;
        color: #888;
        padding: 2rem 1rem;
        font-size: 0.85rem;
        border-top: 1px solid #eee;
        margin-top: 2rem;
    }
    .phase-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #333;
        margin: 1.5rem 0 0.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #1f77b4;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    defaults = {
        'data': None,
        'cleaned_data': None,
        'analysis_results': {},
        'last_analysis': None,
        'error_log': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# DATA PROCESSING FUNCTIONS
# =============================================================================

def clean_column_names(df):
    df = df.copy()
    df.columns = (df.columns
                  .str.strip()
                  .str.lower()
                  .str.replace(' ', '_', regex=False)
                  .str.replace('-', '_', regex=False)
                  .str.replace('[^a-z0-9_]', '', regex=True)
                  .str.replace('__+', '_', regex=True))
    return df


def detect_data_types(df):
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                converted = pd.to_numeric(df[col], errors='coerce')
                if converted.notna().sum() / len(df) > 0.8:
                    df[col] = converted
                    continue
            except:
                pass
            try:
                converted = pd.to_datetime(df[col], errors='coerce')
                if converted.notna().sum() / len(df) > 0.8:
                    df[col] = converted
                    continue
            except:
                pass
            if df[col].nunique() / len(df) < 0.1 and df[col].nunique() < 50:
                df[col] = df[col].astype('category')
    return df


def handle_missing_values(df, numeric_strategy='median', categorical_strategy='mode'):
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['category', 'object']).columns

    for col in numeric_cols:
        if df[col].isnull().any():
            if numeric_strategy == 'median':
                df[col].fillna(df[col].median(), inplace=True)
            elif numeric_strategy == 'mean':
                df[col].fillna(df[col].mean(), inplace=True)

    for col in categorical_cols:
        if df[col].isnull().any():
            mode_val = df[col].mode()
            df[col].fillna(mode_val[0] if not mode_val.empty else 'Unknown', inplace=True)

    return df


# =============================================================================
# STATISTICAL ANALYSIS FUNCTIONS
# =============================================================================

def perform_anova(df, dependent_var, independent_var, alpha=0.05):
    """
    Perform One-Way ANOVA and Tukey HSD post-hoc test.
    Core function implementing ANOVA + Tukey HSD per turnkey requirements.
    """
    df = df.copy()

    if dependent_var not in df.columns:
        raise ValueError(f"Dependent variable '{dependent_var}' not found in dataset")
    if independent_var not in df.columns:
        raise ValueError(f"Independent variable '{independent_var}' not found in dataset")

    original_var = independent_var
    if df[independent_var].dtype.name not in ['category', 'object', 'bool']:
        if df[independent_var].nunique() > 5:
            st.warning(f"'{independent_var}' is continuous. Auto-binning into quartiles for ANOVA.")
            q_count = min(4, df[independent_var].nunique())
            labels = ['Q1', 'Q2', 'Q3', 'Q4'][:q_count]
            df[independent_var + '_binned'] = pd.qcut(
                df[independent_var], q=q_count, labels=labels, duplicates='drop'
            )
            independent_var = independent_var + '_binned'
        else:
            df[independent_var] = df[independent_var].astype('category')

    analysis_df = df[[dependent_var, independent_var]].dropna()

    if len(analysis_df) < 10:
        raise ValueError("Insufficient data for ANOVA (minimum 10 observations required)")

    groups = [group[dependent_var].values for name, group in analysis_df.groupby(independent_var)]

    if len(groups) < 2:
        raise ValueError("ANOVA requires at least 2 groups")

    # One-Way ANOVA
    f_stat, p_value = stats.f_oneway(*groups)

    # Tukey HSD Post-Hoc Test
    tukey = pairwise_tukeyhsd(
        endog=analysis_df[dependent_var],
        groups=analysis_df[independent_var],
        alpha=alpha
    )

    # Effect size (Eta-squared)
    grand_mean = analysis_df[dependent_var].mean()
    ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in groups)
    ss_total = sum((x - grand_mean)**2 for g in groups for x in g)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0

    # Group statistics
    group_stats = analysis_df.groupby(independent_var)[dependent_var].agg([
        'count', 'mean', 'std', 'min', 'max'
    ]).round(4)

    # Assumption tests
    levene_stat, levene_p = stats.levene(*groups)
    sample_data = analysis_df[dependent_var].dropna()
    if len(sample_data) > 5000:
        sample_data = sample_data.sample(5000, random_state=42)
    shapiro_stat, shapiro_p = stats.shapiro(sample_data)

    return {
        'f_statistic': float(f_stat),
        'p_value': float(p_value),
        'eta_squared': float(eta_squared),
        'tukey_results': tukey,
        'group_stats': group_stats,
        'independent_var': independent_var,
        'original_independent_var': original_var,
        'dependent_var': dependent_var,
        'significant': bool(p_value < alpha),
        'alpha': alpha,
        'n_observations': len(analysis_df),
        'n_groups': len(groups),
        'levene_test': {'statistic': float(levene_stat), 'p_value': float(levene_p)},
        'shapiro_test': {'statistic': float(shapiro_stat), 'p_value': float(shapiro_p)},
        'assumptions_met': {
            'normality': shapiro_p > 0.05,
            'homogeneity': levene_p > 0.05
        }
    }


def perform_regression(df, dependent_var, independent_var):
    """Perform simple linear regression analysis."""
    temp_df = df[[dependent_var, independent_var]].dropna()

    if len(temp_df) < 10:
        raise ValueError("Insufficient data for regression (minimum 10 observations)")

    x = temp_df[independent_var].values
    y = temp_df[dependent_var].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    predictions = slope * x + intercept
    residuals = y - predictions

    r_squared = r_value ** 2
    n = len(temp_df)
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - 2) if n > 2 else np.nan
    mse = np.mean(residuals**2)
    rmse = np.sqrt(mse)

    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r_squared': float(r_squared),
        'adj_r_squared': float(adj_r_squared),
        'p_value': float(p_value),
        'std_err': float(std_err),
        'rmse': float(rmse),
        'residuals': residuals,
        'predictions': predictions,
        'x': x,
        'y': y,
        'n_observations': n
    }


def interpret_effect_size(eta_sq):
    """Interpret Cohen's guidelines for eta-squared effect size."""
    if eta_sq < 0.01:
        return "Negligible", "Less than 1% of variance explained"
    elif eta_sq < 0.06:
        return "Small", "1-6% of variance explained"
    elif eta_sq < 0.14:
        return "Medium", "6-14% of variance explained"
    else:
        return "Large", "More than 14% of variance explained"


# =============================================================================
# REPORTING FUNCTIONS
# =============================================================================

def generate_insights_report(df, numeric_cols, categorical_cols, analysis_results=None):
    """Generate a comprehensive automated insights report."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"   AUTOMATED ANALYTICAL REPORT - {APP_NAME}")
    lines.append(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"   Version: {APP_VERSION}")
    lines.append("=" * 70)
    lines.append("")

    lines.append("DATA OVERVIEW")
    lines.append("-" * 70)
    lines.append(f"Total Observations: {len(df):,}")
    lines.append(f"Total Variables: {len(df.columns)}")
    lines.append(f"Numeric Variables: {len(numeric_cols)}")
    lines.append(f"Categorical Variables: {len(categorical_cols)}")
    lines.append("")

    missing_data = df.isnull().sum()
    if missing_data.sum() > 0:
        lines.append("MISSING DATA SUMMARY")
        lines.append("-" * 70)
        for col, missing in missing_data[missing_data > 0].items():
            pct = (missing / len(df)) * 100
            lines.append(f"  {col}: {missing:,} missing ({pct:.2f}%)")
        lines.append("")

    if numeric_cols:
        lines.append("NUMERIC VARIABLES SUMMARY")
        lines.append("-" * 70)
        desc = df[numeric_cols].describe().T
        for col in numeric_cols:
            lines.append(f"\n{col}:")
            lines.append(f"  Mean: {desc.loc[col, 'mean']:.4f}")
            lines.append(f"  Std Dev: {desc.loc[col, 'std']:.4f}")
            lines.append(f"  Min: {desc.loc[col, 'min']:.4f}")
            lines.append(f"  Max: {desc.loc[col, 'max']:.4f}")
            skew = stats.skew(df[col].dropna())
            kurt = stats.kurtosis(df[col].dropna())
            lines.append(f"  Skewness: {skew:.4f}")
            lines.append(f"  Kurtosis: {kurt:.4f}")

    if analysis_results and 'f_statistic' in analysis_results:
        lines.append("")
        lines.append("=" * 70)
        lines.append("STATISTICAL ANALYSIS RESULTS")
        lines.append("=" * 70)
        lines.append("")
        lines.append("ONE-WAY ANOVA RESULTS")
        lines.append("-" * 70)
        lines.append(f"Dependent Variable: {analysis_results['dependent_var']}")
        lines.append(f"Independent Variable: {analysis_results['independent_var']}")
        lines.append(f"F-Statistic: {analysis_results['f_statistic']:.4f}")
        lines.append(f"P-Value: {analysis_results['p_value']:.4f}")
        lines.append(f"Significant: {'Yes' if analysis_results['significant'] else 'No'}")
        lines.append(f"Effect Size (eta-squared): {analysis_results['eta_squared']:.4f}")
        lines.append(f"Observations: {analysis_results['n_observations']:,}")
        lines.append(f"Groups: {analysis_results['n_groups']}")

        lines.append("")
        lines.append("TUKEY HSD POST-HOC TEST RESULTS")
        lines.append("-" * 70)
        tukey_df = pd.DataFrame(data=analysis_results['tukey_results']._results_table.data[1:], 
                               columns=analysis_results['tukey_results']._results_table.data[0])
        for _, row in tukey_df.iterrows():
            sig = "SIGNIFICANT" if row['reject'] else "Not significant"
            lines.append(f"  {row['group1']} vs {row['group2']}: Mean Diff = {row['meandiff']:.4f}, p-adj = {row['p-adj']:.4f} [{sig}]")

    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.markdown(f"<p style='color:#666;font-size:0.9rem;'>v{APP_VERSION} | Production Ready</p>", 
                unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 📁 Data Import")
    uploaded_file = st.file_uploader(
        "Upload your data file",
        type=['csv', 'txt', 'xlsx', 'xls'],
        help="Supported formats: CSV, Excel (.xlsx, .xls), TXT"
    )

    if uploaded_file is not None:
        try:
            with st.spinner("📂 Loading data..."):
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(uploaded_file)
                else:
                    try:
                        df = pd.read_csv(uploaded_file)
                    except:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, sep='\t')

                st.session_state.data = df
                st.success(f"Loaded {len(df):,} rows x {len(df.columns)} columns")
                st.markdown(f"<p style='font-size:0.8rem;color:#666;'>File: {uploaded_file.name}</p>", 
                          unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            st.session_state.error_log.append(f"File load error: {str(e)}")

    st.markdown("---")
    st.markdown("### ⚙️ Analysis Configuration")

    analysis_type = st.selectbox(
        "Analysis Type",
        ["Auto-Detect", "ANOVA + Tukey HSD", "Regression Analysis", "Descriptive Statistics"],
        help="Auto-Detect will choose based on your data structure"
    )

    confidence_level = st.slider(
        "Confidence Level", 0.80, 0.99, 0.95, 0.01,
        help="Alpha = 1 - Confidence Level"
    )

    show_advanced = st.checkbox("Show Advanced Diagnostics", value=True)

    st.markdown("---")
    st.markdown("### 🎨 Visualization")

    plot_theme = st.selectbox("Plot Theme", ["whitegrid", "darkgrid", "white", "dark"], index=0)
    color_palette = st.selectbox(
        "Color Palette",
        ["viridis", "plasma", "coolwarm", "Set1", "Set2", "husl", "magma"],
        index=0
    )
    sns.set_style(plot_theme)

    st.markdown("---")

    if st.button("🔄 Reset Application", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size:0.75rem;color:#999;text-align:center;'>2026 Turnkey Operations</p>", 
              unsafe_allow_html=True)

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown(f'<p class="main-header">{APP_ICON} {APP_NAME}</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated statistical analysis pipeline with ANOVA and Tukey HSD post-hoc testing</p>', 
            unsafe_allow_html=True)

# WELCOME SCREEN
if st.session_state.data is None:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🚀 Automated Pipeline</h3>
            <p>Zero-configuration data analysis. Upload your dataset and the system automatically cleans, analyzes, and visualizes results.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📈 ANOVA + Tukey HSD</h3>
            <p>Perform one-way ANOVA with automatic Tukey Honestly Significant Difference post-hoc testing for group comparisons.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📋 Production Ready</h3>
            <p>Enterprise-grade error handling, session management, exportable reports, and responsive design for any device.</p>
        </div>
        """, unsafe_allow_html=True)

    st.info("👈 Get Started: Upload a data file using the sidebar, or try the sample dataset below.")

    st.markdown("### 🧪 Quick Start with Sample Data")

    sample_col1, sample_col2 = st.columns([1, 3])
    with sample_col1:
        if st.button("📊 Generate Sample Dataset", use_container_width=True, type="primary"):
            with st.spinner("Generating sample data..."):
                np.random.seed(42)
                n = 250

                sample_data = pd.DataFrame({
                    'sales_revenue': np.random.normal(10000, 2000, n),
                    'marketing_spend': np.random.normal(5000, 1000, n),
                    'customer_satisfaction': np.random.normal(4.2, 0.6, n),
                    'region': np.random.choice(['North', 'South', 'East', 'West'], n),
                    'product_category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Home', 'Sports'], n),
                    'quarter': np.random.choice(['Q1', 'Q2', 'Q3', 'Q4'], n),
                    'employee_count': np.random.randint(50, 500, n),
                    'years_in_business': np.random.randint(1, 30, n)
                })

                sample_data['sales_revenue'] += 0.4 * sample_data['marketing_spend'] + np.random.normal(0, 500, n)
                sample_data['customer_satisfaction'] += 0.0001 * sample_data['sales_revenue'] + np.random.normal(0, 0.1, n)

                region_effect = {'North': 500, 'South': -300, 'East': 200, 'West': -400}
                sample_data['sales_revenue'] += sample_data['region'].map(region_effect)

                st.session_state.data = sample_data
                st.rerun()

    with sample_col2:
        st.markdown("""
        <div class="info-box" style="margin-top:0;">
            <p><strong>Sample Dataset Features:</strong></p>
            <ul>
                <li>250 observations with realistic business metrics</li>
                <li>Built-in correlations for regression analysis</li>
                <li>Regional effects for ANOVA + Tukey HSD demonstration</li>
                <li>Mix of numeric and categorical variables</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ANALYSIS PIPELINE
else:
    raw_data = st.session_state.data.copy()

    # PHASE 1
    st.markdown('<p class="phase-header">Phase 1: Data Import & Cleaning</p>', unsafe_allow_html=True)

    mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
    mcol1.metric("📊 Rows", f"{len(raw_data):,}")
    mcol2.metric("📋 Columns", len(raw_data.columns))
    mcol3.metric("🔢 Numeric", len(raw_data.select_dtypes(include=[np.number]).columns))
    mcol4.metric("🏷️ Categorical", len(raw_data.select_dtypes(include=['object', 'category']).columns))
    mcol5.metric("⚠️ Missing", f"{raw_data.isnull().sum().sum():,}")

    with st.expander("🔍 Raw Data Preview (First 15 rows)", expanded=False):
        st.dataframe(raw_data.head(15), use_container_width=True, hide_index=True)
        st.caption(f"Full dataset: {len(raw_data):,} rows x {len(raw_data.columns)} columns")

    with st.spinner("🧹 Running automated data cleaning pipeline..."):
        cleaned_data = raw_data.copy()
        cleaned_data = clean_column_names(cleaned_data)
        cleaned_data = detect_data_types(cleaned_data)
        cleaned_data = cleaned_data.drop_duplicates()
        cleaned_data = handle_missing_values(cleaned_data)
        st.session_state.cleaned_data = cleaned_data

    numeric_cols = cleaned_data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = cleaned_data.select_dtypes(include=['category', 'object', 'bool']).columns.tolist()
    datetime_cols = cleaned_data.select_dtypes(include=['datetime64']).columns.tolist()

    st.markdown(f"""
    <div class="success-box">
        <strong>✅ Cleaning Complete!</strong> Standardized column names to snake_case, 
        removed {raw_data.duplicated().sum()} duplicates, imputed missing values, and auto-detected data types. 
        Dataset now has <strong>{len(numeric_cols)} numeric</strong> and <strong>{len(categorical_cols)} categorical</strong> variables.
    </div>
    """, unsafe_allow_html=True)

    # PHASE 2
    st.markdown('<p class="phase-header">Phase 2: Data Profiling</p>', unsafe_allow_html=True)

    profile_tab1, profile_tab2, profile_tab3 = st.tabs(["📋 Overview", "📊 Distributions", "🔗 Correlations"])

    with profile_tab1:
        prof_col1, prof_col2 = st.columns([1, 2])

        with prof_col1:
            st.markdown("### Variable Summary")
            var_summary = pd.DataFrame({
                'Type': ['Numeric', 'Categorical', 'Datetime', 'Total'],
                'Count': [len(numeric_cols), len(categorical_cols), len(datetime_cols), len(cleaned_data.columns)]
            })
            st.dataframe(var_summary, use_container_width=True, hide_index=True)

            if numeric_cols:
                st.markdown("### Quick Numeric Stats")
                quick_stats = cleaned_data[numeric_cols].describe().loc[['mean', 'std', '50%']].T
                quick_stats.columns = ['Mean', 'Std Dev', 'Median']
                st.dataframe(quick_stats.round(3), use_container_width=True)

        with prof_col2:
            if categorical_cols:
                st.markdown("### Categorical Variables Distribution")
                for col in categorical_cols[:3]:
                    st.markdown(f"**{col}**")
                    vc = cleaned_data[col].value_counts().head(8)
                    st.bar_chart(vc)

    with profile_tab2:
        if numeric_cols:
            dist_col = st.selectbox("Select variable for distribution analysis", numeric_cols, key="dist_select")

            dcol1, dcol2 = st.columns(2)
            with dcol1:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.histplot(cleaned_data[dist_col], kde=True, color='steelblue', ax=ax, stat='density')
                ax.set_title(f'Distribution of {dist_col}', fontsize=14, fontweight='bold')
                ax.set_xlabel(dist_col, fontsize=12)
                ax.set_ylabel('Density', fontsize=12)
                plt.tight_layout()
                st.pyplot(fig)

            with dcol2:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.boxplot(y=cleaned_data[dist_col], color='lightcoral', ax=ax)
                ax.set_title(f'Box Plot of {dist_col}', fontsize=14, fontweight='bold')
                plt.tight_layout()
                st.pyplot(fig)

            sample = cleaned_data[dist_col].dropna()
            if len(sample) > 5000:
                sample = sample.sample(5000, random_state=42)
            shapiro_stat, shapiro_p = stats.shapiro(sample)
            normality_status = "✅ Normal" if shapiro_p > 0.05 else "⚠️ Non-normal"
            st.info(f"**Shapiro-Wilk Normality Test**: Statistic = {shapiro_stat:.4f}, p-value = {shapiro_p:.4f} → {normality_status}")

    with profile_tab3:
        if len(numeric_cols) >= 2:
            st.markdown("### Correlation Matrix")
            corr_matrix = cleaned_data[numeric_cols].corr()

            fig, ax = plt.subplots(figsize=(14, 11))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap=color_palette, 
                       center=0, square=True, linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})
            ax.set_title('Correlation Matrix (Lower Triangle)', fontsize=14, fontweight='bold')
            st.pyplot(fig)

            strong_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    val = corr_matrix.iloc[i, j]
                    if abs(val) > 0.7:
                        strong_corr.append({
                            'Variable 1': corr_matrix.columns[i],
                            'Variable 2': corr_matrix.columns[j],
                            'Correlation': round(val, 3),
                            'Strength': 'Strong Positive' if val > 0 else 'Strong Negative'
                        })

            if strong_corr:
                st.markdown("### ⚠️ Strong Correlations Detected (|r| > 0.70)")
                st.dataframe(pd.DataFrame(strong_corr), use_container_width=True, hide_index=True)
        else:
            st.warning("Need at least 2 numeric variables for correlation analysis.")

    # PHASE 3
    st.markdown('<p class="phase-header">Phase 3: Statistical Analysis</p>', unsafe_allow_html=True)

    if analysis_type == "Auto-Detect":
        st.info("🤖 **Auto-Detect Mode**: Analyzing data structure to recommend optimal analysis...")

        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            recommended = "ANOVA + Tukey HSD"
            reason = f"Found {len(numeric_cols)} numeric and {len(categorical_cols)} categorical variables"
        elif len(numeric_cols) >= 2:
            recommended = "Regression Analysis"
            reason = f"Found {len(numeric_cols)} numeric variables suitable for regression"
        else:
            recommended = "Descriptive Statistics"
            reason = "Limited variables for inferential statistics"

        analysis_type = recommended
        st.success(f"**Recommended Analysis: {recommended}** — {reason}")

    st.markdown("### ⚙️ Configure Analysis")

    config_col1, config_col2 = st.columns(2)

    with config_col1:
        if analysis_type == "Regression Analysis":
            dep_var = st.selectbox("Dependent Variable (Y)", numeric_cols, index=0 if numeric_cols else None, key="reg_dep")
            ind_var = st.selectbox("Independent Variable (X)", 
                                  [c for c in numeric_cols if c != dep_var], 
                                  index=0 if len(numeric_cols) > 1 else None, key="reg_ind")

        elif analysis_type == "ANOVA + Tukey HSD":
            dep_var = st.selectbox("Dependent Variable (Numeric)", numeric_cols, index=0 if numeric_cols else None, key="anova_dep")
            grouping_options = categorical_cols + [c for c in numeric_cols if c != dep_var]
            default_idx = 0 if categorical_cols else 0
            ind_var = st.selectbox("Grouping Variable", grouping_options, index=default_idx, key="anova_ind")

        else:
            dep_var = st.selectbox("Variable of Interest", numeric_cols if numeric_cols else cleaned_data.columns.tolist(), index=0, key="desc_var")
            ind_var = None

    with config_col2:
        st.markdown("### Parameters")
        st.markdown(f"**Confidence Level**: {confidence_level:.0%}")
        st.markdown(f"**Alpha (α)**: {1-confidence_level:.2f}")
        st.markdown(f"**Advanced Diagnostics**: {'Enabled' if show_advanced else 'Disabled'}")

        if analysis_type == "ANOVA + Tukey HSD":
            st.info("📊 **Tukey HSD** will automatically run after ANOVA if significant differences are found.")

    run_button = st.button("🚀 Run Statistical Analysis", type="primary", use_container_width=True)

    if run_button:
        try:
            with st.spinner("🔬 Computing statistical analysis..."):
                alpha = 1 - confidence_level

                if analysis_type == "Regression Analysis":
                    results = perform_regression(cleaned_data, dep_var, ind_var)
                    st.session_state.analysis_results = results
                    st.session_state.last_analysis = "regression"

                    st.markdown("---")
                    st.markdown("## 📈 Regression Analysis Results")

                    rcol1, rcol2, rcol3, rcol4, rcol5 = st.columns(5)
                    rcol1.metric("R²", f"{results['r_squared']:.4f}")
                    rcol2.metric("Adj. R²", f"{results['adj_r_squared']:.4f}")
                    rcol3.metric("Slope", f"{results['slope']:.4f}")
                    rcol4.metric("Intercept", f"{results['intercept']:.4f}")
                    sig_color = "normal" if results['p_value'] < 0.05 else "inverse"
                    rcol5.metric("P-value", f"{results['p_value']:.4f}", 
                               delta="Significant" if results['p_value'] < 0.05 else "Not Significant",
                               delta_color=sig_color)

                    st.markdown(f"""
                    <div class="info-box">
                        <h4>📐 Regression Equation</h4>
                        <p style="font-size: 1.3rem; font-family: 'Courier New', monospace; margin: 0.5rem 0;">
                        {dep_var} = {results['intercept']:.4f} + {results['slope']:.4f} x {ind_var}
                        </p>
                        <p style="font-size: 0.9rem; color: #666; margin: 0;">
                        RMSE: {results['rmse']:.4f} | Standard Error: {results['std_err']:.4f} | N = {results['n_observations']:,}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    reg_tab1, reg_tab2, reg_tab3 = st.tabs(["📊 Scatter Plot", "📉 Residual Analysis", "🔍 Diagnostics"])

                    with reg_tab1:
                        fig, ax = plt.subplots(figsize=(12, 8))
                        ax.scatter(results['x'], results['y'], alpha=0.6, color='steelblue', s=50, edgecolors='white', linewidth=0.5, label='Observed Data')
                        ax.plot(results['x'], results['predictions'], color='crimson', linewidth=2.5, label='Regression Line')
                        ax.set_xlabel(ind_var, fontsize=12)
                        ax.set_ylabel(dep_var, fontsize=12)
                        ax.set_title(f'Regression: {dep_var} vs {ind_var}', fontsize=14, fontweight='bold')
                        ax.legend(fontsize=11)
                        ax.grid(True, alpha=0.3, linestyle='--')
                        plt.tight_layout()
                        st.pyplot(fig)

                    with reg_tab2:
                        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
                        axes[0].hist(results['residuals'], bins=30, color='steelblue', edgecolor='white', alpha=0.7)
                        axes[0].set_title('Residual Distribution', fontsize=14, fontweight='bold')
                        axes[0].set_xlabel('Residual Value')
                        axes[0].set_ylabel('Frequency')
                        axes[1].scatter(results['predictions'], results['residuals'], alpha=0.6, color='green')
                        axes[1].axhline(y=0, color='red', linestyle='--', linewidth=2)
                        axes[1].set_title('Residuals vs Predicted', fontsize=14, fontweight='bold')
                        axes[1].set_xlabel('Predicted Values')
                        axes[1].set_ylabel('Residuals')
                        plt.tight_layout()
                        st.pyplot(fig)

                    with reg_tab3:
                        if show_advanced:
                            fig, ax = plt.subplots(figsize=(10, 6))
                            stats.probplot(results['residuals'], dist="norm", plot=ax)
                            ax.set_title('Q-Q Plot (Normality of Residuals)', fontsize=14, fontweight='bold')
                            ax.grid(True, alpha=0.3)
                            st.pyplot(fig)
                            st.info("📊 **Diagnostics**: Check Q-Q plot for normality and residual plots for homoscedasticity.")

                elif analysis_type == "ANOVA + Tukey HSD":
                    results = perform_anova(cleaned_data, dep_var, ind_var, alpha=alpha)
                    st.session_state.analysis_results = results
                    st.session_state.last_analysis = "anova"

                    st.markdown("---")
                    st.markdown("## 📊 One-Way ANOVA & Tukey HSD Results")

                    st.markdown("### 1️⃣ ANOVA Results")

                    acol1, acol2, acol3, acol4 = st.columns(4)
                    acol1.metric("F-Statistic", f"{results['f_statistic']:.4f}")
                    sig_text = "✅ Significant" if results['significant'] else "❌ Not Significant"
                    acol2.metric("P-Value", f"{results['p_value']:.4f}", delta=sig_text,
                               delta_color="normal" if results['significant'] else "inverse")
                    acol3.metric("Effect Size (η²)", f"{results['eta_squared']:.4f}")
                    acol4.metric("Groups", results['n_groups'])

                    if results['significant']:
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>✅ Statistically Significant Result</h4>
                            <p>The ANOVA indicates significant differences between group means 
                            (<strong>F({results['n_groups']-1}, {results['n_observations']-results['n_groups']}) = {results['f_statistic']:.4f}, 
                            p = {results['p_value']:.4f}</strong>). The Tukey HSD post-hoc test below identifies which specific groups differ significantly.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="warning-box">
                            <h4>⚠️ No Significant Difference Detected</h4>
                            <p>ANOVA found no statistically significant difference between group means 
                            (<strong>F = {results['f_statistic']:.4f}, p = {results['p_value']:.4f}</strong>). 
                            Tukey HSD results are provided for completeness but should be interpreted with caution.</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("### ANOVA Summary Table")
                    anova_table = pd.DataFrame({
                        'Source': ['Between Groups', 'Within Groups', 'Total'],
                        'DF': [
                            results['n_groups'] - 1,
                            results['n_observations'] - results['n_groups'],
                            results['n_observations'] - 1
                        ],
                        'F-Statistic': [f"{results['f_statistic']:.4f}", '-', '-'],
                        'P-Value': [f"{results['p_value']:.4f}", '-', '-'],
                        'Significant': ['Yes' if results['significant'] else 'No', '-', '-']
                    })
                    st.dataframe(anova_table, use_container_width=True, hide_index=True)

                    st.markdown("### 📋 ANOVA Assumptions Check")
                    assumptions_df = pd.DataFrame({
                        'Assumption': [
                            'Normality (Shapiro-Wilk)',
                            'Homogeneity of Variance (Levene)',
                            'Independence',
                            'Sample Size (per group >= 5)'
                        ],
                        'Test Statistic': [
                            f"{results['shapiro_test']['statistic']:.4f}",
                            f"{results['levene_test']['statistic']:.4f}",
                            'Assumed by design',
                            f"{results['n_observations'] // results['n_groups']} (avg)"
                        ],
                        'P-Value': [
                            f"{results['shapiro_test']['p_value']:.4f}",
                            f"{results['levene_test']['p_value']:.4f}",
                            '-',
                            '-'
                        ],
                        'Status': [
                            '✅ Met' if results['assumptions_met']['normality'] else '⚠️ Violated',
                            '✅ Met' if results['assumptions_met']['homogeneity'] else '⚠️ Violated',
                            '✅ Assumed',
                            '✅ Adequate' if (results['n_observations'] // results['n_groups']) >= 5 else '⚠️ Low'
                        ]
                    })
                    st.dataframe(assumptions_df, use_container_width=True, hide_index=True)

                    st.markdown("### 📊 Group Descriptive Statistics")
                    st.dataframe(results['group_stats'], use_container_width=True)

                    # TUKEY HSD
                    st.markdown("---")
                    st.markdown("### 2️⃣ Tukey HSD Post-Hoc Test")

                    st.info(f"""
                    **Tukey's Honestly Significant Difference (HSD)** test compares all possible pairs of group means 
                    while controlling the family-wise error rate at alpha = {alpha:.2f}. A significant result (reject = True) 
                    indicates that the pair of groups have statistically different means.
                    """)

                    tukey_data = results['tukey_results']._results_table.data
                    tukey_df = pd.DataFrame(data=tukey_data[1:], columns=tukey_data[0])
                    tukey_df['Significant'] = tukey_df['reject'].apply(lambda x: '✅ Yes' if x else '❌ No')
                    tukey_df['meandiff'] = tukey_df['meandiff'].round(4)
                    tukey_df['p-adj'] = tukey_df['p-adj'].round(4)
                    tukey_df['lower'] = tukey_df['lower'].round(4)
                    tukey_df['upper'] = tukey_df['upper'].round(4)

                    st.dataframe(tukey_df, use_container_width=True)

                    sig_pairs = tukey_df[tukey_df['reject'] == True]
                    if not sig_pairs.empty:
                        st.markdown("### 🔍 Significant Pairwise Differences")
                        for _, row in sig_pairs.iterrows():
                            st.markdown(f"• **{row['group1']}** vs **{row['group2']}**: Mean Diff = `{row['meandiff']:.4f}`, 95% CI = [{row['lower']:.4f}, {row['upper']:.4f}], p-adj = `{row['p-adj']:.4f}` ✅")
                    else:
                        st.markdown("### 🔍 Pairwise Comparisons")
                        st.warning("No statistically significant pairwise differences found at the current alpha level.")

                    anova_tab1, anova_tab2, anova_tab3 = st.tabs(["📊 Group Means", "📦 Box Plots", "📈 Tukey Intervals"])

                    with anova_tab1:
                        fig, ax = plt.subplots(figsize=(14, 8))
                        group_means = results['group_stats']['mean'].sort_values(ascending=False)
                        colors = sns.color_palette(color_palette, len(group_means))
                        bars = ax.bar(range(len(group_means)), group_means.values, color=colors, alpha=0.85, edgecolor='black', linewidth=1.2)
                        ax.set_xticks(range(len(group_means)))
                        ax.set_xticklabels(group_means.index, rotation=45, ha='right')
                        ax.set_ylabel(f'Mean {dep_var}', fontsize=12)
                        ax.set_title(f'Mean {dep_var} by {results["independent_var"]}', fontsize=14, fontweight='bold')
                        ax.grid(axis='y', alpha=0.3, linestyle='--')
                        for bar, val in zip(bars, group_means.values):
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01*max(group_means.values),
                                   f'{val:.2f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
                        plt.tight_layout()
                        st.pyplot(fig)

                    with anova_tab2:
                        fig, ax = plt.subplots(figsize=(12, 7))
                        sns.boxplot(data=cleaned_data, x=results['independent_var'], y=dep_var, palette=color_palette, ax=ax)
                        ax.set_title(f'{dep_var} by {results["independent_var"]}', fontsize=14, fontweight='bold')
                        ax.tick_params(axis='x', rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig)

                    with anova_tab3:
                        fig, ax = plt.subplots(figsize=(14, 8))
                        results['tukey_results'].plot_simultaneous(ax=ax)
                        ax.set_title("Tukey HSD Simultaneous Confidence Intervals", fontsize=14, fontweight='bold')
                        ax.grid(True, alpha=0.3, linestyle='--')
                        plt.tight_layout()
                        st.pyplot(fig)

                    effect_label, effect_desc = interpret_effect_size(results['eta_squared'])
                    st.markdown(f"""
                    <div class="info-box">
                        <h4>📏 Effect Size Interpretation</h4>
                        <p><strong>Eta-squared (η²) = {results['eta_squared']:.4f}</strong> → <strong>{effect_label} Effect</strong></p>
                        <p>{effect_desc}. Approximately {results['eta_squared']*100:.2f}% of the variance in <strong>{dep_var}</strong> is explained by <strong>{results['independent_var']}</strong>.</p>
                    </div>
                    """, unsafe_allow_html=True)

                elif analysis_type == "Descriptive Statistics":
                    st.markdown("---")
                    st.markdown("## 📋 Comprehensive Descriptive Statistics")

                    if numeric_cols:
                        desc_stats = cleaned_data[numeric_cols].describe().T
                        desc_stats['skewness'] = cleaned_data[numeric_cols].skew()
                        desc_stats['kurtosis'] = cleaned_data[numeric_cols].kurtosis()
                        desc_stats['missing'] = cleaned_data[numeric_cols].isnull().sum()
                        desc_stats['missing_pct'] = (cleaned_data[numeric_cols].isnull().sum() / len(cleaned_data) * 100).round(2)
                        desc_stats['iqr'] = desc_stats['75%'] - desc_stats['25%']
                        desc_stats['cv'] = (desc_stats['std'] / desc_stats['mean'] * 100).round(2)

                        st.dataframe(desc_stats.round(4), use_container_width=True)

                        st.download_button(
                            "📥 Download Descriptive Stats (CSV)",
                            desc_stats.to_csv(),
                            "descriptive_statistics.csv",
                            "text/csv",
                            use_container_width=True
                        )

                    if categorical_cols:
                        st.markdown("### Categorical Variables")
                        for col in categorical_cols:
                            st.markdown(f"**{col}**")
                            st.dataframe(cleaned_data[col].value_counts().head(10), use_container_width=True)

        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                <h4>❌ Analysis Error</h4>
                <p>{str(e)}</p>
                <p style="font-size:0.85rem;">Please check your variable selections and ensure sufficient data is available.</p>
            </div>
            """, unsafe_allow_html=True)
            st.session_state.error_log.append(f"Analysis error: {str(e)}")

    # PHASE 4
    st.markdown('<p class="phase-header">Phase 4: Export & Reporting</p>', unsafe_allow_html=True)

    if st.session_state.cleaned_data is not None:
        exp_col1, exp_col2, exp_col3 = st.columns(3)

        with exp_col1:
            st.markdown("### 💾 Data Export")
            csv_data = st.session_state.cleaned_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Cleaned Data (CSV)",
                data=csv_data,
                file_name="cleaned_data.csv",
                mime="text/csv",
                use_container_width=True
            )

        with exp_col2:
            st.markdown("### 📄 Report Generation")
            if st.button("📝 Generate Full Report", use_container_width=True):
                with st.spinner("Generating comprehensive report..."):
                    report = generate_insights_report(
                        st.session_state.cleaned_data,
                        numeric_cols,
                        categorical_cols,
                        st.session_state.analysis_results
                    )
                    st.text_area("Automated Insights Report", report, height=400)

                    st.download_button(
                        label="📥 Download Report (TXT)",
                        data=report,
                        file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

        with exp_col3:
            st.markdown("### 📊 Session Info")
            st.markdown(f"**Last Analysis**: {st.session_state.last_analysis or 'None'}")
            st.markdown(f"**Dataset Size**: {len(st.session_state.cleaned_data):,} rows")
            st.markdown(f"**Variables**: {len(st.session_state.cleaned_data.columns)}")
            if st.session_state.error_log:
                st.markdown(f"**Errors**: {len(st.session_state.error_log)}")

# FOOTER
st.markdown(f"""
<div class="footer">
    <p><strong>{APP_NAME} v{APP_VERSION}</strong> | Production-Ready Statistical Analysis Pipeline</p>
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">
        Features: ANOVA • Tukey HSD • Regression • Descriptive Statistics • Automated Data Cleaning
    </p>
    <p style="font-size: 0.75rem; color: #aaa; margin-top: 0.5rem;">
        Built with Python, Streamlit, SciPy, Statsmodels, and Seaborn
    </p>
</div>
""", unsafe_allow_html=True)
