# User Guide — Turnkey Statistical Analysis Pipeline

## Table of Contents
1. [Getting Started](#getting-started)
2. [Uploading Data](#uploading-data)
3. [Understanding the Pipeline Phases](#understanding-the-pipeline-phases)
4. [ANOVA + Tukey HSD Tutorial](#anova--tukey-hsd-tutorial)
5. [Regression Analysis Tutorial](#regression-analysis-tutorial)
6. [Interpreting Results](#interpreting-results)
7. [Exporting Data](#exporting-data)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection (for initial load; analysis runs locally)
- Screen resolution: 1280x720 or higher recommended

### First Launch
1. Open your terminal/command prompt
2. Navigate to the project directory
3. Run: `streamlit run app.py`
4. Your browser will open to `http://localhost:8501`

---

## Uploading Data

### Supported File Formats
| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Comma-separated values |
| Excel | `.xlsx`, `.xls` | Microsoft Excel files |
| TSV | `.txt` | Tab-separated values |

### Data Requirements
- **Minimum**: 10 rows, 2 columns
- **Recommended**: 50+ rows for reliable statistical inference
- **Maximum**: Tested with datasets up to 100,000 rows

### Column Types
The app auto-detects:
- **Numeric**: Continuous or discrete numbers
- **Categorical**: Text labels with low cardinality (< 10% unique)
- **Datetime**: Date and time strings

---

## Understanding the Pipeline Phases

### Phase 1: Data Import & Cleaning
- Displays raw data metrics (rows, columns, missing values)
- Automatically applies:
  - Snake_case column naming
  - Duplicate row removal
  - Missing value imputation
  - Data type inference

### Phase 2: Data Profiling
Three tabs provide comprehensive exploration:
- **Overview**: Variable counts, quick statistics
- **Distributions**: Histograms, box plots, normality tests
- **Correlations**: Heatmap with strong correlation alerts

### Phase 3: Statistical Analysis
The core analysis engine with configurable parameters.

### Phase 4: Export & Reporting
Download cleaned data, generate comprehensive reports, and review session info.

---

## ANOVA + Tukey HSD Tutorial

### What is ANOVA?
**Analysis of Variance (ANOVA)** tests whether the means of three or more groups are significantly different. It answers: *"Do at least two groups have different means?"*

### What is Tukey HSD?
**Tukey's Honestly Significant Difference (HSD)** is a post-hoc test that runs after a significant ANOVA. It answers: *"Which specific pairs of groups are different?"* while controlling the family-wise error rate.

### Step-by-Step Walkthrough

#### Step 1: Select "ANOVA + Tukey HSD"
In the sidebar, choose this analysis type or let Auto-Detect select it.

#### Step 2: Choose Variables
- **Dependent Variable**: Select a numeric column (e.g., `sales_revenue`)
- **Grouping Variable**: Select a categorical column (e.g., `region`)
  - If you select a numeric grouping variable with >5 unique values, it will be auto-binned into quartiles

#### Step 3: Set Parameters
- **Confidence Level**: Default 95% (α = 0.05)
- **Advanced Diagnostics**: Enable for assumption checking

#### Step 4: Run Analysis
Click **"Run Statistical Analysis"** and review results:

**ANOVA Results Panel:**
- F-Statistic: The test statistic
- P-Value: Significance indicator
- Effect Size (η²): Variance explained
- Groups: Number of groups compared

**Tukey HSD Results Panel:**
- All pairwise comparisons
- Mean differences
- Adjusted p-values
- Confidence intervals
- Significance indicators (✅/❌)

**Visualizations:**
- Group mean bar chart
- Box plots by group
- Tukey simultaneous confidence intervals

### Interpreting ANOVA Results
| P-Value | Interpretation | Action |
|---------|---------------|--------|
| < 0.05 | Significant difference exists | Examine Tukey HSD results |
| ≥ 0.05 | No significant difference | Consider other analyses |

### Interpreting Tukey HSD Results
Look for rows where `reject = True`:
- These pairs have statistically different means
- The `meandiff` column shows the direction and magnitude
- `p-adj` is the adjusted p-value (already corrected for multiple comparisons)

---

## Regression Analysis Tutorial

### When to Use
Use regression when you want to model the relationship between two numeric variables.

### Configuration
1. Select **"Regression Analysis"**
2. Choose **Dependent Variable (Y)**: The outcome you want to predict
3. Choose **Independent Variable (X)**: The predictor

### Reading Results
- **R²**: Proportion of variance explained (0-1, higher is better)
- **P-value**: Significance of the relationship
- **Slope**: Change in Y per unit change in X
- **Equation**: Use for predictions

### Diagnostics
- **Residual Distribution**: Should be approximately normal
- **Q-Q Plot**: Points should follow the diagonal line
- **Residuals vs Predicted**: Should show random scatter (no patterns)

---

## Interpreting Results

### Effect Size Guidelines (Eta-squared)
| η² Value | Effect Size | Interpretation |
|----------|-------------|----------------|
| < 0.01 | Negligible | < 1% variance explained |
| 0.01 - 0.06 | Small | 1-6% variance explained |
| 0.06 - 0.14 | Medium | 6-14% variance explained |
| > 0.14 | Large | > 14% variance explained |

### Assumption Checking
The app automatically tests:
1. **Normality** (Shapiro-Wilk): p > 0.05 indicates normal distribution
2. **Homogeneity** (Levene): p > 0.05 indicates equal variances
3. **Independence**: Assumed by experimental design

---

## Exporting Data

### Cleaned Data
- Format: CSV
- Contents: Fully processed dataset with standardized names and imputed values

### Analysis Report
- Format: Plain text (.txt)
- Contents: Complete statistical summary, test results, and interpretations
- Timestamped filename for version control

### Descriptive Statistics
- Format: CSV
- Contents: Full descriptive statistics table with skewness, kurtosis, IQR, CV

---

## Troubleshooting

### "Insufficient data for ANOVA"
- Ensure at least 10 total observations
- Check that your grouping variable has at least 2 groups
- Verify no group has fewer than 2 observations

### "Variable not found"
- Column names are converted to snake_case (spaces → underscores)
- Check the cleaned data preview for actual column names

### "No significant difference found"
- This is a valid statistical result
- Consider increasing sample size or examining effect size
- Check if assumptions are violated (see Assumptions Check table)

### Visualizations not rendering
- Ensure matplotlib and seaborn are properly installed
- Try refreshing the page (F5)
- Check browser console for JavaScript errors

### Performance issues with large datasets
- Datasets > 50,000 rows may experience slower rendering
- Consider sampling your data for initial exploration
- The Shapiro-Wilk test automatically samples to 5,000 observations

---

## Tips for Best Results

1. **Pre-clean your data**: Remove obvious outliers before upload
2. **Check variable types**: Ensure numeric columns don't contain text
3. **Sufficient sample size**: Aim for at least 20 observations per group for ANOVA
4. **Balanced groups**: ANOVA works best with roughly equal group sizes
5. **Document your workflow**: Use the generated reports for reproducibility
