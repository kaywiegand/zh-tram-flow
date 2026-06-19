# Portfolio Pipeline — Dokumentation

> **Single Source of Truth für alle Portfolio-Artefakte**
>
> Diese Dokumentation erklärt die mechanisierte Portfolio-Pipeline:
> wie sie funktioniert, wie man sie nutzt, und wie man Probleme behebt.
>
> **Status:** 🟢 Operativ seit 2026-06-19
> **Erstellt:** 2026-06-19 von Claude Haiku 4.5

---

## Überblick

Die **Portfolio-Pipeline** ist ein mechanisierter Prozess, der aus einer einzigen Markdown-Datei (`portfolio.md`)
automatisch alle Portfolio-Artefakte generiert:

```
portfolio.md (Einzige Quelle)
    ↓
generate_json_from_portfolio.py
    ↓
public/json/storyline-*.json (4 Views: overview, storyview, techview, socialview)
    ↓
generate_html_from_json.py  +  convert_json_to_md.py
    ↓
public/*.html (4 Präsentationen)  +  public/md/*.md (4 Markdown-Exports)
```

**Warum das wichtig ist:**
- 🎯 **Keine manuellen Syncs** mehr zwischen JSON, HTML und MD
- 📝 **Zentrale Quelle** — alle Änderungen gehen über portfolio.md
- 🔄 **Reproduzierbar** — beliebig oft regenerierbar
- ✅ **Wartbar** — ein File statt vier

---

## Architektur

### 1. Single Source of Truth: `public/md/portfolio.md`

Die **einzige Datei die Sie editieren**.

**Struktur:**
```markdown
# Portfolio Summary — Zurich Tram Flow

## Project
name:       Zurich Tram Flow
slug:       zh-tram-flow
type:       DANSC
...

## Storyline
thesis:     [Die Kernthese]
hook:       [Das Hook/Überraschungs-Statement]
proof:      [4-Schritt-Beweiskette]
so_what:    [Was folgt daraus]

## Problem
kpi_name:   OTP — On-Time Performance
kpi_ist:    87
kpi_soll:   95 %
kpi_gap:    −8 %
problem_statement: |
  [Das Problem ausführlich erklärt]

## Key Findings
### F1 — [Titel]
finding:    [Was wurde gefunden]
number:     [Die Zahl]
source:     [Notebook-Referenz]

### F2 — ...
...

## Model Results
algorithm:  [Algorithmus]
target:     [Target Variable]
metric:     [Metrik]

### Baseline Benchmark
| Model | Logic | Metric |
|:---|:---|:---|
| ...

### Model Progression
| Model | Features | Test MAE | vs. Baseline |
|:---|:---|:---|:---|
| ...

## Recommendations
r1:
  title:    [Titel]
  detail:   [Detaillierte Begründung]

r2: ...

## Research Opportunities
<!-- VIEWS: storyview, techview -->

[Nennung + Beispiele]

## Figures
```yaml
spatial:
  - ../img/...
temporal:
  - ../img/...
```

## Status
generated_by:    /portfolio story
generated_at:    [Datum]
summary_version: [Version]
```

**Konventionen:**
- **Deutsches Zahlenformat:** `18,56 s`, `87 %`, `r ≥ 0,85` (Komma, Leerzeichen vor Einheit)
- **Keine Typos:** Die Datei wird maschinell geparst
- **Quellen als Kommentare:** `<!-- Extracted from Notebook X -->` (optional)
- **View-Marker:** `<!-- VIEWS: overview, storyview, techview -->` (für Research Opportunities)

---

### 2. Build-Scripts

#### `scripts/generate_json_from_portfolio.py`

**Input:** `public/md/portfolio.md`  
**Output:** `public/json/storyline-{overview,storyview,techview,socialview}.json`

