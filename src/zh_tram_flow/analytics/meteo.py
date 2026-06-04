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
  plot_weather_stop_map(lf, flag, vmax=None)
  plot_weather_stop_map_combined(lf, vmax=60.0)
  table_weather_stop_map(lf, flag)
  plot_snow_structural_interaction(lf, cfg=None)
"""

import polars as pl
from zh_tram_flow.plot_styles import (style_ax, LEGEND_KW, LEGEND_KW_RIGHT, LEGEND_KW_LEFT,
                                               mean_kw, median_kw, otp_kw, trend_kw, data_line_kw,
                                               FIG_SINGLE, FIG_2PANEL, FIG_3PANEL, FIG_TIMELINE, FIG_WIDE, FIG_TALL,
                                               TITLE_KW, fmt_line_axis, fmt_line_legend, plotly_title)
from zh_tram_flow.config import ANNO_MEDIAN, auto_export, ANNO_MEAN, BAR_NEUTRAL, OTP_ON_TIME
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

@auto_export("meteo-weather-overview")
def plot_weather_overview(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
    """Stacked bars: Normal (grau) + Delta (Blau-Skala) je Wetterbedingung.
    Rechte Achse: Delta in % (teal Linie).
    """
    from wgnd.core.theme import mpl_style
    from matplotlib.lines import Line2D
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)

    flags = [
        ("has_snow",       "Snow"),
        ("has_heavy_rain", "Heavy Rain"),
        ("has_rain",       "Rain"),
    ]
    _weather_colors = {
        "Snow":     "#2166ac",
        "Heavy Rain": "#4393c3",
        "Rain":      "#92c5de",
    }

    baseline_rows, effect_rows = [], []
    for flag, label in flags:
        df = _weather_compare(lf_delay, flag, label)
        base = df[df[flag] == False]["avg_delay"].values
        eff  = df[df[flag] == True]["avg_delay"].values
        if len(base) > 0 and len(eff) > 0:
            baseline_rows.append({"condition": label, "delay": base[0]})
            effect_rows.append({
                "condition":   label,
                "delay":       eff[0],
                "delta":       eff[0] - base[0],
                "otp_normal":  df[df[flag] == False]["otp_rate"].values[0],
                "otp_weather": df[df[flag] == True]["otp_rate"].values[0],
                "n_weather":   df[df[flag] == True]["n"].values[0],
            })

    x_arr       = list(range(len(baseline_rows)))
    cond_labels = [r["condition"] for r in baseline_rows]
    normal_vals = [r["delay"]     for r in baseline_rows]
    deltas      = [r["delta"]     for r in effect_rows]
    delta_pcts  = [d / n * 100 for d, n in zip(deltas, normal_vals)]

    style = mpl_style()
    _teal = cfg.COLOR_POSITIVE

    fig, ax = plt.subplots(figsize=(10, 5))
    ax_r = ax.twinx()

    # Stacked bars: grau (Normal) als Basis, Blau-Skala (Delta) obendrauf
    ax.bar(x_arr, normal_vals, color="#aaaaaa", alpha=0.6)
    for xi, label, d, nv in zip(x_arr, cond_labels, deltas, normal_vals):
        ax.bar(xi, d, bottom=nv, color=_weather_colors[label], alpha=0.6)
        ax.text(xi, nv + d + 0.5, f"+{d:.0f}s", ha="center", va="bottom", fontsize=9)

    # Rechte Achse: Delta in %
    ax_r.plot(x_arr, delta_pcts, color=_teal, lw=1.0, linestyle="--",
              marker="o", markersize=5, zorder=5)
    ax_r.set_ylabel("Delta (%)", fontsize=10, color=_teal)
    ax_r.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax_r.tick_params(axis="y", colors=_teal, labelsize=9)
    ax_r.spines[["top", "left"]].set_visible(False)
    ax_r.spines["right"].set_color(_teal)

    ax.set_xticks(x_arr)
    ax.set_xticklabels(cond_labels, fontsize=10)
    ax.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax.set_title("Weather Effect on Delays", **TITLE_KW)
    style_ax(ax)

    legend_handles = [
        Line2D([0], [0], color="#aaaaaa", lw=1.0,                  label="Normal"),
        Line2D([0], [0], color="#2166ac", lw=1.0,                  label="Snow"),
        Line2D([0], [0], color="#4393c3", lw=1.0,                  label="Heavy Rain"),
        Line2D([0], [0], color="#92c5de", lw=1.0,                  label="Rain"),
        Line2D([0], [0], color=_teal,     lw=1.0, linestyle="--",  label="Δ (%)"),
    ]
    ax.legend(**LEGEND_KW_RIGHT)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()



def table_weather_overview(lf: pl.LazyFrame) -> pd.DataFrame:
    """Return DataFrame with weather effect stats (delta, OTP, n)."""
    lf_delay = lf.filter(pl.col("canceled") == False)

    flags = [
        ("has_rain",       "Rain"),
        ("has_heavy_rain", "Heavy Rain"),
        ("has_snow",       "Snow"),
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

@auto_export("meteo-temperature-precipitation")
def plot_temperature_precipitation(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
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
        else BAR_NEUTRAL
        for v in temp_bins["avg_delay"]
    ]
    ax1.bar(range(len(temp_bins)), temp_bins["avg_delay"], color=temp_colors, alpha=0.85)
    ax1.axhline(mean_delay, **mean_kw("Ø"))
    zero_mask = temp_bins[temp_bins["temp_bin_5c"] == 0]
    if len(zero_mask) > 0:
        ax1.axvline(zero_mask.index[0], color=cfg.CHART_AXIS, lw=1, linestyle=":", label="0°C")
    ax1.set_xticks(range(len(temp_bins)))
    ax1.set_xticklabels(temp_bins["temp_label"], rotation=45, fontsize=8)
    ax1.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax1.set_title("Delay by Temperature (5°C Bins)", **TITLE_KW)
    ax1.legend(**LEGEND_KW_RIGHT)
    ax1.spines[["top", "right"]].set_visible(False)

    # Precipitation intensity
    pc = [
        cfg.COLOR_NEGATIVE if v > precip_bins["avg_delay"].mean() * 1.1
        else BAR_NEUTRAL
        for v in precip_plot["avg_delay"]
    ]
    ax2.bar(precip_plot["precip_bin"], precip_plot["avg_delay"], color=pc, alpha=0.85)
    for i, (v, n) in enumerate(zip(precip_plot["avg_delay"], precip_plot["n"])):
        ax2.text(i, v + 0.3, f"{v:+.1f}s\n(n={n/1000:.0f}k)", ha="center", fontsize=8)
    ax2.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax2.set_title("Delay by Precipitation Intensity (Rain Days)", **TITLE_KW)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
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
            "avg_delay":  "Avg. Delay (s)",
            "otp_rate":   "OTP",
            "n":          "N Halte",
        })
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
    )
    result["Avg. Delay (s)"] = result["Avg. Delay (s)"].round(1)
    return result.set_index("Temperatur")


# ---------------------------------------------------------------------------
# is_hot feature
# ---------------------------------------------------------------------------

@auto_export("meteo-is-hot")
def plot_is_hot(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
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
    labels_hot = ["Normal (≤20°C)", "Hot (>20°C)"]
    colors_hot = [BAR_NEUTRAL, cfg.COLOR_NEGATIVE]

    style = mpl_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Panel 1: Direktvergleich
    bars = ax1.bar(labels_hot, vals, color=colors_hot, alpha=0.85)
    for bar, v, n in zip(bars, vals, ns):
        ax1.text(bar.get_x() + bar.get_width() / 2, v + 0.3,
                 f"{v:+.1f}s\n(n={n/1e6:.1f}M)", ha="center", fontsize=9)
    ax1.set_title(f"is_hot — Delta: {delta:+.1f}s", **TITLE_KW)
    ax1.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax1.spines[["top", "right"]].set_visible(False)

    # Panel 2: Temperaturkurve mit 20°C-Schwelle
    bin_colors = [cfg.COLOR_NEGATIVE if tb >= 4 else BAR_NEUTRAL
                  for tb in temp_bins_hot["temp_bin_5c"]]
    ax2.bar(range(len(temp_bins_hot)), temp_bins_hot["avg_delay"], color=bin_colors, alpha=0.85)
    tb_list = list(temp_bins_hot["temp_bin_5c"])
    if 4 in tb_list:
        thresh_x = tb_list.index(4) - 0.5
        ax2.axvline(thresh_x, color=cfg.COLOR_NEGATIVE, lw=1.0, linestyle="--", label="20°C Threshold")
    ax2.set_xticks(range(len(temp_bins_hot)))
    ax2.set_xticklabels([f"{b*5}°C" for b in temp_bins_hot["temp_bin_5c"]], rotation=45, fontsize=9)
    ax2.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax2.set_title("Temperature Curve — 20°C Threshold Marked", **TITLE_KW)
    ax2.legend(**LEGEND_KW_RIGHT)
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
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
            "avg_delay": "Avg. Delay (s)",
            "med_delay": "Median (s)",
            "otp_rate":  "OTP",
            "n":         "N Halte",
        })
        .assign(is_hot=lambda df: df["is_hot"].map(
            {False: "Normal (≤20°C)", True: "Heiss (>20°C)"}))
        .assign(OTP=lambda df: df["OTP"].apply(lambda x: f"{x:.1%}"))
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
    )
    result["Avg. Delay (s)"] = result["Avg. Delay (s)"].round(1)
    result["Median (s)"]  = result["Median (s)"].round(1)
    return result.set_index("is_hot")


# ---------------------------------------------------------------------------
# Multicollinearity / correlation matrix
# ---------------------------------------------------------------------------

@auto_export("meteo-multicollinearity-matrix")
def plot_multicollinearity_matrix(lf: pl.LazyFrame, cfg=None, save_as=None) -> plt.Figure:
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
    plt.colorbar(im, ax=ax, label="Pearson Correlation", shrink=0.8)

    ax.set_xticks(range(len(available)))
    ax.set_yticks(range(len(available)))
    ax.set_xticklabels(available, rotation=45, ha="right", fontsize=10)
    ax.set_yticklabels(available, fontsize=10)

    for i in range(len(available)):
        for j in range(len(available)):
            val   = corr_matrix.iloc[i, j]
            color = "white" if abs(val) > 0.5 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8, color=color)

    ax.set_title("Correlation Matrix — Weather × Season × Delay", **TITLE_KW)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
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

@auto_export("meteo-district-weather-sensitivity")
def plot_district_weather_sensitivity(lf: pl.LazyFrame, cfg=None, save_as=None) -> None:
    """Two sorted bar charts (snow / heavy rain) with average line and above-avg highlight."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    titles  = {"has_snow": "Snow", "has_heavy_rain": "Heavy Rain"}
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

        ax.axhline(mean, color="#e05a2b", lw=1.0, linestyle="--", label=f"Ø {mean:.1f}s")
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df["district_name"], rotation=35, ha="right", fontsize=9)
        ax.set_ylabel("Δ Delay vs. Normal Day (s)", **style["label"])
        ax.set_title(f"Weather Sensitivity — {titles[flag]}", **TITLE_KW)
        ax.legend(**LEGEND_KW_RIGHT)
        ax.spines[["top", "right"]].set_visible(False)

    _st = {k: v for k, v in TITLE_KW.items() if k not in ("loc", "pad")}
    plt.suptitle("District Comparison: Snow vs. Heavy Rain", **_st, y=1.02)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
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
        .rename(columns={"district_name": "District"})
        .set_index("District")
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


