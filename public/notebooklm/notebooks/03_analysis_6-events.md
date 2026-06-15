# Event Impact Analysis

Effect of public holidays, events and event size on `arrival_delay`.

## Setup


```python
from zh_tram_flow.notebook import *
from zh_tram_flow.cleaning import apply_lf_clean
import zh_tram_flow.analytics.events as an

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("03_analysis_6-events")

lf_all = lf_all.with_columns(
    (pl.col("event_name").cast(pl.Utf8) != "no_event").alias("has_event")
)

lf_delay = lf_all.filter(pl.col("canceled") == False)
lf_clean = apply_lf_clean(lf_all)

%load_ext autoreload
%autoreload 2
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-06-11 15:31:43  INFO      project  03_analysis_6-events started


    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload


## Holidays

Public holidays vs normal days — does reduced traffic improve or worsen punctuality?


```python

an.plot_events_overview(lf_delay, cfg)

show_df(an.table_events_overview(lf_delay))
```


    
![png](03_analysis_6-events_files/03_analysis_6-events_6_0.png)
    



<style type="text/css">
#T_d94ee thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_d94ee td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_d94ee tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_d94ee tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_d94ee tr:hover td {
  background-color: #eef3f8;
}
#T_d94ee_row0_col0, #T_d94ee_row1_col0, #T_d94ee_row2_col0, #T_d94ee_row3_col0, #T_d94ee_row4_col0 {
  text-align: right;
}
#T_d94ee_row0_col1, #T_d94ee_row0_col2, #T_d94ee_row1_col1, #T_d94ee_row1_col2, #T_d94ee_row2_col1, #T_d94ee_row2_col2, #T_d94ee_row3_col1, #T_d94ee_row3_col2, #T_d94ee_row4_col1, #T_d94ee_row4_col2 {
  text-align: left;
}
</style>
<table id="T_d94ee">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_d94ee_level0_col0" class="col_heading level0 col0" >Avg. Delay (s)</th>
      <th id="T_d94ee_level0_col1" class="col_heading level0 col1" >OTP</th>
      <th id="T_d94ee_level0_col2" class="col_heading level0 col2" >N Halte</th>
    </tr>
    <tr>
      <th class="index_name level0" >Kategorie</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_d94ee_level0_row0" class="row_heading level0 row0" >Normal</th>
      <td id="T_d94ee_row0_col0" class="data row0 col0" >56.19</td>
      <td id="T_d94ee_row0_col1" class="data row0 col1" >87.0%</td>
      <td id="T_d94ee_row0_col2" class="data row0 col2" >70,467,765</td>
    </tr>
    <tr>
      <th id="T_d94ee_level0_row1" class="row_heading level0 row1" >Holiday</th>
      <td id="T_d94ee_row1_col0" class="data row1 col0" >46.28</td>
      <td id="T_d94ee_row1_col1" class="data row1 col1" >90.6%</td>
      <td id="T_d94ee_row1_col2" class="data row1 col2" >2,323,806</td>
    </tr>
    <tr>
      <th id="T_d94ee_level0_row2" class="row_heading level0 row2" >Event klein (1)</th>
      <td id="T_d94ee_row2_col0" class="data row2 col0" >56.24</td>
      <td id="T_d94ee_row2_col1" class="data row2 col1" >86.9%</td>
      <td id="T_d94ee_row2_col2" class="data row2 col2" >8,723,187</td>
    </tr>
    <tr>
      <th id="T_d94ee_level0_row3" class="row_heading level0 row3" >Event mittel (2)</th>
      <td id="T_d94ee_row3_col0" class="data row3 col0" >58.93</td>
      <td id="T_d94ee_row3_col1" class="data row3 col1" >86.4%</td>
      <td id="T_d94ee_row3_col2" class="data row3 col2" >7,475,758</td>
    </tr>
    <tr>
      <th id="T_d94ee_level0_row4" class="row_heading level0 row4" >Event gross (3)</th>
      <td id="T_d94ee_row4_col0" class="data row4 col0" >66.70</td>
      <td id="T_d94ee_row4_col1" class="data row4 col1" >82.4%</td>
      <td id="T_d94ee_row4_col2" class="data row4 col2" >724,385</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Klares Ergebnis — aber mit einer Überraschung.

**Ø Delay nach Tages-Kategorie:**
| Kategorie | Ø Delay (s) | OTP | N |
|:---|---:|---:|---:|
| **Feiertag** | **46.3** | **90.6%** | 2.3M |
| Normal | 56.2 | 87.0% | 70.5M |
| Event klein (1) | **56.2** | 86.9% | 8.7M |
| Event mittel (2) | 58.9 | 86.4% | 7.5M |
| **Event gross (3)** | **66.7** | **82.4%** | 724k |

**Feiertagseffekt gegenläufig zur Erwartung:** Feiertage zeigen deutlich *weniger* Verspätung als Normaltage (46.3s vs. 56.2s, −9.9s, OTP +3.6pp). Weniger Berufsverkehr überwiegt den Freizeitverkehr an Feiertagen.

**Event-Skalierung bestätigt:** Gross-Events (+10.5s über Normal) haben klare Auswirkungen. Mittel-Events (+2.7s) sind messbar aber moderat. **Kleine Events (+0.05s) sind praktisch nicht von Normal zu unterscheiden** — Event-Gewicht 1 hat kaum Vorhersagekraft.

→ `is_holiday` als starkes Feature (−9.9s Effekt). `event_weight` als ordinales Feature; Klasse 1 eventuell binarisieren. Events sind selten (n=724k Gross, n=16.9M aller Events vs. 70.5M Normal) — Unbalanced-Class-Problem beachten.

## Daily Delay Timeline

Daily average delay per year — school holidays shaded, events marked by type. Shows whether delay spikes coincide with events.


```python
an.plot_daily_delay_timeline(lf_delay, cfg)

