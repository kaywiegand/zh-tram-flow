# Zürich Tram Flow

**Projekt:** Zürich Tram Flow
**Beschreibung:** One-Pager für Social/LinkedIn
**Autor:** Kay Wiegand
**Zielgruppe:** LinkedIn · Twitter · Social Media
**Dauer:** 5 Minuten
**Zeitraum:** 2023–2025
**GitHub:** [kaywiegand/zh-tram-flow](https://github.com/kaywiegand/zh-tram-flow)

---


---

### Headline

# Zurich Tram Flow

**Predictive Analytics für das Zürcher Tramnetz**
**94.4M Halt-Ereignisse · −63% MAE · Vier Handlungsfelder**

* **94.4M** — Halt-Ereignisse 2023–2025
* **87%** — OTP Status Quo vs. 95% Ziel
* **18.6s** — LightGBM MAE Vorhersagegenauigkeit
* **−63%** — Verbesserung vs. Baseline


---

### Die Frage

## Die Frage
*Sind Tramverspätungen vorhersagbar? Welche Muster stecken in den Daten?*

Das Zürcher Tramnetz hat ein strukturelles Pünktlichkeitsproblem. OTP 87%, Ziel 95% bis 2028. Wenn Verspätungen Mustern folgen, können wir:


---

### Drei Kernfindungen

## Drei Kernfindungen
*Was die Daten zeigen*

* **✓ Kaskadeneffekt: Verspätungen breiten sich aus**
  - Halt n+1 verzögert sich proportional zu Halt n
  - Pearson r ≥ 0.85 über alle 16 Linien — nicht Zufall
  - Bedeutung: Wenn wir die Kette unterbrechen, stabilisiert sich das Gesamtsystem
* **✓ Root Cause: dwell_time = 0 ist der Hebel**
  - Halte ohne geplante Standzeit können Verspätungen nicht aufholen
  - Typischerweise Koppelstellen — Linie 11 zeigt stärksten Effekt
  - Bedeutung: Fahrplan-Design ist die Ursache und der Hebel zugleich
* **✓ Das Modell ist produktionsreif**
  - LightGBM v2: 18.6s MAE auf ~29M Test-Fahrten (ganzes Jahr 2025)
  - MBE −0.69s, nahezu bias-frei. prev_trip_delay als Live-Signal verfügbar
  - Bedeutung: Echtzeit-Vorhersagen für Leitstelle sind technisch machbar


---

### Die Datenbasis

## Die Datenbasis
*94.4 Millionen Halt-Ereignisse, vier Datenquellen, ein konsistentes Dataset*

* **VBZ IST-Daten**
  - Reale Ankunfts- und Abfahrtszeiten aller Tramhalte 2023–2025
  - Trip × Stop × Zeitstempel Granularität
* **GTFS Fahrplan**
  - Geplante Zeiten, dwell_time, stop_sequence
  - Ermöglicht arrival_delay = IST − SOLL Berechnung
* **Meteo Schweiz**
  - Stündliche Messwerte: Temperatur, Niederschlag, Wind
  - Flags: has_rain, has_heavy_rain, is_hot
* **Event-Kalender**
  - Großveranstaltungen, Feiertage, Messen 2023–2025
  - Kategorisiert nach Typ und Größe

## Dataset-Metriken

* **94.4M** — Halt-Ereignisse
* **36** — Features (LightGBM v2)
* **541 MB** — Parquet (komprimiert)


---

### Vier Empfehlungen

## Vier Empfehlungen
*Direkt durch Analyse und Modell begründet*

* **R1 · Fahrplan-Design [Priorität 1]**
  - Standzeit-Puffer L11 an Koppelstellen
  - dwell_time = 0s ist Root Cause
  - +10s Puffer unterbricht Feedback-Loop
* **R2 · Real-Time Dispatch [Priorität 1]**
  - prev_trip_delay als Echtzeit-Signal nutzen
  - LightGBM v2 Inferenz: Millisekunden
  - MAE 18.6s nachgewiesen
* **R3 · Kapazitätsplanung [Priorität 2]**
  - Taktanpassung 20–22 Uhr
  - hour = 21 stärkstes Temporal-Feature
  - L11 & L8 zeigen erhöhtes Delay
* **R4 · Monitoring [Priorität 2]**
  - OTP-Fokus Kreise 11 & 12
  - Höchste Delay-Level, niedrigste OTP
  - Kombination mit Modell für Prognose


---

### Technologie & Robustheit

## Technologie & Robustheit
*Keine Black-Box — interpretierbar, reproduzierbar, produktionsreif*

* **Algorithmus**
  - LightGBM Gradient Boosting
  - 5× schneller als XGBoost, native Kategoricals
  - Feature Importance direkt interpretierbar
* **Aufteilung**
  - Temporal Split (kein Shuffle)
  - Train 2023–Jun 2024 · Val Jul–Dez 2024 · Test 2025
  - Zukunft darf Vergangenheit nicht kennen — verhindert Data Leakage
* **Validierung**
  - 18.6s MAE auf ~29M Test-Fahrten (ein ganzes Jahr)
  - XGBoost-Vergleich bestätigt Robustheit
  - Isotonic Regression Kalibrierung senkt MBE von +8.3s auf −0.69s


---

### Portfolio-Wert

## Portfolio-Wert
*Warum dieses Projekt zählt*

Das ist nicht Kaggle. Nicht eine akademische Übung. Das ist ein echtes ML-Projekt mit:

## Das Fazit

> Ich habe ein ML-Projekt von Grund auf gebaut — mit echten Stakeholder-Fragen, echter Datenqualitäts-Arbeit, echter Produktion. Die Kaskadenentdeckung war das, was alles transformiert hat. Das ist nicht der Algorithmus — das ist die Arbeit davor.
