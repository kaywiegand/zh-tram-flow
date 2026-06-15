# Spatial Analysis

Where delays accumulate: top delay stops, district breakdown and line comparison.

## Setup


```python
from zh_tram_flow.notebook import *
import zh_tram_flow.analytics.spatial as an

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("03_analysis_4-spatial")

# lf_all   — train + test features combined (all years)
# lf_delay — lf_all filtered: canceled == False
# lf_clean — analysis-ready: canceled=False · stop_sequence>1 · no Linie E/L50/L51
#             departure_delay / delay_delta masked to NaN for Nov 14–Dec 23 2025
#             (is_anomal flag added for transparency)
%load_ext autoreload
%autoreload 2
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-06-11 14:52:36  INFO      project  03_analysis_4-spatial started


    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload


## Top Delay Stops

Stops with highest average `arrival_delay` — potential bottleneck candidates.


```python
an.plot_top_delay_stops(lf_delay, cfg)
log("Top 10 Tabelle")
show_df(an.table_top_delay_stops(lf_delay))
```

    
    [1m[38;2;52;97;141m───  TOP DELAY STOPS  ────────────────────────────────────────[0m



    
![png](03_analysis_4-spatial_files/03_analysis_4-spatial_6_1.png)
    


    [38;2;52;97;141mTop 10 Tabelle[0m



<style type="text/css">
#T_e2fe2 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_e2fe2 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_e2fe2 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_e2fe2 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_e2fe2 tr:hover td {
  background-color: #eef3f8;
}
#T_e2fe2_row0_col0, #T_e2fe2_row1_col0, #T_e2fe2_row2_col0, #T_e2fe2_row3_col0, #T_e2fe2_row4_col0, #T_e2fe2_row5_col0, #T_e2fe2_row6_col0, #T_e2fe2_row7_col0, #T_e2fe2_row8_col0, #T_e2fe2_row9_col0 {
  text-align: left;
}
#T_e2fe2_row0_col1, #T_e2fe2_row0_col2, #T_e2fe2_row0_col3, #T_e2fe2_row1_col1, #T_e2fe2_row1_col2, #T_e2fe2_row1_col3, #T_e2fe2_row2_col1, #T_e2fe2_row2_col2, #T_e2fe2_row2_col3, #T_e2fe2_row3_col1, #T_e2fe2_row3_col2, #T_e2fe2_row3_col3, #T_e2fe2_row4_col1, #T_e2fe2_row4_col2, #T_e2fe2_row4_col3, #T_e2fe2_row5_col1, #T_e2fe2_row5_col2, #T_e2fe2_row5_col3, #T_e2fe2_row6_col1, #T_e2fe2_row6_col2, #T_e2fe2_row6_col3, #T_e2fe2_row7_col1, #T_e2fe2_row7_col2, #T_e2fe2_row7_col3, #T_e2fe2_row8_col1, #T_e2fe2_row8_col2, #T_e2fe2_row8_col3, #T_e2fe2_row9_col1, #T_e2fe2_row9_col2, #T_e2fe2_row9_col3 {
  text-align: right;
}
</style>
<table id="T_e2fe2">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_e2fe2_level0_col0" class="col_heading level0 col0" >Halt</th>
      <th id="T_e2fe2_level0_col1" class="col_heading level0 col1" >Avg. Delay (s)</th>
      <th id="T_e2fe2_level0_col2" class="col_heading level0 col2" >OTP</th>
      <th id="T_e2fe2_level0_col3" class="col_heading level0 col3" >n Stops</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_e2fe2_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_e2fe2_row0_col0" class="data row0 col0" >Zürich, Friedrichstrasse</td>
      <td id="T_e2fe2_row0_col1" class="data row0 col1" >144.60</td>
      <td id="T_e2fe2_row0_col2" class="data row0 col2" >0.60</td>
      <td id="T_e2fe2_row0_col3" class="data row0 col3" >14375</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_e2fe2_row1_col0" class="data row1 col0" >Zürich, Frohburg</td>
      <td id="T_e2fe2_row1_col1" class="data row1 col1" >116.70</td>
      <td id="T_e2fe2_row1_col2" class="data row1 col2" >0.70</td>
      <td id="T_e2fe2_row1_col3" class="data row1 col3" >14390</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_e2fe2_row2_col0" class="data row2 col0" >Zürich, Albisgütli</td>
      <td id="T_e2fe2_row2_col1" class="data row2 col1" >101.80</td>
      <td id="T_e2fe2_row2_col2" class="data row2 col2" >0.70</td>
      <td id="T_e2fe2_row2_col3" class="data row2 col3" >13992</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_e2fe2_row3_col0" class="data row3 col0" >Zürich, Friedhof Enzenbühl</td>
      <td id="T_e2fe2_row3_col1" class="data row3 col1" >93.80</td>
      <td id="T_e2fe2_row3_col2" class="data row3 col2" >0.70</td>
      <td id="T_e2fe2_row3_col3" class="data row3 col3" >292204</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_e2fe2_row4_col0" class="data row4 col0" >Zürich, Balgrist</td>
      <td id="T_e2fe2_row4_col1" class="data row4 col1" >85.20</td>
      <td id="T_e2fe2_row4_col2" class="data row4 col2" >0.80</td>
      <td id="T_e2fe2_row4_col3" class="data row4 col3" >292940</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_e2fe2_row5_col0" class="data row5 col0" >Zürich, Wetlistrasse</td>
      <td id="T_e2fe2_row5_col1" class="data row5 col1" >83.30</td>
      <td id="T_e2fe2_row5_col2" class="data row5 col2" >0.80</td>
      <td id="T_e2fe2_row5_col3" class="data row5 col3" >291455</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_e2fe2_row6_col0" class="data row6 col0" >Zürich, Leutschenbach</td>
      <td id="T_e2fe2_row6_col1" class="data row6 col1" >82.70</td>
      <td id="T_e2fe2_row6_col2" class="data row6 col2" >0.80</td>
      <td id="T_e2fe2_row6_col3" class="data row6 col3" >546617</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_e2fe2_row7_col0" class="data row7 col0" >Zürich, Burgwies</td>
      <td id="T_e2fe2_row7_col1" class="data row7 col1" >81.50</td>
      <td id="T_e2fe2_row7_col2" class="data row7 col2" >0.80</td>
      <td id="T_e2fe2_row7_col3" class="data row7 col3" >290075</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_e2fe2_row8_col0" class="data row8 col0" >Zürich, Butzenstrasse</td>
      <td id="T_e2fe2_row8_col1" class="data row8 col1" >81.00</td>
      <td id="T_e2fe2_row8_col2" class="data row8 col2" >0.80</td>
      <td id="T_e2fe2_row8_col3" class="data row8 col3" >291885</td>
    </tr>
    <tr>
      <th id="T_e2fe2_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_e2fe2_row9_col0" class="data row9 col0" >Zürich, Messe/Hallenstadion</td>
      <td id="T_e2fe2_row9_col1" class="data row9 col1" >79.30</td>
      <td id="T_e2fe2_row9_col2" class="data row9 col2" >0.80</td>
      <td id="T_e2fe2_row9_col3" class="data row9 col3" >285998</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die höchsten Delay-Werte finden sich NICHT bei den zentralen Knotenpunkten, sondern bei **peripheren Endlinien-Haltestellen**.

**Top-10 Haltestellen nach Ø Delay:**
| Rang | Haltestelle | Ø Delay (s) | OTP | n |
|---:|:---|---:|---:|---:|
| 1 | Zürich, Bertastrasse | **181.6** | 44.6% | 1'307 |
| 2 | Zürich, Friedhof Sihlfeld | 167.0 | 49.5% | 1'307 |
| 3 | Zürich, Friedrichstrasse | 144.6 | 56.7% | 14'375 |
| 4 | Zürich, Frohburg | 116.7 | 67.7% | 14'390 |
| 5 | Zürich, Albisgütli | 101.8 | 65.6% | 13'992 |
| 6 | Zürich, Friedhof Enzenbühl | 93.8 | 74.9% | 292'204 |
| 7 | Zürich, Balgrist | 85.2 | 77.0% | 292'940 |

**Interpretationshinweis:** Die Spitzenreiter 1–5 haben sehr niedrige Beobachtungszahlen (n=1'307 für Bertastrasse und Friedhof Sihlfeld) — das sind wahrscheinlich **Sonder- oder Eventlinien** (Albisgütli = L13/17 Sonderbetrieb; Frohburg/Friedhof Sihlfeld = Bestattungsfahrten?). Bei kleinem n sind extreme Mittelwerte statistisch instabil.

Ab Rang 6 (Friedhof Enzenbühl n=292'204) sind die Zahlen belastbar: Diese Haltestellen liegen auf **Aussenkorridoren** (Burgwies, Balgrist, Leutschenbach n=546'617) — nicht im Innenstadtkern.

**Frühankünfte (Terminus-Haltestellen):** Terminus-Halte zeigen negative Arrival Delays — Trams warten am Endpunkt auf den nächsten Abfahrtszeitpunkt. Dieser Effekt ist real, aber **verzerrt den Netzschnitt kaum**: `lf_all` = +55.8s vs. `lf_clean` (Starthalte raus) = +56.9s — Δ nur **+1.0s** (→ `03_analysis_1-target`). Terminus-Frühankünfte sind ein strukturelles Muster, kein Messfehler.

→ `bpuic` / `stop_name` als Feature; niedriges n als Qualitäts-Flag beachten; Sonderbetrieb-Haltestellen durch n-Threshold filtern.

## Linien-Dichte vs. Verspätung

Wie viele verschiedene Linien bedienen jede Haltestelle — und sind die meistfrequentierten Knotenpunkte auch die verspätetsten?


```python
an.plot_lines_density_vs_delay(lf_delay, cfg)
show_df(an.table_lines_density_vs_delay(lf_delay))
```

    Haltestellen in BEIDEN Top-20 (viele Linien + hoher Delay): 0



    
![png](03_analysis_4-spatial_files/03_analysis_4-spatial_9_1.png)
    



<style type="text/css">
#T_a309c thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_a309c td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_a309c tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_a309c tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_a309c tr:hover td {
  background-color: #eef3f8;
}
#T_a309c_row0_col0, #T_a309c_row1_col0, #T_a309c_row2_col0, #T_a309c_row3_col0, #T_a309c_row4_col0, #T_a309c_row5_col0, #T_a309c_row6_col0, #T_a309c_row7_col0, #T_a309c_row8_col0, #T_a309c_row9_col0, #T_a309c_row10_col0, #T_a309c_row11_col0, #T_a309c_row12_col0, #T_a309c_row13_col0, #T_a309c_row14_col0 {
  text-align: left;
}
#T_a309c_row0_col1, #T_a309c_row0_col2, #T_a309c_row0_col3, #T_a309c_row1_col1, #T_a309c_row1_col2, #T_a309c_row1_col3, #T_a309c_row2_col1, #T_a309c_row2_col2, #T_a309c_row2_col3, #T_a309c_row3_col1, #T_a309c_row3_col2, #T_a309c_row3_col3, #T_a309c_row4_col1, #T_a309c_row4_col2, #T_a309c_row4_col3, #T_a309c_row5_col1, #T_a309c_row5_col2, #T_a309c_row5_col3, #T_a309c_row6_col1, #T_a309c_row6_col2, #T_a309c_row6_col3, #T_a309c_row7_col1, #T_a309c_row7_col2, #T_a309c_row7_col3, #T_a309c_row8_col1, #T_a309c_row8_col2, #T_a309c_row8_col3, #T_a309c_row9_col1, #T_a309c_row9_col2, #T_a309c_row9_col3, #T_a309c_row10_col1, #T_a309c_row10_col2, #T_a309c_row10_col3, #T_a309c_row11_col1, #T_a309c_row11_col2, #T_a309c_row11_col3, #T_a309c_row12_col1, #T_a309c_row12_col2, #T_a309c_row12_col3, #T_a309c_row13_col1, #T_a309c_row13_col2, #T_a309c_row13_col3, #T_a309c_row14_col1, #T_a309c_row14_col2, #T_a309c_row14_col3 {
  text-align: right;
}
</style>
<table id="T_a309c">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_a309c_level0_col0" class="col_heading level0 col0" >Stop</th>
      <th id="T_a309c_level0_col1" class="col_heading level0 col1" >Linien</th>
      <th id="T_a309c_level0_col2" class="col_heading level0 col2" >Avg. Delay (s)</th>
      <th id="T_a309c_level0_col3" class="col_heading level0 col3" >N Obs</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_a309c_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_a309c_row0_col0" class="data row0 col0" >Zürich, Haldenegg</td>
      <td id="T_a309c_row0_col1" class="data row0 col1" >15</td>
      <td id="T_a309c_row0_col2" class="data row0 col2" >44.50</td>
      <td id="T_a309c_row0_col3" class="data row0 col3" >1018300</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_a309c_row1_col0" class="data row1 col0" >Zürich, Central</td>
      <td id="T_a309c_row1_col1" class="data row1 col1" >15</td>
      <td id="T_a309c_row1_col2" class="data row1 col2" >48.30</td>
      <td id="T_a309c_row1_col3" class="data row1 col3" >1570105</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_a309c_row2_col0" class="data row2 col0" >Zürich, Werd</td>
      <td id="T_a309c_row2_col1" class="data row2 col1" >15</td>
      <td id="T_a309c_row2_col2" class="data row2 col2" >49.20</td>
      <td id="T_a309c_row2_col3" class="data row2 col3" >570956</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_a309c_row3_col0" class="data row3 col0" >Zürich, Stockerstrasse</td>
      <td id="T_a309c_row3_col1" class="data row3 col1" >15</td>
      <td id="T_a309c_row3_col2" class="data row3 col2" >49.80</td>
      <td id="T_a309c_row3_col3" class="data row3 col3" >1071698</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_a309c_row4_col0" class="data row4 col0" >Zürich, Stauffacher</td>
      <td id="T_a309c_row4_col1" class="data row4 col1" >15</td>
      <td id="T_a309c_row4_col2" class="data row4 col2" >60.70</td>
      <td id="T_a309c_row4_col3" class="data row4 col3" >1456054</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_a309c_row5_col0" class="data row5 col0" >Zürich, Löwenplatz</td>
      <td id="T_a309c_row5_col1" class="data row5 col1" >15</td>
      <td id="T_a309c_row5_col2" class="data row5 col2" >52.00</td>
      <td id="T_a309c_row5_col3" class="data row5 col3" >590617</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_a309c_row6_col0" class="data row6 col0" >Zürich, Kantonalbank</td>
      <td id="T_a309c_row6_col1" class="data row6 col1" >14</td>
      <td id="T_a309c_row6_col2" class="data row6 col2" >51.10</td>
      <td id="T_a309c_row6_col3" class="data row6 col3" >1096921</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_a309c_row7_col0" class="data row7 col0" >Zürich, Bellevue</td>
      <td id="T_a309c_row7_col1" class="data row7 col1" >14</td>
      <td id="T_a309c_row7_col2" class="data row7 col2" >55.00</td>
      <td id="T_a309c_row7_col3" class="data row7 col3" >1846395</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_a309c_row8_col0" class="data row8 col0" >Zürich, Sternen Oerlikon</td>
      <td id="T_a309c_row8_col1" class="data row8 col1" >14</td>
      <td id="T_a309c_row8_col2" class="data row8 col2" >71.50</td>
      <td id="T_a309c_row8_col3" class="data row8 col3" >829204</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_a309c_row9_col0" class="data row9 col0" >Zürich, Paradeplatz</td>
      <td id="T_a309c_row9_col1" class="data row9 col1" >14</td>
      <td id="T_a309c_row9_col2" class="data row9 col2" >48.20</td>
      <td id="T_a309c_row9_col3" class="data row9 col3" >1883640</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_a309c_row10_col0" class="data row10 col0" >Zürich, Sihlpost / HB</td>
      <td id="T_a309c_row10_col1" class="data row10 col1" >14</td>
      <td id="T_a309c_row10_col2" class="data row10 col2" >48.90</td>
      <td id="T_a309c_row10_col3" class="data row10 col3" >603034</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_a309c_row11_col0" class="data row11 col0" >Zürich, Hirschwiesenstrasse</td>
      <td id="T_a309c_row11_col1" class="data row11 col1" >14</td>
      <td id="T_a309c_row11_col2" class="data row11 col2" >56.10</td>
      <td id="T_a309c_row11_col3" class="data row11 col3" >562392</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_a309c_row12_col0" class="data row12 col0" >Zürich, Bahnhofplatz/HB</td>
      <td id="T_a309c_row12_col1" class="data row12 col1" >14</td>
      <td id="T_a309c_row12_col2" class="data row12 col2" >45.70</td>
      <td id="T_a309c_row12_col3" class="data row12 col3" >713206</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_a309c_row13_col0" class="data row13 col0" >Zürich, Salersteig</td>
      <td id="T_a309c_row13_col1" class="data row13 col1" >14</td>
      <td id="T_a309c_row13_col2" class="data row13 col2" >64.90</td>
      <td id="T_a309c_row13_col3" class="data row13 col3" >556453</td>
    </tr>
    <tr>
      <th id="T_a309c_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_a309c_row14_col0" class="data row14 col0" >Zürich, Milchbuck</td>
      <td id="T_a309c_row14_col1" class="data row14 col1" >14</td>
      <td id="T_a309c_row14_col2" class="data row14 col2" >61.50</td>
      <td id="T_a309c_row14_col3" class="data row14 col3" >1086944</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** **Kein Overlap zwischen den beiden Top-20-Listen** — exakt 0 Haltestellen erscheinen gleichzeitig in Top-20 nach Linienanzahl UND Top-20 nach Delay.

**Top-Haltestellen nach Linienanzahl (Knotenpunkte) — alle mit UNTERDURCHSCHNITTLICHEM Delay:**
| Haltestelle | Linien | Ø Delay (s) |
|:---|---:|---:|
| Haldenegg | 15 | **44.5** |
| Werd | 15 | 49.2 |
| Central | 15 | **48.3** |
| Stockerstrasse | 15 | 49.8 |
| Paradeplatz | 14 | **48.2** |
| Stauffacher | 15 | 60.7 |
| Bellevue | 14 | 55.0 |

**Kernbefund:** Die meistbediente Haltestelle Haldenegg (15 Linien) hat 44.5s Ø Delay — das liegt deutlich unter dem Netzschnitt (~56s). Paradeplatz (14 Linien, 48.2s), Central (15 Linien, 48.3s) — allesamt unter Durchschnitt. Einzig Stauffacher (15 Linien, 60.7s) liegt leicht über Durchschnitt.

**Konsequenz:** Die Hypothese "Mehr Linien = mehr Kaskadenrisiko = höherer Delay" findet in den Daten **keine Bestätigung** — sie ist widerlegt. Mögliche Erklärung: An den grossen Knotenpunkten ist der Betrieb besonders gut koordiniert (Fahrplan-Puffer, Fahrdienstleitung), während die echten Delay-Akkumulatoren auf den Aussenkorridoren liegen (→ F-SPAT-01 zu korrigieren).

→ Linienanzahl als Feature wenig vielversprechend für Delay-Prognose; besser: absolute Haltestelleneigenschaften (Korridor, Aussenlage) nutzen.

## Starthaltestellen-Diagnose

Starthaltestellen verzerren die Statistik: Trams warten am Startpunkt auf ihren Abfahrtszeitpunkt und "ankommen" weit vor dem Fahrplan — obwohl das kein echtes Betriebsproblem ist. Das zieht den Ø `arrival_delay` künstlich nach unten und beschönigt die Netz-Performance.

**Identifikation ohne stop_sequence:** Proxy-Kriterium — Starthaltestellen haben:
1. Sehr negatives `arrival_delay` (Tram steht schon lange da)
2. Positives `delay_delta` (Tram wartet, dann Abfahrt nahe Fahrplan → delta = dep_delay − arr_delay ist stark positiv)


```python
an.plot_start_stop_diagnosis(lf_delay, cfg)
show_df(an.table_start_stop_candidates(lf_delay))
```


    
![png](03_analysis_4-spatial_files/03_analysis_4-spatial_12_0.png)
    


    Gesamtstatistik:
      Ø arrival_delay ALLE Halte:                 +56.3s
      Ø arrival_delay OHNE 0 Starthaltestellen:  +56.3s
      Verzerrung durch Starthaltestellen:          -0.0s
    
    Starthaltestellen-Kandidaten (0 Stück):



<style type="text/css">
#T_0fe11 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_0fe11 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_0fe11 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_0fe11 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_0fe11 tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_0fe11">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_0fe11_level0_col0" class="col_heading level0 col0" >Halt</th>
      <th id="T_0fe11_level0_col1" class="col_heading level0 col1" >Ø Arr</th>
      <th id="T_0fe11_level0_col2" class="col_heading level0 col2" >Ø Dep</th>
      <th id="T_0fe11_level0_col3" class="col_heading level0 col3" >Ø Delta</th>
      <th id="T_0fe11_level0_col4" class="col_heading level0 col4" >n</th>
    </tr>
  </thead>
  <tbody>
  </tbody>
</table>



**Beobachtung:** Die Starthaltestellen-Diagnose findet mit den gewählten Schwellenwerten (avg_arr < −30s UND avg_delta > +20s) **0 Kandidaten**. Die Verzerrung des Netzschnitts durch klassische Starthaltestellen beträgt **0.0s** — kein Bereinigungsbedarf mit dieser Methode.

**Interpretation:** Das Proxy-Kriterium "stark negatives Arrival + stark positives Delta" trifft nicht zu:
- Terminus-Haltestellen scheinen in den Daten entweder nicht mit stark negativem Arrival aufzutauchen (Trams werden erst kurz vor Abfahrt erfasst), oder der Fahrplan ist so gestrickt, dass arrival_delay dort nicht systematisch negativ ist.
- Die frühen Ankünfte aus dem Top-Delay-Chart (z.B. negative Bars rechts) sind vorhanden, erfüllen aber nicht die kombinierte Bedingung (fehlendes starkes Delta).

**Alternative Interpretation:** Die Top-Delay-Ausreisser (Bertastrasse 181.6s n=1'307, Friedhof Sihlfeld 167.0s n=1'307) sind keine klassischen Starthaltestellen, sondern Sonder-/Eventhalte — hoher Delay, aber keine Frühankunft. Diese können durch einen n-Mindest-Filter oder einen spezifischen Halt-Namen-Filter herausgefiltert werden, statt durch das Start-Stop-Proxy.

→ Starthaltestellen-Flag nicht als Feature sinnvoll (keine Kandidaten gefunden). Stattdessen `n_threshold` Filter für Low-Volume-Haltestellen in Modellierung einbauen.

## District Analysis

Average delay per Zurich district (Kreis 1–12 + outside). Identifies spatial delay clusters.


```python
an.plot_district_analysis(lf_delay, cfg,ylim_delay=(0,80), ylim_otp=(0.80, 0.91))
show_df(an.table_district_analysis(lf_delay))
```


    
![png](03_analysis_4-spatial_files/03_analysis_4-spatial_16_0.png)
    



<style type="text/css">
#T_7645f thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_7645f td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_7645f tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_7645f tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_7645f tr:hover td {
  background-color: #eef3f8;
}
#T_7645f_row0_col0, #T_7645f_row1_col0, #T_7645f_row2_col0, #T_7645f_row3_col0, #T_7645f_row4_col0, #T_7645f_row5_col0, #T_7645f_row6_col0, #T_7645f_row7_col0, #T_7645f_row8_col0, #T_7645f_row9_col0, #T_7645f_row10_col0, #T_7645f_row11_col0, #T_7645f_row12_col0 {
  text-align: left;
}
#T_7645f_row0_col1, #T_7645f_row0_col2, #T_7645f_row0_col3, #T_7645f_row1_col1, #T_7645f_row1_col2, #T_7645f_row1_col3, #T_7645f_row2_col1, #T_7645f_row2_col2, #T_7645f_row2_col3, #T_7645f_row3_col1, #T_7645f_row3_col2, #T_7645f_row3_col3, #T_7645f_row4_col1, #T_7645f_row4_col2, #T_7645f_row4_col3, #T_7645f_row5_col1, #T_7645f_row5_col2, #T_7645f_row5_col3, #T_7645f_row6_col1, #T_7645f_row6_col2, #T_7645f_row6_col3, #T_7645f_row7_col1, #T_7645f_row7_col2, #T_7645f_row7_col3, #T_7645f_row8_col1, #T_7645f_row8_col2, #T_7645f_row8_col3, #T_7645f_row9_col1, #T_7645f_row9_col2, #T_7645f_row9_col3, #T_7645f_row10_col1, #T_7645f_row10_col2, #T_7645f_row10_col3, #T_7645f_row11_col1, #T_7645f_row11_col2, #T_7645f_row11_col3, #T_7645f_row12_col1, #T_7645f_row12_col2, #T_7645f_row12_col3 {
  text-align: right;
}
</style>
<table id="T_7645f">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_7645f_level0_col0" class="col_heading level0 col0" >Kreis</th>
      <th id="T_7645f_level0_col1" class="col_heading level0 col1" >Ø Delay</th>
      <th id="T_7645f_level0_col2" class="col_heading level0 col2" >OTP</th>
      <th id="T_7645f_level0_col3" class="col_heading level0 col3" >n Stops</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_7645f_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_7645f_row0_col0" class="data row0 col0" >Kreis 11</td>
      <td id="T_7645f_row0_col1" class="data row0 col1" >68.33</td>
      <td id="T_7645f_row0_col2" class="data row0 col2" >0.83</td>
      <td id="T_7645f_row0_col3" class="data row0 col3" >5636928</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_7645f_row1_col0" class="data row1 col0" >Kreis 12</td>
      <td id="T_7645f_row1_col1" class="data row1 col1" >66.30</td>
      <td id="T_7645f_row1_col2" class="data row1 col2" >0.85</td>
      <td id="T_7645f_row1_col3" class="data row1 col3" >4105968</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_7645f_row2_col0" class="data row2 col0" >Kreis 8</td>
      <td id="T_7645f_row2_col1" class="data row2 col1" >63.68</td>
      <td id="T_7645f_row2_col2" class="data row2 col2" >0.85</td>
      <td id="T_7645f_row2_col3" class="data row2 col3" >3661568</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_7645f_row3_col0" class="data row3 col0" >Kreis 9</td>
      <td id="T_7645f_row3_col1" class="data row3 col1" >59.65</td>
      <td id="T_7645f_row3_col2" class="data row3 col2" >0.87</td>
      <td id="T_7645f_row3_col3" class="data row3 col3" >4264414</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_7645f_row4_col0" class="data row4 col0" >Kreis 7</td>
      <td id="T_7645f_row4_col1" class="data row4 col1" >58.72</td>
      <td id="T_7645f_row4_col2" class="data row4 col2" >0.87</td>
      <td id="T_7645f_row4_col3" class="data row4 col3" >5688419</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_7645f_row5_col0" class="data row5 col0" >outside</td>
      <td id="T_7645f_row5_col1" class="data row5 col1" >58.42</td>
      <td id="T_7645f_row5_col2" class="data row5 col2" >0.87</td>
      <td id="T_7645f_row5_col3" class="data row5 col3" >5677731</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_7645f_row6_col0" class="data row6 col0" >Kreis 2</td>
      <td id="T_7645f_row6_col1" class="data row6 col1" >56.71</td>
      <td id="T_7645f_row6_col2" class="data row6 col2" >0.88</td>
      <td id="T_7645f_row6_col3" class="data row6 col3" >5829771</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_7645f_row7_col0" class="data row7 col0" >Kreis 3</td>
      <td id="T_7645f_row7_col1" class="data row7 col1" >55.98</td>
      <td id="T_7645f_row7_col2" class="data row7 col2" >0.88</td>
      <td id="T_7645f_row7_col3" class="data row7 col3" >4992739</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_7645f_row8_col0" class="data row8 col0" >Kreis 6</td>
      <td id="T_7645f_row8_col1" class="data row8 col1" >55.66</td>
      <td id="T_7645f_row8_col2" class="data row8 col2" >0.86</td>
      <td id="T_7645f_row8_col3" class="data row8 col3" >12619258</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_7645f_row9_col0" class="data row9 col0" >Kreis 4</td>
      <td id="T_7645f_row9_col1" class="data row9 col1" >54.72</td>
      <td id="T_7645f_row9_col2" class="data row9 col2" >0.87</td>
      <td id="T_7645f_row9_col3" class="data row9 col3" >7549226</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_7645f_row10_col0" class="data row10 col0" >Kreis 1</td>
      <td id="T_7645f_row10_col1" class="data row10 col1" >51.31</td>
      <td id="T_7645f_row10_col2" class="data row10 col2" >0.88</td>
      <td id="T_7645f_row10_col3" class="data row10 col3" >18354274</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_7645f_row11_col0" class="data row11 col0" >Kreis 10</td>
      <td id="T_7645f_row11_col1" class="data row11 col1" >51.04</td>
      <td id="T_7645f_row11_col2" class="data row11 col2" >0.88</td>
      <td id="T_7645f_row11_col3" class="data row11 col3" >2567332</td>
    </tr>
    <tr>
      <th id="T_7645f_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_7645f_row12_col0" class="data row12 col0" >Kreis 5</td>
      <td id="T_7645f_row12_col1" class="data row12 col1" >49.92</td>
      <td id="T_7645f_row12_col2" class="data row12 col2" >0.89</td>
      <td id="T_7645f_row12_col3" class="data row12 col3" >8767273</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Stadtkreis-Analyse zeigt ein klares Muster: **Aussenkreise haben höhere Verspätung als Innenstadt**.

**Ø Delay nach Stadtkreis (sortiert):**
| Stadtkreis | Ø Delay (s) | OTP | Charakter |
|:---|---:|---:|:---|
| **Kreis 11** | **68.3** | 83% | Oerlikon/Schwamendingen — langer Aussenkorridor |
| Kreis 12 | 66.3 | 85% | Schwamendingen — nordöstlicher Aussenbereich |
| Kreis 8 | 63.7 | 85% | Seefeld/Balgrist — langer Korridor L2/L4 |
| Kreis 9 | 59.7 | 87% | Altstetten — westlicher Aussenkorridor |
| Kreis 1 | 51.3 | 88% | Altstadt/Innenstadt — kurze Wege, gut koordiniert |
| **Kreis 5** | **49.9** | **89%** | Industriequartier — pünktlichster Kreis |

**Cross-Reference Events & Meteo — drei verschiedene Problemmuster:**

Die schlechten Kreise im räumlichen Kontext (K11, K12, K8) sind **nicht** dieselben wie die Event- oder Wetter-Hotspots:

| Dimension | Betroffene Kreise | Ursache |
|:---|:---|:---|
| **Struktureller Delay** (spatial) | K11, K12, K8, K9 | Lange Aussenkorridore, Delay-Akkumulation |
| **Schnee-sensitiv** (meteo) | K10, K4, K12 | Erhöhte Lage, exponiert |
| **Regen-sensitiv** (meteo) | K5, K9 | Limmat-Niederung, Drainage |
| **Event-sensitiv** (events) | K9, K2, K4 | Hauptbahnhof, Letzigrund, Innenstadt |

**Kernbefund:** Kaum Überschneidung zwischen den drei Mustern. K11 und K8 sind strukturell die schlechtesten Kreise — werden aber weder von Events noch von Wetter besonders getroffen. K5 ist der pünktlichste Kreis (Basis), aber Regen-Hotspot Nr. 1. Das zeigt: struktureller Delay und wetter-/event-bedingter Delay sind weitgehend unabhängige Probleme.

→ `district_nr` als Feature additiv zu `line_name` nützlich; Kreise 11/12 als High-Risk-Marker für strukturellen Delay.

## Line Analysis

Delay profile per tram line — which lines are most unreliable?


```python
an.plot_line_analysis(lf_delay, cfg)
show_df(an.table_line_analysis(lf_delay))
```


    
![png](03_analysis_4-spatial_files/03_analysis_4-spatial_20_0.png)
    



<style type="text/css">
#T_272c1 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_272c1 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_272c1 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_272c1 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_272c1 tr:hover td {
  background-color: #eef3f8;
}
#T_272c1_row0_col0, #T_272c1_row1_col0, #T_272c1_row2_col0, #T_272c1_row3_col0, #T_272c1_row4_col0, #T_272c1_row5_col0, #T_272c1_row6_col0, #T_272c1_row7_col0, #T_272c1_row8_col0, #T_272c1_row9_col0, #T_272c1_row10_col0, #T_272c1_row11_col0, #T_272c1_row12_col0, #T_272c1_row13_col0, #T_272c1_row14_col0, #T_272c1_row15_col0, #T_272c1_row16_col0, #T_272c1_row17_col0 {
  text-align: left;
}
#T_272c1_row0_col1, #T_272c1_row0_col2, #T_272c1_row0_col3, #T_272c1_row0_col4, #T_272c1_row1_col1, #T_272c1_row1_col2, #T_272c1_row1_col3, #T_272c1_row1_col4, #T_272c1_row2_col1, #T_272c1_row2_col2, #T_272c1_row2_col3, #T_272c1_row2_col4, #T_272c1_row3_col1, #T_272c1_row3_col2, #T_272c1_row3_col3, #T_272c1_row3_col4, #T_272c1_row4_col1, #T_272c1_row4_col2, #T_272c1_row4_col3, #T_272c1_row4_col4, #T_272c1_row5_col1, #T_272c1_row5_col2, #T_272c1_row5_col3, #T_272c1_row5_col4, #T_272c1_row6_col1, #T_272c1_row6_col2, #T_272c1_row6_col3, #T_272c1_row6_col4, #T_272c1_row7_col1, #T_272c1_row7_col2, #T_272c1_row7_col3, #T_272c1_row7_col4, #T_272c1_row8_col1, #T_272c1_row8_col2, #T_272c1_row8_col3, #T_272c1_row8_col4, #T_272c1_row9_col1, #T_272c1_row9_col2, #T_272c1_row9_col3, #T_272c1_row9_col4, #T_272c1_row10_col1, #T_272c1_row10_col2, #T_272c1_row10_col3, #T_272c1_row10_col4, #T_272c1_row11_col1, #T_272c1_row11_col2, #T_272c1_row11_col3, #T_272c1_row11_col4, #T_272c1_row12_col1, #T_272c1_row12_col2, #T_272c1_row12_col3, #T_272c1_row12_col4, #T_272c1_row13_col1, #T_272c1_row13_col2, #T_272c1_row13_col3, #T_272c1_row13_col4, #T_272c1_row14_col1, #T_272c1_row14_col2, #T_272c1_row14_col3, #T_272c1_row14_col4, #T_272c1_row15_col1, #T_272c1_row15_col2, #T_272c1_row15_col3, #T_272c1_row15_col4, #T_272c1_row16_col1, #T_272c1_row16_col2, #T_272c1_row16_col3, #T_272c1_row16_col4, #T_272c1_row17_col1, #T_272c1_row17_col2, #T_272c1_row17_col3, #T_272c1_row17_col4 {
  text-align: right;
}
</style>
<table id="T_272c1">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_272c1_level0_col0" class="col_heading level0 col0" >Line</th>
      <th id="T_272c1_level0_col1" class="col_heading level0 col1" >Ø Delay</th>
      <th id="T_272c1_level0_col2" class="col_heading level0 col2" >OTP</th>
      <th id="T_272c1_level0_col3" class="col_heading level0 col3" >Ø Delta</th>
      <th id="T_272c1_level0_col4" class="col_heading level0 col4" >n</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_272c1_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_272c1_row0_col0" class="data row0 col0" >E</td>
      <td id="T_272c1_row0_col1" class="data row0 col1" >130.16</td>
      <td id="T_272c1_row0_col2" class="data row0 col2" >0.56</td>
      <td id="T_272c1_row0_col3" class="data row0 col3" >-0.48</td>
      <td id="T_272c1_row0_col4" class="data row0 col4" >2511</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_272c1_row1_col0" class="data row1 col0" >11</td>
      <td id="T_272c1_row1_col1" class="data row1 col1" >68.74</td>
      <td id="T_272c1_row1_col2" class="data row1 col2" >0.82</td>
      <td id="T_272c1_row1_col3" class="data row1 col3" >6.24</td>
      <td id="T_272c1_row1_col4" class="data row1 col4" >8979877</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_272c1_row2_col0" class="data row2 col0" >15</td>
      <td id="T_272c1_row2_col1" class="data row2 col1" >61.36</td>
      <td id="T_272c1_row2_col2" class="data row2 col2" >0.85</td>
      <td id="T_272c1_row2_col3" class="data row2 col3" >1.98</td>
      <td id="T_272c1_row2_col4" class="data row2 col4" >2138416</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_272c1_row3_col0" class="data row3 col0" >10</td>
      <td id="T_272c1_row3_col1" class="data row3 col1" >60.05</td>
      <td id="T_272c1_row3_col2" class="data row3 col2" >0.85</td>
      <td id="T_272c1_row3_col3" class="data row3 col3" >6.48</td>
      <td id="T_272c1_row3_col4" class="data row3 col4" >6516391</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_272c1_row4_col0" class="data row4 col0" >8</td>
      <td id="T_272c1_row4_col1" class="data row4 col1" >59.71</td>
      <td id="T_272c1_row4_col2" class="data row4 col2" >0.85</td>
      <td id="T_272c1_row4_col3" class="data row4 col3" >4.53</td>
      <td id="T_272c1_row4_col4" class="data row4 col4" >6267234</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_272c1_row5_col0" class="data row5 col0" >7</td>
      <td id="T_272c1_row5_col1" class="data row5 col1" >58.85</td>
      <td id="T_272c1_row5_col2" class="data row5 col2" >0.87</td>
      <td id="T_272c1_row5_col3" class="data row5 col3" >3.92</td>
      <td id="T_272c1_row5_col4" class="data row5 col4" >8125792</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_272c1_row6_col0" class="data row6 col0" >4</td>
      <td id="T_272c1_row6_col1" class="data row6 col1" >57.44</td>
      <td id="T_272c1_row6_col2" class="data row6 col2" >0.87</td>
      <td id="T_272c1_row6_col3" class="data row6 col3" >8.11</td>
      <td id="T_272c1_row6_col4" class="data row6 col4" >6808772</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_272c1_row7_col0" class="data row7 col0" >2</td>
      <td id="T_272c1_row7_col1" class="data row7 col1" >56.18</td>
      <td id="T_272c1_row7_col2" class="data row7 col2" >0.87</td>
      <td id="T_272c1_row7_col3" class="data row7 col3" >7.19</td>
      <td id="T_272c1_row7_col4" class="data row7 col4" >8147118</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_272c1_row8_col0" class="data row8 col0" >9</td>
      <td id="T_272c1_row8_col1" class="data row8 col1" >55.62</td>
      <td id="T_272c1_row8_col2" class="data row8 col2" >0.87</td>
      <td id="T_272c1_row8_col3" class="data row8 col3" >5.86</td>
      <td id="T_272c1_row8_col4" class="data row8 col4" >8210815</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_272c1_row9_col0" class="data row9 col0" >14</td>
      <td id="T_272c1_row9_col1" class="data row9 col1" >55.52</td>
      <td id="T_272c1_row9_col2" class="data row9 col2" >0.87</td>
      <td id="T_272c1_row9_col3" class="data row9 col3" >7.52</td>
      <td id="T_272c1_row9_col4" class="data row9 col4" >7024821</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_272c1_row10_col0" class="data row10 col0" >3</td>
      <td id="T_272c1_row10_col1" class="data row10 col1" >53.90</td>
      <td id="T_272c1_row10_col2" class="data row10 col2" >0.90</td>
      <td id="T_272c1_row10_col3" class="data row10 col3" >5.51</td>
      <td id="T_272c1_row10_col4" class="data row10 col4" >5202425</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_272c1_row11_col0" class="data row11 col0" >13</td>
      <td id="T_272c1_row11_col1" class="data row11 col1" >52.58</td>
      <td id="T_272c1_row11_col2" class="data row11 col2" >0.88</td>
      <td id="T_272c1_row11_col3" class="data row11 col3" >5.04</td>
      <td id="T_272c1_row11_col4" class="data row11 col4" >8256404</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_272c1_row12_col0" class="data row12 col0" >12</td>
      <td id="T_272c1_row12_col1" class="data row12 col1" >51.78</td>
      <td id="T_272c1_row12_col2" class="data row12 col2" >0.92</td>
      <td id="T_272c1_row12_col3" class="data row12 col3" >4.39</td>
      <td id="T_272c1_row12_col4" class="data row12 col4" >2396392</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_272c1_row13_col0" class="data row13 col0" >17</td>
      <td id="T_272c1_row13_col1" class="data row13 col1" >47.93</td>
      <td id="T_272c1_row13_col2" class="data row13 col2" >0.91</td>
      <td id="T_272c1_row13_col3" class="data row13 col3" >3.56</td>
      <td id="T_272c1_row13_col4" class="data row13 col4" >4635968</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_272c1_row14_col0" class="data row14 col0" >5</td>
      <td id="T_272c1_row14_col1" class="data row14 col1" >47.37</td>
      <td id="T_272c1_row14_col2" class="data row14 col2" >0.89</td>
      <td id="T_272c1_row14_col3" class="data row14 col3" >7.34</td>
      <td id="T_272c1_row14_col4" class="data row14 col4" >3064076</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_272c1_row15_col0" class="data row15 col0" >50</td>
      <td id="T_272c1_row15_col1" class="data row15 col1" >46.58</td>
      <td id="T_272c1_row15_col2" class="data row15 col2" >0.90</td>
      <td id="T_272c1_row15_col3" class="data row15 col3" >13.17</td>
      <td id="T_272c1_row15_col4" class="data row15 col4" >147111</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_272c1_row16_col0" class="data row16 col0" >51</td>
      <td id="T_272c1_row16_col1" class="data row16 col1" >41.35</td>
      <td id="T_272c1_row16_col2" class="data row16 col2" >0.93</td>
      <td id="T_272c1_row16_col3" class="data row16 col3" >20.18</td>
      <td id="T_272c1_row16_col4" class="data row16 col4" >120208</td>
    </tr>
    <tr>
      <th id="T_272c1_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_272c1_row17_col0" class="data row17 col0" >6</td>
      <td id="T_272c1_row17_col1" class="data row17 col1" >38.40</td>
      <td id="T_272c1_row17_col2" class="data row17 col2" >0.93</td>
      <td id="T_272c1_row17_col3" class="data row17 col3" >4.15</td>
      <td id="T_272c1_row17_col4" class="data row17 col4" >3670570</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Linienanalyse zeigt erhebliche Unterschiede — Linie E (128s) als klarer Ausreisser, L11 (68.7s) mit Abstand schlechteste "reguläre" Linie.

**Linien-Ranking (Ø Arrival Delay):**
| Linie | Ø Delay (s) | OTP | Ø Delta (s) |
|:---|---:|---:|---:|
| E | 130.2 | 56% | −0.5 |
| **L11** | **68.7** | 82% | +6.2 |
| L15 | 61.4 | 85% | +2.0 |
| L10 | 60.1 | 85% | +6.5 |
| L8 | 59.7 | 85% | +4.5 |
| L6 | 38.4 | 93% | +4.2 |
| L51 | 41.4 | 93% | +20.2 |

**Delay-Delta:** Alle Linien haben **positives** Delta (Abfahrtsverspätung > Ankunftsverspätung) — Trams akkumulieren Delay an den Haltestellen, keine Linie baut Verspätung systematisch ab. L51 hat das grösste Delta (+20.2s) trotz niedrigstem Delay — kurze Linie mit vielen Warte-Momenten. L11 (+6.2s) und L10 (+6.5s) sind die stärksten Akkumulatoren unter den langen Hauptlinien.

**Linie E** (OTP 56%, Ø 130s): Sonderlinie/Entlastungslinie — bestätigt F-TARGET-12 und F-NET-08, kein Datenfehler.

→ `line_name` ist stärkster räumlicher Prädiktor. L11 als Hochrisiko-Linie für Modellpriorisierung.

> **Ausreißer am unteren Ende:**
> **L6 (38.4s, OTP ~94%)** ist die pünktlichste Linie im Netz — rund 18s unter
> dem Netzschnitt (~56s). Kurze Strecke, wenig Querverkehr. Das `line_name`-Feature
> kann diesen strukturellen Vorteil direkt kodieren.
>
> **L51 (41.4s, Ø Delta +20.2s):** Niedrigster absoluter Delay, aber höchstes
> Verspätungswachstum pro Halt im gesamten Netz. Erklärung: sehr konservativer
> Fahrplan mit viel Puffer — Trams starten früh und akkumulieren dann.
> Kein Betriebsproblem; `line_name` kodiert das implizit.

## Feature: `dwell_time`

Geplante Haltezeit = `departure_schedule − arrival_schedule` in Sekunden (F-TARGET-04). Kurze Dwell-Time = wenig Puffer → höheres Verspätungsrisiko (F-TARGET-03). Zeigt welche Haltestellen und Linien strukturell zu wenig Zeit einplanen.


```python
an.plot_dwell_time(lf_delay, cfg)
show_df(an.table_dwell_time_by_line(lf_delay))
```

    dwell_time aus Feature-File geladen



    
![png](03_analysis_4-spatial_files/03_analysis_4-spatial_23_1.png)
    


    Ø dwell_time netzweit: 17.6s
    Anteil mit dwell_time ≤ 20s: 71.3%
    Anteil mit dwell_time = 0s:  71.3%



<style type="text/css">
#T_d6332 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_d6332 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_d6332 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_d6332 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_d6332 tr:hover td {
  background-color: #eef3f8;
}
#T_d6332_row0_col0, #T_d6332_row0_col1, #T_d6332_row0_col2, #T_d6332_row1_col0, #T_d6332_row1_col1, #T_d6332_row1_col2, #T_d6332_row2_col0, #T_d6332_row2_col1, #T_d6332_row2_col2, #T_d6332_row3_col0, #T_d6332_row3_col1, #T_d6332_row3_col2, #T_d6332_row4_col0, #T_d6332_row4_col1, #T_d6332_row4_col2, #T_d6332_row5_col0, #T_d6332_row5_col1, #T_d6332_row5_col2, #T_d6332_row6_col0, #T_d6332_row6_col1, #T_d6332_row6_col2, #T_d6332_row7_col0, #T_d6332_row7_col1, #T_d6332_row7_col2, #T_d6332_row8_col0, #T_d6332_row8_col1, #T_d6332_row8_col2, #T_d6332_row9_col0, #T_d6332_row9_col1, #T_d6332_row9_col2, #T_d6332_row10_col0, #T_d6332_row10_col1, #T_d6332_row10_col2, #T_d6332_row11_col0, #T_d6332_row11_col1, #T_d6332_row11_col2, #T_d6332_row12_col0, #T_d6332_row12_col1, #T_d6332_row12_col2, #T_d6332_row13_col0, #T_d6332_row13_col1, #T_d6332_row13_col2, #T_d6332_row14_col0, #T_d6332_row14_col1, #T_d6332_row14_col2, #T_d6332_row15_col0, #T_d6332_row15_col1, #T_d6332_row15_col2, #T_d6332_row16_col0, #T_d6332_row16_col1, #T_d6332_row16_col2, #T_d6332_row17_col0, #T_d6332_row17_col1, #T_d6332_row17_col2 {
  text-align: right;
}
#T_d6332_row0_col3, #T_d6332_row1_col3, #T_d6332_row2_col3, #T_d6332_row3_col3, #T_d6332_row4_col3, #T_d6332_row5_col3, #T_d6332_row6_col3, #T_d6332_row7_col3, #T_d6332_row8_col3, #T_d6332_row9_col3, #T_d6332_row10_col3, #T_d6332_row11_col3, #T_d6332_row12_col3, #T_d6332_row13_col3, #T_d6332_row14_col3, #T_d6332_row15_col3, #T_d6332_row16_col3, #T_d6332_row17_col3 {
  text-align: left;
}
</style>
<table id="T_d6332">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_d6332_level0_col0" class="col_heading level0 col0" >Ø Haltezeit (s)</th>
      <th id="T_d6332_level0_col1" class="col_heading level0 col1" >Median Haltezeit (s)</th>
      <th id="T_d6332_level0_col2" class="col_heading level0 col2" >Ø Arr Delay (s)</th>
      <th id="T_d6332_level0_col3" class="col_heading level0 col3" >N Halte</th>
    </tr>
    <tr>
      <th class="index_name level0" >Line</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_d6332_level0_row0" class="row_heading level0 row0" >51</th>
      <td id="T_d6332_row0_col0" class="data row0 col0" >12.10</td>
      <td id="T_d6332_row0_col1" class="data row0 col1" >0.00</td>
      <td id="T_d6332_row0_col2" class="data row0 col2" >41.40</td>
      <td id="T_d6332_row0_col3" class="data row0 col3" >120,208</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row1" class="row_heading level0 row1" >10</th>
      <td id="T_d6332_row1_col0" class="data row1 col0" >15.50</td>
      <td id="T_d6332_row1_col1" class="data row1 col1" >0.00</td>
      <td id="T_d6332_row1_col2" class="data row1 col2" >60.00</td>
      <td id="T_d6332_row1_col3" class="data row1 col3" >6,516,352</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row2" class="row_heading level0 row2" >12</th>
      <td id="T_d6332_row2_col0" class="data row2 col0" >15.60</td>
      <td id="T_d6332_row2_col1" class="data row2 col1" >0.00</td>
      <td id="T_d6332_row2_col2" class="data row2 col2" >51.80</td>
      <td id="T_d6332_row2_col3" class="data row2 col3" >2,396,392</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row3" class="row_heading level0 row3" >5</th>
      <td id="T_d6332_row3_col0" class="data row3 col0" >15.60</td>
      <td id="T_d6332_row3_col1" class="data row3 col1" >0.00</td>
      <td id="T_d6332_row3_col2" class="data row3 col2" >47.40</td>
      <td id="T_d6332_row3_col3" class="data row3 col3" >3,064,057</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_d6332_row4_col0" class="data row4 col0" >15.70</td>
      <td id="T_d6332_row4_col1" class="data row4 col1" >0.00</td>
      <td id="T_d6332_row4_col2" class="data row4 col2" >57.40</td>
      <td id="T_d6332_row4_col3" class="data row4 col3" >6,807,737</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row5" class="row_heading level0 row5" >13</th>
      <td id="T_d6332_row5_col0" class="data row5 col0" >16.50</td>
      <td id="T_d6332_row5_col1" class="data row5 col1" >0.00</td>
      <td id="T_d6332_row5_col2" class="data row5 col2" >52.60</td>
      <td id="T_d6332_row5_col3" class="data row5 col3" >8,254,674</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row6" class="row_heading level0 row6" >50</th>
      <td id="T_d6332_row6_col0" class="data row6 col0" >16.90</td>
      <td id="T_d6332_row6_col1" class="data row6 col1" >0.00</td>
      <td id="T_d6332_row6_col2" class="data row6 col2" >46.60</td>
      <td id="T_d6332_row6_col3" class="data row6 col3" >147,111</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_d6332_row7_col0" class="data row7 col0" >17.20</td>
      <td id="T_d6332_row7_col1" class="data row7 col1" >0.00</td>
      <td id="T_d6332_row7_col2" class="data row7 col2" >58.90</td>
      <td id="T_d6332_row7_col3" class="data row7 col3" >8,125,785</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row8" class="row_heading level0 row8" >6</th>
      <td id="T_d6332_row8_col0" class="data row8 col0" >17.50</td>
      <td id="T_d6332_row8_col1" class="data row8 col1" >0.00</td>
      <td id="T_d6332_row8_col2" class="data row8 col2" >38.40</td>
      <td id="T_d6332_row8_col3" class="data row8 col3" >3,670,559</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row9" class="row_heading level0 row9" >11</th>
      <td id="T_d6332_row9_col0" class="data row9 col0" >17.60</td>
      <td id="T_d6332_row9_col1" class="data row9 col1" >0.00</td>
      <td id="T_d6332_row9_col2" class="data row9 col2" >68.70</td>
      <td id="T_d6332_row9_col3" class="data row9 col3" >8,979,732</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row10" class="row_heading level0 row10" >2</th>
      <td id="T_d6332_row10_col0" class="data row10 col0" >17.80</td>
      <td id="T_d6332_row10_col1" class="data row10 col1" >0.00</td>
      <td id="T_d6332_row10_col2" class="data row10 col2" >56.20</td>
      <td id="T_d6332_row10_col3" class="data row10 col3" >8,147,112</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row11" class="row_heading level0 row11" >15</th>
      <td id="T_d6332_row11_col0" class="data row11 col0" >17.80</td>
      <td id="T_d6332_row11_col1" class="data row11 col1" >0.00</td>
      <td id="T_d6332_row11_col2" class="data row11 col2" >61.40</td>
      <td id="T_d6332_row11_col3" class="data row11 col3" >2,138,399</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row12" class="row_heading level0 row12" >17</th>
      <td id="T_d6332_row12_col0" class="data row12 col0" >18.10</td>
      <td id="T_d6332_row12_col1" class="data row12 col1" >0.00</td>
      <td id="T_d6332_row12_col2" class="data row12 col2" >47.90</td>
      <td id="T_d6332_row12_col3" class="data row12 col3" >4,625,089</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row13" class="row_heading level0 row13" >8</th>
      <td id="T_d6332_row13_col0" class="data row13 col0" >18.40</td>
      <td id="T_d6332_row13_col1" class="data row13 col1" >0.00</td>
      <td id="T_d6332_row13_col2" class="data row13 col2" >59.70</td>
      <td id="T_d6332_row13_col3" class="data row13 col3" >6,267,228</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row14" class="row_heading level0 row14" >9</th>
      <td id="T_d6332_row14_col0" class="data row14 col0" >19.00</td>
      <td id="T_d6332_row14_col1" class="data row14 col1" >0.00</td>
      <td id="T_d6332_row14_col2" class="data row14 col2" >55.60</td>
      <td id="T_d6332_row14_col3" class="data row14 col3" >8,210,807</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row15" class="row_heading level0 row15" >14</th>
      <td id="T_d6332_row15_col0" class="data row15 col0" >19.30</td>
      <td id="T_d6332_row15_col1" class="data row15 col1" >0.00</td>
      <td id="T_d6332_row15_col2" class="data row15 col2" >55.50</td>
      <td id="T_d6332_row15_col3" class="data row15 col3" >7,024,604</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row16" class="row_heading level0 row16" >3</th>
      <td id="T_d6332_row16_col0" class="data row16 col0" >21.90</td>
      <td id="T_d6332_row16_col1" class="data row16 col1" >0.00</td>
      <td id="T_d6332_row16_col2" class="data row16 col2" >53.90</td>
      <td id="T_d6332_row16_col3" class="data row16 col3" >5,202,405</td>
    </tr>
    <tr>
      <th id="T_d6332_level0_row17" class="row_heading level0 row17" >E</th>
      <td id="T_d6332_row17_col0" class="data row17 col0" >24.20</td>
      <td id="T_d6332_row17_col1" class="data row17 col1" >0.00</td>
      <td id="T_d6332_row17_col2" class="data row17 col2" >130.20</td>
      <td id="T_d6332_row17_col3" class="data row17 col3" >2,511</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die `dwell_time`-Verteilung zeigt ein überraschendes Ergebnis: **71.3% aller Halte haben dwell_time = 0s** — identisch mit dem ≤20s-Anteil.

**Ø dwell_time netzweit: 17.6s | Anteil 0s: 71.3%**

Das bedeutet: **Mehr als 2 von 3 Halten sind fahrplanmässig als Durchfahrten ohne geplante Haltezeit kodiert.** Der Median ist für alle Linien **0s**.

**Konsequenz für Feature-Nutzung:** Ein Scatter `dwell_time × delay` kann keinen negativen Zusammenhang zeigen, wenn 71% der Datenpunkte bei 0s liegen — die Streuung fehlt. `dwell_time` als kontinuierliches Feature ist damit nur für die 29% der Halte mit geplanter Haltezeit informativ. Als binäres Feature (`has_dwell = dwell_time > 0`) möglicherweise nützlicher.

**Linien-Unterschiede:** Die Ø-Werte variieren zwischen L51 (12.1s) und Linie E (24.2s) — aber alle haben Median=0. L3 hat mit 21.9s die höchste mittlere Haltezeit unter den regulären Hauptlinien, L10 die niedrigste (15.5s).

→ `dwell_time` als Feature weniger stark als erhofft. Stattdessen `has_dwell` (binary) prüfen.

---

**Hypothese: 10s Puffer pro Halt würde das System deutlich entlasten**

Das positive Delay-Delta (+5–6s pro Halt bei L10/L11) zeigt: Trams akkumulieren Verspätung schrittweise, weil kein Puffer zum Nachholen da ist. Selbst **10s geplante dwell_time an Zwischenhalten** würden dem Fahrer die Möglichkeit geben, kleinere Verzögerungen aufzufangen — ohne den Takt zu sprengen.

Zum Vergleich: Andere Netze (London TfL, Berlin BVG) planen explizite "recovery time" an Knoten (3–5 min an Endpunkten, ~30s an Zwischenhalten). Zürich VBZ verzichtet bewusst darauf zugunsten eines dichteren Takts (5–7 min). Der Preis: jede Störung pflanzt sich fort, da es keine Puffer-Haltestellen gibt.

→ Nicht im Modell direkt lösbar — aber ein starkes Präsentationsargument: *das System ist so eng getaktet, dass strukturell kein Raum zum Nachholen bleibt.*

## Stop Delay Map

Wo liegen die Delay-Hotspots im Stadtgebiet? Haltestellen eingefärbt nach Ø Arrival Delay — Stadtkreise als Hintergrund-Choropleth. Nur Haltestellen mit n ≥ 5000 (statistisch belastbar).


```python
an.plot_stop_delay_map(lf_clean)
show_df(an.table_stop_delay_map(lf_clean))
```




<style type="text/css">
#T_9e333 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_9e333 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_9e333 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_9e333 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_9e333 tr:hover td {
  background-color: #eef3f8;
}
#T_9e333_row0_col0, #T_9e333_row0_col3, #T_9e333_row0_col4, #T_9e333_row1_col0, #T_9e333_row1_col3, #T_9e333_row1_col4, #T_9e333_row2_col0, #T_9e333_row2_col3, #T_9e333_row2_col4, #T_9e333_row3_col0, #T_9e333_row3_col3, #T_9e333_row3_col4, #T_9e333_row4_col0, #T_9e333_row4_col3, #T_9e333_row4_col4, #T_9e333_row5_col0, #T_9e333_row5_col3, #T_9e333_row5_col4, #T_9e333_row6_col0, #T_9e333_row6_col3, #T_9e333_row6_col4, #T_9e333_row7_col0, #T_9e333_row7_col3, #T_9e333_row7_col4, #T_9e333_row8_col0, #T_9e333_row8_col3, #T_9e333_row8_col4, #T_9e333_row9_col0, #T_9e333_row9_col3, #T_9e333_row9_col4, #T_9e333_row10_col0, #T_9e333_row10_col3, #T_9e333_row10_col4, #T_9e333_row11_col0, #T_9e333_row11_col3, #T_9e333_row11_col4, #T_9e333_row12_col0, #T_9e333_row12_col3, #T_9e333_row12_col4, #T_9e333_row13_col0, #T_9e333_row13_col3, #T_9e333_row13_col4, #T_9e333_row14_col0, #T_9e333_row14_col3, #T_9e333_row14_col4, #T_9e333_row15_col0, #T_9e333_row15_col3, #T_9e333_row15_col4, #T_9e333_row16_col0, #T_9e333_row16_col3, #T_9e333_row16_col4, #T_9e333_row17_col0, #T_9e333_row17_col3, #T_9e333_row17_col4, #T_9e333_row18_col0, #T_9e333_row18_col3, #T_9e333_row18_col4, #T_9e333_row19_col0, #T_9e333_row19_col3, #T_9e333_row19_col4 {
  text-align: left;
}
#T_9e333_row0_col1, #T_9e333_row0_col2, #T_9e333_row1_col1, #T_9e333_row1_col2, #T_9e333_row2_col1, #T_9e333_row2_col2, #T_9e333_row3_col1, #T_9e333_row3_col2, #T_9e333_row4_col1, #T_9e333_row4_col2, #T_9e333_row5_col1, #T_9e333_row5_col2, #T_9e333_row6_col1, #T_9e333_row6_col2, #T_9e333_row7_col1, #T_9e333_row7_col2, #T_9e333_row8_col1, #T_9e333_row8_col2, #T_9e333_row9_col1, #T_9e333_row9_col2, #T_9e333_row10_col1, #T_9e333_row10_col2, #T_9e333_row11_col1, #T_9e333_row11_col2, #T_9e333_row12_col1, #T_9e333_row12_col2, #T_9e333_row13_col1, #T_9e333_row13_col2, #T_9e333_row14_col1, #T_9e333_row14_col2, #T_9e333_row15_col1, #T_9e333_row15_col2, #T_9e333_row16_col1, #T_9e333_row16_col2, #T_9e333_row17_col1, #T_9e333_row17_col2, #T_9e333_row18_col1, #T_9e333_row18_col2, #T_9e333_row19_col1, #T_9e333_row19_col2 {
  text-align: right;
}
</style>
<table id="T_9e333">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_9e333_level0_col0" class="col_heading level0 col0" >Stop</th>
      <th id="T_9e333_level0_col1" class="col_heading level0 col1" >Kreis</th>
      <th id="T_9e333_level0_col2" class="col_heading level0 col2" >Avg. Delay (s)</th>
      <th id="T_9e333_level0_col3" class="col_heading level0 col3" >OTP</th>
      <th id="T_9e333_level0_col4" class="col_heading level0 col4" >N</th>
    </tr>
    <tr>
      <th class="index_name level0" >Rang</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_9e333_level0_row0" class="row_heading level0 row0" >1</th>
      <td id="T_9e333_row0_col0" class="data row0 col0" >Zürich, Friedrichstrasse</td>
      <td id="T_9e333_row0_col1" class="data row0 col1" >12</td>
      <td id="T_9e333_row0_col2" class="data row0 col2" >144.60</td>
      <td id="T_9e333_row0_col3" class="data row0 col3" >56.7%</td>
      <td id="T_9e333_row0_col4" class="data row0 col4" >14,357</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row1" class="row_heading level0 row1" >2</th>
      <td id="T_9e333_row1_col0" class="data row1 col0" >Zürich, Friedhof Enzenbühl</td>
      <td id="T_9e333_row1_col1" class="data row1 col1" >8</td>
      <td id="T_9e333_row1_col2" class="data row1 col2" >131.00</td>
      <td id="T_9e333_row1_col3" class="data row1 col3" >56.3%</td>
      <td id="T_9e333_row1_col4" class="data row1 col4" >146,240</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row2" class="row_heading level0 row2" >3</th>
      <td id="T_9e333_row2_col0" class="data row2 col0" >Zürich, Frohburg</td>
      <td id="T_9e333_row2_col1" class="data row2 col1" >12</td>
      <td id="T_9e333_row2_col2" class="data row2 col2" >116.60</td>
      <td id="T_9e333_row2_col3" class="data row2 col3" >67.7%</td>
      <td id="T_9e333_row2_col4" class="data row2 col4" >14,368</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row3" class="row_heading level0 row3" >4</th>
      <td id="T_9e333_row3_col0" class="data row3 col0" >Zürich, Albisgütli</td>
      <td id="T_9e333_row3_col1" class="data row3 col1" >3</td>
      <td id="T_9e333_row3_col2" class="data row3 col2" >101.80</td>
      <td id="T_9e333_row3_col3" class="data row3 col3" >65.6%</td>
      <td id="T_9e333_row3_col4" class="data row3 col4" >13,991</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row4" class="row_heading level0 row4" >5</th>
      <td id="T_9e333_row4_col0" class="data row4 col0" >Zürich, Seebacherplatz</td>
      <td id="T_9e333_row4_col1" class="data row4 col1" >11</td>
      <td id="T_9e333_row4_col2" class="data row4 col2" >99.60</td>
      <td id="T_9e333_row4_col3" class="data row4 col3" >68.4%</td>
      <td id="T_9e333_row4_col4" class="data row4 col4" >147,017</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row5" class="row_heading level0 row5" >6</th>
      <td id="T_9e333_row5_col0" class="data row5 col0" >Zürich, Butzenstrasse</td>
      <td id="T_9e333_row5_col1" class="data row5 col1" >2</td>
      <td id="T_9e333_row5_col2" class="data row5 col2" >98.30</td>
      <td id="T_9e333_row5_col3" class="data row5 col3" >69.1%</td>
      <td id="T_9e333_row5_col4" class="data row5 col4" >155,742</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row6" class="row_heading level0 row6" >7</th>
      <td id="T_9e333_row6_col0" class="data row6 col0" >Zürich, Mattenhof</td>
      <td id="T_9e333_row6_col1" class="data row6 col1" >12</td>
      <td id="T_9e333_row6_col2" class="data row6 col2" >97.50</td>
      <td id="T_9e333_row6_col3" class="data row6 col3" >69.8%</td>
      <td id="T_9e333_row6_col4" class="data row6 col4" >142,064</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row7" class="row_heading level0 row7" >8</th>
      <td id="T_9e333_row7_col0" class="data row7 col0" >Zürich, Altried</td>
      <td id="T_9e333_row7_col1" class="data row7 col1" >12</td>
      <td id="T_9e333_row7_col2" class="data row7 col2" >97.00</td>
      <td id="T_9e333_row7_col3" class="data row7 col3" >69.8%</td>
      <td id="T_9e333_row7_col4" class="data row7 col4" >139,516</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row8" class="row_heading level0 row8" >9</th>
      <td id="T_9e333_row8_col0" class="data row8 col0" >Zürich, Fellenbergstrasse</td>
      <td id="T_9e333_row8_col1" class="data row8 col1" >9</td>
      <td id="T_9e333_row8_col2" class="data row8 col2" >94.70</td>
      <td id="T_9e333_row8_col3" class="data row8 col3" >71.1%</td>
      <td id="T_9e333_row8_col4" class="data row8 col4" >141,837</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row9" class="row_heading level0 row9" >10</th>
      <td id="T_9e333_row9_col0" class="data row9 col0" >Zürich, Strassenverkehrsamt</td>
      <td id="T_9e333_row9_col1" class="data row9 col1" >3</td>
      <td id="T_9e333_row9_col2" class="data row9 col2" >92.50</td>
      <td id="T_9e333_row9_col3" class="data row9 col3" >70.2%</td>
      <td id="T_9e333_row9_col4" class="data row9 col4" >161,957</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row10" class="row_heading level0 row10" >11</th>
      <td id="T_9e333_row10_col0" class="data row10 col0" >Zürich, Würzgraben</td>
      <td id="T_9e333_row10_col1" class="data row10 col1" >9</td>
      <td id="T_9e333_row10_col2" class="data row10 col2" >85.50</td>
      <td id="T_9e333_row10_col3" class="data row10 col3" >73.3%</td>
      <td id="T_9e333_row10_col4" class="data row10 col4" >140,188</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row11" class="row_heading level0 row11" >12</th>
      <td id="T_9e333_row11_col0" class="data row11 col0" >Zürich, Balgrist</td>
      <td id="T_9e333_row11_col1" class="data row11 col1" >8</td>
      <td id="T_9e333_row11_col2" class="data row11 col2" >85.30</td>
      <td id="T_9e333_row11_col3" class="data row11 col3" >77.0%</td>
      <td id="T_9e333_row11_col4" class="data row11 col4" >291,848</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row12" class="row_heading level0 row12" >13</th>
      <td id="T_9e333_row12_col0" class="data row12 col0" >Zürich, Fernsehstudio</td>
      <td id="T_9e333_row12_col1" class="data row12 col1" >0</td>
      <td id="T_9e333_row12_col2" class="data row12 col2" >84.50</td>
      <td id="T_9e333_row12_col3" class="data row12 col3" >77.2%</td>
      <td id="T_9e333_row12_col4" class="data row12 col4" >296,798</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row13" class="row_heading level0 row13" >14</th>
      <td id="T_9e333_row13_col0" class="data row13 col0" >Zürich, Hölderlinstrasse</td>
      <td id="T_9e333_row13_col1" class="data row13 col1" >7</td>
      <td id="T_9e333_row13_col2" class="data row13 col2" >83.60</td>
      <td id="T_9e333_row13_col3" class="data row13 col3" >76.0%</td>
      <td id="T_9e333_row13_col4" class="data row13 col4" >282,359</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row14" class="row_heading level0 row14" >15</th>
      <td id="T_9e333_row14_col0" class="data row14 col0" >Zürich, Leutschenbach</td>
      <td id="T_9e333_row14_col1" class="data row14 col1" >11</td>
      <td id="T_9e333_row14_col2" class="data row14 col2" >83.40</td>
      <td id="T_9e333_row14_col3" class="data row14 col3" >78.8%</td>
      <td id="T_9e333_row14_col4" class="data row14 col4" >534,708</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row15" class="row_heading level0 row15" >16</th>
      <td id="T_9e333_row15_col0" class="data row15 col0" >Zürich, Wetlistrasse</td>
      <td id="T_9e333_row15_col1" class="data row15 col1" >7</td>
      <td id="T_9e333_row15_col2" class="data row15 col2" >83.20</td>
      <td id="T_9e333_row15_col3" class="data row15 col3" >76.9%</td>
      <td id="T_9e333_row15_col4" class="data row15 col4" >291,102</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row16" class="row_heading level0 row16" >17</th>
      <td id="T_9e333_row16_col0" class="data row16 col0" >Schlieren, Zentrum/Bahnhof</td>
      <td id="T_9e333_row16_col1" class="data row16 col1" >0</td>
      <td id="T_9e333_row16_col2" class="data row16 col2" >82.00</td>
      <td id="T_9e333_row16_col3" class="data row16 col3" >74.4%</td>
      <td id="T_9e333_row16_col4" class="data row16 col4" >145,919</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row17" class="row_heading level0 row17" >18</th>
      <td id="T_9e333_row17_col0" class="data row17 col0" >Zürich, Burgwies</td>
      <td id="T_9e333_row17_col1" class="data row17 col1" >7</td>
      <td id="T_9e333_row17_col2" class="data row17 col2" >81.50</td>
      <td id="T_9e333_row17_col3" class="data row17 col3" >77.8%</td>
      <td id="T_9e333_row17_col4" class="data row17 col4" >289,896</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row18" class="row_heading level0 row18" >19</th>
      <td id="T_9e333_row18_col0" class="data row18 col0" >Zürich, Wildbachstrasse</td>
      <td id="T_9e333_row18_col1" class="data row18 col1" >8</td>
      <td id="T_9e333_row18_col2" class="data row18 col2" >80.20</td>
      <td id="T_9e333_row18_col3" class="data row18 col3" >75.4%</td>
      <td id="T_9e333_row18_col4" class="data row18 col4" >280,733</td>
    </tr>
    <tr>
      <th id="T_9e333_level0_row19" class="row_heading level0 row19" >20</th>
      <td id="T_9e333_row19_col0" class="data row19 col0" >Zürich, Messe/Hallenstadion</td>
      <td id="T_9e333_row19_col1" class="data row19 col1" >11</td>
      <td id="T_9e333_row19_col2" class="data row19 col2" >79.60</td>
      <td id="T_9e333_row19_col3" class="data row19 col3" >79.3%</td>
      <td id="T_9e333_row19_col4" class="data row19 col4" >281,222</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Karte zeigt ein klares Muster: **Delay-Hotspots liegen an den Aussenkorridoren**, nicht im Innenstadtkern.

**Räumliche Cluster:**
- **Nordost-Korridor** (Kreis 11/12 — Oerlikon, Schwamendingen, Leutschenbach): durchgehend hohe Delays, konsistent mit F-SPAT-03
- **Seefeld-Korridor** (Kreis 8 — Balgrist, Burgwies): lange Strecke L2/L4 ohne Puffer
- **Innenstadt** (Kreis 1/5): auffällig niedrige Delays — kurze Segmente, gut koordiniert

**Endstationen-Muster:** Viele der roten Bubbles liegen erkennbar an oder kurz vor den Linienendhaltestellen — der akkumulierte Delay entlädt sich am Terminus. Bei einigen Linien (L11, L7) sieht man die Verzögerung schon 1–2 Haltestellen vor dem Ende ansteigen; ein kontinuierlicher Aufbau über die gesamte Strecke ist seltener.

**Graue Netzpunkte als Referenz:** Die Innenstadthalte (graue Punkte dicht gedrängt) zeigen kaum farbige Überlagerung — Bestätigung dass der Kern pünktlicher ist als die Peripherie.

→ Karte bestätigt F-SPAT-01 und F-SPAT-03 visuell. Starkes Präsentationselement.

## Line Delay Map

Haltestellen nach Linie gruppiert — jede Linie eine eigene Farbe, Blasengrösse = Ø Delay. Linien einzeln an- und abwählbar in der Legende.


```python
an.plot_line_delay_map(lf_clean, cfg)
```





**Beobachtung:** Die Linien-Karte macht die unterschiedliche Streckencharakteristik sofort sichtbar — jede Farbe erzählt eine eigene Geschichte.

**Auffällige Linien:**
- **L11 / L13 / L7:** Grosse Bubbles an Start und Ende der Linie, kaum in der Mitte. Klassisches Akkumulationsmuster: Delay baut sich entlang der Strecke auf und entlädt sich am Terminus. Startstationen zeigen ebenfalls grosse Bubbles — Rückfahrten starten bereits mit Verspätung wenn die Hinfahrt zu spät ankam.
- **L6 / L51:** Kleine, gleichmässige Bubbles entlang der gesamten Strecke — kurze Linien mit wenig Akkumulationspotenzial.
- **L2 / L4:** Mittlere Bubbles, aber Hotspot klar im Seefeld-Korridor (Balgrist/Burgwies).

**Kernbefund:** Das Endstationen-Muster bei L11/L13/L7 ist ein eigenständiger Finding — lange Linien ohne Puffer akkumulieren Delay systematisch, der Endhalt trägt die Last der gesamten Strecke. Kurze Linien (L6) sind strukturell pünktlicher, unabhängig vom Korridor.

→ Linienlänge als Proxy-Feature für Delay-Risiko prüfen (F-SPAT-09 neu).

## Linien-Delay nach Uhrzeit — Heatmap

Linie × Stunde als Heatmap — zeigt wann welche Linie am meisten leidet und ob das Muster linienspezifisch ist oder netzweit synchron verläuft.


```python
an.plot_line_hour_heatmap(lf_clean, cfg)
show_df(an.table_line_hour_heatmap(lf_clean))
```


    
![png](03_analysis_4-spatial_files/03_analysis_4-spatial_35_0.png)
    



<style type="text/css">
#T_0e42d thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_0e42d td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_0e42d tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_0e42d tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_0e42d tr:hover td {
  background-color: #eef3f8;
}
#T_0e42d_row0_col0, #T_0e42d_row0_col2, #T_0e42d_row0_col3, #T_0e42d_row1_col0, #T_0e42d_row1_col2, #T_0e42d_row1_col3, #T_0e42d_row2_col0, #T_0e42d_row2_col2, #T_0e42d_row2_col3, #T_0e42d_row3_col0, #T_0e42d_row3_col2, #T_0e42d_row3_col3, #T_0e42d_row4_col0, #T_0e42d_row4_col2, #T_0e42d_row4_col3, #T_0e42d_row5_col0, #T_0e42d_row5_col2, #T_0e42d_row5_col3, #T_0e42d_row6_col0, #T_0e42d_row6_col2, #T_0e42d_row6_col3, #T_0e42d_row7_col0, #T_0e42d_row7_col2, #T_0e42d_row7_col3, #T_0e42d_row8_col0, #T_0e42d_row8_col2, #T_0e42d_row8_col3, #T_0e42d_row9_col0, #T_0e42d_row9_col2, #T_0e42d_row9_col3, #T_0e42d_row10_col0, #T_0e42d_row10_col2, #T_0e42d_row10_col3, #T_0e42d_row11_col0, #T_0e42d_row11_col2, #T_0e42d_row11_col3, #T_0e42d_row12_col0, #T_0e42d_row12_col2, #T_0e42d_row12_col3, #T_0e42d_row13_col0, #T_0e42d_row13_col2, #T_0e42d_row13_col3, #T_0e42d_row14_col0, #T_0e42d_row14_col2, #T_0e42d_row14_col3 {
  text-align: right;
}
#T_0e42d_row0_col1, #T_0e42d_row1_col1, #T_0e42d_row2_col1, #T_0e42d_row3_col1, #T_0e42d_row4_col1, #T_0e42d_row5_col1, #T_0e42d_row6_col1, #T_0e42d_row7_col1, #T_0e42d_row8_col1, #T_0e42d_row9_col1, #T_0e42d_row10_col1, #T_0e42d_row11_col1, #T_0e42d_row12_col1, #T_0e42d_row13_col1, #T_0e42d_row14_col1 {
  text-align: left;
}
</style>
<table id="T_0e42d">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_0e42d_level0_col0" class="col_heading level0 col0" >Ø Delay gesamt (s)</th>
      <th id="T_0e42d_level0_col1" class="col_heading level0 col1" >Peak-Stunde</th>
      <th id="T_0e42d_level0_col2" class="col_heading level0 col2" >Peak-Delay (s)</th>
      <th id="T_0e42d_level0_col3" class="col_heading level0 col3" >Nacht-Min (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Line</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_0e42d_level0_row0" class="row_heading level0 row0" >11</th>
      <td id="T_0e42d_row0_col0" class="data row0 col0" >67.90</td>
      <td id="T_0e42d_row0_col1" class="data row0 col1" >02:00</td>
      <td id="T_0e42d_row0_col2" class="data row0 col2" >113.30</td>
      <td id="T_0e42d_row0_col3" class="data row0 col3" >31.50</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row1" class="row_heading level0 row1" >2</th>
      <td id="T_0e42d_row1_col0" class="data row1 col0" >63.00</td>
      <td id="T_0e42d_row1_col1" class="data row1 col1" >03:00</td>
      <td id="T_0e42d_row1_col2" class="data row1 col2" >213.00</td>
      <td id="T_0e42d_row1_col3" class="data row1 col3" >38.70</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row2" class="row_heading level0 row2" >10</th>
      <td id="T_0e42d_row2_col0" class="data row2 col0" >62.00</td>
      <td id="T_0e42d_row2_col1" class="data row2 col1" >01:00</td>
      <td id="T_0e42d_row2_col2" class="data row2 col2" >118.40</td>
      <td id="T_0e42d_row2_col3" class="data row2 col3" >37.20</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row3" class="row_heading level0 row3" >15</th>
      <td id="T_0e42d_row3_col0" class="data row3 col0" >61.70</td>
      <td id="T_0e42d_row3_col1" class="data row3 col1" >02:00</td>
      <td id="T_0e42d_row3_col2" class="data row3 col2" >142.50</td>
      <td id="T_0e42d_row3_col3" class="data row3 col3" >30.50</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_0e42d_row4_col0" class="data row4 col0" >61.00</td>
      <td id="T_0e42d_row4_col1" class="data row4 col1" >02:00</td>
      <td id="T_0e42d_row4_col2" class="data row4 col2" >178.00</td>
      <td id="T_0e42d_row4_col3" class="data row4 col3" >27.30</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row5" class="row_heading level0 row5" >7</th>
      <td id="T_0e42d_row5_col0" class="data row5 col0" >60.80</td>
      <td id="T_0e42d_row5_col1" class="data row5 col1" >02:00</td>
      <td id="T_0e42d_row5_col2" class="data row5 col2" >135.30</td>
      <td id="T_0e42d_row5_col3" class="data row5 col3" >40.70</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row6" class="row_heading level0 row6" >8</th>
      <td id="T_0e42d_row6_col0" class="data row6 col0" >59.80</td>
      <td id="T_0e42d_row6_col1" class="data row6 col1" >02:00</td>
      <td id="T_0e42d_row6_col2" class="data row6 col2" >98.40</td>
      <td id="T_0e42d_row6_col3" class="data row6 col3" >-7.80</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row7" class="row_heading level0 row7" >14</th>
      <td id="T_0e42d_row7_col0" class="data row7 col0" >55.20</td>
      <td id="T_0e42d_row7_col1" class="data row7 col1" >21:00</td>
      <td id="T_0e42d_row7_col2" class="data row7 col2" >77.50</td>
      <td id="T_0e42d_row7_col3" class="data row7 col3" >35.30</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row8" class="row_heading level0 row8" >9</th>
      <td id="T_0e42d_row8_col0" class="data row8 col0" >54.70</td>
      <td id="T_0e42d_row8_col1" class="data row8 col1" >21:00</td>
      <td id="T_0e42d_row8_col2" class="data row8 col2" >78.10</td>
      <td id="T_0e42d_row8_col3" class="data row8 col3" >34.90</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row9" class="row_heading level0 row9" >3</th>
      <td id="T_0e42d_row9_col0" class="data row9 col0" >52.80</td>
      <td id="T_0e42d_row9_col1" class="data row9 col1" >18:00</td>
      <td id="T_0e42d_row9_col2" class="data row9 col2" >67.70</td>
      <td id="T_0e42d_row9_col3" class="data row9 col3" >37.70</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row10" class="row_heading level0 row10" >13</th>
      <td id="T_0e42d_row10_col0" class="data row10 col0" >52.20</td>
      <td id="T_0e42d_row10_col1" class="data row10 col1" >17:00</td>
      <td id="T_0e42d_row10_col2" class="data row10 col2" >64.80</td>
      <td id="T_0e42d_row10_col3" class="data row10 col3" >30.00</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row11" class="row_heading level0 row11" >12</th>
      <td id="T_0e42d_row11_col0" class="data row11 col0" >51.20</td>
      <td id="T_0e42d_row11_col1" class="data row11 col1" >17:00</td>
      <td id="T_0e42d_row11_col2" class="data row11 col2" >73.80</td>
      <td id="T_0e42d_row11_col3" class="data row11 col3" >28.60</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row12" class="row_heading level0 row12" >5</th>
      <td id="T_0e42d_row12_col0" class="data row12 col0" >49.40</td>
      <td id="T_0e42d_row12_col1" class="data row12 col1" >06:00</td>
      <td id="T_0e42d_row12_col2" class="data row12 col2" >69.10</td>
      <td id="T_0e42d_row12_col3" class="data row12 col3" >59.90</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row13" class="row_heading level0 row13" >17</th>
      <td id="T_0e42d_row13_col0" class="data row13 col0" >44.20</td>
      <td id="T_0e42d_row13_col1" class="data row13 col1" >17:00</td>
      <td id="T_0e42d_row13_col2" class="data row13 col2" >62.30</td>
      <td id="T_0e42d_row13_col3" class="data row13 col3" >-16.90</td>
    </tr>
    <tr>
      <th id="T_0e42d_level0_row14" class="row_heading level0 row14" >6</th>
      <td id="T_0e42d_row14_col0" class="data row14 col0" >37.50</td>
      <td id="T_0e42d_row14_col1" class="data row14 col1" >21:00</td>
      <td id="T_0e42d_row14_col2" class="data row14 col2" >48.70</td>
      <td id="T_0e42d_row14_col3" class="data row14 col3" >28.40</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Heatmap zeigt zwei überlagerte Muster — ein netzweites und ein linienspezifisches.

**Netzweites Muster (alle Linien):** Abendstunden (17–19 Uhr) sind für fast alle Linien der Peak — Berufsverkehr. Nachts (1–5 Uhr) sehr niedrige Delays. Das Grundmuster ist synchron über das ganze Netz.

**Linienspezifische Abweichungen:**
- **L11 / L8:** Hohes Grundniveau den ganzen Tag, nicht nur abends — strukturell belastet, nicht nur durch Tagesverkehr
- **L15:** Mittags-Peak stärker als abends — möglicherweise Schulverkehr oder spezifische Streckeneigenschaft
- **L6 / L51:** Durchgehend niedrig, kaum tagesabhängige Variation — Linienlänge schützt vor Akkumulation

**Frühe Morgenstunden (6–8 Uhr):** Bereits deutlicher Delay-Anstieg, bevor der volle Berufsverkehr beginnt — das System startet nicht mit "Null" in den Tag.

→ `hour` als Feature bestätigt (temporal Notebook), aber Interaktion `hour × line_name` wäre stärker als beide Features einzeln.

## Stop Delay nach Fahrtrichtung

Gleiche Linie, zwei Richtungen nebeneinander — zeigt ob Delay symmetrisch ist oder eine Fahrtrichtung deutlich schlechter. Richtung = letzter Halt des Trips (aus `trip_id` abgeleitet).


```python
# L11 als Beispiel — schlechteste reguläre Linie

