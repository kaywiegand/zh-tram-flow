# ROADMAP.md – Zurich Tram Flow

---

## Phase 0 — Research & Data Foundation ✅ ABGESCHLOSSEN
> Vollständig dokumentiert in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research)

- ✅ IST-Daten: Download, Filter, Parquet-Konvertierung
- ✅ IST-Daten: 8 Spalten, ~94 Mio. Zeilen, 1.096 Parquets, ~1,44 GB
- ✅ GTFS: Einlesen, Filtern auf VBZ Tram, 4 Parquet-Exports
- ✅ GTFS: `gtfs_stops_lookup.parquet` mit Spatial Join (Stadtkreise 1–12)
- ✅ Meteo: 3 Quellen konsolidiert → `meteo-final-export.parquet` (stündlich)
- ✅ Events: 5 Kategorien, 301 Einträge, Gewichtungsschema
- ✅ Polars vs. Pandas Benchmark → Polars (4× schneller, 4× weniger RAM)
- ✅ Master-Datensatz `vbz_master.parquet` erstellt — 26 Spalten: IST + GTFS + Meteo + Events
- ✅ Validierung abgeschlossen (8 Checks: Schema, Abdeckung, Wertebereiche, Nulls, Join-Qualität)

---

## Phase 1 — Setup & Dateneinstieg ✅ ABGESCHLOSSEN

- ✅ Projektstruktur mit wgnd-scaffolding aufgesetzt
- ✅ Datenbasis aus sf_data-research übernommen
  - `data/raw/zh-tram-data-master.parquet`
  - `data/raw/gtfs/`
- ✅ `00_introduction.ipynb` mit Projektkontext und Data Dictionary gefüllt
- ✅ Erste Datenchecks: Schema, Datentypen, Nullwerte, Datenqualität bestätigt
- ✅ `01_exploration.ipynb` aufgebaut (Basic Stats, Completeness, Integrity, Distribution, Correlations, Outliers)

---

## Phase 2 — EDA & Analyse ✅ ABGESCHLOSSEN

### EDA Notebook
- ✅ Basic Statistical Analysis (Polars + wgnd.inspect)
- ✅ Data Completeness (C1–C4 Findings)
- ✅ Data Integrity (I1–I5 Findings)
- ✅ Data Distribution (numerisch + kategorisch)
- ✅ Correlations (R1–R5 Findings, Modellierungs-Fazit: XGBoost/LightGBM)
- ✅ Outlier Detection (O1–O5, Vor/Nach-Vergleich Delays, Log-Skala Precipitation)
- ✅ EDA-Abschluss: Konsolidierte Findings-Tabelle + Feature-Ideen + Cleaning-Prognose

### Analyse-Notebooks (6 Notebooks · 66 Findings)
- ✅ `03_analysis_0-overview.ipynb` — Zentrale Findings, Kernfragen, Executive Summary, Report-Auswahl
- ✅ `03_analysis_1-target.ipynb` — Delay-Verteilung, OTP 87, Cancellations, lf_clean-Strategie (13 Findings)
- ✅ `03_analysis_2-network.ipynb` — Netzveränderungen 2023–2025, Hotspots, Versorgungsqualität (9 Findings)
- ✅ `03_analysis_3-temporal.ipynb` — Stunde, Wochentag, Monat, Saison (10 Findings)
- ✅ `03_analysis_4-spatial.ipynb` — Haltestellen, Stadtkreise, Linien (11 Findings)
- ✅ `03_analysis_5-meteo.ipynb` — Regen, Wind, Schnee, Temperatur (9 Findings)
- ✅ `03_analysis_6-events.ipynb` — Feiertage, Events, Eventgrösse (6 Findings)

### Zentrale Analysefragen — beantwortet
- ✅ Wo entstehen Verspätungen? → Periphere Aussenkorridore (K11/K12), nicht zentrale Knotenpunkte
- ✅ Wann? → Peak 21h (Events), Donnerstag, November — kein Morgenrush
- ✅ Wetter → Schnee +54s stärkster Effekt; geografisch trennbar von Regen
- ✅ Events → Grosse Events +10.5s (primär Abend 18–22h); Feiertage −9.9s (bester Tag-Typ)
- ✅ Extremfälle → OTP 87 %; 71,5 % aller Halte akkumulieren Delay; Linie E separat

### Visualisierungen — erstellt
- ✅ Heatmap Verspätungen nach Tageszeit und Wochentag (L11 / alle Linien)
- ✅ Geografische Hotspot-Karten (Haltestellen, Stadtkreise — Plotly Mapbox)
- ✅ Zeitreihe Verspätungen 2023–2025 (Rolling Average, alle Linien)
- ✅ Event-Tage vs. normale Tage — Stundenauflösung
- ✅ Netzveränderungen 2023→2025 — Choropleth nach Stadtkreis
- ✅ Wetter-Effekte — Schnee/Regen nach Linie und Stadtkreis

