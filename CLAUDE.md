# CLAUDE.md – Zürich Tram Flow

> Projektspezifische Anweisungen für Claude Code.
> Ergänzt die globale CLAUDE.md aus dem wgnd-workspace.

---

## Projekt

| Feld | Inhalt |
| :--- | :--- |
| Slug | `zh-tram-flow` |
| Paket | `zh_tram_flow` (Import mit Underscores) |
| Typ | DANSC (EDA + Modellierung + Dashboard) |
| Stack | Polars · Pandas · GeoPandas · Plotly · Folium · Jupyter |

## Kontext-Einstieg

1. `PROCESS_LOG.md` lesen — aktueller Projektstand und letzte Session
2. `ROADMAP.md` lesen — offene Phasen und Tasks
3. Globale `CLAUDE.md` aus `/Users/kaywiegand/Workspace/` gilt weiterhin

## Datenbasis

Die gesamte Data-Engineering-Phase ist **abgeschlossen** und liegt in:
- Repo: [`sf_data-research`](https://github.com/kaywiegand/sf_data-research) — vollständig dokumentiert
- PROCESS_LOG.md dort lesen für Details zu Entscheidungen, Filtern, Pipeline

**Lokale Dateien in diesem Repo:**

| Datei | Beschreibung |
| :--- | :--- |
| `data/raw/zh-tram-data-master.parquet` | Master-Datensatz: ~88 Mio. Zeilen, 24 Spalten (IST + GTFS + Meteo + Events) |
| `data/raw/gtfs/` | GTFS-Referenztabellen: Haltestellen, Routen, Shapes, Trips (9 Parquets) |

**Wichtig:** `data/raw/` ist schreibgeschützt — Rohdaten nie verändern.
Transformationen → `data/interim/`, finale Daten → `data/processed/`.

## Python-Paket

```python
from zh_tram_flow.config import PATHS      # Pfade
from zh_tram_flow.settings import setup_plotting, logger
```

Paketname hat **Underscores** (`zh_tram_flow`), nicht Bindestriche.
Ordner: `src/zh_tram_flow/`

## Projektspezifische Hinweise

- Polars ist die primäre DataFrame-Bibliothek (94 Mio. Zeilen — Pandas wäre zu langsam)
- Für große Operationen `pl.scan_parquet()` (lazy) bevorzugen
- GTFS-Referenzjahr: 2024 — Spatial Join bereits im Master-Datensatz enthalten
- `canceled = True` Zeilen behalten — sind wichtige Extremfälle für das Modell
- Meteo-Join-Schlüssel: `floor(arrival_schedule, '1h')` = stündliche Granularität

## Notebook-Konventionen

- Jedes Notebook startet mit einer Markdown-Zelle: Zweck, Input, Output
- Polars-Lernmomente explizit kommentieren — dieses Projekt ist auch Lernprojekt
- Outputs (Charts, exportierte Daten) immer in `reports/` oder `data/processed/`
