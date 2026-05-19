"""Analytics-Modul für 03_analysis_2-network.ipynb — Netzveränderungen 2023–2025."""

import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def _get_cfg(cfg):
    if cfg is None:
        from wgnd.core.config import cfg as _default_cfg
        cfg = _default_cfg
    return cfg


# Offizielle Linienfarben VBZ
LINE_COLORS = {
    "2": "#E20A16", "3": "#00892F", "4": "#11296F", "5": "#734522", "6": "#CA7D3C",
    "7": "#000000", "8": "#8AB51F", "9": "#11296F", "10": "#E12472", "11": "#00892F",
    "12": "#92D6E3", "13": "#FFCC00", "14": "#008DC5", "15": "#E20A16", "17": "#8E224D",
    "18": "#E20A16", "19": "#E20A16", "E": "#E20A16",
}


def get_stops_per_line(year: str, path) -> dict:
    """Gibt pro Linie die repräsentativen Haltestellen-Namen zurück (direction 0)."""
    routes = pd.read_csv(path / "routes.txt", dtype=str)
    trips = pd.read_csv(path / "trips.txt", dtype=str)
    stops = pd.read_csv(path / "stops.txt", dtype=str)
    stops["stop_lat"] = stops["stop_lat"].astype(float)
    stops["stop_lon"] = stops["stop_lon"].astype(float)

    tram_r = routes[
        routes["route_id"].str.startswith("1-") &
        routes["route_short_name"].str.match(r"^\d+$|^E$")
    ][["route_id", "route_short_name"]]

    trips_t = (trips.merge(tram_r, on="route_id")
               [lambda df: df["direction_id"] == "0"]
               [["route_short_name", "shape_id", "trip_id"]])

    rep = (trips_t.groupby(["route_short_name", "shape_id"], observed=True)
           .size().reset_index(name="n")
           .sort_values("n", ascending=False)
           .groupby("route_short_name", observed=True).first().reset_index())

    result = {}
    trip_ids = [trips_t[trips_t["shape_id"] == sid]["trip_id"].iloc[0]
                for sid in rep["shape_id"].tolist()]

    st_df = (pl.scan_csv(str(path / "stop_times.txt"), infer_schema_length=100)
             .filter(pl.col("trip_id").is_in(trip_ids))
             .sort(["trip_id", "stop_sequence"]).collect())

    for _, r in rep.iterrows():
        ln = r["route_short_name"]
        sid = r["shape_id"]
        mask = trips_t["shape_id"] == sid
        if not mask.any():
            continue
        tid = trips_t[mask]["trip_id"].iloc[0]
        stop_ids = st_df.filter(pl.col("trip_id") == tid)["stop_id"].to_list()
        st_m = stops[stops["stop_id"].isin(stop_ids)].copy()
        names = set(st_m["stop_name"].dropna())
        lats = st_m.set_index("stop_name")["stop_lat"].to_dict()
        lons = st_m.set_index("stop_name")["stop_lon"].to_dict()
        result[ln] = {"names": names, "coords": {n: (lats.get(n), lons.get(n)) for n in names}}
    return result


def load_gtfs(root_path) -> tuple[dict, list]:
    """Lädt GTFS j23/j24/j25 aus sf_data-research und gibt (gtfs, all_lines) zurück."""
    from pathlib import Path
    root_path = Path(root_path)
    sf_gtfs = root_path.parent / "sf_data-research" / "data" / "raw" / "vbz" / "gtfs"
    years = {
        "j23": sf_gtfs / "2023_google_transit",
        "j24": sf_gtfs / "2024_google_transit",
        "j25": sf_gtfs / "2025_google_transit",
    }
    gtfs = {yr: get_stops_per_line(yr, path) for yr, path in years.items()}
    all_lines = sorted(
        set(ln for yr in gtfs for ln in gtfs[yr]),
        key=lambda x: int(x) if x.isdigit() else 99,
    )
    return gtfs, all_lines


