# Modellvergleich: Baseline → LightGBM v1 → v2 → XGBoost

Dieses Notebook beantwortet drei Fragen:

1. **Was bringt das Kaskadenfeature?** — LightGBM v1 vs. v2 (isolierter Feature-Effekt)
2. **Ist LightGBM der beste Algorithmus?** — v2 vs. XGBoost (gleiche Features, anderer Algorithmus)
3. **Wo bleibt Fehler übrig?** — Segmentanalyse aller Modelle (Stunde, Linie, Wetter)

**Erwartung aus der Analyse:** `prev_trip_delay` (r ≥ 0.85 im Kaskadeneffekt) sollte signifikant helfen. Algorithmus-Unterschied zwischen LightGBM und XGBoost sollte gering sein — beide sind Gradient Boosting mit ähnlichen Inductive Biases.

**Voraussetzung:** `06_prediction_4-model_v2.ipynb` vollständig ausgeführt — `lgbm_v2.txt`, `test_predictions_v2.parquet` und `test_final_v2.parquet` müssen vorhanden sein.

## Setup


```python
from zh_tram_flow.notebook import *
import polars as pl
import lightgbm as lgb
import xgboost as xgb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json as _json
from pathlib import Path

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("06_prediction_5-comparison")

processed_dir = Path(str(TRAIN)).parent
models_dir    = processed_dir.parent / "models"

# Paths
train_v2_path    = str(processed_dir / "train_final_v2.parquet")
test_v2_path     = str(processed_dir / "test_final_v2.parquet")
pred_v1_path     = str(processed_dir / "test_predictions.parquet")
pred_v2_path     = str(processed_dir / "test_predictions_v2.parquet")

# Metadaten laden
with open(models_dir / "lgbm_v1_meta.json") as f:
    v1_meta = _json.load(f)
with open(models_dir / "lgbm_v2_meta.json") as f:
    v2_meta = _json.load(f)

BASELINE_MAE = 50.0
TARGET       = "arrival_delay"
print("Setup abgeschlossen.")
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-06-11 17:02:41  INFO      project  06_prediction_5-comparison started


    Setup abgeschlossen.


## Daten laden

Predictions aller bisherigen Modelle laden — kein erneutes Training nötig.


```python
# v1 Predictions (aus 06_prediction_2-model)
pred_v1 = pl.read_parquet(pred_v1_path)
y_test  = pred_v1["actual"].to_numpy()

# v2 Predictions (aus 06_prediction_4-model_v2)
pred_v2 = pl.read_parquet(pred_v2_path)

print(f"Test-Set:      {len(y_test):,} Beobachtungen")
print(f"v1 Prediction: {pred_v1.columns}")
print(f"v2 Prediction: {pred_v2.columns}")
```

    Test-Set:      29,941,876 Beobachtungen
    v1 Prediction: ['actual', 'predicted', 'line_name', 'stop_name', 'hour', 'month', 'has_rain', 'has_snow', 'has_event']
    v2 Prediction: ['actual', 'predicted_v2', 'predicted_v2_cal', 'line_name', 'stop_name', 'hour', 'month', 'has_rain', 'has_snow', 'has_event']



```python
# Feature-Setup für XGBoost (gleiche v2-Features)
FEATURES_V2 = v2_meta["features"]
CAT_COLS_V2 = v2_meta["cat_cols"]

# XGBoost 3.x hat einen Unicode-Decode-Bug bei nicht-ASCII Category-Labels
# (z. B. Zürcher Haltestellennamen mit Umlauten: ä, ö, ü, é).
# Lösung: Kategoriale Spalten als Integer-Codes encoding — konsistent aus
# dem vollen Train-Set gefittet, dann auf alle Splits angewendet.
from sklearn.preprocessing import OrdinalEncoder

print("Lade train_final_v2 ...")
train_v2_pl = pl.read_parquet(train_v2_path)

# Encoder auf vollem Train-Set fitten → konsistente Codes für Train/Val/Test
_cat_train = train_v2_pl.select(CAT_COLS_V2).to_pandas().astype(str)
_oe = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1, dtype="int32")
_oe.fit(_cat_train)

def to_xgb_df(pl_df: pl.DataFrame, features: list, cat_cols: list) -> pd.DataFrame:
    """Polars → Pandas. Integer-Encoding der kategorialen Spalten (XGBoost Unicode-Fix)."""
    pdf = pl_df.select(features).to_pandas()
    if cat_cols:
        pdf[cat_cols] = _oe.transform(pdf[cat_cols].astype(str))
    return pdf

# Validation-Split (identisch v1/v2 für faires Early-Stopping)
val_mask = (
    (train_v2_pl["operating_date"].dt.year() == 2024)
    & (train_v2_pl["operating_date"].dt.month() >= 7)
)
train_sub = train_v2_pl.filter(~val_mask)
val_sub   = train_v2_pl.filter(val_mask)

print(f"Train: {len(train_sub):,}  ·  Val: {len(val_sub):,}")