**Was es tut:**
1. Liest portfolio.md
2. Lädt JSON-Templates aus `public/json-backup/` (Referenz-Struktur)
3. Extrahiert Findings, Recommendations, Research Opportunities
4. Befüllt die Templates mit portfolio.md-Inhalten
5. Schreibt 4 neue JSON-Files

**Ausführung:**
```bash
python3 scripts/generate_json_from_portfolio.py
```

**Output:**
```
📖 Read portfolio.md (11518 chars)

📝 Processing overview (Storyline A)...
  → Loaded template: public/json-backup/storyline-overview.json
  → Updated content from portfolio.md
✅ Wrote: public/json/storyline-overview.json

... (weitere 3 Views)

✅ JSON generation complete!
```

---

#### `scripts/generate_html_from_json.py`

**Input:** `public/json/storyline-*.json`  
**Output:** `public/{overview,storyview,techview,socialview}.html`

**Was es tut:**
1. Lädt jede JSON-Datei
2. Rendert sie als Reveal.js Präsentation
3. Nutzt `/Users/kaywiegand/Workspace/docs/portfolio/templates/slides-template.html`
4. Schreibt 4 HTML-Dateien

**Ausführung:**
```bash
python3 scripts/generate_html_from_json.py
```

**Output:**
```
Loading template...
✅ Loaded template: /Users/.../slides-template.html

📊 Generating overview...
  → Loaded JSON
  → Built HTML presentation
✅ Wrote: public/overview.html

... (weitere 3 Views)

✅ HTML generation complete!
```

---

#### `scripts/convert_json_to_md.py` (existierend)

**Input:** `public/json/storyline-*.json`  
**Output:** `public/md/{overview,storyview,techview,socialview}.md`

**Was es tut:**
1. Konvertiert JSON-Strukturen zu Markdown
2. Schreibt 4 Markdown-Dateien
3. Kann für Gamma-Import oder andere Markdown-Tools genutzt werden

**Ausführung:**
```bash
python3 scripts/convert_json_to_md.py
```

---

### 3. Backup-Verzeichnisse (Validierung)

- **`public/json-backup/`** — Originale JSON-Templates (Referenz)
- **`public/html-backup/`** — Original HTML-Dateien (visueller Vergleich)

Diese Directories werden **nicht committed** (in `.gitignore`).  
Sie dienen nur der Validierung während der Migration.

---

## Workflow: So benutzt man es

### Standardfall: Änderungen vornehmen

**1. Bearbeite `portfolio.md`**
```bash
vim public/md/portfolio.md
```

Änderungen:
- Zahlen updaten (MAE, OTP, etc.)
- Findings aktualisieren
- Neue Erkenntnisse hinzufügen
- Research Opportunities erweitern

**2. Führe die Pipeline aus**

**Option A: Komplette Pipeline (empfohlen)**
```bash
/project-case full
```

Das tut:
1. ✅ portfolio.md validieren
2. ✅ `generate_json_from_portfolio.py` ausführen
3. ✅ `generate_html_from_json.py` ausführen
4. ✅ `convert_json_to_md.py` ausführen
5. ✅ Git-Commit erstellen
6. ✅ PROCESS_LOG.md updaten

**Option B: Einzelne Schritte**

Nur JSONs regenerieren:
```bash
/project-case json
```

Nur HTMLs + MDs regenerieren:
```bash
/project-case report
```

**3. Validieren**

Die neuen Artefakte werden in `public/` geschrieben:
```bash
ls -la public/json/           # 4 JSON-Files
ls -la public/*.html          # 4 HTML-Präsentationen
ls -la public/md/*.md         # 4 Markdown-Files
```

**4. Committen (wenn nicht automatisch)**

