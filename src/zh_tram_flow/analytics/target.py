"""Analytics-Modul für 03_analysis_1-target.ipynb — Zielvariable arrival_delay."""

import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def _get_cfg(cfg):
    if cfg is None:
        from wgnd.core.config import cfg as _default_cfg
        cfg = _default_cfg
    return cfg


def _compute_delay_stats_year(lf):
    """Gemeinsame Aggregation: Ø Delay nach Jahr."""
    return (
        lf
        .with_columns(pl.col("operating_date").dt.year().alias("year"))
        .group_by("year")
        .agg([
            pl.len().alias("n_stops"),
            pl.col("arrival_delay").mean().alias("arr_mean"),
            pl.col("arrival_delay").median().alias("arr_median"),
            pl.col("departure_delay").mean().alias("dep_mean"),
            pl.col("departure_delay").median().alias("dep_median"),
            pl.col("delay_delta").mean().alias("delta_mean"),
            pl.col("delay_delta").median().alias("delta_median"),
        ])
        .sort("year")
        .collect()
        .to_pandas()
    )


def _draw_year_bars(ax, stats, cfg, style, with_trend=False):
    """Zeichnet Balken + optionale Trendlinien auf ax."""
    years  = stats["year"].astype(int).tolist()
    x_pos  = np.arange(len(years))
    width  = 0.25
    colors = cfg.palette_n(3)
    for i, (col, label, color) in enumerate(zip(
        ["arr_mean", "dep_mean", "delta_mean"],
        ["Arrival Delay", "Departure Delay", "Delay Delta"],
        colors,
    )):
        vals  = stats[col].tolist()
        bar_x = x_pos + i * width
        bars  = ax.bar(bar_x, vals, width, label=label, color=color, alpha=0.85)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    v + (0.4 if v >= 0 else -2.0),
                    f"{v:+.1f}s", ha="center", va="bottom", fontsize=9)
        if with_trend and len(vals) > 1:
            ax.plot(bar_x, vals, color=color, lw=2, linestyle="--",
                    marker="o", markersize=5, alpha=0.9, zorder=5)
    ax.axhline(0, color=cfg.ANNO_REF, lw=1, linestyle=":")
    ax.set_xticks(x_pos + width)
    ax.set_xticklabels([str(y) for y in years], fontsize=11)
    ax.set_ylabel("Sekunden", **style["label"])
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)


def plot_delay_overview_per_year(lf_all, lf_clean=None, cfg=None):
    """Ø Verspätung nach Jahr. lf_clean=None → nur roh; lf_clean übergeben → Vergleich roh vs. bereinigt."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    style      = mpl_style()
    stats_all  = _compute_delay_stats_year(lf_all)

    if lf_clean is None:
        fig, ax = plt.subplots(figsize=(10, 4))
        _draw_year_bars(ax, stats_all, cfg, style)
        ax.set_title("Ø Verspätung pro Halt — nach Jahr (roh)", **style["title"])
    else:
        stats_clean = _compute_delay_stats_year(lf_clean)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 5))
        _draw_year_bars(ax1, stats_all,   cfg, style)
        _draw_year_bars(ax2, stats_clean, cfg, style, with_trend=True)
        ax1.set_title("Roh (lf_all)",          **style["title"])
        ax2.set_title("Bereinigt (lf_clean) + Trendlinie", **style["title"])
        # Print stats for clean
        arr_vals   = stats_clean["arr_mean"].tolist()
        delta_vals = stats_clean["delta_mean"].tolist()
        years_c    = stats_clean["year"].astype(int).tolist()
        print("Bereinigte Jahreswerte (Ø arrival_delay):")
        for yr, v in zip(years_c, arr_vals):
            print(f"  {yr}: {v:+.1f}s")
        if len(arr_vals) >= 2:
            print(f"  Δ {years_c[0]}→{years_c[-1]}: {arr_vals[-1] - arr_vals[0]:+.1f}s")

    plt.tight_layout()
    plt.show()


def table_delay_overview_per_year(lf):
    """Tabelle: Ø Verspätung nach Jahr. Nimmt lf_all oder lf_clean."""
    stats = _compute_delay_stats_year(lf)
    out   = stats.copy()
    out["n_stops"] = out["n_stops"].apply(lambda x: f"{x:,.0f}")
    for col in ["arr_mean", "arr_median", "dep_mean", "dep_median", "delta_mean", "delta_median"]:
        out[col] = out[col].apply(lambda x: f"{x:+.1f}s")
    out.columns = ["Jahr", "N Halte",
                   "Arr Ø", "Arr Median", "Dep Ø", "Dep Median", "Δ Ø", "Δ Median"]
    return out.set_index("Jahr")


def _compute_monthly(lf):
    """Gemeinsame Aggregation: Ø Delay nach Monat/Jahr."""
    df = (
        lf
        .with_columns([
            pl.col("operating_date").dt.year().alias("year"),
            pl.col("operating_date").dt.month().alias("month"),
        ])
        .group_by(["year", "month"])
        .agg([
            pl.col("arrival_delay").mean().alias("arr_mean"),
            pl.col("departure_delay").mean().alias("dep_mean"),
            pl.col("delay_delta").mean().alias("delta_mean"),
        ])
        .sort(["year", "month"])
        .collect()
        .to_pandas()
    )
    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    return df.sort_values("date").reset_index(drop=True)


def plot_monthly_delay(lf_all, lf_clean=None, cfg=None):
    """Monatliche Delay-Zeitreihe. lf_clean=None → nur roh; lf_clean übergeben → bereinigt mit Trendlinien."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    style   = mpl_style()
    colors  = cfg.palette_n(3)
    metrics = [
        ("arr_mean",   "Arrival Delay",   colors[0]),
        ("dep_mean",   "Departure Delay", colors[1]),
        ("delta_mean", "Delay Delta",     colors[2]),
    ]

    def _draw_monthly(ax, df, title, with_trend=False):
        x = np.arange(len(df))
        for col, label, color in metrics:
            y = df[col].values
            ax.plot(df["date"], y, color=color, lw=2, marker="o", markersize=3, label=label)
            if with_trend and len(y) > 1:
                coeffs = np.polyfit(x, y, 1)
                ax.plot(df["date"], np.polyval(coeffs, x),
                        color=color, lw=1.5, linestyle="--", alpha=0.6)
        ax.axhline(0, color=cfg.ANNO_REF, lw=1, linestyle=":")
        for year in [2024, 2025]:
            ax.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=1, linestyle=":")
        ax.set_ylabel("Ø Sekunden", **style["label"])
        ax.set_title(title, **style["title"])
        ax.legend(fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

    if lf_clean is None:
        df_all = _compute_monthly(lf_all)
        fig, ax = plt.subplots(figsize=(14, 5))
        _draw_monthly(ax, df_all, "Monthly Delay — Roh (alle Monate)")
    else:
        df_all   = _compute_monthly(lf_all)
        df_clean = _compute_monthly(lf_clean)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 5), sharey=True)
        _draw_monthly(ax1, df_all,   "Roh (lf_all)")
        _draw_monthly(ax2, df_clean, "Bereinigt (lf_clean) + Trendlinie", with_trend=True)

    plt.tight_layout()
    plt.show()


