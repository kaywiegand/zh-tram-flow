# Deployment Guide

This document describes how to deploy all artifacts of this project publicly.

---

## Overview

| Artifact | Platform | URL | Files |
|:---------|:---------|:----|:------|
| Landing Page | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/landingpage.html | `public/landingpage.html` |
| Artifact Hub | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/ | `public/index.html` |
| Full Report | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/report.html | `public/report.html` |
| Presentation | GitHub Pages | https://kaywiegand.github.io/zh-tram-flow/presentation.html | `public/presentation.html` |
| Dashboard | Streamlit Cloud | https://zh-tram-flow.streamlit.app | `apps/dashboard/app.py` + `apps/dashboard/data/` |

---

## GitHub Pages (HTML Static Files)

### One-Time Setup

1. **Go to Repo Settings → Pages**
2. **Configure:**
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/public**
3. **Click Save**

GitHub will automatically build and deploy whenever you push to `main`.

### Files Deployed

Everything in `/public/` is published:
- `index.html` → https://kaywiegand.github.io/zh-tram-flow/
- `landingpage.html` → https://kaywiegand.github.io/zh-tram-flow/landingpage.html
- `report.html` → https://kaywiegand.github.io/zh-tram-flow/report.html
- `presentation.html` → https://kaywiegand.github.io/zh-tram-flow/presentation.html
- `img/` → all images and interactive HTML maps

### How to Update

Simply push changes to `main` branch:

```bash
git add public/
git commit -m "docs: update landing page copy"
git push origin main
```

GitHub deploys automatically within seconds.

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
