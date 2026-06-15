# Network Analysis — Streckenveränderungen 2023–2025

Das Zürcher Tramnetz ist kein statisches Objekt.
Im Analysezeitraum 2023–2025 gab es mit dem Fahrplanwechsel Dezember 2023 den größten Netzausbau in der Geschichte der VBZ.
Dieses Notebook untersucht **was** sich verändert hat, **wo** und **wann** — und was das für die Pünktlichkeit bedeutet.

**Zentrale Fragen:**
1. Wo haben sich die meisten Änderungen abgespielt? — Haltestellen und Stadtteile
2. Wieviel hat sich verändert? — Quantifizierung pro Linie und gesamt
3. Wann fanden die Änderungen statt? — Zeitachse
4. Hat sich die Lage nach dem Ausbau verbessert oder verschlechtert? — Einlaufzeit neuer Abschnitte
5. Welche Knotenpunkte sind kritische Hotspots? — Kaskaden und Linienüberschneidungen
6. Welche Stadtteile profitieren? — Versorgungsqualität

**Rückschluss für alle weiteren Analysen:** → am Ende dieses Notebooks

## Setup


```python
from zh_tram_flow.notebook import *
import zh_tram_flow.analytics.network as an

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("03_analysis_2-network")

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



    2026-06-11 11:22:54  INFO      project  03_analysis_2-network started


    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload



```python
log("Lade GTFS j23 / j24 / j25 ...")
gtfs, all_lines = an.load_gtfs(PATHS["root"])
success(f"{len(all_lines)} Linien geladen: {all_lines}")

changes = an.build_changes_matrix(gtfs, all_lines)
success(f"Änderungsmatrix: {len(changes)} Linien")
show_df(changes[["line","n_j23","n_j24","n_j25","added_j24","removed_j24","added_j25","removed_j25"]].set_index("line"))


```

    [38;2;52;97;141mLade GTFS j23 / j24 / j25 ...[0m
    [38;2;52;97;141m✓  18 Linien geladen: ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '17', '18', '19', 'E'][0m
    [38;2;52;97;141m✓  Änderungsmatrix: 18 Linien[0m



<style type="text/css">
#T_5c695 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_5c695 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_5c695 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_5c695 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_5c695 tr:hover td {
  background-color: #eef3f8;
}
#T_5c695_row0_col0, #T_5c695_row0_col1, #T_5c695_row0_col2, #T_5c695_row0_col3, #T_5c695_row0_col4, #T_5c695_row0_col5, #T_5c695_row0_col6, #T_5c695_row1_col0, #T_5c695_row1_col1, #T_5c695_row1_col2, #T_5c695_row1_col3, #T_5c695_row1_col4, #T_5c695_row1_col5, #T_5c695_row1_col6, #T_5c695_row2_col0, #T_5c695_row2_col1, #T_5c695_row2_col2, #T_5c695_row2_col3, #T_5c695_row2_col4, #T_5c695_row2_col5, #T_5c695_row2_col6, #T_5c695_row3_col0, #T_5c695_row3_col1, #T_5c695_row3_col2, #T_5c695_row3_col3, #T_5c695_row3_col4, #T_5c695_row3_col5, #T_5c695_row3_col6, #T_5c695_row4_col0, #T_5c695_row4_col1, #T_5c695_row4_col2, #T_5c695_row4_col3, #T_5c695_row4_col4, #T_5c695_row4_col5, #T_5c695_row4_col6, #T_5c695_row5_col0, #T_5c695_row5_col1, #T_5c695_row5_col2, #T_5c695_row5_col3, #T_5c695_row5_col4, #T_5c695_row5_col5, #T_5c695_row5_col6, #T_5c695_row6_col0, #T_5c695_row6_col1, #T_5c695_row6_col2, #T_5c695_row6_col3, #T_5c695_row6_col4, #T_5c695_row6_col5, #T_5c695_row6_col6, #T_5c695_row7_col0, #T_5c695_row7_col1, #T_5c695_row7_col2, #T_5c695_row7_col3, #T_5c695_row7_col4, #T_5c695_row7_col5, #T_5c695_row7_col6, #T_5c695_row8_col0, #T_5c695_row8_col1, #T_5c695_row8_col2, #T_5c695_row8_col3, #T_5c695_row8_col4, #T_5c695_row8_col5, #T_5c695_row8_col6, #T_5c695_row9_col0, #T_5c695_row9_col1, #T_5c695_row9_col2, #T_5c695_row9_col3, #T_5c695_row9_col4, #T_5c695_row9_col5, #T_5c695_row9_col6, #T_5c695_row10_col0, #T_5c695_row10_col1, #T_5c695_row10_col2, #T_5c695_row10_col3, #T_5c695_row10_col4, #T_5c695_row10_col5, #T_5c695_row10_col6, #T_5c695_row11_col0, #T_5c695_row11_col1, #T_5c695_row11_col2, #T_5c695_row11_col3, #T_5c695_row11_col4, #T_5c695_row11_col5, #T_5c695_row11_col6, #T_5c695_row12_col0, #T_5c695_row12_col1, #T_5c695_row12_col2, #T_5c695_row12_col3, #T_5c695_row12_col4, #T_5c695_row12_col5, #T_5c695_row12_col6, #T_5c695_row13_col0, #T_5c695_row13_col1, #T_5c695_row13_col2, #T_5c695_row13_col3, #T_5c695_row13_col4, #T_5c695_row13_col5, #T_5c695_row13_col6, #T_5c695_row14_col0, #T_5c695_row14_col1, #T_5c695_row14_col2, #T_5c695_row14_col3, #T_5c695_row14_col4, #T_5c695_row14_col5, #T_5c695_row14_col6, #T_5c695_row15_col0, #T_5c695_row15_col1, #T_5c695_row15_col2, #T_5c695_row15_col3, #T_5c695_row15_col4, #T_5c695_row15_col5, #T_5c695_row15_col6, #T_5c695_row16_col0, #T_5c695_row16_col1, #T_5c695_row16_col2, #T_5c695_row16_col3, #T_5c695_row16_col4, #T_5c695_row16_col5, #T_5c695_row16_col6, #T_5c695_row17_col0, #T_5c695_row17_col1, #T_5c695_row17_col2, #T_5c695_row17_col3, #T_5c695_row17_col4, #T_5c695_row17_col5, #T_5c695_row17_col6 {
  text-align: right;
}
</style>
<table id="T_5c695">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_5c695_level0_col0" class="col_heading level0 col0" >n_j23</th>
      <th id="T_5c695_level0_col1" class="col_heading level0 col1" >n_j24</th>
      <th id="T_5c695_level0_col2" class="col_heading level0 col2" >n_j25</th>
      <th id="T_5c695_level0_col3" class="col_heading level0 col3" >added_j24</th>
      <th id="T_5c695_level0_col4" class="col_heading level0 col4" >removed_j24</th>
      <th id="T_5c695_level0_col5" class="col_heading level0 col5" >added_j25</th>
      <th id="T_5c695_level0_col6" class="col_heading level0 col6" >removed_j25</th>
    </tr>
    <tr>
      <th class="index_name level0" >line</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
      <th class="blank col5" >&nbsp;</th>
      <th class="blank col6" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_5c695_level0_row0" class="row_heading level0 row0" >2</th>
      <td id="T_5c695_row0_col0" class="data row0 col0" >31</td>
      <td id="T_5c695_row0_col1" class="data row0 col1" >21</td>
      <td id="T_5c695_row0_col2" class="data row0 col2" >31</td>
      <td id="T_5c695_row0_col3" class="data row0 col3" >1</td>
      <td id="T_5c695_row0_col4" class="data row0 col4" >11</td>
      <td id="T_5c695_row0_col5" class="data row0 col5" >10</td>
      <td id="T_5c695_row0_col6" class="data row0 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row1" class="row_heading level0 row1" >3</th>
      <td id="T_5c695_row1_col0" class="data row1 col0" >21</td>
      <td id="T_5c695_row1_col1" class="data row1 col1" >21</td>
      <td id="T_5c695_row1_col2" class="data row1 col2" >21</td>
      <td id="T_5c695_row1_col3" class="data row1 col3" >2</td>
      <td id="T_5c695_row1_col4" class="data row1 col4" >2</td>
      <td id="T_5c695_row1_col5" class="data row1 col5" >0</td>
      <td id="T_5c695_row1_col6" class="data row1 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row2" class="row_heading level0 row2" >4</th>
      <td id="T_5c695_row2_col0" class="data row2 col0" >26</td>
      <td id="T_5c695_row2_col1" class="data row2 col1" >26</td>
      <td id="T_5c695_row2_col2" class="data row2 col2" >26</td>
      <td id="T_5c695_row2_col3" class="data row2 col3" >1</td>
      <td id="T_5c695_row2_col4" class="data row2 col4" >1</td>
      <td id="T_5c695_row2_col5" class="data row2 col5" >1</td>
      <td id="T_5c695_row2_col6" class="data row2 col6" >1</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row3" class="row_heading level0 row3" >5</th>
      <td id="T_5c695_row3_col0" class="data row3 col0" >9</td>
      <td id="T_5c695_row3_col1" class="data row3 col1" >9</td>
      <td id="T_5c695_row3_col2" class="data row3 col2" >14</td>
      <td id="T_5c695_row3_col3" class="data row3 col3" >0</td>
      <td id="T_5c695_row3_col4" class="data row3 col4" >0</td>
      <td id="T_5c695_row3_col5" class="data row3 col5" >6</td>
      <td id="T_5c695_row3_col6" class="data row3 col6" >1</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row4" class="row_heading level0 row4" >6</th>
      <td id="T_5c695_row4_col0" class="data row4 col0" >24</td>
      <td id="T_5c695_row4_col1" class="data row4 col1" >16</td>
      <td id="T_5c695_row4_col2" class="data row4 col2" >16</td>
      <td id="T_5c695_row4_col3" class="data row4 col3" >6</td>
      <td id="T_5c695_row4_col4" class="data row4 col4" >14</td>
      <td id="T_5c695_row4_col5" class="data row4 col5" >0</td>
      <td id="T_5c695_row4_col6" class="data row4 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row5" class="row_heading level0 row5" >7</th>
      <td id="T_5c695_row5_col0" class="data row5 col0" >31</td>
      <td id="T_5c695_row5_col1" class="data row5 col1" >31</td>
      <td id="T_5c695_row5_col2" class="data row5 col2" >31</td>
      <td id="T_5c695_row5_col3" class="data row5 col3" >2</td>
      <td id="T_5c695_row5_col4" class="data row5 col4" >2</td>
      <td id="T_5c695_row5_col5" class="data row5 col5" >0</td>
      <td id="T_5c695_row5_col6" class="data row5 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row6" class="row_heading level0 row6" >8</th>
      <td id="T_5c695_row6_col0" class="data row6 col0" >23</td>
      <td id="T_5c695_row6_col1" class="data row6 col1" >24</td>
      <td id="T_5c695_row6_col2" class="data row6 col2" >24</td>
      <td id="T_5c695_row6_col3" class="data row6 col3" >11</td>
      <td id="T_5c695_row6_col4" class="data row6 col4" >10</td>
      <td id="T_5c695_row6_col5" class="data row6 col5" >1</td>
      <td id="T_5c695_row6_col6" class="data row6 col6" >1</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row7" class="row_heading level0 row7" >9</th>
      <td id="T_5c695_row7_col0" class="data row7 col0" >24</td>
      <td id="T_5c695_row7_col1" class="data row7 col1" >32</td>
      <td id="T_5c695_row7_col2" class="data row7 col2" >32</td>
      <td id="T_5c695_row7_col3" class="data row7 col3" >13</td>
      <td id="T_5c695_row7_col4" class="data row7 col4" >5</td>
      <td id="T_5c695_row7_col5" class="data row7 col5" >1</td>
      <td id="T_5c695_row7_col6" class="data row7 col6" >1</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row8" class="row_heading level0 row8" >10</th>
      <td id="T_5c695_row8_col0" class="data row8 col0" >27</td>
      <td id="T_5c695_row8_col1" class="data row8 col1" >27</td>
      <td id="T_5c695_row8_col2" class="data row8 col2" >27</td>
      <td id="T_5c695_row8_col3" class="data row8 col3" >0</td>
      <td id="T_5c695_row8_col4" class="data row8 col4" >0</td>
      <td id="T_5c695_row8_col5" class="data row8 col5" >0</td>
      <td id="T_5c695_row8_col6" class="data row8 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row9" class="row_heading level0 row9" >11</th>
      <td id="T_5c695_row9_col0" class="data row9 col0" >20</td>
      <td id="T_5c695_row9_col1" class="data row9 col1" >33</td>
      <td id="T_5c695_row9_col2" class="data row9 col2" >34</td>
      <td id="T_5c695_row9_col3" class="data row9 col3" >16</td>
      <td id="T_5c695_row9_col4" class="data row9 col4" >3</td>
      <td id="T_5c695_row9_col5" class="data row9 col5" >10</td>
      <td id="T_5c695_row9_col6" class="data row9 col6" >9</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row10" class="row_heading level0 row10" >12</th>
      <td id="T_5c695_row10_col0" class="data row10 col0" >18</td>
      <td id="T_5c695_row10_col1" class="data row10 col1" >18</td>
      <td id="T_5c695_row10_col2" class="data row10 col2" >18</td>
      <td id="T_5c695_row10_col3" class="data row10 col3" >0</td>
      <td id="T_5c695_row10_col4" class="data row10 col4" >0</td>
      <td id="T_5c695_row10_col5" class="data row10 col5" >0</td>
      <td id="T_5c695_row10_col6" class="data row10 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row11" class="row_heading level0 row11" >13</th>
      <td id="T_5c695_row11_col0" class="data row11 col0" >11</td>
      <td id="T_5c695_row11_col1" class="data row11 col1" >30</td>
      <td id="T_5c695_row11_col2" class="data row11 col2" >30</td>
      <td id="T_5c695_row11_col3" class="data row11 col3" >22</td>
      <td id="T_5c695_row11_col4" class="data row11 col4" >3</td>
      <td id="T_5c695_row11_col5" class="data row11 col5" >0</td>
      <td id="T_5c695_row11_col6" class="data row11 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row12" class="row_heading level0 row12" >14</th>
      <td id="T_5c695_row12_col0" class="data row12 col0" >27</td>
      <td id="T_5c695_row12_col1" class="data row12 col1" >27</td>
      <td id="T_5c695_row12_col2" class="data row12 col2" >27</td>
      <td id="T_5c695_row12_col3" class="data row12 col3" >0</td>
      <td id="T_5c695_row12_col4" class="data row12 col4" >0</td>
      <td id="T_5c695_row12_col5" class="data row12 col5" >0</td>
      <td id="T_5c695_row12_col6" class="data row12 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row13" class="row_heading level0 row13" >15</th>
      <td id="T_5c695_row13_col0" class="data row13 col0" >13</td>
      <td id="T_5c695_row13_col1" class="data row13 col1" >13</td>
      <td id="T_5c695_row13_col2" class="data row13 col2" >13</td>
      <td id="T_5c695_row13_col3" class="data row13 col3" >1</td>
      <td id="T_5c695_row13_col4" class="data row13 col4" >1</td>
      <td id="T_5c695_row13_col5" class="data row13 col5" >1</td>
      <td id="T_5c695_row13_col6" class="data row13 col6" >1</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row14" class="row_heading level0 row14" >17</th>
      <td id="T_5c695_row14_col0" class="data row14 col0" >17</td>
      <td id="T_5c695_row14_col1" class="data row14 col1" >17</td>
      <td id="T_5c695_row14_col2" class="data row14 col2" >17</td>
      <td id="T_5c695_row14_col3" class="data row14 col3" >0</td>
      <td id="T_5c695_row14_col4" class="data row14 col4" >0</td>
      <td id="T_5c695_row14_col5" class="data row14 col5" >0</td>
      <td id="T_5c695_row14_col6" class="data row14 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row15" class="row_heading level0 row15" >18</th>
      <td id="T_5c695_row15_col0" class="data row15 col0" >0</td>
      <td id="T_5c695_row15_col1" class="data row15 col1" >16</td>
      <td id="T_5c695_row15_col2" class="data row15 col2" >0</td>
      <td id="T_5c695_row15_col3" class="data row15 col3" >16</td>
      <td id="T_5c695_row15_col4" class="data row15 col4" >0</td>
      <td id="T_5c695_row15_col5" class="data row15 col5" >0</td>
      <td id="T_5c695_row15_col6" class="data row15 col6" >16</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row16" class="row_heading level0 row16" >19</th>
      <td id="T_5c695_row16_col0" class="data row16 col0" >12</td>
      <td id="T_5c695_row16_col1" class="data row16 col1" >12</td>
      <td id="T_5c695_row16_col2" class="data row16 col2" >12</td>
      <td id="T_5c695_row16_col3" class="data row16 col3" >1</td>
      <td id="T_5c695_row16_col4" class="data row16 col4" >1</td>
      <td id="T_5c695_row16_col5" class="data row16 col5" >0</td>
      <td id="T_5c695_row16_col6" class="data row16 col6" >0</td>
    </tr>
    <tr>
      <th id="T_5c695_level0_row17" class="row_heading level0 row17" >E</th>
      <td id="T_5c695_row17_col0" class="data row17 col0" >0</td>
      <td id="T_5c695_row17_col1" class="data row17 col1" >7</td>
      <td id="T_5c695_row17_col2" class="data row17 col2" >7</td>
      <td id="T_5c695_row17_col3" class="data row17 col3" >7</td>
      <td id="T_5c695_row17_col4" class="data row17 col4" >0</td>
      <td id="T_5c695_row17_col5" class="data row17 col5" >0</td>
      <td id="T_5c695_row17_col6" class="data row17 col6" >0</td>
    </tr>
  </tbody>
</table>



## Überblick — Das Netz im Wandel

Beim Fahrplanwechsel Dezember 2023 (j23 → j24) wurden **10 von 17 regulären Linien** im GTFS verändert — der größte Netzwechsel im VBZ-Analysezeitraum. j24 → j25 ist vergleichsweise stabil (nur L5 +5 neue Halte).

Die größten Änderungen betreffen L13 (+19 Halte), L11 (+13) und L9 (+8). Die Karte unten zeigt alle neuen (orange) und entfernten (grau) Haltestellen ab Dez 2023.

### Interaktive Karte


```python
an.plot_network_changes_map(changes)
```





**Beobachtung:** Die Karte zeigt die räumliche Konzentration der Änderungen: Orange-Cluster in der Innenstadt (Bahnhofstrasse-Achse, Paradeplatz) sowie an den neuen Endabschnitten — L13 Richtung Sihlcity im Süden, L11 Richtung Rehalp im Osten. Grau (entfernte Halte) taucht nur vereinzelt auf — der Wechsel war überwiegend additiv, keine grossen Streckenabschnitte wurden gestrichen.

## Wo? — Räumliche Verteilung der Änderungen


```python
section_header("Neue Haltestellen nach Stadtkreis")
an.plot_new_stops_by_district(changes, lf_all, cfg)
show_df(an.table_new_stops_by_district(changes, lf_all))

