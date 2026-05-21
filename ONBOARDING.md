# ONBOARDING.md — zh-tram-flow
### Einstiegspunkt für jede neue Claude Code Session

Dieses File ist der primäre Kontext-Hub für alle Sessions am Projekt `zh-tram-flow`.
**Immer als erstes lesen — vor jedem anderen File.**

---

## 1 · Session-Start — Lesereihenfolge

```
DIESES FILE          ← start hier
PROCESS_LOG.md       ← aktueller Projektstand, letzte Session
ROADMAP.md           ← offene Phasen und Todos
```

Nur wenn nötig (globaler Kontext / Workspace-Entscheidungen):

```
/Users/kaywiegand/Workspace/CLAUDE.md      ← globale Arbeitsregeln (MASTER)
/Users/kaywiegand/Workspace/BACKLOG.md     ← projektübergreifende offene Punkte
/Users/kaywiegand/Workspace/GLOSSAR.md     ← einheitliches Wording
/Users/kaywiegand/Workspace/PROJECTS.md    ← Workspace-Überblick
```

---

## 2 · Projekt-Kontext

| Feld | Inhalt |
| :--- | :--- |
| Projektname | Zürich Tram Flow |
| Repo | `git@github.com:kaywiegand/zh-tram-flow.git` |
| Typ | DANSC — Data Engineering + Analytics + Data Science |
| Thema | VBZ Zürich Tram · Verspätungsanalyse & Vorhersage |
| Stack | Polars · Pandas · GeoPandas · Plotly · LightGBM · Jupyter · uv |
| Status | 🟢 Phase 4 — Modellierung abgeschlossen · Präsentation offen |
| Nächste Schritte | Fehleranalyse · Insights-Report · Präsentation (Fr) |

### Datenbasis

| Datei | Beschreibung |
| :--- | :--- |
| `data/raw/zh-tram-data-master.parquet` | ~94 Mio. Zeilen · 24 Spalten · IST + GTFS + Meteo + Events |
| `data/raw/gtfs/` | 9 GTFS-Parquets (Haltestellen, Routen, Shapes, Trips) |
| `data/interim/train_raw.parquet` | Train-Set nach Cleaning + Split |
| `data/interim/test_raw.parquet` | Test-Set nach Cleaning + Split |
| `data/processed/train_final.parquet` | ML-ready · 32 Features (55.5 Mio. Zeilen) |
| `data/processed/test_final.parquet` | ML-ready · 32 Features (~25 Mio. Zeilen) |
| `data/models/lgbm_v1.txt` | Trainiertes LightGBM v1 |
| `data/processed/test_predictions.parquet` | Predictions auf Test-Set |

**lf_clean-Filter:**
`canceled == False` · `stop_sequence > 1` · keine Linie E/50/51
`departure_delay` + `delay_delta` maskiert für Nov 14–Dez 23 2025 (GTFS-Artefakt j25→j26)

### Modell-Ergebnisse (LightGBM v1)

| Metrik | Wert |
| :--- | :--- |
| Baseline Stop Mean | 50.7s MAE |
| **Test MAE** | **46.3s (−4.4s vs. Baseline ✅)** |
| Val MAE | 49.0s |
| Val RMSE | 85.0s |
| MBE | +8.3s (Modell unterschätzt systematisch) |
| Training | ~52 Min · 41M Zeilen · 32 Features · Iteration 512 |

### Notebook-Übersicht

| Notebook | Status |
| :--- | :--- |
| `00_introduction.ipynb` | ✅ |
| `01_exploration.ipynb` | ✅ |
| `02_preparation.ipynb` | ✅ |
| `03_analysis_0-overview.ipynb` | ✅ |
| `03_analysis_1-target.ipynb` | ✅ |
| `03_analysis_2-network.ipynb` | ✅ |
| `03_analysis_3-temporal.ipynb` | ✅ |
| `03_analysis_4-spatial.ipynb` | ✅ |
| `03_analysis_5-meteo.ipynb` | ✅ |
| `03_analysis_6-events.ipynb` | ✅ |
| `04_insights.ipynb` | ✅ → `reports/insights.html` (Plotly-Karten eingebettet) |
| `05_feature_engineering.ipynb` | ✅ |
| `06_prediction_0-overview.ipynb` | ✅ |
| `06_prediction_1-baseline.ipynb` | ✅ |
| `06_prediction_2-model.ipynb` | ✅ |
| `06_prediction_3-evaluation.ipynb` | 🔄 Fehleranalyse nach Linie/Stunde/Wetter ausstehend |

