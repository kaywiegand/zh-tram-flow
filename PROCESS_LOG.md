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
| Status | 🟡 Phase 1 — Setup & Dateneinstieg |
| Nächster Schritt | Datenchecks in `01_exploration.ipynb` starten |
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

## Aktueller Stand

**Phase 0 (Data Engineering):** ✅ Abgeschlossen — in `sf_data-research`  
**Phase 1 (Setup & Dateneinstieg):** 🟡 In Arbeit  

**Nächster konkreter Schritt:**  
`01_exploration.ipynb` öffnen, Master-Datensatz vollständig laden,
erste Verteilungen und Datenqualitätschecks durchführen.
