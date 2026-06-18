# Direction ID Architecture Overhaul — Complete Implementation Plan

**Status:** DEFERRED (aktuell nicht-critical) | **Last Updated:** 2026-06-18  
**Trigger:** Observation beim Dashboard-Test: L11 zeigt ~10s Unterschied zwischen Richtung A/B  
**Decision Point:** Siehe OP-1 in BACKLOG.md — erst systematisch analysieren ob Unterschiede signifikant genug sind  

---

## Executive Summary

Aktuell hat das System nur einen **oberflächlichen Fahrtrichtungs-Filter** im Dashboard (Regler mit A/B/Gesamt), aber die zugrundeliegenden Daten (`test_final.parquet`) unterscheiden nicht zwischen den Richtungen. Das führt dazu dass die Filterung keine Datenmäßigen Unterschiede zeigt — nur UI-Unterschiede.

**Dieser Plan** beschreibt einen vollständigen Umbau der Daten-Pipeline um echte Richtungs-Dimension einzuführen:
- train_raw + test_final mit `direction_id` anreichern (via GTFS join)
- Alle Aggregationen neu: `stop × direction`, `line × direction`
- Modell v3 Retraining mit `direction_id` Feature
- Neue Analysen: Asymmetrische Verspätung, richtungsspezifische Hotspots, etc.

**Aufwand:** ~2 Wochen (9 Sessions à 60min)  
**Risiko:** MITTEL (größere Pipeline-Änderung, aber viele kleinere Schritte)  
**Benefit:** Echte Multi-Dimensionalität im System, authentische Richtungs-Analysen  

---

## PHASE 1: CRITICAL PATH — Blocker für alles andere

**Zeitaufwand:** 4–5 Sessions | **Risiko:** Mittel | **Data Dependency:** Hoch

### 1.1 Direction ID in die Raw-Daten einführen

**Ziel:** Jede Zeile in `train_raw` + `test_raw` bekommt `direction_id` (0 oder 1)

**Wie:**
1. **GTFS Lookup aufbauen:** `trip_id` → `direction_id` Mapping aus `gtfs_tram_trips.parquet`
2. **Join:** `train_raw.trip_id` LEFT JOIN `gtfs_trips.trip_id` → extrahiere `direction_id`
3. **Handling:** NULLs dokumentieren (sollten < 0.5% sein)
4. **Output:** Neue Dateien `train_raw_with_direction.parquet`, `test_raw_with_direction.parquet`

**Dateien zu ändern:**
- `/notebooks/02_preparation.ipynb` — neue Sektion "Add Direction ID" nach temporal_split()
- `/src/zh_tram_flow/data/loader.py` — neue Funktion für Trip-ID zu Direction-ID Mapping

**Validation:**
```python
assert direction_df["direction_id"].isin([0, 1]).all()  # Nur 0 oder 1
assert direction_df["direction_id"].notna().sum() / len(direction_df) > 0.995  # < 0.5% NULLs
assert len(direction_df) == len(raw_original)  # Zeilen unverändert
```

---

### 1.2 Direction ID durch Feature-Engineering Pipeline tragen

**Ziel:** Alle aggregierten Features nutzen `direction_id` als zusätzliche Dimension

**Wie:**
1. **`compute_network_stats()`** anpassen: Group-by ändert sich
   ```
   Bisherig: .group_by(["stop_name", "line_name"])
   Neu:      .group_by(["stop_name", "line_name", "direction_id"])
   ```

2. **Join-Keys anpassen:** Statt nur `[stop_name]` nutzen `[stop_name, direction_id]`

3. **Beobachte:** Neue NULLs entstehen? (Z.B. manche Stops nur in einer Richtung)

**Dateien zu ändern:**
- `/src/zh_tram_flow/features/network.py` — `compute_network_stats()` + `apply_network_features()`
- `/src/zh_tram_flow/data/export.py` — `run_export()` Parameter

**Output:** 
- `train_features.parquet` (39 → 40 Spalten: +`direction_id`)
- `test_features.parquet` (identisch)

---

### 1.3 Train/Test Split neu aggregieren

**Ziel:** Komplette Re-Aggregation mit neuer Direction-Dimension

**Wie:**
1. Nach 1.1 + 1.2: Beide Raw-Files durch gesamten Cleaning & Preprocessing laufen
2. `run_export()` aufrufen (updated durch 1.2)
3. Neue Features-Parquets speichern

**Dateien zu ändern:**
- `/notebooks/02_preparation.ipynb` — Zellen nach Direction-ID hinzufügen

**Testen:** Zeilen-Count unverändert? Schema stimmt?

---

### 1.4 Test/Analysis-Daten neu erzeugen

**Ziel:** `train_final.parquet` + `test_final.parquet` mit `direction_id`

