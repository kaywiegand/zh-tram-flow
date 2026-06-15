# Scheduling Recommendations — Modell-gestützte Fahrplanoptimierung

## Der vollständige Kreis

```
1. Analyse       → Delays identifizieren und messen
                   (63 strukturierte Findings, 6 Dimensionen)

2. Kernbefund    → Delays sind intrinsisch, nicht zufällig:
                   dwell_time = Feature #1 · Kaskadeneffekt r=0.85
                   71% aller Halte ohne Puffer → System kann Verspätung
                   nicht abbauen, nur weitergeben

3. Modell        → Vorhersage MAE 18.56s beweist Strukturalität:
                   Zufällige Delays sind nicht vorhersagbar.
                   Vorhersagbar = strukturell = steuerbar.

4. Empfehlung    → Modell-Outputs als Input für Fahrplandesign:
                   WO und WANN entstehen hohe Delays? → dort Puffer einplanen.
```

**Dieses Notebook:** Berechnet eine datengetriebene Empfehlungstabelle —
welche Haltestellen, auf welchen Linien, zu welchen Stunden und unter
welchen Bedingungen einen Fahrplan-Puffer brauchen.

**Wichtige Einschränkung (aus `06_prediction_6`):**
Das Modell sagt *wo und wann* das Risiko hoch ist — nicht *wie viel* Puffer optimal wäre.
Puffergrößen sind Startpunkte für operatives Testing, keine Modellausgaben.

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

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("06_prediction_7-scheduling_recommendations")

MODELS_DIR = Path(TRAIN).parent.parent / "models"
%load_ext autoreload
%autoreload 2
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-06-11 17:49:41  INFO      project  06_prediction_7-scheduling_recommendations started


    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload



```python
# lgbm_v1: schedule-based features only (no prev_trip_delay)
# → richtig für Fahrplanplanung: alle Features zum Planungszeitpunkt bekannt
# lgbm_v2 nutzt prev_trip_delay — das ist ein Echtzeitfeature, nicht planbar
model = lgb.Booster(model_file=str(MODELS_DIR / "lgbm_v1.txt"))

with open(MODELS_DIR / "lgbm_v1_meta.json") as f:
    meta = json.load(f)

FEATURE_COLS = meta["features"]
CAT_COLS = meta["cat_cols"]

# test_final.parquet hat alle Modell-Features (gtfs_year, dwell_time, n_lines_at_stop, etc.)
# test_features.parquet ist die Zwischen-Stufe vor dem Feature-Engineering → hier NICHT verwenden
TEST_FINAL = PATHS["processed"] / "test_final.parquet"

# Polars Lernmoment: lazy loading + cast in einer Pipeline, collect erst am Ende
df_test = (
    pl.scan_parquet(TEST_FINAL)
    .with_columns(pl.col("line_name").cast(pl.Utf8))
    .collect()
    .to_pandas()
)
for col in CAT_COLS:
    df_test[col] = df_test[col].astype("category")

df_test["pred"] = model.predict(df_test[FEATURE_COLS])

# Network reference values
NETWORK_MEAN = df_test["arrival_delay"].mean()
BUFFER_THRESHOLD = 60.0  # Stops with predicted delay above this get a buffer recommendation

print(f"Test rows: {len(df_test):,}")
print(f"Network Ø delay: {NETWORK_MEAN:.1f}s")
print(f"Buffer threshold: {BUFFER_THRESHOLD}s (above = buffer recommended)")
```

    Test rows: 29,941,876
    Network Ø delay: 54.9s
    Buffer threshold: 60.0s (above = buffer recommended)


## Risiko-Matrix: Stop × Linie × Stunde × Kontext

Für jede Kombination aus Haltestelle, Linie, Tageszeit und Betriebsbedingung
berechnet das Modell einen mittleren Delay. Das ist die Grundlage der Empfehlung.

**Kontexte:**
- `Normal` — Werktag, kein Schnee, kein Event
- `Schnee` — has_snow = True
- `Event` — has_event = True
- `Rush` — Donnerstag/Freitag 17–19h (schlechtester Peak laut Temporal-Analyse)
- `Spätnacht` — 21h+ (Post-Event-Welle)


```python
def assign_context(df: pd.DataFrame) -> pd.DataFrame:
    """Assign operational context label to each row."""
    df = df.copy()
    conditions = [
        df["has_snow"].astype(bool),
        df["has_event"].astype(bool) & (df["hour"] >= 18) & (df["hour"] <= 22),
        (df["weekday"].isin([3, 4])) & (df["hour"] >= 17) & (df["hour"] <= 19),
        df["hour"] >= 21,
    ]
    choices = ["Schnee", "Event", "Rush", "Spätnacht"]
    df["context"] = np.select(conditions, choices, default="Normal")
    return df


df_test = assign_context(df_test)
print(df_test["context"].value_counts().to_string())
```

    context
    Normal       21006898
    Event         7363202
    Spätnacht     1019700
    Rush           512156
    Schnee          39920



```python
# Aggregate: mean predicted delay per (stop, line, context)
# min_n=500 filtert statistisch instabile Gruppen
risk_matrix = (
    df_test
    .groupby(["stop_name", "line_name", "context"], observed=True)
    .agg(
        pred_delay=("pred", "mean"),
        actual_delay=("arrival_delay", "mean"),
        stop_lat=("stop_lat", "mean"),
        stop_lon=("stop_lon", "mean"),
        n=("pred", "count"),
    )
    .reset_index()
    .query("n >= 500")
)

# Buffer recommendation
risk_matrix["buffer_needed"] = risk_matrix["pred_delay"] > BUFFER_THRESHOLD
risk_matrix["excess_delay"] = (risk_matrix["pred_delay"] - BUFFER_THRESHOLD).clip(lower=0)

# Rough buffer heuristic: 1/3 of excess delay, rounded to 5s, capped at 60s
# Rationale: not all excess can be recovered at a single stop
risk_matrix["buffer_rec_s"] = (
    (risk_matrix["excess_delay"] / 3)
    .apply(lambda x: round(x / 5) * 5)
    .clip(upper=60)
    .where(risk_matrix["buffer_needed"], other=0)
    .astype(int)
)

n_flagged = risk_matrix["buffer_needed"].sum()
n_total = len(risk_matrix)
print(f"Stop-Linie-Kontext Kombinationen: {n_total:,}")
print(f"Davon mit Buffer-Empfehlung (pred > {BUFFER_THRESHOLD}s): {n_flagged:,} ({n_flagged/n_total:.1%})")
```

    Stop-Linie-Kontext Kombinationen: 1,933
    Davon mit Buffer-Empfehlung (pred > 60.0s): 395 (20.4%)


## Top-Empfehlungen — Prioritätsliste


```python
top_recs = (
    risk_matrix[risk_matrix["buffer_needed"]]
    .sort_values("pred_delay", ascending=False)
    .head(20)
    .copy()
)

top_recs["Haltestelle"] = top_recs["stop_name"].str.replace("Zürich, ", "", regex=False)
top_recs["Linie"] = top_recs["line_name"].apply(lambda x: f"L{x}")
top_recs["Ø Pred. Delay (s)"] = top_recs["pred_delay"].round(1)
top_recs["Ø Ist Delay (s)"] = top_recs["actual_delay"].round(1)
top_recs["Kontext"] = top_recs["context"]
top_recs["Buffer-Empfehlung (s)"] = top_recs["buffer_rec_s"]
top_recs["N"] = top_recs["n"]

show_df(
    top_recs[["Haltestelle", "Linie", "Kontext", "Ø Pred. Delay (s)", "Ø Ist Delay (s)", "Buffer-Empfehlung (s)", "N"]]
    .reset_index(drop=True)
)
```