def table_monthly_delay(lf):
    """Tabelle: Jahresübersicht monatlicher Delay-Mittelwerte. Nimmt lf_all oder lf_clean."""
    df = _compute_monthly(lf)
    yr = df.groupby("year", observed=True)[["arr_mean", "dep_mean", "delta_mean"]].mean().round(1).reset_index()
    yr.columns = ["Jahr", "Ø Arr Delay (s)", "Ø Dep Delay (s)", "Ø Δ (s)"]
    return yr.set_index("Jahr")


def plot_delay_distribution(lf, cfg=None):
    """Delay-Verteilungs-Histogramme: Arrival / Departure / Delta (100k Sample)."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    sample_small = (lf.select(["arrival_delay", "departure_delay", "delay_delta"])
                    .collect().sample(n=min(100_000, lf.select(pl.len()).collect().item()), seed=42))

    style = mpl_style()
    delay_cols = ["arrival_delay", "departure_delay", "delay_delta"]
    titles = ["Arrival Delay", "Departure Delay", "Delay Delta"]
    colors = cfg.palette_n(3)
    CLIP = (-300, 600)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    for ax, col, title, color in zip(axes, delay_cols, titles, colors):
        data = sample_small[col].clip(CLIP[0], CLIP[1]).to_numpy()
        mean_val = float(sample_small[col].mean())
        median_val = float(sample_small[col].median())

        ax.hist(data, bins=80, color=color, alpha=0.85, edgecolor="none")
        ax.axvline(mean_val, color=cfg.ANNO_MEAN, lw=1.5, label=f"Ø {mean_val:.0f}s")
        ax.axvline(median_val, color=cfg.ANNO_MEDIAN, lw=1.5, linestyle="--", label=f"Median {median_val:.0f}s")
        ax.set_title(title, **style["title"])
        ax.set_xlabel("Seconds", **style["label"])
        ax.set_ylabel("Count", **style["label"])
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
        ax.legend(fontsize=9)

    plt.suptitle("Distribution — Sample 100k · clipped −300 to +600s", fontsize=11, color=cfg.CHART_TITLE, y=1.01)
    plt.tight_layout()
    plt.show()


def table_delay_stats(lf):
    """Tabelle: Grundstatistiken aller drei Delay-Spalten (Full Scan)."""
    delay_cols = ["arrival_delay", "departure_delay", "delay_delta"]
    rows = []
    for col in delay_cols:
        r = (
            lf.select([
                pl.col(col).min().alias("min"),
                pl.col(col).mean().alias("mean"),
                pl.col(col).median().alias("median"),
                pl.col(col).std().alias("std"),
                pl.col(col).max().alias("max"),
            ])
            .collect()
            .to_pandas()
            .assign(column=col)
        )
        rows.append(r)
    return pd.concat(rows).set_index("column").round(1)


def plot_delay_distribution_comparison(lf_all, lf_clean=None, cfg=None):
    """Verteilungsvergleich: lf_all (roh) vs. lf_clean (bereinigt) — 6 Histogramme."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    if lf_clean is None:
        _schema = lf_all.collect_schema()
        _has_stop_seq = "stop_sequence" in _schema
        lf_clean = (
            lf_all
            .filter(pl.col("canceled") == False)
            .filter(~(
                (pl.col("operating_date").dt.year() == 2025) &
                (pl.col("operating_date").dt.month() >= 11)
            ))
            .filter(pl.col("line_name") != "E")
        )
        if _has_stop_seq:
            lf_clean = lf_clean.filter(pl.col("stop_sequence") > 1)

    n_samp = 80_000
    n_all = lf_all.select(pl.len()).collect().item()
    n_cln = lf_clean.select(pl.len()).collect().item()
    df_all = (lf_all.select(["arrival_delay", "departure_delay", "delay_delta"])
              .collect().sample(n=min(n_samp, n_all), seed=42).to_pandas())
    df_clean = (lf_clean.select(["arrival_delay", "departure_delay", "delay_delta"])
                .collect().sample(n=min(n_samp, n_cln), seed=42).to_pandas())

    style = mpl_style()
    colors = cfg.palette_n(2)
    metrics = [
        ("arrival_delay",   "Arrival Delay",   (-200, 600)),
        ("departure_delay", "Departure Delay", (-200, 600)),
        ("delay_delta",     "Delay Delta",     (-150, 150)),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(18, 8), sharey=False)
    fig.suptitle("Delay Distribution — Roh vs. Bereinigt", fontsize=13, fontweight="bold", y=1.01)

    for col_i, (col, label, clip) in enumerate(metrics):
        data_all = df_all[col].clip(*clip)
        data_clean = df_clean[col].clip(*clip)
        bins = np.linspace(clip[0], clip[1], 80)

        for row_i, (data, dslabel, color) in enumerate([
            (data_all,   "lf_all (roh)",        colors[0]),
            (data_clean, "lf_clean (bereinigt)", colors[1]),
        ]):
            ax = axes[row_i][col_i]
            ax.hist(data, bins=bins, color=color, alpha=0.82, edgecolor="none", density=True)
            ax.axvline(data.mean(), color=cfg.ANNO_MEAN, lw=1.5, linestyle="--",
                       label=f"Ø {data.mean():+.1f}s")
            ax.axvline(data.median(), color=cfg.ANNO_REF, lw=1.5, linestyle=":",
                       label=f"Med {data.median():+.1f}s")
            ax.axvline(0, color=cfg.CHART_AXIS, lw=1, alpha=0.5)
            ax.set_title(f"{label}\n{dslabel}", **{**style["title"], "fontsize": 10})
            ax.set_xlabel("Sekunden", **style["label"])
            ax.set_ylabel("Dichte", **style["label"])
            ax.legend(fontsize=8)
            ax.spines[["top", "right"]].set_visible(False)

    for col, label in [("arrival_delay", "Arrival"), ("delay_delta", "Delta")]:
        m_all = df_all[col].mean()
        m_clean = df_clean[col].mean()
        print(f"{label:12s}: lf_all={m_all:+.1f}s  →  lf_clean={m_clean:+.1f}s  (Δ {m_clean - m_all:+.1f}s)")

    plt.tight_layout()
    plt.show()