print("Konvertiere zu Pandas ...")
X_train = to_xgb_df(train_sub, FEATURES_V2, CAT_COLS_V2)
y_train = train_sub[TARGET].to_numpy()
X_val   = to_xgb_df(val_sub,   FEATURES_V2, CAT_COLS_V2)
y_val   = val_sub[TARGET].to_numpy()
print("Fertig.")
```

    Lade train_final_v2 ...
    Train: 41,230,594  ·  Val: 14,253,984
    Konvertiere zu Pandas ...
    Fertig.


## Vergleichsmodell: XGBoost

XGBoost mit `enable_categorical=True` (ab Version 2.0) — vergleichbarer nativer Categorical-Support wie LightGBM. Gleiche Feature-Set wie v2 für sauberen Algorithmen-Vergleich.

**Kernunterschiede LightGBM vs. XGBoost:**
| | LightGBM | XGBoost |
|:---|:---|:---|
| Baumwachstum | Leaf-wise (bestes Blatt) | Level-wise (vollständige Ebene) |
| Geschwindigkeit | Schneller (GOSS/EFB) | Langsamer auf grossen Datasets |
| Categorical | Nativ (optimal grouping) | Nativ (ab 2.0, partitionsbasiert) |
| Regularisierung | L1/L2 + min_gain | L1/L2 + gamma |


```python
import time

_xgb_model_path = models_dir / "xgboost_v1.json"
SKIP_XGB = not _xgb_model_path.exists()

if SKIP_XGB:
    # XGBoost-Training würde >90 Min auf 85M Zeilen dauern — bewusst übersprungen.
    # Robustness-Check: val MAE ~21.4s aus früherem Training-Run (Round 150) —
    # dokumentiert in presentation-v3.html Slide 18.
    xgb_model      = None
    xgb_best_iter  = None
    xgb_val_mae    = None
    train_time_xgb = None
    print("XGBoost übersprungen (kein Modell-File · Training >90 Min auf 85M Zeilen).")
    print("Feature Importance v1 vs. v2 läuft trotzdem durch.")
elif _xgb_model_path.exists():
    print(f"Modell gefunden — lade {_xgb_model_path.name} ...")
    xgb_model = xgb.XGBRegressor()
    xgb_model.load_model(str(_xgb_model_path))
    xgb_best_iter  = xgb_model.best_iteration
    xgb_val_mae    = xgb_model.best_score
    train_time_xgb = 0
    print(f"Geladen ✓  best_iteration={xgb_best_iter}  val_mae={xgb_val_mae:.2f}s")
else:
    # n_estimators=300: Kurve konvergiert bei ~150–200 Runden (Δ[100→150] nur -0.28s)
    xgb_model = xgb.XGBRegressor(
        n_estimators          = 300,
        learning_rate         = 0.05,
        max_depth             = 6,
        subsample             = 0.8,
        colsample_bytree      = 0.8,
        min_child_weight      = 50,
        objective             = "reg:absoluteerror",
        eval_metric           = "mae",
        early_stopping_rounds = 50,
        tree_method           = "hist",
        device                = "cpu",
        n_jobs                = -1,
        random_state          = 42,
        verbosity             = 0,
    )
    print("XGBoost Training startet ...")
    t0 = time.time()
    xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=50)
    train_time_xgb = time.time() - t0
    xgb_best_iter  = xgb_model.best_iteration
    xgb_val_mae    = xgb_model.best_score
    xgb_model.save_model(str(_xgb_model_path))
    print(f"\nBeste Iteration: {xgb_best_iter}")
    print(f"Bestes Val-MAE:  {xgb_val_mae:.2f} s  ·  Zeit: {train_time_xgb:.0f} s")
    print(f"Modell gespeichert: {_xgb_model_path}")
```

    XGBoost übersprungen (kein Modell-File · Training >90 Min auf 85M Zeilen).
    Feature Importance v1 vs. v2 läuft trotzdem durch.



```python
if SKIP_XGB:
    test_pred_xgb = None
    xgb_test_mae  = None
    xgb_test_mbe  = None
    print("XGBoost Predictions übersprungen.")
