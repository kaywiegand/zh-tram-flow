# Migration Checklist — portfolio.md als Single Source of Truth

**Datum:** 2026-06-19  
**Ziel:** portfolio.md zu einer vollständigen, mechansisierten Quell-Datei machen

---

## Phase 1: Backup & Vorbereitung ✅

- [x] public/json-backup/ erstellt (Referenz-Snapshot der aktuellen JSONs)
- [x] public/html-backup/ erstellt (Referenz-Snapshot der aktuellen HTMLs)
- [x] MIGRATION_CHECKLIST.md erstellt

---

## Phase 2: portfolio.md erweitern ✅

### Structure Check ✅
- [ ] Alle Kapitel-Titel (nav_labels) aus allen 4 JSONs in portfolio.md dokumentiert?
  - Overview: Einstieg, Ausgangssituation, Überraschungen, Erkenntnis, Das Modell, Empfehlungen, Resultat, Projektrahmen, Ende
  - StoryView: Einstieg, Ausgangssituation, Data Engineering, Exploration, Erkenntnis, Machine Learning, Empfehlungen, Projektrahmen, Weitere Potenziale, Abbinder
  - TechView: Einstieg, Ausgangssituation, Datenstrategie, Baseline, Feature Engineering, Modellauswahl, Evaluation, Empfehlungen, Weitere Potenziale, Abbinder
  - SocialView: Einstieg, Ausgangssituation, Drei Kernbefunde, Die Datenbasis, Vier Empfehlungen, Technologie & Robustheit, Abschluss

### Content Check ✅
- [x] **Key Findings (F1–F6)** mit Zahlen + Quellen vorhanden? ✅
  - F1: 71,3 % dwell_time = 0s
  - F2: 0 Overlap Top-Dichte × Top-Delay
  - F3: Peak 21h (+11,7 s), Donnerstag schlechtester Tag (60,4 s)
  - F4: Schnee +54s, Regen +23,3 s
  - F5: Feiertage −9,9 s, Fachmessen 66,0 s
  - F6: Pearson r ≥ 0,85 auf allen 16 Linien

- [x] **Recommendations (R1–R4)** mit Details vorhanden? ✅
  - R1: Fahrplan-Redesign L11
  - R2: Real-Time Dispatch
  - R3: Kapazitätsmanagement 20–22h
  - R4: OTP-Monitoring nach Stadtkreis

- [x] **Research Opportunities** — mindestens Nennung + OP-1 Beispiel? ✅
  - [x] Statement: "Dashboard-Exploration offenbarte weitere Erkenntnismöglichkeiten" ✅
  - [x] OP-1 erwähnt: Direction-Asymmetrie (~10s Delta) ✅
  - [x] Link zu BACKLOG.md#research-opportunities ✅

### Format Check ✅
- [x] **Deutsches Zahlenformat korrekt?** ✅
  - Dezimaltrennzeichen: Komma → `18,56 s`, `71,5 %`, `r ≥ 0,85`
  - Leerzeichen vor Einheit → `87 %`, `94,4 M`, `18,56 s`
  - Kein `pp` → immer `%`

- [x] **Quellen-Kommentare vorhanden?** (optional, in Phase 3) ✅
  - Format: `<!-- Extracted from storyline-overview.json, chapter "Ausgangssituation" -->`

- [x] **View-Marker integriert?** (Opportunities in storyview/techview) ✅
  - Format: `<!-- VIEWS: overview, storyview, techview -->`
  - Zeigt an welche Presentations-Views diesen Content nutzen

### Data Accuracy Check ✅
- [x] MAE Werte korrekt? ✅
  - Stop Mean Baseline: 50,0 s
  - LightGBM v1: 45,7 s MAE, +8,3 s MBE
  - LightGBM v2: 18,56 s MAE, −0,69 s MBE

- [x] Datensatz-Größen korrekt? ✅
  - Master: 94,4 M Zeilen ✅
  - lf_clean: ~85 M Zeilen ✅
  - Train / Val / Test: 41,2 M / 14,3 M / ~29 M ✅

- [x] Feature-Counts korrekt? ✅
  - v1: 34 Features ✅
  - v2: 36 Features (+prev_trip_delay, +stop_sequence_pct) ✅

- [x] OTP-Wert korrekt? ✅
  - netzweit: 87 % ✅
  - Ziel: 95 % ✅
  - Gap: −8 % ✅

