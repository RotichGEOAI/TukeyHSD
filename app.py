#!/usr/bin/env python3
"""
Turkey HSD Analyzer v2.0 - Main Entry Point
============================================
Auto-detects environment and launches the Streamlit interface.

Usage:
    streamlit run app.py          # Launches Streamlit interface
    python app.py                 # Launches Streamlit interface

Features:
    - One-Way ANOVA + Tukey HSD
    - Two-Way ANOVA with interactions
    - Mean Separation Analysis (CLD, Duncan, LSD, SNK, Scheffe)
    - Simple Effects Analysis
    - Interactive visualizations

Version: 2.0.0
"""

import sys
import os
from pathlib import Path

# ─── Project Configuration ────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
MODULES_DIR = PROJECT_ROOT / "modules"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure directories exist
for d in [DATA_DIR, OUTPUTS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Add modules to path
sys.path.insert(0, str(MODULES_DIR))

# ─── Auto-detect Streamlit Runtime ─────────────────────────────────────────────
try:
    import streamlit as st
    if hasattr(st, 'runtime') or 'streamlit' in sys.modules:
        from streamlit_app import StreamlitApp
        app = StreamlitApp()
        app.run()
        sys.exit(0)
except ImportError:
    pass
except Exception:
    pass

# ─── Main Entry Point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔬 Turkey HSD Analyzer v2.0")
    print("🚀 Launching in STREAMLIT mode...")
    print("Run with: streamlit run app.py")

    try:
        from streamlit_app import StreamlitApp
        app = StreamlitApp()
        app.run()
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
