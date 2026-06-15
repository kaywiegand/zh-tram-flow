# Dwell-Time Simulator

**Fragestellung:** Was wäre wenn VBZ an Haltestellen mehr Puffer einplant?

`dwell_time` ist das **#1-Feature** in LightGBM v1 (Gain: 14.8M — vor `stop_name` 12.7M).
Gleichzeitig zeigt F-SPAT-08: 71.3% aller Halte haben `dwell_time = 0`. Der stärkste
Modell-Prädiktor ist gleichzeitig die grösste strukturelle Lücke im Fahrplan.

Dieses Notebook führt die Simulation durch und stellt dabei eine grundsätzliche Frage:
**Kann ein auf Beobachtungsdaten trainiertes Modell kausale Empfehlungen liefern?**

**Warum LightGBM v1 (nicht v2)?**
v2 hat `prev_trip_delay` — ein Kaskadenfeature, das sich selbst verändern würde,
wenn dwell_time sich ändert. v1 ist self-contained: eine Änderung in `dwell_time`
→ direkt eine neue Vorhersage, ohne Kaskadenabhängigkeit.

**Schließt den Kreis:**
Analyse (F-SPAT-08: kein Puffer) → Modell (Feature #1) → Simulation → Befund über ML-Grenzen

## Setup


```python
from zh_tram_flow.notebook import *
import polars as pl
import lightgbm as lgb
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json
from pathlib import Path

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("06_prediction_6-dwell_simulator")

MODELS_DIR = Path(TRAIN).parent.parent / "models"
%load_ext autoreload
%autoreload 2
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-06-11 17:13:44  INFO      project  06_prediction_6-dwell_simulator started


    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload



```python
model = lgb.Booster(model_file=str(MODELS_DIR / "lgbm_v1.txt"))

with open(MODELS_DIR / "lgbm_v1_meta.json") as f:
    meta = json.load(f)

FEATURE_COLS = meta["features"]
CAT_COLS = meta["cat_cols"]

print(f"Features: {len(FEATURE_COLS)} | #1 by gain: dwell_time")
print(f"Cat cols: {CAT_COLS}")
```

    Features: 32 | #1 by gain: dwell_time
    Cat cols: ['line_name', 'stop_name', 'event_type', 'season', 'gtfs_year']



```python
# test_final.parquet hat alle Modell-Features (gtfs_year, dwell_time, n_lines_at_stop, etc.)
# test_features.parquet ist die Zwischen-Stufe vor dem Feature-Engineering → hier NICHT verwenden
TEST_FINAL = PATHS["processed"] / "test_final.parquet"

# Polars Lernmoment: .cast(pl.Utf8) stellt sicher dass line_name immer String ist,
# unabhängig davon ob es im Parquet als Int oder Str gespeichert ist.
df_test = (
    pl.scan_parquet(TEST_FINAL)
    .with_columns(pl.col("line_name").cast(pl.Utf8))
    .collect()
    .to_pandas()
)
for col in CAT_COLS:
    df_test[col] = df_test[col].astype("category")

print(f"Test rows: {len(df_test):,}")
print(f"Columns: {len(df_test.columns)} (model needs {len(FEATURE_COLS)})")
```

    Test rows: 29,941,876
    Columns: 40 (model needs 32)


## Schritt 1 — dwell_time Verteilung

Bevor wir simulieren: welche Werte nimmt `dwell_time` überhaupt an?


```python
dwell_vc = df_test["dwell_time"].value_counts().sort_index()
print("dwell_time Werteverteilung (Test-Set):")
print(dwell_vc[dwell_vc > 100].to_string())
print()
print(f"Anteil dwell_time = 0:  {(df_test['dwell_time'] == 0).mean():.1%}")
print(f"Anteil dwell_time = 60: {(df_test['dwell_time'] == 60).mean():.1%}")
print(f"Anteil dwell_time 1–59: {((df_test['dwell_time'] > 0) & (df_test['dwell_time'] < 60)).mean():.1%}")
```

    dwell_time Werteverteilung (Test-Set):
    dwell_time
    0      21312198
    60      8432318
    120      196679
    180         292
    240         329
    
    Anteil dwell_time = 0:  71.2%
    Anteil dwell_time = 60: 28.2%
    Anteil dwell_time 1–59: 0.0%


**Befund:** `dwell_time` ist in VBZ-Fahrplandaten **faktisch binär**: entweder `0s` (71.3%) oder `60s` (28.5%).
Werte zwischen 1 und 59 Sekunden existieren nicht — die VBZ plant entweder keinen Puffer (0) oder einen
vollen Aufenthalt (60s). Das hat direkte Konsequenzen für die Simulation:
Eine Simulation mit +10s würde Werte erzeugen, die das Modell **noch nie gesehen hat** —
out-of-distribution Extrapolation.

## Schritt 2 — Konfundierungs-Analyse: dwell_time × Delay

Korreliert höhere dwell_time mit weniger oder mehr Verspätung?


```python
r = df_test["dwell_time"].corr(df_test["arrival_delay"])
print(f"Pearson r (dwell_time × arrival_delay) = {r:.4f}")
print()

# Mean delay by dwell_time value (binary comparison)
summary = (
    df_test.groupby("dwell_time")["arrival_delay"]
    .agg(["mean", "count"])
    .loc[[0, 60]]
)
summary.columns = ["Ø arrival_delay (s)", "N"]
summary.index.name = "dwell_time"
show_df(summary)
```

    Pearson r (dwell_time × arrival_delay) = 0.1581
    



<style type="text/css">
#T_11ee6 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_11ee6 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_11ee6 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_11ee6 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_11ee6 tr:hover td {
  background-color: #eef3f8;
}
#T_11ee6_row0_col0, #T_11ee6_row0_col1, #T_11ee6_row1_col0, #T_11ee6_row1_col1 {
  text-align: right;
}
</style>
<table id="T_11ee6">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_11ee6_level0_col0" class="col_heading level0 col0" >Ø arrival_delay (s)</th>
      <th id="T_11ee6_level0_col1" class="col_heading level0 col1" >N</th>
    </tr>
    <tr>
      <th class="index_name level0" >dwell_time</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_11ee6_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_11ee6_row0_col0" class="data row0 col0" >46.93</td>
      <td id="T_11ee6_row0_col1" class="data row0 col1" >21312198</td>
    </tr>
    <tr>
      <th id="T_11ee6_level0_row1" class="row_heading level0 row1" >60</th>
      <td id="T_11ee6_row1_col0" class="data row1 col0" >74.78</td>
      <td id="T_11ee6_row1_col1" class="data row1 col1" >8432318</td>
    </tr>
  </tbody>
</table>



**Befund:** Pearson r = +0.16 — `dwell_time` korreliert **positiv** mit Verspätung.
Haltestellen mit `dwell_time = 60s` haben im Durchschnitt ~28s mehr Delay als
Haltestellen mit `dwell_time = 0`.

**Erklärung — Konfundierung durch Haltestellen-Komplexität:**

```
Komplexer Stop
    ↓              ↓
dwell_time = 60   arrival_delay hoch
(VBZ plant Puffer  (viel Betrieb,
 an schwierigen    MIV-Interaktion,
 Stops ein)        Fahrgastwechsel)
```

VBZ gibt mehr `dwell_time` an Umsteigepunkten (Stauffacher, Bahnhof Oerlikon, Leutschenbach) —
genau dort, wo strukturell mehr Delay entsteht. Das Modell hat diese Korrelation korrekt gelernt.
Aber: **Correlation ≠ Causation.** Wenn wir einem einfachen Halt +60s geben, wird er
dadurch nicht zu Stauffacher — der Modell-Prädiktor ist hier ein **Proxy**, kein Hebel.

## Schritt 3 — Simulation: 0 → 60s (einziger valider Wert)

Simulation mit dem einzigen Wert, den das Modell trainiert hat: `dwell_time = 0 → 60`.
Was sagt das Modell für Haltestellen, die aktuell keinen Puffer haben?


```python
def simulate_dwell(
    df: pd.DataFrame,
    new_value: int = 60,
    line_name: str | None = None,
) -> pd.DataFrame:
    """Simulate changing dwell_time from 0 to new_value at zero-dwell stops.

    Args:
        df: Test dataframe with pred_base already computed.
        new_value: New dwell_time value (should be a value seen in training — 60 or 120).
        line_name: If given, restrict to this line. None = network-wide.

    Returns:
        Copy of df with pred_sim and delta_delay columns added.
    """
    df_sim = df.copy()
    mask = df_sim["dwell_time"] == 0
    if line_name is not None:
        mask = mask & (df_sim["line_name"].astype(str) == str(line_name))
    df_sim.loc[mask, "dwell_time"] = new_value
    df_sim["pred_sim"] = model.predict(df_sim[FEATURE_COLS])
    df_sim["delta_delay"] = df_sim["pred_sim"] - df_sim["pred_base"]
    if line_name is not None:
        return df_sim[df_sim["line_name"].astype(str) == str(line_name)].copy()
    return df_sim


# Baseline first
df_test["pred_base"] = model.predict(df_test[FEATURE_COLS])
mae_base = np.abs(df_test["pred_base"] - df_test["arrival_delay"]).mean()
print(f"Baseline MAE: {mae_base:.2f}s")
```

    Baseline MAE: 45.74s



```python
# L11: 0 → 60s
sim_l11 = simulate_dwell(df_test, new_value=60, line_name="11")

mae_l11_base = np.abs(sim_l11["pred_base"] - sim_l11["arrival_delay"]).mean()
mae_l11_sim  = np.abs(sim_l11["pred_sim"]  - sim_l11["arrival_delay"]).mean()
mean_delta   = sim_l11["delta_delay"].mean()

print(f"L11 — 0→60s dwell_time:")
print(f"  MAE Baseline:  {mae_l11_base:.2f}s")
print(f"  MAE Simulation:{mae_l11_sim:.2f}s")
print(f"  Ø Δ Delay:     {mean_delta:+.2f}s")
```

    L11 — 0→60s dwell_time:
      MAE Baseline:  52.33s
      MAE Simulation:57.76s
      Ø Δ Delay:     +19.96s



```python
# Per-stop breakdown
stops = (
    sim_l11.groupby("stop_name", observed=True)
    .agg(
        mean_delta=("delta_delay", "mean"),
        mean_actual=("arrival_delay", "mean"),
        n=("delta_delay", "count"),
    )
    .reset_index()
    .sort_values("mean_actual", ascending=False)
)

stop_labels = stops["stop_name"].str.replace("Zürich, ", "", regex=False)
colors = ["#25ac82" if v <= 0 else "#de425b" for v in stops["mean_delta"]]

fig = go.Figure(go.Bar(
    x=stop_labels,
    y=stops["mean_delta"].round(1),
    marker_color=colors,
    hovertemplate="<b>%{x}</b><br>Δ Delay: %{y:.1f}s<extra></extra>",
))
fig.add_hline(y=0, line_dash="dot", line_color="#888", line_width=1)
fig.update_layout(
    title=dict(
        text=(
            f"L11 — Modell-Vorhersage: Δ Delay bei dwell_time 0→60s<br>"
            f"<sup>Grün = Verbesserung · Rot = Verschlechterung · Ø {mean_delta:+.1f}s</sup>"
        ),
        x=0, xanchor="left",
    ),
    xaxis=dict(title="Haltestelle", tickangle=-40),
    yaxis=dict(title="Δ Delay (s)"),
    height=480,
    margin=dict(l=0, r=0, t=80, b=130),
    plot_bgcolor="white",
)
fig.show()

# Companion table
stops_display = stops.copy()
stops_display.insert(0, "Haltestelle", stops_display["stop_name"].str.replace("Zürich, ", "", regex=False))
stops_display["Ø Delay Ist (s)"] = stops_display["mean_actual"].round(1)
stops_display["Δ Delay 0→60s (s)"] = stops_display["mean_delta"].round(1)
stops_display["N"] = stops_display["n"]
show_df(stops_display[["Haltestelle", "Ø Delay Ist (s)", "Δ Delay 0→60s (s)", "N"]].set_index("Haltestelle"))
```




<style type="text/css">
#T_5e96b thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_5e96b td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_5e96b tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_5e96b tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_5e96b tr:hover td {
  background-color: #eef3f8;
}
#T_5e96b_row0_col0, #T_5e96b_row0_col1, #T_5e96b_row0_col2, #T_5e96b_row1_col0, #T_5e96b_row1_col1, #T_5e96b_row1_col2, #T_5e96b_row2_col0, #T_5e96b_row2_col1, #T_5e96b_row2_col2, #T_5e96b_row3_col0, #T_5e96b_row3_col1, #T_5e96b_row3_col2, #T_5e96b_row4_col0, #T_5e96b_row4_col1, #T_5e96b_row4_col2, #T_5e96b_row5_col0, #T_5e96b_row5_col1, #T_5e96b_row5_col2, #T_5e96b_row6_col0, #T_5e96b_row6_col1, #T_5e96b_row6_col2, #T_5e96b_row7_col0, #T_5e96b_row7_col1, #T_5e96b_row7_col2, #T_5e96b_row8_col0, #T_5e96b_row8_col1, #T_5e96b_row8_col2, #T_5e96b_row9_col0, #T_5e96b_row9_col1, #T_5e96b_row9_col2, #T_5e96b_row10_col0, #T_5e96b_row10_col1, #T_5e96b_row10_col2, #T_5e96b_row11_col0, #T_5e96b_row11_col1, #T_5e96b_row11_col2, #T_5e96b_row12_col0, #T_5e96b_row12_col1, #T_5e96b_row12_col2, #T_5e96b_row13_col0, #T_5e96b_row13_col1, #T_5e96b_row13_col2, #T_5e96b_row14_col0, #T_5e96b_row14_col1, #T_5e96b_row14_col2, #T_5e96b_row15_col0, #T_5e96b_row15_col1, #T_5e96b_row15_col2, #T_5e96b_row16_col0, #T_5e96b_row16_col1, #T_5e96b_row16_col2, #T_5e96b_row17_col0, #T_5e96b_row17_col1, #T_5e96b_row17_col2, #T_5e96b_row18_col0, #T_5e96b_row18_col1, #T_5e96b_row18_col2, #T_5e96b_row19_col0, #T_5e96b_row19_col1, #T_5e96b_row19_col2, #T_5e96b_row20_col0, #T_5e96b_row20_col1, #T_5e96b_row20_col2, #T_5e96b_row21_col0, #T_5e96b_row21_col1, #T_5e96b_row21_col2, #T_5e96b_row22_col0, #T_5e96b_row22_col1, #T_5e96b_row22_col2, #T_5e96b_row23_col0, #T_5e96b_row23_col1, #T_5e96b_row23_col2, #T_5e96b_row24_col0, #T_5e96b_row24_col1, #T_5e96b_row24_col2, #T_5e96b_row25_col0, #T_5e96b_row25_col1, #T_5e96b_row25_col2, #T_5e96b_row26_col0, #T_5e96b_row26_col1, #T_5e96b_row26_col2, #T_5e96b_row27_col0, #T_5e96b_row27_col1, #T_5e96b_row27_col2, #T_5e96b_row28_col0, #T_5e96b_row28_col1, #T_5e96b_row28_col2, #T_5e96b_row29_col0, #T_5e96b_row29_col1, #T_5e96b_row29_col2, #T_5e96b_row30_col0, #T_5e96b_row30_col1, #T_5e96b_row30_col2, #T_5e96b_row31_col0, #T_5e96b_row31_col1, #T_5e96b_row31_col2, #T_5e96b_row32_col0, #T_5e96b_row32_col1, #T_5e96b_row32_col2, #T_5e96b_row33_col0, #T_5e96b_row33_col1, #T_5e96b_row33_col2, #T_5e96b_row34_col0, #T_5e96b_row34_col1, #T_5e96b_row34_col2, #T_5e96b_row35_col0, #T_5e96b_row35_col1, #T_5e96b_row35_col2, #T_5e96b_row36_col0, #T_5e96b_row36_col1, #T_5e96b_row36_col2, #T_5e96b_row37_col0, #T_5e96b_row37_col1, #T_5e96b_row37_col2, #T_5e96b_row38_col0, #T_5e96b_row38_col1, #T_5e96b_row38_col2, #T_5e96b_row39_col0, #T_5e96b_row39_col1, #T_5e96b_row39_col2, #T_5e96b_row40_col0, #T_5e96b_row40_col1, #T_5e96b_row40_col2, #T_5e96b_row41_col0, #T_5e96b_row41_col1, #T_5e96b_row41_col2, #T_5e96b_row42_col0, #T_5e96b_row42_col1, #T_5e96b_row42_col2, #T_5e96b_row43_col0, #T_5e96b_row43_col1, #T_5e96b_row43_col2, #T_5e96b_row44_col0, #T_5e96b_row44_col1, #T_5e96b_row44_col2, #T_5e96b_row45_col0, #T_5e96b_row45_col1, #T_5e96b_row45_col2, #T_5e96b_row46_col0, #T_5e96b_row46_col1, #T_5e96b_row46_col2, #T_5e96b_row47_col0, #T_5e96b_row47_col1, #T_5e96b_row47_col2, #T_5e96b_row48_col0, #T_5e96b_row48_col1, #T_5e96b_row48_col2, #T_5e96b_row49_col0, #T_5e96b_row49_col1, #T_5e96b_row49_col2, #T_5e96b_row50_col0, #T_5e96b_row50_col1, #T_5e96b_row50_col2, #T_5e96b_row51_col0, #T_5e96b_row51_col1, #T_5e96b_row51_col2, #T_5e96b_row52_col0, #T_5e96b_row52_col1, #T_5e96b_row52_col2, #T_5e96b_row53_col0, #T_5e96b_row53_col1, #T_5e96b_row53_col2, #T_5e96b_row54_col0, #T_5e96b_row54_col1, #T_5e96b_row54_col2, #T_5e96b_row55_col0, #T_5e96b_row55_col1, #T_5e96b_row55_col2, #T_5e96b_row56_col0, #T_5e96b_row56_col1, #T_5e96b_row56_col2, #T_5e96b_row57_col0, #T_5e96b_row57_col1, #T_5e96b_row57_col2, #T_5e96b_row58_col0, #T_5e96b_row58_col1, #T_5e96b_row58_col2, #T_5e96b_row59_col0, #T_5e96b_row59_col1, #T_5e96b_row59_col2, #T_5e96b_row60_col0, #T_5e96b_row60_col1, #T_5e96b_row60_col2, #T_5e96b_row61_col0, #T_5e96b_row61_col1, #T_5e96b_row61_col2, #T_5e96b_row62_col0, #T_5e96b_row62_col1, #T_5e96b_row62_col2, #T_5e96b_row63_col0, #T_5e96b_row63_col1, #T_5e96b_row63_col2, #T_5e96b_row64_col0, #T_5e96b_row64_col1, #T_5e96b_row64_col2, #T_5e96b_row65_col0, #T_5e96b_row65_col1, #T_5e96b_row65_col2, #T_5e96b_row66_col0, #T_5e96b_row66_col1, #T_5e96b_row66_col2, #T_5e96b_row67_col0, #T_5e96b_row67_col1, #T_5e96b_row67_col2, #T_5e96b_row68_col0, #T_5e96b_row68_col1, #T_5e96b_row68_col2, #T_5e96b_row69_col0, #T_5e96b_row69_col1, #T_5e96b_row69_col2, #T_5e96b_row70_col0, #T_5e96b_row70_col1, #T_5e96b_row70_col2, #T_5e96b_row71_col0, #T_5e96b_row71_col1, #T_5e96b_row71_col2, #T_5e96b_row72_col0, #T_5e96b_row72_col1, #T_5e96b_row72_col2, #T_5e96b_row73_col0, #T_5e96b_row73_col1, #T_5e96b_row73_col2, #T_5e96b_row74_col0, #T_5e96b_row74_col1, #T_5e96b_row74_col2, #T_5e96b_row75_col0, #T_5e96b_row75_col1, #T_5e96b_row75_col2, #T_5e96b_row76_col0, #T_5e96b_row76_col1, #T_5e96b_row76_col2, #T_5e96b_row77_col0, #T_5e96b_row77_col1, #T_5e96b_row77_col2, #T_5e96b_row78_col0, #T_5e96b_row78_col1, #T_5e96b_row78_col2, #T_5e96b_row79_col0, #T_5e96b_row79_col1, #T_5e96b_row79_col2, #T_5e96b_row80_col0, #T_5e96b_row80_col1, #T_5e96b_row80_col2, #T_5e96b_row81_col0, #T_5e96b_row81_col1, #T_5e96b_row81_col2, #T_5e96b_row82_col0, #T_5e96b_row82_col1, #T_5e96b_row82_col2, #T_5e96b_row83_col0, #T_5e96b_row83_col1, #T_5e96b_row83_col2, #T_5e96b_row84_col0, #T_5e96b_row84_col1, #T_5e96b_row84_col2, #T_5e96b_row85_col0, #T_5e96b_row85_col1, #T_5e96b_row85_col2, #T_5e96b_row86_col0, #T_5e96b_row86_col1, #T_5e96b_row86_col2, #T_5e96b_row87_col0, #T_5e96b_row87_col1, #T_5e96b_row87_col2, #T_5e96b_row88_col0, #T_5e96b_row88_col1, #T_5e96b_row88_col2, #T_5e96b_row89_col0, #T_5e96b_row89_col1, #T_5e96b_row89_col2, #T_5e96b_row90_col0, #T_5e96b_row90_col1, #T_5e96b_row90_col2, #T_5e96b_row91_col0, #T_5e96b_row91_col1, #T_5e96b_row91_col2, #T_5e96b_row92_col0, #T_5e96b_row92_col1, #T_5e96b_row92_col2, #T_5e96b_row93_col0, #T_5e96b_row93_col1, #T_5e96b_row93_col2, #T_5e96b_row94_col0, #T_5e96b_row94_col1, #T_5e96b_row94_col2, #T_5e96b_row95_col0, #T_5e96b_row95_col1, #T_5e96b_row95_col2, #T_5e96b_row96_col0, #T_5e96b_row96_col1, #T_5e96b_row96_col2, #T_5e96b_row97_col0, #T_5e96b_row97_col1, #T_5e96b_row97_col2, #T_5e96b_row98_col0, #T_5e96b_row98_col1, #T_5e96b_row98_col2, #T_5e96b_row99_col0, #T_5e96b_row99_col1, #T_5e96b_row99_col2, #T_5e96b_row100_col0, #T_5e96b_row100_col1, #T_5e96b_row100_col2 {
  text-align: right;
}
</style>
<table id="T_5e96b">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_5e96b_level0_col0" class="col_heading level0 col0" >Ø Delay Ist (s)</th>
      <th id="T_5e96b_level0_col1" class="col_heading level0 col1" >Δ Delay 0→60s (s)</th>
      <th id="T_5e96b_level0_col2" class="col_heading level0 col2" >N</th>
    </tr>
    <tr>
      <th class="index_name level0" >Haltestelle</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_5e96b_level0_row0" class="row_heading level0 row0" >Neumarkt</th>
      <td id="T_5e96b_row0_col0" class="data row0 col0" >244.60</td>
      <td id="T_5e96b_row0_col1" class="data row0 col1" >34.50</td>
      <td id="T_5e96b_row0_col2" class="data row0 col2" >5</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row1" class="row_heading level0 row1" >ETH/Universitätsspital</th>
      <td id="T_5e96b_row1_col0" class="data row1 col0" >157.00</td>
      <td id="T_5e96b_row1_col1" class="data row1 col1" >9.30</td>
      <td id="T_5e96b_row1_col2" class="data row1 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row2" class="row_heading level0 row2" >Bahnhof Oerlikon Ost</th>
      <td id="T_5e96b_row2_col0" class="data row2 col0" >152.50</td>
      <td id="T_5e96b_row2_col1" class="data row2 col1" >17.80</td>
      <td id="T_5e96b_row2_col2" class="data row2 col2" >15</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row3" class="row_heading level0 row3" >Haldenbach</th>
      <td id="T_5e96b_row3_col0" class="data row3 col0" >147.00</td>
      <td id="T_5e96b_row3_col1" class="data row3 col1" >8.00</td>
      <td id="T_5e96b_row3_col2" class="data row3 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row4" class="row_heading level0 row4" >Englischviertelstrasse</th>
      <td id="T_5e96b_row4_col0" class="data row4 col0" >138.10</td>
      <td id="T_5e96b_row4_col1" class="data row4 col1" >16.40</td>
      <td id="T_5e96b_row4_col2" class="data row4 col2" >85</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row5" class="row_heading level0 row5" >Universität Irchel</th>
      <td id="T_5e96b_row5_col0" class="data row5 col0" >129.00</td>
      <td id="T_5e96b_row5_col1" class="data row5 col1" >19.60</td>
      <td id="T_5e96b_row5_col2" class="data row5 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row6" class="row_heading level0 row6" >Friedhof Enzenbühl</th>
      <td id="T_5e96b_row6_col0" class="data row6 col0" >128.70</td>
      <td id="T_5e96b_row6_col1" class="data row6 col1" >17.40</td>
      <td id="T_5e96b_row6_col2" class="data row6 col2" >43875</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row7" class="row_heading level0 row7" >Kantonsschule</th>
      <td id="T_5e96b_row7_col0" class="data row7 col0" >124.70</td>
      <td id="T_5e96b_row7_col1" class="data row7 col1" >25.50</td>
      <td id="T_5e96b_row7_col2" class="data row7 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row8" class="row_heading level0 row8" >Fernsehstudio</th>
      <td id="T_5e96b_row8_col0" class="data row8 col0" >121.60</td>
      <td id="T_5e96b_row8_col1" class="data row8 col1" >0.20</td>
      <td id="T_5e96b_row8_col2" class="data row8 col2" >45237</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row9" class="row_heading level0 row9" >Langmauerstrasse</th>
      <td id="T_5e96b_row9_col0" class="data row9 col0" >119.00</td>
      <td id="T_5e96b_row9_col1" class="data row9 col1" >19.10</td>
      <td id="T_5e96b_row9_col2" class="data row9 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row10" class="row_heading level0 row10" >Letzistrasse</th>
      <td id="T_5e96b_row10_col0" class="data row10 col0" >118.00</td>
      <td id="T_5e96b_row10_col1" class="data row10 col1" >14.90</td>
      <td id="T_5e96b_row10_col2" class="data row10 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row11" class="row_heading level0 row11" >Winkelriedstrasse</th>
      <td id="T_5e96b_row11_col0" class="data row11 col0" >116.00</td>
      <td id="T_5e96b_row11_col1" class="data row11 col1" >16.00</td>
      <td id="T_5e96b_row11_col2" class="data row11 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row12" class="row_heading level0 row12" >Kinkelstrasse</th>
      <td id="T_5e96b_row12_col0" class="data row12 col0" >110.00</td>
      <td id="T_5e96b_row12_col1" class="data row12 col1" >33.70</td>
      <td id="T_5e96b_row12_col2" class="data row12 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row13" class="row_heading level0 row13" >Seilbahn Rigiblick</th>
      <td id="T_5e96b_row13_col0" class="data row13 col0" >100.00</td>
      <td id="T_5e96b_row13_col1" class="data row13 col1" >28.20</td>
      <td id="T_5e96b_row13_col2" class="data row13 col2" >3</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row14" class="row_heading level0 row14" >Leutschenbach</th>
      <td id="T_5e96b_row14_col0" class="data row14 col0" >96.30</td>
      <td id="T_5e96b_row14_col1" class="data row14 col1" >12.30</td>
      <td id="T_5e96b_row14_col2" class="data row14 col2" >87914</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row15" class="row_heading level0 row15" >Hölderlinstrasse</th>
      <td id="T_5e96b_row15_col0" class="data row15 col0" >94.90</td>
      <td id="T_5e96b_row15_col1" class="data row15 col1" >29.60</td>
      <td id="T_5e96b_row15_col2" class="data row15 col2" >811</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row16" class="row_heading level0 row16" >Sternen Oerlikon</th>
      <td id="T_5e96b_row16_col0" class="data row16 col0" >92.10</td>
      <td id="T_5e96b_row16_col1" class="data row16 col1" >19.00</td>
      <td id="T_5e96b_row16_col2" class="data row16 col2" >84460</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row17" class="row_heading level0 row17" >Strassenverkehrsamt</th>
      <td id="T_5e96b_row17_col0" class="data row17 col0" >88.80</td>
      <td id="T_5e96b_row17_col1" class="data row17 col1" >15.00</td>
      <td id="T_5e96b_row17_col2" class="data row17 col2" >2651</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row18" class="row_heading level0 row18" >Balgrist</th>
      <td id="T_5e96b_row18_col0" class="data row18 col0" >81.50</td>
      <td id="T_5e96b_row18_col1" class="data row18 col1" >10.00</td>
      <td id="T_5e96b_row18_col2" class="data row18 col2" >87351</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row19" class="row_heading level0 row19" >Glattpark</th>
      <td id="T_5e96b_row19_col0" class="data row19 col0" >80.70</td>
      <td id="T_5e96b_row19_col1" class="data row19 col1" >13.90</td>
      <td id="T_5e96b_row19_col2" class="data row19 col2" >90026</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row20" class="row_heading level0 row20" >Wetlistrasse</th>
      <td id="T_5e96b_row20_col0" class="data row20 col0" >80.40</td>
      <td id="T_5e96b_row20_col1" class="data row20 col1" >21.70</td>
      <td id="T_5e96b_row20_col2" class="data row20 col2" >87211</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row21" class="row_heading level0 row21" >Messe/Hallenstadion</th>
      <td id="T_5e96b_row21_col0" class="data row21 col0" >80.20</td>
      <td id="T_5e96b_row21_col1" class="data row21 col1" >48.50</td>
      <td id="T_5e96b_row21_col2" class="data row21 col2" >87910</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row22" class="row_heading level0 row22" >Oerlikerhus</th>
      <td id="T_5e96b_row22_col0" class="data row22 col0" >80.00</td>
      <td id="T_5e96b_row22_col1" class="data row22 col1" >40.70</td>
      <td id="T_5e96b_row22_col2" class="data row22 col2" >90131</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row23" class="row_heading level0 row23" >Bahnhof Oerlikon</th>
      <td id="T_5e96b_row23_col0" class="data row23 col0" >79.70</td>
      <td id="T_5e96b_row23_col1" class="data row23 col1" >12.90</td>
      <td id="T_5e96b_row23_col2" class="data row23 col2" >87351</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row24" class="row_heading level0 row24" >Wildbachstrasse</th>
      <td id="T_5e96b_row24_col0" class="data row24 col0" >78.00</td>
      <td id="T_5e96b_row24_col1" class="data row24 col1" >29.70</td>
      <td id="T_5e96b_row24_col2" class="data row24 col2" >2443</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row25" class="row_heading level0 row25" >Burgwies</th>
      <td id="T_5e96b_row25_col0" class="data row25 col0" >77.90</td>
      <td id="T_5e96b_row25_col1" class="data row25 col1" >15.80</td>
      <td id="T_5e96b_row25_col2" class="data row25 col2" >86494</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row26" class="row_heading level0 row26" >Milchbuck</th>
      <td id="T_5e96b_row26_col0" class="data row26 col0" >75.30</td>
      <td id="T_5e96b_row26_col1" class="data row26 col1" >11.40</td>
      <td id="T_5e96b_row26_col2" class="data row26 col2" >158</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row27" class="row_heading level0 row27" >Hedwigsteig</th>
      <td id="T_5e96b_row27_col0" class="data row27 col0" >75.00</td>
      <td id="T_5e96b_row27_col1" class="data row27 col1" >-1.90</td>
      <td id="T_5e96b_row27_col2" class="data row27 col2" >86460</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row28" class="row_heading level0 row28" >Guggachstrasse</th>
      <td id="T_5e96b_row28_col0" class="data row28 col0" >74.90</td>
      <td id="T_5e96b_row28_col1" class="data row28 col1" >11.40</td>
      <td id="T_5e96b_row28_col2" class="data row28 col2" >155</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row29" class="row_heading level0 row29" >Regensbergbrücke</th>
      <td id="T_5e96b_row29_col0" class="data row29 col0" >73.10</td>
      <td id="T_5e96b_row29_col1" class="data row29 col1" >13.00</td>
      <td id="T_5e96b_row29_col2" class="data row29 col2" >88162</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row30" class="row_heading level0 row30" >Bad Allenmoos</th>
      <td id="T_5e96b_row30_col0" class="data row30 col0" >70.00</td>
      <td id="T_5e96b_row30_col1" class="data row30 col1" >17.30</td>
      <td id="T_5e96b_row30_col2" class="data row30 col2" >88224</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row31" class="row_heading level0 row31" >Römerhof</th>
      <td id="T_5e96b_row31_col0" class="data row31 col0" >69.20</td>
      <td id="T_5e96b_row31_col1" class="data row31 col1" >20.20</td>
      <td id="T_5e96b_row31_col2" class="data row31 col2" >1581</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row32" class="row_heading level0 row32" >Berninaplatz</th>
      <td id="T_5e96b_row32_col0" class="data row32 col0" >69.00</td>
      <td id="T_5e96b_row32_col1" class="data row32 col1" >28.50</td>
      <td id="T_5e96b_row32_col2" class="data row32 col2" >122</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row33" class="row_heading level0 row33" >Hegibachplatz B</th>
      <td id="T_5e96b_row33_col0" class="data row33 col0" >67.40</td>
      <td id="T_5e96b_row33_col1" class="data row33 col1" >30.20</td>
      <td id="T_5e96b_row33_col2" class="data row33 col2" >86900</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row34" class="row_heading level0 row34" >Kronenstrasse</th>
      <td id="T_5e96b_row34_col0" class="data row34 col0" >65.70</td>
      <td id="T_5e96b_row34_col1" class="data row34 col1" >12.60</td>
      <td id="T_5e96b_row34_col2" class="data row34 col2" >84859</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row35" class="row_heading level0 row35" >Salersteig</th>
      <td id="T_5e96b_row35_col0" class="data row35 col0" >65.50</td>
      <td id="T_5e96b_row35_col1" class="data row35 col1" >29.20</td>
      <td id="T_5e96b_row35_col2" class="data row35 col2" >122</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row36" class="row_heading level0 row36" >Signaustrasse</th>
      <td id="T_5e96b_row36_col0" class="data row36 col0" >65.00</td>
      <td id="T_5e96b_row36_col1" class="data row36 col1" >40.20</td>
      <td id="T_5e96b_row36_col2" class="data row36 col2" >87336</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row37" class="row_heading level0 row37" >Opernhaus</th>
      <td id="T_5e96b_row37_col0" class="data row37 col0" >64.60</td>
      <td id="T_5e96b_row37_col1" class="data row37 col1" >9.20</td>
      <td id="T_5e96b_row37_col2" class="data row37 col2" >4775</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row38" class="row_heading level0 row38" >Kreuzplatz</th>
      <td id="T_5e96b_row38_col0" class="data row38 col0" >63.80</td>
      <td id="T_5e96b_row38_col1" class="data row38 col1" >25.90</td>
      <td id="T_5e96b_row38_col2" class="data row38 col2" >80968</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row39" class="row_heading level0 row39" >Sihlcity Nord</th>
      <td id="T_5e96b_row39_col0" class="data row39 col0" >63.70</td>
      <td id="T_5e96b_row39_col1" class="data row39 col1" >22.60</td>
      <td id="T_5e96b_row39_col2" class="data row39 col2" >5310</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row40" class="row_heading level0 row40" >Sihlstrasse</th>
      <td id="T_5e96b_row40_col0" class="data row40 col0" >63.70</td>
      <td id="T_5e96b_row40_col1" class="data row40 col1" >17.40</td>
      <td id="T_5e96b_row40_col2" class="data row40 col2" >1593</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row41" class="row_heading level0 row41" >Uetlihof</th>
      <td id="T_5e96b_row41_col0" class="data row41 col0" >63.10</td>
      <td id="T_5e96b_row41_col1" class="data row41 col1" >32.60</td>
      <td id="T_5e96b_row41_col2" class="data row41 col2" >5288</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row42" class="row_heading level0 row42" >Brunnenhof</th>
      <td id="T_5e96b_row42_col0" class="data row42 col0" >62.80</td>
      <td id="T_5e96b_row42_col1" class="data row42 col1" >20.90</td>
      <td id="T_5e96b_row42_col2" class="data row42 col2" >88310</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row43" class="row_heading level0 row43" >Bahnhofstrasse/HB</th>
      <td id="T_5e96b_row43_col0" class="data row43 col0" >61.20</td>
      <td id="T_5e96b_row43_col1" class="data row43 col1" >13.80</td>
      <td id="T_5e96b_row43_col2" class="data row43 col2" >83617</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row44" class="row_heading level0 row44" >Schaffhauserplatz</th>
      <td id="T_5e96b_row44_col0" class="data row44 col0" >60.80</td>
      <td id="T_5e96b_row44_col1" class="data row44 col1" >17.50</td>
      <td id="T_5e96b_row44_col2" class="data row44 col2" >88171</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row45" class="row_heading level0 row45" >Stauffacher</th>
      <td id="T_5e96b_row45_col0" class="data row45 col0" >60.10</td>
      <td id="T_5e96b_row45_col1" class="data row45 col1" >4.70</td>
      <td id="T_5e96b_row45_col2" class="data row45 col2" >1453</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row46" class="row_heading level0 row46" >Beckenhof</th>
      <td id="T_5e96b_row46_col0" class="data row46 col0" >59.50</td>
      <td id="T_5e96b_row46_col1" class="data row46 col1" >31.00</td>
      <td id="T_5e96b_row46_col2" class="data row46 col2" >84913</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row47" class="row_heading level0 row47" >Tunnelstrasse</th>
      <td id="T_5e96b_row47_col0" class="data row47 col0" >58.30</td>
      <td id="T_5e96b_row47_col1" class="data row47 col1" >30.00</td>
      <td id="T_5e96b_row47_col2" class="data row47 col2" >5472</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row48" class="row_heading level0 row48" >Bucheggplatz D</th>
      <td id="T_5e96b_row48_col0" class="data row48 col0" >57.90</td>
      <td id="T_5e96b_row48_col1" class="data row48 col1" >13.30</td>
      <td id="T_5e96b_row48_col2" class="data row48 col2" >85999</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row49" class="row_heading level0 row49" >Stockerstrasse</th>
      <td id="T_5e96b_row49_col0" class="data row49 col0" >57.90</td>
      <td id="T_5e96b_row49_col1" class="data row49 col1" >22.00</td>
      <td id="T_5e96b_row49_col2" class="data row49 col2" >5591</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row50" class="row_heading level0 row50" >Bahnhof Stadelhofen</th>
      <td id="T_5e96b_row50_col0" class="data row50 col0" >57.80</td>
      <td id="T_5e96b_row50_col1" class="data row50 col1" >21.20</td>
      <td id="T_5e96b_row50_col2" class="data row50 col2" >80574</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row51" class="row_heading level0 row51" >Bürkliplatz</th>
      <td id="T_5e96b_row51_col0" class="data row51 col0" >57.60</td>
      <td id="T_5e96b_row51_col1" class="data row51 col1" >18.30</td>
      <td id="T_5e96b_row51_col2" class="data row51 col2" >95059</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row52" class="row_heading level0 row52" >Bahnhof Enge/Bederstr.</th>
      <td id="T_5e96b_row52_col0" class="data row52 col0" >57.10</td>
      <td id="T_5e96b_row52_col1" class="data row52 col1" >14.30</td>
      <td id="T_5e96b_row52_col2" class="data row52 col2" >5313</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row53" class="row_heading level0 row53" >Kreuzstrasse</th>
      <td id="T_5e96b_row53_col0" class="data row53 col0" >57.10</td>
      <td id="T_5e96b_row53_col1" class="data row53 col1" >24.50</td>
      <td id="T_5e96b_row53_col2" class="data row53 col2" >4850</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row54" class="row_heading level0 row54" >Laubegg</th>
      <td id="T_5e96b_row54_col0" class="data row54 col0" >56.80</td>
      <td id="T_5e96b_row54_col1" class="data row54 col1" >20.60</td>
      <td id="T_5e96b_row54_col2" class="data row54 col2" >5287</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row55" class="row_heading level0 row55" >Laubiweg</th>
      <td id="T_5e96b_row55_col0" class="data row55 col0" >56.80</td>
      <td id="T_5e96b_row55_col1" class="data row55 col1" >34.30</td>
      <td id="T_5e96b_row55_col2" class="data row55 col2" >88242</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row56" class="row_heading level0 row56" >Hirschwiesenstrasse</th>
      <td id="T_5e96b_row56_col0" class="data row56 col0" >56.50</td>
      <td id="T_5e96b_row56_col1" class="data row56 col1" >32.40</td>
      <td id="T_5e96b_row56_col2" class="data row56 col2" >158</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row57" class="row_heading level0 row57" >Stampfenbachplatz</th>
      <td id="T_5e96b_row57_col0" class="data row57 col0" >56.50</td>
      <td id="T_5e96b_row57_col1" class="data row57 col1" >22.60</td>
      <td id="T_5e96b_row57_col2" class="data row57 col2" >84771</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row58" class="row_heading level0 row58" >Waffenplatzstrasse</th>
      <td id="T_5e96b_row58_col0" class="data row58 col0" >56.40</td>
      <td id="T_5e96b_row58_col1" class="data row58 col1" >31.10</td>
      <td id="T_5e96b_row58_col2" class="data row58 col2" >5305</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row59" class="row_heading level0 row59" >Saalsporthalle</th>
      <td id="T_5e96b_row59_col0" class="data row59 col0" >55.90</td>
      <td id="T_5e96b_row59_col1" class="data row59 col1" >24.70</td>
      <td id="T_5e96b_row59_col2" class="data row59 col2" >5303</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row60" class="row_heading level0 row60" >Bellevue</th>
      <td id="T_5e96b_row60_col0" class="data row60 col0" >55.50</td>
      <td id="T_5e96b_row60_col1" class="data row60 col1" >14.30</td>
      <td id="T_5e96b_row60_col2" class="data row60 col2" >96116</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row61" class="row_heading level0 row61" >Hottingerplatz</th>
      <td id="T_5e96b_row61_col0" class="data row61 col0" >55.00</td>
      <td id="T_5e96b_row61_col1" class="data row61 col1" >11.50</td>
      <td id="T_5e96b_row61_col2" class="data row61 col2" >1508</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row62" class="row_heading level0 row62" >Sihlquai/HB</th>
      <td id="T_5e96b_row62_col0" class="data row62 col0" >54.00</td>
      <td id="T_5e96b_row62_col1" class="data row62 col1" >28.50</td>
      <td id="T_5e96b_row62_col2" class="data row62 col2" >1</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row63" class="row_heading level0 row63" >Höschgasse</th>
      <td id="T_5e96b_row63_col0" class="data row63 col0" >53.10</td>
      <td id="T_5e96b_row63_col1" class="data row63 col1" >30.00</td>
      <td id="T_5e96b_row63_col2" class="data row63 col2" >4846</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row64" class="row_heading level0 row64" >Bahnhofquai/HB</th>
      <td id="T_5e96b_row64_col0" class="data row64 col0" >52.40</td>
      <td id="T_5e96b_row64_col1" class="data row64 col1" >18.20</td>
      <td id="T_5e96b_row64_col2" class="data row64 col2" >84624</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row65" class="row_heading level0 row65" >Kantonalbank</th>
      <td id="T_5e96b_row65_col0" class="data row65 col0" >51.40</td>
      <td id="T_5e96b_row65_col1" class="data row65 col1" >15.50</td>
      <td id="T_5e96b_row65_col2" class="data row65 col2" >94895</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row66" class="row_heading level0 row66" >Kunsthaus</th>
      <td id="T_5e96b_row66_col0" class="data row66 col0" >51.30</td>
      <td id="T_5e96b_row66_col1" class="data row66 col1" >15.10</td>
      <td id="T_5e96b_row66_col2" class="data row66 col2" >1507</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row67" class="row_heading level0 row67" >Feldeggstrasse</th>
      <td id="T_5e96b_row67_col0" class="data row67 col0" >50.60</td>
      <td id="T_5e96b_row67_col1" class="data row67 col1" >31.90</td>
      <td id="T_5e96b_row67_col2" class="data row67 col2" >4859</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row68" class="row_heading level0 row68" >Paradeplatz</th>
      <td id="T_5e96b_row68_col0" class="data row68 col0" >50.50</td>
      <td id="T_5e96b_row68_col1" class="data row68 col1" >16.20</td>
      <td id="T_5e96b_row68_col2" class="data row68 col2" >95367</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row69" class="row_heading level0 row69" >Werd</th>
      <td id="T_5e96b_row69_col0" class="data row69 col0" >50.10</td>
      <td id="T_5e96b_row69_col1" class="data row69 col1" >22.30</td>
      <td id="T_5e96b_row69_col2" class="data row69 col2" >1390</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row70" class="row_heading level0 row70" >Rennweg</th>
      <td id="T_5e96b_row70_col0" class="data row70 col0" >49.80</td>
      <td id="T_5e96b_row70_col1" class="data row70 col1" >18.20</td>
      <td id="T_5e96b_row70_col2" class="data row70 col2" >88629</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row71" class="row_heading level0 row71" >Fröhlichstrasse</th>
      <td id="T_5e96b_row71_col0" class="data row71 col0" >49.40</td>
      <td id="T_5e96b_row71_col1" class="data row71 col1" >18.20</td>
      <td id="T_5e96b_row71_col2" class="data row71 col2" >4840</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row72" class="row_heading level0 row72" >Bahnhof Selnau</th>
      <td id="T_5e96b_row72_col0" class="data row72 col0" >43.30</td>
      <td id="T_5e96b_row72_col1" class="data row72 col1" >14.00</td>
      <td id="T_5e96b_row72_col2" class="data row72 col2" >111</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row73" class="row_heading level0 row73" >Sihlpost / HB</th>
      <td id="T_5e96b_row73_col0" class="data row73 col0" >41.60</td>
      <td id="T_5e96b_row73_col1" class="data row73 col1" >13.00</td>
      <td id="T_5e96b_row73_col2" class="data row73 col2" >845</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row74" class="row_heading level0 row74" >Letzigrund</th>
      <td id="T_5e96b_row74_col0" class="data row74 col0" >38.40</td>
      <td id="T_5e96b_row74_col1" class="data row74 col1" >3.80</td>
      <td id="T_5e96b_row74_col2" class="data row74 col2" >34</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row75" class="row_heading level0 row75" >Central</th>
      <td id="T_5e96b_row75_col0" class="data row75 col0" >36.00</td>
      <td id="T_5e96b_row75_col1" class="data row75 col1" >18.60</td>
      <td id="T_5e96b_row75_col2" class="data row75 col2" >3780</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row76" class="row_heading level0 row76" >Albisriederplatz B</th>
      <td id="T_5e96b_row76_col0" class="data row76 col0" >34.80</td>
      <td id="T_5e96b_row76_col1" class="data row76 col1" >10.90</td>
      <td id="T_5e96b_row76_col2" class="data row76 col2" >34</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row77" class="row_heading level0 row77" >Lochergut</th>
      <td id="T_5e96b_row77_col0" class="data row77 col0" >32.30</td>
      <td id="T_5e96b_row77_col1" class="data row77 col1" >18.90</td>
      <td id="T_5e96b_row77_col2" class="data row77 col2" >34</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row78" class="row_heading level0 row78" >Zypressenstrasse</th>
      <td id="T_5e96b_row78_col0" class="data row78 col0" >32.10</td>
      <td id="T_5e96b_row78_col1" class="data row78 col1" >12.40</td>
      <td id="T_5e96b_row78_col2" class="data row78 col2" >34</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row79" class="row_heading level0 row79" >Zürich,Kalkbreite/Bhf.Wiedikon</th>
      <td id="T_5e96b_row79_col0" class="data row79 col0" >31.40</td>
      <td id="T_5e96b_row79_col1" class="data row79 col1" >13.50</td>
      <td id="T_5e96b_row79_col2" class="data row79 col2" >34</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row80" class="row_heading level0 row80" >Löwenplatz</th>
      <td id="T_5e96b_row80_col0" class="data row80 col0" >29.70</td>
      <td id="T_5e96b_row80_col1" class="data row80 col1" >21.30</td>
      <td id="T_5e96b_row80_col2" class="data row80 col2" >849</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row81" class="row_heading level0 row81" >Rudolf-Brun-Brücke</th>
      <td id="T_5e96b_row81_col0" class="data row81 col0" >27.40</td>
      <td id="T_5e96b_row81_col1" class="data row81 col1" >29.50</td>
      <td id="T_5e96b_row81_col2" class="data row81 col2" >3475</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row82" class="row_heading level0 row82" >Rathaus</th>
      <td id="T_5e96b_row82_col0" class="data row82 col0" >26.60</td>
      <td id="T_5e96b_row82_col1" class="data row82 col1" >24.50</td>
      <td id="T_5e96b_row82_col2" class="data row82 col2" >3478</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row83" class="row_heading level0 row83" >Haldenegg</th>
      <td id="T_5e96b_row83_col0" class="data row83 col0" >26.40</td>
      <td id="T_5e96b_row83_col1" class="data row83 col1" >26.40</td>
      <td id="T_5e96b_row83_col2" class="data row83 col2" >3476</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row84" class="row_heading level0 row84" >Helmhaus</th>
      <td id="T_5e96b_row84_col0" class="data row84 col0" >26.30</td>
      <td id="T_5e96b_row84_col1" class="data row84 col1" >30.60</td>
      <td id="T_5e96b_row84_col2" class="data row84 col2" >3476</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row85" class="row_heading level0 row85" >Museum für Gestaltung</th>
      <td id="T_5e96b_row85_col0" class="data row85 col0" >24.00</td>
      <td id="T_5e96b_row85_col1" class="data row85 col1" >29.50</td>
      <td id="T_5e96b_row85_col2" class="data row85 col2" >1</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row86" class="row_heading level0 row86" >Röslistrasse</th>
      <td id="T_5e96b_row86_col0" class="data row86 col0" >23.20</td>
      <td id="T_5e96b_row86_col1" class="data row86 col1" >16.90</td>
      <td id="T_5e96b_row86_col2" class="data row86 col2" >3499</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row87" class="row_heading level0 row87" >Bahnhofplatz/HB</th>
      <td id="T_5e96b_row87_col0" class="data row87 col0" >22.60</td>
      <td id="T_5e96b_row87_col1" class="data row87 col1" >27.30</td>
      <td id="T_5e96b_row87_col2" class="data row87 col2" >851</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row88" class="row_heading level0 row88" >Sonneggstrasse</th>
      <td id="T_5e96b_row88_col0" class="data row88 col0" >22.30</td>
      <td id="T_5e96b_row88_col1" class="data row88 col1" >18.70</td>
      <td id="T_5e96b_row88_col2" class="data row88 col2" >3512</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row89" class="row_heading level0 row89" >Bezirksgebäude</th>
      <td id="T_5e96b_row89_col0" class="data row89 col0" >21.20</td>
      <td id="T_5e96b_row89_col1" class="data row89 col1" >23.70</td>
      <td id="T_5e96b_row89_col2" class="data row89 col2" >45</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row90" class="row_heading level0 row90" >Zch, Bhf.Wollishofen/Staubstr.</th>
      <td id="T_5e96b_row90_col0" class="data row90 col0" >18.40</td>
      <td id="T_5e96b_row90_col1" class="data row90 col1" >9.60</td>
      <td id="T_5e96b_row90_col2" class="data row90 col2" >40</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row91" class="row_heading level0 row91" >Limmatplatz</th>
      <td id="T_5e96b_row91_col0" class="data row91 col0" >18.00</td>
      <td id="T_5e96b_row91_col1" class="data row91 col1" >33.70</td>
      <td id="T_5e96b_row91_col2" class="data row91 col2" >1</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row92" class="row_heading level0 row92" >Quellenstrasse</th>
      <td id="T_5e96b_row92_col0" class="data row92 col0" >18.00</td>
      <td id="T_5e96b_row92_col1" class="data row92 col1" >31.10</td>
      <td id="T_5e96b_row92_col2" class="data row92 col2" >1</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row93" class="row_heading level0 row93" >Ottikerstrasse</th>
      <td id="T_5e96b_row93_col0" class="data row93 col0" >17.50</td>
      <td id="T_5e96b_row93_col1" class="data row93 col1" >16.80</td>
      <td id="T_5e96b_row93_col2" class="data row93 col2" >3513</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row94" class="row_heading level0 row94" >Billoweg</th>
      <td id="T_5e96b_row94_col0" class="data row94 col0" >17.40</td>
      <td id="T_5e96b_row94_col1" class="data row94 col1" >10.00</td>
      <td id="T_5e96b_row94_col2" class="data row94 col2" >40</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row95" class="row_heading level0 row95" >Brunaustrasse</th>
      <td id="T_5e96b_row95_col0" class="data row95 col0" >17.30</td>
      <td id="T_5e96b_row95_col1" class="data row95 col1" >26.90</td>
      <td id="T_5e96b_row95_col2" class="data row95 col2" >40</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row96" class="row_heading level0 row96" >Renggerstrasse</th>
      <td id="T_5e96b_row96_col0" class="data row96 col0" >14.60</td>
      <td id="T_5e96b_row96_col1" class="data row96 col1" >13.30</td>
      <td id="T_5e96b_row96_col2" class="data row96 col2" >40</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row97" class="row_heading level0 row97" >Bahnhof Enge</th>
      <td id="T_5e96b_row97_col0" class="data row97 col0" >-5.50</td>
      <td id="T_5e96b_row97_col1" class="data row97 col1" >23.40</td>
      <td id="T_5e96b_row97_col2" class="data row97 col2" >40</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row98" class="row_heading level0 row98" >Museum Rietberg</th>
      <td id="T_5e96b_row98_col0" class="data row98 col0" >-11.00</td>
      <td id="T_5e96b_row98_col1" class="data row98 col1" >31.30</td>
      <td id="T_5e96b_row98_col2" class="data row98 col2" >40</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row99" class="row_heading level0 row99" >Morgental</th>
      <td id="T_5e96b_row99_col0" class="data row99 col0" >-24.20</td>
      <td id="T_5e96b_row99_col1" class="data row99 col1" >43.70</td>
      <td id="T_5e96b_row99_col2" class="data row99 col2" >20</td>
    </tr>
    <tr>
      <th id="T_5e96b_level0_row100" class="row_heading level0 row100" >Butzenstrasse</th>
      <td id="T_5e96b_row100_col0" class="data row100 col0" >-28.30</td>
      <td id="T_5e96b_row100_col1" class="data row100 col1" >47.70</td>
      <td id="T_5e96b_row100_col2" class="data row100 col2" >20</td>
    </tr>
  </tbody>
</table>



## Schritt 4 — Netzweit: 0 → 60s


```python
sim_net = simulate_dwell(df_test, new_value=60, line_name=None)

mae_net_base = np.abs(sim_net["pred_base"] - sim_net["arrival_delay"]).mean()
mae_net_sim  = np.abs(sim_net["pred_sim"]  - sim_net["arrival_delay"]).mean()
mean_delta_net = sim_net["delta_delay"].mean()

print(f"Netzweit — 0→60s:")
print(f"  MAE Baseline:  {mae_net_base:.2f}s")
print(f"  MAE Simulation:{mae_net_sim:.2f}s")
print(f"  Ø Δ Delay:     {mean_delta_net:+.2f}s")

# Per-line summary
line_summary = (
    sim_net.groupby(sim_net["line_name"].astype(str))
    .agg(
        mean_delta=("delta_delay", "mean"),
        n=("delta_delay", "count"),
    )
    .reset_index()
    .sort_values("mean_delta")
)
line_summary["Ø Δ Delay (s)"] = line_summary["mean_delta"].round(1)
line_summary.insert(0, "Linie", line_summary["line_name"].apply(lambda x: f"L{x}"))
show_df(line_summary[["Linie", "Ø Δ Delay (s)", "n"]].set_index("Linie"))
```

    Netzweit — 0→60s:
      MAE Baseline:  45.74s
      MAE Simulation:52.46s
      Ø Δ Delay:     +20.72s



<style type="text/css">
#T_e9ca5 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_e9ca5 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_e9ca5 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_e9ca5 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_e9ca5 tr:hover td {
  background-color: #eef3f8;
}
#T_e9ca5_row0_col0, #T_e9ca5_row0_col1, #T_e9ca5_row1_col0, #T_e9ca5_row1_col1, #T_e9ca5_row2_col0, #T_e9ca5_row2_col1, #T_e9ca5_row3_col0, #T_e9ca5_row3_col1, #T_e9ca5_row4_col0, #T_e9ca5_row4_col1, #T_e9ca5_row5_col0, #T_e9ca5_row5_col1, #T_e9ca5_row6_col0, #T_e9ca5_row6_col1, #T_e9ca5_row7_col0, #T_e9ca5_row7_col1, #T_e9ca5_row8_col0, #T_e9ca5_row8_col1, #T_e9ca5_row9_col0, #T_e9ca5_row9_col1, #T_e9ca5_row10_col0, #T_e9ca5_row10_col1, #T_e9ca5_row11_col0, #T_e9ca5_row11_col1, #T_e9ca5_row12_col0, #T_e9ca5_row12_col1, #T_e9ca5_row13_col0, #T_e9ca5_row13_col1, #T_e9ca5_row14_col0, #T_e9ca5_row14_col1, #T_e9ca5_row15_col0, #T_e9ca5_row15_col1, #T_e9ca5_row16_col0, #T_e9ca5_row16_col1 {
  text-align: right;
}
</style>
<table id="T_e9ca5">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_e9ca5_level0_col0" class="col_heading level0 col0" >Ø Δ Delay (s)</th>
      <th id="T_e9ca5_level0_col1" class="col_heading level0 col1" >n</th>
    </tr>
    <tr>
      <th class="index_name level0" >Linie</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_e9ca5_level0_row0" class="row_heading level0 row0" >L3</th>
      <td id="T_e9ca5_row0_col0" class="data row0 col0" >16.10</td>
      <td id="T_e9ca5_row0_col1" class="data row0 col1" >1685982</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row1" class="row_heading level0 row1" >L8</th>
      <td id="T_e9ca5_row1_col0" class="data row1 col0" >19.00</td>
      <td id="T_e9ca5_row1_col1" class="data row1 col1" >2007818</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row2" class="row_heading level0 row2" >L9</th>
      <td id="T_e9ca5_row2_col0" class="data row2 col0" >19.50</td>
      <td id="T_e9ca5_row2_col1" class="data row2 col1" >2839792</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row3" class="row_heading level0 row3" >L17</th>
      <td id="T_e9ca5_row3_col0" class="data row3 col0" >19.70</td>
      <td id="T_e9ca5_row3_col1" class="data row3 col1" >1624041</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row4" class="row_heading level0 row4" >L50</th>
      <td id="T_e9ca5_row4_col0" class="data row4 col0" >19.90</td>
      <td id="T_e9ca5_row4_col1" class="data row4 col1" >142104</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row5" class="row_heading level0 row5" >L11</th>
      <td id="T_e9ca5_row5_col0" class="data row5 col0" >20.00</td>
      <td id="T_e9ca5_row5_col1" class="data row5 col1" >2834343</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row6" class="row_heading level0 row6" >L2</th>
      <td id="T_e9ca5_row6_col0" class="data row6 col0" >20.20</td>
      <td id="T_e9ca5_row6_col1" class="data row6 col1" >2689497</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row7" class="row_heading level0 row7" >L14</th>
      <td id="T_e9ca5_row7_col0" class="data row7 col0" >20.20</td>
      <td id="T_e9ca5_row7_col1" class="data row7 col1" >2191741</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row8" class="row_heading level0 row8" >L7</th>
      <td id="T_e9ca5_row8_col0" class="data row8 col0" >20.70</td>
      <td id="T_e9ca5_row8_col1" class="data row8 col1" >2683825</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row9" class="row_heading level0 row9" >L15</th>
      <td id="T_e9ca5_row9_col0" class="data row9 col0" >21.00</td>
      <td id="T_e9ca5_row9_col1" class="data row9 col1" >1019990</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row10" class="row_heading level0 row10" >L5</th>
      <td id="T_e9ca5_row10_col0" class="data row10 col0" >21.00</td>
      <td id="T_e9ca5_row10_col1" class="data row10 col1" >954246</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row11" class="row_heading level0 row11" >L4</th>
      <td id="T_e9ca5_row11_col0" class="data row11 col0" >21.30</td>
      <td id="T_e9ca5_row11_col1" class="data row11 col1" >2256185</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row12" class="row_heading level0 row12" >L6</th>
      <td id="T_e9ca5_row12_col0" class="data row12 col0" >21.70</td>
      <td id="T_e9ca5_row12_col1" class="data row12 col1" >1145448</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row13" class="row_heading level0 row13" >L13</th>
      <td id="T_e9ca5_row13_col0" class="data row13 col0" >22.30</td>
      <td id="T_e9ca5_row13_col1" class="data row13 col1" >2647723</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row14" class="row_heading level0 row14" >L51</th>
      <td id="T_e9ca5_row14_col0" class="data row14 col0" >22.70</td>
      <td id="T_e9ca5_row14_col1" class="data row14 col1" >115162</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row15" class="row_heading level0 row15" >L10</th>
      <td id="T_e9ca5_row15_col0" class="data row15 col0" >24.40</td>
      <td id="T_e9ca5_row15_col1" class="data row15 col1" >2266026</td>
    </tr>
    <tr>
      <th id="T_e9ca5_level0_row16" class="row_heading level0 row16" >L12</th>
      <td id="T_e9ca5_row16_col0" class="data row16 col0" >27.30</td>
      <td id="T_e9ca5_row16_col1" class="data row16 col1" >837953</td>
    </tr>
  </tbody>
</table>



## Key Findings

→ Vollständige Findings-Tabelle in [`03_analysis_0-overview.ipynb`](03_analysis_0-overview.ipynb).

`Präsentation`: **hot** = Kernbefund · **story** = gutes Narrativ · **—** = intern

| ID | Finding | Präsentation |
|:---|:---|:---:|
| F-SIM-01 | `dwell_time` ist Feature #1 in v1 (Gain 14.8M), aber faktisch **binär** in VBZ-Daten: entweder 0s (71.3%) oder 60s (28.5%). Werte zwischen 1–59s existieren nicht — jede Simulation mit +10s, +20s wäre out-of-distribution. | **hot** |
| F-SIM-02 | `dwell_time` korreliert **positiv** mit Delay (r=+0.16): Stops mit 60s haben ~28s mehr Delay als Stops mit 0s. Ursache: Konfundierung durch Stopschwierigkeit — VBZ gibt Puffer an komplexen Stops, die auch mehr Delay haben. Das Modell hat die Korrelation korrekt gelernt. | **hot** |
| F-SIM-03 | Simulation 0→60s: Modell erhöht Delay-Vorhersage um **+20s** (L11: +19.96s, Netzweit: +20.72s) — keine Verbesserung. **Feature Importance ≠ kausaler Hebel.** Das Modell kann nicht unterscheiden ob ein Stop dwell_time=60 hat weil er komplex ist (historisch) oder weil VBZ ihm Puffer gibt (hypothetisch). | **story** |
| F-SIM-04 | Operative Empfehlung trotzdem valide (Domänenwissen + F-SPAT-08): stopspezifische dwell_time kalibrieren statt pauschaler 0/60s — manche Stops brauchen 15s, andere 90s. Quantifizierung des Nutzens erfordert A/B-Test oder Instrumental Variable. Observational ML kann den Kausaleffekt nicht isolieren. | **story** |
