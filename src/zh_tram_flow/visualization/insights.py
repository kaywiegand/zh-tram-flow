"""
visualization/insights.py
-------------------------
Report-ready plots for 04_insights.ipynb.

One function per insight section. All plots use cfg + line_color()
so a single theme change propagates everywhere.
"""
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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
]


def _add_milestones(ax: plt.Axes) -> None:
    for date, _label, _y_frac in MILESTONES:
        ax.axvline(pd.Timestamp(date), color=cfg.ANNO_REF, lw=1.2,
                   linestyle="--", ymax=0.95, zorder=1)


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
    monthly["date"] = pd.to_datetime(monthly[["year", "month"]].assign(day=1))

    lines = sorted(monthly["line_name"].astype(str).unique(),
                   key=lambda x: int(x) if x.isdigit() else 99)

    fig, ax = plt.subplots(figsize=(14, 5))

    for ln in lines:
        df = monthly[monthly["line_name"] == ln].sort_values("date")
        ax.plot(df["date"], df["avg_delay"],
                color=line_color(ln), lw=1.2, label=f"L{ln}")

    _add_milestones(ax)

    ax.set_ylim(0, 120)
    ax.set_title("Monatliche Ø Ankunftsverspätung — alle Linien 2023–2025",
                 **{**style["title"], "pad": 24})
    ax.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%ds"))
    _spine_style(ax)

    handles, labels = ax.get_legend_handles_labels()
    handles.append(_milestone_legend_handle())
    labels.append("Fahrplanwechsel / Baustelle")
    ax.legend(handles=handles, labels=labels,
              fontsize=9, loc="upper right", ncol=8,
              frameon=False)

    plt.tight_layout()
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
        .sort("otp_pct")
        .collect(engine="streaming")
        .to_pandas()
    )

    otp_mean = (otp["otp_pct"] * otp["n"]).sum() / otp["n"].sum()
    bar_colors = [line_color(str(ln)) for ln in otp["line_name"]]
    line_labels = [f"L{ln}" for ln in otp["line_name"]]

    fig, ax = plt.subplots(figsize=(14, 5))
    bars = ax.bar(line_labels, otp["otp_pct"], color=bar_colors, alpha=0.85)
    for bar, val in zip(bars, otp["otp_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.2,
                f"{val:.1f}%", ha="center", fontsize=9, color=cfg.CHART_AXIS_TEXT)

    ax.axhline(otp_mean, color=cfg.ANNO_MEAN, lw=1.0, linestyle=":",
               label=f"Ø Netz {otp_mean:.0f}%")
    ax.axhline(95, color=cfg.ANNO_REF, lw=1.0, linestyle="--",
               label="Ziel VBZ 95%")

    ax.set_ylim(75, 100)
    ax.set_title("OTP pro Linie", **{**style["title"], "pad": 14})
    ax.set_ylabel("On-Time Performance (%)", **style["label"])
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    _spine_style(ax)
    ax.legend(fontsize=9, frameon=False, loc="upper left", ncol=2)
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
    bars = ax.bar(labels, values, color=colors, width=0.5)
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


def plot_dwell_analysis(lf: pl.LazyFrame) -> None:
    """2 Panels: Anteil Durchfahrtshalte + Ø Delay vs. Dwell Time pro Linie.

    Panel 1: gestapelter Balken — % Haltestellen mit dwell=0s (Durchfahrt) vs. >0s (Puffer).
    Panel 2: gruppierter Balken — Ø Arrival Delay vs. Ø Dwell Time.
    Beide sortiert nach Ø Arrival Delay descending.
    """
    style = mpl_style()

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

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # Panel 1: Durchfahrtshalte als Balken (Tramlinienfarben) + Pufferzeit als gestrichelte Linie
    ax = axes[0]
    pct_null = data["pct_null_dwell"] * 100
    pct_puffer = 100 - pct_null
    ax.bar(x, pct_null, color=lc, alpha=0.7, label="Durchfahrtshalte (dwell = 0s)")
    for i, pn in enumerate(pct_null):
        ax.text(i, pn / 2, f"{pn:.0f}%", va="center", ha="center",
                fontsize=8, color="white", fontweight="bold")
    ax.plot(x, pct_puffer, color="#888888", lw=1.0, linestyle="--",
            marker="o", markersize=3, label="Mit Pufferzeit (dwell > 0s)")
    ax.set_xticks(x)
    ax.set_xticklabels(line_labels, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_title("Anteil Durchfahrtshalte pro Linie", **{**style["title"], "pad": 14})
    ax.set_ylabel("Anteil Haltestellen (%)", **style["label"])
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.legend(fontsize=9, frameon=False, loc="upper right", ncol=2)
    _spine_style(ax)

    # Panel 2: Delay als Balken (Tramlinienfarben) + Dwell Time als gestrichelte Linie
    ax = axes[1]
    ax.bar(x, data["avg_delay"], color=lc, alpha=0.7, label="Ø Arrival Delay")
    ax.plot(x, data["avg_dwell"].fillna(0), color="#888888", lw=1.0, linestyle="--",
            marker="o", markersize=3, label="Ø Dwell Time (Puffer)")
    ax.set_xticks(x)
    ax.set_xticklabels(line_labels, fontsize=9)
    ax.set_title("Verspätung vs. geplanter Puffer pro Linie", **{**style["title"], "pad": 14})
    ax.set_ylabel("Sekunden", **style["label"])
    ax.legend(fontsize=9, frameon=False, loc="upper right", ncol=2)
    _spine_style(ax)

    plt.tight_layout()
    plt.show()


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

def plot_district_maps(lf: pl.LazyFrame) -> None:
    """Zwei Stadtkreis-Karten untereinander: Ø Arrival Delay + OTP."""
    import plotly.graph_objects as go

    district_stats = (
        lf
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
    otp_map   = dict(zip(district_stats["district_nr"].astype(str),
                         district_stats["otp_pct"].round(1)))

    geo_path = PATHS["raw"] / "stadtkreise.geojson"
    with open(geo_path) as f:
        stadtkreise = json.load(f)

    kreis_ids    = [str(feat["properties"]["objid"]) for feat in stadtkreise["features"]]
    kreis_delays = [delay_map.get(kid, 0) for kid in kreis_ids]
    kreis_otps   = [otp_map.get(kid, 0) for kid in kreis_ids]

    label_lats, label_lons, delay_texts, otp_texts = [], [], [], []
    for feat in stadtkreise["features"]:
        coords = np.array(feat["geometry"]["coordinates"][0])
        label_lats.append(coords[:, 1].mean())
        label_lons.append(coords[:, 0].mean())
        kid = feat["properties"]["objid"]
        delay_texts.append(f"K{kid}<br>{delay_map.get(str(kid), 0):.0f}s")
        otp_texts.append(f"K{kid}<br>{otp_map.get(str(kid), 0):.0f}%")

    mapbox_cfg  = dict(style="carto-positron", zoom=10.5,
                       center={"lat": 47.378, "lon": 8.540})
    marker_cfg  = dict(line=dict(color="#888888", width=1), opacity=0.7)
    layout_base = dict(mapbox=mapbox_cfg,
                       margin={"r": 0, "t": 40, "l": 0, "b": 0},
                       height=500, showlegend=False)

    fig1 = go.Figure()
    fig1.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise, locations=kreis_ids, z=kreis_delays,
        featureidkey="properties.objid",
        colorscale=[[0, "#e8f4f8"], [0.5, cfg.COLOR_SIGNAL], [1, cfg.COLOR_NEGATIVE]],
        zmin=min(kreis_delays), zmax=max(kreis_delays),
        colorbar=dict(title="Delay (s)", thickness=12, len=0.5),
        marker=marker_cfg,
        hovertemplate="<b>Kreis %{location}</b><br>Ø Delay: %{z:.1f}s<extra></extra>",
    ))
    fig1.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons, mode="text", text=delay_texts,
        textfont=dict(size=11, color="#333333"), hoverinfo="skip",
    ))
    fig1.update_layout(**layout_base, title=dict(
        text="Stadtkreise — Ø Arrival Delay (hell = pünktlich, rot = verspätet)",
        font=dict(size=14, color=cfg.CHART_TITLE), x=0, xanchor="left",
    ))
    fig1.show()

    fig2 = go.Figure()
    fig2.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise, locations=kreis_ids, z=kreis_otps,
        featureidkey="properties.objid",
        colorscale=[[0, cfg.COLOR_NEGATIVE], [0.5, cfg.COLOR_SIGNAL], [1, "#e8f4f8"]],
        zmin=min(kreis_otps), zmax=max(kreis_otps),
        colorbar=dict(title="OTP (%)", thickness=12, len=0.5),
        marker=marker_cfg,
        hovertemplate="<b>Kreis %{location}</b><br>OTP: %{z:.1f}%<extra></extra>",
    ))
    fig2.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons, mode="text", text=otp_texts,
        textfont=dict(size=11, color="#333333"), hoverinfo="skip",
    ))
    fig2.update_layout(**layout_base, title=dict(
        text="Stadtkreise — OTP (rot = niedrig, hell = hoch)",
        font=dict(size=14, color=cfg.CHART_TITLE), x=0, xanchor="left",
    ))
    fig2.show()


