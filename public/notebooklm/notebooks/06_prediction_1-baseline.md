# Baseline

Wir bauen vier regelbasierte Baselines — ohne Machine Learning. Jede berechnet den **mittleren `arrival_delay`** auf einer anderen Granularitätsstufe aus den Trainingsdaten und wendet diese Vorhersage auf den Testdatensatz an.

Ziel: Den **härtesten Gegner** identifizieren, den das ML-Modell schlagen muss.

## Setup


```python
from zh_tram_flow.notebook import *
import polars as pl
import numpy as np

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("06_prediction_1-baseline")
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-05-20 13:11:22  INFO      project  06_prediction_1-baseline started


## Data

Wir verwenden `train_features.parquet` — das vollständige Feature-Set inkl. Rohspalten. Filter identisch mit `lf_clean` aus den Analysis-Notebooks.


```python
from zh_tram_flow.cleaning import apply_lf_clean

train_lf = apply_lf_clean(pl.scan_parquet(TRAIN))
test_lf  = apply_lf_clean(pl.scan_parquet(TEST))

# Collect only what we need for baseline computation
COLS_NEEDED = ["arrival_delay", "hour", "line_name", "stop_name"]

train = train_lf.select(COLS_NEEDED).collect()
test  = test_lf.select(COLS_NEEDED).collect()

print(f"Train rows: {len(train):,}")
print(f"Test rows:  {len(test):,}")
```

    Train rows: 55,484,578
    Test rows:  29,941,876


## Helpers


```python
def mae(actual: pl.Series, predicted: pl.Series) -> float:
    """Mean Absolute Error in seconds."""
    return (actual - predicted).abs().mean()


def rmse(actual: pl.Series, predicted: pl.Series) -> float:
    """Root Mean Squared Error in seconds."""
    return ((actual - predicted) ** 2).mean() ** 0.5


def otp_accuracy(actual: pl.Series, predicted: pl.Series, threshold: int = 60) -> float:
    """Share of predictions within ±threshold seconds of actual delay."""
    return ((actual - predicted).abs() <= threshold).mean()
```

## Baseline 1 — Grand Mean

Einfachste Baseline: Wir sagen für jede Fahrt **denselben Wert** vorher — den mittleren `arrival_delay` über alle Trainingsdaten.


```python
grand_mean = train["arrival_delay"].mean()
print(f"Grand mean delay: {grand_mean:.1f}s")

pred_grand = pl.Series("pred", [grand_mean] * len(test))

b1_mae  = mae(test["arrival_delay"], pred_grand)
b1_rmse = rmse(test["arrival_delay"], pred_grand)
b1_otp  = otp_accuracy(test["arrival_delay"], pred_grand)

print(f"MAE:  {b1_mae:.1f}s")
print(f"RMSE: {b1_rmse:.1f}s")
print(f"OTP accuracy (±60s): {b1_otp:.1%}")
```

    Grand mean delay: 58.0s
    MAE:  50.6s
    RMSE: 78.1s
    OTP accuracy (±60s): 71.3%


## Baseline 2 — Hour Mean

Wir sagen den mittleren Delay **pro Stunde** vorher. Berücksichtigt Rush-Hour-Muster.


```python
hour_means = (
    train
    .group_by("hour")
    .agg(pl.col("arrival_delay").mean().alias("pred_hour_mean"))
)

test_b2 = test.join(hour_means, on="hour", how="left")
# Fallback for unseen hours (shouldn't happen, but safe)
test_b2 = test_b2.with_columns(
    pl.col("pred_hour_mean").fill_null(grand_mean)
)

b2_mae  = mae(test_b2["arrival_delay"], test_b2["pred_hour_mean"])
b2_rmse = rmse(test_b2["arrival_delay"], test_b2["pred_hour_mean"])
b2_otp  = otp_accuracy(test_b2["arrival_delay"], test_b2["pred_hour_mean"])

