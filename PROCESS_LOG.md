# PROCESS_LOG.md – Zürich Tram Flow

> Projektverlauf und AI-Kontext-Einstieg.
> Dieses File ist der Einstiegspunkt für neue Claude-Sessions.

---

## Projekt-Übersicht

| Feld | Inhalt |
| :--- | :--- |
| Projektname | Zürich Tram Flow |
| Repo | `zh-tram-flow` |
| Typ | DANSC (EDA + Modellierung + Dashboard) |
| Erstellt | 2026-05-11 |
| Status | 🟢 Phase 4 — Modellierung (LightGBM v1 trainiert · Test MAE 45.7s) |
| Nächster Schritt | `06_prediction_3-evaluation.ipynb` ausbauen · Fehleranalyse · Portfolio-Aufbereitung starten (BACKLOG #10, #19) |
| Datenbasis | `sf_data-research` — Phase 0 abgeschlossen |
| Stack | Python · Polars · Pandas · GeoPandas · Plotly |

---

## Datenbasis auf einen Blick

Die gesamte Data-Engineering-Phase ist in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) dokumentiert.

**Master-Datensatz:** `data/raw/zh-tram-data-master.parquet`
- ~94.4 Mio. Zeilen · 26 Spalten · ~541 MB
- Enthält: IST-Verspätungsdaten + GTFS-Haltestellen + Meteo-Stundenwerte + Events
- Zeitraum: 2023–2025 · Betreiber: VBZ Zürich · Produkt: Tram

**GTFS-Referenztabellen:** `data/raw/gtfs/`
- 9 Parquet-Dateien (Stops, Routes, Shapes, Trips — Tram + Gesamtnetz)
- Referenzjahr: 2024

---

## Verlauf

### 2026-05-11 — Projekt aufgesetzt (wgnd-scaffolding)

- Projektstruktur mit `wgnd-scaffolding` generiert (`--slug zh-tram-flow --type DAN`)
- Git-Repo initialisiert: `git@github.com:kaywiegand/zh-tram-flow.git`
- Scaffolding in dieser Session grundlegend überarbeitet (Details → `wgnd-scaffolding/PROCESS_LOG.md`):
  - `--slug` Pflichtfeld, Ordner = Slug, `src/zh_tram_flow/` mit Unterstrichen
  - `PROCESS_LOG.md`, `ROADMAP.md`, `CLAUDE.md` automatisch erstellt
  - Repo-Naming Convention festgelegt: kein Typ-Prefix, Hyphens als Standard

### 2026-05-11 — Startpunkt aus sf_data-research übertragen

**Was wurde gemacht:**
- `README.md` vollständig neu geschrieben — Projektbeschreibung aus sf_data-research übernommen,
  Struktur auf Scaffolding-Layout angepasst, Python-Imports korrigiert (Bindestriche → Unterstriche),
  Verweis auf sf_data-research und wgnd-toolkit ergänzt
- `ROADMAP.md` aktualisiert — Phase 0 (Research) als abgeschlossen markiert,
  Phasen 1–4 mit konkreten Analyse-Fragen, Visualisierungen, Modellierungs-Tasks und
  offenen Entscheidungen aus sf_data-research übernommen
- `notebooks/00_introduction.ipynb` gefüllt:
  - Project Facts, Scenario, Mission, zentrale Fragen
  - Methode & Metriken
  - Sektion "Datenbasis & Data Engineering" mit Verweis auf sf_data-research,
    Übersicht aller Notebooks und Entscheidungstabelle
  - Vollständiges Data Dictionary (26 Spalten mit Typ, Quelle, Beschreibung)
  - GTFS-Referenztabellen dokumentiert
  - Setup-Zellen mit korrekten Imports (`zh_tram_flow`)
  - Dateicheck-Zellen (Schema, Zeilenanzahl, GTFS-Übersicht)
- `data/raw/zh-tram-data-master.parquet` kopiert aus `sf_data-research/data/interim/vbz/vbz_master.parquet`
- `data/raw/gtfs/` kopiert aus `sf_data-research/data/interim/vbz/gtfs/` (9 Parquet-Dateien)

**Offene Entscheidungen für Phase 2 (aus sf_data-research übernommen):**

| Entscheidung | Kontext |
| :--- | :--- |
| Dashboard-Tooling | Dash + Plotly vs. Streamlit vs. Tableau — nach EDA entscheiden |
| Zeitreihe vs. klassisches ML | Erst nach EDA sinnvoll zu entscheiden |
| Split-Strategie | Jahres-Split als Einstieg (2025 als Test-Jahr) — in Phase 3 verfeinern |
| Geo-Bibliothek für Dashboard | Folium (interaktiv, einfach) oder Plotly (performanter) |

---

### 2026-05-12 — EDA abgeschlossen (`01_exploration.ipynb`)

**Was wurde gemacht:**
- `01_exploration.ipynb` vollständig aufgebaut und finalisiert
- Sections: Basic Stats · Completeness (C1–C4) · Integrity (I1–I5) · Distribution ·
  Correlations (R1–R5) · Outlier Detection (O1–O5) · Features Inspection · Key Findings
- Datenqualitäts-Findings dokumentiert: 16 Befunde, topic-gruppiert mit "Vor Split?"-Spalte
- Modellierungs-Entscheidung: XGBoost (schwache lineare Korrelationen → Schwellenwert-Effekte)
- Feature-Ideen-Tabelle erstellt: 15 Features (Zeit, Wetter-Flags, Kategoriale, Interaktionen)
- Cleaning-Prognose: ~1,7 Mio. Zeilen (~2%) strukturelle Reduktion
- Sampling-Strategie dokumentiert (`gather_every(2)` + `sample(fraction=0.1)`, ~5%)
- `ROADMAP.md` aktualisiert: Phase 1 ✅, Phase 2 AKTUELL, XGBoost + Cleaning-Architektur
- `BACKLOG.md` ergänzt: wgnd-toolkit #2/#3, dansc_zh-tram-flow #2/#3

**Technische Entscheidungen:**
- Split-Strategie: 2023–2024 Train / 2025 Test (temporal, kein Random Shuffle)
- Delay-Cleaning-Grenze: `|delay| > 3.600s` (±1h) als Rausfilter-Schwelle
- Linien 50/51/E behalten (Sonder-/Nachtlinien — Entscheidung vertagt)
- `wgnd.inspect_correlations` auf Sample — Korrelationsmatrix aus ~4.5 Mio. Zeilen

---

