# 🔬 Turkey HSD Analyzer v2.0

> **Advanced ANOVA & Mean Separation Analysis Platform**
>
> A production-ready Streamlit application for One-Way ANOVA, Two-Way ANOVA, and comprehensive mean separation analysis.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What's New in v2.0

### Mean Separation Analysis Toolsets
- **Compact Letter Display (CLD)** — Visual grouping of non-significant means
- **Duncan's Multiple Range Test (MRT)** — Step-down procedure with decreasing critical values
- **Fisher's LSD** — Least Significant Difference test (protected approach)
- **Student-Newman-Keuls (SNK)** — Balanced approach between Tukey and Duncan
- **Scheffe's Test** — Most conservative, valid for all possible contrasts

### Two-Way ANOVA Capabilities
- **Full factorial analysis** with interaction effects
- **Simple Effects Analysis** — Examine one factor within each level of the other
- **Interaction Plots** — Plotly interactive line plots with error bars
- **Profile Plots** — Alternative view of interaction patterns
- **Cell Means Heatmaps** — Visualize all treatment combinations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Installation

```bash
# Clone or download
git clone https://github.com/your-org/turkey-hsd-analyzer.git
cd turkey-hsd-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Launch

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## 📖 Usage Guide

### 1. Upload Data
Upload CSV, Excel, or TXT files via the sidebar. The system auto-detects formats and infers data types.

### 2. Select Analysis Type

| Analysis | When to Use |
|----------|-------------|
| **One-Way ANOVA** | Compare means across 3+ groups with Tukey HSD post-hoc |
| **Two-Way ANOVA** | Analyze two factors simultaneously with interactions |
| **Mean Separation** | Multiple comparison methods (Tukey, Duncan, LSD, SNK, Scheffe) |
| **Descriptive Statistics** | Comprehensive data profiling |
| **Auto-Detect** | Let the system choose based on your data structure |

### 3. Configure & Run
Select variables, set significance level (α), and click **Run Analysis**.

### 4. Interpret Results
- **ANOVA Table** — F-statistics, p-values, effect sizes (η², ω²)
- **Post-Hoc Tests** — Pairwise comparisons with significance indicators
- **Compact Letter Display** — Groups sharing letters are not significantly different
- **Visualizations** — Bar charts, box plots, interaction plots, heatmaps

---

## 📊 Statistical Methods

### One-Way ANOVA
Tests whether means differ across three or more independent groups.

**Assumptions:**
- Independence of observations
- Normally distributed residuals
- Homogeneity of variances

### Two-Way ANOVA
Analyzes two categorical factors and their interaction on a continuous response.

**Key Outputs:**
- Main effects for Factor A and Factor B
- Interaction effect (A × B)
- Simple effects when interaction is significant
- Cell means and marginal means

### Mean Separation Methods

| Method | Conservatism | Best For |
|--------|-------------|----------|
| **Tukey HSD** | Conservative | All pairwise comparisons, balanced designs |
| **Duncan's MRT** | Moderate | Agricultural/experimental research |
| **Fisher's LSD** | Liberal | Exploratory analysis (after significant ANOVA) |
| **SNK Test** | Moderate | General post-hoc testing |
| **Scheffe's Test** | Most Conservative | Complex contrasts, many groups |

### Compact Letter Display (CLD)
Groups sharing the same letter are **NOT** significantly different (p > α).
Groups with different letters **ARE** significantly different.

---

## 🏗️ Project Structure

```
turkey-hsd-analyzer/
│
├── app.py                      # Main entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .streamlit/
│   └── config.toml            # Streamlit configuration
│
├── modules/
│   ├── __init__.py            # Package initialization
│   ├── statistics.py          # Core statistical functions
│   │   ├── perform_anova()           # One-Way ANOVA
│   │   ├── perform_two_way_anova()   # Two-Way ANOVA
│   │   ├── perform_tukey_hsd()       # Tukey HSD
│   │   ├── compact_letter_display()  # CLD generation
│   │   ├── duncans_mrt()             # Duncan's test
│   │   ├── fishers_lsd()             # Fisher's LSD
│   │   ├── snk_test()                # SNK test
│   │   ├── scheffe_test()            # Scheffe's test
│   │   ├── simple_effects_analysis() # Simple effects
│   │   ├── interaction_plot()        # Interaction plot data
│   │   └── profile_plot()            # Profile plot data
│   │
│   └── streamlit_app.py        # Streamlit UI interface
│       ├── render_sidebar()          # Sidebar controls
│       ├── render_one_way_anova()    # One-Way ANOVA UI
│       ├── render_two_way_anova()    # Two-Way ANOVA UI
│       ├── render_mean_separation()  # Mean separation UI
│       └── render_export()           # Export functionality
│
├── data/                       # Sample datasets (generated)
├── outputs/                    # Generated outputs
└── reports/                    # Report templates
```

---

## 🧪 Sample Data

Click **"Generate Agriculture Data"** or **"Generate Clinical Data"** on the welcome screen to create synthetic datasets for immediate testing.

**Agriculture Dataset:**
- Fertilizer types: Control, NPK, Organic, Biochar
- Yield measurements with soil type and replication

**Clinical Dataset:**
- Treatments: Placebo, Drug A, Drug B, Drug C
- Blood pressure with gender and age group

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t turkey-hsd-analyzer .

# Run container
docker run -p 8501:8501 turkey-hsd-analyzer

# Or use docker-compose
docker-compose up -d
```

---

## ☁️ Streamlit Cloud

1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Set main file: `app.py`
4. Deploy

---

## 📋 Requirements

- Python 3.9+
- streamlit >= 1.28.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- scipy >= 1.11.0
- statsmodels >= 0.14.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- plotly >= 5.15.0
- openpyxl >= 3.1.0

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License — See LICENSE file.

---

<p align="center">
  <strong>🔬 Turkey HSD Analyzer v2.0</strong><br>
  <em>Advanced ANOVA. Mean Separation. Production Ready.</em>
</p>
