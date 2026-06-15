# Exploratory Data Analysis (EDA) & Discovery

## Data Acquisition

### Preparation

#### Imports


```python
# data
import pandas as pd
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# admin
from pathlib import Path
import psutil
import sys
import os

# wgnd
from wgnd.core.theme import setup
from wgnd.core._output import (
    section_header, 
    log, 
    success, 
    warn
)
from wgnd.inspect import (
    inspect,
    inspect_missing,
    inspect_outliers,
    inspect_outlier_detail,
    inspect_correlations,
)
from zh_tram_flow.utils_polars import get_categorical_stats

setup()
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



#### Settings


```python
%load_ext autoreload
%autoreload 2
```

#### Constants


```python
BASE_DIR        = Path('../')
DATA_RAW_DIR    = BASE_DIR / 'data' / 'raw'
DATA            = DATA_RAW_DIR / 'zh-tram-data-master.parquet'

SEED            = 42

print(DATA)
```

    ../data/raw/zh-tram-data-master.parquet


### Data Gathering


```python

# RAM Test Polars Eager vs Lazy

def get_ram():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

print(f"RAM: {get_ram():.2f} MB")
available_ram = psutil.virtual_memory().available / (1024**3) # in GB
print(f"Freier RAM: {available_ram:.2f} GB")

#print()
#df_raw = pl.read_parquet(DATA)
#print(f"Nach Eager Read: {get_ram():.2f} MB")

print()
lf_raw = pl.scan_parquet(DATA)
print(f"Nach Lazy Scan: {get_ram():.2f} MB")
print('Lazy Scan, keine Veränderung')

print()
print(f"RAM: {get_ram():.2f} MB")
available_ram = psutil.virtual_memory().available / (1024**3) # in GB
print(f"Freier RAM: {available_ram:.2f} GB")
```

    RAM: 200.64 MB
    Freier RAM: 6.13 GB
    
    Nach Lazy Scan: 200.79 MB
    Lazy Scan, keine Veränderung
    
    RAM: 200.79 MB
    Freier RAM: 6.13 GB



```python
# Der Polars Lazy-Frame
lf = pl.scan_parquet(DATA)

# EDA-Sample: ~5% des Gesamtdatensatzes als Pandas DataFrame für wgnd.inspect
#
# Strategie: gather_every(2) + sample(fraction=0.1)
# → gather_every(2) läuft lazy (vor collect) und halbiert den Datensatz systematisch,
#   d.h. jede zweite Zeile über den gesamten Zeitraum — zeitliche Abdeckung bleibt erhalten.
# → sample(fraction=0.1) zieht danach zufällig 10% aus dieser Hälfte.
# → Ergebnis: ~5% des Gesamtdatensatzes, deterministisch via SEED.
#
# Warum kein stratifiziertes Sampling?
# Für die EDA robust genug: canceled (4.5%) und alle 18 Linien sind bei 5% (~4.5 Mio. Zeilen)
# mit hoher Wahrscheinlichkeit gut vertreten. Stratifizierung nach line_name ist für die
# Modellierungsphase vorgemerkt (BACKLOG #3) — dort kritischer als hier.


df_eda = (
    lf
    .gather_every(2)
    .collect()
    .sample(fraction=0.1, seed=SEED)
    .to_pandas()
)

# Analoge Polars-Variante des Samples (für Polars-spezifische Operationen)
lf_eda = (
    lf
    .gather_every(2)
    .collect()
    .sample(fraction=0.1, seed=SEED)
)

# Bereinigte Delay-Variante: |delay| > 3.600s entfernt — für Verteilungs-Visualisierungen
df_delays_clean = df_eda[df_eda["arrival_delay"].abs() <= 3600].copy()
```

#### Besonderheit für die große Datenmenge





**Best Practice** 
Das Grundprinzip, bei einer EDA mit großen Datensätzen, heißt "**Lazy first**, **Sample second**, **Full last**" — arbeiten in drei Stufen:

1. Verwendung von **Polars** statt Pandas, um mit der **Lazy-API** deskriptive Statistiken (Mean, Median, Verteilungen) üer den gesamten Datensatz zu berechnen.
2. Verwendung von **Samples** mit Polars für die visuelle Inspektion von Einzelfällen. Vergleich der Sample Mittelwerte mit den Mittelwerte des gesamten Datensatzes.
3. Die Reihenfolge bleibt, Meta-Daten, Statistiken global, Visualisierung via Sample.

##### Sample Strategien


Zufallsauswahl nach Anzahl / 5k
```
df_sample = df.sample(n=5000)
```
Zufallsauswahl nach Anteil / 10%
```
df_sample = df.sample(fraction=0.1) 
```
Mit Zurücklegen
```
df_sample = df.sample(fraction=0.1, with_replacement=True)
```
Mit Reproduzierbarkeit
```
df_sample = df.sample(fraction=0.1, seed=42)
```
Systematische Auswahl / jedes 10te
```
df_sample = df.gather_every(10)
```
Kopf- bzw Fußzeilen
```
df_top = df.head(10)   
df_bottom = df.tail(10)
```
X zufällige Samples nach Gruppe
```
df_stratified = df.group_by("category").agg(
    pl.all().sample(n=100)
).explode(pl.all())

```

##### Übersicht der Sampling-Methoden in Polars

| Methode | Logik | Anwendungsfall | Performance |
| :--- | :--- | :--- | :--- |
| **`.sample(n/fraction)`** | Zufallsauswahl | Repräsentative EDA, Training von ML-Modellen | Mittel |
| **`.gather_every(n)`** | Jedes n-te Element | Zeitreihen, Sensordaten, sehr große Streams | Sehr schnell |
| **`.head(n)` / `.tail(n)`** | Erste / Letzte Zeilen | Schneller Check von Schema und Datentypen | Blitzschnell |
| **`.filter(condition)`** | Logische Bedingung | Fokus auf spezifische Teilpopulationen | Schnell |
| **`.unique()`** | Keine Duplikate | Analyse der Vielfalt von Kategorien | Schnell |
| **`group_by().sample()`** | Pro Gruppe n Zeilen | Stratified Sampling (z.B. bei Betrugserkennung) | Langsamer |

## Analysis



### Basic Statistical Analysis



> _Vollständige EDA-Übersicht mit wgnd.inspect._


```python
# --- Pandas with wgnd.inspect 