### 2026-05-13 — Preparation aufgebaut (`02_preparation.ipynb` + `cleaning.py`)

**Was wurde gemacht:**
- `src/zh_tram_flow/cleaning.py` neu erstellt:
  - 6 strukturelle Cleaning-Funktionen (Polars LazyFrame)
  - `structural_cleaning_pipeline()` — lazy, vor dem Split
  - `impute_meteo_rolling()` — Forward/Backward Fill, nach dem Split
  - `report_step()` für Cleaning-Reporting
- `02_preparation.ipynb` komplett neu gebaut (vorher: leeres Scaffold):
  - Intro mit Pipeline-Diagramm + Leakage-Prinzip
  - EDA-Findings als Cleaning-Agenda
  - Phase 1: strukturelles Cleaning via `cleaning.py` → `interim/zh-tram-structural-clean.parquet`
  - Phase 2: Temporal Split mit Strategie-Erklärung → `interim/train_raw.parquet` + `test_raw.parquet`
  - Phase 3: Meteo-Imputation (Forward/Backward Fill) → `processed/train_prepared.parquet`
  - Phase 4: Zeitfeatures + Wetter-Flags → `processed/train_features.parquet`
- `01_exploration.ipynb` finalisiert: FutureWarning gefixt, Beschriftungen bereinigt, Distribution-Scale-Fix

**Notebook noch nicht ausgeführt:** `02_preparation.ipynb` ist aufgebaut aber noch nicht auf den
echten Daten gelaufen — Cleaning-Zahlen sind Prognosen aus der EDA.

---

### 2026-05-13 bis 2026-05-15 — Analyse-Phase (03_analysis_* Notebooks)

**Was wurde gemacht:**
- Alle 6 Analyse-Notebooks aufgebaut und vollständig mit Daten befüllt:
  - `03_analysis_0-overview.ipynb` — Zentrale Findings-Tabelle (50+ Findings, F-TARGET bis F-EVNT)
  - `03_analysis_1-target.ipynb` — Zielvariable, OTP, Cancellations, Delay-Verteilung
  - `03_analysis_2-network.ipynb` — GTFS-Netzveränderungen, Einlaufzeit, Hotspots
  - `03_analysis_3-temporal.ipynb` — Stunden, Wochentag, Monat, Saison, Jahrestrend
  - `03_analysis_4-spatial.ipynb` — Haltestellen, Stadtkreise, Linien-Ranking
  - `03_analysis_5-meteo.ipynb` — Schnee, Regen, Temperatur, Niederschlagsintensität
  - `03_analysis_6-events.ipynb` — Feiertage, Events, Event-Typen
- Alle Beobachtungszellen mit tatsächlichen Zahlen aus den Show-DF-Outputs korrigiert
- Key-Findings-Tabelle im Overview vollständig aktualisiert (alle 50+ Findings auf `done`)
- Kernfragen & KPIs Sektion im Overview mit verifizierten Werten befüllt

**Wichtige Erkenntnisse (Auswahl):**
- Kein klassischer Morgenrush: 7h liegt unter Netzschnitt; Peak bei 21h (Events-Abreisewelle)
- Hotspots sind periphere Aussenkorridore, NICHT zentrale Knotenpunkte (0 Overlap)
- Schnee stärkster Wettereffekt (+54.0s); Kälte überraschend BESSER als Wärme
- Fachmessen schlechteste Event-Kategorie (66.0s); Feiertage bester Tag-Typ (−9.9s)
- Winter beste Jahreszeit (51.7s, OTP 88.9%); Herbst schlechteste
- 71.3% aller dwell_time = 0s — kein nutzbares kontinuierliches Feature

---

### 2026-05-15 bis 2026-05-16 — Analyse-Korrekturen + Methodische Entscheidungen

**Was wurde gemacht:**
- Alle Beobachtungszellen nochmals geprüft und mit echten Tabellenwerten belegt
- Verständliche Erklärungen zu komplexen Themen in Notebooks eingefügt:
  - OTP 120s-Schwellwert: VBZ-Standard / VDPW dokumentiert (target + overview)
  - Datendefinitions-Änderung Juli 2024: einfache Erklärung in target-Notebook
  - Fahrplanwechsel Dez 2023: einfache Erklärung in target-Notebook
  - Linie E Pro/Contra + Entscheid: in OTP-per-Line-Beobachtung
  - Starthaltestellen-Verzerrung: Beweis-Plot + Erklärung in target-Notebook
- `is_windy` aus Weather-Analyse entfernt (NaN überall, nie korrekt befüllt)
- Schulferien-Streifen in Temporal Full-Year-Trendplot eingebaut (ZH Schulferien 2023–2025)
- Bereinigter Delay-per-Year-Plot mit Trendlinien im Target-Notebook ergänzt
- Starthalte-Verzerrungsanalyse als eigener Abschnitt im Target-Notebook (3 Beweis-Plots)

**Strukturelle Entscheidungen (Methodische Weichenstellung):**

| Entscheidung | Kategorie | Begründung |
|:---|:---|:---|
| `canceled == False` für Delay-Analyse | 🔴 Filter | Datendefinitions-Artefakt Jul 2024 |
| Nov/Dez 2025 aus Train+Test | 🔴 Filter | GTFS-Vorbereitungsartefakt |
| `stop_sequence > 1` für Delay-Baseline | 🔴 Filter | Starthalte-Puffer verfälscht Metriken |
| Linie E ausschliessen | 🔴 Ausschluss | Strukturell nicht vergleichbar (OTP 56%) |
| `gtfs_year` als Feature | 🟡 Feature | Netzwechsel Dez 2023 für L9/L11/L13 |
| `is_windy` entfernen | 🔴 Feature-Drop | NaN überall, kein informativer Wert |
| Linie 18/L50/L51 dokumentieren | 🟢 Kontext | Temporäre Linien, zu wenig Daten |

Diese Entscheidungen sind in `02_preparation.ipynb` als "Bereinigungsstrategie"-Sektion dokumentiert
und fliessen in `05_feature_engineering.ipynb` ein.

**Notebook-Struktur aktualisiert:**
- `04_insights.ipynb` (bestehendes Scaffold) → bleibt als Report/Business-Communication
- `05_feature_engineering.ipynb` → NEU angelegt (Feature Engineering + Modell-Vorbereitung)

---

---

### 2026-05-19 — Meta-Alignment: Notebooks finalisiert, Docs synchronisiert

**Was wurde gemacht:**

