# Feature Engineering

Finales Feature-Set für die Modellierung — basierend auf den Erkenntnissen der Analyse-Phase.

**Input:** `train_prepared.parquet` · `test_prepared.parquet`
**Output:** `train_final.parquet` · `test_final.parquet`

## Agenda




### Filter (vor Feature Engineering)

| Filter | Bedingung | Grund |
|:---|:---|:---|
| Canceled | `canceled == False` | Datendefinitions-Artefakt Jul 2024 (F-TARGET-05) |
| Starthalte | `stop_sequence > 1` | Eingebauter Puffer verfälscht Delay-Metriken (F-SPAT-06) |
| Linie E | `line_name != "E"` | Strukturell nicht vergleichbar — OTP 56%, Ø 130s (F-NET-08) |
| Nov/Dez 2025 | Nur Test-Set | GTFS-Artefakt Fahrplanwechsel j25→j26 (F-TARGET-06) |

### Features raus

| Feature | Grund |
|:---|:---|
| `is_rush_hour` | Morgenrush existiert nicht im Signal — 7h unter Netz-Ø (F-TEMP-01) |
| `is_windy` | NaN überall, nie befüllt (F-WEAT-03) |
| `is_canceled` | Nach Filter redundant |
| `global_radiation` | Kein Finding, kein Signal |
| `humidity` | Kein Finding, kein Signal |
| `rain_duration` | Redundant mit `precipitation` |
| `district_name` | Redundant mit `district_nr` |

### Features neu

| Feature | Formel | Finding |
|:---|:---|:---|
| `year` | `operating_date.year` | Aufwärtstrend real (F-TEMP-07) |
| `event_weight_x_hour` | `event_weight × hour` | Event-Effekt primär abends 18–22h (F-EVNT-03) |
| `is_late_night_weekend` | `is_weekend & hour ∈ [0–3]` | Partyverkehr Fr/Sa (F-TEMP-10) |
| `n_lines_at_stop` | Network Stats (train only) | Liniendichte pro Haltestelle (F-SPAT-07) |
| `n_stops_line` | Network Stats (train only) | Linienlänge als Peripheral-Proxy (F-SPAT-09) |
| `is_start_stop` | Network Stats (train only) | Starthalte-Flag für Modell (F-SPAT-06) |
| `is_end_stop` | Network Stats (train only) | Terminus-Flag für Modell (F-SPAT-02) |

## Setup


```python
from zh_tram_flow.notebook import *
from zh_tram_flow.config import PATHS
import zh_tram_flow.features.final as fe
from zh_tram_flow.features.network import compute_network_stats

%load_ext autoreload
%autoreload 2

TRAIN_PREP  = PATHS["processed"] / "train_prepared.parquet"
TEST_PREP   = PATHS["processed"] / "test_prepared.parquet"
TRAIN_FINAL = PATHS["processed"] / "train_final.parquet"
TEST_FINAL  = PATHS["processed"] / "test_final.parquet"
```

## Feature Engineering


```python
section_header("Feature Engineering")

lf_train_prep = pl.scan_parquet(TRAIN_PREP)
lf_test_prep  = pl.scan_parquet(TEST_PREP)

# Filter
lf_train = fe.apply_lf_clean(lf_train_prep)
lf_test  = fe.apply_lf_clean(lf_test_prep)

# Network stats aus Train berechnen (kein Leakage)
network_stats = compute_network_stats(lf_train)

# Features bauen + Spalten bereinigen
lf_train_feat = fe.select_final_columns(fe.build_features(lf_train, network_stats))
lf_test_feat  = fe.select_final_columns(fe.build_features(lf_test,  network_stats))

n_train = lf_train_feat.select(pl.len()).collect().item()
n_test  = lf_test_feat.select(pl.len()).collect().item()
n_feat  = len(lf_train_feat.collect_schema().names())
log(f"Train: {n_train:,} Zeilen · {n_feat} Features")
log(f"Test:  {n_test:,} Zeilen · {n_feat} Features")
```

    
    [1m[38;2;52;97;141m───  FEATURE ENGINEERING  ────────────────────────────────────[0m
    [38;2;52;97;141mTrain: 55,484,578 Zeilen · 40 Features[0m
    [38;2;52;97;141mTest:  29,941,876 Zeilen · 40 Features[0m


## Export für Modellierung


```python
section_header("Export")

lf_train_feat.sink_parquet(TRAIN_FINAL)
lf_test_feat.sink_parquet(TEST_FINAL)

log(f"Exportiert: {TRAIN_FINAL.name}")
log(f"Exportiert: {TEST_FINAL.name}")
```

    
    [1m[38;2;52;97;141m───  EXPORT  ─────────────────────────────────────────────────[0m
    [38;2;52;97;141mExportiert: train_final.parquet[0m
    [38;2;52;97;141mExportiert: test_final.parquet[0m



```python

```