@auto_export("meteo-stop-weather-ranking")
def plot_stop_weather_ranking(lf: pl.LazyFrame, cfg=None, top_n: int = 20, save_as=None) -> None:
    """Horizontal bar charts: top stops by Δ delay for snow and heavy rain."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    titles  = {"has_snow": "Snow", "has_heavy_rain": "Heavy Rain"}
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

        ax.axvline(mean, color="#e05a2b", lw=1.0, linestyle="--", label=f"Ø {mean:.1f}s")
        ax.set_yticks(range(len(df)))
        ax.set_yticklabels(df["stop_name"], fontsize=8)
        ax.set_xlabel("Δ Delay vs. Normal Day (s)", **style["label"])
        ax.set_title(f"Top {top_n} Stops — {titles[flag]}", **TITLE_KW)
        ax.legend(**LEGEND_KW_RIGHT)
        ax.spines[["top", "right"]].set_visible(False)

    _st = {k: v for k, v in TITLE_KW.items() if k not in ("loc", "pad")}
    plt.suptitle("Stop Ranking: Snow vs. Heavy Rain", **_st, y=1.02)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
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
            columns={"delta": labels[flag], "stop_name": "Stop"}
        ).reset_index(drop=True)
        top.index += 1
        result = top if result is None else result.merge(top, on="Stop", how="outer")

    return result.set_index("Stop")


@auto_export("meteo-line-weather-exposure")
def plot_line_weather_exposure(lf: pl.LazyFrame, cfg=None, save_as=None) -> None:
    """Sorted bar charts: Δ delay per line for snow and heavy rain."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)

    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [f for f in ["has_snow", "has_heavy_rain"] if f in _schema]
    titles  = {"has_snow": "Snow", "has_heavy_rain": "Heavy Rain"}
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

        ax.axhline(mean, color="#e05a2b", lw=1.0, linestyle="--", label=f"Ø {mean:.1f}s")
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(df["line_name"], rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("Δ Delay vs. Normal Day (s)", **style["label"])
        ax.set_title(f"Line Exposure — {titles[flag]}", **TITLE_KW)
        ax.legend(**LEGEND_KW_RIGHT)
        ax.spines[["top", "right"]].set_visible(False)

    _st = {k: v for k, v in TITLE_KW.items() if k not in ("loc", "pad")}
    plt.suptitle("Which Lines Suffer Most from Weather?", **_st, y=1.02)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
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
            columns={"delta": labels[flag], "line_name": "Line"}
        )
        result = col if result is None else result.merge(col, on="Line", how="outer")

    return (
        result
        .sort_values("Δ Schnee (s)" if "Δ Schnee (s)" in result.columns else result.columns[1],
                     ascending=False)
        .set_index("Line")
    )


