# BACKLOG.md — zh-tram-flow
### Projektspezifische offene Tasks + Ideen

Offene Punkte die während der Arbeit auffallen aber nicht sofort umgesetzt werden.
Erledigte Items → als Pointer in PROCESS_LOG dokumentieren, hier entfernen.

Prio: `1` = hoch · `2` = mittel · `3` = niedrig

---

## Visual Selection & Integration

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 52 | **README Key Visual Selection** — Wähle 1 Grafik für die Scan-Ebene (nach Badges, vor TL;DR). Kandidaten: `network-hotspots.png` · `spatial-stop-delay-map.png` · `target-otp.png`. Entscheidung: Was erzählt die stärkste Story in 1 Bild? | 2 |
| 53 | **View-HTML Visuals Inventory** — Für jede View (overview/techview/storyview/socialview) die Top 3–5 Chart-Kandidaten identifizieren. Pro View eine Zeile in dieser Tabelle (unten). | 1 |
| 54 | **Visuals einpflegen** — Nach #52/#53 entschieden, die ausgewählten PNGs/interaktiven HTMLs in die View-HTMLs embedden. | 2 |

---

## Visual Asset Planning

**README** (nach Badges-Zeile)
```
Slot: 1 Key Visual
Größe: ~600px Breite
Format: PNG oder interaktive Plotly-HTML
Kandidaten:
  - network-hotspots.png (geografisch, zeigt Problem)
  - spatial-stop-delay-map.png (Detail-Haltestellen)
  - target-otp.png (Problem-Statement: 87 % vs. 95 %)
  - temporal-hour-of-day.png (Temporal Pattern)
Status: [ ] Ausgewählt
```

**public/overview.html** (Scan-Ebene, Hiring Manager)
```
Slots: 3–5 Charts (max 150–200 KB)
Fokus: KPIs + Überblick Dimensionen
Kandidaten:
  - [ ] target-otp.png (OTP Overview)
  - [ ] spatial-district-analysis.png (Geo-Muster)
  - [ ] temporal-hour-of-day.png (Temporal-Muster)
  - [ ] meteo-weather-overview.png (Wetter-Impact)
  - [ ] spatial-cascade-effect.png (Cascade-Effekt visualisiert)
Status: [ ] Finalisiert
```

**public/techview.html** (Tech Deep-Dive)
```
Slots: 5–7 Charts (Max 250 KB)
Fokus: Data Engineering + Model Evaluation
Kandidaten:
  - [ ] network-einlaufzeit.png (Feature: Laufzeit)
  - [ ] spatial-line-hour-heatmap.png (Feature Interaction)
  - [ ] target-delay-distribution-comparison.png (Target-Distribution)
  - [ ] meteo-multicollinearity-matrix.png (Feature Correlation)
  - [ ] spatial-stop-delay-map.html (interaktive Karte)
  - [ ] target-trip-level-validation.png (Data Quality)
Status: [ ] Finalisiert
```

**public/storyview.html** (Narrative Story)
```
Slots: 6–8 Charts (Max 300 KB)
Fokus: Beweiskette (Anomalie → Gradient → Mechanismus → Kaskade)
Kandidaten:
  - [ ] spatial-stop-delay-map.html (Anomalie: Peripherie)
  - [ ] spatial-line-delay-profile-map.html (Gradient entlang Strecke)
  - [ ] spatial-dwell-time.png (Mechanismus: 0s dwell)
  - [ ] spatial-cascade-effect.png (Cascade visualisiert)
  - [ ] meteo-snow-structural-interaction.png (Wetter-Feedback)
  - [ ] target-delay-per-line-timeline.png (Temporal Trend)
  - [ ] events-daily-delay-timeline.png (Events & Kaskade)
Status: [ ] Finalisiert
```

**public/socialview.html** (1-Pager, Social/LinkedIn)
```
Slots: 2–3 Charts (Max 100 KB)
Fokus: Impact-Story, compact
Kandidaten:
  - [ ] spatial-stop-delay-map.png (Problem visualisiert)
  - [ ] spatial-cascade-effect.png (Root Cause)
  - [ ] target-otp.png (Performance Gap)
Status: [ ] Finalisiert
```

