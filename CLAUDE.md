# CLAUDE.md — Zürich Tram Flow

> Projektspezifische Anweisungen für Claude Code.
> Ergänzt die globale CLAUDE.md aus dem Workspace-Root.

---

## Projekt

| Feld | Inhalt |
| :--- | :--- |
| Slug | `zh-tram-flow` |
| Paket | `zh_tram_flow` (Import mit Underscores) |
| Typ | DANSC — Data Analysis + Data Science |
| Stack | Polars · Pandas · Plotly · LightGBM · Jupyter · uv |

---

## Session-Einstieg

```
1. PROCESS_LOG.md lesen — aktueller Stand und letzte Session
2. ROADMAP.md lesen — offene Phasen
3. Globale CLAUDE.md aus /Users/kaywiegand/Workspace/ gilt weiterhin
```

---

## Datenbasis

Data-Engineering-Phase abgeschlossen — liegt in `sf_data-research`.

```
data/raw/        ← schreibgeschützt, nie verändern
data/interim/    ← nach Cleaning + Split
data/processed/  ← ML-ready, finale Features
models/          ← trainierte Modelle
```

Python-Paket:
```python
from zh_tram_flow.config import PATHS
from zh_tram_flow.settings import setup_plotting, logger
```

---

## Projektspezifische Konventionen

- Polars ist die primäre DataFrame-Bibliothek — `pl.scan_parquet()` (lazy) bevorzugen
- `canceled = True` Zeilen behalten — relevante Extremfälle für das Modell
- Lernmomente mit Polars explizit kommentieren — dieses Projekt ist auch Lernprojekt
- Alle Outputs (Charts, Daten) → `public/` oder `data/processed/`, nie im Notebook-Root
  - `public/img/` ← exportierte Charts (PNG + interaktive HTML)
  - `public/mds/` ← Portfolio-Docs
  - Hinweis: Dieses Projekt nutzt `public/` statt `reports/` — GitHub Pages Deployment-Anforderung

## Style-Gate — automatisch aktiv

`scripts/check_style.py` läuft via PostToolUse-Hook automatisch nach jedem Edit an
`analytics/*.py` und `visualization/*.py`. Bei Verstößen erscheint eine Warnung.

**Session-Start-Pflicht für Claude:**
1. Prüfen ob `.claude/settings.json` existiert → Hooks sind aktiv
2. Kay beim ersten Edit darauf hinweisen: "Hook ist konfiguriert — style-check läuft automatisch"
3. Bei neuem Session-Start Kay einmalig sagen: "Bitte /hooks öffnen damit der Settings-Watcher die Hooks aufnimmt"

Manuell ausführen:
```bash
source .venv/bin/activate && python scripts/check_style.py
```
Regeln: TITLE_KW, plotly_title(), LEGEND_KW_RIGHT, English labels, ylim-Parameter, keine Nulllinien.

## Qualitätssicherung — Pflicht nach jeder Code-Änderung

Nach jeder nicht-trivialen Änderung an Python-Files **vor** der Fertigmeldung:

```bash
source .venv/bin/activate && python -c "from zh_tram_flow.[modul] import [symbol]; print('OK')"
```

Mindestens das geänderte Modul importieren. Bei Decorator/Config-Änderungen zusätzlich
einen echten Funktionsaufruf testen (wie `auto_export`-Test mit `exists: True, size: X bytes`).

Nicht akzeptabel: Code als fertig melden ohne Import-Test.
