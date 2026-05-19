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
"""

import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def _get_cfg(cfg):
    if cfg is None:
        from zh_tram_flow.notebook import NotebookConfig
        cfg = NotebookConfig()
    return cfg


# ---------------------------------------------------------------------------
# Events Overview
# ---------------------------------------------------------------------------

def plot_events_overview(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
    """Bar charts: delay and OTP by day category (Normal / Feiertag / Event)."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    categories = (
        lf_delay
        .with_columns([
            pl.when(pl.col("is_holiday")).then(pl.lit("Feiertag"))
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

    order    = ["Normal", "Feiertag", "Event klein (1)", "Event mittel (2)", "Event gross (3)"]
    cat_plot = categories.set_index("day_type").reindex(order).dropna().reset_index()

    style    = mpl_style()
    avg      = cat_plot[cat_plot["day_type"] == "Normal"]["avg_delay"].values[0]
    colors_cat = [
        cfg.COLOR_NEGATIVE if v > avg * 1.1
        else cfg.COLOR_POSITIVE if v < avg * 0.95
        else cfg.PALETTE_CATEGORICAL[4]
        for v in cat_plot["avg_delay"]
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    # Delay
    bars = ax1.bar(cat_plot["day_type"], cat_plot["avg_delay"], color=colors_cat, alpha=0.85)
    ax1.axhline(avg, color=cfg.ANNO_MEAN, lw=1.5, linestyle="--", label=f"Normal: {avg:.1f}s")
    for bar, v in zip(bars, cat_plot["avg_delay"]):
        n_val = cat_plot.loc[cat_plot["avg_delay"] == v, "n"].values[0]
        ax1.text(bar.get_x() + bar.get_width() / 2, v + 0.3,
                 f"{v:+.1f}s\n(n={n_val/1000:.0f}k)",
                 ha="center", va="bottom", fontsize=8)
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Delay nach Tages-Kategorie", **style["title"])
    ax1.tick_params(axis="x", rotation=20)
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    # OTP
    otp_base   = cat_plot[cat_plot["day_type"] == "Normal"]["otp_rate"].values[0]
    otp_colors = [cfg.COLOR_POSITIVE if v >= otp_base else cfg.COLOR_NEGATIVE
                  for v in cat_plot["otp_rate"]]
    ax2.bar(cat_plot["day_type"], cat_plot["otp_rate"], color=otp_colors, alpha=0.85)
    ax2.axhline(otp_base, color=cfg.ANNO_MEAN, lw=1.5, linestyle="--", label="Normal OTP")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax2.set_ylabel("OTP Rate", **style["label"])
    ax2.set_title("OTP nach Tages-Kategorie", **style["title"])
    ax2.tick_params(axis="x", rotation=20)
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()


def table_events_overview(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return delay + OTP stats per day category."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    categories = (
        lf_delay
        .with_columns([
            pl.when(pl.col("is_holiday")).then(pl.lit("Feiertag"))
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

    order    = ["Normal", "Feiertag", "Event klein (1)", "Event mittel (2)", "Event gross (3)"]
    cat_plot = categories.set_index("day_type").reindex(order).dropna().reset_index()

    result = (
        cat_plot[["day_type", "avg_delay", "otp_rate", "n"]]
        .rename(columns={
            "day_type":  "Kategorie",
            "avg_delay": "Ø Delay (s)",
            "otp_rate":  "OTP",
            "n":         "N Halte",
        })
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
    )
    result["Ø Delay (s)"] = result["Ø Delay (s)"].round(2)
    return result.set_index("Kategorie")


# ---------------------------------------------------------------------------
# Event type + hourly profile
# ---------------------------------------------------------------------------

def plot_event_type_hourly_profile(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
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
    et_colors = [cfg.COLOR_NEGATIVE if v > baseline * 1.15 else cfg.PALETTE_CATEGORICAL[4]
                 for v in event_type["avg_delay"]]
    ax1.barh(event_type["event_type"], event_type["avg_delay"], color=et_colors, alpha=0.85)
    ax1.axvline(baseline, color=cfg.ANNO_MEAN, lw=1.5, linestyle="--",
                label=f"Ø Normal: {baseline:.1f}s")
    ax1.set_xlabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Delay nach Event-Typ", **style["title"])
    ax1.invert_yaxis()
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    # Stunden-Profil
    for has_ev, label, color in [(False, "Normaltag", colors[0]), (True, "Event-Tag", colors[1])]:
        df = hourly_event[hourly_event["has_event"] == has_ev].sort_values("hour")
        ax2.plot(df["hour"], df["avg_delay"], color=color, lw=2,
                 marker="o", markersize=4, label=label)
    ax2.set_xticks(range(0, 24, 2))
    ax2.set_xlabel("Stunde", **style["label"])
    ax2.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax2.set_title("Stunden-Profil: Normaltag vs. Event-Tag", **style["title"])
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Event district effect
# ---------------------------------------------------------------------------

def plot_event_district_effect(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
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
    colors_bar = [cfg.COLOR_NEGATIVE if d > 2 else cfg.PALETTE_CATEGORICAL[4]
                  for d in pivot_district["delta"]]
    colors2    = cfg.palette_n(2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Delta
    bars = ax1.barh(pivot_district["district_name"], pivot_district["delta"],
                    color=colors_bar, alpha=0.85)
    ax1.axvline(0, color=cfg.ANNO_REF, lw=1, linestyle=":")
    ax1.bar_label(bars,
                  labels=[f"+{v:.1f}s" if v > 0 else f"{v:.1f}s"
                          for v in pivot_district["delta"]],
                  padding=3, fontsize=8)
    ax1.set_xlabel("Δ Delay Event − Normal (s)", **style["label"])
    ax1.set_title("Event-Effekt nach Stadtkreis", **style["title"])
    ax1.spines[["top", "right"]].set_visible(False)

    # Absolute Delays
    x = range(len(pivot_district))
    w = 0.35
    ax2.bar([xi - w / 2 for xi in x], pivot_district["normal"], w,
            label="Normal", color=colors2[0], alpha=0.85)
    ax2.bar([xi + w / 2 for xi in x], pivot_district["event"], w,
            label="Event-Tag", color=colors2[1], alpha=0.85)
    ax2.set_xticks(x)
    ax2.set_xticklabels(pivot_district["district_name"], rotation=45, ha="right", fontsize=9)
    ax2.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax2.set_title("Ø Delay — Normal vs. Event-Tag nach Kreis", **style["title"])
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()


def plot_monthly_holiday_timeline(lf: pl.LazyFrame, cfg=None) -> None:
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
                color=colors[i], lw=2, marker="o", markersize=4, label=str(year))

    _add_schulferien(ax, alpha=0.13, color="#999999")

    for i, hdate in enumerate(holiday_dates):
        lbl = "Feiertag" if i == 0 else None
        ax.axvline(pd.Timestamp(hdate), color="#bbbbbb", lw=0.8,
                   linestyle="--", alpha=0.5, label=lbl)

    ax.set_xlabel("Monat", **style["label"])
    ax.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax.set_title("Monthly Delay Profile — Holidays & School Breaks", **style["title"])
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
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
        textfont=dict(size=11, color="#cccccc"),
        hoverinfo="skip",
    ))

    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_zoom=11,
        mapbox_center={"lat": 47.378, "lon": 8.540},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=650,
        title="Event Impact per Stop — Δ Delay (Event vs. Normal)",
    )
    fig.show()


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
            "stop_name":     "Haltestelle",
            "district_name": "Stadtkreis",
            "normal":        "Normal (s)",
            "event":         "Event-Tag (s)",
            "delta":         "Δ (s)",
            "n_event":       "N Halte (Events)",
        })
        .round({"Normal (s)": 1, "Event-Tag (s)": 1})
        .reset_index(drop=True)
    )


def plot_daily_delay_timeline(lf: pl.LazyFrame, cfg=None) -> None:
    """Daily avg delay per year (3 subplots) with school break shading and event type markers."""
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

    style = mpl_style()
    line_color = "#222222"
    years = [2023, 2024, 2025]
    fig, axes = plt.subplots(3, 1, figsize=(18, 12), sharex=False)

    for ax, year in zip(axes, years):
        df_year = daily[daily["operating_date"].dt.year == year].sort_values("operating_date")
        baseline = df_year["avg_delay"].mean()

        ax.plot(df_year["operating_date"], df_year["avg_delay"],
                color=line_color, lw=1.2, alpha=0.85)
        ax.axhline(baseline, color=cfg.ANNO_MEAN, lw=1, linestyle="--",
                   alpha=0.6, label=f"Ø {baseline:.1f}s")

        _add_schulferien(ax, alpha=0.22, color="#999999")

        ev_year = event_dates[event_dates["operating_date"].dt.year == year]
        shown = set()
        for _, row in ev_year.iterrows():
            cat = row["category"]
            lbl = cat if cat not in shown else None
            ax.axvline(row["operating_date"], color=category_colors.get(cat, "#aaaaaa"),
                       lw=1.0, alpha=0.8, label=lbl)
            shown.add(cat)

        ax.set_title(str(year), **style["title"])
        ax.set_ylabel("Ø Delay (s)", **style["label"])
        ax.set_xlim(pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"))
        ax.legend(fontsize=8, loc="upper left", ncol=4)
        ax.spines[["top", "right"]].set_visible(False)

    axes[-1].set_xlabel("Datum", **style["label"])
    fig.suptitle("Daily Delay Timeline — Events & School Breaks", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
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
            "avg_delay":      "Ø Delay (s)",
            "otp":            "OTP",
            "n":              "N Halte",
        })
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"Ø Delay (s)": lambda df: df["Ø Delay (s)"].round(1)})
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
            "district_name": "Stadtkreis",
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
    return result.set_index("Stadtkreis")