---

## Portfolio-Aufbereitung — nächste Sessions

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 50 | **`overview.html` neu generieren** — `/project-case report` ausführen. Scan + Dive + Deep-Dive Ebenen mit eingebetteten Charts. Ziel: 150–300 KB. | 1 |
| 51 | **Weitere Presentation Views** — Falls nötig nach Review. Storytelling-JSONs sind Single Source of Truth. | 2 |
| 60 | **public/pdf/ aufräumen** — PDF-Exporte sind Temp-Dateien (6 MB). Nur Portfolio-relevante PDF behalten, Rest entfernen. | 3 |

---

## Projekt-Prozess als Portfolio-Story

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 66 | **"Wie ich dieses Projekt gebaut habe" — Prozess-Story als eigenständiges Artefakt** | 1 |

**Idee:** Das Projekt hat nicht nur ein starkes fachliches Ergebnis — es hat auch einen reproduzierbaren, automatisierten Workflow der selbst Portfolio-Wert hat. Das gehört sichtbar gemacht.

**Was gezeigt werden soll:**

| Baustein | Inhalt |
| :--- | :--- |
| `wgnd-scaffolding` | Projekt-Struktur in Minuten — Ordner, CLAUDE.md, ROADMAP, BACKLOG, pyproject.toml automatisch |
| `wgnd-toolkit` | Eigene Python-Bibliothek für Plotting, Exporte, Notebook-Utilities |
| Skills / Slash-Commands | `/project-review` · `/project-case` · `/project-init` — automatisierter Qualitätscheck vor jedem Release |
| Hooks | PostToolUse Style-Check läuft automatisch nach jedem Code-Edit — kein manuelles Prüfen |
| CONVENTIONS.md | Einheitliche Regeln für alle Projekte — einmal definiert, überall gültig |
| Strukturierte Findings (F-IDs) | Ticket-System für Data-Analyse — Jira-Analogie, vollständige Rückverfolgbarkeit |

**Mögliche Artefakte:**

1. **Slide in `storyview.html`** — 1 Slide "Wie das Projekt gebaut wurde": Prozess-Grafik mit den 6 Bausteinen. Ersetzt den fehlenden AI-Workflow Slide, jetzt mit echtem Inhalt.
2. **LinkedIn-Artikel** — "Wie ich meinen Data-Science-Workflow automatisiert habe" — konkret, mit Screenshots, reproduzierbar.
3. **README-Sektion** — Kurzer Absatz "How this was built" mit Links auf wgnd-scaffolding + wgnd-toolkit.

**Offene Frage vor Umsetzung:** Framing klären:
- Sachlich: *"Automatisierter Entwicklungs-Workflow mit Claude Code"*
- Differenzierend: *"Ich habe meine eigenen Slash-Commands gebaut"*
- Story: *"Vom leeren Ordner zum Portfolio-Projekt — mit diesem Workflow"*

---

## Präsentation

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
<!-- Erledigt 2026-06-02:
  #26 Live Vorhersage HTML-Widget — scripts/generate_widget_data.py → lgbm_v1 → 168k Predictions →
       JSON in reports/live-prediction.html eingebettet; 5 Controls: Stop × Linie × Stunde × Tagtyp × Wetter;
       SVG-Sparkline Tageskurve; Link-Button auf Danke-Slide in presentation.html
-->

<!-- Erledigt 2026-05-28 → presentation-v2.html + presentation-v3.html:
  #19 Präsentation erstellt (21 Slides, T-Shape, Data Engineering, Analysis, Data Science)
  #20 Mit Claude Code als Workflow-Übungsfall gebaut
  #21 Industry Know-how: Baseline-Benchmarking, Temporal Split, Feature Engineering als Output
  #22 Data Engineering Story: 38 GB raw → 85M Zeilen → 34 Features ML-ready
  #23 Modern Stack: LightGBM + Polars auf Laptop
  #24 Analyse diktiert das Modell: 4-Schritt-Beweiskette
  #25 Feature Engineering als Analyse-Output: Finding → Feature explizit
  #28 Kernthese: "vorhersagbar = steuerbar" als Einstieg + roter Faden
  #29 Design überarbeitet: linksbündig, Whitespace, Normal Case, Evidence Chain
  #30 Impact-Momente: Hotspot-Haltestellen, 4-Schritt-Beweiskette, Kaskadeneffekt
