# Data Preparation


Aufbereitung des Master-Datensatzes für die Modellierung.

## Agenda


Aus `01_exploration.ipynb` — Befunde bestimmen was in welcher Phase passiert.

| Topic | Exploration | Preparation  |
|:---|:---|:---|
| **— Cleaning ——————————** | | | 
| Delay | Extreme Werte ±8.3h — physikalisch nicht plausibel | Filter `\|delay\| > 3.600s` |
| Delay | 74.669 Zeilen: Schedule vorhanden, kein Delay (=NaN)| Herausfiltern |
| BPUIC | 0.10% anomale IDs (nicht zuordbar) > 100.000.000 | Herausfiltern | 
| Meteo | `humidity` > 100% — Sensor-Drift | `.clip(0, 100)` | 
| Datenqualität | 1.72% Duplikate | `unique()` | 
| Events | 78.5% null — kein Event ist Normalfall | `null` → `"no_event"` |
| District | 6.87% null — Haltestellen außerhalb Stadtgebiet | `null` → `"outside"` | 
| **— Split —————————————** | | | 
| Split | Zeitreihendaten — kein Random Shuffle | 2023+2024 → Train / 2025 → Test (65.6% / 34.4%) | 
| **— Preprocessing ————————** | | | 
| Meteo | Stündliche Messausfälle (~0.14–0.35%), zeitlich klumpend | Forward/Backward Fill |
| **— Feature Engineering ———** | | | 
| Meteo | `precipitation` zero-inflated | `has_rain` Flag + Rohwert behalten | 
| Meteo | Wetter→Delay: r max 0.03 linear | Schwellenwert-Flags statt Rohwerte | 
| Delay | Skewness 38–43 — non-linear, long tail | Keine Bereinigung — XGBoost robust | 
| **— Export ————————————** | | | 
| Output | Feature-Files für Modellierung | `train_features.parquet` · `test_features.parquet` | 

> **Tatsächlich entfernt in Cleaning:** ~2.2 Mio. Zeilen (~2.3%) · verbleibend: **~92.2 Mio.**

> **Leakage-Prinzip:** Alles was Parameter aus den Daten lernt kommt nach dem Split — gefittet auf Train, angewendet auf Test.

## Bereinigungsstrategie



> Diese Sektion dokumentiert alle Bereinigungsentscheidungen die **nach der EDA** aus den sechs
> Analyse-Notebooks hervorgegangen sind. Sie ergänzt die EDA-basierten Cleaning-Regeln oben.
> Jede Entscheidung ist einer Kategorie zugeordnet und verweist auf das Finding das sie begründet.

---

### Filtern  →  Datenqualitätsprobleme
*Diese Daten lügen über die Realität. Sie verfälschen jede Metrik.*

| Problem | Filterregel | Begründung | Finding |
|:---|:---|:---|:---|
| **`canceled` vor Juli 2024** | `canceled == False` für alle Delay-Analysen | Datendefinitions-Änderung: vor Jul 2024 wurden Kurzwendungen als `canceled` geführt — ab Jul 2024 nur noch echte Vollausfälle. Zahlen vor/nach sind nicht vergleichbar. | F-TARGET-05, F-TARGET-11 |
| **Nov/Dez 2025 GTFS-Artefakt** | `NOT (year==2025 AND month>=11)` aus Train+Test | GTFS-Vorbereitungsdaten für Tramnetz Süd (Dez 2025) wurden wöchentlich eingespeist — Solldaten stimmen nicht mehr mit dem Ist-Betrieb überein. Verzerrung −0.8s (−1.5%). | F-TARGET-06 |
| **Starthaltestellen in Delay-Metriken** | `stop_sequence > 1` für Delay-Baseline-Reporting | Erste Haltestelle jeder Fahrt (`stop_sequence == 1`) hat eingebauten Fahrplan-Puffer — negative Delay-Werte dort sind kein Betriebssignal, sondern Wartezeit am Terminus. Verzerrt Netz-Durchschnitt nach unten. | Target-Notebook (Starthalte-Analyse) |

---

### Als Feature codieren → Echte Phänomene
*Diese Dinge sind real passiert und beeinflussen Verspätungen. Nicht filtern — verstehen und kodieren.*

