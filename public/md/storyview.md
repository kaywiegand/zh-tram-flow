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

**Verspätungsvorhersage im Zürcher Tramnetz**
**Datengetriebenes Analyse- und ML-Projekt | 2023–2025**

* **94,4 M** — Halt-Ereignisse
* **87 %** — OTP heute · Ziel: 95 %
* **18,56 s** — MAE LightGBM v2
* **−63 %** — vs. Baseline

## Übergreifende These
*Ein Satz, der das gesamte Projekt trägt*

> Die Verspätungen im Zürcher Tramnetz sind vorhersagbar — weil sie im Fahrplan-Design verankert sind, nicht im zufälligen Betrieb.

## Inhaltsübersicht
*Der gesamte Daten-Lifecycle von Rohdaten bis Vorhersage-Modell*

1. Ausgangssituation
2. Exploration / EDA
3. Data Preprocessing
4. Analyse & Erkenntnisse
5. Machine Learning
6. Praxisanwendung
7. Empfehlungen
8. Technische Umsetzung
9. Ausblick


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

## Vorgehen in zwei Schritten
*Von der Ursachenanalyse zur Vorhersage*


## Alle Linien nicht im Soll
*Keine einzige Linie erreicht dauerhaft das Ziel<br>Die Lücke zieht sich durch das gesamte Netz*


## Kein Aufwärtstrend erkennbar
*OTP schwankt saisonal, aber der Mittelwert bewegt sich seit 2023 nicht*



---

### Exploration / EDA

## Widerlegte Annahmen
*Drei initiale Annahmen wurden mit Befunden aus den Daten klar widerlegt*


## Innenstadt ist pünktlicher
*Räumlich: Verspätungs-Hotspots liegen an der Peripherie, nicht im Stadtzentrum*


## Peak am Abend
*Temporal: Um 21 Uhr entstehen die höchsten Verspätungen — nicht im Morgenrush<br>Der Peak um 2 Uhr ist ein Artefakt des Nachtbetriebs — bei minimaler Fahrtenzahl wirkt jede einzelne Verspätung überproportional gross*


## Weitere Eindrücke
*Erste Kennzahlen aus der explorativen Datenanalyse*

* **+54 s** — Schnee-Effekt netzweit
* **+23,3 s** — Regen-Effekt netzweit
* **−9,9 s** — Feiertage vs. Normal
* **66,0 s** — Fachmessen (schlechteste Event-Kategorie)
* **Einordnung**
  - Feiertage sind der beste Tagestyp: −9,9 s vs. Normal
  - Der Rückgang des motorisierten Individualverkehrs (MIV) an Feiertagen überwiegt jeden Event-Effekt
  - Event-Wirkung ist ein Abend-Phänomen (18–22h): tagsüber kein messbarer Unterschied


---

### Data Preprocessing

## Master-Datensatz und GTFS-Fahrplandaten
*Data Refinement als Fundament mit initialen Master-Datensatz und GTFS Fahrplandaten*

* **VBZ IST-Daten (Primärquelle)**
  - Reale Ankunfts- und Abfahrtszeiten aller Tramhalte 2023–2025
  - Granularität: Fahrt × Haltestelle × Timestamp
  - Enthält canceled = True Fahrten — bewusst behalten (relevante Extremfälle)
* **GTFS (Fahrplandaten)**
  - Geplante Ankunfts-/Abfahrtszeiten, dwell_time, stop_sequence
  - Liniengeometrien und Haltestellen-Koordinaten (lat/lon)
  - Join-Key: trip_id × stop_id × service_date

## Kontextquellen der Dimensionen
*Für jede Analysedimension wurden die Datenquellen im Vorfeld im Master-Datensatz schon kontextuell angereichert*

* **Meteo Schweiz**
  - Stündliche Messwerte: Temperatur, Niederschlag, Windgeschwindigkeit
  - Join über Zeitstempel (hour-level) auf IST-Daten
  - Abgeleitete Flags: has_rain, has_snow, has_heavy_rain, is_hot
* **Event-Kalender**
  - Grossveranstaltungen Zürich 2023–2025: Konzerte, Messen, Sport
  - Kategorisierung: event_type, event_size, event_weight
  - Ergebnis: 94,4 Mio. Zeilen · 26 Features · 541 MB Parquet
* **Network**
  - Linientopologie: 16 Linien, ca. 190 Haltestellen
  - Kontext-Features: n_lines_at_stop, n_stops_line
  - Basis für linienübergreifendes Lernen (stop_sequence_pct)
* **Target**
  - arrival_delay in Sekunden, aus IST- vs. Soll-Zeit berechnet
  - OTP-Schwellwert: Ankunft ≤ 2 Minuten Verspätung
  - canceled = True bewusst als Extremfall im Target erhalten

