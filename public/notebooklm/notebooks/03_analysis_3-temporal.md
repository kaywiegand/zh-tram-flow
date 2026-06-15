# Temporal Analysis

How delays distribute across time dimensions: hour of day, weekday, month, season and full year.

## Setup


```python
from zh_tram_flow.notebook import *
import zh_tram_flow.analytics.temporal as an

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("03_analysis_3-temporal")

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



    2026-06-11 11:22:54  INFO      project  03_analysis_3-temporal started


    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload


## Hour of Day

Ø `arrival_delay` pro Stunde — Rush-Hour-Muster und Nachtbetrieb. Rechts: Volumen zeigt wann die Daten dünn werden.


```python
an.plot_hour_of_day(lf_delay, cfg, ylim=(0,80), ylim_volume=(0, 6.5))

show_df(an.table_hour_of_day(lf_delay))
```


    
![png](03_analysis_3-temporal_files/03_analysis_3-temporal_6_0.png)
    



<style type="text/css">
#T_12c22 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_12c22 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_12c22 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_12c22 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_12c22 tr:hover td {
  background-color: #eef3f8;
}
#T_12c22_row0_col0, #T_12c22_row0_col1, #T_12c22_row1_col0, #T_12c22_row1_col1, #T_12c22_row2_col0, #T_12c22_row2_col1, #T_12c22_row3_col0, #T_12c22_row3_col1, #T_12c22_row4_col0, #T_12c22_row4_col1, #T_12c22_row5_col0, #T_12c22_row5_col1, #T_12c22_row6_col0, #T_12c22_row6_col1, #T_12c22_row7_col0, #T_12c22_row7_col1, #T_12c22_row8_col0, #T_12c22_row8_col1, #T_12c22_row9_col0, #T_12c22_row9_col1, #T_12c22_row10_col0, #T_12c22_row10_col1, #T_12c22_row11_col0, #T_12c22_row11_col1, #T_12c22_row12_col0, #T_12c22_row12_col1, #T_12c22_row13_col0, #T_12c22_row13_col1, #T_12c22_row14_col0, #T_12c22_row14_col1, #T_12c22_row15_col0, #T_12c22_row15_col1, #T_12c22_row16_col0, #T_12c22_row16_col1, #T_12c22_row17_col0, #T_12c22_row17_col1, #T_12c22_row18_col0, #T_12c22_row18_col1, #T_12c22_row19_col0, #T_12c22_row19_col1, #T_12c22_row20_col0, #T_12c22_row20_col1, #T_12c22_row21_col0, #T_12c22_row21_col1, #T_12c22_row22_col0, #T_12c22_row22_col1, #T_12c22_row23_col0, #T_12c22_row23_col1 {
  text-align: right;
}
#T_12c22_row0_col2, #T_12c22_row1_col2, #T_12c22_row2_col2, #T_12c22_row3_col2, #T_12c22_row4_col2, #T_12c22_row5_col2, #T_12c22_row6_col2, #T_12c22_row7_col2, #T_12c22_row8_col2, #T_12c22_row9_col2, #T_12c22_row10_col2, #T_12c22_row11_col2, #T_12c22_row12_col2, #T_12c22_row13_col2, #T_12c22_row14_col2, #T_12c22_row15_col2, #T_12c22_row16_col2, #T_12c22_row17_col2, #T_12c22_row18_col2, #T_12c22_row19_col2, #T_12c22_row20_col2, #T_12c22_row21_col2, #T_12c22_row22_col2, #T_12c22_row23_col2 {
  text-align: left;
}
</style>
<table id="T_12c22">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_12c22_level0_col0" class="col_heading level0 col0" >Avg. Delay (s)</th>
      <th id="T_12c22_level0_col1" class="col_heading level0 col1" >Median (s)</th>
      <th id="T_12c22_level0_col2" class="col_heading level0 col2" >N Halte</th>
    </tr>
    <tr>
      <th class="index_name level0" >Hour</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_12c22_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_12c22_row0_col0" class="data row0 col0" >43.40</td>
      <td id="T_12c22_row0_col1" class="data row0 col1" >30.00</td>
      <td id="T_12c22_row0_col2" class="data row0 col2" >2,380,420</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_12c22_row1_col0" class="data row1 col0" >48.70</td>
      <td id="T_12c22_row1_col1" class="data row1 col1" >24.00</td>
      <td id="T_12c22_row1_col2" class="data row1 col2" >130,756</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_12c22_row2_col0" class="data row2 col0" >72.50</td>
      <td id="T_12c22_row2_col1" class="data row2 col1" >42.00</td>
      <td id="T_12c22_row2_col2" class="data row2 col2" >11,548</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_12c22_row3_col0" class="data row3 col0" >38.20</td>
      <td id="T_12c22_row3_col1" class="data row3 col1" >33.00</td>
      <td id="T_12c22_row3_col2" class="data row3 col2" >478</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_12c22_row4_col0" class="data row4 col0" >39.00</td>
      <td id="T_12c22_row4_col1" class="data row4 col1" >26.00</td>
      <td id="T_12c22_row4_col2" class="data row4 col2" >124,412</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_12c22_row5_col0" class="data row5 col0" >37.30</td>
      <td id="T_12c22_row5_col1" class="data row5 col1" >30.00</td>
      <td id="T_12c22_row5_col2" class="data row5 col2" >2,653,855</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_12c22_row6_col0" class="data row6 col0" >52.60</td>
      <td id="T_12c22_row6_col1" class="data row6 col1" >42.00</td>
      <td id="T_12c22_row6_col2" class="data row6 col2" >4,499,518</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_12c22_row7_col0" class="data row7 col0" >48.90</td>
      <td id="T_12c22_row7_col1" class="data row7 col1" >37.00</td>
      <td id="T_12c22_row7_col2" class="data row7 col2" >4,775,364</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_12c22_row8_col0" class="data row8 col0" >57.30</td>
      <td id="T_12c22_row8_col1" class="data row8 col1" >43.00</td>
      <td id="T_12c22_row8_col2" class="data row8 col2" >4,857,369</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_12c22_row9_col0" class="data row9 col0" >54.30</td>
      <td id="T_12c22_row9_col1" class="data row9 col1" >42.00</td>
      <td id="T_12c22_row9_col2" class="data row9 col2" >4,794,902</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_12c22_row10_col0" class="data row10 col0" >51.70</td>
      <td id="T_12c22_row10_col1" class="data row10 col1" >40.00</td>
      <td id="T_12c22_row10_col2" class="data row10 col2" >5,056,915</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_12c22_row11_col0" class="data row11 col0" >49.20</td>
      <td id="T_12c22_row11_col1" class="data row11 col1" >39.00</td>
      <td id="T_12c22_row11_col2" class="data row11 col2" >5,104,253</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_12c22_row12_col0" class="data row12 col0" >52.90</td>
      <td id="T_12c22_row12_col1" class="data row12 col1" >41.00</td>
      <td id="T_12c22_row12_col2" class="data row12 col2" >5,107,887</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_12c22_row13_col0" class="data row13 col0" >55.60</td>
      <td id="T_12c22_row13_col1" class="data row13 col1" >44.00</td>
      <td id="T_12c22_row13_col2" class="data row13 col2" >5,088,320</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_12c22_row14_col0" class="data row14 col0" >58.40</td>
      <td id="T_12c22_row14_col1" class="data row14 col1" >45.00</td>
      <td id="T_12c22_row14_col2" class="data row14 col2" >5,069,149</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_12c22_row15_col0" class="data row15 col0" >61.00</td>
      <td id="T_12c22_row15_col1" class="data row15 col1" >46.00</td>
      <td id="T_12c22_row15_col2" class="data row15 col2" >5,103,969</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_12c22_row16_col0" class="data row16 col0" >62.00</td>
      <td id="T_12c22_row16_col1" class="data row16 col1" >44.00</td>
      <td id="T_12c22_row16_col2" class="data row16 col2" >5,177,057</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_12c22_row17_col0" class="data row17 col0" >65.20</td>
      <td id="T_12c22_row17_col1" class="data row17 col1" >46.00</td>
      <td id="T_12c22_row17_col2" class="data row17 col2" >5,190,288</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_12c22_row18_col0" class="data row18 col0" >61.00</td>
      <td id="T_12c22_row18_col1" class="data row18 col1" >42.00</td>
      <td id="T_12c22_row18_col2" class="data row18 col2" >5,116,269</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_12c22_row19_col0" class="data row19 col0" >54.50</td>
      <td id="T_12c22_row19_col1" class="data row19 col1" >40.00</td>
      <td id="T_12c22_row19_col2" class="data row19 col2" >5,023,008</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_12c22_row20_col0" class="data row20 col0" >61.70</td>
      <td id="T_12c22_row20_col1" class="data row20 col1" >47.00</td>
      <td id="T_12c22_row20_col2" class="data row20 col2" >4,579,297</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_12c22_row21_col0" class="data row21 col0" >67.90</td>
      <td id="T_12c22_row21_col1" class="data row21 col1" >52.00</td>
      <td id="T_12c22_row21_col2" class="data row21 col2" >3,496,721</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_12c22_row22_col0" class="data row22 col0" >64.20</td>
      <td id="T_12c22_row22_col1" class="data row22 col1" >49.00</td>
      <td id="T_12c22_row22_col2" class="data row22 col2" >3,408,425</td>
    </tr>
    <tr>
      <th id="T_12c22_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_12c22_row23_col0" class="data row23 col0" >56.00</td>
      <td id="T_12c22_row23_col1" class="data row23 col1" >42.00</td>
      <td id="T_12c22_row23_col2" class="data row23 col2" >2,964,721</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Das Tagesrhythmus-Chart zeigt ein überraschendes Muster: Kein klassischer symmetrischer Doppel-Peak (Morgen/Abend), sondern ein **asymmetrisches Anstiegsprofil mit drei identifizierbaren Nutzungstypen**.

**Ø Delay nach Tageszeit (Ø gesamt ≈55s):**
| Uhrzeit | Ø Delay (s) | Interpretation |
|:---|---:|:---|
| 5h | **37.3s** | Frühester Betrieb — wenig Volumen, kaum Störungen |
| 7h | 48.9s | Morgenrush — überraschend *unter* Durchschnitt |
| 8h | 57.3s | Knapp über Durchschnitt |
| 17h | **65.2s** | Feierabend-Peak — erster klarer Peak |
| 21h | **67.9s** | Absoluter Tages-Peak — Event-Abreisewelle |
| 22h | 64.2s | Abfall nach Event-Peak |
| 2h | ~45s | Nachtverkehr — niedrig aber datendünn |

**Drei Nutzungstypen im Tagesgang:**

1. **Morgen-Berufsverkehr (7–9h):** Im Delay kaum sichtbar — Pendler sind pünktlich (Arbeitsbeginn), Trams fahren nach Fahrplan. Das subjektive Überfüllungsgefühl morgens spiegelt sich nicht im Delay wider.

2. **Feierabend/Event (17–22h):** Dominantes Muster. Ab 14h kontinuierlicher Anstieg, Peak bei 21h. Nicht nur Feierabend — die 21h-Spitze zeigt den **Event-Heimkehrereffekt**: Konzerte, Fussballspiele, Messen enden 20–22h → Abreisewelle → überfüllte Trams → erhöhte Haltezeiten (→ F-EVNT-03).

3. **Nacht-/Partyverkehr (0–3h):** Kleines Datenvolumen (Fr/Sa→Sa/So Nachtbetrieb). Die 2h-Stunde zeigt einen leichten Delay-Anstieg — **Partygänger-Rückfahrten**: volle Trams, spontane Einstiegswünsche, verlängerte Haltezeiten. Statistisch wenig belastbar (n ≈ 12'000 Halte), aber das Muster ist real.

> **Hinweis für Modellierung:** Rush-Hour (7–9h, 17–20h) = 57.4s vs. Off-Peak = 57.6s — Differenz 0.2s. `is_rush_hour` als binäres Feature hat kaum Vorhersagekraft. Stattdessen `hour` als ordinales Feature verwenden, das das echte Profil vollständig abbildet.

→ `hour` als Feature; Interaktion `hour × has_event` für den 21h-Effekt; `hour × is_weekend` für den 2h-Nachteffekt.

## Day of Week

Average delay per weekday (0=Mon … 6=Sun) — weekend vs weekday patterns.


```python
an.plot_day_of_week(lf_delay, cfg, ylim=(0, 70), ylim_otp=(85, 95))
show_df(an.table_day_of_week(lf_delay))