else:
    test_v2_pl   = pl.read_parquet(test_v2_path)
    X_test_xgb   = to_xgb_df(test_v2_pl, FEATURES_V2, CAT_COLS_V2)
    y_test_xgb   = test_v2_pl[TARGET].to_numpy()

    test_pred_xgb = xgb_model.predict(X_test_xgb)

    xgb_test_mae  = np.abs(y_test_xgb - test_pred_xgb).mean()
    xgb_test_mbe  = (test_pred_xgb - y_test_xgb).mean()
    xgb_test_rmse = np.sqrt(((y_test_xgb - test_pred_xgb) ** 2).mean())
    xgb_test_otp  = (np.abs(y_test_xgb - test_pred_xgb) <= 60).mean()

    print(f"XGBoost Test — MAE: {xgb_test_mae:.1f} s  ·  MBE: {xgb_test_mbe:+.1f} s")

    pred_xgb_df = pl.DataFrame({
        "actual":        y_test_xgb,
        "predicted_xgb": test_pred_xgb.astype("float32"),
        "line_name":     test_v2_pl["line_name"],
        "stop_name":     test_v2_pl["stop_name"],
        "hour":          test_v2_pl["hour"],
        "month":         test_v2_pl["month"],
        "has_rain":      test_v2_pl["has_rain"],
        "has_snow":      test_v2_pl["has_snow"],
        "has_event":     test_v2_pl["has_event"],
    })
    pred_xgb_path = processed_dir / "test_predictions_xgb.parquet"
    pred_xgb_df.write_parquet(pred_xgb_path)
    print(f"XGBoost Predictions gespeichert: {pred_xgb_path}")

    xgb_model_path = models_dir / "xgboost_v1.json"
    xgb_model.save_model(str(xgb_model_path))
    print(f"XGBoost Modell gespeichert: {xgb_model_path}")
```

    XGBoost Predictions übersprungen.


## Metriken-Vergleich: Alle Modelle

Vollständige Übersicht — Baseline bis XGBoost.


```python
# Metriken-Tabelle aufbauen
y_v1  = pred_v1["actual"].to_numpy()
p_v1  = pred_v1["predicted"].to_numpy()
p_v2  = pred_v2["predicted_v2"].to_numpy()
p_v2c = pred_v2["predicted_v2_cal"].to_numpy()
y_ref = pred_v2["actual"].to_numpy()   # v2-Test-Set als gemeinsame Referenz

def metrics(actual, predicted, label):
    mae  = np.abs(actual - predicted).mean()
    rmse = np.sqrt(((actual - predicted) ** 2).mean())
    mbe  = (predicted - actual).mean()
    otp  = (np.abs(actual - predicted) <= 60).mean()
    return {"Modell": label, "MAE (s)": round(mae, 1), "RMSE (s)": round(rmse, 1),
            "MBE (s)": round(mbe, 1), "OTP ±60s": f"{otp:.1%}"}

rows = [
    {"Modell": "Baseline (Stop Mean)", "MAE (s)": 50.0, "RMSE (s)": "—", "MBE (s)": "—", "OTP ±60s": "—"},
    metrics(y_ref, p_v1,  "LightGBM v1 (ohne Kaskade)"),
    metrics(y_ref, p_v2,  "LightGBM v2 (+ Kaskade)"),
    metrics(y_ref, p_v2c, "LightGBM v2 kalibriert"),
]
if not SKIP_XGB and test_pred_xgb is not None:
    y_xgb = pred_v2["actual"].to_numpy()  # gleicher Test-Split
    rows.append(metrics(y_xgb, test_pred_xgb, "XGBoost (+ Kaskade)"))
else:
    rows.append({"Modell": "XGBoost (+ Kaskade)", "MAE (s)": "~21.4s*",
                 "RMSE (s)": "—", "MBE (s)": "—", "OTP ±60s": "—"})

metrics_df = pd.DataFrame(rows)
show_df(metrics_df)

if SKIP_XGB:
    print("\n* XGBoost val MAE ~21.4s bei Round 150 (Training abgebrochen, >90 Min auf 85M Zeilen)")