def build_changes_matrix(gtfs: dict, all_lines: list) -> pd.DataFrame:
    """Baut die Änderungsmatrix aus GTFS-Daten auf."""
    rows = []
    for ln in all_lines:
        n23 = gtfs["j23"].get(ln, {}).get("names", set())
        n24 = gtfs["j24"].get(ln, {}).get("names", set())
        n25 = gtfs["j25"].get(ln, {}).get("names", set())
        added_j24 = n24 - n23
        removed_j24 = n23 - n24
        added_j25 = n25 - n24
        removed_j25 = n24 - n25
        rows.append({
            "line": ln, "n_j23": len(n23), "n_j24": len(n24), "n_j25": len(n25),
            "added_j24": len(added_j24), "removed_j24": len(removed_j24),
            "added_j25": len(added_j25), "removed_j25": len(removed_j25),
            "changed_j24": bool(added_j24 or removed_j24),
            "changed_j25": bool(added_j25 or removed_j25),
            "names_j23": n23, "names_j24": n24, "names_j25": n25,
            "names_added_j24": added_j24, "names_removed_j24": removed_j24,
            "names_added_j25": added_j25, "names_removed_j25": removed_j25,
            "coords_j23": gtfs["j23"].get(ln, {}).get("coords", {}),
            "coords_j24": gtfs["j24"].get(ln, {}).get("coords", {}),
            "coords_j25": gtfs["j25"].get(ln, {}).get("coords", {}),
        })
    return pd.DataFrame(rows)


def plot_network_changes_map(changes: pd.DataFrame) -> None:
    """Plotly Mapbox: neue Haltestellen (orange) und entfernte (grau) ab Dez 2023."""
    import plotly.graph_objects as go

    added_rows, removed_rows = [], []
    for _, row in changes.iterrows():
        ln = row["line"]
        for name, (lat, lon) in row["coords_j24"].items():
            if name in row["names_added_j24"] and lat and lon:
                added_rows.append({"name": name, "line": ln, "lat": lat, "lon": lon})
        for name, (lat, lon) in row["coords_j23"].items():
            if name in row["names_removed_j24"] and lat and lon:
                removed_rows.append({"name": name, "line": ln, "lat": lat, "lon": lon})

    fig = go.Figure()

    if removed_rows:
        rem = pd.DataFrame(removed_rows)
        fig.add_trace(go.Scattermapbox(
            lat=rem["lat"], lon=rem["lon"],
            mode="markers",
            marker=dict(size=8, color="#bbbbbb", opacity=0.7),
            text=rem.apply(lambda r: f"{r['name'].replace('Zürich, ', '')}<br>L{r['line']} — entfernt nach j23", axis=1),
            hovertemplate="<b>%{text}</b><extra></extra>",
            name="Entfernt nach j23",
        ))

    if added_rows:
        add = pd.DataFrame(added_rows)
        fig.add_trace(go.Scattermapbox(
            lat=add["lat"], lon=add["lon"],
            mode="markers",
            marker=dict(size=10, color="#FF6B00", opacity=0.85),
            text=add.apply(lambda r: f"{r['name'].replace('Zürich, ', '')}<br>L{r['line']} — neu ab Dez 2023", axis=1),
            hovertemplate="<b>%{text}</b><extra></extra>",
            name="Neu ab Dez 2023",
        ))

    fig.update_layout(
        mapbox=dict(style="carto-positron", center=dict(lat=47.378, lon=8.540), zoom=12),
        margin=dict(l=0, r=0, t=40, b=0),
        height=520,
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.85)", borderwidth=1),
        title=dict(text="Netzänderungen Dez 2023 — neue und entfernte Haltestellen",
                   font=dict(size=14)),
    )
    fig.show()