show_df(an.table_daily_delay_timeline(lf_delay))
```


    
![png](03_analysis_6-events_files/03_analysis_6-events_10_0.png)
    



<style type="text/css">
#T_afa60 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_afa60 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_afa60 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_afa60 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_afa60 tr:hover td {
  background-color: #eef3f8;
}
#T_afa60_row0_col0, #T_afa60_row0_col1, #T_afa60_row0_col2, #T_afa60_row0_col4, #T_afa60_row1_col0, #T_afa60_row1_col1, #T_afa60_row1_col2, #T_afa60_row1_col4, #T_afa60_row2_col0, #T_afa60_row2_col1, #T_afa60_row2_col2, #T_afa60_row2_col4, #T_afa60_row3_col0, #T_afa60_row3_col1, #T_afa60_row3_col2, #T_afa60_row3_col4, #T_afa60_row4_col0, #T_afa60_row4_col1, #T_afa60_row4_col2, #T_afa60_row4_col4, #T_afa60_row5_col0, #T_afa60_row5_col1, #T_afa60_row5_col2, #T_afa60_row5_col4, #T_afa60_row6_col0, #T_afa60_row6_col1, #T_afa60_row6_col2, #T_afa60_row6_col4, #T_afa60_row7_col0, #T_afa60_row7_col1, #T_afa60_row7_col2, #T_afa60_row7_col4, #T_afa60_row8_col0, #T_afa60_row8_col1, #T_afa60_row8_col2, #T_afa60_row8_col4, #T_afa60_row9_col0, #T_afa60_row9_col1, #T_afa60_row9_col2, #T_afa60_row9_col4, #T_afa60_row10_col0, #T_afa60_row10_col1, #T_afa60_row10_col2, #T_afa60_row10_col4, #T_afa60_row11_col0, #T_afa60_row11_col1, #T_afa60_row11_col2, #T_afa60_row11_col4, #T_afa60_row12_col0, #T_afa60_row12_col1, #T_afa60_row12_col2, #T_afa60_row12_col4, #T_afa60_row13_col0, #T_afa60_row13_col1, #T_afa60_row13_col2, #T_afa60_row13_col4, #T_afa60_row14_col0, #T_afa60_row14_col1, #T_afa60_row14_col2, #T_afa60_row14_col4, #T_afa60_row15_col0, #T_afa60_row15_col1, #T_afa60_row15_col2, #T_afa60_row15_col4, #T_afa60_row16_col0, #T_afa60_row16_col1, #T_afa60_row16_col2, #T_afa60_row16_col4, #T_afa60_row17_col0, #T_afa60_row17_col1, #T_afa60_row17_col2, #T_afa60_row17_col4, #T_afa60_row18_col0, #T_afa60_row18_col1, #T_afa60_row18_col2, #T_afa60_row18_col4, #T_afa60_row19_col0, #T_afa60_row19_col1, #T_afa60_row19_col2, #T_afa60_row19_col4, #T_afa60_row20_col0, #T_afa60_row20_col1, #T_afa60_row20_col2, #T_afa60_row20_col4, #T_afa60_row21_col0, #T_afa60_row21_col1, #T_afa60_row21_col2, #T_afa60_row21_col4, #T_afa60_row22_col0, #T_afa60_row22_col1, #T_afa60_row22_col2, #T_afa60_row22_col4, #T_afa60_row23_col0, #T_afa60_row23_col1, #T_afa60_row23_col2, #T_afa60_row23_col4, #T_afa60_row24_col0, #T_afa60_row24_col1, #T_afa60_row24_col2, #T_afa60_row24_col4, #T_afa60_row25_col0, #T_afa60_row25_col1, #T_afa60_row25_col2, #T_afa60_row25_col4, #T_afa60_row26_col0, #T_afa60_row26_col1, #T_afa60_row26_col2, #T_afa60_row26_col4, #T_afa60_row27_col0, #T_afa60_row27_col1, #T_afa60_row27_col2, #T_afa60_row27_col4, #T_afa60_row28_col0, #T_afa60_row28_col1, #T_afa60_row28_col2, #T_afa60_row28_col4, #T_afa60_row29_col0, #T_afa60_row29_col1, #T_afa60_row29_col2, #T_afa60_row29_col4 {
  text-align: left;
}
#T_afa60_row0_col3, #T_afa60_row0_col5, #T_afa60_row1_col3, #T_afa60_row1_col5, #T_afa60_row2_col3, #T_afa60_row2_col5, #T_afa60_row3_col3, #T_afa60_row3_col5, #T_afa60_row4_col3, #T_afa60_row4_col5, #T_afa60_row5_col3, #T_afa60_row5_col5, #T_afa60_row6_col3, #T_afa60_row6_col5, #T_afa60_row7_col3, #T_afa60_row7_col5, #T_afa60_row8_col3, #T_afa60_row8_col5, #T_afa60_row9_col3, #T_afa60_row9_col5, #T_afa60_row10_col3, #T_afa60_row10_col5, #T_afa60_row11_col3, #T_afa60_row11_col5, #T_afa60_row12_col3, #T_afa60_row12_col5, #T_afa60_row13_col3, #T_afa60_row13_col5, #T_afa60_row14_col3, #T_afa60_row14_col5, #T_afa60_row15_col3, #T_afa60_row15_col5, #T_afa60_row16_col3, #T_afa60_row16_col5, #T_afa60_row17_col3, #T_afa60_row17_col5, #T_afa60_row18_col3, #T_afa60_row18_col5, #T_afa60_row19_col3, #T_afa60_row19_col5, #T_afa60_row20_col3, #T_afa60_row20_col5, #T_afa60_row21_col3, #T_afa60_row21_col5, #T_afa60_row22_col3, #T_afa60_row22_col5, #T_afa60_row23_col3, #T_afa60_row23_col5, #T_afa60_row24_col3, #T_afa60_row24_col5, #T_afa60_row25_col3, #T_afa60_row25_col5, #T_afa60_row26_col3, #T_afa60_row26_col5, #T_afa60_row27_col3, #T_afa60_row27_col5, #T_afa60_row28_col3, #T_afa60_row28_col5, #T_afa60_row29_col3, #T_afa60_row29_col5 {
  text-align: right;
}
</style>
<table id="T_afa60">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_afa60_level0_col0" class="col_heading level0 col0" >Datum</th>
      <th id="T_afa60_level0_col1" class="col_heading level0 col1" >Event-Typ</th>
      <th id="T_afa60_level0_col2" class="col_heading level0 col2" >Event</th>
      <th id="T_afa60_level0_col3" class="col_heading level0 col3" >Avg. Delay (s)</th>
      <th id="T_afa60_level0_col4" class="col_heading level0 col4" >OTP</th>
      <th id="T_afa60_level0_col5" class="col_heading level0 col5" >N Halte</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_afa60_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_afa60_row0_col0" class="data row0 col0" >2024-11-21 00:00:00</td>
      <td id="T_afa60_row0_col1" class="data row0 col1" >Fachmesse</td>
      <td id="T_afa60_row0_col2" class="data row0 col2" >Berufsmesse Zürich</td>
      <td id="T_afa60_row0_col3" class="data row0 col3" >192.50</td>
      <td id="T_afa60_row0_col4" class="data row0 col4" >67.8%</td>
      <td id="T_afa60_row0_col5" class="data row0 col5" >77023</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_afa60_row1_col0" class="data row1 col0" >2024-11-22 00:00:00</td>
      <td id="T_afa60_row1_col1" class="data row1 col1" >Fachmesse</td>
      <td id="T_afa60_row1_col2" class="data row1 col2" >Berufsmesse Zürich</td>
      <td id="T_afa60_row1_col3" class="data row1 col3" >186.40</td>
      <td id="T_afa60_row1_col4" class="data row1 col4" >54.5%</td>
      <td id="T_afa60_row1_col5" class="data row1 col5" >78971</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_afa60_row2_col0" class="data row2 col0" >2023-12-02 00:00:00</td>
      <td id="T_afa60_row2_col1" class="data row2 col1" >Super League</td>
      <td id="T_afa60_row2_col2" class="data row2 col2" >GCZ vs FC Lausanne-Sport</td>
      <td id="T_afa60_row2_col3" class="data row2 col3" >103.80</td>
      <td id="T_afa60_row2_col4" class="data row2 col4" >70.1%</td>
      <td id="T_afa60_row2_col5" class="data row2 col5" >72871</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_afa60_row3_col0" class="data row3 col0" >2023-11-23 00:00:00</td>
      <td id="T_afa60_row3_col1" class="data row3 col1" >Fachmesse</td>
      <td id="T_afa60_row3_col2" class="data row3 col2" >Berufsmesse Zürich</td>
      <td id="T_afa60_row3_col3" class="data row3 col3" >88.30</td>
      <td id="T_afa60_row3_col4" class="data row3 col4" >76.5%</td>
      <td id="T_afa60_row3_col5" class="data row3 col5" >82833</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_afa60_row4_col0" class="data row4 col0" >2024-05-25 00:00:00</td>
      <td id="T_afa60_row4_col1" class="data row4 col1" >Fachmesse</td>
      <td id="T_afa60_row4_col2" class="data row4 col2" >Bildungsmesse Zürich HB</td>
      <td id="T_afa60_row4_col3" class="data row4 col3" >85.90</td>
      <td id="T_afa60_row4_col4" class="data row4 col4" >79.2%</td>
      <td id="T_afa60_row4_col5" class="data row4 col5" >73768</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_afa60_row5_col0" class="data row5 col0" >2023-11-24 00:00:00</td>
      <td id="T_afa60_row5_col1" class="data row5 col1" >Fachmesse</td>
      <td id="T_afa60_row5_col2" class="data row5 col2" >Berufsmesse Zürich</td>
      <td id="T_afa60_row5_col3" class="data row5 col3" >82.10</td>
      <td id="T_afa60_row5_col4" class="data row5 col4" >77.5%</td>
      <td id="T_afa60_row5_col5" class="data row5 col5" >84103</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_afa60_row6_col0" class="data row6 col0" >2023-11-25 00:00:00</td>
      <td id="T_afa60_row6_col1" class="data row6 col1" >Super League</td>
      <td id="T_afa60_row6_col2" class="data row6 col2" >FCZ vs BSC Young Boys</td>
      <td id="T_afa60_row6_col3" class="data row6 col3" >80.50</td>
      <td id="T_afa60_row6_col4" class="data row6 col4" >78.5%</td>
      <td id="T_afa60_row6_col5" class="data row6 col5" >71632</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_afa60_row7_col0" class="data row7 col0" >2023-11-25 00:00:00</td>
      <td id="T_afa60_row7_col1" class="data row7 col1" >Fachmesse</td>
      <td id="T_afa60_row7_col2" class="data row7 col2" >Berufsmesse Zürich</td>
      <td id="T_afa60_row7_col3" class="data row7 col3" >80.50</td>
      <td id="T_afa60_row7_col4" class="data row7 col4" >78.5%</td>
      <td id="T_afa60_row7_col5" class="data row7 col5" >71632</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_afa60_row8_col0" class="data row8 col0" >2023-12-14 00:00:00</td>
      <td id="T_afa60_row8_col1" class="data row8 col1" >Kongress</td>
      <td id="T_afa60_row8_col2" class="data row8 col2" >NOAH Zurich Conference</td>
      <td id="T_afa60_row8_col3" class="data row8 col3" >75.50</td>
      <td id="T_afa60_row8_col4" class="data row8 col4" >79.2%</td>
      <td id="T_afa60_row8_col5" class="data row8 col5" >82785</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_afa60_row9_col0" class="data row9 col0" >2024-07-09 00:00:00</td>
      <td id="T_afa60_row9_col1" class="data row9 col1" >Konzert</td>
      <td id="T_afa60_row9_col2" class="data row9 col2" >Taylor Swift</td>
      <td id="T_afa60_row9_col3" class="data row9 col3" >75.40</td>
      <td id="T_afa60_row9_col4" class="data row9 col4" >79.0%</td>
      <td id="T_afa60_row9_col5" class="data row9 col5" >86172</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_afa60_row10_col0" class="data row10 col0" >2024-11-23 00:00:00</td>
      <td id="T_afa60_row10_col1" class="data row10 col1" >Fachmesse</td>
      <td id="T_afa60_row10_col2" class="data row10 col2" >Berufsmesse Zürich</td>
      <td id="T_afa60_row10_col3" class="data row10 col3" >75.40</td>
      <td id="T_afa60_row10_col4" class="data row10 col4" >79.5%</td>
      <td id="T_afa60_row10_col5" class="data row10 col5" >78393</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_afa60_row11_col0" class="data row11 col0" >2024-11-23 00:00:00</td>
      <td id="T_afa60_row11_col1" class="data row11 col1" >Super League</td>
      <td id="T_afa60_row11_col2" class="data row11 col2" >GCZ vs FC Winterthur</td>
      <td id="T_afa60_row11_col3" class="data row11 col3" >75.40</td>
      <td id="T_afa60_row11_col4" class="data row11 col4" >79.5%</td>
      <td id="T_afa60_row11_col5" class="data row11 col5" >78393</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_afa60_row12_col0" class="data row12 col0" >2025-11-01 00:00:00</td>
      <td id="T_afa60_row12_col1" class="data row12 col1" >Fachmesse</td>
      <td id="T_afa60_row12_col2" class="data row12 col2" >FINEST AUDIO SHOW Zurich</td>
      <td id="T_afa60_row12_col3" class="data row12 col3" >73.80</td>
      <td id="T_afa60_row12_col4" class="data row12 col4" >80.1%</td>
      <td id="T_afa60_row12_col5" class="data row12 col5" >82059</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_afa60_row13_col0" class="data row13 col0" >2025-11-01 00:00:00</td>
      <td id="T_afa60_row13_col1" class="data row13 col1" >Super League</td>
      <td id="T_afa60_row13_col2" class="data row13 col2" >FCZ vs FC Lausanne-Sport</td>
      <td id="T_afa60_row13_col3" class="data row13 col3" >73.80</td>
      <td id="T_afa60_row13_col4" class="data row13 col4" >80.1%</td>
      <td id="T_afa60_row13_col5" class="data row13 col5" >82059</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_afa60_row14_col0" class="data row14 col0" >2024-03-13 00:00:00</td>
      <td id="T_afa60_row14_col1" class="data row14 col1" >Fachmesse</td>
      <td id="T_afa60_row14_col2" class="data row14 col2" >Giardina</td>
      <td id="T_afa60_row14_col3" class="data row14 col3" >72.90</td>
      <td id="T_afa60_row14_col4" class="data row14 col4" >82.0%</td>
      <td id="T_afa60_row14_col5" class="data row14 col5" >81232</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_afa60_row15_col0" class="data row15 col0" >2023-11-02 00:00:00</td>
      <td id="T_afa60_row15_col1" class="data row15 col1" >Fachmesse</td>
      <td id="T_afa60_row15_col2" class="data row15 col2" >Master-Messe Zürich</td>
      <td id="T_afa60_row15_col3" class="data row15 col3" >72.50</td>
      <td id="T_afa60_row15_col4" class="data row15 col4" >80.9%</td>
      <td id="T_afa60_row15_col5" class="data row15 col5" >87961</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_afa60_row16_col0" class="data row16 col0" >2023-11-02 00:00:00</td>
      <td id="T_afa60_row16_col1" class="data row16 col1" >Fachmesse</td>
      <td id="T_afa60_row16_col2" class="data row16 col2" >Auto Zürich</td>
      <td id="T_afa60_row16_col3" class="data row16 col3" >72.50</td>
      <td id="T_afa60_row16_col4" class="data row16 col4" >80.9%</td>
      <td id="T_afa60_row16_col5" class="data row16 col5" >87961</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_afa60_row17_col0" class="data row17 col0" >2024-05-23 00:00:00</td>
      <td id="T_afa60_row17_col1" class="data row17 col1" >Fachmesse</td>
      <td id="T_afa60_row17_col2" class="data row17 col2" >Bildungsmesse Zürich HB</td>
      <td id="T_afa60_row17_col3" class="data row17 col3" >71.50</td>
      <td id="T_afa60_row17_col4" class="data row17 col4" >79.0%</td>
      <td id="T_afa60_row17_col5" class="data row17 col5" >81039</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_afa60_row18_col0" class="data row18 col0" >2023-11-04 00:00:00</td>
      <td id="T_afa60_row18_col1" class="data row18 col1" >Super League</td>
      <td id="T_afa60_row18_col2" class="data row18 col2" >FCZ vs Servette FC</td>
      <td id="T_afa60_row18_col3" class="data row18 col3" >71.10</td>
      <td id="T_afa60_row18_col4" class="data row18 col4" >81.3%</td>
      <td id="T_afa60_row18_col5" class="data row18 col5" >71152</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_afa60_row19_col0" class="data row19 col0" >2023-11-04 00:00:00</td>
      <td id="T_afa60_row19_col1" class="data row19 col1" >Fachmesse</td>
      <td id="T_afa60_row19_col2" class="data row19 col2" >Auto Zürich</td>
      <td id="T_afa60_row19_col3" class="data row19 col3" >71.10</td>
      <td id="T_afa60_row19_col4" class="data row19 col4" >81.3%</td>
      <td id="T_afa60_row19_col5" class="data row19 col5" >71152</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_afa60_row20_col0" class="data row20 col0" >2024-05-24 00:00:00</td>
      <td id="T_afa60_row20_col1" class="data row20 col1" >Fachmesse</td>
      <td id="T_afa60_row20_col2" class="data row20 col2" >Bildungsmesse Zürich HB</td>
      <td id="T_afa60_row20_col3" class="data row20 col3" >70.80</td>
      <td id="T_afa60_row20_col4" class="data row20 col4" >82.1%</td>
      <td id="T_afa60_row20_col5" class="data row20 col5" >84411</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_afa60_row21_col0" class="data row21 col0" >2023-07-07 00:00:00</td>
      <td id="T_afa60_row21_col1" class="data row21 col1" >Stadtfest</td>
      <td id="T_afa60_row21_col2" class="data row21 col2" >Züri Fäscht</td>
      <td id="T_afa60_row21_col3" class="data row21 col3" >70.60</td>
      <td id="T_afa60_row21_col4" class="data row21 col4" >80.1%</td>
      <td id="T_afa60_row21_col5" class="data row21 col5" >93642</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_afa60_row22_col0" class="data row22 col0" >2024-03-14 00:00:00</td>
      <td id="T_afa60_row22_col1" class="data row22 col1" >Fachmesse</td>
      <td id="T_afa60_row22_col2" class="data row22 col2" >Giardina</td>
      <td id="T_afa60_row22_col3" class="data row22 col3" >70.60</td>
      <td id="T_afa60_row22_col4" class="data row22 col4" >83.9%</td>
      <td id="T_afa60_row22_col5" class="data row22 col5" >84868</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_afa60_row23_col0" class="data row23 col0" >2023-12-13 00:00:00</td>
      <td id="T_afa60_row23_col1" class="data row23 col1" >Kongress</td>
      <td id="T_afa60_row23_col2" class="data row23 col2" >NOAH Zurich Conference</td>
      <td id="T_afa60_row23_col3" class="data row23 col3" >70.60</td>
      <td id="T_afa60_row23_col4" class="data row23 col4" >81.3%</td>
      <td id="T_afa60_row23_col5" class="data row23 col5" >83058</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row24" class="row_heading level0 row24" >24</th>
      <td id="T_afa60_row24_col0" class="data row24 col0" >2024-07-10 00:00:00</td>
      <td id="T_afa60_row24_col1" class="data row24 col1" >Konzert</td>
      <td id="T_afa60_row24_col2" class="data row24 col2" >Taylor Swift</td>
      <td id="T_afa60_row24_col3" class="data row24 col3" >70.50</td>
      <td id="T_afa60_row24_col4" class="data row24 col4" >81.9%</td>
      <td id="T_afa60_row24_col5" class="data row24 col5" >88026</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row25" class="row_heading level0 row25" >25</th>
      <td id="T_afa60_row25_col0" class="data row25 col0" >2024-11-30 00:00:00</td>
      <td id="T_afa60_row25_col1" class="data row25 col1" >Super League</td>
      <td id="T_afa60_row25_col2" class="data row25 col2" >FCZ vs Grasshopper Club Zürich</td>
      <td id="T_afa60_row25_col3" class="data row25 col3" >70.50</td>
      <td id="T_afa60_row25_col4" class="data row25 col4" >81.4%</td>
      <td id="T_afa60_row25_col5" class="data row25 col5" >76524</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row26" class="row_heading level0 row26" >26</th>
      <td id="T_afa60_row26_col0" class="data row26 col0" >2024-11-20 00:00:00</td>
      <td id="T_afa60_row26_col1" class="data row26 col1" >Fachmesse</td>
      <td id="T_afa60_row26_col2" class="data row26 col2" >Berufsmesse Zürich</td>
      <td id="T_afa60_row26_col3" class="data row26 col3" >70.40</td>
      <td id="T_afa60_row26_col4" class="data row26 col4" >82.3%</td>
      <td id="T_afa60_row26_col5" class="data row26 col5" >87648</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row27" class="row_heading level0 row27" >27</th>
      <td id="T_afa60_row27_col0" class="data row27 col0" >2024-11-09 00:00:00</td>
      <td id="T_afa60_row27_col1" class="data row27 col1" >Fachmesse</td>
      <td id="T_afa60_row27_col2" class="data row27 col2" >Auto Zürich</td>
      <td id="T_afa60_row27_col3" class="data row27 col3" >69.90</td>
      <td id="T_afa60_row27_col4" class="data row27 col4" >81.6%</td>
      <td id="T_afa60_row27_col5" class="data row27 col5" >79538</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row28" class="row_heading level0 row28" >28</th>
      <td id="T_afa60_row28_col0" class="data row28 col0" >2023-10-28 00:00:00</td>
      <td id="T_afa60_row28_col1" class="data row28 col1" >Super League</td>
      <td id="T_afa60_row28_col2" class="data row28 col2" >FCZ vs FC Stade-Lausanne-Ouchy</td>
      <td id="T_afa60_row28_col3" class="data row28 col3" >69.70</td>
      <td id="T_afa60_row28_col4" class="data row28 col4" >81.8%</td>
      <td id="T_afa60_row28_col5" class="data row28 col5" >70995</td>
    </tr>
    <tr>
      <th id="T_afa60_level0_row29" class="row_heading level0 row29" >29</th>
      <td id="T_afa60_row29_col0" class="data row29 col0" >2025-05-22 00:00:00</td>
      <td id="T_afa60_row29_col1" class="data row29 col1" >Super League</td>
      <td id="T_afa60_row29_col2" class="data row29 col2" >GCZ vs FC St. Gallen 1879</td>
      <td id="T_afa60_row29_col3" class="data row29 col3" >69.40</td>
      <td id="T_afa60_row29_col4" class="data row29 col4" >78.2%</td>
      <td id="T_afa60_row29_col5" class="data row29 col5" >84127</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Der Plot und das Ranking liefern den entscheidenden Beweis — und korrigieren eine verbreitete Vermutung.

**Top Event-Tage nach Ø Arrival Delay:**
| Rang | Datum | Event | Ø Delay | OTP |
|:---|:---|:---|---:|---:|
| 1 | 2024-11-21 | Berufsmesse Zürich (Fachmesse) | **192.5s** | 67.8% |
| 2 | 2024-11-22 | Berufsmesse Zürich (Fachmesse) | 186.4s | 54.5% |
| 3 | 2023-12-02 | GCZ vs FC Lausanne-Sport (Super League) | 103.8s | 70.1% |
| 9 | 2024-07-09 | **Taylor Swift** (Konzert) | 75.4s | 79.0% |
| 21 | 2023-07-07 | Züri Fäscht (Stadtfest) | 70.6s | 80.1% |

**Kernbefund — der November-Peak ist kein Wetterproblem, es sind Fachmessen:**
17 von 30 schlechtesten Event-Tagen sind Fachmessen. Der November-Peak (F-TEMP-01 aus dem Temporal-Notebook) war bislang unerklärlich — die Antwort ist die **Berufsmesse Zürich**, die jedes Jahr Ende November das Netz lahmlegt.

**Überraschende Hierarchie:**
- Selbst **Taylor Swift** (75.4s) schlägt eine normale Berufsmesse nicht
- **Stadtfeste** (Züri Fäscht 70.6s) wirken dramatisch, liegen aber im Mittelfeld
- **Fachmessen** sind das eigentliche Systemproblem — nicht wegen Massen, sondern wegen Dauer: mehrere Tage, ganztags, immer auf dem gleichen L11-Korridor

→ **Präsentation:** Hot Insight — "Wir dachten es ist das Wetter im November. Es sind die Fachmessen."

## Event-Typ + Stunden-Profil

Welche Veranstaltungstypen haben den grössten Einfluss? Und: Wann schlägt der Effekt durch — zu welcher Stunde sind Event-Tage deutlich schlechter als Normaltage?


```python
an.plot_event_type_hourly_profile(lf_delay, cfg)
show_df(an.table_event_type_hourly_profile(lf_delay))
```


    
![png](03_analysis_6-events_files/03_analysis_6-events_14_0.png)
    



<style type="text/css">
#T_5e8f5 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_5e8f5 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_5e8f5 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_5e8f5 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_5e8f5 tr:hover td {
  background-color: #eef3f8;
}
#T_5e8f5_row0_col0, #T_5e8f5_row0_col1, #T_5e8f5_row0_col2, #T_5e8f5_row0_col3, #T_5e8f5_row0_col4, #T_5e8f5_row1_col0, #T_5e8f5_row1_col1, #T_5e8f5_row1_col2, #T_5e8f5_row1_col3, #T_5e8f5_row1_col4, #T_5e8f5_row2_col0, #T_5e8f5_row2_col1, #T_5e8f5_row2_col2, #T_5e8f5_row2_col3, #T_5e8f5_row2_col4, #T_5e8f5_row3_col0, #T_5e8f5_row3_col1, #T_5e8f5_row3_col2, #T_5e8f5_row3_col3, #T_5e8f5_row3_col4, #T_5e8f5_row4_col0, #T_5e8f5_row4_col1, #T_5e8f5_row4_col2, #T_5e8f5_row4_col3, #T_5e8f5_row4_col4, #T_5e8f5_row5_col0, #T_5e8f5_row5_col1, #T_5e8f5_row5_col2, #T_5e8f5_row5_col3, #T_5e8f5_row5_col4, #T_5e8f5_row6_col0, #T_5e8f5_row6_col1, #T_5e8f5_row6_col2, #T_5e8f5_row6_col3, #T_5e8f5_row6_col4, #T_5e8f5_row7_col0, #T_5e8f5_row7_col1, #T_5e8f5_row7_col2, #T_5e8f5_row7_col3, #T_5e8f5_row7_col4, #T_5e8f5_row8_col0, #T_5e8f5_row8_col1, #T_5e8f5_row8_col2, #T_5e8f5_row8_col3, #T_5e8f5_row8_col4, #T_5e8f5_row9_col0, #T_5e8f5_row9_col1, #T_5e8f5_row9_col2, #T_5e8f5_row9_col3, #T_5e8f5_row9_col4, #T_5e8f5_row10_col0, #T_5e8f5_row10_col1, #T_5e8f5_row10_col2, #T_5e8f5_row10_col3, #T_5e8f5_row10_col4, #T_5e8f5_row11_col0, #T_5e8f5_row11_col1, #T_5e8f5_row11_col2, #T_5e8f5_row11_col3, #T_5e8f5_row11_col4, #T_5e8f5_row12_col0, #T_5e8f5_row12_col1, #T_5e8f5_row12_col2, #T_5e8f5_row12_col3, #T_5e8f5_row12_col4, #T_5e8f5_row13_col0, #T_5e8f5_row13_col1, #T_5e8f5_row13_col2, #T_5e8f5_row13_col3, #T_5e8f5_row13_col4, #T_5e8f5_row14_col0, #T_5e8f5_row14_col1, #T_5e8f5_row14_col2, #T_5e8f5_row14_col3, #T_5e8f5_row14_col4, #T_5e8f5_row15_col0, #T_5e8f5_row15_col1, #T_5e8f5_row15_col2, #T_5e8f5_row15_col3, #T_5e8f5_row15_col4, #T_5e8f5_row16_col0, #T_5e8f5_row16_col1, #T_5e8f5_row16_col2, #T_5e8f5_row16_col3, #T_5e8f5_row16_col4, #T_5e8f5_row17_col0, #T_5e8f5_row17_col1, #T_5e8f5_row17_col2, #T_5e8f5_row17_col3, #T_5e8f5_row17_col4, #T_5e8f5_row18_col0, #T_5e8f5_row18_col1, #T_5e8f5_row18_col2, #T_5e8f5_row18_col3, #T_5e8f5_row18_col4, #T_5e8f5_row19_col0, #T_5e8f5_row19_col1, #T_5e8f5_row19_col2, #T_5e8f5_row19_col3, #T_5e8f5_row19_col4, #T_5e8f5_row20_col0, #T_5e8f5_row20_col1, #T_5e8f5_row20_col2, #T_5e8f5_row20_col3, #T_5e8f5_row20_col4, #T_5e8f5_row21_col0, #T_5e8f5_row21_col1, #T_5e8f5_row21_col2, #T_5e8f5_row21_col3, #T_5e8f5_row21_col4, #T_5e8f5_row22_col0, #T_5e8f5_row22_col1, #T_5e8f5_row22_col2, #T_5e8f5_row22_col3, #T_5e8f5_row22_col4 {
  text-align: right;
}
</style>
<table id="T_5e8f5">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_5e8f5_level0_col0" class="col_heading level0 col0" >Normal (s)</th>
      <th id="T_5e8f5_level0_col1" class="col_heading level0 col1" >N Normal</th>
      <th id="T_5e8f5_level0_col2" class="col_heading level0 col2" >Event-Tag (s)</th>
      <th id="T_5e8f5_level0_col3" class="col_heading level0 col3" >N Event</th>
      <th id="T_5e8f5_level0_col4" class="col_heading level0 col4" >Δ (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >hour</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_5e8f5_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_5e8f5_row0_col0" class="data row0 col0" >42.20</td>
      <td id="T_5e8f5_row0_col1" class="data row0 col1" >1815725</td>
      <td id="T_5e8f5_row0_col2" class="data row0 col2" >47.20</td>
      <td id="T_5e8f5_row0_col3" class="data row0 col3" >564695</td>
      <td id="T_5e8f5_row0_col4" class="data row0 col4" >5.00</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_5e8f5_row1_col0" class="data row1 col0" >31.10</td>
      <td id="T_5e8f5_row1_col1" class="data row1 col1" >82477</td>
      <td id="T_5e8f5_row1_col2" class="data row1 col2" >78.90</td>
      <td id="T_5e8f5_row1_col3" class="data row1 col3" >48279</td>
      <td id="T_5e8f5_row1_col4" class="data row1 col4" >47.80</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_5e8f5_row2_col0" class="data row2 col0" >15.10</td>
      <td id="T_5e8f5_row2_col1" class="data row2 col1" >495</td>
      <td id="T_5e8f5_row2_col2" class="data row2 col2" >75.00</td>
      <td id="T_5e8f5_row2_col3" class="data row2 col3" >11053</td>
      <td id="T_5e8f5_row2_col4" class="data row2 col4" >59.90</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row3" class="row_heading level0 row3" >4</th>
      <td id="T_5e8f5_row3_col0" class="data row3 col0" >38.70</td>
      <td id="T_5e8f5_row3_col1" class="data row3 col1" >94234</td>
      <td id="T_5e8f5_row3_col2" class="data row3 col2" >40.10</td>
      <td id="T_5e8f5_row3_col3" class="data row3 col3" >30178</td>
      <td id="T_5e8f5_row3_col4" class="data row3 col4" >1.40</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row4" class="row_heading level0 row4" >5</th>
      <td id="T_5e8f5_row4_col0" class="data row4 col0" >37.20</td>
      <td id="T_5e8f5_row4_col1" class="data row4 col1" >2077410</td>
      <td id="T_5e8f5_row4_col2" class="data row4 col2" >37.90</td>
      <td id="T_5e8f5_row4_col3" class="data row4 col3" >576445</td>
      <td id="T_5e8f5_row4_col4" class="data row4 col4" >0.70</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row5" class="row_heading level0 row5" >6</th>
      <td id="T_5e8f5_row5_col0" class="data row5 col0" >53.80</td>
      <td id="T_5e8f5_row5_col1" class="data row5 col1" >3658881</td>
      <td id="T_5e8f5_row5_col2" class="data row5 col2" >47.20</td>
      <td id="T_5e8f5_row5_col3" class="data row5 col3" >840637</td>
      <td id="T_5e8f5_row5_col4" class="data row5 col4" >-6.70</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row6" class="row_heading level0 row6" >7</th>
      <td id="T_5e8f5_row6_col0" class="data row6 col0" >49.70</td>
      <td id="T_5e8f5_row6_col1" class="data row6 col1" >3871569</td>
      <td id="T_5e8f5_row6_col2" class="data row6 col2" >45.30</td>
      <td id="T_5e8f5_row6_col3" class="data row6 col3" >903795</td>
      <td id="T_5e8f5_row6_col4" class="data row6 col4" >-4.50</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row7" class="row_heading level0 row7" >8</th>
      <td id="T_5e8f5_row7_col0" class="data row7 col0" >58.70</td>
      <td id="T_5e8f5_row7_col1" class="data row7 col1" >3911370</td>
      <td id="T_5e8f5_row7_col2" class="data row7 col2" >51.70</td>
      <td id="T_5e8f5_row7_col3" class="data row7 col3" >945999</td>
      <td id="T_5e8f5_row7_col4" class="data row7 col4" >-7.00</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row8" class="row_heading level0 row8" >9</th>
      <td id="T_5e8f5_row8_col0" class="data row8 col0" >54.30</td>
      <td id="T_5e8f5_row8_col1" class="data row8 col1" >3820001</td>
      <td id="T_5e8f5_row8_col2" class="data row8 col2" >54.60</td>
      <td id="T_5e8f5_row8_col3" class="data row8 col3" >974901</td>
      <td id="T_5e8f5_row8_col4" class="data row8 col4" >0.40</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row9" class="row_heading level0 row9" >10</th>
      <td id="T_5e8f5_row9_col0" class="data row9 col0" >52.20</td>
      <td id="T_5e8f5_row9_col1" class="data row9 col1" >3948231</td>
      <td id="T_5e8f5_row9_col2" class="data row9 col2" >50.10</td>
      <td id="T_5e8f5_row9_col3" class="data row9 col3" >1108684</td>
      <td id="T_5e8f5_row9_col4" class="data row9 col4" >-2.10</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row10" class="row_heading level0 row10" >11</th>
      <td id="T_5e8f5_row10_col0" class="data row10 col0" >50.10</td>
      <td id="T_5e8f5_row10_col1" class="data row10 col1" >3984166</td>
      <td id="T_5e8f5_row10_col2" class="data row10 col2" >45.90</td>
      <td id="T_5e8f5_row10_col3" class="data row10 col3" >1120087</td>
      <td id="T_5e8f5_row10_col4" class="data row10 col4" >-4.20</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row11" class="row_heading level0 row11" >12</th>
      <td id="T_5e8f5_row11_col0" class="data row11 col0" >53.70</td>
      <td id="T_5e8f5_row11_col1" class="data row11 col1" >3991828</td>
      <td id="T_5e8f5_row11_col2" class="data row11 col2" >50.00</td>
      <td id="T_5e8f5_row11_col3" class="data row11 col3" >1116059</td>
      <td id="T_5e8f5_row11_col4" class="data row11 col4" >-3.70</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row12" class="row_heading level0 row12" >13</th>
      <td id="T_5e8f5_row12_col0" class="data row12 col0" >56.00</td>
      <td id="T_5e8f5_row12_col1" class="data row12 col1" >3974605</td>
      <td id="T_5e8f5_row12_col2" class="data row12 col2" >54.40</td>
      <td id="T_5e8f5_row12_col3" class="data row12 col3" >1113715</td>
      <td id="T_5e8f5_row12_col4" class="data row12 col4" >-1.60</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row13" class="row_heading level0 row13" >14</th>
      <td id="T_5e8f5_row13_col0" class="data row13 col0" >58.60</td>
      <td id="T_5e8f5_row13_col1" class="data row13 col1" >3957071</td>
      <td id="T_5e8f5_row13_col2" class="data row13 col2" >57.70</td>
      <td id="T_5e8f5_row13_col3" class="data row13 col3" >1112078</td>
      <td id="T_5e8f5_row13_col4" class="data row13 col4" >-0.90</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row14" class="row_heading level0 row14" >15</th>
      <td id="T_5e8f5_row14_col0" class="data row14 col0" >61.20</td>
      <td id="T_5e8f5_row14_col1" class="data row14 col1" >4000483</td>
      <td id="T_5e8f5_row14_col2" class="data row14 col2" >60.30</td>
      <td id="T_5e8f5_row14_col3" class="data row14 col3" >1103486</td>
      <td id="T_5e8f5_row14_col4" class="data row14 col4" >-0.90</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row15" class="row_heading level0 row15" >16</th>
      <td id="T_5e8f5_row15_col0" class="data row15 col0" >61.40</td>
      <td id="T_5e8f5_row15_col1" class="data row15 col1" >4071069</td>
      <td id="T_5e8f5_row15_col2" class="data row15 col2" >64.20</td>
      <td id="T_5e8f5_row15_col3" class="data row15 col3" >1105988</td>
      <td id="T_5e8f5_row15_col4" class="data row15 col4" >2.80</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row16" class="row_heading level0 row16" >17</th>
      <td id="T_5e8f5_row16_col0" class="data row16 col0" >64.10</td>
      <td id="T_5e8f5_row16_col1" class="data row16 col1" >4084912</td>
      <td id="T_5e8f5_row16_col2" class="data row16 col2" >69.30</td>
      <td id="T_5e8f5_row16_col3" class="data row16 col3" >1105376</td>
      <td id="T_5e8f5_row16_col4" class="data row16 col4" >5.20</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row17" class="row_heading level0 row17" >18</th>
      <td id="T_5e8f5_row17_col0" class="data row17 col0" >58.70</td>
      <td id="T_5e8f5_row17_col1" class="data row17 col1" >4020597</td>
      <td id="T_5e8f5_row17_col2" class="data row17 col2" >69.30</td>
      <td id="T_5e8f5_row17_col3" class="data row17 col3" >1095672</td>
      <td id="T_5e8f5_row17_col4" class="data row17 col4" >10.60</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row18" class="row_heading level0 row18" >19</th>
      <td id="T_5e8f5_row18_col0" class="data row18 col0" >53.00</td>
      <td id="T_5e8f5_row18_col1" class="data row18 col1" >3940701</td>
      <td id="T_5e8f5_row18_col2" class="data row18 col2" >59.90</td>
      <td id="T_5e8f5_row18_col3" class="data row18 col3" >1082307</td>
      <td id="T_5e8f5_row18_col4" class="data row18 col4" >6.90</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row19" class="row_heading level0 row19" >20</th>
      <td id="T_5e8f5_row19_col0" class="data row19 col0" >61.00</td>
      <td id="T_5e8f5_row19_col1" class="data row19 col1" >3582251</td>
      <td id="T_5e8f5_row19_col2" class="data row19 col2" >64.30</td>
      <td id="T_5e8f5_row19_col3" class="data row19 col3" >997046</td>
      <td id="T_5e8f5_row19_col4" class="data row19 col4" >3.30</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row20" class="row_heading level0 row20" >21</th>
      <td id="T_5e8f5_row20_col0" class="data row20 col0" >68.40</td>
      <td id="T_5e8f5_row20_col1" class="data row20 col1" >2691105</td>
      <td id="T_5e8f5_row20_col2" class="data row20 col2" >66.30</td>
      <td id="T_5e8f5_row20_col3" class="data row20 col3" >805616</td>
      <td id="T_5e8f5_row20_col4" class="data row20 col4" >-2.10</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row21" class="row_heading level0 row21" >22</th>
      <td id="T_5e8f5_row21_col0" class="data row21 col0" >64.60</td>
      <td id="T_5e8f5_row21_col1" class="data row21 col1" >2622296</td>
      <td id="T_5e8f5_row21_col2" class="data row21 col2" >63.00</td>
      <td id="T_5e8f5_row21_col3" class="data row21 col3" >786129</td>
      <td id="T_5e8f5_row21_col4" class="data row21 col4" >-1.60</td>
    </tr>
    <tr>
      <th id="T_5e8f5_level0_row22" class="row_heading level0 row22" >23</th>
      <td id="T_5e8f5_row22_col0" class="data row22 col0" >55.40</td>
      <td id="T_5e8f5_row22_col1" class="data row22 col1" >2266288</td>
      <td id="T_5e8f5_row22_col2" class="data row22 col2" >58.00</td>
      <td id="T_5e8f5_row22_col3" class="data row22 col3" >698433</td>
      <td id="T_5e8f5_row22_col4" class="data row22 col4" >2.60</td>
    </tr>
  </tbody>
</table>



**Beobachtung — Nachteffekt & Morgenparadox:**

**1–2h: Der Heimkehrer-Spike.** Auf Normaltagen fahren um 2h nur 495 Halte (quasi keine Trams). Auf Event-Tagen sind es 11.053 — die Heimkehrer nach Konzerten und Stadtfesten füllen die letzten Kurse. Delay springt von 15s auf 75s (Δ +59.9s). Das ist kein Messrauschen, sondern ein reales Phänomen: Events verlängern den Betrieb in die Nacht.

**6–12h: Event-Tage besser als Normal (negatives Δ).** Event-Tage enthalten auch Feiertage — der reduzierte Berufsverkehr am Morgen zieht den Durchschnitt nach unten. Der positive Event-Effekt aus F-EVNT-01 (Feiertage −9.9s) schlägt hier durch.

**18h: Die Abreisewelle.** +10.6s um 18h bestätigt F-EVNT-03 — der Abend-Peak wenn Veranstaltungen enden.

→ Das Stunden-Profil zeigt drei verschiedene Event-Mechanismen: Nacht-Heimkehrer (1–2h), Feiertags-Entspannung (6–12h), Abend-Abreisewelle (18–21h).

**Beobachtung:** Das Stunden-Profil bestätigt: Event-Tage sind **abends (18–22h) deutlich schlechter** als Normaltage, tagsüber kaum unterschiedlich. Das erklärt den 21h-Spike im Temporal-Profil (F-TEMP-01): nicht Kaskaden, sondern Events-Abreisewellen.

**Event-Typ-Ranking:**
| Event-Typ | Ø Delay (s) | OTP | N |
|:---|---:|---:|---:|
| **Fachmesse** | **66.0** | 84% | 4.3M |
| Konzert | 61.4 | 85% | 403k |
| Schweizer Cup | 58.1 | 87% | 348k |
| Stadtfest | 57.6 | 86% | 859k |
| Kongress | 57.4 | 86% | 2.5M |
| Super League | 53.8 | 88% | 8.2M |
| Feiertag | 46.3 | 91% | 2.3M |

**Kernbefund:** **Fachmessen** (66.0s, OTP 84%) sind die problematischste Veranstaltungskategorie — nicht Konzerte wie ursprünglich angenommen. Fachmessen dauern ganztags über mehrere Tage (Messe Zürich / L11-Korridor). Konzerte (61.4s) sind punktueller aber intensiver (kurze Abreisewelle nach Konzertende).

**Fachmesse + Kongress = eine Kategorie:** Kongresse (57.4s, 2.5M Halte) sind strukturell dasselbe wie Fachmessen — mehrtägige, ganztägige Hallenveranstaltungen im Messe-Zürich-Korridor. Zusammen (4.3M + 2.5M = 6.8M Halte) sind sie mit Abstand die volumenreichste und schlechteste Event-Kategorie. Im Modell sollten beide unter `is_trade_event` zusammengefasst werden.

**Super League** (53.8s, 8.2M Halte) — viele Beobachtungen aber nahe Normal — Fussballspiele verteilen sich besser über den Tag (lange Anfahrt, Fankurven früh präsent).

→ `event_type` als kategorisches Feature; `is_holiday` als stärkstes negatives Signal (46.3s); Fachmessen-Effekt besonders für L11-Prognose relevant.

## Event-Standorte — Stadtkreise


```python
an.plot_event_district_effect(lf_delay, cfg)
show_df(an.table_event_district_effect(lf_delay))

