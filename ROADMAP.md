# ROADMAP.md – Zürich Tram Flow

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
- ✅ Master-Datensatz `vbz_master.parquet` erstellt — 24 Spalten: IST + GTFS + Meteo + Events
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
- ✅ Correlations (R1–R5 Findings, Modellierungs-Fazit: XGBoost)
- ✅ Outlier Detection (O1–O5, Vor/Nach-Vergleich Delays, Log-Skala Precipitation)
- ✅ EDA-Abschluss: Konsolidierte Findings-Tabelle (topic-grouped) + Feature-Ideen + Cleaning-Prognose

### Zentrale Analysefragen
- [ ] Wo entstehen die meisten Verspätungen? (Haltestelle, Linie, Stadtkreis)
- [ ] Wann? (Tageszeit, Wochentag, Saison)
- [ ] Korrelation Verspätung ↔ Wetter (Regen, Temperatur, Wind)
- [ ] Korrelation Verspätung ↔ Events (Gewichtung 1–3)
- [ ] Ausreißer & Extremfälle identifizieren (Ausfälle, Kettenverspätungen)

### Visualisierungen
- [ ] Heatmap Verspätungen nach Tageszeit und Wochentag
- [ ] Geografische Hotspot-Karte (Stadtkreise, Haltestellen)
- [ ] Zeitreihe Verspätungen 2023–2025
- [ ] Event-Tage vs. normale Tage — visueller Vergleich

---

## Phase 3 — Cleaning & Vorbereitung · AKTUELL

### Cleaning-Architektur (aus EDA-Findings)
- ✅ `src/zh_tram_flow/cleaning.py` erstellt — strukturelle Pipeline + Meteo-Imputation
- ✅ `02_preparation.ipynb` aufgebaut — Phase 1–4 Struktur, Split-Strategie dokumentiert
- [ ] `02_preparation.ipynb` ausführen: strukturelles Cleaning auf Rohdaten
  - `|delay| > 3.600s` → rausfiltern
  - `bpuic > 100.000.000` → rausfiltern
  - `humidity > 100` → clip auf 100
  - Duplikate, Schedule/Delay-Mismatch
- [ ] Train / Test Split ausführen — 2025 als Test-Jahr (temporal, kein Shuffle)
- [ ] Meteo-Imputation (Forward/Backward Fill) auf Train + Test
- [ ] Cleaning-Report: tatsächliche Zahlen nach Ausführung dokumentieren

### Feature Engineering
- ✅ Zeitfeatures geplant: Stunde, Wochentag, Monat, `ist_hvz`, `ist_wochenende`
- ✅ Binäre Flags geplant: `hat_regen`, `hat_starkregen`, `hat_flut`, `is_canceled`
- ✅ Kategoriale Encodings geplant: line_name, district_name, event_size
- [ ] Encoding-Entscheidung: Label-Encoding vs. Target-Encoding für `line_name`
- [ ] `train_features.parquet` + `test_features.parquet` exportieren

---

## Phase 4 — Modellierung · GEPLANT

### Modell-Entscheidung (aus EDA-Findings)
> Wetter→Delay Korrelationen sind nicht-linear (max r=0.03) → XGBoost als primäres Modell

- [ ] Baseline-Modell definieren (einfachste sinnvolle Vorhersage)
- [ ] XGBoost Training & Evaluation
- [ ] Feature Importance analysieren
- [ ] Vorhersagegenauigkeit pro Linie und Stadtkreis
- [ ] Verhalten auf Event-Tagen prüfen

---

## Phase 5 — Dashboard & Präsentation · GEPLANT

### Tooling-Entscheidung
- [ ] Dash + Plotly vs. Streamlit vs. Tableau
- [ ] Entscheidung nach Phase 2 Erfahrung

### Interface
- [ ] Historik: Heatmaps Stadtkreise und Zeitverläufe
- [ ] Predictive: What-if Eingabemaske
  (z.B. Freitag + Regen + Spiel im Letzigrund → Erwarteter Delay)

---

## Offene Entscheidungen

| Entscheidung | Wann |
| :--- | :--- |
| Dashboard-Tooling | Phase 2 Ende |
| Split-Strategie final | Phase 3 Anfang |
| Geo-Bibliothek für Dashboard | Phase 2 Ende (nach EDA-Erfahrung) |