**✅ PHASE 1 COMPLETE:** portfolio.md ist erweitert, Research Opportunities dokumentiert, Status aktualisiert

---

## Phase 3: Build-Scripts schreiben

- [ ] `scripts/generate_json_from_portfolio.py` erstellt
  - Input: public/mds/portfolio.md
  - Output: public/json/storyline-{overview,storyview,techview,socialview}.json
  - Logik: VIEW-Marker parsen → pro View JSON generieren

- [ ] `scripts/generate_html_from_json.py` erstellt
  - Input: public/json/storyline-*.json
  - Output: public/{overview,storyview,techview,socialview}.html
  - Template: /Workspace/docs/portfolio/templates/slides-template.html

- [ ] `scripts/convert_json_to_md.py` verifiziert
  - Test: Funktioniert mit neu generierten JSONs?

---

## Phase 4: Testing & Validation

### Backup-Vergleich
- [ ] Neue JSONs vs. json-backup/:
  - Checksummen verglichen? (sollten identisch sein oder nur Whitespace-Diffs)
  - Critical fields (nav_labels, KPIs) geprüft?

- [ ] Neue HTMLs vs. html-backup/:
  - Visuell im Browser verglichen (overview, storyview, techview, socialview)?
  - Opportunities-Sektion in storyview.html und techview.html vorhanden?

- [ ] Neue MDs:
  - convert_json_to_md.py produziert 4 neue MD-Files?
  - Inhalte identisch mit Backups?

### Struktur-Validierung
- [ ] JSON-Schema validieren
  - meta.storyline: "A", "B", "C", "D"
  - chapters: Array mit nav_label
  - slides: Array mit title, subtitle, content
  - content[].type: figures, agenda, sections, statement, etc.

- [ ] HTML validieren
  - reveal.js-Struktur vorhanden (section mit nested sections)?
  - Alle figure-References existieren?
  - CSS loaded, keine Fehler in Browser Console?

- [ ] MD validieren
  - Alle 4 Files vorhanden (overview, storyview, techview, socialview)?
  - Keine leeren Sections?

---

## Phase 5: project-case Skill aktualisieren

- [ ] `skills/project-case/project-case.md` angepasst:
  - Mode `json`: Neu dokumentiert
  - Mode `report`: Neu dokumentiert
  - Mode `full`: Workflow aktualisiert

- [ ] CLAUDE.md (zh-tram-flow) aktualisiert:
  - Build-Pipeline dokumentiert
  - Script-Verwendung erklärt

- [ ] PROCESS_LOG.md (zh-tram-flow) aktualisiert:
  - Session-Eintrag: "Portfolio-Pipeline mechanisiert"
  - Pointer auf Backups

---

## Phase 6: Git & Commit

- [ ] .gitignore aktualisiert:
  - `public/json-backup/` hinzugefügt
  - `public/html-backup/` hinzugefügt

- [ ] Scripts committet:
  ```bash
  git add scripts/generate_json_from_portfolio.py scripts/generate_html_from_json.py
  git commit -m "feat: mechanized portfolio pipeline (JSON + HTML generation)"
  ```

- [ ] Dokumentation committet:
  ```bash
  git add skills/project-case/project-case.md CLAUDE.md PROCESS_LOG.md
  git commit -m "docs: portfolio pipeline documentation + modes"
  ```

- [ ] Artefakte committet:
  ```bash
  git add public/mds/portfolio.md public/json/ public/*.html
  git commit -m "feat: generated portfolio artifacts from new pipeline"
  ```

---

## Success Criteria ✅

- [x] Backups erstellt
- [ ] portfolio.md erweitert (12–15 KB, 400–500 Zeilen)
- [ ] generate_json_from_portfolio.py funktioniert
- [ ] generate_html_from_json.py funktioniert
- [ ] Neue Artefakte identisch zu Backups (oder minimal Diffs)
- [ ] project-case Skill dokumentiert
- [ ] Alles committed

---

## Notes

- Backups bleiben in Repo bis zum End of Phase 5
- Nach erfolgreicher Validierung können Backups gelöscht werden
- research Opportunities: Minimal in portfolio.md (Nennung + OP-1 Beispiel), detailliert in BACKLOG.md
- View-Marker in HTML-Kommentaren (Best Practice, lesbar in Markdown)