<style type="text/css">
#T_5e92f thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_5e92f td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_5e92f tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_5e92f tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_5e92f tr:hover td {
  background-color: #eef3f8;
}
#T_5e92f_row0_col0, #T_5e92f_row0_col1, #T_5e92f_row0_col2, #T_5e92f_row1_col0, #T_5e92f_row1_col1, #T_5e92f_row1_col2, #T_5e92f_row2_col0, #T_5e92f_row2_col1, #T_5e92f_row2_col2, #T_5e92f_row3_col0, #T_5e92f_row3_col1, #T_5e92f_row3_col2, #T_5e92f_row4_col0, #T_5e92f_row4_col1, #T_5e92f_row4_col2, #T_5e92f_row5_col0, #T_5e92f_row5_col1, #T_5e92f_row5_col2, #T_5e92f_row6_col0, #T_5e92f_row6_col1, #T_5e92f_row6_col2, #T_5e92f_row7_col0, #T_5e92f_row7_col1, #T_5e92f_row7_col2, #T_5e92f_row8_col0, #T_5e92f_row8_col1, #T_5e92f_row8_col2, #T_5e92f_row9_col0, #T_5e92f_row9_col1, #T_5e92f_row9_col2, #T_5e92f_row10_col0, #T_5e92f_row10_col1, #T_5e92f_row10_col2, #T_5e92f_row11_col0, #T_5e92f_row11_col1, #T_5e92f_row11_col2, #T_5e92f_row12_col0, #T_5e92f_row12_col1, #T_5e92f_row12_col2, #T_5e92f_row13_col0, #T_5e92f_row13_col1, #T_5e92f_row13_col2, #T_5e92f_row14_col0, #T_5e92f_row14_col1, #T_5e92f_row14_col2, #T_5e92f_row15_col0, #T_5e92f_row15_col1, #T_5e92f_row15_col2, #T_5e92f_row16_col0, #T_5e92f_row16_col1, #T_5e92f_row16_col2, #T_5e92f_row17_col0, #T_5e92f_row17_col1, #T_5e92f_row17_col2, #T_5e92f_row18_col0, #T_5e92f_row18_col1, #T_5e92f_row18_col2, #T_5e92f_row19_col0, #T_5e92f_row19_col1, #T_5e92f_row19_col2 {
  text-align: left;
}
#T_5e92f_row0_col3, #T_5e92f_row0_col4, #T_5e92f_row0_col5, #T_5e92f_row0_col6, #T_5e92f_row1_col3, #T_5e92f_row1_col4, #T_5e92f_row1_col5, #T_5e92f_row1_col6, #T_5e92f_row2_col3, #T_5e92f_row2_col4, #T_5e92f_row2_col5, #T_5e92f_row2_col6, #T_5e92f_row3_col3, #T_5e92f_row3_col4, #T_5e92f_row3_col5, #T_5e92f_row3_col6, #T_5e92f_row4_col3, #T_5e92f_row4_col4, #T_5e92f_row4_col5, #T_5e92f_row4_col6, #T_5e92f_row5_col3, #T_5e92f_row5_col4, #T_5e92f_row5_col5, #T_5e92f_row5_col6, #T_5e92f_row6_col3, #T_5e92f_row6_col4, #T_5e92f_row6_col5, #T_5e92f_row6_col6, #T_5e92f_row7_col3, #T_5e92f_row7_col4, #T_5e92f_row7_col5, #T_5e92f_row7_col6, #T_5e92f_row8_col3, #T_5e92f_row8_col4, #T_5e92f_row8_col5, #T_5e92f_row8_col6, #T_5e92f_row9_col3, #T_5e92f_row9_col4, #T_5e92f_row9_col5, #T_5e92f_row9_col6, #T_5e92f_row10_col3, #T_5e92f_row10_col4, #T_5e92f_row10_col5, #T_5e92f_row10_col6, #T_5e92f_row11_col3, #T_5e92f_row11_col4, #T_5e92f_row11_col5, #T_5e92f_row11_col6, #T_5e92f_row12_col3, #T_5e92f_row12_col4, #T_5e92f_row12_col5, #T_5e92f_row12_col6, #T_5e92f_row13_col3, #T_5e92f_row13_col4, #T_5e92f_row13_col5, #T_5e92f_row13_col6, #T_5e92f_row14_col3, #T_5e92f_row14_col4, #T_5e92f_row14_col5, #T_5e92f_row14_col6, #T_5e92f_row15_col3, #T_5e92f_row15_col4, #T_5e92f_row15_col5, #T_5e92f_row15_col6, #T_5e92f_row16_col3, #T_5e92f_row16_col4, #T_5e92f_row16_col5, #T_5e92f_row16_col6, #T_5e92f_row17_col3, #T_5e92f_row17_col4, #T_5e92f_row17_col5, #T_5e92f_row17_col6, #T_5e92f_row18_col3, #T_5e92f_row18_col4, #T_5e92f_row18_col5, #T_5e92f_row18_col6, #T_5e92f_row19_col3, #T_5e92f_row19_col4, #T_5e92f_row19_col5, #T_5e92f_row19_col6 {
  text-align: right;
}
</style>
<table id="T_5e92f">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_5e92f_level0_col0" class="col_heading level0 col0" >Haltestelle</th>
      <th id="T_5e92f_level0_col1" class="col_heading level0 col1" >Linie</th>
      <th id="T_5e92f_level0_col2" class="col_heading level0 col2" >Kontext</th>
      <th id="T_5e92f_level0_col3" class="col_heading level0 col3" >Ø Pred. Delay (s)</th>
      <th id="T_5e92f_level0_col4" class="col_heading level0 col4" >Ø Ist Delay (s)</th>
      <th id="T_5e92f_level0_col5" class="col_heading level0 col5" >Buffer-Empfehlung (s)</th>
      <th id="T_5e92f_level0_col6" class="col_heading level0 col6" >N</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_5e92f_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_5e92f_row0_col0" class="data row0 col0" >Friedhof Enzenbühl</td>
      <td id="T_5e92f_row0_col1" class="data row0 col1" >L11</td>
      <td id="T_5e92f_row0_col2" class="data row0 col2" >Spätnacht</td>
      <td id="T_5e92f_row0_col3" class="data row0 col3" >136.80</td>
      <td id="T_5e92f_row0_col4" class="data row0 col4" >151.30</td>
      <td id="T_5e92f_row0_col5" class="data row0 col5" >25</td>
      <td id="T_5e92f_row0_col6" class="data row0 col6" >1171</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_5e92f_row1_col0" class="data row1 col0" >Altried</td>
      <td id="T_5e92f_row1_col1" class="data row1 col1" >L9</td>
      <td id="T_5e92f_row1_col2" class="data row1 col2" >Spätnacht</td>
      <td id="T_5e92f_row1_col3" class="data row1 col3" >124.60</td>
      <td id="T_5e92f_row1_col4" class="data row1 col4" >131.50</td>
      <td id="T_5e92f_row1_col5" class="data row1 col5" >20</td>
      <td id="T_5e92f_row1_col6" class="data row1 col6" >1650</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_5e92f_row2_col0" class="data row2 col0" >Friedhof Enzenbühl</td>
      <td id="T_5e92f_row2_col1" class="data row2 col1" >L15</td>
      <td id="T_5e92f_row2_col2" class="data row2 col2" >Normal</td>
      <td id="T_5e92f_row2_col3" class="data row2 col3" >123.20</td>
      <td id="T_5e92f_row2_col4" class="data row2 col4" >128.80</td>
      <td id="T_5e92f_row2_col5" class="data row2 col5" >20</td>
      <td id="T_5e92f_row2_col6" class="data row2 col6" >1423</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_5e92f_row3_col0" class="data row3 col0" >Friedhof Enzenbühl</td>
      <td id="T_5e92f_row3_col1" class="data row3 col1" >L4</td>
      <td id="T_5e92f_row3_col2" class="data row3 col2" >Event</td>
      <td id="T_5e92f_row3_col3" class="data row3 col3" >122.10</td>
      <td id="T_5e92f_row3_col4" class="data row3 col4" >142.40</td>
      <td id="T_5e92f_row3_col5" class="data row3 col5" >20</td>
      <td id="T_5e92f_row3_col6" class="data row3 col6" >632</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_5e92f_row4_col0" class="data row4 col0" >Seebacherplatz</td>
      <td id="T_5e92f_row4_col1" class="data row4 col1" >L14</td>
      <td id="T_5e92f_row4_col2" class="data row4 col2" >Spätnacht</td>
      <td id="T_5e92f_row4_col3" class="data row4 col3" >118.20</td>
      <td id="T_5e92f_row4_col4" class="data row4 col4" >116.00</td>
      <td id="T_5e92f_row4_col5" class="data row4 col5" >20</td>
      <td id="T_5e92f_row4_col6" class="data row4 col6" >1493</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_5e92f_row5_col0" class="data row5 col0" >Friedhof Enzenbühl</td>
      <td id="T_5e92f_row5_col1" class="data row5 col1" >L11</td>
      <td id="T_5e92f_row5_col2" class="data row5 col2" >Rush</td>
      <td id="T_5e92f_row5_col3" class="data row5 col3" >110.50</td>
      <td id="T_5e92f_row5_col4" class="data row5 col4" >141.80</td>
      <td id="T_5e92f_row5_col5" class="data row5 col5" >15</td>
      <td id="T_5e92f_row5_col6" class="data row5 col6" >767</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_5e92f_row6_col0" class="data row6 col0" >Friedhof Enzenbühl</td>
      <td id="T_5e92f_row6_col1" class="data row6 col1" >L4</td>
      <td id="T_5e92f_row6_col2" class="data row6 col2" >Normal</td>
      <td id="T_5e92f_row6_col3" class="data row6 col3" >109.70</td>
      <td id="T_5e92f_row6_col4" class="data row6 col4" >127.90</td>
      <td id="T_5e92f_row6_col5" class="data row6 col5" >15</td>
      <td id="T_5e92f_row6_col6" class="data row6 col6" >2054</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_5e92f_row7_col0" class="data row7 col0" >Fernsehstudio</td>
      <td id="T_5e92f_row7_col1" class="data row7 col1" >L11</td>
      <td id="T_5e92f_row7_col2" class="data row7 col2" >Rush</td>
      <td id="T_5e92f_row7_col3" class="data row7 col3" >108.50</td>
      <td id="T_5e92f_row7_col4" class="data row7 col4" >159.40</td>
      <td id="T_5e92f_row7_col5" class="data row7 col5" >15</td>
      <td id="T_5e92f_row7_col6" class="data row7 col6" >724</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_5e92f_row8_col0" class="data row8 col0" >Friedhof Enzenbühl</td>
      <td id="T_5e92f_row8_col1" class="data row8 col1" >L11</td>
      <td id="T_5e92f_row8_col2" class="data row8 col2" >Event</td>
      <td id="T_5e92f_row8_col3" class="data row8 col3" >108.30</td>
      <td id="T_5e92f_row8_col4" class="data row8 col4" >129.80</td>
      <td id="T_5e92f_row8_col5" class="data row8 col5" >15</td>
      <td id="T_5e92f_row8_col6" class="data row8 col6" >10100</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_5e92f_row9_col0" class="data row9 col0" >Friedhof Enzenbühl</td>
      <td id="T_5e92f_row9_col1" class="data row9 col1" >L11</td>
      <td id="T_5e92f_row9_col2" class="data row9 col2" >Normal</td>
      <td id="T_5e92f_row9_col3" class="data row9 col3" >108.20</td>
      <td id="T_5e92f_row9_col4" class="data row9 col4" >127.20</td>
      <td id="T_5e92f_row9_col5" class="data row9 col5" >15</td>
      <td id="T_5e92f_row9_col6" class="data row9 col6" >31773</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_5e92f_row10_col0" class="data row10 col0" >Fellenbergstrasse</td>
      <td id="T_5e92f_row10_col1" class="data row10 col1" >L3</td>
      <td id="T_5e92f_row10_col2" class="data row10 col2" >Rush</td>
      <td id="T_5e92f_row10_col3" class="data row10 col3" >101.80</td>
      <td id="T_5e92f_row10_col4" class="data row10 col4" >129.70</td>
      <td id="T_5e92f_row10_col5" class="data row10 col5" >15</td>
      <td id="T_5e92f_row10_col6" class="data row10 col6" >809</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_5e92f_row11_col0" class="data row11 col0" >Mattenhof</td>
      <td id="T_5e92f_row11_col1" class="data row11 col1" >L7</td>
      <td id="T_5e92f_row11_col2" class="data row11 col2" >Rush</td>
      <td id="T_5e92f_row11_col3" class="data row11 col3" >101.60</td>
      <td id="T_5e92f_row11_col4" class="data row11 col4" >159.90</td>
      <td id="T_5e92f_row11_col5" class="data row11 col5" >15</td>
      <td id="T_5e92f_row11_col6" class="data row11 col6" >732</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_5e92f_row12_col0" class="data row12 col0" >Butzenstrasse</td>
      <td id="T_5e92f_row12_col1" class="data row12 col1" >L7</td>
      <td id="T_5e92f_row12_col2" class="data row12 col2" >Rush</td>
      <td id="T_5e92f_row12_col3" class="data row12 col3" >100.20</td>
      <td id="T_5e92f_row12_col4" class="data row12 col4" >143.40</td>
      <td id="T_5e92f_row12_col5" class="data row12 col5" >15</td>
      <td id="T_5e92f_row12_col6" class="data row12 col6" >807</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_5e92f_row13_col0" class="data row13 col0" >Rentenanstalt</td>
      <td id="T_5e92f_row13_col1" class="data row13 col1" >L8</td>
      <td id="T_5e92f_row13_col2" class="data row13 col2" >Event</td>
      <td id="T_5e92f_row13_col3" class="data row13 col3" >100.00</td>
      <td id="T_5e92f_row13_col4" class="data row13 col4" >54.20</td>
      <td id="T_5e92f_row13_col5" class="data row13 col5" >15</td>
      <td id="T_5e92f_row13_col6" class="data row13 col6" >1192</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_5e92f_row14_col0" class="data row14 col0" >Hölderlinstrasse</td>
      <td id="T_5e92f_row14_col1" class="data row14 col1" >L8</td>
      <td id="T_5e92f_row14_col2" class="data row14 col2" >Event</td>
      <td id="T_5e92f_row14_col3" class="data row14 col3" >99.40</td>
      <td id="T_5e92f_row14_col4" class="data row14 col4" >115.70</td>
      <td id="T_5e92f_row14_col5" class="data row14 col5" >15</td>
      <td id="T_5e92f_row14_col6" class="data row14 col6" >11308</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_5e92f_row15_col0" class="data row15 col0" >Seebacherplatz</td>
      <td id="T_5e92f_row15_col1" class="data row15 col1" >L14</td>
      <td id="T_5e92f_row15_col2" class="data row15 col2" >Event</td>
      <td id="T_5e92f_row15_col3" class="data row15 col3" >99.20</td>
      <td id="T_5e92f_row15_col4" class="data row15 col4" >111.70</td>
      <td id="T_5e92f_row15_col5" class="data row15 col5" >15</td>
      <td id="T_5e92f_row15_col6" class="data row15 col6" >11227</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_5e92f_row16_col0" class="data row16 col0" >Würzgraben</td>
      <td id="T_5e92f_row16_col1" class="data row16 col1" >L51</td>
      <td id="T_5e92f_row16_col2" class="data row16 col2" >Event</td>
      <td id="T_5e92f_row16_col3" class="data row16 col3" >97.30</td>
      <td id="T_5e92f_row16_col4" class="data row16 col4" >57.60</td>
      <td id="T_5e92f_row16_col5" class="data row16 col5" >10</td>
      <td id="T_5e92f_row16_col6" class="data row16 col6" >579</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_5e92f_row17_col0" class="data row17 col0" >Seebacherplatz</td>
      <td id="T_5e92f_row17_col1" class="data row17 col1" >L14</td>
      <td id="T_5e92f_row17_col2" class="data row17 col2" >Rush</td>
      <td id="T_5e92f_row17_col3" class="data row17 col3" >95.10</td>
      <td id="T_5e92f_row17_col4" class="data row17 col4" >138.10</td>
      <td id="T_5e92f_row17_col5" class="data row17 col5" >10</td>
      <td id="T_5e92f_row17_col6" class="data row17 col6" >733</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_5e92f_row18_col0" class="data row18 col0" >Beckenhof</td>
      <td id="T_5e92f_row18_col1" class="data row18 col1" >L4</td>
      <td id="T_5e92f_row18_col2" class="data row18 col2" >Event</td>
      <td id="T_5e92f_row18_col3" class="data row18 col3" >93.30</td>
      <td id="T_5e92f_row18_col4" class="data row18 col4" >92.80</td>
      <td id="T_5e92f_row18_col5" class="data row18 col5" >10</td>
      <td id="T_5e92f_row18_col6" class="data row18 col6" >1338</td>
    </tr>
    <tr>
      <th id="T_5e92f_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_5e92f_row19_col0" class="data row19 col0" >Butzenstrasse</td>
      <td id="T_5e92f_row19_col1" class="data row19 col1" >L7</td>
      <td id="T_5e92f_row19_col2" class="data row19 col2" >Event</td>
      <td id="T_5e92f_row19_col3" class="data row19 col3" >93.10</td>
      <td id="T_5e92f_row19_col4" class="data row19 col4" >103.90</td>
      <td id="T_5e92f_row19_col5" class="data row19 col5" >10</td>
      <td id="T_5e92f_row19_col6" class="data row19 col6" >12527</td>
    </tr>
  </tbody>