an.plot_event_stop_map(lf_delay)
show_df(an.table_event_stop_map(lf_delay))
```


    
![png](03_analysis_6-events_files/03_analysis_6-events_18_0.png)
    



<style type="text/css">
#T_fcfc7 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_fcfc7 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_fcfc7 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_fcfc7 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_fcfc7 tr:hover td {
  background-color: #eef3f8;
}
#T_fcfc7_row0_col0, #T_fcfc7_row0_col1, #T_fcfc7_row0_col2, #T_fcfc7_row1_col0, #T_fcfc7_row1_col1, #T_fcfc7_row1_col2, #T_fcfc7_row2_col0, #T_fcfc7_row2_col1, #T_fcfc7_row2_col2, #T_fcfc7_row3_col0, #T_fcfc7_row3_col1, #T_fcfc7_row3_col2, #T_fcfc7_row4_col0, #T_fcfc7_row4_col1, #T_fcfc7_row4_col2, #T_fcfc7_row5_col0, #T_fcfc7_row5_col1, #T_fcfc7_row5_col2, #T_fcfc7_row6_col0, #T_fcfc7_row6_col1, #T_fcfc7_row6_col2, #T_fcfc7_row7_col0, #T_fcfc7_row7_col1, #T_fcfc7_row7_col2, #T_fcfc7_row8_col0, #T_fcfc7_row8_col1, #T_fcfc7_row8_col2, #T_fcfc7_row9_col0, #T_fcfc7_row9_col1, #T_fcfc7_row9_col2, #T_fcfc7_row10_col0, #T_fcfc7_row10_col1, #T_fcfc7_row10_col2, #T_fcfc7_row11_col0, #T_fcfc7_row11_col1, #T_fcfc7_row11_col2, #T_fcfc7_row12_col0, #T_fcfc7_row12_col1, #T_fcfc7_row12_col2 {
  text-align: right;
}
#T_fcfc7_row0_col3, #T_fcfc7_row1_col3, #T_fcfc7_row2_col3, #T_fcfc7_row3_col3, #T_fcfc7_row4_col3, #T_fcfc7_row5_col3, #T_fcfc7_row6_col3, #T_fcfc7_row7_col3, #T_fcfc7_row8_col3, #T_fcfc7_row9_col3, #T_fcfc7_row10_col3, #T_fcfc7_row11_col3, #T_fcfc7_row12_col3 {
  text-align: left;
}
</style>
<table id="T_fcfc7">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_fcfc7_level0_col0" class="col_heading level0 col0" >Normal (s)</th>
      <th id="T_fcfc7_level0_col1" class="col_heading level0 col1" >Event-Tag (s)</th>
      <th id="T_fcfc7_level0_col2" class="col_heading level0 col2" >Δ (s)</th>
      <th id="T_fcfc7_level0_col3" class="col_heading level0 col3" >N Halte (Events)</th>
    </tr>
    <tr>
      <th class="index_name level0" >District</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_fcfc7_level0_row0" class="row_heading level0 row0" >Kreis 2</th>
      <td id="T_fcfc7_row0_col0" class="data row0 col0" >56.10</td>
      <td id="T_fcfc7_row0_col1" class="data row0 col1" >59.10</td>
      <td id="T_fcfc7_row0_col2" class="data row0 col2" >3.00</td>
      <td id="T_fcfc7_row0_col3" class="data row0 col3" >1,218,286</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row1" class="row_heading level0 row1" >Kreis 9</th>
      <td id="T_fcfc7_row1_col0" class="data row1 col0" >59.10</td>
      <td id="T_fcfc7_row1_col1" class="data row1 col1" >61.50</td>
      <td id="T_fcfc7_row1_col2" class="data row1 col2" >2.40</td>
      <td id="T_fcfc7_row1_col3" class="data row1 col3" >917,796</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row2" class="row_heading level0 row2" >Kreis 3</th>
      <td id="T_fcfc7_row2_col0" class="data row2 col0" >55.70</td>
      <td id="T_fcfc7_row2_col1" class="data row2 col1" >56.90</td>
      <td id="T_fcfc7_row2_col2" class="data row2 col2" >1.20</td>
      <td id="T_fcfc7_row2_col3" class="data row2 col3" >1,044,697</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row3" class="row_heading level0 row3" >Kreis 4</th>
      <td id="T_fcfc7_row3_col0" class="data row3 col0" >54.50</td>
      <td id="T_fcfc7_row3_col1" class="data row3 col1" >55.70</td>
      <td id="T_fcfc7_row3_col2" class="data row3 col2" >1.20</td>
      <td id="T_fcfc7_row3_col3" class="data row3 col3" >1,623,785</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row4" class="row_heading level0 row4" >Kreis 12</th>
      <td id="T_fcfc7_row4_col0" class="data row4 col0" >66.10</td>
      <td id="T_fcfc7_row4_col1" class="data row4 col1" >66.80</td>
      <td id="T_fcfc7_row4_col2" class="data row4 col2" >0.70</td>
      <td id="T_fcfc7_row4_col3" class="data row4 col3" >900,360</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row5" class="row_heading level0 row5" >Kreis 1</th>
      <td id="T_fcfc7_row5_col0" class="data row5 col0" >51.20</td>
      <td id="T_fcfc7_row5_col1" class="data row5 col1" >51.70</td>
      <td id="T_fcfc7_row5_col2" class="data row5 col2" >0.40</td>
      <td id="T_fcfc7_row5_col3" class="data row5 col3" >3,880,130</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row6" class="row_heading level0 row6" >Kreis 6</th>
      <td id="T_fcfc7_row6_col0" class="data row6 col0" >55.60</td>
      <td id="T_fcfc7_row6_col1" class="data row6 col1" >55.90</td>
      <td id="T_fcfc7_row6_col2" class="data row6 col2" >0.30</td>
      <td id="T_fcfc7_row6_col3" class="data row6 col3" >2,719,031</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row7" class="row_heading level0 row7" >Kreis 8</th>
      <td id="T_fcfc7_row7_col0" class="data row7 col0" >63.60</td>
      <td id="T_fcfc7_row7_col1" class="data row7 col1" >63.80</td>
      <td id="T_fcfc7_row7_col2" class="data row7 col2" >0.20</td>
      <td id="T_fcfc7_row7_col3" class="data row7 col3" >779,710</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row8" class="row_heading level0 row8" >Kreis 11</th>
      <td id="T_fcfc7_row8_col0" class="data row8 col0" >68.50</td>
      <td id="T_fcfc7_row8_col1" class="data row8 col1" >67.70</td>
      <td id="T_fcfc7_row8_col2" class="data row8 col2" >-0.80</td>
      <td id="T_fcfc7_row8_col3" class="data row8 col3" >1,213,499</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row9" class="row_heading level0 row9" >Kreis 7</th>
      <td id="T_fcfc7_row9_col0" class="data row9 col0" >59.00</td>
      <td id="T_fcfc7_row9_col1" class="data row9 col1" >57.80</td>
      <td id="T_fcfc7_row9_col2" class="data row9 col2" >-1.20</td>
      <td id="T_fcfc7_row9_col3" class="data row9 col3" >1,252,520</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row10" class="row_heading level0 row10" >Kreis 5</th>
      <td id="T_fcfc7_row10_col0" class="data row10 col0" >50.20</td>
      <td id="T_fcfc7_row10_col1" class="data row10 col1" >48.90</td>
      <td id="T_fcfc7_row10_col2" class="data row10 col2" >-1.20</td>
      <td id="T_fcfc7_row10_col3" class="data row10 col3" >1,889,417</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row11" class="row_heading level0 row11" >Kreis 10</th>
      <td id="T_fcfc7_row11_col0" class="data row11 col0" >51.30</td>
      <td id="T_fcfc7_row11_col1" class="data row11 col1" >50.00</td>
      <td id="T_fcfc7_row11_col2" class="data row11 col2" >-1.40</td>
      <td id="T_fcfc7_row11_col3" class="data row11 col3" >559,348</td>
    </tr>
    <tr>
      <th id="T_fcfc7_level0_row12" class="row_heading level0 row12" >outside</th>
      <td id="T_fcfc7_row12_col0" class="data row12 col0" >58.80</td>
      <td id="T_fcfc7_row12_col1" class="data row12 col1" >57.20</td>
      <td id="T_fcfc7_row12_col2" class="data row12 col2" >-1.60</td>
      <td id="T_fcfc7_row12_col3" class="data row12 col3" >1,248,557</td>
    </tr>
  </tbody>
</table>






<style type="text/css">
#T_c64c4 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_c64c4 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_c64c4 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_c64c4 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_c64c4 tr:hover td {
  background-color: #eef3f8;
}
#T_c64c4_row0_col0, #T_c64c4_row0_col1, #T_c64c4_row1_col0, #T_c64c4_row1_col1, #T_c64c4_row2_col0, #T_c64c4_row2_col1, #T_c64c4_row3_col0, #T_c64c4_row3_col1, #T_c64c4_row4_col0, #T_c64c4_row4_col1, #T_c64c4_row5_col0, #T_c64c4_row5_col1, #T_c64c4_row6_col0, #T_c64c4_row6_col1, #T_c64c4_row7_col0, #T_c64c4_row7_col1, #T_c64c4_row8_col0, #T_c64c4_row8_col1, #T_c64c4_row9_col0, #T_c64c4_row9_col1, #T_c64c4_row10_col0, #T_c64c4_row10_col1, #T_c64c4_row11_col0, #T_c64c4_row11_col1, #T_c64c4_row12_col0, #T_c64c4_row12_col1, #T_c64c4_row13_col0, #T_c64c4_row13_col1, #T_c64c4_row14_col0, #T_c64c4_row14_col1, #T_c64c4_row15_col0, #T_c64c4_row15_col1, #T_c64c4_row16_col0, #T_c64c4_row16_col1, #T_c64c4_row17_col0, #T_c64c4_row17_col1, #T_c64c4_row18_col0, #T_c64c4_row18_col1, #T_c64c4_row19_col0, #T_c64c4_row19_col1 {
  text-align: left;
}
#T_c64c4_row0_col2, #T_c64c4_row0_col3, #T_c64c4_row0_col4, #T_c64c4_row0_col5, #T_c64c4_row1_col2, #T_c64c4_row1_col3, #T_c64c4_row1_col4, #T_c64c4_row1_col5, #T_c64c4_row2_col2, #T_c64c4_row2_col3, #T_c64c4_row2_col4, #T_c64c4_row2_col5, #T_c64c4_row3_col2, #T_c64c4_row3_col3, #T_c64c4_row3_col4, #T_c64c4_row3_col5, #T_c64c4_row4_col2, #T_c64c4_row4_col3, #T_c64c4_row4_col4, #T_c64c4_row4_col5, #T_c64c4_row5_col2, #T_c64c4_row5_col3, #T_c64c4_row5_col4, #T_c64c4_row5_col5, #T_c64c4_row6_col2, #T_c64c4_row6_col3, #T_c64c4_row6_col4, #T_c64c4_row6_col5, #T_c64c4_row7_col2, #T_c64c4_row7_col3, #T_c64c4_row7_col4, #T_c64c4_row7_col5, #T_c64c4_row8_col2, #T_c64c4_row8_col3, #T_c64c4_row8_col4, #T_c64c4_row8_col5, #T_c64c4_row9_col2, #T_c64c4_row9_col3, #T_c64c4_row9_col4, #T_c64c4_row9_col5, #T_c64c4_row10_col2, #T_c64c4_row10_col3, #T_c64c4_row10_col4, #T_c64c4_row10_col5, #T_c64c4_row11_col2, #T_c64c4_row11_col3, #T_c64c4_row11_col4, #T_c64c4_row11_col5, #T_c64c4_row12_col2, #T_c64c4_row12_col3, #T_c64c4_row12_col4, #T_c64c4_row12_col5, #T_c64c4_row13_col2, #T_c64c4_row13_col3, #T_c64c4_row13_col4, #T_c64c4_row13_col5, #T_c64c4_row14_col2, #T_c64c4_row14_col3, #T_c64c4_row14_col4, #T_c64c4_row14_col5, #T_c64c4_row15_col2, #T_c64c4_row15_col3, #T_c64c4_row15_col4, #T_c64c4_row15_col5, #T_c64c4_row16_col2, #T_c64c4_row16_col3, #T_c64c4_row16_col4, #T_c64c4_row16_col5, #T_c64c4_row17_col2, #T_c64c4_row17_col3, #T_c64c4_row17_col4, #T_c64c4_row17_col5, #T_c64c4_row18_col2, #T_c64c4_row18_col3, #T_c64c4_row18_col4, #T_c64c4_row18_col5, #T_c64c4_row19_col2, #T_c64c4_row19_col3, #T_c64c4_row19_col4, #T_c64c4_row19_col5 {
  text-align: right;
}
</style>
<table id="T_c64c4">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_c64c4_level0_col0" class="col_heading level0 col0" >Stop</th>
      <th id="T_c64c4_level0_col1" class="col_heading level0 col1" >District</th>
      <th id="T_c64c4_level0_col2" class="col_heading level0 col2" >Normal (s)</th>
      <th id="T_c64c4_level0_col3" class="col_heading level0 col3" >Event-Tag (s)</th>
      <th id="T_c64c4_level0_col4" class="col_heading level0 col4" >Δ (s)</th>
      <th id="T_c64c4_level0_col5" class="col_heading level0 col5" >N Halte (Events)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_c64c4_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_c64c4_row0_col0" class="data row0 col0" >Zürich, Bachmattstrasse</td>
      <td id="T_c64c4_row0_col1" class="data row0 col1" >Kreis 9</td>
      <td id="T_c64c4_row0_col2" class="data row0 col2" >61.60</td>
      <td id="T_c64c4_row0_col3" class="data row0 col3" >69.70</td>
      <td id="T_c64c4_row0_col4" class="data row0 col4" >8.10</td>
      <td id="T_c64c4_row0_col5" class="data row0 col5" >60513</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_c64c4_row1_col0" class="data row1 col0" >Zürich, Grimselstrasse</td>
      <td id="T_c64c4_row1_col1" class="data row1 col1" >Kreis 9</td>
      <td id="T_c64c4_row1_col2" class="data row1 col2" >59.70</td>
      <td id="T_c64c4_row1_col3" class="data row1 col3" >67.00</td>
      <td id="T_c64c4_row1_col4" class="data row1 col4" >7.30</td>
      <td id="T_c64c4_row1_col5" class="data row1 col5" >60208</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_c64c4_row2_col0" class="data row2 col0" >Zürich, Farbhof</td>
      <td id="T_c64c4_row2_col1" class="data row2 col1" >Kreis 9</td>
      <td id="T_c64c4_row2_col2" class="data row2 col2" >62.40</td>
      <td id="T_c64c4_row2_col3" class="data row2 col3" >68.70</td>
      <td id="T_c64c4_row2_col4" class="data row2 col4" >6.30</td>
      <td id="T_c64c4_row2_col5" class="data row2 col5" >61365</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_c64c4_row3_col0" class="data row3 col0" >Zürich, Lindenplatz</td>
      <td id="T_c64c4_row3_col1" class="data row3 col1" >Kreis 9</td>
      <td id="T_c64c4_row3_col2" class="data row3 col2" >63.80</td>
      <td id="T_c64c4_row3_col3" class="data row3 col3" >69.70</td>
      <td id="T_c64c4_row3_col4" class="data row3 col4" >5.90</td>
      <td id="T_c64c4_row3_col5" class="data row3 col5" >61312</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_c64c4_row4_col0" class="data row4 col0" >Zürich, Museum Rietberg</td>
      <td id="T_c64c4_row4_col1" class="data row4 col1" >Kreis 2</td>
      <td id="T_c64c4_row4_col2" class="data row4 col2" >54.30</td>
      <td id="T_c64c4_row4_col3" class="data row4 col3" >59.80</td>
      <td id="T_c64c4_row4_col4" class="data row4 col4" >5.50</td>
      <td id="T_c64c4_row4_col5" class="data row4 col5" >66535</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_c64c4_row5_col0" class="data row5 col0" >Zürich, Micafil</td>
      <td id="T_c64c4_row5_col1" class="data row5 col1" >Kreis 9</td>
      <td id="T_c64c4_row5_col2" class="data row5 col2" >65.50</td>
      <td id="T_c64c4_row5_col3" class="data row5 col3" >70.90</td>
      <td id="T_c64c4_row5_col4" class="data row5 col4" >5.30</td>
      <td id="T_c64c4_row5_col5" class="data row5 col5" >61322</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_c64c4_row6_col0" class="data row6 col0" >Zürich, Siemens</td>
      <td id="T_c64c4_row6_col1" class="data row6 col1" >Kreis 9</td>
      <td id="T_c64c4_row6_col2" class="data row6 col2" >60.40</td>
      <td id="T_c64c4_row6_col3" class="data row6 col3" >65.40</td>
      <td id="T_c64c4_row6_col4" class="data row6 col4" >5.00</td>
      <td id="T_c64c4_row6_col5" class="data row6 col5" >61233</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_c64c4_row7_col0" class="data row7 col0" >Schlieren, Mülligen</td>
      <td id="T_c64c4_row7_col1" class="data row7 col1" >outside</td>
      <td id="T_c64c4_row7_col2" class="data row7 col2" >53.70</td>
      <td id="T_c64c4_row7_col3" class="data row7 col3" >58.30</td>
      <td id="T_c64c4_row7_col4" class="data row7 col4" >4.60</td>
      <td id="T_c64c4_row7_col5" class="data row7 col5" >61400</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_c64c4_row8_col0" class="data row8 col0" >Zürich, Brunaustrasse</td>
      <td id="T_c64c4_row8_col1" class="data row8 col1" >Kreis 2</td>
      <td id="T_c64c4_row8_col2" class="data row8 col2" >57.50</td>
      <td id="T_c64c4_row8_col3" class="data row8 col3" >62.20</td>
      <td id="T_c64c4_row8_col4" class="data row8 col4" >4.60</td>
      <td id="T_c64c4_row8_col5" class="data row8 col5" >67421</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_c64c4_row9_col0" class="data row9 col0" >Schlieren, Zentrum/Bahnhof</td>
      <td id="T_c64c4_row9_col1" class="data row9 col1" >outside</td>
      <td id="T_c64c4_row9_col2" class="data row9 col2" >48.70</td>
      <td id="T_c64c4_row9_col3" class="data row9 col3" >53.10</td>
      <td id="T_c64c4_row9_col4" class="data row9 col4" >4.30</td>
      <td id="T_c64c4_row9_col5" class="data row9 col5" >61397</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_c64c4_row10_col0" class="data row10 col0" >Zürich, Fröhlichstrasse</td>
      <td id="T_c64c4_row10_col1" class="data row10 col1" >Kreis 8</td>
      <td id="T_c64c4_row10_col2" class="data row10 col2" >67.70</td>
      <td id="T_c64c4_row10_col3" class="data row10 col3" >72.00</td>
      <td id="T_c64c4_row10_col4" class="data row10 col4" >4.30</td>
      <td id="T_c64c4_row10_col5" class="data row10 col5" >118469</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_c64c4_row11_col0" class="data row11 col0" >Zürich, Heerenwiesen</td>
      <td id="T_c64c4_row11_col1" class="data row11 col1" >Kreis 12</td>
      <td id="T_c64c4_row11_col2" class="data row11 col2" >68.50</td>
      <td id="T_c64c4_row11_col3" class="data row11 col3" >72.80</td>
      <td id="T_c64c4_row11_col4" class="data row11 col4" >4.30</td>
      <td id="T_c64c4_row11_col5" class="data row11 col5" >60034</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_c64c4_row12_col0" class="data row12 col0" >Zürich, Friedhof Enzenbühl</td>
      <td id="T_c64c4_row12_col1" class="data row12 col1" >Kreis 8</td>
      <td id="T_c64c4_row12_col2" class="data row12 col2" >92.90</td>
      <td id="T_c64c4_row12_col3" class="data row12 col3" >97.10</td>
      <td id="T_c64c4_row12_col4" class="data row12 col4" >4.20</td>
      <td id="T_c64c4_row12_col5" class="data row12 col5" >63714</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_c64c4_row13_col0" class="data row13 col0" >Zürich, Freihofstrasse</td>
      <td id="T_c64c4_row13_col1" class="data row13 col1" >Kreis 9</td>
      <td id="T_c64c4_row13_col2" class="data row13 col2" >54.50</td>
      <td id="T_c64c4_row13_col3" class="data row13 col3" >58.60</td>
      <td id="T_c64c4_row13_col4" class="data row13 col4" >4.10</td>
      <td id="T_c64c4_row13_col5" class="data row13 col5" >63600</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_c64c4_row14_col0" class="data row14 col0" >Zürich, Bahnhof Enge</td>
      <td id="T_c64c4_row14_col1" class="data row14 col1" >Kreis 2</td>
      <td id="T_c64c4_row14_col2" class="data row14 col2" >52.70</td>
      <td id="T_c64c4_row14_col3" class="data row14 col3" >56.70</td>
      <td id="T_c64c4_row14_col4" class="data row14 col4" >4.10</td>
      <td id="T_c64c4_row14_col5" class="data row14 col5" >99671</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_c64c4_row15_col0" class="data row15 col0" >Zürich, Laubegg</td>
      <td id="T_c64c4_row15_col1" class="data row15 col1" >Kreis 3</td>
      <td id="T_c64c4_row15_col2" class="data row15 col2" >53.00</td>
      <td id="T_c64c4_row15_col3" class="data row15 col3" >57.00</td>
      <td id="T_c64c4_row15_col4" class="data row15 col4" >4.10</td>
      <td id="T_c64c4_row15_col5" class="data row15 col5" >66602</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_c64c4_row16_col0" class="data row16 col0" >Zürich, Kappeli</td>
      <td id="T_c64c4_row16_col1" class="data row16 col1" >Kreis 9</td>
      <td id="T_c64c4_row16_col2" class="data row16 col2" >56.30</td>
      <td id="T_c64c4_row16_col3" class="data row16 col3" >60.40</td>
      <td id="T_c64c4_row16_col4" class="data row16 col4" >4.10</td>
      <td id="T_c64c4_row16_col5" class="data row16 col5" >60107</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_c64c4_row17_col0" class="data row17 col0" >Schlieren, Gasometerbrücke</td>
      <td id="T_c64c4_row17_col1" class="data row17 col1" >outside</td>
      <td id="T_c64c4_row17_col2" class="data row17 col2" >56.70</td>
      <td id="T_c64c4_row17_col3" class="data row17 col3" >60.80</td>
      <td id="T_c64c4_row17_col4" class="data row17 col4" >4.00</td>
      <td id="T_c64c4_row17_col5" class="data row17 col5" >61428</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_c64c4_row18_col0" class="data row18 col0" >Zürich, Zypressenstrasse</td>
      <td id="T_c64c4_row18_col1" class="data row18 col1" >Kreis 4</td>
      <td id="T_c64c4_row18_col2" class="data row18 col2" >52.00</td>
      <td id="T_c64c4_row18_col3" class="data row18 col3" >56.00</td>
      <td id="T_c64c4_row18_col4" class="data row18 col4" >4.00</td>
      <td id="T_c64c4_row18_col5" class="data row18 col5" >99131</td>
    </tr>
    <tr>
      <th id="T_c64c4_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_c64c4_row19_col0" class="data row19 col0" >Zürich, Letzigrund</td>
      <td id="T_c64c4_row19_col1" class="data row19 col1" >Kreis 4</td>
      <td id="T_c64c4_row19_col2" class="data row19 col2" >55.40</td>
      <td id="T_c64c4_row19_col3" class="data row19 col3" >59.40</td>
      <td id="T_c64c4_row19_col4" class="data row19 col4" >3.90</td>
      <td id="T_c64c4_row19_col5" class="data row19 col5" >62959</td>
    </tr>
  </tbody>
</table>



**Beobachtung — Räumliche Event-Muster:**

Die Karte zeigt vier verschiedene Mechanismen wie Events das Netz belasten:

**Kreis 9 — Ausstrahlungskorridor:** Die erhöhten Werte entlang Linie 2 (Bachmattstrasse, Grimselstrasse, Farbhof, Lindenplatz) zeigen dass Event-Delays von der Innenstadt nach Westen propagieren. K9 ist der Heimweg für Besucher aus dem Umland — Messe Zürich und Hallenstadion entlassen ihr Publikum direkt in diesen Korridor.

**Kreis 2 — Bahnhof- und Stadion-Zugang:** Bahnhof Enge und Museum Rietberg (Linie 7/13) sind Umsteigeknoten für Event-Besucher. K2 verbindet Innenstadt mit dem Süden der Stadt und dem Bahnhof Enge als Endpunkt mehrerer Linien.

**Kreis 4 — Stadion-Korridor:** Zypressenstrasse und Letzigrund (FCZ-Stadion) zeigen dass K4 bei Fussball-Events unter Druck steht. Der Korridor ist stark befahren und hat wenig Puffer bei zusätzlichem Ansturm.

**Kreis 3 — Innenstadt-Effekt:** Analog zu K4, aber als direkter Innenstadteffekt. K3 (Wiedikon/Sihlfeld) liegt auf den gleichen Durchgangskorridoren und trägt den erhöhten Druck wenn die Innenstadt bei Events überlastet ist.

→ **Präsentation:** Die Karte beantwortet "wo" — nicht überall gleichmässig, sondern auf vier klar identifizierbaren Korridoren. Hot Insight: K9 ist nicht selbst Eventort, sondern trägt die Konsequenzen.

**Beobachtung:** Der Event-Effekt auf Stadtkreis-Ebene ist überraschend klein — und in mehreren Kreisen sogar negativ.

**Δ Delay Event-Tag vs. Normaltag nach Stadtkreis:**
| Stadtkreis | Normal (s) | Event-Tag (s) | Δ |
|:---|---:|---:|---:|
| Kreis 2 | 56.1 | 59.1 | **+3.0** |
| Kreis 9 | 59.1 | 61.5 | **+2.4** |
| Kreis 3 | 55.7 | 56.9 | +1.2 |
| Kreis 4 | 54.5 | 55.7 | +1.2 |
| Kreis 11 | 68.5 | 67.7 | **−0.8** (leicht besser!) |
| Kreis 5 | 50.2 | 48.9 | −1.2 |
| outside | 58.8 | 57.2 | −1.6 |

**Kernbefund:** Nur Kreise 2 (+3.0s) und 9 (+2.4s) zeigen messbare positive Event-Effekte. Kreis 11 (wo Hallenstadion und Messe Zürich liegen!) zeigt an Event-Tagen sogar leicht *niedrigere* Delays (−0.8s) — überraschend.

**Erklärungsansatz:** Die Event-Klassifizierung ist netzweit (ganzer Betriebstag), nicht linienbezogen. Der starke Effekt einer Fachmesse auf L11-Abendstunden wird durch den gesamten Tagesbetrieb von Kreis 11 "verdünnt". Ein Kreis-Δ von +3.0s entspricht einem sehr kleinen Effekt relativ zur Kreis-Streuung — die räumliche Aggregation verbirgt den zeitlichen (Abend-)Effekt.

→ Feature-Empfehlung: `has_event × hour` Interaktion ist aussagekräftiger als nur `district × has_event`. Der Abend-Effekt (F-EVNT-03) bleibt die stärkste räumlich-zeitliche Signatur.

## Kapazitäts-Erholung: Feiertag vs. Wochenende vs. Normaltag

Wenn Pendler ausbleiben und der Privatverkehr zurückgeht, erholt sich das Tramnetz — ohne jede Taktänderung.

Feiertage erreichen nahezu Wochenend-Niveau oder unterschreiten es. Kernbotschaft: **Die Kapazitätsgrenze des Netzes liegt beim Strassenverkehr**, nicht beim Fahrgastaufkommen. Das Netz könnte strukturell besser performen — wenn der MIV reduziert wird.

Drei Kurven: `Normaler Werktag` · `Wochenende` · `Feiertag` — pro Stunde (0–23 h).


```python
an.plot_holiday_recovery(lf_delay)
```


    
![png](03_analysis_6-events_files/03_analysis_6-events_22_0.png)
    


## Haltestellen- & Linien-Ranking

Welche Haltestellen und Linien leiden am stärksten unter Events? Bar-Charts für direkten Rang-Vergleich — ergänzt die Karten-Ansicht weiter oben.


```python
an.plot_event_stop_ranking(lf_delay, cfg)

