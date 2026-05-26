# BACKLOG.md — zh-tram-flow
### Projektspezifische offene Tasks + Ideen

Offene Punkte die während der Arbeit auffallen aber nicht sofort umgesetzt werden.
Erledigte Items → als Pointer in PROCESS_LOG dokumentieren, hier entfernen.

Prio: `1` = hoch · `2` = mittel · `3` = niedrig

---

## Präsentation

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 19 | **Präsentation zh-tram-flow (10–15 Min · ~11 Slides)** — Gliederung: (1) Einleitung + Tech Stack · (2–3) Data Engineering · (4) Projekt Scope · (5) EDA & Preparation · (6–8) Analyse & Insights · (9) Preprocessing & Baseline · (10) Modell & Evaluation · (11) Live Vorhersage | 2 |
| 20 | **Präsentation als Claude-Workflow-Übungsfall** — Reveal.js HTML mit Claude bauen: CLAUDE.md schreiben → Explore → Plan → Draft → Code → Review → Final `reports/presentation.html` | 2 |
| 21 | **Präsentation — Industry Know-how** — Beating the naive baseline · Temporal Split · Feature Leakage · Large-scale ML · Feature Engineering as Analysis Output | 2 |
| 22 | **Präsentation — Data Engineering Story** — Datenmenge als roter Faden: 38 GB raw → 94 Mio. Zeilen → 55.5 Mio. Train → 32 Features ML-ready | 2 |
| 23 | **Präsentation — Modern Stack Argument** — LightGBM + Polars auf Laptop: 55M Zeilen Training in 18 Min, Prediction in 3.5 Min | 2 |
| 24 | **Präsentation — Analyse diktiert das Modell** — 55 Findings haben Feature Engineering direkt diktiert. Botschaft: "Ich habe nicht einfach ein Modell trainiert." | 2 |
| 25 | **Präsentation — Feature Engineering als Analyse-Output** — Finding → Feature zeigen: F-TEMP-01 → `hour` · F-WEAT-01 → `has_snow` · F-SPAT-01 → `stop_name` | 2 |
| 26 | **Präsentation — Live Vorhersage als HTML-Widget** — Predictions vorberechnen → JSON → JavaScript-Lookup. Kein Server nötig. Dropdown: Stop × Linie × Stunde × Wetter-Flag | 2 |
| 28 | **Präsentation — Kernthese + Impact-Aussage schärfen** — Eine klare Hauptbotschaft formulieren: Was ist die eine Erkenntnis, die bleibt? Aktuell wirkt die Präsentation wie eine solide Analyse ohne konkreten Punch. Ziel: Thesis als Einstieg und Abschluss, jede Slide trägt zur Kernaussage bei. | 2 |
| 29 | **Präsentation — Design überarbeiten** — Schlichter, eleganter, professioneller. Weniger Elemente pro Slide, mehr Whitespace, saubere Typographie. | 2 |
| 30 | **Präsentation — Impact-Momente inszenieren** — Versteckten Impact explizit herausarbeiten und als "Aha-Slides" aufbauen: Peripherie-Hotspots, kein Morgenrush, Fachmesse schlägt Taylor Swift, Feiertag = beste Tage, Netzausbau am falschen Ort. Keine Finding-Liste — eine Überraschung pro Slide. | 2 |

---

## Portfolio-Aufbereitung

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 41 | **Key-Visual ins README** — Einen der starken Plots aus `reports/figures/` auswählen, in README einbinden (`![...](reports/figures/...)`). Einziger A-Punkt im Portfolio-Check — ohne Visual ist der GitHub-Auftritt leer. Kandidaten: `geo-delay-hotspots.png` (Karte, sofort verständlich) oder `tempo-day-hours.png` (Peak 21h, kein Morgenrush). | 1 |
| 10 | **Portfolio-Beschreibung** — Findings-System (strukturierte IDs, Impact, Action, Status) als bewusste Engineering-Entscheidung hervorheben. Analogie zu Ticket-Systemen. Gehört in README + Bewerbungsunterlagen. | 1 |
| 34 | **Single Source of Truth für Zahlen + Metriken** — Audit: Welche Zahl steht wo? Für jeden Fakt (MAE, Baseline, Zeilenzahlen, Finding-Counts) einen Primärort (Notebook-Zelle) festlegen. Alle anderen Vorkommen durch Pointer ersetzen. Kein Fakt doppelt in MD-Files. | 1 |
| 35 | **Reporting aufräumen** — File-Naming und Exports auf konsistente Konvention bringen: `plotly_chart_1/2/3.html` in `figures/` umbenennen oder entfernen, `index.html` Zweck klären, PNG-Naming vereinheitlichen. | 1 |
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
| 32 | **Modell-Tuning** — LightGBM v1 Hyperparameter systematisch optimieren (Optuna). Ziel: MBE +8.3s adressieren und MAE unter 45.7s drücken. Ergebnis: `lgbm_v2.txt`. | 2 |
| 33 | **Zweites Modell** — Alternativmodell als Vergleich trainieren und gegen LightGBM v1 benchmarken. Kandidaten: XGBoost (strukturell ähnlich, fairer Vergleich) · Ridge Regression (interpretabel, Kontrast zur Boost-Komplexität). | 3 |

---

## Tools

| # | Beschreibung | Prio |
| :--- | :--- | :--- |
| 27 | **Interaktives Prediction-Tool** — Streamlit-App: Dropdown Stop/Linie/Stunde/Wetter → vorhergesagter Delay. LightGBM direkt laden, kein Server. Konzept im Planmodus entwerfen. | 2 |
| 31 | **Dashboard — Spielmodus + Vorhersagemodus** — Zwei Modi: (1) Spielmodus: explorative Historik-Ansicht mit interaktiven Heatmaps, Zeitreihen und Karten; (2) Vorhersagemodus: Eingabemaske Stop × Linie × Stunde × Wetter → Delay. Erweitert #27 um den explorativen Modus. Tooling-Entscheidung ausstehend (Streamlit vs. Dash). | 2 |
