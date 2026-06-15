# Analysis Overview

Central entry point for all analysis notebooks.
Core questions, notebook index and key findings summary.

**Datensatz:** 93'904'623 Zeilen (lf_all) · 3 Jahre (2023–2025) · 16 Tramlinien + Linie E · Zürich
**Bereinigt (lf_clean):** canceled==False · stop_sequence > 1 · kein Nov/Dez 2025 · kein Linie E

## Executive Summary

**93.9 Mio. Datenpunkte · 3 Jahre (2023–2025) · 16 Tramlinien · Zürich**

Das Zürcher Tramnetz fährt mit einer systemischen Schwäche: **an 71.5% aller Halte akkumuliert die Tram Verspätung** — kein Puffer ist eingebaut. OTP liegt bei 87%. Das ist stabil, aber strukturell fragil.

**Die 6 stärksten Erkenntnisse:**

| # | Kernbotschaft | Finding |
|:---|:---|:---|
| 1 | Verspätungen entstehen an der **Peripherie**, nicht im Zentrum — Central und Paradeplatz performen gut, Schwamendingen und Oerlikon (K11/K12) sind die Hotspots | F-SPAT-01/03 |
| 2 | **Kein Morgenrush** — das dominante Muster ist Feierabend + Events. Peak um 21h (67.9s) durch Abreisewellen. Donnerstag schlechtester Wochentag | F-TEMP-01/02 |
| 3 | **Schnee ist der stärkste Einzeleinflussfaktor** (+54s, OTP −10.9pp) — und geografisch klar trennbar von Regen (Höhenlagen vs. Flusstäler) | F-WEAT-01/07 |
| 4 | **Feiertage sind die besten Tage** (−9.9s) — der Berufsverkehrs-Rückgang überwiegt jeden Event-Effekt | F-EVNT-01 |
| 5 | Der **größte Fahrplanwechsel in VBZ-Geschichte** (Dez 2023) ist im Delay-Signal unsichtbar (+0.5s netzweit) — und zielte nicht auf die Problemkreise | F-NET-03/09 |
| 6 | **Vorhersagbar = Strukturell = Steuerbar** — MAE 18.56s beweist: Delays folgen Mustern. Das Modell identifiziert WO und WANN Fahrplan-Puffer fehlen und liefert damit die Grundlage für datengetriebenes Schedule-Design | F-REC-01/02 |

