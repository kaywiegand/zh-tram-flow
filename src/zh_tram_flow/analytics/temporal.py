"""Analytics-Modul für 03_analysis_3-temporal.ipynb — Zeitliche Muster."""

import polars as pl
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
        lbl = "Schulferien ZH" if not labeled else None
        ax.axvspan(pd.Timestamp(s), pd.Timestamp(e), alpha=alpha, color=color, label=lbl, zorder=0)
        labeled = True


def plot_hour_of_day(lf, cfg=None, save_as=None):
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
    _teal = cfg.COLOR_POSITIVE
    threshold = hourly.loc[hourly["hour"] == 8, "avg_delay"].values[0]
    colors = [cfg.COLOR_NEGATIVE if v >= threshold else "#aaaaaa"
              for v in hourly["avg_delay"]]

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()

    pct_n = hourly["n"] / hourly["n"].sum() * 100
    ax2.plot(hourly["hour"], pct_n, color=_teal,
             lw=1.5, linestyle="--", zorder=1, label="Anteil Halt-Ereignisse (%)")
    ax2.set_ylabel("Anteil Halt-Ereignisse (%)", fontsize=11, color=_teal, labelpad=8)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax2.tick_params(axis="y", colors=_teal, labelsize=9)
    ax2.spines[["top", "left"]].set_visible(False)
    ax2.spines["right"].set_color(_teal)

    ax1.bar(hourly["hour"], hourly["avg_delay"], color=colors, alpha=0.6,
            width=0.9, zorder=2)
    ax1.axhline(avg, color=cfg.ANNO_MEAN, lw=1.0, linestyle=":",
                label=f"Ø {avg:.1f}s", zorder=3)
    ax1.set_xlabel("Stunde", **style["label"])
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Ø Verspätung nach Stunde des Tages", **style["title"])
    ax1.set_xticks(range(0, 24, 2))
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    ax1.tick_params(colors=cfg.CHART_AXIS_TEXT, labelsize=10)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               fontsize=9, frameon=False, loc="upper right", ncol=2)

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
        hourly.rename(columns={"hour": "Stunde", "avg_delay": "Ø Delay (s)", "med_delay": "Median (s)", "n": "N Halte"})
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Ø Delay (s)": 1, "Median (s)": 1})
        .set_index("Stunde")
    )


def plot_day_of_week(lf, cfg=None, save_as=None):
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
    _teal = cfg.COLOR_POSITIVE
    colors = [cfg.COLOR_NEGATIVE if v > 58.5 else "#aaaaaa"
              for v in daily["avg_delay"]]

    fig, ax = plt.subplots(figsize=(14, 5))
    x = range(len(day_labels))

    ax.bar(x, daily["avg_delay"], color=colors, alpha=0.6)
    ax.axhline(avg, color=cfg.ANNO_MEAN, lw=1.0, linestyle=":", label=f"Ø {avg:.1f}s")

    for i, v in enumerate(daily["avg_delay"]):
        ax.text(i, v + 0.3, f"{v:+.1f}s", ha="center", va="bottom", fontsize=9)

    ax2 = ax.twinx()
    ax2.plot(x, daily["otp_pct"], color=_teal, lw=1.5,
             marker="D", markersize=4, linestyle="--", alpha=0.7, label="OTP (%)")
    ax2.set_ylabel("OTP (%)", color=_teal, fontsize=10)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax2.tick_params(axis="y", labelcolor=_teal)
    ax2.spines[["top", "left"]].set_visible(False)
    ax2.spines["right"].set_color(_teal)

    ax.set_xticks(x)
    ax.set_xticklabels(day_labels, fontsize=11)
    ax.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax.set_title("Ø Verspätung + OTP nach Wochentag", **style["title"])
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2,
              fontsize=9, frameon=False, loc="upper right", ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
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
    daily_table.insert(0, "Wochentag", day_labels[:len(daily_table)])
    return (
        daily_table[["Wochentag", "avg_delay", "med_delay", "p95_delay", "n"]]
        .rename(columns={"avg_delay": "Ø Delay (s)", "med_delay": "Median (s)", "p95_delay": "P95 (s)", "n": "N Halte"})
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Ø Delay (s)": 1, "Median (s)": 1, "P95 (s)": 1})
        .set_index("Wochentag")
    )


