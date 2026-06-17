# Portfolio Summary — Zürich Tram Flow
<!-- Interface-Datei: Befüllt von /portfolio story (2026-05-28).
     Einzige Zahlenquelle für /portfolio report und /portfolio slides.
     KEINE Inhalte aus Notebooks kopieren — nur kuratierte Kernaussagen.
-->

---

## Project

```
name:       Zürich Tram Flow
slug:       zh-tram-flow
type:       DANSC
stage:      Phase 4 abgeschlossen — LightGBM v2 trainiert, Evaluation + Vergleich fertig
target:     arrival_delay (Sekunden)
stack:      Python · Polars · Pandas · LightGBM · Plotly · Jupyter · uv
period:     2023–2025
rows:       ~85 M (lf_clean) · 94.4M total
notebooks:  12
findings:   63
```

---

## Storyline

```
thesis:     Die Verspätungen im Zürcher Tramnetz sind vorhersagbar — weil sie im
            Fahrplan-Design verankert sind, nicht im zufälligen Betrieb.

hook:       Der Hauptpeak liegt um 21h (Abreisewelle nach Events) — nicht um 8h
            (Morgenrush). Und alle 16 Tramlinien zeigen Pearson r ≥ 0.85 zwischen
            aufeinanderfolgenden Halten: Der Delay kaskadiert systematisch.

proof:      4-Schritt-Beweiskette:
            1. Anomalie — periphere Hotspots, nicht zentrale Knotenpunkte
            2. Gradient — Delay wächst entlang der Strecke (L11 vs. L6 als Kontrast)
            3. Mechanismus — 71.3% dwell_time = 0s: kein Puffer, keine Erholung möglich
            4. Kaskade — Pearson r ≥ 0.85 netzweit: systematisch, kein Einzelfall

so_what:    Was vorhersagbar ist, ist steuerbar. Das Modell bestätigt die Analyse:
            prev_trip_delay (Kaskadenindikator) ist das stärkste neue Feature in v2
            — MAE sinkt von 45.7s auf 18,56 s. Fahrplan-Redesign an L11 ist der Hebel.
```

---

## Problem

```
kpi_name:   OTP — On-Time Performance (arrival_delay ≤ 120s)
kpi_ist:    87
kpi_soll:   95% (VBZ-Standard / VDPW)
kpi_gap:    −8pp

problem_statement: |
  Das Zürcher Tramnetz operiert systemisch unter dem VBZ-Zielwert: 87% OTP
  statt 95%. An 71.5% aller Halte akkumulieren Trams Verspätung — und 71.3%
  aller Haltestellen haben 0s dwell_time, also keinen eingebauten Puffer.
  Das ist kein Wetter- und kein Event-Problem. Es ist ein Fahrplan-Design-Problem.
```

---

## Key Findings
<!-- 6 Findings mit je einer konkreten Zahl, direkt aus Analyse-Phase -->

### F1 — Struktur: Kein Puffer eingebaut
```
finding:   71.5% aller Halte akkumulieren Delay (delay_delta > 0) — weil
           71.3% der Haltestellen 0s dwell_time haben. Das Netz hat keinen
           Erholungsmechanismus eingebaut.
number:    71.3% dwell_time = 0s
source:    03_analysis_1-target.ipynb · 03_analysis_4-spatial.ipynb
```

### F2 — Geo: Hotspots an der Peripherie
```
finding:   Die schlimmsten Haltestellen sind periphere Aussenkorridore —
           Friedhof Enzenbühl (93.8s), Balgrist (85.2s), Leutschenbach (82.7s).
           Zentrale Knotenpunkte (Central, Paradeplatz) liegen unter Netzschnitt.
           0 Overlap zwischen höchster Liniendichte und höchstem Delay.
number:    0 Overlap Top-Dichte × Top-Delay
source:    03_analysis_4-spatial.ipynb
```

### F3 — Zeit: Kein Morgenrush — Peak um 21h
```
finding:   7h liegt mit 48.9s unter dem Netzschnitt. Der echte Peak ist 21h (67.9s)
           durch Events-Abreisewellen. Donnerstag ist der schlechteste Wochentag
           (60.4s, P95=194s) — nicht Freitag. November jeweils Jahreshöchstwert.
number:    +11.7s um 21h vs. Netzschnitt
source:    03_analysis_3-temporal.ipynb
```

