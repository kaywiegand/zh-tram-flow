# Evaluation

Wir laden die fertig berechneten Test-Predictions aus `06_prediction_2-model.ipynb` und analysieren wo das Modell gut und wo es schwächer ist.

**Benchmark:** Stop Mean Baseline MAE = 50.0s &nbsp;|&nbsp; **LightGBM v1 Test MAE = 45.7s** (−4.3s gegenüber Baseline ✅)

## Setup


```python
from zh_tram_flow.notebook import *
import polars as pl
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("06_prediction_3-evaluation")

```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-05-27 09:09:09  INFO      project  06_prediction_3-evaluation started


## Load Model & Predictions


```python
pred_path = Path(str(TEST)).parent / "test_predictions.parquet"
pred = pl.read_parquet(pred_path)

print(f"Predictions geladen: {len(pred):,} Zeilen")
print(f"Spalten: {pred.columns}")
pred.head(5)
```

    Predictions geladen: 29,941,876 Zeilen
    Spalten: ['actual', 'predicted', 'line_name', 'stop_name', 'hour', 'month', 'has_rain', 'has_snow', 'has_event']





<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (5, 9)</small><table border="1" class="dataframe"><thead><tr><th>actual</th><th>predicted</th><th>line_name</th><th>stop_name</th><th>hour</th><th>month</th><th>has_rain</th><th>has_snow</th><th>has_event</th></tr><tr><td>f32</td><td>f32</td><td>cat</td><td>cat</td><td>i8</td><td>i8</td><td>bool</td><td>bool</td><td>bool</td></tr></thead><tbody><tr><td>99.0</td><td>0.101883</td><td>&quot;2&quot;</td><td>&quot;Zürich, Kreuzstrasse&quot;</td><td>5</td><td>1</td><td>false</td><td>false</td><td>true</td></tr><tr><td>124.0</td><td>1.643478</td><td>&quot;2&quot;</td><td>&quot;Zürich, Feldeggstrasse&quot;</td><td>5</td><td>1</td><td>false</td><td>false</td><td>true</td></tr><tr><td>16.0</td><td>1.643478</td><td>&quot;2&quot;</td><td>&quot;Zürich, Feldeggstrasse&quot;</td><td>5</td><td>1</td><td>false</td><td>false</td><td>true</td></tr><tr><td>16.0</td><td>0.101883</td><td>&quot;2&quot;</td><td>&quot;Zürich, Kreuzstrasse&quot;</td><td>5</td><td>1</td><td>false</td><td>false</td><td>true</td></tr><tr><td>4.0</td><td>24.418571</td><td>&quot;2&quot;</td><td>&quot;Zürich, Zypressenstrasse&quot;</td><td>5</td><td>1</td><td>false</td><td>false</td><td>true</td></tr></tbody></table></div>



## Metriken — Modell vs. Baseline


```python
def mae(df, actual='actual', predicted='predicted'):
    return (df[actual] - df[predicted]).abs().mean()

def rmse(df, actual='actual', predicted='predicted'):
    return ((df[actual] - df[predicted]) ** 2).mean() ** 0.5

def otp(df, actual='actual', predicted='predicted', threshold=60):
    return ((df[actual] - df[predicted]).abs() <= threshold).mean()

# Modell-Metriken auf Test-Set
model_mae  = mae(pred)
model_rmse = rmse(pred)
model_otp  = otp(pred)

# Baseline-Werte aus 06_prediction_1-baseline.ipynb (Stop Mean)
BASELINE_MAE  = 50.0   # Stop Mean MAE
BASELINE_RMSE = 77.4   # Stop Mean RMSE
BASELINE_OTP  = 0.719  # Stop Mean OTP ±60s

results = pl.DataFrame({
    "":          ["Stop Mean Baseline", "LightGBM v1", "Gewinn"],
    "MAE (s)":   [BASELINE_MAE, round(model_mae, 1), round(BASELINE_MAE - model_mae, 1)],
    "RMSE (s)":  [BASELINE_RMSE, round(model_rmse, 1), round(BASELINE_RMSE - model_rmse, 1)],
    "OTP ±60s":  [f"{BASELINE_OTP:.1%}", f"{model_otp:.1%}", f"+{(model_otp - BASELINE_OTP):.1%}"],
})

show_df(results.to_pandas())
```


<style type="text/css">
#T_e6192 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_e6192 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_e6192 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_e6192 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_e6192 tr:hover td {
  background-color: #eef3f8;
}
#T_e6192_row0_col0, #T_e6192_row0_col3, #T_e6192_row1_col0, #T_e6192_row1_col3, #T_e6192_row2_col0, #T_e6192_row2_col3 {
  text-align: left;
}
#T_e6192_row0_col1, #T_e6192_row0_col2, #T_e6192_row1_col1, #T_e6192_row1_col2, #T_e6192_row2_col1, #T_e6192_row2_col2 {
  text-align: right;
}
</style>
<table id="T_e6192">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_e6192_level0_col0" class="col_heading level0 col0" ></th>
      <th id="T_e6192_level0_col1" class="col_heading level0 col1" >MAE (s)</th>
      <th id="T_e6192_level0_col2" class="col_heading level0 col2" >RMSE (s)</th>
      <th id="T_e6192_level0_col3" class="col_heading level0 col3" >OTP ±60s</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_e6192_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_e6192_row0_col0" class="data row0 col0" >Stop Mean Baseline</td>
      <td id="T_e6192_row0_col1" class="data row0 col1" >50.00</td>
      <td id="T_e6192_row0_col2" class="data row0 col2" >77.40</td>
      <td id="T_e6192_row0_col3" class="data row0 col3" >71.9%</td>
    </tr>
    <tr>
      <th id="T_e6192_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_e6192_row1_col0" class="data row1 col0" >LightGBM v1</td>
      <td id="T_e6192_row1_col1" class="data row1 col1" >45.70</td>
      <td id="T_e6192_row1_col2" class="data row1 col2" >75.60</td>
      <td id="T_e6192_row1_col3" class="data row1 col3" >77.5%</td>
    </tr>
    <tr>
      <th id="T_e6192_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_e6192_row2_col0" class="data row2 col0" >Gewinn</td>
      <td id="T_e6192_row2_col1" class="data row2 col1" >4.30</td>
      <td id="T_e6192_row2_col2" class="data row2 col2" >1.80</td>
      <td id="T_e6192_row2_col3" class="data row2 col3" >+5.6%</td>
    </tr>
  </tbody>
</table>



## Error Analysis

Wo liegt das Modell daneben? Wir schlüsseln den MAE auf nach:
- **Tageszeit** — Rush-Hour vs. Nacht
- **Linie** — welche Linien sind schwer vorherzusagen?
- **Wetter** — Schnee / Regen / normal
- **Monat** — saisonale Schwächen


```python
# --- MAE nach Stunde ---
mae_hour = (
    pred
    .with_columns((pl.col('actual') - pl.col('predicted')).abs().alias('abs_err'))
    .group_by('hour')
    .agg(pl.col('abs_err').mean().alias('MAE'), pl.len().alias('n'))
    .sort('hour')
)

fig = px.bar(mae_hour.to_pandas(), x='hour', y='MAE',
             title='MAE nach Tageszeit',
             labels={'hour': 'Stunde', 'MAE': 'MAE (s)'})
fig.add_hline(y=model_mae, line_dash='dash', line_color='gray',
              annotation_text=f'Gesamt MAE {model_mae:.1f}s')
fig.show()
show_df(mae_hour.sort('MAE', descending=True).to_pandas())
```