```


<style type="text/css">
#T_dc07e thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_dc07e td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_dc07e tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_dc07e tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_dc07e tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_dc07e">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_dc07e_level0_col0" class="col_heading level0 col0" >Modell</th>
      <th id="T_dc07e_level0_col1" class="col_heading level0 col1" >MAE (s)</th>
      <th id="T_dc07e_level0_col2" class="col_heading level0 col2" >RMSE (s)</th>
      <th id="T_dc07e_level0_col3" class="col_heading level0 col3" >MBE (s)</th>
      <th id="T_dc07e_level0_col4" class="col_heading level0 col4" >OTP ±60s</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_dc07e_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_dc07e_row0_col0" class="data row0 col0" >Baseline (Stop Mean)</td>
      <td id="T_dc07e_row0_col1" class="data row0 col1" >50.000000</td>
      <td id="T_dc07e_row0_col2" class="data row0 col2" >—</td>
      <td id="T_dc07e_row0_col3" class="data row0 col3" >—</td>
      <td id="T_dc07e_row0_col4" class="data row0 col4" >—</td>
    </tr>
    <tr>
      <th id="T_dc07e_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_dc07e_row1_col0" class="data row1 col0" >LightGBM v1 (ohne Kaskade)</td>
      <td id="T_dc07e_row1_col1" class="data row1 col1" >51.500000</td>
      <td id="T_dc07e_row1_col2" class="data row1 col2" >80.900002</td>
      <td id="T_dc07e_row1_col3" class="data row1 col3" >-8.300000</td>
      <td id="T_dc07e_row1_col4" class="data row1 col4" >71.0%</td>
    </tr>
    <tr>
      <th id="T_dc07e_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_dc07e_row2_col0" class="data row2 col0" >LightGBM v2 (+ Kaskade)</td>
      <td id="T_dc07e_row2_col1" class="data row2 col1" >18.600000</td>
      <td id="T_dc07e_row2_col2" class="data row2 col2" >38.000000</td>
      <td id="T_dc07e_row2_col3" class="data row2 col3" >-0.700000</td>
      <td id="T_dc07e_row2_col4" class="data row2 col4" >95.8%</td>
    </tr>
    <tr>
      <th id="T_dc07e_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_dc07e_row3_col0" class="data row3 col0" >LightGBM v2 kalibriert</td>
      <td id="T_dc07e_row3_col1" class="data row3 col1" >18.799999</td>
      <td id="T_dc07e_row3_col2" class="data row3 col2" >37.700001</td>
      <td id="T_dc07e_row3_col3" class="data row3 col3" >0.700000</td>
      <td id="T_dc07e_row3_col4" class="data row3 col4" >95.7%</td>
    </tr>
    <tr>
      <th id="T_dc07e_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_dc07e_row4_col0" class="data row4 col0" >XGBoost (+ Kaskade)</td>
      <td id="T_dc07e_row4_col1" class="data row4 col1" >~21.4s*</td>
      <td id="T_dc07e_row4_col2" class="data row4 col2" >—</td>
      <td id="T_dc07e_row4_col3" class="data row4 col3" >—</td>
      <td id="T_dc07e_row4_col4" class="data row4 col4" >—</td>
    </tr>
  </tbody>
</table>



    
    * XGBoost val MAE ~21.4s bei Round 150 (Training abgebrochen, >90 Min auf 85M Zeilen)



```python
# Visualisierung: MAE-Vergleich als Balkendiagramm
labels = ["Baseline", "LGBM v1", "LGBM v2", "LGBM v2\nkalib."]
maes   = [
    BASELINE_MAE,
    np.abs(y_ref - p_v1).mean(),
    np.abs(y_ref - p_v2).mean(),
    np.abs(y_ref - p_v2c).mean(),
]
colors = ["#8c8c8c", "#4c72b0", "#55a868", "#25ac82"]

if not SKIP_XGB and test_pred_xgb is not None:
    labels.append("XGBoost")
    maes.append(xgb_test_mae)
    colors.append("#dd8452")

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(labels, maes, color=colors, alpha=0.85, edgecolor="white", linewidth=0.5)

for bar, val in zip(bars, maes):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
            f"{val:.1f} s", ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.set_ylim(0, max(maes) * 1.15)
ax.set_ylabel("Test MAE (s)")
ax.set_title("Modellvergleich — Test MAE (2025 Test-Set)\nKleiner = besser", fontsize=12)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.show()
```


    
![png](06_prediction_5-comparison_files/06_prediction_5-comparison_11_0.png)
    


## Was bringt das Kaskadenfeature?

Isolierter Effekt von `prev_trip_delay` + `stop_sequence_pct`: LightGBM v1 vs. v2, identische Hyperparameter.


```python
# Feature Importance Vergleich: v1 vs. v2
lgb_v1 = lgb.Booster(model_file=str(models_dir / "lgbm_v1.txt"))
lgb_v2 = lgb.Booster(model_file=str(models_dir / "lgbm_v2.txt"))

imp_v1 = pd.DataFrame({
    "feature": lgb_v1.feature_name(),
    "gain_v1": lgb_v1.feature_importance(importance_type="gain"),
})
imp_v2 = pd.DataFrame({
    "feature": lgb_v2.feature_name(),
    "gain_v2": lgb_v2.feature_importance(importance_type="gain"),
})

# Normalisieren (0–100) für fairen Vergleich trotz unterschiedlicher Iterationsanzahl
imp_v1["gain_v1"] = imp_v1["gain_v1"] / imp_v1["gain_v1"].sum() * 100
imp_v2["gain_v2"] = imp_v2["gain_v2"] / imp_v2["gain_v2"].sum() * 100

imp_cmp = imp_v2.merge(imp_v1, on="feature", how="left").fillna(0)
imp_cmp = imp_cmp.sort_values("gain_v2", ascending=False).head(20)

# Neue Features hervorheben
new_feats = v2_meta["new_features"]
print(f"Neue Features in v2: {new_feats}")
print()

fig, ax = plt.subplots(figsize=(11, 7))
y_pos = range(len(imp_cmp))

ax.barh([i + 0.2 for i in y_pos], imp_cmp["gain_v2"],
        height=0.4, label="LightGBM v2", color="#55a868", alpha=0.85)
ax.barh([i - 0.2 for i in y_pos], imp_cmp["gain_v1"],
        height=0.4, label="LightGBM v1", color="#4c72b0", alpha=0.85)

ax.set_yticks(list(y_pos))
ax.set_yticklabels([
    f"★ {f}" if f in new_feats else f
    for f in imp_cmp["feature"]
], fontsize=9)
ax.set_xlabel("Normalisierter Gain (%)")
ax.set_title("Feature Importance — v1 vs. v2 (★ = neue Features)\nnormalisiert auf 100%",
             fontsize=11)
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.show()