### F4 — Wetter: Schnee geografisch trennbar von Regen
```
finding:   Schnee ist der stärkste Einzeleffekt (+54s, OTP −10.9pp). Geografisch
           klar trennbar: Schnee trifft Höhenlagen (K10/K4/K12), Regen trifft
           Flusstäler (K5 / Limmat). Linien reagieren komplett unterschiedlich:
           L9 Schnee +75.9s vs. Regen +10.0s — L17 umgekehrt.
number:    Schnee +54s · Regen +23.3s
source:    03_analysis_5-meteo.ipynb
```

### F5 — Events: Feiertage beste Tage, Fachmessen schlechteste Kategorie
```
finding:   Feiertage sind mit 46.3s (−9.9s vs. Normal) der beste Tagestyp —
           der MIV-Rückgang überwiegt jeden Event-Effekt. Event-Wirkung ist
           ein Abend-Phänomen (18–22h): tagsüber kein messbarer Unterschied.
           Fachmessen (66.0s) schlagen Taylor Swift (75.4s) in der Rangliste.
number:    Feiertage −9.9s · Fachmessen 66.0s
source:    03_analysis_6-events.ipynb
```

### F6 — Kaskade: Pearson r ≥ 0.85 auf allen 16 Linien
```
finding:   Der Delay an einem Halt überträgt sich mit r ≥ 0.85 auf den nächsten
           Halt desselben Trips — auf allen 16 Linien. Das ist kein statistisches
           Artefakt, sondern ein lernbares Signal: prev_trip_delay ist in LightGBM v2
           das stärkste neue Feature und erklärt den Sprung von 45.7s auf 18,56 s MAE.
number:    Pearson r ≥ 0.85 (alle 16 Linien)
source:    03_analysis_4-spatial.ipynb · 06_prediction_4-model_v2.ipynb
```

---

## Model Results
<!-- Nur befüllen wenn ML-Projekt (Typ DANSC oder DSC) -->

```
algorithm:      LightGBM (gradient boosting)
target:         arrival_delay (Sekunden)
metric:         MAE (Mean Absolute Error — direkt in Sekunden kommunizierbar)
split_strategy: temporal — 2023–Jun 2024 Train / Jul–Dez 2024 Val / 2025 Test (kein Shuffle)
train_rows:     41.2M
val_rows:       14.3M
test_rows:      ~29 M (inkl. Nov/Dez 2025 — vorher ausgeschlossen, nach Maskierung drin)
```

### Baseline Benchmark

| Model | Logic | Metric |
|---|---|---|
| Grand Mean | Always predict ⌀ (56.3s) | 50.6s MAE |
| Hour Mean | Predict ⌀ by hour | 50.5s MAE |
| Line Mean | Predict ⌀ by line | 50.4s MAE |
| **Stop Mean** | **Predict ⌀ by stop** | **50.0s MAE ← Benchmark** |

### Model Progression

| Model | Features | Test MAE | vs. Baseline | Data Requirement |
|---|---|---|---|---|
| Stop Mean Baseline | — | 50.0s | — | Historical stop mean |
| LightGBM v1 | 34 (Zeit · Wetter · Events · Linie · Stop) | 45.7s | −4.3s | Schedule + Weather + Events |
| LightGBM v2 | 36 (+prev_trip_delay, +stop_sequence_pct) | **18,56 s** | **−31.4s (−63%)** | + Live-Signal (Vorgänger-Halt) |

```
best_model:     LightGBM v2
best_metric:    18,56 s MAE (Test) · MBE −0,69 s (nahezu bias-frei)
key_insight:    prev_trip_delay ist das stärkste neue Feature — bestätigt die
                Kaskadenanalyse: Das Signal steckt in den Daten, nicht im Algorithmus.
                XGBoost Robustheits-Check: val MAE ~21.4s (150 Runden, >90 Min auf 85M Zeilen)
                → LightGBM klar überlegen bei Trainingszeit.
mbe_v1:         +8,3 s (Modell war systematisch zu optimistisch)
mbe_v2:         −0,69 s (Isotonic-Regression-Kalibrierung wirksam)
otp_v1:         77.5% (vs. Stop-Mean-Baseline 71.9%)
```

