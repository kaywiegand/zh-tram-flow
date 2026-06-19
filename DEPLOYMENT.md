# Deployment Guide

Zurich Tram Flow — Production deployment for GitHub Pages (static artifacts), Streamlit Cloud (dashboard), and model retraining.

---

## Quick Start

### Local Development

```bash
git clone https://github.com/kaywiegand/zh-tram-flow.git
cd zh-tram-flow

# Install dependencies (analysis + ML)
uv sync --extra dan --extra dsc

# Launch Jupyter
jupyter lab
```

**Prerequisites:** Python 3.10+, [uv](https://docs.astral.sh/uv/)

> **Note:** Raw data not included (541 MB). Data engineering in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research). To run prediction notebooks, download `train_final_v2.parquet` and `test_final_v2.parquet` from release assets.

---

## Overview — Public Artifacts

| Artifact | Platform | URL | Location |
|:---------|:---------|:----|:---------|
| Artifact Hub | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/ | `public/index.html` |
| Executive Summary | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/overview.html | `public/overview.html` |
| Narrative Story | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/storyview.html | `public/storyview.html` |
| Technical Deep-Dive | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/techview.html | `public/techview.html` |
| LinkedIn 1-Pager | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/socialview.html | `public/socialview.html` |
| Interactive Map | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/network-map.html | `public/network-map.html` |
| Dashboard (Live) | Streamlit Cloud | https://zh-tram-flow.streamlit.app | `apps/dashboard/app.py` |

---

## 1. GitHub Pages (Static Artifacts)

### One-Time Setup

1. Go to **Settings → Pages**
2. **Source:** Deploy from a branch · **Branch:** `main` · **Folder:** `/public`
3. Click **Save**

GitHub auto-deploys whenever you push to `main`.

### Files Deployed

Everything in `/public/`:
- `index.html` → Hub (4-View System)
- `overview.html` → Executive summary
- `storyview.html` → Narrative 4-step proof chain
- `techview.html` → Technical deep-dive
- `socialview.html` → LinkedIn compact
- `network-map.html` → Interactive Plotly map (663KB)
- `img/` → Exported charts (PNG)
- `json/storyline-*.json` → **Single source of truth** for content
- `md/` → Markdown exports (auto-generated from JSON)

### Deploy

Push to trigger auto-deployment:

```bash
git add public/
git commit -m "docs: update reports"
git push origin main
# → Live at https://kaywiegand.github.io/zh-tram-flow/ (30s)
```

### Important: JSON ↔ HTML Sync

`public/json/storyline-*.json` are single source of truth. Manually sync HTML if needed.

**Consistency check (run before commit):**
```bash
# Verifies JSON/HTML/MD are in sync
/project-review  # Schritt 3.7 cross-artefact consistency check
```

---

## 2. Streamlit Dashboard (Interactive App)

### Setup (One-time)

1. Go to https://share.streamlit.io — sign in with GitHub
2. Click **New app**:
   - Repository: `kaywiegand/zh-tram-flow`
   - Branch: `main`
   - File: `apps/dashboard/app.py`
3. Click **Deploy**

App live at **https://zh-tram-flow.streamlit.app**

### Pre-requisite: Precomputed Aggregations

Dashboard loads fast via pre-computed Parquet aggregations. **Must be committed:**

```bash
# Generate (after updating data)
uv run python apps/dashboard/precompute.py

# Commit
git add apps/dashboard/data/*.parquet
git commit -m "chore: update dashboard aggregations"
git push
```

**Aggregations in `apps/dashboard/data/`:**
| File | Rows | Purpose |
| :--- | :---: | :--- |
| `stop_agg.parquet` | 190 | Per-Stop KPIs: mean_delay, p90_delay, otp_pct |
| `line_agg.parquet` | 14 | Per-Line: mean_delay, otp_pct |
| `hourly_agg.parquet` | 168 | Temporal: delay by hour×weekday |
| `weather_agg.parquet` | ~9 | Weather sensitivity |
| `stop_line_lookup.parquet` | 1170 | Predictor features per Stop×Line |
| `route_profile.parquet` | 190 | Spatial delay profile |
| `route_profile_by_direction.parquet` | ~380 | Direction-specific (A/B) |

### Deploy

Push to trigger auto-deployment (1–2 min rebuild):

```bash
git add apps/dashboard/
git commit -m "feat(dashboard): new section"
git push origin main
# → Live at https://zh-tram-flow.streamlit.app (1–2 min)
```

### Local Testing

```bash
# Pre-compute (one-time)
uv run python apps/dashboard/precompute.py

# Run locally
uv run streamlit run apps/dashboard/app.py
# → http://localhost:8501
```