<style type="text/css">
#T_1241e thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_1241e td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_1241e tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_1241e tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_1241e tr:hover td {
  background-color: #eef3f8;
}
#T_1241e_row0_col0, #T_1241e_row0_col1, #T_1241e_row0_col2, #T_1241e_row1_col0, #T_1241e_row1_col1, #T_1241e_row1_col2, #T_1241e_row2_col0, #T_1241e_row2_col1, #T_1241e_row2_col2, #T_1241e_row3_col0, #T_1241e_row3_col1, #T_1241e_row3_col2, #T_1241e_row4_col0, #T_1241e_row4_col1, #T_1241e_row4_col2, #T_1241e_row5_col0, #T_1241e_row5_col1, #T_1241e_row5_col2, #T_1241e_row6_col0, #T_1241e_row6_col1, #T_1241e_row6_col2, #T_1241e_row7_col0, #T_1241e_row7_col1, #T_1241e_row7_col2, #T_1241e_row8_col0, #T_1241e_row8_col1, #T_1241e_row8_col2, #T_1241e_row9_col0, #T_1241e_row9_col1, #T_1241e_row9_col2, #T_1241e_row10_col0, #T_1241e_row10_col1, #T_1241e_row10_col2, #T_1241e_row11_col0, #T_1241e_row11_col1, #T_1241e_row11_col2, #T_1241e_row12_col0, #T_1241e_row12_col1, #T_1241e_row12_col2, #T_1241e_row13_col0, #T_1241e_row13_col1, #T_1241e_row13_col2, #T_1241e_row14_col0, #T_1241e_row14_col1, #T_1241e_row14_col2, #T_1241e_row15_col0, #T_1241e_row15_col1, #T_1241e_row15_col2, #T_1241e_row16_col0, #T_1241e_row16_col1, #T_1241e_row16_col2, #T_1241e_row17_col0, #T_1241e_row17_col1, #T_1241e_row17_col2, #T_1241e_row18_col0, #T_1241e_row18_col1, #T_1241e_row18_col2, #T_1241e_row19_col0, #T_1241e_row19_col1, #T_1241e_row19_col2, #T_1241e_row20_col0, #T_1241e_row20_col1, #T_1241e_row20_col2, #T_1241e_row21_col0, #T_1241e_row21_col1, #T_1241e_row21_col2, #T_1241e_row22_col0, #T_1241e_row22_col1, #T_1241e_row22_col2 {
  text-align: right;
}
</style>
<table id="T_1241e">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_1241e_level0_col0" class="col_heading level0 col0" >hour</th>
      <th id="T_1241e_level0_col1" class="col_heading level0 col1" >MAE</th>
      <th id="T_1241e_level0_col2" class="col_heading level0 col2" >n</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_1241e_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_1241e_row0_col0" class="data row0 col0" >2</td>
      <td id="T_1241e_row0_col1" class="data row0 col1" >82.36</td>
      <td id="T_1241e_row0_col2" class="data row0 col2" >2969</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_1241e_row1_col0" class="data row1 col0" >1</td>
      <td id="T_1241e_row1_col1" class="data row1 col1" >58.42</td>
      <td id="T_1241e_row1_col2" class="data row1 col2" >43943</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_1241e_row2_col0" class="data row2 col0" >17</td>
      <td id="T_1241e_row2_col1" class="data row2 col1" >54.49</td>
      <td id="T_1241e_row2_col2" class="data row2 col2" >1711703</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_1241e_row3_col0" class="data row3 col0" >16</td>
      <td id="T_1241e_row3_col1" class="data row3 col1" >53.28</td>
      <td id="T_1241e_row3_col2" class="data row3 col2" >1709312</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_1241e_row4_col0" class="data row4 col0" >18</td>
      <td id="T_1241e_row4_col1" class="data row4 col1" >52.79</td>
      <td id="T_1241e_row4_col2" class="data row4 col2" >1694478</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_1241e_row5_col0" class="data row5 col0" >20</td>
      <td id="T_1241e_row5_col1" class="data row5 col1" >49.63</td>
      <td id="T_1241e_row5_col2" class="data row5 col2" >1537534</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_1241e_row6_col0" class="data row6 col0" >15</td>
      <td id="T_1241e_row6_col1" class="data row6 col1" >47.69</td>
      <td id="T_1241e_row6_col2" class="data row6 col2" >1684937</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_1241e_row7_col0" class="data row7 col0" >21</td>
      <td id="T_1241e_row7_col1" class="data row7 col1" >47.36</td>
      <td id="T_1241e_row7_col2" class="data row7 col2" >1260073</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_1241e_row8_col0" class="data row8 col0" >19</td>
      <td id="T_1241e_row8_col1" class="data row8 col1" >47.26</td>
      <td id="T_1241e_row8_col2" class="data row8 col2" >1660664</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_1241e_row9_col0" class="data row9 col0" >22</td>
      <td id="T_1241e_row9_col1" class="data row9 col1" >46.56</td>
      <td id="T_1241e_row9_col2" class="data row9 col2" >1234761</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_1241e_row10_col0" class="data row10 col0" >8</td>
      <td id="T_1241e_row10_col1" class="data row10 col1" >46.50</td>
      <td id="T_1241e_row10_col2" class="data row10 col2" >1608924</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_1241e_row11_col0" class="data row11 col0" >14</td>
      <td id="T_1241e_row11_col1" class="data row11 col1" >45.82</td>
      <td id="T_1241e_row11_col2" class="data row11 col2" >1678027</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_1241e_row12_col0" class="data row12 col0" >23</td>
      <td id="T_1241e_row12_col1" class="data row12 col1" >44.30</td>
      <td id="T_1241e_row12_col2" class="data row12 col2" >1025491</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_1241e_row13_col0" class="data row13 col0" >9</td>
      <td id="T_1241e_row13_col1" class="data row13 col1" >43.66</td>
      <td id="T_1241e_row13_col2" class="data row13 col2" >1584551</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_1241e_row14_col0" class="data row14 col0" >13</td>
      <td id="T_1241e_row14_col1" class="data row14 col1" >43.65</td>
      <td id="T_1241e_row14_col2" class="data row14 col2" >1685103</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_1241e_row15_col0" class="data row15 col0" >10</td>
      <td id="T_1241e_row15_col1" class="data row15 col1" >42.76</td>
      <td id="T_1241e_row15_col2" class="data row15 col2" >1681609</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_1241e_row16_col0" class="data row16 col0" >7</td>
      <td id="T_1241e_row16_col1" class="data row16 col1" >42.65</td>
      <td id="T_1241e_row16_col2" class="data row16 col2" >1577620</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_1241e_row17_col0" class="data row17 col0" >12</td>
      <td id="T_1241e_row17_col1" class="data row17 col1" >42.32</td>
      <td id="T_1241e_row17_col2" class="data row17 col2" >1692468</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_1241e_row18_col0" class="data row18 col0" >11</td>
      <td id="T_1241e_row18_col1" class="data row18 col1" >40.42</td>
      <td id="T_1241e_row18_col2" class="data row18 col2" >1693484</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_1241e_row19_col0" class="data row19 col0" >0</td>
      <td id="T_1241e_row19_col1" class="data row19 col1" >40.37</td>
      <td id="T_1241e_row19_col2" class="data row19 col2" >788163</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_1241e_row20_col0" class="data row20 col0" >6</td>
      <td id="T_1241e_row20_col1" class="data row20 col1" >40.04</td>
      <td id="T_1241e_row20_col2" class="data row20 col2" >1483656</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_1241e_row21_col0" class="data row21 col0" >4</td>
      <td id="T_1241e_row21_col1" class="data row21 col1" >36.87</td>
      <td id="T_1241e_row21_col2" class="data row21 col2" >37048</td>
    </tr>
    <tr>
      <th id="T_1241e_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_1241e_row22_col0" class="data row22 col0" >5</td>
      <td id="T_1241e_row22_col1" class="data row22 col1" >33.54</td>
      <td id="T_1241e_row22_col2" class="data row22 col2" >865358</td>
    </tr>
  </tbody>
