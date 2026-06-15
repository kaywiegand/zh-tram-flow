# LightGBM v2 — Kaskadenfeature

**Erweiterung des LightGBM v1-Modells** um den Kaskadenindikator `prev_trip_delay`.

**Motivation aus der Analyse:**
Der räumliche Analyseteil (`03_analysis_4-spatial.ipynb`) hat gezeigt, dass der Pearson-Korrelationskoeffizient zwischen dem Delay an Halt N und Halt N+1 netzweit r ≥ 0.85 beträgt. Verspätung kaskadiert fast vollständig von Halt zu Halt — und v1 hat dieses Signal noch nicht genutzt.

**Neue Features:**
| Feature | Beschreibung | Begründung |
|:---|:---|:---|
| `prev_trip_delay` | Arrival Delay am vorherigen Halt desselben Trips | Direkter Kaskadenindikator (r ≥ 0.85) |
| `stop_sequence_pct` | Position entlang der Linie (0 = Anfang · 1 = Ende) | Akkumulationseffekt: Delay wächst zur Peripherie |

**Hinweis:** `prev_trip_delay` verwendet den *tatsächlich gemessenen* Delay des Vorgänger-Halts — das ist kein Leakage für den operativen Anwendungsfall (Echtzeit-Prognose Halt für Halt), aber kein Feature für "Prognose vor Fahrtbeginn".

## Setup


```python
from zh_tram_flow.notebook import *
import polars as pl
import lightgbm as lgb
import numpy as np
import pandas as pd
from pathlib import Path

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("06_prediction_4-model_v2")

processed_dir  = Path(str(TRAIN)).parent
models_dir     = processed_dir.parent / "models"
models_dir.mkdir(exist_ok=True)

train_features_path = str(TRAIN)                              # train_features.parquet
train_final_path    = str(TRAIN).replace("train_features", "train_final")
test_features_path  = str(TEST)                               # test_features.parquet
test_final_path     = str(TEST).replace("test_features", "test_final")

train_v2_path = str(processed_dir / "train_final_v2.parquet")
test_v2_path  = str(processed_dir / "test_final_v2.parquet")

BASELINE_MAE = 50.0   # Stop Mean — aus 06_prediction_1-baseline
V1_VAL_MAE   = 49.05  # LightGBM v1 Validation MAE
V1_TEST_MAE  = 45.7   # LightGBM v1 Test MAE
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload



<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-05-28 21:36:44  INFO      project  06_prediction_4-model_v2 started


## Feature Engineering v2

### Strategie

`train_final.parquet` enthält bereits alle engineerten Features — aber keine `stop_sequence` (war als ID-Spalte ausgeschlossen). Wir holen sie aus `train_features.parquet` und joinen sie, um dann `prev_trip_delay` und `stop_sequence_pct` zu berechnen.

**Join-Key:** `(trip_id, operating_date, stop_name)` — eindeutig, da ein Tram denselben Halt pro Trip/Tag nur einmal bedient.


```python
def add_cascade_features(final_path: str, features_path: str) -> pl.DataFrame:
    """Fügt prev_trip_delay + stop_sequence_pct zu einem final-Parquet hinzu.
    
    Vorgehen:
      1. stop_sequence aus features-Parquet (nur nicht-canceled Zeilen)
      2. Left-Join auf (trip_id, operating_date, stop_name)
      3. Sort by (trip_id, operating_date, stop_sequence)
      4. prev_trip_delay = shift(1).over([trip_id, operating_date]), Null → 0.0
      5. stop_sequence_pct = stop_sequence / n_stops_line
    """
    print(f"Lade {Path(final_path).name} ...")
    df = pl.read_parquet(final_path)
    print(f"  {len(df):,} rows, {len(df.columns)} cols")

    print(f"Lade stop_sequence aus {Path(features_path).name} ...")
    seq_df = (
        pl.read_parquet(
            features_path,
            columns=["trip_id", "operating_date", "stop_name", "stop_sequence", "canceled"],
        )
        .filter(pl.col("canceled") == False)
        .drop("canceled")
        # Deduplizieren — sicherheitshalber (sollte eindeutig sein)
        .unique(subset=["trip_id", "operating_date", "stop_name"], keep="first")
    )
    print(f"  stop_sequence lookup: {len(seq_df):,} rows")

    print("Join + Kaskaden-Berechnung ...")
    result = (
        df
        .join(seq_df, on=["trip_id", "operating_date", "stop_name"], how="left")
        .sort(["trip_id", "operating_date", "stop_sequence"])
        .with_columns(
            # Kaskadenindikator: Delay am vorherigen Halt desselben Trips
            pl.col("arrival_delay")
              .shift(1)
              .over(["trip_id", "operating_date"])
              .fill_null(0.0)   # erster Halt eines Trips → kein Vorgänger → 0
              .alias("prev_trip_delay"),
            # Positions-Feature: 0 = Anfangshalt · 1 = Endhalt
            (pl.col("stop_sequence") / pl.col("n_stops_line"))
              .alias("stop_sequence_pct"),
        )
    )

    null_count = result["stop_sequence"].null_count()
    if null_count > 0:
        print(f"  ⚠️  {null_count:,} Zeilen ohne stop_sequence (Join-Fehler?) — werden behalten")
    print(f"  ✓  {len(result):,} rows · neue Spalten: prev_trip_delay, stop_sequence_pct, stop_sequence")
    return result