log("Netto-Änderungen pro Linie (j23→j24 und j24→j25)")
show_df(an.table_network_netto_changes(changes))
```

    
    [1m[38;2;52;97;141m───  NEUE HALTESTELLEN NACH STADTKREIS  ──────────────────────[0m



    
![png](03_analysis_2-network_files/03_analysis_2-network_11_1.png)
    



<style type="text/css">
#T_ebd2e thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_ebd2e td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_ebd2e tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_ebd2e tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_ebd2e tr:hover td {
  background-color: #eef3f8;
}
#T_ebd2e_row0_col0, #T_ebd2e_row1_col0, #T_ebd2e_row2_col0, #T_ebd2e_row3_col0, #T_ebd2e_row4_col0, #T_ebd2e_row5_col0, #T_ebd2e_row6_col0, #T_ebd2e_row7_col0, #T_ebd2e_row8_col0, #T_ebd2e_row9_col0, #T_ebd2e_row10_col0, #T_ebd2e_row11_col0, #T_ebd2e_row12_col0 {
  text-align: left;
}
#T_ebd2e_row0_col1, #T_ebd2e_row1_col1, #T_ebd2e_row2_col1, #T_ebd2e_row3_col1, #T_ebd2e_row4_col1, #T_ebd2e_row5_col1, #T_ebd2e_row6_col1, #T_ebd2e_row7_col1, #T_ebd2e_row8_col1, #T_ebd2e_row9_col1, #T_ebd2e_row10_col1, #T_ebd2e_row11_col1, #T_ebd2e_row12_col1 {
  text-align: right;
}
</style>
<table id="T_ebd2e">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_ebd2e_level0_col0" class="col_heading level0 col0" >District</th>
      <th id="T_ebd2e_level0_col1" class="col_heading level0 col1" >Neue Halte (ab j24)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_ebd2e_level0_row0" class="row_heading level0 row0" >8</th>
      <td id="T_ebd2e_row0_col0" class="data row0 col0" >Kreis 1</td>
      <td id="T_ebd2e_row0_col1" class="data row0 col1" >12</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row1" class="row_heading level0 row1" >6</th>
      <td id="T_ebd2e_row1_col0" class="data row1 col0" >Kreis 3</td>
      <td id="T_ebd2e_row1_col1" class="data row1 col1" >10</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row2" class="row_heading level0 row2" >1</th>
      <td id="T_ebd2e_row2_col0" class="data row2 col0" >Kreis 6</td>
      <td id="T_ebd2e_row2_col1" class="data row2 col1" >10</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row3" class="row_heading level0 row3" >7</th>
      <td id="T_ebd2e_row3_col0" class="data row3 col0" >Kreis 7</td>
      <td id="T_ebd2e_row3_col1" class="data row3 col1" >9</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row4" class="row_heading level0 row4" >2</th>
      <td id="T_ebd2e_row4_col0" class="data row4 col0" >Kreis 2</td>
      <td id="T_ebd2e_row4_col1" class="data row4 col1" >6</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row5" class="row_heading level0 row5" >12</th>
      <td id="T_ebd2e_row5_col0" class="data row5 col0" >Kreis 5</td>
      <td id="T_ebd2e_row5_col1" class="data row5 col1" >5</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row6" class="row_heading level0 row6" >5</th>
      <td id="T_ebd2e_row6_col0" class="data row6 col0" >Kreis 4</td>
      <td id="T_ebd2e_row6_col1" class="data row6 col1" >4</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row7" class="row_heading level0 row7" >9</th>
      <td id="T_ebd2e_row7_col0" class="data row7 col0" >Kreis 11</td>
      <td id="T_ebd2e_row7_col1" class="data row7 col1" >4</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row8" class="row_heading level0 row8" >10</th>
      <td id="T_ebd2e_row8_col0" class="data row8 col0" >Kreis 8</td>
      <td id="T_ebd2e_row8_col1" class="data row8 col1" >3</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row9" class="row_heading level0 row9" >11</th>
      <td id="T_ebd2e_row9_col0" class="data row9 col0" >Kreis 10</td>
      <td id="T_ebd2e_row9_col1" class="data row9 col1" >3</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row10" class="row_heading level0 row10" >4</th>
      <td id="T_ebd2e_row10_col0" class="data row10 col0" >Kreis 12</td>
      <td id="T_ebd2e_row10_col1" class="data row10 col1" >1</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row11" class="row_heading level0 row11" >0</th>
      <td id="T_ebd2e_row11_col0" class="data row11 col0" >outside</td>
      <td id="T_ebd2e_row11_col1" class="data row11 col1" >1</td>
    </tr>
    <tr>
      <th id="T_ebd2e_level0_row12" class="row_heading level0 row12" >3</th>
      <td id="T_ebd2e_row12_col0" class="data row12 col0" >Kreis 9</td>
      <td id="T_ebd2e_row12_col1" class="data row12 col1" >1</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mNetto-Änderungen pro Linie (j23→j24 und j24→j25)[0m



<style type="text/css">
#T_d17a9 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_d17a9 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_d17a9 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_d17a9 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_d17a9 tr:hover td {
  background-color: #eef3f8;
}
#T_d17a9_row0_col0, #T_d17a9_row0_col1, #T_d17a9_row0_col2, #T_d17a9_row0_col3, #T_d17a9_row0_col4, #T_d17a9_row0_col5, #T_d17a9_row0_col6, #T_d17a9_row0_col7, #T_d17a9_row0_col8, #T_d17a9_row1_col0, #T_d17a9_row1_col1, #T_d17a9_row1_col2, #T_d17a9_row1_col3, #T_d17a9_row1_col4, #T_d17a9_row1_col5, #T_d17a9_row1_col6, #T_d17a9_row1_col7, #T_d17a9_row1_col8, #T_d17a9_row2_col0, #T_d17a9_row2_col1, #T_d17a9_row2_col2, #T_d17a9_row2_col3, #T_d17a9_row2_col4, #T_d17a9_row2_col5, #T_d17a9_row2_col6, #T_d17a9_row2_col7, #T_d17a9_row2_col8, #T_d17a9_row3_col0, #T_d17a9_row3_col1, #T_d17a9_row3_col2, #T_d17a9_row3_col3, #T_d17a9_row3_col4, #T_d17a9_row3_col5, #T_d17a9_row3_col6, #T_d17a9_row3_col7, #T_d17a9_row3_col8, #T_d17a9_row4_col0, #T_d17a9_row4_col1, #T_d17a9_row4_col2, #T_d17a9_row4_col3, #T_d17a9_row4_col4, #T_d17a9_row4_col5, #T_d17a9_row4_col6, #T_d17a9_row4_col7, #T_d17a9_row4_col8, #T_d17a9_row5_col0, #T_d17a9_row5_col1, #T_d17a9_row5_col2, #T_d17a9_row5_col3, #T_d17a9_row5_col4, #T_d17a9_row5_col5, #T_d17a9_row5_col6, #T_d17a9_row5_col7, #T_d17a9_row5_col8, #T_d17a9_row6_col0, #T_d17a9_row6_col1, #T_d17a9_row6_col2, #T_d17a9_row6_col3, #T_d17a9_row6_col4, #T_d17a9_row6_col5, #T_d17a9_row6_col6, #T_d17a9_row6_col7, #T_d17a9_row6_col8, #T_d17a9_row7_col0, #T_d17a9_row7_col1, #T_d17a9_row7_col2, #T_d17a9_row7_col3, #T_d17a9_row7_col4, #T_d17a9_row7_col5, #T_d17a9_row7_col6, #T_d17a9_row7_col7, #T_d17a9_row7_col8, #T_d17a9_row8_col0, #T_d17a9_row8_col1, #T_d17a9_row8_col2, #T_d17a9_row8_col3, #T_d17a9_row8_col4, #T_d17a9_row8_col5, #T_d17a9_row8_col6, #T_d17a9_row8_col7, #T_d17a9_row8_col8, #T_d17a9_row9_col0, #T_d17a9_row9_col1, #T_d17a9_row9_col2, #T_d17a9_row9_col3, #T_d17a9_row9_col4, #T_d17a9_row9_col5, #T_d17a9_row9_col6, #T_d17a9_row9_col7, #T_d17a9_row9_col8, #T_d17a9_row10_col0, #T_d17a9_row10_col1, #T_d17a9_row10_col2, #T_d17a9_row10_col3, #T_d17a9_row10_col4, #T_d17a9_row10_col5, #T_d17a9_row10_col6, #T_d17a9_row10_col7, #T_d17a9_row10_col8, #T_d17a9_row11_col0, #T_d17a9_row11_col1, #T_d17a9_row11_col2, #T_d17a9_row11_col3, #T_d17a9_row11_col4, #T_d17a9_row11_col5, #T_d17a9_row11_col6, #T_d17a9_row11_col7, #T_d17a9_row11_col8, #T_d17a9_row12_col0, #T_d17a9_row12_col1, #T_d17a9_row12_col2, #T_d17a9_row12_col3, #T_d17a9_row12_col4, #T_d17a9_row12_col5, #T_d17a9_row12_col6, #T_d17a9_row12_col7, #T_d17a9_row12_col8, #T_d17a9_row13_col0, #T_d17a9_row13_col1, #T_d17a9_row13_col2, #T_d17a9_row13_col3, #T_d17a9_row13_col4, #T_d17a9_row13_col5, #T_d17a9_row13_col6, #T_d17a9_row13_col7, #T_d17a9_row13_col8, #T_d17a9_row14_col0, #T_d17a9_row14_col1, #T_d17a9_row14_col2, #T_d17a9_row14_col3, #T_d17a9_row14_col4, #T_d17a9_row14_col5, #T_d17a9_row14_col6, #T_d17a9_row14_col7, #T_d17a9_row14_col8, #T_d17a9_row15_col0, #T_d17a9_row15_col1, #T_d17a9_row15_col2, #T_d17a9_row15_col3, #T_d17a9_row15_col4, #T_d17a9_row15_col5, #T_d17a9_row15_col6, #T_d17a9_row15_col7, #T_d17a9_row15_col8, #T_d17a9_row16_col0, #T_d17a9_row16_col1, #T_d17a9_row16_col2, #T_d17a9_row16_col3, #T_d17a9_row16_col4, #T_d17a9_row16_col5, #T_d17a9_row16_col6, #T_d17a9_row16_col7, #T_d17a9_row16_col8, #T_d17a9_row17_col0, #T_d17a9_row17_col1, #T_d17a9_row17_col2, #T_d17a9_row17_col3, #T_d17a9_row17_col4, #T_d17a9_row17_col5, #T_d17a9_row17_col6, #T_d17a9_row17_col7, #T_d17a9_row17_col8 {
  text-align: right;
}
</style>
<table id="T_d17a9">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_d17a9_level0_col0" class="col_heading level0 col0" >Halte j23</th>
      <th id="T_d17a9_level0_col1" class="col_heading level0 col1" >Halte j24</th>
      <th id="T_d17a9_level0_col2" class="col_heading level0 col2" >Halte j25</th>
      <th id="T_d17a9_level0_col3" class="col_heading level0 col3" >+j24</th>
      <th id="T_d17a9_level0_col4" class="col_heading level0 col4" >-j24</th>
      <th id="T_d17a9_level0_col5" class="col_heading level0 col5" >+j25</th>
      <th id="T_d17a9_level0_col6" class="col_heading level0 col6" >-j25</th>
      <th id="T_d17a9_level0_col7" class="col_heading level0 col7" >Δ j23→j24</th>
      <th id="T_d17a9_level0_col8" class="col_heading level0 col8" >Δ j24→j25</th>
    </tr>
    <tr>
      <th class="index_name level0" >Line</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
      <th class="blank col5" >&nbsp;</th>
      <th class="blank col6" >&nbsp;</th>
      <th class="blank col7" >&nbsp;</th>
      <th class="blank col8" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_d17a9_level0_row0" class="row_heading level0 row0" >2</th>
      <td id="T_d17a9_row0_col0" class="data row0 col0" >31</td>
      <td id="T_d17a9_row0_col1" class="data row0 col1" >21</td>
      <td id="T_d17a9_row0_col2" class="data row0 col2" >31</td>
      <td id="T_d17a9_row0_col3" class="data row0 col3" >1</td>
      <td id="T_d17a9_row0_col4" class="data row0 col4" >11</td>
      <td id="T_d17a9_row0_col5" class="data row0 col5" >10</td>
      <td id="T_d17a9_row0_col6" class="data row0 col6" >0</td>
      <td id="T_d17a9_row0_col7" class="data row0 col7" >-10</td>
      <td id="T_d17a9_row0_col8" class="data row0 col8" >10</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row1" class="row_heading level0 row1" >3</th>
      <td id="T_d17a9_row1_col0" class="data row1 col0" >21</td>
      <td id="T_d17a9_row1_col1" class="data row1 col1" >21</td>
      <td id="T_d17a9_row1_col2" class="data row1 col2" >21</td>
      <td id="T_d17a9_row1_col3" class="data row1 col3" >2</td>
      <td id="T_d17a9_row1_col4" class="data row1 col4" >2</td>
      <td id="T_d17a9_row1_col5" class="data row1 col5" >0</td>
      <td id="T_d17a9_row1_col6" class="data row1 col6" >0</td>
      <td id="T_d17a9_row1_col7" class="data row1 col7" >0</td>
      <td id="T_d17a9_row1_col8" class="data row1 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row2" class="row_heading level0 row2" >4</th>
      <td id="T_d17a9_row2_col0" class="data row2 col0" >26</td>
      <td id="T_d17a9_row2_col1" class="data row2 col1" >26</td>
      <td id="T_d17a9_row2_col2" class="data row2 col2" >26</td>
      <td id="T_d17a9_row2_col3" class="data row2 col3" >1</td>
      <td id="T_d17a9_row2_col4" class="data row2 col4" >1</td>
      <td id="T_d17a9_row2_col5" class="data row2 col5" >1</td>
      <td id="T_d17a9_row2_col6" class="data row2 col6" >1</td>
      <td id="T_d17a9_row2_col7" class="data row2 col7" >0</td>
      <td id="T_d17a9_row2_col8" class="data row2 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row3" class="row_heading level0 row3" >5</th>
      <td id="T_d17a9_row3_col0" class="data row3 col0" >9</td>
      <td id="T_d17a9_row3_col1" class="data row3 col1" >9</td>
      <td id="T_d17a9_row3_col2" class="data row3 col2" >14</td>
      <td id="T_d17a9_row3_col3" class="data row3 col3" >0</td>
      <td id="T_d17a9_row3_col4" class="data row3 col4" >0</td>
      <td id="T_d17a9_row3_col5" class="data row3 col5" >6</td>
      <td id="T_d17a9_row3_col6" class="data row3 col6" >1</td>
      <td id="T_d17a9_row3_col7" class="data row3 col7" >0</td>
      <td id="T_d17a9_row3_col8" class="data row3 col8" >5</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row4" class="row_heading level0 row4" >6</th>
      <td id="T_d17a9_row4_col0" class="data row4 col0" >24</td>
      <td id="T_d17a9_row4_col1" class="data row4 col1" >16</td>
      <td id="T_d17a9_row4_col2" class="data row4 col2" >16</td>
      <td id="T_d17a9_row4_col3" class="data row4 col3" >6</td>
      <td id="T_d17a9_row4_col4" class="data row4 col4" >14</td>
      <td id="T_d17a9_row4_col5" class="data row4 col5" >0</td>
      <td id="T_d17a9_row4_col6" class="data row4 col6" >0</td>
      <td id="T_d17a9_row4_col7" class="data row4 col7" >-8</td>
      <td id="T_d17a9_row4_col8" class="data row4 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row5" class="row_heading level0 row5" >7</th>
      <td id="T_d17a9_row5_col0" class="data row5 col0" >31</td>
      <td id="T_d17a9_row5_col1" class="data row5 col1" >31</td>
      <td id="T_d17a9_row5_col2" class="data row5 col2" >31</td>
      <td id="T_d17a9_row5_col3" class="data row5 col3" >2</td>
      <td id="T_d17a9_row5_col4" class="data row5 col4" >2</td>
      <td id="T_d17a9_row5_col5" class="data row5 col5" >0</td>
      <td id="T_d17a9_row5_col6" class="data row5 col6" >0</td>
      <td id="T_d17a9_row5_col7" class="data row5 col7" >0</td>
      <td id="T_d17a9_row5_col8" class="data row5 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row6" class="row_heading level0 row6" >8</th>
      <td id="T_d17a9_row6_col0" class="data row6 col0" >23</td>
      <td id="T_d17a9_row6_col1" class="data row6 col1" >24</td>
      <td id="T_d17a9_row6_col2" class="data row6 col2" >24</td>
      <td id="T_d17a9_row6_col3" class="data row6 col3" >11</td>
      <td id="T_d17a9_row6_col4" class="data row6 col4" >10</td>
      <td id="T_d17a9_row6_col5" class="data row6 col5" >1</td>
      <td id="T_d17a9_row6_col6" class="data row6 col6" >1</td>
      <td id="T_d17a9_row6_col7" class="data row6 col7" >1</td>
      <td id="T_d17a9_row6_col8" class="data row6 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row7" class="row_heading level0 row7" >9</th>
      <td id="T_d17a9_row7_col0" class="data row7 col0" >24</td>
      <td id="T_d17a9_row7_col1" class="data row7 col1" >32</td>
      <td id="T_d17a9_row7_col2" class="data row7 col2" >32</td>
      <td id="T_d17a9_row7_col3" class="data row7 col3" >13</td>
      <td id="T_d17a9_row7_col4" class="data row7 col4" >5</td>
      <td id="T_d17a9_row7_col5" class="data row7 col5" >1</td>
      <td id="T_d17a9_row7_col6" class="data row7 col6" >1</td>
      <td id="T_d17a9_row7_col7" class="data row7 col7" >8</td>
      <td id="T_d17a9_row7_col8" class="data row7 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row8" class="row_heading level0 row8" >10</th>
      <td id="T_d17a9_row8_col0" class="data row8 col0" >27</td>
      <td id="T_d17a9_row8_col1" class="data row8 col1" >27</td>
      <td id="T_d17a9_row8_col2" class="data row8 col2" >27</td>
      <td id="T_d17a9_row8_col3" class="data row8 col3" >0</td>
      <td id="T_d17a9_row8_col4" class="data row8 col4" >0</td>
      <td id="T_d17a9_row8_col5" class="data row8 col5" >0</td>
      <td id="T_d17a9_row8_col6" class="data row8 col6" >0</td>
      <td id="T_d17a9_row8_col7" class="data row8 col7" >0</td>
      <td id="T_d17a9_row8_col8" class="data row8 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row9" class="row_heading level0 row9" >11</th>
      <td id="T_d17a9_row9_col0" class="data row9 col0" >20</td>
      <td id="T_d17a9_row9_col1" class="data row9 col1" >33</td>
      <td id="T_d17a9_row9_col2" class="data row9 col2" >34</td>
      <td id="T_d17a9_row9_col3" class="data row9 col3" >16</td>
      <td id="T_d17a9_row9_col4" class="data row9 col4" >3</td>
      <td id="T_d17a9_row9_col5" class="data row9 col5" >10</td>
      <td id="T_d17a9_row9_col6" class="data row9 col6" >9</td>
      <td id="T_d17a9_row9_col7" class="data row9 col7" >13</td>
      <td id="T_d17a9_row9_col8" class="data row9 col8" >1</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row10" class="row_heading level0 row10" >12</th>
      <td id="T_d17a9_row10_col0" class="data row10 col0" >18</td>
      <td id="T_d17a9_row10_col1" class="data row10 col1" >18</td>
      <td id="T_d17a9_row10_col2" class="data row10 col2" >18</td>
      <td id="T_d17a9_row10_col3" class="data row10 col3" >0</td>
      <td id="T_d17a9_row10_col4" class="data row10 col4" >0</td>
      <td id="T_d17a9_row10_col5" class="data row10 col5" >0</td>
      <td id="T_d17a9_row10_col6" class="data row10 col6" >0</td>
      <td id="T_d17a9_row10_col7" class="data row10 col7" >0</td>
      <td id="T_d17a9_row10_col8" class="data row10 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row11" class="row_heading level0 row11" >13</th>
      <td id="T_d17a9_row11_col0" class="data row11 col0" >11</td>
      <td id="T_d17a9_row11_col1" class="data row11 col1" >30</td>
      <td id="T_d17a9_row11_col2" class="data row11 col2" >30</td>
      <td id="T_d17a9_row11_col3" class="data row11 col3" >22</td>
      <td id="T_d17a9_row11_col4" class="data row11 col4" >3</td>
      <td id="T_d17a9_row11_col5" class="data row11 col5" >0</td>
      <td id="T_d17a9_row11_col6" class="data row11 col6" >0</td>
      <td id="T_d17a9_row11_col7" class="data row11 col7" >19</td>
      <td id="T_d17a9_row11_col8" class="data row11 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row12" class="row_heading level0 row12" >14</th>
      <td id="T_d17a9_row12_col0" class="data row12 col0" >27</td>
      <td id="T_d17a9_row12_col1" class="data row12 col1" >27</td>
      <td id="T_d17a9_row12_col2" class="data row12 col2" >27</td>
      <td id="T_d17a9_row12_col3" class="data row12 col3" >0</td>
      <td id="T_d17a9_row12_col4" class="data row12 col4" >0</td>
      <td id="T_d17a9_row12_col5" class="data row12 col5" >0</td>
      <td id="T_d17a9_row12_col6" class="data row12 col6" >0</td>
      <td id="T_d17a9_row12_col7" class="data row12 col7" >0</td>
      <td id="T_d17a9_row12_col8" class="data row12 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row13" class="row_heading level0 row13" >15</th>
      <td id="T_d17a9_row13_col0" class="data row13 col0" >13</td>
      <td id="T_d17a9_row13_col1" class="data row13 col1" >13</td>
      <td id="T_d17a9_row13_col2" class="data row13 col2" >13</td>
      <td id="T_d17a9_row13_col3" class="data row13 col3" >1</td>
      <td id="T_d17a9_row13_col4" class="data row13 col4" >1</td>
      <td id="T_d17a9_row13_col5" class="data row13 col5" >1</td>
      <td id="T_d17a9_row13_col6" class="data row13 col6" >1</td>
      <td id="T_d17a9_row13_col7" class="data row13 col7" >0</td>
      <td id="T_d17a9_row13_col8" class="data row13 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row14" class="row_heading level0 row14" >17</th>
      <td id="T_d17a9_row14_col0" class="data row14 col0" >17</td>
      <td id="T_d17a9_row14_col1" class="data row14 col1" >17</td>
      <td id="T_d17a9_row14_col2" class="data row14 col2" >17</td>
      <td id="T_d17a9_row14_col3" class="data row14 col3" >0</td>
      <td id="T_d17a9_row14_col4" class="data row14 col4" >0</td>
      <td id="T_d17a9_row14_col5" class="data row14 col5" >0</td>
      <td id="T_d17a9_row14_col6" class="data row14 col6" >0</td>
      <td id="T_d17a9_row14_col7" class="data row14 col7" >0</td>
      <td id="T_d17a9_row14_col8" class="data row14 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row15" class="row_heading level0 row15" >18</th>
      <td id="T_d17a9_row15_col0" class="data row15 col0" >0</td>
      <td id="T_d17a9_row15_col1" class="data row15 col1" >16</td>
      <td id="T_d17a9_row15_col2" class="data row15 col2" >0</td>
      <td id="T_d17a9_row15_col3" class="data row15 col3" >16</td>
      <td id="T_d17a9_row15_col4" class="data row15 col4" >0</td>
      <td id="T_d17a9_row15_col5" class="data row15 col5" >0</td>
      <td id="T_d17a9_row15_col6" class="data row15 col6" >16</td>
      <td id="T_d17a9_row15_col7" class="data row15 col7" >16</td>
      <td id="T_d17a9_row15_col8" class="data row15 col8" >-16</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row16" class="row_heading level0 row16" >19</th>
      <td id="T_d17a9_row16_col0" class="data row16 col0" >12</td>
      <td id="T_d17a9_row16_col1" class="data row16 col1" >12</td>
      <td id="T_d17a9_row16_col2" class="data row16 col2" >12</td>
      <td id="T_d17a9_row16_col3" class="data row16 col3" >1</td>
      <td id="T_d17a9_row16_col4" class="data row16 col4" >1</td>
      <td id="T_d17a9_row16_col5" class="data row16 col5" >0</td>
      <td id="T_d17a9_row16_col6" class="data row16 col6" >0</td>
      <td id="T_d17a9_row16_col7" class="data row16 col7" >0</td>
      <td id="T_d17a9_row16_col8" class="data row16 col8" >0</td>
    </tr>
    <tr>
      <th id="T_d17a9_level0_row17" class="row_heading level0 row17" >E</th>
      <td id="T_d17a9_row17_col0" class="data row17 col0" >0</td>
      <td id="T_d17a9_row17_col1" class="data row17 col1" >7</td>
      <td id="T_d17a9_row17_col2" class="data row17 col2" >7</td>
      <td id="T_d17a9_row17_col3" class="data row17 col3" >7</td>
      <td id="T_d17a9_row17_col4" class="data row17 col4" >0</td>
      <td id="T_d17a9_row17_col5" class="data row17 col5" >0</td>
      <td id="T_d17a9_row17_col6" class="data row17 col6" >0</td>
      <td id="T_d17a9_row17_col7" class="data row17 col7" >7</td>
      <td id="T_d17a9_row17_col8" class="data row17 col8" >0</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Das Balkendiagramm zeigt, dass die meisten neuen GTFS-Haltestellen in den Innenstadt-Kreisen erscheinen — Kreis 1 mit 12 neuen Haltestellen führt. Das ist zunächst überraschend, lässt sich aber nach Prüfung der konkreten Haltestellen-Namen erklären.

**Top-Kreise nach neuen GTFS-Haltestellen (ab Dez 2023):**
| Stadtkreis | Neue Halte |
|:---|---:|
| Kreis 1 (Altstadt/City) | **12** |
| Kreis 3 (Wiedikon) | 10 |
| Kreis 6 (Unterstrass) | 10 |
| Kreis 7 (Fluntern/Witikon) | 9 |
| Kreis 2 (Enge/Wollishofen) | 6 |
| Kreis 8 (Riesbach) | 5 |

**Was steckt dahinter — zwei verschiedene Ursachen:**

1. **GTFS-Artefakt (K1, K6):** Die meisten "neuen" Halte in Kreis 1 sind Stammhaltestellen, die seit Jahrzehnten bestehen — Paradeplatz, Bahnhofstrasse/HB, Rennweg, Stockerstrasse, Tunnelstrasse. Sie erscheinen als "neu", weil L6, L8, L9, L13 ab j24 andere repräsentative Trip-Shapes im GTFS nutzen, die durch diese Innenstadt-Achse führen. **Keine neue Infrastruktur.**

2. **Echte Streckenerweiterungen (K3, K8):**
   - **L13 → Sihlcity/Süd (K3):** Albisgütli, Laubegg, Eschergutweg, Waidfussweg, Sihlcity Nord, Uetlihof — echte neue Endabschnitte im Süden
   - **L11 → Rehalp/Zürichberg (K8):** Balgrist, Rehalp, Burgwies, Friedhof Enzenbühl, Hedwigsteig, Hegibachplatz — Verlängerung Richtung Zürichberg

**Kritischer Kontrast:**  
Die tatsächlichen Problemkreise K11 (Schwamendingen) und K12 (Oerlikon) — beide Spitze bei Verspätung in der Spatial-Analyse — haben **keine** neuen Haltestellen erhalten. Der Netzausbau zielte in Richtungen, die ohnehin gut performen.

## Wieviel? — Quantifizierung der Änderungen


```python
an.plot_network_stop_count_by_line(changes, cfg)