</table>




```python
# --- MAE nach Linie ---
mae_line = (
    pred
    .with_columns((pl.col('actual') - pl.col('predicted')).abs().alias('abs_err'))
    .group_by('line_name')
    .agg(pl.col('abs_err').mean().alias('MAE'), pl.len().alias('n'))
    .sort('MAE', descending=True)
)

fig = px.bar(mae_line.to_pandas(), x='line_name', y='MAE',
             title='MAE nach Linie',
             labels={'line_name': 'Linie', 'MAE': 'MAE (s)'})
fig.add_hline(y=model_mae, line_dash='dash', line_color='gray',
              annotation_text=f'Gesamt MAE {model_mae:.1f}s')
fig.show()
show_df(mae_line.to_pandas())
```




<style type="text/css">
#T_b0730 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_b0730 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_b0730 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_b0730 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_b0730 tr:hover td {
  background-color: #eef3f8;
}
#T_b0730_row0_col0, #T_b0730_row1_col0, #T_b0730_row2_col0, #T_b0730_row3_col0, #T_b0730_row4_col0, #T_b0730_row5_col0, #T_b0730_row6_col0, #T_b0730_row7_col0, #T_b0730_row8_col0, #T_b0730_row9_col0, #T_b0730_row10_col0, #T_b0730_row11_col0, #T_b0730_row12_col0, #T_b0730_row13_col0, #T_b0730_row14_col0, #T_b0730_row15_col0, #T_b0730_row16_col0 {
  text-align: left;
}
#T_b0730_row0_col1, #T_b0730_row0_col2, #T_b0730_row1_col1, #T_b0730_row1_col2, #T_b0730_row2_col1, #T_b0730_row2_col2, #T_b0730_row3_col1, #T_b0730_row3_col2, #T_b0730_row4_col1, #T_b0730_row4_col2, #T_b0730_row5_col1, #T_b0730_row5_col2, #T_b0730_row6_col1, #T_b0730_row6_col2, #T_b0730_row7_col1, #T_b0730_row7_col2, #T_b0730_row8_col1, #T_b0730_row8_col2, #T_b0730_row9_col1, #T_b0730_row9_col2, #T_b0730_row10_col1, #T_b0730_row10_col2, #T_b0730_row11_col1, #T_b0730_row11_col2, #T_b0730_row12_col1, #T_b0730_row12_col2, #T_b0730_row13_col1, #T_b0730_row13_col2, #T_b0730_row14_col1, #T_b0730_row14_col2, #T_b0730_row15_col1, #T_b0730_row15_col2, #T_b0730_row16_col1, #T_b0730_row16_col2 {
  text-align: right;
}
</style>
<table id="T_b0730">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_b0730_level0_col0" class="col_heading level0 col0" >line_name</th>
      <th id="T_b0730_level0_col1" class="col_heading level0 col1" >MAE</th>
      <th id="T_b0730_level0_col2" class="col_heading level0 col2" >n</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_b0730_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_b0730_row0_col0" class="data row0 col0" >11</td>
      <td id="T_b0730_row0_col1" class="data row0 col1" >52.33</td>
      <td id="T_b0730_row0_col2" class="data row0 col2" >2834343</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_b0730_row1_col0" class="data row1 col0" >8</td>
      <td id="T_b0730_row1_col1" class="data row1 col1" >51.08</td>
      <td id="T_b0730_row1_col2" class="data row1 col2" >2007818</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_b0730_row2_col0" class="data row2 col0" >15</td>
      <td id="T_b0730_row2_col1" class="data row2 col1" >50.50</td>
      <td id="T_b0730_row2_col2" class="data row2 col2" >1019990</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_b0730_row3_col0" class="data row3 col0" >10</td>
      <td id="T_b0730_row3_col1" class="data row3 col1" >49.89</td>
      <td id="T_b0730_row3_col2" class="data row3 col2" >2266026</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_b0730_row4_col0" class="data row4 col0" >2</td>
      <td id="T_b0730_row4_col1" class="data row4 col1" >46.72</td>
      <td id="T_b0730_row4_col2" class="data row4 col2" >2689497</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_b0730_row5_col0" class="data row5 col0" >4</td>
      <td id="T_b0730_row5_col1" class="data row5 col1" >45.99</td>
      <td id="T_b0730_row5_col2" class="data row5 col2" >2256185</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_b0730_row6_col0" class="data row6 col0" >9</td>
      <td id="T_b0730_row6_col1" class="data row6 col1" >45.81</td>
      <td id="T_b0730_row6_col2" class="data row6 col2" >2839792</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_b0730_row7_col0" class="data row7 col0" >5</td>
      <td id="T_b0730_row7_col1" class="data row7 col1" >45.05</td>
      <td id="T_b0730_row7_col2" class="data row7 col2" >954246</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_b0730_row8_col0" class="data row8 col0" >13</td>
      <td id="T_b0730_row8_col1" class="data row8 col1" >44.87</td>
      <td id="T_b0730_row8_col2" class="data row8 col2" >2647723</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_b0730_row9_col0" class="data row9 col0" >14</td>
      <td id="T_b0730_row9_col1" class="data row9 col1" >44.63</td>
      <td id="T_b0730_row9_col2" class="data row9 col2" >2191741</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_b0730_row10_col0" class="data row10 col0" >7</td>
      <td id="T_b0730_row10_col1" class="data row10 col1" >44.31</td>
      <td id="T_b0730_row10_col2" class="data row10 col2" >2683825</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_b0730_row11_col0" class="data row11 col0" >50</td>
      <td id="T_b0730_row11_col1" class="data row11 col1" >42.74</td>
      <td id="T_b0730_row11_col2" class="data row11 col2" >142104</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_b0730_row12_col0" class="data row12 col0" >3</td>
      <td id="T_b0730_row12_col1" class="data row12 col1" >42.12</td>
      <td id="T_b0730_row12_col2" class="data row12 col2" >1685982</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_b0730_row13_col0" class="data row13 col0" >51</td>
      <td id="T_b0730_row13_col1" class="data row13 col1" >39.55</td>
      <td id="T_b0730_row13_col2" class="data row13 col2" >115162</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_b0730_row14_col0" class="data row14 col0" >17</td>
      <td id="T_b0730_row14_col1" class="data row14 col1" >39.26</td>
      <td id="T_b0730_row14_col2" class="data row14 col2" >1624041</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_b0730_row15_col0" class="data row15 col0" >6</td>
      <td id="T_b0730_row15_col1" class="data row15 col1" >36.58</td>
      <td id="T_b0730_row15_col2" class="data row15 col2" >1145448</td>
    </tr>
    <tr>
      <th id="T_b0730_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_b0730_row16_col0" class="data row16 col0" >12</td>
      <td id="T_b0730_row16_col1" class="data row16 col1" >34.52</td>
      <td id="T_b0730_row16_col2" class="data row16 col2" >837953</td>
    </tr>
  </tbody>
