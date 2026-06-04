"""
visualization/insights.py
-------------------------
Report-ready plots for 04_insights.ipynb.

One function per insight section. All plots use cfg + line_color()
so a single theme change propagates everywhere.
"""
import json
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
import matplotlib.ticker as mticker
from matplotlib.lines import Line2D
import polars as pl

from wgnd.core.config import cfg

from zh_tram_flow.config import PATHS, line_color
from zh_tram_flow.plot_styles import (style_ax, LEGEND_KW, LEGEND_KW_RIGHT, LEGEND_KW_LEFT,
                                       mean_kw, median_kw, otp_kw, trend_kw, data_line_kw,
                                       FIG_SINGLE, FIG_2PANEL, FIG_3PANEL, FIG_TIMELINE, FIG_WIDE, FIG_TALL,
                                       TITLE_KW, fmt_line_axis, fmt_line_legend, plotly_title)


# ── Shared helpers ────────────────────────────────────────────────────────────

# Key network milestones shown as vertical reference lines.
MILESTONES = [
    ("2023-12-10", "Fahrplanwechsel Dez 2023", 0.06),
    ("2024-06-15", "Baustellen-Ende Limmatplatz", 0.92),
    ("2024-12-08", "Fahrplanwechsel Dez 2024", 0.06),
    ("2025-12-14", "Fahrplanwechsel Dez 2025", 0.06),
]


def _add_milestones(ax: plt.Axes) -> None:
    for date, _label, _y_frac in MILESTONES:
        ax.axvline(pd.Timestamp(date), color=cfg.ANNO_REF, lw=1.2,
                   linestyle="--", ymax=0.85, zorder=1)


def _milestone_legend_handle() -> Line2D:
    return Line2D(
        [0], [0],
        color=cfg.ANNO_REF, lw=1.2, linestyle="--",
        label="Timetable Change / Construction",
    )



# ── Section: Netzstruktur ─────────────────────────────────────────────────────

