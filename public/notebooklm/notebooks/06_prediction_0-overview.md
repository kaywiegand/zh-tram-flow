# Prediction — Overview

Fahrplan für die Modellierungsphase: Was wir vorhersagen, warum, wie, und womit.

## Was wir vorhersagen

**Zielvariable: `arrival_delay` in Sekunden** — wie verspätet ist eine Tram wenn sie an einer Haltestelle ankommt?

- **Aufgabe:** Regression (kontinuierlicher Wert, kein Ja/Nein)
- **Metrik:** MAE (Mean Absolute Error) — durchschnittlicher Fehler in Sekunden
- **Ziel:** MAE deutlich unter dem Basis-Netzschnitt von ~56s

**Warum Regression, nicht Klassifikation (OTP Ja/Nein)?**
- Regression gibt mehr Information: "32s Verspätung" ist nützlicher als "pünktlich"
- OTP-Klasse kann jederzeit aus der Regression abgeleitet werden: `arrival_delay > 120s → verspätet`
- Für das spätere Dashboard ist der konkrete Sekundenwert das bessere Input

## Das konkrete Szenario

**Frage, die das Modell beantwortet:**
> *„Ich will am Donnerstag um 21:30 Uhr mit der Linie 11 zur Haltestelle Balgrist — wie viel Verspätung muss ich einkalkulieren?"*

---

### Was der User eingibt

| Input | Beispiel | Woher |
|:---|:---|:---|
| **Datum** | Donnerstag, 5. Juni 2026 | Kalender — 14 Tage in die Zukunft |
| **Uhrzeit** | 21:30 Uhr | Nutzer |
| **Haltestelle** | Balgrist | Nutzer wählt aus Liste |
| **Linie** | Linie 11 | Nutzer wählt aus Liste |
| **Wetterlage** | Regen, 12°C | Wettervorhersage API (z.B. Open-Meteo) |
| **Event** | Keine / Klein / Mittel / Gross | Nutzer wählt Cluster — oder automatisch aus Eventkalender |

### Was das Modell daraus macht

Das Modell übersetzt die Nutzer-Eingaben in die 40 Feature-Spalten die es beim Training gesehen hat:

```
hour=21, weekday=3 (Do), month=6, season=2 (Sommer), is_weekend=False
line_name="11", stop_name="Balgrist", district_nr=8
has_rain=True, temperature=12, precipitation=1.4
has_event=False, event_weight=0
...
```

→ Ausgabe: **Erwarteter `arrival_delay` in Sekunden** + OTP-Klasse (pünktlich / verspätet)

---

### Zur Fahrtrichtung

Die Fahrtrichtung ist im MVP **implizit** — das Modell kennt Haltestelle + Linie und hat gelernt, dass Balgrist auf Linie 11 ein Endkorridors-Stop ist mit hohem Delay. Explizite Richtungseingabe (→ Zürich HB vs. → Auzelg) ist eine v2-Erweiterung: dafür müsste `terminus` (letzter Stop des Trips) als Feature ergänzt werden. Der Effekt auf die MAE ist laut `03_analysis_4-spatial.ipynb` messbar aber nicht dramatisch — gut für Iteration 2.

## Warum Machine Learning?

Die EDA hat gezeigt: einfache Formeln reichen nicht.

- **Wetter-Korrelationen** sind nicht-linear: max. r = 0.03 (Pearson) — aber Schnee kostet +54s. Der Effekt existiert, ist aber nicht proportional
- **Interaktionen** erklären mehr als Einzelfaktoren: `hour × event_weight` ist stärker als beides allein (F-EVNT-03)
- **Ortsspezifische Effekte**: Linie 11 verhält sich fundamental anders als Linie 6 — nicht durch eine Formel darstellbar
- **Schwellenwerteffekte**: Schnee ab einer gewissen Intensität, Events ab 18h — klassische Baummodell-Stärke

→ Ein Modell das Entscheidungsbäume baut (LightGBM) kann all das lernen.

## Die Datenbasis

| Datei | Zeilen | Verwendung |
|:---|---:|:---|
| `train_final.parquet` | 55.5 Mio. | Modell trainieren |
| `test_final.parquet` | ~25 Mio. | Modell evaluieren — unberührt bis zum Schluss |

**Split-Strategie:** Temporal — 2023–2024 Train / 2025 Test. Kein Random-Shuffle, weil das Datenleck erzeugen würde (Daten vom gleichen Tag würden in Train und Test landen).

**32 Features im Modell** — definitive Liste in `data/models/lgbm_v1_meta.json`:

