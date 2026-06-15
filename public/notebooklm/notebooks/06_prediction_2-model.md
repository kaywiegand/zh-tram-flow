# Model — LightGBM

Training des LightGBM-Modells auf `train_final.parquet`. Temporaler Split: 2023–2024 als Train, 2024 Q4 als internes Validation-Set, 2025 als Test.

**Benchmark aus Baseline-Notebook:** Stop Mean MAE = 50.0s — das Modell muss diesen Wert unterbieten.

## Setup


```python
from zh_tram_flow.notebook import *
import polars as pl
import lightgbm as lgb
import numpy as np
import pandas as pd
from pathlib import Path

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("06_prediction_2-model")

MODELS_DIR = Path(TRAIN).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload



<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-05-20 19:22:31  INFO      project  06_prediction_2-model started


## Feature Set

Wir laden `train_final.parquet` — das ML-bereite Dataset ohne Rohdaten-Spalten. Folgende Spalten werden explizit **ausgeschlossen**:

| Spalte | Grund |
|:---|:---|
| `departure_delay` | Leakage — nur nach Abfahrt bekannt |
| `delay_delta` | Leakage — nur nach Ankunft bekannt |
| `trip_id` | ID-Spalte, kein Signal |
| `operating_date` | Durch month/weekday/season abgedeckt |


```python
TARGET = "arrival_delay"

# Leaky: nur nach Ankunft bekannt
# IDs / redundant: keine Vorhersagekraft
EXCLUDE = [
    TARGET,
    "departure_delay",   # leaky
    "delay_delta",       # leaky
    "canceled",          # nach apply_lf_clean redundant — kein Signal
    "trip_id",           # ID
    "operating_date",    # durch month/weekday/year abgedeckt
    "event_name",        # zu granular — event_type + event_weight reichen
    "stop_lat",          # redundant mit stop_name
    "stop_lon",          # redundant mit stop_name
]

# Polars: nur Features + Target laden (spart RAM)
train_path = str(TRAIN).replace("train_features", "train_final")
test_path  = str(TEST).replace("test_features", "test_final")

print("Lade Trainingsdaten...")
train_pl = pl.read_parquet(train_path)
print(f"Train: {len(train_pl):,} rows, {len(train_pl.columns)} cols")

FEATURES = [c for c in train_pl.columns if c not in EXCLUDE]
CAT_COLS  = [c for c in ["line_name", "stop_name", "event_type", "season", "gtfs_year"] if c in FEATURES]

print(f"\nFeatures ({len(FEATURES)}):")
print(FEATURES)
print(f"\nKategoriale Features: {CAT_COLS}")
```

    Lade Trainingsdaten...
    Train: 55,484,578 rows, 40 cols
    
    Features (32):
    ['line_name', 'stop_name', 'district_nr', 'temperature', 'precipitation', 'wind_speed', 'flood_intensity', 'event_type', 'event_size', 'hour', 'weekday', 'month', 'year', 'season', 'is_weekend', 'is_november', 'gtfs_year', 'has_rain', 'has_heavy_rain', 'has_snow', 'has_flood', 'is_hot', 'is_holiday', 'has_event', 'event_weight', 'dwell_time', 'n_lines_at_stop', 'n_stops_line', 'is_start_stop', 'is_end_stop', 'event_weight_x_hour', 'is_late_night_weekend']
    
    Kategoriale Features: ['line_name', 'stop_name', 'event_type', 'season', 'gtfs_year']


## Validation Split

Wir splitten die Trainingsdaten zeitlich: **2023 + erstes Halbjahr 2024** als eigentliche Trainingsdaten, **zweites Halbjahr 2024** als internes Validation-Set für Early Stopping. So sieht das Modell beim Training nie Daten aus 2025.


```python
# Zeitlicher Validation-Split innerhalb der Trainingsdaten
# Train:      2023-01 bis 2024-06
# Validation: 2024-07 bis 2024-12
val_mask = (
    (train_pl["operating_date"].dt.year() == 2024)
    & (train_pl["operating_date"].dt.month() >= 7)
)

train_sub = train_pl.filter(~val_mask)
val_sub   = train_pl.filter(val_mask)

print(f"Train subset:      {len(train_sub):,} rows")
print(f"Validation subset: {len(val_sub):,} rows")