**Wie:**
1. Aggregationen aus 1.3 laden
2. Features wie bisher engineered
3. `test_final.parquet` speichern (39 → 40 Spalten)

**Dateien zu ändern:**
- `/notebooks/05_feature_engineering.ipynb` + `/06_prediction_*.ipynb`

**Output:** 
- `train_final.parquet` (mit direction_id)
- `test_final.parquet` (mit direction_id)

---

## PHASE 2: HIGH IMPACT — Dashboard & Modell

**Zeitaufwand:** 2–3 Sessions | **Risiko:** Niedrig

### 2.1 Dashboard Aggregationen neu schreiben

**Ziel:** Neue parquet-Dateien für richtungs-stratifizierte Analysen

**Neue Aggregationen:**
```
stop_direction_agg.parquet
  Dimensionen: stop_name, direction_id
  Spalten: mean_delay, p90_delay, otp_pct, n_obs
  → 2× so viele Zeilen wie stop_agg

line_direction_agg.parquet
  Dimensionen: line_name, direction_id
  Spalten: mean_delay, p90_delay, otp_pct, n_obs
  → 2× so viele Zeilen wie line_agg

route_profile_with_direction.parquet
  (ersetzt/ergänzt route_profile_by_direction.parquet)
```

**Dateien zu ändern:**
- `/apps/dashboard/precompute.py` — neue Aggregations-Blöcke

---

### 2.2 Dashboard UI — Richtungs-Filter perfektionieren

**Ziel:** Streamlit UI nutzt echte Richtungs-Unterschiede

**Was funktioniert jetzt schon:**
- Selectbox mit Gesamt/Richtung A/B Labels
- Map + Chart + Stats filtern nach Auswahl

**Was wird besser:**
- Filter zeigt echte Datenunterschiede (nicht nur UI-Unterschiede)
- Vergleich Hinfahrt vs. Rückfahrt ist aussagekräftig

**Dateien zu ändern:**
- `/apps/dashboard/app.py` — Regler nutzt die neuen `line_direction_agg` Daten

---

### 2.3 Model v3 — Retraining mit Direction Feature

**Ziel:** LightGBM Modell mit `direction_id` als zusätzliches Feature

**Wie:**
1. `train_final.parquet` mit direction_id laden
2. Feature-Set: v2 (34 Features) + `direction_id` (1 Feature) = 35 Features
3. LightGBM trainieren (gleiche Hyperparameter wie v2)
4. Neue Metrics: Test MAE v3 vs. v2 vergleichen
5. Feature Importance prüfen: ist direction_id Top-10?

**Dateien zu ändern:**
- `/notebooks/06_prediction_4-model_v2.ipynb` → neu: `06_prediction_4a-model_v3.ipynb`

**Output:** 
- `lgbm_v3.pkl` (trainiertes Modell)
- Updated Model Progression Tabelle (v1 → v2 → v3)

---

## PHASE 3: NICE-TO-HAVE — Analysen & Visualisierungen

**Zeitaufwand:** 3–4 Sessions | **Risiko:** Niedrig

### 3.1 Analyse-Notebook: Direction-spezifische Hotspots

**Neu:** `/notebooks/03_analysis_8-direction.ipynb`

**Inhalte:**
1. **Frage 1:** Sind Hotspots richtungsspezifisch?
   - Top-10 Delays pro Richtung (Tabellen)
   - Kartenvisualisierung: Hotspots mit Richtungs-Pfeilen

2. **Frage 2:** Kaskaden pro Richtung?
   - `prev_trip_delay` Correlation: Dir 0 vs. 1
   - Unterschiedliche Propagation-Muster?

3. **Frage 3:** Wetter-Effekt richtungsspezifisch?
   - Schnee-Delay pro Richtung + Höhenlage

4. **Frage 4:** Linienlänge × Richtung Effekt?
   - Lange Linien: asymmetrischer?

**Output:** 4–5 neue Charts + 10–15 Findings (F-DIR-01–F-DIR-N)

---

### 3.2 Neue Dashboard-Seite: "Direction Insights"

**Neue Seite im Streamlit** mit:
1. **Heatmap:** Line × Direction × Delay
2. **Asymmetrie-Ranking:** Welche Linien sind am schieflastend?
3. **Empfehlungen:** "Linie 9 Richtung 1 braucht Maßnahmen"

---

### 3.3 Report aktualisieren

**Updates in `/public/index.html`:**
- Neue Sektion: "Direction Asymmetry Analysis"
- 2–3 Key Charts eingebettet
- Links zu Direction-Insights-Seite im Dashboard

---

## PHASE 4: Dokumentation

**Zeitaufwand:** 1–2 Sessions

