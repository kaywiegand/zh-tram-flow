"""
notebook.py
-----------
Central entry point for all notebooks.

Usage:
    from zh_tram_flow.notebook import *

    TRAIN, TEST, lf = setup_analysis("03_analysis_target")
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

from zh_tram_flow.config import PATHS, PROJECT_NAME, RANDOM_SEED
from zh_tram_flow.settings import setup_plotting, logger


def setup_analysis(notebook_name: str = "notebook"):
    """Standard setup for all analysis notebooks.

    Activates theme, configures plotting, logs start.
    Returns (TRAIN, TEST, lf) ready to use.

    Usage:
        TRAIN, TEST, lf = setup_analysis("03_analysis_target")
    """
    from wgnd.core.theme import setup
    setup_plotting()
    setup()
    logger.info(f"{notebook_name} started")

    TRAIN = PATHS["processed"] / "train_features.parquet"
    TEST  = PATHS["processed"] / "test_features.parquet"
    lf    = pl.scan_parquet(TRAIN)

    return TRAIN, TEST, lf


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
