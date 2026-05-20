"""
notebook.py
-----------
Central entry point for all notebooks.

Usage:
    from zh_tram_flow.notebook import *

    TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("03_analysis_target")
"""

import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from wgnd.inspect import (
    inspect,
    inspect_missing,
    inspect_duplicates,
    inspect_outliers,
    inspect_outlier_detail,
    inspect_correlations,
)
from wgnd.core._output import success, warn, log, info_box, show_df, section_header
from wgnd.core.config import cfg

from zh_tram_flow.config import PATHS, PROJECT_NAME, RANDOM_SEED, LINE_COLORS, LINE_TEXT_COLORS, line_color, line_colors
from zh_tram_flow.settings import setup_plotting, logger


def setup_analysis(notebook_name: str = "notebook"):
    """Standard setup for all analysis notebooks.

    Activates theme, configures plotting, logs start.
    Returns (TRAIN, TEST, lf, lf_all, lf_delay, lf_clean) ready to use.

    lf_all   — train + test features combined (all years)
    lf_delay — lf_all filtered: canceled == False
    lf_clean — analysis-ready: canceled=False · stop_sequence>1 · no Linie E/L50/L51
               departure_delay / delay_delta masked to NaN for Nov 14–Dec 23 2025
               (is_anomal flag added for that window)

    Usage:
        TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("03_analysis_1-target")
    """
    from wgnd.core.theme import setup
    from zh_tram_flow.cleaning import apply_lf_clean

    setup_plotting()
    setup()
    logger.info(f"{notebook_name} started")

    TRAIN = PATHS["processed"] / "train_features.parquet"
    TEST  = PATHS["processed"] / "test_features.parquet"
    lf    = pl.scan_parquet(TRAIN)

    lf_all   = pl.concat([pl.scan_parquet(TRAIN), pl.scan_parquet(TEST)])
    lf_delay = lf_all.filter(pl.col("canceled") == False)
    lf_clean = apply_lf_clean(lf_all)

    return TRAIN, TEST, lf, lf_all, lf_delay, lf_clean


__all__ = [
    # data
    "pl", "pd", "np", "plt", "sns", "Path",
    # wgnd output
    "section_header", "log", "success", "warn", "info_box", "show_df",
    # wgnd inspect
    "inspect", "inspect_missing", "inspect_duplicates",
    "inspect_outliers", "inspect_outlier_detail", "inspect_correlations",
    # config
    "cfg", "PATHS", "PROJECT_NAME", "RANDOM_SEED",
    # setup
    "setup_plotting", "logger", "setup_analysis",
]
