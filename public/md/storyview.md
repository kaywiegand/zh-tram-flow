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

1. Die Ausgangsfrage
2. Data Engineering
3. Exploration
4. Die Erkenntnis
5. Machine Learning
6. Die Handlungsempfehlungen
7. Projektrahmen und Workflow


---

### Ausgangsfrage

## Die Ausgangsfrage
*Eine einfache Beobachtung, eine konkrete Frage*

> Das Zürcher Tramnetz operiert mit 87 % OTP systemisch unter dem VBZ-Zielwert von 95 %. An 71,5 % aller Halte akkumulieren Trams Verspätung. Das ist kein Wetter- und kein Event-Problem. Die Frage: Wo entsteht die Verspätung wirklich — und ist sie vorhersagbar?
* *87 %* — OTP netzweit 2023–2025
* **95 %** — VBZ-Ziel bis 2028
* **−8 PP** — Strukturelle Lücke
* **56,3 s** — Ø Ankunftsverspätung


---

### Data Engineering

## Data Engineering
*Vier Quellen, ein reproduzierbarer Pipeline*

* **Primärquelle: VBZ IST-Daten**
  - Reale Ankunfts- und Abfahrtszeiten aller Tramhalte 2023–2025
  - Granularität: jede Fahrt, jede Haltestelle, jeder Zeitstempel
  - 94,4 Mio. Zeilen — verarbeitet mit Polars (lazy evaluation)
* **Fahrplandaten: GTFS**
  - Geplante Zeiten, dwell_time, stop_sequence, Liniengeometrien
  - Ermöglicht Berechnung von arrival_delay = IST − SOLL
* **Wetterdaten: Meteo Schweiz**
  - Stündliche Messwerte: Temperatur, Niederschlag, Windgeschwindigkeit
  - Flags: has_rain, has_snow, is_hot — für Modell und EDA
* **Event-Kalender**
  - Grossveranstaltungen Zürich 2023–2025: Konzerte, Messen, Sport, Feiertage
  - Ergebnis: 94,4 Mio. Zeilen · 26 Features · 541 MB Parquet

## Data Engineering
*Cleaning als Forschungsentscheidung, nicht als Routine*



---

### Exploration

## Exploration
*Drei Überraschungen und ein Muster*


## Exploration
*Hotspots an der Peripherie, Peak am Abend*


## Exploration
*Wetter: Schnee und Regen treffen unterschiedliche Stadtteile*

* **+54s** — Schnee-Effekt netzweit
* **+23,3 s** — Regen-Effekt netzweit
* **−9,9 s** — Feiertage vs. Normal
* **66,0 s** — Fachmessen (schlechteste Event-Kategorie)
> Feiertage sind der beste Tagestyp: −9,9 s vs. Normal. Der MIV-Rückgang überwiegt jeden Event-Effekt. Event-Wirkung ist ein Abend-Phänomen (18–22h): tagsüber kein messbarer Unterschied.


---

### Erkenntnis

## Die Erkenntnis
*Kein Puffer im Fahrplan, die Verspätung kaskadiert — in vier Schritten bewiesen*

* **71,5 %** — Halte akkumulieren Delay
* **L11** — 68,7 s · OTP 82 %, stärkste Akkumulation
* **71,3 %** — Haltestellen ohne Standzeit (0s)
* **r ≥ 0,85** — Kaskadenkorrelation alle 16 Linien


---

### Machine Learning

## Machine Learning
*Ziel: arrival_delay in Sekunden — direkt kommunizierbar, kein Schwellwert-Bias*

> Warum ML? Weil die Struktur der Daten nichtlinear ist: Linie × Haltestelle × Tageszeit × Wetter × Event interagieren auf eine Weise, die kein handcodiertes Modell erfassen kann. Und weil prev_trip_delay ein Echtzeit-Signal ist, das einen Feedback-Loop im Modell ermöglicht.

## Machine Learning
*Der Kaskadenindikator erklärt den Sprung von v1 auf v2*

* **41 Mio.** — Trainings-Fahrten 2023–Jun 2024
* **~29 Mio.** — Test-Fahrten vollständiges Jahr 2025
* **−0,69 s** — MBE nach Isotonic-Regression-Kalibrierung
> prev_trip_delay ist das stärkste neue Feature in v2 und erklärt den Sprung von 45,7 s auf 18,56 s MAE. Das Signal war in den Daten — die EDA hat es zuerst aufgezeigt, das Modell hat es bestätigt.

## Machine Learning
*Feature Importance bestätigt die Kaskadenthese*


## Machine Learning
*Das Modell in konkreten Szenarien*

> Das Modell kombiniert 36 Features zu einer konkreten Sekundenvorhersage. Drei Beispiele aus echten Betriebssituationen:


---

### Empfehlungen

## Die Handlungsempfehlungen
*Vier Empfehlungen, direkt durch Befunde gedeckt*



---

### Projektrahmen

## Der Projektrahmen
*Open Data, AI-Workflow, vollständig reproduzierbar*

* **Datenbasis und Umfang**
  - VBZ IST-Daten · GTFS · Meteo Schweiz · Event-Kalender
  - 94,4 Mio. Zeilen · 26 Features · 541 MB Parquet
  - 3 vollständige Betriebsjahre · 16 Linien · ca. 190 Haltestellen
  - 66 dokumentierte Befunde in 12 Jupyter-Notebooks
* **Technologie-Stack**
  - Python · Polars (85 Mio. Zeilen, lazy evaluation) · Jupyter · uv
  - LightGBM (Modellierung) · Plotly (Visualisierung) · Streamlit (Dashboard)
  - Trainingszeit LightGBM v2: ca. 18 Minuten auf Consumer-Hardware
* **AI-Workflow als Differenziator**
  - Claude Code für iterative Analyse, Code-Refactoring, Dokumentation
  - Promptbasiertes Scaffolding: von der Idee zur Notebook-Struktur in Minuten
  - Menschliche Entscheidungsverantwortung bleibt bei allen Finding-Interpretationen
* **Reproduzierbarkeit**
  - Vollständiger Code auf GitHub, alle Datenquellen öffentlich
  - Data Engineering vollständig reproduzierbar via Polars-Pipeline
  - Alle Befunde rückverfolgbar auf Finding-IDs in den Notebooks

## Was vorhersagbar ist, ist steuerbar.
*Ein Projekt, das zeigt: Datengetriebene Analyse ist kein akademisches Artefakt — sie liefert operative Entscheidungsgrundlagen.*

* **87 %** — OTP heute
* **95 %** — VBZ-Ziel 2028

## Zurich Tram Flow
*Kay Wiegand · 2023–2025*

* **94,4 M** — Halt-Ereignisse
* **16** — Tramlinien
* **66** — Befunde
* **12** — Notebooks
* **18,56 s** — MAE · LightGBM v2
* **−63 %** — vs. Baseline