# ---------------------------------------------------------------------------
# Daily Delay Timeline — Weather markers
# ---------------------------------------------------------------------------

@auto_export("meteo-daily-delay-weather-timeline")
def plot_daily_delay_weather_timeline(lf: pl.LazyFrame, cfg=None, save_as=None) -> None:
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
        ("has_rain",       "Rain",      "#bbbbbb", 0.5, 0.8),
        ("has_heavy_rain", "Heavy Rain", "#e74c3c", 0.8, 2.0),
        ("has_snow",       "Snow",     "#5b9bd5", 0.9, 2.0),
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
                color="#222222", lw=1.0, alpha=0.85, label="Ø Delay")
        ax.axhline(baseline, color="#888888", lw=1, linestyle="--",
                   alpha=0.7, label=f"Ø {baseline:.1f}s")

        # Weather markers
        for flag, (dates, label, color, alpha, lw) in weather_dates.items():
            shown = False
            for d in dates[dates.dt.year == year]:
                lbl = label if not shown else None
                ax.axvline(pd.Timestamp(d), color=color, lw=lw, alpha=alpha, label=lbl)
                shown = True

        ax.set_ylabel("Avg. Delay (s)", **style["label"])
        ax.set_xlim(pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"))
        ax.spines[["top", "right"]].set_visible(False)

        # Temperature overlay (second y-axis)
        ax2 = ax.twinx()
        ax2.plot(df_year["operating_date"], df_year["avg_temp"],
                 color="#f1c40f", lw=1.0, alpha=0.7, label="Temperature")
        temp_mean = df_year["avg_temp"].mean()
        ax2.axhline(temp_mean, color="#f1c40f", lw=0.8, linestyle="--",
                    alpha=0.5, label=f"Ø {temp_mean:.1f}°C")
        ax2.set_ylabel("Temperature (°C)", color="#f1c40f", fontsize=9)
        ax2.tick_params(axis="y", labelcolor="#f1c40f")
        ax2.spines[["top"]].set_visible(False)

        # Combined legend
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, **LEGEND_KW_RIGHT)
        ax.set_title(str(year), **TITLE_KW)

    axes[-1].set_xlabel("Date", **style["label"])
    fig.suptitle("Daily Delay Timeline — Weather Events & Temperature", fontsize=11, fontweight="bold", x=0.05, ha="left", y=1.01)
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()