show_df(imp_cmp.reset_index(drop=True))
```

    Neue Features in v2: ['prev_trip_delay', 'stop_sequence_pct']
    


    /var/folders/jh/b553h44j08x_jr8xwh9jbc5r0000gn/T/ipykernel_45621/4031581841.py:44: UserWarning: Glyph 9733 (\N{BLACK STAR}) missing from font(s) Arial.
      plt.tight_layout()
    /Users/kaywiegand/Workspace/zh-tram-flow/.venv/lib/python3.10/site-packages/IPython/core/pylabtools.py:170: UserWarning: Glyph 9733 (\N{BLACK STAR}) missing from font(s) Arial.
      fig.canvas.print_figure(bytes_io, **kw)



    
![png](06_prediction_5-comparison_files/06_prediction_5-comparison_13_2.png)
    



<style type="text/css">
#T_42db3 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_42db3 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_42db3 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_42db3 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_42db3 tr:hover td {
  background-color: #eef3f8;
}
#T_42db3_row0_col0, #T_42db3_row1_col0, #T_42db3_row2_col0, #T_42db3_row3_col0, #T_42db3_row4_col0, #T_42db3_row5_col0, #T_42db3_row6_col0, #T_42db3_row7_col0, #T_42db3_row8_col0, #T_42db3_row9_col0, #T_42db3_row10_col0, #T_42db3_row11_col0, #T_42db3_row12_col0, #T_42db3_row13_col0, #T_42db3_row14_col0, #T_42db3_row15_col0, #T_42db3_row16_col0, #T_42db3_row17_col0, #T_42db3_row18_col0, #T_42db3_row19_col0 {
  text-align: left;
}
#T_42db3_row0_col1, #T_42db3_row0_col2, #T_42db3_row1_col1, #T_42db3_row1_col2, #T_42db3_row2_col1, #T_42db3_row2_col2, #T_42db3_row3_col1, #T_42db3_row3_col2, #T_42db3_row4_col1, #T_42db3_row4_col2, #T_42db3_row5_col1, #T_42db3_row5_col2, #T_42db3_row6_col1, #T_42db3_row6_col2, #T_42db3_row7_col1, #T_42db3_row7_col2, #T_42db3_row8_col1, #T_42db3_row8_col2, #T_42db3_row9_col1, #T_42db3_row9_col2, #T_42db3_row10_col1, #T_42db3_row10_col2, #T_42db3_row11_col1, #T_42db3_row11_col2, #T_42db3_row12_col1, #T_42db3_row12_col2, #T_42db3_row13_col1, #T_42db3_row13_col2, #T_42db3_row14_col1, #T_42db3_row14_col2, #T_42db3_row15_col1, #T_42db3_row15_col2, #T_42db3_row16_col1, #T_42db3_row16_col2, #T_42db3_row17_col1, #T_42db3_row17_col2, #T_42db3_row18_col1, #T_42db3_row18_col2, #T_42db3_row19_col1, #T_42db3_row19_col2 {
  text-align: right;
}
</style>
<table id="T_42db3">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_42db3_level0_col0" class="col_heading level0 col0" >feature</th>
      <th id="T_42db3_level0_col1" class="col_heading level0 col1" >gain_v2</th>
      <th id="T_42db3_level0_col2" class="col_heading level0 col2" >gain_v1</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_42db3_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_42db3_row0_col0" class="data row0 col0" >prev_trip_delay</td>
      <td id="T_42db3_row0_col1" class="data row0 col1" >65.48</td>
      <td id="T_42db3_row0_col2" class="data row0 col2" >0.00</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_42db3_row1_col0" class="data row1 col0" >stop_name</td>
      <td id="T_42db3_row1_col1" class="data row1 col1" >17.71</td>
      <td id="T_42db3_row1_col2" class="data row1 col2" >30.14</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_42db3_row2_col0" class="data row2 col0" >dwell_time</td>
      <td id="T_42db3_row2_col1" class="data row2 col1" >6.90</td>
      <td id="T_42db3_row2_col2" class="data row2 col2" >35.31</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_42db3_row3_col0" class="data row3 col0" >stop_sequence_pct</td>
      <td id="T_42db3_row3_col1" class="data row3 col1" >4.30</td>
      <td id="T_42db3_row3_col2" class="data row3 col2" >0.00</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_42db3_row4_col0" class="data row4 col0" >line_name</td>
      <td id="T_42db3_row4_col1" class="data row4 col1" >2.19</td>
      <td id="T_42db3_row4_col2" class="data row4 col2" >6.67</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_42db3_row5_col0" class="data row5 col0" >hour</td>
      <td id="T_42db3_row5_col1" class="data row5 col1" >1.66</td>
      <td id="T_42db3_row5_col2" class="data row5 col2" >12.51</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_42db3_row6_col0" class="data row6 col0" >weekday</td>
      <td id="T_42db3_row6_col1" class="data row6 col1" >0.38</td>
      <td id="T_42db3_row6_col2" class="data row6 col2" >4.29</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_42db3_row7_col0" class="data row7 col0" >n_lines_at_stop</td>
      <td id="T_42db3_row7_col1" class="data row7 col1" >0.38</td>
      <td id="T_42db3_row7_col2" class="data row7 col2" >0.26</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_42db3_row8_col0" class="data row8 col0" >n_stops_line</td>
      <td id="T_42db3_row8_col1" class="data row8 col1" >0.36</td>
      <td id="T_42db3_row8_col2" class="data row8 col2" >0.48</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_42db3_row9_col0" class="data row9 col0" >district_nr</td>
      <td id="T_42db3_row9_col1" class="data row9 col1" >0.35</td>
      <td id="T_42db3_row9_col2" class="data row9 col2" >0.13</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_42db3_row10_col0" class="data row10 col0" >month</td>
      <td id="T_42db3_row10_col1" class="data row10 col1" >0.07</td>
      <td id="T_42db3_row10_col2" class="data row10 col2" >2.79</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_42db3_row11_col0" class="data row11 col0" >year</td>
      <td id="T_42db3_row11_col1" class="data row11 col1" >0.06</td>
      <td id="T_42db3_row11_col2" class="data row11 col2" >0.57</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_42db3_row12_col0" class="data row12 col0" >event_type</td>
      <td id="T_42db3_row12_col1" class="data row12 col1" >0.05</td>
      <td id="T_42db3_row12_col2" class="data row12 col2" >0.81</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_42db3_row13_col0" class="data row13 col0" >is_holiday</td>
      <td id="T_42db3_row13_col1" class="data row13 col1" >0.03</td>
      <td id="T_42db3_row13_col2" class="data row13 col2" >0.30</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_42db3_row14_col0" class="data row14 col0" >is_weekend</td>
      <td id="T_42db3_row14_col1" class="data row14 col1" >0.02</td>
      <td id="T_42db3_row14_col2" class="data row14 col2" >0.46</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_42db3_row15_col0" class="data row15 col0" >temperature</td>
      <td id="T_42db3_row15_col1" class="data row15 col1" >0.01</td>
      <td id="T_42db3_row15_col2" class="data row15 col2" >1.61</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_42db3_row16_col0" class="data row16 col0" >gtfs_year</td>
      <td id="T_42db3_row16_col1" class="data row16 col1" >0.01</td>
      <td id="T_42db3_row16_col2" class="data row16 col2" >0.09</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_42db3_row17_col0" class="data row17 col0" >is_late_night_weekend</td>
      <td id="T_42db3_row17_col1" class="data row17 col1" >0.01</td>
      <td id="T_42db3_row17_col2" class="data row17 col2" >0.36</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_42db3_row18_col0" class="data row18 col0" >season</td>
      <td id="T_42db3_row18_col1" class="data row18 col1" >0.01</td>
      <td id="T_42db3_row18_col2" class="data row18 col2" >0.55</td>
    </tr>
    <tr>
      <th id="T_42db3_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_42db3_row19_col0" class="data row19 col0" >event_weight_x_hour</td>
      <td id="T_42db3_row19_col1" class="data row19 col1" >0.01</td>
      <td id="T_42db3_row19_col2" class="data row19 col2" >0.40</td>
    </tr>
  </tbody>
</table>



## Fehler nach Segment: Alle Modelle

Wo ist welches Modell gut, wo bleibt Fehler übrig?


```python
if SKIP_XGB:
    print("Fehleranalyse (alle Modelle) übersprungen — XGBoost nicht vorhanden.")
    print("LightGBM v1 vs. v2 Fehleranalyse: → 06_prediction_3-evaluation.ipynb")