# Pandas konvertieren für LightGBM
# Kategoriale Spalten als pandas Categorical — LightGBM erkennt diese nativ
def to_lgb_df(pl_df: pl.DataFrame, features: list, cat_cols: list) -> pd.DataFrame:
    pdf = pl_df.select(features).to_pandas()
    for col in cat_cols:
        if col in pdf.columns:
            pdf[col] = pdf[col].astype("category")
    return pdf

print("Konvertiere zu Pandas...")
X_train = to_lgb_df(train_sub, FEATURES, CAT_COLS)
y_train = train_sub[TARGET].to_numpy()

X_val   = to_lgb_df(val_sub, FEATURES, CAT_COLS)
y_val   = val_sub[TARGET].to_numpy()

print("Fertig.")
```

    Train subset:      41,230,594 rows
    Validation subset: 14,253,984 rows
    Konvertiere zu Pandas...
    Fertig.


## Training

LightGBM-Parameter für den ersten Lauf — bewusst konservativ:
- `num_leaves=63`: moderate Baumkomplexität
- `learning_rate=0.05`: langsam und stabil
- `n_estimators=1000` mit Early Stopping nach 50 Runden ohne Verbesserung
- `metric=mae`: optimiert direkt auf unsere Hauptmetrik


```python
lgb_train = lgb.Dataset(X_train, label=y_train, free_raw_data=False)
lgb_val   = lgb.Dataset(X_val,   label=y_val,   reference=lgb_train, free_raw_data=False)

params = {
    "objective":     "regression_l1",   # optimiert MAE direkt
    "metric":        "mae",
    "num_leaves":    63,
    "learning_rate": 0.05,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq":  5,
    "min_child_samples": 50,
    "verbose":       -1,
    "n_jobs":        -1,
}

callbacks = [
    lgb.early_stopping(stopping_rounds=50, verbose=True),
    lgb.log_evaluation(period=50),
]

print("Training startet...")
model = lgb.train(
    params,
    lgb_train,
    num_boost_round=1000,
    valid_sets=[lgb_val],
    callbacks=callbacks,
)

print(f"\nBeste Iteration: {model.best_iteration}")
print(f"Bestes Val-MAE:  {model.best_score['valid_0']['l1']:.2f}s")
```

    Training startet...


    Training until validation scores don't improve for 50 rounds
    [50]	valid_0's l1: 49.5621
    [100]	valid_0's l1: 49.3104
    [150]	valid_0's l1: 49.2009
    [200]	valid_0's l1: 49.1464
    [250]	valid_0's l1: 49.1222
    [300]	valid_0's l1: 49.1017
    [350]	valid_0's l1: 49.0799
    [400]	valid_0's l1: 49.0635
    [450]	valid_0's l1: 49.0591
    [500]	valid_0's l1: 49.0541
    Early stopping, best iteration is:
    [481]	valid_0's l1: 49.0503
    
    Beste Iteration: 481
    Bestes Val-MAE:  49.05s


## Validation — Ergebnis


```python
val_pred = model.predict(X_val, num_iteration=model.best_iteration)

val_mae  = np.abs(y_val - val_pred).mean()
val_rmse = np.sqrt(((y_val - val_pred) ** 2).mean())
val_otp  = (np.abs(y_val - val_pred) <= 60).mean()

BASELINE_MAE = 50.0  # Stop Mean aus Baseline-Notebook (06_prediction_1-baseline)

print(f"Val MAE:          {val_mae:.1f}s")
print(f"Val RMSE:         {val_rmse:.1f}s")
print(f"Val OTP (±60s):   {val_otp:.1%}")
print()
print(f"Baseline (Stop Mean): {BASELINE_MAE}s")
delta = BASELINE_MAE - val_mae
if delta > 0:
    print(f"Modell schlaegt Baseline um {delta:.1f}s")
else:
    print(f"Modell schlechter als Baseline um {abs(delta):.1f}s — Parameter pruefen")
```

    Val MAE:          49.1s
    Val RMSE:         85.0s
    Val OTP (±60s):   75.5%
    
    Baseline (Stop Mean): 50.0s
    Modell schlaegt Baseline um 0.9s


## Feature Importance


```python
import plotly.express as px

importance = pd.DataFrame({
    "feature":    model.feature_name(),
    "importance": model.feature_importance(importance_type="gain"),
}).sort_values("importance", ascending=False).head(20)