-->

---

## Portfolio-Aufbereitung

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
<!-- Erledigt 2026-06-01:
  #43 Export-Cells in Analyse-Notebooks — save_as=None zu allen 35 matplotlib Plot-Funktionen ergänzt;
       ## Export Sektion (Markdown + Code) in 03_analysis_2/3/4/5/6-*.ipynb eingefügt;
       35 PNGs reproduzierbar nach reports/img/ exportierbar (temporal/spatial/meteo/events/network)
  #39 Interaktive Linienansicht — plot_line_route_map + table_line_route_map in analytics/spatial.py;
       GTFS-Routen-Linie + Stop-Bubbles (grün→amber→rot) + Top-3 Annotation; Notebook-Cells in 03_analysis_4-spatial.ipynb
  #34 Single Source of Truth Audit — Fakten-Register in PROCESS_LOG.md; 93.9M→94.4M in portfolio.md korrigiert;
       Konvention dokumentiert: portfolio.md = Präsentations-Interface, README = externe Leser, PROCESS_LOG ab jetzt Pointer
  #10 Portfolio-Beschreibung README — Findings-System in README → Approach/Data Analysis erklärt:
       strukturierte IDs (F-NET-07), Impact/Action/Result-Tabelle, Jira-Analogie, "Analysis dictates the model"
  #42 Dwell-Optimierungs-Simulator — 06_prediction_6-dwell_simulator.ipynb; Hauptbefund: dwell_time
       binär (0/60s), r=+0.16 Konfundierung, Feature Importance ≠ kausaler Hebel; F-SIM-01–04 dokumentiert
  #45 Findings-Index — 03_analysis_0-overview.ipynb: F-SIM-01–04 + F-REC-01–04 eingetragen;
       Executive Summary 6. Erkenntnis + Kernthese 4. Befund; Report-Auswahl neue Sektion
  #44 Presentation Full-Circle-Folie — Slide 21 "Der vollständige Kreis" + Danke-Slide Next Steps aktualisiert
  #40 Situationsvergleich — plot_line_context_map + table_line_context_map in spatial.py;
       5 Kontexte (Normal/Schnee/Event/Rush/Spätnacht); Notebook-Cells in 03_analysis_4-spatial.ipynb
  #44 Presentation Full-Circle-Folie — Slide 21 "Der vollständige Kreis" + Danke-Slide aktualisiert
  #46 Empfehlungskarte — Export-Zelle in 06_prediction_7; reports/img/scheduling-recommendations-map.html;
       Full-Circle-Section in index.html mit iframe + 4-step proof-chain
-->

<!-- Erledigt 2026-05-29:
  Portfolio-Pipeline ausgeführt:
  - reports/mds/portfolio.md erstellt (Interface-File: Kernthese, 6 Findings, Modellprogression, 4 Empfehlungen)
  - reports/index.html erstellt (narrativer 3-Ebenen-Report: Scan · Dive · Deep-Dive)
  - reports/ als Web-Projekt restrukturiert: img/ · mds/ · index.html · network-map.html
  - insights_v1.html + template.html entfernt · config.py PATHS["figures"] → reports/img/
  - wgnd-scaffolding + globale CLAUDE.md auf neue Struktur aktualisiert (3 Commits)
-->

<!-- Erledigt 2026-05-28:
  #41 Key-Visual: geo-delay-hotspots.png in README eingebunden ✅
  #35 Reporting aufräumen: plotly_chart_1/2/3.html → beschreibende Namen, meteo-saison.png (Duplikat) gelöscht ✅
       save_fig() Helper implementiert in src/zh_tram_flow/notebook.py ✅
