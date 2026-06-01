# PROCESS_LOG.md – Zürich Tram Flow

> Projektverlauf und AI-Kontext-Einstieg.
> Dieses File ist der Einstiegspunkt für neue Claude-Sessions.

---

## Projekt-Übersicht

| Feld | Inhalt |
| :--- | :--- |
| Projektname | Zürich Tram Flow |
| Repo | `zh-tram-flow` |
| Typ | DANSC — Data Analysis + Data Science |
| Erstellt | 2026-05-11 |
| Status | 🟢 Phase 4 ABGESCHLOSSEN — LightGBM v2 trainiert · Phase 5 (Dashboard) ausstehend |
| Nächster Schritt | /project-case report ausführen · Phase 5 Dashboard-Tooling entscheiden |
| Datenbasis | `sf_data-research` — Phase 0 abgeschlossen |
| Stack | Python · Polars · Pandas · Plotly · LightGBM · uv |

---

## Datenbasis auf einen Blick

Die gesamte Data-Engineering-Phase ist in [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) dokumentiert.

**Master-Datensatz:** `data/raw/zh-tram-data-master.parquet`
- ~94.4 Mio. Zeilen · 26 Spalten · ~541 MB
- Enthält: IST-Verspätungsdaten + GTFS-Haltestellen + Meteo-Stundenwerte + Events
- Zeitraum: 2023–2025 · Betreiber: VBZ Zürich · Produkt: Tram
- **Integrität:** Das Master-File ist korrekt — es spiegelt exakt wider, was VBZ geliefert hat. Der Join `bpuic → stop_name/stop_lat/stop_lon` ist fehlerfrei. Abweichungen in Analysen sind immer auf Eigenschaften der VBZ-Quelldaten zurückzuführen, nicht auf den Join.

**Bekannte VBZ-Quelldaten-Eigenschaft — Kurs-Varianten:**
Manche Tramlinien bedienen neben dem Hauptkurs auch seltenere Kurs-Varianten (z. B. L2 verlängert via Tunnelstrasse → Museum Rietberg → Wollishofen). Diese Varianten-Halte erscheinen im IST-Datensatz mit deutlich niedrigerer Frequenz (< 1% des Hauptkurses) und sind von GTFS bestätigt — kein Datenfehler. In Visualisierungen mit Haltestellenbezug (z. B. `plot_line_delay_profile_map`) werden sie durch einen relativen Frequenzfilter (< 5% des meistbesuchten Halts) ausgeblendet, um den repräsentativen Betrieb zu zeigen. → Dokumentiert in `03_analysis_4-spatial.ipynb`.

**GTFS-Referenztabellen:** `data/raw/gtfs/`
- 9 Parquet-Dateien (Stops, Routes, Shapes, Trips — Tram + Gesamtnetz)
- Referenzjahr: 2024

---

## Fakten-Register — Single Source of Truth

Primärorte für alle Kernzahlen des Projekts.
**Regel:** Zahlen stehen in Notebooks. Nur die unten gelisteten Files dürfen Zahlen direkt enthalten.
PROCESS_LOG Session-Notes verwenden ab dieser Sektion Pointer auf Notebooks — keine Metriken-Tabellen.

| Fakt | Wert | Primärquelle (Notebook) | Sekundär erlaubt in |
| :--- | :--- | :--- | :--- |
| Master-Datensatz Zeilen | 94.4M | `00_introduction.ipynb` — Dateicheck-Zelle | README · portfolio.md |
| lf_clean Zeilen | ~85M | `02_preparation.ipynb` | portfolio.md |
| Train / Val / Test Zeilen | 41.2M / 14.3M / ~29M | `05_feature_engineering.ipynb` | portfolio.md |
| Findings gesamt | 55 | `03_analysis_0-overview.ipynb` | README · ROADMAP · portfolio.md |
| OTP netzweit | 87.0% | `03_analysis_1-target.ipynb` | README · ROADMAP · portfolio.md |
| Delay-Akkumulation | 71.5% | `03_analysis_1-target.ipynb` | README · portfolio.md |
| Stop Mean Baseline MAE | 50.0s | `06_prediction_1-baseline.ipynb` | README · ROADMAP · portfolio.md |
| LightGBM v1 Test MAE / MBE | 45.7s / +8.3s | `06_prediction_2-model.ipynb` | README · ROADMAP · portfolio.md |
| LightGBM v2 Test MAE / MBE | 18.56s / −0.69s | `06_prediction_4-model_v2.ipynb` | README · ROADMAP · portfolio.md |
| XGBoost val MAE (Robustheits-Check) | ~21.4s | `06_prediction_5-comparison.ipynb` | portfolio.md |

