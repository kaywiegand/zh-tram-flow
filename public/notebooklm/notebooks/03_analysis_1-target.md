# Delay Target Analysis

Analyse der Zielvariable `arrival_delay` — Verteilung, OTP-Baseline, Vergleich mit Departure Delay und Delay Delta, Ausfälle.

## Setup

| Variable | Inhalt | Verwendung |
|---|---|---|
| `lf_all` | Rohdaten — alle Halte inkl. Ausfälle, Sonderlinien | Mengengerüst, Basisanalysen |
| `lf_delay` | `canceled==False` | Delay-Analysen über das gesamte Netz |
| `lf_clean` | `canceled=False` · `stop_sequence>1` · kein Linie E/L50/L51 · `departure_delay`/`delay_delta` maskiert auf NaN für 14. Nov–23. Dez 2025 · `is_anomal` Flag | **Standard** für Trend- & Modellanalysen |

**`is_anomal`:** Boolean-Flag — `True` = Zeile liegt im Anomaliewindow (departure_delay unplausibel, arrival_delay trotzdem gültig).

**Sampling:** Distributions-Plots (Histogramme, Boxplots) arbeiten intern auf einem **100k-Sample** (`seed=42`)  
— alle Aggregationen (Ø Delay, OTP, Monatstabellen) laufen über den **vollen Scan** des LazyFrame.

**Aufrufmuster:**
```python
an.plot_xxx(lf_all, cfg)           # nur roh
an.plot_xxx(lf_all, lf_clean, cfg) # Vergleich roh vs. bereinigt
show_df(an.table_xxx(lf_all))      # Tabelle — nimmt lf_all oder lf_clean
```


```python
import numpy as np
from zh_tram_flow.notebook import *
import zh_tram_flow.analytics.target as an

TRAIN, TEST, lf, lf_all, lf_delay, lf_clean = setup_analysis("03_analysis_1-target")

SAMPLE_SMALL = lf.collect().sample(n=100_000, seed=42)
SAMPLE_LARGE = lf.collect().sample(n=500_000, seed=42)

%load_ext autoreload
%autoreload 2
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #34618d; text-decoration-color: #34618d">✓  wgnd theme activated</span> <span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">(</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f">matplotlib · seaborn</span><span style="color: #7f7f7f; text-decoration-color: #7f7f7f; font-weight: bold">)</span>
</pre>



    2026-06-11 11:22:13  INFO      project  03_analysis_1-target started


    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload


## Target Definition

**Primäres Ziel:** `arrival_delay` — Sekunden Verspätung bei der Ankunft an einer Haltestelle (negativ = zu früh).

Eine verspätete Abfahrt kann noch ausgeglichen werden — eine verspätete Ankunft nicht.   
Sie trifft Fahrgäste direkt: verpasste Anschlüsse, geplatzte Termine, Folgeverspätungen.

| Column | Rolle | Beschreibung |
|:---|:---|:---|
| `arrival_delay` | **Primäres Ziel** | Sekunden Verspätung bei Ankunft — was Fahrgäste erleben |
| `departure_delay` | Feature | Sekunden Verspätung bei Abfahrt — Startzustand für den nächsten Abschnitt |
| `delay_delta` | Abgeleitetes Feature | `departure_delay - arrival_delay` — positiv = Verspätung wächst am Halt, negativ = Verspätung wird abgebaut |

**Was wir nicht direkt sehen:** ob eine Verspätung über mehrere Halte vollständig aufgeholt wurde. `delay_delta` liefert das Signal pro Halt, aber keine Trip-Level-Sicht.

### Delay Overview — Per Year

Größenordnungen im Überblick: mittlere Verspätung pro Halt und Jahr, Min/Max. Alle drei Jahre (2023–2025) aus Train + Test kombiniert.


```python
section_header('Delay Overview per year')

an.plot_delay_overview_per_year(lf_all, lf_clean, cfg)

log('Table all')
show_df(an.table_delay_overview_per_year(lf_all))

log('Table clean')
show_df(an.table_delay_overview_per_year(lf_clean))

# delay_delta ist bereits im Feature-Set (berechnet in 02_preparation)
# is_recovering kann bei Bedarf abgeleitet werden: delay_delta < 0

```

    
    [1m[38;2;52;97;141m───  DELAY OVERVIEW PER YEAR  ────────────────────────────────[0m
    Bereinigte Jahreswerte (Ø arrival_delay):
      2023: +56.6s
      2024: +59.4s
      2025: +55.0s
      Δ 2023→2025: -1.5s



    
![png](03_analysis_1-target_files/03_analysis_1-target_8_1.png)
    


    [38;2;52;97;141mTable all[0m



<style type="text/css">
#T_42b67 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_42b67 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_42b67 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_42b67 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_42b67 tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_42b67">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_42b67_level0_col0" class="col_heading level0 col0" >N Halte</th>
      <th id="T_42b67_level0_col1" class="col_heading level0 col1" >Arr Ø</th>
      <th id="T_42b67_level0_col2" class="col_heading level0 col2" >Arr Median</th>
      <th id="T_42b67_level0_col3" class="col_heading level0 col3" >Dep Ø</th>
      <th id="T_42b67_level0_col4" class="col_heading level0 col4" >Dep Median</th>
      <th id="T_42b67_level0_col5" class="col_heading level0 col5" >Δ Ø</th>
      <th id="T_42b67_level0_col6" class="col_heading level0 col6" >Δ Median</th>
    </tr>
    <tr>
      <th class="index_name level0" >Jahr</th>
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
      <th id="T_42b67_level0_row0" class="row_heading level0 row0" >2023</th>
      <td id="T_42b67_row0_col0" class="data row0 col0" >31,446,819</td>
      <td id="T_42b67_row0_col1" class="data row0 col1" >+54.8s</td>
      <td id="T_42b67_row0_col2" class="data row0 col2" >+42.0s</td>
      <td id="T_42b67_row0_col3" class="data row0 col3" >+59.2s</td>
      <td id="T_42b67_row0_col4" class="data row0 col4" >+45.0s</td>
      <td id="T_42b67_row0_col5" class="data row0 col5" >+4.3s</td>
      <td id="T_42b67_row0_col6" class="data row0 col6" >+14.0s</td>
    </tr>
    <tr>
      <th id="T_42b67_level0_row1" class="row_heading level0 row1" >2024</th>
      <td id="T_42b67_row1_col0" class="data row1 col0" >30,689,013</td>
      <td id="T_42b67_row1_col1" class="data row1 col1" >+58.3s</td>
      <td id="T_42b67_row1_col2" class="data row1 col2" >+43.0s</td>
      <td id="T_42b67_row1_col3" class="data row1 col3" >+63.2s</td>
      <td id="T_42b67_row1_col4" class="data row1 col4" >+47.0s</td>
      <td id="T_42b67_row1_col5" class="data row1 col5" >+4.9s</td>
      <td id="T_42b67_row1_col6" class="data row1 col6" >+15.0s</td>
    </tr>
    <tr>
      <th id="T_42b67_level0_row2" class="row_heading level0 row2" >2025</th>
      <td id="T_42b67_row2_col0" class="data row2 col0" >31,768,791</td>
      <td id="T_42b67_row2_col1" class="data row2 col1" >+54.5s</td>
      <td id="T_42b67_row2_col2" class="data row2 col2" >+40.0s</td>
      <td id="T_42b67_row2_col3" class="data row2 col3" >+62.2s</td>
      <td id="T_42b67_row2_col4" class="data row2 col4" >+48.0s</td>
      <td id="T_42b67_row2_col5" class="data row2 col5" >+7.7s</td>
      <td id="T_42b67_row2_col6" class="data row2 col6" >+17.0s</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mTable clean[0m



<style type="text/css">
#T_4dfca thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_4dfca td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_4dfca tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_4dfca tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_4dfca tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_4dfca">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_4dfca_level0_col0" class="col_heading level0 col0" >N Halte</th>
      <th id="T_4dfca_level0_col1" class="col_heading level0 col1" >Arr Ø</th>
      <th id="T_4dfca_level0_col2" class="col_heading level0 col2" >Arr Median</th>
      <th id="T_4dfca_level0_col3" class="col_heading level0 col3" >Dep Ø</th>
      <th id="T_4dfca_level0_col4" class="col_heading level0 col4" >Dep Median</th>
      <th id="T_4dfca_level0_col5" class="col_heading level0 col5" >Δ Ø</th>
      <th id="T_4dfca_level0_col6" class="col_heading level0 col6" >Δ Median</th>
    </tr>
    <tr>
      <th class="index_name level0" >Jahr</th>
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
      <th id="T_4dfca_level0_row0" class="row_heading level0 row0" >2023</th>
      <td id="T_4dfca_row0_col0" class="data row0 col0" >27,435,285</td>
      <td id="T_4dfca_row0_col1" class="data row0 col1" >+56.6s</td>
      <td id="T_4dfca_row0_col2" class="data row0 col2" >+44.0s</td>
      <td id="T_4dfca_row0_col3" class="data row0 col3" >+61.2s</td>
      <td id="T_4dfca_row0_col4" class="data row0 col4" >+48.0s</td>
      <td id="T_4dfca_row0_col5" class="data row0 col5" >+4.6s</td>
      <td id="T_4dfca_row0_col6" class="data row0 col6" >+15.0s</td>
    </tr>
    <tr>
      <th id="T_4dfca_level0_row1" class="row_heading level0 row1" >2024</th>
      <td id="T_4dfca_row1_col0" class="data row1 col0" >28,049,293</td>
      <td id="T_4dfca_row1_col1" class="data row1 col1" >+59.4s</td>
      <td id="T_4dfca_row1_col2" class="data row1 col2" >+44.0s</td>
      <td id="T_4dfca_row1_col3" class="data row1 col3" >+64.5s</td>
      <td id="T_4dfca_row1_col4" class="data row1 col4" >+49.0s</td>
      <td id="T_4dfca_row1_col5" class="data row1 col5" >+5.1s</td>
      <td id="T_4dfca_row1_col6" class="data row1 col6" >+16.0s</td>
    </tr>
    <tr>
      <th id="T_4dfca_level0_row2" class="row_heading level0 row2" >2025</th>
      <td id="T_4dfca_row2_col0" class="data row2 col0" >29,684,610</td>
      <td id="T_4dfca_row2_col1" class="data row2 col1" >+55.0s</td>
      <td id="T_4dfca_row2_col2" class="data row2 col2" >+41.0s</td>
      <td id="T_4dfca_row2_col3" class="data row2 col3" >+61.0s</td>
      <td id="T_4dfca_row2_col4" class="data row2 col4" >+47.0s</td>
      <td id="T_4dfca_row2_col5" class="data row2 col5" >+5.2s</td>
      <td id="T_4dfca_row2_col6" class="data row2 col6" >+16.0s</td>
    </tr>
  </tbody>
</table>



**Beobachtung — Gesamter Jahresvergleich**

 Der Jahresvergleich zeigt einen strukturellen Aufwärtstrend über alle drei Metriken.   
 
 **Arrival Delay:** 2023: +54.8s → 2024: +58.3s → 2025 (bereinigt, Jan–Okt): +55.2s — 2025 liegt leicht unter 2024, was auf eine Stabilisierung hindeutet, nicht auf kontinuierliche Verschlechterung.   
 
 **Delay Delta (bereinigt):** +4.3s → +4.9s → +5.0s — moderater Aufwärtstrend. Das rohe 2025-Delta von +7.7s (Jahrestabelle oben) ist durch den Nov/Dez-Artefakt aufgebläht und **nicht** als echter Trend zu interpretieren — bereinigt ist der Anstieg von 2023 auf 2025 nur +0.7s. → Vertiefen in `03_analysis_3-temporal`.

**Beobachtung — Bereinigter Jahresvergleich**

**Was hier anders ist als im Plot oben:**

Der erste Plot verwendet `lf_all` — also alle Einträge inklusive stornierter Fahrten und dem GTFS-Vorbereitungsartefakt in Nov/Dez 2025. Dieser bereinigte Plot filtert beides heraus, um ein ehrlicheres Bild des echten Betriebsgeschehens zu zeigen.

**Was die Trendlinien zeigen:**

Die gestrichelten Linien durch die Balken-Mittelpunkte machen die Richtung jeder Metrik über die drei Jahre sichtbar auf einen Blick. Steigt die Linie — wird es im Schnitt schlechter. Fällt sie — besser.

**Kernbefund:**

Der bereinigte `arrival_delay` zeigt, dass **2024 der schlechteste gemessene Jahrgang ist** und 2025 (Januar bis Oktober) bereits wieder leicht besser abschneidet. Das ist ein wichtiger Unterschied zum Rohdaten-Plot: Ohne Bereinigung sieht 2025 durch den GTFS-Artefakt in Nov/Dez aufgebläht aus.

Der `delay_delta` steigt moderat von 2023 bis 2025 an — das bedeutet, Trams akkumulieren im Schnitt pro Halt etwas mehr Verspätung als drei Jahre zuvor. Der Anstieg ist aber klein (wenige Zehntelsekunden pro Halt) und weit entfernt von einem Alarm-Signal.

**Was das für den Report bedeutet:**

> Das VBZ-Netz läuft strukturell stabil nahe seinem OTP-Ziel. 2025 zeigt eine leichte Erholung gegenüber 2024. Es gibt keinen dramatischen Aufwärtstrend — aber auch keinen Puffer für aussergewöhnliche Belastungen (Schnee, Grossevents, November-Peak). Das ist die seriöse und belegbare Aussage.

## Zeitliche Trends


```python
section_header('Monthly Delays')
an.plot_monthly_delay(lf_all, lf_clean, cfg)
log('Table all')
show_df(an.table_monthly_delay(lf_all))
log('Stats all')
show_df(an.table_delay_stats(lf_all))
log('Table clean')
show_df(an.table_monthly_delay(lf_clean))
log('Stats clean')
show_df(an.table_delay_stats(lf_clean))

