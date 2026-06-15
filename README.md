# Zürich Tram Flow

**Delay analysis and prediction across Zürich's tram network — 94.4M stop events, 3 years, 16–18 lines.**

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Polars](https://img.shields.io/badge/Polars-0.20+-orange)
![LightGBM](https://img.shields.io/badge/LightGBM-4.0+-green)
![Type](https://img.shields.io/badge/Type-Analysis%20%2B%20Prediction-lightgrey)
![Status](https://img.shields.io/badge/Status-Phase%204%20complete-brightgreen)

---

## TL;DR

**Target:** `arrival_delay` — how many seconds late a tram arrives at a stop · **OTP (On-Time Performance):** a stop is counted as on time if arrival delay < 120s

- **87.0% OTP** across the network — against VBZ's own target of 95%. The gap is structural, not random.
- **Peripheral corridors dominate.** Friedhof Enzenbühl (93.8s) and Balgrist (85.2s) are the worst stops — while Paradeplatz, where 14–15 lines cross, performs well.
- **71.3% of all stops have 0s dwell time.** No recovery buffer built in. Delay accumulates and propagates: Pearson r ≥ 0.85 between consecutive stops across all lines.
- **Snow is the strongest single factor:** +54s average delay, OTP −10.9pp — geographically separable from rain.
- **LightGBM v2: MAE 18.56s — 63% below the Stop Mean baseline (50.0s).** Adding `prev_trip_delay` (cascade feature, derived from analysis finding F-NET-07) drove the main improvement. The model confirms the analysis: delay is predictable because it's structural.

---

## Where to start

| You are… | Start here |
| :--- | :--- |
| New to the project | [`00_introduction`](notebooks/00_introduction.ipynb) — context, data dictionary, network overview |
| Looking for findings | [`03_analysis_0-overview`](notebooks/03_analysis_0-overview.ipynb) — all 63 findings indexed |
| Looking for the model | [`06_prediction_0-overview`](notebooks/06_prediction_0-overview.ipynb) — ML approach and results |
| Want to see it live | [Report](https://kaywiegand.github.io/zh-tram-flow/report.html) · [Dashboard](https://zh-tram-flow.streamlit.app) |

---

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Dataset](#dataset)
- [Approach](#approach)
  - [Data Engineering](#data-engineering)
  - [Data Analysis](#data-analysis)
  - [Data Science](#data-science)
  - [Data Storytelling](#data-storytelling)
- [Results](#results)
- [Notebooks](#notebooks)
- [Tech Stack](#tech-stack)
- [Reports & Artifacts](#reports--artifacts)
- [Setup](#setup)
- [Author](#author)

---

## Project Overview

Public transport is part of everyday life — everyone experiences it, everyone has an opinion on it. That makes it an ideal subject for communicating data analysis and data science to a broad audience: no insider knowledge required to understand what a tram delay means or why it matters.

The choice of Zürich's tram network was deliberate on three levels:

- **Relatability** — delays are a lived experience, not an abstract metric. The findings connect directly to what commuters notice every day.
- **Public good & sustainability** — public transit is a collective resource. Better scheduling and transparency serve society, not a private interest.
- **Data quality** — Zürich's VBZ publishes granular real-time departure and arrival data for every stop event as Open Government Data. Combined with weather, GTFS schedule, and event data, this creates a rare foundation: large enough for real ML, concrete enough for operational recommendations.

The project covers the full data cycle end-to-end:

| Phase | Scope | Where |
| :--- | :--- | :--- |
| **Data Engineering** | Ingest, join, validate 4 data sources (IST · GTFS · Weather · Events) → master dataset | [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) |
| **Data Analysis** | 6 analysis dimensions · 63 structured findings | [`03_analysis_0-overview`](notebooks/03_analysis_0-overview.ipynb) |
| **Data Science** | Feature engineering → LightGBM v1 + v2 → evaluation | [`06_prediction_0-overview`](notebooks/06_prediction_0-overview.ipynb) |
| **Data Storytelling** | Report · Presentation · Dashboard · Landing Page | [`public/index.html`](https://kaywiegand.github.io/zh-tram-flow/) |

---

## Problem Statement

Three questions frame the analysis:

1. **Where and when do delays occur** — and what structural patterns drive them?
2. **What factors matter most** — weather, topology, time of day, events?
3. **Can delays be predicted** before they happen, and with what accuracy?

**OTP — On-Time Performance:** a stop event is counted as on time if `arrival_delay < 120s`.

| Metric | Value |
| :--- | :--- |
| Network OTP (2023–2025) | **87.0%** |
| VBZ target | **95%** |
| Gap | **−8pp** |

87.0% sounds acceptable. It isn't — because 71.5% of all stops *accumulate* delay along the route. The network has no built-in recovery mechanism: 71.3% of stops have 0s planned dwell time. A delay that enters a trip stays in the trip, and spreads to the next.

The goal is not just a model, but a full analytical story: **analysis dictates the model, findings become features.**

---

## Dataset

**Final dataset:** `data/raw/zh-tram-data-master.parquet` — produced by [`sf_data-research`](https://github.com/kaywiegand/sf_data-research)

| Property | Value |
| :--- | :--- |
| Rows | 94.4M · ~541 MB (Parquet) |
| Columns | 26 |
| Period | 2023–2025 |
| Granularity | Per stop arrival/departure event |
| Network | VBZ Zürich — 16–18 lines per year (varies by timetable) |

**Data sources joined:**

- **IST real-time data** — [opentransportdata.swiss](https://data.opentransportdata.swiss): per-stop arrival/departure times for every trip · 36 ZIP files · ~38 GB compressed
- **GTFS schedule** — [ZVV](https://www.zvv.ch): stop coordinates, district assignment, line definitions · 3 annual versions (j23/j24/j25)
- **Weather** — [Stadt Zürich OGD](https://data.stadt-zuerich.ch): hourly values from 3 city measurement stations · temperature, precipitation, snow, radiation
- **Events** — manually curated: 301 entries · 5 categories (Feiertag, Stadtfest, Konzert, Messe, Fussball) · weighted 1–3

**Known issues:**

- `is_windy` is always `NaN` across all years — excluded from all models
- Nov–Dec 2025 departure delay masked due to a provider infrastructure issue — arrival delay unaffected
- `canceled` flag definition changed at provider in Jul 2024 — see [DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)

→ Full column descriptions: [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)

---

## Approach

### Data Engineering

*(in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research))*

- **Feasibility check** — do the data sources exist, in what format and granularity, and can they be meaningfully joined?
- **Pipeline** — 36 ZIP files → ~38 GB raw → filtered, cleaned, joined with GTFS + Meteo + Events → `vbz_master.parquet`
- **Validation** — 8 checks: schema, coverage, value ranges, nulls, join quality

### Data Analysis

→ [`03_analysis_0-overview`](notebooks/03_analysis_0-overview.ipynb) — index of all 63 findings

6 analysis notebooks · **63 structured findings** across 6 dimensions: Target · Network · Temporal · Spatial · Weather · Events

| Dimension | Notebook | Key Finding |
| :--- | :--- | :--- |
| **Target** | [03_analysis_1-target](notebooks/03_analysis_1-target.ipynb) | OTP 87% · 71.5% of stops accumulate delay |
| **Network** | [03_analysis_2-network](notebooks/03_analysis_2-network.ipynb) | Dec 2023 VBZ overhaul invisible in delay signal (+0.5s net) |
| **Temporal** | [03_analysis_3-temporal](notebooks/03_analysis_3-temporal.ipynb) | Peak at 21h (event wave) — not morning rush |
| **Spatial** | [03_analysis_4-spatial](notebooks/03_analysis_4-spatial.ipynb) | Peripheral corridors dominate · 0 overlap density vs. delay |
| **Weather** | [03_analysis_5-meteo](notebooks/03_analysis_5-meteo.ipynb) | Snow +54s · geographically separable from rain |
| **Events** | [03_analysis_6-events](notebooks/03_analysis_6-events.ipynb) | Public holidays best day type · effect is evening-only (18–22h) |

Every finding gets a structured entry (ID · Finding · Impact · Action → Feature · Result) — tracked systematically, impact-rated, linked to model decisions. **"Analysis dictates the model"** — no feature was added speculatively.

### Data Science

→ [`06_prediction_0-overview`](notebooks/06_prediction_0-overview.ipynb) — ML approach and metrics

| Model | Features | Test MAE | vs. Baseline |
| :--- | :---: | :---: | :--- |
| Stop Mean Baseline | — | 50.0s | — |
| LightGBM v1 | 34 | 45.7s | −4.3s |
| **LightGBM v2** | **36** | **18.56s** | **−31.4s (−63%)** |

Strategy: temporal train/test split — 2023–Jun 2024 train / Jul–Dec 2024 val / 2025 hold-out test.
`prev_trip_delay` (cascade feature from F-NET-07) drives the main improvement. The signal was in the data — not in the algorithm.

### Data Storytelling

| Artifact | What it shows |
| :--- | :--- |
| [Report](public/report.html) | Full narrative — Scan (30s) · Dive (5min) · Deep-Dive (30min) reading layers |
| [Presentation](public/presentation.html) | Slide deck for live presentation — pipeline, findings, model, recommendations |
| [Landing Page](public/landingpage.html) | Non-technical entry point — story without jargon |
| [Dashboard](https://zh-tram-flow.streamlit.app) | Interactive map explorer — click any stop, line, or district |

---

## Results

### Model

Top features (LightGBM v2 by gain): `stop_name` · `prev_trip_delay` · `hour` · `line_name` · `has_snow`

MAE 18.56s means the model is on average less than 19 seconds off — on a network where the worst stops average 90+ seconds late. Bias (MBE) is −0.69s, effectively zero.

### Recommendations

Four concrete actions that follow directly from the analysis findings:

| # | Recommendation | Evidence |
| :--- | :--- | :--- |
| R1 | **Fahrplan-Redesign L11** — add schedule buffer at 3–5 critical coupling points | L11 highest delay accumulation · 0s dwell · cascade r ≥ 0.85 |
| R2 | **Real-time dispatch** — use cascade model as early warning signal | `prev_trip_delay` explains −31.4s MAE improvement |
| R3 | **Capacity boost 20–22h** — increase frequency on L11/L8 during event evenings | 21h peak +11.7s · Thursday + large event = worst combination |
| R4 | **Priority monitoring K11/K12** — automated OTP alerts at stop level | Kreis 11: 68.3s avg · OTP 83% · structurally disadvantaged |

→ Full risk matrix and stop-level recommendations: [`06_prediction_7-scheduling_recommendations`](notebooks/06_prediction_7-scheduling_recommendations.ipynb)

---

## Notebooks

| Notebook | What you'll find |
| :--- | :--- |
| [00_introduction](notebooks/00_introduction.ipynb) | Project context · data dictionary · VBZ line colours |
| [01_exploration](notebooks/01_exploration.ipynb) | EDA: distributions · data quality · correlations · outliers |
| [02_preparation](notebooks/02_preparation.ipynb) | Cleaning strategy · temporal split · feature prep |
| [03_analysis_0-overview](notebooks/03_analysis_0-overview.ipynb) | All 63 findings indexed · executive summary |
| [03_analysis_1-target](notebooks/03_analysis_1-target.ipynb) | Delay distribution · OTP 87% · cancellation patterns |
| [03_analysis_2-network](notebooks/03_analysis_2-network.ipynb) | Network changes 2023–2025 · hotspot mapping |
| [03_analysis_3-temporal](notebooks/03_analysis_3-temporal.ipynb) | Hour/weekday/month patterns — peak at 21h |
| [03_analysis_4-spatial](notebooks/03_analysis_4-spatial.ipynb) | Stops · districts · lines — periphery vs. centre |
| [03_analysis_5-meteo](notebooks/03_analysis_5-meteo.ipynb) | Snow · rain · wind — geographic separation of effects |
| [03_analysis_6-events](notebooks/03_analysis_6-events.ipynb) | Holidays · concerts · football — impact by size + hour |
| [04_insights](notebooks/04_insights.ipynb) | Synthesised narrative across all dimensions |
| [05_feature_engineering](notebooks/05_feature_engineering.ipynb) | Feature construction · encoding decisions · export |
| [06_prediction_0-overview](notebooks/06_prediction_0-overview.ipynb) | ML approach · metrics · baseline explanation |
| [06_prediction_1-baseline](notebooks/06_prediction_1-baseline.ipynb) | Stop Mean baseline = 50.0s MAE |
| [06_prediction_2-model](notebooks/06_prediction_2-model.ipynb) | First model: 34 features · Test MAE 45.7s |
| [06_prediction_3-evaluation](notebooks/06_prediction_3-evaluation.ipynb) | Residuals · error analysis · feature importance |
| [06_prediction_4-model_v2](notebooks/06_prediction_4-model_v2.ipynb) | Cascade feature → Test MAE 18.56s |
| [06_prediction_5-comparison](notebooks/06_prediction_5-comparison.ipynb) | All models compared — final verdict |
| [06_prediction_6-dwell_simulator](notebooks/06_prediction_6-dwell_simulator.ipynb) | Dwell-time confounding · binary distribution · cascade mechanism |
| [06_prediction_7-scheduling_recommendations](notebooks/06_prediction_7-scheduling_recommendations.ipynb) | Risk matrix Stop×Line×Context · scheduling buffer recommendations |

---

## Tech Stack

| Category | Tools |
| :--- | :--- |
| Language | Python 3.10 |
| Data (large) | Polars 0.20+ — lazy evaluation, Parquet I/O |
| Data (small) | Pandas |
| Visualisation | Plotly (interactive maps + charts) · Matplotlib · Seaborn |
| ML | LightGBM 4.0+ (native categorical support) |
| Packaging | uv · pyproject.toml |
| Toolkit | [wgnd-toolkit](https://github.com/kaywiegand/wgnd-toolkit) — shared analytics helpers |
| Notebooks | JupyterLab |

---

## Reports & Artifacts

| Artifact | Link |
| :--- | :--- |
| Full Report | https://kaywiegand.github.io/zh-tram-flow/report.html |
| Presentation | https://kaywiegand.github.io/zh-tram-flow/presentation.html |
| Landing Page | https://kaywiegand.github.io/zh-tram-flow/landingpage.html |
| Dashboard | https://zh-tram-flow.streamlit.app |
| Artifact Hub | https://kaywiegand.github.io/zh-tram-flow/ |

---

## Setup

```bash
git clone https://github.com/kaywiegand/zh-tram-flow.git
cd zh-tram-flow
uv sync --extra dan --extra dsc  # dan = analysis deps · dsc = ML deps (LightGBM etc.)
jupyter lab
```

> **Note:** Raw data is not included (541 MB Parquet). Download `data/processed/train_final_v2.parquet` and `test_final_v2.parquet` from release assets to run prediction notebooks.

→ Full setup, deployment, and retraining instructions: [docs/SETUP.md](docs/SETUP.md)

---

## Author

**Kay Alexander Wiegand**
Senior Consultant · Data Scientist · Berlin
[LinkedIn](https://de.linkedin.com/in/kaywiegand) · [GitHub](https://github.com/kaywiegand)

*Data engineering in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) · built with [`wgnd-toolkit`](https://github.com/kaywiegand/wgnd-toolkit) and [`wgnd-scaffolding`](https://github.com/kaywiegand/wgnd-scaffolding).*