-->
| 1 | **README vs. `00_introduction.ipynb`** — Rollentrennung teilweise aufgelöst (Data Dictionary → docs/, Deliverables-Sektion in 00_introduction, Workflow-Tabelle ersetzt Notebook-Liste). Noch offen: explizite Regel dokumentieren wer was liest. | 2 |
<!-- Erledigt 2026-06-17: #53/#55 — ToC in 14 restlichen Notebooks eingefügt, alle 21 Notebooks haben jetzt ## Inhalt -->
| 54 | **Line Colors Tabelle** — Hex-Codes mit farbigen Swatches ergänzen (`<span style="background:#RRGGBB">`) in `03_analysis_0-overview.ipynb`. Funktioniert in JupyterLab, VSCode, nbviewer. | 3 |

---

## 🗓️ Morgen — Notebooks & Präsentation finalisieren

### Notebooks überarbeiten & finalisieren

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
<!-- Erledigt 2026-06-17: #55 → siehe #53 -->
<!-- Erledigt 2026-06-17: #56 — 03_analysis_1–6 alle deutschen Header → Englisch, Kernfragen-Bezug (Q1–Q5) als Callout in Intro-Zelle jedes Notebooks -->
<!-- Erledigt 2026-06-17: #57 — 06_prediction_0-overview: Planungssprache → Ergebnissprache, alle Headers English, Notebooks-Tabelle vollständig (7), Key Decisions, Success Criteria mit Actual-Spalte -->
| 58 | **`03_analysis_7-findings.ipynb` finalisieren** — Notebook-Inhalte prüfen: Findings-Tabelle vollständig? Header englisch? "Why Structured Finding IDs?"-Abschnitt professionell? | 2 |
| 59 | **Line Colors mit Swatches** — `03_analysis_0-overview.ipynb`: Hex-Codes visuell ergänzen. → BACKLOG #54 | 3 |

### Präsentation & Artefakte finalisieren

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
<!-- Erledigt 2026-06-17:
  #60 presentation-v4.html + #61 presentation.html — obsolet. Ersetzt durch 4-View-System:
       overview.html (Management) · techview.html (DS/Tech) · storyview.html (Portfolio) · socialview.html (Social)
       _archive/ gelöscht. Dashboard-URL (Streamlit) bleibt offen → #65
-->
| 62 | **`public/index.html` reviewen** — Zahlen, Links und Findings-Referenzen prüfen. | 1 |
| 65 | **`public/index.html` — Dashboard-Link prüfen** — Link auf Live Dashboard (Streamlit) zeigt nicht korrekt. URL verifizieren und korrigieren sobald Streamlit Cloud deployed. | 2 |
| 63 | **`/project-case check`** — Portfolio-Readiness prüfen bevor weitere Aufbereitung. Gibt Priorisierung für die letzten Schritte. | 1 |
| 64 | **README finalisieren** — Rollentrennung README vs. `00_introduction` explizit dokumentieren. Deliverables-Liste aktuell? → BACKLOG #1 schliessen. | 2 |
| 5 | **Pipeline-Skizze dokumentieren** — vollständige Datenpipeline in `00_introduction.ipynb`: wann lazy, wann collect(), wann sink_parquet() und warum. Format: Diagramm + Begründungstabelle. | 2 |
<!-- Erledigt 2026-06-02:
  #6 Meta-Abgleich — 00_introduction.ipynb (Cell 6: Modellauswahl aktualisiert, Cell 15: 55→63 Findings + 4 neue Notebooks, MAEs korrigiert, Statuses ✅); README (06-6/07 ergänzt); ROADMAP (Phase 4 um Simulation & Empfehlungen erweitert)
  #14 Events-Ranking — plot_event_stop_ranking + plot_event_line_ranking + table_event_line_ranking in analytics/events.py; neue Section in 03_analysis_6-events.ipynb; Export-Cells ergänzt
-->

---