train_v2 = add_cascade_features(train_final_path, train_features_path)
test_v2  = add_cascade_features(test_final_path,  test_features_path)
```

    Lade train_final.parquet ...
      55,484,578 rows, 40 cols
    Lade stop_sequence aus train_features.parquet ...
      stop_sequence lookup: 57,524,380 rows
    Join + Kaskaden-Berechnung ...
      ⚠️  3 Zeilen ohne stop_sequence (Join-Fehler?) — werden behalten
      ✓  55,484,578 rows · neue Spalten: prev_trip_delay, stop_sequence_pct, stop_sequence
    Lade test_final.parquet ...
      29,941,876 rows, 40 cols
    Lade stop_sequence aus test_features.parquet ...
      stop_sequence lookup: 30,811,179 rows
    Join + Kaskaden-Berechnung ...
      ✓  29,941,876 rows · neue Spalten: prev_trip_delay, stop_sequence_pct, stop_sequence



```python
# Schnell-Check: Korrelation prev_trip_delay ↔ arrival_delay
r = train_v2.select(
    pl.corr("prev_trip_delay", "arrival_delay")
).item()
print(f"Pearson r(prev_trip_delay, arrival_delay) = {r:.4f}")
print()

# Verteilung des neuen Features
show_df(
    train_v2.select("prev_trip_delay").describe().to_pandas()
)
```

    Pearson r(prev_trip_delay, arrival_delay) = 0.8961
    



<style type="text/css">
#T_444fe thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_444fe td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_444fe tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_444fe tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_444fe tr:hover td {
  background-color: #eef3f8;
}
#T_444fe_row0_col0, #T_444fe_row1_col0, #T_444fe_row2_col0, #T_444fe_row3_col0, #T_444fe_row4_col0, #T_444fe_row5_col0, #T_444fe_row6_col0, #T_444fe_row7_col0, #T_444fe_row8_col0 {
  text-align: left;
}
#T_444fe_row0_col1, #T_444fe_row1_col1, #T_444fe_row2_col1, #T_444fe_row3_col1, #T_444fe_row4_col1, #T_444fe_row5_col1, #T_444fe_row6_col1, #T_444fe_row7_col1, #T_444fe_row8_col1 {
  text-align: right;
}
</style>
<table id="T_444fe">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_444fe_level0_col0" class="col_heading level0 col0" >statistic</th>
      <th id="T_444fe_level0_col1" class="col_heading level0 col1" >prev_trip_delay</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_444fe_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_444fe_row0_col0" class="data row0 col0" >count</td>
      <td id="T_444fe_row0_col1" class="data row0 col1" >55484578.00</td>
    </tr>
    <tr>
      <th id="T_444fe_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_444fe_row1_col0" class="data row1 col0" >null_count</td>
      <td id="T_444fe_row1_col1" class="data row1 col1" >0.00</td>
    </tr>
    <tr>
      <th id="T_444fe_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_444fe_row2_col0" class="data row2 col0" >mean</td>
      <td id="T_444fe_row2_col1" class="data row2 col1" >54.08</td>
    </tr>
    <tr>
      <th id="T_444fe_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_444fe_row3_col0" class="data row3 col0" >std</td>
      <td id="T_444fe_row3_col1" class="data row3 col1" >77.33</td>
    </tr>
    <tr>
      <th id="T_444fe_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_444fe_row4_col0" class="data row4 col0" >min</td>
      <td id="T_444fe_row4_col1" class="data row4 col1" >-3594.00</td>
    </tr>
    <tr>
      <th id="T_444fe_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_444fe_row5_col0" class="data row5 col0" >25%</td>
      <td id="T_444fe_row5_col1" class="data row5 col1" >7.00</td>
    </tr>
    <tr>
      <th id="T_444fe_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_444fe_row6_col0" class="data row6 col0" >50%</td>
      <td id="T_444fe_row6_col1" class="data row6 col1" >40.00</td>
    </tr>
    <tr>
      <th id="T_444fe_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_444fe_row7_col0" class="data row7 col0" >75%</td>
      <td id="T_444fe_row7_col1" class="data row7 col1" >81.00</td>
    </tr>
    <tr>
      <th id="T_444fe_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_444fe_row8_col0" class="data row8 col0" >max</td>
      <td id="T_444fe_row8_col1" class="data row8 col1" >3579.00</td>
    </tr>
  </tbody>
</table>




```python
from pathlib import Path as _Path