fig = px.bar(
    importance,
    x="importance",
    y="feature",
    orientation="h",
    title="Top 20 Feature Importance (Gain)",
    labels={"importance": "Gain", "feature": ""},
)
fig.update_layout(yaxis=dict(autorange="reversed"), height=550)
fig.show()

show_df(importance.reset_index(drop=True))
```




<style type="text/css">
#T_c2f3d thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_c2f3d td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_c2f3d tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_c2f3d tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_c2f3d tr:hover td {
  background-color: #eef3f8;
}
#T_c2f3d_row0_col0, #T_c2f3d_row1_col0, #T_c2f3d_row2_col0, #T_c2f3d_row3_col0, #T_c2f3d_row4_col0, #T_c2f3d_row5_col0, #T_c2f3d_row6_col0, #T_c2f3d_row7_col0, #T_c2f3d_row8_col0, #T_c2f3d_row9_col0, #T_c2f3d_row10_col0, #T_c2f3d_row11_col0, #T_c2f3d_row12_col0, #T_c2f3d_row13_col0, #T_c2f3d_row14_col0, #T_c2f3d_row15_col0, #T_c2f3d_row16_col0, #T_c2f3d_row17_col0, #T_c2f3d_row18_col0, #T_c2f3d_row19_col0 {
  text-align: left;
}
#T_c2f3d_row0_col1, #T_c2f3d_row1_col1, #T_c2f3d_row2_col1, #T_c2f3d_row3_col1, #T_c2f3d_row4_col1, #T_c2f3d_row5_col1, #T_c2f3d_row6_col1, #T_c2f3d_row7_col1, #T_c2f3d_row8_col1, #T_c2f3d_row9_col1, #T_c2f3d_row10_col1, #T_c2f3d_row11_col1, #T_c2f3d_row12_col1, #T_c2f3d_row13_col1, #T_c2f3d_row14_col1, #T_c2f3d_row15_col1, #T_c2f3d_row16_col1, #T_c2f3d_row17_col1, #T_c2f3d_row18_col1, #T_c2f3d_row19_col1 {
  text-align: right;
}
</style>
<table id="T_c2f3d">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_c2f3d_level0_col0" class="col_heading level0 col0" >feature</th>
      <th id="T_c2f3d_level0_col1" class="col_heading level0 col1" >importance</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_c2f3d_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_c2f3d_row0_col0" class="data row0 col0" >dwell_time</td>
      <td id="T_c2f3d_row0_col1" class="data row0 col1" >14835920.71</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_c2f3d_row1_col0" class="data row1 col0" >stop_name</td>
      <td id="T_c2f3d_row1_col1" class="data row1 col1" >12662327.64</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_c2f3d_row2_col0" class="data row2 col0" >hour</td>
      <td id="T_c2f3d_row2_col1" class="data row2 col1" >5255929.66</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_c2f3d_row3_col0" class="data row3 col0" >line_name</td>
      <td id="T_c2f3d_row3_col1" class="data row3 col1" >2804034.06</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_c2f3d_row4_col0" class="data row4 col0" >weekday</td>
      <td id="T_c2f3d_row4_col1" class="data row4 col1" >1804062.50</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_c2f3d_row5_col0" class="data row5 col0" >month</td>
      <td id="T_c2f3d_row5_col1" class="data row5 col1" >1170301.06</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_c2f3d_row6_col0" class="data row6 col0" >temperature</td>
      <td id="T_c2f3d_row6_col1" class="data row6 col1" >676527.31</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_c2f3d_row7_col0" class="data row7 col0" >wind_speed</td>
      <td id="T_c2f3d_row7_col1" class="data row7 col1" >348464.85</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_c2f3d_row8_col0" class="data row8 col0" >event_type</td>
      <td id="T_c2f3d_row8_col1" class="data row8 col1" >342169.37</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_c2f3d_row9_col0" class="data row9 col0" >precipitation</td>
      <td id="T_c2f3d_row9_col1" class="data row9 col1" >281741.49</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_c2f3d_row10_col0" class="data row10 col0" >year</td>
      <td id="T_c2f3d_row10_col1" class="data row10 col1" >237995.28</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_c2f3d_row11_col0" class="data row11 col0" >season</td>
      <td id="T_c2f3d_row11_col1" class="data row11 col1" >231475.60</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_c2f3d_row12_col0" class="data row12 col0" >n_stops_line</td>
      <td id="T_c2f3d_row12_col1" class="data row12 col1" >199666.53</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_c2f3d_row13_col0" class="data row13 col0" >is_weekend</td>
      <td id="T_c2f3d_row13_col1" class="data row13 col1" >193783.97</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_c2f3d_row14_col0" class="data row14 col0" >event_weight_x_hour</td>
      <td id="T_c2f3d_row14_col1" class="data row14 col1" >169835.57</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_c2f3d_row15_col0" class="data row15 col0" >is_late_night_weekend</td>
      <td id="T_c2f3d_row15_col1" class="data row15 col1" >149197.77</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_c2f3d_row16_col0" class="data row16 col0" >is_holiday</td>
      <td id="T_c2f3d_row16_col1" class="data row16 col1" >126587.53</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_c2f3d_row17_col0" class="data row17 col0" >n_lines_at_stop</td>
      <td id="T_c2f3d_row17_col1" class="data row17 col1" >110251.96</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_c2f3d_row18_col0" class="data row18 col0" >flood_intensity</td>
      <td id="T_c2f3d_row18_col1" class="data row18 col1" >92395.34</td>
    </tr>
    <tr>
      <th id="T_c2f3d_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_c2f3d_row19_col0" class="data row19 col0" >is_november</td>
      <td id="T_c2f3d_row19_col1" class="data row19 col1" >89831.00</td>
    </tr>
  </tbody>
</table>



## Export

Modell und Test-Predictions speichern — werden in `06_prediction_3-evaluation.ipynb` geladen.


```python
import json as _json

