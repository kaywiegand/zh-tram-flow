"""Analytics-Modul für 03_analysis_3-temporal.ipynb — Zeitliche Muster."""

import polars as pl
from zh_tram_flow.plot_styles import (style_ax, LEGEND_KW, LEGEND_KW_RIGHT, LEGEND_KW_LEFT,
                                               mean_kw, median_kw, otp_kw, trend_kw, data_line_kw,
                                               FIG_SINGLE, FIG_2PANEL, FIG_3PANEL, FIG_TIMELINE, FIG_WIDE, FIG_TALL,
                                               TITLE_KW, fmt_line_axis, fmt_line_legend)
from zh_tram_flow.config import ANNO_MEDIAN, auto_export, ANNO_MEAN, YEAR_COLORS, SEASON_COLORS, BAR_NEUTRAL, DELAY_COLOR, OTP_ON_TIME
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def _get_cfg(cfg):
    if cfg is None:
        from wgnd.core.config import cfg as _default_cfg
        cfg = _default_cfg
    return cfg


# Schulferien Kanton Zürich 2023–2025
_SCHULFERIEN = [
    ("2023-02-06", "2023-02-17"), ("2023-04-10", "2023-04-21"),
    ("2023-07-08", "2023-08-11"), ("2023-10-02", "2023-10-13"),
    ("2023-12-23", "2024-01-05"), ("2024-02-05", "2024-02-16"),
    ("2024-04-08", "2024-04-19"), ("2024-07-06", "2024-08-09"),
    ("2024-09-30", "2024-10-11"), ("2024-12-21", "2025-01-03"),
    ("2025-02-03", "2025-02-14"), ("2025-04-07", "2025-04-17"),
    ("2025-07-05", "2025-08-08"), ("2025-10-06", "2025-10-17"),
]


def _add_schulferien(ax, alpha: float = 0.13, color: str = "#999999") -> None:
    """Schulferienperioden als graue Flächen in eine Achse einzeichnen."""
    labeled = False
    for s, e in _SCHULFERIEN:
        lbl = "School Holidays ZH" if not labeled else None
        ax.axvspan(pd.Timestamp(s), pd.Timestamp(e), alpha=alpha, color=color, label=lbl, zorder=0)
        labeled = True


