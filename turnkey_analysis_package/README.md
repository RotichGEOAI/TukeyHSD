# 📊 Turnkey Statistical Analysis Pipeline

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-ff4b4b.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **production-ready Streamlit application** for automated statistical analysis, replicating and enhancing the R turnkey operations pipeline with full support for **ANOVA and Tukey HSD post-hoc testing**.

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| **📁 Automated Data Import** | CSV, Excel (.xlsx/.xls), TXT with auto-detection |
| **🧹 Smart Data Cleaning** | Snake_case naming, duplicate removal, missing value imputation, auto type detection |
| **📊 ANOVA + Tukey HSD** | One-way ANOVA with automatic Tukey Honestly Significant Difference post-hoc testing |
| **📈 Regression Analysis** | Simple linear regression with R², diagnostics, and residual analysis |
| **📋 Descriptive Statistics** | Comprehensive profiling with normality tests and effect sizes |
| **🤖 Auto-Detect Mode** | Automatically selects optimal analysis based on data structure |
| **📄 Export & Reporting** | Download cleaned data, comprehensive TXT reports, and CSV statistics |
| **🎨 Customizable Visualizations** | Multiple themes and color palettes |

---

## 📦 Installation

### Prerequisites
- Python >= 3.9
- pip package manager

### Quick Start

```bash
# 1. Clone or download the repository
cd turnkey_analysis_package

# 2. Create a virtual environment (recommended)
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the application
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

---

## 📖 Usage Guide

### Step 1: Upload Your Data
- Use the sidebar to upload a CSV, Excel, or TXT file
- Or click **"Generate Sample Dataset"** to test with built-in demo data

### Step 2: Automated Cleaning
The pipeline automatically:
- Standardizes column names to `snake_case`
- Removes duplicate rows
- Imputes missing values (median for numeric, mode for categorical)
- Auto-detects data types (numeric, categorical, datetime)

### Step 3: Select Analysis Type
Choose from the sidebar:
- **Auto-Detect** — Recommends analysis based on your data
- **ANOVA + Tukey HSD** — Compare group means with post-hoc testing
- **Regression Analysis** — Simple linear regression with diagnostics
- **Descriptive Statistics** — Comprehensive data profiling

### Step 4: Configure & Run
- Select your dependent and independent variables
- Adjust confidence level (default: 95%)
- Toggle advanced diagnostics
- Click **"Run Statistical Analysis"**

### Step 5: Export Results
- Download cleaned data as CSV
- Generate and download comprehensive analysis reports
- Export descriptive statistics

---

## 🔬 ANOVA + Tukey HSD Explained

### When to Use
ANOVA (Analysis of Variance) tests whether there are statistically significant differences between the means of three or more independent groups. Tukey HSD is the **post-hoc test** that identifies **which specific groups** differ after a significant ANOVA result.

### How It Works in This App
1. **One-Way ANOVA** computes the F-statistic and p-value
2. If p < α (significant), the app automatically runs **Tukey HSD**
3. Tukey HSD compares all possible pairs while controlling family-wise error rate
4. Results show mean differences, confidence intervals, and adjusted p-values

### Automatic Features
- **Smart Binning**: Continuous grouping variables are automatically binned into quartiles
- **Assumption Checking**: Shapiro-Wilk (normality) and Levene (homogeneity) tests
- **Effect Size**: Eta-squared (η²) with Cohen's interpretation guidelines

---

## 🏗️ Project Structure

```
turnkey_analysis_package/
│
├── app.py                    # Application entry point (Streamlit)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── docs/
│   ├── USER_GUIDE.md         # Detailed user documentation
│   ├── API_REFERENCE.md      # Function documentation
│   ├── DEPLOYMENT.md         # Deployment instructions
│   └── ARCHITECTURE.md       # Technical architecture
│
└── assets/
    └── (static assets)
```

---

## 🌐 Deployment

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud (Free)
1. Push code to GitHub
2. Connect repository at [share.streamlit.io](https://share.streamlit.io)
3. Select `app.py` as the entry point

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### AWS / Azure / GCP
Deploy as a containerized application using the provided Dockerfile, or use platform-specific Python hosting solutions.

---

## 📋 Requirements

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | >=1.28.0 | Web application framework |
| pandas | >=2.0.0 | Data manipulation |
| numpy | >=1.24.0 | Numerical computing |
| scipy | >=1.11.0 | Statistical functions |
| statsmodels | >=0.14.0 | ANOVA, Tukey HSD, regression |
| matplotlib | >=3.7.0 | Plotting |
| seaborn | >=0.12.0 | Statistical visualization |
| scikit-learn | >=1.3.0 | ML utilities |
| openpyxl | >=3.1.0 | Excel file I/O |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Statistical computing powered by [SciPy](https://scipy.org) and [Statsmodels](https://www.statsmodels.org)
- Visualization by [Matplotlib](https://matplotlib.org) and [Seaborn](https://seaborn.pydata.org)
- Inspired by R's `easystats` and `rmarkdown` ecosystems

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/turnkey-ops/turnkey-analysis/issues)
- **Documentation**: See `docs/` folder
- **Email**: support@turnkey-ops.example.com

---

<p align="center">
  <strong>Turnkey Statistical Analysis Pipeline v1.0.0</strong><br>
  Production-Ready | Automated | Enterprise-Grade
</p>
