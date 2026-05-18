"""
Meteo analytics — weather impact on tram delays.

Functions:
  plot_weather_overview(lf, cfg=None)
  table_weather_overview(lf)
  plot_temperature_precipitation(lf, cfg=None)
  table_temperature_bins(lf)
  plot_is_hot(lf, cfg=None)
  table_is_hot(lf)
  plot_multicollinearity_matrix(lf, cfg=None)
  table_correlation_with_delay(lf)
"""

import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_cfg(cfg):
    if cfg is None:
        from zh_tram_flow.notebook import NotebookConfig
        cfg = NotebookConfig()
    return cfg


def _weather_compare(lf_delay: pl.LazyFrame, flag: str, label: str) -> pd.DataFrame:
    """Return avg_delay / otp_rate / n for True/False values of *flag*."""
    return (
        lf_delay
        .group_by(flag)
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort(flag)
        .collect()
        .to_pandas()
        .assign(condition=label)
    )


# ---------------------------------------------------------------------------
# Weather Overview
# ---------------------------------------------------------------------------

def plot_weather_overview(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
    """Bar chart: Normal vs. Wettereffekt for rain / heavy rain / snow."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    flags = [
        ("has_rain",       "Regen"),
        ("has_heavy_rain", "Starkregen"),
        ("has_snow",       "Schnee"),
    ]

    baseline_rows, effect_rows = [], []
    for flag, label in flags:
        df = _weather_compare(lf_delay, flag, label)
        base = df[df[flag] == False]["avg_delay"].values
        eff  = df[df[flag] == True]["avg_delay"].values
        if len(base) > 0 and len(eff) > 0:
            baseline_rows.append({"condition": label, "delay": base[0], "type": "Normal"})
            effect_rows.append({
                "condition":   label,
                "delay":       eff[0],
                "type":        "Wettereffekt",
                "delta":       eff[0] - base[0],
                "otp_normal":  df[df[flag] == False]["otp_rate"].values[0],
                "otp_weather": df[df[flag] == True]["otp_rate"].values[0],
                "n_weather":   df[df[flag] == True]["n"].values[0],
            })

    n         = len(baseline_rows)
    x_arr     = list(range(n))
    width     = 0.35
    cond_labels  = [r["condition"]  for r in baseline_rows]
    normal_vals  = [r["delay"]      for r in baseline_rows]
    weather_vals = [r["delay"]      for r in effect_rows]
    deltas       = [r["delta"]      for r in effect_rows]

    style  = mpl_style()
    colors = cfg.palette_n(2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    # Panel 1: Absoluter Delay-Vergleich
    ax1.bar([xi - width / 2 for xi in x_arr], normal_vals,  width,
            label="Normal", color=colors[0], alpha=0.85)
    b2 = ax1.bar([xi + width / 2 for xi in x_arr], weather_vals, width,
                 label="Wettereffekt", color=cfg.COLOR_NEGATIVE, alpha=0.85)
    for b, v in zip(b2, weather_vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:+.1f}s", ha="center", fontsize=8)
    ax1.set_xticks(x_arr)
    ax1.set_xticklabels(cond_labels, fontsize=10)
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Delay Normal vs. Wettereffekt", **style["title"])
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    # Panel 2: Delta (Mehrverspätung durch Wetter)
    delta_colors = [cfg.COLOR_NEGATIVE if d > 2 else cfg.PALETTE_CATEGORICAL[4] for d in deltas]
    ax2.bar(cond_labels, deltas, color=delta_colors, alpha=0.85)
    ax2.axhline(0, color=cfg.ANNO_REF, lw=1, linestyle=":")
    for i, v in enumerate(deltas):
        ax2.text(i, v + 0.2, f"+{v:.1f}s", ha="center", fontsize=9)
    ax2.set_ylabel("Mehrverspätung durch Wetter (s)", **style["label"])
    ax2.set_title("Wetter-Delta: Zusätzliche Verspätung", **style["title"])
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()

    # Print summary
    for r in effect_rows:
        print(f"{r['condition']:20s}: +{r['delta']:+.1f}s  "
              f"OTP {r['otp_normal']:.1%} → {r['otp_weather']:.1%}  "
              f"(n={r['n_weather']:,})")



def table_weather_overview(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return DataFrame with weather effect stats (delta, OTP, n)."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    flags = [
        ("has_rain",       "Regen"),
        ("has_heavy_rain", "Starkregen"),
        ("has_snow",       "Schnee"),
    ]

    effect_rows = []
    for flag, label in flags:
        df = _weather_compare(lf_delay, flag, label)
        base = df[df[flag] == False]["avg_delay"].values
        eff  = df[df[flag] == True]["avg_delay"].values
        if len(base) > 0 and len(eff) > 0:
            effect_rows.append({
                "condition":   label,
                "delta":       round(eff[0] - base[0], 1),
                "otp_normal":  f"{df[df[flag] == False]['otp_rate'].values[0]:.1%}",
                "otp_weather": f"{df[df[flag] == True]['otp_rate'].values[0]:.1%}",
                "n_weather":   f"{df[df[flag] == True]['n'].values[0]:,.0f}",
            })

    result = pd.DataFrame(effect_rows)
    result.columns = ["Wetterbedingung", "Δ Delay (s)", "OTP Normal", "OTP Wetter", "N (Wettertage)"]
    return result.set_index("Wetterbedingung")


# ---------------------------------------------------------------------------
# Temperature + Precipitation
# ---------------------------------------------------------------------------

def plot_temperature_precipitation(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
    """Bar charts: delay by temperature bin and precipitation intensity."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    temp_bins = (
        lf_delay
        .with_columns(
            (pl.col("temperature") / 5).floor().cast(pl.Int32).alias("temp_bin_5c")
        )
        .group_by("temp_bin_5c")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("temp_bin_5c")
        .collect()
        .to_pandas()
    )
    temp_bins = temp_bins[temp_bins["n"] >= 5000]
    temp_bins["temp_label"] = temp_bins["temp_bin_5c"].apply(lambda x: f"{x*5}–{x*5+5}°C")

    precip_bins = (
        lf_delay
        .filter(pl.col("has_rain") == True)
        .with_columns(
            pl.when(pl.col("precipitation") < 2).then(pl.lit("< 2mm"))
              .when(pl.col("precipitation") < 5).then(pl.lit("2–5mm"))
              .when(pl.col("precipitation") < 10).then(pl.lit("5–10mm"))
              .otherwise(pl.lit("> 10mm"))
              .alias("precip_bin")
        )
        .group_by("precip_bin")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .sort("avg_delay")
        .collect()
        .to_pandas()
    )

    precip_order = ["< 2mm", "2–5mm", "5–10mm", "> 10mm"]
    precip_plot  = precip_bins.set_index("precip_bin").reindex(precip_order).dropna().reset_index()

    style = mpl_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    # Temperature curve
    mean_delay = temp_bins["avg_delay"].mean()
    temp_colors = [
        cfg.COLOR_NEGATIVE if v > mean_delay * 1.1
        else cfg.COLOR_POSITIVE if v < mean_delay * 0.9
        else cfg.PALETTE_CATEGORICAL[4]
        for v in temp_bins["avg_delay"]
    ]
    ax1.bar(range(len(temp_bins)), temp_bins["avg_delay"], color=temp_colors, alpha=0.85)
    ax1.axhline(mean_delay, color=cfg.ANNO_MEAN, lw=1.5, linestyle="--", label="Ø")
    zero_mask = temp_bins[temp_bins["temp_bin_5c"] == 0]
    if len(zero_mask) > 0:
        ax1.axvline(zero_mask.index[0], color=cfg.CHART_AXIS, lw=1, linestyle=":", label="0°C")
    ax1.set_xticks(range(len(temp_bins)))
    ax1.set_xticklabels(temp_bins["temp_label"], rotation=45, fontsize=8)
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Verspätung nach Temperatur (5°C-Bins)", **style["title"])
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    # Precipitation intensity
    pc = [
        cfg.COLOR_NEGATIVE if v > precip_bins["avg_delay"].mean() * 1.1
        else cfg.PALETTE_CATEGORICAL[4]
        for v in precip_plot["avg_delay"]
    ]
    ax2.bar(precip_plot["precip_bin"], precip_plot["avg_delay"], color=pc, alpha=0.85)
    for i, (v, n) in enumerate(zip(precip_plot["avg_delay"], precip_plot["n"])):
        ax2.text(i, v + 0.3, f"{v:+.1f}s\n(n={n/1000:.0f}k)", ha="center", fontsize=8)
    ax2.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax2.set_title("Verspätung nach Niederschlagsintensität (Regentage)", **style["title"])
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()