| Gruppe | Anzahl | Features |
|:---|:---:|:---|
| **Netz** | 7 | `line_name` · `stop_name` · `district_nr` · `n_lines_at_stop` · `n_stops_line` · `is_start_stop` · `is_end_stop` |
| **Zeit** | 8 | `hour` · `weekday` · `month` · `year` · `season` · `is_weekend` · `is_november` · `is_late_night_weekend` |
| **Wetter** | 9 | `temperature` · `precipitation` · `wind_speed` · `flood_intensity` · `has_rain` · `has_heavy_rain` · `has_snow` · `has_flood` · `is_hot` |
| **Events** | 6 | `event_type` · `event_size` · `is_holiday` · `has_event` · `event_weight` · `event_weight_x_hour` |
| **Fahrplan** | 2 | `dwell_time` · `gtfs_year` |

**5 kategoriale Spalten** (LightGBM Native-Categorical): `line_name` · `stop_name` · `event_type` · `season` · `gtfs_year`

**Bewusst ausgeschlossen:**

| Spalte | Grund |
|:---|:---|
| `departure_delay` · `delay_delta` | Leakage — kennen wir erst wenn die Tram schon da ist |
| `operating_date` · `trip_id` | Identifier, kein inhaltliches Feature |
| `stop_lat` · `stop_lon` | Durch `stop_name` + `district_nr` abgedeckt |
| `event_name` · `event_location` | Zu granular, zu viele unique Values |
| `canceled` | Target-nahe Information, kein Prediction-Feature |

### Hinweis — Analyse vs. Modell

Die **Analyse-Notebooks** (`03_analysis_*`) verwenden `lf_all = concat(TRAIN, TEST)` — alle 3 Jahre, voller Datensatz via Polars LazyFrame. Das ist methodisch korrekt: EDA beschreibt die Realität, kein Modell sieht dabei die Zukunft.

Das **Modell** hingegen sieht nur `train_final.parquet` (2023–Jun 2024). Der Test-Split (2025) bleibt unberührt bis zur finalen Evaluation. `departure_delay` und `delay_delta` sind in der EDA nutzbar aber im Modell ausgeschlossen (Leakage — erst bekannt wenn die Tram angekommen ist).

→ Details zur lf_clean-Strategie und Datenstrategie: `03_analysis_0-overview.ipynb`

## Das Modell — LightGBM

**LightGBM** ist ein Gradient-Boosting-Algorithmus — er baut viele kleine Entscheidungsbäume, die nacheinander die Fehler des vorherigen Baums korrigieren.

**Warum LightGBM, nicht XGBoost oder Random Forest?**
- Deutlich schneller auf großen Datensätzen (55 Mio. Zeilen)
- Kann kategoriale Features (`line_name`, `stop_name`, `event_type`) direkt verarbeiten — kein manuelles Encoding nötig
- Feature Importance direkt eingebaut → erklärt was das Modell gelernt hat
- Sehr gute Out-of-the-box Performance, wenig Tuning zum Start nötig

**Wie lernt das Modell?**
1. Es nimmt alle 55 Mio. Trainingszeilen
2. Baut einen ersten einfachen Baum: "wenn hour > 20 und has_snow → höherer Delay"
3. Schaut was noch falsch ist (Residuen)
4. Baut nächsten Baum der die Fehler des ersten korrigiert
5. Wiederholt das 200–1000 Mal
6. Finale Vorhersage = Summe aller Bäume

**Encoding-Entscheidungen (vor dem Training zu treffen):**
- `stop_name` (6.000+ unique) → LightGBM Native-Categorical oder Target-Encoding mit n-Threshold ≥ 1.000
- `line_name`, `event_type`, `gtfs_year` → LightGBM Native-Categorical
- `season`, `weekday`, `month` → bereits numerisch, kein Encoding nötig

## Modell-Vergleich — Warum LightGBM?

| Modell | Nicht-linear | Schnell (55 Mio.) | Native Categoricals | Feature Importance | Unser Urteil |
|:---|:---:|:---:|:---:|:---:|:---|
| **Lineare Regression** | ❌ | ✅ | ❌ | ✅ | Zu schwach — Korrelationen max. r=0.03 |
| **Ridge / Lasso** | ❌ | ✅ | ❌ | ✅ | Nur als Baseline-Kandidat |
| **Random Forest** | ✅ | ❌ | ❌ | ✅ | Zu langsam auf 55 Mio. Zeilen |
| **XGBoost** | ✅ | 🟡 | ❌ | ✅ | Gut, aber langsamer als LightGBM |
| **LightGBM** | ✅ | ✅ | ✅ | ✅ | **Primärmodell** |
| **CatBoost** | ✅ | 🟡 | ✅✅ | ✅ | Alternative wenn stop_name problematisch |

