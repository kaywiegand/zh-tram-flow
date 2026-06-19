# Zahlenformat nach Sprache des Fließtextes

## Regel
Alle Zahlen, Metriken und Einheiten verwenden das Format der Sprache des umgebenden Textes.

### Format nach Sprache

| Sprache | Dezimal | Leerzeichen | Beispiele |
|:---|:---|:---|:---|
| **Deutsch** | Komma | JA (vor Einheit) | `18,56 s` · `29 M Zeilen` · `87 %` · `50,0 s` |
| **Englisch** | Punkt | NEIN | `18.56s` · `29M rows` · `87%` · `50.0s` |

### Anwendung nach Datei

| Datei | Sprache | Format |
|:---|:---|:---|
| `README.md` | Englisch | `18.56s`, `29M`, `87%`, `50.0s` |
| `ROADMAP.md` | Deutsch | `18,56 s`, `29 M`, `87 %`, `50,0 s` |
| `PROCESS_LOG.md` | Deutsch | `18,56 s`, `29 M`, `87 %`, `50,0 s` |
| `CLAUDE.md` | Deutsch | `18,56 s`, `29 M`, `87 %`, `50,0 s` |
| `BACKLOG.md` | Deutsch | `18,56 s`, `29 M`, `87 %`, `50,0 s` |
| `public/*.html` | Deutsch | `18,56 s`, `29 M`, `87 %`, `50,0 s` |
| `notebooks/*.ipynb` | GEMISCHT | Pro Markdown-Zelle: Sprache bestimmt Format |
| `src/**/*.py` | Code (Englisch) | `18.56s`, `29M`, `87%`, `50.0s` |
| `public/json/*.json` | Code (Englisch) | `18.56`, `29`, `87`, `50.0` |

### Beispiele für Konsistenz

**ENGLISCHER TEXT mit Zahlen:**
```
LightGBM v2: MAE 18.56s — 63% below the baseline.
The dataset has 94.4M rows across 3 years.
```

**DEUTSCHER TEXT mit Zahlen:**
```
LightGBM v2: MAE 18,56 s — 63 % unter der Baseline.
Der Datensatz hat 94,4 M Zeilen über 3 Jahre.
```

### Ausnahmen

1. **Code und Variablen** (Python, JSON) → immer Englisch (Punkt, kein Leerzeichen)
   ```python
   mae = 18.56  # nicht 18,56
   rows = 94.4  # nicht 94,4
   ```

2. **URLs, Links, externe Quellen** → unverändert übernehmen

3. **Zitierte Zahlenwerte aus Fremddaten** → Original-Format beibehalten

### Warum diese Regel

- **Professionell**: Zahlenformat folgt sprachlichen Konventionen (DIN 1355 Deutsch, IEEE Englisch)
- **Lesbar**: Keine kognitiven Brüche durch gemischte Formate
- **Konsistent**: Gleiche Sprache → immer gleiche Regel
- **Wartbar**: Einfach zu prüfen, ob Formate stimmen

### Überprüfung vor Commit

```bash
# Deutsch-Files: keine Punkte in Metriken (außer in URLs/Code)
grep -E " [0-9]+\.[0-9]+ (s|M|%|Zeilen)" *.md

# English-Files: keine Kommas in Metriken
grep -E " [0-9]+,[0-9]+ (s|M|%|rows)" *.md README.md
```