- **`03_analysis_3-temporal.ipynb`**: F-TEMP-10 ergänzt (Nacht-/Partyverkehr 0–3h Fr/Sa), Präsentation-Spalte in Key Findings hinzugefügt
- **`03_analysis_2-network.ipynb`**: Grosse Überarbeitung:
  - Folium vollständig entfernt → Plotly Mapbox für alle Karten
  - GTFS-Ladelogik + Änderungsmatrix-Aufbau in `analytics/network.py` ausgelagert (`load_gtfs()`, `build_changes_matrix()`)
  - `plot_network_changes_map()` und `plot_service_quality_district_map()` als Plotly-Funktionen in `network.py`
  - Stale Platzhalter, tote Datei-Links, leere Zellen, Emojis bereinigt
  - Beobachtungen mit echten Haltestellen-Namen (GTFS-Artefakt K1 vs. echte Erweiterungen K3/K8) korrigiert
  - F-NET-09 ergänzt: Netzausbau vs. Delay-Hotspots — kein Overlap
- **`03_analysis_0-overview.ipynb`**: Vollständige Finalisierung:
  - Key Findings auf 55 Findings aktualisiert (+8 neue: F-SPAT-09/10/11, F-WEAT-07/08/09, F-TEMP-10, F-NET-09)
  - `Präs.` Spalte (hot / story / —) für alle 55 Findings
  - Executive Summary eingefügt (5 Kernbotschaften)
  - Report-Auswahl Section (hot+story, 6 Themenblöcke)
  - Kernfragen: "Central (15 Linien)" → "Haldenegg (15 Linien, 44.5s)" korrigiert
  - Modelling Insights: stale Meta-Kommentare entfernt, "Rushhour morgens" → korrekt auf 21h-Peak umgeschrieben
  - Line Colors: Emojis entfernt
  - 2 leere Zellen gelöscht
- **`README.md`**: Version 0.3.0, Status aktualisiert, neue Sektion "Was die Daten zeigen" (5 hot findings), Tech Stack Sektion, Notebook-Struktur auf aktuelle 10 Notebooks aktualisiert, MVP Phase ✅
- **`ROADMAP.md`**: Phase 2 vollständig abgehakt (6 Notebooks + 55 Findings), Phase 3 auf "Feature Engineering" umbenannt mit vollständiger Feature-Kandidaten-Tabelle (Prio 1/2/3 mit F-Referenzen), Offene Entscheidungen aktualisiert

---

### 2026-05-20 — Prediction Phase gestartet · LightGBM v1 trainiert

**Was wurde gemacht:**

- **`06_prediction_0-overview.ipynb`** neu erstellt: Vorhersage-Ansatz, konkretes Szenario, Modellvergleich (LightGBM vs. Alternativen), vollständige Metriken-Tabelle (10 Metriken inkl. Ausschluss-Begründungen), Baseline-Erklärung
- **`06_prediction_1-baseline.ipynb`** neu erstellt und ausgeführt:
  - 4 regelbasierte Baselines (Grand Mean / Hour Mean / Line Mean / Stop Mean)
  - **Stop Mean = 50.0s MAE** als Benchmark definiert
- **`06_prediction_2-model.ipynb`** neu erstellt und ausgeführt:
  - LightGBM v1 · 5 native Categorical Cols
  - Temporaler Validation-Split: 2023–Jun 2024 Train / Jul–Dez 2024 Val
  - Early Stopping nach 512 Iterationen
  - Val MAE: 49.0s · **Test MAE: 45.7s** (Baseline −4.3s ✅)
  - Export: `data/models/lgbm_v1.txt` + `lgbm_v1_meta.json` + `test_predictions.parquet`
- **`06_prediction_3-evaluation.ipynb`** Skeleton angelegt
- `pyproject.toml`: `lightgbm>=4.0` in dsc-Extras ergänzt
- `libomp` via Homebrew installiert (macOS-Dependency für LightGBM)
- Metriken-Sektion im Overview erweitert: SMAPE, MdAE, MSLE, MBE, Pinball Loss mit Ausschluss-Begründung

**Technische Entscheidungen:**

| Entscheidung | Ergebnis |
|:---|:---|
| Modell | LightGBM (statt XGBoost) — native Cat-Support, schneller |
| Primärmetrik | MAE — direkt in Sekunden, kommunizierbar |
| Modell-Speicherformat | LightGBM nativ (`.txt`) — nicht Pickle/Joblib |
| Validation-Split | Jul–Dez 2024 — kein Data-Leakage aus 2025 |
| Leaky Features | `departure_delay`, `delay_delta` ausgeschlossen |

---

### 2026-05-19 — Vollständiges Projekt-Review (AI-Analyse)

Vollständiger Review der abgeschlossenen Analyse-Phase — gelesen wurden: README, ROADMAP, alle 6 Analyse-Notebooks, `04_insights.ipynb`, `03_analysis_0-overview.ipynb` und ein repräsentativer Blick in `src/zh_tram_flow/analytics/`.

---

**Backlog-Kandidaten**