</table>



## Kontext-Vergleich: Normal vs. Schnee vs. Event

Wie verändert sich das Risikobild je nach Betriebsbedingung?
Zeigt welche Linien/Stops kontextspezifische Puffer brauchen.


```python
# Per-line, per-context: mean predicted delay
line_context = (
    risk_matrix
    .groupby(["line_name", "context"], observed=True)["pred_delay"]
    .mean()
    .reset_index()
)

contexts = ["Normal", "Rush", "Event", "Schnee", "Spätnacht"]
colors   = ["#2E86AB", "#ffa600", "#de425b", "#6a5acd", "#25ac82"]

fig = go.Figure()

for ctx, col in zip(contexts, colors):
    sub = line_context[line_context["context"] == ctx].sort_values("pred_delay", ascending=False)
    fig.add_trace(go.Bar(
        name=ctx,
        x=sub["line_name"].apply(lambda x: f"L{x}"),
        y=sub["pred_delay"].round(1),
        marker_color=col,
    ))

fig.add_hline(
    y=BUFFER_THRESHOLD,
    line_dash="dot",
    line_color="#888",
    annotation_text=f"Buffer-Schwelle {BUFFER_THRESHOLD}s",
    annotation_position="top right",
)

fig.update_layout(
    barmode="group",
    title=dict(
        text="Ø Pred. Delay nach Linie × Kontext — Wann welche Linie Puffer braucht",
        x=0, xanchor="left",
    ),
    xaxis=dict(title="Linie"),
    yaxis=dict(title="Ø Pred. Delay (s)"),
    height=480,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(l=0, r=0, t=100, b=40),
    plot_bgcolor="white",
)
fig.show()

# Table: lines that need buffer in multiple contexts
buffer_by_line_ctx = (
    risk_matrix[risk_matrix["buffer_needed"]]
    .groupby(["line_name", "context"], observed=True)
    .agg(n_stops=("stop_name", "nunique"), mean_excess=("excess_delay", "mean"))
    .reset_index()
)
buffer_by_line_ctx["Linie"] = buffer_by_line_ctx["line_name"].apply(lambda x: f"L{x}")
buffer_by_line_ctx["Kontext"] = buffer_by_line_ctx["context"]
buffer_by_line_ctx["Stops mit Buffer-Bedarf"] = buffer_by_line_ctx["n_stops"]
buffer_by_line_ctx["Ø Überschuss (s)"] = buffer_by_line_ctx["mean_excess"].round(1)
show_df(
    buffer_by_line_ctx[["Linie", "Kontext", "Stops mit Buffer-Bedarf", "Ø Überschuss (s)"]]
    .sort_values(["Linie", "Kontext"])
    .reset_index(drop=True)
)
```




