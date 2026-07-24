# API Reference — Turnkey Statistical Analysis Pipeline

## Module: app.py

### Data Processing Functions

#### `clean_column_names(df)`
Standardizes DataFrame column names to snake_case format.

**Parameters:**
- `df` (pd.DataFrame): Input dataframe

**Returns:**
- `pd.DataFrame`: DataFrame with standardized column names

**Example:**
```python
import pandas as pd
from app import clean_column_names

df = pd.DataFrame({'Sales Revenue': [100, 200], 'Region Name': ['A', 'B']})
cleaned = clean_column_names(df)
# Columns become: ['sales_revenue', 'region_name']
```

---

#### `detect_data_types(df)`
Automatically detects and converts column data types.

**Detection Order:**
1. Numeric (if >80% of values convert successfully)
2. Datetime (if >80% of values parse as dates)
3. Categorical (if <10% unique values and <50 categories)
4. Object (fallback for text)

**Parameters:**
- `df` (pd.DataFrame): Input dataframe

**Returns:**
- `pd.DataFrame`: DataFrame with optimized data types

---

#### `handle_missing_values(df, numeric_strategy='median', categorical_strategy='mode')`
Imputes missing values using specified strategies.

**Parameters:**
- `df` (pd.DataFrame): Input dataframe
- `numeric_strategy` (str): 'median', 'mean', or 'drop'
- `categorical_strategy` (str): 'mode', 'constant', or 'drop'

**Returns:**
- `pd.DataFrame`: DataFrame with imputed values

---

### Statistical Analysis Functions

#### `perform_anova(df, dependent_var, independent_var, alpha=0.05)`
Performs One-Way ANOVA and Tukey HSD post-hoc test.

**Parameters:**
- `df` (pd.DataFrame): Cleaned dataset
- `dependent_var` (str): Name of numeric dependent variable
- `independent_var` (str): Name of grouping variable
- `alpha` (float): Significance level (default: 0.05)

**Returns:**
```python
{
    'f_statistic': float,           # ANOVA F-statistic
    'p_value': float,               # ANOVA p-value
    'eta_squared': float,           # Effect size (η²)
    'tukey_results': TukeyHSDResults,  # Post-hoc test object
    'group_stats': DataFrame,       # Descriptive stats by group
    'independent_var': str,         # Actual variable used (may be binned)
    'original_independent_var': str,# Original variable name
    'dependent_var': str,           # Dependent variable name
    'significant': bool,            # Whether p < alpha
    'alpha': float,                 # Significance level used
    'n_observations': int,          # Total valid observations
    'n_groups': int,                # Number of groups
    'levene_test': dict,            # {'statistic': float, 'p_value': float}
    'shapiro_test': dict,           # {'statistic': float, 'p_value': float}
    'assumptions_met': dict         # {'normality': bool, 'homogeneity': bool}
}
```

**Raises:**
- `ValueError`: If variables not found or insufficient data

**Example:**
```python
from app import perform_anova
import pandas as pd

df = pd.DataFrame({
    'score': [85, 90, 78, 92, 88, 75, 80, 95],
    'group': ['A', 'A', 'B', 'B', 'C', 'C', 'A', 'B']
})

results = perform_anova(df, 'score', 'group', alpha=0.05)
print(f"F = {results['f_statistic']:.4f}, p = {results['p_value']:.4f}")
```

---

#### `perform_regression(df, dependent_var, independent_var)`
Performs simple linear regression analysis.

**Parameters:**
- `df` (pd.DataFrame): Cleaned dataset
- `dependent_var` (str): Name of dependent variable (Y)
- `independent_var` (str): Name of independent variable (X)

**Returns:**
```python
{
    'slope': float,                 # Regression slope (β₁)
    'intercept': float,             # Y-intercept (β₀)
    'r_squared': float,             # Coefficient of determination
    'adj_r_squared': float,         # Adjusted R²
    'p_value': float,               # Significance of slope
    'std_err': float,               # Standard error of estimate
    'rmse': float,                  # Root mean squared error
    'residuals': ndarray,           # Residual values
    'predictions': ndarray,         # Predicted values
    'x': ndarray,                   # Independent variable values
    'y': ndarray,                   # Dependent variable values
    'n_observations': int           # Sample size
}
```

**Example:**
```python
from app import perform_regression

results = perform_regression(df, 'sales', 'marketing_spend')
print(f"Equation: sales = {results['intercept']:.2f} + {results['slope']:.4f} * marketing_spend")
```

---

#### `interpret_effect_size(eta_sq)`
Interprets eta-squared effect size using Cohen's guidelines.

**Parameters:**
- `eta_sq` (float): Eta-squared value

**Returns:**
- `tuple`: (effect_size_label, description)

| eta_sq | Label | Description |
|--------|-------|-------------|
| < 0.01 | Negligible | < 1% variance explained |
| 0.01-0.06 | Small | 1-6% variance explained |
| 0.06-0.14 | Medium | 6-14% variance explained |
| > 0.14 | Large | > 14% variance explained |

---

### Reporting Functions

#### `generate_insights_report(df, numeric_cols, categorical_cols, analysis_results=None)`
Generates a comprehensive text report of the analysis.

**Parameters:**
- `df` (pd.DataFrame): Cleaned dataset
- `numeric_cols` (list): List of numeric column names
- `categorical_cols` (list): List of categorical column names
- `analysis_results` (dict, optional): Results from statistical analysis

**Returns:**
- `str`: Formatted text report

---

## Session State Variables

The application uses Streamlit session state to persist data:

| Key | Type | Description |
|-----|------|-------------|
| `data` | DataFrame | Raw uploaded data |
| `cleaned_data` | DataFrame | Processed data after cleaning |
| `analysis_results` | dict | Results from last statistical analysis |
| `last_analysis` | str | Type of last analysis performed |
| `error_log` | list | List of error messages |

---

## Configuration Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `APP_NAME` | "Turnkey Statistical Analysis" | Application name |
| `APP_VERSION` | "1.0.0" | Current version |
| `APP_ICON` | "📊" | UI icon |

---

## Dependencies

### Core
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing

### Statistics
- **scipy.stats**: Statistical tests (f_oneway, linregress, shapiro, levene)
- **statsmodels.stats.multicomp**: Tukey HSD implementation

### Visualization
- **matplotlib**: Base plotting library
- **seaborn**: Statistical visualization

### Optional
- **scikit-learn**: Machine learning utilities (StandardScaler)
- **openpyxl**: Excel file I/O