---

## Figures
<!-- Alle relevanten Exports in reports/../img/ — 21 Dateien -->

```yaml
spatial:
  - ../img/geo-delay-hotspots.png           # Hotspot-Karte: Blasen = Ø Delay (KEY VISUAL)
  - ../img/geo-delay.png                    # Stop-Delay-Überblick, alle Haltestellen
  - ../img/geo-delay-otp-stadkreise.png     # OTP nach Stadtkreis (Choropleth)
  - ../img/geo-stadtkreise-haltestellen-delay.png  # Stops + Stadtkreise kombiniert
  - ../img/geo-stop-delay-interactive.html  # Interaktive Haltestellen-Delay-Karte (Plotly)

temporal:
  - ../img/tempo-day-hours.png              # Ø Delay nach Stunde (0–23h), alle Linien
  - ../img/tempo-week-days.png              # Ø Delay nach Wochentag, Vergleich Linien
  - ../img/tempo-saison.png                 # Ø Delay nach Saison

network:
  - ../img/network.png                      # Netzübersicht mit allen Tramlinien
  - ../img/total-network-delay.png          # Ø Arrival Delay aller 16 Linien (Bar)
  - ../img/total-network-delay-delta.png    # Delay Delta (Akkumulationsrate) aller Linien
  - ../img/total-network-otp.png            # OTP aller Linien im Vergleich
  - ../img/total-network-line-delay-dwell.png  # Linie: Delay + Dwell kombiniert
  - ../img/total-network-line-dwell.png     # Dwell-Time-Profil aller Linien
  - ../img/network-line-delta-map.html      # Interaktive Δ-Linien-Karte (Plotly Mapbox)

meteo:
  - ../img/meteo-types.png                  # Wettertypen-Vergleich: Normal / Regen / Schnee
  - ../img/meteo-schnee.png                 # Schnee-Effekt nach Stadtkreis (Choropleth)
  - ../img/meteo-starkregen.png             # Starkregen-Effekt nach Stadtkreis
  - ../img/meteo-weather-impact-map.html    # Interaktive Wetter-Impact-Karte (Schnee + Regen)

events:
  - ../img/events-timeline.png             # Event-Timeline 2023–2025 mit Kategorien
  - ../img/events-delta.png                # Event-Kategorien: Delay-Vergleich

model:
  # Feature Importance Chart: noch nicht exportiert (BACKLOG #43)
  # Nach Export via save_fig() hier eintragen: ../img/model-feature-importance.png
```

---

## Recommendations

```
r1:
  title:  Fahrplan-Redesign L11 — gezielter Puffer einbauen
  detail: 71.3% aller Haltestellen haben 0s dwell_time — kein Erholungsmechanismus.
          L11 (68.7s, OTP 82%) und ihre Endstationen zeigen die stärkste Akkumulation.
          Selbst +10s Puffer an 3–5 kritischen Koppelstellen würde den Kaskadeneffekt
          unterbrechen (Hebel #1, direkt durch dwell_time=0 und Pearson r ≥ 0.85 gedeckt).

r2:
  title:  Real-Time Dispatch — Kaskadenmodell operativ nutzen
  detail: LightGBM v2 mit prev_trip_delay erreicht MAE 18,56 s (−63% vs. Baseline).
          Das Signal ist echtzeit-verfügbar (Vorgänger-Halt als Input). Dispatchsystem
          könnte automatisch Taktlücken schließen bevor der Kaskadeneffekt entsteht.

r3:
  title:  Kapazitätsmanagement 20–22h — Event-Abreisewelle abfedern
  detail: Peak ist 21h (+11.7s vs. Netzschnitt) durch Abreisewellen.
          Donnerstag + Freitag mit Grossevents ist die kritischste Kombination.
          Takterhöhung 20–22h auf L11/L8 (beide dauerhaft erhöhtes Grundniveau)
          wäre durch Daten direkt begründbar.

r4:
  title:  OTP-Monitoring nach Stadtkreis — K11/K12 als Priority Zones
  detail: Kreis 11 (68,3 s, OTP 83%) und Kreis 12 (66.3s) sind strukturell benachteiligt.
          Automatisiertes Alert-System auf Haltestellenebene — kombiniert mit dem
          Prediction-Modell als Frühwarnsignal — ermöglicht proaktive Steuerung
          statt reaktiver Entstörung.
```