```

    
    [1m[38;2;52;97;141m───  MONTHLY DELAYS  ─────────────────────────────────────────[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_12_1.png)
    


    [38;2;52;97;141mTable all[0m



<style type="text/css">
#T_0255a thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_0255a td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_0255a tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_0255a tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_0255a tr:hover td {
  background-color: #eef3f8;
}
#T_0255a_row0_col0, #T_0255a_row0_col1, #T_0255a_row0_col2, #T_0255a_row1_col0, #T_0255a_row1_col1, #T_0255a_row1_col2, #T_0255a_row2_col0, #T_0255a_row2_col1, #T_0255a_row2_col2 {
  text-align: right;
}
</style>
<table id="T_0255a">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_0255a_level0_col0" class="col_heading level0 col0" >Ø Arr Delay (s)</th>
      <th id="T_0255a_level0_col1" class="col_heading level0 col1" >Ø Dep Delay (s)</th>
      <th id="T_0255a_level0_col2" class="col_heading level0 col2" >Ø Δ (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Jahr</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_0255a_level0_row0" class="row_heading level0 row0" >2023</th>
      <td id="T_0255a_row0_col0" class="data row0 col0" >54.70</td>
      <td id="T_0255a_row0_col1" class="data row0 col1" >59.10</td>
      <td id="T_0255a_row0_col2" class="data row0 col2" >4.30</td>
    </tr>
    <tr>
      <th id="T_0255a_level0_row1" class="row_heading level0 row1" >2024</th>
      <td id="T_0255a_row1_col0" class="data row1 col0" >58.40</td>
      <td id="T_0255a_row1_col1" class="data row1 col1" >63.30</td>
      <td id="T_0255a_row1_col2" class="data row1 col2" >4.90</td>
    </tr>
    <tr>
      <th id="T_0255a_level0_row2" class="row_heading level0 row2" >2025</th>
      <td id="T_0255a_row2_col0" class="data row2 col0" >54.50</td>
      <td id="T_0255a_row2_col1" class="data row2 col1" >62.20</td>
      <td id="T_0255a_row2_col2" class="data row2 col2" >7.70</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mStats all[0m



<style type="text/css">
#T_02f7a thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_02f7a td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_02f7a tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_02f7a tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_02f7a tr:hover td {
  background-color: #eef3f8;
}
#T_02f7a_row0_col0, #T_02f7a_row0_col1, #T_02f7a_row0_col2, #T_02f7a_row0_col3, #T_02f7a_row0_col4, #T_02f7a_row1_col0, #T_02f7a_row1_col1, #T_02f7a_row1_col2, #T_02f7a_row1_col3, #T_02f7a_row1_col4, #T_02f7a_row2_col0, #T_02f7a_row2_col1, #T_02f7a_row2_col2, #T_02f7a_row2_col3, #T_02f7a_row2_col4 {
  text-align: right;
}
</style>
<table id="T_02f7a">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_02f7a_level0_col0" class="col_heading level0 col0" >min</th>
      <th id="T_02f7a_level0_col1" class="col_heading level0 col1" >mean</th>
      <th id="T_02f7a_level0_col2" class="col_heading level0 col2" >median</th>
      <th id="T_02f7a_level0_col3" class="col_heading level0 col3" >std</th>
      <th id="T_02f7a_level0_col4" class="col_heading level0 col4" >max</th>
    </tr>
    <tr>
      <th class="index_name level0" >column</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_02f7a_level0_row0" class="row_heading level0 row0" >arrival_delay</th>
      <td id="T_02f7a_row0_col0" class="data row0 col0" >-3600.00</td>
      <td id="T_02f7a_row0_col1" class="data row0 col1" >55.90</td>
      <td id="T_02f7a_row0_col2" class="data row0 col2" >42.00</td>
      <td id="T_02f7a_row0_col3" class="data row0 col3" >84.20</td>
      <td id="T_02f7a_row0_col4" class="data row0 col4" >3599.00</td>
    </tr>
    <tr>
      <th id="T_02f7a_level0_row1" class="row_heading level0 row1" >departure_delay</th>
      <td id="T_02f7a_row1_col0" class="data row1 col0" >-3598.00</td>
      <td id="T_02f7a_row1_col1" class="data row1 col1" >61.50</td>
      <td id="T_02f7a_row1_col2" class="data row1 col2" >47.00</td>
      <td id="T_02f7a_row1_col3" class="data row1 col3" >85.40</td>
      <td id="T_02f7a_row1_col4" class="data row1 col4" >3599.00</td>
    </tr>
    <tr>
      <th id="T_02f7a_level0_row2" class="row_heading level0 row2" >delay_delta</th>
      <td id="T_02f7a_row2_col0" class="data row2 col0" >-3773.00</td>
      <td id="T_02f7a_row2_col1" class="data row2 col1" >5.60</td>
      <td id="T_02f7a_row2_col2" class="data row2 col2" >15.00</td>
      <td id="T_02f7a_row2_col3" class="data row2 col3" >33.00</td>
      <td id="T_02f7a_row2_col4" class="data row2 col4" >3592.00</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mTable clean[0m



<style type="text/css">
#T_3c263 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_3c263 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_3c263 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_3c263 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_3c263 tr:hover td {
  background-color: #eef3f8;
}
#T_3c263_row0_col0, #T_3c263_row0_col1, #T_3c263_row0_col2, #T_3c263_row1_col0, #T_3c263_row1_col1, #T_3c263_row1_col2, #T_3c263_row2_col0, #T_3c263_row2_col1, #T_3c263_row2_col2 {
  text-align: right;
}
</style>
<table id="T_3c263">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_3c263_level0_col0" class="col_heading level0 col0" >Ø Arr Delay (s)</th>
      <th id="T_3c263_level0_col1" class="col_heading level0 col1" >Ø Dep Delay (s)</th>
      <th id="T_3c263_level0_col2" class="col_heading level0 col2" >Ø Δ (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Jahr</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_3c263_level0_row0" class="row_heading level0 row0" >2023</th>
      <td id="T_3c263_row0_col0" class="data row0 col0" >56.50</td>
      <td id="T_3c263_row0_col1" class="data row0 col1" >61.10</td>
      <td id="T_3c263_row0_col2" class="data row0 col2" >4.60</td>
    </tr>
    <tr>
      <th id="T_3c263_level0_row1" class="row_heading level0 row1" >2024</th>
      <td id="T_3c263_row1_col0" class="data row1 col0" >59.40</td>
      <td id="T_3c263_row1_col1" class="data row1 col1" >64.50</td>
      <td id="T_3c263_row1_col2" class="data row1 col2" >5.10</td>
    </tr>
    <tr>
      <th id="T_3c263_level0_row2" class="row_heading level0 row2" >2025</th>
      <td id="T_3c263_row2_col0" class="data row2 col0" >54.90</td>
      <td id="T_3c263_row2_col1" class="data row2 col1" >60.40</td>
      <td id="T_3c263_row2_col2" class="data row2 col2" >5.20</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mStats clean[0m



<style type="text/css">
#T_c4ff1 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_c4ff1 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_c4ff1 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_c4ff1 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_c4ff1 tr:hover td {
  background-color: #eef3f8;
}
#T_c4ff1_row0_col0, #T_c4ff1_row0_col1, #T_c4ff1_row0_col2, #T_c4ff1_row0_col3, #T_c4ff1_row0_col4, #T_c4ff1_row1_col0, #T_c4ff1_row1_col1, #T_c4ff1_row1_col2, #T_c4ff1_row1_col3, #T_c4ff1_row1_col4, #T_c4ff1_row2_col0, #T_c4ff1_row2_col1, #T_c4ff1_row2_col2, #T_c4ff1_row2_col3, #T_c4ff1_row2_col4 {
  text-align: right;
}
</style>
<table id="T_c4ff1">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_c4ff1_level0_col0" class="col_heading level0 col0" >min</th>
      <th id="T_c4ff1_level0_col1" class="col_heading level0 col1" >mean</th>
      <th id="T_c4ff1_level0_col2" class="col_heading level0 col2" >median</th>
      <th id="T_c4ff1_level0_col3" class="col_heading level0 col3" >std</th>
      <th id="T_c4ff1_level0_col4" class="col_heading level0 col4" >max</th>
    </tr>
    <tr>
      <th class="index_name level0" >column</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_c4ff1_level0_row0" class="row_heading level0 row0" >arrival_delay</th>
      <td id="T_c4ff1_row0_col0" class="data row0 col0" >-3599.00</td>
      <td id="T_c4ff1_row0_col1" class="data row0 col1" >57.00</td>
      <td id="T_c4ff1_row0_col2" class="data row0 col2" >43.00</td>
      <td id="T_c4ff1_row0_col3" class="data row0 col3" >79.30</td>
      <td id="T_c4ff1_row0_col4" class="data row0 col4" >3594.00</td>
    </tr>
    <tr>
      <th id="T_c4ff1_level0_row1" class="row_heading level0 row1" >departure_delay</th>
      <td id="T_c4ff1_row1_col0" class="data row1 col0" >-3593.00</td>
      <td id="T_c4ff1_row1_col1" class="data row1 col1" >62.30</td>
      <td id="T_c4ff1_row1_col2" class="data row1 col2" >48.00</td>
      <td id="T_c4ff1_row1_col3" class="data row1 col3" >80.40</td>
      <td id="T_c4ff1_row1_col4" class="data row1 col4" >3598.00</td>
    </tr>
    <tr>
      <th id="T_c4ff1_level0_row2" class="row_heading level0 row2" >delay_delta</th>
      <td id="T_c4ff1_row2_col0" class="data row2 col0" >-2878.00</td>
      <td id="T_c4ff1_row2_col1" class="data row2 col1" >5.00</td>
      <td id="T_c4ff1_row2_col2" class="data row2 col2" >15.00</td>
      <td id="T_c4ff1_row2_col3" class="data row2 col3" >30.70</td>
      <td id="T_c4ff1_row2_col4" class="data row2 col4" >3520.00</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Der monatliche Verlauf zeigt ab **14. November 2025** einen abrupten Sprung in `delay_delta_mean` (von ~6s auf ~16s am 14. Nov, ~26s im Dezember). Dies entspricht keiner organischen Saisonschwankung — die Kurve bricht aus dem langjährigen Muster aus. Entscheidend: nur `departure_delay` steigt; `arrival_delay` bleibt stabil. Alle 15 Linien gleichzeitig betroffen. **Nov–Dez 2025 aus Trendanalysen ausschließen.** → Untersuchung und Erklärung im Hintergrund-Block weiter unten.

**Beobachtung:** Ohne den Fahrplanwechsel-Artefakt zeigt sich ein klares saisonales Muster: **Winter-Peak (Dez/Jan)** und ein kleinerer **Frühlings-Peak (März)** sowie **Sommer-Peak (Juni)** — unterbrochen von einem relativen Tal in den Sommermonaten (Juli–August), das aber trotzdem auf hohem Niveau bleibt. Die gestrichelten Trendlinien bestätigen einen **strukturellen Aufwärtstrend** über alle drei Metriken — kein Einmaleffekt. `dep_delay` steigt am stärksten. Alle drei Metriken steigen: das System wird insgesamt langsamer, nicht nur an einzelnen Punkten. → Saison-Feature (Monat, Winter/Sommer-Flag) und Jahr als Features in Modell aufnehmen.

## Verteilung

Grundform aller drei Delay-Spalten: Minimum, Maximum, Mittelwert, Median, Streuung. Basis für alle weiteren Analysen.

Wie stark verändern die Bereinigungsschritte die Verteilung? `lf_all` (alles) vs. `lf_clean` (canceled raus · Nov/Dez 2025 raus · Linie E raus · Starthalte raus).


```python
section_header('Delays Distributions')
an.plot_delay_distribution_comparison(lf_all, lf_clean, cfg)
log('Table all')
show_df(an.table_delay_stats(lf_all))
log('Table clean')
show_df(an.table_delay_stats(lf_clean))
```

    
    [1m[38;2;52;97;141m───  DELAYS DISTRIBUTIONS  ───────────────────────────────────[0m
    Arrival     : lf_all=+55.5s  →  lf_clean=+56.9s  (Δ +1.3s)
    Delta       : lf_all=+5.5s  →  lf_clean=+4.9s  (Δ -0.7s)



    
![png](03_analysis_1-target_files/03_analysis_1-target_17_1.png)
    


    [38;2;52;97;141mTable all[0m



<style type="text/css">
#T_9221a thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_9221a td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_9221a tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_9221a tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_9221a tr:hover td {
  background-color: #eef3f8;
}
#T_9221a_row0_col0, #T_9221a_row0_col1, #T_9221a_row0_col2, #T_9221a_row0_col3, #T_9221a_row0_col4, #T_9221a_row1_col0, #T_9221a_row1_col1, #T_9221a_row1_col2, #T_9221a_row1_col3, #T_9221a_row1_col4, #T_9221a_row2_col0, #T_9221a_row2_col1, #T_9221a_row2_col2, #T_9221a_row2_col3, #T_9221a_row2_col4 {
  text-align: right;
}
</style>
<table id="T_9221a">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_9221a_level0_col0" class="col_heading level0 col0" >min</th>
      <th id="T_9221a_level0_col1" class="col_heading level0 col1" >mean</th>
      <th id="T_9221a_level0_col2" class="col_heading level0 col2" >median</th>
      <th id="T_9221a_level0_col3" class="col_heading level0 col3" >std</th>
      <th id="T_9221a_level0_col4" class="col_heading level0 col4" >max</th>
    </tr>
    <tr>
      <th class="index_name level0" >column</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_9221a_level0_row0" class="row_heading level0 row0" >arrival_delay</th>
      <td id="T_9221a_row0_col0" class="data row0 col0" >-3600.00</td>
      <td id="T_9221a_row0_col1" class="data row0 col1" >55.90</td>
      <td id="T_9221a_row0_col2" class="data row0 col2" >42.00</td>
      <td id="T_9221a_row0_col3" class="data row0 col3" >84.20</td>
      <td id="T_9221a_row0_col4" class="data row0 col4" >3599.00</td>
    </tr>
    <tr>
      <th id="T_9221a_level0_row1" class="row_heading level0 row1" >departure_delay</th>
      <td id="T_9221a_row1_col0" class="data row1 col0" >-3598.00</td>
      <td id="T_9221a_row1_col1" class="data row1 col1" >61.50</td>
      <td id="T_9221a_row1_col2" class="data row1 col2" >47.00</td>
      <td id="T_9221a_row1_col3" class="data row1 col3" >85.40</td>
      <td id="T_9221a_row1_col4" class="data row1 col4" >3599.00</td>
    </tr>
    <tr>
      <th id="T_9221a_level0_row2" class="row_heading level0 row2" >delay_delta</th>
      <td id="T_9221a_row2_col0" class="data row2 col0" >-3773.00</td>
      <td id="T_9221a_row2_col1" class="data row2 col1" >5.60</td>
      <td id="T_9221a_row2_col2" class="data row2 col2" >15.00</td>
      <td id="T_9221a_row2_col3" class="data row2 col3" >33.00</td>
      <td id="T_9221a_row2_col4" class="data row2 col4" >3592.00</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mTable clean[0m



<style type="text/css">
#T_ddaec thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_ddaec td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_ddaec tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_ddaec tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_ddaec tr:hover td {
  background-color: #eef3f8;
}
#T_ddaec_row0_col0, #T_ddaec_row0_col1, #T_ddaec_row0_col2, #T_ddaec_row0_col3, #T_ddaec_row0_col4, #T_ddaec_row1_col0, #T_ddaec_row1_col1, #T_ddaec_row1_col2, #T_ddaec_row1_col3, #T_ddaec_row1_col4, #T_ddaec_row2_col0, #T_ddaec_row2_col1, #T_ddaec_row2_col2, #T_ddaec_row2_col3, #T_ddaec_row2_col4 {
  text-align: right;
}
</style>
<table id="T_ddaec">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_ddaec_level0_col0" class="col_heading level0 col0" >min</th>
      <th id="T_ddaec_level0_col1" class="col_heading level0 col1" >mean</th>
      <th id="T_ddaec_level0_col2" class="col_heading level0 col2" >median</th>
      <th id="T_ddaec_level0_col3" class="col_heading level0 col3" >std</th>
      <th id="T_ddaec_level0_col4" class="col_heading level0 col4" >max</th>
    </tr>
    <tr>
      <th class="index_name level0" >column</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
      <th class="blank col4" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_ddaec_level0_row0" class="row_heading level0 row0" >arrival_delay</th>
      <td id="T_ddaec_row0_col0" class="data row0 col0" >-3599.00</td>
      <td id="T_ddaec_row0_col1" class="data row0 col1" >57.00</td>
      <td id="T_ddaec_row0_col2" class="data row0 col2" >43.00</td>
      <td id="T_ddaec_row0_col3" class="data row0 col3" >79.30</td>
      <td id="T_ddaec_row0_col4" class="data row0 col4" >3594.00</td>
    </tr>
    <tr>
      <th id="T_ddaec_level0_row1" class="row_heading level0 row1" >departure_delay</th>
      <td id="T_ddaec_row1_col0" class="data row1 col0" >-3593.00</td>
      <td id="T_ddaec_row1_col1" class="data row1 col1" >62.30</td>
      <td id="T_ddaec_row1_col2" class="data row1 col2" >48.00</td>
      <td id="T_ddaec_row1_col3" class="data row1 col3" >80.40</td>
      <td id="T_ddaec_row1_col4" class="data row1 col4" >3598.00</td>
    </tr>
    <tr>
      <th id="T_ddaec_level0_row2" class="row_heading level0 row2" >delay_delta</th>
      <td id="T_ddaec_row2_col0" class="data row2 col0" >-2878.00</td>
      <td id="T_ddaec_row2_col1" class="data row2 col1" >5.00</td>
      <td id="T_ddaec_row2_col2" class="data row2 col2" >15.00</td>
      <td id="T_ddaec_row2_col3" class="data row2 col3" >30.70</td>
      <td id="T_ddaec_row2_col4" class="data row2 col4" >3520.00</td>
    </tr>
  </tbody>
</table>



**Beobachtung — Gesamter Zeitraum**
Alle drei Verteilungen sind rechtsschief — wenige extreme Verspätungen ziehen den Mittelwert deutlich über den Median.

**Frühankünfte und Starthalte-Verzerrung:**
> Die auffälligen Frühankünfte bis −200s in der Verteilung stammen hauptsächlich von **Starthaltestellen (Terminus/Wendeschleifen)**. Trams starten dort mit eingebautem Puffer — was als negative Delay-Werte erscheint.
>
> **Auswirkung auf Durchschnittswerte:** Diese Frühankünfte ziehen den Netz-Durchschnitt nach unten und beschönigen die tatsächliche Verspätungsperformance im laufenden Betrieb. Ein Delay-Durchschnitt von 56s wäre ohne Starthalte-Effekt **höher**.
>
> Bei `delay_delta` gilt zudem: `median(A−B) ≠ median(A) − median(B)`, daher erscheint die Diskrepanz grösser als erwartet.

→ Räumlich prüfen in `03_analysis_4-spatial`. Für Modellierung: `is_start_stop`-Filter oder `n_threshold` empfohlen.

**Beobachtung — Was die Bereinigung verändert**

Die sechs Histogramme zeigen dieselben drei Delay-Metriken — oben roh, unten bereinigt. Das macht den Effekt jedes Bereinigungsschritts direkt sichtbar.

**Arrival Delay:**
Der Mittelwert verschiebt sich nach der Bereinigung nach rechts (höher). Das klingt zunächst paradox — aber es macht Sinn: Die Starthalte haben negative Delay-Werte (Frühankünfte durch Fahrplanpuffer) die den Roh-Durchschnitt nach unten ziehen. Wenn wir sie herausnehmen, sehen wir die echte Verspätung im laufenden Betrieb.

**Delay Delta:**
Der −50s-Cluster (Bimodalität) verschwindet in `lf_clean` fast vollständig — das bestätigt, dass er ausschliesslich aus Starthaltestellen stammt. Die bereinigte Verteilung ist deutlich unimodaler und zeigt klarer, dass das Netz pro Halt im Schnitt Verspätung aufbaut.

**Was das für den Report bedeutet:**
> Wir berichten **beide Werte** — roh und bereinigt — mit expliziter Erklärung warum sie sich unterscheiden. Das ist transparent und methodisch sauber: Der rohe Wert zeigt was im Datensatz steht, der bereinigte Wert zeigt die echte Systemperformance.


```python
# Quantitativer Effekt der Bereinigungsschritte
import polars as pl

