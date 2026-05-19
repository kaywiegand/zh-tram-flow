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
        from wgnd.core.config import cfg as _default_cfg
        cfg = _default_cfg
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


# ---------------------------------------------------------------------------
# District Weather Sensitivity
# ---------------------------------------------------------------------------

def plot_district_weather_sensitivity(lf: pl.LazyFrame, cfg=None) -> None:
    """Two sorted bar charts (snow / heavy rain) with average line and above-avg highlight."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    titles  = {"has_snow": "Schnee", "has_heavy_rain": "Starkregen"}
    colors  = cfg.palette_n(2)
    style   = mpl_style()

    def _district_delta(flag):
        district = (
            lf_delay
            .group_by(["district_name", flag])
            .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
            .collect()
            .to_pandas()
        )
        normal  = district[district[flag] == False][["district_name", "avg_delay"]].rename(columns={"avg_delay": "normal"})
        weather = district[district[flag] == True][["district_name", "avg_delay"]].rename(columns={"avg_delay": "weather"})
        merged  = normal.merge(weather, on="district_name").dropna()
        merged  = merged[merged["district_name"] != "outside"].copy()
        merged["delta"] = (merged["weather"] - merged["normal"]).round(1)
        return merged.sort_values("delta", ascending=False).reset_index(drop=True)

    fig, axes = plt.subplots(1, len(weather_flags), figsize=(14, 5), sharey=False)
    if len(weather_flags) == 1:
        axes = [axes]

    for ax, flag, color in zip(axes, weather_flags, colors):
        df   = _district_delta(flag)
        mean = df["delta"].mean()
        above = df["delta"] >= mean

        bar_colors = [color if a else "#bbbbbb" for a in above]
        bars = ax.bar(range(len(df)), df["delta"], color=bar_colors, alpha=0.88)
        ax.bar_label(bars, labels=[f"+{v:.1f}" if v > 0 else f"{v:.1f}" for v in df["delta"]],
                     padding=2, fontsize=8)

        ax.axhline(mean, color="#e05a2b", lw=1.5, linestyle="--", label=f"Ø {mean:.1f}s")
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df["district_name"], rotation=35, ha="right", fontsize=9)
        ax.set_ylabel("Δ Delay vs. Normaltag (s)", **style["label"])
        ax.set_title(f"Wetterempfindlichkeit — {titles[flag]}", **style["title"])
        ax.legend(fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)

    _st = {k: v for k, v in style["title"].items() if k not in ("loc", "pad")}
    plt.suptitle("Stadtkreis-Vergleich: Schnee vs. Starkregen", **_st, y=1.02)
    plt.tight_layout()
    plt.show()


def table_district_weather_sensitivity(lf: pl.LazyFrame) -> pd.DataFrame:
    """Δ delay per Stadtkreis for snow and heavy rain side by side."""
    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    labels = {"has_snow": "Δ Schnee (s)", "has_heavy_rain": "Δ Starkregen (s)"}

    result = None
    for flag in weather_flags:
        district = (
            lf_delay
            .group_by(["district_name", flag])
            .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
            .collect()
            .to_pandas()
        )
        normal  = district[district[flag] == False][["district_name", "avg_delay"]].rename(columns={"avg_delay": "normal"})
        weather = district[district[flag] == True][["district_name", "avg_delay"]].rename(columns={"avg_delay": "weather"})
        merged  = normal.merge(weather, on="district_name").dropna()
        merged["delta"] = (merged["weather"] - merged["normal"]).round(1)
        col = merged[["district_name", "delta"]].rename(columns={"delta": labels[flag]})
        result = col if result is None else result.merge(col, on="district_name")

    return (
        result[result["district_name"] != "outside"]
        .sort_values("district_name")
        .rename(columns={"district_name": "Stadtkreis"})
        .set_index("Stadtkreis")
    )


# ---------------------------------------------------------------------------
# Stop & Line Weather Ranking
# ---------------------------------------------------------------------------

def _weather_delta_df(lf_delay, flag, group_col, min_n=500):
    """Compute Δ delay (weather vs normal) per group_col for a given flag."""
    agg = (
        lf_delay
        .group_by([group_col, flag])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )
    normal  = agg[agg[flag] == False][[group_col, "avg_delay"]].rename(columns={"avg_delay": "normal"})
    weather = agg[agg[flag] == True][[group_col, "avg_delay", "n"]].rename(columns={"avg_delay": "weather"})
    merged  = normal.merge(weather, on=group_col).dropna()
    merged  = merged[merged["n"] > min_n].copy()
    merged["delta"] = (merged["weather"] - merged["normal"]).round(1)
    return merged


def plot_stop_weather_ranking(lf: pl.LazyFrame, cfg=None, top_n: int = 20) -> None:
    """Horizontal bar charts: top stops by Δ delay for snow and heavy rain."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    titles  = {"has_snow": "Schnee", "has_heavy_rain": "Starkregen"}
    colors  = cfg.palette_n(2)
    style   = mpl_style()

    fig, axes = plt.subplots(1, len(weather_flags), figsize=(16, 7), sharey=False)
    if len(weather_flags) == 1:
        axes = [axes]

    for ax, flag, color in zip(axes, weather_flags, colors):
        df   = _weather_delta_df(lf_delay, flag, "stop_name")
        df   = df.nlargest(top_n, "delta").sort_values("delta", ascending=True).reset_index(drop=True)
        mean = df["delta"].mean()
        above = df["delta"] >= mean

        bar_colors = [color if a else "#bbbbbb" for a in above]
        bars = ax.barh(range(len(df)), df["delta"], color=bar_colors, alpha=0.88)
        ax.bar_label(bars, labels=[f"+{v:.1f}" if v > 0 else f"{v:.1f}" for v in df["delta"]],
                     padding=3, fontsize=8)

        ax.axvline(mean, color="#e05a2b", lw=1.5, linestyle="--", label=f"Ø {mean:.1f}s")
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df["stop_name"], fontsize=8)
        ax.set_xlabel("Δ Delay vs. Normaltag (s)", **style["label"])
        ax.set_title(f"Top {top_n} Haltestellen — {titles[flag]}", **style["title"])
        ax.legend(fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)

    _st = {k: v for k, v in style["title"].items() if k not in ("loc", "pad")}
    plt.suptitle("Haltestellen-Ranking: Schnee vs. Starkregen", **_st, y=1.02)
    plt.tight_layout()
    plt.show()


