---
title: Zurich Tram Flow
slug: zh-tram-flow
type: DANSC
tags: [data-science, data-analysis, time-series, gradient-boosting, lightgbm, polars, open-data, transit, portfolio]
status: phase-4-complete
date_completed: 2026-06
stack: Python · Polars · LightGBM · Plotly · Jupyter
rows: 94.4M
model_mae: 18,56 s
improvement: -63% vs. baseline
links:
  github: https://github.com/kaywiegand/zh-tram-flow
  report: https://kaywiegand.github.io/zh-tram-flow/report.html
  dashboard: https://zh-tram-flow.streamlit.app
---

# Zurich Tram Flow

**Delay analysis and prediction across Zürich's tram network — 94.4M stop events, 3 years, 16 lines.**

## Thesis

Delays in Zürich's tram network are predictable because they are embedded in schedule design, not random operations.

## Key Findings

- **Spatial**: Peripheral corridors dominate. Friedhof Enzenbühl (93.8s), Balgrist (85.2s) — not central Paradeplatz.
- **Temporal**: Peak at 21h (post-event wave), not morning rush. Thursday worst weekday.
- **Weather**: Snow +54s, OTP −10.9pp. Geographically separable from rain (elevation zones vs. river valleys).
- **Events**: Large events +10.5s during 18–22h. Public holidays −9.9s (best day type).
- **Cascade**: Pearson r ≥ 0.85 between consecutive stop delays. Delay propagates systematically.

## Model Results

| Model | Test MAE | vs. Baseline |
|:------|:--------:|:------------:|
| Stop Mean Baseline | 50.0s | — |
| LightGBM v1 | 45.7s | −4.3s |
| **LightGBM v2** | **18,56 s** | **−63%** |

Key driver: `prev_trip_delay` (cascade indicator) — top-2 feature by gain.

## Links

- [[sf_data-research]] — Data engineering phase (38 GB raw → 94.4M rows)
- [[wgnd-toolkit]] — shared analytics helpers
- [Full Report](https://kaywiegand.github.io/zh-tram-flow/report.html)
- [Dashboard](https://zh-tram-flow.streamlit.app)
- [Presentation](https://kaywiegand.github.io/zh-tram-flow/presentation.html)
