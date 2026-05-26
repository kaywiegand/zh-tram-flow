# Portfolio Checklist
### Quality-Check — zh-tram-flow

**Datum Check:** 2026-05-26
**Status vor Check:** Analyse ✅ · Feature Engineering ✅ · LightGBM v1 trainiert · Evaluation 🔄 Skeleton
**Reviewer:** Kay + Claude

Legende: ✅ erfüllt · B = vorhanden, unvollständig · A = fehlt komplett · C = kleine Anpassung · ? = nicht geprüft

---

## Dimension 1 — Story

- [C] Projektziel in maximal 3 Sätzen formuliert
  → README "Kurzbeschreibung" vorhanden, eher 4 Sätze, könnten schärfer sein. Kein Single Punch-Line-Satz.
- [B] Headline-Ergebnis vorhanden (eine Zahl, ein Befund)
  → MAE 45.7s vs. Baseline 50.0s steht im README, aber eingebettet in Phase-Liste — kein prominentes Heading.
- [B] Relevanz klar: Warum interessant für jemanden außerhalb?
  → README Abschnitt 2–4 erklärt es gut. Per Präsentations-Feedback: Impact ist vorhanden aber nicht sichtbar gemacht. Versteckte Insights (Peripherie-Hotspots, Fachmesse > Taylor Swift) kommen nicht als Punch.
- [✅] Use Case / Anwendungskontext definiert
  → Section 10 "Business Cases & KPIs" — drei Zielgruppen, konkrete KPIs.
- [✅] Wichtige Entscheidungen begründet
  → PROCESS_LOG sehr detailliert. Jede methodische Entscheidung mit Begründung dokumentiert.

**Offene Punkte:** #28 (Kernthese), #30 (Impact-Momente), #10 (Portfolio-Beschreibung)

---

## Dimension 2 — Struktur

- [✅] Verzeichnisstruktur entspricht wgnd-scaffolding Standard
- [✅] `README.md` vorhanden und ausgefüllt (Version 0.4.0, vollständige Sections)
- [✅] `ROADMAP.md` vorhanden mit aktuellem Phasen-Status
- [✅] `PROCESS_LOG.md` vorhanden und sehr aktuell (letzte Session: 2026-05-21)
- [✅] `pyproject.toml` vorhanden
- [✅] Notebooks klar nach Phase benannt (`00_` bis `06_`)
- [B] `reports/` Ordner vorhanden — aber unordentlich
  → `plotly_chart_1/2/3.html` in `figures/` sind auto-generierte Rohdateien ohne klaren Zweck.
  → `index.html` in `reports/` — Zweck unklar, in README als "Executive Summary HTML" benannt, aber wann erzeugt?
  → PNG-Naming inkonsistent (Mix aus `geo-`, `tempo-`, `meteo-`, `total-`).
- [✅] `src/` Package vorhanden (zh_tram_flow mit analytics, features, visualization, data)
- [?] `.gitignore` korrekt — laut README ist `data/` nicht in Git, nicht direkt geprüft

**Offene Punkte:** #35 (Reporting aufräumen)

---

## Dimension 3 — Kohärenz

- [B] README und `00_introduction.ipynb` erzählen dieselbe Geschichte
  → BACKLOG #6 offen — Synchronisierung ausstehend. Notebook-Struktur-Sektion in Introduction vermutlich veraltet.
- [?] Phasen-Namen stimmen mit `docs/CONVENTIONS.md` überein
  → Nicht direkt geprüft. Phasen-Namen in README und ROADMAP scheinen konsistent.
- [C] ROADMAP und PROCESS_LOG synchron
  → Weitgehend synchron. ROADMAP zeigt Phase 3 Checkboxen offen (02_preparation ausführen) — aber PROCESS_LOG sagt train/test_final exportiert. Kleine Lücke.
- [B] Alle Notebooks in `00_introduction.ipynb` referenziert
  → BACKLOG #7 offen: Workflow-Sektion zeigt nicht aktuelle 16-Notebook-Struktur.
- [B] Headline-Ergebnis konsistent (README, Introduction, Reports)
  → MAE 45.7s steht in README und PROCESS_LOG. Ob `00_introduction.ipynb` und `06_prediction_0-overview.ipynb` denselben Wert zeigen — nicht geprüft.