print(f"MAE:  {b2_mae:.1f}s")
print(f"RMSE: {b2_rmse:.1f}s")
print(f"OTP accuracy (±60s): {b2_otp:.1%}")
```

    MAE:  50.5s
    RMSE: 77.8s
    OTP accuracy (±60s): 71.4%


## Baseline 3 — Line Mean

Wir sagen den mittleren Delay **pro Linie** vorher. Berücksichtigt linienspezifische Charakteristiken.


```python
line_means = (
    train
    .group_by("line_name")
    .agg(pl.col("arrival_delay").mean().alias("pred_line_mean"))
)

test_b3 = test.join(line_means, on="line_name", how="left")
test_b3 = test_b3.with_columns(
    pl.col("pred_line_mean").fill_null(grand_mean)
)

b3_mae  = mae(test_b3["arrival_delay"], test_b3["pred_line_mean"])
b3_rmse = rmse(test_b3["arrival_delay"], test_b3["pred_line_mean"])
b3_otp  = otp_accuracy(test_b3["arrival_delay"], test_b3["pred_line_mean"])

print(f"MAE:  {b3_mae:.1f}s")
print(f"RMSE: {b3_rmse:.1f}s")
print(f"OTP accuracy (±60s): {b3_otp:.1%}")
```

    MAE:  50.4s
    RMSE: 77.8s
    OTP accuracy (±60s): 71.5%


## Baseline 4 — Stop Mean

Die härteste Baseline: Wir sagen den mittleren Delay **pro Haltestelle** vorher. Haltestellen haben sehr unterschiedliche strukturelle Delay-Profile — dieser Ansatz kommt dem ML-Modell am nächsten.


```python
stop_means = (
    train
    .group_by("stop_name")
    .agg(pl.col("arrival_delay").mean().alias("pred_stop_mean"))
)

test_b4 = test.join(stop_means, on="stop_name", how="left")
test_b4 = test_b4.with_columns(
    pl.col("pred_stop_mean").fill_null(grand_mean)
)

b4_mae  = mae(test_b4["arrival_delay"], test_b4["pred_stop_mean"])
b4_rmse = rmse(test_b4["arrival_delay"], test_b4["pred_stop_mean"])
b4_otp  = otp_accuracy(test_b4["arrival_delay"], test_b4["pred_stop_mean"])

print(f"MAE:  {b4_mae:.1f}s")
print(f"RMSE: {b4_rmse:.1f}s")
print(f"OTP accuracy (±60s): {b4_otp:.1%}")
```

    MAE:  50.0s
    RMSE: 77.4s
    OTP accuracy (±60s): 71.9%


## Ergebnis — Baseline Vergleich


```python
results = pl.DataFrame({
    "Baseline":     ["Grand Mean", "Hour Mean", "Line Mean", "Stop Mean"],
    "Granularität": ["—",          "Stunde",    "Linie",     "Haltestelle"],
    "MAE (s)":      [round(b1_mae, 1), round(b2_mae, 1), round(b3_mae, 1), round(b4_mae, 1)],
    "RMSE (s)":     [round(b1_rmse, 1), round(b2_rmse, 1), round(b3_rmse, 1), round(b4_rmse, 1)],
    "OTP ±60s":     [
        f"{b1_otp:.1%}",
        f"{b2_otp:.1%}",
        f"{b3_otp:.1%}",
        f"{b4_otp:.1%}",
    ],
})