**Konvention — welche Files dürfen Zahlen enthalten:**

| File | Zahlen erlaubt? | Begründung |
| :--- | :--- | :--- |
| `reports/mds/portfolio.md` | ✅ ja — ist Präsentations-Interface | Einzige Quelle für `/portfolio slides` + `/portfolio report` |
| `README.md` | ✅ ja — externe Leser | Kernzahlen (Modell-Tabelle, Key Findings) direkt lesbar |
| `ROADMAP.md` | ✅ ja — Phase-Completion-Flags | Meilenstein-Nachweis, historisch korrekt |
| `PROCESS_LOG.md` (ab jetzt) | ⚠️ nur Pointer | Session-Notes zeigen auf Notebook, keine Metriken-Tabellen |
| `CLAUDE.md` / `BACKLOG.md` | ❌ nein | Meta-Files — kein Platz für Fakten |

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
**Phase 4 (Modellierung):** ✅ Abgeschlossen — LightGBM v1 + v2 trainiert, XGBoost Robustheits-Check, Evaluation vollständig · Details → `06_prediction_*`
**Phase 5 (Dashboard):** ⏳ Ausstehend — Tooling-Entscheidung (Streamlit vs. Dash) steht noch aus

**Notebook-Übersicht (alle ausgeführt und committed):**
```
00_introduction.ipynb            ✅ fertig
01_exploration.ipynb             ✅ fertig
02_preparation.ipynb             ✅ ausgeführt — train/test + features in data/
03_analysis_0-overview.ipynb     ✅ fertig (55 Findings · Executive Summary)
03_analysis_1-target.ipynb       ✅ fertig
03_analysis_2-network.ipynb      ✅ fertig
03_analysis_3-temporal.ipynb     ✅ fertig
03_analysis_4-spatial.ipynb      ✅ fertig
03_analysis_5-meteo.ipynb        ✅ fertig
03_analysis_6-events.ipynb       ✅ fertig
04_insights.ipynb                ✅ ausgeführt — Narrative Report alle 7 Abschnitte
05_feature_engineering.ipynb     ✅ ausgeführt — train_final_v2 + test_final_v2 exportiert
06_prediction_0-overview.ipynb   ✅ fertig — Ansatz, Metriken, Baseline, Szenario
06_prediction_1-baseline.ipynb   ✅ ausgeführt — Stop Mean 50.0s als Benchmark
06_prediction_2-model.ipynb      ✅ ausgeführt — LightGBM v1: Test MAE 45.7s
06_prediction_3-evaluation.ipynb ✅ ausgeführt — Fehleranalyse, Feature Importance, Residuals
06_prediction_4-model_v2.ipynb   ✅ ausgeführt — LightGBM v2: Test MAE 18.56s, MBE −0.69s
06_prediction_5-comparison.ipynb ⏭️  Skeleton — XGBoost-Ergebnis in presentation-v3 dokumentiert
```

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

---

### 2026-05-27 — Dwell-Linienkarte + Kaskadenanalyse (Spatial Notebook erweitert)

**Was wurde gemacht:**

Zwei neue Analyse-Funktionen in `src/zh_tram_flow/analytics/spatial.py` + 4 neue Zellen in `03_analysis_4-spatial.ipynb`:

**1. `plot_stop_dwell_map(lf_clean, line_name="11")` → neue Sektion "Dwell-Linienkarte"**
- Plotly Mapbox: Haltestellen der Linie 11 auf der Karte eingefärbt nach % dwell_time=0s (kein Puffer), skaliert nach Ø Arrival Delay
- Colorscale: Teal (gut) → Amber (mittel) → Rot (schlecht), cmin=50%, cmax=100%
- Route-Linie grau → Haltestellen als Bubbles — räumlich greifbar wo fehlender Puffer auf hohen Delay trifft
- Schließt analytischen Kreis: dwell_time = Feature #1 im Modell → Karte zeigt das Problem geografisch