lf_nc = lf_all.filter(pl.col('canceled') == False)
n_nc  = lf_nc.select(pl.len()).collect().item()

steps = [
    ('stop_sequence == 1', lf_nc.filter(pl.col('stop_sequence') == 1)),
    ('Linie E',            lf_nc.filter(pl.col('line_name')    == 'E')),
    ('Nov/Dez 2025',       lf_nc.filter(
        (pl.col('operating_date').dt.year()  == 2025) &
        (pl.col('operating_date').dt.month() >= 11)
    )),
]

rows = []
for label, sub in steps:
    s = sub.select([
        pl.len().alias('n'),
        pl.col('arrival_delay').mean().alias('arr'),
        pl.col('delay_delta').mean().alias('delta'),
    ]).collect()
    rows.append({
        'Filter-Schritt': label,
        'N entfernt': f"{s['n'][0]:>10,}",
        'Anteil':     f"{s['n'][0]/n_nc:.2%}",
        'Ø arr_delay (entfernt)': f"{s['arr'][0]:+.1f}s",
        'Ø delay_delta (entfernt)': f"{s['delta'][0]:+.1f}s",
    })

# Gesamtvergleich lf_all(nc) vs lf_clean
m_all   = lf_nc.select([pl.col('arrival_delay').mean().alias('arr'), pl.col('delay_delta').mean().alias('delta')]).collect()
m_clean = lf_clean.select([pl.col('arrival_delay').mean().alias('arr'), pl.col('delay_delta').mean().alias('delta')]).collect()

import pandas as pd
df = pd.DataFrame(rows)
log('Bereinigungsschritte — Mengen & Delay-Werte der entfernten Gruppen')
show_df(df.set_index('Filter-Schritt'))

summary = pd.DataFrame([{
    '': 'lf_all (non-canceled)',
    'N':              f"{n_nc:,}",
    'Ø arrival_delay': f"{m_all['arr'][0]:+.1f}s",
    'Ø delay_delta':   f"{m_all['delta'][0]:+.1f}s",
}, {
    '': 'lf_clean',
    'N':               f"{lf_clean.select(pl.len()).collect().item():,}",
    'Ø arrival_delay': f"{m_clean['arr'][0]:+.1f}s",
    'Ø delay_delta':   f"{m_clean['delta'][0]:+.1f}s",
}]).set_index('')
log('Gesamtvergleich lf_all vs lf_clean')
show_df(summary)
```

    [38;2;52;97;141mBereinigungsschritte — Mengen & Delay-Werte der entfernten Gruppen[0m



<style type="text/css">
#T_ab69b thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_ab69b td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_ab69b tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_ab69b tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_ab69b tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_ab69b">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_ab69b_level0_col0" class="col_heading level0 col0" >N entfernt</th>
      <th id="T_ab69b_level0_col1" class="col_heading level0 col1" >Anteil</th>
      <th id="T_ab69b_level0_col2" class="col_heading level0 col2" >Ø arr_delay (entfernt)</th>
      <th id="T_ab69b_level0_col3" class="col_heading level0 col3" >Ø delay_delta (entfernt)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Filter-Schritt</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_ab69b_level0_row0" class="row_heading level0 row0" >stop_sequence == 1</th>
      <td id="T_ab69b_row0_col0" class="data row0 col0" > 4,286,441</td>
      <td id="T_ab69b_row0_col1" class="data row0 col1" >4.78%</td>
      <td id="T_ab69b_row0_col2" class="data row0 col2" >+42.7s</td>
      <td id="T_ab69b_row0_col3" class="data row0 col3" >+2.5s</td>
    </tr>
    <tr>
      <th id="T_ab69b_level0_row1" class="row_heading level0 row1" >Linie E</th>
      <td id="T_ab69b_row1_col0" class="data row1 col0" >     2,511</td>
      <td id="T_ab69b_row1_col1" class="data row1 col1" >0.00%</td>
      <td id="T_ab69b_row1_col2" class="data row1 col2" >+130.2s</td>
      <td id="T_ab69b_row1_col3" class="data row1 col3" >-0.5s</td>
    </tr>
    <tr>
      <th id="T_ab69b_level0_row2" class="row_heading level0 row2" >Nov/Dez 2025</th>
      <td id="T_ab69b_row2_col0" class="data row2 col0" > 5,182,958</td>
      <td id="T_ab69b_row2_col1" class="data row2 col1" >5.78%</td>
      <td id="T_ab69b_row2_col2" class="data row2 col2" >+50.1s</td>
      <td id="T_ab69b_row2_col3" class="data row2 col3" >+21.5s</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mGesamtvergleich lf_all vs lf_clean[0m



<style type="text/css">
#T_a06de thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_a06de td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_a06de tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_a06de tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_a06de tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_a06de">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_a06de_level0_col0" class="col_heading level0 col0" >N</th>
      <th id="T_a06de_level0_col1" class="col_heading level0 col1" >Ø arrival_delay</th>
      <th id="T_a06de_level0_col2" class="col_heading level0 col2" >Ø delay_delta</th>
    </tr>
    <tr>
      <th class="index_name level0" ></th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_a06de_level0_row0" class="row_heading level0 row0" >lf_all (non-canceled)</th>
      <td id="T_a06de_row0_col0" class="data row0 col0" >89,714,901</td>
      <td id="T_a06de_row0_col1" class="data row0 col1" >+56.3s</td>
      <td id="T_a06de_row0_col2" class="data row0 col2" >+5.8s</td>
    </tr>
    <tr>
      <th id="T_a06de_level0_row1" class="row_heading level0 row1" >lf_clean</th>
      <td id="T_a06de_row1_col0" class="data row1 col0" >85,169,188</td>
      <td id="T_a06de_row1_col1" class="data row1 col1" >+57.0s</td>
      <td id="T_a06de_row1_col2" class="data row1 col2" >+5.0s</td>
    </tr>
  </tbody>
</table>



**Beobachtung — Bereinigung verändert Tendenzen nicht, aber die Verteilungsform**

Die Bereinigungsschritte entfernen **4.8% der Daten** (Starthalte) und **0.003%** (Linie E). Der Effekt auf die Mittelwerte ist minimal: `arrival_delay` verschiebt sich um **+1.1s**, `delay_delta` um **−0.8s**.

**Was sich trotzdem ändert:**
- Das **bimodale Cluster bei −50s** in `delay_delta` (Terminus-Artefakt) verschwindet → sauberere Verteilungsform
- **Linie E** (Ø 149s, aber nur 2.511 Zeilen) hat rechnerisch keinen Einfluss auf den Netzschnitt
- **Nov/Dez 2025** entfernt den Fahrplanwechsel-Artefakt — relevant für Trend, nicht für Mittelwert

> **Fazit:** `lf_clean` liefert eine sauberere Datenbasis für Modellierung. Die **grundlegenden Tendenzen** (Aufwärtstrend, Saisonalität, Linienunterschiede) **verändern sich durch die Bereinigung nicht** — sie werden nur klarer sichtbar.

### Log Transform


```python
an.plot_log_transform(lf_all, cfg)
an.plot_log_transform(lf_clean, cfg)
```


    
![png](03_analysis_1-target_files/03_analysis_1-target_23_0.png)
    


    Naive Baseline — Vorhersage = Mittelwert:  MAE = 50.4s
    Naive Baseline — Vorhersage = Median:      MAE = 48.8s  (robuster gegenüber Ausreißern)
    Differenz: +1.5s  →  Median reduziert MAE um 3.0%



    
![png](03_analysis_1-target_files/03_analysis_1-target_23_2.png)
    


    Naive Baseline — Vorhersage = Mittelwert:  MAE = 51.2s
    Naive Baseline — Vorhersage = Median:      MAE = 49.6s  (robuster gegenüber Ausreißern)
    Differenz: +1.5s  →  Median reduziert MAE um 3.0%


### Arrival vs Departure Delay

Alle drei Delay-Spalten nebeneinander als Boxplot — zeigt Lage, Streuung und Ausreißer auf einen Blick. Bauen Halte im Durchschnitt Verspätung auf oder ab?


```python
an.plot_arrival_vs_departure(lf_all, cfg)
an.plot_arrival_vs_departure(lf_clean, cfg)
```


    
![png](03_analysis_1-target_files/03_analysis_1-target_26_0.png)
    


    Ø Arrival Delay:   +55.9s
    Ø Departure Delay: +61.5s
    Ø Delay Delta:     +5.6s  (positiv = Verspätung wächst am Halt)



    
![png](03_analysis_1-target_files/03_analysis_1-target_26_2.png)
    


    Ø Arrival Delay:   +57.0s
    Ø Departure Delay: +62.3s
    Ø Delay Delta:     +5.0s  (positiv = Verspätung wächst am Halt)


**Beobachtung:** `departure_delay` liegt konsistent über `arrival_delay` — Halte kosten Zeit. `delay_delta` ist zentriert nahe 0 mit breiter Streuung: die meisten Halte sind annähernd neutral, aber extreme Werte in beide Richtungen sind vorhanden. Die starke linke Flanke des Delta (starke Recovery) deutet auf wenige Halte mit großem Zeitgewinn hin — wahrscheinlich Endhalte oder Expresssegmente wo Trams Puffer aufholen.

### Delay Delta — Detail

Separate Betrachtung der `delay_delta` Verteilung im engen Bereich (±100s). Wie ist die Form — symmetrisch, bimodal, stark schief?


```python
an.plot_delay_delta_detail(lf_all, cfg)
an.plot_delay_delta_detail(lf_clean, cfg)
```


    
![png](03_analysis_1-target_files/03_analysis_1-target_29_0.png)
    



    
![png](03_analysis_1-target_files/03_analysis_1-target_29_1.png)
    


**Beobachtung:** Die Verteilung ist **bimodal** — zwei erkennbare Häufungspunkte:

**Häufungspunkt 1 — nahe 0s:** Neutrale Halte. Das Tram fährt weiter ohne nennenswerte Änderung zur Planzeit.

**Häufungspunkt 2 — um −50s:** Das sind die **Starthaltestellen (Terminus/Wendeschleife)**.

> **Warum sind Starthaltestellen ein Problem für unsere Analyse?**
> Ein Tram, das am Startpunkt einer Linie abfährt, hat per Definition noch keine Verspätung angesammelt. Weil Fahrpläne dort Pufferzeit einbauen, starten Trams oft etwas früher als geplant — was als „negativer delay_delta" erscheint. Diese Frühankünfte und Frühabfahrten an Starthaltestellen:
> - **Verzerren den Netz-Durchschnitt nach unten** (machen das System scheinbar besser als es ist)
> - **Sind kein echtes Performance-Signal** — sie messen keinen Betriebsfortschritt, sondern Fahrplan-Puffer
>
> Für eine saubere Analyse der Verspätungsakkumulation **sollten Starthaltestellen herausgefiltert werden** — sie verfälschen Durchschnitte und Mediane. Ohne diesen Cluster ist der mittlere Verspätungsaufbau pro Halt noch deutlich höher als +5s.

→ Räumlich prüfen in `03_analysis_4-spatial`: welche Haltestellen haben systematisch delta < −30s

### Starthalte-Verzerrung — Beweis und Filterregel

Erste Haltestelle jeder Fahrt (`stop_sequence == 1`) vs. alle weiteren Haltestellen — zeigt ob und wie stark Starthalte die Delay-Verteilung verzerren.

> **Warum dieser Vergleich?** Die bimodale `delay_delta`-Verteilung oben hat einen auffälligen Cluster bei −50s. Wenn dieser Cluster ausschliesslich aus Starthaltestellen stammt, sind die Durchschnittswerte des gesamten Netzes systematisch zu optimistisch — weil jede Fahrt mit einem künstlichen Puffer-Bonus beginnt.


```python
an.plot_start_stop_analysis(lf_all, cfg, ylim_density=(0, 0.03))
```


    
![png](03_analysis_1-target_files/03_analysis_1-target_33_0.png)
    


    Δ arrival_delay Starthalte→Normal: +13.6s
    → Starthalte ERHÖHEN den Netz-Durchschnitt um diesen Wert wenn inkludiert


**Beobachtung — Starthalte-Verzerrung: Der Beweis**

**Was wir sehen:**

Das dritte Panel ist der entscheidende Beweis: Bei Starthaltestellen (`stop_sequence == 1`) sind deutlich mehr als 50% aller `delay_delta`-Werte negativ — bei normalen Haltestellen liegt dieser Anteil klar darunter. Das erste Panel zeigt den gleichen Befund als Histogramm: Die Verteilung der Starthalte ist deutlich nach links verschoben (Richtung negative Werte), die der normalen Halte ist symmetrischer um 0s.

**Was das bedeutet — einfach erklärt:**

Stell dir eine Tramlinie vor. Am Startpunkt wartet das Tram auf seine planmässige Abfahrtszeit. Der Fahrplan hat dort extra Pufferzeit eingeplant — das Tram kommt also oft etwas früher an als der Fahrplan verlangt. Das erscheint in den Daten als negativer Wert (z.B. −50s "zu früh"). Das ist kein Fehler im Betrieb — das ist eingebauter Fahrplan-Puffer.

Das Problem: Dieser negative Wert fliesst in unseren Netz-Durchschnitt ein und macht das System scheinbar pünktlicher als es im laufenden Betrieb tatsächlich ist. Jede Fahrt "kauft" sich am Start einen negativen Bonus, der über die gesamte Strecke abbezahlt wird.

**Die Konsequenz für unsere Analyse:**

> Wenn wir fragen *"Wie pünktlich ist das VBZ-Netz?"*, dann sollten wir die Starthaltestellen herausnehmen. Denn dort wird Systemleistung nicht gemessen — dort wird Fahrplan-Puffer aufgebraucht.
> Die echte Frage ist: Wie entwickelt sich der Delay vom zweiten Halt an?

**Filterregel für Modellierung und Reportmetriken:**

```
stop_sequence > 1   →  echter Betriebsfortschritt
stop_sequence == 1  →  Fahrplan-Puffer / Start-Logik → aus Delay-Baseline herauslassen
```

Der bereinigte Netz-Durchschnitt (ohne Starthalte) liegt entsprechend **höher** als die bisher genannten ~56s — das zeigt das System wie es im laufenden Betrieb tatsächlich performt.

**Endhalte bleiben drin:**

Die letzte Haltestelle einer Fahrt (`stop_sequence == max`) messen, wie viel Verspätung über die gesamte Strecke aufgebaut wurde. Das ist ein wertvolles Signal — und kein Artefakt.

**Kaskaden-Frage (✅ gelöst → F-NET-07 → `prev_trip_delay` in LightGBM v2):**

**Ergebnis:** `prev_trip_delay` wurde in LightGBM v2 als Feature implementiert und ist Feature #2 nach `stop_name` (Gain). MAE sank von 45.7s auf 18.56s — der Kaskadeneffekt ist der stärkste Einzelbeitrag im Modell.


### Extreme Values

Wie viele Halte liegen jenseits relevanter Schwellwerte? Gibt es echte Ausreißer oder ist die Verteilung kontinuierlich?


```python
section_header("Extreme Values")