result = inspect(df_eda, sections=['memory', 'dimensions', 'dtypes', 'numeric', 'categorical'])
```

    
    [1m[38;2;52;97;141m───  MEMORY  ─────────────────────────────────────────────────[0m



<style type="text/css">
#T_cb371 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_cb371 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_cb371 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_cb371 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_cb371 tr:hover td {
  background-color: #eef3f8;
}
#T_cb371_row0_col0, #T_cb371_row0_col1, #T_cb371_row1_col0, #T_cb371_row1_col1, #T_cb371_row2_col0, #T_cb371_row2_col1, #T_cb371_row3_col0, #T_cb371_row3_col1, #T_cb371_row4_col0, #T_cb371_row4_col1, #T_cb371_row5_col0, #T_cb371_row5_col1, #T_cb371_row6_col0, #T_cb371_row6_col1, #T_cb371_row7_col0, #T_cb371_row7_col1, #T_cb371_row8_col0, #T_cb371_row8_col1, #T_cb371_row9_col0, #T_cb371_row9_col1, #T_cb371_row10_col0, #T_cb371_row10_col1, #T_cb371_row11_col0, #T_cb371_row11_col1, #T_cb371_row12_col0, #T_cb371_row12_col1, #T_cb371_row13_col0, #T_cb371_row13_col1, #T_cb371_row14_col0, #T_cb371_row14_col1, #T_cb371_row15_col0, #T_cb371_row15_col1, #T_cb371_row16_col0, #T_cb371_row16_col1, #T_cb371_row17_col0, #T_cb371_row17_col1, #T_cb371_row18_col0, #T_cb371_row18_col1, #T_cb371_row19_col0, #T_cb371_row19_col1, #T_cb371_row20_col0, #T_cb371_row20_col1, #T_cb371_row21_col0, #T_cb371_row21_col1, #T_cb371_row22_col0, #T_cb371_row22_col1, #T_cb371_row23_col0, #T_cb371_row23_col1, #T_cb371_row24_col0, #T_cb371_row24_col1, #T_cb371_row25_col0, #T_cb371_row25_col1 {
  text-align: left;
}
#T_cb371_row0_col2, #T_cb371_row0_col3, #T_cb371_row1_col2, #T_cb371_row1_col3, #T_cb371_row2_col2, #T_cb371_row2_col3, #T_cb371_row3_col2, #T_cb371_row3_col3, #T_cb371_row4_col2, #T_cb371_row4_col3, #T_cb371_row5_col2, #T_cb371_row5_col3, #T_cb371_row6_col2, #T_cb371_row6_col3, #T_cb371_row7_col2, #T_cb371_row7_col3, #T_cb371_row8_col2, #T_cb371_row8_col3, #T_cb371_row9_col2, #T_cb371_row9_col3, #T_cb371_row10_col2, #T_cb371_row10_col3, #T_cb371_row11_col2, #T_cb371_row11_col3, #T_cb371_row12_col2, #T_cb371_row12_col3, #T_cb371_row13_col2, #T_cb371_row13_col3, #T_cb371_row14_col2, #T_cb371_row14_col3, #T_cb371_row15_col2, #T_cb371_row15_col3, #T_cb371_row16_col2, #T_cb371_row16_col3, #T_cb371_row17_col2, #T_cb371_row17_col3, #T_cb371_row18_col2, #T_cb371_row18_col3, #T_cb371_row19_col2, #T_cb371_row19_col3, #T_cb371_row20_col2, #T_cb371_row20_col3, #T_cb371_row21_col2, #T_cb371_row21_col3, #T_cb371_row22_col2, #T_cb371_row22_col3, #T_cb371_row23_col2, #T_cb371_row23_col3, #T_cb371_row24_col2, #T_cb371_row24_col3, #T_cb371_row25_col2, #T_cb371_row25_col3 {
  text-align: right;
}
</style>
<table id="T_cb371">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_cb371_level0_col0" class="col_heading level0 col0" >column</th>
      <th id="T_cb371_level0_col1" class="col_heading level0 col1" >dtype</th>
      <th id="T_cb371_level0_col2" class="col_heading level0 col2" >memory_kb</th>
      <th id="T_cb371_level0_col3" class="col_heading level0 col3" >memory_pct</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_cb371_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_cb371_row0_col0" class="data row0 col0" >trip_id</td>
      <td id="T_cb371_row0_col1" class="data row0 col1" >object</td>
      <td id="T_cb371_row0_col2" class="data row0 col2" >391742.66</td>
      <td id="T_cb371_row0_col3" class="data row0 col3" >45.46%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_cb371_row1_col0" class="data row1 col0" >operating_date</td>
      <td id="T_cb371_row1_col1" class="data row1 col1" >datetime64[ms]</td>
      <td id="T_cb371_row1_col2" class="data row1 col2" >36858.80</td>
      <td id="T_cb371_row1_col3" class="data row1 col3" >4.28%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_cb371_row2_col0" class="data row2 col0" >arrival_schedule</td>
      <td id="T_cb371_row2_col1" class="data row2 col1" >datetime64[us]</td>
      <td id="T_cb371_row2_col2" class="data row2 col2" >36858.80</td>
      <td id="T_cb371_row2_col3" class="data row2 col3" >4.28%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_cb371_row3_col0" class="data row3 col0" >departure_schedule</td>
      <td id="T_cb371_row3_col1" class="data row3 col1" >datetime64[us]</td>
      <td id="T_cb371_row3_col2" class="data row3 col2" >36858.80</td>
      <td id="T_cb371_row3_col3" class="data row3 col3" >4.28%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_cb371_row4_col0" class="data row4 col0" >flood_intensity</td>
      <td id="T_cb371_row4_col1" class="data row4 col1" >float64</td>
      <td id="T_cb371_row4_col2" class="data row4 col2" >36858.80</td>
      <td id="T_cb371_row4_col3" class="data row4 col3" >4.28%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_cb371_row5_col0" class="data row5 col0" >district_nr</td>
      <td id="T_cb371_row5_col1" class="data row5 col1" >float64</td>
      <td id="T_cb371_row5_col2" class="data row5 col2" >36858.80</td>
      <td id="T_cb371_row5_col3" class="data row5 col3" >4.28%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_cb371_row6_col0" class="data row6 col0" >event_size</td>
      <td id="T_cb371_row6_col1" class="data row6 col1" >float64</td>
      <td id="T_cb371_row6_col2" class="data row6 col2" >36858.80</td>
      <td id="T_cb371_row6_col3" class="data row6 col3" >4.28%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_cb371_row7_col0" class="data row7 col0" >departure_delay</td>
      <td id="T_cb371_row7_col1" class="data row7 col1" >float32</td>
      <td id="T_cb371_row7_col2" class="data row7 col2" >18429.40</td>
      <td id="T_cb371_row7_col3" class="data row7 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_cb371_row8_col0" class="data row8 col0" >arrival_delay</td>
      <td id="T_cb371_row8_col1" class="data row8 col1" >float32</td>
      <td id="T_cb371_row8_col2" class="data row8 col2" >18429.40</td>
      <td id="T_cb371_row8_col3" class="data row8 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_cb371_row9_col0" class="data row9 col0" >bpuic</td>
      <td id="T_cb371_row9_col1" class="data row9 col1" >int32</td>
      <td id="T_cb371_row9_col2" class="data row9 col2" >18429.40</td>
      <td id="T_cb371_row9_col3" class="data row9 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_cb371_row10_col0" class="data row10 col0" >global_radiation</td>
      <td id="T_cb371_row10_col1" class="data row10 col1" >float32</td>
      <td id="T_cb371_row10_col2" class="data row10 col2" >18429.40</td>
      <td id="T_cb371_row10_col3" class="data row10 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_cb371_row11_col0" class="data row11 col0" >precipitation</td>
      <td id="T_cb371_row11_col1" class="data row11 col1" >float32</td>
      <td id="T_cb371_row11_col2" class="data row11 col2" >18429.40</td>
      <td id="T_cb371_row11_col3" class="data row11 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_cb371_row12_col0" class="data row12 col0" >wind_speed</td>
      <td id="T_cb371_row12_col1" class="data row12 col1" >float32</td>
      <td id="T_cb371_row12_col2" class="data row12 col2" >18429.40</td>
      <td id="T_cb371_row12_col3" class="data row12 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_cb371_row13_col0" class="data row13 col0" >stop_lat</td>
      <td id="T_cb371_row13_col1" class="data row13 col1" >float32</td>
      <td id="T_cb371_row13_col2" class="data row13 col2" >18429.40</td>
      <td id="T_cb371_row13_col3" class="data row13 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_cb371_row14_col0" class="data row14 col0" >rain_duration</td>
      <td id="T_cb371_row14_col1" class="data row14 col1" >float32</td>
      <td id="T_cb371_row14_col2" class="data row14 col2" >18429.40</td>
      <td id="T_cb371_row14_col3" class="data row14 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_cb371_row15_col0" class="data row15 col0" >humidity</td>
      <td id="T_cb371_row15_col1" class="data row15 col1" >float32</td>
      <td id="T_cb371_row15_col2" class="data row15 col2" >18429.40</td>
      <td id="T_cb371_row15_col3" class="data row15 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_cb371_row16_col0" class="data row16 col0" >stop_lon</td>
      <td id="T_cb371_row16_col1" class="data row16 col1" >float32</td>
      <td id="T_cb371_row16_col2" class="data row16 col2" >18429.40</td>
      <td id="T_cb371_row16_col3" class="data row16 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_cb371_row17_col0" class="data row17 col0" >temperature</td>
      <td id="T_cb371_row17_col1" class="data row17 col1" >float32</td>
      <td id="T_cb371_row17_col2" class="data row17 col2" >18429.40</td>
      <td id="T_cb371_row17_col3" class="data row17 col3" >2.14%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_cb371_row18_col0" class="data row18 col0" >stop_name</td>
      <td id="T_cb371_row18_col1" class="data row18 col1" >category</td>
      <td id="T_cb371_row18_col2" class="data row18 col2" >9244.36</td>
      <td id="T_cb371_row18_col3" class="data row18 col3" >1.07%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_cb371_row19_col0" class="data row19 col0" >stop_sequence</td>
      <td id="T_cb371_row19_col1" class="data row19 col1" >int16</td>
      <td id="T_cb371_row19_col2" class="data row19 col2" >9214.70</td>
      <td id="T_cb371_row19_col3" class="data row19 col3" >1.07%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_cb371_row20_col0" class="data row20 col0" >event_name</td>
      <td id="T_cb371_row20_col1" class="data row20 col1" >category</td>
      <td id="T_cb371_row20_col2" class="data row20 col2" >4615.02</td>
      <td id="T_cb371_row20_col3" class="data row20 col3" >0.54%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_cb371_row21_col0" class="data row21 col0" >line_name</td>
      <td id="T_cb371_row21_col1" class="data row21 col1" >category</td>
      <td id="T_cb371_row21_col2" class="data row21 col2" >4608.92</td>
      <td id="T_cb371_row21_col3" class="data row21 col3" >0.53%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_cb371_row22_col0" class="data row22 col0" >event_location</td>
      <td id="T_cb371_row22_col1" class="data row22 col1" >category</td>
      <td id="T_cb371_row22_col2" class="data row22 col2" >4608.76</td>
      <td id="T_cb371_row22_col3" class="data row22 col3" >0.53%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_cb371_row23_col0" class="data row23 col0" >district_name</td>
      <td id="T_cb371_row23_col1" class="data row23 col1" >category</td>
      <td id="T_cb371_row23_col2" class="data row23 col2" >4608.40</td>
      <td id="T_cb371_row23_col3" class="data row23 col3" >0.53%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row24" class="row_heading level0 row24" >24</th>
      <td id="T_cb371_row24_col0" class="data row24 col0" >event_type</td>
      <td id="T_cb371_row24_col1" class="data row24 col1" >category</td>
      <td id="T_cb371_row24_col2" class="data row24 col2" >4608.25</td>
      <td id="T_cb371_row24_col3" class="data row24 col3" >0.53%</td>
    </tr>
    <tr>
      <th id="T_cb371_level0_row25" class="row_heading level0 row25" >25</th>
      <td id="T_cb371_row25_col0" class="data row25 col0" >canceled</td>
      <td id="T_cb371_row25_col1" class="data row25 col1" >bool</td>
      <td id="T_cb371_row25_col2" class="data row25 col2" >4607.35</td>
      <td id="T_cb371_row25_col3" class="data row25 col3" >0.53%</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mTotal: 861734.71 KB  (841.54 MB)[0m
    
    [1m[38;2;52;97;141m───  DIMENSIONS  ─────────────────────────────────────────────[0m



<style type="text/css">
#T_5513a thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_5513a td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_5513a tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_5513a tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_5513a tr:hover td {
  background-color: #eef3f8;
}
#T_5513a_row0_col0, #T_5513a_row0_col2, #T_5513a_row1_col0, #T_5513a_row1_col2, #T_5513a_row2_col0, #T_5513a_row2_col2, #T_5513a_row3_col0, #T_5513a_row3_col2, #T_5513a_row4_col0, #T_5513a_row4_col2 {
  text-align: left;
}
#T_5513a_row0_col1, #T_5513a_row1_col1, #T_5513a_row2_col1, #T_5513a_row3_col1, #T_5513a_row4_col1 {
  text-align: right;
}
</style>
<table id="T_5513a">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_5513a_level0_col0" class="col_heading level0 col0" >metric</th>
      <th id="T_5513a_level0_col1" class="col_heading level0 col1" >count</th>
      <th id="T_5513a_level0_col2" class="col_heading level0 col2" >pct</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_5513a_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_5513a_row0_col0" class="data row0 col0" >rows</td>
      <td id="T_5513a_row0_col1" class="data row0 col1" >4717926</td>
      <td id="T_5513a_row0_col2" class="data row0 col2" ></td>
    </tr>
    <tr>
      <th id="T_5513a_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_5513a_row1_col0" class="data row1 col0" >columns</td>
      <td id="T_5513a_row1_col1" class="data row1 col1" >26</td>
      <td id="T_5513a_row1_col2" class="data row1 col2" ></td>
    </tr>
    <tr>
      <th id="T_5513a_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_5513a_row2_col0" class="data row2 col0" >duplicates</td>
      <td id="T_5513a_row2_col1" class="data row2 col1" >0</td>
      <td id="T_5513a_row2_col2" class="data row2 col2" >0.0%</td>
    </tr>
    <tr>
      <th id="T_5513a_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_5513a_row3_col0" class="data row3 col0" >empty rows (all NaN)</td>
      <td id="T_5513a_row3_col1" class="data row3 col1" >0</td>
      <td id="T_5513a_row3_col2" class="data row3 col2" >0.0%</td>
    </tr>
    <tr>
      <th id="T_5513a_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_5513a_row4_col0" class="data row4 col0" >empty cols (all NaN)</td>
      <td id="T_5513a_row4_col1" class="data row4 col1" >0</td>
      <td id="T_5513a_row4_col2" class="data row4 col2" >0.0%</td>
    </tr>
  </tbody>
</table>



    
    [1m[38;2;52;97;141m───  DTYPES  ─────────────────────────────────────────────────[0m



<style type="text/css">
#T_beb81 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_beb81 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_beb81 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_beb81 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_beb81 tr:hover td {
  background-color: #eef3f8;
}
#T_beb81_row0_col0, #T_beb81_row0_col1, #T_beb81_row1_col0, #T_beb81_row1_col1, #T_beb81_row2_col0, #T_beb81_row2_col1, #T_beb81_row3_col0, #T_beb81_row3_col1, #T_beb81_row4_col0, #T_beb81_row4_col1, #T_beb81_row5_col0, #T_beb81_row5_col1, #T_beb81_row6_col0, #T_beb81_row6_col1, #T_beb81_row7_col0, #T_beb81_row7_col1, #T_beb81_row8_col0, #T_beb81_row8_col1, #T_beb81_row9_col0, #T_beb81_row9_col1, #T_beb81_row10_col0, #T_beb81_row10_col1, #T_beb81_row11_col0, #T_beb81_row11_col1, #T_beb81_row12_col0, #T_beb81_row12_col1, #T_beb81_row13_col0, #T_beb81_row13_col1, #T_beb81_row14_col0, #T_beb81_row14_col1, #T_beb81_row15_col0, #T_beb81_row15_col1, #T_beb81_row16_col0, #T_beb81_row16_col1, #T_beb81_row17_col0, #T_beb81_row17_col1, #T_beb81_row18_col0, #T_beb81_row18_col1, #T_beb81_row19_col0, #T_beb81_row19_col1, #T_beb81_row20_col0, #T_beb81_row20_col1, #T_beb81_row21_col0, #T_beb81_row21_col1, #T_beb81_row22_col0, #T_beb81_row22_col1, #T_beb81_row23_col0, #T_beb81_row23_col1, #T_beb81_row24_col0, #T_beb81_row24_col1, #T_beb81_row25_col0, #T_beb81_row25_col1 {
  text-align: left;
}
#T_beb81_row0_col2, #T_beb81_row0_col3, #T_beb81_row0_col4, #T_beb81_row0_col5, #T_beb81_row1_col2, #T_beb81_row1_col3, #T_beb81_row1_col4, #T_beb81_row1_col5, #T_beb81_row2_col2, #T_beb81_row2_col3, #T_beb81_row2_col4, #T_beb81_row2_col5, #T_beb81_row3_col2, #T_beb81_row3_col3, #T_beb81_row3_col4, #T_beb81_row3_col5, #T_beb81_row4_col3, #T_beb81_row4_col4, #T_beb81_row4_col5, #T_beb81_row5_col3, #T_beb81_row5_col4, #T_beb81_row5_col5, #T_beb81_row6_col3, #T_beb81_row6_col4, #T_beb81_row6_col5, #T_beb81_row7_col3, #T_beb81_row7_col4, #T_beb81_row7_col5, #T_beb81_row8_col2, #T_beb81_row8_col3, #T_beb81_row8_col4, #T_beb81_row8_col5, #T_beb81_row9_col2, #T_beb81_row9_col3, #T_beb81_row9_col4, #T_beb81_row9_col5, #T_beb81_row10_col3, #T_beb81_row10_col4, #T_beb81_row10_col5, #T_beb81_row11_col3, #T_beb81_row11_col4, #T_beb81_row11_col5, #T_beb81_row12_col3, #T_beb81_row12_col4, #T_beb81_row12_col5, #T_beb81_row13_col3, #T_beb81_row13_col4, #T_beb81_row13_col5, #T_beb81_row14_col3, #T_beb81_row14_col4, #T_beb81_row14_col5, #T_beb81_row15_col3, #T_beb81_row15_col4, #T_beb81_row15_col5, #T_beb81_row16_col3, #T_beb81_row16_col4, #T_beb81_row16_col5, #T_beb81_row17_col3, #T_beb81_row17_col4, #T_beb81_row17_col5, #T_beb81_row18_col3, #T_beb81_row18_col4, #T_beb81_row18_col5, #T_beb81_row19_col3, #T_beb81_row19_col4, #T_beb81_row19_col5, #T_beb81_row20_col3, #T_beb81_row20_col4, #T_beb81_row20_col5, #T_beb81_row21_col3, #T_beb81_row21_col4, #T_beb81_row21_col5, #T_beb81_row22_col3, #T_beb81_row22_col4, #T_beb81_row22_col5, #T_beb81_row23_col3, #T_beb81_row23_col4, #T_beb81_row23_col5, #T_beb81_row24_col3, #T_beb81_row24_col4, #T_beb81_row24_col5, #T_beb81_row25_col3, #T_beb81_row25_col4, #T_beb81_row25_col5 {
  text-align: right;
}
#T_beb81_row4_col2, #T_beb81_row5_col2, #T_beb81_row6_col2, #T_beb81_row7_col2, #T_beb81_row10_col2, #T_beb81_row11_col2, #T_beb81_row12_col2, #T_beb81_row13_col2, #T_beb81_row14_col2, #T_beb81_row15_col2, #T_beb81_row16_col2, #T_beb81_row17_col2, #T_beb81_row18_col2, #T_beb81_row19_col2, #T_beb81_row20_col2, #T_beb81_row21_col2, #T_beb81_row22_col2, #T_beb81_row23_col2, #T_beb81_row24_col2, #T_beb81_row25_col2 {
  text-align: right;
  color: #de425b;
  font-weight: 500;
}
</style>
<table id="T_beb81">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_beb81_level0_col0" class="col_heading level0 col0" >column</th>
      <th id="T_beb81_level0_col1" class="col_heading level0 col1" >dtype</th>
      <th id="T_beb81_level0_col2" class="col_heading level0 col2" >missing_cnt</th>
      <th id="T_beb81_level0_col3" class="col_heading level0 col3" >missing_pct</th>
      <th id="T_beb81_level0_col4" class="col_heading level0 col4" >unique</th>
      <th id="T_beb81_level0_col5" class="col_heading level0 col5" >unique_pct</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_beb81_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_beb81_row0_col0" class="data row0 col0" >operating_date</td>
      <td id="T_beb81_row0_col1" class="data row0 col1" >datetime64[ms]</td>
      <td id="T_beb81_row0_col2" class="data row0 col2" >0</td>
      <td id="T_beb81_row0_col3" class="data row0 col3" >0.00%</td>
      <td id="T_beb81_row0_col4" class="data row0 col4" >1092</td>
      <td id="T_beb81_row0_col5" class="data row0 col5" >0.02%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_beb81_row1_col0" class="data row1 col0" >trip_id</td>
      <td id="T_beb81_row1_col1" class="data row1 col1" >object</td>
      <td id="T_beb81_row1_col2" class="data row1 col2" >0</td>
      <td id="T_beb81_row1_col3" class="data row1 col3" >0.00%</td>
      <td id="T_beb81_row1_col4" class="data row1 col4" >321006</td>
      <td id="T_beb81_row1_col5" class="data row1 col5" >6.80%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_beb81_row2_col0" class="data row2 col0" >line_name</td>
      <td id="T_beb81_row2_col1" class="data row2 col1" >category</td>
      <td id="T_beb81_row2_col2" class="data row2 col2" >0</td>
      <td id="T_beb81_row2_col3" class="data row2 col3" >0.00%</td>
      <td id="T_beb81_row2_col4" class="data row2 col4" >18</td>
      <td id="T_beb81_row2_col5" class="data row2 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_beb81_row3_col0" class="data row3 col0" >bpuic</td>
      <td id="T_beb81_row3_col1" class="data row3 col1" >int32</td>
      <td id="T_beb81_row3_col2" class="data row3 col2" >0</td>
      <td id="T_beb81_row3_col3" class="data row3 col3" >0.00%</td>
      <td id="T_beb81_row3_col4" class="data row3 col4" >634</td>
      <td id="T_beb81_row3_col5" class="data row3 col5" >0.01%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_beb81_row4_col0" class="data row4 col0" >arrival_schedule</td>
      <td id="T_beb81_row4_col1" class="data row4 col1" >datetime64[us]</td>
      <td id="T_beb81_row4_col2" class="data row4 col2" >6906</td>
      <td id="T_beb81_row4_col3" class="data row4 col3" >0.15%</td>
      <td id="T_beb81_row4_col4" class="data row4 col4" >1253941</td>
      <td id="T_beb81_row4_col5" class="data row4 col5" >26.58%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_beb81_row5_col0" class="data row5 col0" >arrival_delay</td>
      <td id="T_beb81_row5_col1" class="data row5 col1" >float32</td>
      <td id="T_beb81_row5_col2" class="data row5 col2" >11320</td>
      <td id="T_beb81_row5_col3" class="data row5 col3" >0.24%</td>
      <td id="T_beb81_row5_col4" class="data row5 col4" >3637</td>
      <td id="T_beb81_row5_col5" class="data row5 col5" >0.08%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_beb81_row6_col0" class="data row6 col0" >departure_schedule</td>
      <td id="T_beb81_row6_col1" class="data row6 col1" >datetime64[us]</td>
      <td id="T_beb81_row6_col2" class="data row6 col2" >6764</td>
      <td id="T_beb81_row6_col3" class="data row6 col3" >0.14%</td>
      <td id="T_beb81_row6_col4" class="data row6 col4" >1254177</td>
      <td id="T_beb81_row6_col5" class="data row6 col5" >26.58%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_beb81_row7_col0" class="data row7 col0" >departure_delay</td>
      <td id="T_beb81_row7_col1" class="data row7 col1" >float32</td>
      <td id="T_beb81_row7_col2" class="data row7 col2" >11286</td>
      <td id="T_beb81_row7_col3" class="data row7 col3" >0.24%</td>
      <td id="T_beb81_row7_col4" class="data row7 col4" >3714</td>
      <td id="T_beb81_row7_col5" class="data row7 col5" >0.08%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_beb81_row8_col0" class="data row8 col0" >canceled</td>
      <td id="T_beb81_row8_col1" class="data row8 col1" >bool</td>
      <td id="T_beb81_row8_col2" class="data row8 col2" >0</td>
      <td id="T_beb81_row8_col3" class="data row8 col3" >0.00%</td>
      <td id="T_beb81_row8_col4" class="data row8 col4" >2</td>
      <td id="T_beb81_row8_col5" class="data row8 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_beb81_row9_col0" class="data row9 col0" >stop_sequence</td>
      <td id="T_beb81_row9_col1" class="data row9 col1" >int16</td>
      <td id="T_beb81_row9_col2" class="data row9 col2" >0</td>
      <td id="T_beb81_row9_col3" class="data row9 col3" >0.00%</td>
      <td id="T_beb81_row9_col4" class="data row9 col4" >68</td>
      <td id="T_beb81_row9_col5" class="data row9 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_beb81_row10_col0" class="data row10 col0" >stop_name</td>
      <td id="T_beb81_row10_col1" class="data row10 col1" >category</td>
      <td id="T_beb81_row10_col2" class="data row10 col2" >4508</td>
      <td id="T_beb81_row10_col3" class="data row10 col3" >0.10%</td>
      <td id="T_beb81_row10_col4" class="data row10 col4" >223</td>
      <td id="T_beb81_row10_col5" class="data row10 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_beb81_row11_col0" class="data row11 col0" >stop_lat</td>
      <td id="T_beb81_row11_col1" class="data row11 col1" >float32</td>
      <td id="T_beb81_row11_col2" class="data row11 col2" >4508</td>
      <td id="T_beb81_row11_col3" class="data row11 col3" >0.10%</td>
      <td id="T_beb81_row11_col4" class="data row11 col4" >221</td>
      <td id="T_beb81_row11_col5" class="data row11 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_beb81_row12_col0" class="data row12 col0" >stop_lon</td>
      <td id="T_beb81_row12_col1" class="data row12 col1" >float32</td>
      <td id="T_beb81_row12_col2" class="data row12 col2" >4508</td>
      <td id="T_beb81_row12_col3" class="data row12 col3" >0.10%</td>
      <td id="T_beb81_row12_col4" class="data row12 col4" >222</td>
      <td id="T_beb81_row12_col5" class="data row12 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_beb81_row13_col0" class="data row13 col0" >district_nr</td>
      <td id="T_beb81_row13_col1" class="data row13 col1" >float64</td>
      <td id="T_beb81_row13_col2" class="data row13 col2" >325158</td>
      <td id="T_beb81_row13_col3" class="data row13 col3" >6.89%</td>
      <td id="T_beb81_row13_col4" class="data row13 col4" >12</td>
      <td id="T_beb81_row13_col5" class="data row13 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_beb81_row14_col0" class="data row14 col0" >district_name</td>
      <td id="T_beb81_row14_col1" class="data row14 col1" >category</td>
      <td id="T_beb81_row14_col2" class="data row14 col2" >325158</td>
      <td id="T_beb81_row14_col3" class="data row14 col3" >6.89%</td>
      <td id="T_beb81_row14_col4" class="data row14 col4" >12</td>
      <td id="T_beb81_row14_col5" class="data row14 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_beb81_row15_col0" class="data row15 col0" >temperature</td>
      <td id="T_beb81_row15_col1" class="data row15 col1" >float32</td>
      <td id="T_beb81_row15_col2" class="data row15 col2" >16584</td>
      <td id="T_beb81_row15_col3" class="data row15 col3" >0.35%</td>
      <td id="T_beb81_row15_col4" class="data row15 col4" >3489</td>
      <td id="T_beb81_row15_col5" class="data row15 col5" >0.07%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_beb81_row16_col0" class="data row16 col0" >humidity</td>
      <td id="T_beb81_row16_col1" class="data row16 col1" >float32</td>
      <td id="T_beb81_row16_col2" class="data row16 col2" >16584</td>
      <td id="T_beb81_row16_col3" class="data row16 col3" >0.35%</td>
      <td id="T_beb81_row16_col4" class="data row16 col4" >6455</td>
      <td id="T_beb81_row16_col5" class="data row16 col5" >0.14%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_beb81_row17_col0" class="data row17 col0" >rain_duration</td>
      <td id="T_beb81_row17_col1" class="data row17 col1" >float32</td>
      <td id="T_beb81_row17_col2" class="data row17 col2" >12759</td>
      <td id="T_beb81_row17_col3" class="data row17 col3" >0.27%</td>
      <td id="T_beb81_row17_col4" class="data row17 col4" >1976</td>
      <td id="T_beb81_row17_col5" class="data row17 col5" >0.04%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_beb81_row18_col0" class="data row18 col0" >precipitation</td>
      <td id="T_beb81_row18_col1" class="data row18 col1" >float32</td>
      <td id="T_beb81_row18_col2" class="data row18 col2" >11815</td>
      <td id="T_beb81_row18_col3" class="data row18 col3" >0.25%</td>
      <td id="T_beb81_row18_col4" class="data row18 col4" >88</td>
      <td id="T_beb81_row18_col5" class="data row18 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_beb81_row19_col0" class="data row19 col0" >wind_speed</td>
      <td id="T_beb81_row19_col1" class="data row19 col1" >float32</td>
      <td id="T_beb81_row19_col2" class="data row19 col2" >13666</td>
      <td id="T_beb81_row19_col3" class="data row19 col3" >0.29%</td>
      <td id="T_beb81_row19_col4" class="data row19 col4" >634</td>
      <td id="T_beb81_row19_col5" class="data row19 col5" >0.01%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_beb81_row20_col0" class="data row20 col0" >global_radiation</td>
      <td id="T_beb81_row20_col1" class="data row20 col1" >float32</td>
      <td id="T_beb81_row20_col2" class="data row20 col2" >14061</td>
      <td id="T_beb81_row20_col3" class="data row20 col3" >0.30%</td>
      <td id="T_beb81_row20_col4" class="data row20 col4" >11912</td>
      <td id="T_beb81_row20_col5" class="data row20 col5" >0.25%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_beb81_row21_col0" class="data row21 col0" >flood_intensity</td>
      <td id="T_beb81_row21_col1" class="data row21 col1" >float64</td>
      <td id="T_beb81_row21_col2" class="data row21 col2" >7344</td>
      <td id="T_beb81_row21_col3" class="data row21 col3" >0.16%</td>
      <td id="T_beb81_row21_col4" class="data row21 col4" >6</td>
      <td id="T_beb81_row21_col5" class="data row21 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_beb81_row22_col0" class="data row22 col0" >event_name</td>
      <td id="T_beb81_row22_col1" class="data row22 col1" >category</td>
      <td id="T_beb81_row22_col2" class="data row22 col2" >3704729</td>
      <td id="T_beb81_row22_col3" class="data row22 col3" >78.52%</td>
      <td id="T_beb81_row22_col4" class="data row22 col4" >72</td>
      <td id="T_beb81_row22_col5" class="data row22 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_beb81_row23_col0" class="data row23 col0" >event_type</td>
      <td id="T_beb81_row23_col1" class="data row23 col1" >category</td>
      <td id="T_beb81_row23_col2" class="data row23 col2" >3704729</td>
      <td id="T_beb81_row23_col3" class="data row23 col3" >78.52%</td>
      <td id="T_beb81_row23_col4" class="data row23 col4" >9</td>
      <td id="T_beb81_row23_col5" class="data row23 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row24" class="row_heading level0 row24" >24</th>
      <td id="T_beb81_row24_col0" class="data row24 col0" >event_size</td>
      <td id="T_beb81_row24_col1" class="data row24 col1" >float64</td>
      <td id="T_beb81_row24_col2" class="data row24 col2" >3704729</td>
      <td id="T_beb81_row24_col3" class="data row24 col3" >78.52%</td>
      <td id="T_beb81_row24_col4" class="data row24 col4" >3</td>
      <td id="T_beb81_row24_col5" class="data row24 col5" >0.00%</td>
    </tr>
    <tr>
      <th id="T_beb81_level0_row25" class="row_heading level0 row25" >25</th>
      <td id="T_beb81_row25_col0" class="data row25 col0" >event_location</td>
      <td id="T_beb81_row25_col1" class="data row25 col1" >category</td>
      <td id="T_beb81_row25_col2" class="data row25 col2" >3704729</td>
      <td id="T_beb81_row25_col3" class="data row25 col3" >78.52%</td>
      <td id="T_beb81_row25_col4" class="data row25 col4" >12</td>
      <td id="T_beb81_row25_col5" class="data row25 col5" >0.00%</td>
    </tr>
  </tbody>
</table>



    
    [1m[38;2;52;97;141m───  NUMERIC STATS  ──────────────────────────────────────────[0m



<style type="text/css">
#T_6ee67 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_6ee67 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_6ee67 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_6ee67 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_6ee67 tr:hover td {
  background-color: #eef3f8;
}
#T_6ee67_row0_col0, #T_6ee67_row1_col0, #T_6ee67_row2_col0, #T_6ee67_row3_col0, #T_6ee67_row4_col0, #T_6ee67_row5_col0, #T_6ee67_row6_col0, #T_6ee67_row7_col0, #T_6ee67_row8_col0, #T_6ee67_row9_col0, #T_6ee67_row10_col0, #T_6ee67_row11_col0, #T_6ee67_row12_col0, #T_6ee67_row13_col0, #T_6ee67_row14_col0 {
  text-align: left;
}
#T_6ee67_row0_col1, #T_6ee67_row0_col2, #T_6ee67_row0_col3, #T_6ee67_row0_col4, #T_6ee67_row0_col5, #T_6ee67_row0_col6, #T_6ee67_row0_col7, #T_6ee67_row0_col8, #T_6ee67_row0_col9, #T_6ee67_row0_col10, #T_6ee67_row0_col11, #T_6ee67_row1_col1, #T_6ee67_row1_col2, #T_6ee67_row1_col3, #T_6ee67_row1_col4, #T_6ee67_row1_col5, #T_6ee67_row1_col6, #T_6ee67_row1_col7, #T_6ee67_row1_col8, #T_6ee67_row1_col9, #T_6ee67_row1_col10, #T_6ee67_row1_col11, #T_6ee67_row2_col1, #T_6ee67_row2_col2, #T_6ee67_row2_col3, #T_6ee67_row2_col4, #T_6ee67_row2_col5, #T_6ee67_row2_col6, #T_6ee67_row2_col7, #T_6ee67_row2_col8, #T_6ee67_row2_col9, #T_6ee67_row2_col10, #T_6ee67_row2_col11, #T_6ee67_row3_col1, #T_6ee67_row3_col2, #T_6ee67_row3_col3, #T_6ee67_row3_col4, #T_6ee67_row3_col5, #T_6ee67_row3_col6, #T_6ee67_row3_col7, #T_6ee67_row3_col8, #T_6ee67_row3_col9, #T_6ee67_row3_col10, #T_6ee67_row3_col11, #T_6ee67_row4_col1, #T_6ee67_row4_col2, #T_6ee67_row4_col3, #T_6ee67_row4_col4, #T_6ee67_row4_col5, #T_6ee67_row4_col6, #T_6ee67_row4_col7, #T_6ee67_row4_col8, #T_6ee67_row4_col9, #T_6ee67_row4_col10, #T_6ee67_row4_col11, #T_6ee67_row5_col1, #T_6ee67_row5_col2, #T_6ee67_row5_col3, #T_6ee67_row5_col4, #T_6ee67_row5_col5, #T_6ee67_row5_col6, #T_6ee67_row5_col7, #T_6ee67_row5_col8, #T_6ee67_row5_col9, #T_6ee67_row5_col10, #T_6ee67_row5_col11, #T_6ee67_row6_col1, #T_6ee67_row6_col2, #T_6ee67_row6_col3, #T_6ee67_row6_col4, #T_6ee67_row6_col5, #T_6ee67_row6_col6, #T_6ee67_row6_col7, #T_6ee67_row6_col8, #T_6ee67_row6_col9, #T_6ee67_row6_col10, #T_6ee67_row6_col11, #T_6ee67_row7_col1, #T_6ee67_row7_col2, #T_6ee67_row7_col3, #T_6ee67_row7_col4, #T_6ee67_row7_col5, #T_6ee67_row7_col6, #T_6ee67_row7_col7, #T_6ee67_row7_col8, #T_6ee67_row7_col9, #T_6ee67_row7_col10, #T_6ee67_row7_col11, #T_6ee67_row8_col1, #T_6ee67_row8_col2, #T_6ee67_row8_col3, #T_6ee67_row8_col4, #T_6ee67_row8_col5, #T_6ee67_row8_col6, #T_6ee67_row8_col7, #T_6ee67_row8_col8, #T_6ee67_row8_col9, #T_6ee67_row8_col10, #T_6ee67_row8_col11, #T_6ee67_row9_col1, #T_6ee67_row9_col2, #T_6ee67_row9_col3, #T_6ee67_row9_col4, #T_6ee67_row9_col5, #T_6ee67_row9_col6, #T_6ee67_row9_col7, #T_6ee67_row9_col8, #T_6ee67_row9_col9, #T_6ee67_row9_col10, #T_6ee67_row9_col11, #T_6ee67_row10_col1, #T_6ee67_row10_col2, #T_6ee67_row10_col3, #T_6ee67_row10_col4, #T_6ee67_row10_col5, #T_6ee67_row10_col6, #T_6ee67_row10_col7, #T_6ee67_row10_col8, #T_6ee67_row10_col9, #T_6ee67_row10_col10, #T_6ee67_row10_col11, #T_6ee67_row11_col1, #T_6ee67_row11_col2, #T_6ee67_row11_col3, #T_6ee67_row11_col4, #T_6ee67_row11_col5, #T_6ee67_row11_col6, #T_6ee67_row11_col7, #T_6ee67_row11_col8, #T_6ee67_row11_col9, #T_6ee67_row11_col10, #T_6ee67_row11_col11, #T_6ee67_row12_col1, #T_6ee67_row12_col2, #T_6ee67_row12_col3, #T_6ee67_row12_col4, #T_6ee67_row12_col5, #T_6ee67_row12_col6, #T_6ee67_row12_col7, #T_6ee67_row12_col8, #T_6ee67_row12_col9, #T_6ee67_row12_col10, #T_6ee67_row12_col11, #T_6ee67_row13_col1, #T_6ee67_row13_col2, #T_6ee67_row13_col3, #T_6ee67_row13_col4, #T_6ee67_row13_col5, #T_6ee67_row13_col6, #T_6ee67_row13_col7, #T_6ee67_row13_col8, #T_6ee67_row13_col9, #T_6ee67_row13_col10, #T_6ee67_row13_col11, #T_6ee67_row14_col1, #T_6ee67_row14_col2, #T_6ee67_row14_col3, #T_6ee67_row14_col4, #T_6ee67_row14_col5, #T_6ee67_row14_col6, #T_6ee67_row14_col7, #T_6ee67_row14_col8, #T_6ee67_row14_col9, #T_6ee67_row14_col10, #T_6ee67_row14_col11 {
  text-align: right;
}
</style>
<table id="T_6ee67">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_6ee67_level0_col0" class="col_heading level0 col0" >column</th>
      <th id="T_6ee67_level0_col1" class="col_heading level0 col1" >missing_pct</th>
      <th id="T_6ee67_level0_col2" class="col_heading level0 col2" >count</th>
      <th id="T_6ee67_level0_col3" class="col_heading level0 col3" >mean</th>
      <th id="T_6ee67_level0_col4" class="col_heading level0 col4" >median</th>
      <th id="T_6ee67_level0_col5" class="col_heading level0 col5" >std</th>
      <th id="T_6ee67_level0_col6" class="col_heading level0 col6" >min</th>
      <th id="T_6ee67_level0_col7" class="col_heading level0 col7" >25%</th>
      <th id="T_6ee67_level0_col8" class="col_heading level0 col8" >75%</th>
      <th id="T_6ee67_level0_col9" class="col_heading level0 col9" >max</th>
      <th id="T_6ee67_level0_col10" class="col_heading level0 col10" >mean_median_diff</th>
      <th id="T_6ee67_level0_col11" class="col_heading level0 col11" >skewness</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_6ee67_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_6ee67_row0_col0" class="data row0 col0" >bpuic</td>
      <td id="T_6ee67_row0_col1" class="data row0 col1" >0.00%</td>
      <td id="T_6ee67_row0_col2" class="data row0 col2" >4717926.00</td>
      <td id="T_6ee67_row0_col3" class="data row0 col3" >9399000.77</td>
      <td id="T_6ee67_row0_col4" class="data row0 col4" >8591220.00</td>
      <td id="T_6ee67_row0_col5" class="data row0 col5" >26255697.03</td>
      <td id="T_6ee67_row0_col6" class="data row0 col6" >8502572.00</td>
      <td id="T_6ee67_row0_col7" class="data row0 col7" >8591060.00</td>
      <td id="T_6ee67_row0_col8" class="data row0 col8" >8591335.00</td>
      <td id="T_6ee67_row0_col9" class="data row0 col9" >859423901.00</td>
      <td id="T_6ee67_row0_col10" class="data row0 col10" >807780.77</td>
      <td id="T_6ee67_row0_col11" class="data row0 col11" >32.32</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_6ee67_row1_col0" class="data row1 col0" >arrival_delay</td>
      <td id="T_6ee67_row1_col1" class="data row1 col1" >0.24%</td>
      <td id="T_6ee67_row1_col2" class="data row1 col2" >4706606.00</td>
      <td id="T_6ee67_row1_col3" class="data row1 col3" >56.16</td>
      <td id="T_6ee67_row1_col4" class="data row1 col4" >42.00</td>
      <td id="T_6ee67_row1_col5" class="data row1 col5" >113.35</td>
      <td id="T_6ee67_row1_col6" class="data row1 col6" >-29892.00</td>
      <td id="T_6ee67_row1_col7" class="data row1 col7" >12.00</td>
      <td id="T_6ee67_row1_col8" class="data row1 col8" >81.00</td>
      <td id="T_6ee67_row1_col9" class="data row1 col9" >33785.00</td>
      <td id="T_6ee67_row1_col10" class="data row1 col10" >14.16</td>
      <td id="T_6ee67_row1_col11" class="data row1 col11" >64.25</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_6ee67_row2_col0" class="data row2 col0" >departure_delay</td>
      <td id="T_6ee67_row2_col1" class="data row2 col1" >0.24%</td>
      <td id="T_6ee67_row2_col2" class="data row2 col2" >4706640.00</td>
      <td id="T_6ee67_row2_col3" class="data row2 col3" >61.76</td>
      <td id="T_6ee67_row2_col4" class="data row2 col4" >47.00</td>
      <td id="T_6ee67_row2_col5" class="data row2 col5" >113.26</td>
      <td id="T_6ee67_row2_col6" class="data row2 col6" >-29876.00</td>
      <td id="T_6ee67_row2_col7" class="data row2 col7" >16.00</td>
      <td id="T_6ee67_row2_col8" class="data row2 col8" >88.00</td>
      <td id="T_6ee67_row2_col9" class="data row2 col9" >33785.00</td>
      <td id="T_6ee67_row2_col10" class="data row2 col10" >14.76</td>
      <td id="T_6ee67_row2_col11" class="data row2 col11" >59.26</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_6ee67_row3_col0" class="data row3 col0" >stop_sequence</td>
      <td id="T_6ee67_row3_col1" class="data row3 col1" >0.00%</td>
      <td id="T_6ee67_row3_col2" class="data row3 col2" >4717926.00</td>
      <td id="T_6ee67_row3_col3" class="data row3 col3" >12.77</td>
      <td id="T_6ee67_row3_col4" class="data row3 col4" >11.00</td>
      <td id="T_6ee67_row3_col5" class="data row3 col5" >8.46</td>
      <td id="T_6ee67_row3_col6" class="data row3 col6" >1.00</td>
      <td id="T_6ee67_row3_col7" class="data row3 col7" >6.00</td>
      <td id="T_6ee67_row3_col8" class="data row3 col8" >19.00</td>
      <td id="T_6ee67_row3_col9" class="data row3 col9" >70.00</td>
      <td id="T_6ee67_row3_col10" class="data row3 col10" >1.77</td>
      <td id="T_6ee67_row3_col11" class="data row3 col11" >0.82</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_6ee67_row4_col0" class="data row4 col0" >stop_lat</td>
      <td id="T_6ee67_row4_col1" class="data row4 col1" >0.10%</td>
      <td id="T_6ee67_row4_col2" class="data row4 col2" >4713418.00</td>
      <td id="T_6ee67_row4_col3" class="data row4 col3" >47.38</td>
      <td id="T_6ee67_row4_col4" class="data row4 col4" >47.38</td>
      <td id="T_6ee67_row4_col5" class="data row4 col5" >0.02</td>
      <td id="T_6ee67_row4_col6" class="data row4 col6" >47.33</td>
      <td id="T_6ee67_row4_col7" class="data row4 col7" >47.37</td>
      <td id="T_6ee67_row4_col8" class="data row4 col8" >47.40</td>
      <td id="T_6ee67_row4_col9" class="data row4 col9" >47.45</td>
      <td id="T_6ee67_row4_col10" class="data row4 col10" >0.00</td>
      <td id="T_6ee67_row4_col11" class="data row4 col11" >0.70</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_6ee67_row5_col0" class="data row5 col0" >stop_lon</td>
      <td id="T_6ee67_row5_col1" class="data row5 col1" >0.10%</td>
      <td id="T_6ee67_row5_col2" class="data row5 col2" >4713418.00</td>
      <td id="T_6ee67_row5_col3" class="data row5 col3" >8.54</td>
      <td id="T_6ee67_row5_col4" class="data row5 col4" >8.54</td>
      <td id="T_6ee67_row5_col5" class="data row5 col5" >0.02</td>
      <td id="T_6ee67_row5_col6" class="data row5 col6" >8.44</td>
      <td id="T_6ee67_row5_col7" class="data row5 col7" >8.53</td>
      <td id="T_6ee67_row5_col8" class="data row5 col8" >8.55</td>
      <td id="T_6ee67_row5_col9" class="data row5 col9" >8.64</td>
      <td id="T_6ee67_row5_col10" class="data row5 col10" >0.00</td>
      <td id="T_6ee67_row5_col11" class="data row5 col11" >-0.53</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_6ee67_row6_col0" class="data row6 col0" >district_nr</td>
      <td id="T_6ee67_row6_col1" class="data row6 col1" >6.89%</td>
      <td id="T_6ee67_row6_col2" class="data row6 col2" >4392768.00</td>
      <td id="T_6ee67_row6_col3" class="data row6 col3" >5.24</td>
      <td id="T_6ee67_row6_col4" class="data row6 col4" >5.00</td>
      <td id="T_6ee67_row6_col5" class="data row6 col5" >3.42</td>
      <td id="T_6ee67_row6_col6" class="data row6 col6" >1.00</td>
      <td id="T_6ee67_row6_col7" class="data row6 col7" >2.00</td>
      <td id="T_6ee67_row6_col8" class="data row6 col8" >7.00</td>
      <td id="T_6ee67_row6_col9" class="data row6 col9" >12.00</td>
      <td id="T_6ee67_row6_col10" class="data row6 col10" >0.24</td>
      <td id="T_6ee67_row6_col11" class="data row6 col11" >0.40</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_6ee67_row7_col0" class="data row7 col0" >temperature</td>
      <td id="T_6ee67_row7_col1" class="data row7 col1" >0.35%</td>
      <td id="T_6ee67_row7_col2" class="data row7 col2" >4701342.00</td>
      <td id="T_6ee67_row7_col3" class="data row7 col3" >13.20</td>
      <td id="T_6ee67_row7_col4" class="data row7 col4" >12.48</td>
      <td id="T_6ee67_row7_col5" class="data row7 col5" >8.03</td>
      <td id="T_6ee67_row7_col6" class="data row7 col6" >-4.75</td>
      <td id="T_6ee67_row7_col7" class="data row7 col7" >7.16</td>
      <td id="T_6ee67_row7_col8" class="data row7 col8" >19.28</td>
      <td id="T_6ee67_row7_col9" class="data row7 col9" >35.80</td>
      <td id="T_6ee67_row7_col10" class="data row7 col10" >0.72</td>
      <td id="T_6ee67_row7_col11" class="data row7 col11" >0.22</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_6ee67_row8_col0" class="data row8 col0" >humidity</td>
      <td id="T_6ee67_row8_col1" class="data row8 col1" >0.35%</td>
      <td id="T_6ee67_row8_col2" class="data row8 col2" >4701342.00</td>
      <td id="T_6ee67_row8_col3" class="data row8 col3" >67.58</td>
      <td id="T_6ee67_row8_col4" class="data row8 col4" >70.61</td>
      <td id="T_6ee67_row8_col5" class="data row8 col5" >16.91</td>
      <td id="T_6ee67_row8_col6" class="data row8 col6" >18.58</td>
      <td id="T_6ee67_row8_col7" class="data row8 col7" >55.65</td>
      <td id="T_6ee67_row8_col8" class="data row8 col8" >81.19</td>
      <td id="T_6ee67_row8_col9" class="data row8 col9" >101.37</td>
      <td id="T_6ee67_row8_col10" class="data row8 col10" >-3.03</td>
      <td id="T_6ee67_row8_col11" class="data row8 col11" >-0.53</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_6ee67_row9_col0" class="data row9 col0" >rain_duration</td>
      <td id="T_6ee67_row9_col1" class="data row9 col1" >0.27%</td>
      <td id="T_6ee67_row9_col2" class="data row9 col2" >4705167.00</td>
      <td id="T_6ee67_row9_col3" class="data row9 col3" >5.92</td>
      <td id="T_6ee67_row9_col4" class="data row9 col4" >0.00</td>
      <td id="T_6ee67_row9_col5" class="data row9 col5" >15.81</td>
      <td id="T_6ee67_row9_col6" class="data row9 col6" >0.00</td>
      <td id="T_6ee67_row9_col7" class="data row9 col7" >0.00</td>
      <td id="T_6ee67_row9_col8" class="data row9 col8" >0.00</td>
      <td id="T_6ee67_row9_col9" class="data row9 col9" >60.00</td>
      <td id="T_6ee67_row9_col10" class="data row9 col10" >5.92</td>
      <td id="T_6ee67_row9_col11" class="data row9 col11" >2.67</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_6ee67_row10_col0" class="data row10 col0" >precipitation</td>
      <td id="T_6ee67_row10_col1" class="data row10 col1" >0.25%</td>
      <td id="T_6ee67_row10_col2" class="data row10 col2" >4706111.00</td>
      <td id="T_6ee67_row10_col3" class="data row10 col3" >0.12</td>
      <td id="T_6ee67_row10_col4" class="data row10 col4" >0.00</td>
      <td id="T_6ee67_row10_col5" class="data row10 col5" >0.60</td>
      <td id="T_6ee67_row10_col6" class="data row10 col6" >0.00</td>
      <td id="T_6ee67_row10_col7" class="data row10 col7" >0.00</td>
      <td id="T_6ee67_row10_col8" class="data row10 col8" >0.00</td>
      <td id="T_6ee67_row10_col9" class="data row10 col9" >23.90</td>
      <td id="T_6ee67_row10_col10" class="data row10 col10" >0.12</td>
      <td id="T_6ee67_row10_col11" class="data row10 col11" >11.89</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_6ee67_row11_col0" class="data row11 col0" >wind_speed</td>
      <td id="T_6ee67_row11_col1" class="data row11 col1" >0.29%</td>
      <td id="T_6ee67_row11_col2" class="data row11 col2" >4704260.00</td>
      <td id="T_6ee67_row11_col3" class="data row11 col3" >1.93</td>
      <td id="T_6ee67_row11_col4" class="data row11 col4" >1.74</td>
      <td id="T_6ee67_row11_col5" class="data row11 col5" >1.02</td>
      <td id="T_6ee67_row11_col6" class="data row11 col6" >0.25</td>
      <td id="T_6ee67_row11_col7" class="data row11 col7" >1.19</td>
      <td id="T_6ee67_row11_col8" class="data row11 col8" >2.44</td>
      <td id="T_6ee67_row11_col9" class="data row11 col9" >10.08</td>
      <td id="T_6ee67_row11_col10" class="data row11 col10" >0.19</td>
      <td id="T_6ee67_row11_col11" class="data row11 col11" >1.31</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_6ee67_row12_col0" class="data row12 col0" >global_radiation</td>
      <td id="T_6ee67_row12_col1" class="data row12 col1" >0.30%</td>
      <td id="T_6ee67_row12_col2" class="data row12 col2" >4703865.00</td>
      <td id="T_6ee67_row12_col3" class="data row12 col3" >185.12</td>
      <td id="T_6ee67_row12_col4" class="data row12 col4" >65.46</td>
      <td id="T_6ee67_row12_col5" class="data row12 col5" >243.26</td>
      <td id="T_6ee67_row12_col6" class="data row12 col6" >0.01</td>
      <td id="T_6ee67_row12_col7" class="data row12 col7" >0.03</td>
      <td id="T_6ee67_row12_col8" class="data row12 col8" >296.58</td>
      <td id="T_6ee67_row12_col9" class="data row12 col9" >1041.18</td>
      <td id="T_6ee67_row12_col10" class="data row12 col10" >119.66</td>
      <td id="T_6ee67_row12_col11" class="data row12 col11" >1.34</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_6ee67_row13_col0" class="data row13 col0" >flood_intensity</td>
      <td id="T_6ee67_row13_col1" class="data row13 col1" >0.16%</td>
      <td id="T_6ee67_row13_col2" class="data row13 col2" >4710582.00</td>
      <td id="T_6ee67_row13_col3" class="data row13 col3" >0.07</td>
      <td id="T_6ee67_row13_col4" class="data row13 col4" >0.00</td>
      <td id="T_6ee67_row13_col5" class="data row13 col5" >0.48</td>
      <td id="T_6ee67_row13_col6" class="data row13 col6" >0.00</td>
      <td id="T_6ee67_row13_col7" class="data row13 col7" >0.00</td>
      <td id="T_6ee67_row13_col8" class="data row13 col8" >0.00</td>
      <td id="T_6ee67_row13_col9" class="data row13 col9" >11.00</td>
      <td id="T_6ee67_row13_col10" class="data row13 col10" >0.07</td>
      <td id="T_6ee67_row13_col11" class="data row13 col11" >14.87</td>
    </tr>
    <tr>
      <th id="T_6ee67_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_6ee67_row14_col0" class="data row14 col0" >event_size</td>
      <td id="T_6ee67_row14_col1" class="data row14 col1" >78.52%</td>
      <td id="T_6ee67_row14_col2" class="data row14 col2" >1013197.00</td>
      <td id="T_6ee67_row14_col3" class="data row14 col3" >1.46</td>
      <td id="T_6ee67_row14_col4" class="data row14 col4" >1.00</td>
      <td id="T_6ee67_row14_col5" class="data row14 col5" >0.57</td>
      <td id="T_6ee67_row14_col6" class="data row14 col6" >1.00</td>
      <td id="T_6ee67_row14_col7" class="data row14 col7" >1.00</td>
      <td id="T_6ee67_row14_col8" class="data row14 col8" >2.00</td>
      <td id="T_6ee67_row14_col9" class="data row14 col9" >3.00</td>
      <td id="T_6ee67_row14_col10" class="data row14 col10" >0.46</td>
      <td id="T_6ee67_row14_col11" class="data row14 col11" >0.77</td>
    </tr>
  </tbody>
</table>



    
    [1m[38;2;52;97;141m───  CATEGORICAL STATS  ──────────────────────────────────────[0m



<style type="text/css">
#T_862ee thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_862ee td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_862ee tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_862ee tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_862ee tr:hover td {
  background-color: #eef3f8;
}
#T_862ee_row0_col0, #T_862ee_row0_col4, #T_862ee_row1_col0, #T_862ee_row1_col4, #T_862ee_row2_col0, #T_862ee_row2_col4, #T_862ee_row3_col0, #T_862ee_row3_col4, #T_862ee_row4_col0, #T_862ee_row4_col4, #T_862ee_row5_col0, #T_862ee_row5_col4, #T_862ee_row6_col0, #T_862ee_row6_col4, #T_862ee_row7_col0, #T_862ee_row7_col4 {
  text-align: left;
}
#T_862ee_row0_col1, #T_862ee_row0_col2, #T_862ee_row0_col3, #T_862ee_row0_col5, #T_862ee_row0_col6, #T_862ee_row1_col1, #T_862ee_row1_col2, #T_862ee_row1_col3, #T_862ee_row1_col5, #T_862ee_row1_col6, #T_862ee_row2_col1, #T_862ee_row2_col2, #T_862ee_row2_col3, #T_862ee_row2_col5, #T_862ee_row2_col6, #T_862ee_row3_col1, #T_862ee_row3_col3, #T_862ee_row3_col5, #T_862ee_row3_col6, #T_862ee_row4_col1, #T_862ee_row4_col3, #T_862ee_row4_col5, #T_862ee_row4_col6, #T_862ee_row5_col1, #T_862ee_row5_col3, #T_862ee_row5_col5, #T_862ee_row5_col6, #T_862ee_row6_col1, #T_862ee_row6_col3, #T_862ee_row6_col5, #T_862ee_row6_col6, #T_862ee_row7_col1, #T_862ee_row7_col3, #T_862ee_row7_col5, #T_862ee_row7_col6 {
  text-align: right;
}
#T_862ee_row3_col2, #T_862ee_row4_col2, #T_862ee_row5_col2, #T_862ee_row6_col2, #T_862ee_row7_col2 {
  text-align: right;
  color: #de425b;
  font-weight: 500;
}
</style>
<table id="T_862ee">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_862ee_level0_col0" class="col_heading level0 col0" >column</th>
      <th id="T_862ee_level0_col1" class="col_heading level0 col1" >missing_pct</th>
      <th id="T_862ee_level0_col2" class="col_heading level0 col2" >missing_cnt</th>
      <th id="T_862ee_level0_col3" class="col_heading level0 col3" >uniques</th>
      <th id="T_862ee_level0_col4" class="col_heading level0 col4" >top_value</th>
      <th id="T_862ee_level0_col5" class="col_heading level0 col5" >top_value_cnt</th>
      <th id="T_862ee_level0_col6" class="col_heading level0 col6" >top_value_freq_pct</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_862ee_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_862ee_row0_col0" class="data row0 col0" >trip_id</td>
      <td id="T_862ee_row0_col1" class="data row0 col1" >0.00%</td>
      <td id="T_862ee_row0_col2" class="data row0 col2" >0</td>
      <td id="T_862ee_row0_col3" class="data row0 col3" >321006</td>
      <td id="T_862ee_row0_col4" class="data row0 col4" >85:3849:62691-08009-1</td>
      <td id="T_862ee_row0_col5" class="data row0 col5" >460</td>
      <td id="T_862ee_row0_col6" class="data row0 col6" >0.01%</td>
    </tr>
    <tr>
      <th id="T_862ee_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_862ee_row1_col0" class="data row1 col0" >line_name</td>
      <td id="T_862ee_row1_col1" class="data row1 col1" >0.00%</td>
      <td id="T_862ee_row1_col2" class="data row1 col2" >0</td>
      <td id="T_862ee_row1_col3" class="data row1 col3" >18</td>
      <td id="T_862ee_row1_col4" class="data row1 col4" >11</td>
      <td id="T_862ee_row1_col5" class="data row1 col5" >457773</td>
      <td id="T_862ee_row1_col6" class="data row1 col6" >9.70%</td>
    </tr>
    <tr>
      <th id="T_862ee_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_862ee_row2_col0" class="data row2 col0" >canceled</td>
      <td id="T_862ee_row2_col1" class="data row2 col1" >0.00%</td>
      <td id="T_862ee_row2_col2" class="data row2 col2" >0</td>
      <td id="T_862ee_row2_col3" class="data row2 col3" >2</td>
      <td id="T_862ee_row2_col4" class="data row2 col4" >False</td>
      <td id="T_862ee_row2_col5" class="data row2 col5" >4490484</td>
      <td id="T_862ee_row2_col6" class="data row2 col6" >95.18%</td>
    </tr>
    <tr>
      <th id="T_862ee_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_862ee_row3_col0" class="data row3 col0" >stop_name</td>
      <td id="T_862ee_row3_col1" class="data row3 col1" >0.10%</td>
      <td id="T_862ee_row3_col2" class="data row3 col2" >4508</td>
      <td id="T_862ee_row3_col3" class="data row3 col3" >223</td>
      <td id="T_862ee_row3_col4" class="data row3 col4" >Zürich, Paradeplatz</td>
      <td id="T_862ee_row3_col5" class="data row3 col5" >98184</td>
      <td id="T_862ee_row3_col6" class="data row3 col6" >2.08%</td>
    </tr>
    <tr>
      <th id="T_862ee_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_862ee_row4_col0" class="data row4 col0" >district_name</td>
      <td id="T_862ee_row4_col1" class="data row4 col1" >6.89%</td>
      <td id="T_862ee_row4_col2" class="data row4 col2" >325158</td>
      <td id="T_862ee_row4_col3" class="data row4 col3" >12</td>
      <td id="T_862ee_row4_col4" class="data row4 col4" >Kreis 1</td>
      <td id="T_862ee_row4_col5" class="data row4 col5" >955357</td>
      <td id="T_862ee_row4_col6" class="data row4 col6" >20.25%</td>
    </tr>
    <tr>
      <th id="T_862ee_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_862ee_row5_col0" class="data row5 col0" >event_name</td>
      <td id="T_862ee_row5_col1" class="data row5 col1" >78.52%</td>
      <td id="T_862ee_row5_col2" class="data row5 col2" >3704729</td>
      <td id="T_862ee_row5_col3" class="data row5 col3" >72</td>
      <td id="T_862ee_row5_col4" class="data row5 col4" >Zürich Design Weeks</td>
      <td id="T_862ee_row5_col5" class="data row5 col5" >54729</td>
      <td id="T_862ee_row5_col6" class="data row5 col6" >1.16%</td>
    </tr>
    <tr>
      <th id="T_862ee_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_862ee_row6_col0" class="data row6 col0" >event_type</td>
      <td id="T_862ee_row6_col1" class="data row6 col1" >78.52%</td>
      <td id="T_862ee_row6_col2" class="data row6 col2" >3704729</td>
      <td id="T_862ee_row6_col3" class="data row6 col3" >9</td>
      <td id="T_862ee_row6_col4" class="data row6 col4" >Super League</td>
      <td id="T_862ee_row6_col5" class="data row6 col5" >433438</td>
      <td id="T_862ee_row6_col6" class="data row6 col6" >9.19%</td>
    </tr>
    <tr>
      <th id="T_862ee_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_862ee_row7_col0" class="data row7 col0" >event_location</td>
      <td id="T_862ee_row7_col1" class="data row7 col1" >78.52%</td>
      <td id="T_862ee_row7_col2" class="data row7 col2" >3704729</td>
      <td id="T_862ee_row7_col3" class="data row7 col3" >12</td>
      <td id="T_862ee_row7_col4" class="data row7 col4" >Letzigrund</td>
      <td id="T_862ee_row7_col5" class="data row7 col5" >467976</td>
      <td id="T_862ee_row7_col6" class="data row7 col6" >9.92%</td>
    </tr>
  </tbody>
</table>




```python
# --- Polars insights

