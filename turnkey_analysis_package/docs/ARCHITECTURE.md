# Technical Architecture — Turnkey Statistical Analysis Pipeline

## Overview

This document describes the technical architecture, design decisions, and implementation details of the Turnkey Statistical Analysis Pipeline.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (Streamlit)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Sidebar    │  │  Main       │  │  Visualization      │  │
│  │  Controls   │  │  Content    │  │  Engine             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Data       │  │  Statistical│  │  Reporting          │  │
│  │  Processing │  │  Analysis   │  │  Engine             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Pandas     │  │  NumPy      │  │  Session State      │  │
│  │  DataFrames │  │  Arrays     │  │  Management         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Data Processing Pipeline

```
Raw Upload → Type Detection → Cleaning → Validation → Analysis Ready
```

**Functions:**
- `clean_column_names()`: Regex-based snake_case conversion
- `detect_data_types()`: Heuristic-based type inference
- `handle_missing_values()`: Strategy-based imputation

### 2. Statistical Analysis Engine

**ANOVA + Tukey HSD Workflow:**
```
Input Data → Validate Variables → Auto-Bin (if needed) 
    → One-Way ANOVA (scipy.stats.f_oneway)
    → Effect Size Calculation (eta-squared)
    → Assumption Testing (Shapiro-Wilk, Levene)
    → Tukey HSD (statsmodels.pairwise_tukeyhsd)
    → Results Compilation
```

**Regression Workflow:**
```
Input Data → Validate Variables → Linear Regression (scipy.stats.linregress)
    → Diagnostics (R², RMSE, residuals)
    → Visualization Generation
```

### 3. Visualization System

Built on Matplotlib + Seaborn with:
- Dynamic theming (whitegrid, darkgrid, etc.)
- Configurable color palettes
- Responsive figure sizing
- Export-ready plots

### 4. Session State Management

Streamlit's session state persists:
- Uploaded data across reruns
- Analysis results for export
- Error logs for debugging
- User preferences

## Design Patterns

### Defensive Programming
- Input validation before analysis
- Graceful error handling with user-friendly messages
- Automatic fallback strategies (e.g., binning continuous variables)

### Separation of Concerns
- Data processing isolated from analysis
- Analysis logic separated from visualization
- Reporting decoupled from computation

### Configuration over Code
- Analysis parameters configurable via UI
- Visualization settings adjustable in sidebar
- Export formats selectable by user

## Data Flow

```
1. User uploads file → stored in session_state.data
2. Cleaning pipeline → produces session_state.cleaned_data
3. User selects analysis → configuration stored
4. Analysis execution → results stored in session_state.analysis_results
5. Visualization → rendered from results
6. Export → generated from cleaned_data and analysis_results
```

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| UI | Streamlit | >=1.28 | Web application framework |
| Data | Pandas | >=2.0 | Data manipulation |
| Compute | NumPy | >=1.24 | Numerical operations |
| Statistics | SciPy | >=1.11 | Statistical tests |
| Statistics | Statsmodels | >=0.14 | ANOVA, Tukey HSD |
| Visualization | Matplotlib | >=3.7 | Base plotting |
| Visualization | Seaborn | >=0.12 | Statistical plots |
| ML | Scikit-learn | >=1.3 | Preprocessing utilities |
| I/O | OpenPyXL | >=3.1 | Excel file support |

## Performance Considerations

### Dataset Size Handling
- **Small (< 1,000 rows)**: Full analysis, all diagnostics
- **Medium (1,000 - 50,000 rows)**: Sampling for normality tests
- **Large (> 50,000 rows)**: Consider data preprocessing before upload

### Optimization Strategies
1. **Lazy Loading**: Data preview limited to first 15 rows
2. **Sampling**: Shapiro-Wilk test limited to 5,000 observations
3. **Caching**: Session state prevents recomputation
4. **Vectorization**: NumPy operations for statistical computing

## Error Handling Strategy

| Error Type | Handling | User Feedback |
|------------|----------|---------------|
| File format | Try multiple parsers | Specific error message |
| Missing variables | Validation check | Suggest available columns |
| Insufficient data | Minimum threshold | Recommend minimum sample size |
| Assumption violations | Flag in results | Warning with interpretation |
| Computation errors | Try-except blocks | Friendly error box |

## Security Considerations

1. **File Upload**: Only CSV, Excel, TXT accepted
2. **Data Privacy**: All processing happens locally
3. **Session Isolation**: Each user has independent session state
4. **No External Calls**: No API keys or external services required

## Future Enhancements

### Planned Features
- [ ] Two-way ANOVA with interaction effects
- [ ] Non-parametric alternatives (Kruskal-Wallis, Mann-Whitney)
- [ ] Multiple regression with variable selection
- [ ] Time series analysis components
- [ ] Automated report generation (PDF)
- [ ] Data transformation utilities (log, square root)

### Scalability Roadmap
- [ ] Database connector support (SQL, BigQuery)
- [ ] Distributed computing for large datasets
- [ ] Caching layer for repeated analyses
- [ ] REST API for programmatic access