<style type="text/css">
#T_cee81 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_cee81 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_cee81 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_cee81 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_cee81 tr:hover td {
  background-color: #eef3f8;
}
#T_cee81_row0_col0, #T_cee81_row0_col1, #T_cee81_row1_col0, #T_cee81_row1_col1, #T_cee81_row2_col0, #T_cee81_row2_col1, #T_cee81_row3_col0, #T_cee81_row3_col1, #T_cee81_row4_col0, #T_cee81_row4_col1, #T_cee81_row5_col0, #T_cee81_row5_col1, #T_cee81_row6_col0, #T_cee81_row6_col1, #T_cee81_row7_col0, #T_cee81_row7_col1, #T_cee81_row8_col0, #T_cee81_row8_col1, #T_cee81_row9_col0, #T_cee81_row9_col1, #T_cee81_row10_col0, #T_cee81_row10_col1, #T_cee81_row11_col0, #T_cee81_row11_col1, #T_cee81_row12_col0, #T_cee81_row12_col1, #T_cee81_row13_col0, #T_cee81_row13_col1, #T_cee81_row14_col0, #T_cee81_row14_col1, #T_cee81_row15_col0, #T_cee81_row15_col1, #T_cee81_row16_col0, #T_cee81_row16_col1, #T_cee81_row17_col0, #T_cee81_row17_col1, #T_cee81_row18_col0, #T_cee81_row18_col1, #T_cee81_row19_col0, #T_cee81_row19_col1, #T_cee81_row20_col0, #T_cee81_row20_col1, #T_cee81_row21_col0, #T_cee81_row21_col1, #T_cee81_row22_col0, #T_cee81_row22_col1, #T_cee81_row23_col0, #T_cee81_row23_col1, #T_cee81_row24_col0, #T_cee81_row24_col1, #T_cee81_row25_col0, #T_cee81_row25_col1, #T_cee81_row26_col0, #T_cee81_row26_col1, #T_cee81_row27_col0, #T_cee81_row27_col1, #T_cee81_row28_col0, #T_cee81_row28_col1, #T_cee81_row29_col0, #T_cee81_row29_col1, #T_cee81_row30_col0, #T_cee81_row30_col1, #T_cee81_row31_col0, #T_cee81_row31_col1, #T_cee81_row32_col0, #T_cee81_row32_col1, #T_cee81_row33_col0, #T_cee81_row33_col1, #T_cee81_row34_col0, #T_cee81_row34_col1, #T_cee81_row35_col0, #T_cee81_row35_col1, #T_cee81_row36_col0, #T_cee81_row36_col1, #T_cee81_row37_col0, #T_cee81_row37_col1, #T_cee81_row38_col0, #T_cee81_row38_col1, #T_cee81_row39_col0, #T_cee81_row39_col1, #T_cee81_row40_col0, #T_cee81_row40_col1, #T_cee81_row41_col0, #T_cee81_row41_col1, #T_cee81_row42_col0, #T_cee81_row42_col1, #T_cee81_row43_col0, #T_cee81_row43_col1, #T_cee81_row44_col0, #T_cee81_row44_col1, #T_cee81_row45_col0, #T_cee81_row45_col1, #T_cee81_row46_col0, #T_cee81_row46_col1, #T_cee81_row47_col0, #T_cee81_row47_col1, #T_cee81_row48_col0, #T_cee81_row48_col1, #T_cee81_row49_col0, #T_cee81_row49_col1, #T_cee81_row50_col0, #T_cee81_row50_col1, #T_cee81_row51_col0, #T_cee81_row51_col1, #T_cee81_row52_col0, #T_cee81_row52_col1, #T_cee81_row53_col0, #T_cee81_row53_col1, #T_cee81_row54_col0, #T_cee81_row54_col1, #T_cee81_row55_col0, #T_cee81_row55_col1, #T_cee81_row56_col0, #T_cee81_row56_col1 {
  text-align: left;
}
#T_cee81_row0_col2, #T_cee81_row0_col3, #T_cee81_row1_col2, #T_cee81_row1_col3, #T_cee81_row2_col2, #T_cee81_row2_col3, #T_cee81_row3_col2, #T_cee81_row3_col3, #T_cee81_row4_col2, #T_cee81_row4_col3, #T_cee81_row5_col2, #T_cee81_row5_col3, #T_cee81_row6_col2, #T_cee81_row6_col3, #T_cee81_row7_col2, #T_cee81_row7_col3, #T_cee81_row8_col2, #T_cee81_row8_col3, #T_cee81_row9_col2, #T_cee81_row9_col3, #T_cee81_row10_col2, #T_cee81_row10_col3, #T_cee81_row11_col2, #T_cee81_row11_col3, #T_cee81_row12_col2, #T_cee81_row12_col3, #T_cee81_row13_col2, #T_cee81_row13_col3, #T_cee81_row14_col2, #T_cee81_row14_col3, #T_cee81_row15_col2, #T_cee81_row15_col3, #T_cee81_row16_col2, #T_cee81_row16_col3, #T_cee81_row17_col2, #T_cee81_row17_col3, #T_cee81_row18_col2, #T_cee81_row18_col3, #T_cee81_row19_col2, #T_cee81_row19_col3, #T_cee81_row20_col2, #T_cee81_row20_col3, #T_cee81_row21_col2, #T_cee81_row21_col3, #T_cee81_row22_col2, #T_cee81_row22_col3, #T_cee81_row23_col2, #T_cee81_row23_col3, #T_cee81_row24_col2, #T_cee81_row24_col3, #T_cee81_row25_col2, #T_cee81_row25_col3, #T_cee81_row26_col2, #T_cee81_row26_col3, #T_cee81_row27_col2, #T_cee81_row27_col3, #T_cee81_row28_col2, #T_cee81_row28_col3, #T_cee81_row29_col2, #T_cee81_row29_col3, #T_cee81_row30_col2, #T_cee81_row30_col3, #T_cee81_row31_col2, #T_cee81_row31_col3, #T_cee81_row32_col2, #T_cee81_row32_col3, #T_cee81_row33_col2, #T_cee81_row33_col3, #T_cee81_row34_col2, #T_cee81_row34_col3, #T_cee81_row35_col2, #T_cee81_row35_col3, #T_cee81_row36_col2, #T_cee81_row36_col3, #T_cee81_row37_col2, #T_cee81_row37_col3, #T_cee81_row38_col2, #T_cee81_row38_col3, #T_cee81_row39_col2, #T_cee81_row39_col3, #T_cee81_row40_col2, #T_cee81_row40_col3, #T_cee81_row41_col2, #T_cee81_row41_col3, #T_cee81_row42_col2, #T_cee81_row42_col3, #T_cee81_row43_col2, #T_cee81_row43_col3, #T_cee81_row44_col2, #T_cee81_row44_col3, #T_cee81_row45_col2, #T_cee81_row45_col3, #T_cee81_row46_col2, #T_cee81_row46_col3, #T_cee81_row47_col2, #T_cee81_row47_col3, #T_cee81_row48_col2, #T_cee81_row48_col3, #T_cee81_row49_col2, #T_cee81_row49_col3, #T_cee81_row50_col2, #T_cee81_row50_col3, #T_cee81_row51_col2, #T_cee81_row51_col3, #T_cee81_row52_col2, #T_cee81_row52_col3, #T_cee81_row53_col2, #T_cee81_row53_col3, #T_cee81_row54_col2, #T_cee81_row54_col3, #T_cee81_row55_col2, #T_cee81_row55_col3, #T_cee81_row56_col2, #T_cee81_row56_col3 {
  text-align: right;
}
</style>
<table id="T_cee81">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_cee81_level0_col0" class="col_heading level0 col0" >Linie</th>
      <th id="T_cee81_level0_col1" class="col_heading level0 col1" >Kontext</th>
      <th id="T_cee81_level0_col2" class="col_heading level0 col2" >Stops mit Buffer-Bedarf</th>
      <th id="T_cee81_level0_col3" class="col_heading level0 col3" >Ø Überschuss (s)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_cee81_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_cee81_row0_col0" class="data row0 col0" >L10</td>
      <td id="T_cee81_row0_col1" class="data row0 col1" >Event</td>
      <td id="T_cee81_row0_col2" class="data row0 col2" >10</td>
      <td id="T_cee81_row0_col3" class="data row0 col3" >7.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_cee81_row1_col0" class="data row1 col0" >L10</td>
      <td id="T_cee81_row1_col1" class="data row1 col1" >Normal</td>
      <td id="T_cee81_row1_col2" class="data row1 col2" >1</td>
      <td id="T_cee81_row1_col3" class="data row1 col3" >12.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_cee81_row2_col0" class="data row2 col0" >L10</td>
      <td id="T_cee81_row2_col1" class="data row2 col1" >Rush</td>
      <td id="T_cee81_row2_col2" class="data row2 col2" >10</td>
      <td id="T_cee81_row2_col3" class="data row2 col3" >10.50</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_cee81_row3_col0" class="data row3 col0" >L10</td>
      <td id="T_cee81_row3_col1" class="data row3 col1" >Spätnacht</td>
      <td id="T_cee81_row3_col2" class="data row3 col2" >8</td>
      <td id="T_cee81_row3_col3" class="data row3 col3" >3.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_cee81_row4_col0" class="data row4 col0" >L11</td>
      <td id="T_cee81_row4_col1" class="data row4 col1" >Event</td>
      <td id="T_cee81_row4_col2" class="data row4 col2" >18</td>
      <td id="T_cee81_row4_col3" class="data row4 col3" >12.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_cee81_row5_col0" class="data row5 col0" >L11</td>
      <td id="T_cee81_row5_col1" class="data row5 col1" >Normal</td>
      <td id="T_cee81_row5_col2" class="data row5 col2" >14</td>
      <td id="T_cee81_row5_col3" class="data row5 col3" >9.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_cee81_row6_col0" class="data row6 col0" >L11</td>
      <td id="T_cee81_row6_col1" class="data row6 col1" >Rush</td>
      <td id="T_cee81_row6_col2" class="data row6 col2" >16</td>
      <td id="T_cee81_row6_col3" class="data row6 col3" >15.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_cee81_row7_col0" class="data row7 col0" >L11</td>
      <td id="T_cee81_row7_col1" class="data row7 col1" >Spätnacht</td>
      <td id="T_cee81_row7_col2" class="data row7 col2" >12</td>
      <td id="T_cee81_row7_col3" class="data row7 col3" >18.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_cee81_row8_col0" class="data row8 col0" >L12</td>
      <td id="T_cee81_row8_col1" class="data row8 col1" >Event</td>
      <td id="T_cee81_row8_col2" class="data row8 col2" >1</td>
      <td id="T_cee81_row8_col3" class="data row8 col3" >5.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_cee81_row9_col0" class="data row9 col0" >L12</td>
      <td id="T_cee81_row9_col1" class="data row9 col1" >Rush</td>
      <td id="T_cee81_row9_col2" class="data row9 col2" >10</td>
      <td id="T_cee81_row9_col3" class="data row9 col3" >11.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_cee81_row10_col0" class="data row10 col0" >L12</td>
      <td id="T_cee81_row10_col1" class="data row10 col1" >Spätnacht</td>
      <td id="T_cee81_row10_col2" class="data row10 col2" >1</td>
      <td id="T_cee81_row10_col3" class="data row10 col3" >0.70</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_cee81_row11_col0" class="data row11 col0" >L13</td>
      <td id="T_cee81_row11_col1" class="data row11 col1" >Event</td>
      <td id="T_cee81_row11_col2" class="data row11 col2" >10</td>
      <td id="T_cee81_row11_col3" class="data row11 col3" >6.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_cee81_row12_col0" class="data row12 col0" >L13</td>
      <td id="T_cee81_row12_col1" class="data row12 col1" >Normal</td>
      <td id="T_cee81_row12_col2" class="data row12 col2" >2</td>
      <td id="T_cee81_row12_col3" class="data row12 col3" >15.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_cee81_row13_col0" class="data row13 col0" >L13</td>
      <td id="T_cee81_row13_col1" class="data row13 col1" >Rush</td>
      <td id="T_cee81_row13_col2" class="data row13 col2" >2</td>
      <td id="T_cee81_row13_col3" class="data row13 col3" >10.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_cee81_row14_col0" class="data row14 col0" >L13</td>
      <td id="T_cee81_row14_col1" class="data row14 col1" >Spätnacht</td>
      <td id="T_cee81_row14_col2" class="data row14 col2" >1</td>
      <td id="T_cee81_row14_col3" class="data row14 col3" >15.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_cee81_row15_col0" class="data row15 col0" >L14</td>
      <td id="T_cee81_row15_col1" class="data row15 col1" >Event</td>
      <td id="T_cee81_row15_col2" class="data row15 col2" >6</td>
      <td id="T_cee81_row15_col3" class="data row15 col3" >13.10</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_cee81_row16_col0" class="data row16 col0" >L14</td>
      <td id="T_cee81_row16_col1" class="data row16 col1" >Normal</td>
      <td id="T_cee81_row16_col2" class="data row16 col2" >3</td>
      <td id="T_cee81_row16_col3" class="data row16 col3" >13.70</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_cee81_row17_col0" class="data row17 col0" >L14</td>
      <td id="T_cee81_row17_col1" class="data row17 col1" >Rush</td>
      <td id="T_cee81_row17_col2" class="data row17 col2" >4</td>
      <td id="T_cee81_row17_col3" class="data row17 col3" >13.70</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_cee81_row18_col0" class="data row18 col0" >L14</td>
      <td id="T_cee81_row18_col1" class="data row18 col1" >Spätnacht</td>
      <td id="T_cee81_row18_col2" class="data row18 col2" >12</td>
      <td id="T_cee81_row18_col3" class="data row18 col3" >12.50</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_cee81_row19_col0" class="data row19 col0" >L15</td>
      <td id="T_cee81_row19_col1" class="data row19 col1" >Event</td>
      <td id="T_cee81_row19_col2" class="data row19 col2" >23</td>
      <td id="T_cee81_row19_col3" class="data row19 col3" >9.00</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_cee81_row20_col0" class="data row20 col0" >L15</td>
      <td id="T_cee81_row20_col1" class="data row20 col1" >Normal</td>
      <td id="T_cee81_row20_col2" class="data row20 col2" >21</td>
      <td id="T_cee81_row20_col3" class="data row20 col3" >11.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_cee81_row21_col0" class="data row21 col0" >L15</td>
      <td id="T_cee81_row21_col1" class="data row21 col1" >Rush</td>
      <td id="T_cee81_row21_col2" class="data row21 col2" >7</td>
      <td id="T_cee81_row21_col3" class="data row21 col3" >7.00</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_cee81_row22_col0" class="data row22 col0" >L15</td>
      <td id="T_cee81_row22_col1" class="data row22 col1" >Spätnacht</td>
      <td id="T_cee81_row22_col2" class="data row22 col2" >1</td>
      <td id="T_cee81_row22_col3" class="data row22 col3" >7.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_cee81_row23_col0" class="data row23 col0" >L17</td>
      <td id="T_cee81_row23_col1" class="data row23 col1" >Event</td>
      <td id="T_cee81_row23_col2" class="data row23 col2" >1</td>
      <td id="T_cee81_row23_col3" class="data row23 col3" >14.40</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row24" class="row_heading level0 row24" >24</th>
      <td id="T_cee81_row24_col0" class="data row24 col0" >L17</td>
      <td id="T_cee81_row24_col1" class="data row24 col1" >Normal</td>
      <td id="T_cee81_row24_col2" class="data row24 col2" >5</td>
      <td id="T_cee81_row24_col3" class="data row24 col3" >7.00</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row25" class="row_heading level0 row25" >25</th>
      <td id="T_cee81_row25_col0" class="data row25 col0" >L17</td>
      <td id="T_cee81_row25_col1" class="data row25 col1" >Rush</td>
      <td id="T_cee81_row25_col2" class="data row25 col2" >2</td>
      <td id="T_cee81_row25_col3" class="data row25 col3" >14.40</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row26" class="row_heading level0 row26" >26</th>
      <td id="T_cee81_row26_col0" class="data row26 col0" >L2</td>
      <td id="T_cee81_row26_col1" class="data row26 col1" >Event</td>
      <td id="T_cee81_row26_col2" class="data row26 col2" >7</td>
      <td id="T_cee81_row26_col3" class="data row26 col3" >7.70</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row27" class="row_heading level0 row27" >27</th>
      <td id="T_cee81_row27_col0" class="data row27 col0" >L2</td>
      <td id="T_cee81_row27_col1" class="data row27 col1" >Normal</td>
      <td id="T_cee81_row27_col2" class="data row27 col2" >4</td>
      <td id="T_cee81_row27_col3" class="data row27 col3" >3.60</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row28" class="row_heading level0 row28" >28</th>
      <td id="T_cee81_row28_col0" class="data row28 col0" >L2</td>
      <td id="T_cee81_row28_col1" class="data row28 col1" >Rush</td>
      <td id="T_cee81_row28_col2" class="data row28 col2" >2</td>
      <td id="T_cee81_row28_col3" class="data row28 col3" >15.70</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row29" class="row_heading level0 row29" >29</th>
      <td id="T_cee81_row29_col0" class="data row29 col0" >L2</td>
      <td id="T_cee81_row29_col1" class="data row29 col1" >Spätnacht</td>
      <td id="T_cee81_row29_col2" class="data row29 col2" >5</td>
      <td id="T_cee81_row29_col3" class="data row29 col3" >9.00</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row30" class="row_heading level0 row30" >30</th>
      <td id="T_cee81_row30_col0" class="data row30 col0" >L3</td>
      <td id="T_cee81_row30_col1" class="data row30 col1" >Event</td>
      <td id="T_cee81_row30_col2" class="data row30 col2" >2</td>
      <td id="T_cee81_row30_col3" class="data row30 col3" >16.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row31" class="row_heading level0 row31" >31</th>
      <td id="T_cee81_row31_col0" class="data row31 col0" >L3</td>
      <td id="T_cee81_row31_col1" class="data row31 col1" >Normal</td>
      <td id="T_cee81_row31_col2" class="data row31 col2" >2</td>
      <td id="T_cee81_row31_col3" class="data row31 col3" >9.60</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row32" class="row_heading level0 row32" >32</th>
      <td id="T_cee81_row32_col0" class="data row32 col0" >L3</td>
      <td id="T_cee81_row32_col1" class="data row32 col1" >Rush</td>
      <td id="T_cee81_row32_col2" class="data row32 col2" >4</td>
      <td id="T_cee81_row32_col3" class="data row32 col3" >12.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row33" class="row_heading level0 row33" >33</th>
      <td id="T_cee81_row33_col0" class="data row33 col0" >L3</td>
      <td id="T_cee81_row33_col1" class="data row33 col1" >Spätnacht</td>
      <td id="T_cee81_row33_col2" class="data row33 col2" >2</td>
      <td id="T_cee81_row33_col3" class="data row33 col3" >13.60</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row34" class="row_heading level0 row34" >34</th>
      <td id="T_cee81_row34_col0" class="data row34 col0" >L4</td>
      <td id="T_cee81_row34_col1" class="data row34 col1" >Event</td>
      <td id="T_cee81_row34_col2" class="data row34 col2" >25</td>
      <td id="T_cee81_row34_col3" class="data row34 col3" >13.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row35" class="row_heading level0 row35" >35</th>
      <td id="T_cee81_row35_col0" class="data row35 col0" >L4</td>
      <td id="T_cee81_row35_col1" class="data row35 col1" >Normal</td>
      <td id="T_cee81_row35_col2" class="data row35 col2" >14</td>
      <td id="T_cee81_row35_col3" class="data row35 col3" >12.50</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row36" class="row_heading level0 row36" >36</th>
      <td id="T_cee81_row36_col0" class="data row36 col0" >L4</td>
      <td id="T_cee81_row36_col1" class="data row36 col1" >Rush</td>
      <td id="T_cee81_row36_col2" class="data row36 col2" >17</td>
      <td id="T_cee81_row36_col3" class="data row36 col3" >4.10</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row37" class="row_heading level0 row37" >37</th>
      <td id="T_cee81_row37_col0" class="data row37 col0" >L4</td>
      <td id="T_cee81_row37_col1" class="data row37 col1" >Spätnacht</td>
      <td id="T_cee81_row37_col2" class="data row37 col2" >4</td>
      <td id="T_cee81_row37_col3" class="data row37 col3" >16.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row38" class="row_heading level0 row38" >38</th>
      <td id="T_cee81_row38_col0" class="data row38 col0" >L5</td>
      <td id="T_cee81_row38_col1" class="data row38 col1" >Event</td>
      <td id="T_cee81_row38_col2" class="data row38 col2" >7</td>
      <td id="T_cee81_row38_col3" class="data row38 col3" >13.40</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row39" class="row_heading level0 row39" >39</th>
      <td id="T_cee81_row39_col0" class="data row39 col0" >L5</td>
      <td id="T_cee81_row39_col1" class="data row39 col1" >Normal</td>
      <td id="T_cee81_row39_col2" class="data row39 col2" >1</td>
      <td id="T_cee81_row39_col3" class="data row39 col3" >9.90</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row40" class="row_heading level0 row40" >40</th>
      <td id="T_cee81_row40_col0" class="data row40 col0" >L50</td>
      <td id="T_cee81_row40_col1" class="data row40 col1" >Event</td>
      <td id="T_cee81_row40_col2" class="data row40 col2" >14</td>
      <td id="T_cee81_row40_col3" class="data row40 col3" >9.40</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row41" class="row_heading level0 row41" >41</th>
      <td id="T_cee81_row41_col0" class="data row41 col0" >L50</td>
      <td id="T_cee81_row41_col1" class="data row41 col1" >Normal</td>
      <td id="T_cee81_row41_col2" class="data row41 col2" >6</td>
      <td id="T_cee81_row41_col3" class="data row41 col3" >7.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row42" class="row_heading level0 row42" >42</th>
      <td id="T_cee81_row42_col0" class="data row42 col0" >L51</td>
      <td id="T_cee81_row42_col1" class="data row42 col1" >Event</td>
      <td id="T_cee81_row42_col2" class="data row42 col2" >6</td>
      <td id="T_cee81_row42_col3" class="data row42 col3" >14.30</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row43" class="row_heading level0 row43" >43</th>
      <td id="T_cee81_row43_col0" class="data row43 col0" >L51</td>
      <td id="T_cee81_row43_col1" class="data row43 col1" >Normal</td>
      <td id="T_cee81_row43_col2" class="data row43 col2" >2</td>
      <td id="T_cee81_row43_col3" class="data row43 col3" >19.30</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row44" class="row_heading level0 row44" >44</th>
      <td id="T_cee81_row44_col0" class="data row44 col0" >L6</td>
      <td id="T_cee81_row44_col1" class="data row44 col1" >Event</td>
      <td id="T_cee81_row44_col2" class="data row44 col2" >2</td>
      <td id="T_cee81_row44_col3" class="data row44 col3" >5.80</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row45" class="row_heading level0 row45" >45</th>
      <td id="T_cee81_row45_col0" class="data row45 col0" >L7</td>
      <td id="T_cee81_row45_col1" class="data row45 col1" >Event</td>
      <td id="T_cee81_row45_col2" class="data row45 col2" >3</td>
      <td id="T_cee81_row45_col3" class="data row45 col3" >20.40</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row46" class="row_heading level0 row46" >46</th>
      <td id="T_cee81_row46_col0" class="data row46 col0" >L7</td>
      <td id="T_cee81_row46_col1" class="data row46 col1" >Normal</td>
      <td id="T_cee81_row46_col2" class="data row46 col2" >4</td>
      <td id="T_cee81_row46_col3" class="data row46 col3" >11.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row47" class="row_heading level0 row47" >47</th>
      <td id="T_cee81_row47_col0" class="data row47 col0" >L7</td>
      <td id="T_cee81_row47_col1" class="data row47 col1" >Rush</td>
      <td id="T_cee81_row47_col2" class="data row47 col2" >6</td>
      <td id="T_cee81_row47_col3" class="data row47 col3" >14.80</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row48" class="row_heading level0 row48" >48</th>
      <td id="T_cee81_row48_col0" class="data row48 col0" >L7</td>
      <td id="T_cee81_row48_col1" class="data row48 col1" >Spätnacht</td>
      <td id="T_cee81_row48_col2" class="data row48 col2" >4</td>
      <td id="T_cee81_row48_col3" class="data row48 col3" >13.30</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row49" class="row_heading level0 row49" >49</th>
      <td id="T_cee81_row49_col0" class="data row49 col0" >L8</td>
      <td id="T_cee81_row49_col1" class="data row49 col1" >Event</td>
      <td id="T_cee81_row49_col2" class="data row49 col2" >14</td>
      <td id="T_cee81_row49_col3" class="data row49 col3" >12.50</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row50" class="row_heading level0 row50" >50</th>
      <td id="T_cee81_row50_col0" class="data row50 col0" >L8</td>
      <td id="T_cee81_row50_col1" class="data row50 col1" >Normal</td>
      <td id="T_cee81_row50_col2" class="data row50 col2" >2</td>
      <td id="T_cee81_row50_col3" class="data row50 col3" >13.10</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row51" class="row_heading level0 row51" >51</th>
      <td id="T_cee81_row51_col0" class="data row51 col0" >L8</td>
      <td id="T_cee81_row51_col1" class="data row51 col1" >Rush</td>
      <td id="T_cee81_row51_col2" class="data row51 col2" >5</td>
      <td id="T_cee81_row51_col3" class="data row51 col3" >9.00</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row52" class="row_heading level0 row52" >52</th>
      <td id="T_cee81_row52_col0" class="data row52 col0" >L8</td>
      <td id="T_cee81_row52_col1" class="data row52 col1" >Spätnacht</td>
      <td id="T_cee81_row52_col2" class="data row52 col2" >9</td>
      <td id="T_cee81_row52_col3" class="data row52 col3" >11.00</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row53" class="row_heading level0 row53" >53</th>
      <td id="T_cee81_row53_col0" class="data row53 col0" >L9</td>
      <td id="T_cee81_row53_col1" class="data row53 col1" >Event</td>
      <td id="T_cee81_row53_col2" class="data row53 col2" >4</td>
      <td id="T_cee81_row53_col3" class="data row53 col3" >14.00</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row54" class="row_heading level0 row54" >54</th>
      <td id="T_cee81_row54_col0" class="data row54 col0" >L9</td>
      <td id="T_cee81_row54_col1" class="data row54 col1" >Normal</td>
      <td id="T_cee81_row54_col2" class="data row54 col2" >1</td>
      <td id="T_cee81_row54_col3" class="data row54 col3" >11.60</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row55" class="row_heading level0 row55" >55</th>
      <td id="T_cee81_row55_col0" class="data row55 col0" >L9</td>
      <td id="T_cee81_row55_col1" class="data row55 col1" >Rush</td>
      <td id="T_cee81_row55_col2" class="data row55 col2" >1</td>
      <td id="T_cee81_row55_col3" class="data row55 col3" >3.20</td>
    </tr>
    <tr>
      <th id="T_cee81_level0_row56" class="row_heading level0 row56" >56</th>
      <td id="T_cee81_row56_col0" class="data row56 col0" >L9</td>
      <td id="T_cee81_row56_col1" class="data row56 col1" >Spätnacht</td>
      <td id="T_cee81_row56_col2" class="data row56 col2" >15</td>
      <td id="T_cee81_row56_col3" class="data row56 col3" >14.30</td>
    </tr>
  </tbody>