| Priorität | Bereich | Beschreibung |
|:---|:---|:---|
| **Hoch** | Code | Tests decken nur Scaffold-Dummy-Funktionen ab (57 Zeilen, 4 Tests). 5.187 Zeilen Analytics-Code haben 0% Testabdeckung. |
| **Hoch** | Doku | `04_insights.ipynb` enthält ausschließlich Text-Zellen — keine Code-Zellen mit Plot-Calls oder `show_df()`-Ausgaben. Report ist Prosa, aber kein ausführbares Notebook. Muss gebaut werden vor HTML-Export. |
| **Mittel** | Analyse | Top-2 Hotspot-Stops (Bertastrasse 181.6s n=1.307, Sihlfeld 167.0s n=1.307) haben sehr kleines n vs. Enzenbühl (n=292.204). Methodenproblem: Mittelwerte aus kleinen n sind instabil. n-Schwelle im Plot hochsetzen (≥ 50.000) oder als "Randfälle" explizit ausweisen. |
| **Mittel** | Code | `spatial.py` importiert `matplotlib` — Projekt hat auf Plotly standardisiert. Prüfen ob Import aktiv genutzt wird oder nur Überbleibsel. |
| **Mittel** | Analyse | Linie 51 hat höchsten `delay_delta` aller Linien (+20.2s, weit über L11 +6.2s) — nirgendwo interpretiert. Zumindest eine Beobachtungszeile im Spatial-Notebook. |
| **Mittel** | Doku | `00_introduction.ipynb` Workflow-Sektion veraltet (BACKLOG #7). Zeigt nicht aktuelle 10-Notebook-Struktur. |
| **Mittel** | Analyse | Kaskadeneffekt (`prev_trip_delay`, F-NET-07) ist als Feature-Kandidat gelistet aber nie analysiert. Explorations-Check: Hat der Datensatz trip_id-Kontinuität über mehrere Fahrten? Vor Feature-Engineering klären. |
| **Niedrig** | Struktur | `reports/` Ordner wahrscheinlich leer. Kein exportierter Plot committet. |
| **Niedrig** | Code | `_get_cfg()` Fallback-Logik in den Analytics-Modulen ist fragil (try/except auf Import-Ebene mit anonymer `_FallbackCfg`-Klasse). Schwer debuggbar wenn wgnd-toolkit umbricht. |
| **Niedrig** | Doku | Kein CHANGELOG. Sinnvoll ab Phase 4 wenn Breaking Changes an Features entstehen können. |

---

**Top-Insights für den Report (Präsentationswert-Ranking)**

**1. Strukturelle Pufferschwäche** — 71.5% aller Halte akkumulieren Delay; 71.3% aller `dwell_time` = 0s. Kein Wetter-, kein Event-Problem — ein Fahrplan-Design-Problem. Visualisierung: Anteil akkumulierend vs. reduzierend + `dwell_time`-Histogramm (fast alles bei 0s).

**2. Kein Morgenrush** — 7h liegt bei 48.9s (unter Netzschnitt). Peak 21h (67.9s) durch Abreisewellen. Donnerstag schlechtester Wochentag (60.4s, P95=194s), nicht Freitag. Visualisierung: Linienchart nach Stunde + Bar-Chart Wochentage.

**3. Hotspots an der Peripherie, nicht im Zentrum** — Central (48.3s, 15 Linien) und Paradeplatz (48.2s, 14 Linien) liegen unter Netzschnitt. Enzenbühl (93.8s) und Balgrist (85.2s) führen die echte Liste an. 0 Überschneidung zwischen Top-Dichte- und Top-Delay-Stops. Visualisierung: Karte mit Delay-Blasen oder Scatter Liniendichte vs. Delay.

**4. Schnee stärkster Einzelfaktor — geografisch trennbar von Regen** — Schnee +54s, OTP −10.9pp. Schnee trifft Höhenlagen (K10/K4/K12), Regen trifft Flusstäler (K5). L17 leidet stark unter Regen (+41.2s), kaum unter Schnee; L9 umgekehrt (+75.9s Schnee). Visualisierung: zwei Choropleth-Karten "Schnee-Effekt" / "Regen-Effekt" nebeneinander.

**5. Feiertage beste Tage** — 46.3s vs. 56.2s normal (−9.9s). OTP 90.6% vs. 87.0%. Rückgang des Berufsverkehrs übertrifft Event-Effekt. Direkte Implikation: ÖPNV funktioniert besser wenn weniger Autos unterwegs sind. Visualisierung: Vergleichs-Bar "Feiertag / Normal / Großevent".

**6. Größter Fahrplanwechsel VBZ-Geschichte unsichtbar** — Dez 2023 (L9/L11/L13 fundamental umgebaut): netzweit +0.5s. Geänderte Linien (L11 +5.3s) und unveränderte Linien (L15 +5.2s) bewegen sich identisch. Visualisierung: Zeitreihe 2023–2025 mit vertikaler Linie Dez 2023, veränderte vs. stabile Linien.

**7. Netzausbau am falschen Ort** — Erweiterungen nach K3 (55.7s) und K8 (63.7s). K11 (68.3s, OTP 83%) und K12 (66.3s) bekamen nichts. 0 Überschneidung Investitionsort / Problemort. Visualisierung: Choropleth "Neue Haltestellen 2024" überlagert mit "Ø Delay pro Stadtkreis".

**8. Berufsmesse schlägt Taylor Swift** — Trade Fairs schlechteste Event-Kategorie (66.0s, OTP 84%). Schlechtester Tag im Datensatz: Berufsmesse 21.11.2024 (192.5s, OTP 54.5%). Taylor Swift: 75.4s — weniger als halb so viel. Visualisierung: Bar-Chart Event-Kategorien + Timeline der schlimmsten Einzeltage mit annotierten Labels.

**9. Winter beste Jahreszeit** (Bonus) — Winter 51.7s (OTP 88.9%) besser als Frühling und Sommer. Herbst schlechteste Jahreszeit (61.2s). Kfz-Rückgang im Winter übertrifft Schnee-Effekt.

---

## Aktueller Stand

**Phase 0 (Data Engineering):** ✅ Abgeschlossen — in `sf_data-research`
**Phase 1 (Setup & Dateneinstieg):** ✅ Abgeschlossen
**Phase 2 (EDA & Analyse):** ✅ Abgeschlossen — 6 Analyse-Notebooks · 55 Findings
**Phase 3 (Feature Engineering):** ✅ Abgeschlossen — `train_final.parquet` / `test_final.parquet` (55.5M Zeilen)
**Phase 4 (Modellierung):** 🔄 In Arbeit — LightGBM v1 trainiert · Test MAE 45.7s
**Phase 5 (Dashboard):** ⏳ Ausstehend

**Notebook-Übersicht:**
```
00_introduction.ipynb            ✅ fertig
01_exploration.ipynb             ✅ fertig
02_preparation.ipynb             ✅ ausgeführt — train/test_raw + prepared + features in data/
03_analysis_0-overview.ipynb     ✅ fertig (55 Findings · Executive Summary · Report-Auswahl)
03_analysis_1-target.ipynb       ✅ fertig
03_analysis_2-network.ipynb      ✅ fertig
03_analysis_3-temporal.ipynb     ✅ fertig
03_analysis_4-spatial.ipynb      ✅ fertig
03_analysis_5-meteo.ipynb        ✅ fertig
03_analysis_6-events.ipynb       ✅ fertig
04_insights.ipynb                🔄 Struktur + Texte + Code fertig — noch nicht ausgeführt
05_feature_engineering.ipynb     🔄 neu ausführen — test_features muss mit Nov/Dez 2025 rebuild werden
06_prediction_0-overview.ipynb   ✅ fertig — Ansatz, Metriken, Baseline, Szenario
06_prediction_1-baseline.ipynb   🔄 neu ausführen nach test_features rebuild
06_prediction_2-model.ipynb      ✅ ausgeführt — LightGBM v1: Test MAE 45.7s (481 Bäume)
06_prediction_3-evaluation.ipynb 🔄 Skeleton — Fehleranalyse ausstehend
```

**Nächste konkrete Schritte:**
1. `04_insights.ipynb` ausführen (Kernel neu starten → alle Zellen) — add_vline Fix noch offen
2. `06_prediction_3-evaluation.ipynb` ausbauen — Fehleranalyse nach Linie, Stunde, Wetter
3. HTML-Export: `jupyter nbconvert --to html --no-input --output-dir reports --output index 04_insights.ipynb`
4. Projekt-Wrap-up: README final, Portfolio-Text

---

### 2026-05-20 — Plot-Finalisierung für Präsentation

**Was wurde gemacht:**

10 Plot-Anpassungen in 5 Dateien — Ziel: konsistentes, präsentationsreifes Erscheinungsbild.

| Datei | Funktion | Änderung |
|:---|:---|:---|
| `visualization/insights.py` | `plot_monthly_delay_by_line` | Legende `ncol=8` (2 Zeilen, kein Overflow nach rechts) |
| `visualization/insights.py` | `plot_otp_by_line` | Ø-Linie gepunktet+gelb, Ziel-Linie grau+gestrichelt, `ncol=2` |
| `visualization/insights.py` | `plot_dwell_analysis` | Tramlinienfarben für Balken, Pufferzeit als graue gestrichelte Linie |
| `visualization/insights.py` | `plot_arrival_vs_departure_timeline` | Komplett rewritten → 3-Panel Daily Delay Timeline (wie `an.plot_daily_delay_timeline`), ohne Sonstiges |
| `analytics/spatial.py` | `plot_district_analysis` | Ø-Linien gepunktet, `lw=1.0` |
| `analytics/temporal.py` | `plot_hour_of_day` | Halt-Ereignisse-Linie aus Legende entfernt |
| `analytics/temporal.py` | `plot_day_of_week` | Kombinierte Legende, `ncol=3`, `frameon=False`, `lw=1.0` |
| `analytics/meteo.py` | `plot_weather_overview` | `frameon=False`, `ncol=2`, `alpha=0.7` |
| `analytics/events.py` | `plot_events_overview` | Normal-Referenzlinien grau+gepunktet (ANNO_REF) |
| `analytics/events.py` | `plot_daily_delay_timeline` | Sonstiges-Events aus Marker-Plot gefiltert |

**Nächste Schritte:**
- `04_insights.ipynb` neu ausführen (Kernel restart → Run All)
- `ins_arr_dep_timeline` Zelle mit `plot_arrival_vs_departure_timeline(lf_clean)` befüllen
- HTML-Export: `jupyter nbconvert --to html --no-input 04_insights.ipynb`

**Zweite Runde Plot-Refinements (2026-05-21):**

| Datei | Funktion | Änderung |
|:---|:---|:---|
| `visualization/insights.py` | `plot_dwell_analysis` | Rechte y-Achse für Dwell-Linie in beiden Panels; Labels oben auf Balken (grau); Legende zeigt nur die Dwell-Linie |
| `analytics/spatial.py` | `plot_district_analysis` | Linien-Annotations direkt an Referenzlinien, keine Legende; 85%-Ziel-Linie zurück auf `--` (kein Durchschnitt) |
| `analytics/events.py` | `plot_daily_delay_timeline` | 3 Subplots → 1 kontinuierlicher Plot 2023–2025 mit Jahresgrenzen |

---

### 2026-05-20 — Insights-Notebook Komplett-Umbau

**Was wurde gemacht:**

**Dramaturgie neu strukturiert** — 7 Abschnitte mit klarer narrativer Logik:
1. Netzstruktur — Das Netz ist stabil (Fahrplanwechsel unsichtbar)
2. OTP — Kein Puffer eingebaut (strukturelle Schwäche, neu: direkt nach Stabilität)
3. Geografie — Hotspots periphere Aussenkorridore
4. Temporalität — Peak 21h, kein Morgenrush
5. Meteorologie — Schnee stärkster Faktor, geografisch trennbar
6. Events — Feiertage beste Tage, Fachmessen schlechteste Kategorie
7. Netz — Ausbau am falschen Ort

**Neue Code-Zellen:**
- Plotly monthly delay mit 3 Fahrplanwechsel-Markierungen (Dez 2023, Baustellen-Ende, Dez 2024) — kein Netzschnitt
- Delay Delta Timeline (täglich, fill tozeroy)
- Arrival vs. Departure Timeline (gemeinsam, keine Ferien/Sonstiges-Marker)
- District Delay Choropleth (gleicher Kartentyp wie Netzausbau-Karte, blau→rot)

**Alle Narrativ-Texte** im Bullet-Style umgeschrieben — fette Kategorien, Zahlen als Bullets, kein Fließtext

**Technische Änderungen:**
| Datei | Änderung |
|:---|:---|
| `src/zh_tram_flow/analytics/meteo.py` | `plot_weather_stop_map()` erhält `vmax` Parameter — gleiche Farbskala für Schnee/Regen-Karten |
| `notebooks/06_prediction_2-model.ipynb` | `BASELINE_MAE` korrigiert: 50.7 → 50.0 |
| `notebooks/03_analysis_2/3/4-*.ipynb` | lf-Kommentarblock in Setup-Zellen ergänzt |

**Bekanntes offenes Problem:**
- `fig.add_vline(x=date_string)` wirft TypeError — x muss numerischer Timestamp sein (`pd.Timestamp(date).value / 1e6`)

---

## Präsentations-Fakten — Zahlen für Portfolio & Bewerbung

### Datenbasis
- **~94 Mio. Rohdatenpunkte** — 3 Jahre (2023–2025), 16 Tramlinien, VBZ Zürich
- **~55 Mio. Trainingszeilen** nach Cleaning + Filter (lf_clean)
- **~30 Mio. Testzeilen** (2025, inkl. Nov/Dez — nach Rebuild von test_features)
- Feature-Set dokumentiert in `05_feature_engineering.ipynb`

### Performance — Laufzeiten
| Schritt | Zeilen | Dauer |
|:---|:---|:---|
| Daten laden + Pandas-Konvertierung | 55.5M | ~20s |
| LightGBM Training (41M Train-Rows) | 41M | ~18 Min |
| Validation Prediction (14M Rows) | 14M | ~8 Min |
| Test Prediction + Export (~30M Rows) | ~30M | ~3.5 Min |
| **Gesamt Notebook-Laufzeit** | — | **~30 Min** |

### Modell-Ergebnisse
| Metrik | Stop Mean Baseline | LightGBM v1 | Gewinn |
|:---|:---|:---|:---|
| MAE (Test) | 50.0s | **45.7s** | −4.3s |
| RMSE (Test) | 77.4s | 75.6s | −1.8s |
| OTP ±60s | 71.9% | 77.5% | +5.6pp |
| MBE | — | +8.3s | — (zu optimistisch) |

### Fehleranalyse
- **Schwerste Stunden:** 17h (54.5s) · 16h (53.3s) · 18h (52.8s) — Rush-Hour
- **Schwerste Linien:** L11 (52.3s) · L8 (51.1s) · L15 (50.5s)
- **Beste Linien:** L12 (34.5s) · L6 (36.6s) · L17 (39.3s)
- **Schnee:** MAE 58.9s (n=39.920) — stärkste Schwäche
- **Regen:** MAE 49.6s · **Normal:** 45.4s

### Live-Szenario
- Input: Dienstag 17:00 · Paradeplatz · Linie 11 · leichter Regen
- Output: **48s vorhergesagter Delay**

### Bekannte Limitierungen (für Portfolio-Reflexion)
- `stop_name` als native Categorical statt Target Encoding — Verbesserungspotenzial v2
- MBE +8.3s — Modell systematisch zu optimistisch
- `prev_trip_delay` (Kaskadeneffekt) nicht implementiert — trip_id Kontinuität ungeprüft

---

### 2026-05-20 — Nov/Dez 2025 Anomalie: Untersuchung + Refactoring abgeschlossen

**Ausgangsbefund aus den Daten:**
- `departure_delay` explodiert ab exakt **14. November 2025** (delta: 6.1s am 13. Nov → 16.4s am 14. Nov → 30s+ bis 21. Nov)
- `arrival_delay` bleibt stabil — kein operativer Verspätungsanstieg
- Alle 15 Linien betroffen, alle Stops betroffen
- `arrival_schedule` + `departure_schedule` Werte: **komplett stabil** (kein j26-Fahrplan im Datensatz)
- Anomalie endet: **23. Dezember 2025** (neun Tage nach dem offiziellen Fahrplanwechsel 14. Dez)

**Was Webrecherche ergab:**
- Fahrplanwechsel (j26) offiziell: **14. Dezember 2025** — grösster in VBZ-Geschichte (10 von 14 Linien geändert)
- Neuer j26-Fahrplan in Apps & Online verfügbar: **"ab Mitte November 2025"** (VBZ/ZVV-Ankündigung)
- Bahnhofquai-Baustelle: erst ab 14. Dezember 2025 — kein November-Effekt
- **Kein spezifisches Ereignis für den 14. November 2025** publiziert oder auffindbar

**Wahrscheinlichste Erklärung (Datensatz-Artefakt):**

> Ab Mitte November 2025 (exakt: 14. Nov) begann VBZ den j26-Fahrplan **operativ vorzubereiten** — Fahrer-Einweisung, neue Umläufe, Probefahrten auf modifizierten Routen. Die tatsächlichen Abfahrtzeiten ("IST") orientierten sich zunehmend an den j26-Fahrzeiten, während der Referenzwert `departure_schedule` im Datensatz weiterhin j25 enthielt. Das erzeugt künstlich erhöhte `departure_delay`-Werte. `arrival_delay` bleibt davon unberührt, weil Haltestellenpositionen physisch unverändert blieben. Nach dem offiziellen Fahrplanwechsel (14. Dez) laufen IST und SOLL wieder im gleichen Regime → delta kehrt in KW52 zur Normalverteilung zurück.

**Fazit:**
- Kein Modell-Fehler, kein Analyse-Fehler — reines Messsystem-Artefakt an der Regime-Grenze j25/j26
- Exakte Ursache nicht abschliessend beweisbar ohne VBZ-interne Daten

**Entscheidung: Maskierung statt Ausschluss**

Statt Nov/Dez 2025 komplett zu filtern, werden `departure_delay` und `delay_delta` für Nov 14–Dez 23 2025 auf NaN gesetzt. `arrival_delay` (Zielvariable) bleibt unberührt. Neues `is_anomal`-Flag für Transparenz.

Begründung: `departure_delay` / `delay_delta` sind keine Modell-Features. Durch Maskierung statt Ausschluss gewinnen wir **+~5M Testzeilen (+~20%)** und vollständige November-Abdeckung (~58s Ø arrival_delay — schlechtester Monat, bisher komplett aus der Evaluation ausgeschlossen).

**Technische Umsetzung (2026-05-20):**

| Datei | Änderung |
|:---|:---|
| `src/zh_tram_flow/data/cleaning.py` | `mask_departure_anomaly()` + `apply_lf_clean()` + Konstanten `ANOMALY_START/END` |
| `src/zh_tram_flow/cleaning.py` | Re-export aller neuen Symbole |
| `src/zh_tram_flow/notebook.py` | `setup_analysis()` gibt 6 Werte zurück: `TRAIN, TEST, lf, lf_all, lf_delay, lf_clean` |
| `src/zh_tram_flow/features/final.py` | `apply_lf_clean()` via `mask_departure_anomaly()`, `is_test` Parameter entfernt |
| `03_analysis_1-target.ipynb` | Setup-Zelle + Anomalie-Dokumentation (Zellen 73 + f63a634c) aktualisiert |
| `03_analysis_2/3/4/5/6-*.ipynb` | Setup-Zellen auf 6-Rückgabewert migriert |
| `04_insights.ipynb` | Setup-Zelle migriert |
| `06_prediction_1-baseline.ipynb` | Setup-Zelle + inline Filter ersetzt durch `apply_lf_clean` |
| `05_feature_engineering.ipynb` | `is_test`-Parameter aus `apply_lf_clean`-Aufrufen entfernt |

**Offene Schritte nach diesem Refactoring:**
1. `05_feature_engineering.ipynb` neu ausführen → `test_features.parquet` mit Nov/Dez 2025 (~30M Zeilen)
2. `06_prediction_1-baseline.ipynb` neu ausführen → aktualisierte Benchmark-Zahlen
3. Analysis-Notebooks neu ausführen → Plots zeigen dann Nov/Dez 2025 (optional)

---

### 2026-05-26 — Workspace-Dokumentation konsolidiert · BACKLOG.md angelegt

**Was wurde gemacht:**

- **Workspace-Ebene umgebaut:** `docs/` Ordnerstruktur aufgesetzt — alle globalen MD-Files zentralisiert
- **`CLAUDE.md` (Workspace) komplett neu geschrieben** — Single Entry Point für alle Session-Typen:
  Session-Start Protokoll (Scope-Frage + Rollen-Frage), vollständiger Rollen-Katalog (9 Rollen),
  mechanische Post-Commit Checkliste, Pointer auf Portfolio-Workflow
- **`docs/CONVENTIONS.md` erstellt** — Zusammenführung von `docs/GLOSSAR.md` + Notebook-Konventionen:
  Notebook-Struktur, Wording-Glossar, Variablen-Konventionen, Qualitätsprüfung vor Commit
- **`docs/portfolio/`** neu: `STANDARD.md` (3 Lese-Ebenen, 5 Qualitätsdimensionen),
  `CHECKLIST.md` (Quality-Check-Vorlage → als `PORTFOLIO_CHECK.md` ins Projekt kopieren),
  `WORKFLOW.md` (5-Schritt Aufbereitungs-Prozess)
- **`ONBOARDING.md` (Workspace + Projekt) gelöscht** — ersetzt durch Session-Start-Block in `CLAUDE.md`
- **`zh-tram-flow/CLAUDE.md` auf ~30 Zeilen geschlankt** — Parquet-Pfad-Tabelle und Meteo-Join-Details entfernt
  (→ stehen in Notebooks); nur Projekt-Identität, Stack, Datenbasis-Regeln, projektspez. Konventionen behalten
- **`zh-tram-flow/BACKLOG.md` neu erstellt** — 22 projektspezifische Items aus Workspace-BACKLOG extrahiert,
  nach Themenblöcken gruppiert: Präsentation (19–26) · Portfolio-Aufbereitung · Analyse · Modell v2 · Tools
- **Prio-System geändert:** H/M/L → 1/2/3 (1 = hoch · 2 = mittel · 3 = niedrig)

**Strukturprinzip (fest etabliert):**

| Regel | Begründung |
|:---|:---|
| MD-Files = Meta-Files | Metriken, Findings, Outputs immer in Notebooks — nie in MD-Files kopieren |
| Kein Fakt in zwei Files | Redundanz erzeugt Drift — Pointer statt Kopie |
| PROCESS_LOG: Pointer auf Notebooks | Kein MAE, keine Zeilenzahlen direkt im Log |
| ROADMAP: konzeptionell | Ausgangslage → Phasen → Ziel — nur bei Phasenwechsel ändern |
| BACKLOG: operativ | Alle offenen Tasks hier, nach jeder Session aktualisieren |

---

### 2026-05-26 — Portfolio-Audit + Narrative-These eingebaut

**Was wurde gemacht:**

- **Portfolio-Review** durchgeführt: BACKLOG.md um Items 28–35, 36–41 ergänzt (Präsentation, Analyse, Reporting, Dashboard, Modell v2). Prio aller Präsentations-Items auf 2 gesetzt (nach portfolio-ready).
- **`PORTFOLIO_CHECK.md`** angelegt — Audit der 5 Dimensionen: 1 A-Punkt (Key-Visual fehlt im README), 7 B-Punkte (Evaluation unvollständig, Introduction veraltet, SoT-Audit ausstehend, Reporting unordentlich), Reproduzierbarkeit grün.
- **Kernthese verankert** (Backlog #36 + #37, erledigt):
  - `03_analysis_0-overview.ipynb`: Synthese-Block nach Executive Summary — drei Findings als eine Aussage
  - `04_insights.ipynb`: neue Sektion "Kernthese" als Einstieg vor "Netzstruktur"
  - `03_analysis_1-target.ipynb`: Root-Cause-Sektion direkt nach OTP-Befund — verbindet F-TARGET-03 (71.5% akkumulieren) mit F-SPAT-08 (71.3% dwell_time = 0s)

**Methodische Entscheidung:**
Kernthese definiert: dwell_time = 0s (Fahrplan-Design) + Peripherie-Hotspots (Geografie) + Netzausbau am falschen Ort (Investment) = drei Befunde, eine Aussage. Verankert in allen relevanten Notebooks — nicht mehr als Einzel-Findings versteckt.

**Nächster Schritt:** #38 — Hebel-Vergleich: dwell_time vs. Wetter vs. Events vs. Tageszeit als relativer Vergleichs-Plot

---

### 2026-05-21 — Insights-Report HTML-Export finalisiert

**Was wurde gemacht:**

- **`04_insights.ipynb`** — Fahrplanwechsel-Narrative korrigiert:
  - Dez 2023: "grösster Netzumbau" korrekt (war es zu dem Zeitpunkt — 10 von 17 Linien)
  - Dez 2025: Korrekturfakten aus Wikipedia — 7 von 18 Linien, L50/L51 als Baustellen-Linien für Bahnhofquai-Sanierung bis Dez 2026
  - Fehlender Leerzeichen-Trenner zwischen den zwei Abschnitten gefixt
- **Setup-Zelle** in `04_insights.ipynb`: `pio.renderers.default = "notebook_connected"` hinzugefügt — damit erzeugen zukünftige Notebook-Runs direkt HTML-kompatible Plotly-Outputs (CDN-Link im Output statt nur JSON)
- **Plotly-Maps in HTML** gefixt:
  - Ursache: SRI-Integrity-Hash im Plotly CDN-Script schlug fehl (Browser blockiert Script still)
  - Fix: `integrity`- und `crossorigin`-Attribute aus dem `<script>`-Tag entfernt
  - Betrifft: gespeicherter Notebook-Output (cell `f1692f25`) + `reports/insights.html`
- **HTML-Export** `reports/insights.html` neu generiert — 3.4 MB, 3× `Plotly.newPlot`, alle Karten sichtbar ✅
- **Reports-Aufräumen**: 16 PNG-Figures zu `reports/figures/` hinzugefügt, `tram_lines_map.html` von `reports/figures/` nach `reports/` verschoben, `reports/tables/.gitkeep` entfernt
- Stale Notebooks gelöscht: `notebooks/03_analysis_5-weather.ipynb`, `notebooks/04_feature_engineering.ipynb`, `DISCUSSION.md`

**Technische Erkenntnis — Plotly in nbconvert HTML-Exports:**

| Thema | Detail |
|:---|:---|
| MIME-Typ | Plotly speichert `application/vnd.plotly.v1+json` — nbconvert kennt das Format nicht |
| Fix (dauerhaft) | `pio.renderers.default = "notebook_connected"` → Plotly erzeugt auch `text/html` Output |
| Fix (einmalig) | `pio.to_html(fig, include_plotlyjs='cdn')` retroaktiv in gespeicherte Outputs injiziert |
| SRI-Problem | Plotly Python 6.7.0 bundelt Hash für eigene Plotly.js-Datei — CDN liefert geringfügig andere Minifizierung → Hash schlägt fehl |
| Lösung | `integrity`- und `crossorigin`-Attribute entfernt — CDN lädt ohne SRI-Check |
| Embedding | Matplotlib/Seaborn-Charts: `data:image/png;base64,...` direkt im HTML eingebettet — keine separaten Bilddateien |

**Nächste konkrete Schritte:**
1. `06_prediction_3-evaluation.ipynb` ausbauen — Fehleranalyse nach Linie, Stunde, Wetter
2. Projekt-Wrap-up: README final, Portfolio-Text

---

### 2026-05-26 — Hebel-Vergleich umgesetzt (Backlog #38)

**Was wurde gemacht:**

- **`plot_lever_comparison(lf)`** neu in `src/zh_tram_flow/visualization/insights.py`:
  - Struktureller Hebel dynamisch berechnet: `mean(delay_delta) × avg_stops_per_trip`
  - 7 externe Faktoren (Schnee, Starkregen, November, Abend 21h, Grossereignis, Donnerstag, Feiertag) als verifizierte Δ-Werte aus `03_analysis_*.ipynb`
  - Horizontal-Bar-Chart: Amber = Strukturfaktor · Blau-Abstufungen = externe Faktoren · Teal = Feiertag (positiv)
  - Trennlinie zwischen Struktur und Extern · Einheiten-Hinweis (kumuliert pro Fahrt vs. Δ pro Halt)
- **`04_insights.ipynb`**: neue Sektion "Hebel-Vergleich" zwischen Setup-Zelle und "## Netzstruktur" eingefügt:
  - Markdown-Intro mit Methodenerklärung und Kernbefund (Fahrplan = steuerbarer Hebel #1)
  - Code-Zelle `plot_lever_comparison(lf_clean)`
  - Import `plot_lever_comparison` in Setup-Zelle ergänzt

**Methodische Entscheidung — Einheiten:**
Strukturfaktor (kumulierter Trip-Aufbau) und externe Faktoren (Δ Arrival Delay pro Halt) sind unterschiedliche Einheiten — im Chart transparent gemacht (Einheiten-Hinweis + Trennlinie). Kein Umrechnen: der Strukturfaktor ist bewusst als Kumulat gezeigt, weil er akkumulierend wirkt; externe Faktoren sind situative Aufschläge pro Halt.

**Nächster Schritt:** #39 — Interaktive Linienansicht: Plotly-Karte mit Haltestellen nach Delay eingefärbt in `03_analysis_4-spatial.ipynb`

---

### 2026-05-27 — Feature Importance + Predicted vs. Actual (Phase 4 abgeschlossen)

**Was wurde gemacht:**

- **`06_prediction_3-evaluation.ipynb`** — zwei neue Zellblöcke:
  - **Feature Importance (Gain):** lädt `lgbm_v1.txt`, normalisiert Gain auf %, Horizontal-Barplot mit Farb-Kodierung (Amber >10%, Teal >2%, Grau Rest) + Tabelle Top-15. Beantwortet: hat das Modell dieselben Muster gelernt wie die 55 Findings?
  - **Predicted vs. Actual (Hexbin):** 100k Stichprobe, Hexbin-Dichte, y=x Referenzlinie, Bias-Linie (MBE +8.3s) rot eingezeichnet. Macht den Optimismus-Bias visuell greifbar.
- **ROADMAP:** Evaluation auf ✅ gesetzt, Phase 4 vollständig abgeschlossen

**Nächster Schritt:** Portfolio-Aufbereitung — BACKLOG #41 (Key Visual ins README) als erster konkreter Schritt

---

### 2026-05-26 — Drei Analyse-Items umgesetzt (Dwell-Folge-Analyse)

**Was wurde gemacht:**

Drei neue Plot-Funktionen als Folge aus der Dwell-Scatter-Analyse (vorherige Session) — eine pro bestehendem Analytics-Notebook:

**1. `plot_snow_structural_interaction(lf_clean)` → `analytics/meteo.py` + `03_analysis_5-meteo.ipynb`**
- Zeigt: Schnee verstärkt nicht nur extern (+54 s Arrival Delay), sondern auch den strukturellen Aufbau-Mechanismus (+33 % delay_delta: 4.95 s → 6.58 s/Halt)
- Zwei Panels: Akkumulationsrate (strukturell) + Arrival Delay (Fahrgast-Impact)
- Neue Sektion vor Key Findings im Meteo-Notebook (nach Multikollinearität-Beobachtung)

**2. `plot_holiday_recovery(lf_delay)` → `analytics/events.py` + `03_analysis_6-events.ipynb`**
- Zeigt: Stundenprofil Normaler Werktag vs. Wochenende vs. Feiertag — Netz erholt sich auf Feiertagen ohne Taktreduktion
- Kernbotschaft: Kapazitätsgrenze liegt beim MIV, nicht beim Fahrgastaufkommen
- Drei Linien (0–23 h) · neue Sektion vor Key Findings im Events-Notebook

**3. `plot_line_profiles(lf_all)` → `analytics/network.py` + `03_analysis_2-network.ipynb`**
- Zeigt: Strukturelle Kennzahlen aller Tram-Linien als normalisierte Heatmap (5 Dimensionen: Ø Halte/Fahrt, Stadtkreise, Innenstadt-Anteil, Strukturfaktor, Ø Arrival Delay)
- Linien sortiert nach Strukturfaktor absteigend · VBZ-Farben als y-Achsenbeschriftung
- Neue Sektion zwischen Versorgungsqualität und Fazit im Network-Notebook

**Technische Entscheidung — Strukturfaktor in `plot_line_profiles`:**
`delay_delta` on the fly als `departure_delay - arrival_delay` berechnet (nicht auf vorberechnete Spalte angewiesen) → robuster gegenüber verschiedenen `lf_all`-Versionen.

**Nächster Schritt:** #39 — Interaktive Linienansicht: Plotly-Karte mit Haltestellen nach Delay eingefärbt in `03_analysis_4-spatial.ipynb`