# ── Section: Infrastruktur ────────────────────────────────────────────────────

def plot_district_delay_map(lf: pl.LazyFrame) -> None:
    """Stadtkreise eingefärbt nach Ø Arrival Delay — Plotly Mapbox."""
    import plotly.graph_objects as go

    district_delay = (
        lf
        .group_by("district_nr")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            ((pl.col("arrival_delay").abs() <= 120).mean() * 100).alias("otp_pct"),
            pl.len().alias("n"),
        ])
        .collect(engine="streaming")
        .to_pandas()
    )
    delay_map = dict(zip(district_delay["district_nr"].astype(str),
                         district_delay["avg_delay"].round(1)))
    otp_map   = dict(zip(district_delay["district_nr"].astype(str),
                         district_delay["otp_pct"].round(1)))

    geo_path = PATHS["raw"] / "stadtkreise.geojson"
    with open(geo_path) as f:
        stadtkreise = json.load(f)

    kreis_ids    = [str(feat["properties"]["objid"]) for feat in stadtkreise["features"]]
    kreis_delays = [delay_map.get(kid, 0) for kid in kreis_ids]

    label_lats, label_lons, label_texts = [], [], []
    for feat in stadtkreise["features"]:
        coords = np.array(feat["geometry"]["coordinates"][0])
        label_lats.append(coords[:, 1].mean())
        label_lons.append(coords[:, 0].mean())
        kid = feat["properties"]["objid"]
        d   = delay_map.get(str(kid), 0)
        otp = otp_map.get(str(kid), 0)
        label_texts.append(f"K{kid}<br>{d:.0f}s / {otp:.0f}%")

    colorscale = [[0, "#e8f4f8"], [0.5, cfg.COLOR_SIGNAL], [1, cfg.COLOR_NEGATIVE]]

    fig = go.Figure()
    fig.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise,
        locations=kreis_ids,
        z=kreis_delays,
        featureidkey="properties.objid",
        colorscale=colorscale,
        zmin=min(kreis_delays),
        zmax=max(kreis_delays),
        colorbar=dict(title="Ø Delay (s)", len=0.5, y=0.5),
        marker=dict(line=dict(color="#888888", width=1), opacity=0.7),
        hovertemplate="<b>Kreis %{location}</b><br>Ø Delay: %{z:.1f}s<extra></extra>",
    ))
    fig.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons, mode="text", text=label_texts,
        textfont=dict(size=11, color="#333333"), hoverinfo="skip",
    ))
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=11, mapbox_center={"lat": 47.378, "lon": 8.540},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=600,
        title=dict(
            text="Stadtkreise — Ø Arrival Delay (hell = pünktlich, rot = verspätet)",
            font=dict(size=14, color=cfg.CHART_TITLE),
            x=0, xanchor="left",
        ),
    )
    fig.show()


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
    """Daily avg arrival delay 2023–2025 — 3 panels by year with event markers (no Sonstiges).

    Replikation von an.plot_daily_delay_timeline ohne Sonstiges-Marker.
    Input: lf_clean (canceled=False, stop_sequence>1, kein E/L50/L51).
    """
    from zh_tram_flow.analytics.temporal import _add_schulferien

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

    years = [2023, 2024, 2025]
    fig, axes = plt.subplots(3, 1, figsize=(18, 12), sharex=False)

    for ax, year in zip(axes, years):
        df_year = daily[daily["operating_date"].dt.year == year].sort_values("operating_date")
        baseline = df_year["avg_delay"].mean()

        ax.plot(df_year["operating_date"], df_year["avg_delay"],
                color="#222222", lw=1.2, alpha=0.85)
        ax.axhline(baseline, color=cfg.ANNO_MEAN, lw=1.0, linestyle=":",
                   alpha=0.6, label=f"Ø {baseline:.1f}s")

        _add_schulferien(ax, alpha=0.22, color="#999999")

        ev_year = event_dates[event_dates["operating_date"].dt.year == year]
        shown: set = set()
        for _, row in ev_year.iterrows():
            cat = row["category"]
            lbl = cat if cat not in shown else None
            ax.axvline(row["operating_date"], color=_category_colors[cat],
                       lw=1.0, alpha=0.8, label=lbl)
            shown.add(cat)

        ax.set_title(str(year), **{**style["title"], "pad": 14})
        ax.set_ylabel("Ø Arrival Delay (s)", **style["label"])
        ax.set_xlim(pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"))
        ax.legend(fontsize=9, frameon=False, loc="upper left", ncol=4)
        _spine_style(ax)

    axes[-1].set_xlabel("Datum", **style["label"])
    plt.suptitle("Daily Delay Timeline 2023–2025 — Events & Schulferien",
                 fontsize=14, fontweight="bold", color=cfg.CHART_TITLE, y=1.01)
    plt.tight_layout()
    plt.show()
