# PROCESS_LOG.md – Zürich Tram Flow

> Projektverlauf und AI-Kontext-Einstieg.
> Dieses File ist der Einstiegspunkt für neue Claude-Sessions.

---

## Projekt-Übersicht

| Feld | Inhalt |
| :--- | :--- |
| Projektname | Zürich Tram Flow |
| Repo | `zh-tram-flow` |
| Typ | DANSC (EDA + Modellierung + Dashboard) |
| Erstellt | 2026-05-11 |
| Status | 🟢 Phase 3 — Cleaning & Vorbereitung (02_preparation aufgebaut) |
| Nächster Schritt | `02_preparation.ipynb` ausführen — Cleaning, Split, Feature Export |
| Datenbasis | `sf_data-research` — Phase 0 abgeschlossen |
| Stack | Python · Polars · Pandas · GeoPandas · Plotly · Folium |

---

## Datenbasis auf einen Blick

Die gesamte Data-Engineering-Phase ist in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) dokumentiert.

**Master-Datensatz:** `data/raw/zh-tram-data-master.parquet`
- ~88 Mio. Zeilen · 24 Spalten · ~460 MB
- Enthält: IST-Verspätungsdaten + GTFS-Haltestellen + Meteo-Stundenwerte + Events
- Zeitraum: 2023–2025 · Betreiber: VBZ Zürich · Produkt: Tram

**GTFS-Referenztabellen:** `data/raw/gtfs/`
- 9 Parquet-Dateien (Stops, Routes, Shapes, Trips — Tram + Gesamtnetz)
- Referenzjahr: 2024

---

## Verlauf

### 2026-05-11 — Projekt aufgesetzt (wgnd-scaffolding)

- Projektstruktur mit `wgnd-scaffolding` generiert (`--slug zh-tram-flow --type DAN`)
- Git-Repo initialisiert: `git@github.com:kaywiegand/zh-tram-flow.git`
- Scaffolding in dieser Session grundlegend überarbeitet (Details → `wgnd-scaffolding/PROCESS_LOG.md`):
  - `--slug` Pflichtfeld, Ordner = Slug, `src/zh_tram_flow/` mit Unterstrichen
  - `PROCESS_LOG.md`, `ROADMAP.md`, `CLAUDE.md` automatisch erstellt
  - Repo-Naming Convention festgelegt: kein Typ-Prefix, Hyphens als Standard

### 2026-05-11 — Startpunkt aus sf_data-research übertragen

**Was wurde gemacht:**
- `README.md` vollständig neu geschrieben — Projektbeschreibung aus sf_data-research übernommen,
  Struktur auf Scaffolding-Layout angepasst, Python-Imports korrigiert (Bindestriche → Unterstriche),
  Verweis auf sf_data-research und wgnd-toolkit ergänzt
- `ROADMAP.md` aktualisiert — Phase 0 (Research) als abgeschlossen markiert,
  Phasen 1–4 mit konkreten Analyse-Fragen, Visualisierungen, Modellierungs-Tasks und
  offenen Entscheidungen aus sf_data-research übernommen
- `notebooks/00_introduction.ipynb` gefüllt:
  - Project Facts, Scenario, Mission, zentrale Fragen
  - Methode & Metriken
  - Sektion "Datenbasis & Data Engineering" mit Verweis auf sf_data-research,
    Übersicht aller Notebooks und Entscheidungstabelle
  - Vollständiges Data Dictionary (24 Spalten mit Typ, Quelle, Beschreibung)
  - GTFS-Referenztabellen dokumentiert
  - Setup-Zellen mit korrekten Imports (`zh_tram_flow`)
  - Dateicheck-Zellen (Schema, Zeilenanzahl, GTFS-Übersicht)
- `data/raw/zh-tram-data-master.parquet` kopiert aus `sf_data-research/data/interim/vbz/vbz_master.parquet`
- `data/raw/gtfs/` kopiert aus `sf_data-research/data/interim/vbz/gtfs/` (9 Parquet-Dateien)

**Offene Entscheidungen für Phase 2 (aus sf_data-research übernommen):**