show_df(results.to_pandas())
```


<style type="text/css">
#T_e17ba thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_e17ba td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_e17ba tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_e17ba tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_e17ba tr:hover td {
  background-color: #eef3f8;
}
#T_e17ba_row0_col0, #T_e17ba_row0_col1, #T_e17ba_row0_col4, #T_e17ba_row1_col0, #T_e17ba_row1_col1, #T_e17ba_row1_col4, #T_e17ba_row2_col0, #T_e17ba_row2_col1, #T_e17ba_row2_col4, #T_e17ba_row3_col0, #T_e17ba_row3_col1, #T_e17ba_row3_col4 {
  text-align: left;
}
#T_e17ba_row0_col2, #T_e17ba_row0_col3, #T_e17ba_row1_col2, #T_e17ba_row1_col3, #T_e17ba_row2_col2, #T_e17ba_row2_col3, #T_e17ba_row3_col2, #T_e17ba_row3_col3 {
  text-align: right;
}
</style>
<table id="T_e17ba">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_e17ba_level0_col0" class="col_heading level0 col0" >Baseline</th>
      <th id="T_e17ba_level0_col1" class="col_heading level0 col1" >Granularität</th>
      <th id="T_e17ba_level0_col2" class="col_heading level0 col2" >MAE (s)</th>
      <th id="T_e17ba_level0_col3" class="col_heading level0 col3" >RMSE (s)</th>
      <th id="T_e17ba_level0_col4" class="col_heading level0 col4" >OTP ±60s</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_e17ba_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_e17ba_row0_col0" class="data row0 col0" >Grand Mean</td>
      <td id="T_e17ba_row0_col1" class="data row0 col1" >—</td>
      <td id="T_e17ba_row0_col2" class="data row0 col2" >50.60</td>
      <td id="T_e17ba_row0_col3" class="data row0 col3" >78.10</td>
      <td id="T_e17ba_row0_col4" class="data row0 col4" >71.3%</td>
    </tr>
    <tr>
      <th id="T_e17ba_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_e17ba_row1_col0" class="data row1 col0" >Hour Mean</td>
      <td id="T_e17ba_row1_col1" class="data row1 col1" >Stunde</td>
      <td id="T_e17ba_row1_col2" class="data row1 col2" >50.50</td>
      <td id="T_e17ba_row1_col3" class="data row1 col3" >77.80</td>
      <td id="T_e17ba_row1_col4" class="data row1 col4" >71.4%</td>
    </tr>
    <tr>
      <th id="T_e17ba_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_e17ba_row2_col0" class="data row2 col0" >Line Mean</td>
      <td id="T_e17ba_row2_col1" class="data row2 col1" >Linie</td>
      <td id="T_e17ba_row2_col2" class="data row2 col2" >50.40</td>
      <td id="T_e17ba_row2_col3" class="data row2 col3" >77.80</td>
      <td id="T_e17ba_row2_col4" class="data row2 col4" >71.5%</td>
    </tr>
    <tr>
      <th id="T_e17ba_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_e17ba_row3_col0" class="data row3 col0" >Stop Mean</td>
      <td id="T_e17ba_row3_col1" class="data row3 col1" >Haltestelle</td>
      <td id="T_e17ba_row3_col2" class="data row3 col2" >50.00</td>
      <td id="T_e17ba_row3_col3" class="data row3 col3" >77.40</td>
      <td id="T_e17ba_row3_col4" class="data row3 col4" >71.9%</td>
    </tr>
  </tbody>
</table>



## Benchmark

Die **Stop Mean Baseline** ist unser Benchmark — sie ist die härteste regelbasierte Linie, die das LightGBM-Modell schlagen muss.

Das ML-Modell bringt gegenüber dieser Baseline dann Mehrwert, wenn es zusätzlich:
- Tageszeit und Wochentag berücksichtigt (Rush-Hour-Effekte)
- Wetterbedingungen einbezieht (Regen, Schnee)
- Event-Cluster erkennt
- Kombinationen dieser Faktoren lernt (Interaktionen)

**Ziel für das Modell:** MAE unter dem Stop-Mean-Wert.


```python
print(f"Benchmark (Stop Mean MAE): {b4_mae:.1f}s")
print(f"Das LightGBM-Modell muss MAE < {b4_mae:.1f}s erreichen, um die Baseline zu schlagen.")
```

    Benchmark (Stop Mean MAE): 50.0s
    Das LightGBM-Modell muss MAE < 50.0s erreichen, um die Baseline zu schlagen.

