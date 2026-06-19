# CLAUDE.md — Zurich Tram Flow

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

## Public-Artefakte — Architektur und Reproduzierbarkeit

### Übersicht: Wie JSON, HTML und MD zusammenhängen

```
public/json/storyline-*.json   ← SINGLE SOURCE OF TRUTH für Inhalt
        │
        ├── manuell synchronisiert → public/*.html  (View-Präsentationen)
        │
        └── automatisch generiert → public/md/*.md  (Gamma / Markdown-Export)
                via: python convert_json_to_md.py
```

**Wichtig:** Es gibt kein Build-Script das HTML aus JSON generiert.
Die HTMLs wurden manuell gebaut und werden manuell mit den JSONs synchron gehalten.
Die JSONs sind die inhaltliche Referenz — bei Widersprüchen gilt immer der JSON.

---

### Research Opportunities — wichtiger Hinweis

Dieses Projekt dokumentiert nicht nur Kernfindings sondern auch **7 systematische Forschungsmöglichkeiten (OP-1 bis OP-7)** die durch interaktive Dashboard-Exploration identifiziert wurden:

- **Dokumentiert in:**
  - `BACKLOG.md` → Sektion "Research Opportunities" (detaillierte Hypothesen + Prioritäten)
  - `public/json/storyline-*.json` → Neue Sektion "Weitere Potenziale" vor Closing-Slide
  - `public/*.html` → Manuell synchron mit JSON-Content halten
  - `notebooks/03_analysis_0-overview.ipynb` → Sektion "Analysis Gaps & Open Research Questions"

- **Warum wichtig:** Portfolio zeigt nicht nur "fertig" sondern auch "lebendig" und "iterativ"
- **Fehler:** Research Opportunities-Sektion in JSONs/HTMLs vergessen = Inconsistency

Beim Ändern der Opportunities: immer JSON → dann HTML manuell nachziehen.

---

### Schritt-für-Schritt: Änderungen reproduzieren

**1. Inhalt ändern → immer zuerst im JSON**

```
public/json/storyline-overview.json   → overview.html
public/json/storyline-techview.json   → techview.html
public/json/storyline-storyview.json  → storyview.html
public/json/storyline-socialview.json → socialview.html
```

Felder im JSON:
- `nav_label` → Kapitelname in der Nav-Leiste des HTML
- `title` → `<h2>` im Slide
- `subtitle` → `.subline` im Slide
- `content[].type` → steuert den Inhaltsblock (figures / steps / sections / statement / table)
- `content[].items` → die konkreten Inhalte

**2. Änderung in HTML übertragen**

Manuell: die entsprechende Slide-Section im HTML anpassen.
Nach jeder Änderung: `/project-review` Schritt 3.7 ausführen → prüft Drift zwischen JSON und HTML.

**3. MD-Files regenerieren (nach JSON-Änderung)**

```bash
python scripts/convert_json_to_md.py
```

Schreibt alle vier `public/md/*.md` neu aus den JSONs.
Wird für Gamma-Import und andere Markdown-basierte Tools genutzt.

**4. Zahlenformat-Regel (Deutsch)**

Alle Zahlen in deutschen Artefakten (HTML/JSON/MD):
- Dezimaltrennzeichen: Komma → `18,56 s`, `71,5 %`, `r ≥ 0,85`
- Leerzeichen vor Einheit → `87 %`, `94,4 M`, `18,56 s`
- Kein `pp` → immer `%`
- CSS-Werte (`0.18s`, `0.85em`) nie anfassen

---

### Dateien im Überblick

| Datei | Rolle | Geändert durch |
| :--- | :--- | :--- |
| `public/json/storyline-*.json` | Content Source of Truth | Manuell |
| `public/*.html` | Präsentations-Views (Reveal.js) | Manuell (aus JSON) |
| `public/md/*.md` | Markdown-Export (Gamma, etc.) | `python scripts/convert_json_to_md.py` |
| `public/index.html` | Navigation-Hub | Manuell |
| `public/img/` | Charts (PNG + interaktive HTML) | Notebook Export-Cells |

