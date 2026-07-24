# Architecture Documentation

## System Overview

The Turnkey Statistical Analysis Pipeline is a single-page Streamlit application designed for interactive statistical analysis. It follows a modular architecture with clear separation between data processing, statistical computation, and presentation layers.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Sidebar    │  │  Main Panel │  │  Session State      │ │
│  │  Controls   │  │  Tabs       │  │  Management         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Processing Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Import     │  │  Cleaning   │  │  Type Detection     │ │
│  │  Parser     │  │  Engine     │  │  & Optimization     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Statistical Analysis Layer                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  ANOVA +    │  │  Regression │  │  Descriptive        │ │
│  │  Tukey HSD  │  │  Analysis   │  │  Statistics         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Visualization & Export Layer                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Matplotlib │  │  Seaborn    │  │  Report Generator   │ │
│  │  Charts     │  │  Plots      │  │  (TXT/CSV Export)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Upload Phase**: File → Pandas DataFrame → Type Detection
2. **Cleaning Phase**: Raw Data → Name Standardization → Missing Value Imputation → Deduplication
3. **Profiling Phase**: Cleaned Data → Summary Statistics → Distribution Plots → Correlation Matrix
4. **Analysis Phase**: Cleaned Data → Statistical Test → Results Object → Visualization
5. **Export Phase**: Results → TXT Report / CSV Data → Download

## Key Design Decisions

### Session State Management
- All data and results stored in `st.session_state`
- Prevents re-computation on UI interactions
- Enables state persistence across widget interactions

### Defensive Programming
- Try-except blocks around all file I/O
- Validation of minimum data requirements before analysis
- Graceful degradation when optional features fail

### Statistical Rigor
- Shapiro-Wilk test limited to 5000 samples (performance)
- Automatic binning of continuous grouping variables
- Eta-squared effect size reporting with Cohen's guidelines

## Performance Considerations

| Bottleneck | Mitigation |
|------------|------------|
| Large file uploads | Configurable max upload size (default 200MB) |
| Shapiro-Wilk test | Sample capped at 5000 observations |
| Correlation matrices | Upper triangle masked to reduce rendering |
| DataFrame operations | In-place operations where possible |

## Security

- No persistent storage of uploaded data
- All processing happens in-memory
- No external API calls
- XSS protection via Streamlit's sandboxed execution