_train_v2_exists = _Path(train_v2_path).exists()
_test_v2_exists  = _Path(test_v2_path).exists()

if _train_v2_exists and _test_v2_exists:
    print("train_final_v2.parquet + test_final_v2.parquet bereits vorhanden — Export übersprungen.")
    print(f"  {train_v2_path}")
    print(f"  {test_v2_path}")
else:
    print("Exportiere train_final_v2.parquet ...")
    train_v2.write_parquet(train_v2_path)
    print(f"  ✓  {train_v2_path}")

    print("Exportiere test_final_v2.parquet ...")
    test_v2.write_parquet(test_v2_path)
    print(f"  ✓  {test_v2_path}")
```

    train_final_v2.parquet + test_final_v2.parquet bereits vorhanden — Export übersprungen.
      /Users/kaywiegand/Workspace/zh-tram-flow/data/processed/train_final_v2.parquet
      /Users/kaywiegand/Workspace/zh-tram-flow/data/processed/test_final_v2.parquet


## Feature Set v2

Vergleich v1 vs. v2 — was ist neu, was bleibt gleich.


```python
TARGET  = "arrival_delay"

# Gleiche Exclude-Liste wie v1, ergänzt um interne Hilfsspalten
EXCLUDE_V2 = [
    TARGET,
    "departure_delay",
    "delay_delta",
    "canceled",
    "trip_id",
    "operating_date",
    "event_name",
    "stop_lat",
    "stop_lon",
    "stop_sequence",   # roh — durch stop_sequence_pct abgedeckt
]

FEATURES_V2 = [c for c in train_v2.columns if c not in EXCLUDE_V2]
CAT_COLS_V2 = [c for c in ["line_name", "stop_name", "event_type", "season", "gtfs_year"]
               if c in FEATURES_V2]

# v1 Feature-Set (aus Metadaten)
import json as _json
with open(models_dir / "lgbm_v1_meta.json") as f:
    v1_meta = _json.load(f)
FEATURES_V1 = v1_meta["features"]

new_features = [f for f in FEATURES_V2 if f not in FEATURES_V1]
removed      = [f for f in FEATURES_V1 if f not in FEATURES_V2]

print(f"Features v1: {len(FEATURES_V1)}")
print(f"Features v2: {len(FEATURES_V2)}")
print(f"\n  Neu in v2:     {new_features}")
print(f"  Entfernt:      {removed if removed else '—'}")
```

    Features v1: 32
    Features v2: 34
    
      Neu in v2:     ['prev_trip_delay', 'stop_sequence_pct']
      Entfernt:      —


## Validation Split

Identischer temporaler Split wie v1:
* **Train:**      2023-01 bis 2024-06
* **Validation:** 2024-07 bis 2024-12
* **Test:**       2025 (nie gesehen während Training)


```python
def to_lgb_df(pl_df: pl.DataFrame, features: list, cat_cols: list) -> pd.DataFrame:
    pdf = pl_df.select(features).to_pandas()
    for col in cat_cols:
        if col in pdf.columns:
            pdf[col] = pdf[col].astype("category")
    return pdf


val_mask = (
    (train_v2["operating_date"].dt.year() == 2024)
    & (train_v2["operating_date"].dt.month() >= 7)
)
train_sub = train_v2.filter(~val_mask)
val_sub   = train_v2.filter(val_mask)

print(f"Train subset:      {len(train_sub):,} rows")
print(f"Validation subset: {len(val_sub):,} rows")

print("Konvertiere zu Pandas ...")
X_train = to_lgb_df(train_sub, FEATURES_V2, CAT_COLS_V2)
y_train = train_sub[TARGET].to_numpy()
X_val   = to_lgb_df(val_sub, FEATURES_V2, CAT_COLS_V2)
y_val   = val_sub[TARGET].to_numpy()
print("Fertig.")
```

    Train subset:      41,230,594 rows
    Validation subset: 14,253,984 rows
    Konvertiere zu Pandas ...
    Fertig.


## Training: LightGBM v2

Gleiche Hyperparameter wie v1 — nur das Feature Set ist erweitert. So ist der Vergleich sauber: jede Verbesserung kommt ausschliesslich aus den neuen Features.


```python
_lgbm_v2_path      = models_dir / "lgbm_v2.txt"
_lgbm_v2_meta_path = models_dir / "lgbm_v2_meta.json"