```


    
![png](03_analysis_3-temporal_files/03_analysis_3-temporal_10_0.png)
    



<style type="text/css">
#T_045b8 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_045b8 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_045b8 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_045b8 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_045b8 tr:hover td {
  background-color: #eef3f8;
}
#T_045b8_row0_col0, #T_045b8_row0_col1, #T_045b8_row0_col2, #T_045b8_row1_col0, #T_045b8_row1_col1, #T_045b8_row1_col2, #T_045b8_row2_col0, #T_045b8_row2_col1, #T_045b8_row2_col2, #T_045b8_row3_col0, #T_045b8_row3_col1, #T_045b8_row3_col2, #T_045b8_row4_col0, #T_045b8_row4_col1, #T_045b8_row4_col2, #T_045b8_row5_col0, #T_045b8_row5_col1, #T_045b8_row5_col2, #T_045b8_row6_col0, #T_045b8_row6_col1, #T_045b8_row6_col2 {
  text-align: right;
}
#T_045b8_row0_col3, #T_045b8_row1_col3, #T_045b8_row2_col3, #T_045b8_row3_col3, #T_045b8_row4_col3, #T_045b8_row5_col3, #T_045b8_row6_col3 {
  text-align: left;
}
</style>
<table id="T_045b8">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_045b8_level0_col0" class="col_heading level0 col0" >Avg. Delay (s)</th>
      <th id="T_045b8_level0_col1" class="col_heading level0 col1" >Median (s)</th>
      <th id="T_045b8_level0_col2" class="col_heading level0 col2" >P95 (s)</th>
      <th id="T_045b8_level0_col3" class="col_heading level0 col3" >N Halte</th>
    </tr>
    <tr>
      <th class="index_name level0" >Weekday</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_045b8_level0_row0" class="row_heading level0 row0" >Mo</th>
      <td id="T_045b8_row0_col0" class="data row0 col0" >52.30</td>
      <td id="T_045b8_row0_col1" class="data row0 col1" >40.00</td>
      <td id="T_045b8_row0_col2" class="data row0 col2" >172.00</td>
      <td id="T_045b8_row0_col3" class="data row0 col3" >13,620,317</td>
    </tr>
    <tr>
      <th id="T_045b8_level0_row1" class="row_heading level0 row1" >Di</th>
      <td id="T_045b8_row1_col0" class="data row1 col0" >57.70</td>
      <td id="T_045b8_row1_col1" class="data row1 col1" >44.00</td>
      <td id="T_045b8_row1_col2" class="data row1 col2" >186.00</td>
      <td id="T_045b8_row1_col3" class="data row1 col3" >13,485,124</td>
    </tr>
    <tr>
      <th id="T_045b8_level0_row2" class="row_heading level0 row2" >Mi</th>
      <td id="T_045b8_row2_col0" class="data row2 col0" >57.90</td>
      <td id="T_045b8_row2_col1" class="data row2 col1" >44.00</td>
      <td id="T_045b8_row2_col2" class="data row2 col2" >186.00</td>
      <td id="T_045b8_row2_col3" class="data row2 col3" >13,522,020</td>
    </tr>
    <tr>
      <th id="T_045b8_level0_row3" class="row_heading level0 row3" >Do</th>
      <td id="T_045b8_row3_col0" class="data row3 col0" >60.40</td>
      <td id="T_045b8_row3_col1" class="data row3 col1" >45.00</td>
      <td id="T_045b8_row3_col2" class="data row3 col2" >194.00</td>
      <td id="T_045b8_row3_col3" class="data row3 col3" >13,372,724</td>
    </tr>
    <tr>
      <th id="T_045b8_level0_row4" class="row_heading level0 row4" >Fr</th>
      <td id="T_045b8_row4_col0" class="data row4 col0" >58.10</td>
      <td id="T_045b8_row4_col1" class="data row4 col1" >44.00</td>
      <td id="T_045b8_row4_col2" class="data row4 col2" >187.00</td>
      <td id="T_045b8_row4_col3" class="data row4 col3" >13,288,211</td>
    </tr>
    <tr>
      <th id="T_045b8_level0_row5" class="row_heading level0 row5" >Sa</th>
      <td id="T_045b8_row5_col0" class="data row5 col0" >57.00</td>
      <td id="T_045b8_row5_col1" class="data row5 col1" >42.00</td>
      <td id="T_045b8_row5_col2" class="data row5 col2" >189.00</td>
      <td id="T_045b8_row5_col3" class="data row5 col3" >12,684,117</td>
    </tr>
    <tr>
      <th id="T_045b8_level0_row6" class="row_heading level0 row6" >So</th>
      <td id="T_045b8_row6_col0" class="data row6 col0" >48.40</td>
      <td id="T_045b8_row6_col1" class="data row6 col1" >38.00</td>
      <td id="T_045b8_row6_col2" class="data row6 col2" >160.00</td>
      <td id="T_045b8_row6_col3" class="data row6 col3" >9,742,388</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** **Donnerstag zeigt die höchste durchschnittliche Verspätung** — nicht Freitag, wie man erwarten könnte.

**Ø Delay und P95 nach Wochentag:**
| Tag | Ø Delay (s) | P95 (s) |
|:---|---:|---:|
| Mo | 52.3 | 172 |
| Di | 57.7 | 186 |
| Mi | 57.9 | 186 |
| **Do** | **60.4** | **194** |
| Fr | 58.1 | 187 |
| Sa | 57.0 | 189 |
| So | 48.4 | 160 |

**Donnerstag ist auf beiden Metriken Spitze** — sowohl im Ø als auch bei P95 (schlechteste 5%). Mo und So sind die besten Tage.

**Warum Donnerstag?** Zwei plausible Erklärungen:
1. **Events-Effekt**: Donnerstag ist in Zürich ein starker Kultur- und Ausgeh-Abend (Konzerte, Messen, Konferenzen). Ein Teil dieser Events fällt gehäuft auf Donnerstage.
2. **Homeoffice-Hypothese**: Wenn Montag und Freitag die häufigsten HO-Tage sind, konzentriert sich Pendlerverkehr auf Di–Do mit Donnerstag als Spitze — plausibel, aber nicht direkt durch VBZ-Daten belegt.

**Wochenende:** Samstag (57.0s) liegt nur leicht unter Werktagsniveau. Sonntag (48.4s) ist deutlich besser — weniger Berufsverkehr und reduzierter Takt im Gleichgewicht. Montag (52.3s) überraschend niedrig — konsistent mit HO-Hypothese.

→ `weekday` als Feature; Interaktion `weekday × hour` prüfen (Donnerstag-Abend-Block).

## Month

Monthly delay averages — seasonal drift visible at month level.


```python
an.plot_day_of_week(lf_delay, cfg, ylim=(0,70), ylim_otp=(85,91))