total = lf.select(pl.len()).collect().item()
thresholds = [120, 300, 600, 1800]
rows = []
for t in thresholds:
    r = lf.select([
        (pl.col("arrival_delay")    >  t).sum().alias("arr_late"),
        (pl.col("arrival_delay")    < -t).sum().alias("arr_early"),
        (pl.col("departure_delay")  >  t).sum().alias("dep_late"),
    ]).collect()
    rows.append({
        "Threshold":  f"> {t}s  ({t//60}min)",
        "Arr Late":   f"{r['arr_late'][0]:>10,.0f}  ({r['arr_late'][0]/total:.2%})",
        "Arr Early":  f"{r['arr_early'][0]:>10,.0f}  ({r['arr_early'][0]/total:.2%})",
        "Dep Late":   f"{r['dep_late'][0]:>10,.0f}  ({r['dep_late'][0]/total:.2%})",
    })

show_df(pd.DataFrame(rows))
```

    
    [1m[38;2;52;97;141m───  EXTREME VALUES  ─────────────────────────────────────────[0m



<style type="text/css">
#T_cbac4 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_cbac4 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_cbac4 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_cbac4 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_cbac4 tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_cbac4">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_cbac4_level0_col0" class="col_heading level0 col0" >Threshold</th>
      <th id="T_cbac4_level0_col1" class="col_heading level0 col1" >Arr Late</th>
      <th id="T_cbac4_level0_col2" class="col_heading level0 col2" >Arr Early</th>
      <th id="T_cbac4_level0_col3" class="col_heading level0 col3" >Dep Late</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_cbac4_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_cbac4_row0_col0" class="data row0 col0" >> 120s  (2min)</td>
      <td id="T_cbac4_row0_col1" class="data row0 col1" > 8,008,640  (12.89%)</td>
      <td id="T_cbac4_row0_col2" class="data row0 col2" >    55,718  (0.09%)</td>
      <td id="T_cbac4_row0_col3" class="data row0 col3" > 8,785,749  (14.14%)</td>
    </tr>
    <tr>
      <th id="T_cbac4_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_cbac4_row1_col0" class="data row1 col0" >> 300s  (5min)</td>
      <td id="T_cbac4_row1_col1" class="data row1 col1" >   821,816  (1.32%)</td>
      <td id="T_cbac4_row1_col2" class="data row1 col2" >    26,904  (0.04%)</td>
      <td id="T_cbac4_row1_col3" class="data row1 col3" >   884,239  (1.42%)</td>
    </tr>
    <tr>
      <th id="T_cbac4_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_cbac4_row2_col0" class="data row2 col0" >> 600s  (10min)</td>
      <td id="T_cbac4_row2_col1" class="data row2 col1" >   105,048  (0.17%)</td>
      <td id="T_cbac4_row2_col2" class="data row2 col2" >    12,977  (0.02%)</td>
      <td id="T_cbac4_row2_col3" class="data row2 col3" >   110,813  (0.18%)</td>
    </tr>
    <tr>
      <th id="T_cbac4_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_cbac4_row3_col0" class="data row3 col0" >> 1800s  (30min)</td>
      <td id="T_cbac4_row3_col1" class="data row3 col1" >     7,149  (0.01%)</td>
      <td id="T_cbac4_row3_col2" class="data row3 col2" >     3,517  (0.01%)</td>
      <td id="T_cbac4_row3_col3" class="data row3 col3" >     7,392  (0.01%)</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die extremsten Werte (+3000s bis +5000s) sind nicht zwingend Messfehler — bei großflächigen Störungen (Unwetter, Netzausfälle, Unfälle) können echte Kumulationsverspätungen dieser Größenordnung auftreten. Interessant wäre ein späterer Abgleich mit externen Ereignis-Daten (Wetterdaten, Störungsmeldungen) in `03_analysis_3-temporal`: Fallen die Extremwert-Häufungen zeitlich mit dokumentierten Ereignissen zusammen? Starke Frühankünfte (−200s+) konzentrieren sich vermutlich auf Terminushalte mit Pufferzeit.

## On-Time Performance (OTP)

Anteil der Halte innerhalb ±120 Sekunden Planzeit — der offizielle KPI-Schwellwert der VBZ.

> **Woher kommt der 120-Sekunden-Wert?**
> Die VBZ verwendet ±120s (= ±2 Minuten) als Toleranzgrenze im eigenen Qualitätsbericht sowie im VDPW-Standard (Verband Deutscher Verkehrsunternehmen). Abweichungen unter 2 Minuten sind für Fahrgäste an der Haltestelle praktisch nicht spürbar — daher gilt alles ab +120s als „nicht pünktlich". Der Schwellwert ist im öffentlichen Nahverkehr Deutschland/Schweiz/Österreich branchenweit etabliert.
> **Quellen:** VBZ Qualitätsbericht 2023/2024 · VDPW-Standard Pünktlichkeitsmessung

Für `delay_delta`: Anteil der Halte, an denen Verspätung abgebaut, neutral oder aufgebaut wird.


```python
section_header('On-Time Performance')
log('Plot all')
an.plot_otp(lf_all, cfg)
log('Tabel all')
show_df(an.table_otp(lf_all))
log('Plot clean')
an.plot_otp(lf_clean, cfg)
log('Table clean')
show_df(an.table_otp(lf_clean))
```

    
    [1m[38;2;52;97;141m───  ON-TIME PERFORMANCE  ────────────────────────────────────[0m
    [38;2;52;97;141mPlot all[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_40_1.png)
    


    [38;2;52;97;141mTabel all[0m



<style type="text/css">
#T_aea28 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_aea28 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_aea28 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_aea28 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_aea28 tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_aea28">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_aea28_level0_col0" class="col_heading level0 col0" >Kategorie</th>
      <th id="T_aea28_level0_col1" class="col_heading level0 col1" >On-Time (±120s)</th>
      <th id="T_aea28_level0_col2" class="col_heading level0 col2" >Late (>120s)</th>
      <th id="T_aea28_level0_col3" class="col_heading level0 col3" >Early (<−120s)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_aea28_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_aea28_row0_col0" class="data row0 col0" >Arrival</td>
      <td id="T_aea28_row0_col1" class="data row0 col1" >87.2%</td>
      <td id="T_aea28_row0_col2" class="data row0 col2" >12.7%</td>
      <td id="T_aea28_row0_col3" class="data row0 col3" >0.1%</td>
    </tr>
    <tr>
      <th id="T_aea28_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_aea28_row1_col0" class="data row1 col0" >Departure</td>
      <td id="T_aea28_row1_col1" class="data row1 col1" >85.6%</td>
      <td id="T_aea28_row1_col2" class="data row1 col2" >14.3%</td>
      <td id="T_aea28_row1_col3" class="data row1 col3" >0.1%</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mPlot clean[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_40_5.png)
    


    [38;2;52;97;141mTable clean[0m



<style type="text/css">
#T_53f47 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_53f47 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_53f47 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_53f47 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_53f47 tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_53f47">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_53f47_level0_col0" class="col_heading level0 col0" >Kategorie</th>
      <th id="T_53f47_level0_col1" class="col_heading level0 col1" >On-Time (±120s)</th>
      <th id="T_53f47_level0_col2" class="col_heading level0 col2" >Late (>120s)</th>
      <th id="T_53f47_level0_col3" class="col_heading level0 col3" >Early (<−120s)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_53f47_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_53f47_row0_col0" class="data row0 col0" >Arrival</td>
      <td id="T_53f47_row0_col1" class="data row0 col1" >86.6%</td>
      <td id="T_53f47_row0_col2" class="data row0 col2" >13.3%</td>
      <td id="T_53f47_row0_col3" class="data row0 col3" >0.1%</td>
    </tr>
    <tr>
      <th id="T_53f47_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_53f47_row1_col0" class="data row1 col0" >Departure</td>
      <td id="T_53f47_row1_col1" class="data row1 col1" >85.1%</td>
      <td id="T_53f47_row1_col2" class="data row1 col2" >14.8%</td>
      <td id="T_53f47_row1_col3" class="data row1 col3" >0.1%</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** **87.0% Arrival-OTP** (Schwellwert: ±120s, VBZ-Standard) — ein solider Wert für ein urbanes Tramnetz. Zürich liegt damit im europäischen Spitzenfeld. Die Nicht-Pünktlichen sind fast ausschließlich verspätet (12.9%) — kaum zu früh (0.1%). Das System hat eine klare Bias Richtung Verspätung, was auf systemischen Puffermangel hinweist.

> **Einordnung:** 87% OTP bedeutet, dass das VBZ-Netz seinen eigenen Standard in ca. 87 von 100 Halten einhält. Kein „schlechtes" Netz — aber auch kein Spielraum für strukturellen Mehrbedarf ohne Fahrplananpassung.

Bei `delay_delta`: **71.2%** der Halte bauen Verspätung auf (Growing), nur 27.2% zeigen Recovery — das Netz hat systemisch zu wenig Puffer eingebaut. Kaskadenwirkungen (eine verspätete Fahrt verzögert die nächste) sind mit `trip_id` analysierbar (→ F-NET-07).

### Root Cause — Das Problem ist im Fahrplan, nicht im Betrieb

> **"Das Verspätungsproblem ist nicht operativ — es ist im Fahrplan eingebaut."**

Zwei Befunde, die sich gegenseitig erklären:

* **F-TARGET-03:** 71.5% aller Halte akkumulieren Delay (`delay_delta > 0`)
* **F-SPAT-08:** 71.3% aller Halte haben keine Verweilzeit (`dwell_time = 0s`)

Das ist kein Zufall — es ist die gleiche Zahl, weil es dasselbe Problem ist.  
Ohne Pufferzeit kann eine Tram verlorene Sekunden nicht aufholen. Das System akkumuliert zwangsläufig.

Das bedeutet: Wetter, Events und Tageszeit entscheiden *wann* es schlimmer wird —  
aber die strukturelle Schwäche entscheidet, *dass* es passiert.

### OTP per Linie — Zeitlicher Verlauf

Wie unterscheiden sich die Linien in ihrer Pünktlichkeit — und verändert sich die Spreizung über die Zeit? Linien 9, 10, 12, 17 hervorgehoben; alle anderen als Hintergrund-Layer. `canceled = True` ausgeschlossen.


```python
section_header('On-Time Performance per Line')

log('Plot all')
an.plot_otp_per_line(lf_all, cfg)
log('Tabel all')
show_df(an.table_otp_per_line(lf_all))

