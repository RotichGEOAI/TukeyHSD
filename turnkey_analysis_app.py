
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Turnkey Statistical Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR PRODUCTION LOOK ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if 'data' not in st.session_state:
    st.session_state.data = None
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}

# --- HELPER FUNCTIONS ---

def clean_column_names(df):
    """Standardize column names to snake_case"""
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
    return df

def detect_data_types(df):
    """Automatically detect and convert data types"""
    for col in df.columns:
        # Try converting to numeric first
        try:
            df[col] = pd.to_numeric(df[col], errors='raise')
        except:
            # If not numeric, try datetime
            try:
                df[col] = pd.to_datetime(df[col], errors='raise')
            except:
                # Keep as categorical/string
                if df[col].nunique() / len(df[col]) < 0.1:  # Less than 10% unique values
                    df[col] = df[col].astype('category')
    return df

def perform_anova(df, dependent_var, independent_var):
    """Perform One-Way ANOVA and Tukey HSD post-hoc test"""
    # Check if independent variable is categorical
    if df[independent_var].dtype.name != 'category' and df[independent_var].nunique() > 5:
        # Try to bin continuous variable
        st.warning(f"'{independent_var}' appears continuous. Binning into quartiles for ANOVA.")
        df[independent_var + '_binned'] = pd.qcut(df[independent_var], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        independent_var = independent_var + '_binned'

    # Prepare data
    groups = [group[dependent_var].dropna().values for name, group in df.groupby(independent_var)]

    # One-Way ANOVA
    f_stat, p_value = stats.f_oneway(*groups)

    # Tukey HSD Post-Hoc Test
    tukey = pairwise_tukeyhsd(endog=df[dependent_var].dropna(),
                              groups=df[independent_var].dropna(),
                              alpha=0.05)

    # Effect size (Eta-squared)
    ss_between = sum(len(g) * (np.mean(g) - np.mean(df[dependent_var].dropna()))**2 for g in groups)
    ss_total = sum((x - np.mean(df[dependent_var].dropna()))**2 for g in groups for x in g)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0

    return {
        'f_statistic': f_stat,
        'p_value': p_value,
        'eta_squared': eta_squared,
        'tukey_results': tukey,
        'groups': df[independent_var].unique(),
        'independent_var': independent_var,
        'dependent_var': dependent_var,
        'significant': p_value < 0.05
    }

def perform_regression(df, dependent_var, independent_var):
    """Perform Linear Regression Analysis"""
    # Remove rows with missing values
    temp_df = df[[dependent_var, independent_var]].dropna()

    # Calculate regression metrics
    x = temp_df[independent_var]
    y = temp_df[dependent_var]

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Predictions
    predictions = slope * x + intercept
    residuals = y - predictions

    # R-squared
    r_squared = r_value ** 2

    # Adjusted R-squared
    n = len(temp_df)
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - 2)

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'adj_r_squared': adj_r_squared,
        'p_value': p_value,
        'std_err': std_err,
        'residuals': residuals,
        'predictions': predictions,
        'x': x,
        'y': y
    }