---

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

## Dashboard — Precomputed Aggregations

Das Streamlit-Dashboard (`apps/dashboard/app.py`) nutzt vorberechnete Aggregationen für Performance.

**Generierung:**
```bash
uv run python apps/dashboard/precompute.py
```

Diese Datei muss einmalig vor Dashboard-Start ausgeführt werden. Sie liest `data/processed/test_final.parquet` (~29M rows) und schreibt 7 kleine Parquet-Dateien nach `apps/dashboard/data/`.

**Output-Dateien — Dimensionen und Zweck:**

| Datei | Zeilen | Dimensionen | Zweck |
|:------|:-------|:-----------|:------|
| `stop_agg.parquet` | 190 | `stop_name` | Per-Stop KPIs: mean_delay, p90_delay, otp_pct, dwell_time_median |
| `line_agg.parquet` | 14 | `line_name` | Per-Linie Aggregates: mean_delay, otp_pct, n_stops, n_obs |
| `hourly_agg.parquet` | 168 | `hour × weekday` | Temporal pattern: mean_delay nach Tageszeit und Wochentag |
| `weather_agg.parquet` | ~9 | `weather_condition` | Weather sensitivity: delay-Impact von Rain/Snow/Hot |
| `stop_line_lookup.parquet` | 1170 | `stop_name × line_name` | Vorhersage-Features per Stop-Line-Paar (für Streamlit-Predictor) |
| `route_profile.parquet` | 190 | `line_name × stop_name` | Räumliches Delay-Profil: lat/lon + mean_delay je Haltestelle auf jeder Linie |
| **`route_profile_by_direction.parquet`** | **~380** | **`line_name × direction_id × stop_name`** | **Richtungs-spezifisches Profil: Split nach Fahrtrichtung A/B (neu für Direction-Filter)** |

**`route_profile_by_direction.parquet` — neu ab Phase 5:**
- Enthält die gleiche Struktur wie `route_profile`, aber pro Fahrtrichtung (`direction_id` 0 oder 1)
- Geographic Split: Jede Linie wird an der Latitude in zwei Richtungen aufgespaltet
- Dienen dem Dashboard-Filter "Fahrtrichtung A" / "Fahrtrichtung B"
- Labels zeigen tatsächliche Start/End-Stop-Namen (z. B. "Richtung A: Wollishofen → Central")
- **Erforderlich** für die Direction-Filter-Implementierung auf allen 3 Dashboard-Seiten

**Workflow nach Code-Änderungen:**
1. Code ändern (z. B. neue Aggregation hinzufügen)
2. `precompute.py` anpassen
3. `uv run python apps/dashboard/precompute.py` ausführen (dauert ~10–30 Sekunden)
4. Neue Parquet-Dateien entstehen in `apps/dashboard/data/`
5. Dashboard mit `streamlit run app.py` starten — liest die neuen Dateien

**Git-Behandlung:**
- Alle Parquet-Dateien sind in `.gitignore` NICHT eingetragen (sind im Repo)
- Grund: Dashboard lädt sie direkt aus `apps/dashboard/data/` — keine zusätzliche Berechnung
- Größe: ~150 KB (mit Kompression) — vertretbar für schnelles Onboarding

---

## Qualitätssicherung — Pflicht nach jeder Code-Änderung

Nach jeder nicht-trivialen Änderung an Python-Files **vor** der Fertigmeldung:

```bash
source .venv/bin/activate && python -c "from zh_tram_flow.[modul] import [symbol]; print('OK')"
```

Mindestens das geänderte Modul importieren. Bei Decorator/Config-Änderungen zusätzlich
einen echten Funktionsaufruf testen (wie `auto_export`-Test mit `exists: True, size: X bytes`).

Nicht akzeptabel: Code als fertig melden ohne Import-Test.