**2. `plot_cascade_effect(lf_clean)` + `table_cascade_effect(lf_clean)` → neue Sektion "Kaskadenanalyse"**
- Pearson-r(delay_n, delay_n+1) per Linie via Polars `shift(1).over(["trip_id", "operating_date"])` nach Sort nach `stop_sequence`
- Streaming-Collect für 80M Zeilen — kein OOM
- Bar-Chart sortiert nach Korrelation absteigend, farbkodiert: Rot ≥0.85 (stark) · Amber ≥0.70 (mittel) · Teal <0.70 (schwach)
- Tabelle mit Linie / Pearson r / N Halte / Stärke (Emoji-Flag)
- Beantwortet BACKLOG #18: Kaskadeneffekt messbar?

**BACKLOG-Update:**
- #42 neu: **Dwell-Optimierungs-Simulator** — zweites Prediction-Tool, nimmt modifizierte dwell_time-Werte als Input → lgbm_v1 berechnet Δ-Delay. Schließt Kreis Analyse → Modell → Handlungsempfehlung. `06_prediction_4-dwell_simulator.ipynb`

**Nächster Schritt:** `03_analysis_4-spatial.ipynb` neu ausführen → dann #42 Dwell-Simulator planen

---

### 2026-05-27 — 6N Trace-Architektur: Jahr-Toggle für Routen + Haltestellen

**Was wurde gemacht:**

- **`plot_line_delay_profile_map` + `plot_line_dwell_profile_map`** in `src/zh_tram_flow/analytics/spatial.py` komplett rewritten:
  - **6N Trace-Layout** (war: 2N): 3 Jahre × N Routen + 3 Jahre × N Bubble-Traces
  - **Per-year Stop-Aggregation** — separate `group_by` pro 2023/2024/2025 mit `min_n // 3` Schwelle
  - **Jahr-Schalter** (2023/2024/2025/Alle Jahre) blendet jetzt Routen **und** Haltestellen gemeinsam um — nicht nur die Route
  - **j25-Bubbles als Legende-Anker** (`showlegend=True`, `legendgroup`): bei anderen Jahren `visible="legendonly"` → Legende bleibt immer sicht- und klickbar
  - **`_make_year_buttons()`** entfernt → ersetzt durch `_make_vis_year_buttons(N)` + `_year_vis(yr, N)` Helpers
  - **"Alle Jahre"** Option neu: alle 3 Routen-Sets gleichzeitig sichtbar + nur j25-Bubbles (kein Triple-Count)
  - **Globale Bubble-Normalisierung** über alle Jahre → konsistente visuelle Skala beim Jahr-Wechsel
  - **Colorbar** in Dwell-Karte: einfacher `_show_colorbar`-Flag statt fragiler `fig.data`-Suche

**Technische Entscheidung:**
j25-Bubbles immer als Legende-Anker → bei Jahreswechsel zu 2023/2024 werden j23/j24-Bubbles sichtbar und j25-Bubbles auf `"legendonly"` gesetzt. Einzelne Linien per Legende-Klick only vollständig für Jahr 2025, da nur j25-Traces im legendgroup sind. Das ist der primäre Use-Case (Standard-Ansicht = 2025).

**Nächster Schritt:** `03_analysis_4-spatial.ipynb` im Notebook ausführen — beide Karten verifizieren

---

### 2026-05-27 — 2N Restyle-Architektur + Spurious-Stop-Filter

**Was wurde gemacht:**

**`plot_line_delay_profile_map` + `plot_line_dwell_profile_map`** komplett auf 2N-Architektur umgestellt (ersetzt die 6N-Architektur vom gleichen Tag):

**2N Trace-Layout:**
- `[0..N-1]` Route-Traces · `[N..2N-1]` Bubble-Traces (fester Trace-Satz, keine Duplikate pro Jahr)
- Jahr-Wechsel via Plotly `restyle` — tauscht `lat/lon/marker.size` (bzw. `marker.color`) der bestehenden Traces
- Visibility bleibt vollständig unangetastet → Legende-Klick und Alle-aus/ein funktionieren wie in `tram_lines_map.html`

**Warum 6N abgelöst:** 6N hatte das Legenden-Verhalten gebrochen — Jahr-Wechsel und Linien-Toggle liefen in Konflikt, weil `visible`-Toggling für beide Funktionen benutzt wurde. Mit `restyle` wird nur der Dateninhalt getauscht, `visible` gehört exklusiv der Legende.

**Kurs-Varianten-Filter** (`commit d72e59a`)

**Was das Problem war (korrigierte Erklärung nach GTFS-Verifikation):**