show_df(an.table_network_netto_changes(changes))

```


    
![png](03_analysis_2-network_files/03_analysis_2-network_14_0.png)
    



<style type="text/css">
#T_a3ce2 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_a3ce2 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_a3ce2 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_a3ce2 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_a3ce2 tr:hover td {
  background-color: #eef3f8;
}
#T_a3ce2_row0_col0, #T_a3ce2_row0_col1, #T_a3ce2_row0_col2, #T_a3ce2_row0_col3, #T_a3ce2_row0_col4, #T_a3ce2_row0_col5, #T_a3ce2_row0_col6, #T_a3ce2_row0_col7, #T_a3ce2_row0_col8, #T_a3ce2_row1_col0, #T_a3ce2_row1_col1, #T_a3ce2_row1_col2, #T_a3ce2_row1_col3, #T_a3ce2_row1_col4, #T_a3ce2_row1_col5, #T_a3ce2_row1_col6, #T_a3ce2_row1_col7, #T_a3ce2_row1_col8, #T_a3ce2_row2_col0, #T_a3ce2_row2_col1, #T_a3ce2_row2_col2, #T_a3ce2_row2_col3, #T_a3ce2_row2_col4, #T_a3ce2_row2_col5, #T_a3ce2_row2_col6, #T_a3ce2_row2_col7, #T_a3ce2_row2_col8, #T_a3ce2_row3_col0, #T_a3ce2_row3_col1, #T_a3ce2_row3_col2, #T_a3ce2_row3_col3, #T_a3ce2_row3_col4, #T_a3ce2_row3_col5, #T_a3ce2_row3_col6, #T_a3ce2_row3_col7, #T_a3ce2_row3_col8, #T_a3ce2_row4_col0, #T_a3ce2_row4_col1, #T_a3ce2_row4_col2, #T_a3ce2_row4_col3, #T_a3ce2_row4_col4, #T_a3ce2_row4_col5, #T_a3ce2_row4_col6, #T_a3ce2_row4_col7, #T_a3ce2_row4_col8, #T_a3ce2_row5_col0, #T_a3ce2_row5_col1, #T_a3ce2_row5_col2, #T_a3ce2_row5_col3, #T_a3ce2_row5_col4, #T_a3ce2_row5_col5, #T_a3ce2_row5_col6, #T_a3ce2_row5_col7, #T_a3ce2_row5_col8, #T_a3ce2_row6_col0, #T_a3ce2_row6_col1, #T_a3ce2_row6_col2, #T_a3ce2_row6_col3, #T_a3ce2_row6_col4, #T_a3ce2_row6_col5, #T_a3ce2_row6_col6, #T_a3ce2_row6_col7, #T_a3ce2_row6_col8, #T_a3ce2_row7_col0, #T_a3ce2_row7_col1, #T_a3ce2_row7_col2, #T_a3ce2_row7_col3, #T_a3ce2_row7_col4, #T_a3ce2_row7_col5, #T_a3ce2_row7_col6, #T_a3ce2_row7_col7, #T_a3ce2_row7_col8, #T_a3ce2_row8_col0, #T_a3ce2_row8_col1, #T_a3ce2_row8_col2, #T_a3ce2_row8_col3, #T_a3ce2_row8_col4, #T_a3ce2_row8_col5, #T_a3ce2_row8_col6, #T_a3ce2_row8_col7, #T_a3ce2_row8_col8, #T_a3ce2_row9_col0, #T_a3ce2_row9_col1, #T_a3ce2_row9_col2, #T_a3ce2_row9_col3, #T_a3ce2_row9_col4, #T_a3ce2_row9_col5, #T_a3ce2_row9_col6, #T_a3ce2_row9_col7, #T_a3ce2_row9_col8, #T_a3ce2_row10_col0, #T_a3ce2_row10_col1, #T_a3ce2_row10_col2, #T_a3ce2_row10_col3, #T_a3ce2_row10_col4, #T_a3ce2_row10_col5, #T_a3ce2_row10_col6, #T_a3ce2_row10_col7, #T_a3ce2_row10_col8, #T_a3ce2_row11_col0, #T_a3ce2_row11_col1, #T_a3ce2_row11_col2, #T_a3ce2_row11_col3, #T_a3ce2_row11_col4, #T_a3ce2_row11_col5, #T_a3ce2_row11_col6, #T_a3ce2_row11_col7, #T_a3ce2_row11_col8, #T_a3ce2_row12_col0, #T_a3ce2_row12_col1, #T_a3ce2_row12_col2, #T_a3ce2_row12_col3, #T_a3ce2_row12_col4, #T_a3ce2_row12_col5, #T_a3ce2_row12_col6, #T_a3ce2_row12_col7, #T_a3ce2_row12_col8, #T_a3ce2_row13_col0, #T_a3ce2_row13_col1, #T_a3ce2_row13_col2, #T_a3ce2_row13_col3, #T_a3ce2_row13_col4, #T_a3ce2_row13_col5, #T_a3ce2_row13_col6, #T_a3ce2_row13_col7, #T_a3ce2_row13_col8, #T_a3ce2_row14_col0, #T_a3ce2_row14_col1, #T_a3ce2_row14_col2, #T_a3ce2_row14_col3, #T_a3ce2_row14_col4, #T_a3ce2_row14_col5, #T_a3ce2_row14_col6, #T_a3ce2_row14_col7, #T_a3ce2_row14_col8, #T_a3ce2_row15_col0, #T_a3ce2_row15_col1, #T_a3ce2_row15_col2, #T_a3ce2_row15_col3, #T_a3ce2_row15_col4, #T_a3ce2_row15_col5, #T_a3ce2_row15_col6, #T_a3ce2_row15_col7, #T_a3ce2_row15_col8, #T_a3ce2_row16_col0, #T_a3ce2_row16_col1, #T_a3ce2_row16_col2, #T_a3ce2_row16_col3, #T_a3ce2_row16_col4, #T_a3ce2_row16_col5, #T_a3ce2_row16_col6, #T_a3ce2_row16_col7, #T_a3ce2_row16_col8, #T_a3ce2_row17_col0, #T_a3ce2_row17_col1, #T_a3ce2_row17_col2, #T_a3ce2_row17_col3, #T_a3ce2_row17_col4, #T_a3ce2_row17_col5, #T_a3ce2_row17_col6, #T_a3ce2_row17_col7, #T_a3ce2_row17_col8 {
  text-align: right;
}
</style>
<table id="T_a3ce2">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_a3ce2_level0_col0" class="col_heading level0 col0" >Halte j23</th>
      <th id="T_a3ce2_level0_col1" class="col_heading level0 col1" >Halte j24</th>
      <th id="T_a3ce2_level0_col2" class="col_heading level0 col2" >Halte j25</th>
      <th id="T_a3ce2_level0_col3" class="col_heading level0 col3" >+j24</th>
      <th id="T_a3ce2_level0_col4" class="col_heading level0 col4" >-j24</th>
      <th id="T_a3ce2_level0_col5" class="col_heading level0 col5" >+j25</th>
      <th id="T_a3ce2_level0_col6" class="col_heading level0 col6" >-j25</th>
      <th id="T_a3ce2_level0_col7" class="col_heading level0 col7" >Δ j23→j24</th>
      <th id="T_a3ce2_level0_col8" class="col_heading level0 col8" >Δ j24→j25</th>
    </tr>
    <tr>
      <th class="index_name level0" >Line</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
      <th class="blank col5" >&nbsp;</th>
      <th class="blank col6" >&nbsp;</th>
      <th class="blank col7" >&nbsp;</th>
      <th class="blank col8" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_a3ce2_level0_row0" class="row_heading level0 row0" >2</th>
      <td id="T_a3ce2_row0_col0" class="data row0 col0" >31</td>
      <td id="T_a3ce2_row0_col1" class="data row0 col1" >21</td>
      <td id="T_a3ce2_row0_col2" class="data row0 col2" >31</td>
      <td id="T_a3ce2_row0_col3" class="data row0 col3" >1</td>
      <td id="T_a3ce2_row0_col4" class="data row0 col4" >11</td>
      <td id="T_a3ce2_row0_col5" class="data row0 col5" >10</td>
      <td id="T_a3ce2_row0_col6" class="data row0 col6" >0</td>
      <td id="T_a3ce2_row0_col7" class="data row0 col7" >-10</td>
      <td id="T_a3ce2_row0_col8" class="data row0 col8" >10</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row1" class="row_heading level0 row1" >3</th>
      <td id="T_a3ce2_row1_col0" class="data row1 col0" >21</td>
      <td id="T_a3ce2_row1_col1" class="data row1 col1" >21</td>
      <td id="T_a3ce2_row1_col2" class="data row1 col2" >21</td>
      <td id="T_a3ce2_row1_col3" class="data row1 col3" >2</td>
      <td id="T_a3ce2_row1_col4" class="data row1 col4" >2</td>
      <td id="T_a3ce2_row1_col5" class="data row1 col5" >0</td>
      <td id="T_a3ce2_row1_col6" class="data row1 col6" >0</td>
      <td id="T_a3ce2_row1_col7" class="data row1 col7" >0</td>
      <td id="T_a3ce2_row1_col8" class="data row1 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row2" class="row_heading level0 row2" >4</th>
      <td id="T_a3ce2_row2_col0" class="data row2 col0" >26</td>
      <td id="T_a3ce2_row2_col1" class="data row2 col1" >26</td>
      <td id="T_a3ce2_row2_col2" class="data row2 col2" >26</td>
      <td id="T_a3ce2_row2_col3" class="data row2 col3" >1</td>
      <td id="T_a3ce2_row2_col4" class="data row2 col4" >1</td>
      <td id="T_a3ce2_row2_col5" class="data row2 col5" >1</td>
      <td id="T_a3ce2_row2_col6" class="data row2 col6" >1</td>
      <td id="T_a3ce2_row2_col7" class="data row2 col7" >0</td>
      <td id="T_a3ce2_row2_col8" class="data row2 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row3" class="row_heading level0 row3" >5</th>
      <td id="T_a3ce2_row3_col0" class="data row3 col0" >9</td>
      <td id="T_a3ce2_row3_col1" class="data row3 col1" >9</td>
      <td id="T_a3ce2_row3_col2" class="data row3 col2" >14</td>
      <td id="T_a3ce2_row3_col3" class="data row3 col3" >0</td>
      <td id="T_a3ce2_row3_col4" class="data row3 col4" >0</td>
      <td id="T_a3ce2_row3_col5" class="data row3 col5" >6</td>
      <td id="T_a3ce2_row3_col6" class="data row3 col6" >1</td>
      <td id="T_a3ce2_row3_col7" class="data row3 col7" >0</td>
      <td id="T_a3ce2_row3_col8" class="data row3 col8" >5</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row4" class="row_heading level0 row4" >6</th>
      <td id="T_a3ce2_row4_col0" class="data row4 col0" >24</td>
      <td id="T_a3ce2_row4_col1" class="data row4 col1" >16</td>
      <td id="T_a3ce2_row4_col2" class="data row4 col2" >16</td>
      <td id="T_a3ce2_row4_col3" class="data row4 col3" >6</td>
      <td id="T_a3ce2_row4_col4" class="data row4 col4" >14</td>
      <td id="T_a3ce2_row4_col5" class="data row4 col5" >0</td>
      <td id="T_a3ce2_row4_col6" class="data row4 col6" >0</td>
      <td id="T_a3ce2_row4_col7" class="data row4 col7" >-8</td>
      <td id="T_a3ce2_row4_col8" class="data row4 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row5" class="row_heading level0 row5" >7</th>
      <td id="T_a3ce2_row5_col0" class="data row5 col0" >31</td>
      <td id="T_a3ce2_row5_col1" class="data row5 col1" >31</td>
      <td id="T_a3ce2_row5_col2" class="data row5 col2" >31</td>
      <td id="T_a3ce2_row5_col3" class="data row5 col3" >2</td>
      <td id="T_a3ce2_row5_col4" class="data row5 col4" >2</td>
      <td id="T_a3ce2_row5_col5" class="data row5 col5" >0</td>
      <td id="T_a3ce2_row5_col6" class="data row5 col6" >0</td>
      <td id="T_a3ce2_row5_col7" class="data row5 col7" >0</td>
      <td id="T_a3ce2_row5_col8" class="data row5 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row6" class="row_heading level0 row6" >8</th>
      <td id="T_a3ce2_row6_col0" class="data row6 col0" >23</td>
      <td id="T_a3ce2_row6_col1" class="data row6 col1" >24</td>
      <td id="T_a3ce2_row6_col2" class="data row6 col2" >24</td>
      <td id="T_a3ce2_row6_col3" class="data row6 col3" >11</td>
      <td id="T_a3ce2_row6_col4" class="data row6 col4" >10</td>
      <td id="T_a3ce2_row6_col5" class="data row6 col5" >1</td>
      <td id="T_a3ce2_row6_col6" class="data row6 col6" >1</td>
      <td id="T_a3ce2_row6_col7" class="data row6 col7" >1</td>
      <td id="T_a3ce2_row6_col8" class="data row6 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row7" class="row_heading level0 row7" >9</th>
      <td id="T_a3ce2_row7_col0" class="data row7 col0" >24</td>
      <td id="T_a3ce2_row7_col1" class="data row7 col1" >32</td>
      <td id="T_a3ce2_row7_col2" class="data row7 col2" >32</td>
      <td id="T_a3ce2_row7_col3" class="data row7 col3" >13</td>
      <td id="T_a3ce2_row7_col4" class="data row7 col4" >5</td>
      <td id="T_a3ce2_row7_col5" class="data row7 col5" >1</td>
      <td id="T_a3ce2_row7_col6" class="data row7 col6" >1</td>
      <td id="T_a3ce2_row7_col7" class="data row7 col7" >8</td>
      <td id="T_a3ce2_row7_col8" class="data row7 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row8" class="row_heading level0 row8" >10</th>
      <td id="T_a3ce2_row8_col0" class="data row8 col0" >27</td>
      <td id="T_a3ce2_row8_col1" class="data row8 col1" >27</td>
      <td id="T_a3ce2_row8_col2" class="data row8 col2" >27</td>
      <td id="T_a3ce2_row8_col3" class="data row8 col3" >0</td>
      <td id="T_a3ce2_row8_col4" class="data row8 col4" >0</td>
      <td id="T_a3ce2_row8_col5" class="data row8 col5" >0</td>
      <td id="T_a3ce2_row8_col6" class="data row8 col6" >0</td>
      <td id="T_a3ce2_row8_col7" class="data row8 col7" >0</td>
      <td id="T_a3ce2_row8_col8" class="data row8 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row9" class="row_heading level0 row9" >11</th>
      <td id="T_a3ce2_row9_col0" class="data row9 col0" >20</td>
      <td id="T_a3ce2_row9_col1" class="data row9 col1" >33</td>
      <td id="T_a3ce2_row9_col2" class="data row9 col2" >34</td>
      <td id="T_a3ce2_row9_col3" class="data row9 col3" >16</td>
      <td id="T_a3ce2_row9_col4" class="data row9 col4" >3</td>
      <td id="T_a3ce2_row9_col5" class="data row9 col5" >10</td>
      <td id="T_a3ce2_row9_col6" class="data row9 col6" >9</td>
      <td id="T_a3ce2_row9_col7" class="data row9 col7" >13</td>
      <td id="T_a3ce2_row9_col8" class="data row9 col8" >1</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row10" class="row_heading level0 row10" >12</th>
      <td id="T_a3ce2_row10_col0" class="data row10 col0" >18</td>
      <td id="T_a3ce2_row10_col1" class="data row10 col1" >18</td>
      <td id="T_a3ce2_row10_col2" class="data row10 col2" >18</td>
      <td id="T_a3ce2_row10_col3" class="data row10 col3" >0</td>
      <td id="T_a3ce2_row10_col4" class="data row10 col4" >0</td>
      <td id="T_a3ce2_row10_col5" class="data row10 col5" >0</td>
      <td id="T_a3ce2_row10_col6" class="data row10 col6" >0</td>
      <td id="T_a3ce2_row10_col7" class="data row10 col7" >0</td>
      <td id="T_a3ce2_row10_col8" class="data row10 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row11" class="row_heading level0 row11" >13</th>
      <td id="T_a3ce2_row11_col0" class="data row11 col0" >11</td>
      <td id="T_a3ce2_row11_col1" class="data row11 col1" >30</td>
      <td id="T_a3ce2_row11_col2" class="data row11 col2" >30</td>
      <td id="T_a3ce2_row11_col3" class="data row11 col3" >22</td>
      <td id="T_a3ce2_row11_col4" class="data row11 col4" >3</td>
      <td id="T_a3ce2_row11_col5" class="data row11 col5" >0</td>
      <td id="T_a3ce2_row11_col6" class="data row11 col6" >0</td>
      <td id="T_a3ce2_row11_col7" class="data row11 col7" >19</td>
      <td id="T_a3ce2_row11_col8" class="data row11 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row12" class="row_heading level0 row12" >14</th>
      <td id="T_a3ce2_row12_col0" class="data row12 col0" >27</td>
      <td id="T_a3ce2_row12_col1" class="data row12 col1" >27</td>
      <td id="T_a3ce2_row12_col2" class="data row12 col2" >27</td>
      <td id="T_a3ce2_row12_col3" class="data row12 col3" >0</td>
      <td id="T_a3ce2_row12_col4" class="data row12 col4" >0</td>
      <td id="T_a3ce2_row12_col5" class="data row12 col5" >0</td>
      <td id="T_a3ce2_row12_col6" class="data row12 col6" >0</td>
      <td id="T_a3ce2_row12_col7" class="data row12 col7" >0</td>
      <td id="T_a3ce2_row12_col8" class="data row12 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row13" class="row_heading level0 row13" >15</th>
      <td id="T_a3ce2_row13_col0" class="data row13 col0" >13</td>
      <td id="T_a3ce2_row13_col1" class="data row13 col1" >13</td>
      <td id="T_a3ce2_row13_col2" class="data row13 col2" >13</td>
      <td id="T_a3ce2_row13_col3" class="data row13 col3" >1</td>
      <td id="T_a3ce2_row13_col4" class="data row13 col4" >1</td>
      <td id="T_a3ce2_row13_col5" class="data row13 col5" >1</td>
      <td id="T_a3ce2_row13_col6" class="data row13 col6" >1</td>
      <td id="T_a3ce2_row13_col7" class="data row13 col7" >0</td>
      <td id="T_a3ce2_row13_col8" class="data row13 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row14" class="row_heading level0 row14" >17</th>
      <td id="T_a3ce2_row14_col0" class="data row14 col0" >17</td>
      <td id="T_a3ce2_row14_col1" class="data row14 col1" >17</td>
      <td id="T_a3ce2_row14_col2" class="data row14 col2" >17</td>
      <td id="T_a3ce2_row14_col3" class="data row14 col3" >0</td>
      <td id="T_a3ce2_row14_col4" class="data row14 col4" >0</td>
      <td id="T_a3ce2_row14_col5" class="data row14 col5" >0</td>
      <td id="T_a3ce2_row14_col6" class="data row14 col6" >0</td>
      <td id="T_a3ce2_row14_col7" class="data row14 col7" >0</td>
      <td id="T_a3ce2_row14_col8" class="data row14 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row15" class="row_heading level0 row15" >18</th>
      <td id="T_a3ce2_row15_col0" class="data row15 col0" >0</td>
      <td id="T_a3ce2_row15_col1" class="data row15 col1" >16</td>
      <td id="T_a3ce2_row15_col2" class="data row15 col2" >0</td>
      <td id="T_a3ce2_row15_col3" class="data row15 col3" >16</td>
      <td id="T_a3ce2_row15_col4" class="data row15 col4" >0</td>
      <td id="T_a3ce2_row15_col5" class="data row15 col5" >0</td>
      <td id="T_a3ce2_row15_col6" class="data row15 col6" >16</td>
      <td id="T_a3ce2_row15_col7" class="data row15 col7" >16</td>
      <td id="T_a3ce2_row15_col8" class="data row15 col8" >-16</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row16" class="row_heading level0 row16" >19</th>
      <td id="T_a3ce2_row16_col0" class="data row16 col0" >12</td>
      <td id="T_a3ce2_row16_col1" class="data row16 col1" >12</td>
      <td id="T_a3ce2_row16_col2" class="data row16 col2" >12</td>
      <td id="T_a3ce2_row16_col3" class="data row16 col3" >1</td>
      <td id="T_a3ce2_row16_col4" class="data row16 col4" >1</td>
      <td id="T_a3ce2_row16_col5" class="data row16 col5" >0</td>
      <td id="T_a3ce2_row16_col6" class="data row16 col6" >0</td>
      <td id="T_a3ce2_row16_col7" class="data row16 col7" >0</td>
      <td id="T_a3ce2_row16_col8" class="data row16 col8" >0</td>
    </tr>
    <tr>
      <th id="T_a3ce2_level0_row17" class="row_heading level0 row17" >E</th>
      <td id="T_a3ce2_row17_col0" class="data row17 col0" >0</td>
      <td id="T_a3ce2_row17_col1" class="data row17 col1" >7</td>
      <td id="T_a3ce2_row17_col2" class="data row17 col2" >7</td>
      <td id="T_a3ce2_row17_col3" class="data row17 col3" >7</td>
      <td id="T_a3ce2_row17_col4" class="data row17 col4" >0</td>
      <td id="T_a3ce2_row17_col5" class="data row17 col5" >0</td>
      <td id="T_a3ce2_row17_col6" class="data row17 col6" >0</td>
      <td id="T_a3ce2_row17_col7" class="data row17 col7" >7</td>
      <td id="T_a3ce2_row17_col8" class="data row17 col8" >0</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Das Quantifizierungs-Chart und die Tabelle liefern klare Zahlen zum Ausmass der GTFS-Änderungen.

**Netto-Änderungen j23 → j24 (die grossen Bewegungen):**
| Linie | j23 | j24 | j25 | Δ j23→j24 | Anmerkung |
|:---|---:|---:|---:|---:|:---|
| **L13** | 11 | 30 | 30 | **+19** | Grösste Änderung (+173%) |
| **L11** | 20 | 33 | 34 | **+13** | +16 hinzu, -3 entfernt |
| **L9** | 24 | 32 | 32 | **+8** | +13 hinzu, -5 entfernt |
| L18 | 0 | 16 | 0 | +16 | Temporäre Linie — nur 2024 aktiv |
| **L6** | 24 | 16 | 16 | **−8** | Netto 8 Halte entfernt |

**Anomalie L2:** j23=31 Halte → j24=21 (−10) → j25=31 (+10 zurück). Die Haltestellen-Zahl schwankt stark zwischen den Jahren, obwohl L2 als "stabil" gilt. Wahrscheinlich eine GTFS-Routing-Variante (andere Wendeäste oder Kursführung je Fahrplan), keine reale Streckenkürzung und Rückkehr.

**Neu in j25 (nicht j24):** L5 wächst von 9 auf 14 Halte (+5) — der einzige nennenswerte Ausbau beim j24→j25-Übergang.

**Stabil über alle Jahre:** L10, L12, L14, L17 (identische Haltestellen-Zahl in j23/j24/j25) — echte Referenzlinien für jahresübergreifende Vergleiche.

## Wann? — Zeitachse der Änderungen


```python
an.plot_monthly_delay_all_lines(lf_all, cfg, ylim=(0, 200))

