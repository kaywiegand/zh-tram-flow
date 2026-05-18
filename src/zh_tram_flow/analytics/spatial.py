"""Analytics-Modul für 03_analysis_4-spatial.ipynb — Räumliche Verspätungsanalyse."""

import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def _get_cfg(cfg):
    if cfg is None:
        from zh_tram_flow.notebook import NotebookConfig
        cfg = NotebookConfig()
    return cfg


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
        .filter(pl.col("n") >= 1000)
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
        .filter(pl.col("n") >= 1000)
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
    """Tabelle: Top 10 Haltestellen nach Ø Delay (min. 1000 Beobachtungen)."""
    top_stops = (
        lf
        .group_by(["bpuic", "stop_name"])
        .agg([
            pl.col("arrival_delay").mean().alias("avg_delay"),
            pl.col("arrival_delay").median().alias("med_delay"),
            (pl.col("arrival_delay").abs() <= 120).mean().alias("otp_rate"),
            pl.len().alias("n"),
        ])
        .filter(pl.col("n") >= 1000)
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

    style = mpl_style()
    avg = districts["avg_delay"].mean()
    colors_d = [cfg.COLOR_NEGATIVE if v > avg * 1.1 else cfg.COLOR_POSITIVE if v < avg * 0.9
                else cfg.PALETTE_CATEGORICAL[4] for v in districts["avg_delay"]]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    bars = ax1.bar(districts["district_name"], districts["avg_delay"], color=colors_d, alpha=0.85)
    ax1.axhline(avg, color=cfg.ANNO_MEAN, lw=1.5, linestyle="--", label=f"Ø {avg:.1f}s")
    ax1.set_ylabel("Ø Arrival Delay (s)", **style["label"])
    ax1.set_title("Verspätung nach Stadtkreis", **style["title"])
    ax1.tick_params(axis="x", rotation=45)
    ax1.legend(fontsize=9)
    ax1.spines[["top", "right"]].set_visible(False)

    otp_colors = [cfg.COLOR_POSITIVE if v >= 0.87 else cfg.COLOR_NEGATIVE
                  for v in districts["otp_rate"]]
    ax2.bar(districts["district_name"], districts["otp_rate"], color=otp_colors, alpha=0.85)
    ax2.axhline(0.85, color=cfg.ANNO_REF, lw=1, linestyle=":", label="85%-Ziel")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax2.set_ylabel("OTP Rate", **style["label"])
    ax2.set_title("OTP nach Stadtkreis", **style["title"])
    ax2.tick_params(axis="x", rotation=45)
    ax2.legend(fontsize=9)
    ax2.spines[["top", "right"]].set_visible(False)

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
        print("⚠  dwell_time nicht in Feature-File — wird inline berechnet (02_preparation noch nicht neu ausgeführt)")

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