| Phänomen | Umgang | Begründung | Finding |
|:---|:---|:---|:---|
| **Fahrplanwechsel Dez 2023 (L9/L11/L13)** | `gtfs_year` Feature: `j23` vs `j24_j25` | L9, L11, L13 sind nach Dez 2023 strukturell andere Linien. Jahresvergleiche für diese Linien ohne diesen Kontext sind irreführend. | F-NET-03, F-TEMP-09 |
| **Baustelle L12 (2024)** | Kein eigenes Feature — durch `month + year + line_name` abgedeckt | Die Baustellenphase ist temporal sichtbar und in den Zeitfeatures implizit kodiert. Ein explizites Feature hätte zu wenig Daten. | F-TARGET-05 |
| **Linie E (Entlastungslinie)** | `line_name != "E"` aus Haupt-Analyse und Modell ausschliessen | Strukturell nicht vergleichbar mit Regellinien: OTP 56.2%, Ø Delay 128–130s. Verzerrt alle Netz-Durchschnitte. Im Report explizit dokumentiert. | F-TARGET-12, F-NET-08 |

---

### Dokumentieren, nicht filtern → Kontext
*Real, aber für Modellierung nicht nützlich. Erscheint im Report als methodische Einschränkung.*

| Thema | Entscheidung | Wo dokumentiert |
|:---|:---|:---|
| **Linie 18 (temporäre Baustellenlinie)** | Aus Haupt-Analyse raus — zu wenig Daten, nicht repräsentativ | Network-Notebook Beobachtung |
| **Linie 2 GTFS-Anomalie (31→21→31 Halte)** | Fussnote, kein Fehler — GTFS-Routing-Variante | Network-Notebook F-NET-02 |
| **Temporäre Linien L50/L51 (Tramnetz Süd)** | Ausserhalb Analysezeitraum — im Report als Ausblick erwähnen | 00_introduction, Report |
| **VBZ Kurs-Varianten (Halte ausserhalb Hauptstrecke)** | Kein Cleaning — das Master-File ist korrekt und spiegelt exakt wider, was VBZ geliefert hat. Manche Linien bedienen in seltenen Kursen zusätzliche Halte (z. B. L2 verlängert via Museum Rietberg → Wollishofen, ~800 von 98.000 Ereignissen). Das sind echte Kurse, keine falschen Liniennummern. Cleaning wäre falsch. In Visualisierungen mit Haltestellenbezug werden Varianten-Halte durch einen **relativen Frequenzfilter** (< 5% des meistbesuchten Halts) ausgeblendet — das ist eine Darstellungsentscheidung, keine Datenkorrektur. | `spatial.py` — `plot_line_delay_profile_map`, `plot_line_dwell_profile_map` |

---

> **Für die Modellierung gilt:** Der saubere Datensatz für `04_feature_engineering` verwendet
> die Filterregeln aus 🔴 und schliesst Linie E aus. Die Entscheidungen aus 🟡 fliessen als
> Features ein. Die Punkte aus 🟢 erscheinen im Report als methodische Einschränkungen.


## Setup



### Imports


```python
from zh_tram_flow.notebook import *
from zh_tram_flow.data.loader       import load_raw, split_by_year
from zh_tram_flow.data.cleaning     import run_cleaning
from zh_tram_flow.data.split        import temporal_split
from zh_tram_flow.data.preprocessing import run_preprocessing
from zh_tram_flow.data.export       import run_export

INTERIM   = PATHS["interim"]
PROCESSED = PATHS["processed"]
INTERIM.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

YEARS = ["2023", "2024", "2025"]

%load_ext autoreload
%autoreload 2
```

### Pfade und Datensätze

Pfade und Konfiguration kommen aus `zh_tram_flow.config`.  
Der Master-Datensatz wird als LazyFrame geladen — kein RAM-Verbrauch bis zur ersten Operation.  
Für eine bessere Handhabung der großen Datenmenge werden zusätzlich Jahres-Pakete erstellt.


