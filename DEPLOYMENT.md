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

## Streamlit Cloud (Dashboard)

### Prerequisites

The dashboard uses pre-computed aggregation tables to avoid loading 29M rows at startup:

```bash
# Run once (whenever raw data changes)
make precompute

# This creates apps/dashboard/data/*.parquet files
# Commit them to git
git add apps/dashboard/data/
git commit -m "data: update dashboard aggregations"
git push origin main
```

### One-Time Setup

1. **Go to https://share.streamlit.io**
2. **Sign in with GitHub** (connect account if needed)
3. **Click "New app"**
4. **Fill in:**
   - Repository: `kaywiegand/zh-tram-flow`
   - Branch: `main`
   - File: `apps/dashboard/app.py`
5. **Click Deploy**

Streamlit builds and deploys automatically. Your app will be live at **https://zh-tram-flow.streamlit.app**.

### How to Update

Push changes to `main` branch:

```bash
# Make changes to apps/dashboard/app.py
git add apps/dashboard/
git commit -m "feat(dashboard): add new section"
git push origin main
```

Streamlit auto-rebuilds within 1–2 minutes. Watch the build logs at:
https://share.streamlit.io/kaywiegand/zh-tram-flow/main/apps/dashboard/app.py

### Troubleshooting

**"ModuleNotFoundError"**
- Streamlit automatically installs from `requirements.txt`
- Ensure `apps/dashboard/requirements.txt` is up-to-date

**Dashboard loads slowly**
- Check if `apps/dashboard/data/*.parquet` files exist and are committed
- Run `make precompute` locally to regenerate them

**Charts don't render**
- Ensure Plotly is installed: check `apps/dashboard/requirements.txt`
- Clear browser cache

---

## Local Testing

Before pushing to production, test locally:

### Dashboard

```bash
# Setup (one-time)
make precompute

# Run
make dashboard
# Opens http://localhost:8501
```

### Static Pages

Open in browser:
```bash
open public/index.html
open public/landingpage.html
open public/report.html
open public/presentation.html
```

Or run a simple server:
```bash
cd public
python -m http.server 8000
# Open http://localhost:8000
```

---

## Makefile Shortcuts

```bash
make deploy-pages      # Shows GitHub Pages setup instructions
make deploy-streamlit  # Shows Streamlit Cloud setup instructions
make precompute        # Pre-compute dashboard data aggregations
make dashboard         # Run dashboard locally
```

---

## Notes

- **All HTML files are static** — no server needed for Pages
- **Dashboard uses Streamlit** — needs Python environment
- **Aggregations are cached** — `@st.cache_data` means dashboard startup is fast (< 1 second with pre-computed data)
- **URLs are permanent** — share them widely, they won't change

---

## URLs to Share

- **General overview:** https://kaywiegand.github.io/zh-tram-flow/
- **Try the dashboard:** https://zh-tram-flow.streamlit.app
- **GitHub:** https://github.com/kaywiegand/zh-tram-flow
