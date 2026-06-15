# Weather Impact Analysis

How weather conditions affect `arrival_delay`: rain, heavy rain, wind, snow and temperature.

## Setup


```python
from zh_tram_flow.notebook import *
import zh_tram_flow.analytics.meteo as an

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("03_analysis_5-meteo")

%load_ext autoreload
%autoreload 2
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-06-11 15:45:42  INFO      project  03_analysis_5-meteo started


    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload


## Wetterübersicht — alle Faktoren im Vergleich

Vergleich aller binären Wetterbedingungen auf einen Blick: Regen, starker Regen, Wind, Schnee — jeweils True vs. False. Zeigt welcher Faktor den grössten Einfluss hat.


```python
an.plot_weather_overview(lf_delay, cfg)

show_df(an.table_weather_overview(lf_delay))
```


    
![png](03_analysis_5-meteo_files/03_analysis_5-meteo_6_0.png)
    



<style type="text/css">
#T_05a15 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_05a15 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_05a15 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_05a15 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_05a15 tr:hover td {
  background-color: #eef3f8;
}
#T_05a15_row0_col0, #T_05a15_row1_col0, #T_05a15_row2_col0 {
  text-align: right;
}
#T_05a15_row0_col1, #T_05a15_row0_col2, #T_05a15_row0_col3, #T_05a15_row1_col1, #T_05a15_row1_col2, #T_05a15_row1_col3, #T_05a15_row2_col1, #T_05a15_row2_col2, #T_05a15_row2_col3 {
  text-align: left;
}
</style>
<table id="T_05a15">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_05a15_level0_col0" class="col_heading level0 col0" >Δ Delay (s)</th>
      <th id="T_05a15_level0_col1" class="col_heading level0 col1" >OTP Normal</th>
      <th id="T_05a15_level0_col2" class="col_heading level0 col2" >OTP Wetter</th>
      <th id="T_05a15_level0_col3" class="col_heading level0 col3" >N (Wettertage)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Wetterbedingung</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_05a15_level0_row0" class="row_heading level0 row0" >Rain</th>
      <td id="T_05a15_row0_col0" class="data row0 col0" >8.90</td>
      <td id="T_05a15_row0_col1" class="data row0 col1" >87.4%</td>
      <td id="T_05a15_row0_col2" class="data row0 col2" >84.3%</td>
      <td id="T_05a15_row0_col3" class="data row0 col3" >10,152,819</td>
    </tr>
    <tr>
      <th id="T_05a15_level0_row1" class="row_heading level0 row1" >Heavy Rain</th>
      <td id="T_05a15_row1_col0" class="data row1 col0" >23.30</td>
      <td id="T_05a15_row1_col1" class="data row1 col1" >87.0%</td>
      <td id="T_05a15_row1_col2" class="data row1 col2" >79.4%</td>
      <td id="T_05a15_row1_col3" class="data row1 col3" >228,193</td>
    </tr>
    <tr>
      <th id="T_05a15_level0_row2" class="row_heading level0 row2" >Snow</th>
      <td id="T_05a15_row2_col0" class="data row2 col0" >54.00</td>
      <td id="T_05a15_row2_col1" class="data row2 col1" >87.1%</td>
      <td id="T_05a15_row2_col2" class="data row2 col2" >76.1%</td>
      <td id="T_05a15_row2_col3" class="data row2 col3" >273,151</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Schnee hat den stärksten Einzeleffekt (+54.0s, OTP −10.9pp), gefolgt von Starkregen (+23.3s). Leichter Regen ist messbar aber moderat (+8.9s).

**`is_windy` — Feature-Idee, aber nicht nutzbar:**
Wind als Feature wurde untersucht, zeigt aber NaN in der gesamten Analyse. Ursache: Das Feature war in der Datenvorbereitung als Feature-Idee vorgesehen, wurde aber nie korrekt befüllt (vermutlich keine Tage mit Wind > 40km/h im Datensatz, oder das Feature wurde nie in die parquet-Dateien geschrieben).
Inhaltlich: Zürich ist durch Bebauung und Hügellagen relativ windgeschützt. Trams sind schwer und auf Schienen gebunden — Wind unter ~60 km/h hat kaum messbaren Betriebseffekt. **`is_windy` wird aus dem Feature-Set entfernt.** (→ F-WEAT-03)

**Wetter-Effekte im Überblick (3 valide Features):**
| Bedingung | Δ Delay (s) | OTP Normal | OTP Wetter | N |
|:---|---:|---:|---:|---:|
| Regen | +8.9 | 87.4% | 84.3% | 10.2M |
| Starkregen | +23.3 | 87.0% | 79.4% | 228k |
| **Schnee** | **+54.0** | **87.1%** | **76.1%** | 273k |

**Wichtige Einschränkung:** Das ist reine Korrelation, keine Kausalität. Alle Wetter-Features haben niedrige Korrelation mit `arrival_delay` (max 0.042). Wetter alleine erklärt wenig Varianz — Wetter-Features bleiben aber als schwache eigenständige Signale im Modell.

**Niederschlagsintensität** zeigt eine klare Dosis-Wirkungs-Beziehung: <2mm=62.6s → >10mm=89.5s. Das ist der stärkste und klarste Wettereffekt im Notebook.

→ Wetter-Flags behalten: `has_snow`, `precipitation`, `has_rain`, `has_heavy_rain`; `is_windy` entfernen; Multikollinearität mit Monat/Saison beachten.

## Temperatur — Kontinuierlicher Effekt

Temperatur in 5°C-Bins: zeigt ob der Effekt linear ist oder ob es Schwellwerte gibt (z.B. Frost unter 0°C).

**Beobachtung:** Der Temperatureffekt ist monoton ansteigend — **kältere Temperaturen haben WENIGER Delay, wärmere MEHR**.

**Ø Delay nach Temperaturbereich (5°C-Bins):**
| Temperatur | Ø Delay (s) | OTP |
|:---|---:|---:|
| −5–0°C | 54.5 | 88.9% |
| **0–5°C** | **53.8** | **88.1%** (niedrigster Delay!) |
| 5–10°C | 55.4 | 87.4% |
| 15–20°C | 56.7 | 86.8% |
| 25–30°C | 59.7 | 85.3% |
| 35–40°C | 64.0 | 84.6% (n=15k — wenige Daten) |

**Kernbefund:** Die Kälte-Hypothese ist falsch — 0–5°C ist die beste Temperaturzone. Wärme verschlechtert die Pünktlichkeit graduell. Aber der Gesamteffekt ist klein: `is_hot` (>20°C) bringt nur **+2.0s Delta** (55.8s vs. 57.8s, OTP −1.1pp) — im Kontext aller Features ein schwaches Signal.

**Warum mehr Delay bei Wärme?**
- Sommer = mehr Freizeitverkehr, Tourismus, Events → vollere Trams, längere Boardingzeiten
- Gleisausdehnung bei Extremhitze (>30°C) → VBZ-Langsamfahrstellen (klassisches Problem)
- Im 35–40°C-Bin (n=15k) ist der Effekt am stärksten, aber die Datenbasis ist sehr dünn

**Kälte profitiert:** Konsistent mit F-TEMP-06 (Winter = beste Jahreszeit). Mögliche Ursache: weniger MIV bei Schnee/Frost kompensiert Halte-Verzögerungen.

→ `temperature` als kontinuierliches Feature; `is_hot` (>20°C) als binärer Flag; Effekt ist real aber klein (+2s) — nicht überbewerten.

## Feature: `is_hot`

Validierung des `is_hot`-Flags (temperature > 20°C) — binäre Vereinfachung des nicht-linearen Temperatureffekts für das Modell (F-WEAT-04).


```python
an.plot_is_hot(lf_delay, cfg, ylim_compare=(0, 70), ylim_curve=(0,70))
show_df(an.table_is_hot(lf_delay))
```


    
![png](03_analysis_5-meteo_files/03_analysis_5-meteo_12_0.png)
    


    Normal (≤20°C): Ø +55.8s  OTP 87.3%  (n=69.6M)
    Heiss  (>20°C): Ø +57.8s  OTP 86.2%  (n=20.1M)
    → Delta is_hot: +2.0s



<style type="text/css">
#T_7bc20 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_7bc20 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_7bc20 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_7bc20 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_7bc20 tr:hover td {
  background-color: #eef3f8;
}
#T_7bc20_row0_col0, #T_7bc20_row0_col1, #T_7bc20_row1_col0, #T_7bc20_row1_col1 {
  text-align: right;
}
#T_7bc20_row0_col2, #T_7bc20_row0_col3, #T_7bc20_row1_col2, #T_7bc20_row1_col3 {
  text-align: left;
}
</style>
<table id="T_7bc20">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_7bc20_level0_col0" class="col_heading level0 col0" >Avg. Delay (s)</th>
      <th id="T_7bc20_level0_col1" class="col_heading level0 col1" >Median (s)</th>
      <th id="T_7bc20_level0_col2" class="col_heading level0 col2" >OTP</th>
      <th id="T_7bc20_level0_col3" class="col_heading level0 col3" >N Halte</th>
    </tr>
    <tr>
      <th class="index_name level0" >is_hot</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_7bc20_level0_row0" class="row_heading level0 row0" >Normal (≤20°C)</th>
      <td id="T_7bc20_row0_col0" class="data row0 col0" >55.80</td>
      <td id="T_7bc20_row0_col1" class="data row0 col1" >42.00</td>
      <td id="T_7bc20_row0_col2" class="data row0 col2" >87.3%</td>
      <td id="T_7bc20_row0_col3" class="data row0 col3" >69,599,631</td>
    </tr>
    <tr>
      <th id="T_7bc20_level0_row1" class="row_heading level0 row1" >Heiss (>20°C)</th>
      <td id="T_7bc20_row1_col0" class="data row1 col0" >57.80</td>
      <td id="T_7bc20_row1_col1" class="data row1 col1" >44.00</td>
      <td id="T_7bc20_row1_col2" class="data row1 col2" >86.2%</td>
      <td id="T_7bc20_row1_col3" class="data row1 col3" >20,115,270</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Das `is_hot`-Feature (temperature > 20°C) validiert sich sauber.

**is_hot Vergleich:**
| Kategorie | Ø Delay (s) | OTP | N |
|:---|---:|---:|---:|
| Normal (≤20°C) | ~56s | ~87% | ~66M |
| Heiss (>20°C) | ~58s | ~86% | ~20M |

Der Effekt ist messbar aber moderat — `is_hot` ist ein nützlicher binärer Proxy für den kontinuierlichen Temperatureffekt. 
Die 20°C-Schwelle trennt zwei klar unterschiedliche Verteilungen, auch wenn der Effekt kleiner ist als der Schnee- oder Starkregen-Effekt.

## Daily Delay Timeline — Weather Events

Täglicher Delay-Verlauf pro Jahr — Schnee, Starkregen und Hitze als farbige Marker. Zeigt ob Delay-Spitzen mit Wetterereignissen zusammenfallen.


```python
an.plot_daily_delay_weather_timeline(lf_all, cfg)
show_df(an.table_daily_delay_weather_timeline(lf_clean))
```


    
![png](03_analysis_5-meteo_files/03_analysis_5-meteo_16_0.png)
    



<style type="text/css">
#T_b08ce thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_b08ce td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_b08ce tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_b08ce tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_b08ce tr:hover td {
  background-color: #eef3f8;
}
#T_b08ce_row0_col0, #T_b08ce_row0_col1, #T_b08ce_row0_col3, #T_b08ce_row1_col0, #T_b08ce_row1_col1, #T_b08ce_row1_col3, #T_b08ce_row2_col0, #T_b08ce_row2_col1, #T_b08ce_row2_col3, #T_b08ce_row3_col0, #T_b08ce_row3_col1, #T_b08ce_row3_col3, #T_b08ce_row4_col0, #T_b08ce_row4_col1, #T_b08ce_row4_col3, #T_b08ce_row5_col0, #T_b08ce_row5_col1, #T_b08ce_row5_col3, #T_b08ce_row6_col0, #T_b08ce_row6_col1, #T_b08ce_row6_col3, #T_b08ce_row7_col0, #T_b08ce_row7_col1, #T_b08ce_row7_col3, #T_b08ce_row8_col0, #T_b08ce_row8_col1, #T_b08ce_row8_col3, #T_b08ce_row9_col0, #T_b08ce_row9_col1, #T_b08ce_row9_col3, #T_b08ce_row10_col0, #T_b08ce_row10_col1, #T_b08ce_row10_col3, #T_b08ce_row11_col0, #T_b08ce_row11_col1, #T_b08ce_row11_col3, #T_b08ce_row12_col0, #T_b08ce_row12_col1, #T_b08ce_row12_col3, #T_b08ce_row13_col0, #T_b08ce_row13_col1, #T_b08ce_row13_col3, #T_b08ce_row14_col0, #T_b08ce_row14_col1, #T_b08ce_row14_col3, #T_b08ce_row15_col0, #T_b08ce_row15_col1, #T_b08ce_row15_col3, #T_b08ce_row16_col0, #T_b08ce_row16_col1, #T_b08ce_row16_col3, #T_b08ce_row17_col0, #T_b08ce_row17_col1, #T_b08ce_row17_col3, #T_b08ce_row18_col0, #T_b08ce_row18_col1, #T_b08ce_row18_col3, #T_b08ce_row19_col0, #T_b08ce_row19_col1, #T_b08ce_row19_col3, #T_b08ce_row20_col0, #T_b08ce_row20_col1, #T_b08ce_row20_col3, #T_b08ce_row21_col0, #T_b08ce_row21_col1, #T_b08ce_row21_col3, #T_b08ce_row22_col0, #T_b08ce_row22_col1, #T_b08ce_row22_col3, #T_b08ce_row23_col0, #T_b08ce_row23_col1, #T_b08ce_row23_col3, #T_b08ce_row24_col0, #T_b08ce_row24_col1, #T_b08ce_row24_col3, #T_b08ce_row25_col0, #T_b08ce_row25_col1, #T_b08ce_row25_col3, #T_b08ce_row26_col0, #T_b08ce_row26_col1, #T_b08ce_row26_col3, #T_b08ce_row27_col0, #T_b08ce_row27_col1, #T_b08ce_row27_col3, #T_b08ce_row28_col0, #T_b08ce_row28_col1, #T_b08ce_row28_col3, #T_b08ce_row29_col0, #T_b08ce_row29_col1, #T_b08ce_row29_col3 {
  text-align: left;
}
#T_b08ce_row0_col2, #T_b08ce_row0_col4, #T_b08ce_row1_col2, #T_b08ce_row1_col4, #T_b08ce_row2_col2, #T_b08ce_row2_col4, #T_b08ce_row3_col2, #T_b08ce_row3_col4, #T_b08ce_row4_col2, #T_b08ce_row4_col4, #T_b08ce_row5_col2, #T_b08ce_row5_col4, #T_b08ce_row6_col2, #T_b08ce_row6_col4, #T_b08ce_row7_col2, #T_b08ce_row7_col4, #T_b08ce_row8_col2, #T_b08ce_row8_col4, #T_b08ce_row9_col2, #T_b08ce_row9_col4, #T_b08ce_row10_col2, #T_b08ce_row10_col4, #T_b08ce_row11_col2, #T_b08ce_row11_col4, #T_b08ce_row12_col2, #T_b08ce_row12_col4, #T_b08ce_row13_col2, #T_b08ce_row13_col4, #T_b08ce_row14_col2, #T_b08ce_row14_col4, #T_b08ce_row15_col2, #T_b08ce_row15_col4, #T_b08ce_row16_col2, #T_b08ce_row16_col4, #T_b08ce_row17_col2, #T_b08ce_row17_col4, #T_b08ce_row18_col2, #T_b08ce_row18_col4, #T_b08ce_row19_col2, #T_b08ce_row19_col4, #T_b08ce_row20_col2, #T_b08ce_row20_col4, #T_b08ce_row21_col2, #T_b08ce_row21_col4, #T_b08ce_row22_col2, #T_b08ce_row22_col4, #T_b08ce_row23_col2, #T_b08ce_row23_col4, #T_b08ce_row24_col2, #T_b08ce_row24_col4, #T_b08ce_row25_col2, #T_b08ce_row25_col4, #T_b08ce_row26_col2, #T_b08ce_row26_col4, #T_b08ce_row27_col2, #T_b08ce_row27_col4, #T_b08ce_row28_col2, #T_b08ce_row28_col4, #T_b08ce_row29_col2, #T_b08ce_row29_col4 {
  text-align: right;
}
</style>
<table id="T_b08ce">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_b08ce_level0_col0" class="col_heading level0 col0" >Datum</th>
      <th id="T_b08ce_level0_col1" class="col_heading level0 col1" >Wetter</th>
      <th id="T_b08ce_level0_col2" class="col_heading level0 col2" >Avg. Delay (s)</th>
      <th id="T_b08ce_level0_col3" class="col_heading level0 col3" >OTP</th>
      <th id="T_b08ce_level0_col4" class="col_heading level0 col4" >N Halte</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_b08ce_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_b08ce_row0_col0" class="data row0 col0" >2024-11-21 00:00:00</td>
      <td id="T_b08ce_row0_col1" class="data row0 col1" >Snow</td>
      <td id="T_b08ce_row0_col2" class="data row0 col2" >404.60</td>
      <td id="T_b08ce_row0_col3" class="data row0 col3" >42.1%</td>
      <td id="T_b08ce_row0_col4" class="data row0 col4" >27789</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_b08ce_row1_col0" class="data row1 col0" >2024-11-22 00:00:00</td>
      <td id="T_b08ce_row1_col1" class="data row1 col1" >Snow</td>
      <td id="T_b08ce_row1_col2" class="data row1 col2" >149.10</td>
      <td id="T_b08ce_row1_col3" class="data row1 col3" >54.7%</td>
      <td id="T_b08ce_row1_col4" class="data row1 col4" >14290</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_b08ce_row2_col0" class="data row2 col0" >2025-09-01 00:00:00</td>
      <td id="T_b08ce_row2_col1" class="data row2 col1" >Heavy Rain</td>
      <td id="T_b08ce_row2_col2" class="data row2 col2" >145.50</td>
      <td id="T_b08ce_row2_col3" class="data row2 col3" >62.4%</td>
      <td id="T_b08ce_row2_col4" class="data row2 col4" >4187</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_b08ce_row3_col0" class="data row3 col0" >2023-12-01 00:00:00</td>
      <td id="T_b08ce_row3_col1" class="data row3 col1" >Snow</td>
      <td id="T_b08ce_row3_col2" class="data row3 col2" >136.60</td>
      <td id="T_b08ce_row3_col3" class="data row3 col3" >60.3%</td>
      <td id="T_b08ce_row3_col4" class="data row3 col4" >18823</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_b08ce_row4_col0" class="data row4 col0" >2024-07-12 00:00:00</td>
      <td id="T_b08ce_row4_col1" class="data row4 col1" >Heavy Rain</td>
      <td id="T_b08ce_row4_col2" class="data row4 col2" >132.00</td>
      <td id="T_b08ce_row4_col3" class="data row4 col3" >66.1%</td>
      <td id="T_b08ce_row4_col4" class="data row4 col4" >4236</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_b08ce_row5_col0" class="data row5 col0" >2025-07-26 00:00:00</td>
      <td id="T_b08ce_row5_col1" class="data row5 col1" >Heavy Rain</td>
      <td id="T_b08ce_row5_col2" class="data row5 col2" >131.20</td>
      <td id="T_b08ce_row5_col3" class="data row5 col3" >66.8%</td>
      <td id="T_b08ce_row5_col4" class="data row5 col4" >4389</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_b08ce_row6_col0" class="data row6 col0" >2023-11-14 00:00:00</td>
      <td id="T_b08ce_row6_col1" class="data row6 col1" >Heavy Rain</td>
      <td id="T_b08ce_row6_col2" class="data row6 col2" >119.50</td>
      <td id="T_b08ce_row6_col3" class="data row6 col3" >60.5%</td>
      <td id="T_b08ce_row6_col4" class="data row6 col4" >4469</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_b08ce_row7_col0" class="data row7 col0" >2025-09-04 00:00:00</td>
      <td id="T_b08ce_row7_col1" class="data row7 col1" >Heavy Rain</td>
      <td id="T_b08ce_row7_col2" class="data row7 col2" >113.00</td>
      <td id="T_b08ce_row7_col3" class="data row7 col3" >68.7%</td>
      <td id="T_b08ce_row7_col4" class="data row7 col4" >4895</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_b08ce_row8_col0" class="data row8 col0" >2025-10-22 00:00:00</td>
      <td id="T_b08ce_row8_col1" class="data row8 col1" >Heavy Rain</td>
      <td id="T_b08ce_row8_col2" class="data row8 col2" >111.40</td>
      <td id="T_b08ce_row8_col3" class="data row8 col3" >67.3%</td>
      <td id="T_b08ce_row8_col4" class="data row8 col4" >9967</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_b08ce_row9_col0" class="data row9 col0" >2024-09-05 00:00:00</td>
      <td id="T_b08ce_row9_col1" class="data row9 col1" >Heavy Rain</td>
      <td id="T_b08ce_row9_col2" class="data row9 col2" >99.30</td>
      <td id="T_b08ce_row9_col3" class="data row9 col3" >70.8%</td>
      <td id="T_b08ce_row9_col4" class="data row9 col4" >4750</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_b08ce_row10_col0" class="data row10 col0" >2024-06-21 00:00:00</td>
      <td id="T_b08ce_row10_col1" class="data row10 col1" >Heavy Rain</td>
      <td id="T_b08ce_row10_col2" class="data row10 col2" >93.30</td>
      <td id="T_b08ce_row10_col3" class="data row10 col3" >71.7%</td>
      <td id="T_b08ce_row10_col4" class="data row10 col4" >4897</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_b08ce_row11_col0" class="data row11 col0" >2024-04-15 00:00:00</td>
      <td id="T_b08ce_row11_col1" class="data row11 col1" >Hitze</td>
      <td id="T_b08ce_row11_col2" class="data row11 col2" >92.40</td>
      <td id="T_b08ce_row11_col3" class="data row11 col3" >70.3%</td>
      <td id="T_b08ce_row11_col4" class="data row11 col4" >3677</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_b08ce_row12_col0" class="data row12 col0" >2023-06-14 00:00:00</td>
      <td id="T_b08ce_row12_col1" class="data row12 col1" >Hitze</td>
      <td id="T_b08ce_row12_col2" class="data row12 col2" >91.40</td>
      <td id="T_b08ce_row12_col3" class="data row12 col3" >73.6%</td>
      <td id="T_b08ce_row12_col4" class="data row12 col4" >45372</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_b08ce_row13_col0" class="data row13 col0" >2025-01-04 00:00:00</td>
      <td id="T_b08ce_row13_col1" class="data row13 col1" >Snow</td>
      <td id="T_b08ce_row13_col2" class="data row13 col2" >91.20</td>
      <td id="T_b08ce_row13_col3" class="data row13 col3" >75.6%</td>
      <td id="T_b08ce_row13_col4" class="data row13 col4" >26710</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_b08ce_row14_col0" class="data row14 col0" >2023-07-12 00:00:00</td>
      <td id="T_b08ce_row14_col1" class="data row14 col1" >Heavy Rain</td>
      <td id="T_b08ce_row14_col2" class="data row14 col2" >90.50</td>
      <td id="T_b08ce_row14_col3" class="data row14 col3" >75.9%</td>
      <td id="T_b08ce_row14_col4" class="data row14 col4" >13162</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_b08ce_row15_col0" class="data row15 col0" >2023-12-02 00:00:00</td>
      <td id="T_b08ce_row15_col1" class="data row15 col1" >Snow</td>
      <td id="T_b08ce_row15_col2" class="data row15 col2" >89.50</td>
      <td id="T_b08ce_row15_col3" class="data row15 col3" >74.0%</td>
      <td id="T_b08ce_row15_col4" class="data row15 col4" >42449</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_b08ce_row16_col0" class="data row16 col0" >2023-09-21 00:00:00</td>
      <td id="T_b08ce_row16_col1" class="data row16 col1" >Heavy Rain</td>
      <td id="T_b08ce_row16_col2" class="data row16 col2" >89.10</td>
      <td id="T_b08ce_row16_col3" class="data row16 col3" >71.5%</td>
      <td id="T_b08ce_row16_col4" class="data row16 col4" >3301</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_b08ce_row17_col0" class="data row17 col0" >2025-07-31 00:00:00</td>
      <td id="T_b08ce_row17_col1" class="data row17 col1" >Hitze</td>
      <td id="T_b08ce_row17_col2" class="data row17 col2" >87.00</td>
      <td id="T_b08ce_row17_col3" class="data row17 col3" >77.4%</td>
      <td id="T_b08ce_row17_col4" class="data row17 col4" >40587</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_b08ce_row18_col0" class="data row18 col0" >2025-07-12 00:00:00</td>
      <td id="T_b08ce_row18_col1" class="data row18 col1" >Hitze</td>
      <td id="T_b08ce_row18_col2" class="data row18 col2" >82.90</td>
      <td id="T_b08ce_row18_col3" class="data row18 col3" >76.6%</td>
      <td id="T_b08ce_row18_col4" class="data row18 col4" >60761</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_b08ce_row19_col0" class="data row19 col0" >2025-07-02 00:00:00</td>
      <td id="T_b08ce_row19_col1" class="data row19 col1" >Hitze</td>
      <td id="T_b08ce_row19_col2" class="data row19 col2" >82.50</td>
      <td id="T_b08ce_row19_col3" class="data row19 col3" >74.8%</td>
      <td id="T_b08ce_row19_col4" class="data row19 col4" >81762</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row20" class="row_heading level0 row20" >20</th>
      <td id="T_b08ce_row20_col0" class="data row20 col0" >2025-06-21 00:00:00</td>
      <td id="T_b08ce_row20_col1" class="data row20 col1" >Hitze</td>
      <td id="T_b08ce_row20_col2" class="data row20 col2" >81.50</td>
      <td id="T_b08ce_row20_col3" class="data row20 col3" >76.9%</td>
      <td id="T_b08ce_row20_col4" class="data row20 col4" >63793</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row21" class="row_heading level0 row21" >21</th>
      <td id="T_b08ce_row21_col0" class="data row21 col0" >2024-07-09 00:00:00</td>
      <td id="T_b08ce_row21_col1" class="data row21 col1" >Hitze</td>
      <td id="T_b08ce_row21_col2" class="data row21 col2" >81.10</td>
      <td id="T_b08ce_row21_col3" class="data row21 col3" >76.5%</td>
      <td id="T_b08ce_row21_col4" class="data row21 col4" >69831</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row22" class="row_heading level0 row22" >22</th>
      <td id="T_b08ce_row22_col0" class="data row22 col0" >2025-04-05 00:00:00</td>
      <td id="T_b08ce_row22_col1" class="data row22 col1" >Hitze</td>
      <td id="T_b08ce_row22_col2" class="data row22 col2" >79.70</td>
      <td id="T_b08ce_row22_col3" class="data row22 col3" >72.9%</td>
      <td id="T_b08ce_row22_col4" class="data row22 col4" >22532</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row23" class="row_heading level0 row23" >23</th>
      <td id="T_b08ce_row23_col0" class="data row23 col0" >2024-09-07 00:00:00</td>
      <td id="T_b08ce_row23_col1" class="data row23 col1" >Hitze</td>
      <td id="T_b08ce_row23_col2" class="data row23 col2" >79.40</td>
      <td id="T_b08ce_row23_col3" class="data row23 col3" >78.0%</td>
      <td id="T_b08ce_row23_col4" class="data row23 col4" >57976</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row24" class="row_heading level0 row24" >24</th>
      <td id="T_b08ce_row24_col0" class="data row24 col0" >2023-10-07 00:00:00</td>
      <td id="T_b08ce_row24_col1" class="data row24 col1" >Hitze</td>
      <td id="T_b08ce_row24_col2" class="data row24 col2" >79.10</td>
      <td id="T_b08ce_row24_col3" class="data row24 col3" >76.0%</td>
      <td id="T_b08ce_row24_col4" class="data row24 col4" >18862</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row25" class="row_heading level0 row25" >25</th>
      <td id="T_b08ce_row25_col0" class="data row25 col0" >2024-01-18 00:00:00</td>
      <td id="T_b08ce_row25_col1" class="data row25 col1" >Snow</td>
      <td id="T_b08ce_row25_col2" class="data row25 col2" >70.00</td>
      <td id="T_b08ce_row25_col3" class="data row25 col3" >80.6%</td>
      <td id="T_b08ce_row25_col4" class="data row25 col4" >13040</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row26" class="row_heading level0 row26" >26</th>
      <td id="T_b08ce_row26_col0" class="data row26 col0" >2023-01-17 00:00:00</td>
      <td id="T_b08ce_row26_col1" class="data row26 col1" >Snow</td>
      <td id="T_b08ce_row26_col2" class="data row26 col2" >67.70</td>
      <td id="T_b08ce_row26_col3" class="data row26 col3" >81.4%</td>
      <td id="T_b08ce_row26_col4" class="data row26 col4" >4600</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row27" class="row_heading level0 row27" >27</th>
      <td id="T_b08ce_row27_col0" class="data row27 col0" >2023-01-18 00:00:00</td>
      <td id="T_b08ce_row27_col1" class="data row27 col1" >Snow</td>
      <td id="T_b08ce_row27_col2" class="data row27 col2" >58.10</td>
      <td id="T_b08ce_row27_col3" class="data row27 col3" >86.8%</td>
      <td id="T_b08ce_row27_col4" class="data row27 col4" >31699</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row28" class="row_heading level0 row28" >28</th>
      <td id="T_b08ce_row28_col0" class="data row28 col0" >2024-12-22 00:00:00</td>
      <td id="T_b08ce_row28_col1" class="data row28 col1" >Snow</td>
      <td id="T_b08ce_row28_col2" class="data row28 col2" >55.80</td>
      <td id="T_b08ce_row28_col3" class="data row28 col3" >86.6%</td>
      <td id="T_b08ce_row28_col4" class="data row28 col4" >10422</td>
    </tr>
    <tr>
      <th id="T_b08ce_level0_row29" class="row_heading level0 row29" >29</th>
      <td id="T_b08ce_row29_col0" class="data row29 col0" >2024-01-09 00:00:00</td>
      <td id="T_b08ce_row29_col1" class="data row29 col1" >Snow</td>
      <td id="T_b08ce_row29_col2" class="data row29 col2" >55.20</td>
      <td id="T_b08ce_row29_col3" class="data row29 col3" >86.6%</td>
      <td id="T_b08ce_row29_col4" class="data row29 col4" >6622</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Der tägliche Delay-Verlauf zeigt klare Wetter-Signaturen — aber Schnee-Tage ragen als Spitzen heraus, während Regen eher ein erhöhtes Grundrauschen erzeugt.

**Schnee-Spitzen** sind gut sichtbar als isolierte Peaks: einzelne Tage mit deutlich erhöhtem Delay, die mit blauen Markern zusammenfallen. Besonders ausgeprägt in den Wintermonaten Jan/Feb 2023 und 2024.

**Starkregen** erscheint als rote Häufung, oft im Herbst/Winter — weniger als singuläre Spitze, mehr als Phase erhöhter Delays.

**Temperatur** (gelbe Linie): Im Winter (niedrige Temperatur) sind die Delays tendenziell niedriger — konsistent mit F-WEAT-04. Sommerhitze (+20°C) korreliert mit leicht erhöhtem Grundniveau.

**Wichtige Einschränkung:** Wetter erklärt nicht alle Spitzen — Events (Berufsmesse, Stadtfest) können ähnliche Delay-Peaks erzeugen ohne Wetter-Marker. Die Kombination beider Notebooks ist nötig für eine vollständige Erklärung der Delay-Spitzen.

→ Schnee = scharfe, isolierte Peaks. Regen = diffuse Erhöhung. Wetter alleine erklärt die Varianz nicht vollständig (r < 0.05).

## Weather Impact Map — Stop Level

Δ Delay pro Haltestelle an Schnee- und Starkregen-Tagen vs. Normaltagen. Zeigt ob bestimmte Stadtteile oder Korridore besonders wetterempfindlich sind.

> **Warum Δ (Delta)?** Haltestellen haben sehr unterschiedliche Basis-Delays — eine Endhaltestelle hat strukturell mehr Delay als eine Innenstadthaltestelle. Δ = Wetter-Delay minus Normal-Delay macht Haltestellen vergleichbar: es zeigt den *zusätzlichen* Effekt des Wetters, unabhängig vom strukturellen Niveau.


```python
an.plot_weather_stop_map(lf_clean, flag="has_snow")
show_df(an.table_weather_stop_map(lf_clean, flag="has_snow"))
```




<style type="text/css">
#T_e3e64 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_e3e64 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_e3e64 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_e3e64 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_e3e64 tr:hover td {
  background-color: #eef3f8;
}
#T_e3e64_row0_col0, #T_e3e64_row0_col1, #T_e3e64_row1_col0, #T_e3e64_row1_col1, #T_e3e64_row2_col0, #T_e3e64_row2_col1, #T_e3e64_row3_col0, #T_e3e64_row3_col1, #T_e3e64_row4_col0, #T_e3e64_row4_col1, #T_e3e64_row5_col0, #T_e3e64_row5_col1, #T_e3e64_row6_col0, #T_e3e64_row6_col1, #T_e3e64_row7_col0, #T_e3e64_row7_col1, #T_e3e64_row8_col0, #T_e3e64_row8_col1, #T_e3e64_row9_col0, #T_e3e64_row9_col1, #T_e3e64_row10_col0, #T_e3e64_row10_col1, #T_e3e64_row11_col0, #T_e3e64_row11_col1, #T_e3e64_row12_col0, #T_e3e64_row12_col1, #T_e3e64_row13_col0, #T_e3e64_row13_col1, #T_e3e64_row14_col0, #T_e3e64_row14_col1, #T_e3e64_row15_col0, #T_e3e64_row15_col1, #T_e3e64_row16_col0, #T_e3e64_row16_col1, #T_e3e64_row17_col0, #T_e3e64_row17_col1, #T_e3e64_row18_col0, #T_e3e64_row18_col1, #T_e3e64_row19_col0, #T_e3e64_row19_col1 {
  text-align: left;
}
#T_e3e64_row0_col2, #T_e3e64_row0_col3, #T_e3e64_row0_col4, #T_e3e64_row0_col5, #T_e3e64_row1_col2, #T_e3e64_row1_col3, #T_e3e64_row1_col4, #T_e3e64_row1_col5, #T_e3e64_row2_col2, #T_e3e64_row2_col3, #T_e3e64_row2_col4, #T_e3e64_row2_col5, #T_e3e64_row3_col2, #T_e3e64_row3_col3, #T_e3e64_row3_col4, #T_e3e64_row3_col5, #T_e3e64_row4_col2, #T_e3e64_row4_col3, #T_e3e64_row4_col4, #T_e3e64_row4_col5, #T_e3e64_row5_col2, #T_e3e64_row5_col3, #T_e3e64_row5_col4, #T_e3e64_row5_col5, #T_e3e64_row6_col2, #T_e3e64_row6_col3, #T_e3e64_row6_col4, #T_e3e64_row6_col5, #T_e3e64_row7_col2, #T_e3e64_row7_col3, #T_e3e64_row7_col4, #T_e3e64_row7_col5, #T_e3e64_row8_col2, #T_e3e64_row8_col3, #T_e3e64_row8_col4, #T_e3e64_row8_col5, #T_e3e64_row9_col2, #T_e3e64_row9_col3, #T_e3e64_row9_col4, #T_e3e64_row9_col5, #T_e3e64_row10_col2, #T_e3e64_row10_col3, #T_e3e64_row10_col4, #T_e3e64_row10_col5, #T_e3e64_row11_col2, #T_e3e64_row11_col3, #T_e3e64_row11_col4, #T_e3e64_row11_col5, #T_e3e64_row12_col2, #T_e3e64_row12_col3, #T_e3e64_row12_col4, #T_e3e64_row12_col5, #T_e3e64_row13_col2, #T_e3e64_row13_col3, #T_e3e64_row13_col4, #T_e3e64_row13_col5, #T_e3e64_row14_col2, #T_e3e64_row14_col3, #T_e3e64_row14_col4, #T_e3e64_row14_col5, #T_e3e64_row15_col2, #T_e3e64_row15_col3, #T_e3e64_row15_col4, #T_e3e64_row15_col5, #T_e3e64_row16_col2, #T_e3e64_row16_col3, #T_e3e64_row16_col4, #T_e3e64_row16_col5, #T_e3e64_row17_col2, #T_e3e64_row17_col3, #T_e3e64_row17_col4, #T_e3e64_row17_col5, #T_e3e64_row18_col2, #T_e3e64_row18_col3, #T_e3e64_row18_col4, #T_e3e64_row18_col5, #T_e3e64_row19_col2, #T_e3e64_row19_col3, #T_e3e64_row19_col4, #T_e3e64_row19_col5 {
  text-align: right;
}
</style>
<table id="T_e3e64">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_e3e64_level0_col0" class="col_heading level0 col0" >Stop</th>
      <th id="T_e3e64_level0_col1" class="col_heading level0 col1" >District</th>
      <th id="T_e3e64_level0_col2" class="col_heading level0 col2" >Normal (s)</th>
      <th id="T_e3e64_level0_col3" class="col_heading level0 col3" >Schnee (s)</th>
      <th id="T_e3e64_level0_col4" class="col_heading level0 col4" >Δ (s)</th>
      <th id="T_e3e64_level0_col5" class="col_heading level0 col5" >N Halte</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_e3e64_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_e3e64_row0_col0" class="data row0 col0" >Zürich, Bahnhof Selnau</td>
      <td id="T_e3e64_row0_col1" class="data row0 col1" >Kreis 1</td>
      <td id="T_e3e64_row0_col2" class="data row0 col2" >54.90</td>
      <td id="T_e3e64_row0_col3" class="data row0 col3" >246.50</td>
      <td id="T_e3e64_row0_col4" class="data row0 col4" >191.60</td>
      <td id="T_e3e64_row0_col5" class="data row0 col5" >971</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_e3e64_row1_col0" class="data row1 col0" >Zürich, Helvetiaplatz</td>
      <td id="T_e3e64_row1_col1" class="data row1 col1" >Kreis 4</td>
      <td id="T_e3e64_row1_col2" class="data row1 col2" >58.50</td>
      <td id="T_e3e64_row1_col3" class="data row1 col3" >176.50</td>
      <td id="T_e3e64_row1_col4" class="data row1 col4" >117.90</td>
      <td id="T_e3e64_row1_col5" class="data row1 col5" >867</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_e3e64_row2_col0" class="data row2 col0" >Zürich, Bahnhof Hardbrücke</td>
      <td id="T_e3e64_row2_col1" class="data row2 col1" >Kreis 4</td>
      <td id="T_e3e64_row2_col2" class="data row2 col2" >60.30</td>
      <td id="T_e3e64_row2_col3" class="data row2 col3" >178.20</td>
      <td id="T_e3e64_row2_col4" class="data row2 col4" >117.90</td>
      <td id="T_e3e64_row2_col5" class="data row2 col5" >847</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_e3e64_row3_col0" class="data row3 col0" >Zürich, Hardplatz</td>
      <td id="T_e3e64_row3_col1" class="data row3 col1" >Kreis 4</td>
      <td id="T_e3e64_row3_col2" class="data row3 col2" >61.00</td>
      <td id="T_e3e64_row3_col3" class="data row3 col3" >177.60</td>
      <td id="T_e3e64_row3_col4" class="data row3 col4" >116.60</td>
      <td id="T_e3e64_row3_col5" class="data row3 col5" >855</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_e3e64_row4_col0" class="data row4 col0" >Zürich, Bäckeranlage</td>
      <td id="T_e3e64_row4_col1" class="data row4 col1" >Kreis 4</td>
      <td id="T_e3e64_row4_col2" class="data row4 col2" >62.80</td>
      <td id="T_e3e64_row4_col3" class="data row4 col3" >175.10</td>
      <td id="T_e3e64_row4_col4" class="data row4 col4" >112.30</td>
      <td id="T_e3e64_row4_col5" class="data row4 col5" >864</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_e3e64_row5_col0" class="data row5 col0" >Zürich, Waidfussweg</td>
      <td id="T_e3e64_row5_col1" class="data row5 col1" >Kreis 10</td>
      <td id="T_e3e64_row5_col2" class="data row5 col2" >45.40</td>
      <td id="T_e3e64_row5_col3" class="data row5 col3" >155.80</td>
      <td id="T_e3e64_row5_col4" class="data row5 col4" >110.40</td>
      <td id="T_e3e64_row5_col5" class="data row5 col5" >701</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_e3e64_row6_col0" class="data row6 col0" >Zürich, Güterbahnhof</td>
      <td id="T_e3e64_row6_col1" class="data row6 col1" >Kreis 4</td>
      <td id="T_e3e64_row6_col2" class="data row6 col2" >52.30</td>
      <td id="T_e3e64_row6_col3" class="data row6 col3" >161.30</td>
      <td id="T_e3e64_row6_col4" class="data row6 col4" >108.90</td>
      <td id="T_e3e64_row6_col5" class="data row6 col5" >855</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_e3e64_row7_col0" class="data row7 col0" >Zürich, Alte Trotte</td>
      <td id="T_e3e64_row7_col1" class="data row7 col1" >Kreis 10</td>
      <td id="T_e3e64_row7_col2" class="data row7 col2" >53.80</td>
      <td id="T_e3e64_row7_col3" class="data row7 col3" >160.10</td>
      <td id="T_e3e64_row7_col4" class="data row7 col4" >106.30</td>
      <td id="T_e3e64_row7_col5" class="data row7 col5" >703</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_e3e64_row8_col0" class="data row8 col0" >Zürich, Eschergutweg</td>
      <td id="T_e3e64_row8_col1" class="data row8 col1" >Kreis 10</td>
      <td id="T_e3e64_row8_col2" class="data row8 col2" >40.20</td>
      <td id="T_e3e64_row8_col3" class="data row8 col3" >145.40</td>
      <td id="T_e3e64_row8_col4" class="data row8 col4" >105.20</td>
      <td id="T_e3e64_row8_col5" class="data row8 col5" >702</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_e3e64_row9_col0" class="data row9 col0" >Zürich, Uetlihof</td>
      <td id="T_e3e64_row9_col1" class="data row9 col1" >Kreis 3</td>
      <td id="T_e3e64_row9_col2" class="data row9 col2" >57.40</td>
      <td id="T_e3e64_row9_col3" class="data row9 col3" >162.00</td>
      <td id="T_e3e64_row9_col4" class="data row9 col4" >104.60</td>
      <td id="T_e3e64_row9_col5" class="data row9 col5" >909</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_e3e64_row10_col0" class="data row10 col0" >Zürich, Rentenanstalt</td>
      <td id="T_e3e64_row10_col1" class="data row10 col1" >Kreis 2</td>
      <td id="T_e3e64_row10_col2" class="data row10 col2" >50.60</td>
      <td id="T_e3e64_row10_col3" class="data row10 col3" >155.00</td>
      <td id="T_e3e64_row10_col4" class="data row10 col4" >104.40</td>
      <td id="T_e3e64_row10_col5" class="data row10 col5" >774</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_e3e64_row11_col0" class="data row11 col0" >Zürich, Laubegg</td>
      <td id="T_e3e64_row11_col1" class="data row11 col1" >Kreis 3</td>
      <td id="T_e3e64_row11_col2" class="data row11 col2" >53.60</td>
      <td id="T_e3e64_row11_col3" class="data row11 col3" >154.90</td>
      <td id="T_e3e64_row11_col4" class="data row11 col4" >101.30</td>
      <td id="T_e3e64_row11_col5" class="data row11 col5" >920</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_e3e64_row12_col0" class="data row12 col0" >Zürich, Bahnhof Enge</td>
      <td id="T_e3e64_row12_col1" class="data row12 col1" >Kreis 2</td>
      <td id="T_e3e64_row12_col2" class="data row12 col2" >53.40</td>
      <td id="T_e3e64_row12_col3" class="data row12 col3" >152.20</td>
      <td id="T_e3e64_row12_col4" class="data row12 col4" >98.80</td>
      <td id="T_e3e64_row12_col5" class="data row12 col5" >1508</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_e3e64_row13_col0" class="data row13 col0" >Zürich, Tunnelstrasse</td>
      <td id="T_e3e64_row13_col1" class="data row13 col1" >Kreis 2</td>
      <td id="T_e3e64_row13_col2" class="data row13 col2" >53.50</td>
      <td id="T_e3e64_row13_col3" class="data row13 col3" >149.20</td>
      <td id="T_e3e64_row13_col4" class="data row13 col4" >95.70</td>
      <td id="T_e3e64_row13_col5" class="data row13 col5" >2044</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_e3e64_row14_col0" class="data row14 col0" >Zürich, Wipkingerplatz</td>
      <td id="T_e3e64_row14_col1" class="data row14 col1" >Kreis 10</td>
      <td id="T_e3e64_row14_col2" class="data row14 col2" >44.70</td>
      <td id="T_e3e64_row14_col3" class="data row14 col3" >134.80</td>
      <td id="T_e3e64_row14_col4" class="data row14 col4" >90.10</td>
      <td id="T_e3e64_row14_col5" class="data row14 col5" >784</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_e3e64_row15_col0" class="data row15 col0" >Zürich, Saalsporthalle</td>
      <td id="T_e3e64_row15_col1" class="data row15 col1" >Kreis 3</td>
      <td id="T_e3e64_row15_col2" class="data row15 col2" >55.70</td>
      <td id="T_e3e64_row15_col3" class="data row15 col3" >142.90</td>
      <td id="T_e3e64_row15_col4" class="data row15 col4" >87.30</td>
      <td id="T_e3e64_row15_col5" class="data row15 col5" >1193</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_e3e64_row16_col0" class="data row16 col0" >Zürich, Meierhofplatz</td>
      <td id="T_e3e64_row16_col1" class="data row16 col1" >Kreis 10</td>
      <td id="T_e3e64_row16_col2" class="data row16 col2" >59.80</td>
      <td id="T_e3e64_row16_col3" class="data row16 col3" >146.40</td>
      <td id="T_e3e64_row16_col4" class="data row16 col4" >86.70</td>
      <td id="T_e3e64_row16_col5" class="data row16 col5" >883</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_e3e64_row17_col0" class="data row17 col0" >Zürich, Schwert</td>
      <td id="T_e3e64_row17_col1" class="data row17 col1" >Kreis 10</td>
      <td id="T_e3e64_row17_col2" class="data row17 col2" >56.00</td>
      <td id="T_e3e64_row17_col3" class="data row17 col3" >142.70</td>
      <td id="T_e3e64_row17_col4" class="data row17 col4" >86.70</td>
      <td id="T_e3e64_row17_col5" class="data row17 col5" >884</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_e3e64_row18_col0" class="data row18 col0" >Zürich, Wartau</td>
      <td id="T_e3e64_row18_col1" class="data row18 col1" >Kreis 10</td>
      <td id="T_e3e64_row18_col2" class="data row18 col2" >45.90</td>
      <td id="T_e3e64_row18_col3" class="data row18 col3" >132.30</td>
      <td id="T_e3e64_row18_col4" class="data row18 col4" >86.40</td>
      <td id="T_e3e64_row18_col5" class="data row18 col5" >869</td>
    </tr>
    <tr>
      <th id="T_e3e64_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_e3e64_row19_col0" class="data row19 col0" >Zürich, Zwielplatz</td>
      <td id="T_e3e64_row19_col1" class="data row19 col1" >Kreis 10</td>
      <td id="T_e3e64_row19_col2" class="data row19 col2" >56.40</td>
      <td id="T_e3e64_row19_col3" class="data row19 col3" >142.70</td>
      <td id="T_e3e64_row19_col4" class="data row19 col4" >86.30</td>
      <td id="T_e3e64_row19_col5" class="data row19 col5" >877</td>
    </tr>
  </tbody>
</table>




```python
an.plot_weather_stop_map(lf_clean, flag="has_heavy_rain")
show_df(an.table_weather_stop_map(lf_clean, flag="has_heavy_rain"))
```




<style type="text/css">
#T_ff4a3 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_ff4a3 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_ff4a3 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_ff4a3 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_ff4a3 tr:hover td {
  background-color: #eef3f8;
}
#T_ff4a3_row0_col0, #T_ff4a3_row0_col1, #T_ff4a3_row1_col0, #T_ff4a3_row1_col1, #T_ff4a3_row2_col0, #T_ff4a3_row2_col1, #T_ff4a3_row3_col0, #T_ff4a3_row3_col1, #T_ff4a3_row4_col0, #T_ff4a3_row4_col1, #T_ff4a3_row5_col0, #T_ff4a3_row5_col1, #T_ff4a3_row6_col0, #T_ff4a3_row6_col1, #T_ff4a3_row7_col0, #T_ff4a3_row7_col1, #T_ff4a3_row8_col0, #T_ff4a3_row8_col1, #T_ff4a3_row9_col0, #T_ff4a3_row9_col1, #T_ff4a3_row10_col0, #T_ff4a3_row10_col1, #T_ff4a3_row11_col0, #T_ff4a3_row11_col1, #T_ff4a3_row12_col0, #T_ff4a3_row12_col1, #T_ff4a3_row13_col0, #T_ff4a3_row13_col1, #T_ff4a3_row14_col0, #T_ff4a3_row14_col1, #T_ff4a3_row15_col0, #T_ff4a3_row15_col1, #T_ff4a3_row16_col0, #T_ff4a3_row16_col1, #T_ff4a3_row17_col0, #T_ff4a3_row17_col1, #T_ff4a3_row18_col0, #T_ff4a3_row18_col1, #T_ff4a3_row19_col0, #T_ff4a3_row19_col1 {
  text-align: left;
}
#T_ff4a3_row0_col2, #T_ff4a3_row0_col3, #T_ff4a3_row0_col4, #T_ff4a3_row0_col5, #T_ff4a3_row1_col2, #T_ff4a3_row1_col3, #T_ff4a3_row1_col4, #T_ff4a3_row1_col5, #T_ff4a3_row2_col2, #T_ff4a3_row2_col3, #T_ff4a3_row2_col4, #T_ff4a3_row2_col5, #T_ff4a3_row3_col2, #T_ff4a3_row3_col3, #T_ff4a3_row3_col4, #T_ff4a3_row3_col5, #T_ff4a3_row4_col2, #T_ff4a3_row4_col3, #T_ff4a3_row4_col4, #T_ff4a3_row4_col5, #T_ff4a3_row5_col2, #T_ff4a3_row5_col3, #T_ff4a3_row5_col4, #T_ff4a3_row5_col5, #T_ff4a3_row6_col2, #T_ff4a3_row6_col3, #T_ff4a3_row6_col4, #T_ff4a3_row6_col5, #T_ff4a3_row7_col2, #T_ff4a3_row7_col3, #T_ff4a3_row7_col4, #T_ff4a3_row7_col5, #T_ff4a3_row8_col2, #T_ff4a3_row8_col3, #T_ff4a3_row8_col4, #T_ff4a3_row8_col5, #T_ff4a3_row9_col2, #T_ff4a3_row9_col3, #T_ff4a3_row9_col4, #T_ff4a3_row9_col5, #T_ff4a3_row10_col2, #T_ff4a3_row10_col3, #T_ff4a3_row10_col4, #T_ff4a3_row10_col5, #T_ff4a3_row11_col2, #T_ff4a3_row11_col3, #T_ff4a3_row11_col4, #T_ff4a3_row11_col5, #T_ff4a3_row12_col2, #T_ff4a3_row12_col3, #T_ff4a3_row12_col4, #T_ff4a3_row12_col5, #T_ff4a3_row13_col2, #T_ff4a3_row13_col3, #T_ff4a3_row13_col4, #T_ff4a3_row13_col5, #T_ff4a3_row14_col2, #T_ff4a3_row14_col3, #T_ff4a3_row14_col4, #T_ff4a3_row14_col5, #T_ff4a3_row15_col2, #T_ff4a3_row15_col3, #T_ff4a3_row15_col4, #T_ff4a3_row15_col5, #T_ff4a3_row16_col2, #T_ff4a3_row16_col3, #T_ff4a3_row16_col4, #T_ff4a3_row16_col5, #T_ff4a3_row17_col2, #T_ff4a3_row17_col3, #T_ff4a3_row17_col4, #T_ff4a3_row17_col5, #T_ff4a3_row18_col2, #T_ff4a3_row18_col3, #T_ff4a3_row18_col4, #T_ff4a3_row18_col5, #T_ff4a3_row19_col2, #T_ff4a3_row19_col3, #T_ff4a3_row19_col4, #T_ff4a3_row19_col5 {
  text-align: right;
}
</style>
<table id="T_ff4a3">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_ff4a3_level0_col0" class="col_heading level0 col0" >Stop</th>
      <th id="T_ff4a3_level0_col1" class="col_heading level0 col1" >District</th>
      <th id="T_ff4a3_level0_col2" class="col_heading level0 col2" >Normal (s)</th>
      <th id="T_ff4a3_level0_col3" class="col_heading level0 col3" >Starkregen (s)</th>
      <th id="T_ff4a3_level0_col4" class="col_heading level0 col4" >Δ (s)</th>
      <th id="T_ff4a3_level0_col5" class="col_heading level0 col5" >N Halte</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_ff4a3_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_ff4a3_row0_col0" class="data row0 col0" >Zürich, Toni-Areal</td>
      <td id="T_ff4a3_row0_col1" class="data row0 col1" >Kreis 5</td>
      <td id="T_ff4a3_row0_col2" class="data row0 col2" >55.30</td>
      <td id="T_ff4a3_row0_col3" class="data row0 col3" >99.80</td>
      <td id="T_ff4a3_row0_col4" class="data row0 col4" >44.50</td>
      <td id="T_ff4a3_row0_col5" class="data row0 col5" >701</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_ff4a3_row1_col0" class="data row1 col0" >Zürich, Technopark</td>
      <td id="T_ff4a3_row1_col1" class="data row1 col1" >Kreis 5</td>
      <td id="T_ff4a3_row1_col2" class="data row1 col2" >58.60</td>
      <td id="T_ff4a3_row1_col3" class="data row1 col3" >100.90</td>
      <td id="T_ff4a3_row1_col4" class="data row1 col4" >42.20</td>
      <td id="T_ff4a3_row1_col5" class="data row1 col5" >699</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_ff4a3_row2_col0" class="data row2 col0" >Zürich, Sportweg</td>
      <td id="T_ff4a3_row2_col1" class="data row2 col1" >Kreis 5</td>
      <td id="T_ff4a3_row2_col2" class="data row2 col2" >58.80</td>
      <td id="T_ff4a3_row2_col3" class="data row2 col3" >98.80</td>
      <td id="T_ff4a3_row2_col4" class="data row2 col4" >40.00</td>
      <td id="T_ff4a3_row2_col5" class="data row2 col5" >704</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_ff4a3_row3_col0" class="data row3 col0" >Zürich, Quellenstrasse</td>
      <td id="T_ff4a3_row3_col1" class="data row3 col1" >Kreis 5</td>
      <td id="T_ff4a3_row3_col2" class="data row3 col2" >46.40</td>
      <td id="T_ff4a3_row3_col3" class="data row3 col3" >86.10</td>
      <td id="T_ff4a3_row3_col4" class="data row3 col4" >39.70</td>
      <td id="T_ff4a3_row3_col5" class="data row3 col5" >2100</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_ff4a3_row4_col0" class="data row4 col0" >Zürich, Löwenbräu</td>
      <td id="T_ff4a3_row4_col1" class="data row4 col1" >Kreis 5</td>
      <td id="T_ff4a3_row4_col2" class="data row4 col2" >45.90</td>
      <td id="T_ff4a3_row4_col3" class="data row4 col3" >85.30</td>
      <td id="T_ff4a3_row4_col4" class="data row4 col4" >39.40</td>
      <td id="T_ff4a3_row4_col5" class="data row4 col5" >2089</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_ff4a3_row5_col0" class="data row5 col0" >Zürich, Laubegg</td>
      <td id="T_ff4a3_row5_col1" class="data row5 col1" >Kreis 3</td>
      <td id="T_ff4a3_row5_col2" class="data row5 col2" >53.80</td>
      <td id="T_ff4a3_row5_col3" class="data row5 col3" >93.00</td>
      <td id="T_ff4a3_row5_col4" class="data row5 col4" >39.20</td>
      <td id="T_ff4a3_row5_col5" class="data row5 col5" >843</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row6" class="row_heading level0 row6" >6</th>
      <td id="T_ff4a3_row6_col0" class="data row6 col0" >Zürich, Aargauerstrasse</td>
      <td id="T_ff4a3_row6_col1" class="data row6 col1" >Kreis 5</td>
      <td id="T_ff4a3_row6_col2" class="data row6 col2" >67.20</td>
      <td id="T_ff4a3_row6_col3" class="data row6 col3" >106.20</td>
      <td id="T_ff4a3_row6_col4" class="data row6 col4" >39.00</td>
      <td id="T_ff4a3_row6_col5" class="data row6 col5" >705</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row7" class="row_heading level0 row7" >7</th>
      <td id="T_ff4a3_row7_col0" class="data row7 col0" >Zürich, Museum für Gestaltung</td>
      <td id="T_ff4a3_row7_col1" class="data row7 col1" >Kreis 5</td>
      <td id="T_ff4a3_row7_col2" class="data row7 col2" >45.50</td>
      <td id="T_ff4a3_row7_col3" class="data row7 col3" >84.40</td>
      <td id="T_ff4a3_row7_col4" class="data row7 col4" >38.90</td>
      <td id="T_ff4a3_row7_col5" class="data row7 col5" >2106</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row8" class="row_heading level0 row8" >8</th>
      <td id="T_ff4a3_row8_col0" class="data row8 col0" >Zürich, Wildbachstrasse</td>
      <td id="T_ff4a3_row8_col1" class="data row8 col1" >Kreis 8</td>
      <td id="T_ff4a3_row8_col2" class="data row8 col2" >80.10</td>
      <td id="T_ff4a3_row8_col3" class="data row8 col3" >118.90</td>
      <td id="T_ff4a3_row8_col4" class="data row8 col4" >38.80</td>
      <td id="T_ff4a3_row8_col5" class="data row8 col5" >711</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row9" class="row_heading level0 row9" >9</th>
      <td id="T_ff4a3_row9_col0" class="data row9 col0" >Zürich, Limmatplatz</td>
      <td id="T_ff4a3_row9_col1" class="data row9 col1" >Kreis 5</td>
      <td id="T_ff4a3_row9_col2" class="data row9 col2" >47.10</td>
      <td id="T_ff4a3_row9_col3" class="data row9 col3" >85.70</td>
      <td id="T_ff4a3_row9_col4" class="data row9 col4" >38.60</td>
      <td id="T_ff4a3_row9_col5" class="data row9 col5" >2093</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row10" class="row_heading level0 row10" >10</th>
      <td id="T_ff4a3_row10_col0" class="data row10 col0" >Zürich, Saalsporthalle</td>
      <td id="T_ff4a3_row10_col1" class="data row10 col1" >Kreis 3</td>
      <td id="T_ff4a3_row10_col2" class="data row10 col2" >55.80</td>
      <td id="T_ff4a3_row10_col3" class="data row10 col3" >93.80</td>
      <td id="T_ff4a3_row10_col4" class="data row10 col4" >38.00</td>
      <td id="T_ff4a3_row10_col5" class="data row10 col5" >1112</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row11" class="row_heading level0 row11" >11</th>
      <td id="T_ff4a3_row11_col0" class="data row11 col0" >Zürich, Bad Allenmoos</td>
      <td id="T_ff4a3_row11_col1" class="data row11 col1" >Kreis 6</td>
      <td id="T_ff4a3_row11_col2" class="data row11 col2" >69.90</td>
      <td id="T_ff4a3_row11_col3" class="data row11 col3" >107.60</td>
      <td id="T_ff4a3_row11_col4" class="data row11 col4" >37.70</td>
      <td id="T_ff4a3_row11_col5" class="data row11 col5" >732</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_ff4a3_row12_col0" class="data row12 col0" >Zürich, Wipkingerplatz</td>
      <td id="T_ff4a3_row12_col1" class="data row12 col1" >Kreis 10</td>
      <td id="T_ff4a3_row12_col2" class="data row12 col2" >44.90</td>
      <td id="T_ff4a3_row12_col3" class="data row12 col3" >82.40</td>
      <td id="T_ff4a3_row12_col4" class="data row12 col4" >37.60</td>
      <td id="T_ff4a3_row12_col5" class="data row12 col5" >601</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row13" class="row_heading level0 row13" >13</th>
      <td id="T_ff4a3_row13_col0" class="data row13 col0" >Zürich, Escher-Wyss-Platz</td>
      <td id="T_ff4a3_row13_col1" class="data row13 col1" >Kreis 5</td>
      <td id="T_ff4a3_row13_col2" class="data row13 col2" >50.30</td>
      <td id="T_ff4a3_row13_col3" class="data row13 col3" >87.50</td>
      <td id="T_ff4a3_row13_col4" class="data row13 col4" >37.30</td>
      <td id="T_ff4a3_row13_col5" class="data row13 col5" >2800</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row14" class="row_heading level0 row14" >14</th>
      <td id="T_ff4a3_row14_col0" class="data row14 col0" >Zürich, Bernoulli-Häuser</td>
      <td id="T_ff4a3_row14_col1" class="data row14 col1" >Kreis 5</td>
      <td id="T_ff4a3_row14_col2" class="data row14 col2" >59.20</td>
      <td id="T_ff4a3_row14_col3" class="data row14 col3" >96.30</td>
      <td id="T_ff4a3_row14_col4" class="data row14 col4" >37.10</td>
      <td id="T_ff4a3_row14_col5" class="data row14 col5" >1165</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row15" class="row_heading level0 row15" >15</th>
      <td id="T_ff4a3_row15_col0" class="data row15 col0" >Zürich, Bahnhofquai/HB</td>
      <td id="T_ff4a3_row15_col1" class="data row15 col1" >Kreis 1</td>
      <td id="T_ff4a3_row15_col2" class="data row15 col2" >54.50</td>
      <td id="T_ff4a3_row15_col3" class="data row15 col3" >91.10</td>
      <td id="T_ff4a3_row15_col4" class="data row15 col4" >36.60</td>
      <td id="T_ff4a3_row15_col5" class="data row15 col5" >3048</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row16" class="row_heading level0 row16" >16</th>
      <td id="T_ff4a3_row16_col0" class="data row16 col0" >Zürich, Sihlquai/HB</td>
      <td id="T_ff4a3_row16_col1" class="data row16 col1" >Kreis 5</td>
      <td id="T_ff4a3_row16_col2" class="data row16 col2" >46.90</td>
      <td id="T_ff4a3_row16_col3" class="data row16 col3" >83.00</td>
      <td id="T_ff4a3_row16_col4" class="data row16 col4" >36.10</td>
      <td id="T_ff4a3_row16_col5" class="data row16 col5" >2095</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row17" class="row_heading level0 row17" >17</th>
      <td id="T_ff4a3_row17_col0" class="data row17 col0" >Zürich, Uetlihof</td>
      <td id="T_ff4a3_row17_col1" class="data row17 col1" >Kreis 3</td>
      <td id="T_ff4a3_row17_col2" class="data row17 col2" >57.60</td>
      <td id="T_ff4a3_row17_col3" class="data row17 col3" >92.80</td>
      <td id="T_ff4a3_row17_col4" class="data row17 col4" >35.20</td>
      <td id="T_ff4a3_row17_col5" class="data row17 col5" >833</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row18" class="row_heading level0 row18" >18</th>
      <td id="T_ff4a3_row18_col0" class="data row18 col0" >Zürich, Bäckeranlage</td>
      <td id="T_ff4a3_row18_col1" class="data row18 col1" >Kreis 4</td>
      <td id="T_ff4a3_row18_col2" class="data row18 col2" >63.10</td>
      <td id="T_ff4a3_row18_col3" class="data row18 col3" >97.90</td>
      <td id="T_ff4a3_row18_col4" class="data row18 col4" >34.80</td>
      <td id="T_ff4a3_row18_col5" class="data row18 col5" >710</td>
    </tr>
    <tr>
      <th id="T_ff4a3_level0_row19" class="row_heading level0 row19" >19</th>
      <td id="T_ff4a3_row19_col0" class="data row19 col0" >Zürich, Bahnhof Selnau</td>
      <td id="T_ff4a3_row19_col1" class="data row19 col1" >Kreis 1</td>
      <td id="T_ff4a3_row19_col2" class="data row19 col2" >55.40</td>
      <td id="T_ff4a3_row19_col3" class="data row19 col3" >90.20</td>
      <td id="T_ff4a3_row19_col4" class="data row19 col4" >34.80</td>
      <td id="T_ff4a3_row19_col5" class="data row19 col5" >763</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Karten zeigen zwei völlig unterschiedliche geografische Muster für Schnee und Regen.

**Schnee:** Konzentriert auf Kreis 4 (Hardbrücke/Hardplatz-Korridor) und Kreis 10 (Höngg/Wipkingen — erhöhte Lage, exponiert). Bahnhof Selnau als extremer Ausreisser (+190.9s, fast 4× Normal).

**Starkregen:** Konzentriert auf Kreis 5 (Escher Wyss / Toni-Areal Korridor, Limmat-Niederung). Toni-Areal +44s, Technopark +42s — industrielles Entwicklungsgebiet mit Drainage-Problemen.

→ Zwei verschiedene Vulnerabilitätskarten — dasselbe Netz, aber völlig andere Schwachstellen je nach Wetterereignis.

## Stadtkreis-Vergleich — Schnee vs. Starkregen

Δ Delay pro Stadtkreis für Schnee- vs. Starkregen-Tage nebeneinander. Zeigt welche Kreise besonders empfindlich auf welche Wetterbedingung reagieren.


```python
an.plot_district_weather_sensitivity(lf_clean, cfg)
show_df(an.table_district_weather_sensitivity(lf_clean))
```


    
![png](03_analysis_5-meteo_files/03_analysis_5-meteo_25_0.png)
    



<style type="text/css">
#T_8df55 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_8df55 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_8df55 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_8df55 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_8df55 tr:hover td {
  background-color: #eef3f8;
}
#T_8df55_row0_col0, #T_8df55_row0_col1, #T_8df55_row1_col0, #T_8df55_row1_col1, #T_8df55_row2_col0, #T_8df55_row2_col1, #T_8df55_row3_col0, #T_8df55_row3_col1, #T_8df55_row4_col0, #T_8df55_row4_col1, #T_8df55_row5_col0, #T_8df55_row5_col1, #T_8df55_row6_col0, #T_8df55_row6_col1, #T_8df55_row7_col0, #T_8df55_row7_col1, #T_8df55_row8_col0, #T_8df55_row8_col1, #T_8df55_row9_col0, #T_8df55_row9_col1, #T_8df55_row10_col0, #T_8df55_row10_col1, #T_8df55_row11_col0, #T_8df55_row11_col1 {
  text-align: right;
}
</style>
<table id="T_8df55">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_8df55_level0_col0" class="col_heading level0 col0" >Δ Schnee (s)</th>
      <th id="T_8df55_level0_col1" class="col_heading level0 col1" >Δ Starkregen (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >District</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_8df55_level0_row0" class="row_heading level0 row0" >Kreis 7</th>
      <td id="T_8df55_row0_col0" class="data row0 col0" >37.70</td>
      <td id="T_8df55_row0_col1" class="data row0 col1" >18.00</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row1" class="row_heading level0 row1" >Kreis 9</th>
      <td id="T_8df55_row1_col0" class="data row1 col0" >44.40</td>
      <td id="T_8df55_row1_col1" class="data row1 col1" >28.50</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row2" class="row_heading level0 row2" >Kreis 5</th>
      <td id="T_8df55_row2_col0" class="data row2 col0" >45.90</td>
      <td id="T_8df55_row2_col1" class="data row2 col1" >37.20</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row3" class="row_heading level0 row3" >Kreis 10</th>
      <td id="T_8df55_row3_col0" class="data row3 col0" >89.60</td>
      <td id="T_8df55_row3_col1" class="data row3 col1" >27.70</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row4" class="row_heading level0 row4" >Kreis 8</th>
      <td id="T_8df55_row4_col0" class="data row4 col0" >54.70</td>
      <td id="T_8df55_row4_col1" class="data row4 col1" >27.50</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row5" class="row_heading level0 row5" >Kreis 12</th>
      <td id="T_8df55_row5_col0" class="data row5 col0" >65.40</td>
      <td id="T_8df55_row5_col1" class="data row5 col1" >13.60</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row6" class="row_heading level0 row6" >Kreis 4</th>
      <td id="T_8df55_row6_col0" class="data row6 col0" >70.50</td>
      <td id="T_8df55_row6_col1" class="data row6 col1" >24.00</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row7" class="row_heading level0 row7" >Kreis 2</th>
      <td id="T_8df55_row7_col0" class="data row7 col0" >74.70</td>
      <td id="T_8df55_row7_col1" class="data row7 col1" >25.30</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row8" class="row_heading level0 row8" >Kreis 11</th>
      <td id="T_8df55_row8_col0" class="data row8 col0" >49.70</td>
      <td id="T_8df55_row8_col1" class="data row8 col1" >21.40</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row9" class="row_heading level0 row9" >Kreis 6</th>
      <td id="T_8df55_row9_col0" class="data row9 col0" >49.50</td>
      <td id="T_8df55_row9_col1" class="data row9 col1" >20.80</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row10" class="row_heading level0 row10" >Kreis 1</th>
      <td id="T_8df55_row10_col0" class="data row10 col0" >48.70</td>
      <td id="T_8df55_row10_col1" class="data row10 col1" >24.50</td>
    </tr>
    <tr>
      <th id="T_8df55_level0_row11" class="row_heading level0 row11" >Kreis 3</th>
      <td id="T_8df55_row11_col0" class="data row11 col0" >71.40</td>
      <td id="T_8df55_row11_col1" class="data row11 col1" >23.40</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Sortierung wechselt komplett zwischen Schnee und Regen — ein starkes Signal für topographische Ursachen.

| Stadtkreis | Δ Schnee | Δ Regen | Charakter |
|:---|---:|---:|:---|
| **Kreis 10** | **+89.4s** | +27.5s | Höngg — erhöhte Lage, exponiert |
| **Kreis 5** | +45.5s | **+36.8s** | Escher Wyss — Limmat-Niederung |
| Kreis 12 | +64.8s | +13.0s | Schwamendingen — suburban, erhöht |
| Kreis 4 | +69.9s | +23.5s | Aussersihl — urban, Hardbrücke-Korridor |

**Kernbefund:** Schnee trifft exponierte Höhenlagen (Kreis 10, 12, 4). Regen trifft Flusstäler und Niederlagen (Kreis 5, 9). Die Topographie bestimmt die Wetterempfindlichkeit.

## Haltestellen-Ranking — Schnee vs. Starkregen

Top 20 Haltestellen nach Δ Delay — sortiert, mit Durchschnittslinie. Kreise über dem Durchschnitt hervorgehoben. Beide Wetterereignisse separat — die Reihenfolge ändert sich zwischen Schnee und Starkregen.


```python
an.plot_stop_weather_ranking(lf_clean, cfg)
show_df(an.table_stop_weather_ranking(lf_clean))
```


    
![png](03_analysis_5-meteo_files/03_analysis_5-meteo_29_0.png)
    



<style type="text/css">
#T_fee5f thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_fee5f td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_fee5f tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_fee5f tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_fee5f tr:hover td {
  background-color: #eef3f8;
}
#T_fee5f_row0_col0, #T_fee5f_row0_col1, #T_fee5f_row1_col0, #T_fee5f_row1_col1, #T_fee5f_row2_col0, #T_fee5f_row2_col1, #T_fee5f_row3_col0, #T_fee5f_row3_col1, #T_fee5f_row4_col0, #T_fee5f_row4_col1, #T_fee5f_row5_col0, #T_fee5f_row5_col1, #T_fee5f_row6_col0, #T_fee5f_row6_col1, #T_fee5f_row7_col0, #T_fee5f_row7_col1, #T_fee5f_row8_col0, #T_fee5f_row8_col1, #T_fee5f_row9_col0, #T_fee5f_row9_col1, #T_fee5f_row10_col0, #T_fee5f_row10_col1, #T_fee5f_row11_col0, #T_fee5f_row11_col1, #T_fee5f_row12_col0, #T_fee5f_row12_col1, #T_fee5f_row13_col0, #T_fee5f_row13_col1, #T_fee5f_row14_col0, #T_fee5f_row14_col1, #T_fee5f_row15_col0, #T_fee5f_row15_col1, #T_fee5f_row16_col0, #T_fee5f_row16_col1, #T_fee5f_row17_col0, #T_fee5f_row17_col1, #T_fee5f_row18_col0, #T_fee5f_row18_col1, #T_fee5f_row19_col0, #T_fee5f_row19_col1, #T_fee5f_row20_col0, #T_fee5f_row20_col1, #T_fee5f_row21_col0, #T_fee5f_row21_col1, #T_fee5f_row22_col0, #T_fee5f_row22_col1, #T_fee5f_row23_col0, #T_fee5f_row23_col1, #T_fee5f_row24_col0, #T_fee5f_row24_col1, #T_fee5f_row25_col0, #T_fee5f_row25_col1, #T_fee5f_row26_col0, #T_fee5f_row26_col1, #T_fee5f_row27_col0, #T_fee5f_row27_col1, #T_fee5f_row28_col0, #T_fee5f_row28_col1, #T_fee5f_row29_col0, #T_fee5f_row29_col1, #T_fee5f_row30_col0, #T_fee5f_row30_col1, #T_fee5f_row31_col0, #T_fee5f_row31_col1, #T_fee5f_row32_col0, #T_fee5f_row32_col1, #T_fee5f_row33_col0, #T_fee5f_row33_col1, #T_fee5f_row34_col0, #T_fee5f_row34_col1 {
  text-align: right;
}
</style>
<table id="T_fee5f">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_fee5f_level0_col0" class="col_heading level0 col0" >Δ Schnee (s)</th>
      <th id="T_fee5f_level0_col1" class="col_heading level0 col1" >Δ Starkregen (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Stop</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_fee5f_level0_row0" class="row_heading level0 row0" >Zürich, Bahnhof Selnau</th>
      <td id="T_fee5f_row0_col0" class="data row0 col0" >191.60</td>
      <td id="T_fee5f_row0_col1" class="data row0 col1" >34.80</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row1" class="row_heading level0 row1" >Zürich, Rentenanstalt</th>
      <td id="T_fee5f_row1_col0" class="data row1 col0" >104.40</td>
      <td id="T_fee5f_row1_col1" class="data row1 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row2" class="row_heading level0 row2" >Zürich, Alte Trotte</th>
      <td id="T_fee5f_row2_col0" class="data row2 col0" >106.30</td>
      <td id="T_fee5f_row2_col1" class="data row2 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row3" class="row_heading level0 row3" >Zürich, Löwenbräu</th>
      <td id="T_fee5f_row3_col0" class="data row3 col0" >nan</td>
      <td id="T_fee5f_row3_col1" class="data row3 col1" >39.40</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row4" class="row_heading level0 row4" >Zürich, Güterbahnhof</th>
      <td id="T_fee5f_row4_col0" class="data row4 col0" >108.90</td>
      <td id="T_fee5f_row4_col1" class="data row4 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row5" class="row_heading level0 row5" >Zürich, Tunnelstrasse</th>
      <td id="T_fee5f_row5_col0" class="data row5 col0" >95.70</td>
      <td id="T_fee5f_row5_col1" class="data row5 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row6" class="row_heading level0 row6" >Zürich, Helvetiaplatz</th>
      <td id="T_fee5f_row6_col0" class="data row6 col0" >117.90</td>
      <td id="T_fee5f_row6_col1" class="data row6 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row7" class="row_heading level0 row7" >Zürich, Zwielplatz</th>
      <td id="T_fee5f_row7_col0" class="data row7 col0" >86.30</td>
      <td id="T_fee5f_row7_col1" class="data row7 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row8" class="row_heading level0 row8" >Zürich, Bahnhofquai/HB</th>
      <td id="T_fee5f_row8_col0" class="data row8 col0" >nan</td>
      <td id="T_fee5f_row8_col1" class="data row8 col1" >36.60</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row9" class="row_heading level0 row9" >Zürich, Quellenstrasse</th>
      <td id="T_fee5f_row9_col0" class="data row9 col0" >nan</td>
      <td id="T_fee5f_row9_col1" class="data row9 col1" >39.70</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row10" class="row_heading level0 row10" >Zürich, Bernoulli-Häuser</th>
      <td id="T_fee5f_row10_col0" class="data row10 col0" >nan</td>
      <td id="T_fee5f_row10_col1" class="data row10 col1" >37.10</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row11" class="row_heading level0 row11" >Zürich, Uetlihof</th>
      <td id="T_fee5f_row11_col0" class="data row11 col0" >104.60</td>
      <td id="T_fee5f_row11_col1" class="data row11 col1" >35.20</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row12" class="row_heading level0 row12" >Zürich, Museum für Gestaltung</th>
      <td id="T_fee5f_row12_col0" class="data row12 col0" >nan</td>
      <td id="T_fee5f_row12_col1" class="data row12 col1" >38.90</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row13" class="row_heading level0 row13" >Zürich, Waidfussweg</th>
      <td id="T_fee5f_row13_col0" class="data row13 col0" >110.40</td>
      <td id="T_fee5f_row13_col1" class="data row13 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row14" class="row_heading level0 row14" >Zürich, Bad Allenmoos</th>
      <td id="T_fee5f_row14_col0" class="data row14 col0" >nan</td>
      <td id="T_fee5f_row14_col1" class="data row14 col1" >37.70</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row15" class="row_heading level0 row15" >Zürich, Technopark</th>
      <td id="T_fee5f_row15_col0" class="data row15 col0" >nan</td>
      <td id="T_fee5f_row15_col1" class="data row15 col1" >42.20</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row16" class="row_heading level0 row16" >Zürich, Eschergutweg</th>
      <td id="T_fee5f_row16_col0" class="data row16 col0" >105.20</td>
      <td id="T_fee5f_row16_col1" class="data row16 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row17" class="row_heading level0 row17" >Zürich, Aargauerstrasse</th>
      <td id="T_fee5f_row17_col0" class="data row17 col0" >nan</td>
      <td id="T_fee5f_row17_col1" class="data row17 col1" >39.00</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row18" class="row_heading level0 row18" >Zürich, Meierhofplatz</th>
      <td id="T_fee5f_row18_col0" class="data row18 col0" >86.70</td>
      <td id="T_fee5f_row18_col1" class="data row18 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row19" class="row_heading level0 row19" >Zürich, Bäckeranlage</th>
      <td id="T_fee5f_row19_col0" class="data row19 col0" >112.30</td>
      <td id="T_fee5f_row19_col1" class="data row19 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row20" class="row_heading level0 row20" >Zürich, Toni-Areal</th>
      <td id="T_fee5f_row20_col0" class="data row20 col0" >nan</td>
      <td id="T_fee5f_row20_col1" class="data row20 col1" >44.50</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row21" class="row_heading level0 row21" >Zürich, Wartau</th>
      <td id="T_fee5f_row21_col0" class="data row21 col0" >86.40</td>
      <td id="T_fee5f_row21_col1" class="data row21 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row22" class="row_heading level0 row22" >Zürich, Schwert</th>
      <td id="T_fee5f_row22_col0" class="data row22 col0" >86.70</td>
      <td id="T_fee5f_row22_col1" class="data row22 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row23" class="row_heading level0 row23" >Zürich, Wipkingerplatz</th>
      <td id="T_fee5f_row23_col0" class="data row23 col0" >90.10</td>
      <td id="T_fee5f_row23_col1" class="data row23 col1" >37.60</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row24" class="row_heading level0 row24" >Zürich, Bahnhof Hardbrücke</th>
      <td id="T_fee5f_row24_col0" class="data row24 col0" >117.90</td>
      <td id="T_fee5f_row24_col1" class="data row24 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row25" class="row_heading level0 row25" >Zürich, Bahnhof Enge</th>
      <td id="T_fee5f_row25_col0" class="data row25 col0" >98.80</td>
      <td id="T_fee5f_row25_col1" class="data row25 col1" >nan</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row26" class="row_heading level0 row26" >Zürich, Sportweg</th>
      <td id="T_fee5f_row26_col0" class="data row26 col0" >nan</td>
      <td id="T_fee5f_row26_col1" class="data row26 col1" >40.00</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row27" class="row_heading level0 row27" >Zürich, Saalsporthalle</th>
      <td id="T_fee5f_row27_col0" class="data row27 col0" >87.30</td>
      <td id="T_fee5f_row27_col1" class="data row27 col1" >38.00</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row28" class="row_heading level0 row28" >Zürich, Wildbachstrasse</th>
      <td id="T_fee5f_row28_col0" class="data row28 col0" >nan</td>
      <td id="T_fee5f_row28_col1" class="data row28 col1" >38.80</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row29" class="row_heading level0 row29" >Zürich, Escher-Wyss-Platz</th>
      <td id="T_fee5f_row29_col0" class="data row29 col0" >nan</td>
      <td id="T_fee5f_row29_col1" class="data row29 col1" >37.30</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row30" class="row_heading level0 row30" >Zürich, Laubegg</th>
      <td id="T_fee5f_row30_col0" class="data row30 col0" >101.30</td>
      <td id="T_fee5f_row30_col1" class="data row30 col1" >39.20</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row31" class="row_heading level0 row31" >Zürich, Grünaustrasse</th>
      <td id="T_fee5f_row31_col0" class="data row31 col0" >nan</td>
      <td id="T_fee5f_row31_col1" class="data row31 col1" >34.80</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row32" class="row_heading level0 row32" >Zürich, Sihlquai/HB</th>
      <td id="T_fee5f_row32_col0" class="data row32 col0" >nan</td>
      <td id="T_fee5f_row32_col1" class="data row32 col1" >36.10</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row33" class="row_heading level0 row33" >Zürich, Limmatplatz</th>
      <td id="T_fee5f_row33_col0" class="data row33 col0" >nan</td>
      <td id="T_fee5f_row33_col1" class="data row33 col1" >38.60</td>
    </tr>
    <tr>
      <th id="T_fee5f_level0_row34" class="row_heading level0 row34" >Zürich, Hardplatz</th>
      <td id="T_fee5f_row34_col0" class="data row34 col0" >116.60</td>
      <td id="T_fee5f_row34_col1" class="data row34 col1" >nan</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Schnee und Regen treffen komplett verschiedene Haltestellen — kaum Überschneidung in den Top 20.

**Schnee-Ausreisser: Bahnhof Selnau (+190.9s)**
Normal 55.6s → Schnee 246.5s — fast 4× der Normalverzögerung. Einzige Haltestelle in dieser Größenordnung. Selnau liegt am Sihl-Ufer und ist Endpunkt mehrerer Linien; Verzögerungen akkumulieren sich dort. Starker Kandidat für operative Maßnahmen bei Schneeereignissen.

**Schnee-Cluster Kreis 4:** Helvetiaplatz, Bahnhof Hardbrücke, Hardplatz, Bäckeranlage — alle ~115s Delta. Dichter Korridor in Aussersihl.

**Schnee-Cluster Kreis 10:** 8 von 20 Top-Haltestellen in Höngg/Wipkingen — erhöhte Lage, Strecken besonders exponiert.

**Regen-Cluster Kreis 5:** 11 von 20 Top-Haltestellen im Escher Wyss / Toni-Areal Korridor. Toni-Areal +44.2s, Technopark +42.0s — Limmat-Niederung mit Drainage-Problemen bei Starkregen.

→ Räumlich trennscharf: Schnee = Höhenlagen, Regen = Limmat-Korridor.

## Linien-Betroffenheit — Welche Linien leiden am meisten?

Δ Delay pro Linie an Schnee- und Starkregen-Tagen. Zeigt welche Linien besonders wetterempfindlich sind — und ob die Reihenfolge zwischen Schnee und Regen wechselt.


```python
an.plot_line_weather_exposure(lf_clean, cfg)
show_df(an.table_line_weather_exposure(lf_clean))
```


    
![png](03_analysis_5-meteo_files/03_analysis_5-meteo_33_0.png)
    



<style type="text/css">
#T_b368e thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_b368e td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_b368e tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_b368e tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_b368e tr:hover td {
  background-color: #eef3f8;
}
#T_b368e_row0_col0, #T_b368e_row0_col1, #T_b368e_row1_col0, #T_b368e_row1_col1, #T_b368e_row2_col0, #T_b368e_row2_col1, #T_b368e_row3_col0, #T_b368e_row3_col1, #T_b368e_row4_col0, #T_b368e_row4_col1, #T_b368e_row5_col0, #T_b368e_row5_col1, #T_b368e_row6_col0, #T_b368e_row6_col1, #T_b368e_row7_col0, #T_b368e_row7_col1, #T_b368e_row8_col0, #T_b368e_row8_col1, #T_b368e_row9_col0, #T_b368e_row9_col1, #T_b368e_row10_col0, #T_b368e_row10_col1, #T_b368e_row11_col0, #T_b368e_row11_col1, #T_b368e_row12_col0, #T_b368e_row12_col1, #T_b368e_row13_col0, #T_b368e_row13_col1, #T_b368e_row14_col0, #T_b368e_row14_col1 {
  text-align: right;
}
</style>
<table id="T_b368e">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_b368e_level0_col0" class="col_heading level0 col0" >Δ Schnee (s)</th>
      <th id="T_b368e_level0_col1" class="col_heading level0 col1" >Δ Starkregen (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Line</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_b368e_level0_row0" class="row_heading level0 row0" >13</th>
      <td id="T_b368e_row0_col0" class="data row0 col0" >82.40</td>
      <td id="T_b368e_row0_col1" class="data row0 col1" >38.00</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row1" class="row_heading level0 row1" >9</th>
      <td id="T_b368e_row1_col0" class="data row1 col0" >76.40</td>
      <td id="T_b368e_row1_col1" class="data row1 col1" >10.50</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row2" class="row_heading level0 row2" >8</th>
      <td id="T_b368e_row2_col0" class="data row2 col0" >70.00</td>
      <td id="T_b368e_row2_col1" class="data row2 col1" >32.30</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row3" class="row_heading level0 row3" >7</th>
      <td id="T_b368e_row3_col0" class="data row3 col0" >64.40</td>
      <td id="T_b368e_row3_col1" class="data row3 col1" >21.50</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row4" class="row_heading level0 row4" >2</th>
      <td id="T_b368e_row4_col0" class="data row4 col0" >59.00</td>
      <td id="T_b368e_row4_col1" class="data row4 col1" >23.60</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row5" class="row_heading level0 row5" >6</th>
      <td id="T_b368e_row5_col0" class="data row5 col0" >53.00</td>
      <td id="T_b368e_row5_col1" class="data row5 col1" >16.60</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row6" class="row_heading level0 row6" >12</th>
      <td id="T_b368e_row6_col0" class="data row6 col0" >52.00</td>
      <td id="T_b368e_row6_col1" class="data row6 col1" >5.40</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row7" class="row_heading level0 row7" >10</th>
      <td id="T_b368e_row7_col0" class="data row7 col0" >50.50</td>
      <td id="T_b368e_row7_col1" class="data row7 col1" >17.00</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row8" class="row_heading level0 row8" >11</th>
      <td id="T_b368e_row8_col0" class="data row8 col0" >49.80</td>
      <td id="T_b368e_row8_col1" class="data row8 col1" >24.80</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row9" class="row_heading level0 row9" >3</th>
      <td id="T_b368e_row9_col0" class="data row9 col0" >47.10</td>
      <td id="T_b368e_row9_col1" class="data row9 col1" >15.30</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row10" class="row_heading level0 row10" >4</th>
      <td id="T_b368e_row10_col0" class="data row10 col0" >44.40</td>
      <td id="T_b368e_row10_col1" class="data row10 col1" >40.70</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row11" class="row_heading level0 row11" >5</th>
      <td id="T_b368e_row11_col0" class="data row11 col0" >43.20</td>
      <td id="T_b368e_row11_col1" class="data row11 col1" >10.10</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row12" class="row_heading level0 row12" >14</th>
      <td id="T_b368e_row12_col0" class="data row12 col0" >37.70</td>
      <td id="T_b368e_row12_col1" class="data row12 col1" >19.50</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row13" class="row_heading level0 row13" >15</th>
      <td id="T_b368e_row13_col0" class="data row13 col0" >19.00</td>
      <td id="T_b368e_row13_col1" class="data row13 col1" >20.00</td>
    </tr>
    <tr>
      <th id="T_b368e_level0_row14" class="row_heading level0 row14" >17</th>
      <td id="T_b368e_row14_col0" class="data row14 col0" >8.20</td>
      <td id="T_b368e_row14_col1" class="data row14 col1" >41.70</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Linien-Reihenfolge wechselt zwischen Schnee und Regen drastisch — das stärkste Muster im gesamten Wetter-Notebook.

| Linie | Δ Schnee | Δ Regen | Charakteristik |
|:---|---:|---:|:---|
| **13** | **+82.1s** | +37.7s | Hoch bei beiden — kreuzt beide Zonen |
| **9** | +75.9s | +10.0s | Schnee-Linie — Triemli, erhöhte Lagen |
| **17** | +7.7s | **+41.2s** | Regen-Linie — flache Limmat-Route durch Kreis 5 |
| **12** | +51.7s | +5.0s | Stärkster Gegensatz — Schwamendingen/Northeast |
| **4** | +44.2s | +40.4s | Ausgeglichen hoch — zentrale Achse |

**Kernbefund:** Linie 17 ist der klarste Beweis — Schnee fast irrelevant (+7.7s), Regen Platz 1 (+41.2s). Route führt flach durch den Escher Wyss / Kreis 5 Korridor. Linie 9 und 12 sind das Gegenteil: erhöhte Strecken, stark bei Schnee, kaum bei Regen.

→ Topographie des Linienverlaufs bestimmt die Wetterempfindlichkeit der Linie. Vorhersagemodell könnte davon profitieren: Linie + Wettertyp als Interaktionsterm.

## Multikollinearität — Wetter × Saison


```python
an.plot_multicollinearity_matrix(lf_delay, cfg)
show_df(an.table_correlation_with_delay(lf_delay))
```


    
![png](03_analysis_5-meteo_files/03_analysis_5-meteo_36_0.png)
    


    Korrelation mit arrival_delay (abs. sortiert):
      season                   : +0.042  (abs: 0.042)
      has_snow                 : +0.038  (abs: 0.038)
      precipitation            : +0.036  (abs: 0.036)
      has_rain                 : +0.036  (abs: 0.036)
      month                    : +0.034  (abs: 0.034)
      temperature              : +0.018  (abs: 0.018)
      has_heavy_rain           : +0.015  (abs: 0.015)
    
    Wetter-Flags × Saison-Korrelation:
      has_rain             × season: -0.006
      has_heavy_rain       × season: +0.012
      has_snow             × season: -0.048



<style type="text/css">
#T_60a20 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_60a20 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_60a20 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_60a20 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_60a20 tr:hover td {
  background-color: #eef3f8;
}
#T_60a20_row0_col0, #T_60a20_row0_col1, #T_60a20_row1_col0, #T_60a20_row1_col1, #T_60a20_row2_col0, #T_60a20_row2_col1, #T_60a20_row3_col0, #T_60a20_row3_col1, #T_60a20_row4_col0, #T_60a20_row4_col1, #T_60a20_row5_col0, #T_60a20_row5_col1, #T_60a20_row6_col0, #T_60a20_row6_col1 {
  text-align: right;
}
</style>
<table id="T_60a20">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_60a20_level0_col0" class="col_heading level0 col0" >Korrelation mit delay</th>
      <th id="T_60a20_level0_col1" class="col_heading level0 col1" >|Korrelation|</th>
    </tr>
    <tr>
      <th class="index_name level0" >Feature</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_60a20_level0_row0" class="row_heading level0 row0" >season</th>
      <td id="T_60a20_row0_col0" class="data row0 col0" >0.04</td>
      <td id="T_60a20_row0_col1" class="data row0 col1" >0.04</td>
    </tr>
    <tr>
      <th id="T_60a20_level0_row1" class="row_heading level0 row1" >has_snow</th>
      <td id="T_60a20_row1_col0" class="data row1 col0" >0.04</td>
      <td id="T_60a20_row1_col1" class="data row1 col1" >0.04</td>
    </tr>
    <tr>
      <th id="T_60a20_level0_row2" class="row_heading level0 row2" >precipitation</th>
      <td id="T_60a20_row2_col0" class="data row2 col0" >0.04</td>
      <td id="T_60a20_row2_col1" class="data row2 col1" >0.04</td>
    </tr>
    <tr>
      <th id="T_60a20_level0_row3" class="row_heading level0 row3" >has_rain</th>
      <td id="T_60a20_row3_col0" class="data row3 col0" >0.04</td>
      <td id="T_60a20_row3_col1" class="data row3 col1" >0.04</td>
    </tr>
    <tr>
      <th id="T_60a20_level0_row4" class="row_heading level0 row4" >month</th>
      <td id="T_60a20_row4_col0" class="data row4 col0" >0.03</td>
      <td id="T_60a20_row4_col1" class="data row4 col1" >0.03</td>
    </tr>
    <tr>
      <th id="T_60a20_level0_row5" class="row_heading level0 row5" >temperature</th>
      <td id="T_60a20_row5_col0" class="data row5 col0" >0.02</td>
      <td id="T_60a20_row5_col1" class="data row5 col1" >0.02</td>
    </tr>
    <tr>
      <th id="T_60a20_level0_row6" class="row_heading level0 row6" >has_heavy_rain</th>
      <td id="T_60a20_row6_col0" class="data row6 col0" >0.01</td>
      <td id="T_60a20_row6_col1" class="data row6 col1" >0.01</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Korrelationsmatrix bestätigt die erwarteten Zusammenhänge.

**Korrelation mit `arrival_delay` (abs. sortiert):**
- `has_snow` hat die stärkste Korrelation (~0.03–0.05) — absolut gering, aber konsistent
- Wetter-Features sind alle schwach korreliert mit Delay (r < 0.1) — Delay ist primär durch betriebliche Faktoren bestimmt
- `season` und `month` korrelieren erwartungsgemäss mit Wetter-Flags (Multikollinearität vorhanden)
- `has_rain` × `season`: negative Korrelation — Sommer (Season=3) ist trockener als Herbst

→ Wetter-Features sind schwache aber valide Prädiktoren; Multikollinearität mit Saison-Features beim Modellbau beachten.

## Schnee-Verstärker: Strukturelle Verstärkung bei Schnee

Schnee verursacht nicht nur externen Zusatz-Delay — er verstärkt auch den **strukturellen Aufbau-Mechanismus** im Netz.

Jede Haltestelle akkumuliert unter Schnee durchschnittlich **+33 % mehr Delay** als bei Normalbedingungen (`delay_delta`: 4.95 s → 6.58 s/Halt). Für Fahrgäste ergibt sich am Ende der Fahrt ein Zusatz-Impact von **+54 s** Arrival Delay.

Zwei Panels: (1) Akkumulationsrate pro Halt — strukturelle Verstärkung · (2) Sichtbarer Fahrgast-Impact.


```python
an.plot_snow_structural_interaction(lf_clean)
```


    
![png](03_analysis_5-meteo_files/03_analysis_5-meteo_39_0.png)
    


## Key Findings

→ Vollständige Findings-Tabelle mit Impact und Action in [`03_analysis_0-overview.ipynb`](03_analysis_0-overview.ipynb).

`Präsentation`: **hot** = Kernbefund für Präsentation · **story** = gutes Narrativ · **—** = intern/Feature-Engineering

| ID | Finding | Präsentation |
|:---|:---|:---:|
| F-WEAT-01 | **Schnee** stärkster Wettereffekt: +54.0s, OTP 87.1%→76.1% — klarer Schwellwert-Effekt | **hot** |
| F-WEAT-02 | Starkregen: +23.3s, OTP −7.6pp. Niederschlagsintensität zeigt klare Dosis-Wirkungs-Beziehung: <2mm: 62.6s → >10mm: 89.5s | **story** |
| F-WEAT-03 | `is_windy` zeigt NaN — nie korrekt befüllt, inhaltlich kaum relevant. **Aus Feature-Set entfernt.** | — |
| F-WEAT-04 | Temperatureffekt monoton ansteigend. 0–5°C = bester Bereich (53.8s). `is_hot` (>20°C) = +2.0s — schwaches aber reales Signal | — |
| F-WEAT-05 | Alle Wetter-Features schwach korreliert (max r=0.042). Keine Multikollinearität mit Saison — unabhängige Signale | — |
| F-WEAT-06 | `precipitation` (r=0.036) und `has_snow` (r=0.038) nützlichste Features; `temperature` (r=0.018) schwächer | — |
| F-WEAT-07 | **Geografische Trennung:** Schnee trifft Höhenlagen (Kreis 10/4/12), Regen trifft Flusstäler (Kreis 5). Topographie bestimmt Vulnerabilität. Bahnhof Selnau extremer Schnee-Ausreisser: +190.9s (4× Normal) | **hot** |
| F-WEAT-08 | **Regen-Korridor Kreis 5:** 11 von top 20 Regen-Haltestellen im Escher Wyss / Toni-Areal / Limmat-Niederung. Toni-Areal +44.2s, Technopark +42.0s | **story** |
| F-WEAT-09 | **Linien reagieren komplett unterschiedlich:** Linie 17 Schnee +7.7s vs. Regen +41.2s (flache Limmat-Route). Linie 9 Schnee +75.9s vs. Regen +10.0s (erhöhte Lagen). Linie × Wettertyp als Interaktionsterm prüfen | **hot** |
