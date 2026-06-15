# BACKLOG.md — zh-tram-flow
### Projektspezifische offene Tasks + Ideen

Offene Punkte die während der Arbeit auffallen aber nicht sofort umgesetzt werden.
Erledigte Items → als Pointer in PROCESS_LOG dokumentieren, hier entfernen.

Prio: `1` = hoch · `2` = mittel · `3` = niedrig

---

## Artefakte — morgen früh komplett erledigen

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 50 | **`presentation.html` neu generieren** — `/project-case slides` ausführen. Vollständige Slide-Struktur für technisches Publikum. → `presentation-v4.html` (Board-Version) fertig 2026-06-15. | 2 |
| 51 | **`index.html` als Übersicht neu generieren** — `/project-case report` ausführen. Scan + Dive + Deep-Dive Ebenen mit eingebetteten Charts. Ziel: 150–300 KB. | 1 |

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
| 1 | **README vs. `00_introduction.ipynb`** — Rollentrennung klären: wer liest was, wozu? Redundanz auflösen, klare Regel dokumentieren. | 2 |
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
| 18 | **`prev_trip_delay` prüfen** — Kaskadenindikator (F-NET-07). Erst prüfen ob `trip_id` über aufeinanderfolgende Fahrten stabil ist. | 3 |
<!-- Erledigt 2026-05-28:
  #32 LightGBM v2 trainiert: 2 neue Features (prev_trip_delay, stop_sequence_pct) → Test MAE 18.56s, MBE -0.69s — kein Optuna, Feature-Engineering war entscheidend
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