@auto_export("temporal-hour-of-day")
def plot_hour_of_day(lf, cfg=None, ylim=None, save_as=None):
    """Ø Arrival Delay nach Stunde — Delay-Balken (links) + Datenvolumen (rechts, twinx)."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    hourly = (
        lf
        .group_by("hour")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            pl.len().alias("n"),
        ])
        .sort("hour")
        .collect()
        .to_pandas()
    )

    style = mpl_style()
    avg = hourly["avg_delay"].mean()
    _volume_color = "#7f8fa6"   # stahlblau-grau — klar verschieden von OTP-Grün und Delay-Amber
    threshold = avg
    colors = [DELAY_COLOR if v >= threshold else BAR_NEUTRAL
              for v in hourly["avg_delay"]]

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()

    pct_n = hourly["n"] / hourly["n"].sum() * 100
    ax2.plot(hourly["hour"], pct_n, color=_volume_color,
             lw=1.0, linestyle="-.", zorder=1, label="Share of Stop Events (%)")
    ax2.set_ylabel("Share of Stop Events (%)", fontsize=11, color=_volume_color, labelpad=8)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax2.tick_params(axis="y", colors=_volume_color, labelsize=9)
    ax2.spines[["top", "left"]].set_visible(False)
    ax2.spines["right"].set_color(_volume_color)

    ax1.bar(hourly["hour"], hourly["avg_delay"], color=colors, alpha=0.6,
            width=0.9, zorder=2)
    ax1.axhline(avg, **mean_kw(f"Ø {avg:.1f}s"))
    ax1.set_xlabel("Hour", **style["label"])
    ax1.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax1.set_title("Avg. Delay by Hour of Day", **TITLE_KW)
    ax1.set_xticks(range(0, 24, 2))
    style_ax(ax1)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, **LEGEND_KW_RIGHT)
    if ylim is not None:
        ax1.set_ylim(*ylim)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_hour_of_day(lf) -> pd.DataFrame:
    """Tabelle: Ø Delay nach Stunde des Tages."""
    hourly = (
        lf
        .group_by("hour")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            pl.len().alias("n"),
        ])
        .sort("hour")
        .collect()
        .to_pandas()
    )
    return (
        hourly.rename(columns={"hour": "Hour", "avg_delay": "Avg. Delay (s)", "med_delay": "Median (s)", "n": "N Halte"})
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Avg. Delay (s)": 1, "Median (s)": 1})
        .set_index("Hour")
    )


@auto_export("temporal-day-of-week")
def plot_day_of_week(lf, cfg=None, ylim=None, save_as=None):
    """Ø Arrival Delay + OTP nach Wochentag (Mo–So)."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    daily = (
        lf
        .group_by("weekday")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            ((pl.col("arrival_delay").abs() <= 120).mean() * 100).alias("otp_pct"),
            pl.len().alias("n"),
        ])
        .sort("weekday")
        .collect()
        .to_pandas()
    )

    day_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    style = mpl_style()
    avg = daily["avg_delay"].mean()
    colors = [DELAY_COLOR if v > avg else BAR_NEUTRAL
              for v in daily["avg_delay"]]

    fig, ax = plt.subplots(figsize=(14, 5))
    x = range(len(day_labels))

    ax.bar(x, daily["avg_delay"], color=colors, alpha=0.6)
    ax.axhline(avg, **mean_kw(f"Ø {avg:.1f}s"))

    for i, v in enumerate(daily["avg_delay"]):
        ax.text(i, v + 0.3, f"{v:+.1f}s", ha="center", va="bottom", fontsize=9)

    ax2 = ax.twinx()
    ax2.plot(x, daily["otp_pct"], color=OTP_ON_TIME, lw=1.0,
             marker="D", markersize=4, linestyle="--", alpha=0.85, label="OTP (%)")
    ax2.set_ylabel("OTP (%)", color=OTP_ON_TIME, fontsize=10)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax2.tick_params(axis="y", labelcolor=OTP_ON_TIME)
    ax2.spines[["top", "left"]].set_visible(False)
    ax2.spines["right"].set_color(OTP_ON_TIME)

    ax.set_xticks(x)
    ax.set_xticklabels(day_labels, fontsize=11)
    ax.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax.set_title("Avg. Delay + OTP by Day of Week", **TITLE_KW)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, **LEGEND_KW_RIGHT)
    style_ax(ax)
    if ylim is not None:
        ax.set_ylim(*ylim)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()



def table_day_of_week(lf) -> pd.DataFrame:
    """Tabelle: Ø Delay nach Wochentag."""
    daily = (
        lf
        .group_by("weekday")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            pl.col("arrival_delay").quantile(0.95).alias("p95_delay"),
            pl.len().alias("n"),
        ])
        .sort("weekday")
        .collect()
        .to_pandas()
    )
    day_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    daily_table = daily.copy()
    daily_table.insert(0, "Weekday", day_labels[:len(daily_table)])
    return (
        daily_table[["Weekday", "avg_delay", "med_delay", "p95_delay", "n"]]
        .rename(columns={"avg_delay": "Avg. Delay (s)", "med_delay": "Median (s)", "p95_delay": "P95 (s)", "n": "N Halte"})
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Avg. Delay (s)": 1, "Median (s)": 1, "P95 (s)": 1})
        .set_index("Weekday")
    )


