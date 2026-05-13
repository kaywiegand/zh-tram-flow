# Zürich Tram Flow
### Verspätungsanalyse und Vorhersage im Tramnetz Zürich

> **Typ:** DANSC &nbsp;|&nbsp; **Erstellt:** 2026-05-11 &nbsp;|&nbsp; **Version:** 0.2.0  
> **Status:** EDA ✅ · Preparation aufgebaut · Modellierung geplant
> **Datenbasis:** [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) — Research & Data Engineering Phase

---

## Inhalt

1. [Kurzbeschreibung](#1-kurzbeschreibung)
2. [Die Idee](#2-die-idee)
3. [Warum Zürich — warum Tram?](#3-warum-zürich--warum-tram)
4. [Das Problem](#4-das-problem)
5. [Zentrale Fragen](#5-zentrale-fragen)
6. [Projekt-Phasen](#6-projekt-phasen)
7. [Daten & Quellen](#7-daten--quellen)
8. [Business Cases & KPIs](#8-business-cases--kpis)
9. [Motivation & Portfolio-Mehrwert](#9-motivation--portfolio-mehrwert)
10. [Projektstruktur](#projektstruktur)
11. [Schnellstart](#schnellstart)

---

## 1. Kurzbeschreibung

Verspätungen im öffentlichen Nahverkehr sind ärgerlich — für Menschen und für das System.
Dieses Projekt zeigt, was mit offenen Daten und moderner Datenanalyse möglich ist:
Wo entstehen Probleme, warum — und wie lässt sich das vorhersagen?

Als Fallbeispiel dient das Tramnetz Zürich (VBZ). Das Modell soll auch als Blaupause
für andere Städte wie Berlin dienen, die noch kaum Daten öffentlich zur Verfügung stellen.

---

## 2. Die Idee

Aufbau einer vollständigen Datenpipeline zur Analyse und Vorhersage von Verspätungen
im städtischen ÖPNV — vom aufbereiteten Master-Datensatz bis zum interaktiven Dashboard.

**Kernziel:** Zeigen, was Daten im Alltag bewirken können — konkret, nachvollziehbar, menschlich relevant.

---

## 3. Warum Zürich — warum Tram?

**Zürich als Datenbasis:**
- Außergewöhnlich gute Open-Data-Landschaft (Stadt, VBZ, Wetter, Geodaten)
- Hochattraktiver ÖV mit entsprechend hoher Nutzung → gute Analysegrundlage
- Kann als Inspiration und Benchmark für deutsche Städte dienen

**Tram als Fokus:**
- Tram fährt im offenen Stadtverkehr — beeinflusst durch Autos, Fußgänger, Wetter, Topografie
- Kein geschlossenes System wie S-Bahn → mehr und interessantere Einflussfaktoren
- Macht die Analyse für Betreiber und Stadtplanung besonders relevant

**Und Berlin?**
Berlin wäre das emotionalere Beispiel — aber die Datenlage lässt eine solche Analyse
aktuell nicht zu. Das Ziel: dieses Projekt als Anstoß, das zu ändern.

---

## 4. Das Problem

Verspätungen kennt jeder. Aber selten fragt man: **Warum passiert das eigentlich — und
könnte man es verhindern?**

Ein paar Situationen, die jeder kennt:
- Nach dem Konzert oder Fußballspiel stundenlang im Stau — der schöne Abend versaut
- Regelmäßig zu spät beim Arzt oder zur Arbeit — Stress, Frust, schlechte Laune
- Das Tram kommt einfach nicht — und keine verlässliche Info, wann es endlich kommt

Hinter diesen Momenten stecken oft vermeidbare Engpässe: bestimmte Haltestellen,
bestimmte Uhrzeiten, bestimmte Wetterbedingungen. Genau das will dieses Projekt sichtbar machen.

---

## 5. Zentrale Fragen

- Wo entstehen Verspätungen im Tramnetz — und zu welchen Zeiten?
- Welche Einflussfaktoren spielen die größte Rolle? (Wetter, Topografie, Tageszeit, Events)
- Lassen sich Verspätungen vorhersagen, bevor sie entstehen?
- Welche Haltestellen oder Streckenabschnitte lösen Kettenreaktionen aus?
- Was kann ein Betreiber oder eine Stadt konkret besser machen?

---

## 6. Projekt-Phasen

Der Scope ist bewusst in aufeinander aufbauende Versionen gestaffelt — um den MVP
sicher im Projektzeitrahmen zu erreichen und Raum für Erweiterungen zu lassen.

#### Phase 0 – "Data Foundation" ✅ (in `sf_data-research` abgeschlossen)
- Data Engineering: Pipeline für 94 Mio. Zeilen IST-Daten, GTFS, Meteo, Events
- Master-Datensatz `zh-tram-data-master.parquet` (24 Spalten) — vollständig und validiert
- Datenstrategie, Filter-Entscheidungen und Datenqualität dokumentiert
- Tooling: Polars (4× schneller als Pandas), GeoPandas, Visualisierungs-Benchmark

#### MVP – "The Foundation"
- **EDA & Reporting:** Historische Analyse der Hotspots (Kreise/Haltestellen) und Korrelationsmatrix (Wetter vs. Delay)
- Einsatz des eigenen **wgnd-toolkit** und **wgnd-scaffolding**

#### v1.1 – "The Intelligence"
- Definition der Metriken und Methoden
- **Modellierung:** Training eines oder mehrerer Modelle zur Vorhersage von Verspätungen basierend auf Wetter, Zeit und Events
- **Evaluation:** Validierung der Vorhersagegenauigkeit pro Linie und Stadtteil

#### v1.2 – "The Interface"
- **Interaktives Dashboard:**
  - Tooling: Tableau vs. Dash & Plotly (Entscheidung im Projektverlauf)
  - Historik: Heatmaps der Stadtkreise und Zeitverläufe
  - Predictive: "What-if"-Eingabemaske — z.B. *Freitag + Regen + Spiel im Letzigrund → Erwarteter Delay*

#### v1.3 – "Individual Traffic Impact"
- Ergänzung der Verkehrsdichte aus Zählstellendaten (Induktionsschleifen Zürich) als zusätzliches Feature
- Aufzeigen des Zusammenspiels zwischen Tram-Verspätungen und Individualverkehr

---

## 7. Daten & Quellen

**Analysezeitraum:** 2023 – 2025

| Datentyp | Quelle | Strategie | Datei | Format |
| :--- | :--- | :--- | :--- | :--- |
| Verkehrsdaten (IST) | [opentransportdata.swiss](https://data.opentransportdata.swiss) | 2023–25, VBZ & Tram, Format v1 | `data/raw/zh-tram-data-master.parquet` | .parquet |
| Wetterdaten | [Stadt Zürich OGD](https://data.stadt-zuerich.ch/dataset/ugz_meteodaten_stundenmittelwerte) | Stundenmittelwerte, Stampfenbachstrasse & Mythenquai | → im Master-Datensatz | .parquet |
| Geodaten (GTFS) | [ZVV / Zürich OGD](https://data.stadt-zuerich.ch/dataset/vbz_fahrplandaten_gtfs) | Haltestellen-Koordinaten, Stadtkreis-Zuordnung | `data/raw/gtfs/` | .parquet |
| Eventdaten | Manueller Crawl | 5 Kategorien, >1.000 Besucher, Gewichtung 1–3 | → im Master-Datensatz | .parquet |

**Zur Datenmenge (Research-Phase):**
- 36 ZIP-Dateien über 3 Jahre → ca. **38 GB** komprimiert
- Entpackt: **500–720 GB** (schweizweite CSV-Rohdaten)
- Nach Filterung auf VBZ & Tram → **~94 Mio. Zeilen · 1,44 GB** (1.096 Parquet-Dateien)
- Master-Datensatz: **24 Spalten** — IST + GTFS + Meteo + Events, Left-Join (kein Datenverlust)

> Vollständige Datenbeschreibung: [`data/raw/gtfs/`](data/raw/gtfs/) und `notebooks/00_introduction.ipynb` → Data Dictionary

---

## 8. Business Cases & KPIs

### Für den Betreiber (VBZ / Operative Exzellenz)
Ziel: Pünktlichkeit verbessern, Ressourcen gezielter einsetzen

| KPI | Beschreibung |
|---|---|
| On-Time Performance (OTP) | Anteil Fahrten < 2 Min Verspätung |
| Bottleneck Score | Haltestellen, die systemweite Folgeverspätungen auslösen |
| District Delay Index | Durchschnittliche Verspätung pro Stadtkreis |
| Recovery Time | Wie lange braucht das Netz nach einer Störung zur Stabilisierung? |
| Peak Load Variance | Auslastungsschwankungen zu Stoßzeiten |

### Für die Stadtplanung (Infrastruktur & Resilienz)
Ziel: Schwachstellen im Netz identifizieren, Investitionen priorisieren

| KPI | Beschreibung |
|---|---|
| Elevation Impact Ratio | Korrelation zwischen Streckensteigung und wetterbedingten Verspätungen |
| Hotspot Heatmap | Geografische Verteilung der Verspätungsdichte (GIS-basiert) |
| Weather Sensitivity Score | Wie stark reagiert eine Linie auf Regen, Schnee, Glatteis? |
| Infrastructure Bottleneck Index | Physische Engpässe mit regelmäßigem Verspätungsmuster |
| Event Impact Score | Verspätungsanstieg rund um Großveranstaltungen |

### Für Fahrgäste (Citizen Experience & Transparenz)
Ziel: Weniger Stress, mehr Verlässlichkeit im Alltag

| KPI | Beschreibung |
|---|---|
| Prediction Accuracy (MAE) | Vorhersagegenauigkeit pro Stadtteil oder Linie |
| Wait Time Variance | Wo schwanken Wartezeiten am stärksten? |
| Realtime Reliability Score | Übereinstimmung von Echtzeitanzeige und tatsächlicher Ankunft |
| Comfort Window | Anteil Fahrten mit planbarem Puffer für Anschlüsse |

### Gesellschaftlicher Impact (Nachhaltigkeit & Stadtqualität)
Ziel: ÖPNV attraktiver machen, Individualverkehr reduzieren

| KPI | Beschreibung |
|---|---|
| Modal Shift Potential | Geschätzte CO₂-Einsparung bei x% Verlagerung vom Auto |
| SDG 11 Readiness Score | Erfüllungsgrad der UN-Ziele für nachhaltigen Stadtverkehr |
| Noise & Emission Hotspots | Kritische Orte mit hoher Verkehrsbelastung und Alternativpotenzial |
| Livability Index Contribution | Einfluss von ÖPNV-Qualität auf die Lebensqualität pro Stadtkreis |

---

## 9. Motivation & Portfolio-Mehrwert

**Warum dieses Thema?**
Data Science und KI wirken für viele abstrakt. Dieses Projekt macht den Mehrwert
greifbar — an einem Thema, das jeden täglich betrifft.

**Impact — warum das mehr ist als ein Datenprojekt:**
- **Feel-Good City:** Verlässlicher ÖPNV verbessert direkt die Lebensqualität im Stadtraum
- **Nachhaltigkeit:** Attraktiverer ÖPNV reduziert Individualverkehr — weniger CO₂, weniger Lärm
- **Emotionaler Alltag:** Verspätungen erzeugen echten Stress — Frust, Aggression, verpasste Termine
- **Städtebau:** Schwachstellen im Netz identifizieren und Investitionen gezielt steuern
- **SDG 11:** Beitrag zu den UN-Zielen für nachhaltige Städte und Gemeinden

**Was steckt technisch drin?**
- Data Engineering: Ingestion, Cleaning, Wrangling großer Datenmengen (in `sf_data-research`)
- Explorative Analyse (EDA) & Reporting
- Geodaten-Integration & Visualisierung
- Zeitreihenanalyse & Machine Learning (Vorhersagemodell)
- Interaktive Web-App als Abschluss

**Das größere Bild:**
Zürich dient als Referenzmodell — für Städte wie Berlin, die ihre Datenpotenziale
noch nicht ausschöpfen. Das Ziel ist nicht nur ein Portfolio-Projekt, sondern ein
konkreter Anstoß: Bessere Daten = bessere Städte = besserer Alltag für alle.

---

## Projektstruktur

```
zh-tram-flow/
│
├── pyproject.toml          # Paketkonfiguration & Dependencies
├── .gitignore
├── .python-version         # Python-Version für uv (3.10)
├── README.md
├── ROADMAP.md
├── PROCESS_LOG.md
├── CLAUDE.md
│
├── data/                   # NICHT in Git! (.gitignore)
│   ├── raw/                # Eingangsdaten aus sf_data-research — NIEMALS verändern!
│   │   ├── zh-tram-data-master.parquet   # Master: 94 Mio. Zeilen, 24 Spalten
│   │   └── gtfs/                         # GTFS-Referenztabellen (Haltestellen etc.)
│   ├── interim/            # Zwischenstands (gefiltert, teilbereinigt)
│   └── processed/          # Finale, analysefertige Daten
│
├── notebooks/
│   ├── 00_introduction.ipynb    # Projektkontext, Data Dictionary, Datenbeschreibung
│   ├── 01_exploration.ipynb     # EDA: Completeness, Integrity, Distribution, Correlations, Outlier
│   ├── 02_preparation.ipynb     # Cleaning-Pipeline, Train/Test-Split, Feature Engineering
│   ├── 03_analysis.ipynb        # Modellierung & Evaluation (XGBoost)
│   └── 04_insights.ipynb        # Reporting & Dashboard-Vorbereitung
│
├── src/
│   └── zh_tram_flow/       # Das Python-Paket
│       ├── __init__.py
│       ├── config.py        # Zentrale Pfade & Konstanten
│       ├── settings.py      # Plot-Theme, Farben, Logging
│       ├── cleaning.py      # Cleaning-Pipeline: strukturell + Meteo-Imputation
│       ├── notebook.py      # Notebook-Helpers
│       ├── utils.py         # Hilfsfunktionen
│       ├── utils_polars.py  # Polars-spezifische EDA-Helpers
│       ├── data/
│       ├── features/
│       ├── visualization/
│       └── analytics/
│
├── tests/
│   ├── test_data.py
│   └── test_features.py
│
└── reports/
    ├── figures/             # Exportierte Plots
    ├── tables/              # Exportierte Tabellen
    └── index.html           # Executive Summary HTML
```

---

## Schnellstart

### 1. Repository klonen / Ordner öffnen

```bash
# In VS Code: Datei -> Ordner öffnen -> diesen Projektordner wählen
```

### 2. uv installieren (einmalig, falls noch nicht vorhanden)

```bash
pip install uv
```

### 3. Virtuelle Umgebung erstellen & aktivieren

```bash
uv venv
source .venv/bin/activate   # Mac / Linux
# .venv\Scripts\activate    # Windows
```

### 4. Dependencies + Projektpaket installieren

```bash
uv pip install -e ".[dan]"
```

> Das `-e` steht für "editable" — `src/zh_tram_flow/` wird direkt aus dem Quellcode importiert.

### 5. Jupyter Kernel registrieren

```bash
python -m ipykernel install --user --name zh-tram-flow --display-name "Python (zh-tram-flow)"
```

### 6. Los geht's!

Öffne `notebooks/00_introduction.ipynb` für Projektkontext und Datenbeschreibung.

---

## Konfiguration

### Pfade (`src/zh_tram_flow/config.py`)

```python
from zh_tram_flow.config import PATHS

PATHS["raw"]       # data/raw/
PATHS["processed"] # data/processed/
PATHS["figures"]   # reports/figures/
```

### Plotting einrichten

```python
from zh_tram_flow.settings import setup_plotting, logger

setup_plotting()
logger.info("Notebook gestartet")
```

---

## Tests ausführen

```bash
pytest
pytest --cov=src/zh_tram_flow --cov-report=term-missing
```

---

_Aufgebaut mit [wgnd-scaffolding](https://github.com/kaywiegand/wgnd-scaffolding) und [wgnd-toolkit](https://github.com/kaywiegand/wgnd-toolkit)._
_Datenbasis: [sf_data-research](https://github.com/kaywiegand/sf_data-research) — Research & Data Engineering Phase._
