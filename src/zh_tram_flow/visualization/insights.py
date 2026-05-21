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
from wgnd.core.theme import mpl_style

from zh_tram_flow.config import PATHS, line_color


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
        label="Fahrplanwechsel / Baustelle",
    )


def _spine_style(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    ax.tick_params(colors=cfg.CHART_AXIS_TEXT, labelsize=10)


# ── Section: Netzstruktur ─────────────────────────────────────────────────────

def plot_monthly_delay_by_line(lf: pl.LazyFrame) -> None:
    """Monatliche Ø Arrival Delay pro Linie — 1 Panel, nur arrival_delay.

    Input: lf_clean (canceled=False, stop_sequence>1, kein E/L50/L51).
    """
    style = mpl_style()

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
                color=line_color(ln), lw=1.2, label=f"L{ln}")

    _add_milestones(ax)

    ax.set_ylim(0, 120)
    ax.set_title("Monatliche Ø Ankunftsverspätung — alle Linien 2023–2025",
                 **style["title"])
    ax.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%ds"))
    _spine_style(ax)

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
    labels.append("Fahrplanwechsel / Baustelle")
    ncol = math.ceil(len(handles) / 2)
    ax.legend(handles=handles, labels=labels,
              fontsize=9, loc="upper right", ncol=ncol,
              frameon=False)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    plt.show()


# ── Section: OTP ─────────────────────────────────────────────────────────────

def plot_otp_by_line(lf: pl.LazyFrame) -> None:
    """OTP pro Linie — vertikale Balkenchart mit Netz-Schnitt und VBZ-Ziel."""
    style = mpl_style()

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
    line_labels = [f"L{ln}" for ln in otp["line_name"]]

    fig, ax = plt.subplots(figsize=(14, 5))
    bars = ax.bar(line_labels, otp["otp_pct"], color=bar_colors, alpha=0.6)
    for bar, val in zip(bars, otp["otp_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.2,
                f"{val:.1f}%", ha="center", fontsize=9, color=cfg.CHART_AXIS_TEXT)

    ax.axhline(otp_mean, color=cfg.ANNO_MEAN, lw=1.0, linestyle=":",
               label=f"Ø Netz {otp_mean:.0f}%")
    ax.axhline(95, color=cfg.ANNO_REF, lw=1.0, linestyle="--",
               label="Ziel VBZ 95%")

    ax.set_ylim(75, 100)
    ax.set_title("On-Time-Performance (OTP) pro Linie", **style["title"])
    ax.set_ylabel("On-Time Performance (%)", **style["label"])
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    _spine_style(ax)
    ax.legend(fontsize=9, frameon=False, loc="upper right", ncol=2)
    plt.tight_layout()
    plt.show()


def plot_otp_delta_distribution(lf: pl.LazyFrame) -> None:
    """Delay Delta — 3-bar chart: wächst / sinkt / neutral."""
    style = mpl_style()

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
    ax.set_ylim(0, 85)
    ax.set_title("Delay Delta — Akkumulierend vs. Abnehmend (Anteil aller Halte)",
                 **{**style["title"], "pad": 14})
    ax.set_ylabel("Anteil (%)", **style["label"])
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    _spine_style(ax)
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
    line_labels = [f"L{ln}" for ln in data["line_name"]]
    lc = [line_color(str(ln)) for ln in data["line_name"]]
    return data, x, line_labels, lc


def plot_dwell_throughput(lf: pl.LazyFrame) -> None:
    """Anteil Durchfahrtshalte (%) + Ø Verweilzeit (s) pro Linie.

    Balken: % Halte ohne Verweilzeit (Durchfahrt), Tramlinienfarben.
    Linie (rechte Achse): Ø Verweilzeit in Sekunden — anderer Unit für Kontrast.
    Sortiert nach Ø Arrival Delay descending.
    """
    _teal = cfg.COLOR_POSITIVE  # #25ac82 — kein Overlap mit Tramlinienfarben

    style = mpl_style()
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
    ax.set_ylim(0, 108)
    ax.set_title("Anteil Durchfahrtshalte pro Linie", **style["title"])
    ax.set_ylabel("Durchfahrtshalte (%)", **style["label"])
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    ax.tick_params(colors=cfg.CHART_AXIS_TEXT, labelsize=10)

    ax_r = ax.twinx()
    ax_r.plot(x, data["avg_dwell"].fillna(0), color=_teal, lw=1.5, linestyle="--",
              marker="o", markersize=3, label="Ø Verweilzeit (s)")
    ax_r.set_ylabel("Ø Verweilzeit (s)", fontsize=10, color=_teal)
    ax_r.tick_params(axis="y", colors=_teal, labelsize=9)
    ax_r.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0fs"))
    ax_r.spines["top"].set_visible(False)
    ax_r.spines["left"].set_visible(False)
    h, l = ax_r.get_legend_handles_labels()
    ax.legend(h, l, fontsize=9, frameon=False, loc="upper right")

    plt.tight_layout()
    plt.show()


def plot_dwell_vs_delay(lf: pl.LazyFrame) -> None:
    """Ø Arrival Delay (s) + Verweilzeit (%) pro Linie.

    Balken: Ø Arrival Delay in Sekunden, Tramlinienfarben.
    Linie (rechte Achse): Verweilzeit (%) — Anteil Halte mit dwell > 0s.
    Sortiert nach Ø Arrival Delay descending.
    """
    _teal = cfg.COLOR_POSITIVE  # #25ac82 — konsistent mit plot_dwell_throughput

    style = mpl_style()
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
    ax.set_title("Verspätung vs. Verweilzeit pro Linie", **style["title"])
    ax.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    ax.tick_params(colors=cfg.CHART_AXIS_TEXT, labelsize=10)

    ax_r = ax.twinx()
    ax_r.plot(x, pct_verweil, color=_teal, lw=1.5, linestyle="--",
              marker="o", markersize=3, label="Verweilzeit (%)")
    ax_r.set_ylabel("Verweilzeit (%)", fontsize=10, color=_teal)
    ax_r.tick_params(axis="y", colors=_teal, labelsize=9)
    ax_r.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax_r.spines["top"].set_visible(False)
    ax_r.spines["left"].set_visible(False)
    h, l = ax_r.get_legend_handles_labels()
    ax.legend(h, l, fontsize=9, frameon=False, loc="upper right")

    plt.tight_layout()
    plt.show()


def plot_dwell_analysis(lf: pl.LazyFrame) -> None:
    """Wrapper: ruft plot_dwell_throughput + plot_dwell_vs_delay auf."""
    plot_dwell_throughput(lf)
    plot_dwell_vs_delay(lf)


def plot_dwell_by_stop_position(lf: pl.LazyFrame) -> None:
    """Ø Dwell Time nach Stop-Sequenz — zeigt Puffer-Konzentration am Starthalt.

    Input: lf_delay (alle Halte inkl. stop_sequence == 1).
    """
    style = mpl_style()

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
    ax.axhline(rest_mean, color=cfg.ANNO_REF, lw=1.2, linestyle="--",
               label=f"Ø Zwischen-/End-Halte {rest_mean:.1f}s")

    ax.set_title("Dwell Time nach Stop-Position — Puffer fällt auf den Starthalt",
                 **{**style["title"], "pad": 14})
    ax.set_xlabel("Stop-Sequenz (Position im Trip)", **style["label"])
    ax.set_ylabel("Ø Dwell Time (s)", **style["label"])
    ax.legend(fontsize=9, frameon=False, loc="upper right")
    _spine_style(ax)
    plt.tight_layout()
    plt.show()


# ── Section: Geografie ────────────────────────────────────────────────────────

def plot_top_delay_stops(lf: pl.LazyFrame, top_n: int = 20, min_obs: int = 50_000) -> None:
    """Top stops by average arrival delay, horizontal bar chart."""
    style = mpl_style()

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
        f"Top {top_n} Haltestellen — Ø Arrival Delay (min. {min_obs // 1000}k Beobachtungen)",
        **{**style["title"], "pad": 14},
    )
    ax.set_xlabel("Ø Delay (s)", **style["label"])
    _spine_style(ax)
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