show_df(an.table_delay_before_after_switch(lf_all))
```


    
![png](03_analysis_2-network_files/03_analysis_2-network_17_0.png)
    



<style type="text/css">
#T_710c8 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_710c8 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_710c8 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_710c8 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_710c8 tr:hover td {
  background-color: #eef3f8;
}
#T_710c8_row0_col0, #T_710c8_row0_col1, #T_710c8_row1_col0, #T_710c8_row1_col1, #T_710c8_row2_col0, #T_710c8_row2_col1, #T_710c8_row3_col0, #T_710c8_row3_col1, #T_710c8_row4_col0, #T_710c8_row4_col1, #T_710c8_row5_col0, #T_710c8_row5_col1, #T_710c8_row6_col0, #T_710c8_row6_col1, #T_710c8_row7_col0, #T_710c8_row7_col1, #T_710c8_row8_col0, #T_710c8_row8_col1, #T_710c8_row9_col0, #T_710c8_row9_col1, #T_710c8_row10_col0, #T_710c8_row10_col1, #T_710c8_row11_col0, #T_710c8_row11_col1, #T_710c8_row12_col0, #T_710c8_row12_col1, #T_710c8_row13_col0, #T_710c8_row13_col1, #T_710c8_row14_col0, #T_710c8_row14_col1, #T_710c8_row15_col0, #T_710c8_row15_col1, #T_710c8_row16_col0, #T_710c8_row16_col1, #T_710c8_row17_col0, #T_710c8_row17_col1 {
  text-align: left;
}
#T_710c8_row0_col2, #T_710c8_row0_col3, #T_710c8_row0_col4, #T_710c8_row1_col2, #T_710c8_row1_col3, #T_710c8_row1_col4, #T_710c8_row2_col2, #T_710c8_row2_col3, #T_710c8_row2_col4, #T_710c8_row3_col2, #T_710c8_row3_col3, #T_710c8_row3_col4, #T_710c8_row4_col2, #T_710c8_row4_col3, #T_710c8_row4_col4, #T_710c8_row5_col2, #T_710c8_row5_col3, #T_710c8_row5_col4, #T_710c8_row6_col2, #T_710c8_row6_col3, #T_710c8_row6_col4, #T_710c8_row7_col2, #T_710c8_row7_col3, #T_710c8_row7_col4, #T_710c8_row8_col2, #T_710c8_row8_col3, #T_710c8_row8_col4, #T_710c8_row9_col2, #T_710c8_row9_col3, #T_710c8_row9_col4, #T_710c8_row10_col2, #T_710c8_row10_col3, #T_710c8_row10_col4, #T_710c8_row11_col2, #T_710c8_row11_col3, #T_710c8_row11_col4, #T_710c8_row12_col2, #T_710c8_row12_col3, #T_710c8_row12_col4, #T_710c8_row13_col2, #T_710c8_row13_col3, #T_710c8_row13_col4, #T_710c8_row14_col2, #T_710c8_row14_col3, #T_710c8_row14_col4, #T_710c8_row15_col2, #T_710c8_row15_col3, #T_710c8_row15_col4, #T_710c8_row16_col2, #T_710c8_row16_col3, #T_710c8_row16_col4, #T_710c8_row17_col2, #T_710c8_row17_col3, #T_710c8_row17_col4 {
  text-align: right;
}
</style>
<table id="T_710c8">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_710c8_level0_col0" class="col_heading level0 col0" >Line</th>
      <th id="T_710c8_level0_col1" class="col_heading level0 col1" >Typ</th>
      <th id="T_710c8_level0_col2" class="col_heading level0 col2" >nach Wechsel (2024–2025)</th>
      <th id="T_710c8_level0_col3" class="col_heading level0 col3" >vor Wechsel (2023)</th>
      <th id="T_710c8_level0_col4" class="col_heading level0 col4" >Δ (s)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_710c8_level0_row0" class="row_heading level0 row0" >1</th>
      <td id="T_710c8_row0_col0" class="data row0 col0" >11</td>
      <td id="T_710c8_row0_col1" class="data row0 col1" >✦ verändert (j24)</td>
      <td id="T_710c8_row0_col2" class="data row0 col2" >70.40</td>
      <td id="T_710c8_row0_col3" class="data row0 col3" >65.10</td>
      <td id="T_710c8_row0_col4" class="data row0 col4" >5.30</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row1" class="row_heading level0 row1" >5</th>
      <td id="T_710c8_row1_col0" class="data row1 col0" >15</td>
      <td id="T_710c8_row1_col1" class="data row1 col1" >stabil</td>
      <td id="T_710c8_row1_col2" class="data row1 col2" >63.10</td>
      <td id="T_710c8_row1_col3" class="data row1 col3" >57.90</td>
      <td id="T_710c8_row1_col4" class="data row1 col4" >5.20</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row2" class="row_heading level0 row2" >10</th>
      <td id="T_710c8_row2_col0" class="data row2 col0" >5</td>
      <td id="T_710c8_row2_col1" class="data row2 col1" >stabil</td>
      <td id="T_710c8_row2_col2" class="data row2 col2" >48.00</td>
      <td id="T_710c8_row2_col3" class="data row2 col3" >45.60</td>
      <td id="T_710c8_row2_col4" class="data row2 col4" >2.40</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row3" class="row_heading level0 row3" >14</th>
      <td id="T_710c8_row3_col0" class="data row3 col0" >7</td>
      <td id="T_710c8_row3_col1" class="data row3 col1" >stabil</td>
      <td id="T_710c8_row3_col2" class="data row3 col2" >59.60</td>
      <td id="T_710c8_row3_col3" class="data row3 col3" >57.40</td>
      <td id="T_710c8_row3_col4" class="data row3 col4" >2.20</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row4" class="row_heading level0 row4" >8</th>
      <td id="T_710c8_row4_col0" class="data row4 col0" >3</td>
      <td id="T_710c8_row4_col1" class="data row4 col1" >stabil</td>
      <td id="T_710c8_row4_col2" class="data row4 col2" >54.70</td>
      <td id="T_710c8_row4_col3" class="data row4 col3" >52.60</td>
      <td id="T_710c8_row4_col4" class="data row4 col4" >2.10</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row5" class="row_heading level0 row5" >3</th>
      <td id="T_710c8_row5_col0" class="data row5 col0" >13</td>
      <td id="T_710c8_row5_col1" class="data row5 col1" >✦ verändert (j24)</td>
      <td id="T_710c8_row5_col2" class="data row5 col2" >53.00</td>
      <td id="T_710c8_row5_col3" class="data row5 col3" >51.60</td>
      <td id="T_710c8_row5_col4" class="data row5 col4" >1.40</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row6" class="row_heading level0 row6" >13</th>
      <td id="T_710c8_row6_col0" class="data row6 col0" >6</td>
      <td id="T_710c8_row6_col1" class="data row6 col1" >stabil</td>
      <td id="T_710c8_row6_col2" class="data row6 col2" >38.60</td>
      <td id="T_710c8_row6_col3" class="data row6 col3" >37.90</td>
      <td id="T_710c8_row6_col4" class="data row6 col4" >0.70</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row7" class="row_heading level0 row7" >0</th>
      <td id="T_710c8_row7_col0" class="data row7 col0" >10</td>
      <td id="T_710c8_row7_col1" class="data row7 col1" >stabil</td>
      <td id="T_710c8_row7_col2" class="data row7 col2" >60.10</td>
      <td id="T_710c8_row7_col3" class="data row7 col3" >59.50</td>
      <td id="T_710c8_row7_col4" class="data row7 col4" >0.60</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row8" class="row_heading level0 row8" >6</th>
      <td id="T_710c8_row8_col0" class="data row8 col0" >17</td>
      <td id="T_710c8_row8_col1" class="data row8 col1" >stabil</td>
      <td id="T_710c8_row8_col2" class="data row8 col2" >47.90</td>
      <td id="T_710c8_row8_col3" class="data row8 col3" >47.80</td>
      <td id="T_710c8_row8_col4" class="data row8 col4" >0.10</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_710c8_row9_col0" class="data row9 col0" >4</td>
      <td id="T_710c8_row9_col1" class="data row9 col1" >stabil</td>
      <td id="T_710c8_row9_col2" class="data row9 col2" >57.40</td>
      <td id="T_710c8_row9_col3" class="data row9 col3" >57.50</td>
      <td id="T_710c8_row9_col4" class="data row9 col4" >-0.10</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row10" class="row_heading level0 row10" >7</th>
      <td id="T_710c8_row10_col0" class="data row10 col0" >2</td>
      <td id="T_710c8_row10_col1" class="data row10 col1" >stabil</td>
      <td id="T_710c8_row10_col2" class="data row10 col2" >56.20</td>
      <td id="T_710c8_row10_col3" class="data row10 col3" >56.50</td>
      <td id="T_710c8_row10_col4" class="data row10 col4" >-0.30</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row11" class="row_heading level0 row11" >4</th>
      <td id="T_710c8_row11_col0" class="data row11 col0" >14</td>
      <td id="T_710c8_row11_col1" class="data row11 col1" >stabil</td>
      <td id="T_710c8_row11_col2" class="data row11 col2" >55.10</td>
      <td id="T_710c8_row11_col3" class="data row11 col3" >55.80</td>
      <td id="T_710c8_row11_col4" class="data row11 col4" >-0.70</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row12" class="row_heading level0 row12" >15</th>
      <td id="T_710c8_row12_col0" class="data row12 col0" >8</td>
      <td id="T_710c8_row12_col1" class="data row12 col1" >stabil</td>
      <td id="T_710c8_row12_col2" class="data row12 col2" >59.20</td>
      <td id="T_710c8_row12_col3" class="data row12 col3" >60.80</td>
      <td id="T_710c8_row12_col4" class="data row12 col4" >-1.60</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row13" class="row_heading level0 row13" >2</th>
      <td id="T_710c8_row13_col0" class="data row13 col0" >12</td>
      <td id="T_710c8_row13_col1" class="data row13 col1" >stabil</td>
      <td id="T_710c8_row13_col2" class="data row13 col2" >51.20</td>
      <td id="T_710c8_row13_col3" class="data row13 col3" >53.10</td>
      <td id="T_710c8_row13_col4" class="data row13 col4" >-1.90</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row14" class="row_heading level0 row14" >16</th>
      <td id="T_710c8_row14_col0" class="data row14 col0" >9</td>
      <td id="T_710c8_row14_col1" class="data row14 col1" >✦ verändert (j24)</td>
      <td id="T_710c8_row14_col2" class="data row14 col2" >54.30</td>
      <td id="T_710c8_row14_col3" class="data row14 col3" >58.70</td>
      <td id="T_710c8_row14_col4" class="data row14 col4" >-4.40</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row15" class="row_heading level0 row15" >11</th>
      <td id="T_710c8_row15_col0" class="data row15 col0" >50</td>
      <td id="T_710c8_row15_col1" class="data row15 col1" >stabil</td>
      <td id="T_710c8_row15_col2" class="data row15 col2" >46.60</td>
      <td id="T_710c8_row15_col3" class="data row15 col3" >nan</td>
      <td id="T_710c8_row15_col4" class="data row15 col4" >nan</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row16" class="row_heading level0 row16" >12</th>
      <td id="T_710c8_row16_col0" class="data row16 col0" >51</td>
      <td id="T_710c8_row16_col1" class="data row16 col1" >stabil</td>
      <td id="T_710c8_row16_col2" class="data row16 col2" >41.40</td>
      <td id="T_710c8_row16_col3" class="data row16 col3" >nan</td>
      <td id="T_710c8_row16_col4" class="data row16 col4" >nan</td>
    </tr>
    <tr>
      <th id="T_710c8_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_710c8_row17_col0" class="data row17 col0" >E</td>
      <td id="T_710c8_row17_col1" class="data row17 col1" >stabil</td>
      <td id="T_710c8_row17_col2" class="data row17 col2" >128.10</td>
      <td id="T_710c8_row17_col3" class="data row17 col3" >nan</td>
      <td id="T_710c8_row17_col4" class="data row17 col4" >nan</td>
    </tr>
  </tbody>
</table>



**Legende Vertikale Linien:**
| Linie | Bedeutung |
|:---|:---|
| Rot gestrichelt | Fahrplanwechsel Dez 2023 (j23 → j24) — größte Netzreorganisation im Analysezeitraum |
| Grau gepunktet | Jahreswechsel Jan 2024 / Jan 2025 — zur Orientierung |

**Beobachtung:** Kein erkennbarer Knick oder Sprung bei Jan 2024 (Fahrplanwechsel). Die Zeitreihen für alle Linien verlaufen kontinuierlich über den Wechsel hinweg.

**Veränderte vs. stabile Linien — Δ vor/nach Fahrplanwechsel:**
| Linie | Typ | vor (2023) | nach (2024–25) | Δ |
|:---|:---|---:|---:|---:|
| L11 | ✦ verändert | 65.1s | 70.4s | **+5.3s** |
| L13 | ✦ verändert | 51.6s | 53.0s | +1.4s |
| L9 | ✦ verändert | 58.7s | 54.3s | **−4.4s** |
| L15 | stabil | 57.9s | 63.1s | **+5.2s** |
| L8 | stabil | 52.6s | 54.7s | +2.1s |
| L12 | stabil | 53.1s | 51.2s | −1.9s |

**Kernbefund:** Die veränderten Linien zeigen keine einheitliche Richtung — L11 stieg um +5.3s, L9 verbesserte sich um −4.4s. Noch deutlicher: L15 (stabil, keine GTFS-Änderung) erhöhte sich um +5.2s — praktisch identisch mit L11 (+5.3s). Da stabile und veränderte Linien die gleiche Bandbreite an Veränderungen zeigen, liegt die Quelle der Variation nicht im Netzwechsel selbst, sondern in externen Faktoren (saisonale Muster, Fahrgastzuwachs, Wetter).

**Starkes Finding:** Die VBZ hat den grössten Fahrplanwechsel in der Netzgeschichte ohne erkennbare Verspätungs-Disruption durchgeführt. Der Netzwechsel ist im Delay-Signal nicht sichtbar.

## Einlaufzeit — Performen neue Abschnitte anders?


```python
section_header("Einlaufzeit — neue vs. bestehende Haltestellen")

