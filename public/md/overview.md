# Zurich Tram Flow

**Projekt:** Zurich Tram Flow
**Beschreibung:** Ergebnisse & Handlungsempfehlungen
**Autor:** Kay Wiegand
**Zielgruppe:** HR · Business · Hiring Manager
**Dauer:** 10 Minuten
**Zeitraum:** 2023–2025
**GitHub:** [kaywiegand/zh-tram-flow](https://github.com/kaywiegand/zh-tram-flow)

---


---

### Einstieg

# Zurich Tram Flow

**Verspätungsvorhersage im Zürcher Tramnetz**
**Datengetriebenes Analyse- und ML-Projekt**

* **94,4 M** — Halt-Ereignisse 2023–2025
* **87 %** — OTP · Ziel: 95 %
* **71,3 %** — Haltestellen ohne Puffer
* **18,56 s** — Vorhersage-MAE LightGBM v2

## Inhalt
*Diese Präsentation auf einen Blick*

1. Die Ausgangssituation
2. Die Überraschungen
3. Die Erkenntnis
4. Das Modell
5. Die Handlungsempfehlungen
6. Das Resultat
7. Der Projektrahmen


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

## Alle 16 Linien im Soll
*Keine einzige Linie erreicht das Ziel — die Lücke zieht sich durch das gesamte Netz*


## Kein Aufwärtstrend erkennbar
*OTP schwankt saisonal, aber der Mittelwert bewegt sich seit 2023 nicht*



---

### Überraschungen

## Widerlegte Annahmen
*Drei Erwartungen, die die Daten klar widerlegen*


## Die Innenstadt ist pünktlicher
*Verspätungs-Hotspots liegen an der Peripherie, nicht im Stadtzentrum*


## Der Peak am Abend
*Um 21 Uhr entstehen die höchsten Verspätungen — nicht im Morgenrush*



---

### Erkenntnis

## Die Kaskade bei den Verspätungen
*Ohne Puffer im Fahrplan überträgt sich jede Verspätung auf die Folgefahrten*

* **71,5 %** — Halte die Delay akkumulieren
* **L11** — 68,7 s · OTP 82 % — stärkste Akkumulation
* **71,3 %** — Haltestellen ohne Standzeit
* **r ≥ 0,85** — Kaskadenkorrelation alle 16 Linien
> Das ist kein Betriebsversagen. Es ist ein Fahrplan-Design-Thema. Was im Fahrplan nicht vorgesehen ist, kann im Betrieb nicht ausgeglichen werden.
> Zwei externe Einflussfaktoren sind messbar und erheblich: Schnee (+54s) und Grossevents (bis +66s bei Fachmessen). Doch das Grundniveau der Verspätung bleibt auch bei optimalen Bedingungen konstant hoch. Externe Faktoren verstärken, was intern bereits strukturell angelegt ist.
> Trotz Bauphasen, Streckensperrungen und Fahrplanumstellungen hält die VBZ das System bemerkenswert stabil. Die Verspätungslevel schwanken durch diese Eingriffe kaum. Die Ursache liegt nicht in externen Störungen, sondern im Fahrplan-Design selbst.


---

### Das Modell

## Drei Iterationen der Modellierung
*Von der Baseline über Feature Engineering zum finalen Ensemble-Modell*

> Der Sprung von v1 auf v2 kam nicht durch einen besseren Algorithmus, sondern durch das richtige Signal aus der Analyse: den Kaskadenindikator (prev_trip_delay).

## 18,56 Sekunden MAE
*Mittlerer Vorhersagefehler auf einem vollständigen, ungesehenen Testjahr — 63 % unter der Baseline*

* **41 Mio.** — Trainings-Fahrten 2023 bis Mitte 2024
* **~29 Mio.** — Test-Fahrten, vollständiges Jahr 2025
* **−63 %** — Verbesserung vs. Baseline (Stop Mean)
> Kalibrierter Bias: −0.69 Sekunden, nahezu verzerrungsfrei. Trainiert auf Consumer-Hardware in ca. 18 Minuten.

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
*Die Verspätungen im Zürcher Tramnetz folgen klaren Mustern. Das Fahrplan-Design ist die Ursache und der Hebel. Vier Handlungsempfehlungen sind durch die Daten direkt begründet.*



---

### Projektrahmen

## Offen & reproduzierbar
*Open Data, reproduzierbar und vollständig dokumentiert*

* **Datenbasis**
  - VBZ IST-Daten: reale Ankunfts- und Abfahrtszeiten aller Tramhalte
  - GTFS: Fahrplandaten, Haltestellen-Koordinaten, Liniengeometrien
  - Meteo Schweiz: stündliche Messwerte (Temperatur, Niederschlag, Schnee)
  - Event-Kalender: Grossveranstaltungen Zürich 2023–2025
  - Ergebnis: 94,4 Mio. Zeilen · 26 Features · 541 MB Parquet
* **Umfang und Zeitaufwand**
  - Zeitraum: 3 vollständige Betriebsjahre (2023, 2024, 2025)
  - 16 Tramlinien, ca. 190 Haltestellen im Netz
  - 66 dokumentierte Analyse-Befunde in 12 Notebooks
  - Ca. 3 Wochen: 1 Woche Data Engineering, 2 Wochen Analyse und Modellierung
* **Technologie-Stack**
  - Python · Polars (85 Mio. Zeilen, lazy evaluation) · Jupyter · uv
  - LightGBM (Modellierung) · Plotly (Visualisierung) · Streamlit (Dashboard)
  - Trainingszeit LightGBM v2: ca. 18 Minuten auf Consumer-Hardware
* **Reproduzierbarkeit**
  - Vollständiger Code auf GitHub veröffentlicht
  - Data Engineering vollständig reproduzierbar via Polars-Pipeline
  - Alle Datenquellen öffentlich: VBZ Open Data · Meteo Schweiz · GTFS
  - 12 Jupyter-Notebooks, vollständig ausgeführt und dokumentiert
  - Alle Befunde rückverfolgbar auf Finding-IDs in den Notebooks


---

### Ende

# Zurich Tram Flow

**Verspätungsvorhersage im Zürcher Tramnetz**
**Datengetriebenes Analyse- und ML-Projekt**

* **94,4 M** — Halt-Ereignisse 2023–2025
* **87 %** — OTP · Ziel: 95 %
* **71,3 %** — Haltestellen ohne Puffer
* **18,56 s** — Vorhersage-MAE LightGBM v2