section_header('DIMENSIONS')

schema = lf.collect_schema()

# Anzahl der Spalten (sofort verfügbar)
print(f"Anzahl Spalten: {len(schema)}")

# Zeilenanzahl (erfordert einen schnellen Scan der Metadaten)
print(f"Anzahl Zeilen: {lf.select(pl.len()).collect().item()}")

# Null-Counts pro Spalte — aggregiert
print("Anzahl NaN:")
display(lf.select(pl.all().null_count()).collect())

section_header('DTYPES')

for col_name, dtype in schema.items():
    print(f"{col_name:<20} | Typ: {dtype}")

section_header('NUMERIC STATS')

# Umfassende Statistiken für alle Spalten
display( lf.describe())

section_header('CATEGORICAL STATS ')

# Helper-Funktion aus utils_polars.py
get_categorical_stats(lf_eda)

```

    
    [1m[38;2;52;97;141m───  DIMENSIONS  ─────────────────────────────────────────────[0m
    Anzahl Spalten: 26
    Anzahl Zeilen: 94358531
    Anzahl NaN:



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (1, 26)</small><table border="1" class="dataframe"><thead><tr><th>operating_date</th><th>trip_id</th><th>line_name</th><th>bpuic</th><th>arrival_schedule</th><th>arrival_delay</th><th>departure_schedule</th><th>departure_delay</th><th>canceled</th><th>stop_sequence</th><th>stop_name</th><th>stop_lat</th><th>stop_lon</th><th>district_nr</th><th>district_name</th><th>temperature</th><th>humidity</th><th>rain_duration</th><th>precipitation</th><th>wind_speed</th><th>global_radiation</th><th>flood_intensity</th><th>event_name</th><th>event_type</th><th>event_size</th><th>event_location</th></tr><tr><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td></tr></thead><tbody><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>136437</td><td>225018</td><td>136148</td><td>228075</td><td>0</td><td>0</td><td>91219</td><td>91219</td><td>91219</td><td>6494934</td><td>6494934</td><td>329902</td><td>329902</td><td>252491</td><td>236841</td><td>270230</td><td>278078</td><td>144937</td><td>74118488</td><td>74118488</td><td>74118488</td><td>74118488</td></tr></tbody></table></div>


    
    [1m[38;2;52;97;141m───  DTYPES  ─────────────────────────────────────────────────[0m
    operating_date       | Typ: Date
    trip_id              | Typ: String
    line_name            | Typ: Categorical
    bpuic                | Typ: Int32
    arrival_schedule     | Typ: Datetime(time_unit='us', time_zone=None)
    arrival_delay        | Typ: Float32
    departure_schedule   | Typ: Datetime(time_unit='us', time_zone=None)
    departure_delay      | Typ: Float32
    canceled             | Typ: Boolean
    stop_sequence        | Typ: Int16
    stop_name            | Typ: Categorical
    stop_lat             | Typ: Float32
    stop_lon             | Typ: Float32
    district_nr          | Typ: Int8
    district_name        | Typ: Categorical
    temperature          | Typ: Float32
    humidity             | Typ: Float32
    rain_duration        | Typ: Float32
    precipitation        | Typ: Float32
    wind_speed           | Typ: Float32
    global_radiation     | Typ: Float32
    flood_intensity      | Typ: Int16
    event_name           | Typ: Categorical
    event_type           | Typ: Categorical
    event_size           | Typ: Int8
    event_location       | Typ: Categorical
    
    [1m[38;2;52;97;141m───  NUMERIC STATS  ──────────────────────────────────────────[0m



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (9, 27)</small><table border="1" class="dataframe"><thead><tr><th>statistic</th><th>operating_date</th><th>trip_id</th><th>line_name</th><th>bpuic</th><th>arrival_schedule</th><th>arrival_delay</th><th>departure_schedule</th><th>departure_delay</th><th>canceled</th><th>stop_sequence</th><th>stop_name</th><th>stop_lat</th><th>stop_lon</th><th>district_nr</th><th>district_name</th><th>temperature</th><th>humidity</th><th>rain_duration</th><th>precipitation</th><th>wind_speed</th><th>global_radiation</th><th>flood_intensity</th><th>event_name</th><th>event_type</th><th>event_size</th><th>event_location</th></tr><tr><td>str</td><td>str</td><td>str</td><td>str</td><td>f64</td><td>str</td><td>f64</td><td>str</td><td>f64</td><td>f64</td><td>f64</td><td>str</td><td>f64</td><td>f64</td><td>f64</td><td>str</td><td>f64</td><td>f64</td><td>f64</td><td>f64</td><td>f64</td><td>f64</td><td>f64</td><td>str</td><td>str</td><td>f64</td><td>str</td></tr></thead><tbody><tr><td>&quot;count&quot;</td><td>&quot;94358531&quot;</td><td>&quot;94358531&quot;</td><td>&quot;94358531&quot;</td><td>9.4358531e7</td><td>&quot;94222094&quot;</td><td>9.4133513e7</td><td>&quot;94222383&quot;</td><td>9.4130456e7</td><td>9.4358531e7</td><td>9.4358531e7</td><td>&quot;94267312&quot;</td><td>9.4267312e7</td><td>9.4267312e7</td><td>8.7863597e7</td><td>&quot;87863597&quot;</td><td>9.4028629e7</td><td>9.4028629e7</td><td>9.410604e7</td><td>9.412169e7</td><td>9.4088301e7</td><td>9.4080453e7</td><td>9.4213594e7</td><td>&quot;20240043&quot;</td><td>&quot;20240043&quot;</td><td>2.0240043e7</td><td>&quot;20240043&quot;</td></tr><tr><td>&quot;null_count&quot;</td><td>&quot;0&quot;</td><td>&quot;0&quot;</td><td>&quot;0&quot;</td><td>0.0</td><td>&quot;136437&quot;</td><td>225018.0</td><td>&quot;136148&quot;</td><td>228075.0</td><td>0.0</td><td>0.0</td><td>&quot;91219&quot;</td><td>91219.0</td><td>91219.0</td><td>6.494934e6</td><td>&quot;6494934&quot;</td><td>329902.0</td><td>329902.0</td><td>252491.0</td><td>236841.0</td><td>270230.0</td><td>278078.0</td><td>144937.0</td><td>&quot;74118488&quot;</td><td>&quot;74118488&quot;</td><td>7.4118488e7</td><td>&quot;74118488&quot;</td></tr><tr><td>&quot;mean&quot;</td><td>&quot;2024-07-01 14:25:47.805181&quot;</td><td>null</td><td>null</td><td>9.4085e6</td><td>&quot;2024-07-02 12:04:42.307297&quot;</td><td>56.080585</td><td>&quot;2024-07-02 12:03:55.943705&quot;</td><td>61.69416</td><td>0.04824</td><td>12.767443</td><td>null</td><td>47.383392</td><td>8.537123</td><td>5.244116</td><td>null</td><td>13.205679</td><td>67.584198</td><td>5.918949</td><td>0.117638</td><td>1.930183</td><td>185.243271</td><td>0.068817</td><td>null</td><td>null</td><td>1.462097</td><td>null</td></tr><tr><td>&quot;std&quot;</td><td>null</td><td>null</td><td>null</td><td>2.6408e7</td><td>null</td><td>107.901344</td><td>null</td><td>108.913589</td><td>null</td><td>8.466594</td><td>null</td><td>0.018723</td><td>0.023162</td><td>3.41483</td><td>null</td><td>8.027277</td><td>16.910362</td><td>15.813949</td><td>0.594282</td><td>1.020491</td><td>243.392288</td><td>0.47838</td><td>null</td><td>null</td><td>0.567754</td><td>null</td></tr><tr><td>&quot;min&quot;</td><td>&quot;2023-01-01&quot;</td><td>&quot;85:3849:100000-03007-1&quot;</td><td>null</td><td>8.502572e6</td><td>&quot;2023-01-01 04:37:00&quot;</td><td>-35964.0</td><td>&quot;2023-01-01 04:37:00&quot;</td><td>-35956.0</td><td>0.0</td><td>1.0</td><td>null</td><td>47.325005</td><td>8.444579</td><td>1.0</td><td>null</td><td>-4.75</td><td>18.58</td><td>0.0</td><td>0.0</td><td>0.25</td><td>0.01</td><td>0.0</td><td>null</td><td>null</td><td>1.0</td><td>null</td></tr><tr><td>&quot;25%&quot;</td><td>&quot;2023-09-28&quot;</td><td>null</td><td>null</td><td>8.59106e6</td><td>&quot;2023-09-28 20:45:00&quot;</td><td>12.0</td><td>&quot;2023-09-28 20:44:00&quot;</td><td>16.0</td><td>null</td><td>6.0</td><td>null</td><td>47.369728</td><td>8.525832</td><td>2.0</td><td>null</td><td>7.16</td><td>55.66</td><td>0.0</td><td>0.0</td><td>1.19</td><td>0.03</td><td>0.0</td><td>null</td><td>null</td><td>1.0</td><td>null</td></tr><tr><td>&quot;50%&quot;</td><td>&quot;2024-06-28&quot;</td><td>null</td><td>null</td><td>8.59122e6</td><td>&quot;2024-06-28 16:52:00&quot;</td><td>42.0</td><td>&quot;2024-06-28 16:52:00&quot;</td><td>47.0</td><td>null</td><td>11.0</td><td>null</td><td>47.379242</td><td>8.539834</td><td>5.0</td><td>null</td><td>12.48</td><td>70.610001</td><td>0.0</td><td>0.0</td><td>1.74</td><td>65.639999</td><td>0.0</td><td>null</td><td>null</td><td>1.0</td><td>null</td></tr><tr><td>&quot;75%&quot;</td><td>&quot;2025-04-05&quot;</td><td>null</td><td>null</td><td>8.591335e6</td><td>&quot;2025-04-06 00:06:00&quot;</td><td>81.0</td><td>&quot;2025-04-06 00:07:00&quot;</td><td>88.0</td><td>null</td><td>19.0</td><td>null</td><td>47.395756</td><td>8.548299</td><td>7.0</td><td>null</td><td>19.280001</td><td>81.199997</td><td>0.0</td><td>0.0</td><td>2.44</td><td>296.690002</td><td>0.0</td><td>null</td><td>null</td><td>2.0</td><td>null</td></tr><tr><td>&quot;max&quot;</td><td>&quot;2025-12-31&quot;</td><td>&quot;ch:1:sjyid:100648:plan:fffdec7…</td><td>null</td><td>8.59600701e8</td><td>&quot;2026-01-01 04:46:00&quot;</td><td>35043.0</td><td>&quot;2026-01-01 04:45:00&quot;</td><td>35044.0</td><td>1.0</td><td>77.0</td><td>null</td><td>47.452236</td><td>8.647987</td><td>12.0</td><td>null</td><td>35.799999</td><td>101.370003</td><td>60.0</td><td>23.9</td><td>10.08</td><td>1041.180054</td><td>11.0</td><td>null</td><td>null</td><td>3.0</td><td>null</td></tr></tbody></table></div>


    
    [1m[38;2;52;97;141m───  CATEGORICAL STATS   ─────────────────────────────────────[0m





<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (8, 5)</small><table border="1" class="dataframe"><thead><tr><th>column</th><th>missing_cnt</th><th>unique</th><th>top_value</th><th>top_value_cnt</th></tr><tr><td>str</td><td>str</td><td>str</td><td>str</td><td>str</td></tr></thead><tbody><tr><td>&quot;trip_id&quot;</td><td>&quot;0&quot;</td><td>&quot;321006&quot;</td><td>&quot;85:3849:62691-08009-1&quot;</td><td>&quot;460&quot;</td></tr><tr><td>&quot;line_name&quot;</td><td>&quot;0&quot;</td><td>&quot;18&quot;</td><td>&quot;11&quot;</td><td>&quot;457773&quot;</td></tr><tr><td>&quot;canceled&quot;</td><td>&quot;0&quot;</td><td>&quot;2&quot;</td><td>&quot;false&quot;</td><td>&quot;4490484&quot;</td></tr><tr><td>&quot;stop_name&quot;</td><td>&quot;4508&quot;</td><td>&quot;224&quot;</td><td>&quot;Zürich, Paradeplatz&quot;</td><td>&quot;98184&quot;</td></tr><tr><td>&quot;district_name&quot;</td><td>&quot;325158&quot;</td><td>&quot;13&quot;</td><td>&quot;Kreis 1&quot;</td><td>&quot;955357&quot;</td></tr><tr><td>&quot;event_name&quot;</td><td>&quot;3704729&quot;</td><td>&quot;73&quot;</td><td>null</td><td>&quot;0&quot;</td></tr><tr><td>&quot;event_type&quot;</td><td>&quot;3704729&quot;</td><td>&quot;10&quot;</td><td>null</td><td>&quot;0&quot;</td></tr><tr><td>&quot;event_location&quot;</td><td>&quot;3704729&quot;</td><td>&quot;13&quot;</td><td>null</td><td>&quot;0&quot;</td></tr></tbody></table></div>



### Data Completeness



**Quality Check & Duplicates & Missing Values**


```python
# --- Pandas with wgnd.inspect_missing
# --- Und Missing Data Pattern  Heatmap  /// ca. 5 min. 