log("Einlaufzeit Diagramme")
an.plot_ramp_up(changes, lf_all, cfg, ylim=(30, 100))


show_df(an.table_ramp_up(changes, lf_all))

```

    
    [1m[38;2;52;97;141m───  EINLAUFZEIT — NEUE VS. BESTEHENDE HALTESTELLEN  ─────────[0m
    [38;2;52;97;141mEinlaufzeit Diagramme[0m



    
![png](03_analysis_2-network_files/03_analysis_2-network_21_1.png)
    



<style type="text/css">
#T_dd976 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_dd976 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_dd976 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_dd976 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_dd976 tr:hover td {
  background-color: #eef3f8;
}
#T_dd976_row0_col0, #T_dd976_row0_col1, #T_dd976_row0_col2, #T_dd976_row1_col0, #T_dd976_row1_col1, #T_dd976_row1_col2, #T_dd976_row2_col0, #T_dd976_row2_col1, #T_dd976_row2_col2, #T_dd976_row3_col0, #T_dd976_row3_col1, #T_dd976_row3_col2, #T_dd976_row4_col0, #T_dd976_row4_col1, #T_dd976_row4_col2, #T_dd976_row5_col0, #T_dd976_row5_col1, #T_dd976_row5_col2, #T_dd976_row6_col0, #T_dd976_row6_col1, #T_dd976_row6_col2, #T_dd976_row7_col0, #T_dd976_row7_col1, #T_dd976_row7_col2, #T_dd976_row8_col0, #T_dd976_row8_col1, #T_dd976_row8_col2, #T_dd976_row9_col0, #T_dd976_row9_col1, #T_dd976_row9_col2, #T_dd976_row10_col0, #T_dd976_row10_col1, #T_dd976_row10_col2, #T_dd976_row11_col0, #T_dd976_row11_col1, #T_dd976_row11_col2, #T_dd976_row12_col0, #T_dd976_row12_col1, #T_dd976_row12_col2, #T_dd976_row13_col0, #T_dd976_row13_col1, #T_dd976_row13_col2, #T_dd976_row14_col0, #T_dd976_row14_col1, #T_dd976_row14_col2, #T_dd976_row15_col0, #T_dd976_row15_col1, #T_dd976_row15_col2, #T_dd976_row16_col0, #T_dd976_row16_col1, #T_dd976_row16_col2 {
  text-align: right;
}
</style>
<table id="T_dd976">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_dd976_level0_col0" class="col_heading level0 col0" >Bestehende Halte (s)</th>
      <th id="T_dd976_level0_col1" class="col_heading level0 col1" >Neue Halte (s)</th>
      <th id="T_dd976_level0_col2" class="col_heading level0 col2" >Δ neu−best. (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Line</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_dd976_level0_row0" class="row_heading level0 row0" >11</th>
      <td id="T_dd976_row0_col0" class="data row0 col0" >75.70</td>
      <td id="T_dd976_row0_col1" class="data row0 col1" >68.50</td>
      <td id="T_dd976_row0_col2" class="data row0 col2" >-7.20</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row1" class="row_heading level0 row1" >10</th>
      <td id="T_dd976_row1_col0" class="data row1 col0" >57.80</td>
      <td id="T_dd976_row1_col1" class="data row1 col1" >66.50</td>
      <td id="T_dd976_row1_col2" class="data row1 col2" >8.70</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row2" class="row_heading level0 row2" >15</th>
      <td id="T_dd976_row2_col0" class="data row2 col0" >60.80</td>
      <td id="T_dd976_row2_col1" class="data row2 col1" >64.10</td>
      <td id="T_dd976_row2_col2" class="data row2 col2" >3.30</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row3" class="row_heading level0 row3" >8</th>
      <td id="T_dd976_row3_col0" class="data row3 col0" >55.30</td>
      <td id="T_dd976_row3_col1" class="data row3 col1" >63.40</td>
      <td id="T_dd976_row3_col2" class="data row3 col2" >8.10</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row4" class="row_heading level0 row4" >3</th>
      <td id="T_dd976_row4_col0" class="data row4 col0" >53.50</td>
      <td id="T_dd976_row4_col1" class="data row4 col1" >58.80</td>
      <td id="T_dd976_row4_col2" class="data row4 col2" >5.30</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row5" class="row_heading level0 row5" >4</th>
      <td id="T_dd976_row5_col0" class="data row5 col0" >58.20</td>
      <td id="T_dd976_row5_col1" class="data row5 col1" >56.40</td>
      <td id="T_dd976_row5_col2" class="data row5 col2" >-1.80</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row6" class="row_heading level0 row6" >14</th>
      <td id="T_dd976_row6_col0" class="data row6 col0" >54.50</td>
      <td id="T_dd976_row6_col1" class="data row6 col1" >55.70</td>
      <td id="T_dd976_row6_col2" class="data row6 col2" >1.20</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_dd976_row7_col0" class="data row7 col0" >62.80</td>
      <td id="T_dd976_row7_col1" class="data row7 col1" >54.30</td>
      <td id="T_dd976_row7_col2" class="data row7 col2" >-8.50</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row8" class="row_heading level0 row8" >2</th>
      <td id="T_dd976_row8_col0" class="data row8 col0" >56.80</td>
      <td id="T_dd976_row8_col1" class="data row8 col1" >53.50</td>
      <td id="T_dd976_row8_col2" class="data row8 col2" >-3.30</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row9" class="row_heading level0 row9" >13</th>
      <td id="T_dd976_row9_col0" class="data row9 col0" >52.70</td>
      <td id="T_dd976_row9_col1" class="data row9 col1" >53.20</td>
      <td id="T_dd976_row9_col2" class="data row9 col2" >0.50</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row10" class="row_heading level0 row10" >5</th>
      <td id="T_dd976_row10_col0" class="data row10 col0" >45.60</td>
      <td id="T_dd976_row10_col1" class="data row10 col1" >50.70</td>
      <td id="T_dd976_row10_col2" class="data row10 col2" >5.10</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row11" class="row_heading level0 row11" >9</th>
      <td id="T_dd976_row11_col0" class="data row11 col0" >57.40</td>
      <td id="T_dd976_row11_col1" class="data row11 col1" >50.70</td>
      <td id="T_dd976_row11_col2" class="data row11 col2" >-6.70</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row12" class="row_heading level0 row12" >17</th>
      <td id="T_dd976_row12_col0" class="data row12 col0" >49.90</td>
      <td id="T_dd976_row12_col1" class="data row12 col1" >45.40</td>
      <td id="T_dd976_row12_col2" class="data row12 col2" >-4.50</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row13" class="row_heading level0 row13" >50</th>
      <td id="T_dd976_row13_col0" class="data row13 col0" >52.10</td>
      <td id="T_dd976_row13_col1" class="data row13 col1" >40.70</td>
      <td id="T_dd976_row13_col2" class="data row13 col2" >-11.40</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row14" class="row_heading level0 row14" >51</th>
      <td id="T_dd976_row14_col0" class="data row14 col0" >42.80</td>
      <td id="T_dd976_row14_col1" class="data row14 col1" >40.50</td>
      <td id="T_dd976_row14_col2" class="data row14 col2" >-2.30</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row15" class="row_heading level0 row15" >12</th>
      <td id="T_dd976_row15_col0" class="data row15 col0" >51.30</td>
      <td id="T_dd976_row15_col1" class="data row15 col1" >39.70</td>
      <td id="T_dd976_row15_col2" class="data row15 col2" >-11.60</td>
    </tr>
    <tr>
      <th id="T_dd976_level0_row16" class="row_heading level0 row16" >6</th>
      <td id="T_dd976_row16_col0" class="data row16 col0" >38.50</td>
      <td id="T_dd976_row16_col1" class="data row16 col1" >39.10</td>
      <td id="T_dd976_row16_col2" class="data row16 col2" >0.60</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Einlaufzeit-Charts zeigen kein einheitliches Muster — das Ergebnis ist linienabhängig und erklärt sich aus der Lage der Haltestellen.

**Neue vs. bestehende Haltestellen — Ø Delay ab Jan 2024:**
| Linie | Bestehende Halte (s) | Neue Halte (s) | Δ neu−best. |
|:---|---:|---:|---:|
| L11 (verändert) | 75.5 | 68.2 | **−7.3s** (neue besser) |
| L9 (verändert) | 57.4 | 50.8 | **−6.6s** (neue besser) |
| L13 (verändert) | 52.1 | 53.3 | +1.2s (≈ gleich) |
| L10 | 57.6 | 66.4 | **+8.8s** (neue schlechter) |
| L8 | 55.5 | 63.4 | **+7.9s** (neue schlechter) |
| L7 | 62.9 | 54.3 | −8.6s (neue besser) |
| L2 | 56.9 | 53.7 | −3.2s (neue besser) |

**Warum performen die "neuen" L11/L9-Halte besser?**  
L11 und L9 haben im GTFS vor allem Innenstadthalte als "neu" — Paradeplatz, Bellevue, Bürkliplatz, Bahnhof Stadelhofen. Das sind gut ausgebaute, häufig angefahrene Knotenpunkte mit stabiler Infrastruktur. Dass sie besser performen als die "bestehenden" Halte (die eher die Endabschnitte im problematischen K11/K12 abdecken) bestätigt den Befund aus der Stadtkreis-Analyse: Das Randlagen-Problem existiert unabhängig vom Netzwechsel.

**Echte Erweiterungen (L13 Sihlcity, L11 Rehalp):** Für L13 ist Δ ≈ 0 (+1.2s) — die neuen Südabschnitte performen wie der Rest der Linie. Kein Einlauf-Effekt, aber auch kein Einbruch.

**Linien ohne GTFS-Änderung (L10, L8):** Δ +8.8s / +7.9s — die "neuen" GTFS-Shapes dieser Linien führen zufällig durch schlechtere Abschnitte. Kein kausaler Zusammenhang mit echten Streckenerweiterungen.

> **Fazit:** Kein klassischer Einlauf-Effekt nachweisbar. Die Unterschiede sind lagebezogen, nicht zeitbezogen.

## Hotspots & Kaskaden — Kritische Knotenpunkte


```python
section_header("Hotspots & Kaskaden")