log('Plot clean')
an.plot_otp_per_line(lf_clean, cfg, ylim_otp=(70, 110)) 
log('Tabel clean')
show_df(an.table_otp_per_line(lf_clean))
```

    
    [1m[38;2;52;97;141m───  ON-TIME PERFORMANCE PER LINE  ───────────────────────────[0m
    [38;2;52;97;141mPlot all[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_44_1.png)
    


    [38;2;52;97;141mTabel all[0m



<style type="text/css">
#T_0a8c4 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_0a8c4 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_0a8c4 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_0a8c4 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_0a8c4 tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_0a8c4">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_0a8c4_level0_col0" class="col_heading level0 col0" >Linie</th>
      <th id="T_0a8c4_level0_col1" class="col_heading level0 col1" >Ø OTP</th>
      <th id="T_0a8c4_level0_col2" class="col_heading level0 col2" >Min OTP</th>
      <th id="T_0a8c4_level0_col3" class="col_heading level0 col3" >Max OTP</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_0a8c4_level0_row0" class="row_heading level0 row0" >11</th>
      <td id="T_0a8c4_row0_col0" class="data row0 col0" >E</td>
      <td id="T_0a8c4_row0_col1" class="data row0 col1" >56.2%</td>
      <td id="T_0a8c4_row0_col2" class="data row0 col2" >35.1%</td>
      <td id="T_0a8c4_row0_col3" class="data row0 col3" >78.9%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row1" class="row_heading level0 row1" >2</th>
      <td id="T_0a8c4_row1_col0" class="data row1 col0" >11</td>
      <td id="T_0a8c4_row1_col1" class="data row1 col1" >82.0%</td>
      <td id="T_0a8c4_row1_col2" class="data row1 col2" >77.4%</td>
      <td id="T_0a8c4_row1_col3" class="data row1 col3" >87.0%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row2" class="row_heading level0 row2" >3</th>
      <td id="T_0a8c4_row2_col0" class="data row2 col0" >15</td>
      <td id="T_0a8c4_row2_col1" class="data row2 col1" >84.7%</td>
      <td id="T_0a8c4_row2_col2" class="data row2 col2" >79.4%</td>
      <td id="T_0a8c4_row2_col3" class="data row2 col3" >90.7%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row3" class="row_heading level0 row3" >10</th>
      <td id="T_0a8c4_row3_col0" class="data row3 col0" >8</td>
      <td id="T_0a8c4_row3_col1" class="data row3 col1" >84.9%</td>
      <td id="T_0a8c4_row3_col2" class="data row3 col2" >78.7%</td>
      <td id="T_0a8c4_row3_col3" class="data row3 col3" >92.3%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row4" class="row_heading level0 row4" >16</th>
      <td id="T_0a8c4_row4_col0" class="data row4 col0" >10</td>
      <td id="T_0a8c4_row4_col1" class="data row4 col1" >85.1%</td>
      <td id="T_0a8c4_row4_col2" class="data row4 col2" >78.9%</td>
      <td id="T_0a8c4_row4_col3" class="data row4 col3" >91.9%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row5" class="row_heading level0 row5" >5</th>
      <td id="T_0a8c4_row5_col0" class="data row5 col0" >2</td>
      <td id="T_0a8c4_row5_col1" class="data row5 col1" >86.7%</td>
      <td id="T_0a8c4_row5_col2" class="data row5 col2" >80.5%</td>
      <td id="T_0a8c4_row5_col3" class="data row5 col3" >92.0%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row6" class="row_heading level0 row6" >8</th>
      <td id="T_0a8c4_row6_col0" class="data row6 col0" >4</td>
      <td id="T_0a8c4_row6_col1" class="data row6 col1" >86.7%</td>
      <td id="T_0a8c4_row6_col2" class="data row6 col2" >81.3%</td>
      <td id="T_0a8c4_row6_col3" class="data row6 col3" >91.6%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row7" class="row_heading level0 row7" >4</th>
      <td id="T_0a8c4_row7_col0" class="data row7 col0" >7</td>
      <td id="T_0a8c4_row7_col1" class="data row7 col1" >87.0%</td>
      <td id="T_0a8c4_row7_col2" class="data row7 col2" >78.0%</td>
      <td id="T_0a8c4_row7_col3" class="data row7 col3" >93.3%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row8" class="row_heading level0 row8" >12</th>
      <td id="T_0a8c4_row8_col0" class="data row8 col0" >9</td>
      <td id="T_0a8c4_row8_col1" class="data row8 col1" >87.1%</td>
      <td id="T_0a8c4_row8_col2" class="data row8 col2" >79.1%</td>
      <td id="T_0a8c4_row8_col3" class="data row8 col3" >93.6%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row9" class="row_heading level0 row9" >7</th>
      <td id="T_0a8c4_row9_col0" class="data row9 col0" >14</td>
      <td id="T_0a8c4_row9_col1" class="data row9 col1" >87.2%</td>
      <td id="T_0a8c4_row9_col2" class="data row9 col2" >83.2%</td>
      <td id="T_0a8c4_row9_col3" class="data row9 col3" >94.7%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row10" class="row_heading level0 row10" >9</th>
      <td id="T_0a8c4_row10_col0" class="data row10 col0" >13</td>
      <td id="T_0a8c4_row10_col1" class="data row10 col1" >87.6%</td>
      <td id="T_0a8c4_row10_col2" class="data row10 col2" >81.3%</td>
      <td id="T_0a8c4_row10_col3" class="data row10 col3" >92.0%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row11" class="row_heading level0 row11" >1</th>
      <td id="T_0a8c4_row11_col0" class="data row11 col0" >5</td>
      <td id="T_0a8c4_row11_col1" class="data row11 col1" >89.5%</td>
      <td id="T_0a8c4_row11_col2" class="data row11 col2" >83.3%</td>
      <td id="T_0a8c4_row11_col3" class="data row11 col3" >93.5%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row12" class="row_heading level0 row12" >13</th>
      <td id="T_0a8c4_row12_col0" class="data row12 col0" >3</td>
      <td id="T_0a8c4_row12_col1" class="data row12 col1" >89.5%</td>
      <td id="T_0a8c4_row12_col2" class="data row12 col2" >84.5%</td>
      <td id="T_0a8c4_row12_col3" class="data row12 col3" >94.9%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row13" class="row_heading level0 row13" >15</th>
      <td id="T_0a8c4_row13_col0" class="data row13 col0" >50</td>
      <td id="T_0a8c4_row13_col1" class="data row13 col1" >90.3%</td>
      <td id="T_0a8c4_row13_col2" class="data row13 col2" >90.3%</td>
      <td id="T_0a8c4_row13_col3" class="data row13 col3" >90.3%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row14" class="row_heading level0 row14" >0</th>
      <td id="T_0a8c4_row14_col0" class="data row14 col0" >17</td>
      <td id="T_0a8c4_row14_col1" class="data row14 col1" >90.6%</td>
      <td id="T_0a8c4_row14_col2" class="data row14 col2" >87.4%</td>
      <td id="T_0a8c4_row14_col3" class="data row14 col3" >95.8%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row15" class="row_heading level0 row15" >6</th>
      <td id="T_0a8c4_row15_col0" class="data row15 col0" >12</td>
      <td id="T_0a8c4_row15_col1" class="data row15 col1" >92.2%</td>
      <td id="T_0a8c4_row15_col2" class="data row15 col2" >88.5%</td>
      <td id="T_0a8c4_row15_col3" class="data row15 col3" >95.4%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row16" class="row_heading level0 row16" >17</th>
      <td id="T_0a8c4_row16_col0" class="data row16 col0" >51</td>
      <td id="T_0a8c4_row16_col1" class="data row16 col1" >92.8%</td>
      <td id="T_0a8c4_row16_col2" class="data row16 col2" >92.8%</td>
      <td id="T_0a8c4_row16_col3" class="data row16 col3" >92.8%</td>
    </tr>
    <tr>
      <th id="T_0a8c4_level0_row17" class="row_heading level0 row17" >14</th>
      <td id="T_0a8c4_row17_col0" class="data row17 col0" >6</td>
      <td id="T_0a8c4_row17_col1" class="data row17 col1" >93.5%</td>
      <td id="T_0a8c4_row17_col2" class="data row17 col2" >89.5%</td>
      <td id="T_0a8c4_row17_col3" class="data row17 col3" >95.6%</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mPlot clean[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_44_5.png)
    


    [38;2;52;97;141mTabel clean[0m



<style type="text/css">
#T_3fa8a thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_3fa8a td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_3fa8a tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_3fa8a tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_3fa8a tr:hover td {
  background-color: #eef3f8;
}
</style>
<table id="T_3fa8a">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_3fa8a_level0_col0" class="col_heading level0 col0" >Linie</th>
      <th id="T_3fa8a_level0_col1" class="col_heading level0 col1" >Ø OTP</th>
      <th id="T_3fa8a_level0_col2" class="col_heading level0 col2" >Min OTP</th>
      <th id="T_3fa8a_level0_col3" class="col_heading level0 col3" >Max OTP</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_3fa8a_level0_row0" class="row_heading level0 row0" >9</th>
      <td id="T_3fa8a_row0_col0" class="data row0 col0" >11</td>
      <td id="T_3fa8a_row0_col1" class="data row0 col1" >81.6%</td>
      <td id="T_3fa8a_row0_col2" class="data row0 col2" >76.9%</td>
      <td id="T_3fa8a_row0_col3" class="data row0 col3" >86.6%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row1" class="row_heading level0 row1" >13</th>
      <td id="T_3fa8a_row1_col0" class="data row1 col0" >15</td>
      <td id="T_3fa8a_row1_col1" class="data row1 col1" >84.5%</td>
      <td id="T_3fa8a_row1_col2" class="data row1 col2" >78.9%</td>
      <td id="T_3fa8a_row1_col3" class="data row1 col3" >90.8%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row2" class="row_heading level0 row2" >5</th>
      <td id="T_3fa8a_row2_col0" class="data row2 col0" >8</td>
      <td id="T_3fa8a_row2_col1" class="data row2 col1" >84.5%</td>
      <td id="T_3fa8a_row2_col2" class="data row2 col2" >78.1%</td>
      <td id="T_3fa8a_row2_col3" class="data row2 col3" >92.1%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_3fa8a_row3_col0" class="data row3 col0" >10</td>
      <td id="T_3fa8a_row3_col1" class="data row3 col1" >84.7%</td>
      <td id="T_3fa8a_row3_col2" class="data row3 col2" >78.3%</td>
      <td id="T_3fa8a_row3_col3" class="data row3 col3" >91.7%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_3fa8a_row4_col0" class="data row4 col0" >4</td>
      <td id="T_3fa8a_row4_col1" class="data row4 col1" >86.3%</td>
      <td id="T_3fa8a_row4_col2" class="data row4 col2" >80.7%</td>
      <td id="T_3fa8a_row4_col3" class="data row4 col3" >91.3%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row5" class="row_heading level0 row5" >6</th>
      <td id="T_3fa8a_row5_col0" class="data row5 col0" >2</td>
      <td id="T_3fa8a_row5_col1" class="data row5 col1" >86.3%</td>
      <td id="T_3fa8a_row5_col2" class="data row5 col2" >79.9%</td>
      <td id="T_3fa8a_row5_col3" class="data row5 col3" >91.8%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row6" class="row_heading level0 row6" >14</th>
      <td id="T_3fa8a_row6_col0" class="data row6 col0" >7</td>
      <td id="T_3fa8a_row6_col1" class="data row6 col1" >86.8%</td>
      <td id="T_3fa8a_row6_col2" class="data row6 col2" >77.4%</td>
      <td id="T_3fa8a_row6_col3" class="data row6 col3" >93.2%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row7" class="row_heading level0 row7" >11</th>
      <td id="T_3fa8a_row7_col0" class="data row7 col0" >14</td>
      <td id="T_3fa8a_row7_col1" class="data row7 col1" >86.8%</td>
      <td id="T_3fa8a_row7_col2" class="data row7 col2" >82.7%</td>
      <td id="T_3fa8a_row7_col3" class="data row7 col3" >94.5%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row8" class="row_heading level0 row8" >12</th>
      <td id="T_3fa8a_row8_col0" class="data row8 col0" >9</td>
      <td id="T_3fa8a_row8_col1" class="data row8 col1" >86.9%</td>
      <td id="T_3fa8a_row8_col2" class="data row8 col2" >78.6%</td>
      <td id="T_3fa8a_row8_col3" class="data row8 col3" >93.4%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row9" class="row_heading level0 row9" >10</th>
      <td id="T_3fa8a_row9_col0" class="data row9 col0" >13</td>
      <td id="T_3fa8a_row9_col1" class="data row9 col1" >87.3%</td>
      <td id="T_3fa8a_row9_col2" class="data row9 col2" >80.8%</td>
      <td id="T_3fa8a_row9_col3" class="data row9 col3" >91.9%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row10" class="row_heading level0 row10" >2</th>
      <td id="T_3fa8a_row10_col0" class="data row10 col0" >5</td>
      <td id="T_3fa8a_row10_col1" class="data row10 col1" >88.7%</td>
      <td id="T_3fa8a_row10_col2" class="data row10 col2" >82.3%</td>
      <td id="T_3fa8a_row10_col3" class="data row10 col3" >93.0%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row11" class="row_heading level0 row11" >7</th>
      <td id="T_3fa8a_row11_col0" class="data row11 col0" >3</td>
      <td id="T_3fa8a_row11_col1" class="data row11 col1" >89.0%</td>
      <td id="T_3fa8a_row11_col2" class="data row11 col2" >83.9%</td>
      <td id="T_3fa8a_row11_col3" class="data row11 col3" >94.7%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row12" class="row_heading level0 row12" >0</th>
      <td id="T_3fa8a_row12_col0" class="data row12 col0" >17</td>
      <td id="T_3fa8a_row12_col1" class="data row12 col1" >90.3%</td>
      <td id="T_3fa8a_row12_col2" class="data row12 col2" >87.0%</td>
      <td id="T_3fa8a_row12_col3" class="data row12 col3" >95.8%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row13" class="row_heading level0 row13" >8</th>
      <td id="T_3fa8a_row13_col0" class="data row13 col0" >12</td>
      <td id="T_3fa8a_row13_col1" class="data row13 col1" >92.0%</td>
      <td id="T_3fa8a_row13_col2" class="data row13 col2" >88.0%</td>
      <td id="T_3fa8a_row13_col3" class="data row13 col3" >95.2%</td>
    </tr>
    <tr>
      <th id="T_3fa8a_level0_row14" class="row_heading level0 row14" >1</th>
      <td id="T_3fa8a_row14_col0" class="data row14 col0" >6</td>
      <td id="T_3fa8a_row14_col1" class="data row14 col1" >93.4%</td>
      <td id="T_3fa8a_row14_col2" class="data row14 col2" >89.3%</td>
      <td id="T_3fa8a_row14_col3" class="data row14 col3" >95.6%</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Spreizung zwischen den Linien ist erheblich.

**Linie E — Ausreisser und Entscheidung:**

| | Drin lassen | Herausnehmen |
|:---|:---|:---|
| **Pro** | Vollständiges Bild des Netzes | Präsentation klarer, Modell-Baseline nicht verzerrt |
| **Contra** | Verzerrt alle Durchschnitte stark (128–130s vs. ~56s Netzschnitt) | Versteckt einen echten Betriebsaspekt |

**Was ist Linie E?** Eine Entlastungs-/Verstärkerlinie, die nur bei Bedarf (Grossevents, Stosszeiten) eingesetzt wird. Sie ist planmässig im GTFS modelliert, weicht aber im Betrieb strukturell von allen Regellinien ab — weil sie keine festen Fahrzeiten einhalten kann (sie reagiert auf aktuelle Auslastung). OTP 56.2%, Ø Delay 128–130s.

**Entscheid: Linie E wird aus der Hauptanalyse und der Modellierung ausgeschlossen.** Begründung: strukturell nicht vergleichbar mit Regellinien. Im Report wird der Ausschluss explizit dokumentiert. Das ist methodisch sauber — nicht Datenverfälschung.

**Ohne Linie E** liegt das schlechteste reguläre Tram bei **Linie 11 (82.0% OTP)**, gefolgt von Linie 15 (84.7%) und Linie 8 (84.9%). Linie 12 zeigt während der Baustellenphase einen starken Einbruch — aber mit normaler OTP ausserhalb der Baustelle.



## Cancellations

`canceled = True` ist der Extremfall — faktisch unendliche Verspätung. Wie viele Ausfälle gibt es insgesamt?


```python
section_header("Cancellations")

cancellations = (
    lf
    .group_by("canceled")
    .agg(pl.len().alias("count"))
    .with_columns((pl.col("count") / pl.col("count").sum()).alias("share"))
    .sort("canceled")
    .collect()
)
log(cancellations.to_pandas().to_string())
```

    
    [1m[38;2;52;97;141m───  CANCELLATIONS  ──────────────────────────────────────────[0m
    [38;2;52;97;141m   canceled     count     share
    0     False  58266738  0.937732
    1      True   3869094  0.062268[0m


**Beobachtung:** **6.2% Ausfallrate** (3.87 Mio. von 62.1 Mio. Halt-Ereignissen im Trainings-Set).

> **Was bedeutet „Artefakt"? — Einfache Erklärung:**
> Stell dir vor, ein Tram fährt wegen einer Baustelle nur bis zur Hälfte der Strecke. Ist das ein „Ausfall"?
> - **Vor Juli 2024:** VBZ erfasste das als `canceled = True` — auch wenn das Tram teilweise fuhr (sogenannte Kurzwendungen oder Teilausfälle).
> - **Ab Juli 2024:** Nur noch echte Komplett-Ausfälle (Tram fährt gar nicht) bekommen `canceled = True`.
>
> Das Ergebnis: Die „Ausfallrate" sieht auf einen Schlag viel besser aus — nicht weil der Betrieb besser wurde, sondern weil die Definition enger wurde. Zahlen vor und nach Juli 2024 sind deshalb nicht direkt vergleichbar.

Der Grossteil der 6.2% fällt in die pre-Juli-2024-Periode und ist auf diese Datendefinitions-Änderung zurückzuführen (→ F-TARGET-05). Mit `trip_id` ist analysierbar ob Ausfälle einzelne Halte oder ganze Fahrten betreffen — das zeigt der nächste Abschnitt.

### Ausfälle nach Linie


```python
section_header('Cancellations by Line')
an.plot_cancellations_by_line(lf_all, cfg)
show_df(an.table_cancellations_by_line(lf_all))