</table>




```python
# --- MAE nach Wetter ---
mae_weather = (
    pred
    .with_columns([
        (pl.col('actual') - pl.col('predicted')).abs().alias('abs_err'),
        pl.when(pl.col('has_snow')).then(pl.lit('Schnee'))
          .when(pl.col('has_rain')).then(pl.lit('Regen'))
          .otherwise(pl.lit('Normal')).alias('weather'),
    ])
    .group_by('weather')
    .agg(pl.col('abs_err').mean().alias('MAE'), pl.len().alias('n'))
    .sort('MAE', descending=True)
)

fig = px.bar(mae_weather.to_pandas(), x='weather', y='MAE',
             title='MAE nach Wetterbedingung',
             labels={'weather': 'Wetter', 'MAE': 'MAE (s)'})
fig.add_hline(y=model_mae, line_dash='dash', line_color='gray',
              annotation_text=f'Gesamt MAE {model_mae:.1f}s')
fig.show()
show_df(mae_weather.to_pandas())
```




<style type="text/css">
#T_25a9c thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_25a9c td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_25a9c tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_25a9c tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_25a9c tr:hover td {
  background-color: #eef3f8;
}
#T_25a9c_row0_col0, #T_25a9c_row1_col0, #T_25a9c_row2_col0 {
  text-align: left;
}
#T_25a9c_row0_col1, #T_25a9c_row0_col2, #T_25a9c_row1_col1, #T_25a9c_row1_col2, #T_25a9c_row2_col1, #T_25a9c_row2_col2 {
  text-align: right;
}
</style>
<table id="T_25a9c">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_25a9c_level0_col0" class="col_heading level0 col0" >weather</th>
      <th id="T_25a9c_level0_col1" class="col_heading level0 col1" >MAE</th>
      <th id="T_25a9c_level0_col2" class="col_heading level0 col2" >n</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_25a9c_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_25a9c_row0_col0" class="data row0 col0" >Schnee</td>
      <td id="T_25a9c_row0_col1" class="data row0 col1" >58.93</td>
      <td id="T_25a9c_row0_col2" class="data row0 col2" >39920</td>
    </tr>
    <tr>
      <th id="T_25a9c_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_25a9c_row1_col0" class="data row1 col0" >Regen</td>
      <td id="T_25a9c_row1_col1" class="data row1 col1" >49.48</td>
      <td id="T_25a9c_row1_col2" class="data row1 col2" >2699615</td>
    </tr>
    <tr>
      <th id="T_25a9c_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_25a9c_row2_col0" class="data row2 col0" >Normal</td>
      <td id="T_25a9c_row2_col1" class="data row2 col1" >45.35</td>
      <td id="T_25a9c_row2_col2" class="data row2 col2" >27202341</td>
    </tr>
  </tbody>
</table>




```python
# --- MAE nach Monat ---
mae_month = (
    pred
    .with_columns((pl.col('actual') - pl.col('predicted')).abs().alias('abs_err'))
    .group_by('month')
    .agg(pl.col('abs_err').mean().alias('MAE'), pl.len().alias('n'))
    .sort('month')
)

fig = px.bar(mae_month.to_pandas(), x='month', y='MAE',
             title='MAE nach Monat (Test-Jahr 2025)',
             labels={'month': 'Monat', 'MAE': 'MAE (s)'})
fig.add_hline(y=model_mae, line_dash='dash', line_color='gray',
              annotation_text=f'Gesamt MAE {model_mae:.1f}s')
fig.show()
show_df(mae_month.to_pandas())
```




<style type="text/css">
#T_49d04 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_49d04 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_49d04 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_49d04 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_49d04 tr:hover td {
  background-color: #eef3f8;
}
#T_49d04_row0_col0, #T_49d04_row0_col1, #T_49d04_row0_col2, #T_49d04_row1_col0, #T_49d04_row1_col1, #T_49d04_row1_col2, #T_49d04_row2_col0, #T_49d04_row2_col1, #T_49d04_row2_col2, #T_49d04_row3_col0, #T_49d04_row3_col1, #T_49d04_row3_col2, #T_49d04_row4_col0, #T_49d04_row4_col1, #T_49d04_row4_col2, #T_49d04_row5_col0, #T_49d04_row5_col1, #T_49d04_row5_col2, #T_49d04_row6_col0, #T_49d04_row6_col1, #T_49d04_row6_col2, #T_49d04_row7_col0, #T_49d04_row7_col1, #T_49d04_row7_col2, #T_49d04_row8_col0, #T_49d04_row8_col1, #T_49d04_row8_col2, #T_49d04_row9_col0, #T_49d04_row9_col1, #T_49d04_row9_col2, #T_49d04_row10_col0, #T_49d04_row10_col1, #T_49d04_row10_col2, #T_49d04_row11_col0, #T_49d04_row11_col1, #T_49d04_row11_col2 {
  text-align: right;
}
</style>
<table id="T_49d04">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_49d04_level0_col0" class="col_heading level0 col0" >month</th>
      <th id="T_49d04_level0_col1" class="col_heading level0 col1" >MAE</th>
      <th id="T_49d04_level0_col2" class="col_heading level0 col2" >n</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_49d04_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_49d04_row0_col0" class="data row0 col0" >1</td>
      <td id="T_49d04_row0_col1" class="data row0 col1" >41.81</td>
      <td id="T_49d04_row0_col2" class="data row0 col2" >2596478</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_49d04_row1_col0" class="data row1 col0" >2</td>
      <td id="T_49d04_row1_col1" class="data row1 col1" >41.25</td>
      <td id="T_49d04_row1_col2" class="data row1 col2" >2310617</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_49d04_row2_col0" class="data row2 col0" >3</td>
      <td id="T_49d04_row2_col1" class="data row2 col1" >44.38</td>
      <td id="T_49d04_row2_col2" class="data row2 col2" >2559422</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_49d04_row3_col0" class="data row3 col0" >4</td>
      <td id="T_49d04_row3_col1" class="data row3 col1" >45.38</td>
      <td id="T_49d04_row3_col2" class="data row3 col2" >2323347</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_49d04_row4_col0" class="data row4 col0" >5</td>
      <td id="T_49d04_row4_col1" class="data row4 col1" >48.20</td>
      <td id="T_49d04_row4_col2" class="data row4 col2" >2540176</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_49d04_row5_col0" class="data row5 col0" >6</td>
      <td id="T_49d04_row5_col1" class="data row5 col1" >49.73</td>
      <td id="T_49d04_row5_col2" class="data row5 col2" >2400665</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_49d04_row6_col0" class="data row6 col0" >7</td>
      <td id="T_49d04_row6_col1" class="data row6 col1" >49.48</td>
      <td id="T_49d04_row6_col2" class="data row6 col2" >2485490</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_49d04_row7_col0" class="data row7 col0" >8</td>
      <td id="T_49d04_row7_col1" class="data row7 col1" >46.29</td>
      <td id="T_49d04_row7_col2" class="data row7 col2" >2468589</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_49d04_row8_col0" class="data row8 col0" >9</td>
      <td id="T_49d04_row8_col1" class="data row8 col1" >47.15</td>
      <td id="T_49d04_row8_col2" class="data row8 col2" >2816622</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_49d04_row9_col0" class="data row9 col0" >10</td>
      <td id="T_49d04_row9_col1" class="data row9 col1" >49.59</td>
      <td id="T_49d04_row9_col2" class="data row9 col2" >2516937</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_49d04_row10_col0" class="data row10 col0" >11</td>
      <td id="T_49d04_row10_col1" class="data row10 col1" >46.97</td>
      <td id="T_49d04_row10_col2" class="data row10 col2" >2469829</td>
    </tr>
    <tr>
      <th id="T_49d04_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_49d04_row11_col0" class="data row11 col0" >12</td>
      <td id="T_49d04_row11_col1" class="data row11 col1" >38.33</td>
      <td id="T_49d04_row11_col2" class="data row11 col2" >2453704</td>
    </tr>
  </tbody>