# --- Modell (LightGBM nativ) ---
model_path = MODELS_DIR / "lgbm_v1.txt"
model.save_model(str(model_path))
print(f"Modell gespeichert: {model_path}")

# --- Params + Metadaten als JSON ---
meta = {
    "model":           "lgbm_v1",
    "best_iteration":  model.best_iteration,
    "val_mae":         round(val_mae, 2),
    "val_rmse":        round(val_rmse, 2),
    "baseline_mae":    BASELINE_MAE,
    "params":          params,
    "features":        FEATURES,
    "cat_cols":        CAT_COLS,
    "target":          TARGET,
    "train_rows":      len(train_sub),
    "val_rows":        len(val_sub),
}
meta_path = MODELS_DIR / "lgbm_v1_meta.json"
with open(meta_path, "w", encoding="utf-8") as f:
    _json.dump(meta, f, indent=2, ensure_ascii=False)
print(f"Metadaten gespeichert: {meta_path}")

# --- Test-Predictions ---
print("\nLade Testdaten...")
test_pl = pl.read_parquet(test_path)
X_test  = to_lgb_df(test_pl, FEATURES, CAT_COLS)
y_test  = test_pl[TARGET].to_numpy()

test_pred = model.predict(X_test, num_iteration=model.best_iteration)

pred_cols = {
    "actual":    y_test,
    "predicted": test_pred.astype("float32"),
    "line_name": test_pl["line_name"],
    "stop_name": test_pl["stop_name"],
    "hour":      test_pl["hour"],
    "month":     test_pl["month"],
    "has_rain":  test_pl["has_rain"],
    "has_snow":  test_pl["has_snow"],
    "has_event": test_pl["has_event"],
}
# is_anomal: flags Nov 14–Dec 23 2025 rows — useful for evaluation breakdown
if "is_anomal" in test_pl.columns:
    pred_cols["is_anomal"] = test_pl["is_anomal"]

pred_df = pl.DataFrame(pred_cols)

pred_path = Path(test_path).parent / "test_predictions.parquet"
pred_df.write_parquet(pred_path)
print(f"Predictions gespeichert: {pred_path}")

# Quick check Test-MAE
test_mae = np.abs(y_test - test_pred).mean()
print(f"\nTest MAE:  {test_mae:.1f}s")
print(f"Baseline:  {BASELINE_MAE}s")
print(f"Gewinn:    {BASELINE_MAE - test_mae:.1f}s")
```

    Modell gespeichert: /Users/kaywiegand/Workspace/zh-tram-flow/data/models/lgbm_v1.txt
    Metadaten gespeichert: /Users/kaywiegand/Workspace/zh-tram-flow/data/models/lgbm_v1_meta.json
    
    Lade Testdaten...
    Predictions gespeichert: /Users/kaywiegand/Workspace/zh-tram-flow/data/processed/test_predictions.parquet
    
    Test MAE:  45.7s
    Baseline:  50.0s
    Gewinn:    4.3s