---

## Status

```
generated_by:    /portfolio story
generated_at:    2026-05-28
summary_version: 1
portfolio_check: ⚠️ partial (Notebook-Outputs ausgeführt, Feature-Importance-Export ausstehend)
report_html:     ❌ pending
slides_html:     ✅ vorhanden (presentation-v3.html — 21 Slides, manuell erstellt)
```


---


# Zürich Tram Flow

**Delay analysis and prediction across Zürich's tram network — 94.4M stop events, 3 years, 16 lines.**

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Polars](https://img.shields.io/badge/Polars-0.20+-orange)
![LightGBM](https://img.shields.io/badge/LightGBM-4.0+-green)
![Type](https://img.shields.io/badge/Type-DSC-lightgrey)

---

## Key Visual

![Delay hotspots in Zürich's tram network](public/img/spatial-stop-delay-map.png)
*Average arrival delay per stop (2023–2025). Hotspots concentrate in outer corridors — not at central interchange points.*

---

## TL;DR

- **Delays are a periphery problem, not a city-centre problem.** Friedhof Enzenbühl (93.8s) and Balgrist (85.2s) are the worst stops — while Paradeplatz (14–15 lines crossing) performs well.
- **Snow is the strongest single factor:** +54s average delay, OTP −10.9 percentage points. Geographically separable from rain — snow hits elevation zones (K10/K4/K12), rain hits river valleys (K5).
- **LightGBM v2 predicts delay with MAE 18,56 s — 63% below the Stop Mean baseline of 50.0s.** Adding a cascade feature (`prev_trip_delay`) drove the main improvement, confirming that delay propagates through the network.
- **Predictable = structural = actionable.** A MAE of 18,56 s is only achievable if delays follow patterns — random events don't predict this well. The model identifies which stops, lines, and operating conditions need schedule buffer, turning analysis findings directly into scheduling recommendations.

---

## Problem Statement

Transit delays affect millions of commuters daily, yet rarely get analysed at scale with open data. Zürich's VBZ tram network is an exception: it publishes granular real-time departure and arrival data for every stop event. Combined with weather, GTFS schedule, and event data, this creates a foundation for answering three questions:

1. **Where and when do delays occur** — and what structural patterns drive them?
2. **What factors matter most** — weather, topology, time of day, events?
3. **Can delays be predicted** before they happen, and with what accuracy?

The goal is not just a model, but a full analytical story: analysis dictates the model, findings become features.

---

## Dataset

| Property | Value |
| :--- | :--- |
| Source | [opentransportdata.swiss](https://data.opentransportdata.swiss) · [Stadt Zürich OGD](https://data.stadt-zuerich.ch) · ZVV GTFS |
| Size | 94.4M rows × 26 columns · ~541 MB (Parquet) |
| Time Period | 2023–2025 |
| Granularity | Per stop arrival/departure event |
| Network | VBZ Zürich — 16 tram lines |
| License | Open Government Data (OGD) |
| Known Issues | `is_windy` always NaN — excluded from model. Nov–Dec 2025 departure delay masked (infrastructure issue). |

**Raw data pipeline** (in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research)):
36 ZIP files → ~38 GB compressed → 500–720 GB unpacked → filtered to 94.4M rows · 1.44 GB (1,096 Parquet files) → master dataset with GTFS + Meteo + Events joined.

---

## Approach

### Data Engineering *(in `sf_data-research`)*
- Ingestion: 3 years of real-time departure/arrival data from opentransportdata.swiss
- Joins: GTFS stops + district assignment (spatial) · Meteo hourly averages · 5 event categories (301 entries, weighted 1–3)
- Output: `vbz_master.parquet` — 26 columns, fully validated (8 checks)

### Data Analysis
6 analysis notebooks · **63 structured findings** across 6 dimensions:
Target · Network · Temporal · Spatial · Weather · Events

Every finding gets a structured entry — like a ticket:

| Field | Example |
| :--- | :--- |
| **ID** | `F-NET-07` — unique, citable across notebooks and docs |
| **Finding** | Cascade effect confirmed: Pearson r ≥ 0.85 between consecutive stop delays within a trip |
| **Impact** | High — affects every trip in the network, not just individual stops |
| **Action → Feature** | `prev_trip_delay` added to LightGBM v2 |
| **Result** | MAE dropped from 45.7s to **18,56 s** — the single largest improvement |

This mirrors professional data team workflows (think Jira for analysis): findings are tracked systematically, impact-rated, and linked to concrete outputs — features, model decisions, or recommendations. The analysis overview notebook ([`03_analysis_0-overview.ipynb`](notebooks/03_analysis_0-overview.ipynb)) is the index across all 63 findings.

**"Analysis dictates the model"** — no finding was added to the model speculatively. Every feature has a traceable origin in this system.

### Data Science / ML
- Target: `arrival_delay` (seconds) — regression
- Strategy: temporal train/test split — 2023–2024 train, 2025 hold-out test
- Baseline → model progression driven by analysis findings

---

## Results

### Key Findings

| Dimension | Finding | Signal |
| :--- | :--- | :--- |
| Spatial | Peripheral corridors dominate — K11/K12 are high-risk districts | Enzenbühl 93.8s, Balgrist 85.2s |
| Temporal | Peak at 21h (post-event wave), Thursday worst weekday — no morning rush | 21h avg. 67.9s |
| Weather | Snow is strongest factor, geographically separable from rain | Snow +54s, OTP −10.9pp |
| Events | Large events delay during 18–22h; public holidays best day type | Events +10.5s · Holidays −9.9s |
| Network | Dec 2023 VBZ overhaul (largest in history) invisible in delay signal | Net effect +0.5s only |
| OTP | 87 % of stops on time (< 120s late) · 71.5% accumulate delay along route | Baseline for model target |

### Model Comparison

| Model | Test MAE | MBE | Notes |
| :--- | :---: | :---: | :--- |
| Stop Mean Baseline | 50.0s | — | Predicts historic average per stop |
| LightGBM v1 | 45.7s | +8,3 s | 32 features · 481 trees · temporal split |
| **LightGBM v2** | **18,56 s** | **−0,69 s** | +`prev_trip_delay` + `stop_sequence_pct` · −63% vs. baseline |

Top features (LightGBM v2 by gain): `stop_name` · `prev_trip_delay` · `hour` · `line_name` · `has_snow`

---

## Tech Stack

| Category | Tools |
| :--- | :--- |
| Language | Python 3.10 |
| Data (large) | Polars 0.20+ — lazy evaluation, Parquet I/O |
| Data (small) | Pandas |
| Visualisation | Plotly (interactive maps + charts), Matplotlib, Seaborn |
| ML | LightGBM 4.0+ (native categorical support) |
| Packaging | uv, pyproject.toml |
| Toolkit | [wgnd-toolkit](https://github.com/kaywiegand/wgnd-toolkit) — shared analytics helpers |
| Notebooks | JupyterLab |

---

## Project Structure

```
zh-tram-flow/
├── notebooks/
│   ├── 00_introduction.ipynb          ← Start here — project context + data dictionary
│   ├── 01_exploration.ipynb           ← EDA: distributions, integrity, correlations
│   ├── 02_preparation.ipynb           ← Cleaning, train/test split, feature prep
│   ├── 03_analysis_0-overview.ipynb   ← 63 findings index + executive summary
│   ├── 03_analysis_1-target.ipynb     ← Delay distribution, OTP, cancellations
│   ├── 03_analysis_2-network.ipynb    ← Network changes 2023–2025, hotspots
│   ├── 03_analysis_3-temporal.ipynb   ← Hour, weekday, month, season patterns
│   ├── 03_analysis_4-spatial.ipynb    ← Stops, districts, lines
│   ├── 03_analysis_5-meteo.ipynb      ← Rain, wind, snow, temperature
│   ├── 03_analysis_6-events.ipynb     ← Holidays, events, event size
│   ├── 04_insights.ipynb              ← Synthesised narrative report
│   ├── 05_feature_engineering.ipynb   ← Feature construction + export
│   ├── 06_prediction_0-overview.ipynb ← ML approach, metrics, baseline explanation
│   ├── 06_prediction_1-baseline.ipynb ← Stop Mean and rule-based baselines
│   ├── 06_prediction_2-model.ipynb    ← LightGBM v1 training
│   ├── 06_prediction_3-evaluation.ipynb ← Residuals, error analysis, feature importance
│   ├── 06_prediction_4-model_v2.ipynb ← LightGBM v2 + cascade feature
│   └── 06_prediction_5-comparison.ipynb ← Model comparison + final verdict
│
├── public/
│   ├── index.html                     ← Artifact hub (GitHub Pages entry)
│   ├── report.html                    ← Full narrative report (3-layer: Scan · Dive · Deep)
│   ├── presentation.html              ← Slide deck (reveal.js)
│   ├── landingpage.html               ← Landing page for social / HR
│   ├── img/                           ← All exported charts (64 PNGs + interactive HTML)
│   └── mds/portfolio.md              ← Portfolio interface file
│
├── src/zh_tram_flow/                  ← Importable Python package
│   ├── config.py                      ← PATHS, constants
│   ├── settings.py                    ← Plot theme, colours, logging
│   ├── cleaning.py                    ← Structural cleaning pipeline
│   ├── notebook.py                    ← Notebook helpers (save_fig etc.)
│   ├── analytics/                     ← Analysis functions per dimension
│   ├── features/                      ← Feature engineering
│   └── visualization/                 ← Plot functions
│
├── data/                              ← Not in Git (.gitignore)
│   ├── raw/                           ← Master Parquet from sf_data-research
│   ├── interim/                       ← After cleaning + split
│   ├── processed/                     ← ML-ready feature sets
│   └── models/                        ← Trained model files (lgbm_v1.txt, lgbm_v2.txt)
│
├── tests/
├── pyproject.toml                     ← Dependencies + package config
└── ROADMAP.md                         ← Project phases and status
```

---

## Setup

**Prerequisites:** Python 3.10+, [uv](https://docs.astral.sh/uv/)

```bash
# Clone
git clone https://github.com/kaywiegand/zh-tram-flow.git
cd zh-tram-flow

# Install — analysis + ML dependencies
uv sync --extra dan --extra dsc

# Launch notebooks
jupyter lab
```

> **Note:** Raw data is not included in this repo (541 MB Parquet).
> Data engineering is documented in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research).
> To run prediction notebooks, download `data/processed/train_final.parquet` and `test_final.parquet` from the release assets.

---

## Notebooks

| # | Notebook | What you'll find |
| :--- | :--- | :--- |
| 00 | [Introduction](notebooks/00_introduction.ipynb) | Project context, data dictionary, VBZ line colours |
| 01 | [Exploration](notebooks/01_exploration.ipynb) | EDA: distributions, data quality, correlations, outliers |
| 02 | [Preparation](notebooks/02_preparation.ipynb) | Cleaning strategy, temporal split, feature prep |
| 03-0 | [Analysis Overview](notebooks/03_analysis_0-overview.ipynb) | All 63 findings indexed + executive summary |
| 03-1 | [Target](notebooks/03_analysis_1-target.ipynb) | Delay distribution, OTP 87%, cancellation patterns |
| 03-2 | [Network](notebooks/03_analysis_2-network.ipynb) | Network changes 2023–2025, hotspot mapping |
| 03-3 | [Temporal](notebooks/03_analysis_3-temporal.ipynb) | Hour/weekday/month patterns — peak at 21h |
| 03-4 | [Spatial](notebooks/03_analysis_4-spatial.ipynb) | Stops, districts, lines — periphery vs. centre |
| 03-5 | [Weather](notebooks/03_analysis_5-meteo.ipynb) | Snow, rain, wind — geographic separation of effects |
| 03-6 | [Events](notebooks/03_analysis_6-events.ipynb) | Holidays, concerts, football — impact by size + hour |
| 04 | [Insights](notebooks/04_insights.ipynb) | Synthesised narrative across all dimensions |
| 05 | [Feature Engineering](notebooks/05_feature_engineering.ipynb) | Feature construction, encoding decisions, export |
| 06-0 | [ML Overview](notebooks/06_prediction_0-overview.ipynb) | ML approach, metrics definition, baseline explanation |
| 06-1 | [Baseline](notebooks/06_prediction_1-baseline.ipynb) | Stop Mean baseline = 50.0s MAE |
| 06-2 | [LightGBM v1](notebooks/06_prediction_2-model.ipynb) | First model: 32 features, Test MAE 45.7s |
| 06-3 | [Evaluation](notebooks/06_prediction_3-evaluation.ipynb) | Residuals, error analysis, feature importance |
| 06-4 | [LightGBM v2](notebooks/06_prediction_4-model_v2.ipynb) | Cascade feature → Test MAE 18,56 s |
| 06-5 | [Comparison](notebooks/06_prediction_5-comparison.ipynb) | All models compared — final verdict |
| 06-6 | [Dwell Simulator](notebooks/06_prediction_6-dwell_simulator.ipynb) | Dwell-time confounding analysis — binary distribution, cascade mechanism |
| 06-7 | [Scheduling Recommendations](notebooks/06_prediction_7-scheduling_recommendations.ipynb) | Risk matrix Stop×Line×Context, scheduling buffer recommendations |

---

## Dashboard

Interactive Streamlit app — two modes:

| Mode | Description |
| :--- | :--- |
| **Explore** | Historical charts across 5 sections (network, temporal, meteo, events, geo) + interactive Plotly maps |
| **Predict** | Live LightGBM v1 inference: select Stop × Line × Hour × Weekday × Weather → predicted delay |

```bash
uv run streamlit run apps/dashboard/app.py
```

---

## Deployment

All artifacts are deployed and publicly accessible:

| Artifact | URL | How |
| :--- | :--- | :--- |
| **Landing Page** | https://kaywiegand.github.io/zh-tram-flow/landingpage.html | GitHub Pages from `/public` |
| **Artifact Hub** | https://kaywiegand.github.io/zh-tram-flow/ | GitHub Pages default (index.html) |
| **Dashboard** | https://zh-tram-flow.streamlit.app | Streamlit Community Cloud |
| **Full Report** | https://kaywiegand.github.io/zh-tram-flow/report.html | GitHub Pages |
| **Presentation** | https://kaywiegand.github.io/zh-tram-flow/presentation.html | GitHub Pages |

### GitHub Pages Setup

The `/public` folder is deployed as a static website via GitHub Pages.

**To enable (one-time):**
1. Go to **Settings** → **Pages**
2. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: `main`
   - Folder: `/public`
3. Click **Save**
4. GitHub will build and deploy automatically on every push to `main`

**URLs:**
- Main entry: `https://kaywiegand.github.io/zh-tram-flow/` (serves `public/index.html`)
- Direct links: `.../landingpage.html`, `.../report.html`, `.../presentation.html`, etc.

### Streamlit Cloud Setup

The Dashboard is deployed via Streamlit's free Community Cloud.

**To enable (one-time):**
1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click **"New app"**
4. Repository: `kaywiegand/zh-tram-flow`
5. Branch: `main`
6. File: `apps/dashboard/app.py`
7. Click **Deploy**

**Note:** Before deploying, ensure `apps/dashboard/data/*.parquet` files are committed to git.
They are pre-computed aggregations (~1600 rows) generated by `precompute.py`.

### Local Dashboard

To run the dashboard locally (before deploying):

```bash
# One-time: pre-compute aggregations
uv run python apps/dashboard/precompute.py

# Then start the app
uv run streamlit run apps/dashboard/app.py
# Opens http://localhost:8501
```

---

## Reports

| Report | Description |
| :--- | :--- |
| [Full Report](public/report.html) | Narrative HTML report — Scan · Dive · Deep-Dive reading layers |
| [Presentation](public/presentation.html) | Slide deck — DSC pipeline, findings, model results |

---

## Author

**Kay Alexander Wiegand**
Senior Consultant · Data Scientist · Berlin
[LinkedIn](https://de.linkedin.com/in/kaywiegand) · [GitHub](https://github.com/kaywiegand)

---

*Data engineering in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research).
Built with [wgnd-toolkit](https://github.com/kaywiegand/wgnd-toolkit) and [wgnd-scaffolding](https://github.com/kaywiegand/wgnd-scaffolding).*