inspect_missing(df_eda)
```

    
    [1m[38;2;52;97;141m───  MISSING VALUES  ─────────────────────────────────────────[0m



<style type="text/css">
#T_f43b6 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_f43b6 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_f43b6 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_f43b6 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_f43b6 tr:hover td {
  background-color: #eef3f8;
}
#T_f43b6_row0_col0, #T_f43b6_row1_col0, #T_f43b6_row2_col0, #T_f43b6_row3_col0, #T_f43b6_row4_col0, #T_f43b6_row5_col0, #T_f43b6_row6_col0, #T_f43b6_row7_col0, #T_f43b6_row8_col0, #T_f43b6_row9_col0, #T_f43b6_row10_col0, #T_f43b6_row11_col0, #T_f43b6_row12_col0, #T_f43b6_row13_col0, #T_f43b6_row14_col0, #T_f43b6_row15_col0, #T_f43b6_row16_col0, #T_f43b6_row17_col0, #T_f43b6_row18_col0, #T_f43b6_row19_col0 {
  text-align: left;
}
#T_f43b6_row0_col1, #T_f43b6_row1_col1, #T_f43b6_row2_col1, #T_f43b6_row3_col1, #T_f43b6_row4_col1, #T_f43b6_row5_col1, #T_f43b6_row6_col1, #T_f43b6_row7_col1, #T_f43b6_row8_col1, #T_f43b6_row9_col1, #T_f43b6_row10_col1, #T_f43b6_row11_col1, #T_f43b6_row12_col1, #T_f43b6_row13_col1, #T_f43b6_row14_col1, #T_f43b6_row15_col1, #T_f43b6_row16_col1, #T_f43b6_row17_col1, #T_f43b6_row18_col1, #T_f43b6_row19_col1 {
  text-align: right;
  color: #de425b;
  font-weight: 500;
}
#T_f43b6_row0_col2, #T_f43b6_row1_col2, #T_f43b6_row2_col2, #T_f43b6_row3_col2, #T_f43b6_row4_col2, #T_f43b6_row5_col2, #T_f43b6_row6_col2, #T_f43b6_row7_col2, #T_f43b6_row8_col2, #T_f43b6_row9_col2, #T_f43b6_row10_col2, #T_f43b6_row11_col2, #T_f43b6_row12_col2, #T_f43b6_row13_col2, #T_f43b6_row14_col2, #T_f43b6_row15_col2, #T_f43b6_row16_col2, #T_f43b6_row17_col2, #T_f43b6_row18_col2, #T_f43b6_row19_col2 {
  text-align: right;
}
</style>
<table id="T_f43b6">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_f43b6_level0_col0" class="col_heading level0 col0" >column</th>
      <th id="T_f43b6_level0_col1" class="col_heading level0 col1" >missing_cnt</th>
      <th id="T_f43b6_level0_col2" class="col_heading level0 col2" >missing_pct</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_f43b6_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_f43b6_row0_col0" class="data row0 col0" >event_location</td>
      <td id="T_f43b6_row0_col1" class="data row0 col1" >3704729</td>
      <td id="T_f43b6_row0_col2" class="data row0 col2" >78.52%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_f43b6_row1_col0" class="data row1 col0" >event_size</td>
      <td id="T_f43b6_row1_col1" class="data row1 col1" >3704729</td>
      <td id="T_f43b6_row1_col2" class="data row1 col2" >78.52%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_f43b6_row2_col0" class="data row2 col0" >event_type</td>
      <td id="T_f43b6_row2_col1" class="data row2 col1" >3704729</td>
      <td id="T_f43b6_row2_col2" class="data row2 col2" >78.52%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_f43b6_row3_col0" class="data row3 col0" >event_name</td>
      <td id="T_f43b6_row3_col1" class="data row3 col1" >3704729</td>
      <td id="T_f43b6_row3_col2" class="data row3 col2" >78.52%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_f43b6_row4_col0" class="data row4 col0" >district_nr</td>
      <td id="T_f43b6_row4_col1" class="data row4 col1" >325158</td>
      <td id="T_f43b6_row4_col2" class="data row4 col2" >6.89%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_f43b6_row5_col0" class="data row5 col0" >district_name</td>
      <td id="T_f43b6_row5_col1" class="data row5 col1" >325158</td>
      <td id="T_f43b6_row5_col2" class="data row5 col2" >6.89%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_f43b6_row6_col0" class="data row6 col0" >temperature</td>
      <td id="T_f43b6_row6_col1" class="data row6 col1" >16584</td>
      <td id="T_f43b6_row6_col2" class="data row6 col2" >0.35%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_f43b6_row7_col0" class="data row7 col0" >humidity</td>
      <td id="T_f43b6_row7_col1" class="data row7 col1" >16584</td>
      <td id="T_f43b6_row7_col2" class="data row7 col2" >0.35%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_f43b6_row8_col0" class="data row8 col0" >global_radiation</td>
      <td id="T_f43b6_row8_col1" class="data row8 col1" >14061</td>
      <td id="T_f43b6_row8_col2" class="data row8 col2" >0.30%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_f43b6_row9_col0" class="data row9 col0" >wind_speed</td>
      <td id="T_f43b6_row9_col1" class="data row9 col1" >13666</td>
      <td id="T_f43b6_row9_col2" class="data row9 col2" >0.29%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_f43b6_row10_col0" class="data row10 col0" >rain_duration</td>
      <td id="T_f43b6_row10_col1" class="data row10 col1" >12759</td>
      <td id="T_f43b6_row10_col2" class="data row10 col2" >0.27%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_f43b6_row11_col0" class="data row11 col0" >precipitation</td>
      <td id="T_f43b6_row11_col1" class="data row11 col1" >11815</td>
      <td id="T_f43b6_row11_col2" class="data row11 col2" >0.25%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_f43b6_row12_col0" class="data row12 col0" >departure_delay</td>
      <td id="T_f43b6_row12_col1" class="data row12 col1" >11286</td>
      <td id="T_f43b6_row12_col2" class="data row12 col2" >0.24%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_f43b6_row13_col0" class="data row13 col0" >arrival_delay</td>
      <td id="T_f43b6_row13_col1" class="data row13 col1" >11320</td>
      <td id="T_f43b6_row13_col2" class="data row13 col2" >0.24%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_f43b6_row14_col0" class="data row14 col0" >flood_intensity</td>
      <td id="T_f43b6_row14_col1" class="data row14 col1" >7344</td>
      <td id="T_f43b6_row14_col2" class="data row14 col2" >0.16%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_f43b6_row15_col0" class="data row15 col0" >arrival_schedule</td>
      <td id="T_f43b6_row15_col1" class="data row15 col1" >6906</td>
      <td id="T_f43b6_row15_col2" class="data row15 col2" >0.15%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_f43b6_row16_col0" class="data row16 col0" >departure_schedule</td>
      <td id="T_f43b6_row16_col1" class="data row16 col1" >6764</td>
      <td id="T_f43b6_row16_col2" class="data row16 col2" >0.14%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_f43b6_row17_col0" class="data row17 col0" >stop_lat</td>
      <td id="T_f43b6_row17_col1" class="data row17 col1" >4508</td>
      <td id="T_f43b6_row17_col2" class="data row17 col2" >0.10%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_f43b6_row18_col0" class="data row18 col0" >stop_lon</td>
      <td id="T_f43b6_row18_col1" class="data row18 col1" >4508</td>
      <td id="T_f43b6_row18_col2" class="data row18 col2" >0.10%</td>
    </tr>
    <tr>
      <th id="T_f43b6_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_f43b6_row19_col0" class="data row19 col0" >stop_name</td>
      <td id="T_f43b6_row19_col1" class="data row19 col1" >4508</td>
      <td id="T_f43b6_row19_col2" class="data row19 col2" >0.10%</td>
    </tr>
  </tbody>
</table>




    
![png](01_exploration_files/01_exploration_19_2.png)
    





<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>column</th>
      <th>missing_cnt</th>
      <th>missing_pct</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>event_location</td>
      <td>3704729</td>
      <td>78.52</td>
    </tr>
    <tr>
      <th>1</th>
      <td>event_size</td>
      <td>3704729</td>
      <td>78.52</td>
    </tr>
    <tr>
      <th>2</th>
      <td>event_type</td>
      <td>3704729</td>
      <td>78.52</td>
    </tr>
    <tr>
      <th>3</th>
      <td>event_name</td>
      <td>3704729</td>
      <td>78.52</td>
    </tr>
    <tr>
      <th>4</th>
      <td>district_nr</td>
      <td>325158</td>
      <td>6.89</td>
    </tr>
    <tr>
      <th>5</th>
      <td>district_name</td>
      <td>325158</td>
      <td>6.89</td>
    </tr>
    <tr>
      <th>6</th>
      <td>temperature</td>
      <td>16584</td>
      <td>0.35</td>
    </tr>
    <tr>
      <th>7</th>
      <td>humidity</td>
      <td>16584</td>
      <td>0.35</td>
    </tr>
    <tr>
      <th>8</th>
      <td>global_radiation</td>
      <td>14061</td>
      <td>0.30</td>
    </tr>
    <tr>
      <th>9</th>
      <td>wind_speed</td>
      <td>13666</td>
      <td>0.29</td>
    </tr>
    <tr>
      <th>10</th>
      <td>rain_duration</td>
      <td>12759</td>
      <td>0.27</td>
    </tr>
    <tr>
      <th>11</th>
      <td>precipitation</td>
      <td>11815</td>
      <td>0.25</td>
    </tr>
    <tr>
      <th>12</th>
      <td>departure_delay</td>
      <td>11286</td>
      <td>0.24</td>
    </tr>
    <tr>
      <th>13</th>
      <td>arrival_delay</td>
      <td>11320</td>
      <td>0.24</td>
    </tr>
    <tr>
      <th>14</th>
      <td>flood_intensity</td>
      <td>7344</td>
      <td>0.16</td>
    </tr>
    <tr>
      <th>15</th>
      <td>arrival_schedule</td>
      <td>6906</td>
      <td>0.15</td>
    </tr>
    <tr>
      <th>16</th>
      <td>departure_schedule</td>
      <td>6764</td>
      <td>0.14</td>
    </tr>
    <tr>
      <th>17</th>
      <td>stop_lat</td>
      <td>4508</td>
      <td>0.10</td>
    </tr>
    <tr>
      <th>18</th>
      <td>stop_lon</td>
      <td>4508</td>
      <td>0.10</td>
    </tr>
    <tr>
      <th>19</th>
      <td>stop_name</td>
      <td>4508</td>
      <td>0.10</td>
    </tr>
  </tbody>
</table>
</div>




```python
# --- Polars insights for missing values

section_header('Missing Values')


# Null-Counts pro Spalte — aggregiert
print("Anzahl NaN:")
display(lf.select(pl.all().null_count()).collect())

total_items = lf.select(pl.len()).collect().item()

result_missings = (
    lf
    .select(pl.all().null_count())
    .collect()
    .transpose(include_header=True, column_names=["null_count"])
    .with_columns(
        (pl.col("null_count") / total_items * 100).round(2).alias("pct")
    )
)

display(result_missings)

```

    
    [1m[38;2;52;97;141m───  MISSING VALUES  ─────────────────────────────────────────[0m
    Anzahl NaN:



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (1, 26)</small><table border="1" class="dataframe"><thead><tr><th>operating_date</th><th>trip_id</th><th>line_name</th><th>bpuic</th><th>arrival_schedule</th><th>arrival_delay</th><th>departure_schedule</th><th>departure_delay</th><th>canceled</th><th>stop_sequence</th><th>stop_name</th><th>stop_lat</th><th>stop_lon</th><th>district_nr</th><th>district_name</th><th>temperature</th><th>humidity</th><th>rain_duration</th><th>precipitation</th><th>wind_speed</th><th>global_radiation</th><th>flood_intensity</th><th>event_name</th><th>event_type</th><th>event_size</th><th>event_location</th></tr><tr><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td></tr></thead><tbody><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>136437</td><td>225018</td><td>136148</td><td>228075</td><td>0</td><td>0</td><td>91219</td><td>91219</td><td>91219</td><td>6494934</td><td>6494934</td><td>329902</td><td>329902</td><td>252491</td><td>236841</td><td>270230</td><td>278078</td><td>144937</td><td>74118488</td><td>74118488</td><td>74118488</td><td>74118488</td></tr></tbody></table></div>



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (26, 3)</small><table border="1" class="dataframe"><thead><tr><th>column</th><th>null_count</th><th>pct</th></tr><tr><td>str</td><td>u32</td><td>f64</td></tr></thead><tbody><tr><td>&quot;operating_date&quot;</td><td>0</td><td>0.0</td></tr><tr><td>&quot;trip_id&quot;</td><td>0</td><td>0.0</td></tr><tr><td>&quot;line_name&quot;</td><td>0</td><td>0.0</td></tr><tr><td>&quot;bpuic&quot;</td><td>0</td><td>0.0</td></tr><tr><td>&quot;arrival_schedule&quot;</td><td>136437</td><td>0.14</td></tr><tr><td>&hellip;</td><td>&hellip;</td><td>&hellip;</td></tr><tr><td>&quot;flood_intensity&quot;</td><td>144937</td><td>0.15</td></tr><tr><td>&quot;event_name&quot;</td><td>74118488</td><td>78.55</td></tr><tr><td>&quot;event_type&quot;</td><td>74118488</td><td>78.55</td></tr><tr><td>&quot;event_size&quot;</td><td>74118488</td><td>78.55</td></tr><tr><td>&quot;event_location&quot;</td><td>74118488</td><td>78.55</td></tr></tbody></table></div>


#### Missings — Schedule vs. Delay Asymmetrie

**Warum interessant?**  
`arrival_schedule` und `arrival_delay` sollten denselben Null-Anteil haben — wenn kein Zeitstempel vorhanden ist, kann auch kein Delay gemessen werden. Die Counts weichen aber ab: Schedule hat weniger Nulls als Delay. Das bedeutet: es gibt Fahrten, bei denen ein Zeitstempel registriert wurde, aber kein Delay-Wert ankam — typischerweise ein Übertragungsfehler im Sensor-/Reporting-System.

**Was ist auffällig?**  
| Spalte | Null-Count | Anteil |
|---|---|---|
| `arrival_schedule` | 120.477 | 0.13% |
| `arrival_delay` | 195.146 | 0.22% |
| `departure_schedule` | 120.477 | 0.13% |
| `departure_delay` | ~195.228 | 0.22% |

Differenz: ~74.669 Zeilen haben einen Schedule-Wert aber keinen Delay → Fahrt gemeldet, Messung nicht angekommen.

**Empfehlung Cleaning:**  
- Zeilen mit `arrival_schedule IS NULL` → rausfiltern (keine Zeitinformation, für Modell nutzlos)  
- Zeilen mit `arrival_schedule NOT NULL` aber `arrival_delay IS NULL` → für Ausfallanalyse behalten, für Delay-Modell herausfiltern (kein Zielwert vorhanden)


```python
# --- Finding C1: Missings in arrival/departure schedules and delays

section_header('Missings in schedules and delays')

# Asymmetrie zwischen Schedule- und Delay-Nullwerten prüfen
result_c1 = lf.select([
    pl.col("arrival_schedule").null_count().alias("arrival_schedule_null"),
    pl.col("arrival_delay").null_count().alias("arrival_delay_null"),
    pl.col("departure_schedule").null_count().alias("departure_schedule_null"),
    pl.col("departure_delay").null_count().alias("departure_delay_null"),
]).collect()

display(result_c1)

# Kernfrage: Wie viele Zeilen haben Schedule vorhanden, aber Delay fehlt?
result_c1_detail = lf.select([
    # Schedule null, Delay auch null
    ((pl.col("arrival_schedule").is_null()) & (pl.col("arrival_delay").is_null()))
        .sum().alias("beide_null"),
    # Schedule vorhanden, aber Delay fehlt → Übertragungsfehler
    ((pl.col("arrival_schedule").is_not_null()) & (pl.col("arrival_delay").is_null()))
        .sum().alias("schedule_ok_delay_null"),
    # Schedule fehlt, aber Delay vorhanden → unplausibler Sonderfall
    ((pl.col("arrival_schedule").is_null()) & (pl.col("arrival_delay").is_not_null()))
        .sum().alias("schedule_null_delay_ok"),
]).collect()

display(result_c1_detail)

total = lf.select(pl.len()).collect().item()

nutzlos = result_c1_detail["schedule_ok_delay_null"][0] + result_c1_detail["beide_null"][0]
log(f"\n>> Zeilen ohne verwertbaren Delay-Wert: {nutzlos:,}  ({nutzlos/total*100:.2f}% des Gesamtdatensatzes)")

```

    
    [1m[38;2;52;97;141m───  MISSINGS IN SCHEDULES AND DELAYS  ───────────────────────[0m



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (1, 4)</small><table border="1" class="dataframe"><thead><tr><th>arrival_schedule_null</th><th>arrival_delay_null</th><th>departure_schedule_null</th><th>departure_delay_null</th></tr><tr><td>u32</td><td>u32</td><td>u32</td><td>u32</td></tr></thead><tbody><tr><td>136437</td><td>225018</td><td>136148</td><td>228075</td></tr></tbody></table></div>



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (1, 3)</small><table border="1" class="dataframe"><thead><tr><th>beide_null</th><th>schedule_ok_delay_null</th><th>schedule_null_delay_ok</th></tr><tr><td>u32</td><td>u32</td><td>u32</td></tr></thead><tbody><tr><td>136437</td><td>88581</td><td>0</td></tr></tbody></table></div>


    [38;2;52;97;141m
    >> Zeilen ohne verwertbaren Delay-Wert: 225,018  (0.24% des Gesamtdatensatzes)[0m


### Data Integrity



**Invalid Data Detection & Plausibility Check**

#### Extreme Delay-Werte (-29.892s / +34.685s)

**Warum interessant?**  
Verspätungen von -8.3 Stunden (zu früh) oder +9.6 Stunden (zu spät) sind physikalisch nicht plausibel. Ein Tram fährt im Taktbetrieb — Abweichungen über ±1 Stunde deuten fast immer auf Datenfehler hin (falsches Datum eingetragen, Systemfehler bei der Zeitstempelung). Besonders auffällig: der identische Maximalwert bei `arrival_delay` und `departure_delay` (34.685s) — das ist kein Zufall, sondern ein systematischer Fehler in einem spezifischen Datensatz.

**Was ist auffällig?**  
| Kennzahl | arrival_delay | departure_delay |
|---|---|---|
| Min | -29.892s = **-8.3h** | -29.876s = **-8.3h** |
| Max | +34.685s = **+9.6h** | +34.685s = **+9.6h** |
| Identischer Maxwert | ✅ | ✅ |

Faustformel: Alles über ±3.600s (±1h) ist unplausibel für regulären Tramverkehr.

**Empfehlung Cleaning:**  
- Zeilen mit `|delay| > 3.600s` (1h) → rausfiltern oder als `unreliable` flaggen  
- Alternativ: härtere Grenze `|delay| > 1.800s` (30 Min) prüfen — nach Betrachtung der Verteilung entscheiden


```python
# --- Finding I1: Extreme Delay-Werte

section_header('Extreme Delay-Werte')
print() 

# Wie viele Zeilen überschreiten plausible Grenzen?
thresholds = [600, 1800, 3600]  # 10 Min, 30 Min, 1 Stunde in Sekunden

for t in thresholds:
    n = lf.filter(
        (pl.col("arrival_delay").abs() > t) | (pl.col("departure_delay").abs() > t)
    ).select(pl.len()).collect().item()
    total = lf.select(pl.len()).collect().item()
    log(f">> delay >> {t:>5}s ({t//60:>2} Min): {n:>8,} Zeilen  ({n/total*100:.3f}%)")

print()

# Die extremsten Fälle anschauen — was steckt dahinter?
extreme = (
    lf
    .filter(pl.col("arrival_delay").abs() > 3600)
    .select(["operating_date", "line_name", "stop_name", "arrival_delay", "departure_delay", "canceled"])
    .sort("arrival_delay")
    .collect()
)

print(f"Zeilen mit |arrival_delay| > 1h: {len(extreme):,}")
print("\nExtremste negative Werte (zu früh):")
display(extreme.head(5))
print("\nExtremste positive Werte (zu spät):")
display(extreme.tail(5))
```

    
    [1m[38;2;52;97;141m───  EXTREME DELAY-WERTE  ────────────────────────────────────[0m
    
    [38;2;52;97;141m>> delay >>   600s (10 Min):  196,855 Zeilen  (0.209%)[0m
    [38;2;52;97;141m>> delay >>  1800s (30 Min):   22,660 Zeilen  (0.024%)[0m
    [38;2;52;97;141m>> delay >>  3600s (60 Min):    4,899 Zeilen  (0.005%)[0m
    
    Zeilen mit |arrival_delay| > 1h: 4,576
    
    Extremste negative Werte (zu früh):



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (5, 6)</small><table border="1" class="dataframe"><thead><tr><th>operating_date</th><th>line_name</th><th>stop_name</th><th>arrival_delay</th><th>departure_delay</th><th>canceled</th></tr><tr><td>date</td><td>cat</td><td>cat</td><td>f32</td><td>f32</td><td>bool</td></tr></thead><tbody><tr><td>2024-08-08</td><td>&quot;5&quot;</td><td>&quot;Zürich, Letzistrasse&quot;</td><td>-35964.0</td><td>-35950.0</td><td>false</td></tr><tr><td>2024-08-08</td><td>&quot;5&quot;</td><td>&quot;Zürich, Voltastrasse&quot;</td><td>-35958.0</td><td>-35956.0</td><td>false</td></tr><tr><td>2024-08-08</td><td>&quot;5&quot;</td><td>&quot;Zürich, Seilbahn Rigiblick&quot;</td><td>-35946.0</td><td>-35925.0</td><td>false</td></tr><tr><td>2024-08-08</td><td>&quot;5&quot;</td><td>&quot;Zürich, Haldenbach&quot;</td><td>-35934.0</td><td>-35926.0</td><td>false</td></tr><tr><td>2024-08-08</td><td>&quot;5&quot;</td><td>&quot;Zürich, Winkelriedstrasse&quot;</td><td>-35934.0</td><td>-35934.0</td><td>false</td></tr></tbody></table></div>


    
    Extremste positive Werte (zu spät):



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (5, 6)</small><table border="1" class="dataframe"><thead><tr><th>operating_date</th><th>line_name</th><th>stop_name</th><th>arrival_delay</th><th>departure_delay</th><th>canceled</th></tr><tr><td>date</td><td>cat</td><td>cat</td><td>f32</td><td>f32</td><td>bool</td></tr></thead><tbody><tr><td>2025-10-25</td><td>&quot;7&quot;</td><td>&quot;Zürich, Schwamendingerplatz&quot;</td><td>34805.0</td><td>34745.0</td><td>true</td></tr><tr><td>2025-10-25</td><td>&quot;7&quot;</td><td>&quot;Zürich, Roswiesen&quot;</td><td>34865.0</td><td>34865.0</td><td>true</td></tr><tr><td>2025-10-25</td><td>&quot;7&quot;</td><td>&quot;Zürich, Glattwiesen&quot;</td><td>34925.0</td><td>34925.0</td><td>true</td></tr><tr><td>2025-10-25</td><td>&quot;7&quot;</td><td>&quot;Zürich, Probstei&quot;</td><td>34985.0</td><td>34985.0</td><td>true</td></tr><tr><td>2025-10-25</td><td>&quot;7&quot;</td><td>&quot;Zürich, Mattenhof&quot;</td><td>35043.0</td><td>35044.0</td><td>true</td></tr></tbody></table></div>


#### BPUIC-Ausreißer (max 859.600.701)

**Warum interessant?**  
`bpuic` (Betriebspunkt-Identifikation) ist eine strukturierte Haltstellen-ID mit definiertem Format. VBZ-Haltestellen liegen konsistent im Bereich 8.502.572–8.596.001 (7–8-stellig). Der Maximalwert 859.600.701 ist 9-stellig und ~100× größer als der 75%-Wert — klar außerhalb jedes plausiblen Bereichs. Die hohe Skewness (31.6) im bpuic wird fast ausschließlich durch diese Ausreißer erzeugt.

**Was ist auffällig?**  
| Kennzahl | Wert |
|---|---|
| 75%-Perzentil | 8.591.335 |
| Max | 859.600.701 |
| Faktor | ~100× |
| Skewness | 31.6 |

Erwarteter Bereich: `8.500.000 – 8.600.000`  
Anomalie-Schwelle: `> 100.000.000`

**Empfehlung Cleaning:**  
- Zeilen mit `bpuic > 100.000.000` → rausfiltern  
- Prüfen ob diese Zeilen mit bestimmten Linien oder Zeiträumen korrelieren (systematischer Fehler in der Quelle?)


```python
# --- Finding I2: bpuic-Ausreißer

section_header('BPUIC Aussreisser')

bpuic_threshold = 100_000_000

anomale = (
    lf
    .filter(pl.col("bpuic") > bpuic_threshold)
    .select(["operating_date", "line_name", "bpuic", "stop_name"])
    .collect()
)

total = lf.select(pl.len()).collect().item()


# Verteilung der anomalen bpuic-Werte
display(anomale.group_by("bpuic").agg(
    pl.len().alias("n"),
    pl.col("line_name").first().alias("linie"),
    pl.col("operating_date").min().alias("datum_min"),
    pl.col("operating_date").max().alias("datum_max"),
).sort("n", descending=True))

# Normaler Bereich zur Kontrolle
normal_range = lf.select([
    pl.col("bpuic").filter(pl.col("bpuic") <= bpuic_threshold).min().alias("bpuic_min_normal"),
    pl.col("bpuic").filter(pl.col("bpuic") <= bpuic_threshold).max().alias("bpuic_max_normal"),
]).collect()

log(f"\n>> Zeilen mit bpuic > {bpuic_threshold:,}: {len(anomale):,}  ({len(anomale)/total*100:.4f}%)")
log(f"\n>> Normaler bpuic-Bereich: {normal_range['bpuic_min_normal'][0]:,} – {normal_range['bpuic_max_normal'][0]:,}")
```

    
    [1m[38;2;52;97;141m───  BPUIC AUSSREISSER  ──────────────────────────────────────[0m



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (426, 5)</small><table border="1" class="dataframe"><thead><tr><th>bpuic</th><th>n</th><th>linie</th><th>datum_min</th><th>datum_max</th></tr><tr><td>i32</td><td>u32</td><td>cat</td><td>date</td><td>date</td></tr></thead><tbody><tr><td>858734901</td><td>713</td><td>&quot;14&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>858734900</td><td>710</td><td>&quot;14&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>859110501</td><td>696</td><td>&quot;8&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>859110500</td><td>690</td><td>&quot;8&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>859138101</td><td>585</td><td>&quot;14&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>&hellip;</td><td>&hellip;</td><td>&hellip;</td><td>&hellip;</td><td>&hellip;</td></tr><tr><td>850361000</td><td>1</td><td>&quot;9&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>859123300</td><td>1</td><td>&quot;3&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>859143900</td><td>1</td><td>&quot;7&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>859103400</td><td>1</td><td>&quot;17&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr><tr><td>859119400</td><td>1</td><td>&quot;9&quot;</td><td>2025-04-30</td><td>2025-04-30</td></tr></tbody></table></div>


    [38;2;52;97;141m
    >> Zeilen mit bpuic > 100,000,000: 91,137  (0.0966%)[0m
    [38;2;52;97;141m
    >> Normaler bpuic-Bereich: 8,502,572 – 8,596,007[0m


#### Meteo-Lücken (Messausfälle, Rolling Window)

**Warum interessant?**  
Wetterdaten werden stündlich gemessen. Messausfälle entstehen durch Sensor-Neustarts, Wartung oder Übertragungsfehler — sie sind kurz (einzelne Stunden) und zeitlich klumpend. Da der Join auf `floor(arrival_schedule, '1h')` basiert, fallen alle Tramfahrten einer ausgefallenen Stunde gleichzeitig raus. Ein Rolling Mean über ±2 Nachbarstunden füllt diese Lücken zuverlässig.

**Was ist auffällig?**  
| Spalte | Null-Count (Gesamtdatensatz) | Anteil |
|---|---|---|
| `temperature` | ~315.000 | ~0.35% |
| `humidity` | ~315.000 | ~0.35% |
| `rain_duration` | ~237.000 | ~0.26% |
| `wind_speed` | ~237.000 | ~0.27% |
| `global_radiation` | ~258.000 | ~0.29% |
| `flood_intensity` | ~129.000 | ~0.14% |

Alle Meteo-Spalten haben ähnliche Null-Counts → Ausfälle betreffen immer alle Sensoren gleichzeitig (Stationsausfall, nicht einzelne Sensoren).

**Empfehlung Cleaning:**  
- Rolling Mean über `window_size=5` (±2 Stunden) pro Tag: `pl.col("temperature").rolling_mean(5)`  
- Wenn keine Nachbarn vorhanden (Beginn/Ende): Tages-Median als Fallback  
- `flood_intensity` separat behandeln — Rolling Mean ergibt hier keinen Sinn (Ereignis-Indikator), stattdessen `fill_null(0)`


```python
# --- Finding I3: Meteo-Lücken — Muster und Umfang prüfen

section_header('Meteo-Missings')

meteo_cols = ["temperature", "humidity", "rain_duration", "precipitation", "wind_speed", "global_radiation", "flood_intensity"]

# Null-Counts im Gesamtdatensatz
null_counts = lf.select([pl.col(c).null_count().alias(c) for c in meteo_cols]).collect()
total = lf.select(pl.len()).collect().item()

for col in meteo_cols:
    n = null_counts[col][0]
    print(f"{col:<20} null: {n:>8,}  ({n/total*100:.2f}%)")

print()

# Sind die Ausfälle zeitlich klumpend? → Stunden mit vielen gleichzeitigen Null-Werten
lücken_muster = (
    lf
    .filter(pl.col("temperature").is_null())
    .with_columns(
        pl.col("arrival_schedule").dt.truncate("1h").alias("stunde")
    )
    .group_by("stunde")
    .agg(pl.len().alias("n_fahrten_ohne_meteo"))
    .sort("stunde")
    .collect()
)

