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
  - `public/md/` ← Portfolio-Docs (portfolio.md, slides.yaml, generierte View-Exports)
  - Hinweis: Dieses Projekt nutzt `public/` statt `reports/` — GitHub Pages Deployment-Anforderung

---

## Deployment & Production

→ **`DEPLOYMENT.md`** (GitHub OSS Standard)

Alle Deployment-Informationen (Setup, GitHub Pages, Streamlit Cloud, Retraining, Monitoring):
```
git@github.com:kaywiegand/zh-tram-flow.git
DEPLOYMENT.md ← Lese das für Production Setup + Troubleshooting
```

**Übersicht:**
- **Local:** `uv sync && jupyter lab`
- **GitHub Pages (static):** Auto-deploy `/public` auf main-Push
- **Streamlit Cloud (dashboard):** Auto-deploy `apps/dashboard/app.py` auf main-Push
- **Model Retraining:** Manual via Notebooks oder später via GitHub Actions
- **Monitoring:** Manual health checks oder via Logs

## Public-Artefakte — Portfolio Pipeline (mechanisiert ab 2026-06-19)

⚠️ **→ Für komplette Dokumentation: `/project-case` Skill dokumentation lesen** ← 

Hier nur Kurzübersicht. Alles andere (Workflow, Troubleshooting, FAQ, Details) in:
```
/Users/kaywiegand/Workspace/skills/project-case/PORTFOLIO_PIPELINE.md
```

### Zwei Quellen, klar getrennt (seit 2026-07-01)

`portfolio.md` hat nie mechanisch die Slide-Struktur gesteuert — `generate_json_from_portfolio.py`
kopierte `chapters` unverändert aus `public/json-backup/`, Slide-Inhalte wurden zuletzt direkt in den
JSONs von Hand gepflegt (undokumentiert, Ursache für Drift zwischen den Views). Korrigierte Architektur:

```
public/md/portfolio.md   — Fakten: Findings, Recommendations, These (von /project-case story befüllt)
public/md/slides.yaml    — Slide-Struktur + -Inhalt (Single Source of Truth für die 3 Views)
        ↓
[skills/project-case/scripts/] archive_portfolio_artifacts.py → public/archive/vN/  (Backup vor Überschreiben)
        ↓
        ├─ generate_json_from_slides.py     → public/json/storyline-{overview,storyview,techview}.json
        ├─ generate_html_from_json.py       → public/{overview,storyview,techview}.html
        ├─ generate_index_from_portfolio.py → public/index.html  (Hub, aus slides.yaml["hub"] + scripts/index-template.html)
        ├─ convert_json_to_md.py            → public/md/{overview,storyview,techview}.md
        └─ print_slide_matrix.py            → public/md/slides-matrix.md (Audit: Slide × View)
```

**Scripts liegen im Skill, nicht im Projekt** (seit 2026-07-01): `/Users/kaywiegand/Workspace/skills/project-case/scripts/`
— projektübergreifend wiederverwendbar, da sie relativ zum Arbeitsverzeichnis arbeiten. Immer aus
dem Projekt-Root heraus aufrufen (macht `make portfolio` automatisch).

**WICHTIG — wo lebt was (übersteht Regenerierung):**
- **Slide-Inhalt** (Titel, Text, welche Slide in welchem View) → `public/md/slides.yaml` (im Projekt)
- **Hub-Inhalt** (Hero-KPIs, View-Karten) → `public/md/slides.yaml`, Block `hub:` (im Projekt) —
  **nicht** mehr im Template hartcodiert; bei Content-Änderungen mitpflegen!
- **Fakten/Findings/Recommendations** (Referenz beim Slide-Schreiben) → `public/md/portfolio.md` (im Projekt)
- **Slide-Design** → `public/css/slides.css` (im Projekt) + `docs/portfolio/templates/slides-template.html` (global)
- **Hub-Layout/Design** → `scripts/index-template.html` (im Projekt — nur noch Layout/CSS, kein Content mehr)
- **Mechanik** (JSON/HTML/MD generieren) → `skills/project-case/scripts/*.py` (global)
- Generierte `public/*.html` NIE direkt editieren — wird überschrieben (liegt im Archiv).
- `public/json-backup/` ist retiriert — `slides.yaml` ist die einzige Quelle, kein Backup-Schritt mehr nötig.
- Details: `skills/project-case/PORTFOLIO_PIPELINE.md`

**Änderungen machen:**
1. Inhalt in `slides.yaml` (Slides) / `portfolio.md` (Fakten) / Design in css+template / Hub in index-template
2. `make portfolio` (= archive → json → html → index → md → matrix), oder `/project-case report`
3. Jeder Lauf archiviert den alten Stand nach `public/archive/vN/` (gitignored)

---

### Research Opportunities — wichtiger Hinweis

Dieses Projekt dokumentiert nicht nur Kernfindings sondern auch **7 systematische Forschungsmöglichkeiten (OP-1 bis OP-7)** die durch interaktive Dashboard-Exploration identifiziert wurden:

- **Dokumentiert in:**
  - `BACKLOG.md` → Sektion "Research Opportunities" (detaillierte Hypothesen + Prioritäten) — **Autorität**
  - `public/md/portfolio.md` → Sektion "Research Opportunities" (minimal: Nennung + OP-1 Beispiel)
  - Generiert in JSONs und HTMLs aus portfolio.md

- **Warum wichtig:** Portfolio zeigt nicht nur "fertig" sondern auch "lebendig" und "iterativ"
- **Änderungen:** Immer zuerst `slides.yaml` (Slide-Inhalt) / `portfolio.md` (Fakten) aktualisieren, dann `/project-case full` ausführen

---

### Workflow: Änderungen durchführen

**Kompletter Workflow (empfohlen):**
```bash
# 1. slides.yaml editieren (Slide-Struktur/-Inhalt) — portfolio.md bei geänderten Fakten
# 2. Komplette Pipeline ausführen
/project-case full
# → generiert JSON, HTML, MD automatisch
```

**Einzelne Schritte (wenn nötig):**
```bash
# Nur JSONs regenerieren
/project-case json
# → skills/project-case/scripts/generate_json_from_slides.py

# Nur HTMLs + MDs regenerieren
/project-case report
# → skills/project-case/scripts/generate_html_from_json.py
# → skills/project-case/scripts/convert_json_to_md.py
```

**Zahlenformat-Regel (Deutsch):**
Alle Zahlen in portfolio.md (und damit in allen generierten Artefakten):
- Dezimaltrennzeichen: Komma → `18,56 s`, `71,5 %`, `r ≥ 0,85`
- Leerzeichen vor Einheit → `87 %`, `94,4 M`, `18,56 s`
- Kein `pp` → immer `%`

---

### Dateien im Überblick

| Datei | Rolle | Geändert durch |
| :--- | :--- | :--- |
| `public/md/portfolio.md` | Fakten: Findings, Recommendations, These | Manuell / `/project-case story` |
| `public/md/slides.yaml` | Single Source of Truth (Slide-Struktur + -Inhalt + Hub-Block) | Manuell |
| `public/css/slides.css` | Slide-Design (Theme) | Manuell |
| `docs/portfolio/templates/slides-template.html` | Slide-Layout/CSS-Basis | Manuell |
| `scripts/index-template.html` | Hub-Layout/CSS (kein Content mehr) | Manuell |
| `public/json/storyline-*.json` | strukturierte Slide-Extrakte | generiert aus `slides.yaml` (Skill-Script) |
| `public/{overview,storyview,techview}.html` | Präsentations-Views (Reveal.js) | generiert aus JSON (Skill-Script) |
| `public/index.html` | Navigation-Hub | generiert aus portfolio.md + slides.yaml["hub"] + index-template (Skill-Script) |
| `public/md/*.md` | Markdown-Export | generiert (Skill-Script `convert_json_to_md.py`) |
| `public/md/slides-matrix.md` | Audit: Slide × View | generiert (Skill-Script `print_slide_matrix.py`) |
| `public/archive/vN/` | Snapshot vor jedem Lauf (gitignored) | Skill-Script `archive_portfolio_artifacts.py` |

Alle "Skill-Script"-Einträge liegen in `/Users/kaywiegand/Workspace/skills/project-case/scripts/`, nicht im Projekt.
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

## Strecken-Basisdaten — `tramlines_stops.parquet`

Erzeugt durch: `notebooks/01_exploration-tramlines.ipynb` (Export-Zelle ausführen)  
Pfad: `data/processed/tramlines_stops.parquet`  
Laden: `pl.read_parquet(PATHS['processed'] / 'tramlines_stops.parquet')`

| Spalte | Typ | Beschreibung |
|:-------|:----|:-------------|
| `line_name` | String | Liniennummer (z.B. `'8'`, `'E'`) |
| `direction_id` | Int64 | 0 oder 1 — willkürliche GTFS-Labels, **kein** festes Hin/Rück |
| `headsign` | String | Zielanzeige des Trams (z.B. `'Klusplatz B'`) — einziger zuverlässiger Richtungs-Name |
| `stop_sequence` | Int64 | Haltestellenreihenfolge innerhalb der Richtung (1-basiert) |
| `stop_name` | String | Haltestellenname (ohne Präfix `'Zürich, '`) |
| `stop_lat` | Float64 | Breitengrad |
| `stop_lon` | Float64 | Längengrad |

**Zweck:** Geordnete Haltestellen aller 17 Tramlinien für beide Richtungen — direkt ladbar für Dashboard-Features ohne GTFS-Join-Logik.

**Kritische Hinweise:**
- `direction_id` 0 und 1 sind **keine festen Richtungen** — immer `headsign` zur Identifikation verwenden
- L8 hat 30 vs. 40 Halte je Richtung (strukturelle GTFS-Asymmetrie, kein Fehler) — Details in Notebook Architecture-Sektion
- Nicht durch `precompute.py` generiert — wird durch Notebook-Ausführung aktualisiert
- Vollständige Erklärung aller Asymmetrien: `notebooks/01_exploration-tramlines.ipynb`

---

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