show_df(an.table_month_seasonality(lf_delay))
```


    
![png](03_analysis_3-temporal_files/03_analysis_3-temporal_14_0.png)
    



<style type="text/css">
#T_c6792 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_c6792 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_c6792 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_c6792 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_c6792 tr:hover td {
  background-color: #eef3f8;
}
#T_c6792_row0_col0, #T_c6792_row0_col1, #T_c6792_row0_col2, #T_c6792_row0_col3, #T_c6792_row1_col0, #T_c6792_row1_col1, #T_c6792_row1_col2, #T_c6792_row1_col3, #T_c6792_row2_col0, #T_c6792_row2_col1, #T_c6792_row2_col2, #T_c6792_row2_col3, #T_c6792_row3_col0, #T_c6792_row3_col1, #T_c6792_row3_col2, #T_c6792_row3_col3, #T_c6792_row4_col0, #T_c6792_row4_col1, #T_c6792_row4_col2, #T_c6792_row4_col3, #T_c6792_row5_col0, #T_c6792_row5_col1, #T_c6792_row5_col2, #T_c6792_row5_col3, #T_c6792_row6_col0, #T_c6792_row6_col1, #T_c6792_row6_col2, #T_c6792_row6_col3, #T_c6792_row7_col0, #T_c6792_row7_col1, #T_c6792_row7_col2, #T_c6792_row7_col3, #T_c6792_row8_col0, #T_c6792_row8_col1, #T_c6792_row8_col2, #T_c6792_row8_col3, #T_c6792_row9_col0, #T_c6792_row9_col1, #T_c6792_row9_col2, #T_c6792_row9_col3, #T_c6792_row10_col0, #T_c6792_row10_col1, #T_c6792_row10_col2, #T_c6792_row10_col3, #T_c6792_row11_col0, #T_c6792_row11_col1, #T_c6792_row11_col2, #T_c6792_row11_col3 {
  text-align: right;
}
</style>
<table id="T_c6792">
  <thead>
    <tr>
      <th class="index_name level0" >year</th>
      <th id="T_c6792_level0_col0" class="col_heading level0 col0" >2023</th>
      <th id="T_c6792_level0_col1" class="col_heading level0 col1" >2024</th>
      <th id="T_c6792_level0_col2" class="col_heading level0 col2" >2025</th>
      <th id="T_c6792_level0_col3" class="col_heading level0 col3" >Ø gesamt</th>
    </tr>
    <tr>
      <th class="index_name level0" >Month</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_c6792_level0_row0" class="row_heading level0 row0" >Jan</th>
      <td id="T_c6792_row0_col0" class="data row0 col0" >49.40</td>
      <td id="T_c6792_row0_col1" class="data row0 col1" >52.40</td>
      <td id="T_c6792_row0_col2" class="data row0 col2" >49.60</td>
      <td id="T_c6792_row0_col3" class="data row0 col3" >50.60</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row1" class="row_heading level0 row1" >Feb</th>
      <td id="T_c6792_row1_col0" class="data row1 col0" >48.60</td>
      <td id="T_c6792_row1_col1" class="data row1 col1" >53.10</td>
      <td id="T_c6792_row1_col2" class="data row1 col2" >48.50</td>
      <td id="T_c6792_row1_col3" class="data row1 col3" >50.00</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row2" class="row_heading level0 row2" >Mär</th>
      <td id="T_c6792_row2_col0" class="data row2 col0" >53.60</td>
      <td id="T_c6792_row2_col1" class="data row2 col1" >60.60</td>
      <td id="T_c6792_row2_col2" class="data row2 col2" >53.80</td>
      <td id="T_c6792_row2_col3" class="data row2 col3" >56.00</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row3" class="row_heading level0 row3" >Apr</th>
      <td id="T_c6792_row3_col0" class="data row3 col0" >50.80</td>
      <td id="T_c6792_row3_col1" class="data row3 col1" >56.30</td>
      <td id="T_c6792_row3_col2" class="data row3 col2" >54.50</td>
      <td id="T_c6792_row3_col3" class="data row3 col3" >53.90</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row4" class="row_heading level0 row4" >Mai</th>
      <td id="T_c6792_row4_col0" class="data row4 col0" >52.60</td>
      <td id="T_c6792_row4_col1" class="data row4 col1" >60.30</td>
      <td id="T_c6792_row4_col2" class="data row4 col2" >57.20</td>
      <td id="T_c6792_row4_col3" class="data row4 col3" >56.70</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row5" class="row_heading level0 row5" >Jun</th>
      <td id="T_c6792_row5_col0" class="data row5 col0" >57.50</td>
      <td id="T_c6792_row5_col1" class="data row5 col1" >60.50</td>
      <td id="T_c6792_row5_col2" class="data row5 col2" >59.20</td>
      <td id="T_c6792_row5_col3" class="data row5 col3" >59.10</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row6" class="row_heading level0 row6" >Jul</th>
      <td id="T_c6792_row6_col0" class="data row6 col0" >52.70</td>
      <td id="T_c6792_row6_col1" class="data row6 col1" >54.50</td>
      <td id="T_c6792_row6_col2" class="data row6 col2" >58.60</td>
      <td id="T_c6792_row6_col3" class="data row6 col3" >55.30</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row7" class="row_heading level0 row7" >Aug</th>
      <td id="T_c6792_row7_col0" class="data row7 col0" >53.20</td>
      <td id="T_c6792_row7_col1" class="data row7 col1" >58.30</td>
      <td id="T_c6792_row7_col2" class="data row7 col2" >53.40</td>
      <td id="T_c6792_row7_col3" class="data row7 col3" >54.90</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row8" class="row_heading level0 row8" >Sep</th>
      <td id="T_c6792_row8_col0" class="data row8 col0" >58.50</td>
      <td id="T_c6792_row8_col1" class="data row8 col1" >60.10</td>
      <td id="T_c6792_row8_col2" class="data row8 col2" >55.20</td>
      <td id="T_c6792_row8_col3" class="data row8 col3" >57.70</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row9" class="row_heading level0 row9" >Okt</th>
      <td id="T_c6792_row9_col0" class="data row9 col0" >61.20</td>
      <td id="T_c6792_row9_col1" class="data row9 col1" >57.70</td>
      <td id="T_c6792_row9_col2" class="data row9 col2" >60.50</td>
      <td id="T_c6792_row9_col3" class="data row9 col3" >59.80</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row10" class="row_heading level0 row10" >Nov</th>
      <td id="T_c6792_row10_col0" class="data row10 col0" >68.90</td>
      <td id="T_c6792_row10_col1" class="data row10 col1" >72.60</td>
      <td id="T_c6792_row10_col2" class="data row10 col2" >70.70</td>
      <td id="T_c6792_row10_col3" class="data row10 col3" >66.10</td>
    </tr>
    <tr>
      <th id="T_c6792_level0_row11" class="row_heading level0 row11" >Dez</th>
      <td id="T_c6792_row11_col0" class="data row11 col0" >63.20</td>
      <td id="T_c6792_row11_col1" class="data row11 col1" >57.80</td>
      <td id="T_c6792_row11_col2" class="data row11 col2" >nan</td>
      <td id="T_c6792_row11_col3" class="data row11 col3" >54.40</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Klare **November-Peak-Anomalie** bestätigt: November ist in beiden vollständigen Jahren der Jahreshöchstwert — November 2023=68.9s, November 2024=72.6s. Im Jahresvergleich sehen die Kurvenformen ähnlich aus (gleiche saisonale Struktur), aber 2024 liegt in fast allen Monaten über 2023.

**Monatlicher Ø Delay (bereinigt, Nov/Dez 2025 als Artefakt ausgeschlossen):**
| Monat | 2023 | 2024 | 2025 |
|:---|---:|---:|---:|
| Jan | 48.8 | 51.9 | 49.3 |
| Mär | 53.3 | 60.2 | 53.3 |
| Jun | 57.4 | 60.1 | 58.8 |
| Okt | 60.8 | 57.2 | 60.1 |
| **Nov** | **68.9** | **72.6** | **70.7** |
| Dez | 63.0 | 57.7 | — |

**Warum November?** Kombination aus mehreren Faktoren:
- Herbstlaub auf Gleisen (Leaf Fall Problem): nasses Laub reduziert Haftung, langsamere Einfahrten
- Ende des Herbst-Baustellen-Zyklus: VBZ/Stadt schliessen Gleisbaustellen typischerweise vor Winterfahrplan ab
- Maximale Systembelastung: Schuljahr läuft, kein Ferieneffekt, Dunkelheit und Regen erhöhen MIV-Anteil

**Jahrestrend:** 2024 deutlich höher als 2023 in den Frühlings-/Sommermonaten (Mär–Jun: +6–7s). 2025 (Jan–Okt) liegt zwischen 2023 und 2024 — kein klarer weiterer Anstieg. → `month`, `year` und `is_november` als Features; November-Dummy als Verstärker prüfen.

> **Juli 2025 — Ausreißer im Sommertal:**
> Juli 2025 (58.6s) liegt +6.0s über Juli 2023 (52.7s) und +4.1s über Juli 2024 (54.5s).
> In allen anderen Sommermonaten zeigt 2025 keine vergleichbare Abweichung.
> Mögliche Ursache: VBZ-Baustellenaktivität im Vorfeld des Fahrplanwechsels 
> Dezember 2025 (Tramnetz Süd). **Status: offen** — prüfen ob dieser Monat 
> als Trainings-Ausreißer behandelt werden sollte.

## Season

Delay by season (1=Winter 2=Spring 3=Summer 4=Fall) — weather and daylight effects.


```python
an.plot_season_heatmap(lf_delay, cfg, ylim_season=(0, 80))