### Troubleshooting

| Problem | Fix |
| :--- | :--- |
| ModuleNotFoundError | Dependencies auto-installed from `pyproject.toml` · commit any changes |
| Dashboard loads slowly (>2s) | Check `apps/dashboard/data/` files exist and are committed · re-run `precompute.py` |
| Charts don't render | Clear browser cache · verify Plotly in `pyproject.toml` |
| Streamlit cache stale | Run: `streamlit run --client.caching=false` |

---

## 3. Model Retraining

### When to Retrain

- **Weekly:** New VBZ data for previous week
- **Monthly:** Full recalculation if OTP drift > 1pp
- **On-demand:** After feature engineering code changes

### How to Retrain (Manual)

```bash
# 1. Get new data
# Download from sf_data-research or VBZ API
# → data/raw/zh-tram-data-master.parquet

# 2. Run feature engineering
jupyter lab notebooks/05_feature_engineering.ipynb
# Outputs: data/processed/train_final_v2.parquet, test_final_v2.parquet

# 3. Train model
jupyter lab notebooks/06_prediction_4-model_v2.ipynb
# Outputs: data/models/lgbm_v2.txt, lgbm_v2_meta.json

# 4. Verify MAE on holdout 2025
# ✅ If MAE < 25s: safe to deploy
# ❌ If MAE > 25s: investigate before pushing
```

### Commit & Deploy

```bash
git add data/models/lgbm_v2.txt lgbm_v2_meta.json
git commit -m "chore: retrain model v2 on $(date +%Y-%m-%d), MAE 18.56s"
git push origin main
# Dashboard auto-reloads on next Streamlit restart
```

### Version Tracking

Keep all trained models:

```
data/models/
├── lgbm_v1.txt (45.7s MAE) — baseline
├── lgbm_v2.txt (18.56s MAE) — current
└── VERSIONS.md ← Document each
```

**VERSIONS.md:**
```markdown
## v2 (2026-06-19)
- MAE: 18.56s
- Features: 36 (+ prev_trip_delay, stop_sequence_pct)
- Training: 41.2M rows (2023–Jun 2024)
- Test: 2025 (~29M rows)

## v1 (2026-05-20)
- MAE: 45.7s
- Status: ARCHIVED
```

### Rollback

If v2 fails (MAE > 25s):

```bash
git checkout HEAD~1 -- data/models/lgbm_v2.txt
git push origin main
# Investigate what changed, retrain, redeploy
```

---

## 4. Production Notes

### `prev_trip_delay` Feature

Drives main improvement (45.7s → 18.56s). Requires **real-time trip tracking in live inference:**

| Scenario | Feasibility |
| :--- | :--- |
| Dashboard (batch) | ✅ Aggregate previous run's delay |
| Live API | ⚠️ Requires live trip feed from VBZ |
| Fallback | LightGBM v1 (45.7s) or Stop Mean (50.0s) |

### Monitoring

```bash
# Manual health check
python scripts/model_health_check.py
# ✅ Model loaded: lgbm_v2.txt
# ✅ MAE: 18.56s
# ✅ Aggregations fresh (today)
```

**Red flags:**
- MAE > 25s for 3+ days → Retrain urgently
- Dashboard loads > 2s → Re-run `precompute.py`
- Missing aggregations → Commit `apps/dashboard/data/*.parquet`

---

## 5. Troubleshooting

| Problem | Symptom | Fix |
| :--- | :--- | :--- |
| Stale GitHub Pages | Old HTML still showing | Hard refresh: `Cmd+Shift+R` |
| Slow Streamlit | Loads > 5s | Check aggregations exist · run `precompute.py` |
| Model file corrupted | `load_model()` fails | `git checkout HEAD~5 -- data/models/` |
| `prev_trip_delay` missing | KeyError in inference | Retrain: run `05_feature_engineering.ipynb` |
| Charts not rendering | Blank Plotly area | Clear browser cache |

---

## Summary

**Local:** `jupyter lab` for notebooks  
**Testing:** `streamlit run apps/dashboard/app.py`  
**Production:** GitHub Pages (auto on push) + Streamlit Cloud (auto on push) + weekly retraining  

Every `git push main`:
- GitHub Pages deploys (~30s)
- Streamlit Cloud deploys (~1-2 min)
- All artifacts live

**Next:** Set up GitHub Actions for automated weekly retraining (see section 3 comments for skeleton)

---

## URLs to Share

- **General overview:** https://kaywiegand.github.io/zh-tram-flow/
- **Dashboard (live):** https://zh-tram-flow.streamlit.app
- **GitHub repo:** https://github.com/kaywiegand/zh-tram-flow