def table_daily_delay_weather_timeline(lf: pl.LazyFrame) -> pd.DataFrame:
    """Top weather days by avg delay — worst snow, heavy rain, hot days."""
    lf_delay = lf.filter(pl.col("canceled") == False)
    _schema  = lf_delay.collect_schema()

    weather_flags = [
        ("has_snow",       "Snow"),
        ("has_heavy_rain", "Heavy Rain"),
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
            "avg_delay":      "Avg. Delay (s)",
            "otp":            "OTP",
            "n":              "N Halte",
        })
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Stop-level Weather Impact Map
# ---------------------------------------------------------------------------

@auto_export("meteo-weather-stop-map")
def plot_weather_stop_map(
    lf: pl.LazyFrame,
    flag: str = "has_snow",
    vmax: float | None = None,
    save_html: "Path | None" = None,
) -> None:
    """Plotly bubble map: Δ delay per stop for a given weather flag vs normal days.

    Reuses the same pattern as plot_event_stop_map in analytics/events.py.
    flag: 'has_snow', 'has_heavy_rain', or 'is_hot'
    vmax: optional fixed color scale maximum (seconds). When set, only the most
          extreme stops saturate to full red — useful to compare two maps on the
          same scale. Defaults to the 95th percentile of the data.
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
    # Color scale: use provided vmax (fixed range) or fall back to 95th percentile
    _vmax    = vmax if vmax is not None else stops["delta"].quantile(0.95)
    _vmin    = -_vmax if vmax is not None else stops["delta"].quantile(0.05)
    vcenter  = stops["delta"].median()
    vmax     = _vmax
    vmin     = _vmin

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

    flag_labels = {"has_snow": "Snow", "has_heavy_rain": "Heavy Rain", "is_hot": "Hitze"}
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
        textfont=dict(size=11, color="#333333"),
        hoverinfo="skip",
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=11,
        mapbox_center={"lat": 47.378, "lon": 8.540},
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        height=650,
        title=plotly_title(f"Weather Impact per Stop — Δ Delay ({flag_label} vs. Normal)"),
    )
    if save_html is not None:
        fig.write_html(save_html, include_plotlyjs="cdn")
    fig.show()
    return fig


@auto_export("meteo-weather-stop-map-combined")
def plot_weather_stop_map_combined(
    lf: pl.LazyFrame,
    vmax: float = 60.0,
    save_html: "Path | None" = None,
) -> None:
    """Combined Plotly map: stop delay during snow + heavy rain in one figure.

    Legend / navigation items:
      Haltestellen               — all stops, gray background dots
      HS Verspätung bei Schnee   — bubbles colored by avg_delay during snow (YlOrRd)
      HS Verspätung bei Starkregen — bubbles colored by avg_delay during heavy rain (YlOrRd)
      Stadtkreise Schnee         — choropleth + K-labels (one click toggles both)
      Stadtkreise Starkregen     — choropleth + K-labels (one click toggles both)
    """
    import plotly.graph_objects as go
    import json
    import numpy as np
    from pathlib import Path

    lf_delay = lf.filter(pl.col("canceled") == False)

    # ── All stops (gray background skeleton) ─────────────────────────────────
    all_stops = (
        lf_delay
        .group_by(["stop_name"])
        .agg([
            pl.col("stop_lat").mean(),
            pl.col("stop_lon").mean(),
        ])
        .collect()
        .to_pandas()
    )

    # ── Stop-level avg_delay per weather condition ────────────────────────────
    def _stop_weather_delay(flag: str, min_n: int = 500) -> pd.DataFrame:
        return (
            lf_delay
            .filter(pl.col(flag) == True)
            .group_by(["stop_name"])
            .agg([
                pl.col("arrival_delay").mean().alias("avg_delay"),
                pl.col("stop_lat").mean(),
                pl.col("stop_lon").mean(),
                pl.len().alias("n"),
            ])
            .collect()
            .to_pandas()
            .pipe(lambda df: df[df["n"] >= min_n].copy())
        )

    snow_stops = _stop_weather_delay("has_snow")
    rain_stops = _stop_weather_delay("has_heavy_rain")
    snow_stops["avg_delay"] = snow_stops["avg_delay"].round(1)
    rain_stops["avg_delay"] = rain_stops["avg_delay"].round(1)

    # Shared bubble size scale across both layers
    _max_delay = max(
        snow_stops["avg_delay"].max() if len(snow_stops) else 1.0,
        rain_stops["avg_delay"].max() if len(rain_stops) else 1.0,
    )

    def _bubble_size(series: pd.Series) -> pd.Series:
        return (series / _max_delay * 20).clip(lower=4)

    # Color scale: span the actual data range (5th–95th percentile) so the full
    # gradient is used instead of everything saturating to dark red.
    _all_delays = pd.concat([snow_stops["avg_delay"], rain_stops["avg_delay"]])
    vmin = float(_all_delays.quantile(0.05))
    vmax = float(_all_delays.quantile(0.95))

    # ── District-level avg_delay per weather condition ────────────────────────
    def _district_weather_delay(flag: str) -> dict:
        return (
            lf_delay
            .filter(pl.col(flag) == True)
            .group_by("district_nr")
            .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
            .collect()
            .to_pandas()
            .assign(district_nr=lambda df: df["district_nr"].astype(str))
            .set_index("district_nr")["avg_delay"]
            .to_dict()
        )

    snow_d_delay = _district_weather_delay("has_snow")
    rain_d_delay = _district_weather_delay("has_heavy_rain")

    # ── GeoJSON ───────────────────────────────────────────────────────────────
    geo_path = Path(__file__).parents[3] / "data" / "raw" / "stadtkreise.geojson"
    with open(geo_path) as f:
        geojson = json.load(f)

    kreis_ids = [str(feat["properties"]["objid"]) for feat in geojson["features"]]
    label_lats, label_lons = [], []
    for feat in geojson["features"]:
        coords = np.array(feat["geometry"]["coordinates"][0])
        label_lats.append(float(coords[:, 1].mean()))
        label_lons.append(float(coords[:, 0].mean()))
    label_texts = [f"K{kid}" for kid in kreis_ids]

    snow_delays = [snow_d_delay.get(kid, 0.0) for kid in kreis_ids]
    rain_delays  = [rain_d_delay.get(kid, 0.0) for kid in kreis_ids]

    # ── Build figure ──────────────────────────────────────────────────────────
    fig = go.Figure()

    # 1. Snow district choropleth (grouped — legend entry on K-label trace)
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=kreis_ids,
        z=snow_delays,
        featureidkey="properties.objid",
        colorscale="YlOrRd",
        zmin=vmin, zmax=vmax,
        showscale=False,
        legendgroup="Districts Snow",
        showlegend=False,
        marker=dict(line=dict(color="#888888", width=1.5), opacity=0.3),
        hovertemplate="<b>Kreis %{location}</b><br>Ø Delay (Schnee): %{z:.1f}s<extra></extra>",
        name="Stadtkreise Schnee",
    ))

    # 2. Snow K-labels (carries the legend entry — one click toggles choropleth too)
    fig.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons,
        mode="text", text=label_texts,
        textfont=dict(size=11, color="#444444"),
        hoverinfo="skip",
        legendgroup="Districts Snow",
        showlegend=True,
        name="Stadtkreise Schnee",
    ))

    # 3. Heavy rain district choropleth
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=kreis_ids,
        z=rain_delays,
        featureidkey="properties.objid",
        colorscale="YlOrRd",
        zmin=vmin, zmax=vmax,
        showscale=False,
        legendgroup="Districts Heavy Rain",
        showlegend=False,
        marker=dict(line=dict(color="#888888", width=1.5), opacity=0.3),
        hovertemplate="<b>Kreis %{location}</b><br>Ø Delay (Starkregen): %{z:.1f}s<extra></extra>",
        name="Stadtkreise Starkregen",
    ))

    # 4. Heavy rain K-labels
    fig.add_trace(go.Scattermapbox(
        lat=label_lats, lon=label_lons,
        mode="text", text=label_texts,
        textfont=dict(size=11, color="#444444"),
        hoverinfo="skip",
        legendgroup="Districts Heavy Rain",
        showlegend=True,
        name="Stadtkreise Starkregen",
    ))

    # 5. All stops — gray background
    fig.add_trace(go.Scattermapbox(
        lat=all_stops["stop_lat"],
        lon=all_stops["stop_lon"],
        mode="markers",
        marker=dict(size=5, color="#666666", opacity=0.55),
        text=all_stops["stop_name"].str.replace("Zürich, ", ""),
        hovertemplate="<b>%{text}</b><extra></extra>",
        name="Haltestellen",
    ))

    # 6. Snow stop bubbles — reference shared coloraxis so colorbar is always visible
    fig.add_trace(go.Scattermapbox(
        lat=snow_stops["stop_lat"],
        lon=snow_stops["stop_lon"],
        mode="markers",
        marker=dict(
            size=_bubble_size(snow_stops["avg_delay"]),
            color=snow_stops["avg_delay"],
            coloraxis="coloraxis",
            opacity=0.85,
        ),
        text=snow_stops["stop_name"].str.replace("Zürich, ", ""),
        customdata=snow_stops[["avg_delay", "n"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Ø Delay (Schnee): %{customdata[0]:.1f}s<br>"
            "N: %{customdata[1]:,.0f}<extra></extra>"
        ),
        name="HS Verspätung bei Schnee",
    ))

    # 7. Heavy rain stop bubbles — same shared coloraxis
    fig.add_trace(go.Scattermapbox(
        lat=rain_stops["stop_lat"],
        lon=rain_stops["stop_lon"],
        mode="markers",
        marker=dict(
            size=_bubble_size(rain_stops["avg_delay"]),
            color=rain_stops["avg_delay"],
            coloraxis="coloraxis",
            opacity=0.85,
        ),
        text=rain_stops["stop_name"].str.replace("Zürich, ", ""),
        customdata=rain_stops[["avg_delay", "n"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Ø Delay (Starkregen): %{customdata[0]:.1f}s<br>"
            "N: %{customdata[1]:,.0f}<extra></extra>"
        ),
        name="HS Verspätung bei Starkregen",
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": 47.378, "lon": 8.540},
        mapbox_zoom=11.5,
        margin=dict(l=0, r=0, t=30, b=0),
        height=620,
        title=plotly_title("Districts and Stops — Delay during Snow and Heavy Rain"),
        coloraxis=dict(
            colorscale="YlOrRd",
            cmin=vmin,
            cmax=vmax,
            colorbar=dict(title="Avg. Delay (s)", thickness=12, len=0.6),
        ),
    )
    if save_html is not None:
        fig.write_html(save_html, include_plotlyjs="cdn")
    fig.show()
    return fig


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
            "stop_name":     "Stop",
            "district_name": "District",
            "normal":        "Normal (s)",
            "weather":       col,
            "delta":         "Δ (s)",
            "n_weather":     "N Halte",
        })
        .round({"Normal (s)": 1, col: 1})
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Snow Structural Interaction
# ---------------------------------------------------------------------------

@auto_export("meteo-snow-structural-interaction")
def plot_snow_structural_interaction(lf: pl.LazyFrame, cfg=None, save_as=None) -> None:
    """Schnee-Verstärker: delay_delta (Akkumulationsrate) und arrival_delay — normal vs. Schnee.

    Zeigt dass Schnee nicht nur einen externen Zusatz-Delay verursacht,
    sondern den strukturellen Aufbau-Mechanismus verstärkt:
      delay_delta normal ≈ 4.95 s/Halt → Schnee ≈ 6.58 s/Halt (+33 %)

    Zwei Panels:
      Links:  Ø delay_delta — Akkumulationsrate pro Halt (strukturelle Verstärkung)
      Rechts: Ø arrival_delay — sichtbarer Fahrgast-Impact (+54 s)

    Input: lf_clean (benötigt delay_delta, has_snow).
    """
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)
    style = mpl_style()

    stats = (
        lf.filter(pl.col("delay_delta").is_not_null())
        .group_by("has_snow")
        .agg([
            pl.col("delay_delta").mean().alias("mean_dd"),
            pl.col("arrival_delay").mean().alias("mean_arr"),
            pl.len().alias("n"),
        ])
        .sort("has_snow")
        .collect()
        .to_pandas()
    )

    normal_row = stats[stats["has_snow"] == False].iloc[0]
    snow_row   = stats[stats["has_snow"] == True].iloc[0]

    labels     = ["Normal", "Snow"]
    dd_vals    = [normal_row["mean_dd"],  snow_row["mean_dd"]]
    arr_vals   = [normal_row["mean_arr"], snow_row["mean_arr"]]
    bar_colors = ["#aaaaaa", "#2166ac"]

    delta_dd_pct = (snow_row["mean_dd"]  - normal_row["mean_dd"])  / normal_row["mean_dd"]  * 100
    delta_arr_s  =  snow_row["mean_arr"] - normal_row["mean_arr"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

    # --- Panel 1: delay_delta (Akkumulationsrate) ---
    bars1 = ax1.bar(labels, dd_vals, color=bar_colors, width=0.45,
                    edgecolor="white", linewidth=0.5)
    for bar, val in zip(bars1, dd_vals):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 0.05,
                 f"{val:.2f} s", ha="center", va="bottom",
                 fontsize=11, fontweight="bold")
    ax1.annotate(
        f"+{delta_dd_pct:.0f} %",
        xy=(1, snow_row["mean_dd"]),
        xytext=(1.38, (dd_vals[0] + dd_vals[1]) / 2),
        fontsize=13, color="#2166ac", fontweight="bold", va="center",
        arrowprops=dict(arrowstyle="->", color="#2166ac", lw=1.0),
    )
    ax1.set_ylabel("Avg. delay_delta (s / Stop)", **style["label"])
    ax1.set_title("Structural Accumulation Rate\n(delay_delta per Stop)",
                  **TITLE_KW)
    ax1.set_ylim(0, max(dd_vals) * 1.6)
    style_ax(ax1)

    # --- Panel 2: arrival_delay (Fahrgast-Impact) ---
    bars2 = ax2.bar(labels, arr_vals, color=bar_colors, width=0.45,
                    edgecolor="white", linewidth=0.5)
    for bar, val in zip(bars2, arr_vals):
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
                 f"{val:.0f} s", ha="center", va="bottom",
                 fontsize=11, fontweight="bold")
    ax2.annotate(
        f"+{delta_arr_s:.0f} s",
        xy=(1, snow_row["mean_arr"]),
        xytext=(1.38, (arr_vals[0] + arr_vals[1]) / 2),
        fontsize=13, color="#2166ac", fontweight="bold", va="center",
        arrowprops=dict(arrowstyle="->", color="#2166ac", lw=1.0),
    )
    ax2.set_ylabel("Avg. Arrival Delay (s)", **style["label"])
    ax2.set_title("Visible Passenger Impact\n(Arrival Delay)", **TITLE_KW)
    ax2.set_ylim(0, max(arr_vals) * 1.4)
    style_ax(ax2)

    n_snow = int(snow_row["n"])
    n_norm = int(normal_row["n"])
    fig.suptitle(
        f"Snow amplifies structural delay build-up by +{delta_dd_pct:.0f} % "
        f"— passenger impact: +{delta_arr_s:.0f} s",
        fontsize=11, fontweight="bold", x=0.05, ha="left", y=1.02,
    )
    fig.text(
        0.5, -0.03,
        f"Normal days: n={n_norm:,} stops  ·  Snow days: n={n_snow:,} stops  ·  Source: lf_clean",
        ha="center", fontsize=9, color=cfg.ANNO_REF,
    )
    plt.tight_layout()
    if save_as is not None:
        plt.savefig(save_as, dpi=150, bbox_inches="tight")
    plt.show()
