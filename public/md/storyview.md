# Zurich Tram Flow

**Projekt:** Zurich Tram Flow
**Beschreibung:** Der gesamte Daten-Lifecycle
**Autor:** Kay Wiegand
**Zielgruppe:** Portfolio · Konferenz · Vollbild
**Dauer:** 35 Minuten
**Zeitraum:** 2023–2025
**GitHub:** [kaywiegand/zh-tram-flow](https://github.com/kaywiegand/zh-tram-flow)

---


---

### Einstieg

# Zurich Tram Flow

**Von der Frage bis zur Empfehlung**
**Data Engineering · EDA · Machine Learning · Dashboard**

* **94,4 M** — Halt-Ereignisse
* **87 %** — OTP heute · Ziel: 95 %
* **18,56 s** — MAE LightGBM v2
* **−63 %** — vs. Baseline

## Die These
*Ein Satz, der das gesamte Projekt trägt*

> Die Verspätungen im Zürcher Tramnetz sind vorhersagbar — weil sie im Fahrplan-Design verankert sind, nicht im zufälligen Betrieb.
> Was vorhersagbar ist, ist steuerbar. Das Modell bestätigt die Analyse: prev_trip_delay ist das stärkste neue Feature in v2, MAE sinkt von 45,7 s auf 18,56 s. Fahrplan-Redesign an L11 ist der Hebel.

## Inhalt
*Sieben Kapitel, ein durchgehender Datenpfad*

1. Ausgangssituation
2. Data Engineering
3. Exploration
4. Die Erkenntnis
5. Machine Learning
6. Die Handlungsempfehlungen
7. Projektrahmen und Workflow


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
* **−8 %** — Strukturelle
Lücke
  - Der Rückstand ist systemisch, nicht episodisch — er taucht in jedem Jahr, auf jeder Linie auf.
* **56,3 s** — Ø Ankunfts-
verspätung
  - Jede achte Tramfahrt überschreitet den 2-Minuten-Schwellwert. Stabil über alle drei Betriebsjahre.

## Wie wir vorgehen
*Von der Ursachenanalyse zur Vorhersage*



---

### Exploration

## Widerlegte Annahmen
*Drei Erwartungen, die die Daten klar widerlegen*


## Die Innenstadt ist pünktlicher
*Verspätungs-Hotspots liegen an der Peripherie, nicht im Stadtzentrum*


## Der Peak am Abend
*Um 21 Uhr entstehen die höchsten Verspätungen — nicht im Morgenrush*


## Exploration
*Wetter: Schnee und Regen treffen unterschiedliche Stadtteile*

* **+54s** — Schnee-Effekt netzweit
* **+23,3 s** — Regen-Effekt netzweit
* **−9,9 s** — Feiertage vs. Normal
* **66,0 s** — Fachmessen (schlechteste Event-Kategorie)
> Feiertage sind der beste Tagestyp: −9,9 s vs. Normal. Der MIV-Rückgang überwiegt jeden Event-Effekt. Event-Wirkung ist ein Abend-Phänomen (18–22h): tagsüber kein messbarer Unterschied.


---

### Data Engineering

## Datenstrategie
*Primärquellen: VBZ IST-Daten und GTFS-Fahrplan*

* **VBZ IST-Daten (Primärquelle)**
  - Reale Ankunfts- und Abfahrtszeiten aller Tramhalte 2023–2025
  - Granularität: Fahrt × Haltestelle × Timestamp
  - Enthält canceled = True Fahrten — bewusst behalten (relevante Extremfälle)
* **GTFS (Fahrplandaten)**
  - Geplante Ankunfts-/Abfahrtszeiten, dwell_time, stop_sequence
  - Liniengeometrien und Haltestellen-Koordinaten (lat/lon)
  - Join-Key: trip_id × stop_id × service_date

## Datenstrategie
*Kontextquellen: Wetter und Grossveranstaltungen*

* **Meteo Schweiz**
  - Stündliche Messwerte: Temperatur, Niederschlag, Windgeschwindigkeit
  - Join über Zeitstempel (hour-level) auf IST-Daten
  - Abgeleitete Flags: has_rain, has_snow, has_heavy_rain, is_hot
* **Event-Kalender**
  - Grossveranstaltungen Zürich 2023–2025: Konzerte, Messen, Sport
  - Kategorisierung: event_type, event_size, event_weight
  - Ergebnis: 94,4 Mio. Zeilen · 26 Features · 541 MB Parquet

## Data Engineering
*Cleaning als Forschungsentscheidung, nicht als Routine*



---

### Erkenntnis

## Die Kaskade bei den Verspätungen
*Ohne Puffer im Fahrplan überträgt sich jede Verspätung auf die Folgefahrten — in Zahlen*

* **71,5 %** — Halte akkumulieren Delay
* **L11** — 68,7 s · OTP 82 % — stärkste Akkumulation
* **71,3 %** — Haltestellen ohne Standzeit (0s)
* **r ≥ 0,85** — Kaskadenkorrelation alle 16 Linien

## Wie sich die Kaskade aufbaut
*Vier Schritte, vom ersten Anzeichen bis zum netzweiten Beweis*


## Ein Fahrplan-Design-Thema
*Nicht Betriebsversagen — strukturell angelegt*

> Das ist kein Betriebsversagen. Es ist ein Fahrplan-Design-Thema. Was im Fahrplan nicht vorgesehen ist, kann im Betrieb nicht ausgeglichen werden.

## Externe Faktoren verstärken, ändern aber nichts Grundlegendes
*Wetter und Grossevents wirken, das Grundproblem bleibt strukturell*

> Zwei externe Einflussfaktoren sind messbar und erheblich: Schnee (+54s) und Grossevents (bis +66s bei Fachmessen). Doch das Grundniveau der Verspätung bleibt auch bei optimalen Bedingungen konstant hoch. Externe Faktoren verstärken, was intern bereits strukturell angelegt ist.
> Trotz Bauphasen, Streckensperrungen und Fahrplanumstellungen hält die VBZ das System bemerkenswert stabil. Die Verspätungslevel schwanken durch diese Eingriffe kaum. Die Ursache liegt nicht in externen Störungen, sondern im Fahrplan-Design selbst.


---

### Machine Learning

## Warum Machine Learning?
*Drei Iterationen der Modellierung — von der Baseline zum finalen Modell*

> Die Struktur der Daten ist nichtlinear.

## Drei Iterationen der Modellierung
*Von der Baseline über Feature Engineering zum finalen Ensemble-Modell*

> Der Sprung von v1 auf v2 kam nicht durch einen besseren Algorithmus, sondern durch das richtige Signal aus der Analyse: den Kaskadenindikator (prev_trip_delay).

## 18,56 Sekunden MAE
*Mittlerer Vorhersagefehler auf einem vollständigen, ungesehenen Testjahr — 63 % unter der Baseline*

* **41 Mio.** — Trainings-Fahrten 2023–Jun 2024
* **~29 Mio.** — Test-Fahrten vollständiges Jahr 2025
* **−0,69 s** — MBE nach Isotonic-Regression-Kalibrierung
> prev_trip_delay ist das stärkste neue Feature in v2 und erklärt den Sprung von 45,7 s auf 18,56 s MAE. Das Signal war in den Daten — die EDA hat es zuerst aufgezeigt, das Modell hat es bestätigt.


---

### Feature Importance

## Feature Importance
*prev_trip_delay dominiert — die Analyse hat recht behalten*

> Die Kaskadenanalyse (r ≥ 0,85 netzweit) hat die Feature-Wichtigkeit korrekt antizipiert. Das Modell bestätigt: Das Signal steckt in den Daten, nicht im Algorithmus.


---

### Anwendung

## Konkreter Nutzen in der Praxis
*Konkrete Vorhersagen für reale Betriebssituationen zeigen die operative Relevanz*

> Das Modell kombiniert Tageszeit, Linie, Haltestelle, Wetterlage und den Verspätungsstatus des Vorgänger-Trips zu einer konkreten Sekundenvorhersage. So lassen sich kritische Situationen identifizieren, bevor die Kaskade einsetzt.


---

### Empfehlungen

## Vier direkte Hebel nutzen
*Jede Empfehlung ist direkt durch einen Befund aus der Analyse gedeckt*



---

### Resultat

## Was vorhersagbar ist, ist steuerbar.
*Ein Projekt, das zeigt: Datengetriebene Analyse ist kein akademisches Artefakt — sie liefert operative Entscheidungsgrundlagen.*



---

### Projektrahmen

## Daten & Stack
*Umfang der Datenbasis und eingesetzte Technologie*

* **Datenbasis und Umfang**
  - VBZ IST-Daten · GTFS · Meteo Schweiz · Event-Kalender
  - 94,4 Mio. Zeilen · 26 Features · 541 MB Parquet
  - 3 vollständige Betriebsjahre · 16 Linien · ca. 190 Haltestellen
  - 66 dokumentierte Befunde in 12 Jupyter-Notebooks
* **Technologie-Stack**
  - Python · Polars (85 Mio. Zeilen, lazy evaluation) · Jupyter · uv
  - LightGBM (Modellierung) · Plotly (Visualisierung) · Streamlit (Dashboard)
  - Trainingszeit LightGBM v2: ca. 18 Minuten auf Consumer-Hardware

## Offen & reproduzierbar
*Open Data, AI-Workflow, vollständig reproduzierbar*

* **AI-Workflow als Differenziator**
  - Claude Code für iterative Analyse, Code-Refactoring, Dokumentation
  - Promptbasiertes Scaffolding: von der Idee zur Notebook-Struktur in Minuten
  - Menschliche Entscheidungsverantwortung bleibt bei allen Finding-Interpretationen
* **Reproduzierbarkeit**
  - Vollständiger Code auf GitHub, alle Datenquellen öffentlich
  - Data Engineering vollständig reproduzierbar via Polars-Pipeline
  - Alle Befunde rückverfolgbar auf Finding-IDs in den Notebooks


---

### Weitere Potenziale

## Was noch zu erforschen ist
*Dashboard-Exploration offenbarte 7 systematische Forschungsmöglichkeiten*

> Beim interaktiven Erkunden der 16 Linien entstehen neue Fragen: Warum sind Fahrtrichtungen asymmetrisch? Welche Linien dämpfen Delays, welche verstärken sie? Diese Ad-hoc-Entdeckungen sind Signale für strukturelle Potenziale.
* **3 von 7 Forschungsmöglichkeiten — Details in BACKLOG.md**
  - OP-1: Direction-Asymmetrie (~10s Delta zwischen Richtung A/B)
  - OP-2: Stop-Variabilität (Puffer-Stops vs. zeitkritische Stops)
  - OP-7: Kaskaden-Verstärker vs. -Dämpfer pro Linie


---

### Ende

## Zurich Tram Flow
*Kay Wiegand · 2023–2025*

* **94,4 M** — Halt-Ereignisse
* **16** — Tramlinien
* **66** — Befunde
* **12** — Notebooks
* **18,56 s** — MAE · LightGBM v2
* **−63 %** — vs. Baseline