Die L2 hat mehrere **Kurs-Varianten**:
- Hauptkurs (~3.700 GTFS-Trips): Schlieren → Tiefenbrunnen
- Verlängerter Kurs (~900 GTFS-Trips): fährt weiter via Tunnelstrasse → Museum Rietberg → Morgental → Wollishofen

Das sind echte L2-Kurse — die Liniennummer im IST-Datensatz ist korrekt, kein Datenfehler. Museum Rietberg erscheint in der GTFS-Tramplandatei als legitimer L2-Halt.

Das Problem ist eine **Visualisierungsentscheidung**: Zeige ich alle Kurs-Varianten (dann sieht die Karte unübersichtlich aus) oder nur den Hauptkurs? Die HTML-Referenzkarte (`tram_lines_map.html`) verwendet GTFS-Shapes, die nur die primäre Streckengeometrie zeigen — darum sieht sie sauber aus.

In den Profil-Karten zeigten sich alle Varianten-Halte (die selten, aber legitim sind), was die Karte "verfranzt" wirken liess.

**Die Lösung — Visualisierungsfilter:**
Pro Linie und Jahr werden Haltestellen entfernt, die weniger als 5% der meistbesuchten Haltestelle erreichen:
- Hauptkurs-Halte: ~90.000–98.000 Beobachtungen → bleiben
- Varianten-Halte: ~800–1.300 Beobachtungen (< 1%) → werden ausgeblendet

Das ist keine Datenbereinigung (die Daten sind korrekt), sondern eine bewusste Entscheidung: die Karte zeigt den repräsentativen Betrieb, nicht seltene Kurs-Sonderformen. Der Schwellenwert ist relativ, damit er für alle Linien skaliert.

Angewendet auf: `plot_line_delay_profile_map` und `plot_line_dwell_profile_map`.

**Nächster Schritt:** `03_analysis_4-spatial.ipynb` ausführen — beide Karten (Delay + Dwell) verifizieren: Jahr-Toggle, Alle-aus/ein, Linien-Klick, keine Spurious Stops mehr

---

### 2026-05-27 — 04_insights.ipynb: 4-Schritt-Beweiskette in Geografie-Sektion

**Was wurde gemacht:**

Der Geografie-Abschnitt in `04_insights.ipynb` wurde ausgebaut. Bisher gab es dort nur `plot_stop_delay_map` (Anomalie-Karte) und `plot_district_combined`. Die Beweiskette war unvollständig — das Bild nicht aussagekräftig genug.

**6 neue Zellen nach `plot_stop_delay_map`:**

1. `[2fd856ce]` **Text: "Das Muster entlang der Strecke: L11 vs. L6"** — Fragt "warum sitzt die Verspätung dort?" und setzt L11 (schlechteste Linie) als Kontrast zu L6 (beste Linie)
2. `[aa3ca77c]` **Code: `plot_line_delay_profile_map(lf_clean, lines=["11", "6"])`** — Zeigt den Delay-Gradienten: L11-Bubbles wachsen zur Peripherie, L6-Bubbles bleiben gleichmässig klein
3. `[688a0910]` **Text: "Mechanismus: Kein Puffer — keine Erholung"** — Erklärt die Dwell-Map: Farbe = Delay, Grösse = % Halte ohne Puffer (dwell_time=0). Smoking Gun: röteste Bubbles = grösste Bubbles
4. `[5ab24fca]` **Code: `plot_stop_dwell_map(lf_clean, line_name="11")`** — Die Dwell-Map als "Smoking Gun" — L11-Endhalte sind gleichzeitig am rötesten und grössten
5. `[a6e7123b]` **Text: "Beweiskette: Kaskadeneffekt netzweit"** — Schliesst die Beweiskette mit 4-Schritt-Zusammenfassung und erklärt den Pearson-r
6. `[efbf5feb]` **Code: `plot_cascade_effect(lf_clean)`** — Alle 16 Linien r ≥ 0.85: systematische Kaskade, kein Einzelfall

**Die 4-Schritt-Beweiskette ist jetzt vollständig:**
1. Anomalie: `plot_stop_delay_map` — Hotspots an Endhalten
2. Gradient: `plot_line_delay_profile_map(lines=["11","6"])` — Delay wächst entlang der Strecke, L11 vs. L6 als Kontrast
3. Mechanismus: `plot_stop_dwell_map(line_name="11")` — kein Puffer = keine Erholung
4. Beweis: `plot_cascade_effect` — Pearson r ≥ 0.85 netzweit

