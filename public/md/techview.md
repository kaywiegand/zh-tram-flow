# Zurich Tram Flow

**Projekt:** Zurich Tram Flow
**Beschreibung:** Technischer Deep Dive
**Autor:** Kay Wiegand
**Zielgruppe:** Data Scientists · Tech Leads · Interviewer
**Dauer:** 20 Minuten
**Zeitraum:** 2023–2025
**GitHub:** [kaywiegand/zh-tram-flow](https://github.com/kaywiegand/zh-tram-flow)

---


---

### Einstieg

# Zurich Tram Flow

**Das Projekt als End-to-End ML Case**
**Data Engineering · EDA · Feature Engineering · LightGBM**

* **94,4 M** — Halt-Ereignisse, 4 Datenquellen
* **50,0 s** — Baseline MAE (Stop Mean)
* **18,56 s** — LightGBM v2 MAE (Test 2025)
* **−63 %** — Verbesserung vs. Baseline

## Inhalt
*Sechs Abschnitte, ein durchgehender ML-Workflow*

* **Ausgangssituation**
  - OTP-Lücke und Datenlage
* **Datenstrategie**
  - Datenquellen und Integration
  - Cleaning-Entscheidungen
* **Baseline**
  - Stop Mean als Benchmark
* **Feature Engineering**
  - 32 Features v1 · Kaskadenindikator v2
* **Modellauswahl**
  - Warum LightGBM
  - v1 · v2 · Robustheits-Check
* **Evaluation & Ausblick**
  - Feature Importance
  - Produktionsreife & Reflexion
  - Handlungsempfehlungen


---

### Ausgangssituation

## Strukturelle Lücke im Netz
*87 % OTP seit drei Jahren — dauerhaft unter dem VBZ-Ziel von 95 %*

* **87 %** — OTP 2023–2025
(netzweit)
  - Ist-Zustand 2023–2025: 87 % netzweit. Konstant unter dem VBZ-Zielwert, über alle drei Betriebsjahre ohne erkennbaren Aufwärtstrend.
* **95 %** — VBZ-Ziel
bis 2028
  - VBZ-Zielwert: 95 % OTP (On-Time Performance, Ankunft ≤ 2 Minuten Verspätung)
* **−8 PP** — Strukturelle
Lücke
  - Der Rückstand ist systemisch, nicht episodisch — er taucht in jedem Jahr, auf jeder Linie auf.
* **56,3 s** — Ø Ankunfts-
verspätung
  - Jede achte Tramfahrt überschreitet den 2-Minuten-Schwellwert. Stabil über alle drei Betriebsjahre.


---

### Datenstrategie

## Datenstrategie
*Vier Quellen, ein temporaler Join, 94,4 Millionen Zeilen*

* **VBZ IST-Daten (Primärquelle)**
  - Reale Ankunfts- und Abfahrtszeiten aller Tramhalte 2023–2025
  - Granularität: Fahrt × Haltestelle × Timestamp
  - Enthält canceled = True Fahrten — bewusst behalten (relevante Extremfälle)
* **GTFS (Fahrplandaten)**
  - Geplante Ankunfts-/Abfahrtszeiten, dwell_time, stop_sequence
  - Liniengeometrien und Haltestellen-Koordinaten (lat/lon)
  - Join-Key: trip_id × stop_id × service_date
* **Meteo Schweiz**
  - Stündliche Messwerte: Temperatur, Niederschlag, Windgeschwindigkeit
  - Join über Zeitstempel (hour-level) auf IST-Daten
  - Abgeleitete Flags: has_rain, has_snow, has_heavy_rain, is_hot
* **Event-Kalender**
  - Grossveranstaltungen Zürich 2023–2025: Konzerte, Messen, Sport
  - Kategorisierung: event_type, event_size, event_weight
  - Ergebnis: 94,4 Mio. Zeilen · 26 Features · 541 MB Parquet

## Datenstrategie
*Cleaning-Entscheidungen und ihre Begründungen*



---

### Baseline

## Baseline
*Stop Mean als sinnvollster naiver Benchmark*

> Stop Mean gewinnt, weil Haltestellen strukturell unterschiedliche Delay-Level haben. Jedes Modell muss diesen Benchmark schlagen. Grand Mean, Hour Mean und Line Mean liegen alle < 1s voneinander entfernt — reine Mittelwert-Strategien bringen keinen Vorteil.


---

### Feature Engineering

## Feature Engineering
*32 Features v1, 34 Features v2 — der entscheidende Unterschied*

* **Temporale Features (v1)**
  - hour, weekday, month, season, year
  - is_weekend, is_november, is_holiday
  - is_late_night_weekend (Kombinations-Feature)
* **Netz-Features (v1)**
  - line_name, stop_name (native categoricals — kein One-Hot)
  - district_nr, n_lines_at_stop, n_stops_line
  - is_start_stop, is_end_stop, dwell_time
* **Externe Features (v1)**
  - temperature, precipitation, wind_speed
  - has_rain, has_heavy_rain, has_snow, has_flood, is_hot
  - has_event, event_type, event_size, event_weight, event_weight_x_hour
* **Kaskaden-Features (neu in v2)**
  - prev_trip_delay: Verspätung des Vorgänger-Trips an diesem Halt — echtzeit-verfügbar
  - stop_sequence_pct: normierter Streckenfortschritt (0–1) — linienübergreifend lernbar
  - Ergebnis: MAE 45,7 s → 18,56 s, −63 %


---

### Modellauswahl

## Modellauswahl und -Anpassung
*Warum LightGBM, warum kein Hyperparameter-Tuning*


## Modellauswahl und -Anpassung
*v1 zu v2: der Sprung kam aus der Analyse, nicht aus dem Algorithmus*

> v1 war systematisch zu optimistisch (MBE +8,3 s). v2 mit Isotonic-Regression-Kalibrierung: MBE −0,69 s. Der MAE-Sprung von 45,7 s auf 18,56 s entspricht −63 % und erklärt sich vollständig durch prev_trip_delay — das stärkste neue Feature.

## Robustheits-Check
*XGBoost-Vergleich und Stabilitätsprüfung*

* **~21,4 s** — XGBoost val MAE (150 Runden)
* **90+ Min** — XGBoost Trainingszeit auf 85M Zeilen
* **18 Min** — LightGBM v2 Trainingszeit
* **18,56 s** — LightGBM v2 Test MAE (2025)
> XGBoost erreicht auf dem Validation-Set vergleichbare Qualität, braucht aber 5× mehr Zeit. Für iteratives Feature Engineering über mehrere Wochen ist LightGBM die klar überlegene Wahl. Das ist eine Workflow-Entscheidung, keine Qualitätskompromittierung.


---

### Feature Importance

## Feature Importance
*prev_trip_delay dominiert — die Analyse hat recht behalten*

> Die Kaskadenanalyse (r ≥ 0,85 netzweit) hat die Feature-Wichtigkeit korrekt antizipiert. Das Modell bestätigt: Das Signal steckt in den Daten, nicht im Algorithmus.


---

### Evaluation

## Produktionsreife und Reflexion
*Was produktionsreif ist, was offen bleibt*



---

### Empfehlungen

## Vier direkte Hebel nutzen
*Jede Empfehlung ist direkt durch einen Befund aus der Analyse gedeckt*



---

### Weitere Potenziale

## Was noch zu erforschen ist
*Dashboard-Exploration offenbarte 7 systematische Forschungsmöglichkeiten*

> Beim interaktiven Erkunden der 16 Linien entstehen neue Fragen: Warum sind Fahrtrichtungen asymmetrisch? Welche Linien dämpfen Delays, welche verstärken sie? Diese Ad-hoc-Entdeckungen sind Signale für strukturelle Potenziale.
* **4 von 7 Forschungsmöglichkeiten (Auswahl)**
  - OP-1: Direction-Asymmetrie (~10s Delta zwischen Richtung A/B)
  - OP-2: Stop-Variabilität (Puffer-Stops vs. zeitkritische Stops)
  - OP-3: Linienlänge ↔ Delay nicht-linear
  - OP-7: Kaskaden-Verstärker vs. -Dämpfer pro Linie
> Detaillierte Hypothesen, Implementation Paths und Prioritäten → BACKLOG.md, Sektion Research Opportunities.


---

### Ende

## Zurich Tram Flow
*Kay Wiegand · 2023–2025*

* **94,4 M** — Halt-Ereignisse
* **41,2 M** — Trainings-Fahrten
* **~29 M** — Test-Fahrten (2025)
* **34** — Features (v2)
* **18,56 s** — MAE · LightGBM v2
* **−63 %** — vs. Baseline