---

## Phase 3 — Feature Engineering & Vorbereitung ✅ ABGESCHLOSSEN

### Cleaning-Architektur
- ✅ `src/zh_tram_flow/cleaning.py` erstellt — strukturelle Pipeline + Meteo-Imputation
- ✅ `02_preparation.ipynb` aufgebaut — Split-Strategie dokumentiert
- ✅ lf_clean-Strategie definiert (canceled=False, stop_sequence>1, kein L-E/L50/L51, departure_delay/delay_delta maskiert für Nov 14–Dez 23 2025 — arrival_delay clean)
- ✅ `02_preparation.ipynb` ausgeführt: strukturelles Cleaning auf Rohdaten
- ✅ Train/Test-Split ausgeführt — 2025 als Test-Jahr (temporal, kein Shuffle)
- ✅ Meteo-Imputation (Forward/Backward Fill) auf Train + Test
- ✅ Cleaning-Report: Zahlen in Notebook dokumentiert

### Feature Engineering (Kandidaten aus Analyse-Phase)

**Priorität 1 — Muss ins Modell**

| Feature | Begründung |
|:---|:---|
| `hour` | Stärkster temporaler Prädiktor — 21h=+11.7s (F-TEMP-01) |
| `day_of_week` | Do 60.4s vs. So 48.4s (F-TEMP-02) |
| `month` / `season` | November-Peak; Winter beste Jahreszeit (F-TEMP-05/06) |
| `line_name` | L11 68.7s, Linie E separat (F-SPAT-05) |
| `stop_name` (Target-Encoding) | Stärkster räumlicher Prädiktor (F-SPAT-01) |

**Priorität 2 — Wichtig, verfügbar**

| Feature | Begründung |
|:---|:---|
| `has_snow` | +54s, OTP −10.9pp — stärkster Wetter-Effekt (F-WEAT-01) |
| `precipitation` (kontinuierlich) | Dosis-Wirkung messbar, r=0.036 (F-WEAT-02) |
| `is_holiday` | Stärkstes negatives Signal −9.9s (F-EVNT-01) |
| `event_weight × hour` | Interaktion wichtiger als Haupteffekt (F-EVNT-03) |
| `district_nr` | K11/K12 als High-Risk-Marker (F-SPAT-03) |

**Priorität 3 — Interessant, Vorsicht**

| Feature | Begründung |
|:---|:---|
| `gtfs_year` | Strukturbruch Dez 2023; schwaches Signal +0.5s (F-NET-03) |
| `n_stops_line` | Linienlänge als Proxy für Peripheral-Effekt (F-SPAT-09) |
| `prev_trip_delay` | Kaskadenindikator via trip_id (F-NET-07) |
| `hour × is_weekend` | Nacht-/Partyverkehr Fr/Sa 0–3h (F-TEMP-10) |

**Entfernt**

| Feature | Grund |
|:---|:---|
| ~~`is_windy`~~ | NaN — nie befüllt (F-WEAT-03) |

- ✅ Encoding-Entscheidung: LightGBM native Categorical für `stop_name`, `line_name`, `event_type`, `season`
- ✅ `train_features.parquet` + `test_features.parquet` exportiert (55.5M / ~30 M Zeilen, inkl. Nov/Dez 2025)
- ✅ `train_final.parquet` + `test_final.parquet` exportiert (ML-ready · leaky Spalten entfernt)
- ✅ **Feature-Count:** v1 = 32 Features · v2 = 34 Features (+prev_trip_delay, +stop_sequence_pct)

---

## Phase 4 — Modellierung ✅ ABGESCHLOSSEN

### Modell-Entscheidung
> LightGBM — native Categorical Support, schnell auf großen Datensätzen, gradient boosting für nicht-lineare Effekte

### Insights-Report (`04_insights.ipynb`) ✅
- ✅ Dramaturgie: 7 Abschnitte (Netzstruktur → OTP → Geo → Temporal → Meteo → Events → Netz)
- ✅ Alle Texte im Bullet-Style — fette Kategorien, Zahlen als Bullets
- ✅ Neue Plots: Delay Delta Timeline, Arrival vs. Departure, District Delay Choropleth
- ✅ Wetter-Karten mit vmax=60 (gleiche Farbskala Schnee/Regen)
- ✅ Fahrplanwechsel-Narrative korrigiert (Dez 2023 / Dez 2025)
- ✅ Plotly-Renderer auf `notebook_connected` gesetzt — HTML-Export-kompatibel
- ✅ HTML-Export: `public/index.html` (narrativer 3-Ebenen-Report · alle Plotly-Karten sichtbar)

