# Zürich Tram Flow

> **Typ:** DAN &nbsp;|&nbsp; **Erstellt:** 2026-05-11 &nbsp;|&nbsp; **Version:** 0.1.0

---

## Schnellstart

### 1. Repository klonen / Ordner oeffnen

```bash
# In VS Code: Datei -> Ordner oeffnen -> diesen Projektordner waehlen
```

### 2. uv installieren (einmalig, falls noch nicht vorhanden)

```bash
pip install uv
```

### 3. Virtuelle Umgebung erstellen

```bash
uv venv
```

### 4. Umgebung aktivieren

```bash
# Windows:
.venv\Scripts\activate

# Mac / Linux:
source .venv/bin/activate
```

### 5. Dependencies + Projektpaket installieren

```bash
uv pip install -e ".[dan]"
```

> Das `-e` steht fuer "editable" - dein `src/zh-tram-flow/` Paket wird direkt aus dem
> Quellcode importiert. Die eckigen Klammern `[dan]` installieren die DAN-Zusatzpakete
> aus `pyproject.toml`.

### 6. Jupyter Kernel registrieren

```bash
python -m ipykernel install --user --name zh-tram-flow --display-name "Python (zh-tram-flow)"
```

### 7. Los geht's!

Oeffne `notebooks/00_introduction.ipynb` und fange an.

---

## Projektstruktur

```
Zürich Tram Flow/
|
+-- pyproject.toml          # Paketkonfiguration & Dependencies
+-- .gitignore
+-- .python-version         # Python-Version fuer uv (3.10)
+-- README.md
|
+-- data/                   # NICHT in Git! (.gitignore)
|   +-- raw/                # Rohdaten - NIEMALS veraendern!
|   +-- interim/            # Zwischenstands (gefiltert, teilbereinigt)
|   +-- processed/          # Finale, analysefertige Daten
|
+-- notebooks/
|   +-- 00_introduction.ipynb
|   +-- 01_exploration.ipynb
|   +-- 02_preprocessing.ipynb
|   +-- 03_advanced_analytics.ipynb
|   +-- 04_business_report.ipynb
|   +-- project_decision_log.md
|
+-- src/
|   +-- zh-tram-flow/     # Das Python-Paket
|       +-- __init__.py
|       +-- config.py       # Zentrale Pfade & Konstanten
|       +-- settings.py     # Plot-Theme, Farben, Logging
|       +-- utils.py        # Hilfsfunktionen
|       +-- data/
|       +-- features/
|       +-- visualization/
|       +-- analytics/
|
+-- tests/
|   +-- test_data.py
|   +-- test_features.py
|
+-- reports/
    +-- figures/            # Exportierte Plots
    +-- tables/             # Exportierte Tabellen
    +-- index.html          # Executive Summary HTML
```

---

## Konfiguration

### Pfade (`src/zh-tram-flow/config.py`)

```python
from zh-tram-flow.config import PATHS

PATHS["raw"]       # data/raw/
PATHS["processed"] # data/processed/
PATHS["figures"]   # reports/figures/
```

### Plotting einrichten

```python
from zh-tram-flow.settings import setup_plotting, logger

setup_plotting()
logger.info("Notebook gestartet")
```

---

## Tests ausfuehren

```bash
pytest
pytest --cov=src/zh-tram-flow --cov-report=term-missing
```

---

_Generiert mit dem DAN/DSC Scaffolding Generator._