### 4.1 DATA_DICTIONARY.md
```
direction_id | Int64
  GTFS Direction ID (0=Outbound, 1=Return)
  Source: gtfs_tram_trips.parquet join via trip_id
  Range: {0, 1}
  Nulls: < 0.5% (acceptable, dokumentiert)
  Interpretation: Pro Linie unterschiedliche semantische Bedeutung
                  (z.B. L11 Dir 0 = Süd→Nord, Dir 1 = Nord→Süd)
```

### 4.2 BACKLOG.md / ROADMAP.md Update
- Task #67 von "in progress" → "completed"
- Task #68 Status klären

### 4.3 README + CLAUDE.md
```
## Direction Dimension

Das Zürcher Netz ist bidirektional. Jede Linie fährt zwei Richtungen,
oft mit unterschiedlichen Mustern. GTFS bietet direction_id;
wir nutzen diese für richtungs-spezifische Analysen.

Dashboard: Selectbox "Fahrtrichtung" → filtert alle Visualisierungen
Modell: direction_id ist ein Feature (v3 retraining)
Analyse: OP-1, OP-3, OP-7 in BACKLOG adressieren Richtungs-Phänomene
```

---

## Implementation Sequence

| Day | Phase | Tasks | Commitments |
|:---|:---|:---|:---|
| 1–2 | 1.1–1.2 | Raw-Daten enrichen, Cleanup-Tests | train_raw_with_direction.parquet ✅ |
| 3 | 1.3–1.4 | Pipeline re-aggregieren | train_final + test_final mit direction_id ✅ |
| 4–5 | 2.1–2.2 | Dashboard + UI | precompute.py updated, UI live ✅ |
| 6 | 2.3 | Model v3 training | lgbm_v3.pkl + eval metrics ✅ |
| 7–8 | 3.1–3.2 | Analyse-Notebooks + Insights-Seite | 03_analysis_8.ipynb + neuer Tab ✅ |
| 9 | 4.0 | Doku + Final Review | BACKLOG/README/CLAUDE updated ✅ |

---

## Risk Assessment

| Risiko | Szenario | Mitigation |
|:---|:---|:---|
| **Trip-ID Join Mismatch** | Nicht alle IST-trip_ids in GTFS | Sample-Join vorab testen; 0.5%-Threshold akzeptieren; fehlende als direction_id=null |
| **Aggregations-Explosion** | Stop × Direction → 2× Zeilen | Ist beabsichtigt; Memory-Check durchführen |
| **Modell-Regression** | v3 schlechter als v2 | v2 behalten, v3 optional; Feature-Importance dokumentieren |
| **Dashboard-Performance** | Streaming langsam mit 2 Richtungen | Precomputes klein, sollte schnell sein |

---

## Success Criteria

**Phase 1 ✅:**
- [ ] train_raw.parquet + test_raw.parquet haben direction_id (< 0.5% NULLs)
- [ ] test_final.parquet 40 Spalten (39 + direction_id)
- [ ] Zeilen-Count konsistent über alle Stages

**Phase 2 ✅:**
- [ ] Dashboard lädt mit Richtungs-Filter
- [ ] Model v3 trainiert; MAE vs. v2 dokumentiert
- [ ] Stop × Direction Hotspots sichtbar

**Phase 3 ✅:**
- [ ] Analyse-Notebook mit 5+ Findings
- [ ] Direction-Insights-Seite verfügbar
- [ ] Report aktualisiert

---

## Decision Tree: Soll ich das jetzt machen?

**Ja, wenn:**
- [ ] OP-1 Analyse zeigt: Direction-Unterschiede sind **systematisch + signifikant** (>5% OTP-Gap, >15s Delay-Delta)
- [ ] Mehrere Linien zeigen Asymmetrie (nicht nur L11)
- [ ] Time-Budget: 2 Wochen verfügbar

**Nein, wenn:**
- [ ] Direction-Unterschiede sind **Noise** (< 5% der Varianz erklären)
- [ ] Nur einzelne Linien betroffen
- [ ] Andere Priorities höher

**Später entscheiden:**
- Nach OP-1 Dashboard-Analyse durchführen
- Ergebnisse in PROCESS_LOG dokumentieren
- Dann Freigabe für Phase 1

---

## Critical Files

- `src/zh_tram_flow/data/loader.py` — Trip-ID Mapping
- `notebooks/02_preparation.ipynb` — Direction-ID Aggregation
- `src/zh_tram_flow/features/network.py` — Composite-Key Aggregation
- `apps/dashboard/precompute.py` — Richtungs-stratifizierte Aggregationen
- `apps/dashboard/app.py` — Streamlit UI

---

**Letzte Aktualisierung:** 2026-06-18  
**Generieret von:** Claude Agent (Plan-Mode)  
**Status:** Dokumentiert, bereit zur Evaluierung nach OP-1 Dashboard-Analyse