def plot_monthly_delay_by_line(lf: pl.LazyFrame, ylim=None) -> None:
    """Monatliche Ø Arrival Delay pro Linie — 1 Panel, nur arrival_delay.

    Input: lf_clean (canceled=False, stop_sequence>1, kein E/L50/L51).
    """
    monthly = (
        lf
        .with_columns([
            pl.col("operating_date").dt.year().alias("year"),
            pl.col("operating_date").dt.month().alias("month"),
        ])
        .group_by(["year", "month", "line_name"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort(["year", "month"])
        .collect(engine="streaming")
        .to_pandas()
    )
    # Mid-month positioning so the last data point sits visually inside its month
    monthly["date"] = pd.to_datetime(monthly[["year", "month"]].assign(day=15))

    lines = sorted(monthly["line_name"].astype(str).unique(),
                   key=lambda x: int(x) if x.isdigit() else 99)

    fig, ax = plt.subplots(figsize=(14, 5))

    # Soft month grid lines (behind everything) — incl. Jan 2026 for visual close
    for ts in pd.date_range("2023-01-01", "2026-01-01", freq="MS"):
        ax.axvline(ts, color="#cccccc", lw=0.4, alpha=0.5, zorder=0)

    for ln in lines:
        df = monthly[monthly["line_name"] == ln].sort_values("date")
        ax.plot(df["date"], df["avg_delay"],
                color=line_color(ln), lw=1.2, label=fmt_line_legend(ln))

    _add_milestones(ax)

    ax.set_ylim(*(ylim if ylim is not None else (0, 120)))
    ax.set_title("Monthly Avg. Arrival Delay — All Lines 2023–2025",
                 **TITLE_KW)
    ax.set_ylabel("Ø Arrival Delay (s)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%ds"))
    style_ax(ax)

    # X-axis: month numbers 01–12, Jan 2026 tick visible for visual breathing room
    ax.set_xlim(pd.Timestamp("2023-01-01"), pd.Timestamp("2026-01-15"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m"))
    ax.tick_params(axis="x", labelsize=8)

    # Year labels in a second row below month ticks
    trans = ax.get_xaxis_transform()
    for yr in [2023, 2024, 2025]:
        mid = pd.Timestamp(f"{yr}-07-01")
        ax.text(mid, -0.10, str(yr), transform=trans,
                ha="center", va="top", fontsize=9.5,
                color=cfg.CHART_AXIS_TEXT, fontweight="semibold")

    # Legend: always max 2 rows
    handles, labels = ax.get_legend_handles_labels()
    handles.append(_milestone_legend_handle())
    labels.append("Timetable Change / Construction")
    ncol = math.ceil(len(handles) / 2)
    ax.legend(handles=handles, labels=labels,
              **{**LEGEND_KW_RIGHT, "ncol": ncol})

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    plt.show()


# ── Section: OTP ─────────────────────────────────────────────────────────────

def plot_otp_by_line(lf: pl.LazyFrame, ylim=None) -> None:
    """OTP pro Linie — vertikale Balkenchart mit Netz-Schnitt und VBZ-Ziel."""
    otp = (
        lf
        .group_by("line_name")
        .agg([
            ((pl.col("arrival_delay").abs() <= 120).mean() * 100).alias("otp_pct"),
            pl.len().alias("n"),
        ])
        .sort("otp_pct", descending=True)
        .collect(engine="streaming")
        .to_pandas()
    )

    otp_mean = (otp["otp_pct"] * otp["n"]).sum() / otp["n"].sum()
    bar_colors = [line_color(str(ln)) for ln in otp["line_name"]]
    line_labels = [fmt_line_axis(ln) for ln in otp["line_name"]]

    fig, ax = plt.subplots(figsize=(14, 5))
    bars = ax.bar(line_labels, otp["otp_pct"], color=bar_colors, alpha=0.6)
    for bar, val in zip(bars, otp["otp_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.2,
                f"{val:.1f}%", ha="center", fontsize=9, color=cfg.CHART_AXIS_TEXT)

    ax.axhline(otp_mean, **mean_kw(f"Ø Netz {otp_mean:.0f}%"))
    ax.axhline(95, **median_kw("VBZ Target 95%"))

    ax.set_ylim(*(ylim if ylim is not None else (75, 100)))
    ax.set_title("On-Time Performance (OTP) per Line", **TITLE_KW)
    ax.set_ylabel("On-Time Performance (%)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    style_ax(ax)
    ax.legend(**LEGEND_KW_RIGHT)
    plt.tight_layout()
    plt.show()


def plot_otp_delta_distribution(lf: pl.LazyFrame, ylim=None) -> None:
    """Delay Delta — 3-bar chart: wächst / sinkt / neutral."""
    stats = (
        lf
        .filter(pl.col("delay_delta").is_not_null())
        .select([
            (pl.col("delay_delta") < 0).sum().alias("recovering"),
            (pl.col("delay_delta") > 0).sum().alias("growing"),
            (pl.col("delay_delta") == 0).sum().alias("neutral"),
        ])
        .collect(engine="streaming")
    )
    n_total = stats["recovering"][0] + stats["growing"][0] + stats["neutral"][0]
    labels = ["Verspätung wächst", "Verspätung sinkt", "Neutral"]
    values = [
        stats["growing"][0] / n_total * 100,
        stats["recovering"][0] / n_total * 100,
        stats["neutral"][0] / n_total * 100,
    ]
    colors = [cfg.COLOR_NEGATIVE, cfg.COLOR_POSITIVE, cfg.COLOR_NEUTRAL]

    fig, ax = plt.subplots(figsize=(14, 5))
    bars = ax.bar(labels, values, color=colors, width=0.5, alpha=0.6)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f"{val:.1f}%", ha="center", va="bottom",
                fontsize=10, color=cfg.CHART_AXIS_TEXT)
    ax.set_ylim(*(ylim if ylim is not None else (0, 85)))
    ax.set_title("Delay Delta — Accumulating vs. Recovering (Share of All Stops)",
                 **TITLE_KW)
    ax.set_ylabel("Share (%)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    style_ax(ax)
    plt.tight_layout()
    plt.show()


def _dwell_data(lf: pl.LazyFrame) -> tuple:
    """Shared data query for dwell analysis plots."""
    data = (
        lf
        .with_columns(
            (pl.col("departure_schedule") - pl.col("arrival_schedule"))
            .dt.total_seconds().cast(pl.Int32).alias("dwell_time")
        )
        .filter(pl.col("dwell_time") >= 0)
        .group_by("line_name")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("dwell_time").filter(pl.col("dwell_time") <= 120).mean().alias("avg_dwell"),
            (pl.col("dwell_time") == 0).mean().alias("pct_null_dwell"),
        ])
        .sort("avg_delay", descending=True)
        .collect(engine="streaming")
        .to_pandas()
    )
    x = np.arange(len(data))
    line_labels = [fmt_line_axis(ln) for ln in data["line_name"]]
    lc = [line_color(str(ln)) for ln in data["line_name"]]
    return data, x, line_labels, lc


def plot_dwell_throughput(lf: pl.LazyFrame, ylim=None) -> None:
    """Anteil Durchfahrtshalte (%) + Ø Verweilzeit (s) pro Linie.

    Balken: % Halte ohne Verweilzeit (Durchfahrt), Tramlinienfarben.
    Linie (rechte Achse): Ø Verweilzeit in Sekunden — anderer Unit für Kontrast.
    Sortiert nach Ø Arrival Delay descending.
    """
    _teal = cfg.COLOR_POSITIVE  # #25ac82 — kein Overlap mit Tramlinienfarben

    data, x, line_labels, lc = _dwell_data(lf)

    pct_null = data["pct_null_dwell"] * 100

    # Bars at alpha=0.6 so the teal line reads clearly without a halo
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x, pct_null, color=lc, alpha=0.6)
    for i, pn in enumerate(pct_null):
        ax.text(i, pn + 1.2, f"{pn:.0f}%", va="bottom", ha="center",
                fontsize=8, color="#555555")
    ax.set_xticks(x)
    ax.set_xticklabels(line_labels, fontsize=9)
    ax.set_ylim(*(ylim if ylim is not None else (0, 108)))
    ax.set_title("Share of Through-Stops per Line", **TITLE_KW)
    ax.set_ylabel("Through-Stops (%)")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    style_ax(ax)

    ax_r = ax.twinx()
    ax_r.plot(x, data["avg_dwell"].fillna(0), color=_teal, lw=1.5, linestyle="--",
              marker="o", markersize=3, label="Ø Dwell Time (s)")
    ax_r.set_ylabel("Ø Dwell Time (s)", fontsize=10, color=_teal)
    ax_r.tick_params(axis="y", colors=_teal, labelsize=9)
    ax_r.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0fs"))
    ax_r.spines["top"].set_visible(False)
    ax_r.spines["left"].set_visible(False)
    h, l = ax_r.get_legend_handles_labels()
    ax.legend(h, l, **LEGEND_KW_RIGHT)

    plt.tight_layout()
    plt.show()


def plot_dwell_vs_delay(lf: pl.LazyFrame, ylim=None) -> None:
    """Ø Arrival Delay (s) + Verweilzeit (%) pro Linie.

    Balken: Ø Arrival Delay in Sekunden, Tramlinienfarben.
    Linie (rechte Achse): Verweilzeit (%) — Anteil Halte mit dwell > 0s.
    Sortiert nach Ø Arrival Delay descending.
    """
    _teal = cfg.COLOR_POSITIVE  # #25ac82 — konsistent mit plot_dwell_throughput

    data, x, line_labels, lc = _dwell_data(lf)

    pct_verweil = (1 - data["pct_null_dwell"]) * 100

    # Bars at alpha=0.6 so the violet line reads clearly without a halo
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x, data["avg_delay"], color=lc, alpha=0.6)
    for i, v in enumerate(data["avg_delay"]):
        ax.text(i, v + 0.5, f"{v:.0f}s", va="bottom", ha="center",
                fontsize=8, color="#555555")
    ax.set_xticks(x)
    ax.set_xticklabels(line_labels, fontsize=9)
    ax.set_title("Delay vs. Dwell Time per Line", **TITLE_KW)
    ax.set_ylabel("Ø Arrival Delay (s)")
    style_ax(ax)

    ax_r = ax.twinx()
    ax_r.plot(x, pct_verweil, color=_teal, lw=1.5, linestyle="--",
              marker="o", markersize=3, label="Dwell Time (%)")
    ax_r.set_ylabel("Dwell Time (%)", fontsize=10, color=_teal)
    ax_r.tick_params(axis="y", colors=_teal, labelsize=9)
    ax_r.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax_r.spines["top"].set_visible(False)
    ax_r.spines["left"].set_visible(False)
    h, l = ax_r.get_legend_handles_labels()
    ax.legend(h, l, **LEGEND_KW_RIGHT)
    if ylim is not None:
        ax.set_ylim(*ylim)

    plt.tight_layout()
    plt.show()


def plot_dwell_analysis(lf: pl.LazyFrame) -> None:
    """Wrapper: ruft plot_dwell_throughput + plot_dwell_vs_delay auf."""
    plot_dwell_throughput(lf)
    plot_dwell_vs_delay(lf)


def plot_dwell_by_stop_position(lf: pl.LazyFrame, ylim=None) -> None:
    """Ø Dwell Time nach Stop-Sequenz — zeigt Puffer-Konzentration am Starthalt.

    Input: lf_delay (alle Halte inkl. stop_sequence == 1).
    """
    dwell_by_seq = (
        lf
        .with_columns(
            (pl.col("departure_schedule") - pl.col("arrival_schedule"))
            .dt.total_seconds().cast(pl.Int32).alias("dwell_time")
        )
        .filter(pl.col("dwell_time") >= 0)
        .group_by("stop_sequence")
        .agg([
            pl.col("dwell_time").mean().alias("avg_dwell"),
            (pl.col("dwell_time") > 0).mean().alias("pct_has_dwell"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 5000)
        .sort("stop_sequence")
        .collect(engine="streaming")
        .to_pandas()
    )

    colors = [cfg.COLOR_POSITIVE if seq == 1 else cfg.COLOR_NEUTRAL
              for seq in dwell_by_seq["stop_sequence"]]

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(dwell_by_seq["stop_sequence"], dwell_by_seq["avg_dwell"],
           color=colors, alpha=0.8, width=0.8)

    seq1 = dwell_by_seq[dwell_by_seq["stop_sequence"] == 1]
    if not seq1.empty:
        val = seq1["avg_dwell"].values[0]
        ax.annotate(f"Start-Halt\n{val:.0f}s",
                    xy=(1, val), xytext=(3, val * 0.85),
                    fontsize=9, color=cfg.CHART_AXIS_TEXT,
                    arrowprops=dict(arrowstyle="-", color=cfg.CHART_AXIS, lw=0.8))

    rest_mean = dwell_by_seq[dwell_by_seq["stop_sequence"] > 1]["avg_dwell"].mean()
    ax.axhline(rest_mean, **median_kw(f"Ø Mid-/End-Stops {rest_mean:.1f}s"))

    ax.set_title("Dwell Time by Stop Position — Buffer concentrates at first stop",
                 **TITLE_KW)
    ax.set_xlabel("Stop Sequence (position in trip)")
    ax.set_ylabel("Ø Dwell Time (s)")
    ax.legend(**LEGEND_KW_RIGHT)
    style_ax(ax)
    if ylim is not None:
        ax.set_ylim(*ylim)
    plt.tight_layout()
    plt.show()


# ── Section: Geografie ────────────────────────────────────────────────────────

def plot_top_delay_stops(lf: pl.LazyFrame, top_n: int = 20, min_obs: int = 50_000, ylim=None) -> None:
    """Top stops by average arrival delay, horizontal bar chart."""
    df = (
        lf
        .group_by("stop_name")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= min_obs)
        .sort("avg_delay", descending=True)
        .head(top_n)
        .collect(engine="streaming")
        .to_pandas()
        .sort_values("avg_delay")
    )

    norm = (df["avg_delay"] - df["avg_delay"].min()) / (df["avg_delay"].max() - df["avg_delay"].min())
    cmap = mcolors.LinearSegmentedColormap.from_list("delay", ["#f4c9a8", cfg.COLOR_NEGATIVE])
    colors = [cmap(v) for v in norm]

    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(df["stop_name"], df["avg_delay"], color=colors)
    for bar, val in zip(bars, df["avg_delay"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}s", va="center", fontsize=8, color=cfg.CHART_AXIS_TEXT)
    ax.set_xlim(0, df["avg_delay"].max() * 1.15)
    ax.set_title(
        f"Top {top_n} Stops — Ø Arrival Delay (min. {min_obs // 1000}k observations)",
        **TITLE_KW,
    )
    ax.set_xlabel("Ø Delay (s)")
    style_ax(ax)
    if ylim is not None:
        ax.set_ylim(*ylim)
    plt.tight_layout()
    plt.show()


# ── Section: Geografie ────────────────────────────────────────────────────────

# ── District zone classification (consistent across both maps) ────────────────
# Aligned with YlOrRd stop-delay map: white=best · yellow=mid · orange=warn · red=crit
_DISTRICT_ZONE: dict[str, int] = {
    "1": 0, "4": 0, "5": 0, "10": 0,   # Best — weiß/neutral
    "2": 1, "3": 1, "6": 1,             # Mid  — hellgelb
    "7": 2, "9": 2,                     # Warn — orange (+ Außenbezirk = default)
    "8": 3, "11": 3, "12": 3,           # Crit — rot (Problemzone 1)
}
_DISTRICT_COLORSCALE = [
    [0.000, "#f5f5f5"], [0.249, "#f5f5f5"],  # Best  — near white
    [0.250, "#fed976"], [0.499, "#fed976"],  # Mid   — light yellow
    [0.500, "#fd8d3c"], [0.749, "#fd8d3c"],  # Warn  — orange
    [0.750, "#d73027"], [1.000, "#d73027"],  # Crit  — red
]
_DISTRICT_LEGEND_ANNOTATION = (
    "<b>Problemzonen</b><br>"
    "<span style='color:#d73027'>■</span> Problemzone 1 — K8 · K11 · K12<br>"
    "<span style='color:#fd8d3c'>■</span> Problemzone 2 — K7 · K9 · Außen<br>"
    "<span style='color:#fed976'>■</span> Mittelfeld<br>"
    "<span style='color:#f5f5f5'>■</span> Beste Kreise — K1 · K4 · K5 · K10"
)


def _district_stats(lf: pl.LazyFrame):
    """Shared data query for district map plots."""
    import plotly.graph_objects as go

    stats = (
        lf
        .group_by("district_nr")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            ((pl.col("arrival_delay").abs() <= 120).mean() * 100).alias("otp_pct"),
        ])
        .collect(engine="streaming")
        .to_pandas()
    )
    delay_map = dict(zip(stats["district_nr"].astype(str), stats["avg_delay"].round(1)))
    otp_map   = dict(zip(stats["district_nr"].astype(str), stats["otp_pct"].round(1)))

    geo_path = PATHS["raw"] / "stadtkreise.geojson"
    with open(geo_path) as f:
        stadtkreise = json.load(f)

    kreis_ids = [str(feat["properties"]["objid"]) for feat in stadtkreise["features"]]
    # Zone value: default 2 (Warn) for unclassified kreise (Außenbezirk)
    kreis_zones = [_DISTRICT_ZONE.get(kid, 2) for kid in kreis_ids]

    label_lats, label_lons, delay_texts, otp_texts = [], [], [], []
    for feat in stadtkreise["features"]:
        coords = np.array(feat["geometry"]["coordinates"][0])
        label_lats.append(coords[:, 1].mean())
        label_lons.append(coords[:, 0].mean())
        kid = feat["properties"]["objid"]
        delay_texts.append(f"K{kid}<br>{delay_map.get(str(kid), 0):.0f}s")
        otp_texts.append(f"K{kid}<br>{otp_map.get(str(kid), 0):.0f}%")

    return (stadtkreise, kreis_ids, kreis_zones,
            delay_map, otp_map,
            label_lats, label_lons, delay_texts, otp_texts)


def _district_map_layout(title_text: str) -> dict:
    return dict(
        mapbox=dict(style="carto-positron", zoom=10.5,
                    center={"lat": 47.378, "lon": 8.540}),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=500, showlegend=False,
        title=dict(text=title_text,
                   font=dict(size=14, color=cfg.CHART_TITLE), x=0, xanchor="left"),
    )


def plot_district_delay_map(lf: pl.LazyFrame) -> None:
    """Stadtkreise eingefärbt nach Problemzone — Ø Arrival Delay."""
    import plotly.graph_objects as go

    (stadtkreise, kreis_ids, kreis_zones,
     delay_map, _, label_lats, label_lons, delay_texts, _) = _district_stats(lf)

    hover = [
        f"<b>Kreis {kid}</b><br>Ø Delay: {delay_map.get(kid, 0):.1f}s"
        for kid in kreis_ids
    ]

    fig = go.Figure()
    fig.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise, locations=kreis_ids, z=kreis_zones,
        featureidkey="properties.objid",
        colorscale=_DISTRICT_COLORSCALE,
        zmin=0, zmax=3, showscale=True,
        colorbar=dict(
            title="Delay (s)",
            thickness=12, len=0.5,
            showticklabels=False,
        ),
        marker=dict(line=dict(color="#888888", width=1), opacity=0.8),
        hovertext=hover, hovertemplate="%{hovertext}<extra></extra>",
    ))
    fig.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons, mode="text", text=delay_texts,
        textfont=dict(size=11, color="#333333"), hoverinfo="skip",
    ))
    fig.update_layout(**_district_map_layout(
        "Stadtkreise — Ø Arrival Delay"
    ))
    fig.show()