@auto_export("temporal-month-seasonality")
def plot_month_seasonality(lf, cfg=None, panel: str = "both", ylim=None, save_as=None):
    """Saisonalität + Jahresvergleich nach Monat.

    panel: 'both' (default) — zwei Panels nebeneinander
           'left'            — nur Saisonalitäts-Panel (für Insights-Notebook)
    """
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    monthly_avg = (
        lf
        .group_by("month")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort("month")
        .collect()
        .to_pandas()
    )

    month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    style = mpl_style()

    avg = monthly_avg["avg_delay"].mean()
    bar_colors = [DELAY_COLOR if v > avg else BAR_NEUTRAL
                  for v in monthly_avg["avg_delay"]]

    if panel == "left":
        fig, ax1 = plt.subplots(figsize=(10, 5))
    else:
        monthly_by_year = (
            lf
            .with_columns(pl.col("operating_date").dt.year().alias("year"))
            .filter(~((pl.col("year") == 2025) & (pl.col("operating_date").dt.month() >= 11)))
            .group_by(["year", "month"])
            .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
            .sort(["month", "year"])
            .collect()
            .to_pandas()
        )
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    ax1.bar(range(1, 13), monthly_avg["avg_delay"], color=bar_colors, alpha=0.6,
            edgecolor="#bbbbbb", linewidth=0.5)
    ax1.axhline(avg, **mean_kw(f"Ø {avg:.1f}s"))
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(month_names, fontsize=9)
    ax1.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax1.set_title("Avg. Delay by Month (2023–2025)", **TITLE_KW)
    ax1.legend(**LEGEND_KW_RIGHT)
    style_ax(ax1)

    if panel != "left":
        for yr in [2023, 2024, 2025]:
            color = YEAR_COLORS.get(str(yr), BAR_NEUTRAL)
            df = monthly_by_year[monthly_by_year["year"] == yr].sort_values("month")
            ax2.plot(df["month"], df["avg_delay"], color=color, lw=1.0,
                     marker="o", markersize=5, label=str(yr))
        ax2.set_xticks(range(1, 13))
        ax2.set_xticklabels(month_names, fontsize=9)
        ax2.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
        ax2.set_title("Year Comparison — same month (cleaned)", **TITLE_KW)
        ax2.legend(**LEGEND_KW_RIGHT)
        style_ax(ax2)

    if ylim is not None:
        ax1.set_ylim(*ylim)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_month_seasonality(lf) -> pd.DataFrame:
    """Tabelle: Monatsmittelwerte + Jahresvergleich (pivot)."""
    monthly_avg = (
        lf
        .group_by("month")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort("month")
        .collect()
        .to_pandas()
    )
    monthly_by_year = (
        lf
        .with_columns(pl.col("operating_date").dt.year().alias("year"))
        .filter(~((pl.col("year") == 2025) & (pl.col("operating_date").dt.month() >= 11)))
        .group_by(["year", "month"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort(["month", "year"])
        .collect()
        .to_pandas()
    )
    month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    monthly_pivot = monthly_by_year.pivot(index="month", columns="year", values="avg_delay").round(1).reset_index()
    monthly_pivot.insert(0, "Month", [month_names[m - 1] for m in monthly_pivot["month"]])
    monthly_pivot = monthly_pivot.drop(columns=["month"])
    monthly_pivot["Ø gesamt"] = monthly_avg["avg_delay"].round(1).values
    return monthly_pivot.set_index("Month")


@auto_export("temporal-season-heatmap")
def plot_season_heatmap(lf, cfg=None, ylim_season=None, save_as=None):
    """Saisonaler Delay + OTP + Stunde × Wochentag Heatmap."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    season_names = {1: "Winter", 2: "Spring", 3: "Summer", 4: "Autumn"}

    seasonal = (
        lf
        .group_by("season")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("season")
        .collect()
        .to_pandas()
    )
    seasonal["season_name"] = seasonal["season"].map(season_names)

    heatmap_data = (
        lf
        .group_by(["hour", "weekday"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .collect()
        .to_pandas()
        .pivot(index="hour", columns="weekday", values="avg_delay")
        .sort_index()
    )
    day_labels = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    style = mpl_style()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    avg = seasonal["avg_delay"].mean()
    sc = [SEASON_COLORS.get(name, BAR_NEUTRAL) for name in seasonal["season_name"]]
    ax1.bar(seasonal["season_name"], seasonal["avg_delay"], color=sc, alpha=0.85)
    ax1b = ax1.twinx()
    ax1b.plot(seasonal["season_name"], seasonal["otp_rate"],
              color=OTP_ON_TIME, lw=1.0, marker="o", linestyle="--", label="OTP")
    ax1b.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax1b.set_ylabel("OTP Rate", color=OTP_ON_TIME)
    ax1b.tick_params(axis="y", colors=OTP_ON_TIME)
    ax1b.spines["right"].set_color(OTP_ON_TIME)
    ax1.axhline(avg, **mean_kw(f"Ø {avg:.1f}s"))
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax1b.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, **LEGEND_KW_RIGHT)
    ax1.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax1.set_title("Delay + OTP by Season", **TITLE_KW)
    ax1.spines[["top", "right"]].set_visible(False)
    if ylim_season is not None:
        ax1.set_ylim(*ylim_season)

    flat_vals = heatmap_data.values.flatten()
    flat_vals = flat_vals[~np.isnan(flat_vals)]
    vmin_val = np.percentile(flat_vals, 5)
    vmax_val = np.percentile(flat_vals, 95)

    im = ax2.imshow(heatmap_data.values, aspect="auto", origin="upper",
                    cmap="RdYlGn_r", vmin=vmin_val, vmax=vmax_val)
    ax2.set_xticks(range(7))
    ax2.set_xticklabels(day_labels, fontsize=9)
    ax2.set_yticks(range(0, 24, 2))
    ax2.set_yticklabels([f"{h}h" for h in range(0, 24, 2)], fontsize=8)
    ax2.set_title("Heatmap: Hour × Day of Week", **TITLE_KW)
    ax2.set_ylabel("Hour", **style["label"])
    plt.colorbar(im, ax=ax2, label="Avg. Arrival Delay (s)", shrink=0.8)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_season(lf) -> pd.DataFrame:
    """Tabelle: Saisonvergleich Delay + OTP."""
    season_names = {1: "Winter", 2: "Spring", 3: "Summer", 4: "Autumn"}
    seasonal = (
        lf
        .group_by("season")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("season")
        .collect()
        .to_pandas()
    )
    seasonal["season_name"] = seasonal["season"].map(season_names)
    return (
        seasonal[["season", "avg_delay", "otp_rate", "n"]]
        .assign(Jahreszeit=seasonal["season"].map(season_names))
        .rename(columns={"avg_delay": "Avg. Delay (s)", "otp_rate": "OTP", "n": "N Halte"})
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Avg. Delay (s)": 1})
        [["Season", "Avg. Delay (s)", "OTP", "N Halte"]]
        .set_index("Season")
    )


@auto_export("temporal-full-year-trend")
def plot_full_year_trend(lf, cfg=None, ylim_delay=None, ylim_otp=None, save_as=None):
    """7-Tage Rolling Average — täglicher Delay + OTP mit Schulferien-Annotation."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    yearly = (
        lf
        .with_columns(pl.col("operating_date").dt.year().alias("year"))
        .filter(~((pl.col("year") == 2025) & (pl.col("operating_date").dt.month() >= 11)))
        .group_by("operating_date")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
        ])
        .sort("operating_date")
        .collect()
        .to_pandas()
    )
    yearly["date"] = pd.to_datetime(yearly["operating_date"])
    yearly["rolling"] = yearly["avg_delay"].rolling(7, center=True).mean()
    yearly["rolling_otp"] = yearly["otp_rate"].rolling(7, center=True).mean()

    style = mpl_style()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    _add_schulferien(ax1)
    ax1.plot(yearly["date"], yearly["avg_delay"], color=cfg.COLOR_NEUTRAL, lw=0.5, alpha=0.3)
    ax1.plot(yearly["date"], yearly["rolling"], color=DELAY_COLOR, lw=1.0, label="7-Day Avg.")
    ax1.axhline(yearly["avg_delay"].mean(), **mean_kw(f"Ø {yearly['avg_delay'].mean():.1f}s"))
    for year in [2024, 2025]:
        ax1.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=1, linestyle=":")
    ax1.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax1.set_title("Daily Delay + 7-Day Rolling Average (Jan 2023 – Oct 2025)", **TITLE_KW)
    ax1.legend(**LEGEND_KW_RIGHT)
    style_ax(ax1)
    if ylim_delay is not None:
        ax1.set_ylim(*ylim_delay)

    _add_schulferien(ax2)
    ax2.plot(yearly["date"], yearly["otp_rate"], color=cfg.COLOR_NEUTRAL, lw=0.5, alpha=0.3)
    ax2.plot(yearly["date"], yearly["rolling_otp"], color=OTP_ON_TIME, lw=1.0, label="OTP 7-Day Avg.")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    for year in [2024, 2025]:
        ax2.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=1, linestyle=":")
    ax2.set_ylabel("OTP Rate", **style["label"])
    ax2.legend(**LEGEND_KW_RIGHT)
    style_ax(ax2)
    if ylim_otp is not None:
        ax2.set_ylim(*ylim_otp)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_full_year_monthly(lf) -> pd.DataFrame:
    """Tabelle: Monatliche Zusammenfassung (Jahresdurchschnitte bereinigt)."""
    month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    yearly = (
        lf
        .with_columns(pl.col("operating_date").dt.year().alias("year"))
        .filter(~((pl.col("year") == 2025) & (pl.col("operating_date").dt.month() >= 11)))
        .group_by("operating_date")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort("operating_date")
        .collect()
        .to_pandas()
    )
    yearly["date"] = pd.to_datetime(yearly["operating_date"])
    yearly_monthly_avg = (
        yearly.assign(month=lambda df: df["date"].dt.month, year=lambda df: df["date"].dt.year)
        .groupby(["year", "month"], observed=True)["avg_delay"].mean().round(1)
        .unstack("year").reset_index()
    )
    yearly_monthly_avg.insert(0, "Month", [month_names[m - 1] for m in yearly_monthly_avg["month"]])
    return yearly_monthly_avg.drop(columns=["month"]).set_index("Month")