if _lgbm_v2_path.exists():
    # Modell bereits trainiert — laden statt neu trainieren (~2 s statt ~30 min)
    import json as _json_load
    print(f"Modell gefunden — lade {_lgbm_v2_path.name} ...")
    model_v2 = lgb.Booster(model_file=str(_lgbm_v2_path))
    # params + best_score: aus Meta-JSON laden (beim Booster-Load nicht im Objekt)
    if _lgbm_v2_meta_path.exists():
        with open(_lgbm_v2_meta_path) as _f:
            _m = _json_load.load(_f)
        params = _m.get("params", {})
        try:
            _ = model_v2.best_score["valid_0"]["l1"]
        except (AttributeError, KeyError, TypeError):
            model_v2.best_score = {"valid_0": {"l1": _m["val_mae"]}}
    else:
        params = {}
    print(f"Geladen ✓  best_iteration={model_v2.best_iteration}  "
          f"val_mae={model_v2.best_score['valid_0']['l1']:.2f}s")
else:
    lgb_train = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
    lgb_val   = lgb.Dataset(X_val,   label=y_val,   reference=lgb_train, free_raw_data=False)

    params = {
        "objective":        "regression_l1",
        "metric":           "mae",
        "num_leaves":       63,
        "learning_rate":    0.05,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq":     5,
        "min_child_samples": 50,
        "verbose":          -1,
        "n_jobs":           -1,
    }

    callbacks = [
        lgb.early_stopping(stopping_rounds=50, verbose=True),
        lgb.log_evaluation(period=50),
    ]

    print("Training startet ...")
    model_v2 = lgb.train(
        params,
        lgb_train,
        num_boost_round=1000,
        valid_sets=[lgb_val],
        callbacks=callbacks,
    )
    print(f"\nBeste Iteration: {model_v2.best_iteration}")
    print(f"Bestes Val-MAE:  {model_v2.best_score['valid_0']['l1']:.2f}s")
```

    Modell gefunden — lade lgbm_v2.txt ...
    Geladen ✓  best_iteration=-1  val_mae=17.78s


## Ergebnis: v1 vs. v2


```python
v2_val_mae = model_v2.best_score["valid_0"]["l1"]

print("=" * 42)
print(f"  Baseline (Stop Mean):  {BASELINE_MAE:.1f} s")
print(f"  LightGBM v1 Val MAE:   {V1_VAL_MAE:.1f} s  (Δ {BASELINE_MAE - V1_VAL_MAE:+.1f} s)")
print(f"  LightGBM v2 Val MAE:   {v2_val_mae:.2f} s  (Δ {BASELINE_MAE - v2_val_mae:+.2f} s)")
print(f"  v2 vs. v1:             {V1_VAL_MAE - v2_val_mae:+.2f} s")
print("=" * 42)

if v2_val_mae < V1_VAL_MAE:
    print(f"\n✅  v2 verbessert v1 um {V1_VAL_MAE - v2_val_mae:.2f} s — Kaskadenfeature hilft!")
else:
    print(f"\n⚠️  v2 schlechter als v1 um {v2_val_mae - V1_VAL_MAE:.2f} s — Feature-Analyse nötig")
```

    ==========================================
      Baseline (Stop Mean):  50.0 s
      LightGBM v1 Val MAE:   49.0 s  (Δ +1.0 s)
      LightGBM v2 Val MAE:   17.78 s  (Δ +32.22 s)
      v2 vs. v1:             +31.27 s
    ==========================================
    
    ✅  v2 verbessert v1 um 31.27 s — Kaskadenfeature hilft!


## Feature Importance (Gain)

Steht `prev_trip_delay` unter den Top-Features? Das würde bestätigen, dass das Modell die Kaskade tatsächlich nutzt.


```python
import plotly.express as px

importance = pd.DataFrame({
    "feature":    model_v2.feature_name(),
    "importance": model_v2.feature_importance(importance_type="gain"),
}).sort_values("importance", ascending=False).head(20)

# Kaskadenfeature hervorheben
importance["color"] = importance["feature"].apply(
    lambda f: "Kaskadenfeature (neu)" if f in ["prev_trip_delay", "stop_sequence_pct"]
    else "Bestehendes Feature"
)