print(f"Stunden mit fehlenden Temperaturwerten: {len(lücken_muster):,}")
print("Erste 10 Lücken-Stunden:")
display(lücken_muster.head(10))
```

    
    [1m[38;2;52;97;141m───  METEO-MISSINGS  ─────────────────────────────────────────[0m
    temperature          null:  329,902  (0.35%)
    humidity             null:  329,902  (0.35%)
    rain_duration        null:  252,491  (0.27%)
    precipitation        null:  236,841  (0.25%)
    wind_speed           null:  270,230  (0.29%)
    global_radiation     null:  278,078  (0.29%)
    flood_intensity      null:  144,937  (0.15%)
    
    Stunden mit fehlenden Temperaturwerten: 47
    Erste 10 Lücken-Stunden:



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (10, 2)</small><table border="1" class="dataframe"><thead><tr><th>stunde</th><th>n_fahrten_ohne_meteo</th></tr><tr><td>datetime[μs]</td><td>u32</td></tr></thead><tbody><tr><td>null</td><td>136437</td></tr><tr><td>2023-01-13 13:00:00</td><td>5128</td></tr><tr><td>2023-02-21 11:00:00</td><td>5374</td></tr><tr><td>2023-02-22 07:00:00</td><td>5221</td></tr><tr><td>2023-02-22 08:00:00</td><td>5332</td></tr><tr><td>2023-02-22 14:00:00</td><td>5189</td></tr><tr><td>2024-02-29 17:00:00</td><td>5371</td></tr><tr><td>2024-02-29 18:00:00</td><td>5328</td></tr><tr><td>2024-02-29 19:00:00</td><td>5211</td></tr><tr><td>2024-02-29 20:00:00</td><td>4536</td></tr></tbody></table></div>


#### Humidity > 100% (Sensor-Kalibrierungsfehler)

**Warum interessant?**  
Relative Luftfeuchtigkeit ist physikalisch auf 0–100% begrenzt. Werte leicht über 100% (bis ~102%) sind ein bekanntes Kalibrierungsproblem bei Wetterstationen und kein echter Messfehler — aber sie müssen vor dem Modelltraining gekappt werden, da kein ML-Modell mit >100% Luftfeuchtigkeit umgehen kann.

**Was ist auffällig?**  
| Kennzahl | Wert |
|---|---|
| Max `humidity` (Sample) | 101.37% |
| Erwarteter Wertebereich | 0 – 100% |
| Wahrscheinliche Ursache | Sensor-Kalibrierungsdrift |

Werte unter 0% wären ebenfalls anomal — auch das wird mitgeprüft.

**Empfehlung Cleaning:**  
- `humidity` auf `[0, 100]` cappen: `pl.col("humidity").clip(0, 100)`  
- Kein Rausfiltern der Zeilen nötig — nur der Wert selbst wird korrigiert


```python
# --- Finding I4: Humidity > 100% und weitere Wertebereichs-Checks

section_header('Humidity Value Check')

# Humidity-Anomalien
result_humidity = lf.select([
    pl.col("humidity").min().alias("min"),
    pl.col("humidity").max().alias("max"),
    (pl.col("humidity") > 100).sum().alias("n_über_100"),
    (pl.col("humidity") < 0).sum().alias("n_unter_0"),
    pl.col("humidity").filter(pl.col("humidity") > 100).mean().alias("mean_über_100"),
]).collect()

display(result_humidity)
total = lf.select(pl.len()).collect().item()

print()

# Plausibilitäts-Check weiterer physikalischer Grenzen
print("Weitere Wertebereichs-Checks:")
checks = lf.select([
    (pl.col("rain_duration") > 60).sum().alias("rain_duration_über_60min"),   # max ist 60 min/h
    (pl.col("rain_duration") < 0).sum().alias("rain_duration_unter_0"),
    (pl.col("wind_speed") < 0).sum().alias("wind_speed_unter_0"),
    (pl.col("temperature") < -30).sum().alias("temperature_unter_minus30"),   # für Zürich unplausibel
    (pl.col("temperature") > 45).sum().alias("temperature_über_45"),          # für Zürich unplausibel
    (pl.col("district_nr") < 1).sum().alias("district_unter_1"),              # gültig: 1-12
    (pl.col("district_nr") > 12).sum().alias("district_über_12"),
]).collect()

display(checks)

log(f">> Anteil > 100%: {result_humidity['n_über_100'][0]:,}  ({result_humidity['n_über_100'][0]/total*100:.3f}%)")

```

    
    [1m[38;2;52;97;141m───  HUMIDITY VALUE CHECK  ───────────────────────────────────[0m



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (1, 5)</small><table border="1" class="dataframe"><thead><tr><th>min</th><th>max</th><th>n_über_100</th><th>n_unter_0</th><th>mean_über_100</th></tr><tr><td>f32</td><td>f32</td><td>u32</td><td>u32</td><td>f32</td></tr></thead><tbody><tr><td>18.58</td><td>101.370003</td><td>16202</td><td>0</td><td>100.791748</td></tr></tbody></table></div>


    
    Weitere Wertebereichs-Checks:



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (1, 7)</small><table border="1" class="dataframe"><thead><tr><th>rain_duration_über_60min</th><th>rain_duration_unter_0</th><th>wind_speed_unter_0</th><th>temperature_unter_minus30</th><th>temperature_über_45</th><th>district_unter_1</th><th>district_über_12</th></tr><tr><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td><td>u32</td></tr></thead><tbody><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr></tbody></table></div>


    [38;2;52;97;141m>> Anteil > 100%: 16,202  (0.017%)[0m


#### Canceled Trips (~4.5% der Fahrten)

**Warum interessant?**  
Ausgefallene Fahrten (`canceled=True`) sind der extremste Verspätungsfall — keine Verzögerung, sondern kompletter Ausfall. Sie wurden im Wrangling bewusst behalten (worst-case für das Modell). Wichtig zu klären: Haben canceled trips sinnvolle Delay-Werte, oder sind die Delays bei Ausfall null? Das bestimmt wie wir sie im Modell behandeln.

**Was ist auffällig?**  
| Kennzahl | Wert |
|---|---|
| Anteil canceled (5%-Sample) | ~4.52% |
| Hochrechnung Gesamtdatensatz | ~4.0 Mio. Fahrten |
| Häufigste Linie mit Ausfällen | noch zu prüfen |

Frage: Haben canceled trips `arrival_delay = null` (Fahrt kam nicht → keine Messung) oder einen sehr hohen Delay-Wert?

**Empfehlung Cleaning:**  
- `canceled=True` Zeilen **behalten** — unverzichtbar für Modell  
- Als separate Gruppe oder als Feature `is_canceled` (0/1) kodieren  
- Delay-Werte bei canceled=True prüfen: wenn null → für Delay-Vorhersage herausfiltern, für Ausfallmodell behalten


```python
# --- Finding I5: Canceled Trips

section_header('Canceld Trips Analysis')

# Anteil und Verteilung
result_canceled = (
    lf
    .group_by("canceled")
    .agg(pl.len().alias("n"))
    .with_columns((pl.col("n") / pl.col("n").sum() * 100).round(2).alias("pct"))
    .sort("canceled")
    .collect()
)
display(result_canceled)

# Kernfrage: Haben canceled trips Delay-Werte?
result_canceled_delays = (
    lf
    .filter(pl.col("canceled"))
    .select([
        pl.len().alias("total_canceled"),
        pl.col("arrival_delay").null_count().alias("arrival_delay_null"),
        pl.col("departure_delay").null_count().alias("departure_delay_null"),
        pl.col("arrival_delay").mean().alias("mean_arrival_delay"),
        pl.col("arrival_delay").median().alias("median_arrival_delay"),
    ])
    .collect()
)

print("\nCanceled trips — Delay-Analyse:")
display(result_canceled_delays)

# Ausfälle nach Linie — welche Linie hat die meisten?
print("\nAusfälle pro Linie:")
display(
    lf
    .filter(pl.col("canceled"))
    .group_by("line_name")
    .agg(pl.len().alias("n_ausfaelle"))
    .sort("n_ausfaelle", descending=True)
    .collect()
)
```

    
    [1m[38;2;52;97;141m───  CANCELD TRIPS ANALYSIS  ─────────────────────────────────[0m



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (2, 3)</small><table border="1" class="dataframe"><thead><tr><th>canceled</th><th>n</th><th>pct</th></tr><tr><td>bool</td><td>u32</td><td>f64</td></tr></thead><tbody><tr><td>false</td><td>89806659</td><td>95.18</td></tr><tr><td>true</td><td>4551872</td><td>4.82</td></tr></tbody></table></div>


    
    Canceled trips — Delay-Analyse:



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (1, 5)</small><table border="1" class="dataframe"><thead><tr><th>total_canceled</th><th>arrival_delay_null</th><th>departure_delay_null</th><th>mean_arrival_delay</th><th>median_arrival_delay</th></tr><tr><td>u32</td><td>u32</td><td>u32</td><td>f32</td><td>f32</td></tr></thead><tbody><tr><td>4551872</td><td>224993</td><td>227996</td><td>51.875221</td><td>30.0</td></tr></tbody></table></div>


    
    Ausfälle pro Linie:



<div><style>
.dataframe > thead > tr,
.dataframe > tbody > tr {
  text-align: right;
  white-space: pre-wrap;
}
</style>
<small>shape: (18, 2)</small><table border="1" class="dataframe"><thead><tr><th>line_name</th><th>n_ausfaelle</th></tr><tr><td>cat</td><td>u32</td></tr></thead><tbody><tr><td>&quot;9&quot;</td><td>828676</td></tr><tr><td>&quot;10&quot;</td><td>712011</td></tr><tr><td>&quot;12&quot;</td><td>548813</td></tr><tr><td>&quot;17&quot;</td><td>490566</td></tr><tr><td>&quot;7&quot;</td><td>485161</td></tr><tr><td>&hellip;</td><td>&hellip;</td></tr><tr><td>&quot;14&quot;</td><td>93624</td></tr><tr><td>&quot;15&quot;</td><td>78836</td></tr><tr><td>&quot;51&quot;</td><td>990</td></tr><tr><td>&quot;50&quot;</td><td>422</td></tr><tr><td>&quot;E&quot;</td><td>28</td></tr></tbody></table></div>


### Data Distribution



**Numerical Features & Categorical Features & Bivariate Analysis**


```python

result = inspect(df_eda, sections=[ 'numeric'])
```

    
    [1m[38;2;52;97;141m───  NUMERIC STATS  ──────────────────────────────────────────[0m



<style type="text/css">
#T_ec842 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_ec842 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_ec842 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_ec842 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_ec842 tr:hover td {
  background-color: #eef3f8;
}
#T_ec842_row0_col0, #T_ec842_row1_col0, #T_ec842_row2_col0, #T_ec842_row3_col0, #T_ec842_row4_col0, #T_ec842_row5_col0, #T_ec842_row6_col0, #T_ec842_row7_col0, #T_ec842_row8_col0, #T_ec842_row9_col0, #T_ec842_row10_col0, #T_ec842_row11_col0, #T_ec842_row12_col0, #T_ec842_row13_col0, #T_ec842_row14_col0 {
  text-align: left;
}
#T_ec842_row0_col1, #T_ec842_row0_col2, #T_ec842_row0_col3, #T_ec842_row0_col4, #T_ec842_row0_col5, #T_ec842_row0_col6, #T_ec842_row0_col7, #T_ec842_row0_col8, #T_ec842_row0_col9, #T_ec842_row0_col10, #T_ec842_row0_col11, #T_ec842_row1_col1, #T_ec842_row1_col2, #T_ec842_row1_col3, #T_ec842_row1_col4, #T_ec842_row1_col5, #T_ec842_row1_col6, #T_ec842_row1_col7, #T_ec842_row1_col8, #T_ec842_row1_col9, #T_ec842_row1_col10, #T_ec842_row1_col11, #T_ec842_row2_col1, #T_ec842_row2_col2, #T_ec842_row2_col3, #T_ec842_row2_col4, #T_ec842_row2_col5, #T_ec842_row2_col6, #T_ec842_row2_col7, #T_ec842_row2_col8, #T_ec842_row2_col9, #T_ec842_row2_col10, #T_ec842_row2_col11, #T_ec842_row3_col1, #T_ec842_row3_col2, #T_ec842_row3_col3, #T_ec842_row3_col4, #T_ec842_row3_col5, #T_ec842_row3_col6, #T_ec842_row3_col7, #T_ec842_row3_col8, #T_ec842_row3_col9, #T_ec842_row3_col10, #T_ec842_row3_col11, #T_ec842_row4_col1, #T_ec842_row4_col2, #T_ec842_row4_col3, #T_ec842_row4_col4, #T_ec842_row4_col5, #T_ec842_row4_col6, #T_ec842_row4_col7, #T_ec842_row4_col8, #T_ec842_row4_col9, #T_ec842_row4_col10, #T_ec842_row4_col11, #T_ec842_row5_col1, #T_ec842_row5_col2, #T_ec842_row5_col3, #T_ec842_row5_col4, #T_ec842_row5_col5, #T_ec842_row5_col6, #T_ec842_row5_col7, #T_ec842_row5_col8, #T_ec842_row5_col9, #T_ec842_row5_col10, #T_ec842_row5_col11, #T_ec842_row6_col1, #T_ec842_row6_col2, #T_ec842_row6_col3, #T_ec842_row6_col4, #T_ec842_row6_col5, #T_ec842_row6_col6, #T_ec842_row6_col7, #T_ec842_row6_col8, #T_ec842_row6_col9, #T_ec842_row6_col10, #T_ec842_row6_col11, #T_ec842_row7_col1, #T_ec842_row7_col2, #T_ec842_row7_col3, #T_ec842_row7_col4, #T_ec842_row7_col5, #T_ec842_row7_col6, #T_ec842_row7_col7, #T_ec842_row7_col8, #T_ec842_row7_col9, #T_ec842_row7_col10, #T_ec842_row7_col11, #T_ec842_row8_col1, #T_ec842_row8_col2, #T_ec842_row8_col3, #T_ec842_row8_col4, #T_ec842_row8_col5, #T_ec842_row8_col6, #T_ec842_row8_col7, #T_ec842_row8_col8, #T_ec842_row8_col9, #T_ec842_row8_col10, #T_ec842_row8_col11, #T_ec842_row9_col1, #T_ec842_row9_col2, #T_ec842_row9_col3, #T_ec842_row9_col4, #T_ec842_row9_col5, #T_ec842_row9_col6, #T_ec842_row9_col7, #T_ec842_row9_col8, #T_ec842_row9_col9, #T_ec842_row9_col10, #T_ec842_row9_col11, #T_ec842_row10_col1, #T_ec842_row10_col2, #T_ec842_row10_col3, #T_ec842_row10_col4, #T_ec842_row10_col5, #T_ec842_row10_col6, #T_ec842_row10_col7, #T_ec842_row10_col8, #T_ec842_row10_col9, #T_ec842_row10_col10, #T_ec842_row10_col11, #T_ec842_row11_col1, #T_ec842_row11_col2, #T_ec842_row11_col3, #T_ec842_row11_col4, #T_ec842_row11_col5, #T_ec842_row11_col6, #T_ec842_row11_col7, #T_ec842_row11_col8, #T_ec842_row11_col9, #T_ec842_row11_col10, #T_ec842_row11_col11, #T_ec842_row12_col1, #T_ec842_row12_col2, #T_ec842_row12_col3, #T_ec842_row12_col4, #T_ec842_row12_col5, #T_ec842_row12_col6, #T_ec842_row12_col7, #T_ec842_row12_col8, #T_ec842_row12_col9, #T_ec842_row12_col10, #T_ec842_row12_col11, #T_ec842_row13_col1, #T_ec842_row13_col2, #T_ec842_row13_col3, #T_ec842_row13_col4, #T_ec842_row13_col5, #T_ec842_row13_col6, #T_ec842_row13_col7, #T_ec842_row13_col8, #T_ec842_row13_col9, #T_ec842_row13_col10, #T_ec842_row13_col11, #T_ec842_row14_col1, #T_ec842_row14_col2, #T_ec842_row14_col3, #T_ec842_row14_col4, #T_ec842_row14_col5, #T_ec842_row14_col6, #T_ec842_row14_col7, #T_ec842_row14_col8, #T_ec842_row14_col9, #T_ec842_row14_col10, #T_ec842_row14_col11 {
  text-align: right;
}
</style>
<table id="T_ec842">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_ec842_level0_col0" class="col_heading level0 col0" >column</th>
      <th id="T_ec842_level0_col1" class="col_heading level0 col1" >missing_pct</th>
      <th id="T_ec842_level0_col2" class="col_heading level0 col2" >count</th>
      <th id="T_ec842_level0_col3" class="col_heading level0 col3" >mean</th>
      <th id="T_ec842_level0_col4" class="col_heading level0 col4" >median</th>
      <th id="T_ec842_level0_col5" class="col_heading level0 col5" >std</th>
      <th id="T_ec842_level0_col6" class="col_heading level0 col6" >min</th>
      <th id="T_ec842_level0_col7" class="col_heading level0 col7" >25%</th>
      <th id="T_ec842_level0_col8" class="col_heading level0 col8" >75%</th>
      <th id="T_ec842_level0_col9" class="col_heading level0 col9" >max</th>
      <th id="T_ec842_level0_col10" class="col_heading level0 col10" >mean_median_diff</th>
      <th id="T_ec842_level0_col11" class="col_heading level0 col11" >skewness</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_ec842_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_ec842_row0_col0" class="data row0 col0" >bpuic</td>
      <td id="T_ec842_row0_col1" class="data row0 col1" >0.00%</td>
      <td id="T_ec842_row0_col2" class="data row0 col2" >4717926.00</td>
      <td id="T_ec842_row0_col3" class="data row0 col3" >9399000.77</td>
      <td id="T_ec842_row0_col4" class="data row0 col4" >8591220.00</td>
      <td id="T_ec842_row0_col5" class="data row0 col5" >26255697.03</td>
      <td id="T_ec842_row0_col6" class="data row0 col6" >8502572.00</td>
      <td id="T_ec842_row0_col7" class="data row0 col7" >8591060.00</td>
      <td id="T_ec842_row0_col8" class="data row0 col8" >8591335.00</td>
      <td id="T_ec842_row0_col9" class="data row0 col9" >859423901.00</td>
      <td id="T_ec842_row0_col10" class="data row0 col10" >807780.77</td>
      <td id="T_ec842_row0_col11" class="data row0 col11" >32.32</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_ec842_row1_col0" class="data row1 col0" >arrival_delay</td>
      <td id="T_ec842_row1_col1" class="data row1 col1" >0.24%</td>
      <td id="T_ec842_row1_col2" class="data row1 col2" >4706606.00</td>
      <td id="T_ec842_row1_col3" class="data row1 col3" >56.16</td>
      <td id="T_ec842_row1_col4" class="data row1 col4" >42.00</td>
      <td id="T_ec842_row1_col5" class="data row1 col5" >113.35</td>
      <td id="T_ec842_row1_col6" class="data row1 col6" >-29892.00</td>
      <td id="T_ec842_row1_col7" class="data row1 col7" >12.00</td>
      <td id="T_ec842_row1_col8" class="data row1 col8" >81.00</td>
      <td id="T_ec842_row1_col9" class="data row1 col9" >33785.00</td>
      <td id="T_ec842_row1_col10" class="data row1 col10" >14.16</td>
      <td id="T_ec842_row1_col11" class="data row1 col11" >64.25</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_ec842_row2_col0" class="data row2 col0" >departure_delay</td>
      <td id="T_ec842_row2_col1" class="data row2 col1" >0.24%</td>
      <td id="T_ec842_row2_col2" class="data row2 col2" >4706640.00</td>
      <td id="T_ec842_row2_col3" class="data row2 col3" >61.76</td>
      <td id="T_ec842_row2_col4" class="data row2 col4" >47.00</td>
      <td id="T_ec842_row2_col5" class="data row2 col5" >113.26</td>
      <td id="T_ec842_row2_col6" class="data row2 col6" >-29876.00</td>
      <td id="T_ec842_row2_col7" class="data row2 col7" >16.00</td>
      <td id="T_ec842_row2_col8" class="data row2 col8" >88.00</td>
      <td id="T_ec842_row2_col9" class="data row2 col9" >33785.00</td>
      <td id="T_ec842_row2_col10" class="data row2 col10" >14.76</td>
      <td id="T_ec842_row2_col11" class="data row2 col11" >59.26</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_ec842_row3_col0" class="data row3 col0" >stop_sequence</td>
      <td id="T_ec842_row3_col1" class="data row3 col1" >0.00%</td>
      <td id="T_ec842_row3_col2" class="data row3 col2" >4717926.00</td>
      <td id="T_ec842_row3_col3" class="data row3 col3" >12.77</td>
      <td id="T_ec842_row3_col4" class="data row3 col4" >11.00</td>
      <td id="T_ec842_row3_col5" class="data row3 col5" >8.46</td>
      <td id="T_ec842_row3_col6" class="data row3 col6" >1.00</td>
      <td id="T_ec842_row3_col7" class="data row3 col7" >6.00</td>
      <td id="T_ec842_row3_col8" class="data row3 col8" >19.00</td>
      <td id="T_ec842_row3_col9" class="data row3 col9" >70.00</td>
      <td id="T_ec842_row3_col10" class="data row3 col10" >1.77</td>
      <td id="T_ec842_row3_col11" class="data row3 col11" >0.82</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_ec842_row4_col0" class="data row4 col0" >stop_lat</td>
      <td id="T_ec842_row4_col1" class="data row4 col1" >0.10%</td>
      <td id="T_ec842_row4_col2" class="data row4 col2" >4713418.00</td>
      <td id="T_ec842_row4_col3" class="data row4 col3" >47.38</td>
      <td id="T_ec842_row4_col4" class="data row4 col4" >47.38</td>
      <td id="T_ec842_row4_col5" class="data row4 col5" >0.02</td>
      <td id="T_ec842_row4_col6" class="data row4 col6" >47.33</td>
      <td id="T_ec842_row4_col7" class="data row4 col7" >47.37</td>
      <td id="T_ec842_row4_col8" class="data row4 col8" >47.40</td>
      <td id="T_ec842_row4_col9" class="data row4 col9" >47.45</td>
      <td id="T_ec842_row4_col10" class="data row4 col10" >0.00</td>
      <td id="T_ec842_row4_col11" class="data row4 col11" >0.70</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_ec842_row5_col0" class="data row5 col0" >stop_lon</td>
      <td id="T_ec842_row5_col1" class="data row5 col1" >0.10%</td>
      <td id="T_ec842_row5_col2" class="data row5 col2" >4713418.00</td>
      <td id="T_ec842_row5_col3" class="data row5 col3" >8.54</td>
      <td id="T_ec842_row5_col4" class="data row5 col4" >8.54</td>
      <td id="T_ec842_row5_col5" class="data row5 col5" >0.02</td>
      <td id="T_ec842_row5_col6" class="data row5 col6" >8.44</td>
      <td id="T_ec842_row5_col7" class="data row5 col7" >8.53</td>
      <td id="T_ec842_row5_col8" class="data row5 col8" >8.55</td>
      <td id="T_ec842_row5_col9" class="data row5 col9" >8.64</td>
      <td id="T_ec842_row5_col10" class="data row5 col10" >0.00</td>
      <td id="T_ec842_row5_col11" class="data row5 col11" >-0.53</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_ec842_row6_col0" class="data row6 col0" >district_nr</td>
      <td id="T_ec842_row6_col1" class="data row6 col1" >6.89%</td>
      <td id="T_ec842_row6_col2" class="data row6 col2" >4392768.00</td>
      <td id="T_ec842_row6_col3" class="data row6 col3" >5.24</td>
      <td id="T_ec842_row6_col4" class="data row6 col4" >5.00</td>
      <td id="T_ec842_row6_col5" class="data row6 col5" >3.42</td>
      <td id="T_ec842_row6_col6" class="data row6 col6" >1.00</td>
      <td id="T_ec842_row6_col7" class="data row6 col7" >2.00</td>
      <td id="T_ec842_row6_col8" class="data row6 col8" >7.00</td>
      <td id="T_ec842_row6_col9" class="data row6 col9" >12.00</td>
      <td id="T_ec842_row6_col10" class="data row6 col10" >0.24</td>
      <td id="T_ec842_row6_col11" class="data row6 col11" >0.40</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_ec842_row7_col0" class="data row7 col0" >temperature</td>
      <td id="T_ec842_row7_col1" class="data row7 col1" >0.35%</td>
      <td id="T_ec842_row7_col2" class="data row7 col2" >4701342.00</td>
      <td id="T_ec842_row7_col3" class="data row7 col3" >13.20</td>
      <td id="T_ec842_row7_col4" class="data row7 col4" >12.48</td>
      <td id="T_ec842_row7_col5" class="data row7 col5" >8.03</td>
      <td id="T_ec842_row7_col6" class="data row7 col6" >-4.75</td>
      <td id="T_ec842_row7_col7" class="data row7 col7" >7.16</td>
      <td id="T_ec842_row7_col8" class="data row7 col8" >19.28</td>
      <td id="T_ec842_row7_col9" class="data row7 col9" >35.80</td>
      <td id="T_ec842_row7_col10" class="data row7 col10" >0.72</td>
      <td id="T_ec842_row7_col11" class="data row7 col11" >0.22</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_ec842_row8_col0" class="data row8 col0" >humidity</td>
      <td id="T_ec842_row8_col1" class="data row8 col1" >0.35%</td>
      <td id="T_ec842_row8_col2" class="data row8 col2" >4701342.00</td>
      <td id="T_ec842_row8_col3" class="data row8 col3" >67.58</td>
      <td id="T_ec842_row8_col4" class="data row8 col4" >70.61</td>
      <td id="T_ec842_row8_col5" class="data row8 col5" >16.91</td>
      <td id="T_ec842_row8_col6" class="data row8 col6" >18.58</td>
      <td id="T_ec842_row8_col7" class="data row8 col7" >55.65</td>
      <td id="T_ec842_row8_col8" class="data row8 col8" >81.19</td>
      <td id="T_ec842_row8_col9" class="data row8 col9" >101.37</td>
      <td id="T_ec842_row8_col10" class="data row8 col10" >-3.03</td>
      <td id="T_ec842_row8_col11" class="data row8 col11" >-0.53</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_ec842_row9_col0" class="data row9 col0" >rain_duration</td>
      <td id="T_ec842_row9_col1" class="data row9 col1" >0.27%</td>
      <td id="T_ec842_row9_col2" class="data row9 col2" >4705167.00</td>
      <td id="T_ec842_row9_col3" class="data row9 col3" >5.92</td>
      <td id="T_ec842_row9_col4" class="data row9 col4" >0.00</td>
      <td id="T_ec842_row9_col5" class="data row9 col5" >15.81</td>
      <td id="T_ec842_row9_col6" class="data row9 col6" >0.00</td>
      <td id="T_ec842_row9_col7" class="data row9 col7" >0.00</td>
      <td id="T_ec842_row9_col8" class="data row9 col8" >0.00</td>
      <td id="T_ec842_row9_col9" class="data row9 col9" >60.00</td>
      <td id="T_ec842_row9_col10" class="data row9 col10" >5.92</td>
      <td id="T_ec842_row9_col11" class="data row9 col11" >2.67</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_ec842_row10_col0" class="data row10 col0" >precipitation</td>
      <td id="T_ec842_row10_col1" class="data row10 col1" >0.25%</td>
      <td id="T_ec842_row10_col2" class="data row10 col2" >4706111.00</td>
      <td id="T_ec842_row10_col3" class="data row10 col3" >0.12</td>
      <td id="T_ec842_row10_col4" class="data row10 col4" >0.00</td>
      <td id="T_ec842_row10_col5" class="data row10 col5" >0.60</td>
      <td id="T_ec842_row10_col6" class="data row10 col6" >0.00</td>
      <td id="T_ec842_row10_col7" class="data row10 col7" >0.00</td>
      <td id="T_ec842_row10_col8" class="data row10 col8" >0.00</td>
      <td id="T_ec842_row10_col9" class="data row10 col9" >23.90</td>
      <td id="T_ec842_row10_col10" class="data row10 col10" >0.12</td>
      <td id="T_ec842_row10_col11" class="data row10 col11" >11.89</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_ec842_row11_col0" class="data row11 col0" >wind_speed</td>
      <td id="T_ec842_row11_col1" class="data row11 col1" >0.29%</td>
      <td id="T_ec842_row11_col2" class="data row11 col2" >4704260.00</td>
      <td id="T_ec842_row11_col3" class="data row11 col3" >1.93</td>
      <td id="T_ec842_row11_col4" class="data row11 col4" >1.74</td>
      <td id="T_ec842_row11_col5" class="data row11 col5" >1.02</td>
      <td id="T_ec842_row11_col6" class="data row11 col6" >0.25</td>
      <td id="T_ec842_row11_col7" class="data row11 col7" >1.19</td>
      <td id="T_ec842_row11_col8" class="data row11 col8" >2.44</td>
      <td id="T_ec842_row11_col9" class="data row11 col9" >10.08</td>
      <td id="T_ec842_row11_col10" class="data row11 col10" >0.19</td>
      <td id="T_ec842_row11_col11" class="data row11 col11" >1.31</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_ec842_row12_col0" class="data row12 col0" >global_radiation</td>
      <td id="T_ec842_row12_col1" class="data row12 col1" >0.30%</td>
      <td id="T_ec842_row12_col2" class="data row12 col2" >4703865.00</td>
      <td id="T_ec842_row12_col3" class="data row12 col3" >185.12</td>
      <td id="T_ec842_row12_col4" class="data row12 col4" >65.46</td>
      <td id="T_ec842_row12_col5" class="data row12 col5" >243.26</td>
      <td id="T_ec842_row12_col6" class="data row12 col6" >0.01</td>
      <td id="T_ec842_row12_col7" class="data row12 col7" >0.03</td>
      <td id="T_ec842_row12_col8" class="data row12 col8" >296.58</td>
      <td id="T_ec842_row12_col9" class="data row12 col9" >1041.18</td>
      <td id="T_ec842_row12_col10" class="data row12 col10" >119.66</td>
      <td id="T_ec842_row12_col11" class="data row12 col11" >1.34</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_ec842_row13_col0" class="data row13 col0" >flood_intensity</td>
      <td id="T_ec842_row13_col1" class="data row13 col1" >0.16%</td>
      <td id="T_ec842_row13_col2" class="data row13 col2" >4710582.00</td>
      <td id="T_ec842_row13_col3" class="data row13 col3" >0.07</td>
      <td id="T_ec842_row13_col4" class="data row13 col4" >0.00</td>
      <td id="T_ec842_row13_col5" class="data row13 col5" >0.48</td>
      <td id="T_ec842_row13_col6" class="data row13 col6" >0.00</td>
      <td id="T_ec842_row13_col7" class="data row13 col7" >0.00</td>
      <td id="T_ec842_row13_col8" class="data row13 col8" >0.00</td>
      <td id="T_ec842_row13_col9" class="data row13 col9" >11.00</td>
      <td id="T_ec842_row13_col10" class="data row13 col10" >0.07</td>
      <td id="T_ec842_row13_col11" class="data row13 col11" >14.87</td>
    </tr>
    <tr>
      <th id="T_ec842_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_ec842_row14_col0" class="data row14 col0" >event_size</td>
      <td id="T_ec842_row14_col1" class="data row14 col1" >78.52%</td>
      <td id="T_ec842_row14_col2" class="data row14 col2" >1013197.00</td>
      <td id="T_ec842_row14_col3" class="data row14 col3" >1.46</td>
      <td id="T_ec842_row14_col4" class="data row14 col4" >1.00</td>
      <td id="T_ec842_row14_col5" class="data row14 col5" >0.57</td>
      <td id="T_ec842_row14_col6" class="data row14 col6" >1.00</td>
      <td id="T_ec842_row14_col7" class="data row14 col7" >1.00</td>
      <td id="T_ec842_row14_col8" class="data row14 col8" >2.00</td>
      <td id="T_ec842_row14_col9" class="data row14 col9" >3.00</td>
      <td id="T_ec842_row14_col10" class="data row14 col10" >0.46</td>
      <td id="T_ec842_row14_col11" class="data row14 col11" >0.77</td>
    </tr>
  </tbody>
</table>



#### Numerische Features — Rohe Verteilung


```python
from wgnd.viz import grid_histplot
from wgnd.core.config import cfg