def plot_delay_delta_timeline(lf: pl.LazyFrame) -> None:
    """Täglicher Ø Delay Delta 2023–2025 — positiv = Verspätung wächst."""
    style = mpl_style()

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
    ax.plot(daily["operating_date"], pos, lw=1.2, color=cfg.COLOR_NEGATIVE, label="Akkumulierend (≥ 0)")
    ax.plot(daily["operating_date"], neg, lw=1.2, color=cfg.COLOR_POSITIVE, label="Abnehmend (< 0)")
    ax.axhline(0, color=cfg.ANNO_REF, lw=1, linestyle="--")
    ax.set_title("Täglicher Delay Delta 2023–2025 — positiv = Verspätung wächst Stop zu Stop",
                 **{**style["title"], "pad": 14})
    ax.set_ylabel("Ø Delay Delta (s)", **style["label"])
    _spine_style(ax)
    ax.legend(fontsize=9, frameon=False, loc="upper left")
    plt.tight_layout()
    plt.show()


def plot_arrival_vs_departure_timeline(lf: pl.LazyFrame) -> None:
    """Daily avg arrival delay 2023–2025 — 1 kombiniertes Panel mit Event-Markern.

    Analog zu plot_monthly_delay_by_line: gleiche Achsen, Skala und Stil.
    Input: lf_clean (canceled=False, stop_sequence>1, kein E/L50/L51).
    """
    style = mpl_style()

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
        lbl = "Schulferien ZH" if not labeled else None
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
    ax.set_ylim(0, 140)
    ax.set_xlim(pd.Timestamp("2023-01-01"), pd.Timestamp("2026-01-15"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m"))
    ax.tick_params(axis="x", labelsize=8)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%ds"))
    ax.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax.set_title("Daily Delay Timeline 2023–2025 — Events & Schulferien",
                 **style["title"])
    _spine_style(ax)

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
              fontsize=9, loc="upper right", ncol=len(handles),
              frameon=False)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    plt.show()