**Nächster Schritt:** `04_insights.ipynb` komplett durchlaufen lassen · PROCESS_LOG commit · Dann: `03_analysis_4-spatial.ipynb` verifizieren (beide Profil-Karten nach Dwell-Filter-Ergänzung)

---

### 2026-05-27 — 04_insights.ipynb: Storyline auf "vorhersagbar = steuerbar" umgestellt

**Was wurde gemacht:**

Die bisherige Kernthese enthielt einen angreifbaren Claim ("das Geld wurde an den falschen Orten investiert") — wir wissen nicht, wie die Verspätung ohne den Netzausbau ausgesehen hätte. Der Claim war nicht durch unsere Daten gedeckt.

**Neue Storyline:** "Die Verspätungen sind vorhersagbar — weil sie im Fahrplan-Design verankert sind, nicht im Betrieb."

**4 Zellen geändert:**
- `[d8c0bc6a]` **Kernthese** — dritter Bullet von "Investitions-Mismatch" zu "Konsequenz: Was vorhersagbar ist, ist steuerbar"
- `[cac5c4f4]` **Netzausbau 2023** — Befund umgedreht: der Netzausbau hat die Verspätungsstruktur nicht verändert → das ist *Beweis* für die These (Infrastruktur ist nicht der Hebel), kein Vorwurf
- `[acae4978]` **Empfehlungen** — "Kapazität K11/K12 erhöhen" und "Nächster Ausbau → K11/K12" gestrichen (nicht durch Daten gedeckt), ersetzt durch "Fahrplan-Redesign L11" (direkt gedeckt durch Dwell-Map)
- `[13dc8a6a]` **Hotspots-Text** — "kein Netzausbau 2023" aus dem Befund entfernt (steht jetzt als Argument in Netzausbau-Sektion)

**Alle Empfehlungen sind jetzt direkt durch Analysebefunde gedeckt** — kein Claim mehr der Gegeninfos braucht.

**Nächster Schritt:** `04_insights.ipynb` komplett durchlaufen lassen (Kernel-Restart + Run All)

---

### 2026-05-28 — Neue Prediction-Notebooks: v2 + Modellvergleich

**Was wurde gemacht:**

Zwei neue Notebooks angelegt, die den bisherigen Modellierungsstand erweitern:

**`06_prediction_4-model_v2.ipynb`** — LightGBM v2 mit Kaskadenfeature
- `prev_trip_delay`: Delay am Vorgänger-Halt desselben Trips — direkter Kaskadenindikator (Pearson r ≥ 0.85 aus Spatial-Analyse)
- `stop_sequence_pct`: Position entlang der Linie (0 = Anfang · 1 = Ende) — Akkumulationseffekt
- Join-Strategie: `stop_sequence` aus `train_features.parquet` auf `train_final.parquet` joinen via `(trip_id, operating_date, stop_name)`
- Export: `train_final_v2.parquet` + `test_final_v2.parquet`
- Gleiche Hyperparameter wie v1 — isolierter Feature-Effekt messbar
- SHAP-Werte (try/except — benötigt `uv pip install -e ".[dsc]"`)
- Isotonic Regression als Post-hoc-Bias-Kalibrierung (MBE v1: +8.3s)
- Export: `lgbm_v2.txt` + `lgbm_v2_calibrator.joblib` + `lgbm_v2_meta.json` + `test_predictions_v2.parquet`

**`06_prediction_5-comparison.ipynb`** — Modellvergleich: Baseline → LightGBM v1 → v2 → XGBoost
- XGBoost mit `enable_categorical=True` (2.0+, `tree_method=hist`) — gleiche v2-Features, faires Algorithmen-Benchmarking
- Metriken-Tabelle: alle 5 Varianten nebeneinander (MAE, RMSE, MBE, OTP)
- Feature Importance v1 vs. v2 — normalisiert, neue Features hervorgehoben
- Fehlerprofile nach Stunde / Linie / Wetter — alle Modelle überlagert
- Residual-Verteilungen nebeneinander
- Bug gefixt: toter Code im Residuals-Block entfernt, `ae_v1` Längenprüfung mit `assert` gesichert