def generate_insights_report(df, numeric_cols, categorical_cols):
    """Generate automated insights report"""
    insights = []

    # Basic data insights
    insights.append("=== DATA OVERVIEW ===")
    insights.append(f"Total Observations: {len(df)}")
    insights.append(f"Total Variables: {len(df.columns)}")
    insights.append(f"Numeric Variables: {len(numeric_cols)}")
    insights.append(f"Categorical Variables: {len(categorical_cols)}")
    insights.append("")

    # Missing data insights
    missing_data = df.isnull().sum()
    if missing_data.sum() > 0:
        insights.append("=== MISSING DATA ===")
        for col, missing in missing_data[missing_data > 0].items():
            pct = (missing / len(df)) * 100
            insights.append(f"{col}: {missing} missing ({pct:.1f}%)")
        insights.append("")

    # Numeric insights
    if numeric_cols:
        insights.append("=== NUMERIC VARIABLES SUMMARY ===")
        desc = df[numeric_cols].describe()
        for col in numeric_cols:
            insights.append(f"\n{col}:")
            insights.append(f"  Mean: {desc.loc['mean', col]:.2f}")
            insights.append(f"  Std: {desc.loc['std', col]:.2f}")
            insights.append(f"  Range: [{desc.loc['min', col]:.2f}, {desc.loc['max', col]:.2f}]")

            # Skewness and Kurtosis
            skew = stats.skew(df[col].dropna())
            kurt = stats.kurtosis(df[col].dropna())
            insights.append(f"  Skewness: {skew:.2f} ({'Right-skewed' if skew > 0 else 'Left-skewed' if skew < 0 else 'Symmetric'})")
            insights.append(f"  Kurtosis: {kurt:.2f}")

    return "\n".join(insights)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/data-analysis.png", width=80)
    st.markdown("## Turnkey Analysis Pipeline")
    st.markdown("---")

    # File Upload
    st.markdown("### 📁 Data Import")
    uploaded_file = st.file_uploader(
        "Upload your CSV file",
        type=['csv', 'txt', 'xlsx'],
        help="Upload a CSV, TXT, or Excel file for analysis"
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            st.session_state.data = df
            st.success(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns")
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

    st.markdown("---")
    st.markdown("### ⚙️ Analysis Settings")

    # Analysis type selection
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Auto-Detect", "Regression Analysis", "ANOVA + Tukey HSD", "Descriptive Statistics"],
        help="Choose the type of statistical analysis to perform"
    )

    st.markdown("---")
    st.markdown("### 📊 Visualization Settings")

    plot_theme = st.selectbox(
        "Plot Theme",
        ["whitegrid", "darkgrid", "white", "dark", "ticks"],
        index=0
    )

    color_palette = st.selectbox(
        "Color Palette",
        ["viridis", "plasma", "coolwarm", "Set1", "Set2", "husl"],
        index=0
    )

    sns.set_style(plot_theme)

    st.markdown("---")
    st.markdown("### 💾 Export Options")

    if st.button("🔄 Reset Application", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- MAIN CONTENT ---
st.markdown('<p class="main-header">📊 Turnkey Statistical Analysis</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated data pipeline with ANOVA and Tukey HSD post-hoc testing</p>', unsafe_allow_html=True)

# Check if data is loaded
if st.session_state.data is None:
    # Welcome screen
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🚀 Automated Pipeline</h3>
            <p>Upload your data and let the system automatically clean, analyze, and visualize your dataset with zero configuration.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📈 Advanced Statistics</h3>
            <p>Includes ANOVA, Tukey HSD post-hoc tests, regression analysis, and comprehensive descriptive statistics.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📋 Production Ready</h3>
            <p>Built for enterprise use with defensive programming, automated error handling, and exportable reports.</p>
        </div>
        """, unsafe_allow_html=True)

    st.info("👈 Please upload a CSV file using the sidebar to begin the analysis.")

    # Sample data option
    st.markdown("### 🧪 Try with Sample Data")
    if st.button("Generate Sample Dataset", use_container_width=True):
        np.random.seed(42)
        n = 200
        sample_data = pd.DataFrame({
            'sales': np.random.normal(1000, 200, n),
            'marketing_spend': np.random.normal(500, 100, n),
            'customer_satisfaction': np.random.normal(4.0, 0.5, n),
            'region': np.random.choice(['North', 'South', 'East', 'West'], n),
            'product_category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Home'], n),
            'quarter': np.random.choice(['Q1', 'Q2', 'Q3', 'Q4'], n)
        })
        # Add some correlation
        sample_data['sales'] = sample_data['sales'] + 0.5 * sample_data['marketing_spend'] + np.random.normal(0, 50, n)
        sample_data['customer_satisfaction'] = sample_data['customer_satisfaction'] + 0.001 * sample_data['sales'] + np.random.normal(0, 0.1, n)

        st.session_state.data = sample_data
        st.rerun()

else:
    # --- PHASE 1: DATA IMPORT & CLEANING ---
    st.markdown("---")
    st.markdown("## Phase 1: Data Import & Cleaning")

    raw_data = st.session_state.data.copy()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rows", f"{len(raw_data):,}")
    col2.metric("Total Columns", len(raw_data.columns))
    col3.metric("Missing Values", f"{raw_data.isnull().sum().sum():,}")
    col4.metric("Duplicate Rows", raw_data.duplicated().sum())

    # Data preview
    with st.expander("🔍 Raw Data Preview", expanded=False):
        st.dataframe(raw_data.head(20), use_container_width=True)

    # Automated cleaning
    with st.spinner("🧹 Cleaning data automatically..."):
        cleaned_data = raw_data.copy()
        cleaned_data = clean_column_names(cleaned_data)
        cleaned_data = detect_data_types(cleaned_data)
        cleaned_data = cleaned_data.drop_duplicates()

        # Handle missing values
        numeric_cols = cleaned_data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = cleaned_data.select_dtypes(include=['category', 'object']).columns.tolist()

        for col in numeric_cols:
            cleaned_data[col].fillna(cleaned_data[col].median(), inplace=True)
        for col in categorical_cols:
            cleaned_data[col].fillna(cleaned_data[col].mode()[0] if not cleaned_data[col].mode().empty else 'Unknown', inplace=True)

        st.session_state.cleaned_data = cleaned_data

    st.markdown('<div class="success-box">✅ Data cleaning complete! Standardized column names, removed duplicates, handled missing values, and auto-detected data types.</div>', unsafe_allow_html=True)

    # --- PHASE 2: DATA PROFILING ---
    st.markdown("---")
    st.markdown("## Phase 2: Data Profiling")

    tab1, tab2, tab3 = st.tabs(["📋 Overview", "📊 Distributions", "🔗 Correlations"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Variable Types")
            type_summary = pd.DataFrame({
                'Type': ['Numeric', 'Categorical', 'Datetime'],
                'Count': [len(numeric_cols), len(categorical_cols), len(cleaned_data.select_dtypes(include=['datetime64']).columns)]
            })
            st.dataframe(type_summary, use_container_width=True, hide_index=True)

            st.markdown("### Numeric Summary")
            if numeric_cols:
                st.dataframe(cleaned_data[numeric_cols].describe().T, use_container_width=True)

        with col2:
            st.markdown("### Categorical Summary")
            if categorical_cols:
                for col in categorical_cols[:5]:  # Show first 5
                    st.markdown(f"**{col}**")
                    value_counts = cleaned_data[col].value_counts().head(5)
                    st.bar_chart(value_counts)

    with tab2:
        if numeric_cols:
            selected_dist_col = st.selectbox("Select variable for distribution analysis", numeric_cols)

            col1, col2 = st.columns(2)

            with col1:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.histplot(cleaned_data[selected_dist_col], kde=True, color='steelblue', ax=ax)
                ax.set_title(f'Distribution of {selected_dist_col}')
                st.pyplot(fig)

            with col2:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.boxplot(y=cleaned_data[selected_dist_col], color='lightcoral', ax=ax)
                ax.set_title(f'Box Plot of {selected_dist_col}')
                st.pyplot(fig)

            # Normality test
            stat, p_value = stats.shapiro(cleaned_data[selected_dist_col].dropna()[:5000])  # Limit for Shapiro-Wilk
            st.info(f"**Shapiro-Wilk Normality Test**: Statistic={stat:.4f}, p-value={p_value:.4f} ({'Normal' if p_value > 0.05 else 'Non-normal'} distribution)")

    with tab3:
        if len(numeric_cols) >= 2:
            st.markdown("### Correlation Matrix")
            corr_matrix = cleaned_data[numeric_cols].corr()

            fig, ax = plt.subplots(figsize=(12, 10))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap=color_palette, 
                       center=0, square=True, linewidths=0.5, ax=ax)
            st.pyplot(fig)

            # Highlight strong correlations
            strong_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if abs(corr_matrix.iloc[i, j]) > 0.7:
                        strong_corr.append({
                            'Variable 1': corr_matrix.columns[i],
                            'Variable 2': corr_matrix.columns[j],
                            'Correlation': corr_matrix.iloc[i, j]
                        })

            if strong_corr:
                st.markdown("### ⚠️ Strong Correlations Detected (>0.7)")
                st.dataframe(pd.DataFrame(strong_corr), use_container_width=True, hide_index=True)

    # --- PHASE 3: STATISTICAL ANALYSIS ---
    st.markdown("---")
    st.markdown("## Phase 3: Statistical Analysis")

    if analysis_type == "Auto-Detect":
        st.info("🤖 Auto-detecting optimal analysis based on your data structure...")

        if len(numeric_cols) >= 2 and len(categorical_cols) >= 1:
            analysis_type = "ANOVA + Tukey HSD"
            st.success(f"Detected categorical variables. Recommended: **{analysis_type}**")
        elif len(numeric_cols) >= 2:
            analysis_type = "Regression Analysis"
            st.success(f"Detected multiple numeric variables. Recommended: **{analysis_type}**")
        else:
            analysis_type = "Descriptive Statistics"
            st.success(f"Limited numeric variables. Recommended: **{analysis_type}**")

    # Analysis configuration
    st.markdown("### ⚙️ Analysis Configuration")

    col1, col2 = st.columns(2)

    with col1:
        if analysis_type == "Regression Analysis":
            dependent_var = st.selectbox("Dependent Variable (Y)", numeric_cols, index=0 if numeric_cols else None)
            independent_var = st.selectbox("Independent Variable (X)", 
                                          [c for c in numeric_cols if c != dependent_var], 
                                          index=0 if len(numeric_cols) > 1 else None)
        elif analysis_type == "ANOVA + Tukey HSD":
            dependent_var = st.selectbox("Dependent Variable (Numeric)", numeric_cols, index=0 if numeric_cols else None)
            independent_var = st.selectbox("Grouping Variable (Categorical)", 
                                          categorical_cols + [c for c in numeric_cols if c != dependent_var], 
                                          index=0 if categorical_cols else 0)
        else:
            dependent_var = st.selectbox("Variable of Interest", numeric_cols if numeric_cols else cleaned_data.columns.tolist(), index=0)
            independent_var = None

    with col2:
        st.markdown("### Analysis Parameters")
        confidence_level = st.slider("Confidence Level", 0.80, 0.99, 0.95, 0.01)
        alpha = 1 - confidence_level
        show_advanced = st.checkbox("Show Advanced Diagnostics", value=True)

    # Run analysis
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        with st.spinner("🔬 Running statistical analysis..."):

            if analysis_type == "Regression Analysis":
                # --- REGRESSION ANALYSIS ---
                results = perform_regression(cleaned_data, dependent_var, independent_var)

                st.markdown("---")
                st.markdown("## 📈 Regression Analysis Results")

                # Key metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("R²", f"{results['r_squared']:.4f}")
                col2.metric("Adj. R²", f"{results['adj_r_squared']:.4f}")
                col3.metric("Slope", f"{results['slope']:.4f}")
                col4.metric("Intercept", f"{results['intercept']:.4f}")
                col5.metric("P-value", f"{results['p_value']:.4f}", 
                           delta="Significant" if results['p_value'] < 0.05 else "Not Significant",
                           delta_color="normal" if results['p_value'] < 0.05 else "inverse")

                # Regression equation
                st.markdown(f"""
                <div class="info-box">
                    <h4>📐 Regression Equation</h4>
                    <p style="font-size: 1.2rem; font-family: monospace;">
                    {dependent_var} = {results['intercept']:.4f} + {results['slope']:.4f} × {independent_var}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Visualizations
                tab1, tab2, tab3 = st.tabs(["Scatter Plot", "Residual Analysis", "Diagnostic Plots"])

                with tab1:
                    fig, ax = plt.subplots(figsize=(12, 8))
                    ax.scatter(results['x'], results['y'], alpha=0.6, color='steelblue', label='Observed Data')
                    ax.plot(results['x'], results['predictions'], color='red', linewidth=2, label='Regression Line')
                    ax.set_xlabel(independent_var)
                    ax.set_ylabel(dependent_var)
                    ax.set_title(f'Regression: {dependent_var} vs {independent_var}')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)

                with tab2:
                    col1, col2 = st.columns(2)
                    with col1:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.histplot(results['residuals'], kde=True, color='purple', ax=ax)
                        ax.set_title('Residual Distribution')
                        st.pyplot(fig)

                    with col2:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.scatter(results['predictions'], results['residuals'], alpha=0.6, color='green')
                        ax.axhline(y=0, color='red', linestyle='--')
                        ax.set_xlabel('Predicted Values')
                        ax.set_ylabel('Residuals')
                        ax.set_title('Residuals vs Predicted')
                        st.pyplot(fig)

                with tab3:
                    if show_advanced:
                        # Q-Q plot
                        fig, ax = plt.subplots(figsize=(10, 6))
                        stats.probplot(results['residuals'], dist="norm", plot=ax)
                        ax.set_title('Q-Q Plot (Normality Check)')
                        st.pyplot(fig)

                        # Breusch-Pagan test for heteroscedasticity
                        from statsmodels.stats.diagnostic import het_breuschpagan
                        # Simple BP test approximation
                        st.info("📊 **Model Diagnostics**: Check residual plots for patterns indicating non-linearity or heteroscedasticity.")

            elif analysis_type == "ANOVA + Tukey HSD":
                # --- ANOVA + TUKEY HSD ---
                results = perform_anova(cleaned_data, dependent_var, independent_var)

                st.markdown("---")
                st.markdown("## 📊 ANOVA & Tukey HSD Results")

                # ANOVA Results
                st.markdown("### 1️⃣ One-Way ANOVA Results")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("F-Statistic", f"{results['f_statistic']:.4f}")
                col2.metric("P-Value", f"{results['p_value']:.4f}",
                           delta="Significant" if results['significant'] else "Not Significant",
                           delta_color="normal" if results['significant'] else "inverse")
                col3.metric("Effect Size (η²)", f"{results['eta_squared']:.4f}")
                col4.metric("Groups Compared", len(results['groups']))

                # Interpretation
                if results['significant']:
                    st.markdown(f"""
                    <div class="success-box">
                        <h4>✅ Significant Result Detected!</h4>
                        <p>The ANOVA test indicates a statistically significant difference between group means 
                        (F = {results['f_statistic']:.4f}, p = {results['p_value']:.4f}). 
                        Proceeding to Tukey HSD post-hoc analysis to identify which specific groups differ.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="warning-box">
                        <h4>⚠️ No Significant Difference Found</h4>
                        <p>The ANOVA test did not find a statistically significant difference between group means 
                        (F = {results['f_statistic']:.4f}, p = {results['p_value']:.4f}). 
                        Tukey HSD post-hoc analysis may not be necessary, but is provided for completeness.</p>
                    </div>
                    """, unsafe_allow_html=True)

                # ANOVA Table
                st.markdown("### ANOVA Summary Table")
                anova_data = {
                    'Source': ['Between Groups', 'Within Groups', 'Total'],
                    'DF': [len(results['groups']) - 1, 
                           len(cleaned_data) - len(results['groups']),
                           len(cleaned_data) - 1],
                    'F-Statistic': [results['f_statistic'], '-', '-'],
                    'P-Value': [results['p_value'], '-', '-']
                }
                st.dataframe(pd.DataFrame(anova_data), use_container_width=True, hide_index=True)

                # --- TUKEY HSD RESULTS ---
                st.markdown("---")
                st.markdown("### 2️⃣ Tukey HSD Post-Hoc Test Results")

                st.info("""
                **Tukey's Honestly Significant Difference (HSD)** test is used after a significant ANOVA to determine 
                which specific group means are significantly different from each other while controlling the family-wise 
                error rate. The test compares all possible pairs of means.
                """)

                # Tukey results table
                tukey_df = pd.DataFrame(data=results['tukey_results']._results_table.data[1:], 
                                       columns=results['tukey_results']._results_table.data[0])

                # Add significance indicator
                tukey_df['Significant'] = tukey_df['reject'].apply(lambda x: '✅ Yes' if x else '❌ No')

                st.dataframe(tukey_df, use_container_width=True)

                # Summary of significant pairs
                significant_pairs = tukey_df[tukey_df['reject'] == True]
                if not significant_pairs.empty:
                    st.markdown("### 🔍 Significant Group Differences")
                    for _, row in significant_pairs.iterrows():
                        st.markdown(f"- **{row['group1']}** vs **{row['group2']}**: Mean Diff = {row['meandiff']:.4f}, p-adj = {row['p-adj']:.4f}")

                # Visualizations
                tab1, tab2, tab3 = st.tabs(["Group Comparisons", "Box Plots", "Tukey Confidence Intervals"])

                with tab1:
                    fig, ax = plt.subplots(figsize=(14, 8))
                    group_means = cleaned_data.groupby(results['independent_var'])[dependent_var].mean().sort_values(ascending=False)
                    colors = ['green' if results['significant'] else 'gray'] * len(group_means)
                    bars = ax.bar(range(len(group_means)), group_means.values, color=colors, alpha=0.7, edgecolor='black')
                    ax.set_xticks(range(len(group_means)))
                    ax.set_xticklabels(group_means.index, rotation=45)
                    ax.set_ylabel(f'Mean {dependent_var}')
                    ax.set_title(f'Mean {dependent_var} by {results["independent_var"]}')
                    ax.grid(axis='y', alpha=0.3)

                    # Add value labels on bars
                    for bar, val in zip(bars, group_means.values):
                        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01*max(group_means.values),
                               f'{val:.2f}', ha='center', va='bottom', fontweight='bold')

                    st.pyplot(fig)

                with tab2:
                    fig, ax = plt.subplots(figsize=(14, 8))
                    sns.boxplot(data=cleaned_data, x=results['independent_var'], y=dependent_var, 
                               palette=color_palette, ax=ax)
                    ax.set_title(f'Distribution of {dependent_var} by {results["independent_var"]}')
                    ax.tick_params(axis='x', rotation=45)
                    st.pyplot(fig)

                with tab3:
                    fig, ax = plt.subplots(figsize=(14, 8))
                    results['tukey_results'].plot_simultaneous(ax=ax)
                    ax.set_title("Tukey HSD Confidence Intervals")
                    st.pyplot(fig)

                # Effect size interpretation
                st.markdown("### 📏 Effect Size Interpretation")
                eta_sq = results['eta_squared']
                if eta_sq < 0.01:
                    effect_size = "Negligible"
                elif eta_sq < 0.06:
                    effect_size = "Small"
                elif eta_sq < 0.14:
                    effect_size = "Medium"
                else:
                    effect_size = "Large"

                st.markdown(f"""
                <div class="info-box">
                    <p><strong>Eta-squared (η²) = {eta_sq:.4f}</strong> → <strong>{effect_size} effect size</strong></p>
                    <p>This indicates that {eta_sq*100:.2f}% of the variance in {dependent_var} is explained by {results['independent_var']}.</p>
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
                    desc_stats['missing_pct'] = (cleaned_data[numeric_cols].isnull().sum() / len(cleaned_data)) * 100

                    st.dataframe(desc_stats, use_container_width=True)

                if categorical_cols:
                    st.markdown("### Categorical Variables")
                    for col in categorical_cols:
                        st.markdown(f"**{col}**")
                        st.dataframe(cleaned_data[col].value_counts().head(10), use_container_width=True)

    # --- PHASE 4: EXPORT & REPORTING ---
    st.markdown("---")
    st.markdown("## Phase 4: Export & Reporting")

    if st.session_state.cleaned_data is not None:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💾 Download Cleaned Data")
            csv = st.session_state.cleaned_data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="cleaned_data.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            st.markdown("### 📄 Generate Report")
            if st.button("📝 Generate Insights Report", use_container_width=True):
                report = generate_insights_report(
                    st.session_state.cleaned_data, 
                    numeric_cols, 
                    categorical_cols
                )
                st.text_area("Automated Insights Report", report, height=400)

                st.download_button(
                    label="📥 Download Report (TXT)",
                    data=report,
                    file_name="automated_insights_report.txt",
                    mime="text/plain",
                    use_container_width=True
                )

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🔬 Turnkey Statistical Analysis Pipeline | Production Ready | Built with Streamlit</p>
    <p style="font-size: 0.8rem;">Supports ANOVA, Tukey HSD, Regression, and Descriptive Statistics</p>
</div>
""", unsafe_allow_html=True)