def plot_district_otp_map(lf: pl.LazyFrame) -> None:
    """Stadtkreise eingefärbt nach Problemzone — OTP."""
    import plotly.graph_objects as go

    (stadtkreise, kreis_ids, kreis_zones,
     _, otp_map, label_lats, label_lons, _, otp_texts) = _district_stats(lf)

    hover = [
        f"<b>Kreis {kid}</b><br>OTP: {otp_map.get(kid, 0):.1f}%"
        for kid in kreis_ids
    ]

    fig = go.Figure()
    fig.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise, locations=kreis_ids, z=kreis_zones,
        featureidkey="properties.objid",
        colorscale=_DISTRICT_COLORSCALE,
        zmin=0, zmax=3, showscale=True,
        colorbar=dict(
            title="OTP (%)",
            thickness=12, len=0.5,
            showticklabels=False,
        ),
        marker=dict(line=dict(color="#888888", width=1), opacity=0.8),
        hovertext=hover, hovertemplate="%{hovertext}<extra></extra>",
    ))
    fig.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons, mode="text", text=otp_texts,
        textfont=dict(size=11, color="#333333"), hoverinfo="skip",
    ))
    fig.update_layout(**_district_map_layout(
        "Stadtkreise — On-Time-Performance (OTP)"
    ))
    fig.show()