**Begründung für `prev_trip_delay` als wichtigstes neues Feature:**
Die neue Kernthese ("vorhersagbar = steuerbar") braucht einen Modell-Beweis. Wenn `prev_trip_delay` in der Feature Importance oben steht, bestätigt das: die Kaskade ist kein statistisches Artefakt — sie ist ein lernbares Signal. Das schließt den Kreis Analyse → Modell.

**Nächster Schritt:** Notebooks sequenziell ausführen: 04 → 05 → Vergleichs-Ergebnis auswerten

---

### 2026-05-28 — XGBoost Unicode-Fix + presentation-v2.html erstellt

**Was wurde gemacht:**

**XGBoost Unicode-Fix in `06_prediction_5-comparison.ipynb`:**

XGBoost 3.x wirft `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc3` wenn pandas Categorical-Spalten Schweizer Haltestellennamen (ä, ö, ü) enthalten — 0xc3 ist das erste Byte von UTF-8-Multibyte-Zeichen. XGBoost liest Kategorie-Labels intern als raw bytes statt als Python-str.

Lösung: `OrdinalEncoder` aus scikit-learn ersetzt pandas Categorical → Ganzzahl-Codes statt Unicode-Strings. Encoder wird einmalig auf dem vollen Train-Set gefittet und konsistent auf Train, Validation und Test angewendet. `enable_categorical=True` entfernt (nicht kompatibel mit integer-encodierten Spalten).

Geänderte Zellen: `cmp00012` (OrdinalEncoder-Fit + `to_xgb_df()`-Hilfsfunktion) und `cmp00021` (XGBRegressor ohne `enable_categorical`).

**`reports/presentation-v2.html` — neue Präsentation erstellt:**

Vollständige Neuerstellung auf Basis von `presentation.html` (v1). Zentrale Änderungen:

- **Kernthese-Folie (Slide 2):** "Die Verspätungen im Zürcher Tramnetz sind vorhersagbar. Vorhersagbar heisst: steuerbar." — eigene Folie statt nur Bullet in Insights
- **4-Schritt-Beweiskette (Slide 10):** Evidence Chain als visuelles Kernelement: Anomalie → Gradient → Mechanismus → Kaskade. Schliesst direkt aus der Analyse-Phase.
- **Modellentwicklung (Slide 13):** Progressions-Tabelle: Baseline 50.0s → LightGBM v1 45.7s → LightGBM v2 18.56s* → XGBoost (pending)
- **v2-Interpretation (Slide 14):** Zwei Modell-Karten nebeneinander: v1 = Pre-Trip-Modell, v2 = Real-Time-Dispatch — erklärt den Unterschied und den Nutzungskontext
- **Neue Empfehlungen (Slide 16):** Kein "Netzausbau K11/K12" mehr — stattdessen: Fahrplan-Redesign L11 · Real-Time Dispatch · Kapazität Abend · OTP-Monitoring
- **Storyline entfernt:** "Investitions-Mismatch" vollständig raus — neue Empfehlungen sind alle direkt durch Befunde gedeckt
- Struktur: 17 Slides total (4 Section-Divider + 13 Content-Slides)

XGBoost-Zelle im Vergleichs-Notebook läuft noch — Ergebnis wird in Slide 13 als "pending" ausgewiesen. Sobald fertig: Tabelle mit echten XGBoost-Zahlen füllen.

**Nächster Schritt:** `06_prediction_5-comparison.ipynb` fertig laufen lassen · XGBoost-MAE in `presentation-v2.html` Slide 13 eintragen · dann git commit

---

### 2026-05-29 — Notebooks stabilisiert · Portfolio-Pipeline · reports/ als Web-Projekt

**Was wurde gemacht:**

- **Notebook-Stabilisierung** (`06_prediction_4-model_v2.ipynb` + `06_prediction_5-comparison.ipynb`):
  - Load-if-exists Pattern in beiden Modell-Notebooks — kein Re-Training bei Kernel-Neustart
  - SKIP_XGB Flag in comparison Notebook — XGBoost-Zellen überspringen wenn kein Model-File vorhanden
  - `params` aus `lgbm_v2_meta.json` im Load-Branch gelesen — NameError in Export-Zelle behoben
  - Beide Notebooks von Kay erfolgreich vollständig durchlaufen lassen ✅

- **Portfolio-Pipeline ausgeführt** (`/portfolio story` + `/portfolio report`):
  - `reports/mds/portfolio.md` — Interface-File: Kernthese, 6 Findings, Modellprogression, 21 Figures inventarisiert, 4 Empfehlungen
  - `reports/index.html` — narrativer HTML-Report (3 Lese-Ebenen: Scan · Dive · Deep-Dive)

