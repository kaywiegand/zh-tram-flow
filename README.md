# Zürich Tram Flow
### Verspätungsanalyse und Vorhersage im Tramnetz Zürich

> **Typ:** DANSC &nbsp;|&nbsp; **Erstellt:** 2026-05-11 &nbsp;|&nbsp; **Version:** 0.4.0  
> **Status:** Analyse ✅ (55 Findings · 6 Notebooks) · Feature Engineering ✅ · Modellierung 🔄 (LightGBM v1 · MAE 45.7s)  
> **Datenbasis:** [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) — Research & Data Engineering Phase

---

## Inhalt

1. [Kurzbeschreibung](#1-kurzbeschreibung)
2. [Die Idee](#2-die-idee)
3. [Warum Zürich — warum Tram?](#3-warum-zürich--warum-tram)
4. [Das Problem](#4-das-problem)
5. [Was die Daten zeigen](#5-was-die-daten-zeigen)
6. [Zentrale Fragen](#6-zentrale-fragen)
7. [Projekt-Phasen](#7-projekt-phasen)
8. [Daten & Quellen](#8-daten--quellen)
9. [Tech Stack](#9-tech-stack)
10. [Business Cases & KPIs](#10-business-cases--kpis)
11. [Motivation & Portfolio-Mehrwert](#11-motivation--portfolio-mehrwert)
12. [Projektstruktur](#projektstruktur)
13. [Schnellstart](#schnellstart)

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

## 5. Was die Daten zeigen

**93.9 Mio. Datenpunkte · 3 Jahre (2023–2025) · 16 Tramlinien · 55 Findings**

Die abgeschlossene Analyse-Phase liefert klare Antworten — und einige Überraschungen:

- **Verspätungen entstehen an der Peripherie, nicht im Zentrum.** Friedhof Enzenbühl (93.8s), Balgrist (85.2s) und Schwamendingen sind die Hotspots — nicht Central oder Paradeplatz, obwohl dort 14–15 Linien kreuzen.
- **Kein Morgenrush.** Das dominante Muster ist Feierabend + Events. Der Peak liegt bei 21h (67.9s, Abreisewelle nach Konzerten und Spielen). Donnerstag ist der schlechteste Wochentag — nicht Freitag.
- **Schnee ist der stärkste Einzeleinflussfaktor** — +54s, OTP −10.9 Prozentpunkte. Und geografisch klar trennbar von Regen: Schnee trifft Höhenlagen (Kreise 10/4/12), Regen trifft Flusstäler (Kreis 5).
- **Feiertage sind die besten Tage.** −9.9s gegenüber Normal. Der Rückgang des Berufsverkehrs überwiegt jeden Event-Effekt — kontraintuitiv, aber klar belegt.
- **Der größte Fahrplanwechsel in VBZ-Geschichte (Dez 2023) ist im Delay-Signal unsichtbar.** Netzweit nur +0.5s. Und: Die echten Erweiterungen zielten auf gut performende Kreise (K3/K8) — nicht auf die Problemkreise K11/K12.

> Alle 55 Findings: [`03_analysis_0-overview.ipynb`](notebooks/03_analysis_0-overview.ipynb)

---

## 6. Zentrale Fragen

- Wo entstehen Verspätungen im Tramnetz — und zu welchen Zeiten?
- Welche Einflussfaktoren spielen die größte Rolle? (Wetter, Topografie, Tageszeit, Events)
- Lassen sich Verspätungen vorhersagen, bevor sie entstehen?
- Welche Haltestellen oder Streckenabschnitte lösen Kettenreaktionen aus?
- Was kann ein Betreiber oder eine Stadt konkret besser machen?

---

## 7. Projekt-Phasen

Der Scope ist bewusst in aufeinander aufbauende Versionen gestaffelt — um den MVP
sicher im Projektzeitrahmen zu erreichen und Raum für Erweiterungen zu lassen.

#### Phase 0 – "Data Foundation" ✅ (in `sf_data-research` abgeschlossen)
- Data Engineering: Pipeline für 94 Mio. Zeilen IST-Daten, GTFS, Meteo, Events
- Master-Datensatz `zh-tram-data-master.parquet` (24 Spalten) — vollständig und validiert
- Datenstrategie, Filter-Entscheidungen und Datenqualität dokumentiert
- Tooling: Polars (4× schneller als Pandas), GeoPandas, Visualisierungs-Benchmark

#### MVP – "The Foundation" ✅ (Analyse-Phase abgeschlossen)
- **EDA & Reporting:** 55 Findings aus 6 Analyse-Notebooks — Hotspots, Zeitliches Muster, Wetter, Events, Netzveränderungen
- Einsatz des eigenen **wgnd-toolkit** und **wgnd-scaffolding**

#### v1.1 – "The Intelligence" 🔄 (in Arbeit)
- ✅ Feature Engineering: `train_final.parquet` / `test_final.parquet` (55.5M Zeilen · 32 Features)
- ✅ Baseline: Stop Mean MAE = 50.0s als Benchmark definiert
- ✅ LightGBM v1 trainiert: **Test MAE = 45.7s** (Baseline −4.3s · 481 Bäume · 32 Features)
- ✅ Insights-Report: 7 Abschnitte · Bullet-Style Texte · neue Plots (Delta, Choropleth, Wetter-Maps)
- 🔄 **Evaluation:** Fehleranalyse nach Linie, Stadtteil, Wetter, Rush-Hour ausstehend

#### v1.2 – "The Interface"
- **Interaktives Dashboard:**
  - Tooling: Tableau vs. Dash & Plotly (Entscheidung im Projektverlauf)
  - Historik: Heatmaps der Stadtkreise und Zeitverläufe
  - Predictive: "What-if"-Eingabemaske — z.B. *Freitag + Regen + Spiel im Letzigrund → Erwarteter Delay*

#### v1.3 – "Individual Traffic Impact"
- Ergänzung der Verkehrsdichte aus Zählstellendaten (Induktionsschleifen Zürich) als zusätzliches Feature
- Aufzeigen des Zusammenspiels zwischen Tram-Verspätungen und Individualverkehr

---

## 8. Daten & Quellen

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

## 9. Tech Stack

| Bereich | Tool |
|:---|:---|
| DataFrames (groß) | Polars |
| DataFrames (klein/geo) | Pandas · GeoPandas |
| Visualisierung | Plotly (Charts + interaktive Karten) |
| Notebooks | Jupyter |
| Paketierung | wgnd-toolkit · wgnd-scaffolding |
| Laufzeitumgebung | uv · Python 3.10 |

---

## 10. Business Cases & KPIs

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

## 11. Motivation & Portfolio-Mehrwert

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
│   ├── 00_introduction.ipynb          # Projektkontext, Data Dictionary, VBZ-Linienfarben
│   ├── 01_exploration.ipynb           # EDA: Verteilung, Integrität, Korrelation, Ausreisser
│   ├── 02_preparation.ipynb           # Bereinigung, Train/Test-Split, Feature Engineering
│   ├── 03_analysis_0-overview.ipynb   # Zentrale Findings, Kernfragen, Report-Auswahl (55 Findings)
│   ├── 03_analysis_1-target.ipynb     # Delay-Verteilung, OTP, Cancellations
│   ├── 03_analysis_2-network.ipynb    # Netzveränderungen 2023–2025, Hotspots, Versorgungsqualität
│   ├── 03_analysis_3-temporal.ipynb   # Stunde, Wochentag, Monat, Saison
│   ├── 03_analysis_4-spatial.ipynb    # Haltestellen, Stadtkreise, Linien
│   ├── 03_analysis_5-meteo.ipynb      # Regen, Wind, Schnee, Temperatur
│   ├── 03_analysis_6-events.ipynb     # Feiertage, Events, Eventgrösse
│   ├── 04_insights.ipynb              # Executive Report (in Arbeit)
│   ├── 05_feature_engineering.ipynb   # Feature Engineering + train/test_final Export
│   ├── 06_prediction_0-overview.ipynb # Vorhersage-Ansatz, Metriken, Baseline-Erklärung
│   ├── 06_prediction_1-baseline.ipynb # Regelbasierte Baselines (Stop Mean = 50.0s)
│   ├── 06_prediction_2-model.ipynb    # LightGBM Training (MAE 45.7s)
│   └── 06_prediction_3-evaluation.ipynb # Evaluation (in Arbeit)
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
