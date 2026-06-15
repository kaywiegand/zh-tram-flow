# Zürich Tram Flow
**Verspätungsanalyse und Vorhersage im Tramnetz Zürich**

> **Datenbasis:** [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) — Research & Data Engineering Phase (abgeschlossen)  
> **Erstellt mit:** [wgnd-scaffolding](https://github.com/kaywiegand/wgnd-scaffolding) · [wgnd-toolkit](https://github.com/kaywiegand/wgnd-toolkit)

## Facts



| Feld | Wert |
|------|------|
| **Business-Frage** | Wo, wann und warum entstehen Verspätungen im Zürcher Tramnetz — und lassen sie sich vorhersagen? |
| **Stakeholder** | VBZ (Betreiber), Stadtplanung Zürich, Fahrgäste |
| **Methode** | EDA → Thematische Analyse (6 Bereiche) → Feature Engineering → ML-Modell |
| **Hauptdatenquelle** | VBZ IST-Daten 2023–2025 (opentransportdata.swiss) + GTFS + Meteo + Events |
| **Ziel-Metrik** | Vorhersagegenauigkeit (MAE) pro Linie/Stadtkreis; On-Time Performance (OTP) |
| **Out of Scope** | Echtzeit-Feed (GTFS-RT), Daten ab Format v2 (ab Mitte 2025), VBB Berlin |
| **Analysezeitraum** | 2023–2025 (IST-Daten Format v1, einheitlich) |
| **Stack** | Python · Polars · Pandas · LightGBM · Plotly · Jupyter |

## Context



### Scenario

Verspätungen im öffentlichen Nahverkehr sind ärgerlich — für Menschen und für das System.
Das Zürcher Tramnetz (VBZ) bietet eine außergewöhnlich gute Open-Data-Grundlage:
IST-Daten mit Echtzeit-Verspätungen pro Haltestelle, GTFS-Fahrplandaten, Wetterdaten
und Eventkalender — über drei Jahre (2023, 2024 und 2025).

Das Tram fährt im offenen Stadtverkehr — beeinflusst durch Autos, Fußgänger, Wetter,
Topografie und Großveranstaltungen. Das macht es zu einem besonders interessanten
Analysegegenstand für Betreiber, Stadtplanung und Fahrgäste.

### Mission

Aufbau einer vollständigen Analyse- und Vorhersage-Pipeline für Verspätungen im
Zürcher Tramnetz — vom validierten Master-Datensatz bis zum interaktiven Dashboard.
Zürich dient dabei als Referenzmodell für Städte wie Berlin, die ihre Datenpotenziale
noch nicht ausschöpfen.

### Zentrale Fragen

**Betrieb & Muster**
* Wo entstehen Verspätungen im Tramnetz — und zu welchen Zeiten?
* Welche Einflussfaktoren spielen die größte Rolle? (Wetter, Tageszeit, Events, Topografie)
* Lassen sich Verspätungen vorhersagen, bevor sie entstehen?

**Netz & Struktur**
* Hat der Netzausbau Dezember 2023 die Pünktlichkeit an den veränderten Linien und Stadtteilen verbessert oder verschlechtert?
* Zeigen neue Streckenabschnitte eine Einlaufzeit — performen sie in den ersten Monaten schlechter?
* Welche Knotenpunkte sind kritische Hotspots und lösen Kettenreaktionen aus?
* Welche Stadtteile haben durch den Ausbau mehr oder weniger Anbindung bekommen?

**Systemisch**
* Was kann ein Betreiber oder eine Stadt konkret besser machen?

### Methode & Metriken

| Metrik | Zielwert | Begründung |
|--------|----------|-------------|
| On-Time Performance (OTP) | Baseline messen | Anteil Fahrten < 2 Min Verspätung |
| Mean Absolute Error (MAE) | < 60 Sek | Vorhersagegenauigkeit pro Linie/Stadtkreis |
| Hotspot-Ranking | Top-10 Haltestellen/Linien | Räumliche Delay-Konzentration nach Halt, Linie, Stadtkreis |
| Meteo-Effektstärke | Δ Delay pro Wetterbedingung | Schnee/Regen/Temperatur-Einfluss quantifiziert |
| Event Impact Score | Verspätungsanstieg messbar | Vergleich Event-Tage vs. normale Tage |

### Modellauswahl

Entscheidung für **LightGBM** (Gradient Boosting) — native Categorical Support, schnell auf großen Datensätzen (85M+ Zeilen), kein Overfitting durch Early Stopping. Kein Optuna — Feature Engineering war entscheidend, nicht Hyperparameter-Tuning.

#### Ergebnisse

| Modell | Features | Test MAE | vs. Baseline |
|:---|:---|:---:|:---:|
| Stop Mean Baseline | — | 50.0s | — |
| **LightGBM v1** | 32 (Zeit · Wetter · Events · Linie · Stop) | 45.7s | −4.3s |
| **LightGBM v2** | 34 (+`prev_trip_delay`, +`stop_sequence_pct`) | **18.56s** | **−31.4s (−63%)** |

Schlüsselerkenntnis: `prev_trip_delay` (Kaskadenindikator aus Analyse-Finding F-NET-07) ist das stärkste neue Feature — der Sprung von 45.7s auf 18.56s kommt nicht vom Algorithmus, sondern vom Signal in den Daten.

→ Details: [`06_prediction_3-evaluation.ipynb`](06_prediction_3-evaluation.ipynb) · [`06_prediction_4-model_v2.ipynb`](06_prediction_4-model_v2.ipynb)

## Netzstruktur

Das Zürcher Tramnetz (VBZ) besteht im Analysezeitraum 2023–2025 aus **16–18 Linien** je nach Fahrplanjahr.
Die GTFS-Daten werden jährlich als neue Version veröffentlicht — **j23**, **j24** und **j25** entsprechen den drei Betriebsjahren.

> **Interaktive Karte:** [`reports/figures/tram_lines_map.html`](../reports/figures/tram_lines_map.html)
> Alle Linien mit offiziellen VBZ-Farben, Haltestellennamen und Streckenvergleich 2023 / 2024 / 2025.
> Linien und Jahre können einzeln ein- und ausgeblendet werden.

### Fahrplanwechsel Dezember 2023 — j23 → j24

Der Fahrplanwechsel im Dezember 2023 war der **größte Netzausbau in der Geschichte der VBZ**
(*Tramnetz Süd*). Drei Linien wurden fundamental umgebaut:

| Linie | j23 Halte | j24 Halte | Veränderung | Neue Abschnitte |
| :---: | ---: | ---: | :--- | :--- |
| **9** | 24 | 32 | +8 Halte | Bellevue · Paradeplatz · Sihlstrasse · Goldbrunnenplatz |
| **11** | 20 | 33 | +13 Halte | Stadelhofen · Kreuzplatz · Burgwies · Rehalp |
| **13** | 11 | 30 | +19 Halte (+173%) | Altstetten · HB · Paradeplatz · Enge · Sihlcity Nord |
| **7** | 31 | 31 | 2 Halte umbenannt | Post Wollishofen → Renggerstrasse |
| **15** | 13 | 13 | 1 Halt umbenannt | Bucheggplatz → Bucheggplatz D |

Linien **10, 12, 14, 17** sind über alle drei Jahre identisch.
Linie **18** existiert nur im Fahrplanjahr 2024 (j24).

### Implikationen für die Analyse

- **Linienvergleiche über Zeit:** Linien 9, 11 und 13 sind in j23 strukturell andere Linien als in j24/j25 — kürzere Strecken, weniger Halte, anderes Betriebsmuster. Direkter Jahresvergleich für diese Linien ist mit Vorsicht zu interpretieren.
- **Cancellation-Raten:** Erhöhte Ausfallraten in 2023 bei mehreren Linien können teilweise auf kürzere/andere Streckenführungen zurückzuführen sein — nicht zwingend auf schlechtere Betriebsqualität.
- **Feature Engineering:** `line_name` allein reicht nicht — das GTFS-Jahr (j23 vs. j24/j25) ist ein implizites Kontextmerkmal, das strukturelle Unterschiede kodiert.
- **`canceled`-Flag:** Netzweit erhöhte Rate Jan 2023 – Jun 2024, simultane Normalisierung Juli 2024 — wahrscheinlich eine Datendefinitions-Änderung beim Provider (opentransportdata.swiss), nicht ein Infrastrukturproblem. Siehe Finding F-TARGET-05.

## Data




Die gesamte Data-Engineering-Phase wurde in einem separaten Research-Repo durchgeführt
und ist dort vollständig dokumentiert:

> **Quelle:** [`sf_data-research`](https://github.com/kaywiegand/sf_data-research)  
> **Status:** Phase 1 abgeschlossen — Datenbasis vollständig und validiert.

### Was wurde dort gemacht?

| Schritt | Beschreibung | Notebook |
| :--- | :--- | :--- |
| IST-Daten | Download 36 ZIP-Archive (38 GB), Filter auf VBZ & Tram, Parquet-Konvertierung | `vbz-ist-daten.ipynb` |
| GTFS | Fahrplandaten 2023–2025, Spatial Join Stadtkreise, Haltestellen-Lookup | `vbz-gtfs-data.ipynb` |
| Meteo | 3 Quellen konsolidiert (Stampfenbachstr. + Mythenquai), Stundenmittelwerte | `vbz-meteo-data.ipynb` |
| Events | 301 Einträge, 5 Kategorien, Gewichtungsschema 1–3 | `vbz-events-data.ipynb` |
| Benchmark | Polars vs. Pandas: 4× schneller, 4× weniger RAM | `vbz-pandas-vs-polars.ipynb` |
| Master-Merge | Left Join IST + GTFS + Meteo + Events → `vbz_master.parquet` | `vbz-data-master-preparation.ipynb` |
| Validierung | 8 Checks: Schema, Abdeckung, Wertebereiche, Nulls, Join-Qualität, Business-Logik | `vbz-data-master-validation.ipynb` |

### Wichtige Entscheidungen aus der Research-Phase

| Entscheidung | Was | Warum |
| :--- | :--- | :--- |
| Polars statt Pandas | Haupt-DataFrame-Bibliothek | 4× schneller, 4× weniger RAM bei 94 Mio. Zeilen |
| Left Join überall | Merge-Strategie | Kein Datenverlust durch Join-Lücken |
| 2024 als GTFS-Referenzjahr | Fahrplandaten | Vollständigste Datenlage, stabilstes Jahr |
| 2 Meteo-Stationen | Stampfenbachstrasse + Mythenquai | Zwei Topografien: Stadtlage vs. Seelage |
| Scope 2023–2025 v1 | Analysezeitraum | Einheitliches Datenformat, kein Mischformat |
| Stadtkreis im Lookup | district im GTFS-Join | Einmalig sauber im Master, kein wiederholter Spatial Join |
| Ausfälle behalten | `canceled = True` | Extremster Verspätungsfall, für Modell unverzichtbar |
| Schwellenwert Events | >1.000 Besucher | Kleinere Events kein messbarer Netzeinfluss |
| `trip_id` + `stop_sequence` | GTFS-Join-Erweiterung | Trip-Level-Analysen, Kaskadeneffekte, Hotspot-Erkennung |

### Datenmenge

| Stufe | Menge |
| :--- | :--- |
| Rohdaten (schweizweit, komprimiert) | ~38 GB (36 ZIP-Archive) |
| Rohdaten entpackt | ~500–720 GB |
| Nach Filter VBZ + Tram (Parquet) | ~1,44 GB (1.096 Dateien) |
| Master-Datensatz | ~567 MB · 94 Mio. Zeilen · 26 Spalten |

### Data Dictionary



**Datei:** `data/raw/zh-tram-data-master.parquet`  
**Zeilen:** ~94 Millionen · **Spalten:** 26 · **Zeitraum:** 2023–2025

#### IST-Daten (Verkehr)

| # | Spaltenname | Typ | Beschreibung |
| :--- | :--- | :--- | :--- |
| 1 | `operating_date` | `Date` | Betriebstag |
| 2 | `line_name` | `Categorical` | Tramliniennummer (z.B. `"11"`) |
| 3 | `bpuic` | `Int32` | Haltestellen-ID — Join-Schlüssel zu GTFS |
| 4 | `arrival_schedule` | `Datetime` | Planmäßige Ankunftszeit |
| 5 | `arrival_delay` | `Float32` | Verspätung Ankunft in **Sekunden** (negativ = zu früh) |
| 6 | `departure_schedule` | `Datetime` | Planmäßige Abfahrtszeit |
| 7 | `departure_delay` | `Float32` | Verspätung Abfahrt in **Sekunden** |
| 8 | `canceled` | `Boolean` | Fahrtausfall = `True` — Quelle: `FAELLT_AUS_TF` (opentransportdata.swiss) |
| 9 | `trip_id` | `Categorical` | Fahrt-ID aus GTFS — Schlüssel für Trip-Level-Analysen (Kaskaden, Hotspots) |
| 10 | `stop_sequence` | `Int32` | Position des Halts innerhalb der Fahrt (1 = erster Halt) |

> ⚠️ **`canceled` — Datendefinitions-Änderung beim Provider:** Die Ausfallrate ist netzweit erhöht von Jan 2023 bis Jun 2024 und normalisiert sich simultan im Juli 2024 bei allen Linien gleichzeitig. Wahrscheinliche Ursache: opentransportdata.swiss hat `FAELLT_AUS_TF` bis Jun 2024 auch für Teilausfälle (Kurzwendungen) gesetzt — ab Jul 2024 nur noch für vollständige Fahrtausfälle. **Konsequenz für das Modell:** `canceled = True` aus dem Delay-Regressionsmodell ausschließen; `is_pre_july_2024` als Feature für ein separates Cancellation-Modell. → Finding F-TARGET-05

#### GTFS (Fahrplan & Geodaten)

| # | Spaltenname | Typ | Beschreibung |
| :--- | :--- | :--- | :--- |
| 11 | `stop_name` | `Categorical` | Haltestellenname (z.B. `"Paradeplatz"`) |
| 12 | `stop_lat` | `Float32` | Breitengrad (WGS84) |
| 13 | `stop_lon` | `Float32` | Längengrad (WGS84) |
| 14 | `district_nr` | `Int8` | Stadtkreis 1–12 (`null` = außerhalb Stadtgebiet) |
| 15 | `district_name` | `Categorical` | Stadtkreisname (z.B. `"Kreis 1"`) |

#### Meteo-Daten (Wetter)

| # | Spaltenname | Typ | Beschreibung |
| :--- | :--- | :--- | :--- |
| 16 | `temperature` | `Float32` | Temperatur in °C |
| 17 | `humidity` | `Float32` | Relative Luftfeuchtigkeit in % |
| 18 | `rain_duration` | `Float32` | Regendauer in min/h |
| 19 | `precipitation` | `Float32` | Niederschlagsmenge in mm |
| 20 | `wind_speed` | `Float32` | Windgeschwindigkeit in km/h |
| 21 | `global_radiation` | `Float32` | Globalstrahlung in W/m² |
| 22 | `flood_intensity` | `Int16` | Überschwemmungsindikator (ERZ-Meldungen) |

#### Event-Daten

| # | Spaltenname | Typ | Beschreibung |
| :--- | :--- | :--- | :--- |
| 23 | `event_name` | `Categorical` | Name des Events (`null` = kein Event an diesem Tag) |
| 24 | `event_type` | `Categorical` | Kategorie: `Feiertag`, `Stadtfest`, `Konzert`, `Messe`, `Fussball` |
| 25 | `event_size` | `Int8` | Gewichtung: `1` = mittel (>1k), `2` = groß (10k–30k), `3` = sehr groß (>30k) |
| 26 | `event_location` | `Categorical` | Veranstaltungsort (`null` = kein Event) |

#### Join-Strategie

| Join | Schlüssel | Typ |
| :--- | :--- | :--- |
| IST + GTFS Stops | `bpuic` = `bpuic` | Left Join |
| IST + Meteo | `floor(arrival_schedule, '1h')` = `date_time` | Left Join |
| IST + Events | `date(operating_date)` = `Datum` | Left Join |

> **Left Join überall:** Jede Tram-Fahrt bleibt im Datensatz erhalten. Fehlende Werte (z.B. Haltestellen außerhalb Stadtgebiet, Stunden ohne Wetterdaten) erscheinen als `null`.


### GTFS-Referenztabellen

**Verzeichnis:** `data/raw/gtfs/` — Referenzjahr 2024 (vollständigste Datenlage)

| Datei | Beschreibung | Verwendung |
| :--- | :--- | :--- |
| `gtfs_stops_lookup.parquet` | Haltestellen-Lookup: `bpuic` → `stop_name`, Koordinaten, `district_nr`, `district_name` | Join-Tabelle im Master |
| `gtfs_tram_stops.parquet` | Alle VBZ-Tram-Haltestellen mit Koordinaten | Geo-Visualisierungen |
| `gtfs_tram_routes.parquet` | Tramlinien (Route-ID, Linienname, Farbe) | Linien-Visualisierungen |
| `gtfs_tram_shapes.parquet` | Tram-Streckenverläufe als Koordinaten-Sequenzen | Streckenkarte |
| `gtfs_tram_trips.parquet` | Fahrten (Trip-ID, Route-ID, Shape-ID) | Verknüpfung Fahrten ↔ Strecken |
| `gtfs_zurich_stops.parquet` | Alle Zürich-Haltestellen (ZVV, nicht nur Tram) | Gesamtnetz-Überblick |
| `gtfs_zurich_routes.parquet` | Alle ZVV-Linien | Gesamtnetz-Überblick |
| `gtfs_zurich_shapes.parquet` | Alle ZVV-Streckenverläufe | Gesamtnetz-Karte |
| `gtfs_zurich_trips.parquet` | Alle ZVV-Fahrten | Gesamtnetz-Überblick |

## Workflow


### Notebook-Übersicht

| Notebook | Inhalt | Status |
|:---|:---|:---:|
| `00_introduction` | Projektkontext · Data Dictionary · Netzstruktur | ✅ |
| `01_exploration` | EDA: Verteilungen · Integrität · Korrelationen · Ausreisser | ✅ |
| `02_preparation` | Cleaning · Train/Test-Split · Meteo-Imputation | ✅ |
| `03_analysis_0-overview` | 63 Findings · Executive Summary · Report-Auswahl | ✅ |
| `03_analysis_1-target` | Delay-Verteilung · OTP · Cancellations · lf_clean-Strategie | ✅ |
| `03_analysis_2-network` | Netzveränderungen 2023–2025 · Hotspots · Versorgungsqualität | ✅ |
| `03_analysis_3-temporal` | Stunde · Wochentag · Monat · Saison | ✅ |
| `03_analysis_4-spatial` | Haltestellen · Stadtkreise · Linien | ✅ |
| `03_analysis_5-meteo` | Regen · Schnee · Temperatur · Niederschlagsintensität | ✅ |
| `03_analysis_6-events` | Feiertage · Events · Eventgrösse · Stop-/Linien-Ranking | ✅ |
| `04_insights` | Executive Report · Visualisierungen · HTML-Export | ✅ |
| `05_feature_engineering` | Feature-Set · Encoding · `train_final` / `test_final` Export | ✅ |
| `06_prediction_0-overview` | Vorhersage-Ansatz · Metriken · Baseline · Szenario | ✅ |
| `06_prediction_1-baseline` | Regelbasierte Baselines · Benchmark: Stop Mean MAE 50.0s | ✅ |
| `06_prediction_2-model` | LightGBM v1 · 32 Features · Test MAE 45.7s · Feature Importance | ✅ |
| `06_prediction_3-evaluation` | Fehleranalyse · MBE +8.3s · Live-Szenario | ✅ |
| `06_prediction_4-model_v2` | LightGBM v2 · `prev_trip_delay` · Test MAE 18.56s (−63%) | ✅ |
| `06_prediction_5-comparison` | Modellvergleich · XGBoost-Robustness-Check | ✅ |
| `06_prediction_6-dwell_simulator` | Dwell-Time-Simulator · Binäre Verteilung · Konfundierungs-Analyse | ✅ |
| `06_prediction_7-scheduling_recommendations` | Risikomatrix Stop × Linie × Kontext · Empfehlungskarte | ✅ |

### Konventionen

#### Variablen-Präfix

| Präfix | Typ | Bedeutung |
|:---|:---|:---|
| `lf_` | `pl.LazyFrame` | Noch nicht im RAM — Operationen werden zu einem Scan zusammengefasst |
| `df_` | `pl.DataFrame` | Nach `.collect()` — vollständig im RAM |

> **Regel:** `lf_` solange die Pipeline aufgebaut wird. Einmalig `.collect()` → ab dann `df_`.

---

#### Variablen und Dateien über alle Notebooks

| Variable / Datei | Notebook | Beschreibung |
|:---|:---|:---|
| `lf_raw` | 01 · 02 | `pl.scan_parquet(master)` — Rohdaten, lazy |
| `df_eda` | 01 | Sample für EDA: `lf_raw.gather_every(n).collect()` (~1 Mio. Zeilen) |
| `lf_clean` | 02 | `structural_cleaning_pipeline(lf_raw)` — lazy vor dem Split |
| `train_raw.parquet` / `test_raw.parquet` | 02 → `data/interim/` | Temporal Split: 2023–2024 Train / 2025 Test |
| `train_prepared.parquet` / `test_prepared.parquet` | 02 → `data/processed/` | Nach Meteo-Imputation (Forward/Backward Fill) |
| `train_features.parquet` / `test_features.parquet` | 02 → `data/processed/` | Nach Zeit- und Wetter-Features |
| `lf` / `lf_all` / `lf_clean` | 03_analysis_* | Via `setup_analysis()` — scannt `train_final` / `test_final` |
| `train_final.parquet` / `test_final.parquet` | 05 → `data/processed/` | Finales Feature-Set: 55.5 Mio. Zeilen · 40 Spalten |