</table>



## Key Findings — Fehleranalyse

**Rush-Hour ist die stärkste Schwachstelle**
* 16h: 53.3s · 17h: 54.5s · 18h: 52.8s — alle deutlich über Gesamtschnitt (45.7s)
* Beste Stunden: 4–6h mit 33–40s — geringer Verkehr = geringere Varianz

**L11 und L8 schlagen die Baseline nicht**
* L11: 52.3s · L8: 51.1s · L15: 50.5s — alle über Baseline (50.0s)
* Genau die Linien durch K11/K12 — strukturell schwierigste Zonen des Netzes
* Gegenstück: L12 34.5s · L6 36.6s · L17 39.3s — größte Modell-Gewinne

**Schnee überfordert das Modell**
* MAE Schnee 58.9s vs. Normal 45.4s — Differenz +13.5s
* Nur 40k Schnee-Halte im Testjahr 2025 — zu wenig Trainings- und Testdaten für seltene Ereignisse

**Systematischer Optimismus-Bias**
* MBE +8.3s — Modell unterschätzt realen Delay durchgehend
* Besonders ausgeprägt bei Extremlagen: Rush-Hour, Schnee, Linie 11

---

## Verbesserungsmöglichkeiten

**Kurzfristig — gleicher Stack, mehr Signal**
* `prev_stop_delay` als Feature — Delay des Vorgänger-Halts in derselben Fahrt (Kaskadenindikator)
* `stop_sequence` explizit als numerisches Feature — Delay akkumuliert mit Strecke
* Baustellenkalender als binäres Feature — temporäre Streckenstörungen

**Mittelfristig — Modell-Tuning**
* Quantile Regression (`objective="quantile"`) statt MAE — reduziert Optimismus-Bias direkt
* Separate Modelle für L11 / L8 — linienspezifische Muster lernen
* Hyperparameter-Tuning mit Optuna (num_leaves, min_child_samples, learning_rate)

**Längerfristig — alternative Ansätze**
* XGBoost — robuster bei Extremwerten durch andere Baum-Regularisierung
* CatBoost — stärker bei hochkardinalen Kategorien wie `stop_name`
* Sequenzmodell (z.B. LightGBM mit Rolling Features) — explizite Zeitabhängigkeit modellieren

## Feature Importance — Was hat das Modell gelernt?

Hat das Modell dieselben Muster gelernt, die die 55 Findings der Analyse-Phase beschreiben?

Feature Importance (Gain) zeigt, wie viel jedes Feature zur Reduktion des Vorhersagefehlers beiträgt — normalisiert auf 100 %.

`stop_name` und `hour` sollten dominieren (räumlich + temporal stärkste Signale aus Analyse). `has_snow` und `is_holiday` zeigen ob der Wetter- und Event-Effekt gelernt wurde.


```python
import lightgbm as lgb
from wgnd.core.theme import mpl_style
from wgnd.core.config import cfg
import matplotlib.pyplot as plt

model_path = Path(str(TEST)).parent.parent / "models" / "lgbm_v1.txt"
model = lgb.Booster(model_file=str(model_path))

# Feature Importance — Gain (wie viel erklärt jedes Feature?)
feat_imp = (
    pd.DataFrame({
        "feature":    model.feature_name(),
        "gain":       model.feature_importance(importance_type="gain"),
        "split":      model.feature_importance(importance_type="split"),
    })
    .assign(pct=lambda df: df["gain"] / df["gain"].sum() * 100)
    .sort_values("pct", ascending=False)
    .reset_index(drop=True)
)

top = feat_imp.head(20).copy()

# Farb-Kodierung: Amber = dominierend (>10%), Teal = relevant (>2%), Grau = Rest
def _color(pct):
    if pct > 10:  return cfg.COLOR_SIGNAL
    if pct > 2:   return cfg.COLOR_POSITIVE
    return cfg.ANNO_REF

colors = [_color(p) for p in top["pct"]]

style = mpl_style()
fig, ax = plt.subplots(figsize=(10, 7))

bars = ax.barh(
    top["feature"][::-1], top["pct"][::-1],
    color=colors[::-1], edgecolor="white", linewidth=0.4,
)
for bar, pct in zip(bars, top["pct"][::-1]):
    ax.text(
        bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
        f"{pct:.1f}%", va="center", fontsize=9,
        color=cfg.CHART_AXIS_TEXT,
    )

ax.set_xlabel("Importance (% Gain)", **style["label"])
ax.set_title(
    "Feature Importance — LightGBM v1 (Gain)\n"
    "Amber > 10% · Teal > 2% · Grau < 2%",
    **style["title"],
)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
ax.tick_params(colors=cfg.CHART_AXIS_TEXT, labelsize=9)
ax.set_xlim(0, top["pct"].max() * 1.15)
plt.tight_layout()
plt.show()

show_df(
    feat_imp.head(33)
    [["feature", "pct", "split"]]
    .rename(columns={"feature": "Feature", "pct": "Gain (%)", "split": "Splits"})
    .round({"Gain (%)": 2})
    .reset_index(drop=True)
)
```


    
![png](06_prediction_3-evaluation_files/06_prediction_3-evaluation_16_0.png)
    