---

## 3 · Rollen

Je nach Aufgabe in einer der folgenden Rollen arbeiten.
**Explizit nennen welche Rolle aktiv ist.**

### 🔬 Data Analyst / Data Scientist
Zuständig für: EDA · Statistik · Visualisierungen · Feature Engineering · Modellierung · Interpretation

- Polars-Abfragen schreiben — lazy preferred: `pl.scan_parquet()`
- Hypothesen aufstellen und statistisch prüfen
- Findings dokumentieren (F-ID-Nummern-System: F-TARGET, F-SPAT, F-TEMP, F-WEAT, F-EVNT, F-NET)
- LightGBM: Hyperparameter, Feature Selection, Evaluation
- **Jeder neue Plot braucht eine begleitende `show_df()`-Tabelle als Zahlenbasis**

### 🏗️ Developer / Architekt
Zuständig für: Code-Struktur · src/-Paket · Pipelines · Performance · Skalierbarkeit

- `src/zh_tram_flow/` Paket-Struktur pflegen (Import mit Underscores!)
- Cleaning-Pipeline (`cleaning.py`), Analytics-Module (`analytics/`)
- Polars LazyFrame-Architektur: wann `.collect()`, wann `.sink_parquet()`
- Temporal Split korrekt implementieren — kein Look-ahead-Leakage
- **Code ist immer Englisch**: Variablen · Funktionen · Kommentare · Labels

### 🧪 Reviewer / Tester
Zuständig für: Code-Review · Output-Validierung · Qualitätssicherung

- Notebook-Outputs gegen Erwartungswerte prüfen
- Findings auf Plausibilität testen (Zahlen, Relationen, Ausreißer)
- Leakage-Prüfung vor jedem Modell-Training
- GLOSSAR.md-Abgleich: Begriffe in Docs korrekt?
- **Nach jedem Commit: Doc-Checkliste abarbeiten** (→ Abschnitt 6)

---

## 4 · Workflow — Explore → Plan → Implement → Commit

```
1. EXPLORE     Nur lesen. Keine Änderungen. Erst Kontext vollständig verstehen.
2. PLAN        Plan erstellen. Shift+Tab → Plan-Modus. Kay bestätigt explizit.
3. IMPLEMENT   Nur was im Plan steht. Keine spontanen Zusätze.
4. COMMIT      Git-Commit erstellen. Danach zwingend: Doc-Checkliste (→ Abschnitt 6).
```

**Regeln:**
- Erst vorschlagen, dann umsetzen
- Erst lesen, dann ändern — jede betroffene Datei vollständig lesen
- Kein Kontextwechsel mid-session → in BACKLOG notieren, nicht sofort wechseln
- Keine Dateien löschen ohne explizite Erlaubnis
- Bei Unsicherheit fragen — nie raten

---

## 5 · Claude Code — Workflow-Tipps

### Tools & wann was benutzen

| Situation | Tool |
| :--- | :--- |
| Planen, Strategie, Docs besprechen | Chat (kein Filesystem-Zugriff) |
| Code, Notebooks, Scripts, Git | **Claude Code** ← hier sind wir |
| Files umbenennen, sortieren, aufräumen | Cowork |

### Plan-Modus
`Shift+Tab` aktiviert den Plan-Modus.
Claude zeigt einen konkreten Schritt-für-Schritt-Plan — Kay bestätigt explizit bevor umgesetzt wird.

### Notebook-Edits
Vor jedem `NotebookEdit` prüfen: **Ist der Kernel gespeichert und bereit?**
Ungespeicherte Outputs gehen sonst verloren.

### Parallele Tool-Calls
Unabhängige Reads oder Bash-Befehle immer **parallel** aufrufen (gleiche Nachricht, mehrere Tools).
Abhängige Calls sequenziell.

### Session-Abschluss
Am Ende jeder Session:
1. Geänderte Files auflisten
2. Git-Commit-Befehl fertig ausgeben
3. Doc-Checkliste abarbeiten (→ Abschnitt 6)
4. Nächste Schritte konkret nennen