@auto_export("temporal-gtfs-year-comparison")
def plot_gtfs_year_comparison(lf_delay, cfg=None, ylim=None, save_as=None):
    """gtfs_year Feature: j23 vs. j24_j25 — netzweit + umgebaute Linien."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from datetime import date

    _schema = lf_delay.collect_schema()
    if "gtfs_year" in _schema:
        gtfs_col = pl.col("gtfs_year")
        print("gtfs_year aus Feature-File geladen")
    else:
        gtfs_col = (
            pl.when(pl.col("operating_date") < pl.lit(date(2024, 1, 1)))
              .then(pl.lit("j23"))
              .otherwise(pl.lit("j24_j25"))
        )
        print("⚠  gtfs_year nicht in Feature-File — wird inline berechnet (02_preparation noch nicht neu ausgeführt)")

    gtfs_compare = (
        lf_delay
        .with_columns(gtfs_col.alias("_gtfs_year"))
        .group_by("_gtfs_year")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
            pl.col("operating_date").min().alias("date_from"),
            pl.col("operating_date").max().alias("date_to"),
        ])
        .sort("_gtfs_year")
        .collect()
        .to_pandas()
    )

    restructured_lines = ["9", "11", "13"]
    gtfs_lines = (
        lf_delay
        .with_columns(gtfs_col.alias("_gtfs_year"))
        .filter(pl.col("line_name").cast(pl.Utf8).is_in(restructured_lines))
        .group_by(["_gtfs_year", "line_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .sort(["line_name", "_gtfs_year"])
        .collect()
        .to_pandas()
    )

    style = mpl_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    labels = list(gtfs_compare["_gtfs_year"])
    vals = list(gtfs_compare["avg_delay"])
    colors_gtfs = [YEAR_COLORS["2023"], YEAR_COLORS["2024"]]
    bars = ax1.bar(labels, vals, color=colors_gtfs[:len(labels)], alpha=0.85)
    for bar, v, row in zip(bars, vals, gtfs_compare.itertuples()):
        ax1.text(bar.get_x() + bar.get_width() / 2, v + 0.3,
                 f"{v:+.1f}s\nOTP {row.otp_rate:.1%}\n({row.n / 1e6:.1f}M Halte)",
                 ha="center", fontsize=9)
    if len(vals) == 2:
        delta = vals[1] - vals[0]
        ax1.set_title(f"gtfs_year — Netzweit\nDelta j24_j25 vs. j23: {delta:+.1f}s", **TITLE_KW)
    else:
        ax1.set_title("gtfs_year — Netzweit", **TITLE_KW)
    ax1.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax1.spines[["top", "right"]].set_visible(False)

    if len(gtfs_lines) > 0:
        pivot = gtfs_lines.pivot(index="line_name", columns="_gtfs_year", values="avg_delay")
        x = range(len(pivot))
        width = 0.35
        if "j23" in pivot.columns and "j24_j25" in pivot.columns:
            ax2.bar([xi - width / 2 for xi in x], pivot["j23"], width, label="j23", color=colors_gtfs[0], alpha=0.85)
            ax2.bar([xi + width / 2 for xi in x], pivot["j24_j25"], width, label="j24_j25", color=colors_gtfs[1], alpha=0.85)
        ax2.set_xticks(x)
        ax2.set_xticklabels([fmt_line_legend(str(l)) for l in pivot.index], fontsize=11)
        ax2.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
        ax2.set_title("Restructured Lines 9, 11, 13 — Before/After Comparison", **TITLE_KW)
        ax2.legend(**LEGEND_KW_RIGHT)
        ax2.spines[["top", "right"]].set_visible(False)
    else:
        ax2.text(0.5, 0.5, "No data for Lines 9, 11, 13", ha="center", va="center",
                 transform=ax2.transAxes, fontsize=12)

    if ylim is not None:
        ax1.set_ylim(*ylim)
        if len(gtfs_lines) > 0:
            ax2.set_ylim(*ylim)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()

    print("gtfs_year Vergleich:")
    for _, r in gtfs_compare.iterrows():
        print(f"  {r['_gtfs_year']}: Ø {r['avg_delay']:+.1f}s  OTP {r['otp_rate']:.1%}  ({r['n'] / 1e6:.1f}M Halte)  [{r['date_from']} – {r['date_to']}]")



def table_gtfs_year_comparison(lf_delay) -> pd.DataFrame:
    """Tabelle: gtfs_year Vergleich netzweit."""
    from datetime import date

    _schema = lf_delay.collect_schema()
    if "gtfs_year" in _schema:
        gtfs_col = pl.col("gtfs_year")
    else:
        gtfs_col = (
            pl.when(pl.col("operating_date") < pl.lit(date(2024, 1, 1)))
              .then(pl.lit("j23"))
              .otherwise(pl.lit("j24_j25"))
        )

    gtfs_compare = (
        lf_delay
        .with_columns(gtfs_col.alias("_gtfs_year"))
        .group_by("_gtfs_year")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
            pl.col("operating_date").min().alias("date_from"),
            pl.col("operating_date").max().alias("date_to"),
        ])
        .sort("_gtfs_year")
        .collect()
        .to_pandas()
    )
    return (
        gtfs_compare.rename(columns={
            "_gtfs_year": "GTFS-Epoche", "avg_delay": "Avg. Delay (s)", "med_delay": "Median (s)",
            "otp_rate": "OTP", "n": "N Halte", "date_from": "Von", "date_to": "Bis"
        })
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Avg. Delay (s)": 1, "Median (s)": 1})
        .set_index("GTFS-Epoche")
    )