def plot_log_transform(lf, cfg=None):
    """Log-Transform: Arrival Delay roh vs. Signed Log — mit Naive-Baseline MAE."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    sample_small = (lf.select(["arrival_delay"])
                    .collect().sample(n=min(100_000, lf.select(pl.len()).collect().item()), seed=42))
    arr = sample_small["arrival_delay"].to_numpy()
    arr_log = np.sign(arr) * np.log1p(np.abs(arr))

    style = mpl_style()
    colors = cfg.palette_n(2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))

    ax1.hist(np.clip(arr, -300, 600), bins=80, color=colors[0], alpha=0.85, edgecolor="none")
    ax1.axvline(np.mean(arr), color=cfg.ANNO_MEAN, lw=1.5, label=f"Ø {np.mean(arr):.0f}s")
    ax1.axvline(np.median(arr), color=cfg.ANNO_MEDIAN, lw=1.5, linestyle="--", label=f"Median {np.median(arr):.0f}s")
    ax1.set_title("Arrival Delay — Original (clipped)", **style["title"])
    ax1.set_xlabel("Seconds", **style["label"])
    ax1.set_ylabel("Count", **style["label"])
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

    ax2.hist(arr_log, bins=80, color=colors[1], alpha=0.85, edgecolor="none")
    ax2.axvline(np.mean(arr_log), color=cfg.ANNO_MEAN, lw=1.5, label=f"Ø {np.mean(arr_log):.2f}")
    ax2.axvline(np.median(arr_log), color=cfg.ANNO_MEDIAN, lw=1.5, linestyle="--", label=f"Median {np.median(arr_log):.2f}")
    ax2.set_title("Arrival Delay — Signed Log Transform", **style["title"])
    ax2.set_xlabel("sign(x) · log(|x| + 1)", **style["label"])
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

    plt.suptitle("Log-Transform komprimiert Extremwerte — Verteilung nähert sich Normalform",
                 fontsize=11, color=cfg.CHART_TITLE, y=1.01)
    plt.tight_layout()
    plt.show()

    mean_pred = np.mean(arr)
    median_pred = np.median(arr)
    mae_mean = np.mean(np.abs(arr - mean_pred))
    mae_median = np.mean(np.abs(arr - median_pred))
    print(f"Naive Baseline — Vorhersage = Mittelwert:  MAE = {mae_mean:.1f}s")
    print(f"Naive Baseline — Vorhersage = Median:      MAE = {mae_median:.1f}s  (robuster gegenüber Ausreißern)")
    print(f"Differenz: {mae_mean - mae_median:+.1f}s  →  Median reduziert MAE um {(1 - mae_median / mae_mean) * 100:.1f}%")



def plot_arrival_vs_departure(lf, cfg=None):
    """Boxplot: Arrival / Departure / Delay Delta nebeneinander (100k Sample)."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    sample_small = (lf.select(["arrival_delay", "departure_delay", "delay_delta"])
                    .collect().sample(n=min(100_000, lf.select(pl.len()).collect().item()), seed=42))

    style = mpl_style()
    colors = cfg.palette_n(3)
    labels = ["Arrival\nDelay", "Departure\nDelay", "Delay\nDelta"]

    df_box = sample_small[["arrival_delay", "departure_delay", "delay_delta"]].to_pandas().clip(-300, 600)

    fig, ax = plt.subplots(figsize=(10, 5))
    bp = ax.boxplot(
        [df_box[col] for col in ["arrival_delay", "departure_delay", "delay_delta"]],
        labels=labels,
        patch_artist=True,
        medianprops=dict(color=cfg.ANNO_MEDIAN, linewidth=2),
        whiskerprops=dict(color=cfg.CHART_AXIS),
        capprops=dict(color=cfg.CHART_AXIS),
        flierprops=dict(marker=".", markersize=1, alpha=0.15, color=cfg.COLOR_NEUTRAL),
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)

    ax.axhline(0, color=cfg.ANNO_REF, lw=1.2, linestyle="--", label="0s (on time)")
    ax.set_ylabel("Seconds", **style["label"])
    ax.set_title("Distribution — Sample 100k · clipped −300 to +600s", **style["title"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.show()

    means = lf.select([
        pl.col("arrival_delay").mean().alias("arr_mean"),
        pl.col("departure_delay").mean().alias("dep_mean"),
        pl.col("delay_delta").mean().alias("delta_mean"),
    ]).collect()
    print(f"Ø Arrival Delay:   {means['arr_mean'][0]:+.1f}s")
    print(f"Ø Departure Delay: {means['dep_mean'][0]:+.1f}s")
    print(f"Ø Delay Delta:     {means['delta_mean'][0]:+.1f}s  (positiv = Verspätung wächst am Halt)")



def plot_delay_delta_detail(lf, cfg=None):
    """Delay-Delta Verteilung im engen Bereich (±100s) — bimodale Struktur sichtbar."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    sample_small = (lf.select(["delay_delta"])
                    .collect().sample(n=min(100_000, lf.select(pl.len()).collect().item()), seed=42))

    style = mpl_style()
    data_delta = sample_small["delay_delta"].clip(-100, 100).to_numpy()
    mean_delta = float(sample_small["delay_delta"].mean())
    median_delta = float(sample_small["delay_delta"].median())

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.hist(data_delta, bins=120, color=cfg.PALETTE_CATEGORICAL[4], alpha=0.85, edgecolor="none")
    ax.axvline(0, color=cfg.ANNO_REF, lw=1.5, linestyle=":", label="0s (neutral)")
    ax.axvline(mean_delta, color=cfg.ANNO_MEAN, lw=1.5, label=f"Ø {mean_delta:.0f}s")
    ax.axvline(median_delta, color=cfg.ANNO_MEDIAN, lw=1.5, linestyle="--", label=f"Median {median_delta:.0f}s")
    ax.set_xlabel("Seconds  (Δ = departure − arrival)", **style["label"])
    ax.set_ylabel("Count", **style["label"])
    ax.set_title("Delay Delta — Distribution Detail · clipped −100 to +100s", **style["title"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.show()


def plot_start_stop_analysis(lf_delay, cfg=None):
    """Starthalte-Verzerrung: stop_sequence==1 vs. Rest — 3 Panels."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    _schema = lf_delay.collect_schema()
    if "stop_sequence" not in _schema:
        print("⚠  stop_sequence nicht im Feature-Set — bitte 02_preparation neu ausführen")
        return None

    start_stats = (
        lf_delay
        .with_columns((pl.col("stop_sequence") == 1).alias("is_start"))
        .group_by("is_start")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_arr"),
            pl.col("arrival_delay").median().alias("med_arr"),
            pl.col("delay_delta").mean().alias("avg_delta"),
            pl.col("delay_delta").median().alias("med_delta"),
            (pl.col("delay_delta") < 0).mean().alias("pct_neg_delta"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp"),
            pl.len().alias("n"),
        ])
        .sort("is_start")
        .collect()
        .to_pandas()
    )

    _start_full = lf_delay.filter(pl.col("stop_sequence") == 1).select(["delay_delta", "arrival_delay"]).collect()
    _nonstart_full = lf_delay.filter(pl.col("stop_sequence") > 1).select(["delay_delta", "arrival_delay"]).collect()
    n_samp = 60_000
    df_s = _start_full.sample(n=min(n_samp, len(_start_full)), seed=42).to_pandas()
    df_ns = _nonstart_full.sample(n=min(n_samp, len(_nonstart_full)), seed=42).to_pandas()

    style = mpl_style()
    colors = cfg.palette_n(2)
    CLIP = (-300, 400)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    bins = np.linspace(CLIP[0], CLIP[1], 80)
    ax = axes[0]
    ax.hist(df_ns["delay_delta"].clip(*CLIP), bins=bins, density=True,
            alpha=0.55, color=colors[0], label="Normale Halte (stop_seq > 1)")
    ax.hist(df_s["delay_delta"].clip(*CLIP), bins=bins, density=True,
            alpha=0.65, color=cfg.COLOR_NEGATIVE, label="Starthalte (stop_seq == 1)")
    ax.axvline(0, color=cfg.ANNO_REF, lw=1.5, linestyle="--")
    ax.set_xlabel("delay_delta (s)", **style["label"])
    ax.set_ylabel("Dichte", **style["label"])
    ax.set_title("Verteilung delay_delta\nStart vs. Normale Halte", **style["title"])
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)

    ax2 = axes[1]
    labels = ["Starthalte\n(seq==1)", "Alle anderen\n(seq>1)"]
    row_s = start_stats[start_stats["is_start"] == True].iloc[0]
    row_ns = start_stats[start_stats["is_start"] == False].iloc[0]
    arr_vals = [row_s["avg_arr"], row_ns["avg_arr"]]
    delta_vals = [row_s["avg_delta"], row_ns["avg_delta"]]
    x = np.arange(2)
    w = 0.35
    b1 = ax2.bar(x - w / 2, arr_vals, w, label="Ø arrival_delay", color=colors[0], alpha=0.85)
    b2 = ax2.bar(x + w / 2, delta_vals, w, label="Ø delay_delta", color=colors[1], alpha=0.85)
    for b, v in zip(list(b1) + list(b2), arr_vals + delta_vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + (0.5 if v >= 0 else -2.5),
                 f"{v:+.1f}s", ha="center", va="bottom", fontsize=9)
    ax2.axhline(0, color=cfg.ANNO_REF, lw=1, linestyle=":")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=10)
    ax2.set_ylabel("Sekunden", **style["label"])
    ax2.set_title("Ø Delay-Werte\nStart vs. Normale Halte", **style["title"])
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

    ax3 = axes[2]
    pct_vals = [row_s["pct_neg_delta"] * 100, row_ns["pct_neg_delta"] * 100]
    bar_colors = [cfg.COLOR_NEGATIVE, colors[0]]
    bars = ax3.bar(labels, pct_vals, color=bar_colors, alpha=0.85)
    for b, v in zip(bars, pct_vals):
        ax3.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.1f}%",
                 ha="center", fontsize=11, fontweight="bold")
    ax3.set_ylabel("Anteil negativer delay_delta (%)", **style["label"])
    ax3.set_title("Anteil Frühankunft / Frühstart\n(delay_delta < 0)", **style["title"])
    ax3.set_ylim(0, 100)
    ax3.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()

    print(f"Δ arrival_delay Starthalte→Normal: {row_ns['avg_arr'] - row_s['avg_arr']:+.1f}s")
    print(f"→ Starthalte ERHÖHEN den Netz-Durchschnitt um diesen Wert wenn inkludiert")