def table_temperature_bins(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return delay stats per 5°C temperature bin."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    temp_bins = (
        lf_delay
        .with_columns(
            (pl.col("temperature") / 5).floor().cast(pl.Int32).alias("temp_bin_5c")
        )
        .group_by("temp_bin_5c")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("temp_bin_5c")
        .collect()
        .to_pandas()
    )
    temp_bins = temp_bins[temp_bins["n"] >= 5000].copy()
    temp_bins["temp_label"] = temp_bins["temp_bin_5c"].apply(lambda x: f"{x*5}–{x*5+5}°C")

    result = (
        temp_bins[["temp_label", "avg_delay", "otp_rate", "n"]]
        .rename(columns={
            "temp_label": "Temperatur",
            "avg_delay":  "Ø Delay (s)",
            "otp_rate":   "OTP",
            "n":          "N Halte",
        })
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
    )
    result["Ø Delay (s)"] = result["Ø Delay (s)"].round(1)
    return result.set_index("Temperatur")


# ---------------------------------------------------------------------------
# is_hot feature
# ---------------------------------------------------------------------------

def plot_is_hot(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
    """Bar + temperature curve validating the is_hot (>20°C) feature."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema = lf_delay.collect_schema()

    if "is_hot" in _schema:
        hot_col = pl.col("is_hot")
    else:
        hot_col = (pl.col("temperature") > 20)
        print("WARNING: is_hot not in feature file — calculated inline (re-run 02_preparation)")

    hot_compare = (
        lf_delay
        .with_columns(hot_col.alias("_is_hot"))
        .group_by("_is_hot")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("_is_hot")
        .collect()
        .to_pandas()
    )

    temp_bins_hot = (
        lf_delay
        .with_columns(
            (pl.col("temperature") / 5).floor().cast(pl.Int32).alias("temp_bin_5c")
        )
        .group_by("temp_bin_5c")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort("temp_bin_5c")
        .collect()
        .to_pandas()
    )
    temp_bins_hot = temp_bins_hot[temp_bins_hot["temp_bin_5c"].between(-4, 8)]

    vals, otps, ns = [], [], []
    for is_hot_val in [False, True]:
        row = hot_compare[hot_compare["_is_hot"] == is_hot_val]
        if len(row) > 0:
            vals.append(row["avg_delay"].values[0])
            otps.append(row["otp_rate"].values[0])
            ns.append(row["n"].values[0])
        else:
            vals.append(0); otps.append(0); ns.append(0)

    delta = vals[1] - vals[0] if len(vals) == 2 else 0
    labels_hot = ["Normal (≤20°C)", "Heiss (>20°C)"]
    colors_hot = [cfg.PALETTE_CATEGORICAL[4], cfg.COLOR_NEGATIVE]

    style = mpl_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Panel 1: Direktvergleich
    bars = ax1.bar(labels_hot, vals, color=colors_hot, alpha=0.85)
    for bar, v, n in zip(bars, vals, ns):
        ax1.text(bar.get_x() + bar.get_width() / 2, v + 0.3,
                 f"{v:+.1f}s\n(n={n/1e6:.1f}M)", ha="center", fontsize=9)
    ax1.set_title(f"is_hot — Delta: {delta:+.1f}s", **style["title"])
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.spines[["top", "right"]].set_visible(False)

    # Panel 2: Temperaturkurve mit 20°C-Schwelle
    bin_colors = [cfg.COLOR_NEGATIVE if tb >= 4 else cfg.PALETTE_CATEGORICAL[4]
                  for tb in temp_bins_hot["temp_bin_5c"]]
    ax2.bar(range(len(temp_bins_hot)), temp_bins_hot["avg_delay"], color=bin_colors, alpha=0.85)
    tb_list = list(temp_bins_hot["temp_bin_5c"])
    if 4 in tb_list:
        thresh_x = tb_list.index(4) - 0.5
        ax2.axvline(thresh_x, color=cfg.COLOR_NEGATIVE, lw=2, linestyle="--", label="20°C Schwelle")
    ax2.set_xticks(range(len(temp_bins_hot)))
    ax2.set_xticklabels([f"{b*5}°C" for b in temp_bins_hot["temp_bin_5c"]], rotation=45, fontsize=9)
    ax2.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax2.set_title("Temperaturkurve — 20°C Schwelle markiert", **style["title"])
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()

    print(f"Normal (≤20°C): Ø {vals[0]:+.1f}s  OTP {otps[0]:.1%}  (n={ns[0]/1e6:.1f}M)")
    print(f"Heiss  (>20°C): Ø {vals[1]:+.1f}s  OTP {otps[1]:.1%}  (n={ns[1]/1e6:.1f}M)")
    print(f"→ Delta is_hot: {delta:+.1f}s")



def table_is_hot(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return comparison table for is_hot feature."""
    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema = lf_delay.collect_schema()

    if "is_hot" in _schema:
        hot_col = pl.col("is_hot")
    else:
        hot_col = (pl.col("temperature") > 20)

    hot_compare = (
        lf_delay
        .with_columns(hot_col.alias("_is_hot"))
        .group_by("_is_hot")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("_is_hot")
        .collect()
        .to_pandas()
    )

    result = (
        hot_compare
        .rename(columns={
            "_is_hot":   "is_hot",
            "avg_delay": "Ø Delay (s)",
            "med_delay": "Median (s)",
            "otp_rate":  "OTP",
            "n":         "N Halte",
        })
        .assign(is_hot=lambda df: df["is_hot"].map(
            {False: "Normal (≤20°C)", True: "Heiss (>20°C)"}))
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
    )
    result["Ø Delay (s)"] = result["Ø Delay (s)"].round(1)
    result["Median (s)"]  = result["Median (s)"].round(1)
    return result.set_index("is_hot")


# ---------------------------------------------------------------------------
# Multicollinearity / correlation matrix
# ---------------------------------------------------------------------------

def plot_multicollinearity_matrix(lf: pl.LazyFrame, cfg=None) -> plt.Figure:
    """Heatmap of Pearson correlations: weather × season × delay."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    corr_cols = [
        "arrival_delay", "has_rain", "has_heavy_rain", "is_windy", "has_snow",
        "temperature", "precipitation", "month", "season",
    ]
    available = [c for c in corr_cols if c in _schema]

    corr_df = (
        lf_delay
        .select([pl.col(c) for c in available])
        .collect()
        .to_pandas()
    )
    corr_matrix = corr_df[available].astype(float).corr()

    style = mpl_style()
    fig, ax = plt.subplots(figsize=(10, 8))

    im = ax.imshow(corr_matrix.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, label="Pearson Korrelation", shrink=0.8)

    ax.set_xticks(range(len(available)))
    ax.set_yticks(range(len(available)))
    ax.set_xticklabels(available, rotation=45, ha="right", fontsize=10)
    ax.set_yticklabels(available, fontsize=10)

    for i in range(len(available)):
        for j in range(len(available)):
            val   = corr_matrix.iloc[i, j]
            color = "white" if abs(val) > 0.5 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8, color=color)

    ax.set_title("Korrelationsmatrix — Wetter × Saison × Delay", **style["title"])
    plt.tight_layout()
    plt.show()

    # Print sorted correlations with delay
    print("Korrelation mit arrival_delay (abs. sortiert):")
    delay_corr = corr_matrix["arrival_delay"].drop("arrival_delay").abs().sort_values(ascending=False)
    for feat, val in delay_corr.items():
        raw = corr_matrix["arrival_delay"][feat]
        print(f"  {feat:25s}: {raw:+.3f}  (abs: {val:.3f})")

    print("\nWetter-Flags × Saison-Korrelation:")
    for wf in ["has_rain", "has_heavy_rain", "is_windy", "has_snow"]:
        if wf in corr_matrix.columns and "season" in corr_matrix.columns:
            print(f"  {wf:20s} × season: {corr_matrix.loc[wf, 'season']:+.3f}")



def table_correlation_with_delay(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return sorted Pearson correlations of all features with arrival_delay."""
    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    corr_cols = [
        "arrival_delay", "has_rain", "has_heavy_rain", "is_windy", "has_snow",
        "temperature", "precipitation", "month", "season",
    ]
    available = [c for c in corr_cols if c in _schema]

    corr_df = (
        lf_delay
        .select([pl.col(c) for c in available])
        .collect()
        .to_pandas()
    )
    corr_matrix = corr_df[available].astype(float).corr()

    result = (
        corr_matrix["arrival_delay"]
        .drop("arrival_delay")
        .reset_index()
        .rename(columns={"index": "Feature", "arrival_delay": "Korrelation"})
        .assign(abs_corr=lambda df: df["Korrelation"].abs())
        .sort_values("abs_corr", ascending=False)
        .round({"Korrelation": 3, "abs_corr": 3})
    )
    result.columns = ["Feature", "Korrelation mit delay", "|Korrelation|"]
    return result.set_index("Feature")