- [B] Zahlen und Metriken haben Single Source of Truth
  → Per Pre-Audit-Beobachtung: Zahlen stehen an mehreren Orten. Kein explizites Audit gemacht. Duplikations-Risiko hoch bei MAE, Zeilenzahlen, Finding-Counts.

**Offene Punkte:** #6 (Meta-Abgleich), #7 (via #6), #34 (Single Source of Truth)

---

## Dimension 4 — Artefakte

- [B] `00_introduction.ipynb` vorhanden und vollständig ausgeführt
  → Vorhanden und hat Output. Aber: Notebook-Liste und Workflow-Sektion veraltet (#7).
- [✅] Mindestens ein exportierter Report in `reports/`
  → `reports/insights.html` (3.4 MB, alle Plotly-Karten sichtbar ✅)
- [A] Key-Visual in README eingebunden
  → FEHLT. Kein einziges `![...]()` im README. Für GitHub-Auftritt kritisch — leerer First-Impression.
- [✅] Modell gespeichert
  → `data/models/lgbm_v1.txt` + `lgbm_v1_meta.json` + `test_predictions.parquet`
- [B] Alle Kern-Notebooks ausgeführt
  → `06_prediction_3-evaluation.ipynb` nur Skeleton. Metriken und Live-Szenario laut ROADMAP ✅, aber Fehleranalyse nach Linie/Stunde/Wetter noch offen.

**Offene Punkte:** #A Key-Visual (kritisch), Evaluation-Notebook (#19 Präsentation braucht vollständige Zahlen)

---

## Dimension 5 — Reproduzierbarkeit

- [?] `pyproject.toml` vollständig und getestet
  → `lightgbm>=4.0` ergänzt (PROCESS_LOG 2026-05-20). Vollständigkeit nicht frisch geprüft.
- [✅] README enthält Setup-Anleitung
  → Sehr vollständig: Clone → uv → venv → Dependencies → Kernel → Start (6 Schritte).
- [✅] Keine hardcodierten Pfade — nur über `PATHS`-Konfiguration
  → `config.py` mit `PATHS`-Dict dokumentiert, in README erklärt.
- [?] Keine Debug-Zellen / auskommentierten Blöcke in Notebooks
  → Nicht geprüft. Sollte vor finalem Export durchgegangen werden.
- [✅] `data/raw/` nicht im Git committet
  → README: "NICHT in Git! (.gitignore)" — bestätigt.

**Offene Punkte:** pyproject.toml und Notebooks auf Debug-Artefakte prüfen (vor Final-Export)

---

## Ergebnis

| Dimension | Status | Offene Punkte |
| :--- | :--- | :--- |
| 1 · Story | 🟡 B/C | Kernthese fehlt als Punch, Impact nicht sichtbar gemacht (#28, #30) |
| 2 · Struktur | 🟡 B | Reports-Ordner unordentlich (#35) |
| 3 · Kohärenz | 🟠 B | Single SoT fehlt, Introduction veraltet, ROADMAP/PROCESS_LOG Lücke (#6, #34) |
| 4 · Artefakte | 🔴 A+B | Key-Visual im README fehlt (A), Evaluation-Notebook unvollständig (B) |
| 5 · Reproduzierbarkeit | 🟢 C | Kleines Restrisiko bei pyproject.toml + Debug-Zellen |

**Portfolio-ready:** ⬜ Nein — noch nicht
**A-Punkte:** 1 (Key-Visual)
**B-Punkte:** 7
**C-Punkte:** 3

**Empfohlene Reihenfolge:**
1. Key-Visual ins README (A → weg, schnellster Win für GitHub-Auftritt)
2. Evaluation-Notebook vollständig ausführen (Fehleranalyse)
3. Reporting aufräumen: `figures/` bereinigen, Naming konsolidieren (#35)
4. Single Source of Truth Audit: Zahlen tracken, Duplikate auflösen (#34)
5. `00_introduction.ipynb` + README synchronisieren (#6)
6. Kernthese + Impact-Momente in README und Präsentation schärfen (#28, #30)

---

*Standard → `docs/portfolio/STANDARD.md`*
*Workflow → `docs/portfolio/WORKFLOW.md`*