<style type="text/css">
#T_868d7 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_868d7 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_868d7 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_868d7 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_868d7 tr:hover td {
  background-color: #eef3f8;
}
#T_868d7_row0_col0, #T_868d7_row1_col0, #T_868d7_row2_col0, #T_868d7_row3_col0, #T_868d7_row4_col0, #T_868d7_row5_col0, #T_868d7_row6_col0, #T_868d7_row7_col0, #T_868d7_row8_col0, #T_868d7_row9_col0, #T_868d7_row10_col0, #T_868d7_row11_col0, #T_868d7_row12_col0, #T_868d7_row13_col0, #T_868d7_row14_col0, #T_868d7_row15_col0, #T_868d7_row16_col0, #T_868d7_row17_col0, #T_868d7_row18_col0, #T_868d7_row19_col0, #T_868d7_row20_col0, #T_868d7_row21_col0, #T_868d7_row22_col0, #T_868d7_row23_col0, #T_868d7_row24_col0, #T_868d7_row25_col0, #T_868d7_row26_col0, #T_868d7_row27_col0, #T_868d7_row28_col0, #T_868d7_row29_col0, #T_868d7_row30_col0, #T_868d7_row31_col0 {
  text-align: left;
}
#T_868d7_row0_col1, #T_868d7_row0_col2, #T_868d7_row1_col1, #T_868d7_row1_col2, #T_868d7_row2_col1, #T_868d7_row2_col2, #T_868d7_row3_col1, #T_868d7_row3_col2, #T_868d7_row4_col1, #T_868d7_row4_col2, #T_868d7_row5_col1, #T_868d7_row5_col2, #T_868d7_row6_col1, #T_868d7_row6_col2, #T_868d7_row7_col1, #T_868d7_row7_col2, #T_868d7_row8_col1, #T_868d7_row8_col2, #T_868d7_row9_col1, #T_868d7_row9_col2, #T_868d7_row10_col1, #T_868d7_row10_col2, #T_868d7_row11_col1, #T_868d7_row11_col2, #T_868d7_row12_col1, #T_868d7_row12_col2, #T_868d7_row13_col1, #T_868d7_row13_col2, #T_868d7_row14_col1, #T_868d7_row14_col2, #T_868d7_row15_col1, #T_868d7_row15_col2, #T_868d7_row16_col1, #T_868d7_row16_col2, #T_868d7_row17_col1, #T_868d7_row17_col2, #T_868d7_row18_col1, #T_868d7_row18_col2, #T_868d7_row19_col1, #T_868d7_row19_col2, #T_868d7_row20_col1, #T_868d7_row20_col2, #T_868d7_row21_col1, #T_868d7_row21_col2, #T_868d7_row22_col1, #T_868d7_row22_col2, #T_868d7_row23_col1, #T_868d7_row23_col2, #T_868d7_row24_col1, #T_868d7_row24_col2, #T_868d7_row25_col1, #T_868d7_row25_col2, #T_868d7_row26_col1, #T_868d7_row26_col2, #T_868d7_row27_col1, #T_868d7_row27_col2, #T_868d7_row28_col1, #T_868d7_row28_col2, #T_868d7_row29_col1, #T_868d7_row29_col2, #T_868d7_row30_col1, #T_868d7_row30_col2, #T_868d7_row31_col1, #T_868d7_row31_col2 {
  text-align: right;
}
</style>
<table id="T_868d7">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_868d7_level0_col0" class="col_heading level0 col0" >Feature</th>
      <th id="T_868d7_level0_col1" class="col_heading level0 col1" >Gain (%)</th>
      <th id="T_868d7_level0_col2" class="col_heading level0 col2" >Splits</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_868d7_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_868d7_row0_col0" class="data row0 col0" >dwell_time</td>
      <td id="T_868d7_row0_col1" class="data row0 col1" >35.31</td>
      <td id="T_868d7_row0_col2" class="data row0 col2" >509</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_868d7_row1_col0" class="data row1 col0" >stop_name</td>
      <td id="T_868d7_row1_col1" class="data row1 col1" >30.14</td>
      <td id="T_868d7_row1_col2" class="data row1 col2" >9338</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_868d7_row2_col0" class="data row2 col0" >hour</td>
      <td id="T_868d7_row2_col1" class="data row2 col1" >12.51</td>
      <td id="T_868d7_row2_col2" class="data row2 col2" >4533</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_868d7_row3_col0" class="data row3 col0" >line_name</td>
      <td id="T_868d7_row3_col1" class="data row3 col1" >6.67</td>
      <td id="T_868d7_row3_col2" class="data row3 col2" >4086</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_868d7_row4_col0" class="data row4 col0" >weekday</td>
      <td id="T_868d7_row4_col1" class="data row4 col1" >4.29</td>
      <td id="T_868d7_row4_col2" class="data row4 col2" >2044</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_868d7_row5_col0" class="data row5 col0" >month</td>
      <td id="T_868d7_row5_col1" class="data row5 col1" >2.79</td>
      <td id="T_868d7_row5_col2" class="data row5 col2" >1426</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_868d7_row6_col0" class="data row6 col0" >temperature</td>
      <td id="T_868d7_row6_col1" class="data row6 col1" >1.61</td>
      <td id="T_868d7_row6_col2" class="data row6 col2" >2023</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_868d7_row7_col0" class="data row7 col0" >wind_speed</td>
      <td id="T_868d7_row7_col1" class="data row7 col1" >0.83</td>
      <td id="T_868d7_row7_col2" class="data row7 col2" >1314</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_868d7_row8_col0" class="data row8 col0" >event_type</td>
      <td id="T_868d7_row8_col1" class="data row8 col1" >0.81</td>
      <td id="T_868d7_row8_col2" class="data row8 col2" >682</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_868d7_row9_col0" class="data row9 col0" >precipitation</td>
      <td id="T_868d7_row9_col1" class="data row9 col1" >0.67</td>
      <td id="T_868d7_row9_col2" class="data row9 col2" >488</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_868d7_row10_col0" class="data row10 col0" >year</td>
      <td id="T_868d7_row10_col1" class="data row10 col1" >0.57</td>
      <td id="T_868d7_row10_col2" class="data row10 col2" >481</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_868d7_row11_col0" class="data row11 col0" >season</td>
      <td id="T_868d7_row11_col1" class="data row11 col1" >0.55</td>
      <td id="T_868d7_row11_col2" class="data row11 col2" >431</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_868d7_row12_col0" class="data row12 col0" >n_stops_line</td>
      <td id="T_868d7_row12_col1" class="data row12 col1" >0.48</td>
      <td id="T_868d7_row12_col2" class="data row12 col2" >515</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_868d7_row13_col0" class="data row13 col0" >is_weekend</td>
      <td id="T_868d7_row13_col1" class="data row13 col1" >0.46</td>
      <td id="T_868d7_row13_col2" class="data row13 col2" >128</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_868d7_row14_col0" class="data row14 col0" >event_weight_x_hour</td>
      <td id="T_868d7_row14_col1" class="data row14 col1" >0.40</td>
      <td id="T_868d7_row14_col2" class="data row14 col2" >528</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_868d7_row15_col0" class="data row15 col0" >is_late_night_weekend</td>
      <td id="T_868d7_row15_col1" class="data row15 col1" >0.36</td>
      <td id="T_868d7_row15_col2" class="data row15 col2" >92</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_868d7_row16_col0" class="data row16 col0" >is_holiday</td>
      <td id="T_868d7_row16_col1" class="data row16 col1" >0.30</td>
      <td id="T_868d7_row16_col2" class="data row16 col2" >175</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_868d7_row17_col0" class="data row17 col0" >n_lines_at_stop</td>
      <td id="T_868d7_row17_col1" class="data row17 col1" >0.26</td>
      <td id="T_868d7_row17_col2" class="data row17 col2" >201</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_868d7_row18_col0" class="data row18 col0" >flood_intensity</td>
      <td id="T_868d7_row18_col1" class="data row18 col1" >0.22</td>
      <td id="T_868d7_row18_col2" class="data row18 col2" >216</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_868d7_row19_col0" class="data row19 col0" >is_november</td>
      <td id="T_868d7_row19_col1" class="data row19 col1" >0.21</td>
      <td id="T_868d7_row19_col2" class="data row19 col2" >86</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_868d7_row20_col0" class="data row20 col0" >has_rain</td>
      <td id="T_868d7_row20_col1" class="data row20 col1" >0.15</td>
      <td id="T_868d7_row20_col2" class="data row20 col2" >53</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_868d7_row21_col0" class="data row21 col0" >district_nr</td>
      <td id="T_868d7_row21_col1" class="data row21 col1" >0.13</td>
      <td id="T_868d7_row21_col2" class="data row21 col2" >154</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_868d7_row22_col0" class="data row22 col0" >event_size</td>
      <td id="T_868d7_row22_col1" class="data row22 col1" >0.10</td>
      <td id="T_868d7_row22_col2" class="data row22 col2" >143</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_868d7_row23_col0" class="data row23 col0" >gtfs_year</td>
      <td id="T_868d7_row23_col1" class="data row23 col1" >0.09</td>
      <td id="T_868d7_row23_col2" class="data row23 col2" >72</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row24" class="row_heading level0 row24" >24</th>
      <td id="T_868d7_row24_col0" class="data row24 col0" >event_weight</td>
      <td id="T_868d7_row24_col1" class="data row24 col1" >0.03</td>
      <td id="T_868d7_row24_col2" class="data row24 col2" >30</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row25" class="row_heading level0 row25" >25</th>
      <td id="T_868d7_row25_col0" class="data row25 col0" >has_flood</td>
      <td id="T_868d7_row25_col1" class="data row25 col1" >0.02</td>
      <td id="T_868d7_row25_col2" class="data row25 col2" >23</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row26" class="row_heading level0 row26" >26</th>
      <td id="T_868d7_row26_col0" class="data row26 col0" >is_hot</td>
      <td id="T_868d7_row26_col1" class="data row26 col1" >0.02</td>
      <td id="T_868d7_row26_col2" class="data row26 col2" >23</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row27" class="row_heading level0 row27" >27</th>
      <td id="T_868d7_row27_col0" class="data row27 col0" >has_snow</td>
      <td id="T_868d7_row27_col1" class="data row27 col1" >0.01</td>
      <td id="T_868d7_row27_col2" class="data row27 col2" >24</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row28" class="row_heading level0 row28" >28</th>
      <td id="T_868d7_row28_col0" class="data row28 col0" >has_heavy_rain</td>
      <td id="T_868d7_row28_col1" class="data row28 col1" >0.00</td>
      <td id="T_868d7_row28_col2" class="data row28 col2" >4</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row29" class="row_heading level0 row29" >29</th>
      <td id="T_868d7_row29_col0" class="data row29 col0" >has_event</td>
      <td id="T_868d7_row29_col1" class="data row29 col1" >0.00</td>
      <td id="T_868d7_row29_col2" class="data row29 col2" >0</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row30" class="row_heading level0 row30" >30</th>
      <td id="T_868d7_row30_col0" class="data row30 col0" >is_end_stop</td>
      <td id="T_868d7_row30_col1" class="data row30 col1" >0.00</td>
      <td id="T_868d7_row30_col2" class="data row30 col2" >0</td>
    </tr>
    <tr>
      <th id="T_868d7_level0_row31" class="row_heading level0 row31" >31</th>
      <td id="T_868d7_row31_col0" class="data row31 col0" >is_start_stop</td>
      <td id="T_868d7_row31_col1" class="data row31 col1" >0.00</td>
      <td id="T_868d7_row31_col2" class="data row31 col2" >0</td>
    </tr>
  </tbody>