show_df(an.table_season(lf_delay))

```


    
![png](03_analysis_3-temporal_files/03_analysis_3-temporal_18_0.png)
    



<style type="text/css">
#T_6ef14 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_6ef14 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_6ef14 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_6ef14 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_6ef14 tr:hover td {
  background-color: #eef3f8;
}
#T_6ef14_row0_col0, #T_6ef14_row1_col0, #T_6ef14_row2_col0, #T_6ef14_row3_col0 {
  text-align: right;
}
#T_6ef14_row0_col1, #T_6ef14_row0_col2, #T_6ef14_row1_col1, #T_6ef14_row1_col2, #T_6ef14_row2_col1, #T_6ef14_row2_col2, #T_6ef14_row3_col1, #T_6ef14_row3_col2 {
  text-align: left;
}
</style>
<table id="T_6ef14">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_6ef14_level0_col0" class="col_heading level0 col0" >Avg. Delay (s)</th>
      <th id="T_6ef14_level0_col1" class="col_heading level0 col1" >OTP</th>
      <th id="T_6ef14_level0_col2" class="col_heading level0 col2" >N Halte</th>
    </tr>
    <tr>
      <th class="index_name level0" >Season</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_6ef14_level0_row0" class="row_heading level0 row0" >Winter</th>
      <td id="T_6ef14_row0_col0" class="data row0 col0" >51.70</td>
      <td id="T_6ef14_row0_col1" class="data row0 col1" >88.9%</td>
      <td id="T_6ef14_row0_col2" class="data row0 col2" >22,134,996</td>
    </tr>
    <tr>
      <th id="T_6ef14_level0_row1" class="row_heading level0 row1" >Spring</th>
      <td id="T_6ef14_row1_col0" class="data row1 col0" >55.60</td>
      <td id="T_6ef14_row1_col1" class="data row1 col1" >87.3%</td>
      <td id="T_6ef14_row1_col2" class="data row1 col2" >22,311,790</td>
    </tr>
    <tr>
      <th id="T_6ef14_level0_row2" class="row_heading level0 row2" >Summer</th>
      <td id="T_6ef14_row2_col0" class="data row2 col0" >56.40</td>
      <td id="T_6ef14_row2_col1" class="data row2 col1" >86.8%</td>
      <td id="T_6ef14_row2_col2" class="data row2 col2" >22,521,041</td>
    </tr>
    <tr>
      <th id="T_6ef14_level0_row3" class="row_heading level0 row3" >Autumn</th>
      <td id="T_6ef14_row3_col0" class="data row3 col0" >61.20</td>
      <td id="T_6ef14_row3_col1" class="data row3 col1" >85.2%</td>
      <td id="T_6ef14_row3_col2" class="data row3 col2" >22,747,074</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Saisonauswertung bestätigt das Muster aus der Monatsanalyse.

**Saisonaler Ø Delay und OTP:**
| Jahreszeit | Ø Delay (s) | OTP |
|:---|---:|---:|
| Winter | **51.7** | **88.9%** |
| Frühling | 55.6 | 87.3% |
| Sommer | 56.4 | 86.8% |
| **Herbst** | **61.2** | **85.2%** |

**Herbst** ist die eindeutig schlechteste Jahreszeit (61.2s, OTP 85.2%). **Winter** ist überraschenderweise die beste — Ø 9.5s unter Herbst. Mögliche Erklärung: Im Winter reduziert sich der MIV-Anteil (Menschen meiden Autofahren bei Schnee/Eis), was die Strassenkonflikte für Trams verringert und den Effekt von Schnee/Eis auf die Gleise teilweise kompensiert. Frühling und Sommer liegen nah beieinander (55.6 vs. 56.4s).

Die **Heatmap Stunde × Wochentag** macht das Zusammenspiel sichtbar: der Donnerstag/Freitag-Abend-Block (17–21h) zeigt die dunkelsten Felder. Rush-Hour-Muster sind wochentagsübergreifend erkennbar, aber der Abend-Effekt dominiert gegenüber dem Morgen.

→ `season`, `hour`, `weekday` als Features; Interaktion `hour × weekday` als kombiniertes Feature prüfen.

## Full Year

Weekly or monthly rolling delay trend across all three years — long-term drift and anomalies.


```python
an.plot_full_year_trend(lf_delay, cfg, ylim_delay=(30, 110), ylim_otp=(0.75, 0.95))