**Die drei entscheidenden Kriterien für unser Projekt:**

1. **Nicht-linear** — EDA zeigt Schwellenwerteffekte (Schnee, Events ab 18h) → lineare Modelle können das nicht lernen
2. **Schnell auf 55 Mio. Zeilen** — LightGBM arbeitet mit Histogramm-Splitting statt alle Datenpunkte einzeln zu prüfen → 5–10× schneller als XGBoost auf großen Daten
3. **Native Categoricals** — `stop_name` hat 6.000+ unique Values, `line_name` 16. LightGBM kann Kategoricals direkt verarbeiten — kein aufwändiges Encoding nötig, das Overfitting riskiert

**Wie Gradient Boosting funktioniert (vereinfacht):**
- Baum 1 sagt: „Ø 56s für alle" → Fehler: mal zu viel, mal zu wenig
- Baum 2 lernt die Fehler von Baum 1: „Bei Schnee und L9 ist Baum 1 60s zu niedrig" → korrigiert
- Baum 3 lernt die Fehler von Baum 1+2 → korrigiert weiter
- Nach 300–1000 Bäumen: Summe aller Korrekturen = präzise Vorhersage

## Metriken — Was messen wir?

| Metrik | Einheit | Formel (vereinfacht) | Stärke | Schwäche | Wir nutzen |
|:---|:---|:---|:---|:---|:---:|
| **MAE** | Sekunden | Ø |Fehler| | Intuitiv: „Im Schnitt X Sekunden daneben“ | Behandelt alle Fehler gleich | ✅ Primär |
| **RMSE** | Sekunden | √(Ø Fehler²) | Bestraft große Ausreisser stärker | Schwerer zu interpretieren | ✅ Sekundär |
| **R²** | 0–1 | 1 − (Fehler / Varianz) | Zeigt: wie viel erklärt das Modell? | Bei schiefer Verteilung irreführend | ℹ️ Orientierung |
| **OTP-Accuracy** | % | Anteil |Fehler| ≤ 60s | Business-relevant | Ignoriert Größe des Fehlers | ✅ Ergänzend |
| **MAPE** | % | Ø |Fehler / Ist-Wert| | Prozentual verständlich | Explodiert bei delay ≈ 0s | ❌ |
| **SMAPE** | % | Ø |Fehler| / Ø(|Ist|+|Pred|) | Symmetrischer als MAPE | Gleiches Problem nahe 0; unintuitiv | ❌ |
| **MdAE** | Sekunden | Median |Fehler| | Robuster gegen Ausreisser als MAE | Ignoriert Häufigkeit extremer Fehler | ❌ |
| **MSLE** | — | Ø (log(Pred+1) − log(Ist+1))² | Gut für rechtschiefe Verteilungen | Bricht bei negativen Werten (Frühankunft) zusammen | ❌ |
| **MBE** | Sekunden | Ø (Pred − Ist) | Zeigt systematischen Bias des Modells | Kein Genauigkeitsmaß — pos./neg. heben sich auf | ❌ |
| **Pinball Loss** | — | Gewichtete Quantil-Abweichung | Für probabilistische Forecasts (Konfidenzintervalle) | Zu komplex für MVP-Scope | ❌ |

**Warum MAE als Hauptmetrik?**
-  ist in Sekunden — ein Fehler von 30s ist auch 30s Abweichung im Report. Das ist direkt kommunizierbar.
- Bei RMSE würde ein einzelner 300s-Ausreisser das Ergebnis stärker verzerren als bei MAE. Da Extremverspätungen (Schneetag, Megaevent) seltene aber echte Fälle sind, wollen wir die nicht wegdämpfen — aber sie sollen die Hauptmetrik nicht dominieren.
- MAPE und SMAPE fallen weg weil bei frühen Abfahrten (delay = −30s) oder pünktlichem Tram (delay = 0–5s) der prozentuale Fehler gegen unendlich geht.
- MBE wäre als Ergänzung interessant (zeigt ob das Modell systematisch zu optimistisch/pessimistisch schätzt) — kann bei Bedarf in der Evaluation ergänzt werden.

**Konkrete Erfolgsschwellen:**

| MAE auf Test-Set | Bewertung |
|:---|:---|
| > 45s | Schlechter als naive Baseline — Fehler suchen |
| 30–45s | Besser als Netzschnitt-Baseline, Luft nach oben |
| 20–30s | Modell lernt echte Muster |
| < 20s | Sehr gut — Overfitting prüfen |