def plot_otp(lf, cfg=None):
    """OTP-Überblick: Arrival / Departure + Delay-Delta-Anteile."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    otp = lf.select([
        (pl.col("arrival_delay").abs() <= 120).mean().alias("arr_on_time"),
        (pl.col("arrival_delay") > 120).mean().alias("arr_late"),
        (pl.col("arrival_delay") < -120).mean().alias("arr_early"),
        (pl.col("departure_delay").abs() <= 120).mean().alias("dep_on_time"),
        (pl.col("departure_delay") > 120).mean().alias("dep_late"),
        (pl.col("departure_delay") < -120).mean().alias("dep_early"),
        (pl.col("delay_delta") < 0).mean().alias("delta_recovering"),
        (pl.col("delay_delta") == 0).mean().alias("delta_neutral"),
        (pl.col("delay_delta") > 0).mean().alias("delta_growing"),
    ]).collect()

    style = mpl_style()
    x = np.arange(3)
    width = 0.35
    categories = ["On-Time\n(|delay| ≤ 120s)", "Late\n(> 120s)", "Early\n(< −120s)"]
    arr_vals = [otp["arr_on_time"][0], otp["arr_late"][0], otp["arr_early"][0]]
    dep_vals = [otp["dep_on_time"][0], otp["dep_late"][0], otp["dep_early"][0]]
    two_colors = cfg.palette_n(2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))

    b1 = ax1.bar(x - width / 2, arr_vals, width, label="Arrival", color=two_colors[0])
    b2 = ax1.bar(x + width / 2, dep_vals, width, label="Departure", color=two_colors[1])
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=10)
    ax1.set_ylabel("Anteil", **style["label"])
    ax1.set_title("Arrival vs Departure — OTP", **style["title"])
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax1.legend()
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    for bar in [*b1, *b2]:
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                 f"{bar.get_height():.1%}", ha="center", va="bottom", fontsize=9)

    delta_vals = [otp["delta_recovering"][0], otp["delta_neutral"][0], otp["delta_growing"][0]]
    delta_labels = ["Recovering\n(Δ < 0)", "Neutral\n(Δ = 0)", "Growing\n(Δ > 0)"]
    delta_colors = [cfg.COLOR_POSITIVE, cfg.COLOR_NEUTRAL, cfg.COLOR_NEGATIVE]
    b3 = ax2.bar(range(3), delta_vals, width=0.5, color=delta_colors)
    ax2.set_xticks(range(3))
    ax2.set_xticklabels(delta_labels, fontsize=10)
    ax2.set_title("Delay Delta — Recovering vs Growing", **style["title"])
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    for bar in b3:
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.003,
                 f"{bar.get_height():.1%}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.show()


def table_otp(lf):
    """Tabelle: OTP-Kennzahlen (Arrival / Departure / Delta)."""
    otp = lf.select([
        (pl.col("arrival_delay").abs() <= 120).mean().alias("arr_on_time"),
        (pl.col("arrival_delay") > 120).mean().alias("arr_late"),
        (pl.col("arrival_delay") < -120).mean().alias("arr_early"),
        (pl.col("departure_delay").abs() <= 120).mean().alias("dep_on_time"),
        (pl.col("departure_delay") > 120).mean().alias("dep_late"),
        (pl.col("departure_delay") < -120).mean().alias("dep_early"),
        (pl.col("delay_delta") < 0).mean().alias("delta_recovering"),
        (pl.col("delay_delta") == 0).mean().alias("delta_neutral"),
        (pl.col("delay_delta") > 0).mean().alias("delta_growing"),
    ]).collect()
    otp_display = pd.DataFrame([
        {"Kategorie": "Arrival",
         "On-Time (±120s)": f"{otp['arr_on_time'][0]:.1%}",
         "Late (>120s)": f"{otp['arr_late'][0]:.1%}",
         "Early (<−120s)": f"{otp['arr_early'][0]:.1%}"},
        {"Kategorie": "Departure",
         "On-Time (±120s)": f"{otp['dep_on_time'][0]:.1%}",
         "Late (>120s)": f"{otp['dep_late'][0]:.1%}",
         "Early (<−120s)": f"{otp['dep_early'][0]:.1%}"},
    ])
    return otp_display


def plot_otp_per_line(lf_all, cfg=None):
    """OTP je Linie — monatliche Zeitreihen aller Linien (mit Linienfarben)."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.config import line_color

    otp_monthly_line = (
        lf_all
        .filter(pl.col("canceled") == False)
        .with_columns([
            pl.col("operating_date").dt.year().alias("year"),
            pl.col("operating_date").dt.month().alias("month"),
        ])
        .group_by(["year", "month", "line_name"])
        .agg((pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"))
        .sort(["year", "month"])
        .collect()
        .to_pandas()
    )
    otp_monthly_line["date"] = pd.to_datetime(otp_monthly_line[["year", "month"]].assign(day=1))

    lines_all = sorted(otp_monthly_line["line_name"].astype(str).unique(),
                       key=lambda x: int(x) if x.isdigit() else 99)
    avg_otp = otp_monthly_line.groupby("date", observed=True)["otp_rate"].mean().reset_index()

    style = mpl_style()
    fig, ax = plt.subplots(figsize=(14, 5))

    for ln in lines_all:
        df = otp_monthly_line[otp_monthly_line["line_name"] == ln].sort_values("date")
        ax.plot(df["date"], df["otp_rate"],
                color=line_color(ln), lw=1.0, marker="o", markersize=2, label=f"L{ln}")

    ax.plot(avg_otp["date"], avg_otp["otp_rate"],
            color=cfg.ANNO_MEAN, lw=2.5, linestyle="--", alpha=0.9, label="Ø alle Linien")
    ax.axhline(0.85, color=cfg.ANNO_REF, lw=1, linestyle=":", label="85%-Ziel")

    for year in [2024, 2025]:
        ax.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=1, linestyle=":")

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_ylabel("OTP (|arr_delay| ≤ 120s)", **style["label"])
    ax.set_title("OTP per Linie — monatlich (alle Linien)", **style["title"])
    ax.legend(fontsize=7, loc="lower left", ncol=5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    plt.tight_layout()
    plt.show()


def table_otp_per_line(lf_all):
    """Tabelle: OTP pro Linie — Ø / Min / Max (aufsteigend = schlechteste zuerst)."""
    otp_monthly_line = (
        lf_all
        .filter(pl.col("canceled") == False)
        .with_columns([
            pl.col("operating_date").dt.year().alias("year"),
            pl.col("operating_date").dt.month().alias("month"),
        ])
        .group_by(["year", "month", "line_name"])
        .agg((pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"))
        .collect()
        .to_pandas()
    )
    line_otp = (
        otp_monthly_line.groupby("line_name", observed=True)["otp_rate"]
        .agg(["mean", "min", "max"])
        .reset_index()
        .sort_values("mean")
        .round(3)
    )
    line_otp.columns = ["Linie", "Ø OTP", "Min OTP", "Max OTP"]
    for col in ["Ø OTP", "Min OTP", "Max OTP"]:
        line_otp[col] = line_otp[col].apply(lambda x: f"{x:.1%}")
    return line_otp


def table_cancellations_by_line(lf):
    """Tabelle: Ausfallrate nach Linie (Top 15, absteigend)."""
    return (
        lf
        .group_by("line_name")
        .agg([
            pl.len().alias("total"),
            pl.col("canceled").sum().alias("canceled_count"),
        ])
        .with_columns((pl.col("canceled_count") / pl.col("total")).alias("cancel_rate"))
        .sort("cancel_rate", descending=True)
        .head(15)
        .collect()
        .to_pandas()
        .rename(columns={"line_name": "Linie", "total": "Gesamt",
                         "canceled_count": "Ausgefallen", "cancel_rate": "Ausfallrate"})
        .assign(Ausfallrate=lambda df: df["Ausfallrate"].apply(lambda x: f"{x:.1%}"))
        .assign(Gesamt=lambda df: df["Gesamt"].apply(lambda x: f"{x:,.0f}"))
        .set_index("Linie")
    )


def plot_cancellations_by_line(lf, cfg=None):
    """Cancellation Rate — Top 15 Linien als horizontaler Balken."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    cancel_by_line = (
        lf
        .group_by("line_name")
        .agg([
            pl.len().alias("total"),
            pl.col("canceled").sum().alias("canceled_count"),
        ])
        .with_columns((pl.col("canceled_count") / pl.col("total")).alias("cancel_rate"))
        .sort("cancel_rate", descending=True)
        .head(15)
        .collect()
        .to_pandas()
    )

    style    = mpl_style()
    avg_rate = cancel_by_line["cancel_rate"].mean()
    bar_colors = [cfg.COLOR_NEGATIVE if r > avg_rate * 1.5 else cfg.PALETTE_CATEGORICAL[4]
                  for r in cancel_by_line["cancel_rate"]]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.barh(cancel_by_line["line_name"].astype(str), cancel_by_line["cancel_rate"], color=bar_colors)
    ax.axvline(avg_rate, color=cfg.ANNO_MEAN, lw=1.5, linestyle="--", label=f"Ø {avg_rate:.1%}")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1%}"))
    ax.set_xlabel("Cancellation Rate", **style["label"])
    ax.set_title("Cancellation Rate — Top 15 Lines", **style["title"])
    ax.invert_yaxis()
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    plt.tight_layout()
    plt.show()


def plot_trip_level_validation(master_path, cfg=None):
    """Trip-Level Validierung: fully_canceled / mixed / fully_active — pre vs. post Juli 2024."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    trip_cancel = (
        pl.scan_parquet(master_path)
        .select(["operating_date", "trip_id", "canceled"])
        .group_by(["trip_id", "operating_date"])
        .agg([
            pl.len().alias("n_stops"),
            pl.col("canceled").sum().alias("n_canceled"),
            pl.col("canceled").mean().alias("cancel_share"),
        ])
        .with_columns([
            pl.when(pl.col("cancel_share") == 1.0).then(pl.lit("fully_canceled"))
              .when(pl.col("cancel_share") == 0.0).then(pl.lit("fully_active"))
              .otherwise(pl.lit("mixed"))
              .alias("trip_type"),
            (pl.col("operating_date") < pl.date(2024, 7, 1)).alias("is_pre_july_2024"),
        ])
        .collect()
    )

    summary = (
        trip_cancel
        .group_by(["is_pre_july_2024", "trip_type"])
        .agg(pl.len().alias("n_trips"))
        .sort(["is_pre_july_2024", "trip_type"])
        .with_columns(
            pl.when(pl.col("is_pre_july_2024"))
              .then(pl.lit("pre Jul 2024"))
              .otherwise(pl.lit("ab Jul 2024"))
              .alias("is_pre_july_2024")
        )
    )

    total      = len(trip_cancel)
    n_mixed    = trip_cancel.filter(pl.col("trip_type") == "mixed").height
    n_canceled = trip_cancel.filter(pl.col("trip_type") == "fully_canceled").height
    print(f"Gesamt Trips:             {total:>12,}")
    print(f"  fully_active:           {total - n_mixed - n_canceled:>12,}  ({(total - n_mixed - n_canceled)/total:.2%})")
    print(f"  fully_canceled:         {n_canceled:>12,}  ({n_canceled/total:.2%})")
    print(f"  mixed (Kurzwendungen?): {n_mixed:>12,}  ({n_mixed/total:.2%})")

    style  = mpl_style()
    colors = {
        "fully_active":   cfg.COLOR_POSITIVE,
        "mixed":          cfg.PALETTE_CATEGORICAL[5],
        "fully_canceled": cfg.COLOR_NEGATIVE,
    }
    periods = ["pre Jul 2024", "ab Jul 2024"]
    types   = ["fully_active", "mixed", "fully_canceled"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 4))
    for ax, normalize in zip(axes, [False, True]):
        bottoms = {p: 0 for p in periods}
        for t in types:
            vals = []
            for p in periods:
                flag  = (p == "pre Jul 2024")
                sub   = summary.filter(
                    (pl.col("is_pre_july_2024") == p) & (pl.col("trip_type") == t)
                )
                total_p = trip_cancel.filter(pl.col("is_pre_july_2024") == flag).height
                v = sub["n_trips"][0] if len(sub) > 0 else 0
                vals.append(v / total_p if normalize else v)
            bars = ax.bar(periods, vals, bottom=[bottoms[p] for p in periods],
                          label=t, color=colors[t], alpha=0.85)
            for bar, val in zip(bars, vals):
                if val > (0.01 if normalize else 500):
                    ax.text(bar.get_x() + bar.get_width()/2,
                            bar.get_y() + bar.get_height()/2,
                            f"{val:.1%}" if normalize else f"{val:,.0f}",
                            ha="center", va="center", fontsize=9,
                            color="white", fontweight="bold")
            for p, v in zip(periods, vals):
                bottoms[p] += v

        ax.set_title(f"{'Anteil' if normalize else 'Anzahl'} Trips nach Typ", **style["title"])
        if normalize:
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

    axes[0].legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    plt.show()

    return summary.to_pandas()


def plot_cancellation_rate_over_time(lf_all, cfg=None):
    """Monatliche Ausfallrate nach Linie — alle Linien als Zeitreihe."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.config import line_color

    cancel_monthly = (
        lf_all
        .with_columns([
            pl.col("operating_date").dt.year().alias("year"),
            pl.col("operating_date").dt.month().alias("month"),
        ])
        .group_by(["year", "month", "line_name"])
        .agg(pl.col("canceled").mean().alias("cancel_rate"))
        .sort(["year", "month"])
        .collect()
        .to_pandas()
    )
    cancel_monthly["date"] = pd.to_datetime(cancel_monthly[["year", "month"]].assign(day=1))

    lines_all = sorted(cancel_monthly["line_name"].astype(str).unique(),
                       key=lambda x: int(x) if x.isdigit() else 99)
    avg_all   = (cancel_monthly[~cancel_monthly["line_name"].isin(["99"])]
                 .groupby("date", observed=True)["cancel_rate"].mean().reset_index())

    style = mpl_style()
    fig, ax = plt.subplots(figsize=(14, 5))
    for ln in lines_all:
        df = cancel_monthly[cancel_monthly["line_name"] == ln].sort_values("date")
        ax.plot(df["date"], df["cancel_rate"],
                color=line_color(ln), lw=1.0, marker="o", markersize=2, label=f"Linie {ln}")

    ax.plot(avg_all["date"], avg_all["cancel_rate"],
            color=cfg.COLOR_NEUTRAL, lw=4.0, marker="o", markersize=4,
            label="Ø alle Linien", alpha=0.7)
    ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2024-06-30"),
               alpha=0.07, color=cfg.COLOR_NEGATIVE,
               label="Glattalbahn Baustelle (Jan 2023 – Jun 2024)")
    for year in [2024, 2025]:
        ax.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=1, linestyle=":")

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_ylabel("Ausfallrate", **style["label"])
    ax.set_title("Monthly Cancellation Rate vs. Ø alle Linien", **style["title"])
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    plt.tight_layout()
    plt.show()


def plot_delay_per_line_timeline(lf_all, cfg=None):
    """Ø Delay nach Linie — monatliche Zeitreihe für alle 3 Metriken."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.config import line_color

    delay_monthly_line = (
        lf_all
        .filter(pl.col("canceled") == False)
        .with_columns([
            pl.col("operating_date").dt.year().alias("year"),
            pl.col("operating_date").dt.month().alias("month"),
        ])
        .group_by(["year", "month", "line_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("arr_mean"),
            pl.col("departure_delay").mean().alias("dep_mean"),
            pl.col("delay_delta").mean().alias("delta_mean"),
        ])
        .sort(["year", "month"])
        .collect()
        .to_pandas()
    )
    delay_monthly_line["date"] = pd.to_datetime(
        delay_monthly_line[["year", "month"]].assign(day=1)
    )

    lines_all = sorted(delay_monthly_line["line_name"].astype(str).unique(),
                       key=lambda x: int(x) if x.isdigit() else 99)
    colors    = cfg.palette_n(3)
    metrics   = [
        ("arr_mean",   "Arrival Delay",   colors[0]),
        ("dep_mean",   "Departure Delay", colors[1]),
        ("delta_mean", "Delay Delta",     colors[2]),
    ]

    style = mpl_style()
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

    for ax, (col, label, color) in zip(axes, metrics):
        avg = delay_monthly_line.groupby("date", observed=True)[col].mean().reset_index()
        for ln in lines_all:
            df = delay_monthly_line[delay_monthly_line["line_name"] == ln].sort_values("date")
            ax.plot(df["date"], df[col],
                    color=line_color(ln), lw=1.0, marker="o", markersize=2, label=f"L{ln}")
        ax.plot(avg["date"], avg[col],
                color=cfg.ANNO_MEAN, lw=2.5, linestyle="--", alpha=0.9, label="Ø alle Linien")
        ax.axhline(0, color=cfg.ANNO_REF, lw=1, linestyle=":")
        for year in [2024, 2025]:
            ax.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=1, linestyle=":")
        ax.set_ylabel(f"Ø {label} (s)", **style["label"])
        ax.set_title(label, **style["title"])
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

    axes[0].legend(fontsize=7, loc="upper left", ncol=5)
    plt.suptitle("Delay per Linie — monatlich (alle Linien)",
                 fontsize=12, color=cfg.CHART_TITLE)
    plt.tight_layout()
    plt.show()


def table_delay_per_line_summary(lf_all):
    """Tabelle: Ø Delay pro Linie — Gesamtdurchschnitt (absteigende Arrival Delay)."""
    delay_monthly_line = (
        lf_all
        .filter(pl.col("canceled") == False)
        .with_columns([
            pl.col("operating_date").dt.year().alias("year"),
            pl.col("operating_date").dt.month().alias("month"),
        ])
        .group_by(["year", "month", "line_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("arr_mean"),
            pl.col("departure_delay").mean().alias("dep_mean"),
            pl.col("delay_delta").mean().alias("delta_mean"),
        ])
        .collect()
        .to_pandas()
    )
    result = (
        delay_monthly_line
        .groupby("line_name", observed=True)[["arr_mean", "dep_mean", "delta_mean"]]
        .mean()
        .reset_index()
        .sort_values("arr_mean", ascending=False)
        .round(1)
    )
    result.columns = ["Linie", "Ø Arr Delay (s)", "Ø Dep Delay (s)", "Ø Δ (s)"]
    return result.set_index("Linie")