### Kontext-Komprimierung
Bei langen Sessions: `/compact` komprimiert den Context.
Nach Komprimierung → `PROCESS_LOG.md` neu lesen für aktuellen Stand.

---

## 6 · ⚠️ DOC-CHECKLISTE — PFLICHT NACH JEDEM COMMIT

**Kein Commit ist abgeschlossen ohne diese Prüfung. Keine Ausnahmen.**

| File | Wann updaten |
| :--- | :--- |
| `PROCESS_LOG.md` | **Immer** — Datum, was geändert, warum, nächste Schritte |
| `README.md` | Wenn Struktur, Features, Status oder Kennzahlen sich ändern |
| `ROADMAP.md` | Wenn Todos abgehakt werden oder neue hinzukommen |
| `zh-tram-flow/BACKLOG.md` | Wenn neue offene Punkte entstehen oder Items erledigt sind |
| `/Workspace/BACKLOG.md` | Wenn projektübergreifende Punkte auffallen |
| `/Workspace/PROJECTS.md` | Wenn sich der Projektstatus (Phase, Meilenstein) ändert |

**Docs-Commit Format:**
```bash
git commit -m "docs: update PROCESS_LOG, README after <thema>"
```

**Qualitätsprüfung vor jedem Commit (aus GLOSSAR.md):**
- [ ] Phasen-Namen stimmen mit GLOSSAR überein
- [ ] Variablen-Präfix `lf_` / `df_` korrekt verwendet
- [ ] Keine absoluten Zeilenzahlen im Fließtext (ändern sich bei Daten-Updates)
- [ ] Neue Plots haben eine begleitende Datentabelle

---

## 7 · Offene Prioritäten — Stand 2026-05-21

| # | Task | Prio |
| :--- | :--- | :--- |
| B#19 | Präsentation zh-tram-flow (11 Slides · Fr) | **H** |
| B#20 | Präsentation als Claude-Workflow-Übungsfall (Reveal.js) | **H** |
| B#21 | Industry Know-how in Slides einarbeiten | **H** |
| B#22 | Data Engineering Story (Datenmenge als roter Faden) | **H** |
| B#23 | Modern Stack Argument | **H** |
| B#24 | "Analyse diktiert das Modell" Story | **H** |
| B#25 | Feature Engineering als Analyse-Output | **H** |
| B#26 | Live-Vorhersage als HTML-Widget in Präsentation | **H** |
| B#27 | Interaktives Prediction-Tool (Streamlit) | **H** |
| ✅ | `04_insights.ipynb` ausführen + HTML-Export | — |
| — | `06_prediction_3` Fehleranalyse (Linie / Stunde / Wetter) | M |
| B#16 | v2 — Target Encoding für `stop_name` | M |
| B#14 | Events-Notebook: Haltestellen- + Linien-Ranking | M |
| B#9 | Linie 12 Baustellen-Zeitraum validieren | M |

---

## 8 · Tech Stack & Konventionen

### Polars

```python
lf_raw   # LazyFrame — Abfrageplan, kein RAM bis .collect()
df_clean # DataFrame — nach .collect()

pl.scan_parquet(path)   # lazy lesen (preferred)
lf.sink_parquet(path)   # lazy schreiben, kein RAM-Limit
lf.collect()            # nur wenn DataFrame explizit gebraucht wird
```

### Python-Paket

```python
from zh_tram_flow.config import PATHS
from zh_tram_flow.settings import setup_plotting, logger
```

Paketname mit **Underscores** (`zh_tram_flow`), Ordner: `src/zh_tram_flow/`

### Datenpfade

```python
PATHS.raw / "zh-tram-data-master.parquet"   # Rohdaten (nie verändern!)
PATHS.interim / "train_raw.parquet"          # nach Cleaning + Split
PATHS.processed / "train_final.parquet"      # ML-ready
PATHS.models / "lgbm_v1.txt"                # trainiertes Modell
```

### Notebook-Struktur

```
# Notebook Title      ← erste Zelle, einmalig
## Section Title      ← jede Section in eigener Zelle (kollabierbar!)
```

Nie Titel und Inhalt in dieselbe Zelle. Titel kurz halten.

---

*Letzte Aktualisierung: 2026-05-21*
*Zugehöriges Repo: `git@github.com:kaywiegand/zh-tram-flow.git`*