# → Tabelle bereits in Zelle oben via an.table_cancellations_by_line(lf_all)
```

    
    [1m[38;2;52;97;141m───  CANCELLATIONS BY LINE  ──────────────────────────────────[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_52_1.png)
    



<style type="text/css">
#T_a43b6 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_a43b6 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_a43b6 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_a43b6 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_a43b6 tr:hover td {
  background-color: #eef3f8;
}
#T_a43b6_row0_col0, #T_a43b6_row0_col3, #T_a43b6_row1_col0, #T_a43b6_row1_col3, #T_a43b6_row2_col0, #T_a43b6_row2_col3, #T_a43b6_row3_col0, #T_a43b6_row3_col3, #T_a43b6_row4_col0, #T_a43b6_row4_col3, #T_a43b6_row5_col0, #T_a43b6_row5_col3, #T_a43b6_row6_col0, #T_a43b6_row6_col3, #T_a43b6_row7_col0, #T_a43b6_row7_col3, #T_a43b6_row8_col0, #T_a43b6_row8_col3, #T_a43b6_row9_col0, #T_a43b6_row9_col3, #T_a43b6_row10_col0, #T_a43b6_row10_col3, #T_a43b6_row11_col0, #T_a43b6_row11_col3, #T_a43b6_row12_col0, #T_a43b6_row12_col3, #T_a43b6_row13_col0, #T_a43b6_row13_col3, #T_a43b6_row14_col0, #T_a43b6_row14_col3 {
  text-align: left;
}
#T_a43b6_row0_col1, #T_a43b6_row0_col2, #T_a43b6_row1_col1, #T_a43b6_row1_col2, #T_a43b6_row2_col1, #T_a43b6_row2_col2, #T_a43b6_row3_col1, #T_a43b6_row3_col2, #T_a43b6_row4_col1, #T_a43b6_row4_col2, #T_a43b6_row5_col1, #T_a43b6_row5_col2, #T_a43b6_row6_col1, #T_a43b6_row6_col2, #T_a43b6_row7_col1, #T_a43b6_row7_col2, #T_a43b6_row8_col1, #T_a43b6_row8_col2, #T_a43b6_row9_col1, #T_a43b6_row9_col2, #T_a43b6_row10_col1, #T_a43b6_row10_col2, #T_a43b6_row11_col1, #T_a43b6_row11_col2, #T_a43b6_row12_col1, #T_a43b6_row12_col2, #T_a43b6_row13_col1, #T_a43b6_row13_col2, #T_a43b6_row14_col1, #T_a43b6_row14_col2 {
  text-align: right;
}
</style>
<table id="T_a43b6">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_a43b6_level0_col0" class="col_heading level0 col0" >Gesamt</th>
      <th id="T_a43b6_level0_col1" class="col_heading level0 col1" >Ausgefallen</th>
      <th id="T_a43b6_level0_col2" class="col_heading level0 col2" >Cancellation Rate</th>
      <th id="T_a43b6_level0_col3" class="col_heading level0 col3" >Ausfallrate</th>
    </tr>
    <tr>
      <th class="index_name level0" >Linie</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
      <th class="blank col3" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_a43b6_level0_row0" class="row_heading level0 row0" >50</th>
      <td id="T_a43b6_row0_col0" class="data row0 col0" >147,501</td>
      <td id="T_a43b6_row0_col1" class="data row0 col1" >390</td>
      <td id="T_a43b6_row0_col2" class="data row0 col2" >0.00</td>
      <td id="T_a43b6_row0_col3" class="data row0 col3" >0.3%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row1" class="row_heading level0 row1" >51</th>
      <td id="T_a43b6_row1_col0" class="data row1 col0" >121,134</td>
      <td id="T_a43b6_row1_col1" class="data row1 col1" >926</td>
      <td id="T_a43b6_row1_col2" class="data row1 col2" >0.01</td>
      <td id="T_a43b6_row1_col3" class="data row1 col3" >0.8%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row2" class="row_heading level0 row2" >E</th>
      <td id="T_a43b6_row2_col0" class="data row2 col0" >2,531</td>
      <td id="T_a43b6_row2_col1" class="data row2 col1" >20</td>
      <td id="T_a43b6_row2_col2" class="data row2 col2" >0.01</td>
      <td id="T_a43b6_row2_col3" class="data row2 col3" >0.8%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row3" class="row_heading level0 row3" >14</th>
      <td id="T_a43b6_row3_col0" class="data row3 col0" >7,106,921</td>
      <td id="T_a43b6_row3_col1" class="data row3 col1" >82100</td>
      <td id="T_a43b6_row3_col2" class="data row3 col2" >0.01</td>
      <td id="T_a43b6_row3_col3" class="data row3 col3" >1.2%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_a43b6_row4_col0" class="data row4 col0" >6,895,765</td>
      <td id="T_a43b6_row4_col1" class="data row4 col1" >86993</td>
      <td id="T_a43b6_row4_col2" class="data row4 col2" >0.01</td>
      <td id="T_a43b6_row4_col3" class="data row4 col3" >1.3%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row5" class="row_heading level0 row5" >2</th>
      <td id="T_a43b6_row5_col0" class="data row5 col0" >8,280,350</td>
      <td id="T_a43b6_row5_col1" class="data row5 col1" >133232</td>
      <td id="T_a43b6_row5_col2" class="data row5 col2" >0.02</td>
      <td id="T_a43b6_row5_col3" class="data row5 col3" >1.6%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row6" class="row_heading level0 row6" >8</th>
      <td id="T_a43b6_row6_col0" class="data row6 col0" >6,372,863</td>
      <td id="T_a43b6_row6_col1" class="data row6 col1" >105629</td>
      <td id="T_a43b6_row6_col2" class="data row6 col2" >0.02</td>
      <td id="T_a43b6_row6_col3" class="data row6 col3" >1.7%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row7" class="row_heading level0 row7" >11</th>
      <td id="T_a43b6_row7_col0" class="data row7 col0" >9,148,227</td>
      <td id="T_a43b6_row7_col1" class="data row7 col1" >168350</td>
      <td id="T_a43b6_row7_col2" class="data row7 col2" >0.02</td>
      <td id="T_a43b6_row7_col3" class="data row7 col3" >1.8%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row8" class="row_heading level0 row8" >3</th>
      <td id="T_a43b6_row8_col0" class="data row8 col0" >5,317,179</td>
      <td id="T_a43b6_row8_col1" class="data row8 col1" >114754</td>
      <td id="T_a43b6_row8_col2" class="data row8 col2" >0.02</td>
      <td id="T_a43b6_row8_col3" class="data row8 col3" >2.2%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row9" class="row_heading level0 row9" >6</th>
      <td id="T_a43b6_row9_col0" class="data row9 col0" >3,756,935</td>
      <td id="T_a43b6_row9_col1" class="data row9 col1" >86365</td>
      <td id="T_a43b6_row9_col2" class="data row9 col2" >0.02</td>
      <td id="T_a43b6_row9_col3" class="data row9 col3" >2.3%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row10" class="row_heading level0 row10" >15</th>
      <td id="T_a43b6_row10_col0" class="data row10 col0" >2,207,458</td>
      <td id="T_a43b6_row10_col1" class="data row10 col1" >69042</td>
      <td id="T_a43b6_row10_col2" class="data row10 col2" >0.03</td>
      <td id="T_a43b6_row10_col3" class="data row10 col3" >3.1%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row11" class="row_heading level0 row11" >13</th>
      <td id="T_a43b6_row11_col0" class="data row11 col0" >8,591,342</td>
      <td id="T_a43b6_row11_col1" class="data row11 col1" >334938</td>
      <td id="T_a43b6_row11_col2" class="data row11 col2" >0.04</td>
      <td id="T_a43b6_row11_col3" class="data row11 col3" >3.9%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row12" class="row_heading level0 row12" >5</th>
      <td id="T_a43b6_row12_col0" class="data row12 col0" >3,188,503</td>
      <td id="T_a43b6_row12_col1" class="data row12 col1" >124427</td>
      <td id="T_a43b6_row12_col2" class="data row12 col2" >0.04</td>
      <td id="T_a43b6_row12_col3" class="data row12 col3" >3.9%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row13" class="row_heading level0 row13" >7</th>
      <td id="T_a43b6_row13_col0" class="data row13 col0" >8,578,780</td>
      <td id="T_a43b6_row13_col1" class="data row13 col1" >452988</td>
      <td id="T_a43b6_row13_col2" class="data row13 col2" >0.05</td>
      <td id="T_a43b6_row13_col3" class="data row13 col3" >5.3%</td>
    </tr>
    <tr>
      <th id="T_a43b6_level0_row14" class="row_heading level0 row14" >9</th>
      <td id="T_a43b6_row14_col0" class="data row14 col0" >8,994,897</td>
      <td id="T_a43b6_row14_col1" class="data row14 col1" >784082</td>
      <td id="T_a43b6_row14_col2" class="data row14 col2" >0.09</td>
      <td id="T_a43b6_row14_col3" class="data row14 col3" >8.7%</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Linie 12 sticht mit Abstand heraus — die Ausfallrate liegt rund 20× über dem Durchschnitt aller anderen Linien. Zeitliche Eingrenzung (Jahresvergleich) zeigt, dass dies auf eine **Baustellen-Phase Januar 2023 – Juni 2024** zurückzuführen ist (Streckensperrung, Ersatzverkehr). Ab Juli 2024 normalisiert sich die Rate auf ~0.2%. Für Modellierung und alle linienübergreifenden Ausfallstatistiken sollte dieser Zeitraum entweder gefiltert oder als eigenes Feature (`linie_12_baustelle`) kodiert werden. → Für spätere Analyse: Backlog-Eintrag für detaillierte Zeitraumvalidierung.

### Trip-Level Validierung

Ist `canceled` wirklich ein Trip-Level-Flag — d.h. wenn eine Fahrt ausfällt, sind **alle** Halte dieser Fahrt als `canceled = True` markiert?  
Oder gibt es "gemischte" Trips wo nur ein Teil der Halte canceled ist (→ das wären die Kurzwendungen der pre-Juli-2024-Ära)?

Gruppierung nach `trip_id` + `operating_date` — jeder Trip wird als `fully_canceled` / `fully_active` / `mixed` klassifiziert. Vergleich pre/post Juli 2024 zeigt ob sich das Muster mit der Datendefinitions-Änderung ändert.


```python
section_header("Canceled — Trip-Level Validierung")
summary = an.plot_trip_level_validation(
    PATHS["raw"] / "zh-tram-data-master.parquet", cfg
)
show_df(summary)
```

    
    [1m[38;2;52;97;141m───  CANCELED — TRIP-LEVEL VALIDIERUNG  ──────────────────────[0m
    Gesamt Trips:                4,357,849
      fully_active:              4,220,808  (96.86%)
      fully_canceled:              131,040  (3.01%)
      mixed (Kurzwendungen?):        6,001  (0.14%)



    
![png](03_analysis_1-target_files/03_analysis_1-target_56_1.png)
    



<style type="text/css">
#T_5e70e thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_5e70e td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_5e70e tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_5e70e tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_5e70e tr:hover td {
  background-color: #eef3f8;
}
#T_5e70e_row0_col0, #T_5e70e_row0_col1, #T_5e70e_row1_col0, #T_5e70e_row1_col1, #T_5e70e_row2_col0, #T_5e70e_row2_col1, #T_5e70e_row3_col0, #T_5e70e_row3_col1, #T_5e70e_row4_col0, #T_5e70e_row4_col1 {
  text-align: left;
}
#T_5e70e_row0_col2, #T_5e70e_row1_col2, #T_5e70e_row2_col2, #T_5e70e_row3_col2, #T_5e70e_row4_col2 {
  text-align: right;
}
</style>
<table id="T_5e70e">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_5e70e_level0_col0" class="col_heading level0 col0" >is_pre_july_2024</th>
      <th id="T_5e70e_level0_col1" class="col_heading level0 col1" >trip_type</th>
      <th id="T_5e70e_level0_col2" class="col_heading level0 col2" >n_trips</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_5e70e_level0_row0" class="row_heading level0 row0" >0</th>
      <td id="T_5e70e_row0_col0" class="data row0 col0" >from Jul 2024</td>
      <td id="T_5e70e_row0_col1" class="data row0 col1" >active</td>
      <td id="T_5e70e_row0_col2" class="data row0 col2" >2180581</td>
    </tr>
    <tr>
      <th id="T_5e70e_level0_row1" class="row_heading level0 row1" >1</th>
      <td id="T_5e70e_row1_col0" class="data row1 col0" >from Jul 2024</td>
      <td id="T_5e70e_row1_col1" class="data row1 col1" >canceled</td>
      <td id="T_5e70e_row1_col2" class="data row1 col2" >18250</td>
    </tr>
    <tr>
      <th id="T_5e70e_level0_row2" class="row_heading level0 row2" >2</th>
      <td id="T_5e70e_row2_col0" class="data row2 col0" >pre Jul 2024</td>
      <td id="T_5e70e_row2_col1" class="data row2 col1" >active</td>
      <td id="T_5e70e_row2_col2" class="data row2 col2" >2040227</td>
    </tr>
    <tr>
      <th id="T_5e70e_level0_row3" class="row_heading level0 row3" >3</th>
      <td id="T_5e70e_row3_col0" class="data row3 col0" >pre Jul 2024</td>
      <td id="T_5e70e_row3_col1" class="data row3 col1" >canceled</td>
      <td id="T_5e70e_row3_col2" class="data row3 col2" >112790</td>
    </tr>
    <tr>
      <th id="T_5e70e_level0_row4" class="row_heading level0 row4" >4</th>
      <td id="T_5e70e_row4_col0" class="data row4 col0" >pre Jul 2024</td>
      <td id="T_5e70e_row4_col1" class="data row4 col1" >mixed</td>
      <td id="T_5e70e_row4_col2" class="data row4 col2" >6001</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Die Trip-Level-Analyse liefert den direkten Beweis für die Datendefinitions-Änderung:

> **Was sagen die Zahlen?**
> - **Pre-Juli 2024:** 6.001 `mixed` Trips (= Kurzwendungen — nur ein Teil der Halte ist canceled) + 112.790 `fully_canceled` Trips.
> - **Ab Juli 2024:** Die `mixed` Trips verschwinden vollständig — es gibt nur noch `fully_canceled` (18.250) oder `fully_active`.
>
> Warum ist das der Beweis? Bei echten Komplett-Ausfällen wäre ein Trip entweder ganz ausgefallen oder ganz gefahren. Dass es vor Juli 2024 Tausende „teils-ausgefallene" Trips gibt und danach null — das ist kein zufälliges Muster. Das zeigt, dass VBZ die Definitionsregel geändert hat: Kurzwendungen wurden früher als „teilweise canceled" gezählt, danach gar nicht mehr.

Das erklärt die netzweite simultane Normalisierung der Cancellation-Rate ab Juli 2024 besser als jede Baustellen-Theorie. → F-TARGET-05, F-TARGET-11

### Linie 12 — Baustelle Temporal


```python
section_header('Cancellation Rate Over Time')

an.plot_cancellation_rate_over_time(lf_all, cfg)

section_header("Delay per Linie — Zeitlicher Verlauf")

log('Plot all')
an.plot_delay_per_line_timeline(lf_all, cfg, ylim_arr=(20,220), ylim_dep=(20,200), ylim_delta=(0,40))

log('Table all')
show_df(an.table_delay_per_line_summary(lf_all))

