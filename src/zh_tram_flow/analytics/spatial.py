"""Analytics-Modul für 03_analysis_4-spatial.ipynb — Räumliche Verspätungsanalyse.

Added functions:
  plot_stop_dwell_map(lf, line_name="11", cfg=None)
  plot_cascade_effect(lf, cfg=None)
  table_cascade_effect(lf)
"""

import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


_FALLBACK_PALETTE = [
    "#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b2",
    "#937860", "#da8bc3", "#8c8c8c", "#ccb974", "#64b5cd",
    "#2f6690", "#a34b1c", "#2a7a42", "#8a2020", "#4f3f82",
]

# ── District zone classification (consistent across all district plots) ────────
# Zone 0 = Best (white/neutral) · 1 = Mid (yellow) · 2 = Warn (orange) · 3 = Crit (red)
_DISTRICT_ZONE: dict[str, int] = {
    "1": 0, "4": 0, "5": 0, "10": 0,   # Best
    "2": 1, "3": 1, "6": 1,             # Mid
    "7": 2, "9": 2,                     # Warn (default for unclassified)
    "8": 3, "11": 3, "12": 3,           # Crit
}
_DISTRICT_COLORSCALE = [
    [0.000, "#f5f5f5"], [0.249, "#f5f5f5"],
    [0.250, "#fed976"], [0.499, "#fed976"],
    [0.500, "#fd8d3c"], [0.749, "#fd8d3c"],
    [0.750, "#d73027"], [1.000, "#d73027"],
]


