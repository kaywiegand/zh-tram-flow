"""
settings.py
-----------
Visuelle und Logging-Konfiguration:
  - wgnd Theme (Matplotlib / Seaborn)
  - Farbpaletten
  - Logging-Format
"""

import logging
import matplotlib.pyplot as plt
import seaborn as sns

# ─── Farben ────────────────────────────────────────────────────────────────
PALETTE_PRIMARY  = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B"]
PALETTE_SEABORN  = "muted"

# ─── Plot-Stil ─────────────────────────────────────────────────────────────
FIGSIZE_DEFAULT  = (10, 6)
FIGSIZE_WIDE     = (14, 6)
DPI              = 120


def setup_plotting() -> None:
    """Setzt wgnd-Theme, Notebook-Optionen und autoreload."""
    import pandas as pd
    from wgnd.core.theme import setup as wgnd_setup

    wgnd_setup()
    plt.rcParams.update({
        "figure.figsize": FIGSIZE_DEFAULT,
        "figure.dpi":     DPI,

        # ── zh-tram-flow Overrides ─────────────────────────────────────────
        # Einheitlicher Look für alle Charts im Projekt.
        # Überschreiben wgnd-Defaults wo nötig.

        # Grid — KEINE
        "axes.grid":              False,

        # Linien — immer 1px, Marker klein
        "lines.linewidth":        1.0,
        "lines.markersize":       3.0,

        # Achsen — 1px, dunkles Grau
        "axes.linewidth":         1.0,
        "axes.edgecolor":         "#999999",
        "xtick.major.width":      1.0,
        "ytick.major.width":      1.0,
        "xtick.major.size":       4.0,
        "ytick.major.size":       4.0,
        "xtick.color":            "#999999",
        "ytick.color":            "#999999",
        "xtick.labelsize":        9,
        "ytick.labelsize":        9,
        "axes.labelsize":         10,
        "axes.labelcolor":        "#888888",   # leicht heller

        # Legende — kein Kasten, eine horizontale Zeile, oben rechts, dezent
        "legend.frameon":         False,
        "legend.fontsize":        9,
        # ncol muss per-call gesetzt werden (kein rcParam) → LEGEND_KW in plot_styles.py
        "legend.handlelength":    1.5,
        "legend.handleheight":    0.3,
        "legend.borderpad":       0.3,
        "legend.labelspacing":    0.3,
        "legend.columnspacing":   1.0,
        "legend.labelcolor":      "#999999",
    })
    pd.set_option("display.notebook_repr_html", True)
    pd.set_option("display.max_rows", 10)
    pd.set_option("display.max_columns", None)

    try:
        from IPython import get_ipython
        ip = get_ipython()
        if ip:
            ip.run_line_magic("load_ext", "autoreload")
            ip.run_line_magic("autoreload", "2")
    except Exception:
        pass


# ─── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("project")