def plot_district_maps(lf: pl.LazyFrame) -> None:
    """Wrapper: ruft plot_district_delay_map + plot_district_otp_map auf."""
    plot_district_delay_map(lf)
    plot_district_otp_map(lf)


def plot_infra_maps(lf_delay: pl.LazyFrame, lf_clean: pl.LazyFrame) -> None:
    """Zwei Infrastruktur-Karten: Δ Linienanbindung 2023→2025 + Ø Arrival Delay."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    district_stats = (
        lf_clean
        .group_by("district_nr")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            ((pl.col("arrival_delay").abs() <= 120).mean() * 100).alias("otp_pct"),
        ])
        .collect(engine="streaming")
        .to_pandas()
    )
    delay_map = dict(zip(district_stats["district_nr"].astype(str),
                         district_stats["avg_delay"].round(1)))

    def _lines_per_district(yr_start, yr_end):
        return (
            lf_delay
            .filter(pl.col("operating_date").is_between(
                pl.lit(yr_start).str.to_date(), pl.lit(yr_end).str.to_date()))
            .filter(pl.col("district_nr").is_not_null())
            .select(["district_nr", "line_name"])
            .unique()
            .group_by("district_nr")
            .agg(pl.col("line_name").n_unique().alias("n_lines"))
            .collect(engine="streaming")
            .to_pandas()
        )

    j23 = _lines_per_district("2023-01-01", "2023-12-31")
    j25 = _lines_per_district("2025-01-01", "2025-11-30")
    cmp = j23.merge(j25, on="district_nr", how="outer", suffixes=("_23", "_25"))
    cmp["n_lines_23"] = cmp["n_lines_23"].fillna(0).astype(int)
    cmp["n_lines_25"] = cmp["n_lines_25"].fillna(0).astype(int)
    cmp["delta"] = cmp["n_lines_25"] - cmp["n_lines_23"]
    delta_map = dict(zip(cmp["district_nr"].astype(str), cmp["delta"]))

    geo_path = PATHS["raw"] / "stadtkreise.geojson"
    with open(geo_path) as f:
        stadtkreise = json.load(f)

    kreis_ids    = [str(feat["properties"]["objid"]) for feat in stadtkreise["features"]]
    kreis_delays = [delay_map.get(kid, 0) for kid in kreis_ids]
    kreis_deltas = [delta_map.get(kid, 0) for kid in kreis_ids]
    abs_max      = max(abs(v) for v in kreis_deltas) or 1

    label_lats, label_lons, delta_texts, delay_texts = [], [], [], []
    for feat in stadtkreise["features"]:
        coords = feat["geometry"]["coordinates"]
        if feat["geometry"]["type"] == "MultiPolygon":
            all_pts = [pt for poly in coords for ring in poly for pt in ring]
        else:
            all_pts = [pt for ring in coords for pt in ring]
        label_lats.append(sum(p[1] for p in all_pts) / len(all_pts))
        label_lons.append(sum(p[0] for p in all_pts) / len(all_pts))
        kid = feat["properties"]["objid"]
        d = delta_map.get(str(kid), 0)
        delta_texts.append(f"K{kid}<br>{'+' if d > 0 else ''}{d}")
        delay_texts.append(f"K{kid}<br>{delay_map.get(str(kid), 0):.0f}s")

    colorscale_delta = [[0.0, cfg.COLOR_NEGATIVE], [0.5, "#f5f5f5"], [1.0, cfg.COLOR_POSITIVE]]
    colorscale_delay = [[0, "#e8f4f8"], [0.5, cfg.COLOR_SIGNAL], [1, cfg.COLOR_NEGATIVE]]
    mapbox_cfg = dict(style="carto-positron", zoom=10.5,
                      center={"lat": 47.378, "lon": 8.540})
    marker_cfg = dict(line=dict(color="#888888", width=1), opacity=0.7)

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "mapbox"}, {"type": "mapbox"}]],
        subplot_titles=["Δ Linienanbindung 2023 → 2025", "Ø Arrival Delay (s)"],
        horizontal_spacing=0.04,
    )

    fig.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise, locations=kreis_ids, z=kreis_deltas,
        featureidkey="properties.objid", colorscale=colorscale_delta,
        zmin=-abs_max, zmax=abs_max,
        colorbar=dict(title="Δ Linien", len=0.5, y=0.25, x=0.46, thickness=12),
        marker=marker_cfg,
        hovertemplate="<b>Kreis %{location}</b><br>Δ Linien: %{z:+d}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons, mode="text", text=delta_texts,
        textfont=dict(size=11, color="#333333"), hoverinfo="skip",
    ), row=1, col=1)

    fig.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise, locations=kreis_ids, z=kreis_delays,
        featureidkey="properties.objid", colorscale=colorscale_delay,
        zmin=min(kreis_delays), zmax=max(kreis_delays),
        colorbar=dict(title="Delay (s)", len=0.5, y=0.25, x=1.01, thickness=12),
        marker=marker_cfg,
        hovertemplate="<b>Kreis %{location}</b><br>Ø Delay: %{z:.1f}s<extra></extra>",
    ), row=1, col=2)
    fig.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons, mode="text", text=delay_texts,
        textfont=dict(size=11, color="#333333"), hoverinfo="skip",
    ), row=1, col=2)

    fig.update_layout(
        mapbox=mapbox_cfg, mapbox2=mapbox_cfg,
        margin={"r": 10, "t": 60, "l": 10, "b": 0},
        height=520,
        title=dict(
            text="Infrastruktur — Netzausbau 2023→2025 vs. Ø Arrival Delay",
            font=dict(size=14, color=cfg.CHART_TITLE),
            x=0, xanchor="left",
        ),
        showlegend=False,
    )
    fig.show()


# ── Section: Ereignisse / Temporalität ───────────────────────────────────────

def plot_delay_delta_timeline(lf: pl.LazyFrame, ylim=None) -> None:
    """Täglicher Ø Delay Delta 2023–2025 — positiv = Verspätung wächst."""
    daily = (
        lf
        .filter(pl.col("delay_delta").is_not_null())
        .group_by("operating_date")
        .agg(pl.col("delay_delta").mean().alias("delay_delta"))
        .sort("operating_date")
        .collect(engine="streaming")
        .to_pandas()
    )

    pos = daily["delay_delta"].where(daily["delay_delta"] >= 0)
    neg = daily["delay_delta"].where(daily["delay_delta"] < 0)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(daily["operating_date"], pos, lw=1.2, color=cfg.COLOR_NEGATIVE, label="Accumulating (≥ 0)")
    ax.plot(daily["operating_date"], neg, lw=1.2, color=cfg.COLOR_POSITIVE, label="Recovering (< 0)")
    ax.axhline(0, **median_kw("0"))
    ax.set_title("Daily Delay Delta 2023–2025 — positive = delay growing stop to stop",
                 **TITLE_KW)
    ax.set_ylabel("Ø Delay Delta (s)")
    style_ax(ax)
    ax.legend(**LEGEND_KW_LEFT)
    if ylim is not None:
        ax.set_ylim(*ylim)
    plt.tight_layout()
    plt.show()


def plot_arrival_vs_departure_timeline(lf: pl.LazyFrame, ylim=None) -> None:
    """Daily avg arrival delay 2023–2025 — 1 kombiniertes Panel mit Event-Markern.

    Analog zu plot_monthly_delay_by_line: gleiche Achsen, Skala und Stil.
    Input: lf_clean (canceled=False, stop_sequence>1, kein E/L50/L51).
    """
    _event_category_map = {
        "Super League":  "Fussball",
        "Schweizer Cup": "Fussball",
        "Konzert":       "Konzert",
        "Stadtfest":     "Stadtfest",
        "Fachmesse":     "Messe/Kongress",
        "Kongress":      "Messe/Kongress",
    }
    _category_colors = {
        "Fussball":       "#2ecc71",
        "Konzert":        "#e74c3c",
        "Stadtfest":      "#f39c12",
        "Messe/Kongress": "#9b59b6",
    }

    daily = (
        lf
        .group_by("operating_date")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort("operating_date")
        .collect(engine="streaming")
        .to_pandas()
    )
    daily["operating_date"] = pd.to_datetime(daily["operating_date"])

    event_dates = (
        lf
        .filter(pl.col("has_event") == True)
        .group_by(["operating_date", "event_type"])
        .agg(pl.len().alias("n"))
        .sort("operating_date")
        .collect(engine="streaming")
        .to_pandas()
    )
    event_dates["operating_date"] = pd.to_datetime(event_dates["operating_date"])
    event_dates["category"] = event_dates["event_type"].map(_event_category_map).fillna("Sonstiges")
    event_dates = event_dates[event_dates["category"] != "Sonstiges"]

    _SCHULFERIEN = [
        ("2023-02-06", "2023-02-17"), ("2023-04-10", "2023-04-21"),
        ("2023-07-08", "2023-08-11"), ("2023-10-02", "2023-10-13"),
        ("2023-12-23", "2024-01-05"), ("2024-02-05", "2024-02-16"),
        ("2024-04-08", "2024-04-19"), ("2024-07-06", "2024-08-09"),
        ("2024-09-30", "2024-10-11"), ("2024-12-21", "2025-01-03"),
        ("2025-02-03", "2025-02-14"), ("2025-04-07", "2025-04-17"),
        ("2025-07-05", "2025-08-08"), ("2025-10-06", "2025-10-17"),
    ]

    fig, ax = plt.subplots(figsize=(14, 5))

    # Soft month grid lines — same as plot_monthly_delay_by_line
    for ts in pd.date_range("2023-01-01", "2026-01-01", freq="MS"):
        ax.axvline(ts, color="#cccccc", lw=0.4, alpha=0.5, zorder=0)

    # Schulferien bands — ymax=0.9 so they don't bleed into the legend area
    labeled = False
    for s, e in _SCHULFERIEN:
        lbl = "School Holidays ZH" if not labeled else None
        ax.axvspan(pd.Timestamp(s), pd.Timestamp(e),
                   ymin=0, ymax=0.9, alpha=0.10, color="#999999",
                   label=lbl, zorder=0)
        labeled = True

    # Daily delay line
    ax.plot(daily["operating_date"], daily["avg_delay"],
            color="#222222", lw=1.0, alpha=0.85, label="Ø Delay", zorder=10)

    # Event verticals — ymax=0.9, lw=2, etwas transparenter
    shown: set = set()
    for _, row in event_dates.iterrows():
        cat = row["category"]
        lbl = cat if cat not in shown else None
        ax.axvline(row["operating_date"], color=_category_colors[cat],
                   lw=1.0, alpha=1.0, ymax=0.9, label=lbl, zorder=2)
        shown.add(cat)

    # Axes — identical to plot_monthly_delay_by_line
    ax.set_ylim(*(ylim if ylim is not None else (0, 140)))
    ax.set_xlim(pd.Timestamp("2023-01-01"), pd.Timestamp("2026-01-15"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m"))
    ax.tick_params(axis="x", labelsize=8)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%ds"))
    ax.set_ylabel("Ø Arrival Delay (s)")
    ax.set_title("Daily Delay Timeline 2023–2025 — Events & School Holidays",
                 **TITLE_KW)
    style_ax(ax)

    # Year labels in second row below month ticks
    trans = ax.get_xaxis_transform()
    for yr in [2023, 2024, 2025]:
        mid = pd.Timestamp(f"{yr}-07-01")
        ax.text(mid, -0.10, str(yr), transform=trans,
                ha="center", va="top", fontsize=9.5,
                color=cfg.CHART_AXIS_TEXT, fontweight="semibold")

    # Legend: all items in one row, right-aligned
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles, labels=labels,
              **{**LEGEND_KW_RIGHT, "ncol": len(handles)})

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    plt.show()


def plot_dwell_scatter(lf: pl.LazyFrame, ylim=None) -> None:
    """Scatter: % dwell_time=0 vs. Ø Arrival Delay pro Haltestelle.

    Zeigt zwei strukturelle Stop-Typen:
      · Akkumulations-Fallen — hoher dw0-Anteil, positiver delay_delta (rot)
      · Recovery-Anker       — echter Puffer vorhanden, negativer delay_delta (teal)

    Input: lf_clean. dwell_time wird intern aus departure/arrival_schedule berechnet.
    Filter: n >= 50.000 Beobachtungen (stabile Mittelwerte).
    """
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.patheffects as pe_mod

    # ── Daten berechnen ───────────────────────────────────────────────────────
    lf_w = lf.with_columns(
        ((pl.col("departure_schedule") - pl.col("arrival_schedule"))
         .dt.total_seconds().cast(pl.Int32)).alias("dwell_time")
    )
    stop_stats = (
        lf_w
        .filter(pl.col("delay_delta").is_not_null())
        .group_by("stop_name")
        .agg([
            pl.col("dwell_time").eq(0).cast(pl.Float64).mean().alias("pct_dw0"),
            pl.col("delay_delta").mean().alias("mean_dd"),
            pl.col("arrival_delay").mean().alias("mean_arr"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 50_000)
        .collect(engine="streaming")
        .to_pandas()
    )
    stop_stats["pct_dw0"] *= 100
    stop_stats["label"] = (stop_stats["stop_name"]
                           .str.replace("Zürich, ", "", regex=False)
                           .str.replace("Zürich,", "", regex=False)
                           .str.strip())

    net_mean_arr = stop_stats["mean_arr"].mean()
    net_mean_dw0 = stop_stats["pct_dw0"].mean()

    # ── Custom colormap: rot (akkumuliert) → grau → teal (erholt) ─────────────
    cmap = LinearSegmentedColormap.from_list(
        "dw_cmap",
        [cfg.COLOR_NEGATIVE, "#cccccc", cfg.COLOR_POSITIVE],
        N=256,
    )
    dd_abs = 18
    point_sizes = np.clip(np.log10(stop_stats["n"]) * 12, 20, 80)

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 7.5))

    sc = ax.scatter(
        stop_stats["pct_dw0"],
        stop_stats["mean_arr"],
        c=stop_stats["mean_dd"],
        s=point_sizes,
        cmap=cmap,
        vmin=-dd_abs, vmax=dd_abs,
        alpha=0.75,
        linewidths=0.4,
        edgecolors="#888888",
        zorder=3,
    )
    cbar = fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("Ø delay_delta (s/Halt)", fontsize=9, color=cfg.CHART_AXIS_TEXT)
    cbar.ax.tick_params(labelsize=8, colors=cfg.CHART_AXIS_TEXT)

    # Referenzlinien
    ax.axhline(net_mean_arr, **median_kw(f"Net Ø Arrival Delay ({net_mean_arr:.0f}s)"), zorder=2)
    ax.axvline(net_mean_dw0, **mean_kw(f"Net Ø dw0% ({net_mean_dw0:.0f}%)"), zorder=2)

    # Quadrant-Labels
    _qkw = dict(fontsize=8.5, alpha=0.7, style="italic", transform=ax.transAxes)
    ax.text(0.02, 0.98, "Recovery Anchors\n(buffer present, still delayed)",
            va="top", ha="left", color=cfg.COLOR_POSITIVE, **_qkw)
    ax.text(0.98, 0.98, "Accumulation Traps\n(no buffer + high delay)",
            va="top", ha="right", color=cfg.COLOR_NEGATIVE, **_qkw)
    ax.text(0.98, 0.02, "Early Route\n(no buffer, little accumulated yet)",
            va="bottom", ha="right", color=cfg.ANNO_REF, **_qkw)
    ax.text(0.02, 0.02, "Well-planned Stops\n(buffer + on time)",
            va="bottom", ha="left", color=cfg.ANNO_REF, **_qkw)

    # ── Extremstops annotieren ────────────────────────────────────────────────
    _LABEL = {
        "Zürich, Friedhof Enzenbühl":   ( 3.5, -12),
        "Zürich, Mattenhof":            ( 3.5,   5),
        "Zürich, Messe/Hallenstadion":  (-5,     5),
        "Zürich, Balgrist":             ( 3.5,  -9),
        "Zürich, Strassenverkehrsamt":  (-5,     5),
        "Zürich, Seebacherplatz":       (-5,     5),
        "Zürich, Leutschenbach":        ( 3.5,  -9),
        "Zürich, Bahnhof Oerlikon":     (-5,    -9),
        "Zürich, Stauffacher":          ( 3.5,   5),
    }
    stroke = [pe.withStroke(linewidth=2.5, foreground="white")]
    for _, row in stop_stats.iterrows():
        if row["stop_name"] not in _LABEL:
            continue
        ox, oy = _LABEL[row["stop_name"]]
        ax.annotate(
            row["label"],
            xy=(row["pct_dw0"], row["mean_arr"]),
            xytext=(row["pct_dw0"] + ox, row["mean_arr"] + oy),
            fontsize=8, color="#333333",
            arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.8),
            path_effects=stroke,
            zorder=5,
        )

    # ── Achsen + Styling ──────────────────────────────────────────────────────
    ax.set_xlabel("% Stops with dwell_time = 0s (no scheduled buffer)")
    ax.set_ylabel("Ø Arrival Delay (s)")
    ax.set_title("Stop Types: Accumulation Traps vs. Recovery Anchors",
                 **TITLE_KW)
    ax.set_xlim(10, 108)
    ax.set_ylim(*(ylim if ylim is not None else (30, 140)))
    style_ax(ax)
    ax.grid(color="#eeeeee", lw=0.7, zorder=0)
    ax.legend(**{**LEGEND_KW, "loc": "center right"})

    plt.tight_layout()
    plt.show()


def plot_dwell_line_scatter(lf: pl.LazyFrame, ylim=None) -> None:
    """Scatter: struktureller Aufbau pro Fahrt vs. Ø Arrival Delay — pro Linie.

    x = structural_per_trip (mean delay_delta × avg_stops) — kumulierter Aufbau
    y = mean_arrival_delay
    Farbe = mean delay_delta (Akkumulationsrate pro Halt)
    Größe = avg_stops (Routenlänge als visueller Faktor)

    Erklärt: warum L11 trotz gleicher dw0-Rate wie L6 viel mehr Delay hat
    → längere Route + höhere Ausgangs-Verspätung.
    """
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.patheffects as pe_mod

    lf_w = lf.with_columns(
        ((pl.col("departure_schedule") - pl.col("arrival_schedule"))
         .dt.total_seconds().cast(pl.Int32)).alias("dwell_time")
    )

    line_stats = (
        lf_w
        .filter(pl.col("delay_delta").is_not_null())
        .group_by("line_name")
        .agg([
            pl.col("delay_delta").mean().alias("mean_dd"),
            pl.col("arrival_delay").mean().alias("mean_arr"),
        ])
        .collect(engine="streaming")
        .to_pandas()
    )
    avg_stops_line = (
        lf_w
        .group_by(["line_name", "trip_id", "operating_date"])
        .agg(pl.len().alias("n"))
        .group_by("line_name")
        .agg(pl.col("n").mean().alias("avg_stops"))
        .collect(engine="streaming")
        .to_pandas()
    )
    df = (line_stats
          .merge(avg_stops_line, on="line_name")
          .assign(
              structural=lambda d: d["mean_dd"] * d["avg_stops"],
              line_str=lambda d: d["line_name"].astype(str).apply(fmt_line_legend),
          ))

    cmap = LinearSegmentedColormap.from_list(
        "dw_cmap", [cfg.COLOR_POSITIVE, "#cccccc", cfg.COLOR_NEGATIVE], N=256
    )
    s_min, s_max = df["avg_stops"].min(), df["avg_stops"].max()
    sizes = (df["avg_stops"] - s_min) / (s_max - s_min) * 300 + 60

    fig, ax = plt.subplots(figsize=(10, 6.5))

    sc = ax.scatter(
        df["structural"],
        df["mean_arr"],
        c=df["mean_dd"],
        s=sizes,
        cmap=cmap,
        vmin=df["mean_dd"].min(), vmax=df["mean_dd"].max(),
        alpha=0.85,
        linewidths=0.6,
        edgecolors="#888888",
        zorder=3,
    )
    cbar = fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("Ø delay_delta (s/Halt)", fontsize=9, color=cfg.CHART_AXIS_TEXT)
    cbar.ax.tick_params(labelsize=8, colors=cfg.CHART_AXIS_TEXT)

    stroke = [pe.withStroke(linewidth=2.5, foreground="white")]
    for _, row in df.iterrows():
        ax.annotate(
            row["line_str"],
            xy=(row["structural"], row["mean_arr"]),
            xytext=(row["structural"] + 1.5, row["mean_arr"] + 0.5),
            fontsize=9.5, fontweight="bold",
            color=line_color(str(row["line_name"])),
            path_effects=stroke,
            zorder=5,
        )

    # Größen-Legende
    for n_stops in [10, 18, 26]:
        sz = (n_stops - s_min) / (s_max - s_min) * 300 + 60
        ax.scatter([], [], s=sz, color="#bbbbbb", alpha=0.8,
                   edgecolors="#888888", label=f"Ø {n_stops} stops")
    ax.legend(title="Route Length", fontsize=8.5, frameon=False,
              title_fontsize=8.5, loc="upper left")

    ax.set_xlabel("Structural factor: Ø delay_delta × Ø stops / trip (s)")
    ax.set_ylabel("Ø Arrival Delay (s)")
    ax.set_title("Line Profile: Structural Build-up vs. Arrival Delay",
                 **TITLE_KW)
    style_ax(ax)
    ax.grid(color="#eeeeee", lw=0.7, zorder=0)
    if ylim is not None:
        ax.set_ylim(*ylim)

    plt.tight_layout()
    plt.show()


def plot_lever_comparison(lf: pl.LazyFrame, ylim=None) -> None:
    """Hebel-Vergleich: Fahrplan-Struktur vs. externe Einflussfaktoren.

    Strukturfaktor dynamisch aus lf berechnet: mean(delay_delta) × avg_stops_per_trip.
    Externe Faktoren: verifizierte Δ-Werte (s) aus 03_analysis_*.ipynb.
    Einheiten:
        Strukturfaktor = kumulierter Verspätungsaufbau pro Ø Fahrt
        Externe        = Δ Arrival Delay pro Halt vs. Baseline-Bedingung
    """
    # ── Struktureller Hebel (dynamisch) ───────────────────────────────────────
    mean_delta = (
        lf
        .select(pl.col("delay_delta").drop_nulls().mean())
        .collect()
        .item()
    )
    avg_stops = (
        lf
        .group_by(["trip_id", "operating_date"])
        .agg(pl.len().alias("n"))
        .select(pl.col("n").mean())
        .collect(engine="streaming")
        .item()
    )
    structural = mean_delta * avg_stops

    # ── Externe Faktoren (verifiziert aus 03_analysis_*.ipynb) ────────────────
    # Δ Arrival Delay (s) — Aufschlag vs. Baseline-Bedingung, pro Halt
    _ext = [
        ("Snow",           +54.0, "#5b8db8"),   # F-WEAT-01
        ("Heavy Rain",     +22.0, "#5b8db8"),   # F-WEAT-02
        ("November",       +16.4, "#7b9fc4"),   # F-TIME-05
        ("Evening (21h)",  +11.7, "#7b9fc4"),   # F-TIME-01
        ("Major Event",    +10.5, "#9bb5d0"),   # F-EVT-01
        ("Thursday",       + 4.2, "#9bb5d0"),   # F-TIME-03
        ("Holiday",        - 9.9, cfg.COLOR_POSITIVE),  # F-EVT-04
    ]

    # ── Daten zusammenstellen ─────────────────────────────────────────────────
    struct_label = (
        f"Schedule Structure\n(Ø {avg_stops:.0f} stops × {mean_delta:.1f}s / stop)"
    )
    labels = [struct_label] + [f[0] for f in _ext]
    values = [structural]   + [f[1] for f in _ext]
    colors = [cfg.COLOR_SIGNAL] + [f[2] for f in _ext]

    n = len(labels)
    y_pos = list(range(n - 1, -1, -1))   # oben = prominentester Eintrag

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 5.5))

    bars = ax.barh(y_pos, values, color=colors, height=0.52, zorder=3)

    # Wert-Labels
    x_abs_max = max(abs(v) for v in values)
    offset = x_abs_max * 0.02
    for bar, val in zip(bars, values):
        sign = "+" if val > 0 else ""
        txt  = f"{sign}{val:.0f}s"
        if val >= 0:
            ax.text(bar.get_width() + offset,
                    bar.get_y() + bar.get_height() / 2,
                    txt, va="center", ha="left",
                    fontsize=9.5, color=cfg.CHART_AXIS_TEXT, fontweight="semibold")
        else:
            ax.text(bar.get_width() - offset,
                    bar.get_y() + bar.get_height() / 2,
                    txt, va="center", ha="right",
                    fontsize=9.5, color=cfg.CHART_AXIS_TEXT, fontweight="semibold")

    # Trennlinie Strukturfaktor vs. externe Faktoren
    ax.axhline(n - 1.6, color=cfg.ANNO_REF, lw=0.8, linestyle="--", zorder=2)

    # Null-Linie
    ax.axvline(0, color=cfg.ANNO_REF, lw=0.9, alpha=0.7, zorder=2)

    # Bereichs-Labels (links der Y-Achse)
    ax.text(-x_abs_max * 0.025, n - 1, "STRUCTURE",
            ha="right", va="center", fontsize=7.5,
            color=cfg.COLOR_SIGNAL, fontweight="bold")
    ext_mid_y = (y_pos[1] + y_pos[-1]) / 2
    ax.text(-x_abs_max * 0.025, ext_mid_y, "EXTERNAL",
            ha="right", va="center", fontsize=7.5,
            color=cfg.CHART_AXIS_TEXT, fontweight="bold")

    # Einheiten-Hinweis (oben rechts, italic)
    ax.text(0.99, 0.99,
            "Structural factor: cumulative build-up per trip\n"
            "External factors: Δ Arrival Delay per stop vs. baseline",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7.5, color=cfg.ANNO_REF, style="italic",
            linespacing=1.5)

    # Achsen + Styling
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Seconds (s)")
    ax.set_title(
        "Delay Levers: Schedule Structure vs. External Factors",
        **TITLE_KW,
    )
    style_ax(ax)
    ax.grid(axis="x", color="#eeeeee", lw=0.8, zorder=0)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.set_xlim(
        left=min(values) * 1.8,
        right=x_abs_max * 1.30,
    )

    plt.tight_layout()
    plt.show()