def _get_cfg(cfg):
    if cfg is None:
        try:
            from wgnd.core.config import WgndConfig
            cfg = WgndConfig()
        except Exception:
            class _FallbackCfg:
                ANNO_REF = "#888888"
                def palette_n(self, n):
                    return (_FALLBACK_PALETTE * ((n // len(_FALLBACK_PALETTE)) + 1))[:n]
            cfg = _FallbackCfg()
    return cfg


def _load_gtfs_shapes(lines: list[str], year: str = "2025") -> pd.DataFrame:
    """Load GTFS shape coordinates for the dominant route variant per line.

    Uses GTFS shapes parquet files (data/raw/gtfs/) to get the actual track
    geometry — hundreds of intermediate points that follow the real rail geometry,
    not just stop-to-stop straight lines.

    Picks the most-used shape_id per line (direction=1, given year).
    Falls back gracefully to empty DataFrame if GTFS files are missing.

    Returns columns: line_name, lat, lon  (ordered by shape_pt_sequence).
    """
    from zh_tram_flow.config import PATHS

    gtfs_dir = PATHS["raw"] / "gtfs"
    try:
        trips  = pl.read_parquet(gtfs_dir / "gtfs_tram_trips.parquet")
        routes = pl.read_parquet(gtfs_dir / "gtfs_tram_routes.parquet")
        shapes = pl.read_parquet(gtfs_dir / "gtfs_tram_shapes.parquet")
    except FileNotFoundError:
        return pd.DataFrame(columns=["line_name", "lat", "lon"])

    # Dominant shape per line: most trips in `year`, direction=1
    dominant = (
        trips
        .join(routes.select(["route_id", "route_short_name", "year"]),
              on=["route_id", "year"])
        .filter(pl.col("route_short_name").is_in(lines))
        .filter(pl.col("year") == year)
        .filter(pl.col("direction_id") == 1)
        .group_by(["route_short_name", "shape_id"])
        .agg(pl.len().alias("n_trips"))
        .sort("n_trips", descending=True)
        .group_by("route_short_name")
        .agg(pl.col("shape_id").first().alias("shape_id"))
        .rename({"route_short_name": "line_name"})
    )

    return (
        shapes
        .filter(pl.col("year") == year)
        .join(dominant, on="shape_id")
        .sort(["line_name", "shape_pt_sequence"])
        .select(["line_name", "shape_pt_lat", "shape_pt_lon"])
        .rename({"shape_pt_lat": "lat", "shape_pt_lon": "lon"})
        .to_pandas()
    )


def plot_top_delay_stops(lf, cfg=None):
    """Top 20 Haltestellen nach Ø Delay + Top 10 Frühankünfte (Terminus)."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    top_stops = (
        lf
        .group_by(["bpuic", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 5000)
        .sort("avg_delay", descending=True)
        .head(20)
        .collect()
        .to_pandas()
    )

    early_stops = (
        lf
        .group_by(["bpuic", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 5000)
        .sort("avg_delay")
        .head(10)
        .collect()
        .to_pandas()
    )

    style = mpl_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    colors_top = [cfg.COLOR_NEGATIVE if v > top_stops["avg_delay"].mean() * 1.2
                  else cfg.PALETTE_CATEGORICAL[4] for v in top_stops["avg_delay"]]
    ax1.barh(top_stops["stop_name"], top_stops["avg_delay"], color=colors_top, alpha=0.85)
    ax1.axvline(top_stops["avg_delay"].mean(), color=cfg.ANNO_MEAN, lw=1.5, linestyle="--")
    ax1.set_xlabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Top 20 Haltestellen — höchste Verspätung", **style["title"])
    ax1.invert_yaxis()
    ax1.spines[["top", "right"]].set_visible(False)

    ax2.barh(early_stops["stop_name"], early_stops["avg_delay"], color=cfg.COLOR_POSITIVE, alpha=0.85)
    ax2.axvline(0, color=cfg.ANNO_REF, lw=1.5, linestyle=":")
    ax2.set_xlabel("Ø Arrival Delay (s)", **style["label"])
    ax2.set_title("Top 10 Haltestellen — früheste Ankünfte (Terminus)", **style["title"])
    ax2.invert_yaxis()
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()


def table_top_delay_stops(lf) -> pd.DataFrame:
    """Tabelle: Top 10 Haltestellen nach Ø Delay (min. 5000 Beobachtungen — statistically stable)."""
    top_stops = (
        lf
        .group_by(["bpuic", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 5000)
        .sort("avg_delay", descending=True)
        .head(20)
        .collect()
        .to_pandas()
    )
    return (
        top_stops[["stop_name", "avg_delay", "otp_rate", "n"]]
        .rename(columns={"stop_name": "Halt", "avg_delay": "Ø Delay (s)", "otp_rate": "OTP", "n": "n Stops"})
        .head(10)
        .round(1)
    )


def plot_lines_density_vs_delay(lf, cfg=None):
    """Linien-Dichte vs. Verspätung — Scatter + Top 15 nach Linienanzahl."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    lines_per_stop = (
        lf
        .group_by(["bpuic", "stop_name"])
        .agg([
            pl.col("line_name").n_unique().alias("n_lines"),
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 500)
        .sort("n_lines", descending=True)
        .collect()
        .to_pandas()
    )

    top_by_lines = set(lines_per_stop.nlargest(20, "n_lines")["stop_name"])
    top_by_delay = set(lines_per_stop.nlargest(20, "avg_delay")["stop_name"])
    overlap = top_by_lines & top_by_delay

    style = mpl_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    color_scatter = [cfg.COLOR_NEGATIVE if s in overlap
                     else cfg.PALETTE_CATEGORICAL[4] for s in lines_per_stop["stop_name"]]
    ax1.scatter(lines_per_stop["n_lines"], lines_per_stop["avg_delay"],
                s=lines_per_stop["n"] / 800, alpha=0.45, c=color_scatter)
    overlap_df = lines_per_stop[lines_per_stop["stop_name"].isin(overlap)]
    ax1.scatter(overlap_df["n_lines"], overlap_df["avg_delay"],
                s=overlap_df["n"] / 800, alpha=0.9, color=cfg.COLOR_NEGATIVE,
                label="In beiden Top-20 (Linien + Delay)", zorder=5)
    for _, r in overlap_df.iterrows():
        ax1.annotate(r["stop_name"], (r["n_lines"], r["avg_delay"]),
                     fontsize=7, ha="left", va="bottom",
                     xytext=(4, 3), textcoords="offset points")
    ax1.axhline(lines_per_stop["avg_delay"].mean(), color=cfg.ANNO_MEAN,
                lw=1.5, linestyle="--", alpha=0.8, label="Ø Delay")
    ax1.set_xlabel("Anzahl Linien an dieser Haltestelle", **style["label"])
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Linienanzahl vs. Verspätung — alle Haltestellen", **style["title"])
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    top15 = lines_per_stop.nlargest(15, "n_lines").sort_values("n_lines")
    avg_delay_net = lines_per_stop["avg_delay"].mean()
    bar_colors = [cfg.COLOR_NEGATIVE if s in overlap else cfg.PALETTE_CATEGORICAL[4]
                  for s in top15["stop_name"]]
    bars = ax2.barh(top15["stop_name"], top15["n_lines"], color=bar_colors, alpha=0.85)
    for bar, delay in zip(bars, top15["avg_delay"]):
        text_color = cfg.COLOR_NEGATIVE if delay > avg_delay_net * 1.1 else "#555555"
        ax2.text(bar.get_width() + 0.05,
                 bar.get_y() + bar.get_height() / 2,
                 f"Ø {delay:.0f}s", va="center", fontsize=8, color=text_color)
    ax2.set_xlabel("Anzahl Linien", **style["label"])
    ax2.set_title("Top 15 nach Linienanzahl — mit Ø Delay", **style["title"])
    ax2.spines[["top", "right"]].set_visible(False)

    print(f"Haltestellen in BEIDEN Top-20 (viele Linien + hoher Delay): {len(overlap)}")
    for s in sorted(overlap):
        r = lines_per_stop[lines_per_stop["stop_name"] == s].iloc[0]
        print(f"  {s}: {r['n_lines']:.0f} Linien, Ø {r['avg_delay']:.1f}s")

    plt.tight_layout()
    plt.show()


def table_lines_density_vs_delay(lf) -> pd.DataFrame:
    """Tabelle: Top 15 Haltestellen nach Linienanzahl mit Ø Delay."""
    lines_per_stop = (
        lf
        .group_by(["bpuic", "stop_name"])
        .agg([
            pl.col("line_name").n_unique().alias("n_lines"),
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 500)
        .sort("n_lines", descending=True)
        .collect()
        .to_pandas()
    )
    return (
        lines_per_stop.nlargest(15, "n_lines")[["stop_name", "n_lines", "avg_delay", "n"]]
        .rename(columns={"stop_name": "Haltestelle", "n_lines": "Linien", "avg_delay": "Ø Delay (s)", "n": "N Obs"})
        .round({"Ø Delay (s)": 1})
        .reset_index(drop=True)
    )


def plot_start_stop_diagnosis(lf, cfg=None):
    """Starthaltestellen-Diagnose: Frühankunft vs. Delta — Kandidaten identifizieren."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    early_detail = (
        lf
        .group_by(["bpuic", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_arr"),
            pl.col("departure_delay").mean().alias("avg_dep"),
            pl.col("delay_delta").mean().alias("avg_delta"),
            pl.col("arrival_delay").quantile(0.1).alias("q10_arr"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 500)
        .sort("avg_arr")
        .head(30)
        .collect()
        .to_pandas()
    )

    THRESH_ARR = -30
    THRESH_DELTA = 20
    early_detail["is_start_stop"] = (
        (early_detail["avg_arr"] < THRESH_ARR) &
        (early_detail["avg_delta"] > THRESH_DELTA)
    )

    n_start = early_detail["is_start_stop"].sum()
    start_candidates = early_detail[early_detail["is_start_stop"]]["stop_name"].tolist()

    mean_all = lf.select(pl.col("arrival_delay").mean()).collect().item()
    mean_excl = (lf
                 .filter(~pl.col("stop_name").is_in(start_candidates))
                 .select(pl.col("arrival_delay").mean())
                 .collect().item())

    style = mpl_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    colors_sc = [cfg.COLOR_NEGATIVE if s else cfg.PALETTE_CATEGORICAL[4]
                 for s in early_detail["is_start_stop"]]
    ax1.scatter(early_detail["avg_arr"], early_detail["avg_delta"],
                s=early_detail["n"] / 300, alpha=0.75, c=colors_sc)
    for _, r in early_detail[early_detail["is_start_stop"]].iterrows():
        ax1.annotate(r["stop_name"], (r["avg_arr"], r["avg_delta"]),
                     fontsize=7, ha="right", va="bottom",
                     xytext=(-4, 3), textcoords="offset points")
    ax1.axvline(THRESH_ARR, color=cfg.ANNO_REF, lw=1.2, linestyle=":", alpha=0.7,
                label=f"arr < {THRESH_ARR}s")
    ax1.axhline(THRESH_DELTA, color=cfg.ANNO_REF, lw=1.2, linestyle=":", alpha=0.7,
                label=f"delta > {THRESH_DELTA}s")
    ax1.axvline(0, color=cfg.CHART_AXIS, lw=0.8, alpha=0.4)
    ax1.axhline(0, color=cfg.CHART_AXIS, lw=0.8, alpha=0.4)
    ax1.set_xlabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_ylabel("Ø Delay Delta (s)", **style["label"])
    ax1.set_title("Frühankunft vs. Delta — Starthaltestellen als Cluster", **style["title"])
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    bar_colors = [cfg.COLOR_NEGATIVE if s else cfg.PALETTE_CATEGORICAL[4]
                  for s in early_detail.sort_values("avg_arr")["is_start_stop"]]
    bars = ax2.barh(early_detail.sort_values("avg_arr")["stop_name"],
                    early_detail.sort_values("avg_arr")["avg_arr"],
                    color=bar_colors, alpha=0.85)
    ax2.axvline(0, color=cfg.ANNO_REF, lw=1.2, linestyle=":")
    ax2.set_xlabel("Ø Arrival Delay (s)", **style["label"])
    ax2.set_title(f"Top 30 Frühankunfts-Haltestellen\nOrange = Starthaltestellen-Kandidaten (n={n_start})",
                  **style["title"])
    ax2.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()

    print(f"Gesamtstatistik:")
    print(f"  Ø arrival_delay ALLE Halte:                 {mean_all:+.1f}s")
    print(f"  Ø arrival_delay OHNE {n_start} Starthaltestellen:  {mean_excl:+.1f}s")
    print(f"  Verzerrung durch Starthaltestellen:          {mean_excl - mean_all:+.1f}s")
    print(f"\nStarthaltestellen-Kandidaten ({n_start} Stück):")
    for s in start_candidates:
        r = early_detail[early_detail["stop_name"] == s].iloc[0]
        print(f"  {s}: Ø arr={r['avg_arr']:.0f}s, delta={r['avg_delta']:.0f}s")



def table_start_stop_candidates(lf) -> pd.DataFrame:
    """Tabelle: Starthaltestellen-Kandidaten (frühe Ankunft + positives Delta)."""
    early_detail = (
        lf
        .group_by(["bpuic", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_arr"),
            pl.col("departure_delay").mean().alias("avg_dep"),
            pl.col("delay_delta").mean().alias("avg_delta"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 500)
        .sort("avg_arr")
        .head(30)
        .collect()
        .to_pandas()
    )
    early_detail["is_start_stop"] = (
        (early_detail["avg_arr"] < -30) &
        (early_detail["avg_delta"] > 20)
    )
    return (
        early_detail[early_detail["is_start_stop"]][
            ["stop_name", "avg_arr", "avg_dep", "avg_delta", "n"]
        ]
        .rename(columns={"stop_name": "Halt", "avg_arr": "Ø Arr", "avg_dep": "Ø Dep",
                          "avg_delta": "Ø Delta", "n": "n"})
        .round(1)
    )


def plot_district_analysis(lf, cfg=None):
    """Verspätung und OTP nach Stadtkreis — zwei Panels."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    districts = (
        lf
        .group_by(["district_nr", "district_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("avg_delay", descending=True)
        .collect()
        .to_pandas()
    )

    # Zone colors — pastel / dezent, consistent across district plots
    _zone_color = {
        "1": "#e0e0e0", "4": "#e0e0e0", "5": "#e0e0e0", "10": "#e0e0e0",  # Best  (light gray)
        "2": "#fde68a", "3": "#fde68a", "6": "#fde68a",                     # Mid   (soft yellow)
        "7": "#fed7aa", "9": "#fed7aa",                                      # Warn  (soft peach)
        "8": "#fca5a5", "11": "#fca5a5", "12": "#fca5a5",                   # Crit  (soft red)
    }
    colors = [_zone_color.get(str(int(nr)), "#fed7aa")
              for nr in districts["district_nr"]]

    style = mpl_style()
    avg = districts["avg_delay"].mean()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    ax1.bar(districts["district_name"], districts["avg_delay"], color=colors, alpha=0.6,
            edgecolor="#bbbbbb", linewidth=0.5)
    ax1.axhline(avg, color=cfg.ANNO_MEAN, lw=1.0, linestyle=":", label=f"Ø {avg:.1f}s")
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Verspätung nach Stadtkreis", **style["title"])
    ax1.tick_params(axis="x", rotation=45)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.legend(fontsize=9, frameon=False, loc="upper right")

    ax2.bar(districts["district_name"], districts["otp_rate"], color=colors, alpha=0.6,
            edgecolor="#bbbbbb", linewidth=0.5)
    ax2.axhline(0.85, color=cfg.ANNO_REF, lw=1.0, linestyle="--", label="85%-Ziel")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax2.set_ylabel("OTP Rate", **style["label"])
    ax2.set_title("OTP nach Stadtkreis", **style["title"])
    ax2.tick_params(axis="x", rotation=45)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.legend(fontsize=9, frameon=False, loc="upper right")

    plt.tight_layout()
    plt.show()


def plot_district_combined(lf, cfg=None):
    """Verspätung nach Stadtkreis — ein Panel mit OTP als zweite Achse.

    Balken: Ø Arrival Delay (s), Zonenfarben, alpha=0.6.
    Linie (rechte Achse): OTP (%) — teal, gestrichelt.
    Durchschnittslinie auf linker Achse.
    """
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from matplotlib.transforms import blended_transform_factory

    districts = (
        lf
        .group_by(["district_nr", "district_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("avg_delay", descending=True)
        .collect()
        .to_pandas()
    )

    _zone_color = {
        "1": "#e0e0e0", "4": "#e0e0e0", "5": "#e0e0e0", "10": "#e0e0e0",  # Best
        "2": "#fde68a", "3": "#fde68a", "6": "#fde68a",                     # Mid
        "7": "#fed7aa", "9": "#fed7aa",                                      # Warn
        "8": "#fca5a5", "11": "#fca5a5", "12": "#fca5a5",                   # Crit
    }
    colors = [_zone_color.get(str(int(nr)), "#fed7aa") for nr in districts["district_nr"]]

    style = mpl_style()
    avg = districts["avg_delay"].mean()
    x = range(len(districts))

    fig, ax = plt.subplots(figsize=(14, 5))

    ax.bar(districts["district_name"], districts["avg_delay"],
           color=colors, alpha=0.6, edgecolor="#bbbbbb", linewidth=0.5)

    ax.axhline(avg, color=cfg.ANNO_MEAN, lw=1.0, linestyle=":")
    _t = blended_transform_factory(ax.transAxes, ax.transData)
    ax.text(0.99, avg, f"Ø {avg:.1f}s ", va="bottom", ha="right",
            fontsize=8, color=cfg.ANNO_MEAN, transform=_t)

    ax.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax.set_title("Verspätung nach Stadtkreis", **style["title"])
    ax.tick_params(axis="x", rotation=45)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

    _teal = cfg.COLOR_POSITIVE
    ax_r = ax.twinx()
    otp_pct = districts["otp_rate"] * 100
    ax_r.plot(districts["district_name"], otp_pct,
              color=_teal, lw=1.5, linestyle="--",
              marker="o", markersize=4, label="OTP (%)")
    ax_r.set_ylabel("OTP (%)", fontsize=10, color=_teal)
    ax_r.tick_params(axis="y", colors=_teal, labelsize=9)
    ax_r.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax_r.spines["top"].set_visible(False)
    ax_r.spines["left"].set_visible(False)

    h, l = ax_r.get_legend_handles_labels()
    ax.legend(h, l, fontsize=9, frameon=False, loc="upper right")

    plt.tight_layout()
    plt.show()


def table_district_analysis(lf) -> pd.DataFrame:
    """Tabelle: Verspätung und OTP nach Stadtkreis."""
    districts = (
        lf
        .group_by(["district_nr", "district_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("avg_delay", descending=True)
        .collect()
        .to_pandas()
    )
    return (
        districts.sort_values("avg_delay", ascending=False)[
            ["district_name", "avg_delay", "otp_rate", "n"]
        ]
        .rename(columns={"district_name": "Kreis", "avg_delay": "Ø Delay", "otp_rate": "OTP", "n": "n Stops"})
        .round(2)
    )


def plot_line_analysis(lf, cfg=None):
    """Linien-Profil: Arrival Delay / OTP / Delay Delta nach Linie — drei Panels."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.config import line_color

    lines = (
        lf
        .group_by("line_name")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            pl.col("departure_delay").mean().alias("dep_mean"),
            pl.col("delay_delta").mean().alias("delta_mean"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("avg_delay", descending=True)
        .collect()
        .to_pandas()
    )
    lines["line_name_str"] = lines["line_name"].astype(str)
    lc = [line_color(str(ln)) for ln in lines["line_name"]]

    style = mpl_style()
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].barh(lines["line_name_str"], lines["avg_delay"], color=lc, alpha=0.85)
    axes[0].axvline(lines["avg_delay"].mean(), color=cfg.ANNO_MEAN, lw=1.5, linestyle="--")
    axes[0].set_xlabel("Ø Arrival Delay (s)", **style["label"])
    axes[0].set_title("Ø Arrival Delay nach Linie", **style["title"])
    axes[0].invert_yaxis()
    axes[0].spines[["top", "right"]].set_visible(False)

    otp_colors = [cfg.COLOR_POSITIVE if v >= 0.87 else cfg.COLOR_NEGATIVE for v in lines["otp_rate"]]
    axes[1].barh(lines["line_name_str"], lines["otp_rate"], color=otp_colors, alpha=0.85)
    axes[1].axvline(0.85, color=cfg.ANNO_REF, lw=1, linestyle=":", label="85%-Ziel")
    axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    axes[1].set_xlabel("OTP Rate", **style["label"])
    axes[1].set_title("OTP nach Linie", **style["title"])
    axes[1].invert_yaxis()
    axes[1].set_yticklabels([])
    axes[1].legend(fontsize=9)
    axes[1].spines[["top", "right"]].set_visible(False)

    delta_colors = [cfg.COLOR_NEGATIVE if v > 0 else cfg.COLOR_POSITIVE for v in lines["delta_mean"]]
    axes[2].barh(lines["line_name_str"], lines["delta_mean"], color=delta_colors, alpha=0.85)
    axes[2].axvline(0, color=cfg.ANNO_REF, lw=1.5, linestyle=":")
    axes[2].set_xlabel("Ø Delay Delta (s)", **style["label"])
    axes[2].set_title("Delay Delta — baut Linie auf oder ab?", **style["title"])
    axes[2].invert_yaxis()
    axes[2].set_yticklabels([])
    axes[2].spines[["top", "right"]].set_visible(False)

    plt.suptitle("Linien-Profil: Arrival Delay · OTP · Delta", fontsize=12, color=cfg.CHART_TITLE)
    plt.tight_layout()
    plt.show()


def table_line_analysis(lf) -> pd.DataFrame:
    """Tabelle: Ø Delay / OTP / Delta nach Linie."""
    lines = (
        lf
        .group_by("line_name")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            pl.col("departure_delay").mean().alias("dep_mean"),
            pl.col("delay_delta").mean().alias("delta_mean"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .sort("avg_delay", descending=True)
        .collect()
        .to_pandas()
    )
    lines["line_name_str"] = lines["line_name"].astype(str)
    return (
        lines[["line_name_str", "avg_delay", "otp_rate", "delta_mean", "n"]]
        .rename(columns={"line_name_str": "Linie", "avg_delay": "Ø Delay", "otp_rate": "OTP",
                          "delta_mean": "Ø Delta", "n": "n"})
        .round(2)
    )


def plot_dwell_time(lf, cfg=None):
    """Feature dwell_time: Verteilung / Delay-Korrelation / nach Linie — drei Panels."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.config import line_color

    _schema = lf.collect_schema()
    if "dwell_time" in _schema:
        dwell_col = pl.col("dwell_time")
        print("dwell_time aus Feature-File geladen")
    else:
        dwell_col = (
            (pl.col("departure_schedule") - pl.col("arrival_schedule"))
            .dt.total_seconds()
            .cast(pl.Int32)
        )
        print("ℹ  dwell_time wird inline aus departure_schedule − arrival_schedule berechnet")

    dwell_dist = (
        lf
        .with_columns(dwell_col.alias("dwell_time"))
        .filter(pl.col("dwell_time").is_between(0, 120))
        .group_by("dwell_time")
        .agg(pl.len().alias("n"))
        .sort("dwell_time")
        .collect()
        .to_pandas()
    )

    dwell_vs_delay = (
        lf
        .with_columns(dwell_col.alias("dwell_time"))
        .filter(pl.col("dwell_time").is_between(0, 120))
        .group_by("dwell_time")
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 1000)
        .sort("dwell_time")
        .collect()
        .to_pandas()
    )

    dwell_by_line = (
        lf
        .with_columns(dwell_col.alias("dwell_time"))
        .filter(pl.col("dwell_time").is_between(0, 120))
        .group_by("line_name")
        .agg([
            pl.col("dwell_time").mean().alias("avg_dwell"),
            pl.col("dwell_time").median().alias("med_dwell"),
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .sort("avg_dwell")
        .collect()
        .to_pandas()
    )

    style = mpl_style()
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].bar(dwell_dist["dwell_time"], dwell_dist["n"] / 1e6,
                color=cfg.PALETTE_CATEGORICAL[4], alpha=0.75, width=1)
    axes[0].axvline(dwell_dist.assign(w=dwell_dist["dwell_time"] * dwell_dist["n"])["w"].sum() / dwell_dist["n"].sum(),
                    color=cfg.ANNO_MEAN, lw=2, linestyle="--", label="Ø dwell_time")
    axes[0].set_xlabel("Geplante Haltezeit (s)", **style["label"])
    axes[0].set_ylabel("Halt-Ereignisse (Mio.)", **style["label"])
    axes[0].set_title("Verteilung dwell_time", **style["title"])
    axes[0].legend(fontsize=9)
    axes[0].spines[["top", "right"]].set_visible(False)

    scatter_colors = [cfg.COLOR_NEGATIVE if d > dwell_vs_delay["avg_delay"].mean() * 1.1
                      else cfg.COLOR_POSITIVE if d < dwell_vs_delay["avg_delay"].mean() * 0.9
                      else cfg.PALETTE_CATEGORICAL[4] for d in dwell_vs_delay["avg_delay"]]
    axes[1].scatter(dwell_vs_delay["dwell_time"], dwell_vs_delay["avg_delay"],
                    s=dwell_vs_delay["n"] / 3000, alpha=0.5, c=scatter_colors)
    axes[1].axhline(dwell_vs_delay["avg_delay"].mean(), color=cfg.ANNO_MEAN,
                    lw=1.5, linestyle="--", alpha=0.7)
    axes[1].set_xlabel("Geplante Haltezeit (s)", **style["label"])
    axes[1].set_ylabel("Ø Arrival Delay (s)", **style["label"])
    axes[1].set_title("dwell_time vs. Verspätung", **style["title"])
    axes[1].spines[["top", "right"]].set_visible(False)

    dbl = dwell_by_line.sort_values("avg_dwell")
    lc_dwell = [line_color(str(ln)) for ln in dbl["line_name"]]
    axes[2].barh(dbl["line_name"].astype(str), dbl["avg_dwell"], color=lc_dwell, alpha=0.85)
    for i, (dwell, delay) in enumerate(zip(dbl["avg_dwell"], dbl["avg_delay"])):
        axes[2].text(dwell + 0.2, i, f"Ø delay {delay:.0f}s", va="center", fontsize=8)
    axes[2].set_xlabel("Ø dwell_time (s)", **style["label"])
    axes[2].set_title("Ø Haltezeit nach Linie", **style["title"])
    axes[2].spines[["top", "right"]].set_visible(False)

    plt.suptitle("Feature dwell_time — Haltezeit als Puffer-Indikator", fontsize=11, color=cfg.CHART_TITLE)
    plt.tight_layout()
    plt.show()

    avg_dwell = (dwell_dist["dwell_time"] * dwell_dist["n"]).sum() / dwell_dist["n"].sum()
    print(f"Ø dwell_time netzweit: {avg_dwell:.1f}s")
    print(f"Anteil mit dwell_time ≤ 20s: {(dwell_dist[dwell_dist['dwell_time'] <= 20]['n'].sum() / dwell_dist['n'].sum()):.1%}")
    print(f"Anteil mit dwell_time = 0s:  {(dwell_dist[dwell_dist['dwell_time'] == 0]['n'].sum() / dwell_dist['n'].sum()):.1%}")



def table_dwell_time_by_line(lf) -> pd.DataFrame:
    """Tabelle: Ø dwell_time + Ø Delay nach Linie."""
    _schema = lf.collect_schema()
    if "dwell_time" in _schema:
        dwell_col = pl.col("dwell_time")
    else:
        dwell_col = (
            (pl.col("departure_schedule") - pl.col("arrival_schedule"))
            .dt.total_seconds()
            .cast(pl.Int32)
        )

    dwell_by_line = (
        lf
        .with_columns(dwell_col.alias("dwell_time"))
        .filter(pl.col("dwell_time").is_between(0, 120))
        .group_by("line_name")
        .agg([
            pl.col("dwell_time").mean().alias("avg_dwell"),
            pl.col("dwell_time").median().alias("med_dwell"),
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.len().alias("n"),
        ])
        .sort("avg_dwell")
        .collect()
        .to_pandas()
    )
    return (
        dwell_by_line.rename(columns={
            "line_name": "Linie", "avg_dwell": "Ø Haltezeit (s)", "med_dwell": "Median Haltezeit (s)",
            "avg_delay": "Ø Arr Delay (s)", "n": "N Halte"
        })
        .assign(**{"N Halte": lambda df: df["N Halte"].apply(lambda x: f"{x:,.0f}")})
        .round({"Ø Haltezeit (s)": 1, "Median Haltezeit (s)": 1, "Ø Arr Delay (s)": 1})
        .set_index("Linie")
    )


# ---------------------------------------------------------------------------
# Stop Delay Map
# ---------------------------------------------------------------------------

def plot_stop_delay_map(lf: pl.LazyFrame, min_n: int = 5000) -> None:
    """Plotly Mapbox: stops colored by avg arrival_delay. Choropleth districts underneath."""
    import plotly.graph_objects as go
    import json
    from pathlib import Path

    geojson_path = Path(__file__).parents[3] / "data" / "raw" / "stadtkreise.geojson"
    with open(geojson_path) as f:
        geojson = json.load(f)

    all_stops_raw = (
        lf.filter(pl.col("canceled") == False)
        .group_by(["stop_name", "bpuic"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp"),
            pl.col("stop_lat").mean(),
            pl.col("stop_lon").mean(),
            pl.col("district_nr").mode().first().alias("district_nr"),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )
    all_stops = all_stops_raw.copy()
    stops = all_stops_raw[all_stops_raw["n"] >= min_n].copy()
    stops["avg_delay"] = stops["avg_delay"].round(1)
    stops["otp_pct"] = (stops["otp"] * 100).round(1)

    vmin = stops["avg_delay"].quantile(0.05)
    vmax = stops["avg_delay"].quantile(0.95)
    bubble_size = (stops["avg_delay"] / stops["avg_delay"].max() * 20).clip(lower=4)

    # District delay values — same YlOrRd scale as stop bubbles
    district_df = (
        lf.filter(pl.col("canceled") == False)
        .group_by("district_nr")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .collect()
        .to_pandas()
        .dropna()
    )
    district_df["district_nr"] = district_df["district_nr"].astype(str)
    d_delay_map = dict(zip(district_df["district_nr"], district_df["avg_delay"]))

    # K-label centroids + ordered delay values per GeoJSON feature
    kreis_ids = [str(feat["properties"]["objid"]) for feat in geojson["features"]]
    kreis_delays = [d_delay_map.get(kid, 0.0) for kid in kreis_ids]
    label_lats, label_lons, label_texts = [], [], []
    for feat in geojson["features"]:
        coords = np.array(feat["geometry"]["coordinates"][0])
        label_lats.append(float(coords[:, 1].mean()))
        label_lons.append(float(coords[:, 0].mean()))
        label_texts.append(f"K{feat['properties']['objid']}")

    fig = go.Figure()

    # Layer 1: District choropleth — YlOrRd by delay, grouped with K-labels
    # showlegend=False here; the K-label trace (Layer 4) carries the legend entry
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=kreis_ids,
        z=kreis_delays,
        featureidkey="properties.objid",
        colorscale="YlOrRd",
        zmin=vmin, zmax=vmax,
        showscale=False,
        legendgroup="Stadtkreise",
        showlegend=False,
        marker=dict(line=dict(color="#888888", width=1.5), opacity=0.55),
        hovertemplate="<b>Kreis %{location}</b><br>Ø Delay: %{z:.1f}s<extra></extra>",
        name="Stadtkreise",
    ))

    # Layer 2: All stops as gray dots (network skeleton)
    fig.add_trace(go.Scattermapbox(
        lat=all_stops["stop_lat"],
        lon=all_stops["stop_lon"],
        mode="markers",
        marker=dict(size=5, color="#666666", opacity=0.55),
        text=all_stops["stop_name"].str.replace("Zürich, ", ""),
        hovertemplate="<b>%{text}</b><extra></extra>",
        name="Alle Haltestellen",
    ))

    # Layer 3: Highlighted stops — bubbles sized and colored by delay
    fig.add_trace(go.Scattermapbox(
        lat=stops["stop_lat"],
        lon=stops["stop_lon"],
        mode="markers",
        marker=dict(
            size=bubble_size,
            color=stops["avg_delay"],
            colorscale="YlOrRd",
            cmin=vmin, cmax=vmax,
            colorbar=dict(title="Ø Delay (s)", thickness=12, len=0.6),
            opacity=0.85,
        ),
        text=stops["stop_name"].str.replace("Zürich, ", ""),
        customdata=stops[["avg_delay", "otp_pct", "n"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Ø Delay: %{customdata[0]:.1f}s<br>"
            "OTP: %{customdata[1]:.1f}%<br>"
            "N: %{customdata[2]:,.0f}<extra></extra>"
        ),
        name="HS Verspätungen",
    ))

    # Layer 4: K-labels — same legendgroup as choropleth → one click toggles both
    fig.add_trace(go.Scattermapbox(
        lat=label_lats,
        lon=label_lons,
        mode="text",
        text=label_texts,
        textfont=dict(size=11, color="#444444"),
        hoverinfo="skip",
        legendgroup="Stadtkreise",
        showlegend=True,
        name="Stadtkreise",
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": 47.378, "lon": 8.540},
        mapbox_zoom=11.5,
        margin=dict(l=0, r=0, t=30, b=0),
        height=600,
        title=dict(text="Haltestellen nach Ø Arrival Delay", x=0, xanchor="left"),
    )
    fig.show()


def table_stop_delay_map(lf: pl.LazyFrame, top_n: int = 20, min_n: int = 5000) -> pd.DataFrame:
    """Top stops by avg delay with location info."""
    return (
        lf.filter(pl.col("canceled") == False)
        .group_by(["stop_name", "district_nr"])
        .agg([
            pl.col("arrival_delay").mean().alias("Ø Delay (s)"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("OTP"),
            pl.len().alias("N"),
        ])
        .collect()
        .to_pandas()
        .pipe(lambda df: df[df["N"] >= min_n])
        .nlargest(top_n, "Ø Delay (s)")
        .assign(**{
            "Ø Delay (s)": lambda df: df["Ø Delay (s)"].round(1),
            "OTP": lambda df: (df["OTP"] * 100).round(1).astype(str) + "%",
            "N": lambda df: df["N"].apply(lambda x: f"{x:,.0f}"),
        })
        .rename(columns={"stop_name": "Haltestelle", "district_nr": "Kreis"})
        .reset_index(drop=True)
        .assign(Rang=lambda df: range(1, len(df) + 1))
        [["Rang", "Haltestelle", "Kreis", "Ø Delay (s)", "OTP", "N"]]
        .set_index("Rang")
    )


# ---------------------------------------------------------------------------
# Line Delay Map
# ---------------------------------------------------------------------------

def plot_line_delay_map(lf: pl.LazyFrame, cfg=None, min_n: int = 5000) -> None:
    """Plotly Mapbox: stops per line colored by wgnd palette, gray background for all stops."""
    import plotly.graph_objects as go
    cfg = _get_cfg(cfg)

    all_stops = (
        lf.filter(pl.col("canceled") == False)
        .group_by(["stop_name"])
        .agg([
            pl.col("stop_lat").mean(),
            pl.col("stop_lon").mean(),
        ])
        .collect()
        .to_pandas()
    )

    stops = (
        lf.filter(pl.col("canceled") == False)
        .group_by(["line_name", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("stop_lat").mean(),
            pl.col("stop_lon").mean(),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )
    stops = stops[stops["n"] >= min_n].copy()
    stops["avg_delay"] = stops["avg_delay"].round(1)

    line_avg = (
        stops.groupby("line_name", observed=True)["avg_delay"].mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    n_lines = len(line_avg)
    import plotly.colors as pc
    _base = pc.qualitative.Plotly + pc.qualitative.Safe
    palette = [_base[i % len(_base)] for i in range(n_lines)]

    fig = go.Figure()

    # Gray background: full network skeleton
    fig.add_trace(go.Scattermapbox(
        lat=all_stops["stop_lat"],
        lon=all_stops["stop_lon"],
        mode="markers",
        marker=dict(size=5, color="#aaaaaa", opacity=0.35),
        text=all_stops["stop_name"].str.replace("Zürich, ", ""),
        hovertemplate="<b>%{text}</b><extra></extra>",
        name="Alle Haltestellen",
    ))

    for i, line in enumerate(line_avg):
        df = stops[stops["line_name"] == line]
        color = palette[i]
        bubble = (df["avg_delay"] / stops["avg_delay"].max() * 18).clip(lower=4)
        fig.add_trace(go.Scattermapbox(
            lat=df["stop_lat"],
            lon=df["stop_lon"],
            mode="markers",
            marker=dict(size=bubble, color=color, opacity=0.85),
            text=df["stop_name"].str.replace("Zürich, ", ""),
            customdata=df[["avg_delay", "n"]].values,
            hovertemplate=(
                f"<b>Linie {line}</b> — %{{text}}<br>"
                "Ø Delay: %{customdata[0]:.1f}s<br>"
                "N: %{customdata[1]:,.0f}<extra></extra>"
            ),
            name=f"L{line}",
        ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": 47.378, "lon": 8.540},
        mapbox_zoom=11.5,
        margin=dict(l=0, r=0, t=30, b=0),
        height=620,
        title=dict(text="Linien-Haltestellen nach Ø Delay (Linien einzeln an/abwählbar)", x=0, xanchor="left"),
        legend=dict(orientation="v", x=1.0, y=1.0),
    )
    fig.show()


# ---------------------------------------------------------------------------
# Line × Hour Heatmap
# ---------------------------------------------------------------------------

def plot_line_hour_heatmap(lf: pl.LazyFrame, cfg=None) -> None:
    """Heatmap: Linie × Stunde — Ø arrival_delay. Zeigt wann welche Linie am stärksten leidet."""
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)
    style = mpl_style()

    df = (
        lf.filter(pl.col("canceled") == False)
        .with_columns(pl.col("arrival_schedule").dt.hour().alias("hour"))
        .group_by(["line_name", "hour"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .collect()
        .to_pandas()
    )

    pivot = (
        df.pivot(index="line_name", columns="hour", values="avg_delay")
        .reindex(columns=range(24))
    )
    line_order = pivot.mean(axis=1).sort_values(ascending=False).index
    pivot = pivot.loc[line_order]

    fig, ax = plt.subplots(figsize=(16, 6))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(pivot)))
    ax.set_yticklabels([f"L{l}" for l in pivot.index], fontsize=9)
    ax.set_xlabel("Uhrzeit", **style["label"])
    ax.set_ylabel("Linie", **style["label"])
    ax.set_title("Ø Arrival Delay nach Linie und Stunde", **style["title"])

    cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    cbar.set_label("Ø Delay (s)", fontsize=9)
    plt.tight_layout()
    plt.show()


def table_line_hour_heatmap(lf: pl.LazyFrame) -> pd.DataFrame:
    """Peak-Stunde und Ø Delay pro Linie."""
    df = (
        lf.filter(pl.col("canceled") == False)
        .with_columns(pl.col("arrival_schedule").dt.hour().alias("hour"))
        .group_by(["line_name", "hour"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .collect()
        .to_pandas()
    )
    pivot = df.pivot(index="line_name", columns="hour", values="avg_delay").reindex(columns=range(24))
    result = pd.DataFrame({
        "Ø Delay gesamt (s)": pivot.mean(axis=1).round(1),
        "Peak-Stunde": pivot.idxmax(axis=1).apply(lambda h: f"{int(h):02d}:00"),
        "Peak-Delay (s)": pivot.max(axis=1).round(1),
        "Nacht-Min (s)": pivot[[0, 1, 2, 3, 4]].min(axis=1).round(1),
    })
    return (
        result.sort_values("Ø Delay gesamt (s)", ascending=False)
        .rename_axis("Linie")
    )


# ---------------------------------------------------------------------------
# Direction Map — delay per stop split by trip direction
# ---------------------------------------------------------------------------

def plot_stop_delay_by_direction(lf: pl.LazyFrame, line_name: str, min_n: int = 200) -> None:
    """Two Plotly maps side by side: same line, opposite directions, stops colored by delay."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    lf_line = lf.filter(
        (pl.col("canceled") == False) & (pl.col("line_name") == line_name)
    )

    # Compute last stop per trip = direction indicator
    terminus = (
        lf_line
        .group_by("trip_id")
        .agg(
            pl.col("stop_name").sort_by("stop_sequence").last().alias("terminus")
        )
    )

    df = (
        lf_line
        .join(terminus, on="trip_id")
        .group_by(["terminus", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("stop_lat").mean(),
            pl.col("stop_lon").mean(),
            pl.len().alias("n"),
        ])
        .collect()
        .to_pandas()
    )
    df = df[df["n"] >= min_n].copy()
    df["avg_delay"] = df["avg_delay"].round(1)

    directions = df["terminus"].value_counts().nlargest(2).index.tolist()
    if len(directions) < 2:
        print(f"Linie {line_name}: weniger als 2 Richtungen gefunden.")
        return

    vmin = df["avg_delay"].quantile(0.05)
    vmax = df["avg_delay"].quantile(0.95)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f"→ {directions[0].replace('Zürich, ', '')}",
            f"→ {directions[1].replace('Zürich, ', '')}",
        ],
        specs=[[{"type": "mapbox"}, {"type": "mapbox"}]],
        horizontal_spacing=0.02,
    )

    for col, terminus in enumerate(directions, start=1):
        sub = df[df["terminus"] == terminus]
        bubble = (sub["avg_delay"] / df["avg_delay"].max() * 20).clip(lower=5)
        fig.add_trace(go.Scattermapbox(
            lat=sub["stop_lat"],
            lon=sub["stop_lon"],
            mode="markers",
            marker=dict(
                size=bubble,
                color=sub["avg_delay"],
                colorscale="YlOrRd",
                cmin=vmin, cmax=vmax,
                colorbar=dict(title="Ø Delay (s)", thickness=10, len=0.5, x=1.01) if col == 2 else None,
                showscale=(col == 2),
            ),
            text=sub["stop_name"].str.replace("Zürich, ", ""),
            customdata=sub[["avg_delay", "n"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Ø Delay: %{customdata[0]:.1f}s<br>"
                "N: %{customdata[1]:,.0f}<extra></extra>"
            ),
            name=f"→ {terminus.replace('Zürich, ', '')}",
        ), row=1, col=col)

    center = {"lat": df["stop_lat"].mean(), "lon": df["stop_lon"].mean()}
    for col in [1, 2]:
        fig.update_layout(**{
            f"mapbox{'' if col == 1 else col}_style": "carto-positron",
            f"mapbox{'' if col == 1 else col}_center": center,
            f"mapbox{'' if col == 1 else col}_zoom": 12,
        })

    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(text=f"Linie {line_name} — Ø Delay nach Fahrtrichtung", x=0, xanchor="left"),
    )
    fig.show()


# ---------------------------------------------------------------------------
# Dwell-Linienkarte
# ---------------------------------------------------------------------------

def _year_vis(selected_yr: str, N: int) -> list:
    """Visibility list for 6N traces (3 route groups + 3 bubble groups).

    Trace layout for N lines:
      [0..N-1]   j23 routes  — showlegend=False, no legendgroup
      [N..2N-1]  j24 routes  — showlegend=False, no legendgroup
      [2N..3N-1] j25 routes  — showlegend=False, legendgroup="L{line}"
      [3N..4N-1] j23 bubbles — showlegend=False, no legendgroup
      [4N..5N-1] j24 bubbles — showlegend=False, no legendgroup
      [5N..6N-1] j25 bubbles — showlegend=True,  legendgroup="L{line}" ← legend anchor

    j25 bubbles use "legendonly" when a non-2025 year is active so the
    legend stays fully visible and clickable for the "Alle aus → select
    individual line" workflow.
    """
    yr_idx = {"2023": 0, "2024": 1, "2025": 2}[selected_yr]

    route_vis: list = [False] * (3 * N)
    for i in range(N):
        route_vis[yr_idx * N + i] = True

    bubble_vis: list = [False] * (3 * N)
    for i in range(N):
        bubble_vis[yr_idx * N + i] = True
    if selected_yr != "2025":
        for i in range(N):
            bubble_vis[2 * N + i] = "legendonly"   # keep j25 legend entries visible

    return route_vis + bubble_vis


def _make_vis_year_buttons(N: int) -> list:
    """Year selector buttons using pure visibility toggling.

    Buttons: 2023 · 2024 · 2025 · Alle Jahre.
    "Alle Jahre": all 3 route sets visible simultaneously + j25 bubbles.
    active=2 (2025) should be set in the updatemenus dict.
    """
    alle_vis = [True] * (3 * N) + [False] * N + [False] * N + [True] * N
    buttons = []
    for yr in ["2023", "2024", "2025"]:
        buttons.append(dict(
            label=yr,
            method="restyle",
            args=[{"visible": _year_vis(yr, N)}],
        ))
    buttons.append(dict(
        label="Alle Jahre",
        method="restyle",
        args=[{"visible": alle_vis}],
    ))
    return buttons


def plot_line_delay_profile_map(
    lf: pl.LazyFrame,
    lines: list | None = None,
    min_n: int = 1000,
    cfg=None,
) -> None:
    """Interaktive Plotly-Karte: Delay-Profil aller (oder ausgewählter) Tramlinien.

    Jede Linie = VBZ-Linienfarbe, GTFS-Gleisgeometrie als Route, Haltestellen als Bubbles.
    Bubble-Größe: Ø Arrival Delay (power-skaliert — kleiner Delay = sehr kleiner Bubble).

    Verhalten (identisch zur HTML-Karte):
      - Legende-Klick: schaltet eine Linie (Route + Bubbles) ein/aus — togglet true ↔ legendonly
      - "Alle aus": alle Traces auf legendonly → Legende bleibt nutzbar
      - "Alle ein": alle Traces auf true (sichtbar)
      - Jahr-Schalter: tauscht Route-Geometrie + Haltestellenpositionen via restyle —
        verändert NICHT welche Linien sichtbar sind

    Trace-Layout (2N total):
      [0..N-1]   Route-Traces  — showlegend=False, legendgroup="L{line}"
      [N..2N-1]  Bubble-Traces — showlegend=True,  legendgroup="L{line}"

    Jahr-Daten stecken in den Button-args (restyle lat/lon/size) — keine extra Traces.
    min_n gesamt; per-year threshold = min_n // 3.
    Input: lf_clean.
    """
    import plotly.graph_objects as go
    from zh_tram_flow.config import line_color as _lc
    cfg = _get_cfg(cfg)

    lf_base = (
        lf.filter(pl.col("canceled") == False)
          .with_columns(
              pl.col("line_name").cast(pl.Utf8),
              ((pl.col("departure_schedule") - pl.col("arrival_schedule"))
               .dt.total_seconds().cast(pl.Int32)).alias("dwell_time"),
          )
    )

    if lines is None:
        avail = (
            lf_base.select(pl.col("line_name").unique())
                   .collect()["line_name"].to_list()
        )
        def _sort_key(x):
            return (0, int(x)) if x.isdigit() else (1, x)
        lines = sorted(avail, key=_sort_key)
    else:
        lines = [str(l) for l in lines]

    N = len(lines)
    min_n_yr = max(1, min_n // 3)  # per-year threshold: data spread over ~3 years

    # ── Per-year stop aggregation ────────────────────────────────────────────
    stops_by_year: dict[str, pd.DataFrame] = {}
    for yr in ["2023", "2024", "2025"]:
        yr_df = (
            lf_base
            .filter(pl.col("line_name").is_in(lines))
            .filter(pl.col("operating_date").dt.year() == int(yr))
            .group_by(["line_name", "stop_name"])
            .agg([
                pl.col("dwell_time").eq(0).cast(pl.Float64).mean().alias("pct_dw0"),
                pl.col("arrival_delay").mean().alias("mean_delay"),
                pl.col("stop_lat").mean(),
                pl.col("stop_lon").mean(),
                pl.len().alias("n"),
            ])
            .filter(pl.col("n") >= min_n_yr)
            .collect()
            .to_pandas()
        )
        # Display filter: show only stops that represent the main service of a line.
        #
        # Some VBZ tram lines operate rare route variants beyond their primary terminus
        # (e.g. L2 extended via Tunnelstrasse → Museum Rietberg → Wollishofen). These
        # variant stops are real, correctly attributed trips — the master file is accurate
        # and reflects exactly what VBZ delivered. This is NOT a data quality problem and
        # should NOT be fixed in cleaning.
        #
        # The issue is visual: variant stops appear at < 1 % of main-route frequency and
        # make the map look tangled. The 5 %-of-line-max threshold hides them so the map
        # shows representative service only — matching the primary-shape view of the HTML
        # reference map (tram_lines_map.html). This is a display decision, not a
        # data correction. → documented in 02_preparation.ipynb (Bereinigungsstrategie)
        if not yr_df.empty:
            max_n_per_line = yr_df.groupby("line_name", observed=True)["n"].transform("max")
            yr_df = yr_df[yr_df["n"] >= max_n_per_line * 0.05].copy()
        yr_df["pct_dw0_pct"] = (yr_df["pct_dw0"] * 100).round(1)
        yr_df["mean_delay_r"] = yr_df["mean_delay"].round(1)
        yr_df["stop_short"] = yr_df["stop_name"].str.replace("Zürich, ", "", regex=False)
        stops_by_year[yr] = yr_df

    # Global bubble normalisation across all years for consistent scale
    all_delays = pd.concat([df["mean_delay"] for df in stops_by_year.values()])
    d_min, d_max = float(all_delays.min()), float(all_delays.max())
    for yr in stops_by_year:
        norm = (stops_by_year[yr]["mean_delay"] - d_min) / (d_max - d_min + 1e-9)
        stops_by_year[yr]["bubble"] = 2 + (norm ** 1.7) * 22  # power-scaled, range 2–24 px

    # GTFS shapes per year
    shapes_by_year = {yr: _load_gtfs_shapes(lines, year=yr) for yr in ["2023", "2024", "2025"]}

    stops_25 = stops_by_year["2025"]
    center_lat = float(stops_25["stop_lat"].mean()) if not stops_25.empty else 47.378
    center_lon = float(stops_25["stop_lon"].mean()) if not stops_25.empty else 8.540

    fig = go.Figure()

    # ── Route traces [0..N-1]: initialized with 2025 geometry ────────────────
    shapes_25 = shapes_by_year["2025"]
    for line in lines:
        color = _lc(line)
        sub = shapes_25[shapes_25["line_name"] == line]
        fig.add_trace(go.Scattermapbox(
            lat=sub["lat"].tolist() if not sub.empty else [None],
            lon=sub["lon"].tolist() if not sub.empty else [None],
            mode="lines",
            line=dict(color=color, width=2),
            opacity=0.45,
            showlegend=False,
            legendgroup=f"L{line}",
            hoverinfo="skip",
            name=f"L{line} Route",
        ))

    # ── Bubble traces [N..2N-1]: initialized with 2025 stop data ─────────────
    for line in lines:
        color = _lc(line)
        sub = stops_25[stops_25["line_name"] == line]
        if sub.empty:
            fig.add_trace(go.Scattermapbox(
                lat=[], lon=[], mode="markers",
                legendgroup=f"L{line}", showlegend=True, name=f"L{line}",
            ))
            continue
        fig.add_trace(go.Scattermapbox(
            lat=sub["stop_lat"].tolist(),
            lon=sub["stop_lon"].tolist(),
            mode="markers",
            marker=dict(size=sub["bubble"].tolist(), color=color, opacity=0.85),
            text=sub["stop_short"].tolist(),
            customdata=sub[["mean_delay_r", "pct_dw0_pct", "n"]].values,
            hovertemplate=(
                f"<b>L{line}: %{{text}}</b><br>"
                "Ø Arrival Delay: <b>%{customdata[0]:.0f} s</b><br>"
                "Kein Puffer: <b>%{customdata[1]:.0f} %</b><br>"
                "N: %{customdata[2]:,.0f}<extra></extra>"
            ),
            name=f"L{line}",
            legendgroup=f"L{line}",
            showlegend=True,
        ))

    # ── Jahr-Buttons: restyle lat/lon/size, Sichtbarkeit bleibt erhalten ──────
    # Plotly-Verhalten: restyle aktualisiert nur die angegebenen Properties —
    # visible-Zustand (true/legendonly) der Traces wird NICHT verändert.
    def _build_restyle(yr_key: str) -> dict:
        """Restyle-Args für ein bestimmtes Jahr: Routen-Geometrie + Haltestellen-Daten."""
        shp = shapes_by_year[yr_key]
        stp = stops_by_year[yr_key]
        r_lats, r_lons = [], []
        b_lats, b_lons, b_texts, b_data, b_sizes = [], [], [], [], []
        for line in lines:
            s = shp[shp["line_name"] == line]
            r_lats.append(s["lat"].tolist() if not s.empty else [None])
            r_lons.append(s["lon"].tolist() if not s.empty else [None])
        for line in lines:
            b = stp[stp["line_name"] == line]
            if b.empty:
                b_lats.append([]); b_lons.append([]); b_texts.append([])
                b_data.append([]); b_sizes.append([])
            else:
                b_lats.append(b["stop_lat"].tolist())
                b_lons.append(b["stop_lon"].tolist())
                b_texts.append(b["stop_short"].tolist())
                b_data.append(b[["mean_delay_r", "pct_dw0_pct", "n"]].values.tolist())
                b_sizes.append(b["bubble"].tolist())
        # None in Restyle-Liste = "diesen Trace nicht anfassen" → Route-Traces
        # bekommen kein marker.size-Update (sie haben mode="lines").
        return {
            "lat":         r_lats  + b_lats,
            "lon":         r_lons  + b_lons,
            "text":        [None]*N + b_texts,
            "customdata":  [None]*N + b_data,
            "marker.size": [None]*N + b_sizes,
        }

    def _build_restyle_alle() -> dict:
        """Alle Jahre: alle 3 Routen-Geometrien mit None-Trennern + 2025-Haltestellen."""
        combined_lats, combined_lons = [], []
        for line in lines:
            lats, lons = [], []
            for yr in ["2023", "2024", "2025"]:
                s = shapes_by_year[yr][shapes_by_year[yr]["line_name"] == line]
                if not s.empty:
                    if lats: lats.append(None); lons.append(None)
                    lats.extend(s["lat"].tolist()); lons.extend(s["lon"].tolist())
            combined_lats.append(lats or [None])
            combined_lons.append(lons or [None])
        b_lats, b_lons, b_texts, b_data, b_sizes = [], [], [], [], []
        for line in lines:
            b = stops_25[stops_25["line_name"] == line]
            if b.empty:
                b_lats.append([]); b_lons.append([]); b_texts.append([])
                b_data.append([]); b_sizes.append([])
            else:
                b_lats.append(b["stop_lat"].tolist())
                b_lons.append(b["stop_lon"].tolist())
                b_texts.append(b["stop_short"].tolist())
                b_data.append(b[["mean_delay_r", "pct_dw0_pct", "n"]].values.tolist())
                b_sizes.append(b["bubble"].tolist())
        return {
            "lat":         combined_lats + b_lats,
            "lon":         combined_lons + b_lons,
            "text":        [None]*N + b_texts,
            "customdata":  [None]*N + b_data,
            "marker.size": [None]*N + b_sizes,
        }

    year_buttons = [
        dict(label=yr, method="restyle", args=[_build_restyle(yr)])
        for yr in ["2023", "2024", "2025"]
    ]
    year_buttons.append(dict(label="Alle Jahre", method="restyle", args=[_build_restyle_alle()]))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=11.5,
        ),
        updatemenus=[
            dict(
                type="buttons",
                active=1,
                buttons=[
                    dict(
                        label="Alle aus",
                        method="restyle",
                        args=[{"visible": ["legendonly"] * (2 * N)}],
                    ),
                    dict(
                        label="Alle ein",
                        method="restyle",
                        args=[{"visible": [True] * (2 * N)}],
                    ),
                ],
                x=0.0, y=1.0, xanchor="left", yanchor="bottom",
                bgcolor="white", bordercolor="#bbbbbb", borderwidth=1,
                font=dict(size=12),
                pad=dict(r=4, t=4, b=4, l=4),
            ),
            dict(
                type="buttons",
                active=2,
                buttons=year_buttons,
                x=0.24, y=1.0, xanchor="left", yanchor="bottom",
                bgcolor="white", bordercolor="#bbbbbb", borderwidth=1,
                font=dict(size=12),
                direction="right",
                pad=dict(r=4, t=4, b=4, l=4),
            ),
        ],
        legend=dict(
            title="<b>Linie</b><br><sup>Klick = ein/aus</sup>",
            orientation="v",
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#dddddd",
            borderwidth=1,
            x=1.01, xanchor="left",
            y=1.0, yanchor="top",
        ),
        margin=dict(l=0, r=10, t=80, b=0),
        height=720,
        title=dict(
            text=(
                "Delay-Profil je Haltestelle — alle Tramlinien<br>"
                "<sup>Bubble-Größe: Ø Arrival Delay (power-skaliert)"
                "  ·  Farbe: VBZ-Linienfarbe"
                "  ·  Linien über Legende ein-/ausblenden</sup>"
            ),
            x=0, xanchor="left",
        ),
    )
    fig.show()


def plot_line_dwell_profile_map(
    lf: pl.LazyFrame,
    lines: list | None = None,
    min_n: int = 1000,
    cfg=None,
) -> None:
    """Interaktive Plotly-Karte: Dwell Time-Profil aller (oder ausgewählter) Tramlinien.

    Companion-Karte zu plot_line_delay_profile_map — gleiche Struktur, anderes Signal.
    Farbe: Ø scheduled Dwell Time — Rot = 0 s (kein Puffer) · Grün = ≥ 30 s (guter Puffer).
    Bubble-Größe: einheitlich (Signal liegt in der Farbe, nicht der Größe).

    Verhalten identisch zur Delay-Karte:
      - Legende-Klick: schaltet eine Linie ein/aus (true ↔ legendonly)
      - "Alle aus" / "Alle ein" via Buttons
      - Jahr-Schalter: tauscht Route-Geometrie + Haltestellen-Farben via restyle,
        verändert NICHT welche Linien sichtbar sind

    Trace-Layout (2N total):
      [0..N-1]   Route-Traces  — showlegend=False, legendgroup="L{line}"
      [N..2N-1]  Bubble-Traces — showlegend=True,  legendgroup="L{line}"

    min_n gesamt; per-year threshold = min_n // 3.
    Input: lf_clean.
    """
    import plotly.graph_objects as go
    from zh_tram_flow.config import line_color as _lc
    cfg = _get_cfg(cfg)

    lf_base = (
        lf.filter(pl.col("canceled") == False)
          .with_columns(
              pl.col("line_name").cast(pl.Utf8),
              ((pl.col("departure_schedule") - pl.col("arrival_schedule"))
               .dt.total_seconds().cast(pl.Float64)).alias("dwell_time"),
          )
    )

    if lines is None:
        avail = (
            lf_base.select(pl.col("line_name").unique())
                   .collect()["line_name"].to_list()
        )
        def _sort_key(x):
            return (0, int(x)) if x.isdigit() else (1, x)
        lines = sorted(avail, key=_sort_key)
    else:
        lines = [str(l) for l in lines]

    N = len(lines)
    min_n_yr = max(1, min_n // 3)

    # ── Per-year stop aggregation ────────────────────────────────────────────
    stops_by_year: dict[str, pd.DataFrame] = {}
    for yr in ["2023", "2024", "2025"]:
        yr_df = (
            lf_base
            .filter(pl.col("line_name").is_in(lines))
            .filter(pl.col("operating_date").dt.year() == int(yr))
            .group_by(["line_name", "stop_name"])
            .agg([
                pl.col("dwell_time").mean().alias("mean_dwell"),
                pl.col("stop_lat").mean(),
                pl.col("stop_lon").mean(),
                pl.len().alias("n"),
            ])
            .filter(pl.col("n") >= min_n_yr)
            .collect()
            .to_pandas()
        )
        # Display filter — same rationale as plot_line_delay_profile_map:
        # VBZ route variants (real, correctly attributed trips) appear at < 1 % of
        # main-route frequency and make the map look tangled. The 5 %-of-line-max
        # threshold hides them for visual clarity. NOT a data correction — the master
        # file is correct. → documented in 02_preparation.ipynb (Bereinigungsstrategie)
        if not yr_df.empty:
            max_n_per_line = yr_df.groupby("line_name", observed=True)["n"].transform("max")
            yr_df = yr_df[yr_df["n"] >= max_n_per_line * 0.05].copy()
        yr_df["mean_dwell_r"] = yr_df["mean_dwell"].round(1)
        yr_df["stop_short"] = yr_df["stop_name"].str.replace("Zürich, ", "", regex=False)
        stops_by_year[yr] = yr_df

    shapes_by_year = {yr: _load_gtfs_shapes(lines, year=yr) for yr in ["2023", "2024", "2025"]}

    stops_25 = stops_by_year["2025"]
    center_lat = float(stops_25["stop_lat"].mean()) if not stops_25.empty else 47.378
    center_lon = float(stops_25["stop_lon"].mean()) if not stops_25.empty else 8.540

    _dwell_colorscale = [[0.0, "#de425b"], [0.4, "#ffa600"], [1.0, "#25ac82"]]
    _cmin, _cmax = 0, 30
    _colorbar_cfg = dict(
        title="Ø Dwell (s)",
        thickness=14, len=0.55, x=1.02,
        tickvals=[0, 15, 30],
        ticktext=["0 s", "15 s", "≥ 30 s"],
    )

    fig = go.Figure()

    # ── Route traces [0..N-1]: initialized with 2025 geometry ────────────────
    shapes_25 = shapes_by_year["2025"]
    for line in lines:
        color = _lc(line)
        sub = shapes_25[shapes_25["line_name"] == line]
        fig.add_trace(go.Scattermapbox(
            lat=sub["lat"].tolist() if not sub.empty else [None],
            lon=sub["lon"].tolist() if not sub.empty else [None],
            mode="lines",
            line=dict(color=color, width=2),
            opacity=0.35,
            showlegend=False,
            legendgroup=f"L{line}",
            hoverinfo="skip",
            name=f"L{line} Route",
        ))

    # ── Bubble traces [N..2N-1]: initialized with 2025 stop data ─────────────
    _show_colorbar = True
    for line in lines:
        sub = stops_25[stops_25["line_name"] == line]
        if sub.empty:
            fig.add_trace(go.Scattermapbox(
                lat=[], lon=[], mode="markers",
                legendgroup=f"L{line}", showlegend=True, name=f"L{line}",
            ))
            continue
        fig.add_trace(go.Scattermapbox(
            lat=sub["stop_lat"].tolist(),
            lon=sub["stop_lon"].tolist(),
            mode="markers",
            marker=dict(
                size=12,
                color=sub["mean_dwell_r"].tolist(),
                colorscale=_dwell_colorscale,
                cmin=_cmin, cmax=_cmax,
                showscale=_show_colorbar,
                colorbar=_colorbar_cfg if _show_colorbar else None,
                opacity=0.88,
            ),
            text=sub["stop_short"].tolist(),
            customdata=sub[["mean_dwell_r", "n"]].values,
            hovertemplate=(
                f"<b>L{line}: %{{text}}</b><br>"
                "Ø Dwell Time: <b>%{customdata[0]:.0f} s</b><br>"
                "N: %{customdata[1]:,.0f}<extra></extra>"
            ),
            name=f"L{line}",
            legendgroup=f"L{line}",
            showlegend=True,
        ))
        _show_colorbar = False  # colorbar only on first non-empty bubble trace

    # ── Jahr-Buttons: restyle Route-Geometrie + Haltestellen-Farben ──────────
    def _build_restyle_dwell(yr_key: str) -> dict:
        shp = shapes_by_year[yr_key]
        stp = stops_by_year[yr_key]
        r_lats, r_lons = [], []
        b_lats, b_lons, b_texts, b_data, b_colors = [], [], [], [], []
        for line in lines:
            s = shp[shp["line_name"] == line]
            r_lats.append(s["lat"].tolist() if not s.empty else [None])
            r_lons.append(s["lon"].tolist() if not s.empty else [None])
        for line in lines:
            b = stp[stp["line_name"] == line]
            if b.empty:
                b_lats.append([]); b_lons.append([]); b_texts.append([])
                b_data.append([]); b_colors.append([])
            else:
                b_lats.append(b["stop_lat"].tolist())
                b_lons.append(b["stop_lon"].tolist())
                b_texts.append(b["stop_short"].tolist())
                b_data.append(b[["mean_dwell_r", "n"]].values.tolist())
                b_colors.append(b["mean_dwell_r"].tolist())
        return {
            "lat":           r_lats  + b_lats,
            "lon":           r_lons  + b_lons,
            "text":          [None]*N + b_texts,
            "customdata":    [None]*N + b_data,
            "marker.color":  [None]*N + b_colors,
        }

    def _build_restyle_dwell_alle() -> dict:
        combined_lats, combined_lons = [], []
        for line in lines:
            lats, lons = [], []
            for yr in ["2023", "2024", "2025"]:
                s = shapes_by_year[yr][shapes_by_year[yr]["line_name"] == line]
                if not s.empty:
                    if lats: lats.append(None); lons.append(None)
                    lats.extend(s["lat"].tolist()); lons.extend(s["lon"].tolist())
            combined_lats.append(lats or [None])
            combined_lons.append(lons or [None])
        b_lats, b_lons, b_texts, b_data, b_colors = [], [], [], [], []
        for line in lines:
            b = stops_25[stops_25["line_name"] == line]
            if b.empty:
                b_lats.append([]); b_lons.append([]); b_texts.append([])
                b_data.append([]); b_colors.append([])
            else:
                b_lats.append(b["stop_lat"].tolist())
                b_lons.append(b["stop_lon"].tolist())
                b_texts.append(b["stop_short"].tolist())
                b_data.append(b[["mean_dwell_r", "n"]].values.tolist())
                b_colors.append(b["mean_dwell_r"].tolist())
        return {
            "lat":           combined_lats + b_lats,
            "lon":           combined_lons + b_lons,
            "text":          [None]*N + b_texts,
            "customdata":    [None]*N + b_data,
            "marker.color":  [None]*N + b_colors,
        }

    year_buttons = [
        dict(label=yr, method="restyle", args=[_build_restyle_dwell(yr)])
        for yr in ["2023", "2024", "2025"]
    ]
    year_buttons.append(dict(label="Alle Jahre", method="restyle", args=[_build_restyle_dwell_alle()]))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=11.5,
        ),
        updatemenus=[
            dict(
                type="buttons",
                active=1,
                buttons=[
                    dict(
                        label="Alle aus",
                        method="restyle",
                        args=[{"visible": ["legendonly"] * (2 * N)}],
                    ),
                    dict(
                        label="Alle ein",
                        method="restyle",
                        args=[{"visible": [True] * (2 * N)}],
                    ),
                ],
                x=0.0, y=1.0, xanchor="left", yanchor="bottom",
                bgcolor="white", bordercolor="#bbbbbb", borderwidth=1,
                font=dict(size=12),
                pad=dict(r=4, t=4, b=4, l=4),
            ),
            dict(
                type="buttons",
                active=2,
                buttons=year_buttons,
                x=0.24, y=1.0, xanchor="left", yanchor="bottom",
                bgcolor="white", bordercolor="#bbbbbb", borderwidth=1,
                font=dict(size=12),
                direction="right",
                pad=dict(r=4, t=4, b=4, l=4),
            ),
        ],
        legend=dict(
            title="<b>Linie</b><br><sup>Klick = ein/aus</sup>",
            orientation="v",
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#dddddd",
            borderwidth=1,
            x=1.12, xanchor="left",
            y=1.0, yanchor="top",
        ),
        margin=dict(l=0, r=140, t=80, b=0),
        height=720,
        title=dict(
            text=(
                "Dwell Time je Haltestelle — alle Tramlinien<br>"
                "<sup>Farbe: Rot = kein Puffer (0 s) · Grün = guter Puffer (≥ 30 s)"
                "  ·  Größe: einheitlich  ·  Linien über Legende ein-/ausblenden</sup>"
            ),
            x=0, xanchor="left",
        ),
    )
    fig.show()


def plot_stop_dwell_map(lf: pl.LazyFrame, line_name: str = "11", min_n: int = 2000, cfg=None) -> None:
    """Plotly Mapbox: Delay-Profil einer einzelnen Linie.

    Farbe: Ø Arrival Delay (Grün = pünktlich · Rot = verspätet)
    Größe: proportional zu pct_dw0 (% Halte ohne Puffer)

    min_n=2000 filtert Baustellen-Kurzläufer-Endhalte heraus (L6 hat ~230 Varianten).
    Input: lf_clean. line_name als String (z.B. "11", "6").
    """
    import plotly.graph_objects as go
    cfg = _get_cfg(cfg)

    lf_line = (
        lf.filter(pl.col("canceled") == False)
          .filter(pl.col("line_name").cast(pl.Utf8) == line_name)
          .with_columns(
              ((pl.col("departure_schedule") - pl.col("arrival_schedule"))
               .dt.total_seconds().cast(pl.Int32)).alias("dwell_time")
          )
    )

    stops = (
        lf_line
        .group_by("stop_name")
        .agg([
            pl.col("dwell_time").eq(0).cast(pl.Float64).mean().alias("pct_dw0"),
            pl.col("arrival_delay").mean().alias("mean_delay"),
            pl.col("stop_lat").mean(),
            pl.col("stop_lon").mean(),
            pl.col("stop_sequence").mean().alias("mean_seq"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= min_n)
        .sort("mean_seq")
        .collect()
        .to_pandas()
    )

    stops["pct_dw0_pct"] = (stops["pct_dw0"] * 100).round(1)
    stops["mean_delay_r"] = stops["mean_delay"].round(1)
    stops["stop_short"] = stops["stop_name"].str.replace("Zürich, ", "", regex=False)

    # Bubble size: proportional to pct_dw0 (kein Puffer = groß)
    p_min, p_max = stops["pct_dw0"].min(), stops["pct_dw0"].max()
    stops["bubble"] = 8 + (stops["pct_dw0"] - p_min) / (p_max - p_min + 1e-9) * 16

    fig = go.Figure()

    # Haltestellen: Farbe = mean_delay, Größe = pct_dw0
    # Keine Route-Linie: group_by(stop_name) mittelt über beide Fahrtrichtungen,
    # dadurch wäre die Sortierung falsch und die Linie würde kreuz und quer verlaufen.
    fig.add_trace(go.Scattermapbox(
        lat=stops["stop_lat"], lon=stops["stop_lon"],
        mode="markers",
        marker=dict(
            size=stops["bubble"],
            color=stops["mean_delay_r"],
            colorscale=[[0.0, "#25ac82"], [0.5, "#ffa600"], [1.0, "#de425b"]],
            cmin=30, cmax=100,
            colorbar=dict(
                title="Ø Arrival<br>Delay (s)",
                thickness=12, len=0.55,
                tickvals=[30, 60, 100],
                ticktext=["30 s", "60 s", "100 s"],
            ),
            opacity=0.88,
        ),
        text=stops["stop_short"],
        customdata=stops[["mean_delay_r", "pct_dw0_pct", "n"]].values,
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Ø Arrival Delay: <b>%{customdata[0]:.0f} s</b><br>"
            "Kein Puffer (pct_dw0): <b>%{customdata[1]:.0f} %</b><br>"
            "N Beobachtungen: %{customdata[2]:,}<extra></extra>"
        ),
        name=f"Linie {line_name}",
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(
                lat=float(stops["stop_lat"].mean()),
                lon=float(stops["stop_lon"].mean()),
            ),
            zoom=12,
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=620,
        title=dict(
            text=(
                f"Linie {line_name} — Ø Arrival Delay pro Haltestelle<br>"
                "<sup>Farbe: Grün = pünktlich · Rot = verspätet"
                "  ·  Größe: % Halte ohne Puffer (pct_dw0)</sup>"
            ),
            x=0, xanchor="left",
        ),
    )
    fig.show()


# ---------------------------------------------------------------------------
# Kaskadeneffekt
# ---------------------------------------------------------------------------

def plot_cascade_effect(lf: pl.LazyFrame, cfg=None) -> None:
    """Kaskadeneffekt: Pearson-r zwischen delay(Halt n) und delay(Halt n+1) je Linie.

    Misst wie stark sich Verspätung innerhalb einer Fahrt von Halt zu Halt überträgt.
      r → 1.0: Delay kaskadiert vollständig — kein Selbstheilungseffekt.
      r → 0.0: Verspätungen sind unabhängig — Netz erholt sich.

    Farb-Kodierung:
      Rot   (r ≥ 0.85): starke Kaskade
      Amber (r ≥ 0.70): mittlere Kaskade
      Teal  (r < 0.70): gute Erholung

    Input: lf_clean (benötigt trip_id, operating_date, stop_sequence, arrival_delay).
    """
    from wgnd.core.theme import mpl_style
    cfg = _get_cfg(cfg)
    style = mpl_style()

    # Polars: sort innerhalb jedes Trips nach stop_sequence, dann shift(1).over()
    cascade = (
        lf.filter(pl.col("canceled") == False)
          .filter(pl.col("arrival_delay").is_not_null())
          .sort(["trip_id", "operating_date", "stop_sequence"])
          .with_columns(
              pl.col("arrival_delay")
                .shift(1)
                .over(["trip_id", "operating_date"])
                .alias("prev_stop_delay")
          )
          .filter(pl.col("prev_stop_delay").is_not_null())
          .group_by("line_name")
          .agg([
              pl.corr("arrival_delay", "prev_stop_delay").alias("cascade_r"),
              pl.len().alias("n"),
          ])
          .sort("cascade_r", descending=True)
          .collect(engine="streaming")
          .to_pandas()
    )
    cascade["line_name"] = cascade["line_name"].astype(str)

    def _color(r):
        if r >= 0.85: return cfg.COLOR_NEGATIVE
        if r >= 0.70: return cfg.COLOR_SIGNAL
        return cfg.COLOR_POSITIVE

    colors = [_color(r) for r in cascade["cascade_r"]]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(
        cascade["line_name"], cascade["cascade_r"],
        color=colors, edgecolor="white", linewidth=0.5,
    )
    for bar, r in zip(bars, cascade["cascade_r"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
            f"{r:.2f}", ha="center", va="bottom", fontsize=8,
            color=cfg.CHART_AXIS_TEXT,
        )

    ax.axhline(0.85, color=cfg.COLOR_NEGATIVE, lw=1.2, ls="--", alpha=0.6,
               label="Stark (≥ 0.85) — kein Selbstheilungseffekt")
    ax.axhline(0.70, color=cfg.COLOR_SIGNAL,   lw=1.2, ls="--", alpha=0.6,
               label="Mittel (≥ 0.70)")
    ax.set_ylim(0, 1.08)
    ax.set_xlabel("Linie", **style["label"])
    ax.set_ylabel("Kaskadenkoeffizient (Pearson r)", **style["label"])
    ax.set_title(
        "Kaskadeneffekt — Delay-Übertragung von Halt zu Halt je Linie\n"
        "r → 1 = Verspätung kaskadiert vollständig  ·  r → 0 = Netz erholt sich",
        **style["title"],
    )
    ax.legend(fontsize=9, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
    ax.tick_params(colors=cfg.CHART_AXIS_TEXT, labelsize=9)
    plt.tight_layout()
    plt.show()


def table_cascade_effect(lf: pl.LazyFrame) -> pd.DataFrame:
    """Kaskadenkoeffizient (Pearson r) + N Beobachtungen je Linie, sortiert absteigend."""
    cascade = (
        lf.filter(pl.col("canceled") == False)
          .filter(pl.col("arrival_delay").is_not_null())
          .sort(["trip_id", "operating_date", "stop_sequence"])
          .with_columns(
              pl.col("arrival_delay")
                .shift(1)
                .over(["trip_id", "operating_date"])
                .alias("prev_stop_delay")
          )
          .filter(pl.col("prev_stop_delay").is_not_null())
          .group_by("line_name")
          .agg([
              pl.corr("arrival_delay", "prev_stop_delay").alias("cascade_r"),
              pl.len().alias("n"),
          ])
          .sort("cascade_r", descending=True)
          .collect(engine="streaming")
          .to_pandas()
    )
    cascade["line_name"] = cascade["line_name"].astype(str)
    cascade["n_fmt"] = cascade["n"].apply(lambda x: f"{x:,.0f}")
    cascade["Stärke"] = cascade["cascade_r"].apply(
        lambda r: "🔴 Stark" if r >= 0.85 else "🟡 Mittel" if r >= 0.70 else "🟢 Gut"
    )
    return (
        cascade[["line_name", "cascade_r", "n_fmt", "Stärke"]]
        .rename(columns={"line_name": "Linie", "cascade_r": "Pearson r", "n_fmt": "N Halte"})
        .round({"Pearson r": 3})
        .reset_index(drop=True)
    )


def table_stop_delay_by_direction(lf: pl.LazyFrame, line_name: str, min_n: int = 200) -> pd.DataFrame:
    """Top stops by delay per direction for a given line."""
    lf_line = lf.filter(
        (pl.col("canceled") == False) & (pl.col("line_name") == line_name)
    )
    terminus = (
        lf_line
        .group_by("trip_id")
        .agg(pl.col("stop_name").sort_by("stop_sequence").last().alias("terminus"))
    )
    df = (
        lf_line
        .join(terminus, on="trip_id")
        .group_by(["terminus", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("Ø Delay (s)"),
            pl.col("stop_sequence").mean().alias("Ø Stop-Seq"),
            pl.len().alias("N"),
        ])
        .collect()
        .to_pandas()
    )
    df = df[df["N"] >= min_n].copy()
    directions = df["terminus"].value_counts().nlargest(2).index.tolist()

    frames = []
    for d in directions:
        sub = (
            df[df["terminus"] == d]
            .nlargest(10, "Ø Delay (s)")
            [["stop_name", "Ø Delay (s)", "Ø Stop-Seq", "N"]]
            .assign(**{"Richtung": d.replace("Zürich, ", "")})
            .rename(columns={"stop_name": "Haltestelle"})
            .reset_index(drop=True)
        )
        sub.index += 1
        frames.append(sub)

    result = pd.concat(frames).reset_index(drop=True)
    return result[["Richtung", "Haltestelle", "Ø Delay (s)", "Ø Stop-Seq", "N"]]