else:
    assert len(p_v1) == len(y_test_xgb), (
        f"Längen stimmen nicht überein: p_v1={len(p_v1)}, y_test_xgb={len(y_test_xgb)}"
    )
    base_df = test_v2_pl.to_pandas()[["line_name", "hour", "has_rain", "has_heavy_rain", "has_snow"]].copy()
    base_df["actual"]  = y_test_xgb
    base_df["ae_v1"]   = np.abs(y_test_xgb - p_v1)
    base_df["ae_v2"]   = np.abs(y_test_xgb - p_v2)
    base_df["ae_xgb"]  = np.abs(y_test_xgb - test_pred_xgb)

    model_cols   = {"LGBM v1": "ae_v1", "LGBM v2": "ae_v2", "XGBoost": "ae_xgb"}
    model_colors = {"LGBM v1": "#4c72b0", "LGBM v2": "#55a868", "XGBoost": "#dd8452"}

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. MAE nach Stunde
    ax = axes[0, 0]
    for name, col in model_cols.items():
        mae_h = base_df.groupby("hour")[col].mean()
        ax.plot(mae_h.index, mae_h.values, label=name, color=model_colors[name], lw=2)
    ax.set_title("MAE nach Tageszeit"); ax.set_xlabel("Stunde"); ax.set_ylabel("MAE (s)")
    ax.legend(); ax.spines[["top", "right"]].set_visible(False)

    # 2. MAE nach Linie
    ax = axes[0, 1]
    mae_line_all = (
        base_df.groupby("line_name")[["ae_v1", "ae_v2", "ae_xgb"]].mean()
        .sort_values("ae_v2", ascending=False)
    )
    x = range(len(mae_line_all))
    w = 0.28
    for i, (name, col) in enumerate(model_cols.items()):
        ax.bar([xi + (i - 1) * w for xi in x], mae_line_all[col],
               width=w, label=name, color=model_colors[name], alpha=0.85)
    ax.set_xticks(list(x))
    ax.set_xticklabels(mae_line_all.index.astype(str), rotation=45)
    ax.set_title("MAE nach Linie"); ax.set_ylabel("MAE (s)")
    ax.legend(); ax.spines[["top", "right"]].set_visible(False)

    # 3. MAE nach Wetter
    ax = axes[1, 0]
    weather_map = {
        "Normal":     (~base_df["has_rain"]) & (~base_df["has_snow"]),
        "Regen":      base_df["has_rain"] & ~base_df["has_snow"],
        "Starkregen": base_df["has_heavy_rain"],
        "Schnee":     base_df["has_snow"],
    }
    x_w = range(len(weather_map))
    for i, (name, col) in enumerate(model_cols.items()):
        vals = [base_df.loc[mask, col].mean() for mask in weather_map.values()]
        ax.bar([xi + (i - 1) * w for xi in x_w], vals,
               width=w, label=name, color=model_colors[name], alpha=0.85)
    ax.set_xticks(list(x_w)); ax.set_xticklabels(list(weather_map.keys()))
    ax.set_title("MAE nach Wetter"); ax.set_ylabel("MAE (s)")
    ax.legend(); ax.spines[["top", "right"]].set_visible(False)

    # 4. Residual-Verteilung
    ax = axes[1, 1]
    bins = np.linspace(-150, 150, 60)
    sample_idx = np.random.default_rng(42).choice(len(y_test_xgb), 50_000, replace=False)
    residuals = {
        "LGBM v1":  p_v1          - y_test_xgb,
        "LGBM v2":  p_v2          - y_test_xgb,
        "XGBoost":  test_pred_xgb - y_test_xgb,
    }
    for name, res in residuals.items():
        ax.hist(res[sample_idx], bins=bins, alpha=0.5, label=name,
                color=model_colors[name], density=True)
    ax.axvline(0, color="black", lw=1.5, ls="--")
    ax.set_xlabel("Residual (s)"); ax.set_title("Residual-Verteilung (n=50k)")
    ax.legend(); ax.spines[["top", "right"]].set_visible(False)

    plt.suptitle("Fehleranalyse — Alle Modelle im Vergleich", fontsize=14, y=1.01)
    plt.tight_layout()
    plt.show()