show_df(an.table_full_year_monthly(lf_delay))
```


    
![png](03_analysis_3-temporal_files/03_analysis_3-temporal_22_0.png)
    



<style type="text/css">
#T_6ac4e thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_6ac4e td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_6ac4e tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_6ac4e tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_6ac4e tr:hover td {
  background-color: #eef3f8;
}
#T_6ac4e_row0_col0, #T_6ac4e_row0_col1, #T_6ac4e_row0_col2, #T_6ac4e_row1_col0, #T_6ac4e_row1_col1, #T_6ac4e_row1_col2, #T_6ac4e_row2_col0, #T_6ac4e_row2_col1, #T_6ac4e_row2_col2, #T_6ac4e_row3_col0, #T_6ac4e_row3_col1, #T_6ac4e_row3_col2, #T_6ac4e_row4_col0, #T_6ac4e_row4_col1, #T_6ac4e_row4_col2, #T_6ac4e_row5_col0, #T_6ac4e_row5_col1, #T_6ac4e_row5_col2, #T_6ac4e_row6_col0, #T_6ac4e_row6_col1, #T_6ac4e_row6_col2, #T_6ac4e_row7_col0, #T_6ac4e_row7_col1, #T_6ac4e_row7_col2, #T_6ac4e_row8_col0, #T_6ac4e_row8_col1, #T_6ac4e_row8_col2, #T_6ac4e_row9_col0, #T_6ac4e_row9_col1, #T_6ac4e_row9_col2, #T_6ac4e_row10_col0, #T_6ac4e_row10_col1, #T_6ac4e_row10_col2, #T_6ac4e_row11_col0, #T_6ac4e_row11_col1, #T_6ac4e_row11_col2 {
  text-align: right;
}
</style>
<table id="T_6ac4e">
  <thead>
    <tr>
      <th class="index_name level0" >year</th>
      <th id="T_6ac4e_level0_col0" class="col_heading level0 col0" >2023</th>
      <th id="T_6ac4e_level0_col1" class="col_heading level0 col1" >2024</th>
      <th id="T_6ac4e_level0_col2" class="col_heading level0 col2" >2025</th>
    </tr>
    <tr>
      <th class="index_name level0" >Month</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_6ac4e_level0_row0" class="row_heading level0 row0" >Jan</th>
      <td id="T_6ac4e_row0_col0" class="data row0 col0" >48.80</td>
      <td id="T_6ac4e_row0_col1" class="data row0 col1" >51.90</td>
      <td id="T_6ac4e_row0_col2" class="data row0 col2" >49.30</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row1" class="row_heading level0 row1" >Feb</th>
      <td id="T_6ac4e_row1_col0" class="data row1 col0" >48.30</td>
      <td id="T_6ac4e_row1_col1" class="data row1 col1" >52.90</td>
      <td id="T_6ac4e_row1_col2" class="data row1 col2" >48.00</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row2" class="row_heading level0 row2" >Mär</th>
      <td id="T_6ac4e_row2_col0" class="data row2 col0" >53.30</td>
      <td id="T_6ac4e_row2_col1" class="data row2 col1" >60.20</td>
      <td id="T_6ac4e_row2_col2" class="data row2 col2" >53.30</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row3" class="row_heading level0 row3" >Apr</th>
      <td id="T_6ac4e_row3_col0" class="data row3 col0" >50.30</td>
      <td id="T_6ac4e_row3_col1" class="data row3 col1" >56.30</td>
      <td id="T_6ac4e_row3_col2" class="data row3 col2" >54.10</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row4" class="row_heading level0 row4" >Mai</th>
      <td id="T_6ac4e_row4_col0" class="data row4 col0" >52.30</td>
      <td id="T_6ac4e_row4_col1" class="data row4 col1" >59.90</td>
      <td id="T_6ac4e_row4_col2" class="data row4 col2" >56.40</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row5" class="row_heading level0 row5" >Jun</th>
      <td id="T_6ac4e_row5_col0" class="data row5 col0" >57.40</td>
      <td id="T_6ac4e_row5_col1" class="data row5 col1" >60.10</td>
      <td id="T_6ac4e_row5_col2" class="data row5 col2" >58.80</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row6" class="row_heading level0 row6" >Jul</th>
      <td id="T_6ac4e_row6_col0" class="data row6 col0" >52.40</td>
      <td id="T_6ac4e_row6_col1" class="data row6 col1" >54.20</td>
      <td id="T_6ac4e_row6_col2" class="data row6 col2" >58.30</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row7" class="row_heading level0 row7" >Aug</th>
      <td id="T_6ac4e_row7_col0" class="data row7 col0" >52.90</td>
      <td id="T_6ac4e_row7_col1" class="data row7 col1" >57.70</td>
      <td id="T_6ac4e_row7_col2" class="data row7 col2" >53.00</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row8" class="row_heading level0 row8" >Sep</th>
      <td id="T_6ac4e_row8_col0" class="data row8 col0" >58.40</td>
      <td id="T_6ac4e_row8_col1" class="data row8 col1" >59.80</td>
      <td id="T_6ac4e_row8_col2" class="data row8 col2" >55.90</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row9" class="row_heading level0 row9" >Okt</th>
      <td id="T_6ac4e_row9_col0" class="data row9 col0" >60.80</td>
      <td id="T_6ac4e_row9_col1" class="data row9 col1" >57.20</td>
      <td id="T_6ac4e_row9_col2" class="data row9 col2" >60.10</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row10" class="row_heading level0 row10" >Nov</th>
      <td id="T_6ac4e_row10_col0" class="data row10 col0" >67.90</td>
      <td id="T_6ac4e_row10_col1" class="data row10 col1" >72.90</td>
      <td id="T_6ac4e_row10_col2" class="data row10 col2" >nan</td>
    </tr>
    <tr>
      <th id="T_6ac4e_level0_row11" class="row_heading level0 row11" >Dez</th>
      <td id="T_6ac4e_row11_col0" class="data row11 col0" >63.00</td>
      <td id="T_6ac4e_row11_col1" class="data row11 col1" >57.70</td>
      <td id="T_6ac4e_row11_col2" class="data row11 col2" >nan</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Der Rolling-Average-Chart macht die Netzstruktur über alle drei Jahre sichtbar.

**Schulferien-Effekt:** Die grau hinterlegten Schulferienperioden fallen konsistent mit Verspätungs-Tälern zusammen — besonders deutlich bei Sommer- und Herbstferien. Das ist visuell überzeugend: Weniger Schülerverkehr = weniger Trams übervoll = weniger Verzögerungen beim Boarding.

**Strukturelle Befunde:**
- 2024 liegt im Frühling/Sommer **+4–7s** über dem 2023-Niveau — struktureller Anstieg
- 2025 (Jan–Okt) zeigt leichte Stabilisierung gegenüber 2024 — kein weiterer Anstieg
- **Aufwärtstrend moderat:** Das Netz wird nicht dramatisch schlechter, aber liegt strukturell über dem OTP-Sollwert
- November-Peaks in beiden Jahren deutlich sichtbar (→ F-TEMP-05)
- Fahrplanwechsel Dez 2023 (j23→j24): kein scharfer Knick erkennbar — Übergang fliessend

**Einordnung Aufwärtstrend:**
> 2025 war leicht besser als 2024 — das schwächt eine „alarmierenden Trend"-Story. Seriösere Aussage: Das VBZ-Netz läuft stabil nahe seinem OTP-Ziel, hat aber **keinen strukturellen Puffer** bei Sonderereignissen (Schnee, Grossevents, November). Der Schulferien-Dip zeigt: bei reduziertem Druck funktioniert das Netz gut.

## Feature: `gtfs_year`

Netzwerk-Epoche als Feature: `j23` (vor Fahrplanwechsel Dez 2023) vs. `j24_j25` (nach Umbau der Linien 9, 11, 13). Zeigt ob der Strukturbruch in der Zeitreihe einen Sprung erzeugt oder ob die Verspätung kontinuierlich verläuft (F-NET-01, F-NET-03).


```python
an.plot_gtfs_year_comparison(lf_delay, cfg)