## Cleaning, Split und Encoding
*Mit der passenden Data Preparation zur finalen Struktur für das Modell*



---

### Analyse & Erkenntnisse

## Kaskade der Verspätungen
*Ohne Puffer im Fahrplan überträgt sich jede Verspätung auf die Folgefahrten — in Zahlen*

* **71,5 %** — Halte akkumulieren Delay
* **L11** — 68,7 s · OTP 82 % — stärkste Akkumulation
* **71,3 %** — Haltestellen ohne Standzeit (0 s)
* **r ≥ 0,85** — Kaskadenkorrelation alle 16 Linien
> Was an einem Halt beginnt, endet nicht dort:

## Aufbau der Kaskade
*Vier Schritte, vom ersten Anzeichen bis zum netzweiten Beweis*


## Fahrplan-Design-Thema
*Die Verspätungen sind durch die Fahrplangestaltung strukturell angelegt*

> <span class="sw-normal">Das ist kein Betriebsversagen.</span><br><br>Es ist ein Fahrplan-Design-Thema.<br><span class="sw-normal">Was im Fahrplan nicht vorgesehen ist, kann im Betrieb nicht ausgeglichen werden.</span>

## Einfluss externer Faktoren
*Wetter und Grossevents wirken, das Grundproblem bleibt strukturell*

> Zwei externe Einflussfaktoren sind messbar und erheblich: Schnee (+54 s) und Grossevents (bis +66 s bei Fachmessen). Doch das Grundniveau der Verspätung bleibt auch bei optimalen Bedingungen konstant hoch. Externe Faktoren verstärken, was intern bereits strukturell angelegt ist.
> Trotz Bauphasen, Streckensperrungen und Fahrplanumstellungen hält die VBZ das System bemerkenswert stabil. Die Verspätungslevel schwanken durch diese Eingriffe kaum. Die Ursache liegt nicht in externen Störungen, sondern im Fahrplan-Design selbst.


---

### Machine Learning

## Dynamische Modelle statt starrer Regeln
*Herkömmliche Systeme scheitern an nichtlinearen Daten*

> Die Struktur der Daten ist nicht linear.

## Drei Iterationen der Modellierung
*Von der Baseline über Feature Engineering zum finalen Ensemble-Modell*

> Feature Engineering schlägt Hyperparameter-Tuning.

## 18,56 Sekunden MAE
*Mittlerer Vorhersagefehler auf einem vollständigen, ungesehenen Testjahr — 63 % unter der Baseline*

* **41 Mio.** — Trainings-Fahrten 2023–Jun 2024
* **~29 Mio.** — Test-Fahrten vollständiges Jahr 2025
* **−0,69 s** — MBE nach Isotonic-Regression-Kalibrierung
> 18,56 Sekunden bestätigen die Analyse.

## Feature Importance
*prev_trip_delay und stop_sequence_pct dominieren<br>Temporale und Wetter-Features zeigen konsistente, aber schwächere Beiträge*

> Die Kaskadenanalyse (r ≥ 0,85) hat die Feature-Wichtigkeit korrekt antizipiert — das Signal steckt in den Daten, nicht im Algorithmus.


---

### Praxisanwendung

## Konkreter Nutzen in der Praxis
*Konkrete Vorhersagen für reale Betriebssituationen zeigen die operative Relevanz*

> Das Modell kombiniert Tageszeit, Linie, Haltestelle, Wetterlage und den Verspätungsstatus des Vorgänger-Trips zu einer konkreten Sekundenvorhersage. So lassen sich kritische Situationen identifizieren, bevor die Kaskade einsetzt.


---

### Empfehlungen

## Konkrete Handlungsempfehlungen
*Jede Empfehlung ist direkt durch einen Befund aus der Analyse gedeckt*



---

### Technische Umsetzung

## Datenbasis & TechStack
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

## AI Workflow & Pipeline
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

### Ausblick

## Was noch zu erforschen ist
*Dashboard-Exploration offenbarte 7 systematische Forschungsmöglichkeiten*

> Warum sind Fahrtrichtungen asymmetrisch?<br>Welche Linien dämpfen Delays, welche verstärken sie?
* **OP-1**
  - Direction-Asymmetrie (~10 s Delta zwischen Richtung A/B)
* **OP-2**
  - Stop-Variabilität (Puffer-Stops vs. zeitkritische Stops)
* **OP-7**
  - Kaskaden-Verstärker vs. -Dämpfer pro Linie


---

### Resultat

## Zurich Tram Flow
*Verspätungsvorhersage im Zürcher Tramnetz<br>Datengetriebenes Analyse- und ML-Projekt | 2023–2025*

> Was vorhersagbar ist, ist steuerbar.