→ Vollständige Findings: [Key Findings](#Key-Findings) · Feature-Kandidaten: [Modelling Insights](#Modelling-Insights)

---

**Kernthese — vier Befunde, eine Aussage:**

| Befund | Finding |
|:---|:---|
| 71.5% aller Halte akkumulieren Delay · 71.3% haben 0s dwell_time | F-TARGET-03 · F-SPAT-08 |
| Hotspots ausschliesslich an der Peripherie — zentrale Knoten performen gut | F-SPAT-01 · F-SPAT-07 |
| Netzausbau 2023 zielte auf gut-performende Kreise — Problemkreise K11/K12 erhielten nichts | F-NET-09 |
| MAE 18.56s beweist Strukturalität: Zufällige Delays sind nicht so präzise vorhersagbar | F-REC-01 |

> **"Die Verspätungen im Zürcher Tramnetz sind vorhersagbar, sie sind systematisch —  
> und das Modell zeigt wo der Fahrplan geändert werden muss."**

## Datenstrategie — lf_clean Definition



> Basis für alle Trend- und Modellanalysen. Begründung jedes Schritts.

| Filter-Schritt | Bedingung | Anteil entfernt | Begründung |
|:---|:---|:---|:---|
| Non-canceled | `canceled == False` | ~4.4% | Ausgefallene Fahrten haben keine validen Delay-Werte |
| Starthalte | `stop_sequence > 1` | ~4.8% der Non-canceled | Startstops zeigen künstlich niedrige `arrival_delay`-Werte (kein Vorgänger) |
| Linie E | `line_name != 'E'` | ~0.003% | Massiver Ausreisser (OTP 55.7%, 130s Ø Delay, nur 2'511 Zeilen) — separat behandeln |
| Nov/Dez 2025 | Monate 11–12 im Jahr 2025 entfernt | Artefakt | Fahrplanwechsel j25→j26 GTFS: delay_delta springt auf +17.1s/+26.0s — kein echter Betriebstrend |

**Effekt der Bereinigung auf Mittelwerte:** `arrival_delay` +1.1s · `delay_delta` −0.8s — minimal, Tendenzen unverändert.

**Gesamtzeilen:** lf_all = 93'904'623 · Non-canceled = 89'714'901 · lf_clean ≈ 85M (nach allen Filtern)

→ Details und Quantifizierung: `03_analysis_1-target.ipynb` (F-TARGET-05, F-TARGET-06, F-TARGET-12, F-TARGET-13)

### Analyse vs. Modell — Datenbasis im Vergleich

| | Analyse-Notebooks (`03_analysis_*`) | Modell (`06_prediction_*`) |
|:---|:---|:---|
| Datenbasis | `lf_all` = TRAIN + TEST · alle 3 Jahre | `train_final.parquet` · 2023–2024 |
| Warum | EDA darf alles sehen | Kein Blick in die Zukunft — 2025 bleibt unberührt |
| Zeilen | ~85M (lf_clean) | 41.2M Train · 14.3M Val · ~25M Test |
| `departure_delay` | ✅ verfügbar — für Post-hoc-Analyse | ❌ ausgeschlossen — Leakage |
| `delay_delta` | ✅ verfügbar — zeigt Akkumulationsmuster | ❌ ausgeschlossen — Leakage |
| Sampling | Aggregationen: voller Datensatz via Polars LazyFrame. Korrelationen/Scatter: `gather_every(2)` + `sample(fraction=0.1)` → ~4.5M | Kein Sampling — LightGBM trainiert auf vollen 41.2M Zeilen |

Warum die Analyse alle 3 Jahre sieht: EDA beschreibt Realität — dafür soll sie so viel Daten wie möglich sehen. Der Train/Test-Split ist eine Modellierungs-Konvention die verhindert dass das Modell die Zukunft "kennt". Für die Analyse ist das irrelevant — eine Haltestelle die 2025 ein Hotspot ist, war es auch 2023 und 2024.

## Notebooks

| Notebook | Focus |
|:---|:---|
| `03_analysis_1-target.ipynb` | Delay distribution, OTP, arr vs dep, cancellations |
| `03_analysis_2-network.ipynb` | Netzveränderungen 2023–2025 · Vor/Nachher · Einlaufzeit · Hotspots · Versorgungsqualität |
| `03_analysis_3-temporal.ipynb` | Hour · weekday · month · season · full year |
| `03_analysis_4-spatial.ipynb` | Stops · districts · lines |
| `03_analysis_5-meteo.ipynb` | Rain · wind · snow · temperature |
| `03_analysis_6-events.ipynb` | Holidays · events · event size |

> **Hinweis für alle Notebooks:** Das Tramnetz hat sich im Analysezeitraum 2023–2025 verändert.
> Fahrplanwechsel Dezember 2023 (j23 → j24): Linien 9, 11 und 13 wurden fundamental umgebaut.
> Bei linienbezogenen Befunden immer `03_analysis_2-network.ipynb` als Kontext heranziehen.



## Line Colors



Offizielle VBZ-Linienfarben aus GTFS `routes.txt` — verfügbar via `line_color("12")` aus `zh_tram_flow.config`.

| Linie | Farbe | | Linie | Farbe | | Linie | Farbe |
|:---:|:---|:---|:---:|:---|:---|:---:|:---|
| **2** | `#E20A16` | | **8** | `#8AB51F` | | **14** | `#008DC5` |
| **3** | `#00892F` | | **9** | `#11296F` | | **15** | `#E20A16` |
| **4** | `#11296F` | | **10** | `#E12472` | | **17** | `#8E224D` |
| **5** | `#734522` | | **11** | `#00892F` | | **19** | `#E20A16` |
| **6** | `#CA7D3C` | | **12** | `#92D6E3` | | **E** | `#E20A16` |
| **7** | `#000000` | | **13** | `#FFCC00` | | | |


# Analysis Result


## Core Questions

1. Where do delays occur? — stops, districts, lines
2. When do delays occur? — time of day, weekday, season
3. What amplifies delays? — weather, events
4. What does the target itself look like? — distribution, OTP, arr vs dep
5. Which features correlate most with delays?
6. Can delays be predicted? → modeling

## Key Findings

> Alle Findings werden in den jeweiligen Analysis-Notebooks erarbeitet und hier zentral gelistet.
> ID-Schema: `F-{NOTEBOOK}-{NR}` — Status: `open` · `in-progress` · `done`
> Präsentation: `hot` = starkes Einzel-Finding · `story` = Teil einer größeren Erzählung · `—` = technisch/intern

| ID | Notebook | Section | Finding | Präs. | Impact | Action | Status |
|:---|:---|:---|:---|:---|:---|:---|:---|
| F-TARGET-01 | target | Distribution | `arrival_delay` rechtsschiefe Verteilung — Median 42s vs. Mean 56.3s | `—` | Lineare Modelle unterschätzen Extremwerte | Log-Transform + MdAE-Check | done |
| F-TARGET-02 | target | Delay Delta | `delay_delta` bimodal — Recovery-Cluster ~−45s und Akkumulations-Cluster ~+15s; kein Datenfehler | `story` | Systematisches Signal im delta | `delay_delta` als Nebenmetrik | done |
| F-TARGET-03 | target | Delay Delta | **71.5% `delay_delta > 0`** — kein Fahrplanpuffer; Trams akkumulieren an über 2/3 aller Halte | `hot` | Systemischer Puffermangel | `delay_delta` als Nebenmetrik | done |
| F-TARGET-04 | target | Target | `dwell_time` verfügbar; 71.3% = 0s (Durchfahrten ohne Haltezeit) | `—` | Feature schwächer als erwartet | `has_dwell` als Binary | done |
| F-TARGET-05 | target | Cancellations | `canceled`-Artefakt vor Jul 2024 — kein reales Betriebsproblem. Effektive Rate: 6.2% | `—` | Verfälscht Cancellation-Baseline | `canceled=True` aus Delay-Modell | done |
| F-TARGET-06 | target | Monthly Trend | Nov–Dez 2025 GTFS-Artefakt: delay_delta springt auf +17.1s/+26.0s — kein echter Betriebstrend | `—` | Verfälscht Trendanalyse | Nov–Dez 2025 aus Train+Test entfernen | done |
| F-TARGET-07 | target | Extremwerte | Extremwerte bis ±3600s — wahrscheinlich echte Grossstörungen, kein Messfehler | `—` | Robust-Modell bevorzugen | Robust-Loss (MdAE + Huber) | done |
| F-TARGET-08 | target | OTP | `trip_id` + `stop_sequence` im Master-Datensatz — Kaskadenanalyse möglich | `—` | Prediction-Signal verfügbar | `trip_id` in Feature Engineering | done |
| F-TARGET-09 | target | Trend | delay_delta Trend: j23=+4.6s → j24=+5.1s → j25=+5.1s (moderat, stabil) | `story` | Struktureller Aufwärtstrend real aber nicht alarmierend | `year` + `month` als Features | done |
| F-TARGET-10 | target | Trend | `arrival_delay` 2025 (Jan–Okt): **55.8s** — leicht unter 2024 (59.4s) → Stabilisierung | `story` | Netz wird nicht in allen Metriken schlechter | In Trend-Analyse hervorheben | done |
| F-TARGET-11 | target | Cancellations | Synchrone Cancellation-Erhöhung aller Linien vor Jul 2024 — beweist Datendefinitions-Änderung | `—` | Stärkstes Qualitäts-Argument | `is_pre_july_2024` als Feature | done |
| F-TARGET-12 | target | Outlier | **Linie E**: OTP 55.7%, Ø 130s, 2'511 Zeilen — aus lf_clean entfernt | `—` | Outlier verzerrt Modell-Baseline | Als Sonderlinie annotieren | done |
| F-TARGET-13 | target | Datenstrategie | Bereinigung minimal (+1.1s arr, −0.8s delta) — Tendenzen unverändert | `—` | lf_clean ist saubere Modellbasis | lf_clean als Standard | done |
| F-NET-01 | network | Netzveränderungen | L9/L11/L13 Dez 2023: +8/+13/+19 Halte im GTFS. Teils Artefakt (Innenstadtachse), teils echte Erweiterungen (L13→Sihlcity, L11→Rehalp) | `story` | Jahresvergleiche nur mit Kontext | `gtfs_year` Feature kodiert Zeitschnitt | done |
| F-NET-02 | network | Netzveränderungen | Stabile Referenzlinien: L10, L12, L14, L17 identisch über alle Jahre | `—` | Kontrollgruppe für Zeitreihen | Als Referenzlinien verwenden | done |
| F-NET-03 | network | Feature | `gtfs_year` erklärt netzweit nur +0.5s — schwaches Feature | `—` | Kein klarer Netzwechsel-Effekt | `n_stops_line` als Alternative | done |
| F-NET-04 | network | Einlaufzeit | Kein Einlaufzeit-Effekt: Unterschiede lagebezogen, nicht zeitbezogen | `—` | Neubaustrecken keine Einlauf-Toleranz nötig | `is_new_stop` wenig aussagekräftig | done |
| F-NET-05 | network | Hotspots | **Keine Korrelation** Linienanzahl × Delay: Central/Paradeplatz (je 7 Linien, ~49s) — beide unter Netzschnitt | `hot` | Kaskadenrisiko-Hypothese widerlegt | Aussenkorridore statt Knotenpunkte | done |
| F-NET-06 | network | Versorgung | Kreis 12 (+2) und Kreis 4 (+2) gewinnen Linien. Kreis 7 verliert 2 Linien | `—` | Räumliche Netzstruktur-Änderung | Kreise 12/4 verbessert; Kreis 7 verschlechtert | done |
| F-NET-07 | network | Kaskaden | `trip_id` ermöglicht `prev_trip_delay` als Feature | `—` | Prediction-Signal | In Feature Engineering | open |
| F-NET-08 | network | Linie E | Linie E: 130s Ø Delay — Entlastungslinie, separat behandeln | `—` | Extremer Outlier | Als Sonderlinie annotieren | done |
| F-NET-09 | network | Hotspots | **Netzausbau vs. Delay-Hotspots — kein Overlap:** Echte Erweiterungen in K3/K8 (gut performend). K11/K12 (Problemkreise) erhielten nichts | `hot` | Netz ausgebaut, aber nicht wo es gebraucht wird | Kontext für VBZ-Empfehlung | done |
| F-TEMP-01 | temporal | Stunden | Kein Morgenrush (7h=48.9s unter Ø). Peak **21h=67.9s** (Events-Abreisewelle), 17h=65.2s | `hot` | `hour` stärkstes temporales Feature | `hour` + `hour × has_event` | done |
| F-TEMP-02 | temporal | Wochentag | **Donnerstag** kritischster Tag: Ø 60.4s, P95=194s. Montag (52.3s) und Sonntag (48.4s) beste Tage | `hot` | `weekday` als Feature | `day_of_week` ordinalkodiert | done |
| F-TEMP-03 | temporal | Wochentag | Donnerstag-Peak: Events-Häufung (Do-Abend) + HO-Hypothese — nicht direkt belegt | `story` | Interaktion Do × Abend × Events | `is_school_week` als Modifier | done |
| F-TEMP-04 | temporal | Wochentag | Samstag (57.0s) kaum besser als Werktag; Sonntag (48.4s) deutlich besser | `—` | `weekday` ordinalkodiert statt binär | `day_of_week` 7-Kategorien | done |
| F-TEMP-05 | temporal | Monat | **November-Peak**: Nov 2023=68.9s, Nov 2024=72.6s — jeweils Jahreshöchstwert | `hot` | `is_november` als Feature-Flag | Ursache: Laub + Baustellensaison + MIV | done |
| F-TEMP-06 | temporal | Saison | Herbst=61.2s schlechteste; **Winter=51.7s beste Jahreszeit** (OTP 88.9%) — kontraintuitiv | `story` | `season` als Feature | Winter-Vorteil: MIV-Reduktion | done |
| F-TEMP-07 | temporal | Zeitreihe | Aufwärtstrend: 2024 +4–7s über 2023; 2025 leicht moderater (Stabilisierung) | `story` | `year` + `month` als Features | Rolling-Baseline als Feature-Idee | done |
| F-TEMP-08 | temporal | Zeitreihe | Schulferien-Täler im Rolling-Average erkennbar | `—` | Ferieneffekt additiv | `is_school_holiday` aus ZH-Kalender | done |
| F-TEMP-09 | temporal | Feature | `gtfs_year` netzweit +0.5s — bestätigt F-NET-03 | `—` | Schwaches Feature | Empirisch evaluieren | done |
| F-TEMP-10 | temporal | Stunden | Nacht-/Partyverkehr (0–3h): Fr/Sa leichter 2h-Anstieg — Partygänger-Rückfahrten (n datendünn) | `—` | `hour × is_weekend` als Interaktion | In Feature Engineering | done |
| F-SPAT-01 | spatial | Hotspots | Hotspots sind periphere Aussenkorridore: Friedhof Enzenbühl 93.8s, Balgrist 85.2s — **nicht** zentrale Knotenpunkte | `hot` | `stop_name` stärkster räumlicher Prädiktor | Target-Encoding + n-Threshold | done |
| F-SPAT-02 | spatial | Terminus | Terminus-Frühankünfte: lf_all=55.8s vs. lf_clean=56.9s (Δ nur 1s) | `—` | Kein Verzerrungseffekt | n-Threshold-Filter | done |
| F-SPAT-03 | spatial | Stadtkreise | **Kreis 11** schlechtester (68.3s, OTP 83%), Kreis 12 (66.3s). Kreis 5 bester (49.9s, OTP 89%) | `hot` | `district_nr` additiv nützlich | K11/K12 als High-Risk-Marker | done |
| F-SPAT-04 | spatial | Linien | Alle Linien akkumulieren (delta > 0). Stärkste: L4 (+8.1s), L10 (+6.5s), L11 (+6.2s) | `story` | `line_name` als Feature | Linien-Encoding | done |
| F-SPAT-05 | spatial | Linien | `line_name` stärkster räumlicher Prädiktor. L11 (68.7s, OTP 82%) kritischste Hauptlinie | `—` | Beide Features ins Modell | Target-Encoding für `stop_name` | done |
| F-SPAT-06 | spatial | Starthalte | Starthaltestellen-Proxy: 0 Kandidaten — Verzerrung 0.0s | `—` | n-Threshold-Filter empfohlen | `n_threshold` in Preprocessing | done |
| F-SPAT-07 | spatial | Linien-Dichte | **0 Overlap** Top-20-Linienanzahl × Top-20-Delay. Haldenegg (15 Linien, 44.5s), Paradeplatz (14 Linien, 48.2s) — alle unter Netzschnitt | `story` | `n_lines_at_stop` schwaches Feature | Aussenkorridore statt Knotenpunkte | done |
| F-SPAT-08 | spatial | dwell_time | `dwell_time` = 0s für **71.3%** — kein Puffer eingebaut. System akkumuliert unweigerlich | `hot` | Feature schwächer als erwartet | `has_dwell` testen | done |
| F-SPAT-09 | spatial | Endstationen | **Endstationen-Muster:** L11/L13/L7 grosse Delay-Bubbles an Start und Ende. Linienlänge als Proxy-Feature prüfen | `story` | Peripheral-Effekt messbar | `n_stops_line` als Feature | done |
| F-SPAT-10 | spatial | Richtung | Fahrt Richtung Aussenquartiere akkumuliert mehr Delay als Rückfahrt. `trip_direction` als Feature prüfen | `—` | Asymmetrie messbar | `trip_direction` (letzter Stop) | done |
| F-SPAT-11 | spatial | Heatmap | Abend-Peak (17–19 Uhr) netzweit synchron. L11/L8 hohes Grundniveau ganztags | `—` | `hour × line_name` Interaktion stärker als Einzelfeatures | In Feature Engineering | done |
| F-WEAT-01 | weather | Schnee | **Schnee stärkster Wettereffekt**: +54.0s, OTP 87.1%→76.1% (−10.9pp) | `hot` | `has_snow` wichtigstes Wetter-Feature | `has_snow` priorisieren | done |
| F-WEAT-02 | weather | Regen | Starkregen: +23.3s. Dosis-Wirkungs: <2mm=62.6s → >10mm=89.5s | `story` | `precipitation` kontinuierlich als Feature | `rain_scale` 0–4 | done |
| F-WEAT-03 | weather | Wind | `is_windy` = NaN — nie befüllt. **Aus Feature-Set entfernt.** | `—` | Feature-Set bereinigt | `is_windy` entfernt | done |
| F-WEAT-04 | weather | Temperatur | 0–5°C = bester Bereich (53.8s). `is_hot` (>20°C) = +2.0s — schwaches Signal | `—` | Frost-Hypothese falsch | `temperature` kontinuierlich | done |
| F-WEAT-05 | weather | Korrelation | Alle Wetter-Features schwach (max r=0.042) — unabhängige Signale | `—` | Kein Multikollinearitätsproblem | Alle behalten | done |
| F-WEAT-06 | weather | Features | `precipitation` (r=0.036) und `has_snow` (r=0.038) nützlichste Features | `—` | Priorität: Schnee + Niederschlag | Feature-Selection nach Training | done |
| F-WEAT-07 | weather | Geografie | **Geografische Trennung:** Schnee trifft Höhenlagen (K10/K4/K12), Regen trifft Flusstäler (K5). Bahnhof Selnau Schnee-Extremausreisser: +190.9s | `hot` | Topographie bestimmt Vulnerabilität | `district × has_snow` als Interaktion | done |
| F-WEAT-08 | weather | Regen | **Regen-Korridor K5:** 11/20 Top-Regen-Halte im Escher Wyss / Toni-Areal / Limmat. Toni-Areal +44.2s | `story` | Geografisch konzentrierter Effekt | K5 × `has_heavy_rain` | done |
| F-WEAT-09 | weather | Linien | **Linien reagieren komplett unterschiedlich:** L17 Schnee +7.7s vs. Regen +41.2s (Limmat-Route). L9 Schnee +75.9s vs. Regen +10.0s (Höhenlagen) | `hot` | `line × Wettertyp` Interaktionsterm | `line_name × has_snow` | done |
| F-EVNT-01 | events | Feiertage | Feiertage **46.3s vs. Normal 56.2s (−9.9s, OTP +3.6pp)** — bester Tagestyp | `hot` | `is_holiday` wichtigstes Event-Feature | `is_holiday` in `02_preparation` | done |
| F-EVNT-02 | events | Event-Grösse | Gross=66.7s (+10.5s), Mittel=58.9s (+2.7s), Klein=56.2s (+0.05s ≈ Normal) | `story` | `event_weight` ordinal; Klasse 1 binarisieren | `event_weight ≥ 2` als Schwelle | done |
| F-EVNT-03 | events | Stunden | Event-Effekt primär **Abend-Phänomen (18–22h)** — tagsüber kein Unterschied. Erklärt 21h-Spike | `hot` | `has_event × hour` Interaktion | `event_weight × hour` | done |
| F-EVNT-04 | events | Event-Typ | **Fachmessen schlechteste Kategorie** (66.0s, OTP 84%) — nicht Konzerte. Super League 53.8s ≈ Normal | `story` | `event_type` kategorisch | Fachmessen-Effekt für L11 | done |
| F-EVNT-05 | events | Balance | Gross-Events n=724k vs. Normal 70.5M — stark unbalanced | `—` | Oversampling oder gewichtetes Training | Event-Strategie in Modell-Phase | done |
| F-EVNT-06 | events | Stadtkreise | Stadtkreis-Δ auf Event-Tagen minimal (max +3.0s K2). Räumliche Aggregation verbirgt Abend-Effekt | `—` | `has_event × hour` aussagekräftiger | Abend-Fokus in Feature Engineering | done |
| F-SIM-01 | sim | dwell_time | `dwell_time` ist Feature #1 in lgbm_v1 (Gain 14.8M > stop_name 12.7M), aber **faktisch binär**: 0s (71.3%) oder 60s (28.5%) — Werte 1–59s existieren nicht im VBZ-Fahrplan | `hot` | Binäre Verteilung limitiert direkte Simulation — kein kontinuierlicher Hebel | Stopspezifische Kalibrierung statt pauschaler 0/60 | done |
| F-SIM-02 | sim | dwell_time | `dwell_time` korreliert **positiv** mit Delay (r=+0.16): Stops mit 60s haben ~28s mehr Delay. Ursache: Konfundierung — VBZ gibt Puffer an komplexen Stops, die strukturell mehr Delay haben | `hot` | Feature Importance ≠ kausaler Hebel; Modell hat Korrelation korrekt gelernt | Konfundierung explizit kommunizieren | done |
| F-SIM-03 | sim | dwell_time | Simulation 0→60s: Modell erhöht Vorhersage um +20s (L11: +19.96s, netzweit: +20.72s). Modell kann nicht unterscheiden ob dwell_time=60 wegen Stopschwierigkeit (historisch) oder als Puffer (hypothetisch) | `story` | Observational ML isoliert Kausaleffekt nicht | A/B-Test oder Instrumental Variable für Validierung | done |
| F-SIM-04 | sim | dwell_time | Operative Empfehlung trotzdem valide (F-SPAT-08 + Domänenwissen): stopspezifische dwell_time statt 0/60. Quantifizierung erfordert A/B-Test. Modell liefert Diagnose, Betrieb liefert Dosis | `story` | Kausalinferenz braucht experimentelle Daten | Pilot-Experiment mit ausgewählten Stops | done |
| F-REC-01 | rec | full-circle | **Vorhersagbar = Strukturell = Steuerbar.** MAE 18.56s beweist: Delays folgen Mustern. Zufällige Delays wären nicht so präzise vorhersagbar. Was Muster hat, kann durch Fahrplandesign beeinflusst werden | `hot` | Modell transformiert Analyse-Findings in operative Handlungsgrundlage | Modell-Output als Input für Schedule-Design verwenden | done |
| F-REC-02 | rec | recommendations | Risiko-Matrix (Stop × Linie × Kontext) aus lgbm_v1-Vorhersagen identifiziert Stop-Linie-Kontext-Kombinationen mit pred. Delay >60s — Grundlage für stopspezifische dwell_time-Kalibrierung | `hot` | Präzisere Pufferstrategie als pauschale 0/60s | Empfehlungstabelle als Fahrplan-Input nutzen | done |
| F-REC-03 | rec | recommendations | Kontextspezifische Muster: Schnee betrifft andere Stops als Events oder Rush-Hour. Einheitliche Pufferstrategie greift zu kurz → kontextsensitive Fahrpläne (Schneefahrplan, Eventfahrplan) sind die logische Konsequenz | `story` | Mehrere Betriebs-Szenarien mit je eigenem Puffer-Raster | Kontextsensitive Fahrpläne entwerfen | done |
| F-REC-04 | rec | recommendations | Empfohlene Puffergrößen sind Startpunkte (Heuristik: 1/3 Überschuss, gerundet auf 5s). Validierung durch operatives A/B-Testing: Modell liefert Diagnose, Betrieb liefert Dosis | `story` | Kausale Wirkung nicht aus Observational-Daten ableitbar | Randomisiertes Pilot-Experiment für Kalibrierung | done |

## Report-Auswahl — Präsentation & Report

> Gefiltert auf `hot` und `story` Findings. Grundlage für die Narrative des Reports.
> `hot` = starkes Einzel-Finding · `story` = Teil einer größeren Erzählung

### Target & Datenqualität

| ID | Präs. | Kernbotschaft |
|:---|:---:|:---|
| F-TARGET-03 | `hot` | **71.5% aller Halte akkumulieren Delay** — kein Puffer eingebaut |
| F-TARGET-02 | `story` | `delay_delta` bimodal: Recovery-Cluster vs. Akkumulations-Cluster — Systemmuster, kein Datenfehler |
| F-TARGET-09 | `story` | Aufwärtstrend: delay_delta +4.6s→+5.1s (2023→2025) |
| F-TARGET-10 | `story` | `arrival_delay` 2025: 55.8s — Stabilisierung gegenüber 2024 (59.4s) |

### Netz & Struktur

| ID | Präs. | Kernbotschaft |
|:---|:---:|:---|
| F-NET-05 | `hot` | **Keine Korrelation Linienanzahl × Delay** — Haldenegg und Paradeplatz (je 14–15 Linien) unter Netzschnitt |
| F-NET-09 | `hot` | **Netzausbau zielte nicht auf Problemkreise** — K3/K8 ausgebaut, K11/K12 (Hotspots) erhielten nichts |
| F-NET-01 | `story` | L9/L11/L13: teils GTFS-Artefakt (Innenstadt), teils echte Erweiterungen (L13→Sihlcity, L11→Rehalp) |

### Zeit

| ID | Präs. | Kernbotschaft |
|:---|:---:|:---|
| F-TEMP-01 | `hot` | **Kein Morgenrush** — Peak 21h=67.9s (Events-Abreisewelle), 17h=65.2s (Feierabend) |
| F-TEMP-02 | `hot` | **Donnerstag kritischster Tag** (60.4s, P95=194s) — Sonntag bester (48.4s) |
| F-TEMP-05 | `hot` | **November-Peak**: Nov 2024=72.6s — jeweils Jahreshöchstwert |
| F-TEMP-06 | `story` | **Winter beste Jahreszeit** (51.7s, OTP 88.9%) — kontraintuitiv: MIV-Reduktion überwiegt |
| F-TEMP-07 | `story` | Aufwärtstrend 2024 vs. 2023: +4–7s netzweit; 2025 leicht moderater |
| F-TEMP-03 | `story` | Donnerstag-Peak: Events-Häufung + HO-Hypothese — nicht direkt belegt |

### Raum

| ID | Präs. | Kernbotschaft |
|:---|:---:|:---|
| F-SPAT-01 | `hot` | **Hotspots an der Peripherie** — Friedhof Enzenbühl 93.8s, Balgrist 85.2s, nicht zentrale Knotenpunkte |
| F-SPAT-03 | `hot` | **Kreis 11 schlechtester** (68.3s, OTP 83%), Kreis 12 (66.3s) — Aussenquartiere strukturell benachteiligt |
| F-SPAT-08 | `hot` | **dwell_time = 0s für 71.3%** — kein Puffer eingebaut; System akkumuliert unweigerlich |
| F-SPAT-04 | `story` | Alle Linien akkumulieren (delay_delta > 0) — systemisches Muster, kein Einzellinienproblem |
| F-SPAT-07 | `story` | 0 Overlap Top-Dichte × Top-Delay: Haldenegg (15 Linien, 44.5s) und Paradeplatz (14 Linien, 48.2s) unter Netzschnitt |
| F-SPAT-09 | `story` | L11/L13/L7: grosse Delay-Bubbles an Endstationen — Linienlänge als Proxy-Feature |

### Wetter

| ID | Präs. | Kernbotschaft |
|:---|:---:|:---|
| F-WEAT-01 | `hot` | **Schnee stärkster Einzeleffekt** (+54s, OTP −10.9pp) |
| F-WEAT-07 | `hot` | **Geografische Trennung:** Schnee trifft Höhenlagen (K10/K4/K12), Regen trifft Flusstäler (K5) |
| F-WEAT-09 | `hot` | **Linien reagieren komplett unterschiedlich:** L17 Schnee +7.7s vs. Regen +41.2s; L9 umgekehrt |
| F-WEAT-02 | `story` | Starkregen Dosis-Wirkung: <2mm=62.6s → >10mm=89.5s |
| F-WEAT-08 | `story` | **Regen-Korridor K5:** Escher Wyss / Toni-Areal / Limmat — Toni-Areal +44.2s |

### Events & Feiertage

| ID | Präs. | Kernbotschaft |
|:---|:---:|:---|
| F-EVNT-01 | `hot` | **Feiertage beste Tage** (46.3s, −9.9s vs. Normal) — Berufsverkehrs-Rückgang überwiegt |
| F-EVNT-03 | `hot` | **Event-Effekt primär Abend (18–22h)** — tagsüber kein Unterschied; erklärt 21h-Spike |
| F-EVNT-02 | `story` | Event-Grösse: Gross=66.7s (+10.5s), Klein=56.2s ≈ Normal |
| F-EVNT-04 | `story` | **Fachmessen schlechteste Kategorie** (66.0s, OTP 84%) — nicht Konzerte oder Sport |

### Simulation & Empfehlungen (Full Circle)

| ID | Präs. | Kernbotschaft |
|:---|:---:|:---|
| F-REC-01 | `hot` | **Vorhersagbar = Strukturell = Steuerbar** — MAE 18.56s beweist Muster-Existenz; Modell macht aus Analyse eine Handlungsgrundlage |
| F-SIM-01 | `hot` | **dwell_time binär (0/60s)** — VBZ nutzt den stärksten Modell-Prädiktor als On/Off-Schalter statt als kontinuierlichen Hebel |
| F-SIM-02 | `hot` | **Konfundierung:** r=+0.16 — komplexe Stops haben sowohl mehr dwell_time als auch mehr Delay; Feature Importance ≠ kausaler Hebel |
| F-REC-02 | `hot` | **Risiko-Matrix** identifiziert exakt wo Fahrplan-Puffer fehlen (Stop × Linie × Kontext) — Grundlage für stopspezifische dwell_time-Kalibrierung |
| F-SIM-03 | `story` | Simulation 0→60s: Modell sagt +20s Delay vorher — Observational ML isoliert Kausaleffekt nicht; A/B-Test nötig |
| F-REC-03 | `story` | Kontextsensitive Fahrpläne: Schnee, Events und Rush-Hour betreffen verschiedene Stops — ein einheitlicher Puffer greift zu kurz |
| F-SIM-04 | `story` | Modell liefert Diagnose (WO), Betrieb liefert Dosis (WIE VIEL) — operative Empfehlung trotz Modell-Limitierung valide |
| F-REC-04 | `story` | Empfohlene Puffergrößen sind Startpunkte — Validierung durch randomisiertes Pilot-Experiment |

## Kernfragen & KPIs 



> Stand nach Analyse-Phase (vor Modellierung). ✅ = bereits beantwortbar · 🔜 = benötigt Modell · ⚠️ = teilweise / Hypothese

---

#### Baseline KPIs (aus Analyse)

| KPI | Wert | Quelle |
|:---|:---|:---|
| OTP (arrival_delay ≤ 120s) | 87.0% | F-TARGET — Schwellwert ±120s = VBZ-Standard / VDPW |
| Ø arrival_delay (2025 Jan–Okt, bereinigt) | 55.8s | F-TARGET-10 |
| Ø delay_delta (2025 Jan–Okt, bereinigt) | ~+5.1s | F-TARGET-09 |
| Cancellation Rate (effektiv, ab Jul 2024) | 6.2% | F-TARGET-05 |
| November-Anomalie (Artefakt ohne Bereinigung) | +17s / +26s delta | F-TARGET-06 |
| Aufwärtstrend delay_delta 2023→2025 | +4.6s → +5.1s → +5.1s | F-TARGET-09 |

---

#### Kernfrage 1 — Wo entstehen Verspätungen?

**✅ Qualitativ beantwortbar.** Räumliche Hotspots und Linien-Ranking aus Analyse-Phase bekannt.

| Teilfrage | Status | Findings |
|:---|:---|:---|
| Welche Haltestellen sind die grössten Hotspots? | ✅ Periphere Aussenkorridore: Friedhof Enzenbühl 93.8s, Balgrist 85.2s, Leutschenbach 82.7s — NICHT zentrale Knotenpunkte | F-SPAT-01, F-SPAT-07 |
| Welche Linien akkumulieren Verspätung? | ✅ L11 (68.7s, OTP 82%) kritischste Hauptlinie; alle Linien akkumulieren positiv | F-SPAT-04, F-SPAT-05 |
| Welche Stadtkreise haben die höchsten Delays? | ✅ Kreis 11 (68.3s, OTP 83%) schlechtester; Kreis 12 (66.3s); Kreis 5 (49.9s, OTP 89%) bester | F-SPAT-03 |
| Wie gross ist der Starthaltestellen-Verzerrungseffekt? | ✅ 0.0s — kein messbarer Effekt; 0 Starthaltestellen-Kandidaten gefunden | F-SPAT-06, F-SPAT-02 |
| Sind Liniendichte und Verspätung korreliert? | ✅ Keine Korrelation — 0 Overlap; Haldenegg (15 Linien, 44.5s) und Paradeplatz (14 Linien, 48.2s) unter Netzschnitt | F-SPAT-07, F-NET-05 |

---

#### Kernfrage 2 — Wann entstehen Verspätungen?

**✅ Klar beantwortbar.** Zeitliche Muster vollständig analysiert.

| Teilfrage | Status | Findings |
|:---|:---|:---|
| Welche Tagesstunden sind kritisch? | ✅ Kein klassischer Morgenrush (7h=48.9s unter Ø); Peak 21h=67.9s (Events-Abreisewelle); Abend-Peak 17h=65.2s | F-TEMP-01 |
| Welcher Wochentag ist am schlechtesten? | ✅ Donnerstag (60.4s, P95=194s); Montag (52.3s) und Sonntag (48.4s) beste Tage | F-TEMP-02 |
| Welcher Monat ist am schlechtesten? | ✅ November (Nov 2023=67.9s, Nov 2024=72.9s — jeweils Jahreshöchstwert) | F-TEMP-05 |
| Welche Jahreszeit ist am schlechtesten? | ✅ Herbst (61.2s, OTP 85.2%); Winter überraschend beste Jahreszeit (51.7s, OTP 88.9%) | F-TEMP-06 |
| Gibt es einen Aufwärtstrend? | ✅ Ja, moderat und strukturell; 2024 Frühling/Sommer +4–7s über 2023 | F-TARGET-09, F-TEMP-07 |
| Ist der Schulferien-Effekt messbar? | ⚠️ sichtbar im Rolling-Average, noch nicht quantifiziert | F-TEMP-08 |

---

#### Kernfrage 3 — Was verstärkt Verspätungen?

**✅ Qualitativ beantwortbar.** Effektrichtung und relative Grösse bekannt.

| Einflussfaktor | Effekt | Status | Findings |
|:---|:---|:---|:---|
| Schnee | stark positiv (+54.0s, OTP −10.9pp) | ✅ stärkster Wettereffekt | F-WEAT-01 |
| Starkregen | moderat positiv (+23.3s); skaliert mit Intensität | ✅ Dosis-Wirkungs-Effekt | F-WEAT-02 |
| Wind | minimal / unklar | ⚠️ `is_windy` = NaN — Feature fehlt oder ohne Varianz | F-WEAT-03 |
| Hohe Temperatur (>20°C) | schwach positiv (+2.0s); Kälte (0–5°C) ist BESTE Bedingung (53.8s) | ✅ Frost-Hypothese falsch | F-WEAT-04 |
| Feiertag | stark negativ (−9.9s, OTP +3.6pp) — bester Tag-Typ | ✅ Berufsverkehr-Reduktion überwiegt | F-EVNT-01 |
| Grosse Events | positiv (+10.5s), primär Abend-Phänomen (18–22h) | ✅ Fachmessen schlechteste Kategorie (66.0s); Klein-Events ≈ Normal | F-EVNT-03, F-EVNT-04 |
| Fahrplanwechsel j23→j24 | strukturell; netzweit nur +0.5s | ✅ 3 Linien fundamental umgebaut | F-NET-01, F-NET-03 |

---

#### Kernfrage 4 — Wie sieht das Ziel selbst aus?

**✅ Vollständig beantwortbar.**

| Aspekt | Antwort | Findings |
|:---|:---|:---|
| Verteilungsform | Rechtsschiefe (Long Tail) — Log-Transform prüfen | F-TARGET-01 |
| Bimodalität | delay_delta bimodal — Recovery-Cluster ~−45s (netzweit) und Akkumulations-Cluster ~+15s — kein Fehler | F-TARGET-02 |
| Datenqualität Cancellations | Artefakt vor Jul 2024 — Datendefinitions-Änderung; effektive Rate 6.2% | F-TARGET-05, F-TARGET-11 |
| Datenqualität Nov/Dez 2025 | GTFS-Artefakt (+17.1s/+26.0s delta) — aus Analysen ausgeschlossen | F-TARGET-06 |
| Arrival vs. Departure | `delay_delta` = netto akkumuliert pro Halt (+4.6s→+5.1s Trend); `arrival_delay` = Gesamtpuffer inkl. Vorverspätung | F-TARGET-03, F-TARGET-04 |
| Linie E Outlier | OTP 55.7%, Ø 130s — Entlastungslinie, aus lf_clean entfernt, separat behandeln | F-TARGET-12, F-NET-08 |

---

#### Kernfrage 5 — Welche Features korrelieren am stärksten?

**⚠️ Teilweise beantwortbar.** Qualitatives Ranking aus Analyse, quantitativ erst nach Modell-Training.

| Feature-Gruppe | Erwartete Stärke | Basis |
|:---|:---|:---|
| `hour` | ⭐⭐⭐ hoch | F-TEMP-01 — konsistentester Effekt (21h=+11.7s über Ø) |
| `stop_name` / `line_name` | ⭐⭐⭐ hoch | F-SPAT-01, F-SPAT-05 — L11 68.7s vs. L-Mittel |
| `day_of_week` | ⭐⭐ mittel | F-TEMP-02 — Do 60.4s vs. So 48.4s |
| `has_snow` | ⭐⭐ mittel (saisonal) | F-WEAT-01 — r=0.038, +54s absolut |
| `event_weight × hour` | ⭐⭐ mittel (Abend) | F-EVNT-03 — Interaktion wichtiger als Haupteffekt |
| `month` / `season` | ⭐⭐ mittel | F-TEMP-05/06 — Nov peak, Winter best |
| `is_holiday` | ⭐⭐ mittel (negativ) | F-EVNT-01 — stärkstes negatives Signal (−9.9s) |
| `precipitation` | ⭐ gering–mittel | F-WEAT-02 — r=0.036, Dosis-Wirkung messbar |
| `temperature` | ⭐ gering (nicht-linear) | F-WEAT-04 — r=0.018 |
| ~~`is_windy`~~ | ❌ entfernt | F-WEAT-03 — NaN, nie befüllt; aus Feature-Set entfernt |
| **Quantitatives Ranking** | 🔜 nach Modell-Training | Feature Importance / SHAP |

---

#### Kernfrage 6 — Sind Verspätungen vorhersagbar?

**🔜 Modellierungs-Phase.** Aber: Analyse liefert starke Prior-Evidenz.

| Aspekt | Einschätzung | Basis |
|:---|:---|:---|
| Grundsätzliche Vorhersagbarkeit | ✅ sehr wahrscheinlich — starke zeitliche + räumliche Muster | F-TEMP-01/02, F-SPAT-01 |
| Bekannte Schwierigkeiten | Extremwerte (F-TARGET-07), Klassenungleichgewicht Events (F-EVNT-05), Linie E Outlier (F-TARGET-12) | — |
| Feature-Readiness | ⚠️ Feature Engineering in `02_preparation` noch ausstehend; `is_windy` entfernt (F-WEAT-03) | Phase C |
| Baseline-Metrik | OTP 87.0% → Random-Guess würde ~87% erreichen → Modell muss besser sein | F-TARGET |
| Modell-Kandidaten | GradientBoosting / LightGBM (Interaktionen) — 🔜 Modell-Phase | — |


## Modelling Insights



### Priorität der Findings für Modellierung und Vorhersage

#### Priorität 1 — Muss ins Modell (strukturelle Effekte)

*   **Temporale Features** sind mit Abstand die stärksten Signale:
    *   **Stunde des Tages:** Kein Morgenrush — Peak 21h (Events-Abreisewelle), 17h (Feierabend).
    *   **Wochentag:** Do > Mi > Di, Wochenende deutlich tiefer.
    *   **Monat/Saison:** November-Peak, Winter beste Jahreszeit (kontraintuitiv: MIV-Reduktion überwiegt).
    *   *Note:* Diese erklären wahrscheinlich den grössten Teil der Varianz — tram-spezifisches Verhalten folgt dem menschlichen Rhythmus.
*   **Linie** ist ein starkes Signal:
    *   L11 (68.7s), L8 (ca. 62s) deutlich über Durchschnitt (~56s).
    *   Linie E ist ein Sonderfall (130s) — separat behandeln oder ausschliessen.
*   **`stop_sequence`** — nicht als Reihenfolge, sondern als Flag:
    *   Starthalte (`seq==1`) systematisch verzerrt → aus `lf_clean` bereits entfernt, aber als Feature nützlich.

#### Priorität 2 — Wichtig, messbar verfügbar

*   **Wetter-Features:**
    *   **Schnee:** Stärkster Einzeleffekt (+54s, OTP −10.9pp) — geografisch klar trennbar von Regen (Höhenlagen vs. Flusstäler).
    *   **Starkregen:** +23.3s; Dosis-Wirkungs-Effekt messbar.
    *   **is_hot (>20°C):** Kleiner aber messbarer Effekt (+2.0s).
*   **Knotenpunkt-Last:**
    *   Paradeplatz, Haldenegg: Hohe Liniendichte, aber *kein* erhöhter Delay → Kaskadeneffekt nicht bestätigt.
    *   Einzelne High-Delay-Stops (Friedhof Enzenbühl, Balgrist) als Stop-Feature nützlich.
*   **Stadtkreis:**
    *   Kreis 11/12: Erhöhter Delay (Peripherie, Aussenkorridore).
    *   Kreis 5 (Innenstadt): Trotz Dichte nicht schlechter — bester Kreis (49.9s).

#### Priorität 3 — Interessant, aber Vorsicht

*   **Events & Feiertage:**
    *   Grosse Events (+10.5s) klar messbar — primär Abend-Phänomen (18–22h).
    *   Feiertage haben *geringeren* Delay (−9.9s, weniger Verkehr) — kontraintuitiv, aber solide belegt.
    *   *Problem:* Event-Daten nicht immer im Voraus vollständig bekannt.
*   **`gtfs_year` / Fahrplanwechsel:**
    *   F-NET-03: Kodiert strukturellen Zeitschnitt Dez 2023. Netzweit nur +0.5s — schwaches Feature.
    *   Ob Netzstruktur- oder Zeiteffekt — erst im Modellvergleich klärbar. Als Feature aufnehmen, Wichtigkeit per SHAP prüfen.
*   **`delay_delta` Bimodalität:**
    *   Recovery vs. Akkumulation ist ein netzweites Muster, kein Terminus-Artefakt.
    *   *Mögliches Feature:* "Vorheriger Halt hatte Recovery?" als Kaskadenindikator.

---

### Was für die Vorhersage am interessantesten ist

*   Das kontraintuitiv stärkste Ergebnis ist die **temporale Stabilität**: Eine Linie, die 2023 schlecht war, ist 2024 und 2025 immer noch schlecht — mit ähnlichem Muster. Das bedeutet: Ein einfaches Modell mit `Linie × Stunde × Wochentag` als Features sollte bereits eine starke Baseline liefern, bevor Wetter und Events hinzukommen.
*   Der grösste Modellierungsfehler wäre, Nov/Dez 2025 im Trainingsset zu belassen — der Fahrplanwechsel-Artefakt (+17–26s delta) würde die Modell-Residuen verzerren.

---

### Prioritätsliste Findings (Kurzfassung)

| Prio | Feature-Gruppe | Begründung |
| :--- | :--- | :--- |
| **1** | Stunde × Wochentag × Monat | Grösster Varianzanteil, zeitlich stabil über alle 3 Jahre. |
| **1** | Linie | L11/L8 strukturell schlechter, Linie E Sonderfall. |
| **2** | Wetter (Schnee > Regen > Hitze) | Klar messbar, Schnee +54s ist der stärkste Einzeleffekt. |
| **2** | Stop-Identity / Stadtkreis | Bestimmte Halte chronisch erhöht (Friedhof Enzenbühl etc.). |
| **3** | Events / Feiertage | Feiertage senken Delay — kontraintuitiv, robust belegt. |
| **3** | gtfs_year / Fahrplanwechsel | Strukturbruch Dez 2023 — erst per SHAP Wichtigkeit prüfen. |

**Wichtigste Einzelerkenntnis für das Modell:**
Temporale Stabilität über 3 Jahre — eine einfache `Linie × Stunde × Wochentag` Baseline wird bereits stark sein, bevor Wetter und Events dazukommen.