section_header('Numerische Verteilungen — Rohdaten')

# Delays — bereinigt (|delay| ≤ 3.600s) für saubere Skalierung; mit canceled als Hue
fig, _ = grid_histplot(
    df_delays_clean,
    columns=["arrival_delay", "departure_delay"],
    hue="canceled",
    multiple="layer",
    n_cols=2,
    figsize_per_plot=(7, 4),
)
plt.suptitle("Delay-Features — bereinigt (|delay| ≤ 3.600s, orange = canceled)",
             fontsize=13, color=cfg.CHART_TITLE, x=0.02, ha="left", y=1.02)
plt.show()

# Meteo-Features
fig, _ = grid_histplot(
    df_eda,
    columns=["temperature", "precipitation", "rain_duration",
             "wind_speed", "global_radiation", "humidity"],
    n_cols=3,
    figsize_per_plot=(6, 3),
)
plt.suptitle("Meteo-Features — Rohdaten",
             fontsize=13, color=cfg.CHART_TITLE, x=0.02, ha="left", y=1.02)
plt.show()
```

    
    [1m[38;2;52;97;141m───  NUMERISCHE VERTEILUNGEN — ROHDATEN  ─────────────────────[0m



    
![png](01_exploration_files/01_exploration_39_1.png)
    



    
![png](01_exploration_files/01_exploration_39_2.png)
    


#### Kategorische Features — Verteilung


```python
from wgnd.viz import bar

section_header('Kategorische Verteilungen')

# Fahrten pro Linie
line_counts = df_eda["line_name"].value_counts().sort_values()
fig, ax = bar(line_counts, orient="h", title="Fahrten pro Linie (Sample)")
plt.show()

# Fahrten pro Stadtdistrikt (ohne null)
district_counts = df_eda["district_name"].dropna().value_counts().sort_values()
fig, ax = bar(district_counts, orient="h", title="Fahrten pro Stadtdistrikt (Sample, ohne außerhalb)")
plt.show()

# Canceled-Anteil pro Linie — stacked bar
line_cancel = (
    df_eda.groupby("line_name", observed=True)["canceled"]
    .value_counts(normalize=True)
    .mul(100)
    .rename("pct")
    .reset_index()
)
canceled_pct = (
    line_cancel[line_cancel["canceled"] == True]
    .set_index("line_name")["pct"]
    .sort_values()
)
fig, ax = bar(
    canceled_pct, orient="h",
    title="Canceled-Anteil pro Linie (%)",
    ref_val=canceled_pct.mean(), ref_label="Ø"
)
plt.show()
```

    
    [1m[38;2;52;97;141m───  KATEGORISCHE VERTEILUNGEN  ──────────────────────────────[0m



    
![png](01_exploration_files/01_exploration_41_1.png)
    



    
![png](01_exploration_files/01_exploration_41_2.png)
    



    
![png](01_exploration_files/01_exploration_41_3.png)
    


#### Beurteilung der Verteilungen

| Priorität | ID | Befund | Kategorie | Empfehlung | Geklärt? |
|:---|:---:|:---|:---:|:---|:---:|
| **Kritisch** | I1 | Extreme Delays: departure_delay Skewness 42.9, arrival_delay 38.6 — Ausreißer verzerren Modell stark | Integrity | Outlier-Bereinigung via IQR 3× als eigener Cleaning-Schritt | ✓ |
| **Kritisch** | C1 | arrival_schedule/delay Asymmetrie — 74.669 Zeilen: Schedule vorhanden, Delay null; 0 umgekehrt; 195.146 Zeilen (0.22%) ohne verwertbaren Delay-Wert | Completeness | Zeilen mit Schedule-ok aber Delay-null ausschließen oder imputieren | |
| **Hoch** | I4 | `relative_humidity` > 100 % — physikalisch unmöglich | Integrity | Clip auf [0, 100] im Cleaning-Schritt | |
| **Hoch** | I2 | `bpuic` kein numerisches Feature: 91.137 Zeilen (0.10%) außerhalb Normalbereich 8.502.572–8.596.007 — strukturierter ID-Typ | Integrity | Nicht als Float-Feature ins Modell; als kategoriales Label oder Lookup-Key behandeln | ✓ |
| **Mittel** | I3 | Negative Delays — Züge kommen früher als geplant an | Integrity | Plausibel und erwünscht; Wertebereich dokumentieren, kein Clip nötig | ✓ |
| **Mittel** | C3 | `district_nr` Nulls — nicht alle Haltestellen einer Stadtdistrikt zugeordnet | Completeness | Plausibel (Stadtgrenze / GTFS-Mapping); separat dokumentieren | ✓ |
| **Niedrig** | I5 | Zero-Inflated: `precipitation` (Skewness 11.6), `flood_intensity` (14.6), `rain_duration` (2.68) — dominiert durch Nullen | Integrity | Binäres Flag (`hat_regen`) + kontinuierlicher Wert; nicht log-transformieren | ✓ |
| **Niedrig** | C2 | `event_type` / `event_size` fast überall null | Completeness | Plausibel — Normalfall ist kein Event; als Dummy-Feature kodieren | ✓ |
| **Niedrig** | C4 | Duplikate: 1.72 % doppelte Zeilen im Rohdatensatz | Completeness | `distinct()` im Cleaning-Schritt; Ursache unklar (doppelte GTFS-Einträge?) | |

### Data Relationships



**Correlations**


```python
import matplotlib.pyplot as plt
from wgnd.core.config import cfg