| Entscheidung | Kontext |
| :--- | :--- |
| Dashboard-Tooling | Dash + Plotly vs. Streamlit vs. Tableau — nach EDA entscheiden |
| Zeitreihe vs. klassisches ML | Erst nach EDA sinnvoll zu entscheiden |
| Split-Strategie | Jahres-Split als Einstieg (2025 als Test-Jahr) — in Phase 3 verfeinern |
| Geo-Bibliothek für Dashboard | Folium (interaktiv, einfach) oder Plotly (performanter) |

---

### 2026-05-12 — EDA abgeschlossen (`01_exploration.ipynb`)

**Was wurde gemacht:**
- `01_exploration.ipynb` vollständig aufgebaut und finalisiert
- Sections: Basic Stats · Completeness (C1–C4) · Integrity (I1–I5) · Distribution ·
  Correlations (R1–R5) · Outlier Detection (O1–O5) · Features Inspection · Key Findings
- Datenqualitäts-Findings dokumentiert: 16 Befunde, topic-gruppiert mit "Vor Split?"-Spalte
- Modellierungs-Entscheidung: XGBoost (schwache lineare Korrelationen → Schwellenwert-Effekte)
- Feature-Ideen-Tabelle erstellt: 15 Features (Zeit, Wetter-Flags, Kategoriale, Interaktionen)
- Cleaning-Prognose: ~1,7 Mio. Zeilen (~2%) strukturelle Reduktion
- Sampling-Strategie dokumentiert (`gather_every(2)` + `sample(fraction=0.1)`, ~5%)
- `ROADMAP.md` aktualisiert: Phase 1 ✅, Phase 2 AKTUELL, XGBoost + Cleaning-Architektur
- `BACKLOG.md` ergänzt: wgnd-toolkit #2/#3, dansc_zh-tram-flow #2/#3

**Technische Entscheidungen:**
- Split-Strategie: 2023–2024 Train / 2025 Test (temporal, kein Random Shuffle)
- Delay-Cleaning-Grenze: `|delay| > 3.600s` (±1h) als Rausfilter-Schwelle
- Linien 50/51/E behalten (Sonder-/Nachtlinien — Entscheidung vertagt)
- `wgnd.inspect_correlations` auf Sample — Korrelationsmatrix aus ~4.5 Mio. Zeilen

---

### 2026-05-13 — Preparation aufgebaut (`02_preparation.ipynb` + `cleaning.py`)

**Was wurde gemacht:**
- `src/zh_tram_flow/cleaning.py` neu erstellt:
  - 6 strukturelle Cleaning-Funktionen (Polars LazyFrame)
  - `structural_cleaning_pipeline()` — lazy, vor dem Split
  - `impute_meteo_rolling()` — Forward/Backward Fill, nach dem Split
  - `report_step()` für Cleaning-Reporting
- `02_preparation.ipynb` komplett neu gebaut (vorher: leeres Scaffold):
  - Intro mit Pipeline-Diagramm + Leakage-Prinzip
  - EDA-Findings als Cleaning-Agenda
  - Phase 1: strukturelles Cleaning via `cleaning.py` → `interim/zh-tram-structural-clean.parquet`
  - Phase 2: Temporal Split mit Strategie-Erklärung → `interim/train_raw.parquet` + `test_raw.parquet`
  - Phase 3: Meteo-Imputation (Forward/Backward Fill) → `processed/train_prepared.parquet`
  - Phase 4: Zeitfeatures + Wetter-Flags → `processed/train_features.parquet`
- `01_exploration.ipynb` finalisiert: FutureWarning gefixt, Beschriftungen bereinigt, Distribution-Scale-Fix

**Notebook noch nicht ausgeführt:** `02_preparation.ipynb` ist aufgebaut aber noch nicht auf den
echten Daten gelaufen — Cleaning-Zahlen sind Prognosen aus der EDA.

---

## Aktueller Stand

**Phase 0 (Data Engineering):** ✅ Abgeschlossen — in `sf_data-research`  
**Phase 1 (Setup & Dateneinstieg):** ✅ Abgeschlossen  
**Phase 2 (EDA & Analyse):** ✅ Abgeschlossen — `01_exploration.ipynb` fertig  
**Phase 3 (Cleaning & Vorbereitung):** 🟡 In Arbeit — Struktur steht, Ausführung ausstehend  

**Nächster konkreter Schritt:**  
`02_preparation.ipynb` ausführen — Cleaning-Pipeline auf Rohdaten, Split durchführen,
Feature-Tabellen exportieren. Danach `03_analysis.ipynb` anlegen.