### Baseline (`06_prediction_1-baseline.ipynb`) ✅
- ✅ Grand Mean Baseline: 50.6s MAE
- ✅ Hour Mean Baseline: 50.5s MAE
- ✅ Line Mean Baseline: 50.4s MAE
- ✅ **Stop Mean Baseline: 50.0s MAE — definiert als Benchmark**

### LightGBM v1 (`06_prediction_2-model.ipynb`) ✅
- ✅ Temporaler Validation-Split: 2023–Jun 2024 Train / Jul–Dez 2024 Validation
- ✅ 5 native Categorical Cols (LightGBM nativ)
- ✅ Early Stopping nach 50 Runden — beste Iteration: 481
- ✅ Val MAE: 49.0s · **Test MAE: 45.7s** (Baseline −4.3s ✅)
- ✅ Modell gespeichert: `data/models/lgbm_v1.txt` + `lgbm_v1_meta.json`
- ✅ Test-Predictions: `data/processed/test_predictions.parquet`

### Evaluation (`06_prediction_3-evaluation.ipynb`) ✅
- ✅ Metriken: Test MAE 45.7s · RMSE · OTP — Modell vs. Baseline-Tabelle
- ✅ Residuals-Verteilung — MBE +8,3 s (Modell unterschätzt systematisch)
- ✅ Live-Szenario: Di 17h · Paradeplatz · L11 · Regen → **52s**
- ✅ Abschluss-Tabelle: Modell vs. alle Baselines
- ✅ Fehleranalyse: MAE nach Stunde / Linie / Wetter / Monat
- ✅ Feature Importance (Gain) — schließt Kreis Analyse → Modell
- ✅ Predicted vs. Actual (Hexbin) — Bias visuell greifbar

### LightGBM v2 + Kaskadenfeature (`06_prediction_4-model_v2.ipynb`) ✅
- ✅ Feature Engineering: `prev_trip_delay` (Kaskadenindikator) + `stop_sequence_pct` — **34 Features total**
- ✅ Export: `train_final_v2.parquet` + `test_final_v2.parquet` (inkl. Nov/Dez 2025)
- ✅ Training: LightGBM v2 — identische Hyperparameter, erweitertes Feature-Set
- ✅ **Test MAE: 18,56 s · MBE −0,69 s** — −63% vs. Stop Mean Baseline (50.0s)
- ✅ Feature Importance — `prev_trip_delay` in Top-2 (nach `stop_name`) — schließt Kreis zur Analyse
- ✅ Bias-Kalibrierung: Isotonic Regression → MBE von +8,3 s (v1) auf −0,69 s (v2)
- ✅ Export: `lgbm_v2.txt` + `lgbm_v2_meta.json` + `test_predictions_v2.parquet`
- ⏭️ SHAP-Werte — nicht ausgeführt (Aufwand/Nutzen abgewogen, kein Optuna)

### Simulation & Empfehlungen
- ✅ `06_prediction_6-dwell_simulator.ipynb` — Dwell-Time binär (0/60s), Konfundierung r=+0.16 dokumentiert, F-SIM-01–04
- ✅ `06_prediction_7-recommendations.ipynb` — Risikomatrix Stop×Linie×Kontext, Empfehlungskarte, F-REC-01–04

### Modellvergleich — XGBoost Robustheits-Check ✅
- ✅ XGBoost Training — gleiche v2-Features, identischer Split, `enable_categorical=True`
  → val MAE ~21.4s (150 Runden, >90 Min Trainingszeit auf 85M Zeilen)
- ✅ **Fazit: LightGBM klar überlegen** — schneller, besser, native Categorical
- ✅ Ergebnis dokumentiert in `presentation-v3.html` Slide 18
- ⏭️ Vollständige Metriken-Tabelle in `06_prediction_5-comparison.ipynb` — Skeleton vorhanden

---

## Phase 5 — Dashboard & Präsentation · NÄCHSTE PHASE

### Tooling-Entscheidung
- [ ] Dash + Plotly vs. Streamlit vs. Tableau
- [ ] Entscheidung nach Phase 2 Erfahrung

### Interface
- [ ] Historik: Heatmaps Stadtkreise und Zeitverläufe
- [ ] Predictive: What-if Eingabemaske
  (z.B. Freitag + Regen + Spiel im Letzigrund → Erwarteter Delay)

---

## Offene Entscheidungen

| Entscheidung | Status | Notiz |
| :--- | :--- | :--- |
| Split-Strategie | ✅ entschieden | 2025 als Test-Jahr — temporal, kein Shuffle |
| Geo-Bibliothek | ✅ entschieden | Plotly Mapbox (Folium verworfen) |
| Modell-Kandidat | ✅ Richtung klar | LightGBM / GradientBoosting — Interaktionen wichtig |
| Target-Encoding für `stop_name` | offen | n-Threshold festlegen, Overfitting-Risiko prüfen |
| Dashboard-Tooling | offen | Dash + Plotly vs. Streamlit — Entscheidung in Phase 5 |