</table>



## Karte: Wo braucht es Puffer?

Alle Haltestellen mit Buffer-Empfehlung — Farbe nach Kontext, Größe nach empfohlenem Puffer.
Filter auf Normal-Kontext um den strukturellen Basisbedarf zu zeigen.


```python
ctx_colors = {
    "Normal":    "#2E86AB",
    "Rush":      "#ffa600",
    "Event":     "#de425b",
    "Schnee":    "#6a5acd",
    "Spätnacht": "#25ac82",
}

flagged = risk_matrix[risk_matrix["buffer_needed"]].copy()
flagged["stop_short"] = flagged["stop_name"].str.replace("Zürich, ", "", regex=False)
flagged["bubble"] = 8 + (flagged["buffer_rec_s"] / 60) * 20  # scale 8–28px

fig = go.Figure()

for ctx, col in ctx_colors.items():
    sub = flagged[flagged["context"] == ctx]
    if sub.empty:
        continue
    fig.add_trace(go.Scattermapbox(
        lat=sub["stop_lat"],
        lon=sub["stop_lon"],
        mode="markers",
        name=ctx,
        marker=dict(size=sub["bubble"], color=col, opacity=0.80),
        customdata=sub[["stop_short", "line_name", "pred_delay", "buffer_rec_s"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b> · L%{customdata[1]}<br>"
            "Pred. Delay: <b>%{customdata[2]:.0f}s</b><br>"
            "Buffer-Empfehlung: <b>+%{customdata[3]}s</b>"
            "<extra></extra>"
        ),
    ))

fig.update_layout(
    mapbox=dict(
        style="carto-positron",
        center=dict(lat=47.378, lon=8.540),
        zoom=11.5,
    ),
    title=dict(
        text="Fahrplan-Puffer-Empfehlungen nach Haltestelle und Kontext<br><sup>Größe = empfohlener Puffer · Farbe = Betriebskontext</sup>",
        x=0, xanchor="left",
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    height=600,
    margin=dict(l=0, r=0, t=80, b=0),
)
fig.show()
```

    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_49672/1504213642.py:19: DeprecationWarning: *scattermapbox* is deprecated! Use *scattermap* instead. Learn more at: https://plotly.com/python/mapbox-to-maplibre/
      fig.add_trace(go.Scattermapbox(
    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_49672/1504213642.py:19: DeprecationWarning: *scattermapbox* is deprecated! Use *scattermap* instead. Learn more at: https://plotly.com/python/mapbox-to-maplibre/
      fig.add_trace(go.Scattermapbox(
    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_49672/1504213642.py:19: DeprecationWarning: *scattermapbox* is deprecated! Use *scattermap* instead. Learn more at: https://plotly.com/python/mapbox-to-maplibre/
      fig.add_trace(go.Scattermapbox(
    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_49672/1504213642.py:19: DeprecationWarning: *scattermapbox* is deprecated! Use *scattermap* instead. Learn more at: https://plotly.com/python/mapbox-to-maplibre/
      fig.add_trace(go.Scattermapbox(




## Scope: Wie groß ist der Handlungsbedarf?


```python
# Summary: how many unique stops need a buffer, per context?
scope = (
    risk_matrix[risk_matrix["buffer_needed"]]
    .groupby("context", observed=True)
    .agg(
        unique_stops=("stop_name", "nunique"),
        unique_lines=("line_name", "nunique"),
        mean_buffer=("buffer_rec_s", "mean"),
        max_buffer=("buffer_rec_s", "max"),
    )
    .reset_index()
    .sort_values("unique_stops", ascending=False)
)

scope["Kontext"] = scope["context"]
scope["Betroffene Haltestellen"] = scope["unique_stops"]
scope["Betroffene Linien"] = scope["unique_lines"]
scope["Ø Empfohlener Puffer (s)"] = scope["mean_buffer"].round(1)
scope["Max. Puffer (s)"] = scope["max_buffer"]
show_df(
    scope[["Kontext", "Betroffene Haltestellen", "Betroffene Linien", "Ø Empfohlener Puffer (s)", "Max. Puffer (s)"]]
    .reset_index(drop=True)
)
```


<style type="text/css">
#T_7d1c5 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_7d1c5 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_7d1c5 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_7d1c5 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_7d1c5 tr:hover td {
  background-color: #eef3f8;
}
#T_7d1c5_row0_col0, #T_7d1c5_row1_col0, #T_7d1c5_row2_col0, #T_7d1c5_row3_col0 {
  text-align: left;
}
#T_7d1c5_row0_col1, #T_7d1c5_row0_col2, #T_7d1c5_row0_col3, #T_7d1c5_row0_col4, #T_7d1c5_row1_col1, #T_7d1c5_row1_col2, #T_7d1c5_row1_col3, #T_7d1c5_row1_col4, #T_7d1c5_row2_col1, #T_7d1c5_row2_col2, #T_7d1c5_row2_col3, #T_7d1c5_row2_col4, #T_7d1c5_row3_col1, #T_7d1c5_row3_col2, #T_7d1c5_row3_col3, #T_7d1c5_row3_col4 {
  text-align: right;
}
</style>
<table id="T_7d1c5">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_7d1c5_level0_col0" class="col_heading level0 col0" >Kontext</th>
      <th id="T_7d1c5_level0_col1" class="col_heading level0 col1" >Betroffene Haltestellen</th>
      <th id="T_7d1c5_level0_col2" class="col_heading level0 col2" >Betroffene Linien</th>
      <th id="T_7d1c5_level0_col3" class="col_heading level0 col3" >Ø Empfohlener Puffer (s)</th>
      <th id="T_7d1c5_level0_col4" class="col_heading level0 col4" >Max. Puffer (s)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_7d1c5_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_7d1c5_row0_col0" class="data row0 col0" >Event</td>
      <td id="T_7d1c5_row0_col1" class="data row0 col1" >77</td>
      <td id="T_7d1c5_row0_col2" class="data row0 col2" >17</td>
      <td id="T_7d1c5_row0_col3" class="data row0 col3" >3.60</td>
      <td id="T_7d1c5_row0_col4" class="data row0 col4" >20</td>
    </tr>
    <tr>
      <th id="T_7d1c5_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_7d1c5_row1_col0" class="data row1 col0" >Rush</td>
      <td id="T_7d1c5_row1_col1" class="data row1 col1" >73</td>
      <td id="T_7d1c5_row1_col2" class="data row1 col2" >13</td>
      <td id="T_7d1c5_row1_col3" class="data row1 col3" >3.10</td>
      <td id="T_7d1c5_row1_col4" class="data row1 col4" >15</td>
    </tr>
    <tr>
      <th id="T_7d1c5_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_7d1c5_row2_col0" class="data row2 col0" >Spätnacht</td>
      <td id="T_7d1c5_row2_col1" class="data row2 col1" >59</td>
      <td id="T_7d1c5_row2_col2" class="data row2 col2" >12</td>
      <td id="T_7d1c5_row2_col3" class="data row2 col3" >4.00</td>
      <td id="T_7d1c5_row2_col4" class="data row2 col4" >25</td>
    </tr>
    <tr>
      <th id="T_7d1c5_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_7d1c5_row3_col0" class="data row3 col0" >Normal</td>
      <td id="T_7d1c5_row3_col1" class="data row3 col1" >44</td>
      <td id="T_7d1c5_row3_col2" class="data row3 col2" >15</td>
      <td id="T_7d1c5_row3_col3" class="data row3 col3" >3.30</td>
      <td id="T_7d1c5_row3_col4" class="data row3 col4" >20</td>
    </tr>
  </tbody>
</table>



## Key Findings

→ Vollständige Findings-Tabelle in [`03_analysis_0-overview.ipynb`](03_analysis_0-overview.ipynb).

`Präsentation`: **hot** = Kernbefund · **story** = gutes Narrativ · **—** = intern

| ID | Finding | Präsentation |
|:---|:---|:---:|
| F-REC-01 | **Vorhersagbarkeit = Strukturalität = Steuerbarkeit.** MAE 18.56s beweist: Delays folgen Mustern, sie sind kein Zufall. Was Muster hat, kann man designen. Das Modell macht aus einer Analyse-Frage eine Handlungsgrundlage. | **hot** |
| F-REC-02 | Das Modell identifiziert Stop-Linie-Kontext-Kombinationen mit systematisch hohem Delay (>60s vorhergesagt). Diese Kombinationen sind die präzise Grundlage für stopspezifische dwell_time-Kalibrierung — statt pauschaler 0/60s für alle. | **hot** |
| F-REC-03 | Kontextspezifische Muster: Schnee betrifft strukturell andere Stops als Events oder Rush-Hour. Eine einheitliche Pufferstrategie greift zu kurz — kontextsensitive Fahrpläne (Schneefahrplan, Eventfahrplan) sind die logische Konsequenz. | **story** |
| F-REC-04 | Empfohlene Puffergrößen sind Startpunkte, keine Garantien (→ F-SIM-03/04). Validierung erfordert operatives A/B-Testing: ausgewählte Stops erhalten angepasste dwell_time → Delay-Veränderung messen → kalibrieren. Das Modell liefert die Diagnose, der Betrieb die Dosis. | story |

## Export


```python
from pathlib import Path

img_dir = Path("../public/img")
img_dir.mkdir(parents=True, exist_ok=True)

# Re-build map figure explicitly so the export cell is self-contained
fig_export = go.Figure()
for ctx, col in ctx_colors.items():
    sub = flagged[flagged["context"] == ctx]
    if sub.empty:
        continue
    fig_export.add_trace(go.Scattermapbox(
        lat=sub["stop_lat"],
        lon=sub["stop_lon"],
        mode="markers",
        name=ctx,
        marker=dict(size=sub["bubble"], color=col, opacity=0.80),
        customdata=sub[["stop_short", "line_name", "pred_delay", "buffer_rec_s"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b> · L%{customdata[1]}<br>"
            "Pred. Delay: <b>%{customdata[2]:.0f}s</b><br>"
            "Buffer-Empfehlung: <b>+%{customdata[3]}s</b>"
            "<extra></extra>"
        ),
    ))
fig_export.update_layout(
    mapbox=dict(style="carto-positron", center=dict(lat=47.378, lon=8.540), zoom=11.5),
    title=dict(
        text="Fahrplan-Puffer-Empfehlungen nach Haltestelle und Kontext<br>"
             "<sup>Größe = empfohlener Puffer · Farbe = Betriebskontext</sup>",
        x=0, xanchor="left",
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    height=600,
    margin=dict(l=0, r=0, t=80, b=0),
)

out_path = img_dir / "scheduling-recommendations-map.html"
fig_export.write_html(str(out_path), include_plotlyjs="cdn")
print(f"✅ Scheduling recommendations map saved to {out_path}")
```

    ✅ Scheduling recommendations map saved to ../public/img/scheduling-recommendations-map.html


    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_49672/4113231775.py:12: DeprecationWarning: *scattermapbox* is deprecated! Use *scattermap* instead. Learn more at: https://plotly.com/python/mapbox-to-maplibre/
      fig_export.add_trace(go.Scattermapbox(
    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_49672/4113231775.py:12: DeprecationWarning: *scattermapbox* is deprecated! Use *scattermap* instead. Learn more at: https://plotly.com/python/mapbox-to-maplibre/
      fig_export.add_trace(go.Scattermapbox(
    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_49672/4113231775.py:12: DeprecationWarning: *scattermapbox* is deprecated! Use *scattermap* instead. Learn more at: https://plotly.com/python/mapbox-to-maplibre/
      fig_export.add_trace(go.Scattermapbox(
    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_49672/4113231775.py:12: DeprecationWarning: *scattermapbox* is deprecated! Use *scattermap* instead. Learn more at: https://plotly.com/python/mapbox-to-maplibre/
      fig_export.add_trace(go.Scattermapbox(