- **`reports/` als Web-Projekt restrukturiert:**
  - `figures/` → `img/` · `portfolio.md` → `mds/` · `report.html` → `index.html`
  - `tram_lines_map.html` → `network-map.html`
  - `insights_v1.html` + `template.html` entfernt
  - `config.py`: `PATHS["figures"]` zeigt jetzt auf `reports/img/`

- **Infrastruktur-Updates (3 Repos, 3 Commits):**
  - `wgnd-scaffolding`: 7 Template-Files auf `img/` + `mds/` umgestellt
  - Globale `CLAUDE.md`: Struktur-Diagramm (2 Stellen) aktualisiert

**Nächster Schritt:** BACKLOG #10 (Portfolio-Beschreibung README) + #43 (Export-Cells in Notebooks)

---

### 2026-05-28 — presentation-v3.html + XGBoost-Abschluss + Portfolio-Skills-Infrastruktur

**`reports/presentation-v3.html` — 16 Feedback-Punkte eingearbeitet:**

- T-Shape Slide: vollständige Bullet-Listen wiederhergestellt (ETL-Schritte, Analyse-Dimensionen, Preparation-Punkte)
- Section- und Slide-Titles: `text-transform: uppercase` entfernt — Normal Case durchgehend
- Slide 5 (Idee & Scope): Pipe-Step-Buttons als Spalten-Header statt inline-Elemente
- Analyse Überblick: Icons entfernt, Notebook-Titel auf Englisch (Target · Network · Time · Geo · Meteo · Events)
- Reihenfolge: "Das Problem" vor "Analyse Überblick" — Kontext vor Inhalt
- Hotspot-Bullet: "Verspätung konzentriert sich auf wiederkehrende Hotspot-Haltestellen — kein Zufall, sondern ein Muster"
- Slide 18 (Datenverfügbarkeit): Zielgruppen-Framing entfernt — Daten-Verfügbarkeits-Framing (Pre-Trip vs. In-Trip)
- Empfehlung 1: "gezielter Puffer" statt "Puffer an Endstationen"
- Headings durchgehend linksbündig (`text-align: left` auf h2, h3, p, li)
- Mehr Abstand zwischen Slide-Titel und Content (`margin-bottom: 0.85em`)
- Stop-Baseline erklärt als statistisch erhoben aus Trainingsdaten

**XGBoost-Abschluss (Option C):**

Training nach 150 Runden (val MAE 21.37s) abgebrochen — 85M Zeilen machen CPU-Training nicht zumutbar (>90 Min, hohe Last). Entscheidung: XGBoost-Zeile aus Slide 17 entfernt, stattdessen orange Robustheits-Box in Slide 18: *"XGBoost auf gleichem Feature-Set → val MAE ~21.4s (150 Runden) — 5× langsamere Trainingszeit auf 85M Zeilen."* Das ist selbst ein Befund: LightGBM nicht nur ähnlich gut, sondern drastisch schneller.

`cmp00021` in `06_prediction_5-comparison.ipynb` angepasst: `n_estimators` 1000 → 300 (Kurve war bei Round 150 konvergiert), Load-if-exists Pattern (Kernel-Crash-Schutz), Save-after-fit direkt nach Training.

**Portfolio-Skills-Infrastruktur (Workspace-Ebene):**

Drei neue Files für wiederverwendbaren Portfolio-Aufbereitungs-Workflow:
- `~/.claude/commands/portfolio.md` — Claude Code Skill mit 5 Modi: check · story · report · slides · full
- `/Workspace/docs/portfolio/templates/portfolio_summary_template.md` — Interface-File-Template (Brücke Analyse → Präsentation)
- `/Workspace/docs/portfolio/templates/slides-template.html` — CSS/JS-Basis aus presentation-v3 extrahiert, projektunabhängig

Ziel: `/portfolio story` auf einem Projekt aufrufen → `reports/portfolio_summary.md` wird aus Notebook-Markdown-Cells befüllt → `/portfolio slides` generiert daraus `presentation.html` ohne Notebooks erneut lesen zu müssen.

**Nächster Schritt:** `/portfolio check` auf zh-tram-flow als ersten Echttest · dann `/portfolio story` für `reports/portfolio_summary.md`