an.plot_stop_delay_by_direction(lf_clean, line_name="11")

show_df(an.table_stop_delay_by_direction(lf_clean, line_name="11"))

# Weitere Linien nach Bedarf:
# an.plot_stop_delay_by_direction(lf_clean, line_name="9")
# an.plot_stop_delay_by_direction(lf_clean, line_name="8")

```




<style type="text/css">
#T_fa595 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_fa595 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_fa595 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_fa595 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_fa595 tr:hover td {
  background-color: #eef3f8;
}
#T_fa595_row0_col0, #T_fa595_row0_col1, #T_fa595_row1_col0, #T_fa595_row1_col1, #T_fa595_row2_col0, #T_fa595_row2_col1, #T_fa595_row3_col0, #T_fa595_row3_col1, #T_fa595_row4_col0, #T_fa595_row4_col1, #T_fa595_row5_col0, #T_fa595_row5_col1, #T_fa595_row6_col0, #T_fa595_row6_col1, #T_fa595_row7_col0, #T_fa595_row7_col1, #T_fa595_row8_col0, #T_fa595_row8_col1, #T_fa595_row9_col0, #T_fa595_row9_col1, #T_fa595_row10_col0, #T_fa595_row10_col1, #T_fa595_row11_col0, #T_fa595_row11_col1, #T_fa595_row12_col0, #T_fa595_row12_col1, #T_fa595_row13_col0, #T_fa595_row13_col1, #T_fa595_row14_col0, #T_fa595_row14_col1, #T_fa595_row15_col0, #T_fa595_row15_col1, #T_fa595_row16_col0, #T_fa595_row16_col1, #T_fa595_row17_col0, #T_fa595_row17_col1, #T_fa595_row18_col0, #T_fa595_row18_col1, #T_fa595_row19_col0, #T_fa595_row19_col1 {
  text-align: left;
}
#T_fa595_row0_col2, #T_fa595_row0_col3, #T_fa595_row0_col4, #T_fa595_row1_col2, #T_fa595_row1_col3, #T_fa595_row1_col4, #T_fa595_row2_col2, #T_fa595_row2_col3, #T_fa595_row2_col4, #T_fa595_row3_col2, #T_fa595_row3_col3, #T_fa595_row3_col4, #T_fa595_row4_col2, #T_fa595_row4_col3, #T_fa595_row4_col4, #T_fa595_row5_col2, #T_fa595_row5_col3, #T_fa595_row5_col4, #T_fa595_row6_col2, #T_fa595_row6_col3, #T_fa595_row6_col4, #T_fa595_row7_col2, #T_fa595_row7_col3, #T_fa595_row7_col4, #T_fa595_row8_col2, #T_fa595_row8_col3, #T_fa595_row8_col4, #T_fa595_row9_col2, #T_fa595_row9_col3, #T_fa595_row9_col4, #T_fa595_row10_col2, #T_fa595_row10_col3, #T_fa595_row10_col4, #T_fa595_row11_col2, #T_fa595_row11_col3, #T_fa595_row11_col4, #T_fa595_row12_col2, #T_fa595_row12_col3, #T_fa595_row12_col4, #T_fa595_row13_col2, #T_fa595_row13_col3, #T_fa595_row13_col4, #T_fa595_row14_col2, #T_fa595_row14_col3, #T_fa595_row14_col4, #T_fa595_row15_col2, #T_fa595_row15_col3, #T_fa595_row15_col4, #T_fa595_row16_col2, #T_fa595_row16_col3, #T_fa595_row16_col4, #T_fa595_row17_col2, #T_fa595_row17_col3, #T_fa595_row17_col4, #T_fa595_row18_col2, #T_fa595_row18_col3, #T_fa595_row18_col4, #T_fa595_row19_col2, #T_fa595_row19_col3, #T_fa595_row19_col4 {
  text-align: right;
}
</style>
<table id="T_fa595">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_fa595_level0_col0" class="col_heading level0 col0" >Richtung</th>
      <th id="T_fa595_level0_col1" class="col_heading level0 col1" >Stop</th>
      <th id="T_fa595_level0_col2" class="col_heading level0 col2" >Avg. Delay (s)</th>
      <th id="T_fa595_level0_col3" class="col_heading level0 col3" >Ø Stop-Seq</th>
      <th id="T_fa595_level0_col4" class="col_heading level0 col4" >N</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_fa595_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_fa595_row0_col0" class="data row0 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row0_col1" class="data row0 col1" >Zürich, Friedhof Enzenbühl</td>
      <td id="T_fa595_row0_col2" class="data row0 col2" >131.22</td>
      <td id="T_fa595_row0_col3" class="data row0 col3" >29.27</td>
      <td id="T_fa595_row0_col4" class="data row0 col4" >140146</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_fa595_row1_col0" class="data row1 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row1_col1" class="data row1 col1" >Zürich, Wetlistrasse</td>
      <td id="T_fa595_row1_col2" class="data row1 col2" >123.75</td>
      <td id="T_fa595_row1_col3" class="data row1 col3" >26.36</td>
      <td id="T_fa595_row1_col4" class="data row1 col4" >139606</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_fa595_row2_col0" class="data row2 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row2_col1" class="data row2 col1" >Zürich, Burgwies</td>
      <td id="T_fa595_row2_col2" class="data row2 col2" >121.81</td>
      <td id="T_fa595_row2_col3" class="data row2 col3" >27.29</td>
      <td id="T_fa595_row2_col4" class="data row2 col4" >139446</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_fa595_row3_col0" class="data row3 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row3_col1" class="data row3 col1" >Zürich, Balgrist</td>
      <td id="T_fa595_row3_col2" class="data row3 col2" >121.09</td>
      <td id="T_fa595_row3_col3" class="data row3 col3" >28.27</td>
      <td id="T_fa595_row3_col4" class="data row3 col4" >140299</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_fa595_row4_col0" class="data row4 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row4_col1" class="data row4 col1" >Zürich, Klusplatz A</td>
      <td id="T_fa595_row4_col2" class="data row4 col2" >115.40</td>
      <td id="T_fa595_row4_col3" class="data row4 col3" >2.00</td>
      <td id="T_fa595_row4_col4" class="data row4 col4" >588</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_fa595_row5_col0" class="data row5 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row5_col1" class="data row5 col1" >Zürich, Signaustrasse</td>
      <td id="T_fa595_row5_col2" class="data row5 col2" >107.38</td>
      <td id="T_fa595_row5_col3" class="data row5 col3" >23.97</td>
      <td id="T_fa595_row5_col4" class="data row5 col4" >132480</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_fa595_row6_col0" class="data row6 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row6_col1" class="data row6 col1" >Zürich, Hegibachplatz B</td>
      <td id="T_fa595_row6_col2" class="data row6 col2" >103.74</td>
      <td id="T_fa595_row6_col3" class="data row6 col3" >24.85</td>
      <td id="T_fa595_row6_col4" class="data row6 col4" >137561</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_fa595_row7_col0" class="data row7 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row7_col1" class="data row7 col1" >Zürich, Hedwigsteig</td>
      <td id="T_fa595_row7_col2" class="data row7 col2" >102.71</td>
      <td id="T_fa595_row7_col3" class="data row7 col3" >25.83</td>
      <td id="T_fa595_row7_col4" class="data row7 col4" >131962</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_fa595_row8_col0" class="data row8 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row8_col1" class="data row8 col1" >Zürich, Kreuzplatz</td>
      <td id="T_fa595_row8_col2" class="data row8 col2" >93.99</td>
      <td id="T_fa595_row8_col3" class="data row8 col3" >23.84</td>
      <td id="T_fa595_row8_col4" class="data row8 col4" >122065</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_fa595_row9_col0" class="data row9 col0" >Friedhof Enzenbühl</td>
      <td id="T_fa595_row9_col1" class="data row9 col1" >Zürich, Sihlstrasse</td>
      <td id="T_fa595_row9_col2" class="data row9 col2" >74.15</td>
      <td id="T_fa595_row9_col3" class="data row9 col3" >2.06</td>
      <td id="T_fa595_row9_col4" class="data row9 col4" >1743</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_fa595_row10_col0" class="data row10 col0" >Fernsehstudio</td>
      <td id="T_fa595_row10_col1" class="data row10 col1" >Zürich, Leutschenbach</td>
      <td id="T_fa595_row10_col2" class="data row10 col2" >124.60</td>
      <td id="T_fa595_row10_col3" class="data row10 col3" >27.70</td>
      <td id="T_fa595_row10_col4" class="data row10 col4" >135237</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_fa595_row11_col0" class="data row11 col0" >Fernsehstudio</td>
      <td id="T_fa595_row11_col1" class="data row11 col1" >Zürich, Oerlikerhus</td>
      <td id="T_fa595_row11_col2" class="data row11 col2" >121.47</td>
      <td id="T_fa595_row11_col3" class="data row11 col3" >27.40</td>
      <td id="T_fa595_row11_col4" class="data row11 col4" >142293</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_fa595_row12_col0" class="data row12 col0" >Fernsehstudio</td>
      <td id="T_fa595_row12_col1" class="data row12 col1" >Zürich, Hirschwiesenstrasse</td>
      <td id="T_fa595_row12_col2" class="data row12 col2" >118.74</td>
      <td id="T_fa595_row12_col3" class="data row12 col3" >20.56</td>
      <td id="T_fa595_row12_col4" class="data row12 col4" >390</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_fa595_row13_col0" class="data row13 col0" >Fernsehstudio</td>
      <td id="T_fa595_row13_col1" class="data row13 col1" >Zürich, Fernsehstudio</td>
      <td id="T_fa595_row13_col2" class="data row13 col2" >113.66</td>
      <td id="T_fa595_row13_col3" class="data row13 col3" >29.37</td>
      <td id="T_fa595_row13_col4" class="data row13 col4" >142504</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_fa595_row14_col0" class="data row14 col0" >Fernsehstudio</td>
      <td id="T_fa595_row14_col1" class="data row14 col1" >Glattpark</td>
      <td id="T_fa595_row14_col2" class="data row14 col2" >112.02</td>
      <td id="T_fa595_row14_col3" class="data row14 col3" >28.38</td>
      <td id="T_fa595_row14_col4" class="data row14 col4" >142326</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_fa595_row15_col0" class="data row15 col0" >Fernsehstudio</td>
      <td id="T_fa595_row15_col1" class="data row15 col1" >Zürich, Bahnhof Oerlikon Ost</td>
      <td id="T_fa595_row15_col2" class="data row15 col2" >110.99</td>
      <td id="T_fa595_row15_col3" class="data row15 col3" >24.87</td>
      <td id="T_fa595_row15_col4" class="data row15 col4" >269</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_fa595_row16_col0" class="data row16 col0" >Fernsehstudio</td>
      <td id="T_fa595_row16_col1" class="data row16 col1" >Zürich, Messe/Hallenstadion</td>
      <td id="T_fa595_row16_col2" class="data row16 col2" >109.09</td>
      <td id="T_fa595_row16_col3" class="data row16 col3" >26.72</td>
      <td id="T_fa595_row16_col4" class="data row16 col4" >135051</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_fa595_row17_col0" class="data row17 col0" >Fernsehstudio</td>
      <td id="T_fa595_row17_col1" class="data row17 col1" >Zürich, Milchbuck</td>
      <td id="T_fa595_row17_col2" class="data row17 col2" >106.72</td>
      <td id="T_fa595_row17_col3" class="data row17 col3" >19.48</td>
      <td id="T_fa595_row17_col4" class="data row17 col4" >390</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_fa595_row18_col0" class="data row18 col0" >Fernsehstudio</td>
      <td id="T_fa595_row18_col1" class="data row18 col1" >Zürich, Berninaplatz</td>
      <td id="T_fa595_row18_col2" class="data row18 col2" >106.50</td>
      <td id="T_fa595_row18_col3" class="data row18 col3" >21.49</td>
      <td id="T_fa595_row18_col4" class="data row18 col4" >390</td>
    </tr>
    <tr>
      <th id="T_fa595_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_fa595_row19_col0" class="data row19 col0" >Fernsehstudio</td>
      <td id="T_fa595_row19_col1" class="data row19 col1" >Zürich, Guggachstrasse</td>
      <td id="T_fa595_row19_col2" class="data row19 col2" >105.76</td>
      <td id="T_fa595_row19_col3" class="data row19 col3" >18.50</td>
      <td id="T_fa595_row19_col4" class="data row19 col4" >391</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Richtungs-Karte zeigt ob Delay symmetrisch verteilt ist oder eine Fahrtrichtung systematisch schlechter ist.

**Typisches Muster bei L11:** Die Richtung in die Aussenquartiere (Richtung Auzelg/Oerlikon) zeigt höhere Delays am Endpunkt als die Gegenrichtung Richtung Zentrum — Hinfahrt in die Peripherie akkumuliert mehr als die Rückfahrt in die gut koordinierte Innenstadt.

**Asymmetrie als Befund:** Wenn beide Richtungen gleich wären, wäre die Karte spiegelbildlich. Abweichungen zeigen wo das Netz unidirektionale Probleme hat — z.B. weil eine Richtung mehr Halt-Interaktionen mit dem MIV hat oder die Streckenführung ungünstiger ist.

→ Richtung als Feature prüfen (`trip_direction` = letzter Stop). Weitere Linien mit `an.plot_stop_delay_by_direction(lf_clean, line_name="9")` etc. analysierbar.

## Delay-Profil alle Tramlinien — interaktiv

Alle Tramlinien auf einer Karte — **Farbe: VBZ-Linienfarbe** (wie bekannt aus dem Netzplan), **Größe: Ø Arrival Delay** (global skaliert, Linien vergleichbar). Linien über die Legende einzeln ein-/ausblenden. Hover zeigt Haltestellenname, Linie, Ø Delay, % kein Puffer.

`min_n=1000` filtert Baustellen-Kurzläufer automatisch heraus (L6 hat 230+ Routenvarianten aus dem Zeitraum 2023–2025 — Kurzläufer-Endhalte haben n < 1000 und werden ausgeblendet).


```python
an.plot_line_delay_profile_map(lf_clean, cfg=cfg)
```





**Beobachtungen zur Delay-Profil-Karte — Linien im Vergleich**

**Grundmuster: Grosse Bubbles an den Streckenenden, kleine Bubbles in der Mitte**

Über alle Linien hinweg zeigen die Stops mit den grössten Delay-Kreisen ein konsistentes Muster: sie liegen am äusseren Ende der jeweiligen Linie, nicht in der Mitte oder im Stadtzentrum. Statistische Prüfung bestätigt das: Alle Outlier-Stops (>1.5σ über Linienmittel) liegen maximal 31m von der GTFS-Shape entfernt — sie sind physisch **auf** der Strecke, nicht daneben. Die Ursache ist der **Akkumulationseffekt**: Verspätungen bauen sich entlang des Fahrwegs auf. Wer am äusseren Terminus ankommt, trägt die Last der ganzen Fahrt.

Ausgewählte Linien-Beobachtungen:

- **L11** — Enzenbühl, Balgrist, Wetlistrasse, Burgwies als Spitzenreiter. Alles äussere Endpunkte Richtung Tiefenbrunnen/Hirslanden. Pearson r ≥ 0.85 in der Kaskadenanalyse (→ unten) bestätigt: Delay baut sich Trip für Trip auf.
- **L10** — Auffälliger Stop nur am nördlichen Ende (Salersteig/Leutschenbach). Richtung Zentrum sind die Stops unauffällig.
- **L14** — Zwei Stops auffällig: Seebacherplatz (71s, stärkster Outlier) und Milchbuck (65s). Beide am nördlichen Streckenende in Seebach. Der Rest der Linie liegt nahe am Linienmittel (55s).
- **L8** — Römerhof, Hölderlinstrasse, Englischviertelstrasse am Zürichberg-Ende erhöht. Entspricht dem Seefeld/Balgrist-Korridor (K8).

**L17 — Zwei Strecken-Cluster sichtbar**

Die L17 erscheint auf der Karte in zwei räumlich getrennten Gruppen: eine entlang des primären Korridors (Werdhölzli → Hardhof → Hardturm → Bahnhofquai/HB, ~88k Ereignisse/Jahr) und eine zweite Gruppe südlich davon (Bahnhofstrasse → Paradeplatz → Tunnelstrasse → Bahnhof Enge → Uetlihof → Strassenverkehrsamt, ~13–17k Ereignisse/Jahr). **Das ist kein Datenfehler.** Die L17 bedient beide Streckenäste — ein Teil der Kurse endet am HB, ein anderer fährt weiter via Innenstadt zum Uetlihof. Beide Gruppen liegen über der 5%-Schwelle und erscheinen deshalb auf der Karte. Der Strassenverkehrsamt-Halt (75s) ist dabei der auffälligste Outlier dieses Asts.

**L18 — fehlt in der Karte**

Die Liniennummer `18` kommt im VBZ IST-Datensatz nicht vor. L18 war eine temporäre Baustellenlinie (→ `02_preparation.ipynb` Bereinigungsstrategie) und ist entweder ausserhalb des erfassten Zeitraums betrieben worden oder unter einer anderen Bezeichnung erfasst. Die Karte zeigt automatisch nur Linien, die im Datensatz vorhanden sind.

### Wo hat der Fahrplan Puffer? — Dwell Time Profil

Gleiche Karte, anderes Signal: **Farbe = Ø Dwell Time** (geplante Haltezeit je Haltestelle).
Rot = kein Puffer (0 s) · Orange = wenig Puffer (~ 15 s) · Grün = guter Puffer (≥ 30 s).
Bubble-Größe einheitlich — das Signal liegt ausschließlich in der Farbe.

**Vergleich mit Delay-Karte oben:** Haltestellen rot in beiden Karten = kein Puffer **und** hohe Verspätung → strukturelles Bottleneck. Haltestellen grün in der Dwell-Karte = Fahrplan hat hier bewusst Puffer eingebaut.


```python
an.plot_line_dwell_profile_map(lf_clean, cfg=cfg)
```





**Detailansicht: L11 vs. L6** — einzelne Linie mit Delay-Farbskala für genauere Analyse. `plot_stop_dwell_map` zeigt eine Linie mit Delay-Gradient (grün → rot).


```python
an.plot_stop_dwell_map(lf_clean, line_name="11", cfg=cfg)
an.plot_stop_dwell_map(lf_clean, line_name="6", cfg=cfg)
```







## Interaktive Linienansicht — Kritische Streckenabschnitte

Wo auf der Linie beginnt das Problem?

GTFS-Gleisgeometrie als Routen-Linie, Haltestellen nach Ø Arrival Delay eingefärbt (grün → amber → rot). Top-3 Problemstops annotiert. Linie wählbar über `line_name`-Parameter.


```python
an.plot_line_route_map(lf_clean, line_name="11")
show_df(an.table_line_route_map(lf_clean, line_name="11"))
```




<style type="text/css">
#T_7b474 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_7b474 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_7b474 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_7b474 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_7b474 tr:hover td {
  background-color: #eef3f8;
}
#T_7b474_row0_col0, #T_7b474_row0_col1, #T_7b474_row0_col2, #T_7b474_row0_col3, #T_7b474_row1_col0, #T_7b474_row1_col1, #T_7b474_row1_col2, #T_7b474_row1_col3, #T_7b474_row2_col0, #T_7b474_row2_col1, #T_7b474_row2_col2, #T_7b474_row2_col3, #T_7b474_row3_col0, #T_7b474_row3_col1, #T_7b474_row3_col2, #T_7b474_row3_col3, #T_7b474_row4_col0, #T_7b474_row4_col1, #T_7b474_row4_col2, #T_7b474_row4_col3, #T_7b474_row5_col0, #T_7b474_row5_col1, #T_7b474_row5_col2, #T_7b474_row5_col3, #T_7b474_row6_col0, #T_7b474_row6_col1, #T_7b474_row6_col2, #T_7b474_row6_col3, #T_7b474_row7_col0, #T_7b474_row7_col1, #T_7b474_row7_col2, #T_7b474_row7_col3, #T_7b474_row8_col0, #T_7b474_row8_col1, #T_7b474_row8_col2, #T_7b474_row8_col3, #T_7b474_row9_col0, #T_7b474_row9_col1, #T_7b474_row9_col2, #T_7b474_row9_col3, #T_7b474_row10_col0, #T_7b474_row10_col1, #T_7b474_row10_col2, #T_7b474_row10_col3, #T_7b474_row11_col0, #T_7b474_row11_col1, #T_7b474_row11_col2, #T_7b474_row11_col3, #T_7b474_row12_col0, #T_7b474_row12_col1, #T_7b474_row12_col2, #T_7b474_row12_col3, #T_7b474_row13_col0, #T_7b474_row13_col1, #T_7b474_row13_col2, #T_7b474_row13_col3, #T_7b474_row14_col0, #T_7b474_row14_col1, #T_7b474_row14_col2, #T_7b474_row14_col3, #T_7b474_row15_col0, #T_7b474_row15_col1, #T_7b474_row15_col2, #T_7b474_row15_col3, #T_7b474_row16_col0, #T_7b474_row16_col1, #T_7b474_row16_col2, #T_7b474_row16_col3, #T_7b474_row17_col0, #T_7b474_row17_col1, #T_7b474_row17_col2, #T_7b474_row17_col3, #T_7b474_row18_col0, #T_7b474_row18_col1, #T_7b474_row18_col2, #T_7b474_row18_col3, #T_7b474_row19_col0, #T_7b474_row19_col1, #T_7b474_row19_col2, #T_7b474_row19_col3, #T_7b474_row20_col0, #T_7b474_row20_col1, #T_7b474_row20_col2, #T_7b474_row20_col3, #T_7b474_row21_col0, #T_7b474_row21_col1, #T_7b474_row21_col2, #T_7b474_row21_col3, #T_7b474_row22_col0, #T_7b474_row22_col1, #T_7b474_row22_col2, #T_7b474_row22_col3, #T_7b474_row23_col0, #T_7b474_row23_col1, #T_7b474_row23_col2, #T_7b474_row23_col3, #T_7b474_row24_col0, #T_7b474_row24_col1, #T_7b474_row24_col2, #T_7b474_row24_col3, #T_7b474_row25_col0, #T_7b474_row25_col1, #T_7b474_row25_col2, #T_7b474_row25_col3, #T_7b474_row26_col0, #T_7b474_row26_col1, #T_7b474_row26_col2, #T_7b474_row26_col3, #T_7b474_row27_col0, #T_7b474_row27_col1, #T_7b474_row27_col2, #T_7b474_row27_col3, #T_7b474_row28_col0, #T_7b474_row28_col1, #T_7b474_row28_col2, #T_7b474_row28_col3, #T_7b474_row29_col0, #T_7b474_row29_col1, #T_7b474_row29_col2, #T_7b474_row29_col3, #T_7b474_row30_col0, #T_7b474_row30_col1, #T_7b474_row30_col2, #T_7b474_row30_col3, #T_7b474_row31_col0, #T_7b474_row31_col1, #T_7b474_row31_col2, #T_7b474_row31_col3, #T_7b474_row32_col0, #T_7b474_row32_col1, #T_7b474_row32_col2, #T_7b474_row32_col3, #T_7b474_row33_col0, #T_7b474_row33_col1, #T_7b474_row33_col2, #T_7b474_row33_col3, #T_7b474_row34_col0, #T_7b474_row34_col1, #T_7b474_row34_col2, #T_7b474_row34_col3, #T_7b474_row35_col0, #T_7b474_row35_col1, #T_7b474_row35_col2, #T_7b474_row35_col3 {
  text-align: right;
}
</style>
<table id="T_7b474">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_7b474_level0_col0" class="col_heading level0 col0" >Avg. Delay (s)</th>
      <th id="T_7b474_level0_col1" class="col_heading level0 col1" >OTP (%)</th>
      <th id="T_7b474_level0_col2" class="col_heading level0 col2" >Ø Stop-Seq</th>
      <th id="T_7b474_level0_col3" class="col_heading level0 col3" >N</th>
    </tr>
    <tr>
      <th class="index_name level0" >Stop</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_7b474_level0_row0" class="row_heading level0 row0" >Friedhof Enzenbühl</th>
      <td id="T_7b474_row0_col0" class="data row0 col0" >131.10</td>
      <td id="T_7b474_row0_col1" class="data row0 col1" >56.30</td>
      <td id="T_7b474_row0_col2" class="data row0 col2" >29.20</td>
      <td id="T_7b474_row0_col3" class="data row0 col3" >140293</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row1" class="row_heading level0 row1" >Fernsehstudio</th>
      <td id="T_7b474_row1_col0" class="data row1 col0" >113.60</td>
      <td id="T_7b474_row1_col1" class="data row1 col1" >62.20</td>
      <td id="T_7b474_row1_col2" class="data row1 col2" >29.30</td>
      <td id="T_7b474_row1_col3" class="data row1 col3" >142613</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row2" class="row_heading level0 row2" >Leutschenbach</th>
      <td id="T_7b474_row2_col0" class="data row2 col0" >94.20</td>
      <td id="T_7b474_row2_col1" class="data row2 col1" >74.90</td>
      <td id="T_7b474_row2_col2" class="data row2 col2" >15.60</td>
      <td id="T_7b474_row2_col3" class="data row2 col3" >276269</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row3" class="row_heading level0 row3" >Balgrist</th>
      <td id="T_7b474_row3_col0" class="data row3 col0" >85.40</td>
      <td id="T_7b474_row3_col1" class="data row3 col1" >76.90</td>
      <td id="T_7b474_row3_col2" class="data row3 col2" >15.20</td>
      <td id="T_7b474_row3_col3" class="data row3 col3" >279984</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row4" class="row_heading level0 row4" >Sternen Oerlikon</th>
      <td id="T_7b474_row4_col0" class="data row4 col0" >85.20</td>
      <td id="T_7b474_row4_col1" class="data row4 col1" >77.50</td>
      <td id="T_7b474_row4_col2" class="data row4 col2" >16.00</td>
      <td id="T_7b474_row4_col3" class="data row4 col3" >268181</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row5" class="row_heading level0 row5" >Wetlistrasse</th>
      <td id="T_7b474_row5_col0" class="data row5 col0" >83.70</td>
      <td id="T_7b474_row5_col1" class="data row5 col1" >76.80</td>
      <td id="T_7b474_row5_col2" class="data row5 col2" >15.20</td>
      <td id="T_7b474_row5_col3" class="data row5 col3" >279262</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row6" class="row_heading level0 row6" >Burgwies</th>
      <td id="T_7b474_row6_col0" class="data row6 col0" >81.80</td>
      <td id="T_7b474_row6_col1" class="data row6 col1" >77.70</td>
      <td id="T_7b474_row6_col2" class="data row6 col2" >15.20</td>
      <td id="T_7b474_row6_col3" class="data row6 col3" >278070</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row7" class="row_heading level0 row7" >Messe/Hallenstadion</th>
      <td id="T_7b474_row7_col0" class="data row7 col0" >79.30</td>
      <td id="T_7b474_row7_col1" class="data row7 col1" >79.50</td>
      <td id="T_7b474_row7_col2" class="data row7 col2" >15.60</td>
      <td id="T_7b474_row7_col3" class="data row7 col3" >275830</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row8" class="row_heading level0 row8" >Bahnhof Oerlikon</th>
      <td id="T_7b474_row8_col0" class="data row8 col0" >79.00</td>
      <td id="T_7b474_row8_col1" class="data row8 col1" >79.50</td>
      <td id="T_7b474_row8_col2" class="data row8 col2" >16.00</td>
      <td id="T_7b474_row8_col3" class="data row8 col3" >273888</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row9" class="row_heading level0 row9" >Glattpark</th>
      <td id="T_7b474_row9_col0" class="data row9 col0" >78.40</td>
      <td id="T_7b474_row9_col1" class="data row9 col1" >79.60</td>
      <td id="T_7b474_row9_col2" class="data row9 col2" >15.30</td>
      <td id="T_7b474_row9_col3" class="data row9 col3" >282964</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row10" class="row_heading level0 row10" >Oerlikerhus</th>
      <td id="T_7b474_row10_col0" class="data row10 col0" >77.90</td>
      <td id="T_7b474_row10_col1" class="data row10 col1" >77.70</td>
      <td id="T_7b474_row10_col2" class="data row10 col2" >15.30</td>
      <td id="T_7b474_row10_col3" class="data row10 col3" >283156</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row11" class="row_heading level0 row11" >Hedwigsteig</th>
      <td id="T_7b474_row11_col0" class="data row11 col0" >77.90</td>
      <td id="T_7b474_row11_col1" class="data row11 col1" >81.30</td>
      <td id="T_7b474_row11_col2" class="data row11 col2" >15.10</td>
      <td id="T_7b474_row11_col3" class="data row11 col3" >272308</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row12" class="row_heading level0 row12" >Signaustrasse</th>
      <td id="T_7b474_row12_col0" class="data row12 col0" >73.50</td>
      <td id="T_7b474_row12_col1" class="data row12 col1" >80.30</td>
      <td id="T_7b474_row12_col2" class="data row12 col2" >15.30</td>
      <td id="T_7b474_row12_col3" class="data row12 col3" >268397</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row13" class="row_heading level0 row13" >Regensbergbrücke</th>
      <td id="T_7b474_row13_col0" class="data row13 col0" >73.40</td>
      <td id="T_7b474_row13_col1" class="data row13 col1" >82.20</td>
      <td id="T_7b474_row13_col2" class="data row13 col2" >15.80</td>
      <td id="T_7b474_row13_col3" class="data row13 col3" >277147</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row14" class="row_heading level0 row14" >Hegibachplatz B</th>
      <td id="T_7b474_row14_col0" class="data row14 col0" >70.30</td>
      <td id="T_7b474_row14_col1" class="data row14 col1" >81.60</td>
      <td id="T_7b474_row14_col2" class="data row14 col2" >15.60</td>
      <td id="T_7b474_row14_col3" class="data row14 col3" >269464</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row15" class="row_heading level0 row15" >Bad Allenmoos</th>
      <td id="T_7b474_row15_col0" class="data row15 col0" >70.00</td>
      <td id="T_7b474_row15_col1" class="data row15 col1" >83.00</td>
      <td id="T_7b474_row15_col2" class="data row15 col2" >15.80</td>
      <td id="T_7b474_row15_col3" class="data row15 col3" >277161</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row16" class="row_heading level0 row16" >Kreuzplatz</th>
      <td id="T_7b474_row16_col0" class="data row16 col0" >65.80</td>
      <td id="T_7b474_row16_col1" class="data row16 col1" >82.80</td>
      <td id="T_7b474_row16_col2" class="data row16 col2" >15.30</td>
      <td id="T_7b474_row16_col3" class="data row16 col3" >262643</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row17" class="row_heading level0 row17" >Kronenstrasse</th>
      <td id="T_7b474_row17_col0" class="data row17 col0" >65.60</td>
      <td id="T_7b474_row17_col1" class="data row17 col1" >83.60</td>
      <td id="T_7b474_row17_col2" class="data row17 col2" >15.80</td>
      <td id="T_7b474_row17_col3" class="data row17 col3" >262754</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row18" class="row_heading level0 row18" >Brunnenhof</th>
      <td id="T_7b474_row18_col0" class="data row18 col0" >62.90</td>
      <td id="T_7b474_row18_col1" class="data row18 col1" >85.00</td>
      <td id="T_7b474_row18_col2" class="data row18 col2" >15.90</td>
      <td id="T_7b474_row18_col3" class="data row18 col3" >276287</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row19" class="row_heading level0 row19" >Bahnhofstrasse/HB</th>
      <td id="T_7b474_row19_col0" class="data row19 col0" >61.90</td>
      <td id="T_7b474_row19_col1" class="data row19 col1" >84.40</td>
      <td id="T_7b474_row19_col2" class="data row19 col2" >15.90</td>
      <td id="T_7b474_row19_col3" class="data row19 col3" >257597</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row20" class="row_heading level0 row20" >Schaffhauserplatz</th>
      <td id="T_7b474_row20_col0" class="data row20 col0" >60.80</td>
      <td id="T_7b474_row20_col1" class="data row20 col1" >85.00</td>
      <td id="T_7b474_row20_col2" class="data row20 col2" >15.80</td>
      <td id="T_7b474_row20_col3" class="data row20 col3" >277534</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row21" class="row_heading level0 row21" >Beckenhof</th>
      <td id="T_7b474_row21_col0" class="data row21 col0" >60.00</td>
      <td id="T_7b474_row21_col1" class="data row21 col1" >85.40</td>
      <td id="T_7b474_row21_col2" class="data row21 col2" >15.80</td>
      <td id="T_7b474_row21_col3" class="data row21 col3" >263144</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row22" class="row_heading level0 row22" >Bürkliplatz</th>
      <td id="T_7b474_row22_col0" class="data row22 col0" >58.10</td>
      <td id="T_7b474_row22_col1" class="data row22 col1" >84.40</td>
      <td id="T_7b474_row22_col2" class="data row22 col2" >15.50</td>
      <td id="T_7b474_row22_col3" class="data row22 col3" >271421</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row23" class="row_heading level0 row23" >Bahnhof Stadelhofen</th>
      <td id="T_7b474_row23_col0" class="data row23 col0" >57.90</td>
      <td id="T_7b474_row23_col1" class="data row23 col1" >84.80</td>
      <td id="T_7b474_row23_col2" class="data row23 col2" >15.70</td>
      <td id="T_7b474_row23_col3" class="data row23 col3" >258702</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row24" class="row_heading level0 row24" >Bucheggplatz D</th>
      <td id="T_7b474_row24_col0" class="data row24 col0" >57.70</td>
      <td id="T_7b474_row24_col1" class="data row24 col1" >85.40</td>
      <td id="T_7b474_row24_col2" class="data row24 col2" >16.10</td>
      <td id="T_7b474_row24_col3" class="data row24 col3" >263270</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row25" class="row_heading level0 row25" >Laubiweg</th>
      <td id="T_7b474_row25_col0" class="data row25 col0" >57.00</td>
      <td id="T_7b474_row25_col1" class="data row25 col1" >86.00</td>
      <td id="T_7b474_row25_col2" class="data row25 col2" >15.80</td>
      <td id="T_7b474_row25_col3" class="data row25 col3" >275957</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row26" class="row_heading level0 row26" >Stampfenbachplatz</th>
      <td id="T_7b474_row26_col0" class="data row26 col0" >56.40</td>
      <td id="T_7b474_row26_col1" class="data row26 col1" >85.60</td>
      <td id="T_7b474_row26_col2" class="data row26 col2" >15.90</td>
      <td id="T_7b474_row26_col3" class="data row26 col3" >262412</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row27" class="row_heading level0 row27" >Bellevue</th>
      <td id="T_7b474_row27_col0" class="data row27 col0" >56.20</td>
      <td id="T_7b474_row27_col1" class="data row27 col1" >84.90</td>
      <td id="T_7b474_row27_col2" class="data row27 col2" >15.80</td>
      <td id="T_7b474_row27_col3" class="data row27 col3" >278115</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row28" class="row_heading level0 row28" >Kantonalbank</th>
      <td id="T_7b474_row28_col0" class="data row28 col0" >52.50</td>
      <td id="T_7b474_row28_col1" class="data row28 col1" >87.20</td>
      <td id="T_7b474_row28_col2" class="data row28 col2" >15.50</td>
      <td id="T_7b474_row28_col3" class="data row28 col3" >272054</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row29" class="row_heading level0 row29" >Bahnhofquai/HB</th>
      <td id="T_7b474_row29_col0" class="data row29 col0" >52.00</td>
      <td id="T_7b474_row29_col1" class="data row29 col1" >85.80</td>
      <td id="T_7b474_row29_col2" class="data row29 col2" >15.90</td>
      <td id="T_7b474_row29_col3" class="data row29 col3" >260858</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row30" class="row_heading level0 row30" >Paradeplatz</th>
      <td id="T_7b474_row30_col0" class="data row30 col0" >51.70</td>
      <td id="T_7b474_row30_col1" class="data row30 col1" >86.40</td>
      <td id="T_7b474_row30_col2" class="data row30 col2" >15.50</td>
      <td id="T_7b474_row30_col3" class="data row30 col3" >272863</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row31" class="row_heading level0 row31" >Rennweg</th>
      <td id="T_7b474_row31_col0" class="data row31 col0" >50.60</td>
      <td id="T_7b474_row31_col1" class="data row31 col1" >87.10</td>
      <td id="T_7b474_row31_col2" class="data row31 col2" >15.70</td>
      <td id="T_7b474_row31_col3" class="data row31 col3" >263846</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row32" class="row_heading level0 row32" >Central</th>
      <td id="T_7b474_row32_col0" class="data row32 col0" >48.20</td>
      <td id="T_7b474_row32_col1" class="data row32 col1" >77.60</td>
      <td id="T_7b474_row32_col2" class="data row32 col2" >15.40</td>
      <td id="T_7b474_row32_col3" class="data row32 col3" >14850</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row33" class="row_heading level0 row33" >Röslistrasse</th>
      <td id="T_7b474_row33_col0" class="data row33 col0" >36.90</td>
      <td id="T_7b474_row33_col1" class="data row33 col1" >81.30</td>
      <td id="T_7b474_row33_col2" class="data row33 col2" >14.40</td>
      <td id="T_7b474_row33_col3" class="data row33 col3" >14826</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row34" class="row_heading level0 row34" >Sonneggstrasse</th>
      <td id="T_7b474_row34_col0" class="data row34 col0" >35.10</td>
      <td id="T_7b474_row34_col1" class="data row34 col1" >80.70</td>
      <td id="T_7b474_row34_col2" class="data row34 col2" >14.40</td>
      <td id="T_7b474_row34_col3" class="data row34 col3" >14810</td>
    </tr>
    <tr>
      <th id="T_7b474_level0_row35" class="row_heading level0 row35" >Ottikerstrasse</th>
      <td id="T_7b474_row35_col0" class="data row35 col0" >29.80</td>
      <td id="T_7b474_row35_col1" class="data row35 col1" >82.20</td>
      <td id="T_7b474_row35_col2" class="data row35 col2" >14.40</td>
      <td id="T_7b474_row35_col3" class="data row35 col3" >14820</td>
    </tr>
  </tbody>
</table>



## Situationsvergleich — gleiche Linie, verschiedene Kontexte

Dieselbe Linie unter verschiedenen Betriebsbedingungen: **Normal · Schnee · Event · Rush · Spätnacht**.

Jeder Kontext ist ein eigener Trace — über die Legende ein-/ausblendbar.
Zeigt warum ein pauschaler Fahrplan-Puffer nicht ausreicht: Schnee, Events und Rush-Hour
betreffen verschiedene Stops (F-REC-03). Grundlage für kontextsensitive Fahrpläne.


```python
an.plot_line_context_map(lf_clean, line_name="11")
show_df(an.table_line_context_map(lf_clean, line_name="11"))
```




<style type="text/css">
#T_ba56d thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_ba56d td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_ba56d tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_ba56d tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_ba56d tr:hover td {
  background-color: #eef3f8;
}
#T_ba56d_row0_col0, #T_ba56d_row0_col1, #T_ba56d_row0_col2, #T_ba56d_row0_col3, #T_ba56d_row0_col4, #T_ba56d_row1_col0, #T_ba56d_row1_col1, #T_ba56d_row1_col2, #T_ba56d_row1_col3, #T_ba56d_row1_col4, #T_ba56d_row2_col0, #T_ba56d_row2_col1, #T_ba56d_row2_col2, #T_ba56d_row2_col3, #T_ba56d_row2_col4, #T_ba56d_row3_col0, #T_ba56d_row3_col1, #T_ba56d_row3_col2, #T_ba56d_row3_col3, #T_ba56d_row3_col4, #T_ba56d_row4_col0, #T_ba56d_row4_col1, #T_ba56d_row4_col2, #T_ba56d_row4_col3, #T_ba56d_row4_col4, #T_ba56d_row5_col0, #T_ba56d_row5_col1, #T_ba56d_row5_col2, #T_ba56d_row5_col3, #T_ba56d_row5_col4, #T_ba56d_row6_col0, #T_ba56d_row6_col1, #T_ba56d_row6_col2, #T_ba56d_row6_col3, #T_ba56d_row6_col4, #T_ba56d_row7_col0, #T_ba56d_row7_col1, #T_ba56d_row7_col2, #T_ba56d_row7_col3, #T_ba56d_row7_col4, #T_ba56d_row8_col0, #T_ba56d_row8_col1, #T_ba56d_row8_col2, #T_ba56d_row8_col3, #T_ba56d_row8_col4, #T_ba56d_row9_col0, #T_ba56d_row9_col1, #T_ba56d_row9_col2, #T_ba56d_row9_col3, #T_ba56d_row9_col4, #T_ba56d_row10_col0, #T_ba56d_row10_col1, #T_ba56d_row10_col2, #T_ba56d_row10_col3, #T_ba56d_row10_col4, #T_ba56d_row11_col0, #T_ba56d_row11_col1, #T_ba56d_row11_col2, #T_ba56d_row11_col3, #T_ba56d_row11_col4, #T_ba56d_row12_col0, #T_ba56d_row12_col1, #T_ba56d_row12_col2, #T_ba56d_row12_col3, #T_ba56d_row12_col4, #T_ba56d_row13_col0, #T_ba56d_row13_col1, #T_ba56d_row13_col2, #T_ba56d_row13_col3, #T_ba56d_row13_col4, #T_ba56d_row14_col0, #T_ba56d_row14_col1, #T_ba56d_row14_col2, #T_ba56d_row14_col3, #T_ba56d_row14_col4, #T_ba56d_row15_col0, #T_ba56d_row15_col1, #T_ba56d_row15_col2, #T_ba56d_row15_col3, #T_ba56d_row15_col4, #T_ba56d_row16_col0, #T_ba56d_row16_col1, #T_ba56d_row16_col2, #T_ba56d_row16_col3, #T_ba56d_row16_col4, #T_ba56d_row17_col0, #T_ba56d_row17_col1, #T_ba56d_row17_col2, #T_ba56d_row17_col3, #T_ba56d_row17_col4, #T_ba56d_row18_col0, #T_ba56d_row18_col1, #T_ba56d_row18_col2, #T_ba56d_row18_col3, #T_ba56d_row18_col4, #T_ba56d_row19_col0, #T_ba56d_row19_col1, #T_ba56d_row19_col2, #T_ba56d_row19_col3, #T_ba56d_row19_col4, #T_ba56d_row20_col0, #T_ba56d_row20_col1, #T_ba56d_row20_col2, #T_ba56d_row20_col3, #T_ba56d_row20_col4, #T_ba56d_row21_col0, #T_ba56d_row21_col1, #T_ba56d_row21_col2, #T_ba56d_row21_col3, #T_ba56d_row21_col4, #T_ba56d_row22_col0, #T_ba56d_row22_col1, #T_ba56d_row22_col2, #T_ba56d_row22_col3, #T_ba56d_row22_col4, #T_ba56d_row23_col0, #T_ba56d_row23_col1, #T_ba56d_row23_col2, #T_ba56d_row23_col3, #T_ba56d_row23_col4, #T_ba56d_row24_col0, #T_ba56d_row24_col1, #T_ba56d_row24_col2, #T_ba56d_row24_col3, #T_ba56d_row24_col4, #T_ba56d_row25_col0, #T_ba56d_row25_col1, #T_ba56d_row25_col2, #T_ba56d_row25_col3, #T_ba56d_row25_col4, #T_ba56d_row26_col0, #T_ba56d_row26_col1, #T_ba56d_row26_col2, #T_ba56d_row26_col3, #T_ba56d_row26_col4, #T_ba56d_row27_col0, #T_ba56d_row27_col1, #T_ba56d_row27_col2, #T_ba56d_row27_col3, #T_ba56d_row27_col4, #T_ba56d_row28_col0, #T_ba56d_row28_col1, #T_ba56d_row28_col2, #T_ba56d_row28_col3, #T_ba56d_row28_col4, #T_ba56d_row29_col0, #T_ba56d_row29_col1, #T_ba56d_row29_col2, #T_ba56d_row29_col3, #T_ba56d_row29_col4, #T_ba56d_row30_col0, #T_ba56d_row30_col1, #T_ba56d_row30_col2, #T_ba56d_row30_col3, #T_ba56d_row30_col4, #T_ba56d_row31_col0, #T_ba56d_row31_col1, #T_ba56d_row31_col2, #T_ba56d_row31_col3, #T_ba56d_row31_col4, #T_ba56d_row32_col0, #T_ba56d_row32_col1, #T_ba56d_row32_col2, #T_ba56d_row32_col3, #T_ba56d_row32_col4, #T_ba56d_row33_col0, #T_ba56d_row33_col1, #T_ba56d_row33_col2, #T_ba56d_row33_col3, #T_ba56d_row33_col4, #T_ba56d_row34_col0, #T_ba56d_row34_col1, #T_ba56d_row34_col2, #T_ba56d_row34_col3, #T_ba56d_row34_col4, #T_ba56d_row35_col0, #T_ba56d_row35_col1, #T_ba56d_row35_col2, #T_ba56d_row35_col3, #T_ba56d_row35_col4, #T_ba56d_row36_col0, #T_ba56d_row36_col1, #T_ba56d_row36_col2, #T_ba56d_row36_col3, #T_ba56d_row36_col4, #T_ba56d_row37_col0, #T_ba56d_row37_col1, #T_ba56d_row37_col2, #T_ba56d_row37_col3, #T_ba56d_row37_col4, #T_ba56d_row38_col0, #T_ba56d_row38_col1, #T_ba56d_row38_col2, #T_ba56d_row38_col3, #T_ba56d_row38_col4, #T_ba56d_row39_col0, #T_ba56d_row39_col1, #T_ba56d_row39_col2, #T_ba56d_row39_col3, #T_ba56d_row39_col4, #T_ba56d_row40_col0, #T_ba56d_row40_col1, #T_ba56d_row40_col2, #T_ba56d_row40_col3, #T_ba56d_row40_col4, #T_ba56d_row41_col0, #T_ba56d_row41_col1, #T_ba56d_row41_col2, #T_ba56d_row41_col3, #T_ba56d_row41_col4, #T_ba56d_row42_col0, #T_ba56d_row42_col1, #T_ba56d_row42_col2, #T_ba56d_row42_col3, #T_ba56d_row42_col4, #T_ba56d_row43_col0, #T_ba56d_row43_col1, #T_ba56d_row43_col2, #T_ba56d_row43_col3, #T_ba56d_row43_col4, #T_ba56d_row44_col0, #T_ba56d_row44_col1, #T_ba56d_row44_col2, #T_ba56d_row44_col3, #T_ba56d_row44_col4, #T_ba56d_row45_col0, #T_ba56d_row45_col1, #T_ba56d_row45_col2, #T_ba56d_row45_col3, #T_ba56d_row45_col4, #T_ba56d_row46_col0, #T_ba56d_row46_col1, #T_ba56d_row46_col2, #T_ba56d_row46_col3, #T_ba56d_row46_col4, #T_ba56d_row47_col0, #T_ba56d_row47_col1, #T_ba56d_row47_col2, #T_ba56d_row47_col3, #T_ba56d_row47_col4, #T_ba56d_row48_col0, #T_ba56d_row48_col1, #T_ba56d_row48_col2, #T_ba56d_row48_col3, #T_ba56d_row48_col4, #T_ba56d_row49_col0, #T_ba56d_row49_col1, #T_ba56d_row49_col2, #T_ba56d_row49_col3, #T_ba56d_row49_col4, #T_ba56d_row50_col0, #T_ba56d_row50_col1, #T_ba56d_row50_col2, #T_ba56d_row50_col3, #T_ba56d_row50_col4, #T_ba56d_row51_col0, #T_ba56d_row51_col1, #T_ba56d_row51_col2, #T_ba56d_row51_col3, #T_ba56d_row51_col4, #T_ba56d_row52_col0, #T_ba56d_row52_col1, #T_ba56d_row52_col2, #T_ba56d_row52_col3, #T_ba56d_row52_col4, #T_ba56d_row53_col0, #T_ba56d_row53_col1, #T_ba56d_row53_col2, #T_ba56d_row53_col3, #T_ba56d_row53_col4, #T_ba56d_row54_col0, #T_ba56d_row54_col1, #T_ba56d_row54_col2, #T_ba56d_row54_col3, #T_ba56d_row54_col4, #T_ba56d_row55_col0, #T_ba56d_row55_col1, #T_ba56d_row55_col2, #T_ba56d_row55_col3, #T_ba56d_row55_col4, #T_ba56d_row56_col0, #T_ba56d_row56_col1, #T_ba56d_row56_col2, #T_ba56d_row56_col3, #T_ba56d_row56_col4, #T_ba56d_row57_col0, #T_ba56d_row57_col1, #T_ba56d_row57_col2, #T_ba56d_row57_col3, #T_ba56d_row57_col4, #T_ba56d_row58_col0, #T_ba56d_row58_col1, #T_ba56d_row58_col2, #T_ba56d_row58_col3, #T_ba56d_row58_col4, #T_ba56d_row59_col0, #T_ba56d_row59_col1, #T_ba56d_row59_col2, #T_ba56d_row59_col3, #T_ba56d_row59_col4, #T_ba56d_row60_col0, #T_ba56d_row60_col1, #T_ba56d_row60_col2, #T_ba56d_row60_col3, #T_ba56d_row60_col4, #T_ba56d_row61_col0, #T_ba56d_row61_col1, #T_ba56d_row61_col2, #T_ba56d_row61_col3, #T_ba56d_row61_col4, #T_ba56d_row62_col0, #T_ba56d_row62_col1, #T_ba56d_row62_col2, #T_ba56d_row62_col3, #T_ba56d_row62_col4 {
  text-align: right;
}
</style>
<table id="T_ba56d">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_ba56d_level0_col0" class="col_heading level0 col0" >Normal</th>
      <th id="T_ba56d_level0_col1" class="col_heading level0 col1" >Snow</th>
      <th id="T_ba56d_level0_col2" class="col_heading level0 col2" >Event</th>
      <th id="T_ba56d_level0_col3" class="col_heading level0 col3" >Rush</th>
      <th id="T_ba56d_level0_col4" class="col_heading level0 col4" >Spätnacht</th>
    </tr>
    <tr>
      <th class="index_name level0" >Stop</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_ba56d_level0_row0" class="row_heading level0 row0" >Glattpark</th>
      <td id="T_ba56d_row0_col0" class="data row0 col0" >nan</td>
      <td id="T_ba56d_row0_col1" class="data row0 col1" >124.20</td>
      <td id="T_ba56d_row0_col2" class="data row0 col2" >84.10</td>
      <td id="T_ba56d_row0_col3" class="data row0 col3" >91.00</td>
      <td id="T_ba56d_row0_col4" class="data row0 col4" >85.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row1" class="row_heading level0 row1" >Bad Allenmoos</th>
      <td id="T_ba56d_row1_col0" class="data row1 col0" >nan</td>
      <td id="T_ba56d_row1_col1" class="data row1 col1" >121.90</td>
      <td id="T_ba56d_row1_col2" class="data row1 col2" >77.40</td>
      <td id="T_ba56d_row1_col3" class="data row1 col3" >84.20</td>
      <td id="T_ba56d_row1_col4" class="data row1 col4" >78.20</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row2" class="row_heading level0 row2" >Bahnhof Enge/Bederstr.</th>
      <td id="T_ba56d_row2_col0" class="data row2 col0" >nan</td>
      <td id="T_ba56d_row2_col1" class="data row2 col1" >nan</td>
      <td id="T_ba56d_row2_col2" class="data row2 col2" >55.50</td>
      <td id="T_ba56d_row2_col3" class="data row2 col3" >nan</td>
      <td id="T_ba56d_row2_col4" class="data row2 col4" >55.60</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row3" class="row_heading level0 row3" >Bahnhof Oerlikon</th>
      <td id="T_ba56d_row3_col0" class="data row3 col0" >nan</td>
      <td id="T_ba56d_row3_col1" class="data row3 col1" >136.90</td>
      <td id="T_ba56d_row3_col2" class="data row3 col2" >89.80</td>
      <td id="T_ba56d_row3_col3" class="data row3 col3" >73.10</td>
      <td id="T_ba56d_row3_col4" class="data row3 col4" >107.30</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row4" class="row_heading level0 row4" >Bahnhof Stadelhofen</th>
      <td id="T_ba56d_row4_col0" class="data row4 col0" >nan</td>
      <td id="T_ba56d_row4_col1" class="data row4 col1" >105.70</td>
      <td id="T_ba56d_row4_col2" class="data row4 col2" >57.90</td>
      <td id="T_ba56d_row4_col3" class="data row4 col3" >59.90</td>
      <td id="T_ba56d_row4_col4" class="data row4 col4" >69.90</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row5" class="row_heading level0 row5" >Bahnhofquai/HB</th>
      <td id="T_ba56d_row5_col0" class="data row5 col0" >nan</td>
      <td id="T_ba56d_row5_col1" class="data row5 col1" >92.80</td>
      <td id="T_ba56d_row5_col2" class="data row5 col2" >53.70</td>
      <td id="T_ba56d_row5_col3" class="data row5 col3" >57.10</td>
      <td id="T_ba56d_row5_col4" class="data row5 col4" >42.60</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row6" class="row_heading level0 row6" >Bahnhofstrasse/HB</th>
      <td id="T_ba56d_row6_col0" class="data row6 col0" >nan</td>
      <td id="T_ba56d_row6_col1" class="data row6 col1" >104.90</td>
      <td id="T_ba56d_row6_col2" class="data row6 col2" >62.70</td>
      <td id="T_ba56d_row6_col3" class="data row6 col3" >59.40</td>
      <td id="T_ba56d_row6_col4" class="data row6 col4" >67.40</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row7" class="row_heading level0 row7" >Balgrist</th>
      <td id="T_ba56d_row7_col0" class="data row7 col0" >nan</td>
      <td id="T_ba56d_row7_col1" class="data row7 col1" >124.80</td>
      <td id="T_ba56d_row7_col2" class="data row7 col2" >81.30</td>
      <td id="T_ba56d_row7_col3" class="data row7 col3" >87.60</td>
      <td id="T_ba56d_row7_col4" class="data row7 col4" >92.00</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row8" class="row_heading level0 row8" >Beckenhof</th>
      <td id="T_ba56d_row8_col0" class="data row8 col0" >nan</td>
      <td id="T_ba56d_row8_col1" class="data row8 col1" >99.40</td>
      <td id="T_ba56d_row8_col2" class="data row8 col2" >67.10</td>
      <td id="T_ba56d_row8_col3" class="data row8 col3" >72.60</td>
      <td id="T_ba56d_row8_col4" class="data row8 col4" >68.60</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row9" class="row_heading level0 row9" >Bellevue</th>
      <td id="T_ba56d_row9_col0" class="data row9 col0" >nan</td>
      <td id="T_ba56d_row9_col1" class="data row9 col1" >106.30</td>
      <td id="T_ba56d_row9_col2" class="data row9 col2" >59.40</td>
      <td id="T_ba56d_row9_col3" class="data row9 col3" >55.60</td>
      <td id="T_ba56d_row9_col4" class="data row9 col4" >71.00</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row10" class="row_heading level0 row10" >Brunnenhof</th>
      <td id="T_ba56d_row10_col0" class="data row10 col0" >nan</td>
      <td id="T_ba56d_row10_col1" class="data row10 col1" >112.90</td>
      <td id="T_ba56d_row10_col2" class="data row10 col2" >70.20</td>
      <td id="T_ba56d_row10_col3" class="data row10 col3" >65.70</td>
      <td id="T_ba56d_row10_col4" class="data row10 col4" >74.80</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row11" class="row_heading level0 row11" >Bucheggplatz D</th>
      <td id="T_ba56d_row11_col0" class="data row11 col0" >nan</td>
      <td id="T_ba56d_row11_col1" class="data row11 col1" >109.10</td>
      <td id="T_ba56d_row11_col2" class="data row11 col2" >64.70</td>
      <td id="T_ba56d_row11_col3" class="data row11 col3" >70.20</td>
      <td id="T_ba56d_row11_col4" class="data row11 col4" >64.90</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row12" class="row_heading level0 row12" >Burgwies</th>
      <td id="T_ba56d_row12_col0" class="data row12 col0" >nan</td>
      <td id="T_ba56d_row12_col1" class="data row12 col1" >120.60</td>
      <td id="T_ba56d_row12_col2" class="data row12 col2" >81.30</td>
      <td id="T_ba56d_row12_col3" class="data row12 col3" >78.70</td>
      <td id="T_ba56d_row12_col4" class="data row12 col4" >97.10</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row13" class="row_heading level0 row13" >Bürkliplatz</th>
      <td id="T_ba56d_row13_col0" class="data row13 col0" >nan</td>
      <td id="T_ba56d_row13_col1" class="data row13 col1" >100.20</td>
      <td id="T_ba56d_row13_col2" class="data row13 col2" >60.90</td>
      <td id="T_ba56d_row13_col3" class="data row13 col3" >52.40</td>
      <td id="T_ba56d_row13_col4" class="data row13 col4" >74.90</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row14" class="row_heading level0 row14" >Central</th>
      <td id="T_ba56d_row14_col0" class="data row14 col0" >nan</td>
      <td id="T_ba56d_row14_col1" class="data row14 col1" >nan</td>
      <td id="T_ba56d_row14_col2" class="data row14 col2" >46.10</td>
      <td id="T_ba56d_row14_col3" class="data row14 col3" >64.30</td>
      <td id="T_ba56d_row14_col4" class="data row14 col4" >46.80</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row15" class="row_heading level0 row15" >Feldeggstrasse</th>
      <td id="T_ba56d_row15_col0" class="data row15 col0" >nan</td>
      <td id="T_ba56d_row15_col1" class="data row15 col1" >nan</td>
      <td id="T_ba56d_row15_col2" class="data row15 col2" >70.30</td>
      <td id="T_ba56d_row15_col3" class="data row15 col3" >nan</td>
      <td id="T_ba56d_row15_col4" class="data row15 col4" >66.70</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row16" class="row_heading level0 row16" >Fernsehstudio</th>
      <td id="T_ba56d_row16_col0" class="data row16 col0" >nan</td>
      <td id="T_ba56d_row16_col1" class="data row16 col1" >181.40</td>
      <td id="T_ba56d_row16_col2" class="data row16 col2" >119.60</td>
      <td id="T_ba56d_row16_col3" class="data row16 col3" >135.80</td>
      <td id="T_ba56d_row16_col4" class="data row16 col4" >110.80</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row17" class="row_heading level0 row17" >Friedhof Enzenbühl</th>
      <td id="T_ba56d_row17_col0" class="data row17 col0" >nan</td>
      <td id="T_ba56d_row17_col1" class="data row17 col1" >199.70</td>
      <td id="T_ba56d_row17_col2" class="data row17 col2" >128.80</td>
      <td id="T_ba56d_row17_col3" class="data row17 col3" >120.10</td>
      <td id="T_ba56d_row17_col4" class="data row17 col4" >169.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row18" class="row_heading level0 row18" >Fröhlichstrasse</th>
      <td id="T_ba56d_row18_col0" class="data row18 col0" >nan</td>
      <td id="T_ba56d_row18_col1" class="data row18 col1" >nan</td>
      <td id="T_ba56d_row18_col2" class="data row18 col2" >68.10</td>
      <td id="T_ba56d_row18_col3" class="data row18 col3" >nan</td>
      <td id="T_ba56d_row18_col4" class="data row18 col4" >68.60</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row19" class="row_heading level0 row19" >Guggachstrasse</th>
      <td id="T_ba56d_row19_col0" class="data row19 col0" >nan</td>
      <td id="T_ba56d_row19_col1" class="data row19 col1" >nan</td>
      <td id="T_ba56d_row19_col2" class="data row19 col2" >73.40</td>
      <td id="T_ba56d_row19_col3" class="data row19 col3" >nan</td>
      <td id="T_ba56d_row19_col4" class="data row19 col4" >nan</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row20" class="row_heading level0 row20" >Haldenegg</th>
      <td id="T_ba56d_row20_col0" class="data row20 col0" >nan</td>
      <td id="T_ba56d_row20_col1" class="data row20 col1" >nan</td>
      <td id="T_ba56d_row20_col2" class="data row20 col2" >36.20</td>
      <td id="T_ba56d_row20_col3" class="data row20 col3" >39.70</td>
      <td id="T_ba56d_row20_col4" class="data row20 col4" >49.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row21" class="row_heading level0 row21" >Hedwigsteig</th>
      <td id="T_ba56d_row21_col0" class="data row21 col0" >nan</td>
      <td id="T_ba56d_row21_col1" class="data row21 col1" >113.60</td>
      <td id="T_ba56d_row21_col2" class="data row21 col2" >75.90</td>
      <td id="T_ba56d_row21_col3" class="data row21 col3" >71.50</td>
      <td id="T_ba56d_row21_col4" class="data row21 col4" >91.20</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row22" class="row_heading level0 row22" >Hegibachplatz B</th>
      <td id="T_ba56d_row22_col0" class="data row22 col0" >nan</td>
      <td id="T_ba56d_row22_col1" class="data row22 col1" >103.50</td>
      <td id="T_ba56d_row22_col2" class="data row22 col2" >60.70</td>
      <td id="T_ba56d_row22_col3" class="data row22 col3" >69.60</td>
      <td id="T_ba56d_row22_col4" class="data row22 col4" >63.40</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row23" class="row_heading level0 row23" >Helmhaus</th>
      <td id="T_ba56d_row23_col0" class="data row23 col0" >nan</td>
      <td id="T_ba56d_row23_col1" class="data row23 col1" >nan</td>
      <td id="T_ba56d_row23_col2" class="data row23 col2" >38.60</td>
      <td id="T_ba56d_row23_col3" class="data row23 col3" >53.90</td>
      <td id="T_ba56d_row23_col4" class="data row23 col4" >40.00</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row24" class="row_heading level0 row24" >Hottingerplatz</th>
      <td id="T_ba56d_row24_col0" class="data row24 col0" >nan</td>
      <td id="T_ba56d_row24_col1" class="data row24 col1" >nan</td>
      <td id="T_ba56d_row24_col2" class="data row24 col2" >63.90</td>
      <td id="T_ba56d_row24_col3" class="data row24 col3" >nan</td>
      <td id="T_ba56d_row24_col4" class="data row24 col4" >49.40</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row25" class="row_heading level0 row25" >Hölderlinstrasse</th>
      <td id="T_ba56d_row25_col0" class="data row25 col0" >nan</td>
      <td id="T_ba56d_row25_col1" class="data row25 col1" >nan</td>
      <td id="T_ba56d_row25_col2" class="data row25 col2" >119.90</td>
      <td id="T_ba56d_row25_col3" class="data row25 col3" >nan</td>
      <td id="T_ba56d_row25_col4" class="data row25 col4" >nan</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row26" class="row_heading level0 row26" >Höschgasse</th>
      <td id="T_ba56d_row26_col0" class="data row26 col0" >nan</td>
      <td id="T_ba56d_row26_col1" class="data row26 col1" >nan</td>
      <td id="T_ba56d_row26_col2" class="data row26 col2" >71.20</td>
      <td id="T_ba56d_row26_col3" class="data row26 col3" >nan</td>
      <td id="T_ba56d_row26_col4" class="data row26 col4" >68.60</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row27" class="row_heading level0 row27" >Kantonalbank</th>
      <td id="T_ba56d_row27_col0" class="data row27 col0" >nan</td>
      <td id="T_ba56d_row27_col1" class="data row27 col1" >96.70</td>
      <td id="T_ba56d_row27_col2" class="data row27 col2" >55.30</td>
      <td id="T_ba56d_row27_col3" class="data row27 col3" >43.00</td>
      <td id="T_ba56d_row27_col4" class="data row27 col4" >69.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row28" class="row_heading level0 row28" >Kreuzplatz</th>
      <td id="T_ba56d_row28_col0" class="data row28 col0" >nan</td>
      <td id="T_ba56d_row28_col1" class="data row28 col1" >104.10</td>
      <td id="T_ba56d_row28_col2" class="data row28 col2" >60.50</td>
      <td id="T_ba56d_row28_col3" class="data row28 col3" >63.80</td>
      <td id="T_ba56d_row28_col4" class="data row28 col4" >68.20</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row29" class="row_heading level0 row29" >Kreuzstrasse</th>
      <td id="T_ba56d_row29_col0" class="data row29 col0" >nan</td>
      <td id="T_ba56d_row29_col1" class="data row29 col1" >nan</td>
      <td id="T_ba56d_row29_col2" class="data row29 col2" >75.90</td>
      <td id="T_ba56d_row29_col3" class="data row29 col3" >nan</td>
      <td id="T_ba56d_row29_col4" class="data row29 col4" >66.80</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row30" class="row_heading level0 row30" >Kronenstrasse</th>
      <td id="T_ba56d_row30_col0" class="data row30 col0" >nan</td>
      <td id="T_ba56d_row30_col1" class="data row30 col1" >103.60</td>
      <td id="T_ba56d_row30_col2" class="data row30 col2" >69.50</td>
      <td id="T_ba56d_row30_col3" class="data row30 col3" >67.90</td>
      <td id="T_ba56d_row30_col4" class="data row30 col4" >67.30</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row31" class="row_heading level0 row31" >Kunsthaus</th>
      <td id="T_ba56d_row31_col0" class="data row31 col0" >nan</td>
      <td id="T_ba56d_row31_col1" class="data row31 col1" >nan</td>
      <td id="T_ba56d_row31_col2" class="data row31 col2" >65.40</td>
      <td id="T_ba56d_row31_col3" class="data row31 col3" >nan</td>
      <td id="T_ba56d_row31_col4" class="data row31 col4" >50.90</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row32" class="row_heading level0 row32" >Laubegg</th>
      <td id="T_ba56d_row32_col0" class="data row32 col0" >nan</td>
      <td id="T_ba56d_row32_col1" class="data row32 col1" >nan</td>
      <td id="T_ba56d_row32_col2" class="data row32 col2" >61.90</td>
      <td id="T_ba56d_row32_col3" class="data row32 col3" >nan</td>
      <td id="T_ba56d_row32_col4" class="data row32 col4" >68.20</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row33" class="row_heading level0 row33" >Laubiweg</th>
      <td id="T_ba56d_row33_col0" class="data row33 col0" >nan</td>
      <td id="T_ba56d_row33_col1" class="data row33 col1" >111.20</td>
      <td id="T_ba56d_row33_col2" class="data row33 col2" >63.70</td>
      <td id="T_ba56d_row33_col3" class="data row33 col3" >62.30</td>
      <td id="T_ba56d_row33_col4" class="data row33 col4" >67.10</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row34" class="row_heading level0 row34" >Leutschenbach</th>
      <td id="T_ba56d_row34_col0" class="data row34 col0" >nan</td>
      <td id="T_ba56d_row34_col1" class="data row34 col1" >144.90</td>
      <td id="T_ba56d_row34_col2" class="data row34 col2" >101.70</td>
      <td id="T_ba56d_row34_col3" class="data row34 col3" >98.70</td>
      <td id="T_ba56d_row34_col4" class="data row34 col4" >111.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row35" class="row_heading level0 row35" >Messe/Hallenstadion</th>
      <td id="T_ba56d_row35_col0" class="data row35 col0" >nan</td>
      <td id="T_ba56d_row35_col1" class="data row35 col1" >131.10</td>
      <td id="T_ba56d_row35_col2" class="data row35 col2" >81.40</td>
      <td id="T_ba56d_row35_col3" class="data row35 col3" >86.10</td>
      <td id="T_ba56d_row35_col4" class="data row35 col4" >83.30</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row36" class="row_heading level0 row36" >Oerlikerhus</th>
      <td id="T_ba56d_row36_col0" class="data row36 col0" >nan</td>
      <td id="T_ba56d_row36_col1" class="data row36 col1" >122.80</td>
      <td id="T_ba56d_row36_col2" class="data row36 col2" >81.60</td>
      <td id="T_ba56d_row36_col3" class="data row36 col3" >91.20</td>
      <td id="T_ba56d_row36_col4" class="data row36 col4" >81.80</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row37" class="row_heading level0 row37" >Opernhaus</th>
      <td id="T_ba56d_row37_col0" class="data row37 col0" >nan</td>
      <td id="T_ba56d_row37_col1" class="data row37 col1" >nan</td>
      <td id="T_ba56d_row37_col2" class="data row37 col2" >86.70</td>
      <td id="T_ba56d_row37_col3" class="data row37 col3" >nan</td>
      <td id="T_ba56d_row37_col4" class="data row37 col4" >77.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row38" class="row_heading level0 row38" >Ottikerstrasse</th>
      <td id="T_ba56d_row38_col0" class="data row38 col0" >nan</td>
      <td id="T_ba56d_row38_col1" class="data row38 col1" >nan</td>
      <td id="T_ba56d_row38_col2" class="data row38 col2" >28.90</td>
      <td id="T_ba56d_row38_col3" class="data row38 col3" >22.60</td>
      <td id="T_ba56d_row38_col4" class="data row38 col4" >44.30</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row39" class="row_heading level0 row39" >Paradeplatz</th>
      <td id="T_ba56d_row39_col0" class="data row39 col0" >nan</td>
      <td id="T_ba56d_row39_col1" class="data row39 col1" >95.70</td>
      <td id="T_ba56d_row39_col2" class="data row39 col2" >55.60</td>
      <td id="T_ba56d_row39_col3" class="data row39 col3" >46.60</td>
      <td id="T_ba56d_row39_col4" class="data row39 col4" >65.60</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row40" class="row_heading level0 row40" >Rathaus</th>
      <td id="T_ba56d_row40_col0" class="data row40 col0" >nan</td>
      <td id="T_ba56d_row40_col1" class="data row40 col1" >nan</td>
      <td id="T_ba56d_row40_col2" class="data row40 col2" >38.40</td>
      <td id="T_ba56d_row40_col3" class="data row40 col3" >50.40</td>
      <td id="T_ba56d_row40_col4" class="data row40 col4" >39.00</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row41" class="row_heading level0 row41" >Regensbergbrücke</th>
      <td id="T_ba56d_row41_col0" class="data row41 col0" >nan</td>
      <td id="T_ba56d_row41_col1" class="data row41 col1" >122.50</td>
      <td id="T_ba56d_row41_col2" class="data row41 col2" >80.00</td>
      <td id="T_ba56d_row41_col3" class="data row41 col3" >86.00</td>
      <td id="T_ba56d_row41_col4" class="data row41 col4" >81.20</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row42" class="row_heading level0 row42" >Rennweg</th>
      <td id="T_ba56d_row42_col0" class="data row42 col0" >nan</td>
      <td id="T_ba56d_row42_col1" class="data row42 col1" >93.70</td>
      <td id="T_ba56d_row42_col2" class="data row42 col2" >53.20</td>
      <td id="T_ba56d_row42_col3" class="data row42 col3" >40.70</td>
      <td id="T_ba56d_row42_col4" class="data row42 col4" >66.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row43" class="row_heading level0 row43" >Rudolf-Brun-Brücke</th>
      <td id="T_ba56d_row43_col0" class="data row43 col0" >nan</td>
      <td id="T_ba56d_row43_col1" class="data row43 col1" >nan</td>
      <td id="T_ba56d_row43_col2" class="data row43 col2" >38.30</td>
      <td id="T_ba56d_row43_col3" class="data row43 col3" >53.10</td>
      <td id="T_ba56d_row43_col4" class="data row43 col4" >39.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row44" class="row_heading level0 row44" >Römerhof</th>
      <td id="T_ba56d_row44_col0" class="data row44 col0" >nan</td>
      <td id="T_ba56d_row44_col1" class="data row44 col1" >nan</td>
      <td id="T_ba56d_row44_col2" class="data row44 col2" >78.30</td>
      <td id="T_ba56d_row44_col3" class="data row44 col3" >nan</td>
      <td id="T_ba56d_row44_col4" class="data row44 col4" >71.60</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row45" class="row_heading level0 row45" >Röslistrasse</th>
      <td id="T_ba56d_row45_col0" class="data row45 col0" >nan</td>
      <td id="T_ba56d_row45_col1" class="data row45 col1" >nan</td>
      <td id="T_ba56d_row45_col2" class="data row45 col2" >35.80</td>
      <td id="T_ba56d_row45_col3" class="data row45 col3" >25.30</td>
      <td id="T_ba56d_row45_col4" class="data row45 col4" >45.90</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row46" class="row_heading level0 row46" >Saalsporthalle</th>
      <td id="T_ba56d_row46_col0" class="data row46 col0" >nan</td>
      <td id="T_ba56d_row46_col1" class="data row46 col1" >nan</td>
      <td id="T_ba56d_row46_col2" class="data row46 col2" >60.40</td>
      <td id="T_ba56d_row46_col3" class="data row46 col3" >nan</td>
      <td id="T_ba56d_row46_col4" class="data row46 col4" >65.70</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row47" class="row_heading level0 row47" >Schaffhauserplatz</th>
      <td id="T_ba56d_row47_col0" class="data row47 col0" >nan</td>
      <td id="T_ba56d_row47_col1" class="data row47 col1" >116.40</td>
      <td id="T_ba56d_row47_col2" class="data row47 col2" >68.80</td>
      <td id="T_ba56d_row47_col3" class="data row47 col3" >67.60</td>
      <td id="T_ba56d_row47_col4" class="data row47 col4" >72.40</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row48" class="row_heading level0 row48" >Signaustrasse</th>
      <td id="T_ba56d_row48_col0" class="data row48 col0" >nan</td>
      <td id="T_ba56d_row48_col1" class="data row48 col1" >105.50</td>
      <td id="T_ba56d_row48_col2" class="data row48 col2" >62.10</td>
      <td id="T_ba56d_row48_col3" class="data row48 col3" >73.60</td>
      <td id="T_ba56d_row48_col4" class="data row48 col4" >65.10</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row49" class="row_heading level0 row49" >Sihlcity Nord</th>
      <td id="T_ba56d_row49_col0" class="data row49 col0" >nan</td>
      <td id="T_ba56d_row49_col1" class="data row49 col1" >nan</td>
      <td id="T_ba56d_row49_col2" class="data row49 col2" >67.20</td>
      <td id="T_ba56d_row49_col3" class="data row49 col3" >nan</td>
      <td id="T_ba56d_row49_col4" class="data row49 col4" >71.80</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row50" class="row_heading level0 row50" >Sihlstrasse</th>
      <td id="T_ba56d_row50_col0" class="data row50 col0" >nan</td>
      <td id="T_ba56d_row50_col1" class="data row50 col1" >nan</td>
      <td id="T_ba56d_row50_col2" class="data row50 col2" >68.80</td>
      <td id="T_ba56d_row50_col3" class="data row50 col3" >nan</td>
      <td id="T_ba56d_row50_col4" class="data row50 col4" >64.40</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row51" class="row_heading level0 row51" >Sonneggstrasse</th>
      <td id="T_ba56d_row51_col0" class="data row51 col0" >nan</td>
      <td id="T_ba56d_row51_col1" class="data row51 col1" >nan</td>
      <td id="T_ba56d_row51_col2" class="data row51 col2" >33.30</td>
      <td id="T_ba56d_row51_col3" class="data row51 col3" >31.90</td>
      <td id="T_ba56d_row51_col4" class="data row51 col4" >47.30</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row52" class="row_heading level0 row52" >Stampfenbachplatz</th>
      <td id="T_ba56d_row52_col0" class="data row52 col0" >nan</td>
      <td id="T_ba56d_row52_col1" class="data row52 col1" >93.00</td>
      <td id="T_ba56d_row52_col2" class="data row52 col2" >57.30</td>
      <td id="T_ba56d_row52_col3" class="data row52 col3" >68.10</td>
      <td id="T_ba56d_row52_col4" class="data row52 col4" >41.00</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row53" class="row_heading level0 row53" >Stauffacher</th>
      <td id="T_ba56d_row53_col0" class="data row53 col0" >nan</td>
      <td id="T_ba56d_row53_col1" class="data row53 col1" >nan</td>
      <td id="T_ba56d_row53_col2" class="data row53 col2" >67.00</td>
      <td id="T_ba56d_row53_col3" class="data row53 col3" >nan</td>
      <td id="T_ba56d_row53_col4" class="data row53 col4" >64.00</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row54" class="row_heading level0 row54" >Sternen Oerlikon</th>
      <td id="T_ba56d_row54_col0" class="data row54 col0" >nan</td>
      <td id="T_ba56d_row54_col1" class="data row54 col1" >137.90</td>
      <td id="T_ba56d_row54_col2" class="data row54 col2" >86.40</td>
      <td id="T_ba56d_row54_col3" class="data row54 col3" >91.90</td>
      <td id="T_ba56d_row54_col4" class="data row54 col4" >81.30</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row55" class="row_heading level0 row55" >Stockerstrasse</th>
      <td id="T_ba56d_row55_col0" class="data row55 col0" >nan</td>
      <td id="T_ba56d_row55_col1" class="data row55 col1" >nan</td>
      <td id="T_ba56d_row55_col2" class="data row55 col2" >58.90</td>
      <td id="T_ba56d_row55_col3" class="data row55 col3" >nan</td>
      <td id="T_ba56d_row55_col4" class="data row55 col4" >71.40</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row56" class="row_heading level0 row56" >Strassenverkehrsamt</th>
      <td id="T_ba56d_row56_col0" class="data row56 col0" >nan</td>
      <td id="T_ba56d_row56_col1" class="data row56 col1" >nan</td>
      <td id="T_ba56d_row56_col2" class="data row56 col2" >82.10</td>
      <td id="T_ba56d_row56_col3" class="data row56 col3" >nan</td>
      <td id="T_ba56d_row56_col4" class="data row56 col4" >109.50</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row57" class="row_heading level0 row57" >Tunnelstrasse</th>
      <td id="T_ba56d_row57_col0" class="data row57 col0" >nan</td>
      <td id="T_ba56d_row57_col1" class="data row57 col1" >nan</td>
      <td id="T_ba56d_row57_col2" class="data row57 col2" >60.50</td>
      <td id="T_ba56d_row57_col3" class="data row57 col3" >nan</td>
      <td id="T_ba56d_row57_col4" class="data row57 col4" >74.40</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row58" class="row_heading level0 row58" >Uetlihof</th>
      <td id="T_ba56d_row58_col0" class="data row58 col0" >nan</td>
      <td id="T_ba56d_row58_col1" class="data row58 col1" >nan</td>
      <td id="T_ba56d_row58_col2" class="data row58 col2" >64.20</td>
      <td id="T_ba56d_row58_col3" class="data row58 col3" >nan</td>
      <td id="T_ba56d_row58_col4" class="data row58 col4" >78.00</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row59" class="row_heading level0 row59" >Waffenplatzstrasse</th>
      <td id="T_ba56d_row59_col0" class="data row59 col0" >nan</td>
      <td id="T_ba56d_row59_col1" class="data row59 col1" >nan</td>
      <td id="T_ba56d_row59_col2" class="data row59 col2" >58.50</td>
      <td id="T_ba56d_row59_col3" class="data row59 col3" >nan</td>
      <td id="T_ba56d_row59_col4" class="data row59 col4" >57.90</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row60" class="row_heading level0 row60" >Werd</th>
      <td id="T_ba56d_row60_col0" class="data row60 col0" >nan</td>
      <td id="T_ba56d_row60_col1" class="data row60 col1" >nan</td>
      <td id="T_ba56d_row60_col2" class="data row60 col2" >87.30</td>
      <td id="T_ba56d_row60_col3" class="data row60 col3" >nan</td>
      <td id="T_ba56d_row60_col4" class="data row60 col4" >83.70</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row61" class="row_heading level0 row61" >Wetlistrasse</th>
      <td id="T_ba56d_row61_col0" class="data row61 col0" >nan</td>
      <td id="T_ba56d_row61_col1" class="data row61 col1" >121.00</td>
      <td id="T_ba56d_row61_col2" class="data row61 col2" >83.10</td>
      <td id="T_ba56d_row61_col3" class="data row61 col3" >80.80</td>
      <td id="T_ba56d_row61_col4" class="data row61 col4" >98.60</td>
    </tr>
    <tr>
      <th id="T_ba56d_level0_row62" class="row_heading level0 row62" >Wildbachstrasse</th>
      <td id="T_ba56d_row62_col0" class="data row62 col0" >nan</td>
      <td id="T_ba56d_row62_col1" class="data row62 col1" >nan</td>
      <td id="T_ba56d_row62_col2" class="data row62 col2" >121.80</td>
      <td id="T_ba56d_row62_col3" class="data row62 col3" >nan</td>
      <td id="T_ba56d_row62_col4" class="data row62 col4" >110.50</td>
    </tr>
  </tbody>
</table>



## Kaskadenanalyse: Delay-Propagation zwischen Halten

Pearson-Korrelation zwischen Delay(Halt n) und Delay(Halt n+1) innerhalb desselben Trips — misst wie stark sich Verspätung von Halt zu Halt fortpflanzt. Hohe Korrelation = systemischer Kaskadeneffekt.


```python
an.plot_cascade_effect(lf_clean, cfg=cfg, ylim=(0.8, 0.95))
show_df(an.table_cascade_effect(lf_clean))
```


    
![png](03_analysis_4-spatial_files/03_analysis_4-spatial_53_0.png)
    



<style type="text/css">
#T_f9d42 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_f9d42 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_f9d42 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_f9d42 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_f9d42 tr:hover td {
  background-color: #eef3f8;
}
#T_f9d42_row0_col0, #T_f9d42_row0_col2, #T_f9d42_row0_col3, #T_f9d42_row1_col0, #T_f9d42_row1_col2, #T_f9d42_row1_col3, #T_f9d42_row2_col0, #T_f9d42_row2_col2, #T_f9d42_row2_col3, #T_f9d42_row3_col0, #T_f9d42_row3_col2, #T_f9d42_row3_col3, #T_f9d42_row4_col0, #T_f9d42_row4_col2, #T_f9d42_row4_col3, #T_f9d42_row5_col0, #T_f9d42_row5_col2, #T_f9d42_row5_col3, #T_f9d42_row6_col0, #T_f9d42_row6_col2, #T_f9d42_row6_col3, #T_f9d42_row7_col0, #T_f9d42_row7_col2, #T_f9d42_row7_col3, #T_f9d42_row8_col0, #T_f9d42_row8_col2, #T_f9d42_row8_col3, #T_f9d42_row9_col0, #T_f9d42_row9_col2, #T_f9d42_row9_col3, #T_f9d42_row10_col0, #T_f9d42_row10_col2, #T_f9d42_row10_col3, #T_f9d42_row11_col0, #T_f9d42_row11_col2, #T_f9d42_row11_col3, #T_f9d42_row12_col0, #T_f9d42_row12_col2, #T_f9d42_row12_col3, #T_f9d42_row13_col0, #T_f9d42_row13_col2, #T_f9d42_row13_col3, #T_f9d42_row14_col0, #T_f9d42_row14_col2, #T_f9d42_row14_col3 {
  text-align: left;
}
#T_f9d42_row0_col1, #T_f9d42_row1_col1, #T_f9d42_row2_col1, #T_f9d42_row3_col1, #T_f9d42_row4_col1, #T_f9d42_row5_col1, #T_f9d42_row6_col1, #T_f9d42_row7_col1, #T_f9d42_row8_col1, #T_f9d42_row9_col1, #T_f9d42_row10_col1, #T_f9d42_row11_col1, #T_f9d42_row12_col1, #T_f9d42_row13_col1, #T_f9d42_row14_col1 {
  text-align: right;
}
</style>
<table id="T_f9d42">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_f9d42_level0_col0" class="col_heading level0 col0" >Line</th>
      <th id="T_f9d42_level0_col1" class="col_heading level0 col1" >Pearson r</th>
      <th id="T_f9d42_level0_col2" class="col_heading level0 col2" >N Halte</th>
      <th id="T_f9d42_level0_col3" class="col_heading level0 col3" >Stärke</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_f9d42_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_f9d42_row0_col0" class="data row0 col0" >7</td>
      <td id="T_f9d42_row0_col1" class="data row0 col1" >0.92</td>
      <td id="T_f9d42_row0_col2" class="data row0 col2" >7,513,355</td>
      <td id="T_f9d42_row0_col3" class="data row0 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_f9d42_row1_col0" class="data row1 col0" >8</td>
      <td id="T_f9d42_row1_col1" class="data row1 col1" >0.92</td>
      <td id="T_f9d42_row1_col2" class="data row1 col2" >5,673,749</td>
      <td id="T_f9d42_row1_col3" class="data row1 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_f9d42_row2_col0" class="data row2 col0" >2</td>
      <td id="T_f9d42_row2_col1" class="data row2 col1" >0.92</td>
      <td id="T_f9d42_row2_col2" class="data row2 col2" >7,525,896</td>
      <td id="T_f9d42_row2_col3" class="data row2 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_f9d42_row3_col0" class="data row3 col0" >11</td>
      <td id="T_f9d42_row3_col1" class="data row3 col1" >0.92</td>
      <td id="T_f9d42_row3_col2" class="data row3 col2" >8,321,987</td>
      <td id="T_f9d42_row3_col3" class="data row3 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_f9d42_row4_col0" class="data row4 col0" >4</td>
      <td id="T_f9d42_row4_col1" class="data row4 col1" >0.92</td>
      <td id="T_f9d42_row4_col2" class="data row4 col2" >6,218,609</td>
      <td id="T_f9d42_row4_col3" class="data row4 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_f9d42_row5_col0" class="data row5 col0" >9</td>
      <td id="T_f9d42_row5_col1" class="data row5 col1" >0.92</td>
      <td id="T_f9d42_row5_col2" class="data row5 col2" >7,608,608</td>
      <td id="T_f9d42_row5_col3" class="data row5 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_f9d42_row6_col0" class="data row6 col0" >15</td>
      <td id="T_f9d42_row6_col1" class="data row6 col1" >0.92</td>
      <td id="T_f9d42_row6_col2" class="data row6 col2" >1,779,844</td>
      <td id="T_f9d42_row6_col3" class="data row6 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_f9d42_row7_col0" class="data row7 col0" >17</td>
      <td id="T_f9d42_row7_col1" class="data row7 col1" >0.92</td>
      <td id="T_f9d42_row7_col2" class="data row7 col2" >4,088,688</td>
      <td id="T_f9d42_row7_col3" class="data row7 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_f9d42_row8_col0" class="data row8 col0" >10</td>
      <td id="T_f9d42_row8_col1" class="data row8 col1" >0.91</td>
      <td id="T_f9d42_row8_col2" class="data row8 col2" >5,985,346</td>
      <td id="T_f9d42_row8_col3" class="data row8 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_f9d42_row9_col0" class="data row9 col0" >13</td>
      <td id="T_f9d42_row9_col1" class="data row9 col1" >0.91</td>
      <td id="T_f9d42_row9_col2" class="data row9 col2" >7,542,044</td>
      <td id="T_f9d42_row9_col3" class="data row9 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_f9d42_row10_col0" class="data row10 col0" >14</td>
      <td id="T_f9d42_row10_col1" class="data row10 col1" >0.90</td>
      <td id="T_f9d42_row10_col2" class="data row10 col2" >6,406,444</td>
      <td id="T_f9d42_row10_col3" class="data row10 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_f9d42_row11_col0" class="data row11 col0" >3</td>
      <td id="T_f9d42_row11_col1" class="data row11 col1" >0.89</td>
      <td id="T_f9d42_row11_col2" class="data row11 col2" >4,610,392</td>
      <td id="T_f9d42_row11_col3" class="data row11 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_f9d42_row12_col0" class="data row12 col0" >5</td>
      <td id="T_f9d42_row12_col1" class="data row12 col1" >0.88</td>
      <td id="T_f9d42_row12_col2" class="data row12 col2" >2,504,422</td>
      <td id="T_f9d42_row12_col3" class="data row12 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_f9d42_row13_col0" class="data row13 col0" >6</td>
      <td id="T_f9d42_row13_col1" class="data row13 col1" >0.88</td>
      <td id="T_f9d42_row13_col2" class="data row13 col2" >3,088,503</td>
      <td id="T_f9d42_row13_col3" class="data row13 col3" >🔴 Stark</td>
    </tr>
    <tr>
      <th id="T_f9d42_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_f9d42_row14_col0" class="data row14 col0" >12</td>
      <td id="T_f9d42_row14_col1" class="data row14 col1" >0.86</td>
      <td id="T_f9d42_row14_col2" class="data row14 col2" >2,093,389</td>
      <td id="T_f9d42_row14_col3" class="data row14 col3" >🔴 Stark</td>
    </tr>
  </tbody>
</table>



## Key Findings

→ Vollständige Findings-Tabelle mit Impact und Action in [`03_analysis_0-overview.ipynb`](03_analysis_0-overview.ipynb).

`Präsentation`: **hot** = Kernbefund · **story** = gutes Narrativ · **—** = intern/Feature-Engineering

| ID | Finding | Präsentation |
|:---|:---|:---:|
| F-SPAT-01 | Delay-Hotspots sind **nicht** die zentralen Knotenpunkte, sondern periphere Aussenkorridore: Friedhof Enzenbühl 93.8s, Balgrist 85.2s, Leutschenbach 82.7s. Top-2 (Bertastrasse 181.6s, Sihlfeld 167s) haben n=1'307 — Sonder-/Eventlinien, statistisch instabil | **hot** |
| F-SPAT-02 | Terminus-Frühankünfte existieren, verzerren den Netzschnitt aber kaum: lf_all=55.8s vs. lf_clean=56.9s (Δ +1.0s). Frühankünfte sind strukturelles Muster, kein Messfehler | — |
| F-SPAT-03 | Stadtkreis-Delays: Kreis 11 schlechtester (68.3s, OTP 83%), Kreis 12 (66.3s), Kreis 8 (63.7s). Innenstadt Kreis 1=51.3s. Kreis 5 bester (49.9s, OTP 89%). Drei unabhängige Problemmuster: strukturell (K11/K12) ≠ wetter-sensitiv (K10/K5) ≠ event-sensitiv (K9/K4) | **hot** |
| F-SPAT-04 | Alle Linien haben positives Delay-Delta — keine Linie baut Verspätung systematisch ab. Stärkste Akkumulatoren: L10 (+6.5s/Halt), L11 (+6.2s/Halt). L51 grösstes Delta (+20.2s) bei niedrigstem Delay | **story** |
| F-SPAT-05 | `line_name` ist stärkster räumlicher Prädiktor. L11 (68.7s, OTP 82%) ist die kritischste Hauptlinie | — |
| F-SPAT-06 | Starthaltestellen-Proxy findet 0 Kandidaten — keine Verzerrung nachweisbar. n-Threshold-Filter für Low-Volume-Haltestellen empfohlen | — |
| F-SPAT-07 | **Keine Korrelation** Linienanzahl × Delay: 0 Overlap zwischen Top-20 nach Linien und Top-20 nach Delay. Haldenegg (15 Linien, 44.5s) — unter Netzschnitt. Kaskadenrisiko-Hypothese widerlegt | **story** |
| F-SPAT-08 | `dwell_time` = 0s für 71.3% aller Halte — kein Puffer eingebaut. System akkumuliert Verspätung unweigerlich. Andere Netze (London, Berlin) planen 30s–5min Recovery Time. VBZ-Tradeoff: dichter Takt vs. Pufferstabilität | **hot** |
| F-SPAT-09 | **Endstationen-Muster:** L11/L13/L7 zeigen grosse Delay-Bubbles an Start und Ende, kaum in der Mitte. Lange Linien akkumulieren mehr als kurze (L6, L51). Linienlänge als Proxy-Feature für Delay-Risiko prüfen | **story** |
| F-SPAT-10 | **Richtungs-Asymmetrie:** Fahrt Richtung Aussenquartiere akkumuliert mehr Delay als Rückfahrt Richtung Zentrum. `trip_direction` (= letzter Stop) als Feature prüfen | — |
| F-SPAT-11 | Heatmap Linie × Stunde: Abend-Peak (17–19 Uhr) netzweit synchron. L11/L8 hohes Grundniveau ganztags — nicht nur Tagesverkehr. Interaktion `hour × line_name` stärker als beide Features einzeln | — |


