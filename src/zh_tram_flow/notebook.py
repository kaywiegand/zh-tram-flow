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


def save_fig(
    fig,
    name: str,
    *,
    dpi: int = 150,
    html: bool = True,
    png: bool = True,
    overwrite_warn_hours: float = 24.0,
) -> list[Path]:
    """Save a figure to reports/figures/ with a meaningful name.

    Supports Matplotlib figures and Plotly figures.
    Warns if an existing file is newer than `overwrite_warn_hours` hours.

    Parameters
    ----------
    fig   : matplotlib.figure.Figure | plotly.graph_objs.Figure
    name  : slug without extension, e.g. "tempo-day-hours"
    dpi   : resolution for PNG output (Matplotlib only)
    html  : save Plotly figures as .html (default True)
    png   : save Matplotlib as .png, Plotly as .png via kaleido (default True)
    overwrite_warn_hours : warn if existing file is younger than this many hours

    Returns
    -------
    list of Path objects that were written
    """
    import datetime
    import time

    figures_dir: Path = PATHS["figures"]
    figures_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    def _warn_if_recent(path: Path) -> None:
        if path.exists():
            age_h = (time.time() - path.stat().st_mtime) / 3600
            if age_h < overwrite_warn_hours:
                warn(f"Overwriting {path.name} (last modified {age_h:.1f}h ago)")

    # ── Detect figure type ────────────────────────────────────────────────────
    fig_type = type(fig).__module__.split(".")[0]   # "matplotlib" | "plotly"

    if fig_type == "matplotlib" or hasattr(fig, "savefig"):
        if png:
            out = figures_dir / f"{name}.png"
            _warn_if_recent(out)
            fig.savefig(out, dpi=dpi, bbox_inches="tight")
            success(f"Saved → figures/{name}.png")
            written.append(out)

    elif fig_type == "plotly" or hasattr(fig, "write_html"):
        if html:
            out = figures_dir / f"{name}.html"
            _warn_if_recent(out)
            fig.write_html(str(out), include_plotlyjs="cdn")
            success(f"Saved → figures/{name}.html")
            written.append(out)
        if png:
            try:
                out = figures_dir / f"{name}.png"
                _warn_if_recent(out)
                fig.write_image(str(out), width=1400, height=800, scale=2)
                success(f"Saved → figures/{name}.png")
                written.append(out)
            except Exception:
                warn(f"PNG export failed (kaleido not installed?). HTML saved, PNG skipped.")
    else:
        warn(f"save_fig: unknown figure type '{type(fig)}' — skipped.")

    return written


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
    from zh_tram_flow.cleaning import apply_lf_clean

    setup_plotting()   # activates wgnd theme (matplotlib + seaborn)
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
    # export
    "save_fig",
    # line colors
    "LINE_COLORS", "LINE_TEXT_COLORS", "line_color", "line_colors",
]