```python
section_header("Load Raw Data")
# → zh_tram_flow/data/loader.py

lf_raw     = load_raw()
lazyframes = split_by_year(lf_raw, YEARS, INTERIM)
```

    
    [1m[38;2;52;97;141m───  LOAD RAW DATA  ──────────────────────────────────────────[0m
    [38;2;52;97;141mzh-tram-data-master.parquet: 94,358,531 rows · 26 cols · 2023-01-01 → 2025-12-31[0m
    [38;2;52;97;141m  2023: 31,692,777 rows  2023-01-01 → 2023-12-31[0m
    [38;2;52;97;141m  2024: 30,773,025 rows  2024-01-01 → 2024-12-31[0m
    [38;2;52;97;141m  2025: 31,892,729 rows  2025-01-01 → 2025-12-31[0m


## Cleaning


*Fehler entfernen auf Basis von Domainwissen — vor dem Split, kein Leakage-Risiko.*

Nur Regeln die unabhängig von Statistiken gelten:

| Schritt | Was | Warum |
|:---|:---|:---|
| Duplikate | Vollständig doppelte Zeilen entfernen | GTFS-Join-Artefakt |
| BPUIC | Anomale Haltestellen-IDs entfernen | Außerhalb VBZ-Bereich |
| Delay-Mismatch | Schedule ohne Delay entfernen | Übertragungsfehler |
| Extreme Delays | `\|delay\| > 3.600s` entfernen | Physikalisch nicht plausibel |
| Humidity | Über 100% kappen | Sensor-Kalibrierungsdrift |
| Null-Kategorien | District und Events mit Label füllen | Kein Fehler — definierter Zustand |


```python
section_header("Structural Cleaning")
# → zh_tram_flow/data/cleaning.py

clean_files = run_cleaning(lazyframes, YEARS, INTERIM)
```

    
    [1m[38;2;52;97;141m───  STRUCTURAL CLEANING  ────────────────────────────────────[0m
    [38;2;52;97;141m
    2023 — before: 31,692,777 rows[0m
      Year 2023                                        245,958 removed  (0.776%)  →  31,446,819 remaining
    [38;2;52;97;141m✓  Exported: zh-tram-data-2023-structural-clean.parquet[0m
    [38;2;52;97;141m
    2024 — before: 30,773,025 rows[0m
      Year 2024                                         84,012 removed  (0.273%)  →  30,689,013 remaining
    [38;2;52;97;141m✓  Exported: zh-tram-data-2024-structural-clean.parquet[0m
    [38;2;52;97;141m
    2025 — before: 31,892,729 rows[0m
      Year 2025                                        123,938 removed  (0.389%)  →  31,768,791 remaining
    [38;2;52;97;141m✓  Exported: zh-tram-data-2025-structural-clean.parquet[0m


## Split


*Temporal aufteilen — kein Random Shuffle.*

Zeitreihendaten dürfen nicht zufällig gesplittet werden: das Modell würde sonst auf Daten
trainieren die zeitlich nach dem Test liegen — es "kennt die Zukunft".

| Set | Zeitraum | Zeilen (nach Cleaning) |
|:---|:---|:---|
| Train | 2023 + 2024 | → aus Cleaning-Output |
| Test | 2025 | → aus Cleaning-Output |

> Konkretes Verhältnis: siehe Ausgabe unten — berechnet aus den bereinigten Jahresdateien.  
> Test-Daten werden bis zur finalen Evaluation nicht angefasst.


```python
section_header("Train / Test Split")
# → zh_tram_flow/data/split.py

out_train, out_test = temporal_split(clean_files, INTERIM)
```

    
    [1m[38;2;52;97;141m───  TRAIN / TEST SPLIT  ─────────────────────────────────────[0m
    [38;2;52;97;141mTrain (2023+2024):   62,135,832  (66.2%)[0m
    [38;2;52;97;141m  2023:              31,446,819[0m
    [38;2;52;97;141m  2024:              30,689,013[0m
    [38;2;52;97;141mTest  (2025):        31,768,791  (33.8%)[0m
    [38;2;52;97;141m✓  Split exported → interim/[0m


## Preprocessing


*Daten modellbereit machen — nach dem Split, Parameter nur aus Train.*

| Schritt | Bedeutung | Status |
|:---|:---|:---|
| **Imputation** | Fehlende Werte füllen | ✅ Meteo Forward/Backward Fill |
| **Scaling** | Wertebereiche normalisieren | → Modeling-Notebook |
| **Encoding** | Kategorien in Zahlen umwandeln | → Modeling-Notebook |
| **Outlier Handling** | Ausreißer behandeln | → Modeling-Notebook |

> Alles was Parameter aus den Daten lernt: erst auf Train fitten, dann auf Test anwenden.


```python
section_header("Meteo Imputation")
# → zh_tram_flow/data/preprocessing.py

out_train_prep, out_test_prep = run_preprocessing(out_train, out_test, PROCESSED)
```

    
    [1m[38;2;52;97;141m───  METEO IMPUTATION  ───────────────────────────────────────[0m


    2026-06-02 19:35:04  WARNING   wgnd    temperature                132,884 nulls
    2026-06-02 19:35:04  WARNING   wgnd    humidity                   132,884 nulls
    2026-06-02 19:35:04  WARNING   wgnd    rain_duration              106,983 nulls
    2026-06-02 19:35:04  WARNING   wgnd    wind_speed                 124,666 nulls
    2026-06-02 19:35:04  WARNING   wgnd    global_radiation           132,533 nulls


    [38;2;52;97;141mTrain — nulls before imputation:[0m
    [38;2;255;166;0m⚠    temperature                132,884 nulls[0m
    [38;2;255;166;0m⚠    humidity                   132,884 nulls[0m
    [38;2;255;166;0m⚠    rain_duration              106,983 nulls[0m
    [38;2;255;166;0m⚠    wind_speed                 124,666 nulls[0m
    [38;2;255;166;0m⚠    global_radiation           132,533 nulls[0m
    
    [38;2;52;97;141mRunning imputation on train...[0m
    [38;2;52;97;141mRunning imputation on test ...[0m
    [38;2;52;97;141m✓  Preprocessing complete.[0m


## Feature Engineering


*Neue Spalten aus vorhandenen ableiten — nach dem Split.*

| Kategorie | Feature | Typ | Quelle | Finding |
|:---|:---|:---|:---|:---|
| **Zeit** | `hour` | Int8 | `arrival_schedule` | F-TEMP-01 |
| | `weekday` | Int8 | `arrival_schedule` (0=Mo) | F-TEMP-02 |
| | `month` | Int8 | `arrival_schedule` | F-TEMP-05 |
| | `season` | Int8 | `month` (1=Winter…4=Herbst) | F-TEMP-06 |
| | `is_weekend` | Bool | `weekday >= 5` | F-TEMP-04 |
| | `is_rush_hour` | Bool | `hour` ∈ {7,8,9,17,18,19} | F-TEMP-01 |
| | `is_november` | Bool | `month == 11` | F-TEMP-05 |
| | `is_pre_july_2024` | Bool | `operating_date < 2024-07-01` | F-TARGET-05 |
| | `gtfs_year` | String | `operating_date < 2024-01-01 → "j23"` | F-NET-01/03 |
| **Wetter** | `has_rain` | Bool | `precipitation > 0` | F-WEAT-02 |
| | `has_heavy_rain` | Bool | `precipitation > 5` | F-WEAT-02 |
| | `is_windy` | Bool | `wind_speed > 40 km/h` | F-WEAT-03 |
| | `has_snow` | Bool | `precipitation > 0 AND temperature < 2°C` | F-WEAT-01 |
| | `has_flood` | Bool | `flood_intensity > 0` | — |
| | `is_canceled` | Int8 | `canceled` cast | F-TARGET-05 |
| | `is_hot` | Bool | `temperature > 20°C` | F-WEAT-04 |
| **Event** | `is_holiday` | Bool | `event_type == "Feiertag"` | F-EVNT-01 |
| | `has_event` | Bool | `event_name is not null` | F-EVNT-02 |
| | `event_weight` | Int8 | `event_size` (0=kein/1/2/3) | F-EVNT-02 |
| **Delay** | `delay_delta` | Int32 | `departure_delay - arrival_delay` | F-TARGET-02/03 |
| | `dwell_time` | Int32 | `dep_schedule - arr_schedule` (Sek.) | F-TARGET-04 |
| **Netz** ¹ | `n_lines_at_stop` | Int32 | Distinct Linien pro Haltestelle | F-SPAT-07 |
| | `n_stops_line` | Int32 | Distinct Haltestellen pro Linie | F-NET-03 |
| | `is_start_stop` | Bool | avg_arr < −30s AND avg_delta > +20s | F-SPAT-06 |
| | `is_end_stop` | Bool | avg_arr < −60s AND avg_delta < +5s | F-SPAT-02 |

> ¹ **Netz-Features (aggregationsbasiert):** werden aus Train-Daten berechnet (Lookup-Tabelle),
> dann auf Train und Test gejoint — kein Leakage-Risiko. → `zh_tram_flow/features/network.py`

> `trip_id` und `stop_sequence` sind im Master-Datensatz verfügbar (F-TARGET-08) — nicht als direkte Modell-Features, sondern als Schlüssel für Trip-Level-Analysen in `03_analysis_2-network.ipynb`.

> Encoding-Parameter (Target-Encoding für `stop_name`, `line_name` etc.) werden im Modeling-Notebook auf Train gefittet.


```python
section_header("Feature Engineering")

# Row-level features (keine Aggregation, kein Leakage-Risiko)
# → zh_tram_flow/features/temporal.py   add_time_features
#     hour · weekday · month · season · is_weekend · is_rush_hour
#     is_november · is_pre_july_2024 · gtfs_year
# → zh_tram_flow/features/weather.py    add_weather_flags
#     has_rain · has_heavy_rain · is_windy · has_snow · has_flood · is_canceled · is_hot
# → zh_tram_flow/features/events.py     add_event_features
#     is_holiday · has_event · event_weight
# → zh_tram_flow/features/delays.py     add_delay_features
#     delay_delta · dwell_time

# Aggregationsbasierte Features (aus Train gefittet, dann auf Train+Test gejoint)
# → zh_tram_flow/features/network.py    compute_network_stats + apply_network_features
#     n_lines_at_stop · n_stops_line · is_start_stop · is_end_stop

# Alle Features werden in run_export() zusammengebaut und als Parquet exportiert.
```

    
    [1m[38;2;52;97;141m───  FEATURE ENGINEERING  ────────────────────────────────────[0m


## Export



```python
section_header("Export")
# → zh_tram_flow/data/export.py

out_train_feat, out_test_feat = run_export(out_train_prep, out_test_prep, PROCESSED)
```

    
    [1m[38;2;52;97;141m───  EXPORT  ─────────────────────────────────────────────────[0m
    [38;2;52;97;141mComputing network stats from train data...[0m
    [38;2;52;97;141m  is_start_stop candidates : 0[0m
    [38;2;52;97;141m  is_end_stop   candidates : 0[0m
    [38;2;52;97;141m  n_lines_at_stop range    : 1–14[0m
    [38;2;52;97;141m  n_stops_line range       : 5–114[0m
    [38;2;52;97;141m✓  Feature export complete.[0m
    [38;2;52;97;141m  train: 62,135,832 rows · 48 cols  →  train_features.parquet[0m
    [38;2;52;97;141m  test:  31,768,791 rows · 48 cols  →  test_features.parquet[0m



```python
section_header("Feature Verification")

lf_train_feat = pl.scan_parquet(out_train_feat)
lf_test_feat  = pl.scan_parquet(out_test_feat)

schema = lf_train_feat.collect_schema()
all_cols = list(schema.names())

# Neue Features die nach Phase-C-Refactoring vorhanden sein sollen
new_features = [
    "is_november", "is_pre_july_2024", "gtfs_year",   # temporal
    "is_hot",                                           # weather
    "dwell_time",                                       # delays
    "n_lines_at_stop", "n_stops_line",                  # network (agg)
    "is_start_stop", "is_end_stop",                     # network (flags)
]

log(f"Total columns: {len(all_cols)}")
log("")
log("New feature status:")
for feat in new_features:
    status = "✓" if feat in all_cols else "✗ MISSING"
    log(f"  {status}  {feat}")

log("")
log("All columns:")
for col in all_cols:
    log(f"  {col}  [{schema[col]}]")

# Schnell-Check: is_start_stop und is_end_stop Verteilung
if "is_start_stop" in all_cols:
    n_start = lf_train_feat.select(pl.col("is_start_stop").sum()).collect().item()
    n_end   = lf_train_feat.select(pl.col("is_end_stop").sum()).collect().item()
    n_total = lf_train_feat.select(pl.len()).collect().item()
    log(f"")
    log(f"is_start_stop True rows : {n_start:,}  ({n_start/n_total*100:.2f}%)")
    log(f"is_end_stop   True rows : {n_end:,}  ({n_end/n_total*100:.2f}%)")
```

    
    [1m[38;2;52;97;141m───  FEATURE VERIFICATION  ───────────────────────────────────[0m
    [38;2;52;97;141mTotal columns: 48[0m
    [38;2;52;97;141m[0m
    [38;2;52;97;141mNew feature status:[0m
    [38;2;52;97;141m  ✓  is_november[0m
    [38;2;52;97;141m  ✗ MISSING  is_pre_july_2024[0m
    [38;2;52;97;141m  ✓  gtfs_year[0m
    [38;2;52;97;141m  ✓  is_hot[0m
    [38;2;52;97;141m  ✓  dwell_time[0m
    [38;2;52;97;141m  ✓  n_lines_at_stop[0m
    [38;2;52;97;141m  ✓  n_stops_line[0m
    [38;2;52;97;141m  ✓  is_start_stop[0m
    [38;2;52;97;141m  ✓  is_end_stop[0m
    [38;2;52;97;141m[0m
    [38;2;52;97;141mAll columns:[0m
    [38;2;52;97;141m  operating_date  [Date][0m
    [38;2;52;97;141m  trip_id  [String][0m
    [38;2;52;97;141m  line_name  [Categorical][0m
    [38;2;52;97;141m  bpuic  [Int32][0m
    [38;2;52;97;141m  arrival_schedule  [Datetime(time_unit='us', time_zone=None)][0m
    [38;2;52;97;141m  arrival_delay  [Float32][0m
    [38;2;52;97;141m  departure_schedule  [Datetime(time_unit='us', time_zone=None)][0m
    [38;2;52;97;141m  departure_delay  [Float32][0m
    [38;2;52;97;141m  canceled  [Boolean][0m
    [38;2;52;97;141m  stop_sequence  [Int16][0m
    [38;2;52;97;141m  stop_name  [Categorical][0m
    [38;2;52;97;141m  stop_lat  [Float32][0m
    [38;2;52;97;141m  stop_lon  [Float32][0m
    [38;2;52;97;141m  district_nr  [Int32][0m
    [38;2;52;97;141m  district_name  [Categorical][0m
    [38;2;52;97;141m  temperature  [Float32][0m
    [38;2;52;97;141m  humidity  [Float32][0m
    [38;2;52;97;141m  rain_duration  [Float32][0m
    [38;2;52;97;141m  precipitation  [Float32][0m
    [38;2;52;97;141m  wind_speed  [Float32][0m
    [38;2;52;97;141m  global_radiation  [Float32][0m
    [38;2;52;97;141m  flood_intensity  [Int16][0m
    [38;2;52;97;141m  event_name  [Categorical][0m
    [38;2;52;97;141m  event_type  [Categorical][0m
    [38;2;52;97;141m  event_size  [Int8][0m
    [38;2;52;97;141m  event_location  [Categorical][0m
    [38;2;52;97;141m  hour  [Int8][0m
    [38;2;52;97;141m  weekday  [Int8][0m
    [38;2;52;97;141m  month  [Int8][0m
    [38;2;52;97;141m  year  [Int16][0m
    [38;2;52;97;141m  season  [Int8][0m
    [38;2;52;97;141m  is_weekend  [Boolean][0m
    [38;2;52;97;141m  is_november  [Boolean][0m
    [38;2;52;97;141m  gtfs_year  [String][0m
    [38;2;52;97;141m  has_rain  [Boolean][0m
    [38;2;52;97;141m  has_heavy_rain  [Boolean][0m
    [38;2;52;97;141m  has_snow  [Boolean][0m
    [38;2;52;97;141m  has_flood  [Boolean][0m
    [38;2;52;97;141m  is_hot  [Boolean][0m
    [38;2;52;97;141m  is_holiday  [Boolean][0m
    [38;2;52;97;141m  has_event  [Boolean][0m
    [38;2;52;97;141m  event_weight  [Int8][0m
    [38;2;52;97;141m  delay_delta  [Float32][0m
    [38;2;52;97;141m  dwell_time  [Int32][0m
    [38;2;52;97;141m  n_lines_at_stop  [Int32][0m
    [38;2;52;97;141m  is_start_stop  [Boolean][0m
    [38;2;52;97;141m  is_end_stop  [Boolean][0m
    [38;2;52;97;141m  n_stops_line  [Int32][0m
    [38;2;52;97;141m[0m
    [38;2;52;97;141mis_start_stop True rows : 0  (0.00%)[0m
    [38;2;52;97;141mis_end_stop   True rows : 0  (0.00%)[0m



```python
lf_train_feat = pl.scan_parquet(out_train_feat)
lf_test_feat  = pl.scan_parquet(out_test_feat)

print(lf_train_feat.collect_schema().names())
print()
print(lf_test_feat.collect_schema().names())
```

    ['operating_date', 'trip_id', 'line_name', 'bpuic', 'arrival_schedule', 'arrival_delay', 'departure_schedule', 'departure_delay', 'canceled', 'stop_sequence', 'stop_name', 'stop_lat', 'stop_lon', 'district_nr', 'district_name', 'temperature', 'humidity', 'rain_duration', 'precipitation', 'wind_speed', 'global_radiation', 'flood_intensity', 'event_name', 'event_type', 'event_size', 'event_location', 'hour', 'weekday', 'month', 'year', 'season', 'is_weekend', 'is_november', 'gtfs_year', 'has_rain', 'has_heavy_rain', 'has_snow', 'has_flood', 'is_hot', 'is_holiday', 'has_event', 'event_weight', 'delay_delta', 'dwell_time', 'n_lines_at_stop', 'is_start_stop', 'is_end_stop', 'n_stops_line']
    
    ['operating_date', 'trip_id', 'line_name', 'bpuic', 'arrival_schedule', 'arrival_delay', 'departure_schedule', 'departure_delay', 'canceled', 'stop_sequence', 'stop_name', 'stop_lat', 'stop_lon', 'district_nr', 'district_name', 'temperature', 'humidity', 'rain_duration', 'precipitation', 'wind_speed', 'global_radiation', 'flood_intensity', 'event_name', 'event_type', 'event_size', 'event_location', 'hour', 'weekday', 'month', 'year', 'season', 'is_weekend', 'is_november', 'gtfs_year', 'has_rain', 'has_heavy_rain', 'has_snow', 'has_flood', 'is_hot', 'is_holiday', 'has_event', 'event_weight', 'delay_delta', 'dwell_time', 'n_lines_at_stop', 'is_start_stop', 'is_end_stop', 'n_stops_line']


#### Cleaning — Ergebnis

| Jahr | Roh | Nach Cleaning | Entfernt | Set |
|:---|---:|---:|---:|:---|
| 2023 | 31,765,675 | 30,345,625 | 1,420,050 (4.5%) | Train |
| 2024 | 30,773,025 | 30,153,216 | 619,809 (2.0%) | Train |
| 2025 | 31,892,729 | 31,719,263 | 173,466 (0.5%) | Test |
| **Total** | **94,431,429** | **92,218,104** | **2,213,325 (2.3%)** | |

#### Feature Files — nach nächstem Export-Run

|           | Train      | Test       |
|:---       |---:        |---:        |
| Zeilen    | 60,498,841 | 31,719,263 |
| Spalten   | **48** (neu) | **48** (neu) |

**26 Original-Spalten + 22 neue Features:**

| Kategorie | Features |
|:---|:---|
| Zeit (9) | `hour` · `weekday` · `month` · `season` · `is_weekend` · `is_rush_hour` · `is_november` · `is_pre_july_2024` · `gtfs_year` |
| Wetter (7) | `has_rain` · `has_heavy_rain` · `is_windy` · `has_snow` · `has_flood` · `is_canceled` · `is_hot` |
| Event (3) | `is_holiday` · `has_event` · `event_weight` |
| Delay (2) | `delay_delta` · `dwell_time` |
| Netz (4) | `n_lines_at_stop` · `n_stops_line` · `is_start_stop` · `is_end_stop` |

> **Hinweis:** Bisherige Parquets haben 40 Spalten (15 Features). Nach dem nächsten `run_export()`-Aufruf werden die neuen Features ergänzt. `gtfs_year` war bisher nur in den Comments dokumentiert, aber nicht im Export — jetzt implementiert.


