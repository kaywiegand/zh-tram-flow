"""
Events & holidays analytics — impact on tram delays.

Note: The notebook must add the corrected has_event column before calling
these functions:
    lf_all = lf_all.with_columns(
        (pl.col("event_name").cast(pl.Utf8) != "no_event").alias("has_event")
    )

Functions:
  plot_events_overview(lf, cfg=None)
  table_events_overview(lf)
  plot_event_type_hourly_profile(lf, cfg=None)
  plot_event_district_effect(lf, cfg=None)
  table_event_district_effect(lf)
  plot_holiday_recovery(lf, cfg=None)
"""

import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from zh_tram_flow.plot_styles import (style_ax, LEGEND_KW, LEGEND_KW_RIGHT, LEGEND_KW_LEFT,
                                               mean_kw, median_kw, otp_kw, trend_kw, data_line_kw,
                                               FIG_SINGLE, FIG_2PANEL, FIG_3PANEL, FIG_TIMELINE, FIG_WIDE, FIG_TALL,
                                               TITLE_KW, fmt_line_axis, fmt_line_legend, plotly_title)
from zh_tram_flow.config import ANNO_MEDIAN, auto_export, ANNO_MEAN, BAR_NEUTRAL


def _get_cfg(cfg):
    if cfg is None:
        from wgnd.core.config import cfg as _default_cfg
        cfg = _default_cfg
    return cfg


# ---------------------------------------------------------------------------
# Events Overview
# ---------------------------------------------------------------------------