</table>



## Residuals — Systematischer Bias?

Schaut das Modell systematisch zu optimistisch (Vorhersage < Ist) oder zu pessimistisch (Vorhersage > Ist)?

**Mean Bias Error (MBE):** positiv = Modell überschätzt Delay · negativ = unterschätzt


```python
residuals = pred.with_columns(
    (pl.col('actual') - pl.col('predicted')).alias('residual')
)

mbe = residuals['residual'].mean()
print(f"Mean Bias Error (MBE): {mbe:.2f}s")
print(f"  > 0 = Modell unterschätzt Delay (zu optimistisch)")
print(f"  < 0 = Modell überschätzt Delay (zu pessimistisch)")

# Residual-Verteilung
sample = residuals.sample(n=min(50_000, len(residuals)), seed=42)
fig = px.histogram(sample.to_pandas(), x='residual', nbins=100,
                   title='Residual-Verteilung (actual − predicted)',
                   labels={'residual': 'Residual (s)', 'count': 'Anzahl'},
                   range_x=[-300, 300])
fig.add_vline(x=0, line_color='red', line_dash='dash')
fig.add_vline(x=mbe, line_color='orange',
              annotation_text=f'MBE {mbe:.1f}s')
fig.show()
```

    Mean Bias Error (MBE): 8.32s
      > 0 = Modell unterschätzt Delay (zu optimistisch)
      < 0 = Modell überschätzt Delay (zu pessimistisch)




### Predicted vs. Actual — Bias sichtbar gemacht

Hexbin-Dichte (100k Stichprobe): zeigt wo Vorhersagen konzentriert sind.
Ideal: alle Punkte auf der gestrichelten **y = x** Linie.
Der Bias (+8.3s) ist sichtbar als **Verschiebung nach unten** — Modell sagt systematisch weniger Delay voraus als tatsächlich eintritt.


```python
sample = pred.sample(n=100_000, seed=42).to_pandas()

CLIP_LO, CLIP_HI = -120, 500   # sinnvoller Darstellungsbereich (s)

style = mpl_style()
fig, ax = plt.subplots(figsize=(7, 7))

hb = ax.hexbin(
    sample["actual"].clip(CLIP_LO, CLIP_HI),
    sample["predicted"].clip(CLIP_LO, CLIP_HI),
    gridsize=60, cmap="YlOrRd", mincnt=1,
    extent=[CLIP_LO, CLIP_HI, CLIP_LO, CLIP_HI],
)

# Perfekte Vorhersage-Linie (y = x)
ax.plot([CLIP_LO, CLIP_HI], [CLIP_LO, CLIP_HI],
        color="#333333", lw=1.5, ls="--", label="Perfekte Vorhersage (y = x)", zorder=5)

# Bias-Linie (verschoben um MBE)
mbe_val = float(residuals["residual"].mean())
ax.plot([CLIP_LO, CLIP_HI], [CLIP_LO - mbe_val, CLIP_HI - mbe_val],
        color=cfg.COLOR_NEGATIVE, lw=1.5, ls="--",
        label=f"Modell-Bias (MBE +{mbe_val:.1f}s)", zorder=4)

ax.set_xlabel("Tatsächlicher Delay (s)", **style["label"])
ax.set_ylabel("Vorhergesagter Delay (s)", **style["label"])
ax.set_title("Predicted vs. Actual — LightGBM v1\n(Hexbin-Dichte · 100k Stichprobe)", **style["title"])
ax.legend(fontsize=9, frameon=False, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)
ax.tick_params(colors=cfg.CHART_AXIS_TEXT, labelsize=9)

cb = fig.colorbar(hb, ax=ax, fraction=0.03, pad=0.02)
cb.set_label("Anzahl Halte", fontsize=9)
cb.ax.tick_params(labelsize=8)

plt.tight_layout()
plt.show()
```


    
![png](06_prediction_3-evaluation_files/06_prediction_3-evaluation_21_0.png)
    


## Konkrete Vorhersage — Das Szenario aus dem Overview

Live-Demonstration: Eine einzelne Eingabe → eine Vorhersage. Input exakt wie im Szenario aus `06_prediction_0-overview`.


