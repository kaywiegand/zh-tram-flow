# BACKLOG.md — zh-tram-flow
### Projektspezifische offene Tasks + Ideen

Offene Punkte die während der Arbeit auffallen aber nicht sofort umgesetzt werden.
Erledigte Items → als Pointer in PROCESS_LOG dokumentieren, hier entfernen.

Prio: `1` = hoch · `2` = mittel · `3` = niedrig

---

## Präsentation

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 26 | **Präsentation — Live Vorhersage als HTML-Widget** — Predictions vorberechnen → JSON → JavaScript-Lookup. Kein Server nötig. Dropdown: Stop × Linie × Stunde × Wetter-Flag | 2 |

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
| 10 | **Portfolio-Beschreibung** — Findings-System (strukturierte IDs, Impact, Action, Status) als bewusste Engineering-Entscheidung hervorheben. Analogie zu Ticket-Systemen. Gehört in README + Bewerbungsunterlagen. | 1 |
| 34 | **Single Source of Truth für Zahlen + Metriken** — Audit: Welche Zahl steht wo? Für jeden Fakt (MAE, Baseline, Zeilenzahlen, Finding-Counts) einen Primärort (Notebook-Zelle) festlegen. Alle anderen Vorkommen durch Pointer ersetzen. Kein Fakt doppelt in MD-Files. | 1 |
| 43 | **Export-Cells in Analyse-Notebooks** — Jedes Notebook bekommt eine letzte `## Export`-Cell mit `save_fig(fig, "name")`. Sichert alle relevanten Charts reproduzierbar und benannt. Kandidaten: temporal, spatial, meteo, events, network, prediction. | 2 |

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
| 6 | **Meta-Abgleich** — `00_introduction.ipynb` · `README.md` · `ROADMAP.md` synchronisieren: Phasen-Namen · Variablen-Konventionen. | 2 |

---

## Analyse & Notebooks

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 39 | **Interaktive Linienansicht: Kritische Streckenabschnitte** — Neue Plotly-Karte in `03_analysis_4-spatial.ipynb`: Linie wählbar → Linienverlauf auf Karte → Haltestellen nach Ø Delay eingefärbt (grün → rot) → Top-3 Problemstops annotiert. Frage: "Wo auf der Linie beginnt das Problem?" Nutzt GTFS Shapes aus `data/raw/gtfs/`. Basis für #40. | 1 |
| 40 | **Situationsvergleich: gleiche Linie, verschiedene Kontexte** — Erweiterung von #39: dieselbe Linien-Karte filterbar nach Normal · Event · Winter (has_snow=True) · Rush-Hour (17–19h) · Late Night (21h+). Zeigt wie sich das Streckenbild je nach Kontext verändert. Braucht #39 als Basis. | 2 |
| 9 | **Linie 12 Baustellen-Zeitraum** (Jan 2023 – Jun 2024) validieren — genaue Daten aus VBZ-Quellen bestätigen, dann: herausfiltern oder als Binary-Feature kodieren? | 2 |
| 14 | **Events-Notebook: Haltestellen- + Linien-Ranking** — analog zu Meteo-Notebook. Welche Stops/Linien leiden am meisten unter Events? `analytics/events.py` erweitern. | 2 |
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
| 27 | **Interaktives Prediction-Tool** — Streamlit-App: Dropdown Stop/Linie/Stunde/Wetter → vorhergesagter Delay. LightGBM direkt laden, kein Server. Konzept im Planmodus entwerfen. | 2 |
| 31 | **Dashboard — Spielmodus + Vorhersagemodus** — Zwei Modi: (1) Spielmodus: explorative Historik-Ansicht mit interaktiven Heatmaps, Zeitreihen und Karten; (2) Vorhersagemodus: Eingabemaske Stop × Linie × Stunde × Wetter → Delay. Erweitert #27 um den explorativen Modus. Tooling-Entscheidung ausstehend (Streamlit vs. Dash). | 2 |
| 42 | **Dwell-Optimierungs-Simulator** — Zweites Prediction-Tool: Nutzer gibt modifizierte `dwell_time`-Werte für Haltestellen/Linien ein → lgbm_v1 berechnet neue Delays → Δ-Delay wird angezeigt. Schließt den Kreis: Analyse (dwell_time = Feature #1) → Modell (LightGBM) → Handlungsempfehlung (Puffer +10s → Δ MAE?). Umsetzung in `06_prediction_4-dwell_simulator.ipynb`. | 1 |