log("Hotspot Diagramme")
an.plot_hotspots(changes, lf_all, cfg)

log("Hotspot Tabelle")
show_df(an.table_hotspots(changes, lf_all))

```

    
    [1m[38;2;52;97;141m───  HOTSPOTS & KASKADEN  ────────────────────────────────────[0m
    [38;2;52;97;141mHotspot Diagramme[0m



    
![png](03_analysis_2-network_files/03_analysis_2-network_24_1.png)
    


    [38;2;52;97;141mHotspot Tabelle[0m



<style type="text/css">
#T_72172 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_72172 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_72172 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_72172 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_72172 tr:hover td {
  background-color: #eef3f8;
}
#T_72172_row0_col0, #T_72172_row0_col2, #T_72172_row1_col0, #T_72172_row1_col2, #T_72172_row2_col0, #T_72172_row2_col2, #T_72172_row3_col0, #T_72172_row3_col2, #T_72172_row4_col0, #T_72172_row4_col2, #T_72172_row5_col0, #T_72172_row5_col2, #T_72172_row6_col0, #T_72172_row6_col2, #T_72172_row7_col0, #T_72172_row7_col2, #T_72172_row8_col0, #T_72172_row8_col2, #T_72172_row9_col0, #T_72172_row9_col2, #T_72172_row10_col0, #T_72172_row10_col2, #T_72172_row11_col0, #T_72172_row11_col2, #T_72172_row12_col0, #T_72172_row12_col2, #T_72172_row13_col0, #T_72172_row13_col2, #T_72172_row14_col0, #T_72172_row14_col2, #T_72172_row15_col0, #T_72172_row15_col2, #T_72172_row16_col0, #T_72172_row16_col2, #T_72172_row17_col0, #T_72172_row17_col2, #T_72172_row18_col0, #T_72172_row18_col2, #T_72172_row19_col0, #T_72172_row19_col2 {
  text-align: left;
}
#T_72172_row0_col1, #T_72172_row0_col3, #T_72172_row0_col4, #T_72172_row1_col1, #T_72172_row1_col3, #T_72172_row1_col4, #T_72172_row2_col1, #T_72172_row2_col3, #T_72172_row2_col4, #T_72172_row3_col1, #T_72172_row3_col3, #T_72172_row3_col4, #T_72172_row4_col1, #T_72172_row4_col3, #T_72172_row4_col4, #T_72172_row5_col1, #T_72172_row5_col3, #T_72172_row5_col4, #T_72172_row6_col1, #T_72172_row6_col3, #T_72172_row6_col4, #T_72172_row7_col1, #T_72172_row7_col3, #T_72172_row7_col4, #T_72172_row8_col1, #T_72172_row8_col3, #T_72172_row8_col4, #T_72172_row9_col1, #T_72172_row9_col3, #T_72172_row9_col4, #T_72172_row10_col1, #T_72172_row10_col3, #T_72172_row10_col4, #T_72172_row11_col1, #T_72172_row11_col3, #T_72172_row11_col4, #T_72172_row12_col1, #T_72172_row12_col3, #T_72172_row12_col4, #T_72172_row13_col1, #T_72172_row13_col3, #T_72172_row13_col4, #T_72172_row14_col1, #T_72172_row14_col3, #T_72172_row14_col4, #T_72172_row15_col1, #T_72172_row15_col3, #T_72172_row15_col4, #T_72172_row16_col1, #T_72172_row16_col3, #T_72172_row16_col4, #T_72172_row17_col1, #T_72172_row17_col3, #T_72172_row17_col4, #T_72172_row18_col1, #T_72172_row18_col3, #T_72172_row18_col4, #T_72172_row19_col1, #T_72172_row19_col3, #T_72172_row19_col4 {
  text-align: right;
}
</style>
<table id="T_72172">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_72172_level0_col0" class="col_heading level0 col0" >Stop</th>
      <th id="T_72172_level0_col1" class="col_heading level0 col1" >Linien</th>
      <th id="T_72172_level0_col2" class="col_heading level0 col2" >Linienliste</th>
      <th id="T_72172_level0_col3" class="col_heading level0 col3" >Avg. Delay (s)</th>
      <th id="T_72172_level0_col4" class="col_heading level0 col4" >Beobachtungen</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_72172_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_72172_row0_col0" class="data row0 col0" >Zürich, Central</td>
      <td id="T_72172_row0_col1" class="data row0 col1" >7</td>
      <td id="T_72172_row0_col2" class="data row0 col2" >3, 4, 6, 7, 10, 15, 19</td>
      <td id="T_72172_row0_col3" class="data row0 col3" >49.10</td>
      <td id="T_72172_row0_col4" class="data row0 col4" >1081588</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_72172_row1_col0" class="data row1 col0" >Zürich, Paradeplatz</td>
      <td id="T_72172_row1_col1" class="data row1 col1" >7</td>
      <td id="T_72172_row1_col2" class="data row1 col2" >2, 6, 7, 8, 9, 11, 13</td>
      <td id="T_72172_row1_col3" class="data row1 col3" >49.00</td>
      <td id="T_72172_row1_col4" class="data row1 col4" >1270955</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_72172_row2_col0" class="data row2 col0" >Zürich, Stauffacher</td>
      <td id="T_72172_row2_col1" class="data row2 col1" >6</td>
      <td id="T_72172_row2_col2" class="data row2 col2" >2, 3, 8, 9, 14, 19</td>
      <td id="T_72172_row2_col3" class="data row2 col3" >60.20</td>
      <td id="T_72172_row2_col4" class="data row2 col4" >986075</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_72172_row3_col0" class="data row3 col0" >Zürich, Bürkliplatz</td>
      <td id="T_72172_row3_col1" class="data row3 col1" >5</td>
      <td id="T_72172_row3_col2" class="data row3 col2" >2, 5, 8, 9, 11</td>
      <td id="T_72172_row3_col3" class="data row3 col3" >52.30</td>
      <td id="T_72172_row3_col4" class="data row3 col4" >917620</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_72172_row4_col0" class="data row4 col0" >Zürich, Bahnhofplatz/HB</td>
      <td id="T_72172_row4_col1" class="data row4 col1" >5</td>
      <td id="T_72172_row4_col2" class="data row4 col2" >3, 10, 14, 17, 19</td>
      <td id="T_72172_row4_col3" class="data row4 col3" >46.30</td>
      <td id="T_72172_row4_col4" class="data row4 col4" >474041</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_72172_row5_col0" class="data row5 col0" >Zürich, Bahnhofquai/HB</td>
      <td id="T_72172_row5_col1" class="data row5 col1" >5</td>
      <td id="T_72172_row5_col2" class="data row5 col2" >4, 11, 13, 14, 17</td>
      <td id="T_72172_row5_col3" class="data row5 col3" >53.40</td>
      <td id="T_72172_row5_col4" class="data row5 col4" >880893</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_72172_row6_col0" class="data row6 col0" >Zürich, Milchbuck</td>
      <td id="T_72172_row6_col1" class="data row6 col1" >5</td>
      <td id="T_72172_row6_col2" class="data row6 col2" >7, 9, 10, 14, E</td>
      <td id="T_72172_row6_col3" class="data row6 col3" >61.30</td>
      <td id="T_72172_row6_col4" class="data row6 col4" >747434</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_72172_row7_col0" class="data row7 col0" >Zürich, Haldenegg</td>
      <td id="T_72172_row7_col1" class="data row7 col1" >5</td>
      <td id="T_72172_row7_col2" class="data row7 col2" >6, 7, 10, 15, 19</td>
      <td id="T_72172_row7_col3" class="data row7 col3" >45.40</td>
      <td id="T_72172_row7_col4" class="data row7 col4" >711757</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_72172_row8_col0" class="data row8 col0" >Zürich, Stockerstrasse</td>
      <td id="T_72172_row8_col1" class="data row8 col1" >4</td>
      <td id="T_72172_row8_col2" class="data row8 col2" >6, 7, 8, 13</td>
      <td id="T_72172_row8_col3" class="data row8 col3" >50.70</td>
      <td id="T_72172_row8_col4" class="data row8 col4" >725527</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_72172_row9_col0" class="data row9 col0" >Zürich, Sternen Oerlikon</td>
      <td id="T_72172_row9_col1" class="data row9 col1" >4</td>
      <td id="T_72172_row9_col2" class="data row9 col2" >10, 11, 14, E</td>
      <td id="T_72172_row9_col3" class="data row9 col3" >72.70</td>
      <td id="T_72172_row9_col4" class="data row9 col4" >560800</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_72172_row10_col0" class="data row10 col0" >Zürich, Rennweg</td>
      <td id="T_72172_row10_col1" class="data row10 col1" >4</td>
      <td id="T_72172_row10_col2" class="data row10 col2" >6, 7, 11, 13</td>
      <td id="T_72172_row10_col3" class="data row10 col3" >47.30</td>
      <td id="T_72172_row10_col4" class="data row10 col4" >707367</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_72172_row11_col0" class="data row11 col0" >Zürich, Schaffhauserplatz</td>
      <td id="T_72172_row11_col1" class="data row11 col1" >4</td>
      <td id="T_72172_row11_col2" class="data row11 col2" >7, 11, 14, 15</td>
      <td id="T_72172_row11_col3" class="data row11 col3" >57.00</td>
      <td id="T_72172_row11_col4" class="data row11 col4" >709307</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_72172_row12_col0" class="data row12 col0" >Zürich, Kantonalbank</td>
      <td id="T_72172_row12_col1" class="data row12 col1" >4</td>
      <td id="T_72172_row12_col2" class="data row12 col2" >2, 8, 9, 11</td>
      <td id="T_72172_row12_col3" class="data row12 col3" >51.40</td>
      <td id="T_72172_row12_col4" class="data row12 col4" >738839</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_72172_row13_col0" class="data row13 col0" >Zürich, Bahnhofstrasse/HB</td>
      <td id="T_72172_row13_col1" class="data row13 col1" >4</td>
      <td id="T_72172_row13_col2" class="data row13 col2" >6, 7, 11, 13</td>
      <td id="T_72172_row13_col3" class="data row13 col3" >53.10</td>
      <td id="T_72172_row13_col4" class="data row13 col4" >693209</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_72172_row14_col0" class="data row14 col0" >Zürich, Escher-Wyss-Platz</td>
      <td id="T_72172_row14_col1" class="data row14 col1" >4</td>
      <td id="T_72172_row14_col2" class="data row14 col2" >4, 8, 13, 17</td>
      <td id="T_72172_row14_col3" class="data row14 col3" >49.60</td>
      <td id="T_72172_row14_col4" class="data row14 col4" >756141</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_72172_row15_col0" class="data row15 col0" >Zürich,Kalkbreite/Bhf.Wiedikon</td>
      <td id="T_72172_row15_col1" class="data row15 col1" >3</td>
      <td id="T_72172_row15_col2" class="data row15 col2" >2, 3, 19</td>
      <td id="T_72172_row15_col3" class="data row15 col3" >44.90</td>
      <td id="T_72172_row15_col4" class="data row15 col4" >380694</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_72172_row16_col0" class="data row16 col0" >Zürich, Löwenbräu</td>
      <td id="T_72172_row16_col1" class="data row16 col1" >3</td>
      <td id="T_72172_row16_col2" class="data row16 col2" >4, 13, 17</td>
      <td id="T_72172_row16_col3" class="data row16 col3" >46.10</td>
      <td id="T_72172_row16_col4" class="data row16 col4" >569585</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_72172_row17_col0" class="data row17 col0" >Zürich, Bahnhof Enge</td>
      <td id="T_72172_row17_col1" class="data row17 col1" >3</td>
      <td id="T_72172_row17_col2" class="data row17 col2" >5, 6, 7</td>
      <td id="T_72172_row17_col3" class="data row17 col3" >54.70</td>
      <td id="T_72172_row17_col4" class="data row17 col4" >337655</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_72172_row18_col0" class="data row18 col0" >Zürich, Sihlquai/HB</td>
      <td id="T_72172_row18_col1" class="data row18 col1" >3</td>
      <td id="T_72172_row18_col2" class="data row18 col2" >4, 13, 17</td>
      <td id="T_72172_row18_col3" class="data row18 col3" >46.50</td>
      <td id="T_72172_row18_col4" class="data row18 col4" >570669</td>
    </tr>
    <tr>
      <th id="T_72172_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_72172_row19_col0" class="data row19 col0" >Zürich, Tunnelstrasse</td>
      <td id="T_72172_row19_col1" class="data row19 col1" >3</td>
      <td id="T_72172_row19_col2" class="data row19 col2" >6, 7, 13</td>
      <td id="T_72172_row19_col3" class="data row19 col3" >52.90</td>
      <td id="T_72172_row19_col4" class="data row19 col4" >557710</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Knotenpunkte mit den meisten Linien (Central: 7, Paradeplatz: 7) haben beide einen Ø Delay von ca. 49s — das liegt **unter** dem Gesamtdurchschnitt (~55s).

**Top-Hotspots nach Linienanzahl (j25):**
| Haltestelle | Linien | Ø Delay (s) | Beobachtungen |
|:---|---:|---:|---:|
| Central | 7 | 49.1 | 1 081 588 |
| Paradeplatz | 7 | 49.0 | 1 270 955 |
| Stauffacher | 6 | 60.2 | 986 075 |
| Bahnhofplatz/HB | 5 | 46.3 | 474 041 |
| Bürkliplatz | 5 | 52.3 | 917 620 |
| Bahnhofquai/HB | 5 | 53.4 | 880 893 |
| Milchbuck | 5 | 61.3 | 747 434 |

**Kernbefund:** Es gibt **keine positive Korrelation** zwischen Linienanzahl und Verspätung — das Gegenteil scheint möglich. Die grossen Knotenpunkte (Central, Paradeplatz, Bahnhofplatz) liegen alle unter dem Durchschnitt. Das Kaskadenrisiko-Modell "mehr Linien = mehr Delay" findet in den Daten keine Bestätigung. Höhere Delays entstehen offenbar nicht an den zentralen Umsteigeknoten, sondern anderswo im Netz (→ weiterführend in `03_analysis_4-spatial`).

## Versorgungsqualität — Welche Stadtteile profitieren?


```python
section_header("Versorgungsqualität nach Stadtkreis")

