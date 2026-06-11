"""
plot_styles.py
--------------
GLOBALE CHART-REGELN für zh-tram-flow.
Einmal definiert — gilt für alle Analytics-Funktionen in allen Notebooks.

═══════════════════════════════════════════════════════════════════════════
REGELKATALOG (vollständig, verbindlich)
═══════════════════════════════════════════════════════════════════════════

ACHSEN
  Stärke   : 1px  |  Farbe: #999999 (mittleres Grau)
  Ticks    : gleiche Farbe, 9pt  |  Grid: KEINE
  Top/Right: unsichtbar
  → style_ax(ax) auf jede Achse anwenden

LEGENDEN
  Position : upper right  |  Layout: eine horizontale Zeile (ncol=10)
  Kasten   : keiner (frameon=False)  |  Schrift: 9pt  |  Handle: 3px hoch
  → ax.legend(**LEGEND_KW_RIGHT) oder LEGEND_KW_LEFT

REFERENZLINIEN  (axhline / axvline)
  Mittelwert  : gepunktet (:),    #555555, 1px  →  mean_kw("Mean ...")
  Median      : gestrichelt (--), #555555, 1px  →  median_kw("Median ...")
  OTP-Ziel    : gestrichelt (--), #27ae60, 1px  →  otp_kw()
  Trend       : gestrichelt (--), Datenfarbe, 55% alpha  →  trend_kw(color)
  NULL-LINIEN : KEINE — axhline(0) / axvline(0) immer entfernen

DATENLINIEN  (ax.plot)
  Stärke: 1px  |  Marker: "o", size 3
  → data_line_kw(color, label)

FARBEN — Herkunft (kein cfg.PALETTE_CATEGORICAL)
  Tramlinien   : LINE_COLORS / line_color(ln)
  Stadtkreise  : DISTRICT_COLORS / district_color(nr)
  Delay/Target : DELAY_COLOR / ARRIVAL_COLOR / DEPARTURE_COLOR
  OTP          : OTP_ON_TIME / OTP_LATE / OTP_CRITICAL
  Wetter       : WEATHER_COLORS["normal"|"rain"|"heavy_rain"|"snow"]
  Events       : EVENT_COLORS["normal"|"holiday"|"small"|"medium"|"large"]
  Jahre        : YEAR_COLORS["2023"|"2024"|"2025"]
  Jahreszeiten : SEASON_COLORS["Frühling"|"Sommer"|"Herbst"|"Winter"]
  Über Ø       : DELAY_COLOR (#E67E22)
  Grau/Neutral : BAR_NEUTRAL (#b8b8b8)  ← Fallback für alles ohne Semantik
  Vergleich    : COMPARE_BASE / COMPARE_MODEL

FIGURGRÜSSEN
  Single   : FIG_SINGLE   = (12, 4)
  2-Panel  : FIG_2PANEL   = (16, 5)
  3-Panel  : FIG_3PANEL   = (18, 5)
  Timeline : FIG_TIMELINE = (14, 5)
  Wide     : FIG_WIDE     = (20, 5)
  Tall     : FIG_TALL     = (14, 8)

═══════════════════════════════════════════════════════════════════════════
"""

from zh_tram_flow.config import ANNO_MEAN, ANNO_MEDIAN, OTP_ON_TIME

# ── Chart-Titel ───────────────────────────────────────────────────────────────
# Gleiche Schrift wie Achsen-Labels, schwarz, bold, linksbündig.
# matplotlib: **TITLE_KW   |   Plotly: title=plotly_title("...")
TITLE_KW = dict(loc="left", fontsize=11, color="#222222", fontweight="bold", pad=10)

def plotly_title(text: str) -> dict:
    """Einheitlicher Plotly-Titel: linksbündig, bold, 13pt, schwarz.
    Size 13 gleicht den visuellen Unterschied zwischen HTML-Canvas und Matplotlib aus."""
    return dict(text=text, x=0.0, xanchor="left",
                font=dict(size=18, color="#222222", family="Arial", weight="bold"))