def table_stop_weather_ranking(lf: pl.LazyFrame, top_n: int = 20) -> pd.DataFrame:
    """Top stops by Δ delay for snow and heavy rain side by side."""
    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    labels  = {"has_snow": "Δ Schnee (s)", "has_heavy_rain": "Δ Starkregen (s)"}

    result = None
    for flag in weather_flags:
        df  = _weather_delta_df(lf_delay, flag, "stop_name")
        top = df.nlargest(top_n, "delta")[["stop_name", "delta"]].rename(
            columns={"delta": labels[flag], "stop_name": "Haltestelle"}
        ).reset_index(drop=True)
        top.index += 1
        result = top if result is None else result.merge(top, on="Haltestelle", how="outer")

    return result.set_index("Haltestelle")


def plot_line_weather_exposure(lf: pl.LazyFrame, cfg=None) -> None:
    """Sorted bar charts: Δ delay per line for snow and heavy rain."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    titles  = {"has_snow": "Schnee", "has_heavy_rain": "Starkregen"}
    colors  = cfg.palette_n(2)
    style   = mpl_style()

    fig, axes = plt.subplots(1, len(weather_flags), figsize=(14, 5), sharey=False)
    if len(weather_flags) == 1:
        axes = [axes]

    for ax, flag, color in zip(axes, weather_flags, colors):
        df   = _weather_delta_df(lf_delay, flag, "line_name", min_n=1000)
        df   = df.sort_values("delta", ascending=False).reset_index(drop=True)
        mean = df["delta"].mean()
        above = df["delta"] >= mean

        bar_colors = [color if a else "#bbbbbb" for a in above]
        bars = ax.bar(range(len(df)), df["delta"], color=bar_colors, alpha=0.88)
        ax.bar_label(bars, labels=[f"+{v:.1f}" if v > 0 else f"{v:.1f}" for v in df["delta"]],
                     padding=2, fontsize=8)

        ax.axhline(mean, color="#e05a2b", lw=1.5, linestyle="--", label=f"Ø {mean:.1f}s")
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df["line_name"], rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("Δ Delay vs. Normaltag (s)", **style["label"])
        ax.set_title(f"Linien-Betroffenheit — {titles[flag]}", **style["title"])
        ax.legend(fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)

    _st = {k: v for k, v in style["title"].items() if k not in ("loc", "pad")}
    plt.suptitle("Welche Linien leiden am meisten unter Wetter?", **_st, y=1.02)
    plt.tight_layout()
    plt.show()


def table_line_weather_exposure(lf: pl.LazyFrame) -> pd.DataFrame:
    """Δ delay per line for snow and heavy rain side by side."""
    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    labels  = {"has_snow": "Δ Schnee (s)", "has_heavy_rain": "Δ Starkregen (s)"}

    result = None
    for flag in weather_flags:
        df  = _weather_delta_df(lf_delay, flag, "line_name", min_n=1000)
        col = df[["line_name", "delta"]].rename(
            columns={"delta": labels[flag], "line_name": "Linie"}
        )
        result = col if result is None else result.merge(col, on="Linie", how="outer")

    return (
        result
        .sort_values("Δ Schnee (s)" if "Δ Schnee (s)" in result.columns else result.columns[1],
                     ascending=False)
        .set_index("Linie")
    )


# ---------------------------------------------------------------------------
# Daily Delay Timeline — Weather markers
# ---------------------------------------------------------------------------

def plot_daily_delay_weather_timeline(lf: pl.LazyFrame, cfg=None) -> None:
    """Daily avg delay per year (3 subplots) with weather markers and temperature overlay."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    daily = (
        lf_delay
        .group_by("operating_date")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("temperature").mean().alias("avg_temp"),
        ])
        .sort("operating_date")
        .collect()
        .to_pandas()
    )
    daily["operating_date"] = pd.to_datetime(daily["operating_date"])

    # Order matters: rain drawn first (background), snow/heavy rain on top
    weather_flags = [
        ("has_rain",       "Regen",      "#bbbbbb", 0.5, 0.8),
        ("has_heavy_rain", "Starkregen", "#e74c3c", 0.8, 2.0),
        ("has_snow",       "Schnee",     "#5b9bd5", 0.9, 2.0),
    ]
    available_flags = [(f, l, c, a, lw) for f, l, c, a, lw in weather_flags if f in _schema]

    weather_dates = {}
    for flag, label, color, alpha, lw in available_flags:
        dates = (
            lf_delay
            .filter(pl.col(flag) == True)
            .select("operating_date")
            .unique()
            .collect()
            .to_pandas()["operating_date"]
        )
        weather_dates[flag] = (pd.to_datetime(dates), label, color, alpha, lw)

    style = mpl_style()
    years = [2023, 2024, 2025]
    fig, axes = plt.subplots(3, 1, figsize=(18, 12), sharex=False)

    for ax, year in zip(axes, years):
        df_year = daily[daily["operating_date"].dt.year == year].sort_values("operating_date")
        baseline = df_year["avg_delay"].mean()

        # Delay line + mean
        ax.plot(df_year["operating_date"], df_year["avg_delay"],
                color="#222222", lw=1.2, alpha=0.85, label="Ø Delay")
        ax.axhline(baseline, color="#888888", lw=1, linestyle="--",
                   alpha=0.7, label=f"Ø {baseline:.1f}s")

        # Weather markers
        for flag, (dates, label, color, alpha, lw) in weather_dates.items():
            shown = False
            for d in dates[dates.dt.year == year]:
                lbl = label if not shown else None
                ax.axvline(pd.Timestamp(d), color=color, lw=lw, alpha=alpha, label=lbl)
                shown = True

        ax.set_ylabel("Ø Delay (s)", **style["label"])
        ax.set_xlim(pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"))
        ax.spines[["top", "right"]].set_visible(False)

        # Temperature overlay (second y-axis)
        ax2 = ax.twinx()
        ax2.plot(df_year["operating_date"], df_year["avg_temp"],
                 color="#f1c40f", lw=1.0, alpha=0.7, label="Temperatur")
        temp_mean = df_year["avg_temp"].mean()
        ax2.axhline(temp_mean, color="#f1c40f", lw=0.8, linestyle="--",
                    alpha=0.5, label=f"Ø {temp_mean:.1f}°C")
        ax2.set_ylabel("Temperatur (°C)", color="#f1c40f", fontsize=9)
        ax2.tick_params(axis="y", labelcolor="#f1c40f")
        ax2.spines[["top"]].set_visible(False)

        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper left", ncol=5)
        ax.set_title(str(year), **style["title"])

    axes[-1].set_xlabel("Datum", **style["label"])
    fig.suptitle("Daily Delay Timeline — Weather Events & Temperature", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.show()


def table_daily_delay_weather_timeline(lf: pl.LazyFrame) -> pd.DataFrame:
    """Top weather days by avg delay — worst snow, heavy rain, hot days."""
    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [
        ("has_snow",       "Schnee"),
        ("has_heavy_rain", "Starkregen"),
        ("is_hot",         "Hitze"),
    ]
    frames = []
    for flag, label in weather_flags:
        if flag not in _schema:
            continue
        df = (
            lf_delay
            .filter(pl.col(flag) == True)
            .group_by("operating_date")
            .agg([
                pl.col("arrival_delay").mean().alias("avg_delay"),
                (pl.col("arrival_delay").abs() <= 120).mean().alias("otp"),
                pl.len().alias("n"),
            ])
            .sort("avg_delay", descending=True)
            .head(10)
            .collect()
            .to_pandas()
        )
        df["Wetter"] = label
        frames.append(df)

    result = pd.concat(frames).sort_values("avg_delay", ascending=False)
    result["otp"] = result["otp"].apply(lambda x: f"{x:.1%}")
    result["avg_delay"] = result["avg_delay"].round(1)
    return (
        result[["operating_date", "Wetter", "avg_delay", "otp", "n"]]
        .rename(columns={
            "operating_date": "Datum",
            "avg_delay":      "Ø Delay (s)",
            "otp":            "OTP",
            "n":              "N Halte",
        })
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Stop-level Weather Impact Map
# ---------------------------------------------------------------------------

def plot_weather_stop_map(lf: pl.LazyFrame, flag: str = "has_snow") -> None:
    """Plotly bubble map: Δ delay per stop for a given weather flag vs normal days.

    Reuses the same pattern as plot_event_stop_map in analytics/events.py.
    flag: 'has_snow', 'has_heavy_rain', or 'is_hot'
    """
    import plotly.graph_objects as go
    import json
    import numpy as np
    from pathlib import Path

    lf_delay = lf.filter(pl.col("canceled") == False)

    stop_weather = (
        lf_delay
        .group_by(["stop_name", "stop_lat", "stop_lon", "district_name", "district_nr", flag])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal  = stop_weather[stop_weather[flag] == False][["stop_name", "stop_lat", "stop_lon", "avg_delay", "n"]].rename(columns={"avg_delay": "normal", "n": "n_normal"})
    weather = stop_weather[stop_weather[flag] == True][["stop_name", "avg_delay", "n"]].rename(columns={"avg_delay": "weather", "n": "n_weather"})

    stops = normal.merge(weather, on="stop_name").dropna()
    stops = stops[stops["n_weather"] > 500]
    stops["delta"]     = (stops["weather"] - stops["normal"]).round(1)
    stops["abs_delta"] = stops["delta"].abs()
    # Dynamic scale based on actual data
    vmax = stops["delta"].quantile(0.95)
    vmin = stops["delta"].quantile(0.05)
    vcenter = stops["delta"].median()

    district_weather = (
        lf_delay
        .group_by(["district_nr", flag])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .collect()
        .to_pandas()
    )
    d_normal  = district_weather[district_weather[flag] == False][["district_nr", "avg_delay"]].rename(columns={"avg_delay": "normal"})
    d_weather = district_weather[district_weather[flag] == True][["district_nr", "avg_delay"]].rename(columns={"avg_delay": "weather"})
    d_delta   = d_normal.merge(d_weather, on="district_nr").dropna()
    d_delta["delta"] = (d_delta["weather"] - d_delta["normal"]).round(1)
    delta_map = dict(zip(d_delta["district_nr"].astype(str), d_delta["delta"]))

    geo_path = Path(__file__).parents[3] / "data" / "raw" / "stadtkreise.geojson"
    with open(geo_path) as f:
        stadtkreise = json.load(f)

    kreis_ids    = [str(f["properties"]["objid"]) for f in stadtkreise["features"]]
    kreis_deltas = [delta_map.get(kid, 0) for kid in kreis_ids]

    label_lats, label_lons, label_texts = [], [], []
    for feature in stadtkreise["features"]:
        coords = np.array(feature["geometry"]["coordinates"][0])
        label_lats.append(coords[:, 1].mean())
        label_lons.append(coords[:, 0].mean())
        kid = feature["properties"]["objid"]
        d = delta_map.get(str(kid), 0)
        label_texts.append(f"K{kid} ({d:+.1f}s)")

    flag_labels = {"has_snow": "Schnee", "has_heavy_rain": "Starkregen", "is_hot": "Hitze"}
    flag_label  = flag_labels.get(flag, flag)

    fig = go.Figure()

    d_vmax = max(abs(min(kreis_deltas)), abs(max(kreis_deltas))) if kreis_deltas else 10

    fig.add_trace(go.Choroplethmapbox(
        geojson=stadtkreise,
        locations=kreis_ids,
        z=kreis_deltas,
        featureidkey="properties.objid",
        colorscale="RdBu_r",
        zmid=0, zmin=-d_vmax, zmax=d_vmax,
        colorbar=dict(title="Kreis Δ (s)", x=0.01, len=0.4, y=0.6),
        marker=dict(line=dict(color="#888888", width=1), opacity=0.45),
        hovertemplate="<b>Kreis %{location}</b><br>Δ Delay: %{z:+.1f}s<extra></extra>",
    ))

    bubble_size = (stops["abs_delta"] / stops["abs_delta"].max() * 25).clip(lower=3)

    fig.add_trace(go.Scattermapbox(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="markers",
        marker=dict(
            size=bubble_size,
            color=stops["delta"],
            colorscale="RdBu_r",
            cmin=vmin, cmid=vcenter, cmax=vmax,
            colorbar=dict(title="Stop Δ (s)", x=1.0, len=0.4, y=0.6),
            opacity=0.85,
        ),
        text=stops.apply(
            lambda r: f"{r['stop_name']}<br>Normal: {r['normal']:.1f}s<br>{flag_label}: {r['weather']:.1f}s<br>Δ: {r['delta']:+.1f}s",
            axis=1
        ),
        hoverinfo="text",
    ))

    fig.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons,
        mode="text", text=label_texts,
        textfont=dict(size=11, color="#cccccc"),
        hoverinfo="skip",
    ))

    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_zoom=11,
        mapbox_center={"lat": 47.378, "lon": 8.540},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=650,
        title=f"Weather Impact per Stop — Δ Delay ({flag_label} vs. Normal)",
    )
    fig.show()


def table_weather_stop_map(lf: pl.LazyFrame, flag: str = "has_snow") -> pd.DataFrame:
    """Top stops by Δ delay for a given weather flag vs normal days."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    stop_weather = (
        lf_delay
        .group_by(["stop_name", "district_name", flag])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )

    normal  = stop_weather[stop_weather[flag] == False][["stop_name", "district_name", "avg_delay", "n"]].rename(columns={"avg_delay": "normal", "n": "n_normal"})
    weather = stop_weather[stop_weather[flag] == True][["stop_name", "avg_delay", "n"]].rename(columns={"avg_delay": "weather", "n": "n_weather"})

    stops = normal.merge(weather, on="stop_name").dropna()
    stops = stops[stops["n_weather"] > 500]
    stops["delta"] = (stops["weather"] - stops["normal"]).round(1)

    flag_labels = {"has_snow": "Schnee (s)", "has_heavy_rain": "Starkregen (s)", "is_hot": "Hitze (s)"}
    col = flag_labels.get(flag, flag)

    return (
        stops.sort_values("delta", ascending=False)
        .head(20)
        [["stop_name", "district_name", "normal", "weather", "delta", "n_weather"]]
        .rename(columns={
            "stop_name":     "Haltestelle",
            "district_name": "Stadtkreis",
            "normal":        "Normal (s)",
            "weather":       col,
            "delta":         "Δ (s)",
            "n_weather":     "N Halte",
        })
        .round({"Normal (s)": 1, col: 1})
        .reset_index(drop=True)
    )
