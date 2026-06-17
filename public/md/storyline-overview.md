# Zurich Tram Flow

**Projekt:** Zürich Tram Flow
**Beschreibung:** Verspätungsvorhersage im Zürcher Tramnetz, Datengetriebenes Analyse- und ML-Projekt
**Autor:** Kay Wiegand  
**Zielgruppe:** HR · Business · Hiring Manager  
**Dauer:** 10 Minuten  
**Fakt:** 94.4M, Halt-Ereignisse 2023–2025
**Fakt:** 87%, OTP · Ziel: 95%
**Fakt:** 71.3%, Haltestellen ohne Puffer
**Fakt:** 18.6s, Vorhersage-MAE LightGBM v2

---

## Agenda
1. Die Ausgangssituation
2. Die Überraschungen
3. Die Erkenntnis
4. Das Modell
5. Die Handlungsempfehlungen
6. Das Resultat
7. Der Projektrahmen

---

## 1. Ausgangssituation
* **Netzweite OTP (2023–2025):** 87.0% (Ziel: 95%)
* **Ø Ankunftsverspätung:** 56.3s
* **Analysebasis:** 16 Tramlinien, systematischer Rückstand über alle Jahre

---

## 2. Die Überraschungen
* **Hotspots:** Nicht die Innenstadt (Central/Paradeplatz), sondern die Peripherie (Enzenbühl, Balgrist).
* **Peak-Zeiten:** Nicht der Morgenrush, sondern 21:00 Uhr aufgrund von Veranstaltungs-Abreisewellen.
* **Wetter:** Schnee ist nur ein Verstärker (+54s); die Grundursache ist das wetterunabhängige Fahrplan-Design.

---

## 3. Die Erkenntnis
* **Fahrplan-Design:** 71.3% aller Haltestellen haben 0 Sekunden Pufferzeit.
* **Kaskadeneffekt:** Verspätungen bauen sich entlang der Strecke auf (Korrelation $r \geq 0.85$).
* **Fazit:** Es ist kein Betriebsversagen, sondern ein strukturelles Design-Thema. Was im Fahrplan nicht vorgesehen ist, kann im Betrieb nicht ausgeglichen werden.

---

## 4. Das Modell
* **Ergebnis:** LightGBM v2 erreicht einen MAE von **18.6 Sekunden**.
* **Verbesserung:** −63% gegenüber der Baseline (Stop Mean).
* **Nutzen:** Kombination aus Zeit, Wetter und Vorgänger-Trip-Delay ermöglicht Frühwarnungen vor Einsetzen der Kaskade.

---

## 5. Handlungsempfehlungen
1. **Fahrplan-Design:** Gezielte Standzeit-Puffer auf Linie 11 einführen.
2. **Betriebssteuerung:** Vorhersagemodell als Frühwarnsignal in die Leitstelle integrieren.
3. **Kapazitätsplanung:** Takterhöhung auf L11 und L8 zwischen 20:00 und 22:00 Uhr.
4. **Monitoring:** Stadtkreise 11 und 12 als strukturelle Prioritätszonen etablieren.

---

## 6. Resultat
* **Kernbotschaft:** "Was vorhersagbar ist, ist steuerbar."
* **Ziel:** Schließung der Lücke von 87% (heute) auf 95% (VBZ-Ziel 2028).

---

## 7. Projektrahmen
* **Datenbasis:** 94.4 Mio. Halt-Ereignisse, kombiniert aus VBZ IST-Daten, GTFS und Meteo Schweiz.
* **Technologie:** Python, Polars (für schnelles Data Engineering), LightGBM.
* **Reproduzierbarkeit:** Vollständig dokumentiert auf [GitHub](https://github.com/kaywiegand/zh-tram-flow).

---

## Danke
* Zurich Tram Flow  · 2023–2025
* Kay Wiegand
* 94.4M Halt-Ereignisse
* 63 Befunde
* 12 Notebooks
* 18.6s MAE · LightGBM v2
* −63% vs. Baseline
* Technischer Deep Dive →
* Projektverlauf →
* Live-App →
* https://github.com/kaywiegand/zh-tram-flow



