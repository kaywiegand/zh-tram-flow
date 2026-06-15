# Data Dictionary — Zürich Tram Flow

**File:** `data/raw/zh-tram-data-master.parquet`
**Rows:** ~94.4M · **Columns:** 26 · **Period:** 2023–2025
**Source:** [`sf_data-research`](https://github.com/kaywiegand/sf_data-research)

---

## IST Data (Real-Time Operations)

| # | Column | Type | Description |
| :-- | :-- | :-- | :-- |
| 1 | `operating_date` | `Date` | Operating day |
| 2 | `line_name` | `Categorical` | Tram line number (e.g. `"11"`) |
| 3 | `bpuic` | `Int32` | Stop ID — join key to GTFS |
| 4 | `arrival_schedule` | `Datetime` | Scheduled arrival time |
| 5 | `arrival_delay` | `Float32` | Arrival delay in **seconds** (negative = early) · **target variable** |
| 6 | `departure_schedule` | `Datetime` | Scheduled departure time |
| 7 | `departure_delay` | `Float32` | Departure delay in **seconds** |
| 8 | `canceled` | `Boolean` | Trip cancellation = `True` — source: `FAELLT_AUS_TF` |
| 9 | `trip_id` | `Categorical` | GTFS trip ID — key for trip-level analysis (cascades, hotspots) |
| 10 | `stop_sequence` | `Int32` | Stop position within trip (1 = first stop) |

> ⚠️ **`canceled` — Provider definition change:** Cancellation rate is elevated network-wide from Jan 2023 to Jun 2024, normalising simultaneously across all lines in July 2024. Likely cause: opentransportdata.swiss set `FAELLT_AUS_TF` for partial cancellations (short-turns) until Jun 2024 — from Jul 2024 onward for full cancellations only.
> **Model consequence:** `canceled = True` rows excluded from delay regression; `is_pre_july_2024` available as feature for a separate cancellation model. → Finding F-TARGET-05

---

## GTFS (Schedule & Geodata)

| # | Column | Type | Description |
| :-- | :-- | :-- | :-- |
| 11 | `stop_name` | `Categorical` | Stop name (e.g. `"Paradeplatz"`) |
| 12 | `stop_lat` | `Float32` | Latitude (WGS84) |
| 13 | `stop_lon` | `Float32` | Longitude (WGS84) |
| 14 | `district_nr` | `Int8` | City district 1–12 (`null` = outside city boundary) |
| 15 | `district_name` | `Categorical` | District name (e.g. `"Kreis 1"`) |

---

## Weather Data (Meteo)

Joined hourly from three Zürich measurement stations. All values represent the hour of the scheduled arrival.

| # | Column | Type | Description |
| :-- | :-- | :-- | :-- |
| 16 | `temperature` | `Float32` | Temperature in °C |
| 17 | `humidity` | `Float32` | Relative humidity in % |
| 18 | `rain_duration` | `Float32` | Rain duration in min/h |
| 19 | `precipitation` | `Float32` | Precipitation in mm |
| 20 | `wind_speed` | `Float32` | Wind speed in km/h |
| 21 | `global_radiation` | `Float32` | Global radiation in W/m² |
| 22 | `flood_intensity` | `Int16` | Flood indicator (ERZ reports) |

> ⚠️ `is_windy` (derived feature) is always `NaN` — excluded from all models.
> ⚠️ Nov–Dec 2025 departure delay is masked due to a provider infrastructure issue — arrival delay is unaffected.

---

## Event Data

| # | Column | Type | Description |
| :-- | :-- | :-- | :-- |
| 23 | `event_name` | `Categorical` | Event name (`null` = no event on this day) |
| 24 | `event_type` | `Categorical` | Category: `Feiertag`, `Stadtfest`, `Konzert`, `Messe`, `Fussball` |
| 25 | `event_size` | `Int8` | Weight: `1` = medium (>1k), `2` = large (10k–30k), `3` = very large (>30k) |
| 26 | `event_location` | `Categorical` | Venue (`null` = no event) |

---

## Join Strategy

| Join | Key | Type |
| :--- | :--- | :--- |
| IST + GTFS Stops | `bpuic` = `bpuic` | Left Join |
| IST + Meteo | `floor(arrival_schedule, '1h')` = `date_time` | Left Join |
| IST + Events | `date(operating_date)` = `Datum` | Left Join |

> **Left Join everywhere:** every tram stop event is retained. Missing values (stops outside city boundary, hours without weather data) appear as `null`.

---

## Engineered Features (ML Dataset)

The ML-ready dataset (`data/processed/train_final_v2.parquet`, `test_final_v2.parquet`) contains 36 features derived from the master dataset. Key additions:

| Feature | Source | Notes |
| :--- | :--- | :--- |
| `prev_trip_delay` | `arrival_delay` (previous run) | Cascade indicator — strongest new feature in v2 · Finding F-NET-07 |
| `stop_sequence_pct` | `stop_sequence` / max stops | Relative position along route (0–1) |
| `hour` | `arrival_schedule` | Hour of day (0–23) |
| `day_of_week` | `arrival_schedule` | Weekday (0=Mon, 6=Sun) |
| `month` | `operating_date` | Month (1–12) |
| `has_snow` | `precipitation` + `temperature` | Binary snow indicator |
| `is_rush_hour` | `hour` | Morning (7–9h) or evening (17–19h) |
| `dwell_time` | `departure_schedule` − `arrival_schedule` | Planned dwell time in seconds |

Full feature list and encoding decisions: [`05_feature_engineering.ipynb`](../notebooks/05_feature_engineering.ipynb)