```python
import lightgbm as lgb

model_path = Path(str(TEST)).parent.parent / "models" / "lgbm_v1.txt"
model = lgb.Booster(model_file=str(model_path))

# Szenario aus 06_prediction_0-overview:
# Dienstag 17:00 · Haltestelle Paradeplatz · Linie 11 · leichter Regen · kein Event
scenario = pd.DataFrame([{
    "line_name":          "11",
    "stop_name":          "Paradeplatz",
    "district_nr":        1,
    "temperature":        14.0,
    "precipitation":      1.5,
    "wind_speed":         12.0,
    "flood_intensity":    0,
    "event_type":         "none",
    "event_size":         0,
    "hour":               17,
    "weekday":            1,
    "month":              6,
    "year":               2025,
    "season":             "summer",
    "is_weekend":         False,
    "is_november":        False,
    "gtfs_year":          "j25",
    "has_rain":           True,
    "has_heavy_rain":     False,
    "has_snow":           False,
    "has_flood":          False,
    "is_hot":             False,
    "is_holiday":         False,
    "has_event":          False,
    "event_weight":       0,
    "dwell_time":         0,
    "n_lines_at_stop":    14,
    "n_stops_line":       30,
    "is_start_stop":      False,
    "is_end_stop":        False,
    "event_weight_x_hour": 0,
    "is_late_night_weekend": False,
}])

# Kategoriale Spalten setzen
for col in ['line_name', 'stop_name', 'event_type', 'season', 'gtfs_year']:
    scenario[col] = scenario[col].astype('category')

pred_val = model.predict(scenario)[0]
print(f"Szenario: Dienstag 17:00 · Paradeplatz · Linie 11 · leichter Regen")
print(f"Vorhergesagter Delay: {pred_val:.0f}s ({pred_val/60:.1f} min)")
```

    Szenario: Dienstag 17:00 · Paradeplatz · Linie 11 · leichter Regen
    Vorhergesagter Delay: 52s (0.9 min)


## Fazit


```python
fazit = pl.DataFrame({
    "Modell":       ["Grand Mean", "Hour Mean", "Line Mean", "Stop Mean", "LightGBM v1"],
    "MAE (s)":      [50.6, 50.5, 50.4, 50.0, round(model_mae, 1)],
    "vs. Baseline": ["—", "—", "—", "Benchmark", f"-{BASELINE_MAE - model_mae:.1f}s ✅"],
})

show_df(fazit.to_pandas())

print()
print("Fazit:")
print(f"  LightGBM v1 erreicht MAE {model_mae:.1f}s auf dem Test-Set (2025).")
print(f"  Das Modell schlägt die Stop-Mean-Baseline ({BASELINE_MAE}s) um {BASELINE_MAE - model_mae:.1f}s.")
print(f"  Stärkste Schwäche: Rush-Hour und Schneetage (siehe Error Analysis).")
```


<style type="text/css">
#T_d8e02 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_d8e02 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_d8e02 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_d8e02 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_d8e02 tr:hover td {
  background-color: #eef3f8;
}
#T_d8e02_row0_col0, #T_d8e02_row0_col2, #T_d8e02_row1_col0, #T_d8e02_row1_col2, #T_d8e02_row2_col0, #T_d8e02_row2_col2, #T_d8e02_row3_col0, #T_d8e02_row3_col2, #T_d8e02_row4_col0, #T_d8e02_row4_col2 {
  text-align: left;
}
#T_d8e02_row0_col1, #T_d8e02_row1_col1, #T_d8e02_row2_col1, #T_d8e02_row3_col1, #T_d8e02_row4_col1 {
  text-align: right;
}
</style>
<table id="T_d8e02">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_d8e02_level0_col0" class="col_heading level0 col0" >Modell</th>
      <th id="T_d8e02_level0_col1" class="col_heading level0 col1" >MAE (s)</th>
      <th id="T_d8e02_level0_col2" class="col_heading level0 col2" >vs. Baseline</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_d8e02_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_d8e02_row0_col0" class="data row0 col0" >Grand Mean</td>
      <td id="T_d8e02_row0_col1" class="data row0 col1" >50.60</td>
      <td id="T_d8e02_row0_col2" class="data row0 col2" >—</td>
    </tr>
    <tr>
      <th id="T_d8e02_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_d8e02_row1_col0" class="data row1 col0" >Hour Mean</td>
      <td id="T_d8e02_row1_col1" class="data row1 col1" >50.50</td>
      <td id="T_d8e02_row1_col2" class="data row1 col2" >—</td>
    </tr>
    <tr>
      <th id="T_d8e02_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_d8e02_row2_col0" class="data row2 col0" >Line Mean</td>
      <td id="T_d8e02_row2_col1" class="data row2 col1" >50.40</td>
      <td id="T_d8e02_row2_col2" class="data row2 col2" >—</td>
    </tr>
    <tr>
      <th id="T_d8e02_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_d8e02_row3_col0" class="data row3 col0" >Stop Mean</td>
      <td id="T_d8e02_row3_col1" class="data row3 col1" >50.00</td>
      <td id="T_d8e02_row3_col2" class="data row3 col2" >Benchmark</td>
    </tr>
    <tr>
      <th id="T_d8e02_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_d8e02_row4_col0" class="data row4 col0" >LightGBM v1</td>
      <td id="T_d8e02_row4_col1" class="data row4 col1" >45.70</td>
      <td id="T_d8e02_row4_col2" class="data row4 col2" >-4.3s ✅</td>
    </tr>
  </tbody>
</table>



    
    Fazit:
      LightGBM v1 erreicht MAE 45.7s auf dem Test-Set (2025).
      Das Modell schlägt die Stop-Mean-Baseline (50.0s) um 4.3s.
      Stärkste Schwäche: Rush-Hour und Schneetage (siehe Error Analysis).


## Abschluss — Was das Modell zeigt

**Das Modell funktioniert — und es ist ehrlich über seine Grenzen.**

**Was funktioniert**
* Baseline geschlagen: −4.3s MAE auf einem kompletten Testjahr (2025) mit 30 Mio. Halts
* Gute Generalisierung: Test MAE (45.7s) besser als Val MAE (49.0s) — kein Overfitting
* Linien ohne strukturelle Anomalie (L12, L6, L17): Gewinn bis zu −15s gegenüber Baseline
* Live-Vorhersage: Di 17h · Paradeplatz · L11 · Regen → **52s** — plausibel, direkt nutzbar

**Was schwierig bleibt**
* Rush-Hour (16–18h): Delay-Spitzen zu variabel für verlässliche Vorhersage
* L11 / L8: Zu hohe Varianz in den Problemzonen — Baseline nicht geschlagen
* Seltene Ereignisse (Schnee, Extremnacht): zu wenig Daten für robuste Schätzungen
* Systematischer Bias: +8.3s Unterschätzung — Modell ist zu optimistisch

**Was das für die Praxis bedeutet**
* Das Modell eignet sich gut für **typische Situationen** (80% der Halte): normale Tage, bekannte Linien
* Für **Extremlagen** (Rush-Hour, Schnee, L11) braucht es mehr Signal: Cascade-Features, separate Modelle
* Die Fehleranalyse zeigt klar **wo als nächstes** anzusetzen ist — das ist kein Zufallsfund, sondern direkte Ableitung aus den 55 Findings der Analyse-Phase

**Nächste Schritte**
* `prev_stop_delay` Feature hinzufügen → LightGBM v2
* Interaktives Vorhersage-Tool: Haltestelle + Linie + Uhrzeit + Wetter → Delay in Sekunden