---

### 2026-06-01 — Backlog #43 Export-Cells abgeschlossen

**Was wurde gemacht:**

**Teil 1 — `save_as` für alle matplotlib Plot-Funktionen** (commit `e7d4796`, vorherige Session):
- `analytics/events.py`: 6 Funktionen — `plot_events_overview`, `plot_event_type_hourly_profile`, `plot_event_district_effect`, `plot_monthly_holiday_timeline`, `plot_daily_delay_timeline`, `plot_holiday_recovery`
- `analytics/meteo.py`: 9 Funktionen — `plot_weather_overview` bis `plot_snow_structural_interaction`
- `analytics/network.py`: 7 Funktionen — `plot_new_stops_by_district` bis `plot_line_profiles`
- `analytics/spatial.py`: 9 Funktionen — `plot_top_delay_stops` bis `plot_cascade_effect`
- `analytics/temporal.py` (4 von 6 Funktionen) — `plot_full_year_trend` + `plot_gtfs_year_comparison` fehlten noch

**Teil 2 — Fehlende temporal.py Funktionen + Export-Cells** (commit `7ee9ac5`):
- `temporal.py`: `save_as=None` zu `plot_full_year_trend` (L405) + `plot_gtfs_year_comparison` (L482) ergänzt
- Pattern: savefig-Block vor `plt.show()` eingefügt — bei `plot_gtfs_year_comparison` korrekt vor den `print()`-Statements nach show
- **5 Analyse-Notebooks** erhalten je eine `## Export` Sektion (Markdown + Code):
  - `03_analysis_2-network.ipynb`: 7 Plots → `reports/img/network-*.png`
  - `03_analysis_3-temporal.ipynb`: 6 Plots → `reports/img/temporal-*.png`
  - `03_analysis_4-spatial.ipynb`: 8 Plots → `reports/img/spatial-*.png`
  - `03_analysis_5-meteo.ipynb`: 9 Plots → `reports/img/meteo-*.png`
  - `03_analysis_6-events.ipynb`: 5 Plots → `reports/img/events-*.png`
- Plotly/Folium-Karten bewusst ausgeschlossen — haben bereits `save_html`, kein PNG-Export nötig
- 16/16 Tests grün nach allen Änderungen

**Nächster Schritt:** #39 Interaktive Linienansicht — `plot_line_route_map` in `analytics/spatial.py`

---

### 2026-06-01 — Backlog #39 Interaktive Linienansicht abgeschlossen

**Was wurde gemacht** (commit `2bbc9d5`):

- `analytics/spatial.py`: Neue Funktionen `plot_line_route_map` + `table_line_route_map` eingefügt
  - Zwei Plotly-Traces: Trace 0 = GTFS-Routen-Linie (VBZ-Linienfarbe, opacity 50%), Trace 1 = Stop-Bubbles (grün → amber → rot, Größe ∝ Delay)
  - Top-3 Problemstops: Text-Annotation inline im selben Trace (`mode="markers+text"`), leere Strings für alle anderen
  - `stop_short` in `customdata[3]` für Hover — `text`-Array ist durch Annotations belegt
  - 5%-of-max-n Displayfilter (gleich wie `plot_line_delay_profile_map`) filtert Baustellen-Kurzläufer
  - GTFS-Geometrie über bestehenden `_load_gtfs_shapes([line_name], year=year)` Helper geladen
  - `table_line_route_map` als Companion-Tabelle (sortiert nach Ø Delay absteigend)
- `03_analysis_4-spatial.ipynb`: Zwei neue Zellen zwischen `plot_stop_dwell_map` und `## Kaskadenanalyse`:
  - Markdown-Cell: Sektionsheader + Kurzbeschreibung
  - Code-Cell: `an.plot_line_route_map(lf_clean, line_name="11")` + `show_df(an.table_line_route_map(...))`

**Entscheidungen:**
- `customdata[3]` statt separater Trace für Hover-Namen — sauberer, kein redundanter Trace
- Annotation-Format: `"Haltestelle (Xs)"` mit `int(round(...))` für saubere Ganzzahl
- Plotly `carto-positron` als Basemap — konsistent mit allen anderen Spatial-Plots

**Nächster Schritt:** #40 Situationsvergleich (gleiche Linie, verschiedene Kontexte — Normal/Event/Winter/Rush-Hour) · oder #10/#34 Portfolio-Prio-1-Items