def plot_new_stops_by_district(changes: pd.DataFrame, lf_all, cfg=None):
    """Neue Haltestellen ab Dez 2023 nach Stadtkreis — Balkendiagramm."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    district_lookup = (
        lf_all
        .select(["stop_name", "district_nr", "district_name"])
        .drop_nulls()
        .unique()
        .collect()
        .to_pandas()
        .set_index("stop_name")
    )

    all_new = {}
    for _, row in changes.iterrows():
        for name in row["names_added_j24"]:
            all_new[name] = row["line"]

    new_df = pd.DataFrame({"stop_name": list(all_new.keys()), "line": list(all_new.values())})
    new_df = new_df.merge(district_lookup.reset_index(), on="stop_name", how="left")

    by_district = (new_df.groupby("district_name", observed=True)["stop_name"]
                   .nunique().reset_index(name="new_stops")
                   .sort_values("new_stops", ascending=False)
                   .dropna())

    style = mpl_style()
    fig, ax = plt.subplots(figsize=(10, 4))
    bars = ax.barh(by_district["district_name"], by_district["new_stops"],
                   color=cfg.palette_n(len(by_district)))
    ax.bar_label(bars, padding=3, fontsize=10)
    ax.set_xlabel("Anzahl neuer Haltestellen")
    ax.set_title("Neue Haltestellen ab Dez 2023 — nach Stadtkreis", fontweight="bold")
    plt.tight_layout()
    plt.show()


def table_new_stops_by_district(changes: pd.DataFrame, lf_all) -> pd.DataFrame:
    """Tabelle: Neue Haltestellen nach Stadtkreis."""
    district_lookup = (
        lf_all
        .select(["stop_name", "district_nr", "district_name"])
        .drop_nulls()
        .unique()
        .collect()
        .to_pandas()
        .set_index("stop_name")
    )
    all_new = {}
    for _, row in changes.iterrows():
        for name in row["names_added_j24"]:
            all_new[name] = row["line"]
    new_df = pd.DataFrame({"stop_name": list(all_new.keys()), "line": list(all_new.values())})
    new_df = new_df.merge(district_lookup.reset_index(), on="stop_name", how="left")
    by_district = (new_df.groupby("district_name", observed=True)["stop_name"]
                   .nunique().reset_index(name="new_stops")
                   .sort_values("new_stops", ascending=False)
                   .dropna())
    return by_district.rename(columns={"district_name": "Stadtkreis", "new_stops": "Neue Halte (ab j24)"})


def plot_network_stop_count_by_line(changes: pd.DataFrame, cfg=None):
    """Haltestellenanzahl pro Linie 2023/2024/2025 + Netto-Änderung j23→j24."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    lines_with_data = changes[changes[["n_j23", "n_j24", "n_j25"]].max(axis=1) > 0]
    x = np.arange(len(lines_with_data))
    w = 0.27
    colors = cfg.palette_n(3)

    style = mpl_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    ax.bar(x - w, lines_with_data["n_j23"], w, label="2023", color=colors[0], alpha=0.85)
    ax.bar(x, lines_with_data["n_j24"], w, label="2024", color=colors[1], alpha=0.85)
    ax.bar(x + w, lines_with_data["n_j25"], w, label="2025", color=colors[2], alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([f"L{ln}" for ln in lines_with_data["line"]], fontsize=9)
    ax.set_ylabel("Anzahl Haltestellen")
    ax.set_title("Haltestellen pro Linie — 2023 / 2024 / 2025", fontweight="bold")
    ax.legend()

    ax2 = axes[1]
    changed = changes[changes["added_j24"] + changes["removed_j24"] > 0].copy()
    changed["net"] = changed["added_j24"] - changed["removed_j24"]
    changed = changed.sort_values("net", ascending=True)
    bar_colors = [LINE_COLORS.get(ln, "#888") for ln in changed["line"]]
    bars = ax2.barh(changed["line"], changed["net"], color=bar_colors, edgecolor="white", linewidth=0.5)
    ax2.axvline(0, color="#999", linewidth=0.8, linestyle="--")
    ax2.bar_label(bars, labels=[f"+{v}" if v > 0 else str(v) for v in changed["net"]], padding=3, fontsize=9)
    ax2.set_xlabel("Netto neue Haltestellen (j23 → j24)")
    ax2.set_title("Netto-Änderung je Linie — Fahrplanwechsel Dez 2023", fontweight="bold")

    plt.tight_layout()
    plt.show()


def table_network_netto_changes(changes: pd.DataFrame) -> pd.DataFrame:
    """Tabelle: Netto-Änderungen nach Linie (j23/j24/j25 + Δ)."""
    net_table = changes[["line", "n_j23", "n_j24", "n_j25", "added_j24", "removed_j24", "added_j25", "removed_j25"]].copy()
    net_table["net_j24"] = net_table["added_j24"] - net_table["removed_j24"]
    net_table["net_j25"] = net_table["added_j25"] - net_table["removed_j25"]
    net_table = net_table[net_table[["n_j23", "n_j24", "n_j25"]].max(axis=1) > 0]
    net_table.columns = ["Linie", "Halte j23", "Halte j24", "Halte j25", "+j24", "-j24", "+j25", "-j25", "Δ j23→j24", "Δ j24→j25"]
    return net_table.set_index("Linie")


def plot_monthly_delay_all_lines(lf_all, cfg=None):
    """Monatliche Ø Verspätung aller Linien vor/nach Fahrplanwechsel Dez 2023."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.config import line_color

    monthly = (
        lf_all
        .filter(~pl.col("canceled"))
        .with_columns([
            pl.col("operating_date").dt.strftime("%Y-%m").alias("month"),
            pl.col("line_name").cast(pl.Utf8).alias("line"),
        ])
        .group_by(["month", "line"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort(["line", "month"])
        .collect()
        .to_pandas()
    )
    monthly["month"] = pd.to_datetime(monthly["month"])

    FAHRPLANWECHSEL = pd.Timestamp("2024-01-01")
    all_lines_sorted = sorted(monthly["line"].unique(),
                              key=lambda x: int(x) if x.isdigit() else 99)
    avg_all = monthly.groupby("month", observed=True)["avg_delay"].mean().reset_index()

    style = mpl_style()
    fig, ax = plt.subplots(figsize=(14, 6))

    for ln in all_lines_sorted:
        sub = monthly[monthly["line"] == ln].sort_values("month")
        ax.plot(sub["month"], sub["avg_delay"],
                color=line_color(ln), lw=1.0, marker="o", markersize=2, label=f"L{ln}")

    ax.plot(avg_all["month"], avg_all["avg_delay"],
            color=cfg.ANNO_MEAN, lw=2.5, linestyle="--", alpha=0.9, label="Ø alle Linien")
    ax.axvline(FAHRPLANWECHSEL, color=cfg.COLOR_NEGATIVE, lw=1.5,
               linestyle="--", alpha=0.8, label="Fahrplanwechsel Dez 2023")
    for year in [2024, 2025]:
        ax.axvline(pd.Timestamp(f"{year}-01-01"), color=cfg.CHART_AXIS, lw=0.8, linestyle=":")

    ax.set_xlabel("Monat", **style["label"])
    ax.set_ylabel("Ø Ankunftsverspätung (s)", **style["label"])
    ax.set_title("Monatliche Ø Verspätung — alle Linien (Jan 2023 – Okt 2025)", **style["title"])
    ax.set_xlim(pd.Timestamp("2023-01-01"), pd.Timestamp("2025-11-30"))
    ax.legend(fontsize=7, ncol=5, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.show()


def table_delay_before_after_switch(lf_all) -> pd.DataFrame:
    """Tabelle: Ø Delay vor/nach Fahrplanwechsel — alle Linien."""
    FAHRPLANWECHSEL = pd.Timestamp("2024-01-01")

    monthly = (
        lf_all
        .filter(~pl.col("canceled"))
        .with_columns([
            pl.col("operating_date").dt.strftime("%Y-%m").alias("month"),
            pl.col("line_name").cast(pl.Utf8).alias("line"),
        ])
        .group_by(["month", "line"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .sort(["line", "month"])
        .collect()
        .to_pandas()
    )
    monthly["month"] = pd.to_datetime(monthly["month"])

    changed_lines_list = ["9", "11", "13"]
    pivot_fw = monthly.copy()
    pivot_fw["periode"] = pivot_fw["month"].apply(
        lambda m: "vor Wechsel (2023)" if m < FAHRPLANWECHSEL else "nach Wechsel (2024–2025)"
    )
    delay_summary = (
        pivot_fw.groupby(["line", "periode"], observed=True)["avg_delay"]
        .mean().round(1).unstack("periode").reset_index()
    )
    delay_summary.columns.name = None

    if "vor Wechsel (2023)" in delay_summary.columns and "nach Wechsel (2024–2025)" in delay_summary.columns:
        delay_summary["Δ (s)"] = (
            delay_summary["nach Wechsel (2024–2025)"] - delay_summary["vor Wechsel (2023)"]
        ).round(1)
    else:
        delay_summary["Δ (s)"] = float("nan")

    delay_summary.insert(1, "Typ",
        delay_summary["line"].apply(
            lambda ln: "✦ verändert (j24)" if ln in changed_lines_list else "stabil"
        )
    )
    sort_col = "Δ (s)" if "Δ (s)" in delay_summary.columns else "line"
    return (
        delay_summary.rename(columns={"line": "Linie"})
        .sort_values(sort_col, ascending=False, na_position="last")
    )


def plot_einlaufzeit(changes: pd.DataFrame, lf_all, cfg=None):
    """Einlaufzeit: Neue vs. bestehende Haltestellen ab Jan 2024 — alle Linien."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style
    from zh_tram_flow.config import line_color
    import math

    new_stop_names = set()
    for _, row in changes.iterrows():
        new_stop_names.update(row["names_added_j24"])

    monthly_stops = (
        lf_all
        .filter(~pl.col("canceled"))
        .filter(pl.col("operating_date") >= pl.lit("2024-01-01").str.to_date())
        .with_columns([
            pl.col("operating_date").dt.strftime("%Y-%m").alias("month"),
            pl.col("stop_name").cast(pl.Utf8).alias("stop"),
            pl.col("line_name").cast(pl.Utf8).alias("line"),
            pl.col("stop_name").cast(pl.Utf8).is_in(list(new_stop_names)).alias("is_new"),
        ])
        .group_by(["month", "line", "is_new"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"),
             pl.col("stop").n_unique().alias("n_stops"))
        .sort(["line", "month"])
        .collect()
        .to_pandas()
    )
    monthly_stops["month"] = pd.to_datetime(monthly_stops["month"])

    all_lines_sorted = sorted(monthly_stops["line"].unique(),
                              key=lambda x: int(x) if x.isdigit() else 99)

    style = mpl_style()
    ncols = 4
    nrows = math.ceil(len(all_lines_sorted) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, nrows * 4), sharey=False)
    axes_flat = axes.flatten()

    for ax, ln in zip(axes_flat, all_lines_sorted):
        sub = monthly_stops[monthly_stops["line"] == ln]
        lc = line_color(ln)
        for is_new, label, ls, alpha in [
            (False, "Bestehende Halte", "-", 1.0),
            (True, "Neue Halte (ab j24)", "--", 0.75),
        ]:
            s = sub[sub["is_new"] == is_new].sort_values("month")
            if not s.empty:
                ax.plot(s["month"], s["avg_delay"],
                        label=label, lw=1.0, linestyle=ls,
                        color=lc, alpha=alpha,
                        marker="o", markersize=2)
        ax.set_title(f"Linie {ln}", fontweight="bold", fontsize=10)
        ax.set_ylabel("Ø Delay (s)", fontsize=8)
        ax.tick_params(axis="x", labelrotation=30, labelsize=7)
        ax.legend(fontsize=7)
        ax.spines[["top", "right"]].set_visible(False)

    for ax in axes_flat[len(all_lines_sorted):]:
        ax.set_visible(False)

    plt.suptitle("Einlaufzeit: Neue vs. bestehende Haltestellen ab Jan 2024 — alle Linien",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.show()


def table_einlaufzeit(changes: pd.DataFrame, lf_all) -> pd.DataFrame:
    """Tabelle: Neue vs. bestehende Halte — Ø Delay alle Linien ab Jan 2024."""
    new_stop_names = set()
    for _, row in changes.iterrows():
        new_stop_names.update(row["names_added_j24"])

    monthly_stops = (
        lf_all
        .filter(~pl.col("canceled"))
        .filter(pl.col("operating_date") >= pl.lit("2024-01-01").str.to_date())
        .with_columns([
            pl.col("stop_name").cast(pl.Utf8).is_in(list(new_stop_names)).alias("is_new"),
            pl.col("line_name").cast(pl.Utf8).alias("line"),
        ])
        .group_by(["line", "is_new"])
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"))
        .collect()
        .to_pandas()
    )

    existing_df = (
        monthly_stops[monthly_stops["is_new"] == False]
        .groupby("line", observed=True)["avg_delay"].mean().round(1)
        .reset_index().rename(columns={"avg_delay": "Bestehende Halte (s)"})
    )
    new_df_stops = (
        monthly_stops[monthly_stops["is_new"] == True]
        .groupby("line", observed=True)["avg_delay"].mean().round(1)
        .reset_index().rename(columns={"avg_delay": "Neue Halte (s)"})
    )
    einlauf_summary = (
        existing_df.merge(new_df_stops, on="line", how="left")
        .sort_values("Neue Halte (s)", ascending=False, na_position="last")
    )
    einlauf_summary["Δ neu−best. (s)"] = (
        einlauf_summary["Neue Halte (s)"] - einlauf_summary["Bestehende Halte (s)"]
    ).round(1)
    return einlauf_summary.rename(columns={"line": "Linie"}).set_index("Linie")


def plot_hotspots(changes: pd.DataFrame, lf_all, cfg=None):
    """Haltestellen-Hotspots nach Linienanzahl + Linienanzahl vs. Verspätung Scatter."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    stop_lines = {}
    for _, row in changes.iterrows():
        ln = row["line"]
        for name in row["names_j25"]:
            stop_lines.setdefault(name, set()).add(ln)

    hotspot_df = (pd.DataFrame({
        "stop_name": list(stop_lines.keys()),
        "n_lines": [len(v) for v in stop_lines.values()],
        "lines": [", ".join(sorted(v, key=lambda x: int(x) if x.isdigit() else 99))
                  for v in stop_lines.values()]
    })
    .sort_values("n_lines", ascending=False)
    .head(20))

    delay_per_stop = (
        lf_all
        .filter(~pl.col("canceled"))
        .filter(pl.col("operating_date") >= pl.lit("2024-01-01").str.to_date())
        .group_by("stop_name")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"),
             pl.len().alias("n_obs"))
        .filter(pl.col("n_obs") > 1000)
        .collect()
        .to_pandas()
    )

    hotspot_merged = hotspot_df.merge(delay_per_stop, on="stop_name", how="inner")

    style = mpl_style()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax = axes[0]
    bars = ax.barh(hotspot_df["stop_name"][:15][::-1],
                   hotspot_df["n_lines"][:15][::-1],
                   color=cfg.palette_n(1)[0])
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_xlabel("Anzahl Linien")
    ax.set_title("Top 15 Haltestellen nach Linienanzahl (j25)", fontweight="bold")

    ax2 = axes[1]
    scatter = ax2.scatter(hotspot_merged["n_lines"], hotspot_merged["avg_delay"],
                          s=hotspot_merged["n_obs"] / 500, alpha=0.7,
                          color=cfg.palette_n(1)[0], edgecolors="white", linewidth=0.5)
    for _, r in hotspot_merged[hotspot_merged["n_lines"] >= 4].iterrows():
        ax2.annotate(r["stop_name"], (r["n_lines"], r["avg_delay"]),
                     fontsize=8, ha="left", va="bottom",
                     xytext=(4, 4), textcoords="offset points")
    ax2.set_xlabel("Anzahl Linien an der Haltestelle")
    ax2.set_ylabel("Ø Ankunftsverspätung (s)")
    ax2.set_title("Linienanzahl vs. Verspätung — Knotenpunkte 2024–2025", fontweight="bold")
    ax2.axhline(delay_per_stop["avg_delay"].median(), color="#999", linestyle="--",
                linewidth=1, label=f"Median {delay_per_stop['avg_delay'].median():.0f}s")
    ax2.legend(fontsize=9)

    plt.tight_layout()
    plt.show()


def table_hotspots(changes: pd.DataFrame, lf_all) -> pd.DataFrame:
    """Tabelle: Top Hotspots — Linienanzahl + Ø Verspätung."""
    stop_lines = {}
    for _, row in changes.iterrows():
        ln = row["line"]
        for name in row["names_j25"]:
            stop_lines.setdefault(name, set()).add(ln)

    hotspot_df = (pd.DataFrame({
        "stop_name": list(stop_lines.keys()),
        "n_lines": [len(v) for v in stop_lines.values()],
        "lines": [", ".join(sorted(v, key=lambda x: int(x) if x.isdigit() else 99))
                  for v in stop_lines.values()]
    })
    .sort_values("n_lines", ascending=False)
    .head(20))

    delay_per_stop = (
        lf_all
        .filter(~pl.col("canceled"))
        .filter(pl.col("operating_date") >= pl.lit("2024-01-01").str.to_date())
        .group_by("stop_name")
        .agg(pl.col("arrival_delay").mean().alias("avg_delay"),
             pl.len().alias("n_obs"))
        .filter(pl.col("n_obs") > 1000)
        .collect()
        .to_pandas()
    )
    hotspot_merged = hotspot_df.merge(delay_per_stop, on="stop_name", how="inner")
    return (
        hotspot_merged[["stop_name", "n_lines", "lines", "avg_delay", "n_obs"]]
        .sort_values("n_lines", ascending=False)
        .rename(columns={
            "stop_name": "Haltestelle", "n_lines": "Linien",
            "lines": "Linienliste", "avg_delay": "Ø Delay (s)", "n_obs": "Beobachtungen"
        })
        .round({"Ø Delay (s)": 1})
        .reset_index(drop=True)
    )


def plot_service_quality_district_map(lf_all) -> None:
    """Plotly Mapbox Choropleth: Δ Linienanbindung pro Stadtkreis 2023 → 2025."""
    import plotly.graph_objects as go
    import json
    from pathlib import Path

    geojson_path = Path(__file__).parents[3] / "data" / "raw" / "stadtkreise.geojson"
    with open(geojson_path) as f:
        geojson = json.load(f)

    def lines_per_district_nr(year_key):
        yr_start = {"j23": "2023-01-01", "j25": "2025-01-01"}[year_key]
        yr_end   = {"j23": "2023-12-31", "j25": "2025-11-30"}[year_key]
        return (
            lf_all
            .filter(pl.col("operating_date").is_between(
                pl.lit(yr_start).str.to_date(), pl.lit(yr_end).str.to_date()))
            .filter(pl.col("district_nr").is_not_null())
            .select(["district_nr", "line_name"])
            .unique()
            .group_by("district_nr")
            .agg(pl.col("line_name").n_unique().alias(f"lines_{year_key}"))
            .collect()
            .to_pandas()
        )

    j23 = lines_per_district_nr("j23")
    j25 = lines_per_district_nr("j25")
    cmp = j23.merge(j25, on="district_nr", how="outer")
    cmp["lines_j23"] = cmp["lines_j23"].fillna(0).astype(int)
    cmp["lines_j25"] = cmp["lines_j25"].fillna(0).astype(int)
    cmp["delta"] = cmp["lines_j25"] - cmp["lines_j23"]
    cmp["district_nr_str"] = cmp["district_nr"].astype(str)
    cmp["label"] = cmp.apply(
        lambda r: f"Kreis {r['district_nr']}<br>j23: {r['lines_j23']} Linien → j25: {r['lines_j25']} Linien<br>Δ: {'+' if r['delta'] > 0 else ''}{r['delta']}",
        axis=1
    )

    abs_max = cmp["delta"].abs().max()

    fig = go.Figure()

    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=cmp["district_nr_str"],
        z=cmp["delta"],
        featureidkey="properties.objid",
        colorscale=[
            [0.0,  "#E20A16"],
            [0.5,  "#f5f5f5"],
            [1.0,  "#00892F"],
        ],
        zmin=-abs_max,
        zmax=abs_max,
        marker=dict(line=dict(color="white", width=1.5), opacity=0.75),
        colorbar=dict(
            title="Δ Linien",
            thickness=14,
            len=0.55,
            tickvals=list(range(-abs_max, abs_max + 1)),
        ),
        text=cmp["label"],
        hovertemplate="%{text}<extra></extra>",
        name="Δ Linienanbindung",
    ))

    for _, row in cmp.iterrows():
        feat = next(
            (f for f in geojson["features"] if f["properties"]["objid"] == str(row["district_nr"])),
            None
        )
        if feat is None:
            continue
        coords = feat["geometry"]["coordinates"]
        if feat["geometry"]["type"] == "MultiPolygon":
            all_pts = [pt for poly in coords for ring in poly for pt in ring]
        else:
            all_pts = [pt for ring in coords for pt in ring]
        if not all_pts:
            continue
        lon_c = sum(p[0] for p in all_pts) / len(all_pts)
        lat_c = sum(p[1] for p in all_pts) / len(all_pts)
        sign = "+" if row["delta"] > 0 else ""
        fig.add_trace(go.Scattermapbox(
            lat=[lat_c], lon=[lon_c],
            mode="text",
            text=[f"K{row['district_nr']}<br>{sign}{row['delta']}"],
            textfont=dict(size=11, color="#222222"),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.update_layout(
        mapbox=dict(style="carto-positron", center=dict(lat=47.378, lon=8.540), zoom=11.3),
        margin=dict(l=0, r=0, t=40, b=0),
        height=520,
        title=dict(text="Veränderung der Linienanbindung nach Stadtkreis — 2023 → 2025",
                   font=dict(size=14)),
    )
    fig.show()


def plot_service_quality_by_district(lf_all, cfg=None):
    """Versorgungsqualität: Veränderung der Linienanbindung nach Stadtkreis 2023→2025."""
    cfg = _get_cfg(cfg)
    from wgnd.core.theme import mpl_style

    def lines_per_district(year_key):
        yr_start = {"j23": "2023-01-01", "j24": "2024-01-01", "j25": "2025-01-01"}[year_key]
        yr_end = {"j23": "2023-12-31", "j24": "2024-12-31", "j25": "2025-11-30"}[year_key]
        return (
            lf_all
            .filter(pl.col("operating_date").is_between(
                pl.lit(yr_start).str.to_date(), pl.lit(yr_end).str.to_date()))
            .filter(pl.col("district_nr").is_not_null())
            .select(["district_name", "line_name"])
            .unique()
            .group_by("district_name")
            .agg(pl.col("line_name").n_unique().alias(f"lines_{year_key}"))
            .collect()
            .to_pandas()
            .assign(district_name=lambda df: df["district_name"].astype(str))
        )

    dist_j23 = lines_per_district("j23")
    dist_j25 = lines_per_district("j25")

    dist_cmp = dist_j23.merge(dist_j25, on="district_name", how="outer")
    dist_cmp["lines_j23"] = dist_cmp["lines_j23"].fillna(0).astype(int)
    dist_cmp["lines_j25"] = dist_cmp["lines_j25"].fillna(0).astype(int)
    dist_cmp["delta"] = dist_cmp["lines_j25"] - dist_cmp["lines_j23"]
    dist_cmp = dist_cmp.sort_values("delta", ascending=True)

    style = mpl_style()
    fig, ax = plt.subplots(figsize=(10, 5))
    colors_bar = ["#E20A16" if d < 0 else "#00892F" if d > 0 else "#aaa" for d in dist_cmp["delta"]]
    bars = ax.barh(dist_cmp["district_name"], dist_cmp["delta"], color=colors_bar, edgecolor="white")
    ax.bar_label(bars, labels=[f"+{v:.0f}" if v > 0 else f"{v:.0f}" for v in dist_cmp["delta"]],
                 padding=3, fontsize=9)
    ax.axvline(0, color="#999", linewidth=0.8)
    ax.set_xlabel("Δ Anzahl Linien (2025 vs. 2023)")
    ax.set_title("Veränderung der Linienanbindung nach Stadtkreis — 2023 → 2025", fontweight="bold")
    plt.tight_layout()
    plt.show()


def table_service_quality_by_district(lf_all) -> pd.DataFrame:
    """Tabelle: Linienanbindung nach Stadtkreis j23 vs. j25."""
    def lines_per_district(year_key):
        yr_start = {"j23": "2023-01-01", "j24": "2024-01-01", "j25": "2025-01-01"}[year_key]
        yr_end = {"j23": "2023-12-31", "j24": "2024-12-31", "j25": "2025-11-30"}[year_key]
        return (
            lf_all
            .filter(pl.col("operating_date").is_between(
                pl.lit(yr_start).str.to_date(), pl.lit(yr_end).str.to_date()))
            .filter(pl.col("district_nr").is_not_null())
            .select(["district_name", "line_name"])
            .unique()
            .group_by("district_name")
            .agg(pl.col("line_name").n_unique().alias(f"lines_{year_key}"))
            .collect()
            .to_pandas()
            .assign(district_name=lambda df: df["district_name"].astype(str))
        )

    dist_j23 = lines_per_district("j23")
    dist_j25 = lines_per_district("j25")
    dist_cmp = dist_j23.merge(dist_j25, on="district_name", how="outer")
    dist_cmp["lines_j23"] = dist_cmp["lines_j23"].fillna(0).astype(int)
    dist_cmp["lines_j25"] = dist_cmp["lines_j25"].fillna(0).astype(int)
    dist_cmp["delta"] = dist_cmp["lines_j25"] - dist_cmp["lines_j23"]
    return (
        dist_cmp[["district_name", "lines_j23", "lines_j25", "delta"]]
        .sort_values("delta", ascending=False)
        .reset_index(drop=True)
    )