fig = px.bar(
    importance,
    x="importance",
    y="feature",
    orientation="h",
    color="color",
    color_discrete_map={
        "Kaskadenfeature (neu)": "#de425b",
        "Bestehendes Feature":   "#4c72b0",
    },
    title="Top 20 Feature Importance (Gain) — LightGBM v2",
    labels={"importance": "Gain", "feature": "", "color": ""},
)
fig.update_layout(
    yaxis=dict(autorange="reversed"),
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
fig.show()

show_df(importance.drop(columns="color").reset_index(drop=True))
```




<style type="text/css">
#T_73bfc thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_73bfc td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_73bfc tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_73bfc tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_73bfc tr:hover td {
  background-color: #eef3f8;
}
#T_73bfc_row0_col0, #T_73bfc_row1_col0, #T_73bfc_row2_col0, #T_73bfc_row3_col0, #T_73bfc_row4_col0, #T_73bfc_row5_col0, #T_73bfc_row6_col0, #T_73bfc_row7_col0, #T_73bfc_row8_col0, #T_73bfc_row9_col0, #T_73bfc_row10_col0, #T_73bfc_row11_col0, #T_73bfc_row12_col0, #T_73bfc_row13_col0, #T_73bfc_row14_col0, #T_73bfc_row15_col0, #T_73bfc_row16_col0, #T_73bfc_row17_col0, #T_73bfc_row18_col0, #T_73bfc_row19_col0 {
  text-align: left;
}
#T_73bfc_row0_col1, #T_73bfc_row1_col1, #T_73bfc_row2_col1, #T_73bfc_row3_col1, #T_73bfc_row4_col1, #T_73bfc_row5_col1, #T_73bfc_row6_col1, #T_73bfc_row7_col1, #T_73bfc_row8_col1, #T_73bfc_row9_col1, #T_73bfc_row10_col1, #T_73bfc_row11_col1, #T_73bfc_row12_col1, #T_73bfc_row13_col1, #T_73bfc_row14_col1, #T_73bfc_row15_col1, #T_73bfc_row16_col1, #T_73bfc_row17_col1, #T_73bfc_row18_col1, #T_73bfc_row19_col1 {
  text-align: right;
}
</style>
<table id="T_73bfc">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_73bfc_level0_col0" class="col_heading level0 col0" >feature</th>
      <th id="T_73bfc_level0_col1" class="col_heading level0 col1" >importance</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_73bfc_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_73bfc_row0_col0" class="data row0 col0" >prev_trip_delay</td>
      <td id="T_73bfc_row0_col1" class="data row0 col1" >336224495.25</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_73bfc_row1_col0" class="data row1 col0" >stop_name</td>
      <td id="T_73bfc_row1_col1" class="data row1 col1" >90952269.08</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_73bfc_row2_col0" class="data row2 col0" >dwell_time</td>
      <td id="T_73bfc_row2_col1" class="data row2 col1" >35439222.67</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_73bfc_row3_col0" class="data row3 col0" >stop_sequence_pct</td>
      <td id="T_73bfc_row3_col1" class="data row3 col1" >22090759.46</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_73bfc_row4_col0" class="data row4 col0" >line_name</td>
      <td id="T_73bfc_row4_col1" class="data row4 col1" >11227691.53</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_73bfc_row5_col0" class="data row5 col0" >hour</td>
      <td id="T_73bfc_row5_col1" class="data row5 col1" >8506885.65</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_73bfc_row6_col0" class="data row6 col0" >weekday</td>
      <td id="T_73bfc_row6_col1" class="data row6 col1" >1971126.69</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_73bfc_row7_col0" class="data row7 col0" >n_lines_at_stop</td>
      <td id="T_73bfc_row7_col1" class="data row7 col1" >1962133.92</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_73bfc_row8_col0" class="data row8 col0" >n_stops_line</td>
      <td id="T_73bfc_row8_col1" class="data row8 col1" >1833638.63</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_73bfc_row9_col0" class="data row9 col0" >district_nr</td>
      <td id="T_73bfc_row9_col1" class="data row9 col1" >1786287.79</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_73bfc_row10_col0" class="data row10 col0" >month</td>
      <td id="T_73bfc_row10_col1" class="data row10 col1" >336061.12</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_73bfc_row11_col0" class="data row11 col0" >year</td>
      <td id="T_73bfc_row11_col1" class="data row11 col1" >329345.42</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_73bfc_row12_col0" class="data row12 col0" >event_type</td>
      <td id="T_73bfc_row12_col1" class="data row12 col1" >269469.42</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_73bfc_row13_col0" class="data row13 col0" >is_holiday</td>
      <td id="T_73bfc_row13_col1" class="data row13 col1" >156348.37</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_73bfc_row14_col0" class="data row14 col0" >is_weekend</td>
      <td id="T_73bfc_row14_col1" class="data row14 col1" >86457.13</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_73bfc_row15_col0" class="data row15 col0" >temperature</td>
      <td id="T_73bfc_row15_col1" class="data row15 col1" >62073.27</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_73bfc_row16_col0" class="data row16 col0" >gtfs_year</td>
      <td id="T_73bfc_row16_col1" class="data row16 col1" >54552.02</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_73bfc_row17_col0" class="data row17 col0" >is_late_night_weekend</td>
      <td id="T_73bfc_row17_col1" class="data row17 col1" >41926.24</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_73bfc_row18_col0" class="data row18 col0" >season</td>
      <td id="T_73bfc_row18_col1" class="data row18 col1" >41643.02</td>
    </tr>
    <tr>
      <th id="T_73bfc_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_73bfc_row19_col0" class="data row19 col0" >event_weight_x_hour</td>
      <td id="T_73bfc_row19_col1" class="data row19 col1" >26880.89</td>
    </tr>
  </tbody>
</table>



## SHAP-Werte

SHAP (SHapley Additive exPlanations) erklärt, welchen Beitrag jedes Feature für eine einzelne Vorhersage leistet — aussagekräftiger als Gain-Importance, die nur die globale Nutzung misst.

Benötigt: `uv pip install -e ".[dsc]"`


```python
try:
    import shap
    import matplotlib.pyplot as plt

    # SHAP auf einer repräsentativen Stichprobe berechnen (5000 Zeilen)
    SHAP_SAMPLE = 5000
    rng = np.random.default_rng(42)
    idx = rng.choice(len(X_val), size=min(SHAP_SAMPLE, len(X_val)), replace=False)
    X_shap = X_val.iloc[idx].copy()

    print(f"Berechne SHAP auf {len(X_shap):,} Stichproben ...")
    explainer = shap.TreeExplainer(model_v2)
    shap_values = explainer.shap_values(X_shap)

    plt.figure(figsize=(10, 7))
    shap.summary_plot(
        shap_values, X_shap,
        max_display=20,
        show=False,
        plot_type="dot",
    )
    plt.title("SHAP Summary — LightGBM v2 (Stichprobe n=5000)", fontsize=12)
    plt.tight_layout()
    plt.show()

except ImportError:
    print("shap nicht installiert — überspringen.")
    print("Installation: uv pip install -e '.[dsc]'")
```

    shap nicht installiert — überspringen.
    Installation: uv pip install -e '.[dsc]'


## Test-Evaluation


```python
print("Lade Testdaten ...")
test_pl = pl.read_parquet(test_v2_path)
X_test  = to_lgb_df(test_pl, FEATURES_V2, CAT_COLS_V2)
y_test  = test_pl[TARGET].to_numpy()

test_pred_v2 = model_v2.predict(X_test, num_iteration=model_v2.best_iteration)

test_mae_v2  = np.abs(y_test - test_pred_v2).mean()
test_rmse_v2 = np.sqrt(((y_test - test_pred_v2) ** 2).mean())
test_mbe_v2  = (test_pred_v2 - y_test).mean()          # Mean Bias Error
test_otp_v2  = (np.abs(y_test - test_pred_v2) <= 60).mean()

print()
print("=" * 48)
print(f"  Test MAE:        {test_mae_v2:.1f} s  (v1: {V1_TEST_MAE:.1f} s · Δ {V1_TEST_MAE - test_mae_v2:+.1f} s)")
print(f"  Test RMSE:       {test_rmse_v2:.1f} s")
print(f"  MBE (Bias):      {test_mbe_v2:+.1f} s  (v1: +8.3 s)")
print(f"  OTP (±60 s):     {test_otp_v2:.1%}")
print(f"  Baseline:        {BASELINE_MAE:.1f} s")
print("=" * 48)

if test_mbe_v2 > 5:
    print(f"\n⚠️  MBE {test_mbe_v2:+.1f} s — Modell unterschätzt Verspätung systematisch → Bias-Analyse!")
```

    Lade Testdaten ...
    
    ================================================
      Test MAE:        18.6 s  (v1: 45.7 s · Δ +27.1 s)
      Test RMSE:       38.0 s
      MBE (Bias):      -0.7 s  (v1: +8.3 s)
      OTP (±60 s):     95.8%
      Baseline:        50.0 s
    ================================================


## Fehleranalyse

MAE nach Tageszeit, Linie und Wetter — identische Aufteilung wie v1 für direkten Vergleich.


```python
import matplotlib.pyplot as plt

err_df = test_pl.with_columns(
    pl.lit(test_pred_v2.astype("float32")).alias("predicted"),
    pl.lit(y_test.astype("float32")).alias("actual"),
).with_columns(
    (pl.col("predicted") - pl.col("actual")).abs().alias("abs_error")
).to_pandas()

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# MAE nach Stunde
mae_hour = err_df.groupby("hour")["abs_error"].mean().sort_index()
axes[0].bar(mae_hour.index, mae_hour.values, color="#4c72b0", alpha=0.8)
axes[0].axhline(test_mae_v2, color="#de425b", ls="--", lw=1.5, label=f"Ø MAE {test_mae_v2:.1f}s")
axes[0].set_title("MAE nach Tageszeit"); axes[0].set_xlabel("Stunde"); axes[0].legend()

# MAE nach Linie
mae_line = (
    err_df.groupby("line_name")["abs_error"].mean()
    .reset_index()
    .sort_values("abs_error", ascending=False)
)
colors = ["#de425b" if v > test_mae_v2 else "#55a868" for v in mae_line["abs_error"]]
axes[1].bar(mae_line["line_name"].astype(str), mae_line["abs_error"], color=colors, alpha=0.85)
axes[1].axhline(test_mae_v2, color="black", ls="--", lw=1.2)
axes[1].set_title("MAE nach Linie"); axes[1].set_xlabel("Linie")
axes[1].tick_params(axis="x", rotation=45)

# MAE nach Wetter
weather_labels  = ["Normal", "Regen", "Starkregen", "Schnee"]
weather_filters = [
    (~err_df["has_rain"]) & (~err_df["has_snow"]),
    err_df["has_rain"],
    err_df["has_heavy_rain"],
    err_df["has_snow"],
]
mae_weather = [err_df.loc[f, "abs_error"].mean() for f in weather_filters]
axes[2].bar(weather_labels, mae_weather, color=["#4c72b0","#937860","#dd8452","#8172b2"], alpha=0.85)
axes[2].axhline(test_mae_v2, color="black", ls="--", lw=1.2)
axes[2].set_title("MAE nach Wetter")

plt.suptitle("Fehleranalyse LightGBM v2", fontsize=13, y=1.02)
plt.tight_layout()
plt.show()
```

    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_40734/2047512323.py:20: FutureWarning: The default of observed=False is deprecated and will be changed to True in a future version of pandas. Pass observed=False to retain current behavior or observed=True to adopt the future default and silence this warning.
      err_df.groupby("line_name")["abs_error"].mean()
    2026-05-28 20:14:44  INFO      matplotlib.category  Using categorical units to plot a list of strings that are all parsable as floats or dates. If these strings should be plotted as numbers, cast to the appropriate data type before plotting.
    2026-05-28 20:14:44  INFO      matplotlib.category  Using categorical units to plot a list of strings that are all parsable as floats or dates. If these strings should be plotted as numbers, cast to the appropriate data type before plotting.



    
![png](06_prediction_4-model_v2_files/06_prediction_4-model_v2_22_1.png)
    


## Bias-Analyse & Kalibrierung

v1 hatte MBE +8.3 s — das Modell unterschätzte Verspätung systematisch. Hier prüfen wir, ob v2 das verbessert, und wenden falls nötig eine **Isotonic Regression** als Post-hoc-Kalibrierung an.

> **Isotonic Regression:** Monotone, nicht-parametrische Kalibrierung — passt die Predicted-Values so an, dass der Bias auf dem Val-Set verschwindet, ohne die Ranking-Güte zu beeinträchtigen.


```python
from sklearn.isotonic import IsotonicRegression

# Kalibrierung auf Validation-Set trainieren
val_pred_v2 = model_v2.predict(X_val, num_iteration=model_v2.best_iteration)

iso = IsotonicRegression(out_of_bounds="clip")
iso.fit(val_pred_v2, y_val)

# Kalibrierte Test-Predictions
test_pred_v2_cal = iso.predict(test_pred_v2)

cal_mae = np.abs(y_test - test_pred_v2_cal).mean()
cal_mbe = (test_pred_v2_cal - y_test).mean()

print("Bias-Kalibrierung (Isotonic Regression)")
print(f"  Vor Kalibrierung: MAE {test_mae_v2:.1f} s · MBE {test_mbe_v2:+.1f} s")
print(f"  Nach Kalibrierung: MAE {cal_mae:.1f} s · MBE {cal_mbe:+.1f} s")
print()
if cal_mae < test_mae_v2:
    print(f"✅  Kalibrierung verbessert MAE um {test_mae_v2 - cal_mae:.1f} s")
else:
    print("ℹ️  Kalibrierung verändert MAE kaum — Bias war kein kritisches Problem")

# Predicted vs Actual (unkalibriert vs. kalibriert)
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sample = np.random.default_rng(42).choice(len(y_test), 3000, replace=False)

for ax, preds, title in [
    (axes[0], test_pred_v2,     f"v2 unkalibriert (MBE {test_mbe_v2:+.1f} s)"),
    (axes[1], test_pred_v2_cal, f"v2 kalibriert   (MBE {cal_mbe:+.1f} s)"),
]:
    ax.scatter(y_test[sample], preds[sample], alpha=0.15, s=3, color="#4c72b0")
    lims = [min(y_test.min(), preds.min()), max(y_test.max(), preds.max())]
    ax.plot(lims, lims, "r--", lw=1.5, label="Ideal")
    ax.set_xlabel("Actual (s)"); ax.set_ylabel("Predicted (s)")
    ax.set_title(title); ax.legend()

plt.suptitle("Predicted vs. Actual — v2 (Stichprobe n=3000)", fontsize=12)
plt.tight_layout()
plt.show()
```

    Bias-Kalibrierung (Isotonic Regression)
      Vor Kalibrierung: MAE 18.6 s · MBE -0.7 s
      Nach Kalibrierung: MAE 18.8 s · MBE +0.7 s
    
    ℹ️  Kalibrierung verändert MAE kaum — Bias war kein kritisches Problem



    
![png](06_prediction_4-model_v2_files/06_prediction_4-model_v2_24_1.png)
    


## Export


```python
import json as _json
from sklearn.utils import estimator_html_repr
import joblib

# LightGBM v2 Modell
model_v2_path = models_dir / "lgbm_v2.txt"
model_v2.save_model(str(model_v2_path))
print(f"Modell gespeichert: {model_v2_path}")

# Isotonic-Kalibrierer
iso_path = models_dir / "lgbm_v2_calibrator.joblib"
joblib.dump(iso, iso_path)
print(f"Kalibrierer gespeichert: {iso_path}")

# Metadaten
meta_v2 = {
    "model":          "lgbm_v2",
    "best_iteration": model_v2.best_iteration,
    "val_mae":        round(v2_val_mae, 2),
    "test_mae":       round(test_mae_v2, 2),
    "test_mae_cal":   round(cal_mae, 2),
    "test_mbe":       round(test_mbe_v2, 2),
    "test_mbe_cal":   round(cal_mbe, 2),
    "baseline_mae":   BASELINE_MAE,
    "v1_test_mae":    V1_TEST_MAE,
    "params":         params,
    "features":       FEATURES_V2,
    "new_features":   new_features,
    "cat_cols":       CAT_COLS_V2,
    "target":         TARGET,
}
meta_v2_path = models_dir / "lgbm_v2_meta.json"
with open(meta_v2_path, "w", encoding="utf-8") as f:
    _json.dump(meta_v2, f, indent=2, ensure_ascii=False)
print(f"Metadaten gespeichert: {meta_v2_path}")

# Test-Predictions v2 (unkalibriert + kalibriert)
pred_v2_df = pl.DataFrame({
    "actual":         y_test,
    "predicted_v2":   test_pred_v2.astype("float32"),
    "predicted_v2_cal": test_pred_v2_cal.astype("float32"),
    "line_name":      test_pl["line_name"],
    "stop_name":      test_pl["stop_name"],
    "hour":           test_pl["hour"],
    "month":          test_pl["month"],
    "has_rain":       test_pl["has_rain"],
    "has_snow":       test_pl["has_snow"],
    "has_event":      test_pl["has_event"],
})
pred_v2_path = processed_dir / "test_predictions_v2.parquet"
pred_v2_df.write_parquet(pred_v2_path)
print(f"Predictions gespeichert: {pred_v2_path}")

print(f"\n{'='*48}")
print(f"  LightGBM v2 — Zusammenfassung")
print(f"  Test MAE:       {test_mae_v2:.1f} s  (Baseline: {BASELINE_MAE} s · v1: {V1_TEST_MAE} s)")
print(f"  Nach Kalib.:    {cal_mae:.1f} s")
print(f"  MBE vorher:     {test_mbe_v2:+.1f} s")
print(f"  MBE nachher:    {cal_mbe:+.1f} s")
print(f"{'='*48}")
```

    Modell gespeichert: /Users/kaywiegand/Workspace/zh-tram-flow/data/models/lgbm_v2.txt
    Kalibrierer gespeichert: /Users/kaywiegand/Workspace/zh-tram-flow/data/models/lgbm_v2_calibrator.joblib
    Metadaten gespeichert: /Users/kaywiegand/Workspace/zh-tram-flow/data/models/lgbm_v2_meta.json
    Predictions gespeichert: /Users/kaywiegand/Workspace/zh-tram-flow/data/processed/test_predictions_v2.parquet
    
    ================================================
      LightGBM v2 — Zusammenfassung
      Test MAE:       18.6 s  (Baseline: 50.0 s · v1: 45.7 s)
      Nach Kalib.:    18.8 s
      MBE vorher:     -0.7 s
      MBE nachher:    +0.7 s
    ================================================



```python

```