# Session-Patch: installed wgnd version erwartet noch PALETTE_DIVERGENT
# Permanent-Fix benötigt uv reinstall — hier temporäre Lösung für diese Session
_prg = plt.get_cmap(cfg.PALETTE_DIV)
cfg.PALETTE_DIVERGENT = [_prg(i / 6) for i in range(7)]
print("✅ Session-Patch aktiv")
```

    ✅ Session-Patch aktiv



```python
inspect_correlations(df_eda)
# inspect_correlations(df_eda, target='your_target_col', show_pairplot=True)
```

    
    [1m[38;2;52;97;141m───  CORRELATIONS  ───────────────────────────────────────────[0m



<style type="text/css">
#T_31766 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_31766 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_31766 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_31766 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_31766 tr:hover td {
  background-color: #eef3f8;
}
#T_31766_row0_col0, #T_31766_row0_col1, #T_31766_row0_col2, #T_31766_row0_col3, #T_31766_row0_col4, #T_31766_row0_col5, #T_31766_row0_col6, #T_31766_row0_col7, #T_31766_row0_col8, #T_31766_row0_col9, #T_31766_row0_col10, #T_31766_row0_col11, #T_31766_row0_col12, #T_31766_row0_col13, #T_31766_row0_col14, #T_31766_row1_col0, #T_31766_row1_col1, #T_31766_row1_col2, #T_31766_row1_col3, #T_31766_row1_col4, #T_31766_row1_col5, #T_31766_row1_col6, #T_31766_row1_col7, #T_31766_row1_col8, #T_31766_row1_col9, #T_31766_row1_col10, #T_31766_row1_col11, #T_31766_row1_col12, #T_31766_row1_col13, #T_31766_row1_col14, #T_31766_row2_col0, #T_31766_row2_col1, #T_31766_row2_col2, #T_31766_row2_col3, #T_31766_row2_col4, #T_31766_row2_col5, #T_31766_row2_col6, #T_31766_row2_col7, #T_31766_row2_col8, #T_31766_row2_col9, #T_31766_row2_col10, #T_31766_row2_col11, #T_31766_row2_col12, #T_31766_row2_col13, #T_31766_row2_col14, #T_31766_row3_col0, #T_31766_row3_col1, #T_31766_row3_col2, #T_31766_row3_col3, #T_31766_row3_col4, #T_31766_row3_col5, #T_31766_row3_col6, #T_31766_row3_col7, #T_31766_row3_col8, #T_31766_row3_col9, #T_31766_row3_col10, #T_31766_row3_col11, #T_31766_row3_col12, #T_31766_row3_col13, #T_31766_row3_col14, #T_31766_row4_col0, #T_31766_row4_col1, #T_31766_row4_col2, #T_31766_row4_col3, #T_31766_row4_col4, #T_31766_row4_col5, #T_31766_row4_col6, #T_31766_row4_col7, #T_31766_row4_col8, #T_31766_row4_col9, #T_31766_row4_col10, #T_31766_row4_col11, #T_31766_row4_col12, #T_31766_row4_col13, #T_31766_row4_col14, #T_31766_row5_col0, #T_31766_row5_col1, #T_31766_row5_col2, #T_31766_row5_col3, #T_31766_row5_col4, #T_31766_row5_col5, #T_31766_row5_col6, #T_31766_row5_col7, #T_31766_row5_col8, #T_31766_row5_col9, #T_31766_row5_col10, #T_31766_row5_col11, #T_31766_row5_col12, #T_31766_row5_col13, #T_31766_row5_col14, #T_31766_row6_col0, #T_31766_row6_col1, #T_31766_row6_col2, #T_31766_row6_col3, #T_31766_row6_col4, #T_31766_row6_col5, #T_31766_row6_col6, #T_31766_row6_col7, #T_31766_row6_col8, #T_31766_row6_col9, #T_31766_row6_col10, #T_31766_row6_col11, #T_31766_row6_col12, #T_31766_row6_col13, #T_31766_row6_col14, #T_31766_row7_col0, #T_31766_row7_col1, #T_31766_row7_col2, #T_31766_row7_col3, #T_31766_row7_col4, #T_31766_row7_col5, #T_31766_row7_col6, #T_31766_row7_col7, #T_31766_row7_col8, #T_31766_row7_col9, #T_31766_row7_col10, #T_31766_row7_col11, #T_31766_row7_col12, #T_31766_row7_col13, #T_31766_row7_col14, #T_31766_row8_col0, #T_31766_row8_col1, #T_31766_row8_col2, #T_31766_row8_col3, #T_31766_row8_col4, #T_31766_row8_col5, #T_31766_row8_col6, #T_31766_row8_col7, #T_31766_row8_col8, #T_31766_row8_col9, #T_31766_row8_col10, #T_31766_row8_col11, #T_31766_row8_col12, #T_31766_row8_col13, #T_31766_row8_col14, #T_31766_row9_col0, #T_31766_row9_col1, #T_31766_row9_col2, #T_31766_row9_col3, #T_31766_row9_col4, #T_31766_row9_col5, #T_31766_row9_col6, #T_31766_row9_col7, #T_31766_row9_col8, #T_31766_row9_col9, #T_31766_row9_col10, #T_31766_row9_col11, #T_31766_row9_col12, #T_31766_row9_col13, #T_31766_row9_col14, #T_31766_row10_col0, #T_31766_row10_col1, #T_31766_row10_col2, #T_31766_row10_col3, #T_31766_row10_col4, #T_31766_row10_col5, #T_31766_row10_col6, #T_31766_row10_col7, #T_31766_row10_col8, #T_31766_row10_col9, #T_31766_row10_col10, #T_31766_row10_col11, #T_31766_row10_col12, #T_31766_row10_col13, #T_31766_row10_col14, #T_31766_row11_col0, #T_31766_row11_col1, #T_31766_row11_col2, #T_31766_row11_col3, #T_31766_row11_col4, #T_31766_row11_col5, #T_31766_row11_col6, #T_31766_row11_col7, #T_31766_row11_col8, #T_31766_row11_col9, #T_31766_row11_col10, #T_31766_row11_col11, #T_31766_row11_col12, #T_31766_row11_col13, #T_31766_row11_col14, #T_31766_row12_col0, #T_31766_row12_col1, #T_31766_row12_col2, #T_31766_row12_col3, #T_31766_row12_col4, #T_31766_row12_col5, #T_31766_row12_col6, #T_31766_row12_col7, #T_31766_row12_col8, #T_31766_row12_col9, #T_31766_row12_col10, #T_31766_row12_col11, #T_31766_row12_col12, #T_31766_row12_col13, #T_31766_row12_col14, #T_31766_row13_col0, #T_31766_row13_col1, #T_31766_row13_col2, #T_31766_row13_col3, #T_31766_row13_col4, #T_31766_row13_col5, #T_31766_row13_col6, #T_31766_row13_col7, #T_31766_row13_col8, #T_31766_row13_col9, #T_31766_row13_col10, #T_31766_row13_col11, #T_31766_row13_col12, #T_31766_row13_col13, #T_31766_row13_col14, #T_31766_row14_col0, #T_31766_row14_col1, #T_31766_row14_col2, #T_31766_row14_col3, #T_31766_row14_col4, #T_31766_row14_col5, #T_31766_row14_col6, #T_31766_row14_col7, #T_31766_row14_col8, #T_31766_row14_col9, #T_31766_row14_col10, #T_31766_row14_col11, #T_31766_row14_col12, #T_31766_row14_col13, #T_31766_row14_col14 {
  text-align: right;
}
</style>
<table id="T_31766">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_31766_level0_col0" class="col_heading level0 col0" >bpuic</th>
      <th id="T_31766_level0_col1" class="col_heading level0 col1" >arrival_delay</th>
      <th id="T_31766_level0_col2" class="col_heading level0 col2" >departure_delay</th>
      <th id="T_31766_level0_col3" class="col_heading level0 col3" >stop_sequence</th>
      <th id="T_31766_level0_col4" class="col_heading level0 col4" >stop_lat</th>
      <th id="T_31766_level0_col5" class="col_heading level0 col5" >stop_lon</th>
      <th id="T_31766_level0_col6" class="col_heading level0 col6" >district_nr</th>
      <th id="T_31766_level0_col7" class="col_heading level0 col7" >temperature</th>
      <th id="T_31766_level0_col8" class="col_heading level0 col8" >humidity</th>
      <th id="T_31766_level0_col9" class="col_heading level0 col9" >rain_duration</th>
      <th id="T_31766_level0_col10" class="col_heading level0 col10" >precipitation</th>
      <th id="T_31766_level0_col11" class="col_heading level0 col11" >wind_speed</th>
      <th id="T_31766_level0_col12" class="col_heading level0 col12" >global_radiation</th>
      <th id="T_31766_level0_col13" class="col_heading level0 col13" >flood_intensity</th>
      <th id="T_31766_level0_col14" class="col_heading level0 col14" >event_size</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_31766_level0_row0" class="row_heading level0 row0" >bpuic</th>
      <td id="T_31766_row0_col0" class="data row0 col0" >1.00</td>
      <td id="T_31766_row0_col1" class="data row0 col1" >-0.00</td>
      <td id="T_31766_row0_col2" class="data row0 col2" >-0.00</td>
      <td id="T_31766_row0_col3" class="data row0 col3" >-0.00</td>
      <td id="T_31766_row0_col4" class="data row0 col4" >0.18</td>
      <td id="T_31766_row0_col5" class="data row0 col5" >-0.10</td>
      <td id="T_31766_row0_col6" class="data row0 col6" >0.04</td>
      <td id="T_31766_row0_col7" class="data row0 col7" >0.03</td>
      <td id="T_31766_row0_col8" class="data row0 col8" >-0.04</td>
      <td id="T_31766_row0_col9" class="data row0 col9" >-0.01</td>
      <td id="T_31766_row0_col10" class="data row0 col10" >-0.01</td>
      <td id="T_31766_row0_col11" class="data row0 col11" >-0.01</td>
      <td id="T_31766_row0_col12" class="data row0 col12" >0.03</td>
      <td id="T_31766_row0_col13" class="data row0 col13" >-0.00</td>
      <td id="T_31766_row0_col14" class="data row0 col14" >0.00</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row1" class="row_heading level0 row1" >arrival_delay</th>
      <td id="T_31766_row1_col0" class="data row1 col0" >-0.00</td>
      <td id="T_31766_row1_col1" class="data row1 col1" >1.00</td>
      <td id="T_31766_row1_col2" class="data row1 col2" >0.96</td>
      <td id="T_31766_row1_col3" class="data row1 col3" >0.10</td>
      <td id="T_31766_row1_col4" class="data row1 col4" >0.01</td>
      <td id="T_31766_row1_col5" class="data row1 col5" >0.01</td>
      <td id="T_31766_row1_col6" class="data row1 col6" >0.03</td>
      <td id="T_31766_row1_col7" class="data row1 col7" >0.01</td>
      <td id="T_31766_row1_col8" class="data row1 col8" >-0.00</td>
      <td id="T_31766_row1_col9" class="data row1 col9" >0.03</td>
      <td id="T_31766_row1_col10" class="data row1 col10" >0.03</td>
      <td id="T_31766_row1_col11" class="data row1 col11" >0.01</td>
      <td id="T_31766_row1_col12" class="data row1 col12" >-0.00</td>
      <td id="T_31766_row1_col13" class="data row1 col13" >0.00</td>
      <td id="T_31766_row1_col14" class="data row1 col14" >0.02</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row2" class="row_heading level0 row2" >departure_delay</th>
      <td id="T_31766_row2_col0" class="data row2 col0" >-0.00</td>
      <td id="T_31766_row2_col1" class="data row2 col1" >0.96</td>
      <td id="T_31766_row2_col2" class="data row2 col2" >1.00</td>
      <td id="T_31766_row2_col3" class="data row2 col3" >0.10</td>
      <td id="T_31766_row2_col4" class="data row2 col4" >0.01</td>
      <td id="T_31766_row2_col5" class="data row2 col5" >0.01</td>
      <td id="T_31766_row2_col6" class="data row2 col6" >0.02</td>
      <td id="T_31766_row2_col7" class="data row2 col7" >0.00</td>
      <td id="T_31766_row2_col8" class="data row2 col8" >0.00</td>
      <td id="T_31766_row2_col9" class="data row2 col9" >0.03</td>
      <td id="T_31766_row2_col10" class="data row2 col10" >0.03</td>
      <td id="T_31766_row2_col11" class="data row2 col11" >0.01</td>
      <td id="T_31766_row2_col12" class="data row2 col12" >-0.01</td>
      <td id="T_31766_row2_col13" class="data row2 col13" >0.00</td>
      <td id="T_31766_row2_col14" class="data row2 col14" >0.02</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row3" class="row_heading level0 row3" >stop_sequence</th>
      <td id="T_31766_row3_col0" class="data row3 col0" >-0.00</td>
      <td id="T_31766_row3_col1" class="data row3 col1" >0.10</td>
      <td id="T_31766_row3_col2" class="data row3 col2" >0.10</td>
      <td id="T_31766_row3_col3" class="data row3 col3" >1.00</td>
      <td id="T_31766_row3_col4" class="data row3 col4" >0.02</td>
      <td id="T_31766_row3_col5" class="data row3 col5" >0.02</td>
      <td id="T_31766_row3_col6" class="data row3 col6" >0.05</td>
      <td id="T_31766_row3_col7" class="data row3 col7" >-0.00</td>
      <td id="T_31766_row3_col8" class="data row3 col8" >-0.01</td>
      <td id="T_31766_row3_col9" class="data row3 col9" >0.00</td>
      <td id="T_31766_row3_col10" class="data row3 col10" >0.00</td>
      <td id="T_31766_row3_col11" class="data row3 col11" >0.01</td>
      <td id="T_31766_row3_col12" class="data row3 col12" >0.01</td>
      <td id="T_31766_row3_col13" class="data row3 col13" >0.00</td>
      <td id="T_31766_row3_col14" class="data row3 col14" >-0.02</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row4" class="row_heading level0 row4" >stop_lat</th>
      <td id="T_31766_row4_col0" class="data row4 col0" >0.18</td>
      <td id="T_31766_row4_col1" class="data row4 col1" >0.01</td>
      <td id="T_31766_row4_col2" class="data row4 col2" >0.01</td>
      <td id="T_31766_row4_col3" class="data row4 col3" >0.02</td>
      <td id="T_31766_row4_col4" class="data row4 col4" >1.00</td>
      <td id="T_31766_row4_col5" class="data row4 col5" >0.13</td>
      <td id="T_31766_row4_col6" class="data row4 col6" >0.68</td>
      <td id="T_31766_row4_col7" class="data row4 col7" >-0.00</td>
      <td id="T_31766_row4_col8" class="data row4 col8" >-0.00</td>
      <td id="T_31766_row4_col9" class="data row4 col9" >0.00</td>
      <td id="T_31766_row4_col10" class="data row4 col10" >0.00</td>
      <td id="T_31766_row4_col11" class="data row4 col11" >0.00</td>
      <td id="T_31766_row4_col12" class="data row4 col12" >-0.00</td>
      <td id="T_31766_row4_col13" class="data row4 col13" >-0.00</td>
      <td id="T_31766_row4_col14" class="data row4 col14" >0.00</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row5" class="row_heading level0 row5" >stop_lon</th>
      <td id="T_31766_row5_col0" class="data row5 col0" >-0.10</td>
      <td id="T_31766_row5_col1" class="data row5 col1" >0.01</td>
      <td id="T_31766_row5_col2" class="data row5 col2" >0.01</td>
      <td id="T_31766_row5_col3" class="data row5 col3" >0.02</td>
      <td id="T_31766_row5_col4" class="data row5 col4" >0.13</td>
      <td id="T_31766_row5_col5" class="data row5 col5" >1.00</td>
      <td id="T_31766_row5_col6" class="data row5 col6" >0.16</td>
      <td id="T_31766_row5_col7" class="data row5 col7" >-0.00</td>
      <td id="T_31766_row5_col8" class="data row5 col8" >-0.00</td>
      <td id="T_31766_row5_col9" class="data row5 col9" >0.00</td>
      <td id="T_31766_row5_col10" class="data row5 col10" >0.00</td>
      <td id="T_31766_row5_col11" class="data row5 col11" >0.00</td>
      <td id="T_31766_row5_col12" class="data row5 col12" >0.00</td>
      <td id="T_31766_row5_col13" class="data row5 col13" >-0.00</td>
      <td id="T_31766_row5_col14" class="data row5 col14" >-0.00</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row6" class="row_heading level0 row6" >district_nr</th>
      <td id="T_31766_row6_col0" class="data row6 col0" >0.04</td>
      <td id="T_31766_row6_col1" class="data row6 col1" >0.03</td>
      <td id="T_31766_row6_col2" class="data row6 col2" >0.02</td>
      <td id="T_31766_row6_col3" class="data row6 col3" >0.05</td>
      <td id="T_31766_row6_col4" class="data row6 col4" >0.68</td>
      <td id="T_31766_row6_col5" class="data row6 col5" >0.16</td>
      <td id="T_31766_row6_col6" class="data row6 col6" >1.00</td>
      <td id="T_31766_row6_col7" class="data row6 col7" >-0.00</td>
      <td id="T_31766_row6_col8" class="data row6 col8" >0.00</td>
      <td id="T_31766_row6_col9" class="data row6 col9" >0.00</td>
      <td id="T_31766_row6_col10" class="data row6 col10" >0.00</td>
      <td id="T_31766_row6_col11" class="data row6 col11" >-0.00</td>
      <td id="T_31766_row6_col12" class="data row6 col12" >-0.00</td>
      <td id="T_31766_row6_col13" class="data row6 col13" >-0.00</td>
      <td id="T_31766_row6_col14" class="data row6 col14" >0.01</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row7" class="row_heading level0 row7" >temperature</th>
      <td id="T_31766_row7_col0" class="data row7 col0" >0.03</td>
      <td id="T_31766_row7_col1" class="data row7 col1" >0.01</td>
      <td id="T_31766_row7_col2" class="data row7 col2" >0.00</td>
      <td id="T_31766_row7_col3" class="data row7 col3" >-0.00</td>
      <td id="T_31766_row7_col4" class="data row7 col4" >-0.00</td>
      <td id="T_31766_row7_col5" class="data row7 col5" >-0.00</td>
      <td id="T_31766_row7_col6" class="data row7 col6" >-0.00</td>
      <td id="T_31766_row7_col7" class="data row7 col7" >1.00</td>
      <td id="T_31766_row7_col8" class="data row7 col8" >-0.59</td>
      <td id="T_31766_row7_col9" class="data row7 col9" >-0.11</td>
      <td id="T_31766_row7_col10" class="data row7 col10" >-0.02</td>
      <td id="T_31766_row7_col11" class="data row7 col11" >0.01</td>
      <td id="T_31766_row7_col12" class="data row7 col12" >0.51</td>
      <td id="T_31766_row7_col13" class="data row7 col13" >0.05</td>
      <td id="T_31766_row7_col14" class="data row7 col14" >0.14</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row8" class="row_heading level0 row8" >humidity</th>
      <td id="T_31766_row8_col0" class="data row8 col0" >-0.04</td>
      <td id="T_31766_row8_col1" class="data row8 col1" >-0.00</td>
      <td id="T_31766_row8_col2" class="data row8 col2" >0.00</td>
      <td id="T_31766_row8_col3" class="data row8 col3" >-0.01</td>
      <td id="T_31766_row8_col4" class="data row8 col4" >-0.00</td>
      <td id="T_31766_row8_col5" class="data row8 col5" >-0.00</td>
      <td id="T_31766_row8_col6" class="data row8 col6" >0.00</td>
      <td id="T_31766_row8_col7" class="data row8 col7" >-0.59</td>
      <td id="T_31766_row8_col8" class="data row8 col8" >1.00</td>
      <td id="T_31766_row8_col9" class="data row8 col9" >0.36</td>
      <td id="T_31766_row8_col10" class="data row8 col10" >0.20</td>
      <td id="T_31766_row8_col11" class="data row8 col11" >-0.19</td>
      <td id="T_31766_row8_col12" class="data row8 col12" >-0.55</td>
      <td id="T_31766_row8_col13" class="data row8 col13" >0.05</td>
      <td id="T_31766_row8_col14" class="data row8 col14" >-0.03</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row9" class="row_heading level0 row9" >rain_duration</th>
      <td id="T_31766_row9_col0" class="data row9 col0" >-0.01</td>
      <td id="T_31766_row9_col1" class="data row9 col1" >0.03</td>
      <td id="T_31766_row9_col2" class="data row9 col2" >0.03</td>
      <td id="T_31766_row9_col3" class="data row9 col3" >0.00</td>
      <td id="T_31766_row9_col4" class="data row9 col4" >0.00</td>
      <td id="T_31766_row9_col5" class="data row9 col5" >0.00</td>
      <td id="T_31766_row9_col6" class="data row9 col6" >0.00</td>
      <td id="T_31766_row9_col7" class="data row9 col7" >-0.11</td>
      <td id="T_31766_row9_col8" class="data row9 col8" >0.36</td>
      <td id="T_31766_row9_col9" class="data row9 col9" >1.00</td>
      <td id="T_31766_row9_col10" class="data row9 col10" >0.56</td>
      <td id="T_31766_row9_col11" class="data row9 col11" >0.11</td>
      <td id="T_31766_row9_col12" class="data row9 col12" >-0.21</td>
      <td id="T_31766_row9_col13" class="data row9 col13" >0.09</td>
      <td id="T_31766_row9_col14" class="data row9 col14" >-0.07</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row10" class="row_heading level0 row10" >precipitation</th>
      <td id="T_31766_row10_col0" class="data row10 col0" >-0.01</td>
      <td id="T_31766_row10_col1" class="data row10 col1" >0.03</td>
      <td id="T_31766_row10_col2" class="data row10 col2" >0.03</td>
      <td id="T_31766_row10_col3" class="data row10 col3" >0.00</td>
      <td id="T_31766_row10_col4" class="data row10 col4" >0.00</td>
      <td id="T_31766_row10_col5" class="data row10 col5" >0.00</td>
      <td id="T_31766_row10_col6" class="data row10 col6" >0.00</td>
      <td id="T_31766_row10_col7" class="data row10 col7" >-0.02</td>
      <td id="T_31766_row10_col8" class="data row10 col8" >0.20</td>
      <td id="T_31766_row10_col9" class="data row10 col9" >0.56</td>
      <td id="T_31766_row10_col10" class="data row10 col10" >1.00</td>
      <td id="T_31766_row10_col11" class="data row10 col11" >0.08</td>
      <td id="T_31766_row10_col12" class="data row10 col12" >-0.11</td>
      <td id="T_31766_row10_col13" class="data row10 col13" >0.15</td>
      <td id="T_31766_row10_col14" class="data row10 col14" >-0.04</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row11" class="row_heading level0 row11" >wind_speed</th>
      <td id="T_31766_row11_col0" class="data row11 col0" >-0.01</td>
      <td id="T_31766_row11_col1" class="data row11 col1" >0.01</td>
      <td id="T_31766_row11_col2" class="data row11 col2" >0.01</td>
      <td id="T_31766_row11_col3" class="data row11 col3" >0.01</td>
      <td id="T_31766_row11_col4" class="data row11 col4" >0.00</td>
      <td id="T_31766_row11_col5" class="data row11 col5" >0.00</td>
      <td id="T_31766_row11_col6" class="data row11 col6" >-0.00</td>
      <td id="T_31766_row11_col7" class="data row11 col7" >0.01</td>
      <td id="T_31766_row11_col8" class="data row11 col8" >-0.19</td>
      <td id="T_31766_row11_col9" class="data row11 col9" >0.11</td>
      <td id="T_31766_row11_col10" class="data row11 col10" >0.08</td>
      <td id="T_31766_row11_col11" class="data row11 col11" >1.00</td>
      <td id="T_31766_row11_col12" class="data row11 col12" >0.12</td>
      <td id="T_31766_row11_col13" class="data row11 col13" >0.01</td>
      <td id="T_31766_row11_col14" class="data row11 col14" >-0.09</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row12" class="row_heading level0 row12" >global_radiation</th>
      <td id="T_31766_row12_col0" class="data row12 col0" >0.03</td>
      <td id="T_31766_row12_col1" class="data row12 col1" >-0.00</td>
      <td id="T_31766_row12_col2" class="data row12 col2" >-0.01</td>
      <td id="T_31766_row12_col3" class="data row12 col3" >0.01</td>
      <td id="T_31766_row12_col4" class="data row12 col4" >-0.00</td>
      <td id="T_31766_row12_col5" class="data row12 col5" >0.00</td>
      <td id="T_31766_row12_col6" class="data row12 col6" >-0.00</td>
      <td id="T_31766_row12_col7" class="data row12 col7" >0.51</td>
      <td id="T_31766_row12_col8" class="data row12 col8" >-0.55</td>
      <td id="T_31766_row12_col9" class="data row12 col9" >-0.21</td>
      <td id="T_31766_row12_col10" class="data row12 col10" >-0.11</td>
      <td id="T_31766_row12_col11" class="data row12 col11" >0.12</td>
      <td id="T_31766_row12_col12" class="data row12 col12" >1.00</td>
      <td id="T_31766_row12_col13" class="data row12 col13" >-0.01</td>
      <td id="T_31766_row12_col14" class="data row12 col14" >0.04</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row13" class="row_heading level0 row13" >flood_intensity</th>
      <td id="T_31766_row13_col0" class="data row13 col0" >-0.00</td>
      <td id="T_31766_row13_col1" class="data row13 col1" >0.00</td>
      <td id="T_31766_row13_col2" class="data row13 col2" >0.00</td>
      <td id="T_31766_row13_col3" class="data row13 col3" >0.00</td>
      <td id="T_31766_row13_col4" class="data row13 col4" >-0.00</td>
      <td id="T_31766_row13_col5" class="data row13 col5" >-0.00</td>
      <td id="T_31766_row13_col6" class="data row13 col6" >-0.00</td>
      <td id="T_31766_row13_col7" class="data row13 col7" >0.05</td>
      <td id="T_31766_row13_col8" class="data row13 col8" >0.05</td>
      <td id="T_31766_row13_col9" class="data row13 col9" >0.09</td>
      <td id="T_31766_row13_col10" class="data row13 col10" >0.15</td>
      <td id="T_31766_row13_col11" class="data row13 col11" >0.01</td>
      <td id="T_31766_row13_col12" class="data row13 col12" >-0.01</td>
      <td id="T_31766_row13_col13" class="data row13 col13" >1.00</td>
      <td id="T_31766_row13_col14" class="data row13 col14" >-0.01</td>
    </tr>
    <tr>
      <th id="T_31766_level0_row14" class="row_heading level0 row14" >event_size</th>
      <td id="T_31766_row14_col0" class="data row14 col0" >0.00</td>
      <td id="T_31766_row14_col1" class="data row14 col1" >0.02</td>
      <td id="T_31766_row14_col2" class="data row14 col2" >0.02</td>
      <td id="T_31766_row14_col3" class="data row14 col3" >-0.02</td>
      <td id="T_31766_row14_col4" class="data row14 col4" >0.00</td>
      <td id="T_31766_row14_col5" class="data row14 col5" >-0.00</td>
      <td id="T_31766_row14_col6" class="data row14 col6" >0.01</td>
      <td id="T_31766_row14_col7" class="data row14 col7" >0.14</td>
      <td id="T_31766_row14_col8" class="data row14 col8" >-0.03</td>
      <td id="T_31766_row14_col9" class="data row14 col9" >-0.07</td>
      <td id="T_31766_row14_col10" class="data row14 col10" >-0.04</td>
      <td id="T_31766_row14_col11" class="data row14 col11" >-0.09</td>
      <td id="T_31766_row14_col12" class="data row14 col12" >0.04</td>
      <td id="T_31766_row14_col13" class="data row14 col13" >-0.01</td>
      <td id="T_31766_row14_col14" class="data row14 col14" >1.00</td>
    </tr>
  </tbody>
</table>




    
![png](01_exploration_files/01_exploration_47_2.png)
    


    1 highly correlated pair(s) (|r| ≥ 0.8): arrival_delay↔departure_delay


    [38;2;255;166;0m⚠  1 highly correlated pair(s) (|r| ≥ 0.8): arrival_delay↔departure_delay[0m





    {'matrix':                   bpuic  arrival_delay  departure_delay  stop_sequence  \
     bpuic              1.00          -0.00            -0.00          -0.00   
     arrival_delay     -0.00           1.00             0.96           0.10   
     departure_delay   -0.00           0.96             1.00           0.10   
     stop_sequence     -0.00           0.10             0.10           1.00   
     stop_lat           0.18           0.01             0.01           0.02   
     stop_lon          -0.10           0.01             0.01           0.02   
     district_nr        0.04           0.03             0.02           0.05   
     temperature        0.03           0.01             0.00          -0.00   
     humidity          -0.04          -0.00             0.00          -0.01   
     rain_duration     -0.01           0.03             0.03           0.00   
     precipitation     -0.01           0.03             0.03           0.00   
     wind_speed        -0.01           0.01             0.01           0.01   
     global_radiation   0.03          -0.00            -0.01           0.01   
     flood_intensity   -0.00           0.00             0.00           0.00   
     event_size         0.00           0.02             0.02          -0.02   
     
                       stop_lat  stop_lon  district_nr  temperature  humidity  \
     bpuic                 0.18     -0.10         0.04         0.03     -0.04   
     arrival_delay         0.01      0.01         0.03         0.01     -0.00   
     departure_delay       0.01      0.01         0.02         0.00      0.00   
     stop_sequence         0.02      0.02         0.05        -0.00     -0.01   
     stop_lat              1.00      0.13         0.68        -0.00     -0.00   
     stop_lon              0.13      1.00         0.16        -0.00     -0.00   
     district_nr           0.68      0.16         1.00        -0.00      0.00   
     temperature          -0.00     -0.00        -0.00         1.00     -0.59   
     humidity             -0.00     -0.00         0.00        -0.59      1.00   
     rain_duration         0.00      0.00         0.00        -0.11      0.36   
     precipitation         0.00      0.00         0.00        -0.02      0.20   
     wind_speed            0.00      0.00        -0.00         0.01     -0.19   
     global_radiation     -0.00      0.00        -0.00         0.51     -0.55   
     flood_intensity      -0.00     -0.00        -0.00         0.05      0.05   
     event_size            0.00     -0.00         0.01         0.14     -0.03   
     
                       rain_duration  precipitation  wind_speed  global_radiation  \
     bpuic                     -0.01          -0.01       -0.01              0.03   
     arrival_delay              0.03           0.03        0.01             -0.00   
     departure_delay            0.03           0.03        0.01             -0.01   
     stop_sequence              0.00           0.00        0.01              0.01   
     stop_lat                   0.00           0.00        0.00             -0.00   
     stop_lon                   0.00           0.00        0.00              0.00   
     district_nr                0.00           0.00       -0.00             -0.00   
     temperature               -0.11          -0.02        0.01              0.51   
     humidity                   0.36           0.20       -0.19             -0.55   
     rain_duration              1.00           0.56        0.11             -0.21   
     precipitation              0.56           1.00        0.08             -0.11   
     wind_speed                 0.11           0.08        1.00              0.12   
     global_radiation          -0.21          -0.11        0.12              1.00   
     flood_intensity            0.09           0.15        0.01             -0.01   
     event_size                -0.07          -0.04       -0.09              0.04   
     
                       flood_intensity  event_size  
     bpuic                       -0.00        0.00  
     arrival_delay                0.00        0.02  
     departure_delay              0.00        0.02  
     stop_sequence                0.00       -0.02  
     stop_lat                    -0.00        0.00  
     stop_lon                    -0.00       -0.00  
     district_nr                 -0.00        0.01  
     temperature                  0.05        0.14  
     humidity                     0.05       -0.03  
     rain_duration                0.09       -0.07  
     precipitation                0.15       -0.04  
     wind_speed                   0.01       -0.09  
     global_radiation            -0.01        0.04  
     flood_intensity              1.00       -0.01  
     event_size                  -0.01        1.00  ,
     'pairs':              col_1             col_2     r   |r|
     0    arrival_delay   departure_delay  0.96  0.96
     1         stop_lat       district_nr  0.68  0.68
     2      temperature          humidity -0.59  0.59
     3    rain_duration     precipitation  0.56  0.56
     4         humidity  global_radiation -0.55  0.55
     ..             ...               ...   ...   ...
     100       stop_lon       temperature -0.00  0.00
     101       stop_lat        event_size  0.00  0.00
     102    district_nr        wind_speed -0.00  0.00
     103    district_nr  global_radiation -0.00  0.00
     104    district_nr   flood_intensity -0.00  0.00
     
     [105 rows x 4 columns],
     'target': Empty DataFrame
     Columns: []
     Index: []}



#### Korrelations-Findings

| # | Finding | Paare | r | Interpretation | Konsequenz |
|:---|:---|:---|:---:|:---|:---|
| R1 | Delay-Selbstkorrelation | `arrival_delay` ↔ `departure_delay` | 0.95 | Selbe Verspätung setzt sich fort — logisch | Nur eine der beiden als Zielvariable verwenden |
| R2 | Wetter→Delay: schwache lineare Signale | `rain_duration` / `precipitation` ↔ `arrival_delay` | 0.03 | Kein linearer Zusammenhang — Schwellenwert-Effekte wahrscheinlich (Starkregen ≠ leichter Regen) | Baummodell (XGBoost) statt linearer Regression — kann Threshold-Effekte lernen |
| R3 | Events sind saisonal | `event_size` ↔ `temperature` | 0.16 | Große Events finden im Sommer statt (Street Parade, Open Air) — beide Features indirekt saisonal | Nicht gemeinsam ins Modell ohne Saisonalität zu kontrollieren; Monats-Feature erwägen |
| R4 | Überflutung durch Intensität, nicht Dauer | `flood_intensity` ↔ `precipitation` | 0.15 | Stärkster Wetter-Korrelationswert — Intensität entscheidender als Regendauer (r=0.10) | Zero-Inflated behandeln: binäres Flag `hat_flut` + kontinuierlicher Wert |
| R5 | Geografische Multikollinearität | `stop_lat` ↔ `district_nr` | 0.68 | Geografisch erwartet, kein Informationsgewinn | `district_nr` und `stop_lat/lon` nicht gemeinsam ins Modell |

> **Modellierungs-Fazit:** Schwache lineare Korrelationen zwischen Wetter und Delay sind kein Zeichen für Irrelevanz — sie zeigen Nicht-Linearität. XGBoost kann Schwellenwert-Effekte (Starkregen, Extremtemperatur) erkennen, wo Pearson-r versagt. Feature-Engineering-Ideen (Extremwert-Flags, Interaktionen Regen × Distrikt) → Phase 3.

### Outlier Detection


```python
inspect_outliers(df_eda)
# inspect_outlier_detail(df_eda, 'your_col')
```

    
    [1m[38;2;52;97;141m───  OUTLIERS  ───────────────────────────────────────────────[0m



<style type="text/css">
#T_5f0df thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_5f0df td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_5f0df tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_5f0df tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_5f0df tr:hover td {
  background-color: #eef3f8;
}
#T_5f0df_row0_col0, #T_5f0df_row1_col0, #T_5f0df_row2_col0, #T_5f0df_row3_col0, #T_5f0df_row4_col0, #T_5f0df_row5_col0, #T_5f0df_row6_col0, #T_5f0df_row7_col0, #T_5f0df_row8_col0, #T_5f0df_row9_col0, #T_5f0df_row10_col0, #T_5f0df_row11_col0, #T_5f0df_row12_col0, #T_5f0df_row13_col0, #T_5f0df_row14_col0 {
  text-align: left;
}
#T_5f0df_row0_col1, #T_5f0df_row0_col2, #T_5f0df_row0_col3, #T_5f0df_row0_col4, #T_5f0df_row0_col5, #T_5f0df_row0_col7, #T_5f0df_row0_col8, #T_5f0df_row0_col9, #T_5f0df_row0_col10, #T_5f0df_row0_col11, #T_5f0df_row1_col1, #T_5f0df_row1_col2, #T_5f0df_row1_col3, #T_5f0df_row1_col4, #T_5f0df_row1_col5, #T_5f0df_row1_col7, #T_5f0df_row1_col8, #T_5f0df_row1_col9, #T_5f0df_row1_col10, #T_5f0df_row1_col11, #T_5f0df_row2_col1, #T_5f0df_row2_col2, #T_5f0df_row2_col3, #T_5f0df_row2_col4, #T_5f0df_row2_col5, #T_5f0df_row2_col7, #T_5f0df_row2_col8, #T_5f0df_row2_col9, #T_5f0df_row2_col10, #T_5f0df_row2_col11, #T_5f0df_row3_col1, #T_5f0df_row3_col2, #T_5f0df_row3_col3, #T_5f0df_row3_col4, #T_5f0df_row3_col5, #T_5f0df_row3_col7, #T_5f0df_row3_col8, #T_5f0df_row3_col9, #T_5f0df_row3_col10, #T_5f0df_row3_col11, #T_5f0df_row4_col1, #T_5f0df_row4_col2, #T_5f0df_row4_col3, #T_5f0df_row4_col4, #T_5f0df_row4_col5, #T_5f0df_row4_col7, #T_5f0df_row4_col8, #T_5f0df_row4_col9, #T_5f0df_row4_col10, #T_5f0df_row4_col11, #T_5f0df_row5_col1, #T_5f0df_row5_col2, #T_5f0df_row5_col3, #T_5f0df_row5_col4, #T_5f0df_row5_col5, #T_5f0df_row5_col7, #T_5f0df_row5_col8, #T_5f0df_row5_col9, #T_5f0df_row5_col10, #T_5f0df_row5_col11, #T_5f0df_row6_col1, #T_5f0df_row6_col2, #T_5f0df_row6_col3, #T_5f0df_row6_col4, #T_5f0df_row6_col5, #T_5f0df_row6_col7, #T_5f0df_row6_col8, #T_5f0df_row6_col9, #T_5f0df_row6_col10, #T_5f0df_row6_col11, #T_5f0df_row7_col1, #T_5f0df_row7_col2, #T_5f0df_row7_col3, #T_5f0df_row7_col4, #T_5f0df_row7_col5, #T_5f0df_row7_col7, #T_5f0df_row7_col8, #T_5f0df_row7_col9, #T_5f0df_row7_col10, #T_5f0df_row7_col11, #T_5f0df_row8_col1, #T_5f0df_row8_col2, #T_5f0df_row8_col3, #T_5f0df_row8_col4, #T_5f0df_row8_col5, #T_5f0df_row8_col7, #T_5f0df_row8_col8, #T_5f0df_row8_col9, #T_5f0df_row8_col10, #T_5f0df_row8_col11, #T_5f0df_row9_col1, #T_5f0df_row9_col2, #T_5f0df_row9_col3, #T_5f0df_row9_col4, #T_5f0df_row9_col5, #T_5f0df_row9_col7, #T_5f0df_row9_col8, #T_5f0df_row9_col9, #T_5f0df_row9_col10, #T_5f0df_row9_col11, #T_5f0df_row10_col1, #T_5f0df_row10_col2, #T_5f0df_row10_col3, #T_5f0df_row10_col4, #T_5f0df_row10_col5, #T_5f0df_row10_col7, #T_5f0df_row10_col8, #T_5f0df_row10_col9, #T_5f0df_row10_col10, #T_5f0df_row10_col11, #T_5f0df_row11_col1, #T_5f0df_row11_col2, #T_5f0df_row11_col3, #T_5f0df_row11_col4, #T_5f0df_row11_col5, #T_5f0df_row11_col6, #T_5f0df_row11_col7, #T_5f0df_row11_col8, #T_5f0df_row11_col9, #T_5f0df_row11_col10, #T_5f0df_row11_col11, #T_5f0df_row12_col1, #T_5f0df_row12_col2, #T_5f0df_row12_col3, #T_5f0df_row12_col4, #T_5f0df_row12_col5, #T_5f0df_row12_col6, #T_5f0df_row12_col7, #T_5f0df_row12_col8, #T_5f0df_row12_col9, #T_5f0df_row12_col10, #T_5f0df_row12_col11, #T_5f0df_row13_col1, #T_5f0df_row13_col2, #T_5f0df_row13_col3, #T_5f0df_row13_col4, #T_5f0df_row13_col5, #T_5f0df_row13_col6, #T_5f0df_row13_col7, #T_5f0df_row13_col8, #T_5f0df_row13_col9, #T_5f0df_row13_col10, #T_5f0df_row13_col11, #T_5f0df_row14_col1, #T_5f0df_row14_col2, #T_5f0df_row14_col3, #T_5f0df_row14_col4, #T_5f0df_row14_col5, #T_5f0df_row14_col6, #T_5f0df_row14_col7, #T_5f0df_row14_col8, #T_5f0df_row14_col9, #T_5f0df_row14_col10, #T_5f0df_row14_col11 {
  text-align: right;
}
#T_5f0df_row0_col6, #T_5f0df_row1_col6, #T_5f0df_row2_col6, #T_5f0df_row3_col6, #T_5f0df_row4_col6, #T_5f0df_row5_col6, #T_5f0df_row6_col6, #T_5f0df_row7_col6, #T_5f0df_row8_col6, #T_5f0df_row9_col6, #T_5f0df_row10_col6 {
  text-align: right;
  color: #de425b;
  font-weight: 500;
}
</style>
<table id="T_5f0df">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_5f0df_level0_col0" class="col_heading level0 col0" >column</th>
      <th id="T_5f0df_level0_col1" class="col_heading level0 col1" >mean</th>
      <th id="T_5f0df_level0_col2" class="col_heading level0 col2" >median</th>
      <th id="T_5f0df_level0_col3" class="col_heading level0 col3" >mean_med_diff</th>
      <th id="T_5f0df_level0_col4" class="col_heading level0 col4" >lower_1.5x</th>
      <th id="T_5f0df_level0_col5" class="col_heading level0 col5" >upper_1.5x</th>
      <th id="T_5f0df_level0_col6" class="col_heading level0 col6" >outliers_1.5x</th>
      <th id="T_5f0df_level0_col7" class="col_heading level0 col7" >outliers_1.5x_%</th>
      <th id="T_5f0df_level0_col8" class="col_heading level0 col8" >lower_3x</th>
      <th id="T_5f0df_level0_col9" class="col_heading level0 col9" >upper_3x</th>
      <th id="T_5f0df_level0_col10" class="col_heading level0 col10" >outliers_3x</th>
      <th id="T_5f0df_level0_col11" class="col_heading level0 col11" >outliers_3x_%</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_5f0df_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_5f0df_row0_col0" class="data row0 col0" >bpuic</td>
      <td id="T_5f0df_row0_col1" class="data row0 col1" >9399000.77</td>
      <td id="T_5f0df_row0_col2" class="data row0 col2" >8591220.00</td>
      <td id="T_5f0df_row0_col3" class="data row0 col3" >807780.77</td>
      <td id="T_5f0df_row0_col4" class="data row0 col4" >8590647.50</td>
      <td id="T_5f0df_row0_col5" class="data row0 col5" >8591747.50</td>
      <td id="T_5f0df_row0_col6" class="data row0 col6" >1004444</td>
      <td id="T_5f0df_row0_col7" class="data row0 col7" >21.29%</td>
      <td id="T_5f0df_row0_col8" class="data row0 col8" >8590235.00</td>
      <td id="T_5f0df_row0_col9" class="data row0 col9" >8592160.00</td>
      <td id="T_5f0df_row0_col10" class="data row0 col10" >865219</td>
      <td id="T_5f0df_row0_col11" class="data row0 col11" >18.34%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_5f0df_row1_col0" class="data row1 col0" >rain_duration</td>
      <td id="T_5f0df_row1_col1" class="data row1 col1" >5.92</td>
      <td id="T_5f0df_row1_col2" class="data row1 col2" >0.00</td>
      <td id="T_5f0df_row1_col3" class="data row1 col3" >5.92</td>
      <td id="T_5f0df_row1_col4" class="data row1 col4" >0.00</td>
      <td id="T_5f0df_row1_col5" class="data row1 col5" >0.00</td>
      <td id="T_5f0df_row1_col6" class="data row1 col6" >878234</td>
      <td id="T_5f0df_row1_col7" class="data row1 col7" >18.67%</td>
      <td id="T_5f0df_row1_col8" class="data row1 col8" >0.00</td>
      <td id="T_5f0df_row1_col9" class="data row1 col9" >0.00</td>
      <td id="T_5f0df_row1_col10" class="data row1 col10" >878234</td>
      <td id="T_5f0df_row1_col11" class="data row1 col11" >18.67%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_5f0df_row2_col0" class="data row2 col0" >precipitation</td>
      <td id="T_5f0df_row2_col1" class="data row2 col1" >0.12</td>
      <td id="T_5f0df_row2_col2" class="data row2 col2" >0.00</td>
      <td id="T_5f0df_row2_col3" class="data row2 col3" >0.12</td>
      <td id="T_5f0df_row2_col4" class="data row2 col4" >0.00</td>
      <td id="T_5f0df_row2_col5" class="data row2 col5" >0.00</td>
      <td id="T_5f0df_row2_col6" class="data row2 col6" >536327</td>
      <td id="T_5f0df_row2_col7" class="data row2 col7" >11.40%</td>
      <td id="T_5f0df_row2_col8" class="data row2 col8" >0.00</td>
      <td id="T_5f0df_row2_col9" class="data row2 col9" >0.00</td>
      <td id="T_5f0df_row2_col10" class="data row2 col10" >536327</td>
      <td id="T_5f0df_row2_col11" class="data row2 col11" >11.40%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_5f0df_row3_col0" class="data row3 col0" >stop_lon</td>
      <td id="T_5f0df_row3_col1" class="data row3 col1" >8.54</td>
      <td id="T_5f0df_row3_col2" class="data row3 col2" >8.54</td>
      <td id="T_5f0df_row3_col3" class="data row3 col3" >-0.00</td>
      <td id="T_5f0df_row3_col4" class="data row3 col4" >8.49</td>
      <td id="T_5f0df_row3_col5" class="data row3 col5" >8.58</td>
      <td id="T_5f0df_row3_col6" class="data row3 col6" >326261</td>
      <td id="T_5f0df_row3_col7" class="data row3 col7" >6.92%</td>
      <td id="T_5f0df_row3_col8" class="data row3 col8" >8.46</td>
      <td id="T_5f0df_row3_col9" class="data row3 col9" >8.62</td>
      <td id="T_5f0df_row3_col10" class="data row3 col10" >29764</td>
      <td id="T_5f0df_row3_col11" class="data row3 col11" >0.63%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_5f0df_row4_col0" class="data row4 col0" >arrival_delay</td>
      <td id="T_5f0df_row4_col1" class="data row4 col1" >56.16</td>
      <td id="T_5f0df_row4_col2" class="data row4 col2" >42.00</td>
      <td id="T_5f0df_row4_col3" class="data row4 col3" >14.16</td>
      <td id="T_5f0df_row4_col4" class="data row4 col4" >-91.50</td>
      <td id="T_5f0df_row4_col5" class="data row4 col5" >184.50</td>
      <td id="T_5f0df_row4_col6" class="data row4 col6" >234247</td>
      <td id="T_5f0df_row4_col7" class="data row4 col7" >4.98%</td>
      <td id="T_5f0df_row4_col8" class="data row4 col8" >-195.00</td>
      <td id="T_5f0df_row4_col9" class="data row4 col9" >288.00</td>
      <td id="T_5f0df_row4_col10" class="data row4 col10" >71547</td>
      <td id="T_5f0df_row4_col11" class="data row4 col11" >1.52%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_5f0df_row5_col0" class="data row5 col0" >global_radiation</td>
      <td id="T_5f0df_row5_col1" class="data row5 col1" >185.12</td>
      <td id="T_5f0df_row5_col2" class="data row5 col2" >65.46</td>
      <td id="T_5f0df_row5_col3" class="data row5 col3" >119.66</td>
      <td id="T_5f0df_row5_col4" class="data row5 col4" >-444.79</td>
      <td id="T_5f0df_row5_col5" class="data row5 col5" >741.40</td>
      <td id="T_5f0df_row5_col6" class="data row5 col6" >228357</td>
      <td id="T_5f0df_row5_col7" class="data row5 col7" >4.85%</td>
      <td id="T_5f0df_row5_col8" class="data row5 col8" >-889.62</td>
      <td id="T_5f0df_row5_col9" class="data row5 col9" >1186.23</td>
      <td id="T_5f0df_row5_col10" class="data row5 col10" >0</td>
      <td id="T_5f0df_row5_col11" class="data row5 col11" >0.00%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_5f0df_row6_col0" class="data row6 col0" >departure_delay</td>
      <td id="T_5f0df_row6_col1" class="data row6 col1" >61.76</td>
      <td id="T_5f0df_row6_col2" class="data row6 col2" >47.00</td>
      <td id="T_5f0df_row6_col3" class="data row6 col3" >14.76</td>
      <td id="T_5f0df_row6_col4" class="data row6 col4" >-92.00</td>
      <td id="T_5f0df_row6_col5" class="data row6 col5" >196.00</td>
      <td id="T_5f0df_row6_col6" class="data row6 col6" >220501</td>
      <td id="T_5f0df_row6_col7" class="data row6 col7" >4.68%</td>
      <td id="T_5f0df_row6_col8" class="data row6 col8" >-200.00</td>
      <td id="T_5f0df_row6_col9" class="data row6 col9" >304.00</td>
      <td id="T_5f0df_row6_col10" class="data row6 col10" >66920</td>
      <td id="T_5f0df_row6_col11" class="data row6 col11" >1.42%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_5f0df_row7_col0" class="data row7 col0" >flood_intensity</td>
      <td id="T_5f0df_row7_col1" class="data row7 col1" >0.07</td>
      <td id="T_5f0df_row7_col2" class="data row7 col2" >0.00</td>
      <td id="T_5f0df_row7_col3" class="data row7 col3" >0.07</td>
      <td id="T_5f0df_row7_col4" class="data row7 col4" >0.00</td>
      <td id="T_5f0df_row7_col5" class="data row7 col5" >0.00</td>
      <td id="T_5f0df_row7_col6" class="data row7 col6" >208178</td>
      <td id="T_5f0df_row7_col7" class="data row7 col7" >4.42%</td>
      <td id="T_5f0df_row7_col8" class="data row7 col8" >0.00</td>
      <td id="T_5f0df_row7_col9" class="data row7 col9" >0.00</td>
      <td id="T_5f0df_row7_col10" class="data row7 col10" >208178</td>
      <td id="T_5f0df_row7_col11" class="data row7 col11" >4.42%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_5f0df_row8_col0" class="data row8 col0" >wind_speed</td>
      <td id="T_5f0df_row8_col1" class="data row8 col1" >1.93</td>
      <td id="T_5f0df_row8_col2" class="data row8 col2" >1.74</td>
      <td id="T_5f0df_row8_col3" class="data row8 col3" >0.19</td>
      <td id="T_5f0df_row8_col4" class="data row8 col4" >-0.68</td>
      <td id="T_5f0df_row8_col5" class="data row8 col5" >4.32</td>
      <td id="T_5f0df_row8_col6" class="data row8 col6" >139595</td>
      <td id="T_5f0df_row8_col7" class="data row8 col7" >2.97%</td>
      <td id="T_5f0df_row8_col8" class="data row8 col8" >-2.56</td>
      <td id="T_5f0df_row8_col9" class="data row8 col9" >6.19</td>
      <td id="T_5f0df_row8_col10" class="data row8 col10" >15344</td>
      <td id="T_5f0df_row8_col11" class="data row8 col11" >0.33%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_5f0df_row9_col0" class="data row9 col0" >stop_lat</td>
      <td id="T_5f0df_row9_col1" class="data row9 col1" >47.38</td>
      <td id="T_5f0df_row9_col2" class="data row9 col2" >47.38</td>
      <td id="T_5f0df_row9_col3" class="data row9 col3" >0.00</td>
      <td id="T_5f0df_row9_col4" class="data row9 col4" >47.33</td>
      <td id="T_5f0df_row9_col5" class="data row9 col5" >47.43</td>
      <td id="T_5f0df_row9_col6" class="data row9 col6" >89644</td>
      <td id="T_5f0df_row9_col7" class="data row9 col7" >1.90%</td>
      <td id="T_5f0df_row9_col8" class="data row9 col8" >47.29</td>
      <td id="T_5f0df_row9_col9" class="data row9 col9" >47.47</td>
      <td id="T_5f0df_row9_col10" class="data row9 col10" >0</td>
      <td id="T_5f0df_row9_col11" class="data row9 col11" >0.00%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_5f0df_row10_col0" class="data row10 col0" >stop_sequence</td>
      <td id="T_5f0df_row10_col1" class="data row10 col1" >12.77</td>
      <td id="T_5f0df_row10_col2" class="data row10 col2" >11.00</td>
      <td id="T_5f0df_row10_col3" class="data row10 col3" >1.77</td>
      <td id="T_5f0df_row10_col4" class="data row10 col4" >-13.50</td>
      <td id="T_5f0df_row10_col5" class="data row10 col5" >38.50</td>
      <td id="T_5f0df_row10_col6" class="data row10 col6" >31850</td>
      <td id="T_5f0df_row10_col7" class="data row10 col7" >0.68%</td>
      <td id="T_5f0df_row10_col8" class="data row10 col8" >-33.00</td>
      <td id="T_5f0df_row10_col9" class="data row10 col9" >58.00</td>
      <td id="T_5f0df_row10_col10" class="data row10 col10" >2469</td>
      <td id="T_5f0df_row10_col11" class="data row10 col11" >0.05%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_5f0df_row11_col0" class="data row11 col0" >district_nr</td>
      <td id="T_5f0df_row11_col1" class="data row11 col1" >5.24</td>
      <td id="T_5f0df_row11_col2" class="data row11 col2" >5.00</td>
      <td id="T_5f0df_row11_col3" class="data row11 col3" >0.24</td>
      <td id="T_5f0df_row11_col4" class="data row11 col4" >-5.50</td>
      <td id="T_5f0df_row11_col5" class="data row11 col5" >14.50</td>
      <td id="T_5f0df_row11_col6" class="data row11 col6" >0</td>
      <td id="T_5f0df_row11_col7" class="data row11 col7" >0.00%</td>
      <td id="T_5f0df_row11_col8" class="data row11 col8" >-13.00</td>
      <td id="T_5f0df_row11_col9" class="data row11 col9" >22.00</td>
      <td id="T_5f0df_row11_col10" class="data row11 col10" >0</td>
      <td id="T_5f0df_row11_col11" class="data row11 col11" >0.00%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_5f0df_row12_col0" class="data row12 col0" >humidity</td>
      <td id="T_5f0df_row12_col1" class="data row12 col1" >67.58</td>
      <td id="T_5f0df_row12_col2" class="data row12 col2" >70.61</td>
      <td id="T_5f0df_row12_col3" class="data row12 col3" >-3.03</td>
      <td id="T_5f0df_row12_col4" class="data row12 col4" >17.34</td>
      <td id="T_5f0df_row12_col5" class="data row12 col5" >119.50</td>
      <td id="T_5f0df_row12_col6" class="data row12 col6" >0</td>
      <td id="T_5f0df_row12_col7" class="data row12 col7" >0.00%</td>
      <td id="T_5f0df_row12_col8" class="data row12 col8" >-20.97</td>
      <td id="T_5f0df_row12_col9" class="data row12 col9" >157.81</td>
      <td id="T_5f0df_row12_col10" class="data row12 col10" >0</td>
      <td id="T_5f0df_row12_col11" class="data row12 col11" >0.00%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_5f0df_row13_col0" class="data row13 col0" >temperature</td>
      <td id="T_5f0df_row13_col1" class="data row13 col1" >13.20</td>
      <td id="T_5f0df_row13_col2" class="data row13 col2" >12.48</td>
      <td id="T_5f0df_row13_col3" class="data row13 col3" >0.72</td>
      <td id="T_5f0df_row13_col4" class="data row13 col4" >-11.02</td>
      <td id="T_5f0df_row13_col5" class="data row13 col5" >37.46</td>
      <td id="T_5f0df_row13_col6" class="data row13 col6" >0</td>
      <td id="T_5f0df_row13_col7" class="data row13 col7" >0.00%</td>
      <td id="T_5f0df_row13_col8" class="data row13 col8" >-29.20</td>
      <td id="T_5f0df_row13_col9" class="data row13 col9" >55.64</td>
      <td id="T_5f0df_row13_col10" class="data row13 col10" >0</td>
      <td id="T_5f0df_row13_col11" class="data row13 col11" >0.00%</td>
    </tr>
    <tr>
      <th id="T_5f0df_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_5f0df_row14_col0" class="data row14 col0" >event_size</td>
      <td id="T_5f0df_row14_col1" class="data row14 col1" >1.46</td>
      <td id="T_5f0df_row14_col2" class="data row14 col2" >1.00</td>
      <td id="T_5f0df_row14_col3" class="data row14 col3" >0.46</td>
      <td id="T_5f0df_row14_col4" class="data row14 col4" >-0.50</td>
      <td id="T_5f0df_row14_col5" class="data row14 col5" >3.50</td>
      <td id="T_5f0df_row14_col6" class="data row14 col6" >0</td>
      <td id="T_5f0df_row14_col7" class="data row14 col7" >0.00%</td>
      <td id="T_5f0df_row14_col8" class="data row14 col8" >-2.00</td>
      <td id="T_5f0df_row14_col9" class="data row14 col9" >5.00</td>
      <td id="T_5f0df_row14_col10" class="data row14 col10" >0</td>
      <td id="T_5f0df_row14_col11" class="data row14 col11" >0.00%</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141m→ inspect_outlier_detail(df, col) for boxplot+histogram per feature.[0m





<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>column</th>
      <th>mean</th>
      <th>median</th>
      <th>mean_med_diff</th>
      <th>lower_1.5x</th>
      <th>upper_1.5x</th>
      <th>outliers_1.5x</th>
      <th>outliers_1.5x_%</th>
      <th>lower_3x</th>
      <th>upper_3x</th>
      <th>outliers_3x</th>
      <th>outliers_3x_%</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>bpuic</td>
      <td>9399000.77</td>
      <td>8591220.00</td>
      <td>807780.77</td>
      <td>8590647.50</td>
      <td>8591747.50</td>
      <td>1004444</td>
      <td>21.29</td>
      <td>8590235.00</td>
      <td>8592160.00</td>
      <td>865219</td>
      <td>18.34</td>
    </tr>
    <tr>
      <th>1</th>
      <td>rain_duration</td>
      <td>5.92</td>
      <td>0.00</td>
      <td>5.92</td>
      <td>0.00</td>
      <td>0.00</td>
      <td>878234</td>
      <td>18.67</td>
      <td>0.00</td>
      <td>0.00</td>
      <td>878234</td>
      <td>18.67</td>
    </tr>
    <tr>
      <th>2</th>
      <td>precipitation</td>
      <td>0.12</td>
      <td>0.00</td>
      <td>0.12</td>
      <td>0.00</td>
      <td>0.00</td>
      <td>536327</td>
      <td>11.40</td>
      <td>0.00</td>
      <td>0.00</td>
      <td>536327</td>
      <td>11.40</td>
    </tr>
    <tr>
      <th>3</th>
      <td>stop_lon</td>
      <td>8.54</td>
      <td>8.54</td>
      <td>-0.00</td>
      <td>8.49</td>
      <td>8.58</td>
      <td>326261</td>
      <td>6.92</td>
      <td>8.46</td>
      <td>8.62</td>
      <td>29764</td>
      <td>0.63</td>
    </tr>
    <tr>
      <th>4</th>
      <td>arrival_delay</td>
      <td>56.16</td>
      <td>42.00</td>
      <td>14.16</td>
      <td>-91.50</td>
      <td>184.50</td>
      <td>234247</td>
      <td>4.98</td>
      <td>-195.00</td>
      <td>288.00</td>
      <td>71547</td>
      <td>1.52</td>
    </tr>
    <tr>
      <th>5</th>
      <td>global_radiation</td>
      <td>185.12</td>
      <td>65.46</td>
      <td>119.66</td>
      <td>-444.79</td>
      <td>741.40</td>
      <td>228357</td>
      <td>4.85</td>
      <td>-889.62</td>
      <td>1186.23</td>
      <td>0</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>6</th>
      <td>departure_delay</td>
      <td>61.76</td>
      <td>47.00</td>
      <td>14.76</td>
      <td>-92.00</td>
      <td>196.00</td>
      <td>220501</td>
      <td>4.68</td>
      <td>-200.00</td>
      <td>304.00</td>
      <td>66920</td>
      <td>1.42</td>
    </tr>
    <tr>
      <th>7</th>
      <td>flood_intensity</td>
      <td>0.07</td>
      <td>0.00</td>
      <td>0.07</td>
      <td>0.00</td>
      <td>0.00</td>
      <td>208178</td>
      <td>4.42</td>
      <td>0.00</td>
      <td>0.00</td>
      <td>208178</td>
      <td>4.42</td>
    </tr>
    <tr>
      <th>8</th>
      <td>wind_speed</td>
      <td>1.93</td>
      <td>1.74</td>
      <td>0.19</td>
      <td>-0.68</td>
      <td>4.32</td>
      <td>139595</td>
      <td>2.97</td>
      <td>-2.56</td>
      <td>6.19</td>
      <td>15344</td>
      <td>0.33</td>
    </tr>
    <tr>
      <th>9</th>
      <td>stop_lat</td>
      <td>47.38</td>
      <td>47.38</td>
      <td>0.00</td>
      <td>47.33</td>
      <td>47.43</td>
      <td>89644</td>
      <td>1.90</td>
      <td>47.29</td>
      <td>47.47</td>
      <td>0</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>10</th>
      <td>stop_sequence</td>
      <td>12.77</td>
      <td>11.00</td>
      <td>1.77</td>
      <td>-13.50</td>
      <td>38.50</td>
      <td>31850</td>
      <td>0.68</td>
      <td>-33.00</td>
      <td>58.00</td>
      <td>2469</td>
      <td>0.05</td>
    </tr>
    <tr>
      <th>11</th>
      <td>district_nr</td>
      <td>5.24</td>
      <td>5.00</td>
      <td>0.24</td>
      <td>-5.50</td>
      <td>14.50</td>
      <td>0</td>
      <td>0.00</td>
      <td>-13.00</td>
      <td>22.00</td>
      <td>0</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>12</th>
      <td>humidity</td>
      <td>67.58</td>
      <td>70.61</td>
      <td>-3.03</td>
      <td>17.34</td>
      <td>119.50</td>
      <td>0</td>
      <td>0.00</td>
      <td>-20.97</td>
      <td>157.81</td>
      <td>0</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>13</th>
      <td>temperature</td>
      <td>13.20</td>
      <td>12.48</td>
      <td>0.72</td>
      <td>-11.02</td>
      <td>37.46</td>
      <td>0</td>
      <td>0.00</td>
      <td>-29.20</td>
      <td>55.64</td>
      <td>0</td>
      <td>0.00</td>
    </tr>
    <tr>
      <th>14</th>
      <td>event_size</td>
      <td>1.46</td>
      <td>1.00</td>
      <td>0.46</td>
      <td>-0.50</td>
      <td>3.50</td>
      <td>0</td>
      <td>0.00</td>
      <td>-2.00</td>
      <td>5.00</td>
      <td>0</td>
      <td>0.00</td>
    </tr>
  </tbody>
</table>
</div>



#### Delay-Features — Outlier Detail (IQR 1.5× und 3×)


```python
section_header('Delay Outlier — Vor / Nach Bereinigung')
log(f"Roh: {len(df_eda):,} Zeilen  →  Bereinigt: {len(df_delays_clean):,} Zeilen  "
    f"({len(df_eda) - len(df_delays_clean):,} entfernt, "
    f"{(len(df_eda) - len(df_delays_clean)) / len(df_eda) * 100:.3f}%)")