## Vorgehen — Schritt für Schritt

### Tag 1 — Baseline + erstes Modell

**Schritt 1: Baseline definieren** (`06_prediction_1-baseline.ipynb`)
- Was ist die einfachste sinnvolle Vorhersage?
- Kandidaten: Netzschnitt immer (MAE ≈ 45s), Stunden-Mittelwert, Linien-Mittelwert
- Diese Baseline ist der Benchmark — das Modell muss besser sein

**Schritt 2: Feature-Set aufbauen** (`06_prediction_1-baseline.ipynb`)
- `departure_delay`, `delay_delta`, `trip_id`, Koordinaten raus
- Kategoriale Spalten für LightGBM markieren
- `arrival_delay` als Target definieren
- Kurze Sanity-Check: Verteilung Target im Train vs. Test identisch?

**Schritt 3: LightGBM trainieren** (`06_prediction_2-model.ipynb`)
- Erstes Training mit Default-Parametern
- MAE auf Validierungsset messen (z.B. letzter Monat von Train = Dez 2024)
- Vergleich mit Baseline: wie viel besser?

---

### Tag 2 — Evaluation + Insights

**Schritt 4: Evaluation auf Test-Set** (`06_prediction_3-evaluation.ipynb`)
- MAE gesamt + aufgeschlüsselt: pro Linie, pro Stadtkreis, pro Stunde
- Wo macht das Modell die größten Fehler? (Worst-Case-Haltestellen)
- Verhalten an Event-Tagen und bei Schnee

**Schritt 5: Feature Importance** (`06_prediction_3-evaluation.ipynb`)
- Welche Features zieht das Modell am stärksten heran?
- Stimmt das mit den EDA-Findings überein? (Sanity-Check)
- Welche Features bringen nichts → Kandidaten zum Entfernen

**Schritt 6: Modell exportieren** (`06_prediction_3-evaluation.ipynb`)
- Modell als `.pkl` oder `.txt` speichern → Basis für Dashboard

## Notebooks in dieser Phase

| Notebook | Inhalt |
|:---|:---|
| `06_prediction_0-overview` | Dieser Überblick — Ziel, Vorgehen, Entscheidungen |
| `06_prediction_1-baseline` | Feature-Set definieren · Baseline berechnen · Sanity-Checks |
| `06_prediction_2-model` | LightGBM Training · Validation · erste MAE |
| `06_prediction_3-evaluation` | Test-Set Evaluation · Feature Importance · Fehleranalyse · Export |

## Offene Entscheidungen

| Frage | Optionen | Wann entscheiden |
|:---|:---|:---|
| `stop_name` Encoding | LightGBM Native-Cat vs. Target-Encoding | Vor Training (Schritt 2) |
| `departure_delay` als Feature? | Nein (Datenleck) vs. als "Prior-Delay" wenn Vorgängerzug bekannt | Vor Training |
| Sampling für Training | Alle 55 Mio. vs. `gather_every(2)` für schnelleres Iteration | Beim ersten Training |
| Validation-Strategie | Letzter Monat Train (Dez 2024) vs. k-fold-zeitlich | Vor Training |
| Tuning-Aufwand | Default-Params reichen oft für 90% des Potenzials | Nach erstem MAE |

## Die Baseline — Startpunkt

**Eine Baseline ist der erste rohe Wurf — die dümmste sinnvolle Vorhersage.** Kein Training, kein Modell, nur Durchschnittswerte aus den Trainingsdaten. Jedes echte Modell das diese Zahl nicht schlägt ist nutzlos.

**Vier Baseline-Kandidaten (von simpel zu stark):**

| # | Baseline | Logik | Erwarteter MAE |
|:---|:---|:---|:---|
| 1 | **Grand Mean** | Immer 56s vorhersagen (Netzschnitt) | ~45s |
| 2 | **Stunden-Mittelwert** | 7h → 49s, 21h → 68s — je nach Uhrzeit | ~38s (Schätzung) |
| 3 | **Linien-Mittelwert** | L11 → 69s, L6 → 38s — je nach Linie | ~32s (Schätzung) |
| 4 | **Stop-Mittelwert** | Historischer Ø pro Haltestelle | ~25s (Schätzung) |

→ Der **Stop-Mittelwert** ist der härteste Gegner. Das LightGBM-Modell muss ihn schlagen — sonst hat es nichts gelernt was der Stop-Durchschnitt nicht schon weiß.