## Analyse & Notebooks

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 9 | **Linie 12 Baustellen-Zeitraum** (Jan 2023 – Jun 2024) validieren — genaue Daten aus VBZ-Quellen bestätigen, dann: herausfiltern oder als Binary-Feature kodieren? | 2 |
| 2 | **Visualisierungen in `01_exploration.ipynb`** — Data Distribution + Outlier Detection Charts überarbeiten. Welche bringen wirklich Mehrwert? | 2 |
| 3 | **Sampling-Validierung** — `gather_every(2)` vs. `gather_every(3)` für Wetterextreme validieren. Stratifiziertes Sampling nach `line_name` vor Modellierung. | 2 |
| 8 | **Segment-Fahrzeit-Analyse** — war die Tram zwischen zwei Halten schneller/langsamer als geplant? Für `03_analysis_spatial` prüfen. | 3 |
| 4 | **Wettervorhersage als Feature** — Open-Meteo oder MeteoSchweiz Forecast-API. Welche Horizonte realistisch (1h, 3h, 24h)? Passt zu "What-if"-Dashboard. | 3 |

---

## Modell v2

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 16 | **Target Encoding für `stop_name`** — Mittelwert `arrival_delay` pro Stop (n-Threshold ≥ 1000, Smoothing). Erklärt Teil des MBE (+10.1s). Neues `train_final_v2.parquet` → Modell neu trainieren. | 2 |
| 17 | **Netzwerk-Stats als Artefakt speichern** — `compute_network_stats()` Ergebnis als `data/processed/network_stats.parquet` persistieren. Verhindert stilles Leakage bei Neuausführung. | 3 |
<!-- Erledigt 2026-06-16:
  #18 prev_trip_delay geprüft und implementiert — F-NET-07 done; stärkstes Feature in LightGBM v2 (MAE 45.7s → 18,56 s, −63%)
-->
<!-- Erledigt 2026-05-28:
  #32 LightGBM v2 trainiert: 2 neue Features (prev_trip_delay, stop_sequence_pct) → Test MAE 18,56 s, MBE -0,69 s — kein Optuna, Feature-Engineering war entscheidend
  #33 XGBoost als Robustheits-Check: val MAE ~21.4s bei Round 150, Training auf 85M Zeilen >90 Min — LightGBM klar überlegen; Ergebnis in presentation-v3 Slide 18
-->

---

## Tools

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
<!-- Erledigt 2026-06-02:
  #27 Interaktives Prediction-Tool — apps/dashboard/app.py Vorhersage-Modus: lgbm_v1 live-Inferenz, Stop-Lookup aus test_final.parquet
  #31 Dashboard Spielmodus + Vorhersagemodus — apps/dashboard/app.py: Erkunden (19 PNGs + 3 interaktive HTML-Karten + Scheduling-Map) + Vorhersagen; uv run streamlit run apps/dashboard/app.py

Erledigt 2026-06-15:
  #52 Dashboard finalisiert — Explorer-Konzept mit 3 Tools: Linie erkunden · Linien vergleichen · Delay vorhersagen.
      Plotly-Charts auf Basis vorhandener Parquets, datenbasierte Empfehlungen pro Linie, Szenario-Vergleich im Predictor.
      Alte app.py (Chart-Browser) entfernt, app_v2.py → app.py. README und BACKLOG aktualisiert.
-->

---

## Docs & Pflege

| # | Beschreibung | Prio | Status |
| :--- | :--- | :--- | :--- |
| 34 | **Repo-Referenzen aktualisieren wenn `sf_data-research` umbenannt wird** — README, CLAUDE.md, ROADMAP und alle Notebooks verlinken aktuell auf `sf_data-research`. Bei Umbenennung des Repos zu `zh-tram-data` (oder ähnlich) alle Links und Textstellen ersetzen. Betrifft: README.md (mehrere Stellen), ROADMAP.md Phase 0, 00_introduction.ipynb, 06_prediction_5-comparison.ipynb. | 3 | – |

---

## Blueprint & Kommunikation

| # | Beschreibung | Prio | Status |
| :--- | :--- | :--- | :--- |
| 32 | **Communication Concept in /project-review + /project-case** — Integration von `docs/portfolio/COMMUNICATION_CONCEPT.md` als Richtlinie. Checkliste für zielgruppengerechte Artefakte (Landing, Dashboard, Exports) in die Skills einbauen. | 1 | ✅ 2026-06-02 — Blueprint fertig, Workspace BACKLOG #15 |
| 33 | **Short-Form Content (LinkedIn-Artikel)** — Case-Study: "How I built a portfolio project that reaches 8 different audiences." Nach Public Deployment. | 2 | – |