def plot_month_seasonality(lf, cfg=None, panel: str = "both", save_as=None):
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
    bar_colors = [cfg.COLOR_NEGATIVE if v > avg else "#aaaaaa"
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
    ax1.axhline(avg, color=cfg.ANNO_MEAN, lw=1.0, linestyle=":", label=f"Ø {avg:.1f}s")
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(month_names, fontsize=9)
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Ø Verspätung nach Monat (2023–2025)", **style["title"])
    ax1.legend(fontsize=9, frameon=False, loc="upper right")
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    ax1.tick_params(colors=cfg.CHART_AXIS_TEXT, labelsize=9)

    if panel != "left":
        colors = cfg.palette_n(3)
        for (yr, color) in zip([2023, 2024, 2025], colors):
            df = monthly_by_year[monthly_by_year["year"] == yr].sort_values("month")
            ax2.plot(df["month"], df["avg_delay"], color=color, lw=2,
                     marker="o", markersize=5, label=str(yr))
        ax2.set_xticks(range(1, 13))
        ax2.set_xticklabels(month_names, fontsize=9)
        ax2.set_ylabel("Ø Arrival Delay (s)", **style["label"])
        ax2.set_title("Jahresvergleich — gleicher Monat (bereinigt)", **style["title"])
        ax2.legend(fontsize=9, frameon=False, loc="upper right")
        ax2.spines[["top", "right"]].set_visible(False)
        ax2.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

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
    monthly_pivot.insert(0, "Monat", [month_names[m - 1] for m in monthly_pivot["month"]])
    monthly_pivot = monthly_pivot.drop(columns=["month"])
    monthly_pivot["Ø gesamt"] = monthly_avg["avg_delay"].round(1).values
    return monthly_pivot.set_index("Monat")


def plot_season_heatmap(lf, cfg=None, save_as=None):
    """Saisonaler Delay + OTP + Stunde × Wochentag Heatmap."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    season_names = {1: "Winter", 2: "Frühling", 3: "Sommer", 4: "Herbst"}

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
    colors = cfg.palette_n(4)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    avg = seasonal["avg_delay"].mean()
    sc = [cfg.COLOR_NEGATIVE if v > avg * 1.1 else cfg.PALETTE_CATEGORICAL[4] for v in seasonal["avg_delay"]]
    ax1.bar(seasonal["season_name"], seasonal["avg_delay"], color=sc, alpha=0.85)
    ax1b = ax1.twinx()
    ax1b.plot(seasonal["season_name"], seasonal["otp_rate"], color=cfg.ANNO_MEAN, lw=2, marker="o", label="OTP")
    ax1b.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax1b.set_ylabel("OTP Rate", color=cfg.ANNO_MEAN)
    ax1.axhline(avg, color=cfg.ANNO_REF, lw=1, linestyle="--")
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Verspätung + OTP nach Jahreszeit", **style["title"])
    ax1.spines[["top", "right"]].set_visible(False)

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
    ax2.set_title("Heatmap: Stunde × Wochentag", **style["title"])
    ax2.set_ylabel("Stunde", **style["label"])
    plt.colorbar(im, ax=ax2, label="Ø Arrival Delay (s)", shrink=0.8)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_season(lf) -> pd.DataFrame:
    """Tabelle: Saisonvergleich Delay + OTP."""
    season_names = {1: "Winter", 2: "Frühling", 3: "Sommer", 4: "Herbst"}
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
        .rename(columns={"avg_delay": "Ø Delay (s)", "otp_rate": "OTP", "n": "N Halte"})
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Ø Delay (s)": 1})
        [["Jahreszeit", "Ø Delay (s)", "OTP", "N Halte"]]
        .set_index("Jahreszeit")
    )


def plot_full_year_trend(lf, cfg=None):
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
    colors = cfg.palette_n(2)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    _add_schulferien(ax1)
    ax1.plot(yearly["date"], yearly["avg_delay"], color=cfg.COLOR_NEUTRAL, lw=0.5, alpha=0.3)
    ax1.plot(yearly["date"], yearly["rolling"], color=colors[0], lw=2, label="7-Tage Ø")
    ax1.axhline(yearly["avg_delay"].mean(), color=cfg.ANNO_REF, lw=1, linestyle=":",
                label=f"Ø {yearly['avg_delay'].mean():.1f}s")
    for year in [2024, 2025]:
        ax1.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=1, linestyle=":")
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Tägliche Verspätung + 7-Tage Rolling Average (Jan 2023 – Okt 2025)", **style["title"])
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    _add_schulferien(ax2)
    ax2.plot(yearly["date"], yearly["otp_rate"], color=cfg.COLOR_NEUTRAL, lw=0.5, alpha=0.3)
    ax2.plot(yearly["date"], yearly["rolling_otp"], color=colors[1], lw=2, label="OTP 7-Tage Ø")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    for year in [2024, 2025]:
        ax2.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=1, linestyle=":")
    ax2.set_ylabel("OTP Rate", **style["label"])
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
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
    yearly_monthly_avg.insert(0, "Monat", [month_names[m - 1] for m in yearly_monthly_avg["month"]])
    return yearly_monthly_avg.drop(columns=["month"]).set_index("Monat")


def plot_gtfs_year_comparison(lf_delay, cfg=None):
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
    colors_gtfs = [cfg.PALETTE_CATEGORICAL[0], cfg.PALETTE_CATEGORICAL[1]]
    bars = ax1.bar(labels, vals, color=colors_gtfs[:len(labels)], alpha=0.85)
    for bar, v, row in zip(bars, vals, gtfs_compare.itertuples()):
        ax1.text(bar.get_x() + bar.get_width() / 2, v + 0.3,
                 f"{v:+.1f}s\nOTP {row.otp_rate:.1%}\n({row.n / 1e6:.1f}M Halte)",
                 ha="center", fontsize=9)
    if len(vals) == 2:
        delta = vals[1] - vals[0]
        ax1.set_title(f"gtfs_year — Netzweit\nDelta j24_j25 vs. j23: {delta:+.1f}s", **style["title"])
    else:
        ax1.set_title("gtfs_year — Netzweit", **style["title"])
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.spines[["top", "right"]].set_visible(False)

    if len(gtfs_lines) > 0:
        pivot = gtfs_lines.pivot(index="line_name", columns="_gtfs_year", values="avg_delay")
        x = range(len(pivot))
        width = 0.35
        if "j23" in pivot.columns and "j24_j25" in pivot.columns:
            ax2.bar([xi - width / 2 for xi in x], pivot["j23"], width, label="j23", color=colors_gtfs[0], alpha=0.85)
            ax2.bar([xi + width / 2 for xi in x], pivot["j24_j25"], width, label="j24_j25", color=colors_gtfs[1], alpha=0.85)
        ax2.set_xticks(x)
        ax2.set_xticklabels([f"Linie {l}" for l in pivot.index], fontsize=11)
        ax2.set_ylabel("Ø Arrival Delay (s)", **style["label"])
        ax2.set_title("Umgebaute Linien 9, 11, 13\nj23 vs. j24_j25 (Vor/Nach-Vergleich)", **style["title"])
        ax2.legend(fontsize=9)
        ax2.spines[["top", "right"]].set_visible(False)
    else:
        ax2.text(0.5, 0.5, "Keine Daten für Linien 9, 11, 13", ha="center", va="center",
                 transform=ax2.transAxes, fontsize=12)

    plt.tight_layout()
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
            "_gtfs_year": "GTFS-Epoche", "avg_delay": "Ø Delay (s)", "med_delay": "Median (s)",
            "otp_rate": "OTP", "n": "N Halte", "date_from": "Von", "date_to": "Bis"
        })
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Ø Delay (s)": 1, "Median (s)": 1})
        .set_index("GTFS-Epoche")
    )