an.plot_service_quality_by_district(lf_all, cfg)

show_df(an.table_service_quality_by_district(lf_all))

an.plot_service_quality_district_map(lf_all)
```

    
    [1m[38;2;52;97;141m───  VERSORGUNGSQUALITÄT NACH STADTKREIS  ────────────────────[0m



    
![png](03_analysis_2-network_files/03_analysis_2-network_27_1.png)
    



<style type="text/css">
#T_c9a53 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_c9a53 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_c9a53 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_c9a53 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_c9a53 tr:hover td {
  background-color: #eef3f8;
}
#T_c9a53_row0_col0, #T_c9a53_row1_col0, #T_c9a53_row2_col0, #T_c9a53_row3_col0, #T_c9a53_row4_col0, #T_c9a53_row5_col0, #T_c9a53_row6_col0, #T_c9a53_row7_col0, #T_c9a53_row8_col0, #T_c9a53_row9_col0, #T_c9a53_row10_col0, #T_c9a53_row11_col0, #T_c9a53_row12_col0 {
  text-align: left;
}
#T_c9a53_row0_col1, #T_c9a53_row0_col2, #T_c9a53_row0_col3, #T_c9a53_row1_col1, #T_c9a53_row1_col2, #T_c9a53_row1_col3, #T_c9a53_row2_col1, #T_c9a53_row2_col2, #T_c9a53_row2_col3, #T_c9a53_row3_col1, #T_c9a53_row3_col2, #T_c9a53_row3_col3, #T_c9a53_row4_col1, #T_c9a53_row4_col2, #T_c9a53_row4_col3, #T_c9a53_row5_col1, #T_c9a53_row5_col2, #T_c9a53_row5_col3, #T_c9a53_row6_col1, #T_c9a53_row6_col2, #T_c9a53_row6_col3, #T_c9a53_row7_col1, #T_c9a53_row7_col2, #T_c9a53_row7_col3, #T_c9a53_row8_col1, #T_c9a53_row8_col2, #T_c9a53_row8_col3, #T_c9a53_row9_col1, #T_c9a53_row9_col2, #T_c9a53_row9_col3, #T_c9a53_row10_col1, #T_c9a53_row10_col2, #T_c9a53_row10_col3, #T_c9a53_row11_col1, #T_c9a53_row11_col2, #T_c9a53_row11_col3, #T_c9a53_row12_col1, #T_c9a53_row12_col2, #T_c9a53_row12_col3 {
  text-align: right;
}
</style>
<table id="T_c9a53">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_c9a53_level0_col0" class="col_heading level0 col0" >district_name</th>
      <th id="T_c9a53_level0_col1" class="col_heading level0 col1" >lines_j23</th>
      <th id="T_c9a53_level0_col2" class="col_heading level0 col2" >lines_j25</th>
      <th id="T_c9a53_level0_col3" class="col_heading level0 col3" >delta</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_c9a53_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_c9a53_row0_col0" class="data row0 col0" >Kreis 12</td>
      <td id="T_c9a53_row0_col1" class="data row0 col1" >5</td>
      <td id="T_c9a53_row0_col2" class="data row0 col2" >7</td>
      <td id="T_c9a53_row0_col3" class="data row0 col3" >2</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_c9a53_row1_col0" class="data row1 col0" >Kreis 4</td>
      <td id="T_c9a53_row1_col1" class="data row1 col1" >11</td>
      <td id="T_c9a53_row1_col2" class="data row1 col2" >13</td>
      <td id="T_c9a53_row1_col3" class="data row1 col3" >2</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_c9a53_row2_col0" class="data row2 col0" >Kreis 11</td>
      <td id="T_c9a53_row2_col1" class="data row2 col1" >10</td>
      <td id="T_c9a53_row2_col2" class="data row2 col2" >11</td>
      <td id="T_c9a53_row2_col3" class="data row2 col3" >1</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_c9a53_row3_col0" class="data row3 col0" >Kreis 8</td>
      <td id="T_c9a53_row3_col1" class="data row3 col1" >6</td>
      <td id="T_c9a53_row3_col2" class="data row3 col2" >7</td>
      <td id="T_c9a53_row3_col3" class="data row3 col3" >1</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_c9a53_row4_col0" class="data row4 col0" >Kreis 9</td>
      <td id="T_c9a53_row4_col1" class="data row4 col1" >8</td>
      <td id="T_c9a53_row4_col2" class="data row4 col2" >9</td>
      <td id="T_c9a53_row4_col3" class="data row4 col3" >1</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_c9a53_row5_col0" class="data row5 col0" >Kreis 5</td>
      <td id="T_c9a53_row5_col1" class="data row5 col1" >6</td>
      <td id="T_c9a53_row5_col2" class="data row5 col2" >6</td>
      <td id="T_c9a53_row5_col3" class="data row5 col3" >0</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_c9a53_row6_col0" class="data row6 col0" >Kreis 2</td>
      <td id="T_c9a53_row6_col1" class="data row6 col1" >12</td>
      <td id="T_c9a53_row6_col2" class="data row6 col2" >12</td>
      <td id="T_c9a53_row6_col3" class="data row6 col3" >0</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_c9a53_row7_col0" class="data row7 col0" >Kreis 1</td>
      <td id="T_c9a53_row7_col1" class="data row7 col1" >14</td>
      <td id="T_c9a53_row7_col2" class="data row7 col2" >14</td>
      <td id="T_c9a53_row7_col3" class="data row7 col3" >0</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_c9a53_row8_col0" class="data row8 col0" >Kreis 3</td>
      <td id="T_c9a53_row8_col1" class="data row8 col1" >10</td>
      <td id="T_c9a53_row8_col2" class="data row8 col2" >10</td>
      <td id="T_c9a53_row8_col3" class="data row8 col3" >0</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_c9a53_row9_col0" class="data row9 col0" >Kreis 10</td>
      <td id="T_c9a53_row9_col1" class="data row9 col1" >4</td>
      <td id="T_c9a53_row9_col2" class="data row9 col2" >3</td>
      <td id="T_c9a53_row9_col3" class="data row9 col3" >-1</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_c9a53_row10_col0" class="data row10 col0" >Kreis 6</td>
      <td id="T_c9a53_row10_col1" class="data row10 col1" >14</td>
      <td id="T_c9a53_row10_col2" class="data row10 col2" >13</td>
      <td id="T_c9a53_row10_col3" class="data row10 col3" >-1</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_c9a53_row11_col0" class="data row11 col0" >outside</td>
      <td id="T_c9a53_row11_col1" class="data row11 col1" >6</td>
      <td id="T_c9a53_row11_col2" class="data row11 col2" >5</td>
      <td id="T_c9a53_row11_col3" class="data row11 col3" >-1</td>
    </tr>
    <tr>
      <th id="T_c9a53_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_c9a53_row12_col0" class="data row12 col0" >Kreis 7</td>
      <td id="T_c9a53_row12_col1" class="data row12 col1" >11</td>
      <td id="T_c9a53_row12_col2" class="data row12 col2" >9</td>
      <td id="T_c9a53_row12_col3" class="data row12 col3" >-2</td>
    </tr>
  </tbody>
</table>





    python(24153) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.




**Beobachtung:** Der Chart zeigt die Veränderung der Linien-Anbindung pro Stadtkreis (Δ Anzahl verschiedener Linien, 2025 vs. 2023).

**Δ Linien pro Stadtkreis (j23 → j25):**
| Stadtkreis | j23 | j25 | Δ |
|:---|---:|---:|---:|
| Kreis 12 | 5 | 7 | **+2** |
| Kreis 4 | 11 | 13 | **+2** |
| Kreis 9 | 8 | 9 | +1 |
| Kreis 11 | 10 | 11 | +1 |
| Kreis 8 | 6 | 7 | +1 |
| Kreise 1, 2, 3, 5 | — | — | 0 |
| Kreis 10 | 4 | 3 | −1 |
| Kreis 6 | 14 | 13 | −1 |
| Kreis 7 | 11 | 9 | **−2** |

**Wichtiger Kontrast zu Stadtkreis-Chart oben:** Kreis 1 erhielt die meisten neuen Haltestellen (12), aber **null neue Linien** — die Innenstadt wird von denselben Linien bedient, die nun mehr Halte haben. Echte Anbindungs-Verbesserungen (neue Linien) liegen vor allem in Kreis 12 und Kreis 4.

**Verlierer:** Kreis 7 verliert 2 Linien (11→9). Kreis 6 und Kreis 10 verlieren je 1 Linie. Die Versorgungsqualität dieser Kreise hat sich im Betrachtungszeitraum verschlechtert.

## Liniencharakter-Profil — Strukturelle Kennzahlen im Vergleich

Jede Linie hat ein unverwechselbares strukturelles Profil. Fünf Dimensionen im Überblick:

| Dimension | Was sie zeigt |
|:---|:---|
| **Ø Halte / Fahrt** | Routenlänge — je länger, desto mehr Accumulation-Potenzial |
| **Stadtkreise (Anzahl)** | Geografische Reichweite — wie viele verschiedene Kreise werden durchfahren? |
| **Innenstadt-Anteil (%)** | Anteil Halte in Kreisen 1–5 — Exposition zur Innenstadtbelastung |
| **Strukturfaktor (s/Fahrt)** | Ø delay_delta × avg_stops — kumulierter Delay-Aufbau pro Fahrt |
| **Ø Arrival Delay (s)** | Sichtbares Ergebnis für Fahrgäste am Ende |

Heatmap: **Farbe normalisiert pro Spalte** — Dunkel = hoher Wert · Hell = niedriger Wert · Linienbeschriftung in VBZ-Farben.


```python
an.plot_line_profiles(lf_all)
```

    Tram Line Metrics — 5 dimensions per line:
      avg_stops           — avg stops per trip (route length)
      n_districts         — districts served (geographic reach)
      pct_city_center     — share of stops in districts 1–5 (city centre exposure)
      structural_per_trip — avg (departure_delay − arrival_delay) × avg_stops (cumulative build-up)
      mean_arr            — avg arrival delay (passenger-visible outcome)
    Color normalized per column — dark = high value · sorted by structural factor.



    
![png](03_analysis_2-network_files/03_analysis_2-network_30_1.png)
    


## Fazit & Rückschluss auf die weitere Analyse

### Was die Netzanalyse für alle weiteren Notebooks bedeutet

Die GTFS-Analyse über 2023, 2024 und 2025 ergibt folgende strukturelle Erkenntnisse:

#### Verändertes Teilnetz — Jahresvergleich mit Vorbehalt
| Linie | j23 | j24 | j25 | Kontext |
| :---: | ---: | ---: | ---: | :--- |
| **9** | 24 Halte | 32 Halte | 32 Halte | +8 neue Abschnitte ab Dez 2023 |
| **11** | 20 Halte | 33 Halte | 34 Halte | +13 neue Abschnitte ab Dez 2023 |
| **13** | 11 Halte | 30 Halte | 30 Halte | +19 Halte (+173%) ab Dez 2023 |

Für diese Linien ist Linie 9 in 2023 strukturell eine **andere** Linie als Linie 9 in 2024–2025.

> **⚠️ Externe Recherche-Korrektur (Perplexity, Mai 2026):**
> Die VBZ-Medienmitteilung zum Fahrplanwechsel Dez 2023 nennt **keine formalen Streckenumbauten** für Tramlinien 9, 11, 13 — die ausgewiesenen Änderungen betrafen primär Buslinien. Die GTFS-Unterschiede könnten daher sein:
> - **Flexity-Rollout**: neue Fahrzeuge auf Linien 11/13 → präzisere Haltestellenaufzeichnung im GTFS
> - **Takt-/Umlaufänderungen**: mehr Kurse, andere Wendeäste → neue Stop-IDs im GTFS
> - **GTFS-Modellierungsartefakt**: Fahrplankopplungen die als neue Halte erscheinen
>
> Das bedeutet: Die "+173%" bei Linie 13 sind real im GTFS-Datensatz sichtbar, aber die Ursache ist unklar. Das `gtfs_year`-Feature ist trotzdem valide — es kodiert einen echten Zeitschnitt. Ob es Netzstruktur oder nur einen Zeiteffekt erfasst, zeigt der Modellvergleich.

#### Stabiles Referenznetz
Linien mit identischer Stoppanzahl j23 = j24 = j25: **L10, L12, L14, L17** — diese können jahresübergreifend direkt verglichen werden ohne Strukturbruch.

#### Das `gtfs_year`-Feature — kritische Bewertung

```python
# In 02_preparation.ipynb hinzufügen:
pl.when(pl.col("operating_date") < pl.lit("2024-01-01").str.to_date())
  .then(pl.lit("j23"))
  .otherwise(pl.lit("j24_j25"))
  .alias("gtfs_year")
