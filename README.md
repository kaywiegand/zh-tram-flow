# Zürich Tram Flow

**Delay analysis and prediction across Zürich's tram network — 94.4M stop events, 3 years, 16 lines.**

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Polars](https://img.shields.io/badge/Polars-0.20+-orange)
![LightGBM](https://img.shields.io/badge/LightGBM-4.0+-green)
![Type](https://img.shields.io/badge/Type-Analysis%20%2B%20Prediction-lightgrey)

---

## TL;DR

**Target:** `arrival_delay` — how many seconds late a tram arrives at a stop · **OTP (On-Time Performance):** a stop is counted as on time if arrival delay < 120s

- **87.0% OTP** across the network — against VBZ's own 90% target for 2028. The gap is structural, not random.
- **Peripheral corridors dominate.** Friedhof Enzenbühl (93.8s) and Balgrist (85.2s) are the worst stops — while Paradeplatz, where 14–15 lines cross, performs well.
- **71.3% of all stops have 0s dwell time.** No recovery buffer built in. Delay accumulates and propagates: Pearson r ≥ 0.85 between consecutive stops on all 16 lines.
- **Snow is the strongest single factor:** +54s average delay, OTP −10.9pp — geographically separable from rain.
- **LightGBM v2: MAE 18.56s — 63% below the Stop Mean baseline (50.0s).** Adding `prev_trip_delay` (cascade feature, derived from analysis finding F-NET-07) drove the main improvement. The model confirms the analysis: delay is predictable because it's structural.

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
| **Data Engineering** | Ingest, join, validate 3 data sources → master dataset | [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) |
| **Data Analysis** | 6 analysis dimensions · 63 structured findings | `notebooks/03_*` |
| **Data Science** | Feature engineering → LightGBM v1 + v2 → evaluation | `notebooks/05_*` + `06_*` |
| **Data Storytelling** | Report · Presentation · Dashboard · Landing Page | `public/` |

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
| VBZ own target (by 2028) | **90%** |
| Gap | **−3pp** |

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
| Network | VBZ Zürich — 16 tram lines |
| License | Open Government Data (OGD) |

**Data sources joined:**

- **IST real-time data** — [opentransportdata.swiss](https://data.opentransportdata.swiss): per-stop arrival/departure times for every trip · 36 ZIP files · ~38 GB compressed
- **GTFS schedule** — [ZVV](https://www.zvv.ch): stop coordinates, district assignment, line definitions · 3 annual versions (j23/j24/j25)
- **Weather** — [Stadt Zürich OGD](https://data.stadt-zuerich.ch): hourly values from 3 city measurement stations · temperature, precipitation, snow, radiation
- **Events** — manually curated: 301 entries · 5 categories (Feiertag, Stadtfest, Konzert, Messe, Fussball) · weighted 1–3

→ Full column descriptions: [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)

---

## Approach

### Data Engineering

*(in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research))*

- **Feasibility check** — do the data sources exist, in what format and granularity, and can they be meaningfully joined?
- **Pipeline** — 36 ZIP files → ~38 GB raw → filtered, cleaned, joined with GTFS + Meteo + Events → `vbz_master.parquet`
- **Validation** — 8 checks: schema, coverage, value ranges, nulls, join quality

### Data Analysis

→ [`03_analysis_0-overview.ipynb`](notebooks/03_analysis_0-overview.ipynb) — index of all 63 findings

6 analysis notebooks · **63 structured findings** across 6 dimensions:

| Dimension | Notebook | Key Finding |
| :--- | :--- | :--- |
| **Target** | [03-1](notebooks/03_analysis_1-target.ipynb) | OTP 87% · 71.5% of stops accumulate delay |
| **Network** | [03-2](notebooks/03_analysis_2-network.ipynb) | Dec 2023 VBZ overhaul invisible in delay signal (+0.5s net) |
| **Temporal** | [03-3](notebooks/03_analysis_3-temporal.ipynb) | Peak at 21h (event wave) — not morning rush |
| **Spatial** | [03-4](notebooks/03_analysis_4-spatial.ipynb) | Peripheral corridors dominate · 0 overlap density vs. delay |
| **Weather** | [03-5](notebooks/03_analysis_5-meteo.ipynb) | Snow +54s · geographically separable from rain |
| **Events** | [03-6](notebooks/03_analysis_6-events.ipynb) | Public holidays best day type · effect is evening-only (18–22h) |

Every finding gets a structured entry (ID · Finding · Impact · Action → Feature · Result) — tracked systematically, impact-rated, linked to model decisions. **"Analysis dictates the model"** — no feature was added speculatively.

### Data Science

→ [`06_prediction_0-overview.ipynb`](notebooks/06_prediction_0-overview.ipynb) — ML approach and metrics

| Model | Features | Test MAE | vs. Baseline |
| :--- | :---: | :---: | :--- |
| Stop Mean Baseline | — | 50.0s | — |
| LightGBM v1 | 34 | 45.7s | −4.3s |
| **LightGBM v2** | **36** | **18.56s** | **−31.4s (−63%)** |

Strategy: temporal train/test split — 2023–Jun 2024 train / Jul–Dec 2024 val / 2025 hold-out test.
`prev_trip_delay` (cascade feature from F-NET-07) drives the main improvement. The signal was in the data — not in the algorithm.

### Data Storytelling

| Artifact | Description |
| :--- | :--- |
| [Report](public/report.html) | Narrative HTML report — Scan · Dive · Deep-Dive reading layers |
| [Presentation](public/presentation.html) | Slide deck — pipeline, findings, model results |
| [Landing Page](public/landingpage.html) | Entry point for non-technical audiences |
| [Dashboard](https://zh-tram-flow.streamlit.app) | Interactive map explorer — Streamlit |

---

## Results

| Dimension | Finding | Signal |
| :--- | :--- | :--- |
| Spatial | Peripheral corridors dominate — K11/K12 high-risk districts | Enzenbühl 93.8s · Balgrist 85.2s |
| Temporal | Peak at 21h (post-event wave) · Thursday worst weekday | 67.9s at 21h |
| Weather | Snow strongest factor · geographically separable from rain | Snow +54s · OTP −10.9pp |
| Events | Impact is evening-only (18–22h) · public holidays best day type | Holidays −9.9s · Messe 66.0s |
| Network | Dec 2023 VBZ overhaul invisible in delay signal | Net effect +0.5s |
| Structure | 71.3% of stops: 0s dwell time · Pearson r ≥ 0.85 cascade | No buffer, no recovery |

Top features (LightGBM v2 by gain): `stop_name` · `prev_trip_delay` · `hour` · `line_name` · `has_snow`

---

## Notebooks

| # | Notebook | What you'll find |
| :--- | :--- | :--- |
| 00 | [Introduction](notebooks/00_introduction.ipynb) | Project context · data dictionary · VBZ line colours |
| 01 | [Exploration](notebooks/01_exploration.ipynb) | EDA: distributions · data quality · correlations · outliers |
| 02 | [Preparation](notebooks/02_preparation.ipynb) | Cleaning strategy · temporal split · feature prep |
| 03-0 | [Analysis Overview](notebooks/03_analysis_0-overview.ipynb) | All 63 findings indexed · executive summary |
| 03-1 | [Target](notebooks/03_analysis_1-target.ipynb) | Delay distribution · OTP 87% · cancellation patterns |
| 03-2 | [Network](notebooks/03_analysis_2-network.ipynb) | Network changes 2023–2025 · hotspot mapping |
| 03-3 | [Temporal](notebooks/03_analysis_3-temporal.ipynb) | Hour/weekday/month patterns — peak at 21h |
| 03-4 | [Spatial](notebooks/03_analysis_4-spatial.ipynb) | Stops · districts · lines — periphery vs. centre |
| 03-5 | [Weather](notebooks/03_analysis_5-meteo.ipynb) | Snow · rain · wind — geographic separation of effects |
| 03-6 | [Events](notebooks/03_analysis_6-events.ipynb) | Holidays · concerts · football — impact by size + hour |
| 04 | [Insights](notebooks/04_insights.ipynb) | Synthesised narrative across all dimensions |
| 05 | [Feature Engineering](notebooks/05_feature_engineering.ipynb) | Feature construction · encoding decisions · export |
| 06-0 | [ML Overview](notebooks/06_prediction_0-overview.ipynb) | ML approach · metrics · baseline explanation |
| 06-1 | [Baseline](notebooks/06_prediction_1-baseline.ipynb) | Stop Mean baseline = 50.0s MAE |
| 06-2 | [LightGBM v1](notebooks/06_prediction_2-model.ipynb) | First model: 34 features · Test MAE 45.7s |
| 06-3 | [Evaluation](notebooks/06_prediction_3-evaluation.ipynb) | Residuals · error analysis · feature importance |
| 06-4 | [LightGBM v2](notebooks/06_prediction_4-model_v2.ipynb) | Cascade feature → Test MAE 18.56s |
| 06-5 | [Comparison](notebooks/06_prediction_5-comparison.ipynb) | All models compared — final verdict |
| 06-6 | [Dwell Simulator](notebooks/06_prediction_6-dwell_simulator.ipynb) | Dwell-time confounding · binary distribution · cascade mechanism |
| 06-7 | [Scheduling Recommendations](notebooks/06_prediction_7-scheduling_recommendations.ipynb) | Risk matrix Stop×Line×Context · scheduling buffer recommendations |

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
uv sync --extra dan --extra dsc
jupyter lab
```

→ Full setup, deployment, and retraining instructions: [docs/SETUP.md](docs/SETUP.md)

---

## Author

**Kay Alexander Wiegand**
Senior Consultant · Data Scientist · Berlin
[LinkedIn](https://de.linkedin.com/in/kaywiegand) · [GitHub](https://github.com/kaywiegand)

---

*Data engineering in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research).
Built with [wgnd-toolkit](https://github.com/kaywiegand/wgnd-toolkit) and [wgnd-scaffolding](https://github.com/kaywiegand/wgnd-scaffolding).*