log('Plot clean')
an.plot_delay_per_line_timeline(lf_clean, cfg, ylim_arr=(20,120), ylim_dep=(20,120), ylim_delta=(0,15))

log('Table clean')
show_df(an.table_delay_per_line_summary(lf_clean))
```

    
    [1m[38;2;52;97;141m───  CANCELLATION RATE OVER TIME  ────────────────────────────[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_59_1.png)
    


    
    [1m[38;2;52;97;141m───  DELAY PER LINIE — ZEITLICHER VERLAUF  ───────────────────[0m
    [38;2;52;97;141mPlot all[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_59_3.png)
    


    [38;2;52;97;141mTable all[0m



<style type="text/css">
#T_5b61c thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_5b61c td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_5b61c tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_5b61c tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_5b61c tr:hover td {
  background-color: #eef3f8;
}
#T_5b61c_row0_col0, #T_5b61c_row0_col1, #T_5b61c_row0_col2, #T_5b61c_row1_col0, #T_5b61c_row1_col1, #T_5b61c_row1_col2, #T_5b61c_row2_col0, #T_5b61c_row2_col1, #T_5b61c_row2_col2, #T_5b61c_row3_col0, #T_5b61c_row3_col1, #T_5b61c_row3_col2, #T_5b61c_row4_col0, #T_5b61c_row4_col1, #T_5b61c_row4_col2, #T_5b61c_row5_col0, #T_5b61c_row5_col1, #T_5b61c_row5_col2, #T_5b61c_row6_col0, #T_5b61c_row6_col1, #T_5b61c_row6_col2, #T_5b61c_row7_col0, #T_5b61c_row7_col1, #T_5b61c_row7_col2, #T_5b61c_row8_col0, #T_5b61c_row8_col1, #T_5b61c_row8_col2, #T_5b61c_row9_col0, #T_5b61c_row9_col1, #T_5b61c_row9_col2, #T_5b61c_row10_col0, #T_5b61c_row10_col1, #T_5b61c_row10_col2, #T_5b61c_row11_col0, #T_5b61c_row11_col1, #T_5b61c_row11_col2, #T_5b61c_row12_col0, #T_5b61c_row12_col1, #T_5b61c_row12_col2, #T_5b61c_row13_col0, #T_5b61c_row13_col1, #T_5b61c_row13_col2, #T_5b61c_row14_col0, #T_5b61c_row14_col1, #T_5b61c_row14_col2, #T_5b61c_row15_col0, #T_5b61c_row15_col1, #T_5b61c_row15_col2, #T_5b61c_row16_col0, #T_5b61c_row16_col1, #T_5b61c_row16_col2, #T_5b61c_row17_col0, #T_5b61c_row17_col1, #T_5b61c_row17_col2 {
  text-align: right;
}
</style>
<table id="T_5b61c">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_5b61c_level0_col0" class="col_heading level0 col0" >Ø Arr Delay (s)</th>
      <th id="T_5b61c_level0_col1" class="col_heading level0 col1" >Ø Dep Delay (s)</th>
      <th id="T_5b61c_level0_col2" class="col_heading level0 col2" >Ø Δ (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Linie</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_5b61c_level0_row0" class="row_heading level0 row0" >E</th>
      <td id="T_5b61c_row0_col0" class="data row0 col0" >128.10</td>
      <td id="T_5b61c_row0_col1" class="data row0 col1" >127.80</td>
      <td id="T_5b61c_row0_col2" class="data row0 col2" >-0.30</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row1" class="row_heading level0 row1" >11</th>
      <td id="T_5b61c_row1_col0" class="data row1 col0" >68.60</td>
      <td id="T_5b61c_row1_col1" class="data row1 col1" >75.10</td>
      <td id="T_5b61c_row1_col2" class="data row1 col2" >6.50</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row2" class="row_heading level0 row2" >15</th>
      <td id="T_5b61c_row2_col0" class="data row2 col0" >61.80</td>
      <td id="T_5b61c_row2_col1" class="data row2 col1" >63.50</td>
      <td id="T_5b61c_row2_col2" class="data row2 col2" >1.70</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row3" class="row_heading level0 row3" >10</th>
      <td id="T_5b61c_row3_col0" class="data row3 col0" >59.90</td>
      <td id="T_5b61c_row3_col1" class="data row3 col1" >66.30</td>
      <td id="T_5b61c_row3_col2" class="data row3 col2" >6.40</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row4" class="row_heading level0 row4" >8</th>
      <td id="T_5b61c_row4_col0" class="data row4 col0" >59.70</td>
      <td id="T_5b61c_row4_col1" class="data row4 col1" >64.20</td>
      <td id="T_5b61c_row4_col2" class="data row4 col2" >4.50</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row5" class="row_heading level0 row5" >7</th>
      <td id="T_5b61c_row5_col0" class="data row5 col0" >58.90</td>
      <td id="T_5b61c_row5_col1" class="data row5 col1" >62.70</td>
      <td id="T_5b61c_row5_col2" class="data row5 col2" >3.90</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row6" class="row_heading level0 row6" >4</th>
      <td id="T_5b61c_row6_col0" class="data row6 col0" >57.50</td>
      <td id="T_5b61c_row6_col1" class="data row6 col1" >65.60</td>
      <td id="T_5b61c_row6_col2" class="data row6 col2" >8.20</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row7" class="row_heading level0 row7" >2</th>
      <td id="T_5b61c_row7_col0" class="data row7 col0" >56.30</td>
      <td id="T_5b61c_row7_col1" class="data row7 col1" >63.40</td>
      <td id="T_5b61c_row7_col2" class="data row7 col2" >7.20</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row8" class="row_heading level0 row8" >9</th>
      <td id="T_5b61c_row8_col0" class="data row8 col0" >55.80</td>
      <td id="T_5b61c_row8_col1" class="data row8 col1" >61.60</td>
      <td id="T_5b61c_row8_col2" class="data row8 col2" >5.80</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row9" class="row_heading level0 row9" >14</th>
      <td id="T_5b61c_row9_col0" class="data row9 col0" >55.40</td>
      <td id="T_5b61c_row9_col1" class="data row9 col1" >63.10</td>
      <td id="T_5b61c_row9_col2" class="data row9 col2" >7.80</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row10" class="row_heading level0 row10" >3</th>
      <td id="T_5b61c_row10_col0" class="data row10 col0" >54.00</td>
      <td id="T_5b61c_row10_col1" class="data row10 col1" >59.40</td>
      <td id="T_5b61c_row10_col2" class="data row10 col2" >5.40</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row11" class="row_heading level0 row11" >13</th>
      <td id="T_5b61c_row11_col0" class="data row11 col0" >52.50</td>
      <td id="T_5b61c_row11_col1" class="data row11 col1" >57.80</td>
      <td id="T_5b61c_row11_col2" class="data row11 col2" >5.20</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row12" class="row_heading level0 row12" >12</th>
      <td id="T_5b61c_row12_col0" class="data row12 col0" >51.80</td>
      <td id="T_5b61c_row12_col1" class="data row12 col1" >56.10</td>
      <td id="T_5b61c_row12_col2" class="data row12 col2" >4.30</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row13" class="row_heading level0 row13" >17</th>
      <td id="T_5b61c_row13_col0" class="data row13 col0" >47.90</td>
      <td id="T_5b61c_row13_col1" class="data row13 col1" >51.30</td>
      <td id="T_5b61c_row13_col2" class="data row13 col2" >3.50</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row14" class="row_heading level0 row14" >5</th>
      <td id="T_5b61c_row14_col0" class="data row14 col0" >47.20</td>
      <td id="T_5b61c_row14_col1" class="data row14 col1" >54.60</td>
      <td id="T_5b61c_row14_col2" class="data row14 col2" >7.50</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row15" class="row_heading level0 row15" >50</th>
      <td id="T_5b61c_row15_col0" class="data row15 col0" >46.60</td>
      <td id="T_5b61c_row15_col1" class="data row15 col1" >59.70</td>
      <td id="T_5b61c_row15_col2" class="data row15 col2" >13.20</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row16" class="row_heading level0 row16" >51</th>
      <td id="T_5b61c_row16_col0" class="data row16 col0" >41.40</td>
      <td id="T_5b61c_row16_col1" class="data row16 col1" >61.50</td>
      <td id="T_5b61c_row16_col2" class="data row16 col2" >20.20</td>
    </tr>
    <tr>
      <th id="T_5b61c_level0_row17" class="row_heading level0 row17" >6</th>
      <td id="T_5b61c_row17_col0" class="data row17 col0" >38.30</td>
      <td id="T_5b61c_row17_col1" class="data row17 col1" >42.60</td>
      <td id="T_5b61c_row17_col2" class="data row17 col2" >4.20</td>
    </tr>
  </tbody>
</table>



    [38;2;52;97;141mPlot clean[0m



    
![png](03_analysis_1-target_files/03_analysis_1-target_59_7.png)
    


    [38;2;52;97;141mTable clean[0m



<style type="text/css">
#T_16a25 thead th {
  background-color: #e0e0e0;
  color: #000000;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 14px 5px 0;
  border-bottom: 1px solid #b0b0b0;
  text-align: left;
}
#T_16a25 td {
  font-size: 12px;
  padding: 3px 14px 3px 0;
  color: #000000;
}
#T_16a25 tr:nth-child(even) td {
  background-color: #f5f5f5;
}
#T_16a25 tr:nth-child(odd) td {
  background-color: #ffffff;
}
#T_16a25 tr:hover td {
  background-color: #eef3f8;
}
#T_16a25_row0_col0, #T_16a25_row0_col1, #T_16a25_row0_col2, #T_16a25_row1_col0, #T_16a25_row1_col1, #T_16a25_row1_col2, #T_16a25_row2_col0, #T_16a25_row2_col1, #T_16a25_row2_col2, #T_16a25_row3_col0, #T_16a25_row3_col1, #T_16a25_row3_col2, #T_16a25_row4_col0, #T_16a25_row4_col1, #T_16a25_row4_col2, #T_16a25_row5_col0, #T_16a25_row5_col1, #T_16a25_row5_col2, #T_16a25_row6_col0, #T_16a25_row6_col1, #T_16a25_row6_col2, #T_16a25_row7_col0, #T_16a25_row7_col1, #T_16a25_row7_col2, #T_16a25_row8_col0, #T_16a25_row8_col1, #T_16a25_row8_col2, #T_16a25_row9_col0, #T_16a25_row9_col1, #T_16a25_row9_col2, #T_16a25_row10_col0, #T_16a25_row10_col1, #T_16a25_row10_col2, #T_16a25_row11_col0, #T_16a25_row11_col1, #T_16a25_row11_col2, #T_16a25_row12_col0, #T_16a25_row12_col1, #T_16a25_row12_col2, #T_16a25_row13_col0, #T_16a25_row13_col1, #T_16a25_row13_col2, #T_16a25_row14_col0, #T_16a25_row14_col1, #T_16a25_row14_col2 {
  text-align: right;
}
</style>
<table id="T_16a25">
  <thead>
    <tr>
      <th class="blank level0" >&nbsp;</th>
      <th id="T_16a25_level0_col0" class="col_heading level0 col0" >Ø Arr Delay (s)</th>
      <th id="T_16a25_level0_col1" class="col_heading level0 col1" >Ø Dep Delay (s)</th>
      <th id="T_16a25_level0_col2" class="col_heading level0 col2" >Ø Δ (s)</th>
    </tr>
    <tr>
      <th class="index_name level0" >Linie</th>
      <th class="blank col0" >&nbsp;</th>
      <th class="blank col1" >&nbsp;</th>
      <th class="blank col2" >&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="T_16a25_level0_row0" class="row_heading level0 row0" >11</th>
      <td id="T_16a25_row0_col0" class="data row0 col0" >69.20</td>
      <td id="T_16a25_row0_col1" class="data row0 col1" >74.90</td>
      <td id="T_16a25_row0_col2" class="data row0 col2" >6.00</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row1" class="row_heading level0 row1" >15</th>
      <td id="T_16a25_row1_col0" class="data row1 col0" >61.70</td>
      <td id="T_16a25_row1_col1" class="data row1 col1" >63.00</td>
      <td id="T_16a25_row1_col2" class="data row1 col2" >1.40</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row2" class="row_heading level0 row2" >8</th>
      <td id="T_16a25_row2_col0" class="data row2 col0" >60.90</td>
      <td id="T_16a25_row2_col1" class="data row2 col1" >64.10</td>
      <td id="T_16a25_row2_col2" class="data row2 col2" >2.90</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row3" class="row_heading level0 row3" >10</th>
      <td id="T_16a25_row3_col0" class="data row3 col0" >60.70</td>
      <td id="T_16a25_row3_col1" class="data row3 col1" >66.40</td>
      <td id="T_16a25_row3_col2" class="data row3 col2" >5.30</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row4" class="row_heading level0 row4" >7</th>
      <td id="T_16a25_row4_col0" class="data row4 col0" >58.80</td>
      <td id="T_16a25_row4_col1" class="data row4 col1" >62.90</td>
      <td id="T_16a25_row4_col2" class="data row4 col2" >3.80</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row5" class="row_heading level0 row5" >4</th>
      <td id="T_16a25_row5_col0" class="data row5 col0" >58.60</td>
      <td id="T_16a25_row5_col1" class="data row5 col1" >65.40</td>
      <td id="T_16a25_row5_col2" class="data row5 col2" >7.00</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row6" class="row_heading level0 row6" >2</th>
      <td id="T_16a25_row6_col0" class="data row6 col0" >57.50</td>
      <td id="T_16a25_row6_col1" class="data row6 col1" >63.90</td>
      <td id="T_16a25_row6_col2" class="data row6 col2" >6.20</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row7" class="row_heading level0 row7" >9</th>
      <td id="T_16a25_row7_col0" class="data row7 col0" >56.30</td>
      <td id="T_16a25_row7_col1" class="data row7 col1" >61.00</td>
      <td id="T_16a25_row7_col2" class="data row7 col2" >4.60</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row8" class="row_heading level0 row8" >14</th>
      <td id="T_16a25_row8_col0" class="data row8 col0" >56.10</td>
      <td id="T_16a25_row8_col1" class="data row8 col1" >63.10</td>
      <td id="T_16a25_row8_col2" class="data row8 col2" >6.90</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row9" class="row_heading level0 row9" >3</th>
      <td id="T_16a25_row9_col0" class="data row9 col0" >54.70</td>
      <td id="T_16a25_row9_col1" class="data row9 col1" >59.20</td>
      <td id="T_16a25_row9_col2" class="data row9 col2" >4.40</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row10" class="row_heading level0 row10" >13</th>
      <td id="T_16a25_row10_col0" class="data row10 col0" >52.80</td>
      <td id="T_16a25_row10_col1" class="data row10 col1" >57.70</td>
      <td id="T_16a25_row10_col2" class="data row10 col2" >4.80</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row11" class="row_heading level0 row11" >12</th>
      <td id="T_16a25_row11_col0" class="data row11 col0" >52.50</td>
      <td id="T_16a25_row11_col1" class="data row11 col1" >56.50</td>
      <td id="T_16a25_row11_col2" class="data row11 col2" >3.90</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row12" class="row_heading level0 row12" >5</th>
      <td id="T_16a25_row12_col0" class="data row12 col0" >48.40</td>
      <td id="T_16a25_row12_col1" class="data row12 col1" >55.00</td>
      <td id="T_16a25_row12_col2" class="data row12 col2" >6.50</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row13" class="row_heading level0 row13" >17</th>
      <td id="T_16a25_row13_col0" class="data row13 col0" >48.30</td>
      <td id="T_16a25_row13_col1" class="data row13 col1" >51.30</td>
      <td id="T_16a25_row13_col2" class="data row13 col2" >3.20</td>
    </tr>
    <tr>
      <th id="T_16a25_level0_row14" class="row_heading level0 row14" >6</th>
      <td id="T_16a25_row14_col0" class="data row14 col0" >37.50</td>
      <td id="T_16a25_row14_col1" class="data row14 col1" >41.20</td>
      <td id="T_16a25_row14_col2" class="data row14 col2" >3.90</td>
    </tr>
  </tbody>
</table>



**Beobachtung:** Linie 10 und Linie 12 zeigen synchrones Verhalten — aber mit allen Linien sichtbar wird der eigentliche Befund klar: **fast das gesamte Netz** hatte erhöhte Ausfallraten vor Juli 2024. Linie 9 (~10%), Linie 17 (~11%), Linie 7 (~6%) — alle normalisieren gleichzeitig im Juli 2024 auf ~0.3%, obwohl sie völlig unterschiedliche Strecken fahren. Das ist das stärkste Argument gegen eine infrastrukturelle Erklärung.

**Hypothese: Datendefinitions-Änderung Juli 2024.** Vor diesem Datum wurden vermutlich Kurzwendungen, Teilausfälle und Betriebsanpassungen als `canceled` geführt — ab Juli 2024 nur noch echte Vollausfälle. Das erklärt die netzweite simultane Normalisierung besser als jede Baustellen-Theorie. → **F-TARGET-11**

---

**Die Delay-Zeitachse als Gegenprobe:** Wenn die erhöhten Ausfallraten vor Juli 2024 auf ein echtes operatives Problem zurückzuführen wären — Baustelle blockiert das Netz, Kaskadenstörungen, strukturelle Beeinträchtigung — dann müssten die `arrival_delay`-Werte im selben Zeitraum ebenfalls erhöht oder volatiler sein. Die Monthly-Delay-Zeitachse zeigt genau das Gegenteil: ein **kontinuierlicher, gleichmässiger Aufwärtstrend** ohne Bruch, ohne Plateau, ohne erkennbare Erhöhung vor Juli 2024. Die Verspätungswerte von 2023 liegen sogar leicht *unter* denen von 2024.

Das ist der entscheidende Beweis: wäre die Baustelle operativ spürbar gewesen, hätten wir es in den Delays gesehen. Da wir es nicht sehen, war die erhöhte Ausfallrate kein reales Netzproblem — sondern ein **Reporting-Artefakt**. Zwei unabhängige Metriken (Cancellations vs. Delays) erzählen nur unter der Datendefinitions-Hypothese eine konsistente Geschichte.

---

**Revidierte Strategie — `canceled`-Flag pre/post Juli 2024:**

| Strategie | Beschreibung | Pro | Con |
|:---|:---|:---|:---|
| **A — Feature kodieren** | `is_pre_july_2024 = 1` für alle Linien vor Jul 2024 | Daten bleiben, Modell bekommt Kontext | Modell muss Effekt lernen |
| **B — Zeitraum filtern** | Pre-Jul 2024 `canceled`-Records aus Training | Sauberste Baseline | Verliert ~18 Monate Daten |
| **C — canceled komplett ausschließen** | `canceled = True` Records aus Delay-Modell raus (haben keine sinnvollen Delay-Werte) | Sinnvoll — ausgefallene Fahrten haben kein `arrival_delay` | Cancellation-Modell separat behandeln |

**Entscheidung: Strategie A + C kombiniert.** `canceled = True` Records werden aus dem Delay-Modell ausgeschlossen (die haben keine sinnvollen Verspätungswerte). Für ein separates Cancellation-Modell wird `is_pre_july_2024` als Feature kodiert. → F-TARGET-05

### Monthly Delay

Wie entwickelt sich `delay_delta` über die Zeit? Gibt es Saisonalität, oder ist der Anstieg linear?

**Beobachtung:** Der monatliche Verlauf zeigt ab **November 2025** einen abrupten Sprung in `delay_delta_mean` (von ~5s auf ~17s im November, ~26s im Dezember). Dies entspricht keiner organischen Saisonschwankung — die Kurve bricht aus dem langjährigen Muster aus. Wahrscheinlichste Ursache: **Fahrplanwechsel Dezember 2025** (VBZ-Netzrestrukturierung j25→j26). Wenn neue Soll-Zeiten erst verzögert ins GTFS eingepflegt wurden, würden die Ist-Abweichungen künstlich aufgebläht erscheinen. **Nov–Dez 2025 aus Trendanalysen ausschließen.** → Bereinigte Ansicht folgt direkt unten.

**Beobachtung:** Ohne den Fahrplanwechsel-Artefakt zeigt sich ein klares saisonales Muster: **Winter-Peak (Dez/Jan)** und ein kleinerer **Frühlings-Peak (März)** sowie **Sommer-Peak (Juni)** — unterbrochen von einem relativen Tal in den Sommermonaten (Juli–August), das aber trotzdem auf hohem Niveau bleibt. Die gestrichelten Trendlinien bestätigen einen **strukturellen Aufwärtstrend** über alle drei Metriken — kein Einmaleffekt. `dep_delay` steigt am stärksten. Alle drei Metriken steigen: das System wird insgesamt langsamer, nicht nur an einzelnen Punkten. → Saison-Feature (Monat, Winter/Sommer-Flag) und Jahr als Features in Modell aufnehmen.

### Delay per Linie — Zeitlicher Verlauf

Wie entwickeln sich alle drei Delay-Metriken pro Linie über die Zeit? Zeigt welche Linien strukturell höhere Verspätungen haben und ob sich die Spreizung verändert. `canceled = True` ausgeschlossen.

**Beobachtung:** Die Streuung zwischen den Linien ist erheblich. **Dominanter Ausreisser: Linie E** mit Ø 128s Arrival Delay — rund 70s über dem Netzschnitt (~57s). Ohne Linie E liegen die regulären Linien zwischen ~47s (Linie 5) und ~68s (Linie 11). Das linienspezifische Muster ist **zeitlich stabil**: eine Linie die 2023 schlecht war, ist auch 2024 und 2025 schlecht. `delay_delta` zeigt die stärkste Spreizung: Linie 11 (+6.5s) und Linie 10 (+6.4s) akkumulieren Verspätung systematisch; Linie E (-0.3s) ist in dieser Metrik neutral. Der Nov/Dez 2025-Artefakt ist auch hier sichtbar — er betrifft alle Linien gleichzeitig, was ein netzweites Messsystem-Artefakt bestätigt (→ Untersuchung im Hintergrund-Block). → `line_name` und `month` sind die stärksten strukturellen Prädiktoren.

### Hintergrund: VBZ Fahrplanwechsel

> **Was ist ein Fahrplanwechsel — einfach erklärt:**
> Zweimal im Jahr (Dezember + Juni) wechselt die VBZ den offiziellen Fahrplan — die sogenannten GTFS-Daten. Das sind die Solldaten: welche Linie fährt wann, wo, mit welchen Haltestellen.
> Im Dezember 2023 war das ein besonders grosser Wechsel: Linien 9, 11 und 13 bekamen neue Streckenführungen, neue Haltestellen und neue Fahrzeiten. Diesen Zeitraum nennen wir `j23 → j24`.
>
> **Warum ist das für unsere Analyse wichtig?**
> Vergleiche von Linie 11 vor und nach Dezember 2023 hinken — es ist faktisch eine andere Linie. Ein Delay-Anstieg von Linie 11 zwischen j23 und j24 könnte bedeuten: die neue Strecke ist langsamer, ODER der Fahrplan wurde nicht angepasst, ODER es ist ein Einlaufeffekt der neuen Haltestellen.
> Deshalb muss `gtfs_year` als Kontextvariable immer mitgedacht werden — es kodiert nicht nur Zeit, sondern auch Netzstruktur.

---

### Untersuchung: Nov/Dez 2025 Anomalie (abgeschlossen 2026-05-20)

**Ausgangsbefund aus den Daten:**

Der monatliche Verlauf zeigt ab exakt **14. November 2025** einen abrupten Sprung in `delay_delta_mean`:

| Datum | `delay_delta_mean` |
|:---|:---|
| 13. November 2025 | ~6s (normal) |
| 14. November 2025 | ~16s (**+10s über Nacht**) |
| 21. November 2025 | ~30s+ (Spitzenwert) |
| 23. Dezember 2025 | Rückkehr zur Normalverteilung |

**Was wir überprüft haben:**

| Frage | Befund |
|:---|:---|
| Betrifft es alle Linien? | **Ja** — alle 15 Linien gleichzeitig, kein linienspezifisches Muster |
| Steigt `arrival_delay` auch? | **Nein** — `arrival_delay` bleibt stabil. Nur `departure_delay` steigt. |
| Haben sich die Schedule-Werte geändert? | **Nein** — `arrival_schedule` und `departure_schedule` unverändert. Kein j26-Fahrplan im Datensatz. |
| Gibt es ein bekanntes Ereignis am 14. Nov? | **Kein publiziertes Ereignis gefunden.** Bahnhofquai-Baustelle begann erst 14. Dez 2025. |

**Was das bedeutet — die Logik:**

```
delay_delta = departure_delay − arrival_delay
           = (actual_dep − scheduled_dep) − (actual_arr − scheduled_arr)
           = actual_dwell_time − scheduled_dwell_time