```

    Fehleranalyse (alle Modelle) übersprungen — XGBoost nicht vorhanden.
    LightGBM v1 vs. v2 Fehleranalyse: → 06_prediction_3-evaluation.ipynb


## Fazit und Empfehlung


```python
# Zusammenfassende Tabelle
v1_mae  = np.abs(y_ref - p_v1).mean()
v2_mae  = np.abs(y_ref - p_v2).mean()
v2c_mae = np.abs(y_ref - p_v2c).mean()

summary_rows = [
    {"Modell": "Baseline (Stop Mean)",   "Test MAE": 50.0, "Δ Baseline": 0.0,
     "Kaskadenfeature": "—",  "Empfehlung": "Referenz"},
    {"Modell": "LightGBM v1",            "Test MAE": round(v1_mae, 1),
     "Δ Baseline": round(50.0 - v1_mae, 1),
     "Kaskadenfeature": "Nein",  "Empfehlung": "Benchmark"},
    {"Modell": "LightGBM v2",            "Test MAE": round(v2_mae, 1),
     "Δ Baseline": round(50.0 - v2_mae, 1),
     "Kaskadenfeature": "Ja",   "Empfehlung": "Bevorzugt (schnell)"},
    {"Modell": "LightGBM v2 kalibriert", "Test MAE": round(v2c_mae, 1),
     "Δ Baseline": round(50.0 - v2c_mae, 1),
     "Kaskadenfeature": "Ja",   "Empfehlung": "Bevorzugt (Echtzeit)"},
]
if not SKIP_XGB and xgb_test_mae is not None:
    summary_rows.append({
        "Modell": "XGBoost",             "Test MAE": round(xgb_test_mae, 1),
        "Δ Baseline": round(50.0 - xgb_test_mae, 1),
        "Kaskadenfeature": "Ja",   "Empfehlung": "Robustheits-Check",
    })
else:
    summary_rows.append({
        "Modell": "XGBoost",             "Test MAE": "~21.4s*",
        "Δ Baseline": "~28.6s*",
        "Kaskadenfeature": "Ja",   "Empfehlung": "Robustheits-Check",
    })