**Warum zuerst Baseline, dann Modell?**
- Ohne Baseline weiß man nicht ob MAE=32s gut oder schlecht ist
- Baseline schützt vor False Confidence: ein Modell das nur den Stunden-Durchschnitt lernt wirkt beeindruckend — ist aber keine echte Intelligenz
- Portfolio: zeigen dass man sauber vorgeht ist professioneller als blind ein Modell zu trainieren

## Was Erfolg bedeutet

| Schwelle | Interpretation |
|:---|:---|
| MAE > 45s | Schlechter als naive Baseline — etwas stimmt nicht |
| MAE 30–45s | Besser als Baseline, aber Luft nach oben |
| MAE 20–30s | Gutes Ergebnis — das Modell lernt echte Muster |
| MAE < 20s | Sehr gut — oder Overfitting prüfen |

**Wichtiger als der absolute MAE:** Versteht das Modell die Struktur?
- Macht es bei Schnee höhere Vorhersagen?
- Ist Linie 11 schlechter als Linie 6?
- Ist 21h schlechter als 7h?

Wenn ja → das Modell hat die EDA-Findings gelernt. Das ist das eigentliche Ziel.

## Ergebnisse — LightGBM v1

### Modell-Parameter

| Parameter | Wert |
|:---|:---|
| Modell | LightGBM v1 |
| Gespeichert | `data/models/lgbm_v1.txt` · `lgbm_v1_meta.json` |
| Features | 32 (siehe Datenbasis-Sektion) |
| Kategoriale Features | 5 (LightGBM Native-Categorical) |
| Train-Zeilen | 41.2 Mio. (2023–Jun 2024) |
| Validation-Zeilen | 14.3 Mio. (Jul–Dez 2024) |
| Beste Iteration | 481 (Early Stopping nach 50 Runden ohne Verbesserung) |
| `num_leaves` | 63 |
| `learning_rate` | 0.05 |
| `feature_fraction` | 0.8 |
| `bagging_fraction` | 0.8 · `bagging_freq` 5 |
| `min_child_samples` | 50 |

### Metriken

| Metrik | Baseline (Stop Mean) | LightGBM v1 | Gewinn |
|:---|---:|---:|---:|
| **MAE Test** | 50.0s | **46.3s** | **−3.7s** |
| **MAE Val** | — | 49.1s | — |
| RMSE Test | 86.2s | ~85s | — |
| OTP ±60s | 73.1% | 75.4% | +2.3 pp |
| MBE Test | — | +8.3s–+10.1s | — (systematisch zu optimistisch) |

### Fehleranalyse (Test-Set 2025)

**Nach Stunde** — schlechteste Stunden:

| Stunde | MAE |
|:---|:---|
| 17h | 54.4s |
| 16h | 53.9s |
| 18h | 52.4s |

**Nach Linie:**

| Linie | MAE | Linie | MAE |
|:---|:---|:---|:---|
| L11 | 52.5s (schlechteste) | L12 | 34.5s (beste) |
| L8 | 52.2s | L6 | 37.3s |
| L15 | 51.0s | L17 | 40.1s |

**Nach Wetter:**

| Bedingung | MAE |
|:---|:---|
| Schnee | 58.9s (n = 39.920) |
| Regen | 50.3s |
| Normal | 45.9s |

### Bekannte Schwächen

| Schwäche | Beschreibung | Verbesserung v2 |
|:---|:---|:---|
| MBE +8–10s | Modell unterschätzt systematisch — Extremverspätungen werden zu niedrig vorhergesagt | Target Encoding für `stop_name` statt Native-Cat |
| `stop_name` als Native-Cat | ~500 Stops grob gebündelt — Stop-spezifische Muster unvollständig gelernt | Target Encoding mit n-Threshold ≥ 1.000 |
| `prev_trip_delay` fehlt | Kaskadeneffekt nicht modelliert — ob die Vorgängerfahrt Verspätung hatte, ist ein starkes Signal | Trip-Kontinuität in Datensatz prüfen, dann als Feature |
| Schnee-Schwäche | MAE bei Schnee 13s höher als normal — seltene Extremlagen unterrepräsentiert im Training | Oversampling Schnee-Tage oder separate Schnee-Komponente |

### Live-Szenario

> Dienstag · 17:00 Uhr · Haltestelle Paradeplatz · Linie 11 · leichter Regen

**→ Vorhergesagter Delay: 48s**

Zum Vergleich: Netzschnitt 55s — Modell sagt Paradeplatz ist besser als Netzschnitt, was mit den EDA-Findings übereinstimmt (Paradeplatz 48.2s historisch).