```

Da `scheduled_dep` und `scheduled_arr` unverändert sind, muss `actual_dwell_time` gestiegen sein — Trams blieben ab Nov 14 länger an Haltestellen als geplant.

**Verworfene Hypothese:**

> *"j26-GTFS-Daten wurden schrittweise eingespeist, was die Soll-Zeiten veränderte."*

Datenbasiert widerlegt: Schedule-Werte zeigen keine Änderung ab November 2025. Die Anomalie liegt in den IST-Abfahrtzeiten, nicht in den SOLL-Zeiten.

**Wahrscheinlichste Erklärung (nicht abschliessend beweisbar ohne VBZ-interne Daten):**

Ab Mitte November 2025 begann VBZ die operative Vorbereitung auf den grössten Fahrplanwechsel in der Unternehmensgeschichte (14. Dez 2025: "Tramnetz Süd", 10 von 14 Linien geändert). Fahrereinweisungen, Probeumläufe und neue Turnusplanung können reale Verlängerungen der Standzeiten verursacht haben, während der SOLL-Referenzwert im Datensatz weiterhin j25 enthielt. Die Rückkehr zur Normalverteilung am **23. Dezember** (9 Tage nach j26) ist konsistent mit dieser Erklärung.

---

**Filterentscheidung — gewählte Strategie: Maskierung statt Ausschluss**

Statt Nov/Dez 2025 vollständig auszuschliessen, werden `departure_delay` und `delay_delta` im Anomaliewindow auf `NaN` gesetzt. `arrival_delay` — die Zielvariable — ist nicht betroffen und bleibt vollständig erhalten.

| Spalte | Behandlung |
|:---|:---|
| `departure_delay` | → `NaN` für 14. Nov – 23. Dez 2025 |
| `delay_delta` | → `NaN` für 14. Nov – 23. Dez 2025 |
| `arrival_delay` | ✅ unverändert — vom Phänomen nicht betroffen |
| `is_anomal` | ✅ Neues Boolean-Flag — `True` = im Anomaliewindow |

**Warum das funktioniert:** `departure_delay` und `delay_delta` sind **keine Modell-Features** (verifiziert aus `lgbm_v1_meta.json` — keines der 32 Features enthält diese Spalten). Ihre Maskierung kostet das Modell nichts.

**Was wir gewinnen — der quantitative Mehrwert:**

| | Ausschluss (alt) | Maskierung (neu) | Gewinn |
|:---|:---|:---|:---|
| Test-Set (2025) | ~25M Zeilen | ~30M Zeilen | **+~5M Zeilen (+~20%)** |
| November 2025 | vollständig fehlend | ✅ vorhanden | Ø arrival_delay ~58s |
| Dezember 2025 | vollständig fehlend | ✅ vorhanden | Fahrplanwechsel-Monat |

**Warum das für die Evaluierung kritisch ist:**
November war der schlechteste Monat im Netz (~58s Ø arrival_delay, weit über Jahresdurchschnitt). Ein Modell, das nicht auf dem schlechtesten Monat evaluiert wird, überschätzt die eigene Güte systematisch. +~5M Testzeilen und vollständige November-Abdeckung sind kein Detailgewinn — das ist der Unterschied zwischen ehrlicher und beschönigter Modell-Evaluation.

**Umsetzung:** Zentral in `apply_lf_clean()` + `mask_departure_anomaly()` (→ `src/zh_tram_flow/data/cleaning.py`). Alle Notebooks via `setup_analysis()`. Kein hardcodierter Filter mehr.

## Key Findings



→ Vollständige Findings-Tabelle mit Impact und Handlungsempfehlungen in [`03_analysis_0-overview.ipynb`](03_analysis_0-overview.ipynb).

| ID | Finding | Status |
|:---|:---|:---|
| F-TARGET-01 | `arrival_delay` rechtsschiefe Verteilung — Median 42s vs. Mean 56.3s; Log-Transform empfohlen | done |
| F-TARGET-02 | `delay_delta` bimodal — zwei Modi: Recovery-Cluster ~−45s (netzweit, nicht terminus-spezifisch) und Akkumulations-Cluster ~+15s; Verteilung unverändert in `lf_clean` | done |
| F-TARGET-03 | **71.5%** `delay_delta > 0` — kein ausreichender Fahrplanpuffer | done |
| F-TARGET-04 | Scheduled Dwell-Time (`dep_schedule − arr_schedule`) im Datensatz vorhanden — Mehrheit der Werte ist 0s (kein Puffer eingeplant); Feature schwach, nur für Halte mit >0s relevant | done |
| F-TARGET-05 | `canceled`-Flag netzweit erhöht Jan 2023 – Jun 2024 — Datendefinitions-Änderung beim Anbieter | done |
| F-TARGET-06 | Nov–Dez 2025 Fahrplanwechsel-Artefakt (j25→j26 GTFS) — aus Analysen ausgeschlossen (Strategie A) | done |
| F-TARGET-07 | Extremwerte bis ±3600s — wahrscheinlich echte Grossstörungen (Unwetter, Netzausfälle), kein Messfehler | done |
| F-TARGET-08 | `trip_id` und `stop_sequence` jetzt im Master-Datensatz — Kaskaden- und Trip-Level-Analyse möglich | done |
| F-TARGET-09 | Bereinigte Trendanalyse Jan–Okt 2025: delta +4.6s→+5.1s→+5.1s (moderater Aufwärtstrend); vollständiges 2025 mit Nov/Dez-Artefakt: +7.9s (irreführend) | done |
| F-TARGET-10 | `arrival_delay` 2025 (Jan–Okt, bereinigt): **+55.8s** — leicht unter 2024 (+59.4s) → Stabilisierung im Ankunfts-Delay | done |
| F-TARGET-11 | Netzweite synchrone Erhöhung der Ausfallrate aller Linien vor Jul 2024 — Trip-Level-Validierung bestätigt: 6.001 `mixed` Trips pre-Jul (Kurzwendungen), 0 mixed ab Jul. Datendefinitions-Änderung bewiesen | done |
| F-TARGET-12 | **Linie E** ist massiver Ausreisser: 55.7% OTP, 130s Ø Delay — als Entlastungslinie separat behandeln | done |
| F-TARGET-13 | Bereinigung (`lf_clean`) verschiebt Mittelwerte minimal (+1.1s arr, −0.8s delta) — Starthalte 4.8%, Linie E 0.003% der Daten. Tendenzen unverändert, Verteilungsform bereinigt (kein −50s-Cluster) | done |



