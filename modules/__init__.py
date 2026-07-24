"""
Turkey HSD Analyzer v2.0 - Statistical Analysis Modules
=======================================================
Mean Separation Analysis & Two-Way ANOVA Capabilities
"""

__version__ = "2.0.0"
__author__ = "Turkey HSD Analyzer Team"

from .statistics import (
    perform_anova,
    perform_tukey_hsd,
    perform_two_way_anova,
    perform_mean_separation,
    compact_letter_display,
    duncans_mrt,
    fishers_lsd,
    snk_test,
    scheffe_test,
    simple_effects_analysis,
    interaction_plot,
    profile_plot,
)

__all__ = [
    "perform_anova",
    "perform_tukey_hsd",
    "perform_two_way_anova",
    "perform_mean_separation",
    "compact_letter_display",
    "duncans_mrt",
    "fishers_lsd",
    "snk_test",
    "scheffe_test",
    "simple_effects_analysis",
    "interaction_plot",
    "profile_plot",
]