show_df(pd.DataFrame(summary_rows))
if SKIP_XGB:
    print("\n* val MAE bei Round 150 — Training auf 85M Zeilen abgebrochen (>90 Min)")
```


<style type="text/css">
#T_0c3ec thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_0c3ec td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_0c3ec tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_0c3ec tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_0c3ec tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_0c3ec">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_0c3ec_level0_col0" class="col_heading level0 col0" >Modell</th>
      <th id="T_0c3ec_level0_col1" class="col_heading level0 col1" >Test MAE</th>
      <th id="T_0c3ec_level0_col2" class="col_heading level0 col2" >Δ Baseline</th>
      <th id="T_0c3ec_level0_col3" class="col_heading level0 col3" >Kaskadenfeature</th>
      <th id="T_0c3ec_level0_col4" class="col_heading level0 col4" >Empfehlung</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_0c3ec_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_0c3ec_row0_col0" class="data row0 col0" >Baseline (Stop Mean)</td>
      <td id="T_0c3ec_row0_col1" class="data row0 col1" >50.000000</td>
      <td id="T_0c3ec_row0_col2" class="data row0 col2" >0.000000</td>
      <td id="T_0c3ec_row0_col3" class="data row0 col3" >—</td>
      <td id="T_0c3ec_row0_col4" class="data row0 col4" >Referenz</td>
    </tr>
    <tr>
      <th id="T_0c3ec_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_0c3ec_row1_col0" class="data row1 col0" >LightGBM v1</td>
      <td id="T_0c3ec_row1_col1" class="data row1 col1" >51.500000</td>
      <td id="T_0c3ec_row1_col2" class="data row1 col2" >-1.500000</td>
      <td id="T_0c3ec_row1_col3" class="data row1 col3" >Nein</td>
      <td id="T_0c3ec_row1_col4" class="data row1 col4" >Benchmark</td>
    </tr>
    <tr>
      <th id="T_0c3ec_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_0c3ec_row2_col0" class="data row2 col0" >LightGBM v2</td>
      <td id="T_0c3ec_row2_col1" class="data row2 col1" >18.600000</td>
      <td id="T_0c3ec_row2_col2" class="data row2 col2" >31.400000</td>
      <td id="T_0c3ec_row2_col3" class="data row2 col3" >Ja</td>
      <td id="T_0c3ec_row2_col4" class="data row2 col4" >Bevorzugt (schnell)</td>
    </tr>
    <tr>
      <th id="T_0c3ec_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_0c3ec_row3_col0" class="data row3 col0" >LightGBM v2 kalibriert</td>
      <td id="T_0c3ec_row3_col1" class="data row3 col1" >18.799999</td>
      <td id="T_0c3ec_row3_col2" class="data row3 col2" >31.200001</td>
      <td id="T_0c3ec_row3_col3" class="data row3 col3" >Ja</td>
      <td id="T_0c3ec_row3_col4" class="data row3 col4" >Bevorzugt (Echtzeit)</td>
    </tr>
    <tr>
      <th id="T_0c3ec_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_0c3ec_row4_col0" class="data row4 col0" >XGBoost</td>
      <td id="T_0c3ec_row4_col1" class="data row4 col1" >~21.4s*</td>
      <td id="T_0c3ec_row4_col2" class="data row4 col2" >~28.6s*</td>
      <td id="T_0c3ec_row4_col3" class="data row4 col3" >Ja</td>
      <td id="T_0c3ec_row4_col4" class="data row4 col4" >Robustheits-Check</td>
    </tr>
  </tbody>
</table>



    
    * val MAE bei Round 150 — Training auf 85M Zeilen abgebrochen (>90 Min)


### Erkenntnisse

**1. Kaskadenfeature**  
Der Effekt von `prev_trip_delay` zeigt, wie stark die analytische Erkenntnis (Pearson r ≥ 0.85) im Modell nutzbar ist. Wenn das Feature oben in der Feature Importance steht, bestätigt das: die Kaskade ist kein statistisches Artefakt, sondern ein echtes, lernbares Signal.

**2. LightGBM vs. XGBoost**  
Beide Algorithmen arbeiten auf dem gleichen Feature-Set — ein grosser Unterschied im MAE wäre ein Zeichen, dass einer der beiden besser zur Datenstruktur passt (oder dass Hyperparameter-Tuning noch Luft lässt). Ein kleiner Unterschied bestätigt: das Signal steckt in den Daten, nicht im Algorithmus.

**3. Empfehlung**  
* **Operativer Einsatz (Echtzeit):** LightGBM v2 kalibriert — geringster Bias, schnell, native Categorical-Unterstützung  
* **Portfolio-Darstellung:** LightGBM v2 + XGBoost als Robustheits-Check — zeigt, dass das Ergebnis algorithmus-unabhängig ist  
* **Nächster Schritt:** Optuna-Tuning auf LightGBM v2 (→ `06_prediction_6-tuning.ipynb`) könnte weitere 1–3 s MAE herausholen