```

**Was es codiert:** Den Zeitschnitt Dez 2023 — für Linien 9, 11, 13 gibt es im GTFS einen markanten Unterschied. Ob das eine echte Streckenänderung oder ein Modellierungsartefakt ist, ist offen.

**Limitierung:** Für strukturell stabile Linien ist `gtfs_year` eine reine Zeitvariable ohne Netz-Kontext. Ob es tatsächlich die Modellleistung verbessert, **muss empirisch getestet werden**.

**Alternative:** `n_stops_line` als kontinuierliches Signal — trifft den gleichen Sachverhalt, ohne die binäre Vereinfachung.

**Entscheidung:** Feature als Kandidat aufnehmen, im Modellvergleich evaluieren.

#### Hinweis für alle Analysis-Notebooks
> Alle Analysen in `03_analysis_4-spatial`, `03_analysis_3-temporal`, `03_analysis_5-meteo` und `03_analysis_6-events`
> sollten bei Linien-bezogenen Befunden den Netzwechsel Dezember 2023 als Kontextinformation nennen.
> Detaillierte Aufschlüsselung immer mit Verweis auf dieses Notebook: `03_analysis_2-network.ipynb`.

---

#### ✅ Kaskadenanalyse mit `trip_id` (F-NET-07) — implementiert in LightGBM v2

Eine wichtige Folgefrage aus der Target-Analyse: **Wenn ein Trip mit Verspätung endet — startet der nächste Trip (selbes Fahrzeug, andere Richtung) dann ebenfalls zu spät?**

> **Wie die Analyse funktioniert:**
> VBZ plant an den Endpunkten Wendezeit ein (typisch 5–10 Min). Bei moderaten Verspätungen wird diese Wendezeit aufgebraucht und der nächste Trip startet pünktlich. Bei Extremverspätungen (> Wendezeit) kann die Verspätung auf den nächsten Trip übertragen werden — das ist der Kaskadeneffekt.
>
> Mit `trip_id` und der Sortierung nach `operating_date` + `stop_sequence` lässt sich für jeden Trip der letzte Stop-Delay extrahieren und mit dem ersten Stop-Delay des Nachfolge-Trips vergleichen.

**Warum das für die Modellierung wichtig ist:**
Ein Feature `prev_trip_end_delay` (Verspätung am Ende des vorherigen Trips) wäre ein starkes Vorhersage-Signal — insbesondere in den Abendstunden wenn sich Verspätungen aufschaukeln. Das könnte den 21h-Peak aus F-TEMP-01 teilweise erklären.

```python
# Skizze für 02_preparation oder Modellierungsphase:
# trip_end_delay = lf.group_by("trip_id").agg(
#     pl.col("arrival_delay").last().alias("trip_end_delay")
# )
# → join mit nächstem Trip über Fahrzeug-ID / Umlauf-ID
```

**Status:** Offen — Daten sind vorhanden (`trip_id` im Master-Set), Implementierung ausstehend. → F-NET-07

## Key Findings

→ Vollständige Findings-Tabelle mit Impact und Action in [`03_analysis_0-overview.ipynb`](03_analysis_0-overview.ipynb).

| ID | Finding | Präsentation | Status |
|:---|:---|:---|:---|
| F-NET-01 | Im GTFS zeigen L9/L11/L13 zum Fahrplanwechsel Dez 2023 markante Haltestellen-Zunahmen (+8/+13/+19). Keine formalen Tramstrecken-Umbauten dokumentiert — teils GTFS-Artefakte (neue Trip-Shapes durch Innenstadtachse), teils echte Erweiterungen (L13→Sihlcity, L11→Rehalp). | `story` | done |
| F-NET-02 | Stabile Referenzlinien (L10, L12, L14, L17): identische Haltestellen-Zahl über alle drei Jahre — direkte Jahresvergleiche möglich. Anomalie L2: 31→21→31 Halte (j24-Dip), wahrscheinlich GTFS-Routing-Variante. | `—` | done |
| F-NET-03 | `gtfs_year` Feature (`j23` vs `j24_j25`) kodiert den Zeitschnitt Dez 2023. Ob es Netzstruktur oder Zeiteffekt misst, zeigt der Modellvergleich. | `—` | done |
| F-NET-04 | Kein Einlaufzeit-Effekt nachweisbar: Unterschiede zwischen neuen und bestehenden GTFS-Haltestellen sind lagebedingt, nicht zeitbedingt. L11/L9 "neue" Halte = Innenstadtknoten → besser. L10/L8 "neue" Halte = problembelastete Abschnitte → schlechter. | `—` | done |
| F-NET-05 | Keine positive Korrelation zwischen Linienanzahl und Delay: Knotenpunkte Central und Paradeplatz (je 7 Linien) liegen bei 49s — unter dem Netz-Durchschnitt (~55s). Das Kaskadenrisiko-Modell findet in den Daten keine Bestätigung. | `hot` | done |
| F-NET-06 | Versorgungsqualität (Δ Linien): Kreis 12 (+2) und Kreis 4 (+2) gewinnen am meisten. Kreis 7 verliert 2 Linien. Kreis 1 erhielt die meisten neuen GTFS-Haltestellen (12), aber keine neuen Linien. | `—` | done |
| F-NET-07 | `trip_id` ermöglicht Kaskadenanalyse: Verspätungsübertragung von Fahrt zu Fahrt messbar — als Feature `prev_trip_end_delay` für die Modellierungsphase prüfen. | `—` | done |
| F-NET-08 | **Linie E** ist eine Entlastungs-/Verstärkerlinie mit 128.1s Ø Delay — klarer Ausreisser. Kein Datenfehler; im Modell behalten, aber als Sonderlinie annotieren. | `—` | done |
| F-NET-09 | **Netzausbau vs. Delay-Hotspots — kein Overlap:** Die echten Streckenerweiterungen (L13→Sihlcity K3, L11→Rehalp K8) und GTFS-Reorganisation (K1 Innenstadtachse) fanden in Kreisen statt, die ohnehin gut performen. Die Problemkreise K11 (Schwamendingen) und K12 (Oerlikon) erhielten keine neuen Haltestellen. Das Netz wurde ausgebaut, aber nicht dort wo es am meisten gebraucht würde. | `hot` | done |