# ── Heatmap-Farbskala ────────────────────────────────────────────────────────
# Einheitliche Blau-Skala für alle Delay/Metrik-Intensitäts-Heatmaps.
# Divergierende Charts (Korrelation, Delta) behalten ihre eigenen Scales.
#
# Matplotlib:  cmap=HEATMAP_CMAP
# Plotly:      colorscale=HEATMAP_COLORSCALE
import matplotlib.colors as _mcolors
HEATMAP_CMAP = _mcolors.LinearSegmentedColormap.from_list(
    "zh_blue", ["#f0f8ff", "#2E86AB"]
)
HEATMAP_COLORSCALE = [[0.0, "#f0f8ff"], [1.0, "#2E86AB"]]

# Delay/Target-Intensität — für Charts die direkt arrival_delay zeigen
# Semantisch: weiss = kein Delay · orange = hoher Delay (Projektfarbe #E67E22)
DELAY_CMAP = _mcolors.LinearSegmentedColormap.from_list(
    "zh_delay", ["#fff8f0", "#E67E22"]
)
DELAY_COLORSCALE = [[0.0, "#fff8f0"], [1.0, "#E67E22"]]

# ── Linien-Formatierung ───────────────────────────────────────────────────────
def fmt_line_axis(ln) -> str:
    """Tram-Linie für Achsen-Labels: '13' → 'L 13'."""
    return f"L {ln}"

def fmt_line_legend(ln) -> str:
    """Tram-Linie für Legenden: '13' → 'Linie 13'."""
    return f"Linie {ln}"

# ── Figurgrüssen ──────────────────────────────────────────────────────────
FIG_SINGLE   = (12, 4)
FIG_2PANEL   = (16, 5)
FIG_3PANEL   = (18, 5)
FIG_TIMELINE = (14, 5)
FIG_WIDE     = (20, 5)
FIG_TALL     = (14, 8)

# ── Achsen-Stil ───────────────────────────────────────────────────────────
_SPINE_COLOR = "#999999"


def style_ax(ax) -> None:
    """Einheitliche Achsgestaltung: kein top/right, mittelgrau, 1px, kein Grid."""
    ax.spines[["top", "right"]].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(_SPINE_COLOR)
        ax.spines[spine].set_linewidth(1.0)
    ax.tick_params(colors=_SPINE_COLOR, labelsize=9, width=1.0, length=4)
    ax.grid(False)


# ── Legenden ─────────────────────────────────────────────────────────────
LEGEND_KW = dict(
    frameon=False,
    fontsize=9,
    ncol=10,
    handlelength=1.5,
    handleheight=0.3,
    borderpad=0.3,
    labelspacing=0.3,
    columnspacing=1.0,
    loc="upper right",
)

LEGEND_KW_RIGHT = {**LEGEND_KW, "loc": "upper right"}
LEGEND_KW_LEFT  = {**LEGEND_KW, "loc": "upper left"}


# ── Referenzlinien ────────────────────────────────────────────────────────

def mean_kw(label: str = "Mean") -> dict:
    """Mittelwert: gepunktet (:), #555555, 1px."""
    return dict(color=ANNO_MEAN, lw=1.0, linestyle=":", label=label)


def median_kw(label: str = "Median") -> dict:
    """Median: gestrichelt (--), #555555, 1px."""
    return dict(color=ANNO_MEDIAN, lw=1.0, linestyle="--", label=label)


def otp_kw(label: str = "OTP-Ziel (85%)") -> dict:
    """OTP-Ziel: gestrichelt (--), grün #27ae60, 1px."""
    return dict(color=OTP_ON_TIME, lw=1.0, linestyle="--", label=label)


def trend_kw(color: str, label: str = "Trend") -> dict:
    """Trend: gestrichelt (--), Datenfarbe, 55% alpha, 1px."""
    return dict(lw=1.0, color=color, linestyle="--", alpha=0.55, label=label)


# ── Datenlinien ───────────────────────────────────────────────────────────

def data_line_kw(color: str, label: str = "", alpha: float = 1.0) -> dict:
    """Datenlinie: 1px, Marker 'o' size 3."""
    kw = dict(lw=1.0, color=color, marker="o", markersize=3, alpha=alpha)
    if label:
        kw["label"] = label
    return kw