```bash
git add public/json public/*.html public/md
git commit -m "feat: updated portfolio artifacts

- portfolio.md: updated [was geändert]
- Artefakte regeneriert aus pipeline

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

---

## Validierungs-Checkliste

Nach jeder Änderung diese Punkte checken:

- [ ] **portfolio.md**
  - [ ] Alle Zahlen mit korrektem Format? (`18,56 s`, `87 %`, etc.)
  - [ ] Keine Typos in Struktur (headings, sections)?
  - [ ] Quellen-Kommentare vorhanden (optional)?

- [ ] **JSON-Files**
  - [ ] Alle 4 Files vorhanden? (`overview`, `storyview`, `techview`, `socialview`)
  - [ ] Größen ok? (27–32 KB je nach View)
  - [ ] Meta-Daten vorhanden? (extracted findings, recommendations)

- [ ] **HTML-Files**
  - [ ] Alle 4 HTML-Dateien vorhanden?
  - [ ] Im Browser öffbar? (keine Fehler in Console)
  - [ ] Navigation funktioniert? (Links zwischen Slides)

- [ ] **Markdown-Files**
  - [ ] Alle 4 MD-Files vorhanden?
  - [ ] Formatierung ok? (keine broken Markdown)
  - [ ] Zusammenhang zu Originalen korrekt?

- [ ] **index.html**
  - [ ] Landing Page aktualisiert? (neue KPIs, Beschreibung)
  - [ ] Links zu 4 Views funktionieren?
  - [ ] Responsive am Handy?

---

## Troubleshooting

### Problem: Scripts funktionieren nicht

**Fehler: `ModuleNotFoundError: No module named 'json'`**

→ Python 3 nutzen:
```bash
python3 scripts/generate_json_from_portfolio.py
```

---

### Problem: JSON Generation fehlgeschlagen

**Fehler: `FileNotFoundError: JSON template not found`**

→ Backups müssen existieren:
```bash
ls public/json-backup/
# Sollte zeigen: storyline-overview.json, storyline-storyview.json, ...
```

Wenn nicht vorhanden:
```bash
cp public/json/*.json public/json-backup/
```

---

### Problem: HTML sieht merkwürdig aus

**Symptoms:** Keine Styles, broken Layout, leere Seiten

→ Template-Pfad prüfen:
```bash
ls /Users/kaywiegand/Workspace/docs/portfolio/templates/slides-template.html
# Muss existieren
```

Falls nicht: Fallback-Template wird genutzt (basic Reveal.js).

---

### Problem: Zahlenformat nicht konsistent

**Beispiel:** `18.6s` statt `18,56 s`

→ portfolio.md checken:
```bash
grep -n "\.[0-9].*s" public/md/portfolio.md
```

Sollte zeigen: KEINE Treffer (alle Dezimal-Kommata verwenden).

Korrektur:
```bash
# Manuelle Suche-Replace in portfolio.md
18.56 s  → 18,56 s
87%      → 87 %
```

---

### Problem: Scripts laufen langsam

**Symptom:** `generate_json_from_portfolio.py` dauert > 10 Sekunden

→ Normal für große portfolios. Wenn extrem (>60s):
```bash
# Portfolio-Größe checken
wc -l public/md/portfolio.md
# Sollte < 500 Zeilen sein
```

---

## Häufig gestellte Fragen

### F: Kann ich die HTMLs manuell editieren?

**A:** Nicht empfohlen! Sie werden beim nächsten `/project-case full` überschrieben.

Besser: Änderungen in `portfolio.md` machen → Pipeline regeneriert alles.

---

### F: Wo speichert die Pipeline Metadaten?

**A:** Im `_extracted` Feld in den JSON-Files:
```bash
cat public/json/storyline-overview.json | jq ._extracted
```

Das enthält alle extrahierten Findings, Recommendations, etc. (dokumentativ).

---

### F: Kann ich neue Views hinzufügen?

**A:** Ja! Workflow:

1. Neues JSON-Template erstellen: `public/json/storyline-myview.json`
2. `generate_json_from_portfolio.py` updaten (neue View in Loop hinzufügen)
3. HTML-Template anpassen
4. `/project-case full` ausführen

---

### F: Woher kommen die KPI-Zahlen im index.html?

**A:** Manuell in `public/index.html` eingetragen (nicht aus pipeline).

Wenn Zahlen ändern → `index.html` direkt editieren oder `/project-case full` neu ausführen.

---

## Backup & Recovery

### Backups wiederherstellen

Falls etwas schiefgeht, Backups benutzen:

```bash
# JSON-Backups wiederherstellen
cp public/json-backup/* public/json/

# HTML-Backups wiederherstellen
cp public/html-backup/* public/
```

**Wichtig:** Git-History bleibt erhalten:
```bash
git log --oneline public/json/storyline-overview.json
# Zeigt alle vorherigen Versionen
```

---

## Deployment

### GitHub Pages (automatisch)

Die `public/` Ordner wird automatisch zu GitHub Pages deployed:

```
main branch
    ↓
public/ Ordner
    ↓
GitHub Pages
    ↓
https://kaywiegand.github.io/zh-tram-flow/
```

**Nach einem Commit:**
```bash
git push origin main
# → GitHub Actions deployed automatisch
# → index.html ist live unter https://...
```

---

## Technische Details

### Parsing von portfolio.md

Das `generate_json_from_portfolio.py` Script nutzt **Regex-Pattern** um portfolio.md zu parsen:

```python
# Beispiel: Findings extrahieren
pattern = r"### F(\d+) — (.+?)\n```\nfinding:\s*(.+?)\n..."
```

**Wichtig:** Das Format in portfolio.md muss exakt sein:
- Überschriften mit `###`
- Code-Blöcke mit ` ``` `
- Konsistente Indentation

---

### JSON-Struktur

Jede JSON-Datei folgt dieser Struktur:

```json
{
  "meta": {
    "storyline": "A",          // "A", "B", "C", oder "D"
    "presentation_title": "...",
    "audience": "...",
    "duration_minutes": 10,
    ...
  },
  "chapters": [
    {
      "nav_label": "Einstieg",
      "slides": [
        {
          "role": "title",      // oder "standard"
          "title": "...",
          "subtitle": "...",
          "content": [
            {
              "type": "figures",  // oder "agenda", "sections", etc.
              "items": [...]
            }
          ]
        }
      ]
    }
  ],
  "_extracted": {
    "findings": [...],          // Dokumentativ
    "recommendations": [...],
    "updated_at": "2026-06-19"
  }
}
```

---

## Erweiterungen (Zukunft)

Mögliche Verbesserungen:

- [ ] **Automatische Validierung** — CI/CD prüft portfolio.md Format
- [ ] **Spell-Check** — deutsche Rechtschreibung validieren
- [ ] **Zahlen-Validierung** — Zahlen müssen aus Notebooks stammen
- [ ] **PDF-Export** — Portfolio auch als PDF
- [ ] **Analytics** — Track welche View am meisten gelesen wird
- [ ] **Versionierung** — Archive aller portfolio-Versionen

---

## Support & Kontakt

**Bei Problemen:**

1. **Lokale Tests:** Scripts manuell ausführen und Output checken
2. **Git-History:** `git log public/` zeigt was geändert wurde
3. **Backups:** `public/json-backup/` und `public/html-backup/` als Referenz
4. **Documentation:** Dieses File und CLAUDE.md

---

## Changelog

### 2026-06-19 — Initial Release

- ✅ portfolio.md als Single Source of Truth etabliert
- ✅ generate_json_from_portfolio.py geschrieben
- ✅ generate_html_from_json.py geschrieben
- ✅ convert_json_to_md.py verifiziert
- ✅ index.html (Landing Page) erstellt
- ✅ Komplette Dokumentation geschrieben
- ✅ Pipeline mit `/project-case full` integriert

**Status:** 🟢 Production Ready

---

**Generated with ❤️ by Claude Haiku 4.5**  
**Workspace:** `/Users/kaywiegand/Workspace/zh-tram-flow/`