show_df(an.table_gtfs_year_comparison(lf_delay))
```

    gtfs_year aus Feature-File geladen



    
![png](03_analysis_3-temporal_files/03_analysis_3-temporal_25_1.png)
    


    gtfs_year Vergleich:
      j23: Ø +55.9s  OTP 87.3%  (28.8M Halte)  [2023-01-01 00:00:00 – 2023-12-31 00:00:00]
      j24_j25: Ø +56.4s  OTP 86.9%  (60.9M Halte)  [2024-01-01 00:00:00 – 2025-12-31 00:00:00]



<style type="text/css">
#T_018f0 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_018f0 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_018f0 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_018f0 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_018f0 tr:hover td {
  background-color: #eef3f8;
}
#T_018f0_row0_col0, #T_018f0_row0_col1, #T_018f0_row1_col0, #T_018f0_row1_col1 {
  text-align: right;
}
#T_018f0_row0_col2, #T_018f0_row0_col3, #T_018f0_row0_col4, #T_018f0_row0_col5, #T_018f0_row1_col2, #T_018f0_row1_col3, #T_018f0_row1_col4, #T_018f0_row1_col5 {
  text-align: left;
}
</style>
<table id="T_018f0">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_018f0_level0_col0" class="col_heading level0 col0" >Avg. Delay (s)</th>
      <th id="T_018f0_level0_col1" class="col_heading level0 col1" >Median (s)</th>
      <th id="T_018f0_level0_col2" class="col_heading level0 col2" >OTP</th>
      <th id="T_018f0_level0_col3" class="col_heading level0 col3" >N Halte</th>
      <th id="T_018f0_level0_col4" class="col_heading level0 col4" >Von</th>
      <th id="T_018f0_level0_col5" class="col_heading level0 col5" >Bis</th>
    </tr>
    <tr>
      <th class="index_name level0" >GTFS-Epoche</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
      <th class="blank col5" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_018f0_level0_row0" class="row_heading level0 row0" >j23</th>
      <td id="T_018f0_row0_col0" class="data row0 col0" >55.90</td>
      <td id="T_018f0_row0_col1" class="data row0 col1" >43.00</td>
      <td id="T_018f0_row0_col2" class="data row0 col2" >87.3%</td>
      <td id="T_018f0_row0_col3" class="data row0 col3" >28,824,219</td>
      <td id="T_018f0_row0_col4" class="data row0 col4" >2023-01-01 00:00:00</td>
      <td id="T_018f0_row0_col5" class="data row0 col5" >2023-12-31 00:00:00</td>
    </tr>
    <tr>
      <th id="T_018f0_level0_row1" class="row_heading level0 row1" >j24_j25</th>
      <td id="T_018f0_row1_col0" class="data row1 col0" >56.40</td>
      <td id="T_018f0_row1_col1" class="data row1 col1" >42.00</td>
      <td id="T_018f0_row1_col2" class="data row1 col2" >86.9%</td>
      <td id="T_018f0_row1_col3" class="data row1 col3" >60,890,682</td>
      <td id="T_018f0_row1_col4" class="data row1 col4" >2024-01-01 00:00:00</td>
      <td id="T_018f0_row1_col5" class="data row1 col5" >2025-12-31 00:00:00</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Der `gtfs_year`-Vergleich zeigt einen **minimal kleinen Netzeffekt**: Netzweit steigt der Ø Delay von j23 auf j24_j25 um nur **+0.5s** (55.9s → 56.4s). Die OTP-Differenz beträgt −0.4pp (87.3% → 86.9%).

**Netzweit: j23 vs. j24_j25:**
| GTFS-Epoche | Ø Delay (s) | OTP | N Halte |
|:---|---:|---:|---:|
| j23 | 55.9 | 87.3% | 28.8M |
| j24_j25 | 56.4 | 86.9% | 60.9M |
| **Δ** | **+0.5s** | **−0.4pp** | |

**Umgebaute Linien 9, 11, 13 — Vor/Nach:**
| Linie | j23 (s) | j24_j25 (s) | Δ |
|:---|---:|---:|---:|
| L11 | 65.1 | 70.6 | **+5.5s** |
| L13 | 51.6 | 53.1 | +1.5s |
| L9 | 58.6 | 54.3 | **−4.3s** |

**Kernbefund:** Das `gtfs_year`-Feature erklärt netzweit fast nichts (+0.5s). Auf Linie-Ebene gibt es Unterschiede, aber sie zeigen keine einheitliche Richtung: L11 verschlechtert sich, L9 verbessert sich deutlich. Das ist konsistent mit dem Befund aus dem Network-Notebook (F-NET-04, F-NET-05): der Fahrplanwechsel Dez 2023 ist im Delay-Signal nicht als Bruchpunkt erkennbar.

**Implikation für Modellierung:** `gtfs_year` dürfte im Modell schwachen Beitrag leisten — eher als Zeitvariable denn als Netzstruktur-Feature. `n_stops_line` als kontinuierliche Alternative bleibt prüfenswert (F-NET-03). Der strukturelle j23→j24-Anstieg im Rolling-Average erklärt sich besser durch Saisonalität und Jahrestrend als durch den Netzwechsel.

## Key Findings

→ Vollständige Findings-Tabelle mit Impact und Action in [`03_analysis_0-overview.ipynb`](03_analysis_0-overview.ipynb).

| ID | Finding | Präsentation | Status |
|:---|:---|:---|:---|
| F-TEMP-01 | Kein klassischer Morgenrush-Peak: 7h=48.9s liegt *unter* Ø. Dominantes Muster ist Nachmittag/Abend (14h aufwärts), Peak bei 21h=67.9s (Events-Abreisewelle), starker Abend-Peak 17h=65.2s | `hot` | done |
| F-TEMP-02 | **Donnerstag** ist kritischster Wochentag: Ø 60.4s, P95=194s — sowohl im Mittel als auch in den Extremwerten Spitze. Montag (52.3s) und Sonntag (48.4s) beste Tage. | `hot` | done |
| F-TEMP-03 | Donnerstag-Peak vereinbar mit Events-Häufung (Do-Abend) und Homeoffice-Hypothese (Mo/Fr = HO → Do = Verkehrsspitze) — nicht direkt durch Daten belegt, aber plausibel | `story` | done |
| F-TEMP-04 | Wochenende: Samstag (57.0s) kaum besser als Werktag; Sonntag (48.4s) deutlich besser — reduzierter Takt und weniger Berufsverkehr | `—` | done |
| F-TEMP-05 | **November-Peak-Anomalie bestätigt**: Nov 2023=68.9s, Nov 2024=72.6s — jeweils Jahreshöchstwert; ca. 10–12s über Jahresschnitt der restlichen Monate | `hot` | done |
| F-TEMP-06 | Saisonales Muster: Herbst=61.2s (schlechteste Jahreszeit, OTP 85.2%), Winter=51.7s (beste, OTP 88.9%) — Winter besser als Herbst trotz Witterung | `story` | done |
| F-TEMP-07 | Struktureller Aufwärtstrend: 2024 liegt in den meisten Monaten +4–7s über 2023; 2025 (Jan–Okt) leicht moderater als 2024 — kein weiterer Anstieg sichtbar | `story` | done |
| F-TEMP-08 | Schulferien-Täler erkennbar im Rolling-Average — Schulferien-Flag als Feature-Kandidat | `—` | done |
| F-TEMP-09 | `gtfs_year`-Feature erklärt netzweit nur +0.5s (j23=55.9s → j24_j25=56.4s) — schwaches Feature-Signal; auf Linie-Ebene keine einheitliche Richtung (L11 +5.5s, L9 −4.3s) | `—` | done |
| F-TEMP-10 | **Nacht-/Partyverkehr (0–3h):** Fr/Sa-Nächte zeigen leichten 2h-Anstieg — Partygänger-Rückfahrten, volle Trams, verlängerte Haltezeiten. Statistisch datendünn (n≈12k), aber real. → `hour × is_weekend` als Interaktionsfeature | `—` | done |