@auto_export("events-events-overview")
def plot_events_overview(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
    """Stacked bars: Normal (grau) + Delta (Farbe) je Event-Kategorie.
    Rechte Achse: Delta in % (teal Linie). Analog zu plot_weather_overview.
    """
    from wgnd.core.theme import mpl_style
    from matplotlib.lines import Line2D
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    categories = (
        lf_delay
        .with_columns([
            pl.when(pl.col("is_holiday")).then(pl.lit("Holiday"))
              .when(pl.col("has_event") & (pl.col("event_weight") == 1)).then(pl.lit("Event klein (1)"))
              .when(pl.col("has_event") & (pl.col("event_weight") == 2)).then(pl.lit("Event mittel (2)"))
              .when(pl.col("has_event") & (pl.col("event_weight") == 3)).then(pl.lit("Event gross (3)"))
              .otherwise(pl.lit("Normal"))
              .alias("day_type")
        ])
        .group_by("day_type")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal_val = categories.loc[categories["day_type"] == "Normal", "avg_delay"].values[0]

    order    = ["Event gross (3)", "Event mittel (2)", "Event klein (1)", "Holiday"]
    cat_plot = categories.set_index("day_type").reindex(order).dropna().reset_index()

    deltas     = [v - normal_val for v in cat_plot["avg_delay"]]
    delta_pcts = [d / normal_val * 100 for d in deltas]

    _event_colors = {
        "Event gross (3)":  "#d73027",
        "Event mittel (2)": "#d73027",
        "Event klein (1)":  "#fed976",
        "Holiday":         "#92c5de",   # blau — unter Normal (positiv)
    }

    style  = mpl_style()
    _teal  = cfg.COLOR_POSITIVE
    x_arr  = list(range(len(cat_plot)))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax_r = ax.twinx()

    # Stacked bars: grau (Normal) als Basis
    ax.bar(x_arr, [normal_val] * len(x_arr), color="#aaaaaa", alpha=0.6)

    # Delta-Balken obendrauf (oder darunter bei negativem Delta)
    for xi, (_, row), d in zip(x_arr, cat_plot.iterrows(), deltas):
        color = _event_colors[row["day_type"]]
        ax.bar(xi, d, bottom=normal_val, color=color, alpha=0.6)
        sign = "+" if d >= 0 else ""
        y_text = normal_val + d + (0.8 if d >= 0 else -0.8)
        va     = "bottom" if d >= 0 else "top"
        ax.text(xi, y_text, f"{sign}{d:.0f}s",
                ha="center", va=va, fontsize=9)

    # Rechte Achse: Delta in %
    # 0% muss auf Höhe von normal_val liegen → Grenzen proportional zur linken Achse berechnen
    left_max   = 90
    left_frac  = normal_val / left_max          # relative Position von normal_val (0..1)
    r_max      = max(delta_pcts) * 1.25 if max(delta_pcts) > 0 else 10
    r_min      = -left_frac * r_max / (1 - left_frac)  # damit 0% genau bei left_frac liegt

    ax_r.plot(x_arr, delta_pcts, color=_teal, lw=1.0, linestyle="--",
              marker="o", markersize=5, zorder=5)
    ax_r.set_ylim(r_min, r_max)
    ax_r.set_ylabel("Delta (%)", fontsize=10, color=_teal)
    ax_r.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax_r.tick_params(axis="y", colors=_teal, labelsize=9)
    ax_r.spines[["top", "left"]].set_visible(False)
    ax_r.spines["right"].set_color(_teal)

    ax.set_xticks(x_arr)
    ax.set_xticklabels(cat_plot["day_type"], fontsize=10)
    ax.set_ylim(0, left_max)
    ax.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax.set_title("Event Category Impact on Delays", **TITLE_KW)
    style_ax(ax)

    legend_handles = [
        Line2D([0], [0], color="#aaaaaa", lw=1.0,               label="Normal"),
        Line2D([0], [0], color="#d73027", lw=1.0,               label="+Delta"),
        Line2D([0], [0], color="#92c5de", lw=1.0,               label="−Delta"),
        Line2D([0], [0], color=_teal,     lw=1.0, linestyle="--", label="Δ (%)"),
    ]
    ax.legend(**LEGEND_KW_RIGHT)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_events_overview(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return delay + OTP stats per day category."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    categories = (
        lf_delay
        .with_columns([
            pl.when(pl.col("is_holiday")).then(pl.lit("Holiday"))
              .when(pl.col("has_event") & (pl.col("event_weight") == 1)).then(pl.lit("Event klein (1)"))
              .when(pl.col("has_event") & (pl.col("event_weight") == 2)).then(pl.lit("Event mittel (2)"))
              .when(pl.col("has_event") & (pl.col("event_weight") == 3)).then(pl.lit("Event gross (3)"))
              .otherwise(pl.lit("Normal"))
              .alias("day_type")
        ])
        .group_by("day_type")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    order    = ["Normal", "Holiday", "Event klein (1)", "Event mittel (2)", "Event gross (3)"]
    cat_plot = categories.set_index("day_type").reindex(order).dropna().reset_index()

    result = (
        cat_plot[["day_type", "avg_delay", "otp_rate", "n"]]
        .rename(columns={
            "day_type":  "Kategorie",
            "avg_delay": "Avg. Delay (s)",
            "otp_rate":  "OTP",
            "n":         "N Halte",
        })
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
    )
    result["Avg. Delay (s)"] = result["Avg. Delay (s)"].round(2)
    return result.set_index("Kategorie")


# ---------------------------------------------------------------------------
# Event type + hourly profile
# ---------------------------------------------------------------------------

@auto_export("events-event-type-hourly-profile")
def plot_event_type_hourly_profile(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
    """Bar chart of delay by event type + line chart hourly profile (normal vs event day)."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    event_type = (
        lf_delay
        .filter(pl.col("has_event") == True)
        .group_by("event_type")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("avg_delay", descending=True)
        .collect()
        .to_pandas()
    )

    hourly_event = (
        lf_delay
        .group_by(["hour", "has_event"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort(["hour", "has_event"])
        .collect()
        .to_pandas()
    )

    baseline = lf_delay.select(pl.col("arrival_delay").mean()).collect().item()
    style    = mpl_style()
    colors   = cfg.palette_n(2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    # Event-Typ Balken
    et_colors = [cfg.COLOR_NEGATIVE if v > baseline * 1.15 else BAR_NEUTRAL
                 for v in event_type["avg_delay"]]
    ax1.barh(event_type["event_type"], event_type["avg_delay"], color=et_colors, alpha=0.85)
    ax1.axvline(baseline, **mean_kw(f"Ø Normal: {baseline:.1f}s"))
    ax1.set_xlabel("Avg. Arrival Delay (s)", **style["label"])
    ax1.set_title("Delay by Event Type", **TITLE_KW)
    ax1.invert_yaxis()
    ax1.legend(**LEGEND_KW_RIGHT)
    ax1.spines[["top", "right"]].set_visible(False)

    # Stunden-Profil
    for has_ev, label, color in [(False, "Regular Day", colors[0]), (True, "Event Day", colors[1])]:
        df = hourly_event[hourly_event["has_event"] == has_ev].sort_values("hour")
        ax2.plot(df["hour"], df["avg_delay"], color=color, lw=1.0,
                 marker="o", markersize=4, label=label)
    ax2.set_xticks(range(0, 24, 2))
    ax2.set_xlabel("Hour", **style["label"])
    ax2.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax2.set_title("Hourly Profile: Regular Day vs. Event Day", **TITLE_KW)
    ax2.legend(**LEGEND_KW_RIGHT)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


# ---------------------------------------------------------------------------
# Event district effect
# ---------------------------------------------------------------------------

@auto_export("events-event-district-effect")
def plot_event_district_effect(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
    """Bar charts: event impact (delta + absolute) per Stadtkreis."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    district_event = (
        lf_delay
        .group_by(["district_name", "has_event"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal_df = (
        district_event[district_event["has_event"] == False]
        .rename(columns={"avg_delay": "normal", "n": "n_normal"})
        [["district_name", "normal", "n_normal"]]
    )
    event_df = (
        district_event[district_event["has_event"] == True]
        .rename(columns={"avg_delay": "event", "n": "n_event"})
        [["district_name", "event", "n_event"]]
    )

    pivot_district = (
        normal_df.merge(event_df, on="district_name")
                 .dropna(subset=["normal", "event"])
                 .reset_index(drop=True)
    )
    pivot_district["delta"] = pivot_district["event"] - pivot_district["normal"]
    pivot_district = pivot_district.sort_values("delta", ascending=False)

    style      = mpl_style()
    colors_bar = [cfg.COLOR_NEGATIVE if d > 2 else BAR_NEUTRAL
                  for d in pivot_district["delta"]]
    colors2    = cfg.palette_n(2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Delta
    bars = ax1.barh(pivot_district["district_name"], pivot_district["delta"],
                    color=colors_bar, alpha=0.85)
    ax1.bar_label(bars,
                  labels=[f"+{v:.1f}s" if v > 0 else f"{v:.1f}s"
                          for v in pivot_district["delta"]],
                  padding=3, fontsize=8)
    ax1.set_xlabel("Δ Delay Event − Normal (s)", **style["label"])
    ax1.set_title("Event Effect by District", **TITLE_KW)
    ax1.spines[["top", "right"]].set_visible(False)

    # Absolute Delays
    x = range(len(pivot_district))
    w = 0.35
    ax2.bar([xi - w / 2 for xi in x], pivot_district["normal"], w,
            label="Normal", color=colors2[0], alpha=0.85)
    ax2.bar([xi + w / 2 for xi in x], pivot_district["event"], w,
            label="Event Day", color=colors2[1], alpha=0.85)
    ax2.set_xticks(x)
    ax2.set_xticklabels(pivot_district["district_name"], rotation=45, ha="right", fontsize=9)
    ax2.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax2.set_title("Avg. Delay — Normal vs. Event Day by District", **TITLE_KW)
    ax2.legend(**LEGEND_KW_RIGHT)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


@auto_export("events-monthly-holiday-timeline")
def plot_monthly_holiday_timeline(lf: pl.LazyFrame, cfg=None, save_as=None) -> None:
    """Monthly avg delay per year (2023/2024/2025) with school break shading and holiday markers."""
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.analytics.temporal import _add_schulferien
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    monthly = (
        lf_delay
        .with_columns([
            pl.col("operating_date").dt.year().alias("year"),
            pl.col("operating_date").dt.month().alias("month"),
        ])
        .group_by(["year", "month"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort(["year", "month"])
        .collect()
        .to_pandas()
    )
    monthly["date"] = pd.to_datetime(
        monthly[["year", "month"]].assign(day=1).rename(
            columns={"year": "year", "month": "month"}
        )
    )

    holiday_dates = (
        lf_delay
        .filter(pl.col("is_holiday") == True)
        .select("operating_date")
        .unique()
        .collect()
        .to_pandas()["operating_date"]
    )
    holiday_dates = sorted(pd.to_datetime(holiday_dates))

    style  = mpl_style()
    colors = cfg.palette_n(3)

    fig, ax = plt.subplots(figsize=(16, 5))

    for i, year in enumerate([2023, 2024, 2025]):
        df_year = monthly[monthly["year"] == year].sort_values("date")
        ax.plot(df_year["date"], df_year["avg_delay"],
                color=colors[i], lw=1.0, marker="o", markersize=4, label=str(year))

    _add_schulferien(ax, alpha=0.13, color="#999999")

    for i, hdate in enumerate(holiday_dates):
        lbl = "Holiday" if i == 0 else None
        ax.axvline(pd.Timestamp(hdate), color="#bbbbbb", lw=0.8,
                   linestyle="--", alpha=0.5, label=lbl)

    ax.set_xlabel("Month", **style["label"])
    ax.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax.set_title("Monthly Delay Profile — Holidays & School Breaks", **TITLE_KW)
    ax.legend(**LEGEND_KW_RIGHT)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_event_type_hourly_profile(lf: pl.LazyFrame) -> pd.DataFrame:
    """Hourly avg delay: normal days vs event days side by side."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    hourly = (
        lf_delay
        .group_by(["hour", "has_event"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .sort(["hour", "has_event"])
        .collect()
        .to_pandas()
    )

    normal = hourly[hourly["has_event"] == False][["hour", "avg_delay", "n"]].rename(
        columns={"avg_delay": "Normal (s)", "n": "N Normal"}
    )
    event = hourly[hourly["has_event"] == True][["hour", "avg_delay", "n"]].rename(
        columns={"avg_delay": "Event-Tag (s)", "n": "N Event"}
    )

    result = normal.merge(event, on="hour")
    result["Δ (s)"] = (result["Event-Tag (s)"] - result["Normal (s)"]).round(1)
    result["Normal (s)"] = result["Normal (s)"].round(1)
    result["Event-Tag (s)"] = result["Event-Tag (s)"].round(1)
    return result.set_index("hour")


@auto_export("events-stop-map")
def plot_event_stop_map(lf: pl.LazyFrame) -> None:
    """Plotly bubble map: Δ delay per stop (event days vs normal days)."""
    import plotly.graph_objects as go
    import json

    lf_delay = lf.filter(pl.col("canceled") == False)

    stop_event = (
        lf_delay
        .group_by(["stop_name", "stop_lat", "stop_lon", "has_event"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal = (
        stop_event[stop_event["has_event"] == False]
        [["stop_name", "stop_lat", "stop_lon", "avg_delay", "n"]]
        .rename(columns={"avg_delay": "normal", "n": "n_normal"})
    )
    event = (
        stop_event[stop_event["has_event"] == True]
        [["stop_name", "avg_delay", "n"]]
        .rename(columns={"avg_delay": "event", "n": "n_event"})
    )

    stops = normal.merge(event, on="stop_name").dropna()
    stops = stops[stops["n_event"] > 10000]
    stops["delta"] = (stops["event"] - stops["normal"]).round(1)
    stops["abs_delta"] = stops["delta"].abs().clip(upper=20)

    from pathlib import Path
    geo_path = Path(__file__).parents[3] / "data" / "raw" / "stadtkreise.geojson"
    with open(geo_path) as f:
        stadtkreise = json.load(f)

    # District-level delta for choropleth
    district_event = (
        lf_delay
        .group_by(["district_name", "district_nr", "has_event"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .collect()
        .to_pandas()
    )
    d_normal = district_event[district_event["has_event"] == False][["district_nr", "avg_delay"]].rename(columns={"avg_delay": "normal"})
    d_event  = district_event[district_event["has_event"] == True][["district_nr", "avg_delay"]].rename(columns={"avg_delay": "event"})
    d_delta  = d_normal.merge(d_event, on="district_nr").dropna()
    d_delta["delta"] = (d_delta["event"] - d_delta["normal"]).round(1)
    delta_map = dict(zip(d_delta["district_nr"].astype(str), d_delta["delta"]))

    kreis_ids = [str(f["properties"]["objid"]) for f in stadtkreise["features"]]
    kreis_deltas = [delta_map.get(kid, 0) for kid in kreis_ids]

    # Centroids for labels
    import numpy as np
    label_lats, label_lons, label_texts = [], [], []
    for feature in stadtkreise["features"]:
        coords = np.array(feature["geometry"]["coordinates"][0])
        label_lats.append(coords[:, 1].mean())
        label_lons.append(coords[:, 0].mean())
        kid = feature["properties"]["objid"]
        d = delta_map.get(str(kid), 0)
        label_texts.append(f"K{kid} ({d:+.1f}s)")

    fig = go.Figure()

    fig.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise,
        locations=kreis_ids,
        z=kreis_deltas,
        featureidkey="properties.objid",
        colorscale="RdBu_r",
        zmid=0,
        zmin=-5,
        zmax=5,
        colorbar=dict(title="Kreis Δ (s)", x=0.01, len=0.4, y=0.6),
        marker=dict(line=dict(color="#888888", width=1), opacity=0.45),
        hovertemplate="<b>Kreis %{location}</b><br>Δ Delay: %{z:+.1f}s<extra></extra>",
    ))

    fig.add_trace(go.Scattermapbox(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="markers",
        marker=dict(
            size=stops["abs_delta"].clip(lower=1) * 1.5,
            color=stops["delta"],
            colorscale="RdBu_r",
            cmin=-15,
            cmid=0,
            cmax=15,
            colorbar=dict(title="Δ Delay (s)"),
            opacity=0.8,
        ),
        text=stops.apply(
            lambda r: f"{r['stop_name']}<br>Normal: {r['normal']:.1f}s<br>Event: {r['event']:.1f}s<br>Δ: {r['delta']:+.1f}s",
            axis=1
        ),
        hoverinfo="text",
    ))

    fig.add_trace(go.Scattermapbox(
        lat=label_lats,
        lon=label_lons,
        mode="text",
        text=label_texts,
        textfont=dict(size=11, color="#333333"),
        hoverinfo="skip",
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=11,
        mapbox_center={"lat": 47.378, "lon": 8.540},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=650,
        title=plotly_title("Event Impact per Stop — Δ Delay (Event vs. Normal)"),
    )
    fig.show()
    return fig


def table_event_stop_map(lf: pl.LazyFrame) -> pd.DataFrame:
    """Top stops by Δ delay on event days vs normal days."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    stop_event = (
        lf_delay
        .group_by(["stop_name", "district_name", "has_event"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal = (
        stop_event[stop_event["has_event"] == False]
        [["stop_name", "district_name", "avg_delay", "n"]]
        .rename(columns={"avg_delay": "normal", "n": "n_normal"})
    )
    event = (
        stop_event[stop_event["has_event"] == True]
        [["stop_name", "avg_delay", "n"]]
        .rename(columns={"avg_delay": "event", "n": "n_event"})
    )

    stops = normal.merge(event, on="stop_name").dropna()
    stops["delta"] = (stops["event"] - stops["normal"]).round(1)
    stops = stops[stops["n_event"] > 5000].sort_values("delta", ascending=False)

    return (
        stops[["stop_name", "district_name", "normal", "event", "delta", "n_event"]]
        .head(20)
        .rename(columns={
            "stop_name":     "Stop",
            "district_name": "District",
            "normal":        "Normal (s)",
            "event":         "Event-Tag (s)",
            "delta":         "Δ (s)",
            "n_event":       "N Halte (Events)",
        })
        .round({"Normal (s)": 1, "Event-Tag (s)": 1})
        .reset_index(drop=True)
    )


@auto_export("events-daily-delay-timeline")
def plot_daily_delay_timeline(lf: pl.LazyFrame, cfg=None, save_as=None) -> None:
    """Daily avg delay 2023–2025 in einem Plot — Schulferien + Event-Marker (kein Sonstiges)."""
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.analytics.temporal import _add_schulferien
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    daily = (
        lf_delay
        .group_by("operating_date")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort("operating_date")
        .collect()
        .to_pandas()
    )
    daily["operating_date"] = pd.to_datetime(daily["operating_date"])

    event_dates = (
        lf_delay
        .filter(pl.col("has_event") == True)
        .group_by(["operating_date", "event_type"])
        .agg(pl.len().alias("n"))
        .sort("operating_date")
        .collect()
        .to_pandas()
    )
    event_dates["operating_date"] = pd.to_datetime(event_dates["operating_date"])

    event_category_map = {
        "Super League":  "Fussball",
        "Schweizer Cup": "Fussball",
        "Konzert":       "Konzert",
        "Stadtfest":     "Stadtfest",
        "Fachmesse":     "Messe/Kongress",
        "Kongress":      "Messe/Kongress",
    }
    category_colors = {
        "Fussball":      "#2ecc71",
        "Konzert":       "#e74c3c",
        "Stadtfest":     "#f39c12",
        "Messe/Kongress": "#9b59b6",
    }
    event_dates["category"] = event_dates["event_type"].map(event_category_map).fillna("Sonstiges")
    event_dates = event_dates[event_dates["category"] != "Sonstiges"]

    style = mpl_style()

    fig, ax = plt.subplots(figsize=(20, 6))

    baseline = daily["avg_delay"].mean()
    ax.plot(daily["operating_date"], daily["avg_delay"],
            color="#222222", lw=1.0, alpha=0.85)
    ax.axhline(baseline, **mean_kw(f"Ø {baseline:.1f}s"))

    _add_schulferien(ax, alpha=0.22, color="#999999")

    # Jahresgrenzen
    for year in [2024, 2025]:
        ax.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS,
                   lw=0.8, linestyle=":", alpha=0.5)

    # Event-Marker
    shown: set = set()
    for _, row in event_dates.iterrows():
        cat = row["category"]
        lbl = cat if cat not in shown else None
        ax.axvline(row["operating_date"], color=category_colors.get(cat, "#aaaaaa"),
                   lw=1.0, alpha=0.8, label=lbl)
        shown.add(cat)

    ax.set_ylabel("Avg. Delay (s)", **style["label"])
    ax.set_xlabel("Date", **style["label"])
    ax.legend(**LEGEND_KW_RIGHT)
    style_ax(ax)

    fig.suptitle("Daily Delay Timeline 2023–2025 — Events & School Holidays",
                 fontsize=11, fontweight="bold", x=0.05, ha="left", y=1.01)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_daily_delay_timeline(lf: pl.LazyFrame) -> pd.DataFrame:
    """Top event days by avg delay — one row per date with event info."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    return (
        lf_delay
        .filter(pl.col("has_event") == True)
        .group_by(["operating_date", "event_type", "event_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp"),
            pl.len().alias("n"),
        ])
        .sort("avg_delay", descending=True)
        .head(30)
        .collect()
        .to_pandas()
        .rename(columns={
            "operating_date": "Datum",
            "event_type":     "Event-Typ",
            "event_name":     "Event",
            "avg_delay":      "Avg. Delay (s)",
            "otp":            "OTP",
            "n":              "N Halte",
        })
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"Avg. Delay (s)": lambda df: df["Avg. Delay (s)"].round(1)})
        .reset_index(drop=True)
    )


def table_event_district_effect(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return event delta per Stadtkreis (sorted by delta desc)."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    district_event = (
        lf_delay
        .group_by(["district_name", "has_event"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal_df = (
        district_event[district_event["has_event"] == False]
        .rename(columns={"avg_delay": "normal", "n": "n_normal"})
        [["district_name", "normal", "n_normal"]]
    )
    event_df = (
        district_event[district_event["has_event"] == True]
        .rename(columns={"avg_delay": "event", "n": "n_event"})
        [["district_name", "event", "n_event"]]
    )

    pivot_district = (
        normal_df.merge(event_df, on="district_name")
                 .dropna(subset=["normal", "event"])
                 .reset_index(drop=True)
    )
    pivot_district["delta"] = pivot_district["event"] - pivot_district["normal"]
    pivot_district = pivot_district.sort_values("delta", ascending=False)

    result = (
        pivot_district[["district_name", "normal", "event", "delta", "n_event"]]
        .rename(columns={
            "district_name": "District",
            "normal":        "Normal (s)",
            "event":         "Event-Tag (s)",
            "delta":         "Δ (s)",
            "n_event":       "N Halte (Events)",
        })
        .round(1)
    )
    result["N Halte (Events)"] = result["N Halte (Events)"].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) else "—"
    )
    return result.set_index("District")


# ---------------------------------------------------------------------------
# Holiday / Weekend Recovery
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Stop & Line Ranking
# ---------------------------------------------------------------------------

@auto_export("events-stop-ranking")
def plot_event_stop_ranking(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
    """Horizontal bar chart: Top 15 stops by Δ delay on event days vs. normal days."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    stop_event = (
        lf_delay
        .group_by(["stop_name", "has_event"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal = (
        stop_event[stop_event["has_event"] == False]
        [["stop_name", "avg_delay", "n"]]
        .rename(columns={"avg_delay": "normal", "n": "n_normal"})
    )
    event = (
        stop_event[stop_event["has_event"] == True]
        [["stop_name", "avg_delay", "n"]]
        .rename(columns={"avg_delay": "event", "n": "n_event"})
    )

    stops = normal.merge(event, on="stop_name").dropna()
    stops = stops[stops["n_event"] > 5000]
    stops["delta"] = (stops["event"] - stops["normal"]).round(1)
    stops = stops.sort_values("delta", ascending=False).head(15)

    style  = mpl_style()
    colors = [cfg.COLOR_NEGATIVE if d > 0 else cfg.COLOR_POSITIVE for d in stops["delta"]]

    fig, ax = plt.subplots(figsize=(10, 7))

    bars = ax.barh(stops["stop_name"], stops["delta"], color=colors, alpha=0.85)
    ax.bar_label(
        bars,
        labels=[f"+{v:.1f}s" if v > 0 else f"{v:.1f}s" for v in stops["delta"]],
        padding=4, fontsize=9,
    )
    ax.invert_yaxis()
    ax.set_xlabel("Δ Delay (Event − Normal, s)", **style["label"])
    ax.set_title("Top 15 Stops by Event Impact", **TITLE_KW)
    style_ax(ax)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()
    return fig


@auto_export("events-line-ranking")
def plot_event_line_ranking(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
    """Horizontal bar chart: all lines ranked by Δ delay on event days vs. normal days."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    line_event = (
        lf_delay
        .group_by(["line_name", "has_event"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal = (
        line_event[line_event["has_event"] == False]
        [["line_name", "avg_delay", "n"]]
        .rename(columns={"avg_delay": "normal", "n": "n_normal"})
    )
    event = (
        line_event[line_event["has_event"] == True]
        [["line_name", "avg_delay", "n"]]
        .rename(columns={"avg_delay": "event", "n": "n_event"})
    )

    lines = normal.merge(event, on="line_name").dropna()
    lines["delta"] = (lines["event"] - lines["normal"]).round(1)
    lines = lines.sort_values("delta", ascending=False)

    style  = mpl_style()
    colors = [cfg.COLOR_NEGATIVE if d > 2 else BAR_NEUTRAL
              for d in lines["delta"]]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.barh(
        lines["line_name"].apply(lambda x: f"L{x}"),
        lines["delta"],
        color=colors, alpha=0.85,
    )
    ax.bar_label(
        bars,
        labels=[f"+{v:.1f}s" if v > 0 else f"{v:.1f}s" for v in lines["delta"]],
        padding=4, fontsize=9,
    )
    ax.invert_yaxis()
    ax.set_xlabel("Δ Delay Event − Normal (s)", **style["label"])
    ax.set_title("Line Ranking: Event Impact on All Tram Lines", **TITLE_KW)
    style_ax(ax)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()
    return fig


def table_event_line_ranking(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return event impact per tram line: normal vs. event-day delay, sorted by delta."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    line_event = (
        lf_delay
        .group_by(["line_name", "has_event"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal = (
        line_event[line_event["has_event"] == False]
        [["line_name", "avg_delay", "otp_rate", "n"]]
        .rename(columns={"avg_delay": "normal", "otp_rate": "otp_normal", "n": "n_normal"})
    )
    event = (
        line_event[line_event["has_event"] == True]
        [["line_name", "avg_delay", "otp_rate", "n"]]
        .rename(columns={"avg_delay": "event", "otp_rate": "otp_event", "n": "n_event"})
    )

    lines = normal.merge(event, on="line_name").dropna()
    lines["delta"] = (lines["event"] - lines["normal"]).round(1)
    lines["otp_delta"] = ((lines["otp_event"] - lines["otp_normal"]) * 100).round(1)
    lines = lines.sort_values("delta", ascending=False)

    result = (
        lines[["line_name", "normal", "event", "delta", "otp_delta", "n_event"]]
        .rename(columns={
            "line_name":  "Line",
            "normal":     "Normal (s)",
            "event":      "Event-Tag (s)",
            "delta":      "Δ (s)",
            "otp_delta":  "ΔOTP (pp)",
            "n_event":    "N Halte (Events)",
        })
        .round({"Normal (s)": 1, "Event-Tag (s)": 1})
    )
    result["N Halte (Events)"] = result["N Halte (Events)"].apply(lambda x: f"{x:,.0f}")
    result["Line"] = result["Line"].apply(lambda x: f"L{x}")
    return result.set_index("Line")


@auto_export("events-holiday-recovery")
def plot_holiday_recovery(lf: pl.LazyFrame, cfg=None, save_as=None) -> None:
    """Kapazitäts-Erholung: Stundenprofil Normaler Werktag vs. Feiertag vs. Wochenende.

    Wenn Pendler und Privatverkehr wegbleiben, erholt sich das Tramnetz —
    Feiertage erreichen Wochenend-Niveau oder besser, ohne Taktreduktion.
    Botschaft: Kapazitätslimit kommt vom Strassenverkehr, nicht vom Fahrgastaufkommen.

    Drei Kurven: Normaler Werktag · Wochenende · Feiertag
    X: Stunde (0–23)  ·  Y: Ø Arrival Delay (s)

    Input: lf_delay (canceled=False bereits gefiltert vom Notebook).
    """
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)
    style = mpl_style()

    # Classify day type: Feiertag wins over Wochenende
    hourly = (
        lf.filter(pl.col("canceled") == False)
        .with_columns(
            pl.when(pl.col("is_holiday"))
              .then(pl.lit("Holiday"))
              .when(pl.col("is_weekend"))
              .then(pl.lit("Wochenende"))
              .otherwise(pl.lit("Normaler Werktag"))
              .alias("day_type")
        )
        .group_by(["day_type", "hour"])
        .agg(pl.col("arrival_delay").mean().alias("mean_delay"))
        .sort(["day_type", "hour"])
        .collect()
        .to_pandas()
    )

    day_styles = {
        "Normaler Werktag": {"color": "#aaaaaa",          "lw": 2.0, "ls": "-",  "zorder": 2},
        "Wochenende":       {"color": cfg.COLOR_SIGNAL,   "lw": 2.0, "ls": "--", "zorder": 3},
        "Holiday":         {"color": cfg.COLOR_POSITIVE, "lw": 2.5, "ls": "-",  "zorder": 4},
    }
    order = ["Normaler Werktag", "Wochenende", "Holiday"]

    fig, ax = plt.subplots(figsize=(12, 5))

    for day_type in order:
        grp = hourly[hourly["day_type"] == day_type].sort_values("hour")
        if grp.empty:
            continue
        s = day_styles[day_type]
        ax.plot(grp["hour"], grp["mean_delay"],
                color=s["color"], lw=s["lw"], ls=s["ls"], zorder=s["zorder"],
                marker="o", markersize=4, label=day_type)
        # Label at the rightmost point
        last = grp.iloc[-1]
        ax.text(last["hour"] + 0.3, last["mean_delay"],
                f"{last['mean_delay']:.0f} s",
                color=s["color"], fontsize=9, va="center")

    ax.set_xlabel("Hour", **style["label"])
    ax.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax.set_title(
        "Capacity Recovery: Holidays and Weekends Relieve the Tram Network",
        **TITLE_KW,
    )
    ax.set_xticks(range(0, 24))
    ax.set_xlim(-0.5, 24.5)
    ax.legend(**LEGEND_KW_RIGHT)
    style_ax(ax)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()