show_df(an.table_event_stop_map(lf_delay))

an.plot_event_line_ranking(lf_delay, cfg)

show_df(an.table_event_line_ranking(lf_delay))
```


    
![png](03_analysis_6-events_files/03_analysis_6-events_25_0.png)
    



<style type="text/css">
#T_dce00 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_dce00 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_dce00 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_dce00 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_dce00 tr:hover td {
  background-color: #eef3f8;
}
#T_dce00_row0_col0, #T_dce00_row0_col1, #T_dce00_row1_col0, #T_dce00_row1_col1, #T_dce00_row2_col0, #T_dce00_row2_col1, #T_dce00_row3_col0, #T_dce00_row3_col1, #T_dce00_row4_col0, #T_dce00_row4_col1, #T_dce00_row5_col0, #T_dce00_row5_col1, #T_dce00_row6_col0, #T_dce00_row6_col1, #T_dce00_row7_col0, #T_dce00_row7_col1, #T_dce00_row8_col0, #T_dce00_row8_col1, #T_dce00_row9_col0, #T_dce00_row9_col1, #T_dce00_row10_col0, #T_dce00_row10_col1, #T_dce00_row11_col0, #T_dce00_row11_col1, #T_dce00_row12_col0, #T_dce00_row12_col1, #T_dce00_row13_col0, #T_dce00_row13_col1, #T_dce00_row14_col0, #T_dce00_row14_col1, #T_dce00_row15_col0, #T_dce00_row15_col1, #T_dce00_row16_col0, #T_dce00_row16_col1, #T_dce00_row17_col0, #T_dce00_row17_col1, #T_dce00_row18_col0, #T_dce00_row18_col1, #T_dce00_row19_col0, #T_dce00_row19_col1 {
  text-align: left;
}
#T_dce00_row0_col2, #T_dce00_row0_col3, #T_dce00_row0_col4, #T_dce00_row0_col5, #T_dce00_row1_col2, #T_dce00_row1_col3, #T_dce00_row1_col4, #T_dce00_row1_col5, #T_dce00_row2_col2, #T_dce00_row2_col3, #T_dce00_row2_col4, #T_dce00_row2_col5, #T_dce00_row3_col2, #T_dce00_row3_col3, #T_dce00_row3_col4, #T_dce00_row3_col5, #T_dce00_row4_col2, #T_dce00_row4_col3, #T_dce00_row4_col4, #T_dce00_row4_col5, #T_dce00_row5_col2, #T_dce00_row5_col3, #T_dce00_row5_col4, #T_dce00_row5_col5, #T_dce00_row6_col2, #T_dce00_row6_col3, #T_dce00_row6_col4, #T_dce00_row6_col5, #T_dce00_row7_col2, #T_dce00_row7_col3, #T_dce00_row7_col4, #T_dce00_row7_col5, #T_dce00_row8_col2, #T_dce00_row8_col3, #T_dce00_row8_col4, #T_dce00_row8_col5, #T_dce00_row9_col2, #T_dce00_row9_col3, #T_dce00_row9_col4, #T_dce00_row9_col5, #T_dce00_row10_col2, #T_dce00_row10_col3, #T_dce00_row10_col4, #T_dce00_row10_col5, #T_dce00_row11_col2, #T_dce00_row11_col3, #T_dce00_row11_col4, #T_dce00_row11_col5, #T_dce00_row12_col2, #T_dce00_row12_col3, #T_dce00_row12_col4, #T_dce00_row12_col5, #T_dce00_row13_col2, #T_dce00_row13_col3, #T_dce00_row13_col4, #T_dce00_row13_col5, #T_dce00_row14_col2, #T_dce00_row14_col3, #T_dce00_row14_col4, #T_dce00_row14_col5, #T_dce00_row15_col2, #T_dce00_row15_col3, #T_dce00_row15_col4, #T_dce00_row15_col5, #T_dce00_row16_col2, #T_dce00_row16_col3, #T_dce00_row16_col4, #T_dce00_row16_col5, #T_dce00_row17_col2, #T_dce00_row17_col3, #T_dce00_row17_col4, #T_dce00_row17_col5, #T_dce00_row18_col2, #T_dce00_row18_col3, #T_dce00_row18_col4, #T_dce00_row18_col5, #T_dce00_row19_col2, #T_dce00_row19_col3, #T_dce00_row19_col4, #T_dce00_row19_col5 {
  text-align: right;
}
</style>
<table id="T_dce00">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_dce00_level0_col0" class="col_heading level0 col0" >Stop</th>
      <th id="T_dce00_level0_col1" class="col_heading level0 col1" >District</th>
      <th id="T_dce00_level0_col2" class="col_heading level0 col2" >Normal (s)</th>
      <th id="T_dce00_level0_col3" class="col_heading level0 col3" >Event-Tag (s)</th>
      <th id="T_dce00_level0_col4" class="col_heading level0 col4" >Δ (s)</th>
      <th id="T_dce00_level0_col5" class="col_heading level0 col5" >N Halte (Events)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_dce00_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_dce00_row0_col0" class="data row0 col0" >Zürich, Bachmattstrasse</td>
      <td id="T_dce00_row0_col1" class="data row0 col1" >Kreis 9</td>
      <td id="T_dce00_row0_col2" class="data row0 col2" >61.60</td>
      <td id="T_dce00_row0_col3" class="data row0 col3" >69.70</td>
      <td id="T_dce00_row0_col4" class="data row0 col4" >8.10</td>
      <td id="T_dce00_row0_col5" class="data row0 col5" >60513</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_dce00_row1_col0" class="data row1 col0" >Zürich, Grimselstrasse</td>
      <td id="T_dce00_row1_col1" class="data row1 col1" >Kreis 9</td>
      <td id="T_dce00_row1_col2" class="data row1 col2" >59.70</td>
      <td id="T_dce00_row1_col3" class="data row1 col3" >67.00</td>
      <td id="T_dce00_row1_col4" class="data row1 col4" >7.30</td>
      <td id="T_dce00_row1_col5" class="data row1 col5" >60208</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_dce00_row2_col0" class="data row2 col0" >Zürich, Farbhof</td>
      <td id="T_dce00_row2_col1" class="data row2 col1" >Kreis 9</td>
      <td id="T_dce00_row2_col2" class="data row2 col2" >62.40</td>
      <td id="T_dce00_row2_col3" class="data row2 col3" >68.70</td>
      <td id="T_dce00_row2_col4" class="data row2 col4" >6.30</td>
      <td id="T_dce00_row2_col5" class="data row2 col5" >61365</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_dce00_row3_col0" class="data row3 col0" >Zürich, Lindenplatz</td>
      <td id="T_dce00_row3_col1" class="data row3 col1" >Kreis 9</td>
      <td id="T_dce00_row3_col2" class="data row3 col2" >63.80</td>
      <td id="T_dce00_row3_col3" class="data row3 col3" >69.70</td>
      <td id="T_dce00_row3_col4" class="data row3 col4" >5.90</td>
      <td id="T_dce00_row3_col5" class="data row3 col5" >61312</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_dce00_row4_col0" class="data row4 col0" >Zürich, Museum Rietberg</td>
      <td id="T_dce00_row4_col1" class="data row4 col1" >Kreis 2</td>
      <td id="T_dce00_row4_col2" class="data row4 col2" >54.30</td>
      <td id="T_dce00_row4_col3" class="data row4 col3" >59.80</td>
      <td id="T_dce00_row4_col4" class="data row4 col4" >5.50</td>
      <td id="T_dce00_row4_col5" class="data row4 col5" >66535</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_dce00_row5_col0" class="data row5 col0" >Zürich, Micafil</td>
      <td id="T_dce00_row5_col1" class="data row5 col1" >Kreis 9</td>
      <td id="T_dce00_row5_col2" class="data row5 col2" >65.50</td>
      <td id="T_dce00_row5_col3" class="data row5 col3" >70.90</td>
      <td id="T_dce00_row5_col4" class="data row5 col4" >5.30</td>
      <td id="T_dce00_row5_col5" class="data row5 col5" >61322</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_dce00_row6_col0" class="data row6 col0" >Zürich, Siemens</td>
      <td id="T_dce00_row6_col1" class="data row6 col1" >Kreis 9</td>
      <td id="T_dce00_row6_col2" class="data row6 col2" >60.40</td>
      <td id="T_dce00_row6_col3" class="data row6 col3" >65.40</td>
      <td id="T_dce00_row6_col4" class="data row6 col4" >5.00</td>
      <td id="T_dce00_row6_col5" class="data row6 col5" >61233</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_dce00_row7_col0" class="data row7 col0" >Schlieren, Mülligen</td>
      <td id="T_dce00_row7_col1" class="data row7 col1" >outside</td>
      <td id="T_dce00_row7_col2" class="data row7 col2" >53.70</td>
      <td id="T_dce00_row7_col3" class="data row7 col3" >58.30</td>
      <td id="T_dce00_row7_col4" class="data row7 col4" >4.60</td>
      <td id="T_dce00_row7_col5" class="data row7 col5" >61400</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_dce00_row8_col0" class="data row8 col0" >Zürich, Brunaustrasse</td>
      <td id="T_dce00_row8_col1" class="data row8 col1" >Kreis 2</td>
      <td id="T_dce00_row8_col2" class="data row8 col2" >57.50</td>
      <td id="T_dce00_row8_col3" class="data row8 col3" >62.20</td>
      <td id="T_dce00_row8_col4" class="data row8 col4" >4.60</td>
      <td id="T_dce00_row8_col5" class="data row8 col5" >67421</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_dce00_row9_col0" class="data row9 col0" >Zürich, Fröhlichstrasse</td>
      <td id="T_dce00_row9_col1" class="data row9 col1" >Kreis 8</td>
      <td id="T_dce00_row9_col2" class="data row9 col2" >67.70</td>
      <td id="T_dce00_row9_col3" class="data row9 col3" >72.00</td>
      <td id="T_dce00_row9_col4" class="data row9 col4" >4.30</td>
      <td id="T_dce00_row9_col5" class="data row9 col5" >118469</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_dce00_row10_col0" class="data row10 col0" >Schlieren, Zentrum/Bahnhof</td>
      <td id="T_dce00_row10_col1" class="data row10 col1" >outside</td>
      <td id="T_dce00_row10_col2" class="data row10 col2" >48.70</td>
      <td id="T_dce00_row10_col3" class="data row10 col3" >53.10</td>
      <td id="T_dce00_row10_col4" class="data row10 col4" >4.30</td>
      <td id="T_dce00_row10_col5" class="data row10 col5" >61397</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_dce00_row11_col0" class="data row11 col0" >Zürich, Heerenwiesen</td>
      <td id="T_dce00_row11_col1" class="data row11 col1" >Kreis 12</td>
      <td id="T_dce00_row11_col2" class="data row11 col2" >68.50</td>
      <td id="T_dce00_row11_col3" class="data row11 col3" >72.80</td>
      <td id="T_dce00_row11_col4" class="data row11 col4" >4.30</td>
      <td id="T_dce00_row11_col5" class="data row11 col5" >60034</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_dce00_row12_col0" class="data row12 col0" >Zürich, Friedhof Enzenbühl</td>
      <td id="T_dce00_row12_col1" class="data row12 col1" >Kreis 8</td>
      <td id="T_dce00_row12_col2" class="data row12 col2" >92.90</td>
      <td id="T_dce00_row12_col3" class="data row12 col3" >97.10</td>
      <td id="T_dce00_row12_col4" class="data row12 col4" >4.20</td>
      <td id="T_dce00_row12_col5" class="data row12 col5" >63714</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_dce00_row13_col0" class="data row13 col0" >Zürich, Bahnhof Enge</td>
      <td id="T_dce00_row13_col1" class="data row13 col1" >Kreis 2</td>
      <td id="T_dce00_row13_col2" class="data row13 col2" >52.70</td>
      <td id="T_dce00_row13_col3" class="data row13 col3" >56.70</td>
      <td id="T_dce00_row13_col4" class="data row13 col4" >4.10</td>
      <td id="T_dce00_row13_col5" class="data row13 col5" >99671</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_dce00_row14_col0" class="data row14 col0" >Zürich, Laubegg</td>
      <td id="T_dce00_row14_col1" class="data row14 col1" >Kreis 3</td>
      <td id="T_dce00_row14_col2" class="data row14 col2" >53.00</td>
      <td id="T_dce00_row14_col3" class="data row14 col3" >57.00</td>
      <td id="T_dce00_row14_col4" class="data row14 col4" >4.10</td>
      <td id="T_dce00_row14_col5" class="data row14 col5" >66602</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_dce00_row15_col0" class="data row15 col0" >Zürich, Kappeli</td>
      <td id="T_dce00_row15_col1" class="data row15 col1" >Kreis 9</td>
      <td id="T_dce00_row15_col2" class="data row15 col2" >56.30</td>
      <td id="T_dce00_row15_col3" class="data row15 col3" >60.40</td>
      <td id="T_dce00_row15_col4" class="data row15 col4" >4.10</td>
      <td id="T_dce00_row15_col5" class="data row15 col5" >60107</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_dce00_row16_col0" class="data row16 col0" >Zürich, Freihofstrasse</td>
      <td id="T_dce00_row16_col1" class="data row16 col1" >Kreis 9</td>
      <td id="T_dce00_row16_col2" class="data row16 col2" >54.50</td>
      <td id="T_dce00_row16_col3" class="data row16 col3" >58.60</td>
      <td id="T_dce00_row16_col4" class="data row16 col4" >4.10</td>
      <td id="T_dce00_row16_col5" class="data row16 col5" >63600</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_dce00_row17_col0" class="data row17 col0" >Schlieren, Gasometerbrücke</td>
      <td id="T_dce00_row17_col1" class="data row17 col1" >outside</td>
      <td id="T_dce00_row17_col2" class="data row17 col2" >56.70</td>
      <td id="T_dce00_row17_col3" class="data row17 col3" >60.80</td>
      <td id="T_dce00_row17_col4" class="data row17 col4" >4.00</td>
      <td id="T_dce00_row17_col5" class="data row17 col5" >61428</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_dce00_row18_col0" class="data row18 col0" >Zürich, Zypressenstrasse</td>
      <td id="T_dce00_row18_col1" class="data row18 col1" >Kreis 4</td>
      <td id="T_dce00_row18_col2" class="data row18 col2" >52.00</td>
      <td id="T_dce00_row18_col3" class="data row18 col3" >56.00</td>
      <td id="T_dce00_row18_col4" class="data row18 col4" >4.00</td>
      <td id="T_dce00_row18_col5" class="data row18 col5" >99131</td>
    </tr>
    <tr>
      <th id="T_dce00_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_dce00_row19_col0" class="data row19 col0" >Zürich, Letzigrund</td>
      <td id="T_dce00_row19_col1" class="data row19 col1" >Kreis 4</td>
      <td id="T_dce00_row19_col2" class="data row19 col2" >55.40</td>
      <td id="T_dce00_row19_col3" class="data row19 col3" >59.40</td>
      <td id="T_dce00_row19_col4" class="data row19 col4" >3.90</td>
      <td id="T_dce00_row19_col5" class="data row19 col5" >62959</td>
    </tr>
  </tbody>
</table>




    
![png](03_analysis_6-events_files/03_analysis_6-events_25_2.png)
    



<style type="text/css">
#T_36194 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_36194 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_36194 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_36194 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_36194 tr:hover td {
  background-color: #eef3f8;
}
#T_36194_row0_col0, #T_36194_row0_col1, #T_36194_row0_col2, #T_36194_row0_col3, #T_36194_row1_col0, #T_36194_row1_col1, #T_36194_row1_col2, #T_36194_row1_col3, #T_36194_row2_col0, #T_36194_row2_col1, #T_36194_row2_col2, #T_36194_row2_col3, #T_36194_row3_col0, #T_36194_row3_col1, #T_36194_row3_col2, #T_36194_row3_col3, #T_36194_row4_col0, #T_36194_row4_col1, #T_36194_row4_col2, #T_36194_row4_col3, #T_36194_row5_col0, #T_36194_row5_col1, #T_36194_row5_col2, #T_36194_row5_col3, #T_36194_row6_col0, #T_36194_row6_col1, #T_36194_row6_col2, #T_36194_row6_col3, #T_36194_row7_col0, #T_36194_row7_col1, #T_36194_row7_col2, #T_36194_row7_col3, #T_36194_row8_col0, #T_36194_row8_col1, #T_36194_row8_col2, #T_36194_row8_col3, #T_36194_row9_col0, #T_36194_row9_col1, #T_36194_row9_col2, #T_36194_row9_col3, #T_36194_row10_col0, #T_36194_row10_col1, #T_36194_row10_col2, #T_36194_row10_col3, #T_36194_row11_col0, #T_36194_row11_col1, #T_36194_row11_col2, #T_36194_row11_col3, #T_36194_row12_col0, #T_36194_row12_col1, #T_36194_row12_col2, #T_36194_row12_col3, #T_36194_row13_col0, #T_36194_row13_col1, #T_36194_row13_col2, #T_36194_row13_col3, #T_36194_row14_col0, #T_36194_row14_col1, #T_36194_row14_col2, #T_36194_row14_col3, #T_36194_row15_col0, #T_36194_row15_col1, #T_36194_row15_col2, #T_36194_row15_col3, #T_36194_row16_col0, #T_36194_row16_col1, #T_36194_row16_col2, #T_36194_row16_col3, #T_36194_row17_col0, #T_36194_row17_col1, #T_36194_row17_col2, #T_36194_row17_col3 {
  text-align: right;
}
#T_36194_row0_col4, #T_36194_row1_col4, #T_36194_row2_col4, #T_36194_row3_col4, #T_36194_row4_col4, #T_36194_row5_col4, #T_36194_row6_col4, #T_36194_row7_col4, #T_36194_row8_col4, #T_36194_row9_col4, #T_36194_row10_col4, #T_36194_row11_col4, #T_36194_row12_col4, #T_36194_row13_col4, #T_36194_row14_col4, #T_36194_row15_col4, #T_36194_row16_col4, #T_36194_row17_col4 {
  text-align: left;
}
</style>
<table id="T_36194">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_36194_level0_col0" class="col_heading level0 col0" >Normal (s)</th>
      <th id="T_36194_level0_col1" class="col_heading level0 col1" >Event-Tag (s)</th>
      <th id="T_36194_level0_col2" class="col_heading level0 col2" >Δ (s)</th>
      <th id="T_36194_level0_col3" class="col_heading level0 col3" >ΔOTP (pp)</th>
      <th id="T_36194_level0_col4" class="col_heading level0 col4" >N Halte (Events)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Line</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_36194_level0_row0" class="row_heading level0 row0" >LE</th>
      <td id="T_36194_row0_col0" class="data row0 col0" >129.40</td>
      <td id="T_36194_row0_col1" class="data row0 col1" >134.10</td>
      <td id="T_36194_row0_col2" class="data row0 col2" >4.70</td>
      <td id="T_36194_row0_col3" class="data row0 col3" >4.20</td>
      <td id="T_36194_row0_col4" class="data row0 col4" >390</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row1" class="row_heading level0 row1" >L2</th>
      <td id="T_36194_row1_col0" class="data row1 col0" >55.50</td>
      <td id="T_36194_row1_col1" class="data row1 col1" >58.80</td>
      <td id="T_36194_row1_col2" class="data row1 col2" >3.30</td>
      <td id="T_36194_row1_col3" class="data row1 col3" >-1.40</td>
      <td id="T_36194_row1_col4" class="data row1 col4" >1,708,790</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row2" class="row_heading level0 row2" >L7</th>
      <td id="T_36194_row2_col0" class="data row2 col0" >58.30</td>
      <td id="T_36194_row2_col1" class="data row2 col1" >60.70</td>
      <td id="T_36194_row2_col2" class="data row2 col2" >2.40</td>
      <td id="T_36194_row2_col3" class="data row2 col3" >-0.60</td>
      <td id="T_36194_row2_col4" class="data row2 col4" >1,775,931</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row3" class="row_heading level0 row3" >L6</th>
      <td id="T_36194_row3_col0" class="data row3 col0" >38.00</td>
      <td id="T_36194_row3_col1" class="data row3 col1" >39.90</td>
      <td id="T_36194_row3_col2" class="data row3 col2" >1.90</td>
      <td id="T_36194_row3_col3" class="data row3 col3" >-0.40</td>
      <td id="T_36194_row3_col4" class="data row3 col4" >765,213</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row4" class="row_heading level0 row4" >L11</th>
      <td id="T_36194_row4_col0" class="data row4 col0" >68.40</td>
      <td id="T_36194_row4_col1" class="data row4 col1" >70.10</td>
      <td id="T_36194_row4_col2" class="data row4 col2" >1.70</td>
      <td id="T_36194_row4_col3" class="data row4 col3" >-0.50</td>
      <td id="T_36194_row4_col4" class="data row4 col4" >1,957,473</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row5" class="row_heading level0 row5" >L9</th>
      <td id="T_36194_row5_col0" class="data row5 col0" >55.40</td>
      <td id="T_36194_row5_col1" class="data row5 col1" >56.40</td>
      <td id="T_36194_row5_col2" class="data row5 col2" >1.00</td>
      <td id="T_36194_row5_col3" class="data row5 col3" >0.10</td>
      <td id="T_36194_row5_col4" class="data row5 col4" >1,775,814</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row6" class="row_heading level0 row6" >L3</th>
      <td id="T_36194_row6_col0" class="data row6 col0" >53.70</td>
      <td id="T_36194_row6_col1" class="data row6 col1" >54.50</td>
      <td id="T_36194_row6_col2" class="data row6 col2" >0.80</td>
      <td id="T_36194_row6_col3" class="data row6 col3" >-0.70</td>
      <td id="T_36194_row6_col4" class="data row6 col4" >1,127,609</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row7" class="row_heading level0 row7" >L14</th>
      <td id="T_36194_row7_col0" class="data row7 col0" >55.40</td>
      <td id="T_36194_row7_col1" class="data row7 col1" >55.90</td>
      <td id="T_36194_row7_col2" class="data row7 col2" >0.50</td>
      <td id="T_36194_row7_col3" class="data row7 col3" >-0.10</td>
      <td id="T_36194_row7_col4" class="data row7 col4" >1,535,369</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row8" class="row_heading level0 row8" >L5</th>
      <td id="T_36194_row8_col0" class="data row8 col0" >47.50</td>
      <td id="T_36194_row8_col1" class="data row8 col1" >47.00</td>
      <td id="T_36194_row8_col2" class="data row8 col2" >-0.50</td>
      <td id="T_36194_row8_col3" class="data row8 col3" >0.50</td>
      <td id="T_36194_row8_col4" class="data row8 col4" >620,165</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row9" class="row_heading level0 row9" >L13</th>
      <td id="T_36194_row9_col0" class="data row9 col0" >52.70</td>
      <td id="T_36194_row9_col1" class="data row9 col1" >52.10</td>
      <td id="T_36194_row9_col2" class="data row9 col2" >-0.60</td>
      <td id="T_36194_row9_col3" class="data row9 col3" >0.60</td>
      <td id="T_36194_row9_col4" class="data row9 col4" >1,799,252</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row10" class="row_heading level0 row10" >L8</th>
      <td id="T_36194_row10_col0" class="data row10 col0" >60.00</td>
      <td id="T_36194_row10_col1" class="data row10 col1" >58.70</td>
      <td id="T_36194_row10_col2" class="data row10 col2" >-1.30</td>
      <td id="T_36194_row10_col3" class="data row10 col3" >0.40</td>
      <td id="T_36194_row10_col4" class="data row10 col4" >1,358,981</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row11" class="row_heading level0 row11" >L15</th>
      <td id="T_36194_row11_col0" class="data row11 col0" >61.70</td>
      <td id="T_36194_row11_col1" class="data row11 col1" >60.20</td>
      <td id="T_36194_row11_col2" class="data row11 col2" >-1.50</td>
      <td id="T_36194_row11_col3" class="data row11 col3" >0.10</td>
      <td id="T_36194_row11_col4" class="data row11 col4" >437,069</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row12" class="row_heading level0 row12" >L17</th>
      <td id="T_36194_row12_col0" class="data row12 col0" >48.30</td>
      <td id="T_36194_row12_col1" class="data row12 col1" >46.40</td>
      <td id="T_36194_row12_col2" class="data row12 col2" >-1.90</td>
      <td id="T_36194_row12_col3" class="data row12 col3" >0.70</td>
      <td id="T_36194_row12_col4" class="data row12 col4" >954,245</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row13" class="row_heading level0 row13" >L4</th>
      <td id="T_36194_row13_col0" class="data row13 col0" >57.80</td>
      <td id="T_36194_row13_col1" class="data row13 col1" >56.00</td>
      <td id="T_36194_row13_col2" class="data row13 col2" >-1.90</td>
      <td id="T_36194_row13_col3" class="data row13 col3" >0.40</td>
      <td id="T_36194_row13_col4" class="data row13 col4" >1,449,569</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row14" class="row_heading level0 row14" >L51</th>
      <td id="T_36194_row14_col0" class="data row14 col0" >41.90</td>
      <td id="T_36194_row14_col1" class="data row14 col1" >39.70</td>
      <td id="T_36194_row14_col2" class="data row14 col2" >-2.20</td>
      <td id="T_36194_row14_col3" class="data row14 col3" >0.80</td>
      <td id="T_36194_row14_col4" class="data row14 col4" >31,249</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row15" class="row_heading level0 row15" >L10</th>
      <td id="T_36194_row15_col0" class="data row15 col0" >60.60</td>
      <td id="T_36194_row15_col1" class="data row15 col1" >58.00</td>
      <td id="T_36194_row15_col2" class="data row15 col2" >-2.60</td>
      <td id="T_36194_row15_col3" class="data row15 col3" >0.80</td>
      <td id="T_36194_row15_col4" class="data row15 col4" >1,352,660</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row16" class="row_heading level0 row16" >L12</th>
      <td id="T_36194_row16_col0" class="data row16 col0" >52.40</td>
      <td id="T_36194_row16_col1" class="data row16 col1" >49.70</td>
      <td id="T_36194_row16_col2" class="data row16 col2" >-2.70</td>
      <td id="T_36194_row16_col3" class="data row16 col3" >0.60</td>
      <td id="T_36194_row16_col4" class="data row16 col4" >559,110</td>
    </tr>
    <tr>
      <th id="T_36194_level0_row17" class="row_heading level0 row17" >L50</th>
      <td id="T_36194_row17_col0" class="data row17 col0" >47.90</td>
      <td id="T_36194_row17_col1" class="data row17 col1" >42.90</td>
      <td id="T_36194_row17_col2" class="data row17 col2" >-5.00</td>
      <td id="T_36194_row17_col3" class="data row17 col3" >2.20</td>
      <td id="T_36194_row17_col4" class="data row17 col4" >38,247</td>
    </tr>
  </tbody>
</table>



## Key Findings

→ Vollständige Findings-Tabelle mit Impact und Action in [`03_analysis_0-overview.ipynb`](03_analysis_0-overview.ipynb).

| ID | Finding | Status | Präsentation |
|:---|:---|:---|:---|
| F-EVNT-01 | Feiertagseffekt gegenläufig: Feiertage 46.3s vs. Normal 56.2s (−9.9s, OTP +3.6pp) — Berufsverkehrsreduktion überwiegt klar | done | — |
| F-EVNT-02 | Event-Skalierung bestätigt: Gross +10.5s (66.7s), Mittel +2.7s, **Klein ≈ +0.05s (=Normal)**. `event_weight` ist ordinales Feature; Klasse 1 hat kaum Vorhersagekraft. | done | `story` |
| F-EVNT-03 | Event-Effekt ist primär **Abend-Phänomen (18–22h)** — tagsüber kein Unterschied. Erklärt den 21h-Spike aus F-TEMP-01. Nacht-Spike 2h (+59.9s): Heimkehrer nach Events. | done | `story` |
| F-EVNT-04 | **Fachmessen** schlechteste Kategorie (66.0s, OTP 84%) — nicht Konzerte. Fachmessen + Kongresse strukturell gleich (L11-Korridor, mehrere Tage). Konzerte 61.4s, Super League 53.8s nahe Normal. | done | `hot` |
| F-EVNT-05 | Events selten: Gross n=724k vs. Normal 70.5M — stark unbalanced. `is_holiday` als stärkstes einzelnes Event-Feature (−9.9s Effekt). | done | — |
| F-EVNT-06 | Stadtkreis-Δ auf Event-Tagen minimal (max +3.0s in Kreis 2). Kreis 11 (Hallenstadion-Korridor) überraschend leicht besser (−0.8s) — räumliche Aggregation verbirgt Abend-Effekt. Feature-Empfehlung: `has_event × hour` Interaktion. | done | — |
| F-EVNT-07 | **November-Peak erklärt:** Top-30 Event-Tage dominiert von Fachmessen (17/30). Berufsmesse Zürich Nov 2024: 192.5s / OTP 54.5% — schlechtester Tag im gesamten Datensatz. Selbst Taylor Swift (75.4s) schlägt eine Berufsmesse nicht. | done | `hot` |
| F-EVNT-08 | **Räumliche Muster:** K9=Ausstrahlungskorridor (Linie 2 Richtung Schlieren), K2=Bahnhof/Stadion-Zugang, K4=FCZ-Stadion-Korridor, K3=Innenstadt-Effekt. K9 ist nicht selbst Eventort — trägt die Konsequenzen. | done | `story` |
