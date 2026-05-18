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

from zh_tram_flow.notebook import NotebookConfig


# ---------------------------------------------------------------------------
# Events Overview
# ---------------------------------------------------------------------------

def plot_events_overview(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
    """Bar charts: delay and OTP by day category (Normal / Feiertag / Event)."""
    from wgnd.core.theme import mpl_style
    if cfg is None:
        cfg = NotebookConfig()

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
    return fig


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
    if cfg is None:
        cfg = NotebookConfig()

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
    return fig


# ---------------------------------------------------------------------------
# Event district effect
# ---------------------------------------------------------------------------

def plot_event_district_effect(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
    """Bar charts: event impact (delta + absolute) per Stadtkreis."""
    from wgnd.core.theme import mpl_style
    if cfg is None:
        cfg = NotebookConfig()

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
    return fig


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