print("\n── arrival_delay  ROH ──")
inspect_outlier_detail(df_eda, "arrival_delay")

print("\n── arrival_delay  BEREINIGT (|delay| ≤ 3.600s) ──")
inspect_outlier_detail(df_delays_clean, "arrival_delay")

print("\n── departure_delay  ROH ──")
inspect_outlier_detail(df_eda, "departure_delay")

print("\n── departure_delay  BEREINIGT ──")
inspect_outlier_detail(df_delays_clean, "departure_delay")
```

    
    [1m[38;2;52;97;141m───  DELAY OUTLIER — VOR / NACH BEREINIGUNG  ─────────────────[0m
    [38;2;52;97;141mRoh: 4,717,926 Zeilen  →  Bereinigt: 4,706,348 Zeilen  (11,578 entfernt, 0.245%)[0m
    
    ── arrival_delay  ROH ──



    
![png](01_exploration_files/01_exploration_52_1.png)
    


    
    ── arrival_delay  BEREINIGT (|delay| ≤ 3.600s) ──



    
![png](01_exploration_files/01_exploration_52_3.png)
    


    
    ── departure_delay  ROH ──



    
![png](01_exploration_files/01_exploration_52_5.png)
    


    
    ── departure_delay  BEREINIGT ──



    
![png](01_exploration_files/01_exploration_52_7.png)
    


#### Meteo-Features — Outlier Detail (precipitation, wind_speed, temperature)


```python
from wgnd.core.theme import mpl_style
from wgnd.core.config import cfg

section_header('Meteo Outlier Detail')

# wind_speed und temperature: inspect_outlier_detail reicht
inspect_outlier_detail(df_eda, "wind_speed")
inspect_outlier_detail(df_eda, "temperature")

# precipitation: Zero-Inflation + Log-Skala Gegenüberstellung
section_header('Precipitation — Normal vs. Log-Skala')

style = mpl_style()
data      = df_eda["precipitation"].dropna()
data_nz   = data[data > 0]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Links: Normal — Zero-Inflation sichtbar
axes[0].hist(data, bins=60, color=cfg.COLOR_NEGATIVE, alpha=0.85, edgecolor="none")
axes[0].set_title("Normal-Skala — Zero-Inflation dominiert", **style["title"])
axes[0].set_xlabel("precipitation (mm)", **style["label"])
axes[0].set_ylabel("Häufigkeit", **style["label"])
axes[0].spines[["top", "right"]].set_visible(False)
axes[0].spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

# Rechts: Log-Skala, nur Regen-Stunden
axes[1].hist(data_nz, bins=60, color=cfg.ACTIVE_PALETTE[0], alpha=0.85, edgecolor="none")
axes[1].set_xscale("log")
axes[1].set_title(f"Log-Skala — nur Regen-Stunden (n={len(data_nz):,})", **style["title"])
axes[1].set_xlabel("precipitation (mm, log)", **style["label"])
axes[1].set_ylabel("Häufigkeit", **style["label"])
axes[1].axvline(data_nz.median(), color=cfg.COLOR_SIGNAL, linewidth=1.5,
                linestyle="--", label=f"Median: {data_nz.median():.1f}mm")
axes[1].axvline(data_nz.mean(), color=cfg.COLOR_POSITIVE, linewidth=1.5,
                linestyle="--", label=f"Mean: {data_nz.mean():.1f}mm")
axes[1].legend(fontsize=10)
axes[1].spines[["top", "right"]].set_visible(False)
axes[1].spines[["left", "bottom"]].set_color(cfg.CHART_AXIS)

plt.suptitle("precipitation — Zero-Inflation und echte Regenverteilung",
             fontsize=14, color=cfg.CHART_TITLE, ha="left", x=0.02, y=1.02)
plt.tight_layout()
plt.show()

success(f"Regen-Stunden: {len(data_nz):,} von {len(data):,} "
        f"({len(data_nz)/len(data)*100:.1f}%) — "
        f"{100 - len(data_nz)/len(data)*100:.1f}% sind 0")
```

    
    [1m[38;2;52;97;141m───  METEO OUTLIER DETAIL  ───────────────────────────────────[0m



    
![png](01_exploration_files/01_exploration_54_1.png)
    



    
![png](01_exploration_files/01_exploration_54_2.png)
    


    
    [1m[38;2;52;97;141m───  PRECIPITATION — NORMAL VS. LOG-SKALA  ───────────────────[0m



    
![png](01_exploration_files/01_exploration_54_4.png)
    


    [38;2;52;97;141m✓  Regen-Stunden: 536,327 von 4,706,111 (11.4%) — 88.6% sind 0[0m


#### Outlier-Findings

| # | Feature | Skewness | IQR 1.5× Outlier | IQR 3× Outlier | Muster | Vorgehen |
|:---|:---|:---:|:---|:---|:---|:---|
| O1 | `arrival_delay` | 38.6 | hoch | 0.005% (4.707) | Langer rechter Schwanz, extreme Einzelwerte | Rausfiltern `\|delay\| > 3.600s` |
| O2 | `departure_delay` | 42.9 | hoch | 0.005% (4.707) | Identisch zu O1 — systematischer Fehler | Gleiche Grenze wie O1 |
| O3 | `precipitation` | 11.6 | sehr hoch | — | Zero-Inflated: IQR ≈ 0, jeder Regen = statistischer Ausreißer | Kein Clip — binäres Flag `hat_regen` + Wert behalten |
| O4 | `wind_speed` | 1.34 | moderat | — | Leichter Skew, Sturmtage als Ausreißer plausibel | Kein Clip — Extremwerte sind real und modellrelevant |
| O5 | `temperature` | ~0 | minimal | — | Saubere Normalverteilung, keine echten Ausreißer | Keine Bereinigung nötig |

### Features Inspection



**Engineering Inspection**


```python
# Feature Engineering — erste Ideen aus der EDA (Umsetzung in 02_preparation.ipynb)
#
# Zeitfeatures
# stunde         : arrival_schedule.dt.hour          → Tagesrhythmus
# wochentag      : arrival_schedule.dt.weekday       → Mo=0, So=6
# monat          : arrival_schedule.dt.month         → Saisonalität (R3: Events saisonal)
# ist_wochenende : wochentag >= 5
# ist_hvz        : stunde in [7,8,9,17,18,19]        → Hauptverkehrszeit
#
# Binäre Extremwert-Flags (aus R2/R4/O3)
# hat_regen      : precipitation > 0
# hat_starkregen : precipitation > 5.0               → Schwellenwert aus Viz (Log-Skala)
# hat_flut       : flood_intensity > 0
# hat_wind       : wind_speed > 40                   → nach Outlier-Analyse bestimmen
#
# Kategoriale Encodings
# line_name      : Label-Encoding oder Target-Encoding
# district_name  : Label-Encoding (inkl. Kategorie "ausserhalb" für Nulls)
# event_size     : Ordinal — kein Event=0, klein=1, mittel=2, groß=3
# is_canceled    : bereits vorhanden als bool → zu int konvertieren
#
# Interaktionen (für Phase 4, nach Feature Importance)
# hat_regen × district_nr → Welche Stadtkreise leiden bei Regen stärker?
# ist_hvz × line_name     → Welche Linien sind in der HVZ am instabilsten?

print("Feature Engineering — erste Ideen notiert. Umsetzung in 02_preparation.ipynb.")
```

    Feature Engineering — erste Ideen notiert. Umsetzung in 02_preparation.ipynb.


#### Feature-Ideen — Übersicht

| Kategorie | Feature | Basis-Spalte | Begründung |
|:---|:---|:---|:---|
| **Zeit** | `stunde` | `arrival_schedule` | Tagesrhythmus — Rush Hour vs. Randzeiten |
| **Zeit** | `wochentag` | `arrival_schedule` | Werktagsmuster, Wochenend-Effekte |
| **Zeit** | `monat` | `arrival_schedule` | Saisonalität (R3: Events korreliert mit Temp.) |
| **Zeit** | `ist_wochenende` | `wochentag` | Binäres Flag — kompakter als Ordinal |
| **Zeit** | `ist_hvz` | `stunde` | Hauptverkehrszeit 7–9h, 17–19h |
| **Wetter** | `hat_regen` | `precipitation > 0` | Zero-Inflation auflösen (O3) |
| **Wetter** | `hat_starkregen` | `precipitation > 5mm` | Schwellenwert-Effekt aus Viz (R2) |
| **Wetter** | `hat_flut` | `flood_intensity > 0` | Stärkste Wetter-Korrelation r=0.15 (R4) |
| **Wetter** | `hat_wind` | `wind_speed > X` | Schwellenwert nach Outlier-Analyse |
| **Kategorial** | `line_name` enc. | `line_name` | Label- oder Target-Encoding |
| **Kategorial** | `district_name` enc. | `district_name` | inkl. Kategorie `"ausserhalb"` für Nulls |
| **Kategorial** | `event_size` enc. | `event_size` | Ordinal 0–3 (kein Event bis groß) |
| **Kategorial** | `is_canceled` | `canceled` | bool → int (0/1) |
| **Interaktion** | `regen × district` | Kombination | Räumliche Sensitivität bei Regen |
| **Interaktion** | `hvz × linie` | Kombination | Linienstabilität in der Hauptverkehrszeit |

## Key Findings & Next Steps


### Konsolidierte Findings — nach Topic

| Topic | Befund | Empfehlung | Vor Split? |
|:---|:---|:---|:---:|
| **Delay** | Extreme Werte ±8.3h — physikalisch nicht plausibel | Rausfiltern `\|delay\| > 3.600s` | ✓ |
| **Delay** | 74.669 Zeilen: Schedule vorhanden, aber kein Delay | Herausfiltern für Delay-Modell | ✓ |
| **Delay** | `arrival_delay` ↔ `departure_delay` r=0.95 | Nur `arrival_delay` als Zielvariable | — |
| **Delay** | Skewness 38–43 — non-linear, long tail | XGBoost statt lineares Modell | — |
| **Canceled** | 4.5% ausgefallene Fahrten, haben Delay-Werte | Feature `is_canceled`; für Delay-Modell optional herausfiltern | ✓ |
| **BPUIC** | 0.10% anomale IDs > 100.000.000 | Rausfiltern | ✓ |
| **BPUIC** | Nicht als numerisches Feature geeignet | Als kategoriales Label oder Lookup-Key | ✓ |
| **Meteo** | Stündliche Messausfälle (~0.14–0.35%), zeitlich klumpend | Rolling Mean ±2h; `flood_intensity` → `fill_null(0)` | Nach Split |
| **Meteo** | `humidity` > 100% — Sensor-Kalibrierungsdrift | `.clip(0, 100)` | ✓ |
| **Meteo** | `precipitation` zero-inflated (Skewness 11.6) | Flag `hat_regen` + kontinuierlicher Wert behalten | Nach Split |
| **Meteo** | Wetter→Delay: r max 0.03 linear | Schwellenwert-Effekte → XGBoost; Extremwert-Flags als Features | — |
| **Events** | 78.5% null — Normalfall kein Event | `null` → Kategorie `"kein_event"` | ✓ |
| **Events** | Events korreliert mit Temperatur r=0.16 — beide saisonal | Monats-Feature hinzufügen | — |
| **District** | 6.87% null — Haltestellen außerhalb Stadtgebiet | `null` → Kategorie `"ausserhalb"` | ✓ |
| **District** | `stop_lat` ↔ `district_nr` r=0.68 — Multikollinearität | Nicht beide gemeinsam ins Modell | — |
| **Datenqualität** | 1.72% Duplikate | `distinct()` im Cleaning | ✓ |

> **Vor Split?** — ✓ = strukturelles Cleaning (Domainregeln, keine statistischen Parameter → kein Leakage-Risiko)  
> **Nach Split** = statistisch abgeleitete Werte (Rolling Mean, IQR-Grenzen, Encoding) → nur auf Trainingsdaten fitten, auf Testdaten anwenden

### Offene Fragen — alle in der EDA beantwortet

| # | Frage | Antwort |
|---|---|---|
| F1 | Wie viele Zeilen: Schedule ok, aber Delay null? | ~74.669 Zeilen (0.08%) → Herausfiltern |
| F2 | Wie viele Zeilen liegen über ±3.600s? | ~4.707 Zeilen (0.005%) → Rausfiltern |
| F3 | Wie viele anomale BPUICs, welche Linien? | ~91.137 Zeilen (0.10%), mehrere Linien → Rausfiltern |
| F4 | Meteo-Lücken zeitlich klumpend oder zufällig? | Klumpend — Stationsausfälle, alle Sensoren gleichzeitig |
| F5 | Wie viele Humidity-Werte > 100%? | < 5.000 Zeilen — Clip auf 100 reicht |
| F6 | Haben canceled trips Delay-Werte oder sind sie null? | Haben Delay-Werte → als Feature `is_canceled` behalten |

### Prognose der Datensatz-Reduktion nach dem Cleaning

| Cleaning-Schritt | Betroffene Zeilen (ca.) | Anteil | Timing |
|:---|---:|:---:|:---|
| Duplikate entfernen | ~1.500.000 | 1.72% | Vor Split |
| BPUIC > 100.000.000 rausfiltern | ~91.100 | 0.10% | Vor Split |
| Schedule ok, aber Delay null | ~74.700 | 0.08% | Vor Split |
| Extreme Delays \|delay\| > 3.600s | ~4.700 | < 0.01% | Vor Split |
| Humidity clip auf [0, 100] | < 5.000 | < 0.01% | Vor Split |
| Meteo Rolling Mean ±2h (Imputation) | ~130k–315k je Spalte | 0.14–0.35% | Nach Split |
| **Gesamt-Reduktion (strukturell)** | **~1,7 Mio.** | **~2%** | — |

> Nach dem strukturellen Cleaning verbleiben schätzungsweise **~86–87 Mio. Zeilen**.  
> 2025 wird als Test-Jahr reserviert (~15–18 Mio. Zeilen) — Trainingsdatensatz: **~68–72 Mio. Zeilen**.
