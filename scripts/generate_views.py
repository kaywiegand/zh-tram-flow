#!/usr/bin/env python3
"""
Portfolio Views Generator
Reads portfolio.md (SSOT) → generates index.html + overview/storyview/techview.html

Usage:
    python scripts/generate_views.py
    python scripts/generate_views.py --view overview
"""

import re
import sys
from pathlib import Path

BASE    = Path(__file__).parent.parent / "public"
MD_PATH = BASE / "md" / "portfolio.md"
OUT_DIR = BASE


# ══════════════════════════════════════════════════════════════
# VIEW CONFIG — defines structure of each presentation
# ══════════════════════════════════════════════════════════════

VIEW_CONFIG = {
    "overview": {
        "title":    "Ergebnisse & Empfehlungen",
        "audience": "HR · Business · Hiring Manager",
        "duration": "10 Min",
        "chapters": [
            {
                "nav_label": "Einstieg",
                "slides": [
                    {"type": "title"},
                    {"type": "problem"},
                ],
            },
            {
                "nav_label": "Überraschungen",
                "slides": [
                    {"type": "myth_bust"},
                ],
            },
            {
                "nav_label": "Erkenntnis",
                "slides": [
                    {"type": "proof_chain"},
                    {"type": "finding", "id": "F6"},
                ],
            },
            {
                "nav_label": "Modell",
                "slides": [
                    {"type": "model_comparison"},
                ],
            },
            {
                "nav_label": "Empfehlungen",
                "slides": [
                    {"type": "recommendations"},
                ],
            },
            {
                "nav_label": "Abschluss",
                "slides": [
                    {"type": "closing"},
                ],
            },
        ],
    },
    "storyview": {
        "title":    "Der vollständige Projektzyklus",
        "audience": "Portfolio · Hiring Manager · Kollegen",
        "duration": "25 Min",
        "chapters": [
            {
                "nav_label": "Einstieg",
                "slides": [
                    {"type": "title"},
                    {"type": "thesis"},
                ],
            },
            {
                "nav_label": "Genesis",
                "slides": [
                    {"type": "genesis"},
                ],
            },
            {
                "nav_label": "Daten",
                "slides": [
                    {"type": "de_sources"},
                    {"type": "de_pipeline"},
                ],
            },
            {
                "nav_label": "Überraschungen",
                "slides": [
                    {"type": "myth_bust"},
                ],
            },
            {
                "nav_label": "Findings",
                "slides": [
                    {"type": "findings_brief"},
                    {"type": "finding", "id": "F1"},
                    {"type": "finding", "id": "F2"},
                    {"type": "finding", "id": "F3"},
                    {"type": "finding", "id": "F4"},
                    {"type": "finding", "id": "F5"},
                    {"type": "finding", "id": "F6"},
                ],
            },
            {
                "nav_label": "Modell",
                "slides": [
                    {"type": "model_comparison"},
                ],
            },
            {
                "nav_label": "Empfehlungen",
                "slides": [
                    {"type": "recommendations"},
                ],
            },
            {
                "nav_label": "Abschluss",
                "slides": [
                    {"type": "closing"},
                ],
            },
        ],
    },
    "techview": {
        "title":    "Technical Deep-Dive",
        "audience": "Data Scientists · Engineers",
        "duration": "20 Min",
        "chapters": [
            {
                "nav_label": "Einstieg",
                "slides": [
                    {"type": "title"},
                    {"type": "thesis"},
                ],
            },
            {
                "nav_label": "Datenbasis",
                "slides": [
                    {"type": "de_sources"},
                    {"type": "de_pipeline"},
                    {"type": "cleaning_decisions"},
                ],
            },
            {
                "nav_label": "Baseline",
                "slides": [
                    {"type": "model_baseline_table"},
                ],
            },
            {
                "nav_label": "Modell",
                "slides": [
                    {"type": "model_comparison"},
                    {"type": "model_progression_table"},
                    {"type": "model_key_insight"},
                ],
            },
            {
                "nav_label": "Empfehlungen",
                "slides": [
                    {"type": "recommendations"},
                ],
            },
            {
                "nav_label": "Abschluss",
                "slides": [
                    {"type": "closing"},
                ],
            },
        ],
    },
}


# ══════════════════════════════════════════════════════════════
# PARSER — portfolio.md → structured dict
# ══════════════════════════════════════════════════════════════

def parse_portfolio(text: str) -> dict:
    return {
        "project":         _parse_project(text),
        "storyline":       _parse_storyline(text),
        "problem":         _parse_problem(text),
        "findings":        _parse_findings(text),
        "model":           _parse_model(text),
        "recommendations": _parse_recommendations(text),
    }


def _parse_code_block(text: str, section: str) -> dict:
    """Parse a fenced code block under ## Section."""
    m = re.search(rf"## {re.escape(section)}\s*```(.*?)```", text, re.DOTALL)
    if not m:
        return {}
    result = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


def _parse_project(text: str) -> dict:
    return _parse_code_block(text, "Project")


def _parse_storyline(text: str) -> dict:
    m = re.search(r"## Storyline\s*```(.*?)```", text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1).strip()
    result: dict = {}
    current_key = None
    current_lines: list = []
    for line in block.splitlines():
        if re.match(r"^[a-z_]+\s*:", line):
            if current_key:
                result[current_key] = " ".join(current_lines).strip()
            key, _, val = line.partition(":")
            current_key = key.strip()
            current_lines = [val.strip()]
        elif current_key and (line.startswith("            ") or line.startswith("\t")):
            current_lines.append(line.strip())
    if current_key:
        result[current_key] = " ".join(current_lines).strip()
    return result


def _parse_problem(text: str) -> dict:
    m = re.search(r"## Problem\s*```(.*?)```", text, re.DOTALL)
    if not m:
        return {}
    result = {}
    stmt_lines: list = []
    in_stmt = False
    for line in m.group(1).strip().splitlines():
        if line.strip().startswith("problem_statement"):
            in_stmt = True
            _, _, val = line.partition(":")
            stmt_lines.append(val.replace("|", "").strip())
        elif in_stmt and line.startswith("  "):
            stmt_lines.append(line.strip())
        elif ":" in line and not in_stmt:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
        elif in_stmt and line.strip() and not line.startswith(" "):
            in_stmt = False
    result["problem_statement"] = " ".join(stmt_lines).strip()
    return result


def _parse_findings(text: str) -> list:
    findings = []
    pattern = (
        r"### (F\d+) — (.+?)\n"
        r"```\s*\nfinding:\s*(.+?)\nnumber:\s*(.+?)\nsource:\s*(.+?)\n```"
        r"(.*?)(?=\n### F|\n---|\Z)"
    )
    for m in re.finditer(pattern, text, re.DOTALL):
        fid, title, finding, number, source, trailing = m.groups()
        images = re.findall(r"!\[([^\]]+)\]\(([^\)]+)\)", trailing)
        findings.append({
            "id":      fid.strip(),
            "title":   title.strip(),
            "finding": re.sub(r"\s+", " ", finding).strip(),
            "number":  number.strip(),
            "source":  source.strip(),
            "images":  [{"alt": a.strip(), "url": u.strip()} for a, u in images],
        })
    return findings


def _parse_recommendations(text: str) -> list:
    m = re.search(r"## Recommendations\s*```(.*?)```", text, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    recos = []
    parts = re.split(r"\nr(\d+):\s*\n", "\n" + block)
    i = 1
    while i + 1 < len(parts):
        num = parts[i]
        content = parts[i + 1]
        title_m  = re.search(r"title:\s*(.+)",          content)
        detail_m = re.search(r"detail:\s*([\s\S]+?)(?=\n\S|\Z)", content)
        if title_m:
            detail = re.sub(r"\s+", " ", detail_m.group(1)).strip() if detail_m else ""
            recos.append({"num": num, "title": title_m.group(1).strip(), "detail": detail})
        i += 2
    return recos


def _parse_model(text: str) -> dict:
    m = re.search(r"## Model Results(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not m:
        return {}
    sec = m.group(1)

    meta_m = re.search(
        r"```\s*\nbest_model:\s*(.+?)\nbest_metric:\s*(.+?)\nkey_insight:\s*([\s\S]+?)(?=mbe_v1|```|\Z)",
        sec,
    )
    baseline_m    = re.search(r"### Baseline Benchmark\s*\n((?:\|.+\n)+)",    sec)
    progression_m = re.search(r"### Model Progression\s*\n((?:\|.+\n)+)",     sec)

    return {
        "best_model":        meta_m.group(1).strip()  if meta_m else "LightGBM v2",
        "best_metric":       meta_m.group(2).strip()  if meta_m else "18,56 s MAE",
        "key_insight":       re.sub(r"\s+", " ", meta_m.group(3)).strip() if meta_m else "",
        "baseline_table":    baseline_m.group(1)    if baseline_m    else "",
        "progression_table": progression_m.group(1) if progression_m else "",
    }


# ══════════════════════════════════════════════════════════════
# RENDER FUNCTIONS — return HTML strings for each slide type
# ══════════════════════════════════════════════════════════════

def _slide(cls: str, content: str, extra: str = "") -> str:
    return f'<section class="{cls}"{extra}>\n{content}\n</section>'


def _content_slide(subline: str, h2: str, body: str) -> str:
    return f'<section>\n<span class="subline">{subline}</span>\n<h2>{h2}</h2>\n{body}\n</section>'


def render_title(p: dict, view_cfg: dict) -> str:
    proj = p["project"]
    name = proj.get("name", "Portfolio Project")
    period = proj.get("period", "")
    stack  = proj.get("stack", "")
    rows   = proj.get("rows", "")
    nbs    = proj.get("notebooks", "")
    view_title = view_cfg["title"]
    view_aud   = view_cfg["audience"]
    return _slide("title-slide", f"""
  <h1>{name}</h1>
  <p class="sub">{view_title}</p>
  <p class="sub" style="font-size:0.72em;opacity:0.7">{view_aud}</p>
  <div class="kpi-row">
    <div class="kpi"><div class="v">94,4 M</div><div class="l">Halt-Ereignisse<br>{period}</div></div>
    <div class="kpi red"><div class="v">87 %</div><div class="l">OTP · Ziel: 95 %</div></div>
    <div class="kpi amber"><div class="v">71,3 %</div><div class="l">Halte ohne Puffer</div></div>
    <div class="kpi green"><div class="v">18,56 s</div><div class="l">MAE LightGBM v2</div></div>
  </div>
  <div class="meta">{stack} · {rows} Zeilen · {nbs} Notebooks</div>""")


def render_thesis(p: dict) -> str:
    s = p["storyline"]
    thesis  = s.get("thesis",  "")
    hook    = s.get("hook",    "")
    so_what = s.get("so_what", "")
    return _slide("thesis-slide", f"""
  <div class="thesis-label">Kernthese</div>
  <div class="thesis-main">{thesis}</div>
  <div class="thesis-sub">{hook}</div>
  <div class="thesis-punch">{so_what}</div>""")


def render_problem(p: dict) -> str:
    pr   = p["problem"]
    ist  = pr.get("kpi_ist",  "87")
    soll = pr.get("kpi_soll", "95 %")
    gap  = pr.get("kpi_gap",  "−8 %")
    stmt = pr.get("problem_statement", "")
    return f"""<section>
  <span class="subline">Ausgangslage</span>
  <h2>Das strukturelle OTP-Defizit</h2>
  <div class="mrow">
    <div class="m red"><div class="v">{ist} %</div><div class="l">OTP Ist-Stand<br>2023–2025</div></div>
    <div class="m green"><div class="v">{soll}</div><div class="l">VBZ Zielwert<br>bis 2028</div></div>
    <div class="m amber"><div class="v">{gap}</div><div class="l">Strukturelle<br>Lücke</div></div>
    <div class="m"><div class="v">56,3 s</div><div class="l">Ø Ankunfts­<br>verspätung</div></div>
  </div>
  <div class="box" style="margin-top:14px">{stmt}</div>
  <div class="mrow" style="margin-top:12px">
    <div class="m amber"><div class="v">71,3 %</div><div class="l">Haltestellen<br>ohne Puffer</div></div>
    <div class="m red"><div class="v">L11</div><div class="l">68,7 s · OTP 82 %<br>stärkste Akkumulation</div></div>
    <div class="m"><div class="v">r ≥ 0,85</div><div class="l">Kaskadenkorrelation<br>alle 16 Linien</div></div>
  </div>
</section>"""


def render_myth_bust(p: dict) -> str:
    rows = [
        ("Die Innenstadt ist der Verspätungs-Hotspot",
         "Central (48,3 s) und Paradeplatz (48,2 s) liegen unter Netzschnitt. Hotspots: Enzenbühl 93,8 s, Balgrist 85,2 s — ausschliesslich Peripherie."),
        ("Der Morgenrush ist das grösste Zeitproblem",
         "7h liegt mit 48,9 s unter Netzschnitt. Echter Peak: 21h (67,9 s) — Abreisewellen nach Konzerten und Fussballspielen."),
        ("Schlechtes Wetter ist die Hauptursache",
         "Schnee (+54 s) und Regen (+23,3 s) sind Verstärker. Grundniveau (56,3 s) bleibt auch bei optimalen Bedingungen konstant hoch."),
    ]
    pairs = "".join(f"""
    <div class="myth-row-pair">
      <div class="myth-assume">{assume}</div>
      <div class="myth-arrow">→</div>
      <div class="myth-finding">{finding}</div>
    </div>""" for assume, finding in rows)
    return f"""<section>
  <span class="subline">Drei Annahmen — drei Überraschungen</span>
  <h2>Was die Daten widerlegen</h2>
  <div class="myth-rows">{pairs}
  </div>
</section>"""


def render_proof_chain(p: dict) -> str:
    steps = [
        ("1", "Anomalie",  "Periphere Hotspots, nicht zentrale Knotenpunkte — 0 Overlap Top-Dichte × Top-Delay"),
        ("2", "Gradient",  "Delay wächst entlang der Strecke — L11 vs. L6 als extremer Kontrast"),
        ("3", "Mechanismus", "71,3 % dwell_time = 0s — kein Puffer, keine Erholung möglich"),
        ("4", "Kaskade",   "Pearson r ≥ 0,85 auf allen 16 Linien — systematisch, kein Einzelfall"),
    ]
    step_html = "\n    <div class='step-arrow'>→</div>\n".join(
        f'<div class="step"><div class="sn">{n}</div><div class="sl">{l}</div><p>{d}</p></div>'
        for n, l, d in steps
    )
    return f"""<section>
  <span class="subline">Beweiskette</span>
  <h2>4 Schritte zum Kern des Problems</h2>
  <div class="steps">
    {step_html}
  </div>
  <div class="box" style="margin-top:16px">
    <strong>Schlussfolgerung:</strong> Was vorhersagbar ist, ist steuerbar.
    Das Modell bestätigt die Analyse — <em>prev_trip_delay</em> ist das stärkste neue Feature
    und senkt den MAE von 45,7 s auf 18,56 s.
  </div>
</section>"""


def render_finding(p: dict, finding_id: str) -> str:
    findings = {f["id"]: f for f in p["findings"]}
    if finding_id not in findings:
        return f"<!-- finding {finding_id} not found -->"
    f = findings[finding_id]
    title   = f["title"]
    finding = f["finding"]
    number  = f["number"]
    source  = f["source"]
    images  = f["images"]

    img_html = ""
    if images:
        if len(images) == 1:
            img = images[0]
            url = img["url"].replace("../img/", "img/")
            img_html = f'<img src="{url}" alt="{img["alt"]}" style="max-height:280px;width:100%;object-fit:contain;margin-top:12px">'
        else:
            cols = "".join(
                f'<div><img src="{img["url"].replace("../img/", "img/")}" alt="{img["alt"]}" style="max-height:200px;width:100%;object-fit:contain"><div class="caption">{img["alt"]}</div></div>'
                for img in images[:2]
            )
            img_html = f'<div class="cols" style="margin-top:12px">{cols}</div>'

    return f"""<section>
  <span class="subline">Finding {finding_id}</span>
  <h2>{title}</h2>
  <div class="mrow">
    <div class="m blue"><div class="v">{number}</div><div class="l">Kernzahl</div></div>
    <div class="kv-text">{finding}</div>
  </div>
  {img_html}
  <div class="caption" style="text-align:left;margin-top:8px">Quelle: {source}</div>
</section>"""


def render_findings_brief(p: dict) -> str:
    items = "".join(f"""
    <div class="agenda-item">
      <div class="num">{f["id"]}</div>
      <div class="label">{f["title"]} <span style="font-weight:400;color:var(--text-muted)">— {f["number"]}</span></div>
    </div>""" for f in p["findings"])
    return f"""<section>
  <span class="subline">6 Kernbefunde</span>
  <h2>Die Findings auf einen Blick</h2>
  <div class="agenda">{items}
  </div>
</section>"""


def render_genesis(p: dict) -> str:
    proj = p["project"]
    stack = proj.get("stack", "")
    period = proj.get("period", "")
    return f"""<section>
  <span class="subline">Projekthintergrund</span>
  <h2>Warum Zürich, warum Trams?</h2>
  <div class="cols">
    <div class="w55">
      <div class="kv-list">
        <div class="kv-row">
          <div class="kv-fact amber"><div class="fv">3</div><div class="fl">Ebenen der Projektwahl</div></div>
          <div class="kv-text"><strong>Relatability</strong> — Verspätungen sind gelebter Alltag. Kein Insider-Wissen nötig, um das Problem zu verstehen.</div>
        </div>
        <div class="kv-row">
          <div class="kv-fact green"><div class="fv">OGD</div><div class="fl">Open Gov Data</div></div>
          <div class="kv-text"><strong>Datengrundsatz</strong> — VBZ publiziert granulare Echtzeitdaten. Gross genug für echtes ML, konkret genug für operative Empfehlungen.</div>
        </div>
        <div class="kv-row">
          <div class="kv-fact"><div class="fv">↻</div><div class="fl">Vollständiger Zyklus</div></div>
          <div class="kv-text"><strong>Gemeinwohl</strong> — Öffentlicher Verkehr ist ein Gemeingut. Bessere Fahrplanung dient der Gesellschaft, nicht privatem Profit.</div>
        </div>
      </div>
    </div>
    <div class="w45">
      <div class="pf-grid" style="grid-template-columns:1fr">
        <div class="pf-card">
          <div class="pf-title">Stack</div>
          <p style="font-size:0.82em">{stack}</p>
        </div>
        <div class="pf-card">
          <div class="pf-title">Zeitraum & Umfang</div>
          <ul>
            <li>{period} — 3 Betriebsjahre</li>
            <li>94,4 M Halt-Ereignisse</li>
            <li>12 Notebooks · 66 Findings</li>
            <li>Full-Stack DANSC</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</section>"""


def render_de_sources(p: dict) -> str:
    sources = [
        ("VBZ IST-Daten", "Reale Ankunfts- und Abfahrtszeiten pro Trip × Stop", "50 M/Jahr", "36 ZIP-Archive", "Canceled Fahrten behalten — Extremfälle für das Modell"),
        ("GTFS Fahrplan",  "Offizielle Fahrpläne, dwell_time, Haltestellen-Koordinaten", "Yearly", "Parquet", "dwell_time = 0s für 71,3 % aller Halte — Root Cause"),
        ("Meteo Schweiz",  "Stündliche Wetterdaten (Temp, Niederschlag, Wind, Schnee)", "Stündlich", "3 Stationen", "Schnee geografisch trennbar von Regen (Höhenlagen vs. Flusstäler)"),
        ("Event-Kalender", "Grossveranstaltungen, Feiertage — manuell kuriert", "Per Date", "258 Events", "Fachmessen (66,0 s) schlagen Konzerte (75,4 s) in der Rangliste"),
    ]
    cards = "".join(f"""
    <div class="pf-card">
      <div class="pf-title">{name}</div>
      <p style="font-size:0.78em;margin-bottom:6px">{desc}</p>
      <ul>
        <li>Granularität: {gran} · Format: {fmt}</li>
        <li><strong>Key Discovery:</strong> {disc}</li>
      </ul>
    </div>""" for name, desc, gran, fmt, disc in sources)
    return f"""<section>
  <span class="subline">Data Engineering</span>
  <h2>4 heterogene Datenquellen</h2>
  <div class="pf-grid">{cards}
  </div>
</section>"""


def render_de_pipeline(p: dict) -> str:
    steps = [
        ("done",   "VBZ IST", "36 ZIP-Archive · 38 GB komprimiert · schweizweit → VBZ-Tram-Filter"),
        ("done",   "GTFS Join", "dwell_time · stop_coords · stop_sequence — temporale Joins pro service_date"),
        ("done",   "Delay Calc", "arrival_delay = actual_time − scheduled_time · trip_id rekonstruiert"),
        ("done",   "Meteo Join", "Stündliche Werte · floor(timestamp, '1h') · Stadtkreis-Aggregation"),
        ("done",   "Event Join", "258 Events · Gewichtung nach Kategorie + historischem Delay-Impact"),
        ("done",   "Master", "94,4 M Zeilen · 26 Features · 541 MB Parquet · Temporal Split"),
    ]
    steps_html = "".join(
        f'<div class="pipe-step {cls}"><span class="ps-badge">{label}</span><span class="ps-label">{detail}</span></div>'
        for cls, label, detail in steps
    )
    return f"""<section>
  <span class="subline">Data Engineering</span>
  <h2>Integration Pipeline</h2>
  <div class="pipe-steps">
    {steps_html}
  </div>
  <div class="info-cols">
    <div class="info-col blue"><strong>Tool-Wahl: Polars</strong><span>Lazy Evaluation — 94 M Zeilen passen nicht in RAM. Polars scandelt statt zu laden.</span></div>
    <div class="info-col blue"><strong>Dauer: ~3 Wochen</strong><span>Inklusive Reprocessing nach trip_id-Bug — ohne diesen Nachtrag hätte das Modell nicht funktioniert.</span></div>
    <div class="info-col green"><strong>Temporal Split</strong><span>2023–Jun 2024 Train · Jul–Dez 2024 Val · 2025 Test. Kein Shuffle — kein Data Leakage.</span></div>
  </div>
</section>"""


def render_cleaning_decisions(p: dict) -> str:
    rows = [
        ("Canceled Fahrten?", "Wegwerfen (Ausreißer)", "Canceled = systematisch bei Events", "Behalten"),
        ("Shuffle vs. Temporal Split?", "Shuffle für mehr Daten", "Zukünftige Daten ≠ Vergangenheit", "Temporal Split"),
        ("Outlier-Handling?", "Winsorisieren", "MAE bestraft Extremfälle proportional", "Kein Capping"),
        ("One-Hot vs. Native?", "One-Hot Standard", "LightGBM native Categoricals besser", "Native Categoricals"),
    ]
    rows_html_parts = []
    for i, (prob, annahme, befund, entscheidung) in enumerate(rows):
        cls = ' class="hl-green"' if i == 0 else ""
        rows_html_parts.append(
            f"<tr{cls}><td>{prob}</td>"
            f"<td style='color:var(--text-muted)'>{annahme}</td>"
            f"<td>{befund}</td><td><strong>{entscheidung}</strong></td></tr>"
        )
    rows_html = "".join(rows_html_parts)
    return f"""<section>
  <span class="subline">Data Engineering</span>
  <h2>Cleaning als Forschungsentscheidungen</h2>
  <table>
    <tr><th>Problem</th><th>Annahme</th><th>Befund</th><th>Entscheidung</th></tr>
    {rows_html}
  </table>
  <div class="box amber" style="margin-top:14px">
    <strong>Lernpunkt:</strong> Diese Entscheidungen sind keine Routine — jede hat messbare Auswirkungen auf Modell-Performance und Generalisierbarkeit.
  </div>
</section>"""


def render_model_comparison(p: dict) -> str:
    return """<section>
  <span class="subline">ML-Modell</span>
  <h2>LightGBM v1 → v2: Das richtige Signal</h2>
  <div class="model-cards">
    <div class="model-card">
      <span class="card-badge">Baseline</span>
      <h3>Stop Mean</h3>
      <div class="card-mae">50,0 s</div>
      <ul><li>Predict ⌀ by stop — bester naiver Ansatz</li><li>Kein Zeitkontext, kein Wetter, kein Event</li></ul>
      <div class="card-note">Referenzpunkt für alle Modell-Verbesserungen</div>
    </div>
    <div class="model-card">
      <span class="card-badge">LightGBM v1</span>
      <h3>34 Features</h3>
      <div class="card-mae">45,7 s</div>
      <ul><li>Zeit · Wetter · Events · Linie · Stop</li><li>MBE +8,3 s — systematisch zu optimistisch</li></ul>
      <div class="card-note">−4,3 s vs. Baseline — solide, aber kein Durchbruch</div>
    </div>
    <div class="model-card card-green">
      <span class="card-badge">LightGBM v2</span>
      <h3>36 Features</h3>
      <div class="card-mae">18,56 s</div>
      <ul><li>+ prev_trip_delay (Kaskadenindikator)</li><li>+ stop_sequence_pct · Isotonic-Kalibrierung</li><li>MBE −0,69 s — nahezu bias-frei</li></ul>
      <div class="card-note">−31,4 s vs. Baseline · −63 % · Signal aus der Analyse</div>
    </div>
  </div>
  <div class="box green" style="margin-top:14px">
    Der Sprung kam nicht durch einen besseren Algorithmus, sondern durch das richtige Signal:
    <em>prev_trip_delay</em> — der Kaskadenindikator aus der Analyse. Das Modell bestätigt die These.
  </div>
</section>"""


def render_model_baseline_table(p: dict) -> str:
    model = p["model"]
    table_md = model.get("baseline_table", "")
    table_html = _md_table_to_html(table_md, hl_last=True)
    return f"""<section>
  <span class="subline">Baseline Benchmark</span>
  <h2>Stop Mean als härtester naiver Benchmark</h2>
  {table_html}
  <div class="box" style="margin-top:14px">
    <strong>Warum Stop Mean?</strong> Jede Haltestelle hat ein eigenes strukturelles Delay-Niveau.
    Stop Mean nutzt genau dieses — ohne Zeitkontext, Wetter oder Events.
    Wer Stop Mean nicht schlägt, hat nichts gelernt.
  </div>
</section>"""


def render_model_progression_table(p: dict) -> str:
    model = p["model"]
    table_md = model.get("progression_table", "")
    table_html = _md_table_to_html(table_md, hl_last=True)
    return f"""<section>
  <span class="subline">Modell-Evaluation</span>
  <h2>Progression: Baseline → v1 → v2</h2>
  {table_html}
</section>"""


def render_model_key_insight(p: dict) -> str:
    model = p["model"]
    insight = model.get("key_insight", "")
    return f"""<section>
  <span class="subline">Key Insight</span>
  <h2>Das stärkste Feature war in der Analyse versteckt</h2>
  <div class="ev-chain">
    <div class="ev-step">
      <div class="ev-circle">1</div>
      <div class="ev-body"><strong>Analyse-Finding: Pearson r ≥ 0,85</strong><span>Der Delay eines Halts überträgt sich auf den nächsten Halt desselben Trips — auf allen 16 Linien.</span></div>
    </div>
    <div class="ev-arrow">↓</div>
    <div class="ev-step">
      <div class="ev-circle">2</div>
      <div class="ev-body"><strong>Feature Engineering: prev_trip_delay</strong><span>Der Delay des Vorgänger-Halts als Feature. Echtzeit-verfügbar — der vorherige Halt ist immer bekannt.</span></div>
    </div>
    <div class="ev-arrow">↓</div>
    <div class="ev-step climax">
      <div class="ev-circle">3</div>
      <div class="ev-body"><strong>Modell-Ergebnis: MAE 45,7 s → 18,56 s</strong><span>Ein Feature — −59 % MAE-Reduktion. {insight[:120] if len(insight) > 120 else insight}</span></div>
    </div>
  </div>
  <div class="info-cols">
    <div class="info-col blue"><strong>XGBoost Robustheits-Check</strong><span>Val MAE ~21,4 s (150 Runden, >90 Min auf 85 M Zeilen) — LightGBM klar überlegen bei Trainingszeit.</span></div>
    <div class="info-col green"><strong>Deployment-ready</strong><span>prev_trip_delay ist Live-Signal — verfügbar via VBZ-API. Das Modell kann im Echtbetrieb genutzt werden.</span></div>
  </div>
</section>"""


def render_recommendations(p: dict) -> str:
    recos = p["recommendations"]
    cards = "".join(f"""
    <div class="reco">
      <div class="rn">R{r["num"]}</div>
      <div style="flex:1">
        <strong>{r["title"]}</strong>
        <span style="display:block;font-size:0.78em;color:var(--text-muted);margin-top:6px;line-height:1.5">{r["detail"][:200]}{"…" if len(r["detail"]) > 200 else ""}</span>
      </div>
    </div>""" for r in recos)
    return f"""<section>
  <span class="subline">Handlungsempfehlungen</span>
  <h2>4 Hebel — jeder direkt durch Daten gedeckt</h2>
  <div class="reco-grid">{cards}
  </div>
</section>"""


def render_closing(p: dict, view_cfg: dict) -> str:
    proj = p["project"]
    gh   = proj.get("github",    "kaywiegand/zh-tram-flow")
    dash = proj.get("dashboard", "")
    name = proj.get("name",      "Zurich Tram Flow")
    return f"""<section class="closing">
  <h2>{name}</h2>
  <p class="sub">Verspätungen im Zürcher Tramnetz sind vorhersagbar — weil sie strukturell sind.<br>Was vorhersagbar ist, ist steuerbar.</p>
  <div class="closing-stats">
    <div class="closing-stat"><div class="v">94,4 M</div><div class="l">Halt-Ereignisse</div></div>
    <div class="closing-stat"><div class="v green">18,56 s</div><div class="l">MAE LightGBM v2</div></div>
    <div class="closing-stat"><div class="v">−63 %</div><div class="l">vs. Baseline</div></div>
    <div class="closing-stat"><div class="v">4</div><div class="l">Empfehlungen</div></div>
  </div>
  <div class="closing-divider"></div>
  <div class="closing-links">
    <a href="https://github.com/{gh}" target="_blank">GitHub Repo</a>
    {"<a href='" + dash + "' target='_blank'>Live Dashboard</a>" if dash else ""}
    <a href="index.html">← Portfolio Hub</a>
  </div>
</section>"""


# ── Slide dispatch ─────────────────────────────────────────────

RENDERERS = {
    "title":                render_title,
    "thesis":               render_thesis,
    "problem":              render_problem,
    "myth_bust":            render_myth_bust,
    "proof_chain":          render_proof_chain,
    "findings_brief":       render_findings_brief,
    "finding":              render_finding,
    "genesis":              render_genesis,
    "de_sources":           render_de_sources,
    "de_pipeline":          render_de_pipeline,
    "cleaning_decisions":   render_cleaning_decisions,
    "model_comparison":     render_model_comparison,
    "model_baseline_table": render_model_baseline_table,
    "model_progression_table": render_model_progression_table,
    "model_key_insight":    render_model_key_insight,
    "recommendations":      render_recommendations,
    "closing":              render_closing,
}


def render_slide(slide_cfg: dict, portfolio: dict, view_cfg: dict) -> str:
    t = slide_cfg["type"]
    if t == "title":
        return render_title(portfolio, view_cfg)
    elif t == "finding":
        return render_finding(portfolio, slide_cfg["id"])
    elif t == "closing":
        return render_closing(portfolio, view_cfg)
    elif t in RENDERERS:
        return RENDERERS[t](portfolio)
    else:
        return f"<!-- unknown slide type: {t} -->"


# ══════════════════════════════════════════════════════════════
# HTML ASSEMBLY
# ══════════════════════════════════════════════════════════════

NAV_JS = r"""
  Reveal.initialize({
    hash: true, transition: 'slide', transitionSpeed: 'default',
    center: false, controls: false, progress: false
  });

  // ── Nav + Ticks setup ──────────────────────────────────────

  const CHAPTERS = /* CHAPTERS_DATA */;

  // Build #nav tabs
  (function buildNav() {
    const nav = document.getElementById('nav');
    if (!nav) return;
    const chs = nav.querySelector('.chs');
    chs.innerHTML = '';
    CHAPTERS.forEach((ch, i) => {
      const el = document.createElement('div');
      el.className = 'ch';
      el.dataset.chapter = i;
      el.textContent = ch.label;
      el.addEventListener('click', () => Reveal.slide(ch.firstSlide, 0));
      chs.appendChild(el);
    });
    nav.style.display = 'flex';
  })();

  // Build #slideticks
  function buildTicks(totalFlat) {
    const el = document.getElementById('slideticks');
    if (!el) return;
    el.innerHTML = '';
    let chIdx = 0;
    for (let i = 0; i < totalFlat; i++) {
      const isChStart = CHAPTERS[chIdx] && CHAPTERS[chIdx].firstSlide === i;
      if (isChStart && chIdx < CHAPTERS.length - 1) chIdx++;
      const wrap = document.createElement('div');
      wrap.className = 'stk-wrap';
      const tick = document.createElement('div');
      tick.className = 'stk';
      const num = document.createElement('div');
      num.className = 'stk-num';
      num.textContent = i + 1;
      const lbl = document.createElement('div');
      lbl.className = 'stk-ch-label';
      if (CHAPTERS[chIdx] && CHAPTERS[chIdx].firstSlide === i) {
        wrap.classList.add('stk-chapter');
        lbl.textContent = CHAPTERS[chIdx].label;
      }
      wrap.appendChild(lbl);
      wrap.appendChild(tick);
      wrap.appendChild(num);
      el.appendChild(wrap);
    }
  }

  // Build #leftnav
  function buildLeftNav(totalFlat) {
    const el = document.getElementById('leftnav');
    if (!el) return;
    el.innerHTML = '';
    CHAPTERS.forEach(ch => {
      const item = document.createElement('div');
      item.className = 'ln-item ln-chapter';
      item.dataset.slide = ch.firstSlide;
      item.innerHTML = `<div class="ln-tick"></div><div class="ln-label">${ch.label}</div>`;
      item.addEventListener('click', () => Reveal.slide(ch.firstSlide, 0));
      el.appendChild(item);
    });
  }

  // Update active state
  function updateNav(flatIdx) {
    // Nav tabs
    const tabs = document.querySelectorAll('#nav .ch');
    let activeChIdx = 0;
    CHAPTERS.forEach((ch, i) => {
      if (flatIdx >= ch.firstSlide) activeChIdx = i;
    });
    tabs.forEach((tab, i) => {
      tab.className = 'ch' + (i === activeChIdx ? ' active' : i < activeChIdx ? ' done' : '');
    });

    // Ticks
    const ticks = document.querySelectorAll('.stk-wrap');
    ticks.forEach((wrap, i) => {
      wrap.classList.remove('stk-past', 'stk-current', 'stk-chapter-active');
      if (i < flatIdx)      wrap.classList.add('stk-past');
      if (i === flatIdx)    wrap.classList.add('stk-current');
      if (wrap.classList.contains('stk-chapter') && i <= flatIdx) wrap.classList.add('stk-chapter-active');
    });

    // Left nav
    const lnItems = document.querySelectorAll('.ln-item');
    lnItems.forEach((item) => {
      const s = parseInt(item.dataset.slide);
      item.classList.remove('ln-past', 'ln-current');
      if (s < flatIdx)   item.classList.add('ln-past');
      if (s === flatIdx) item.classList.add('ln-current');
    });

    // Progress
    const fill = document.getElementById('progress-fill');
    const total = ticks.length;
    if (fill && total > 1) fill.style.width = ((flatIdx / (total - 1)) * 100) + '%';
  }

  Reveal.on('ready', (e) => {
    // Count total flat slides (outer sections = chapters in our structure)
    const outerSections = document.querySelectorAll('.slides > section');
    let total = 0;
    const flatMap = []; // outerIdx → flatIdx of first inner slide
    outerSections.forEach((outer, oi) => {
      flatMap.push(total);
      const inner = outer.querySelectorAll('section');
      total += inner.length || 1;
    });
    // Patch CHAPTERS firstSlide with actual flat indices
    CHAPTERS.forEach((ch, i) => {
      ch.firstSlide = flatMap[ch.outerIdx] || 0;
    });
    buildTicks(total);
    buildLeftNav(total);
    const flat = Reveal.getState().indexh;
    updateNav(flatMap[flat] || 0);
  });

  Reveal.on('slidechanged', (e) => {
    const outerSections = document.querySelectorAll('.slides > section');
    let flatIdx = 0;
    for (let i = 0; i < e.indexh; i++) {
      const inner = outerSections[i]?.querySelectorAll('section');
      flatIdx += inner?.length || 1;
    }
    flatIdx += e.indexv || 0;
    updateNav(flatIdx);
  });

  // Chart tile handlers
  document.querySelectorAll('a.chart-tile').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      const img = a.querySelector('img');
      if (!img) return;
      const w = window.open('', '_blank');
      w.document.write('<!DOCTYPE html><html><head><style>*{margin:0;padding:0}body{background:#0a0a0a;display:flex;align-items:center;justify-content:center;min-height:100vh}</style></head><body><img src="' + img.src + '" style="max-width:100vw;max-height:100vh;object-fit:contain"></body></html>');
      w.document.close(); w.focus();
    });
  });
"""


def _chapters_data_js(view_cfg: dict) -> str:
    """Generate the CHAPTERS JS array for nav/tick wiring."""
    chapters = view_cfg["chapters"]
    outer_idx = 0
    entries = []
    for ch in chapters:
        entries.append(f'{{label: "{ch["nav_label"]}", outerIdx: {outer_idx}, firstSlide: {outer_idx}}}')
        outer_idx += 1
    return "[" + ", ".join(entries) + "]"


def _md_table_to_html(md_table: str, hl_last: bool = False) -> str:
    """Convert markdown table to HTML. Highlights last data row if hl_last."""
    if not md_table.strip():
        return ""
    lines = [l for l in md_table.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return ""
    # Header
    header_cells = [c.strip().strip("*") for c in lines[0].split("|") if c.strip()]
    th = "".join(f"<th>{c}</th>" for c in header_cells)
    # Skip separator line
    data_lines = [l for l in lines[2:] if not re.match(r"^\s*\|[-| ]+\|\s*$", l)]
    rows_html = ""
    for i, line in enumerate(data_lines):
        cells = [c.strip().strip("*") for c in line.split("|") if c.strip() is not None]
        cells = [c for c in cells if c.strip() != ""]
        is_last = hl_last and i == len(data_lines) - 1
        row_cls = ' class="hl-green"' if is_last else ""
        td = "".join(f"<td>{c}</td>" for c in cells)
        rows_html += f"<tr{row_cls}>{td}</tr>"
    return f"<table><tr>{th}</tr>{rows_html}</table>"


HTML_SHELL = """\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{project_name} — {view_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css">
  <link rel="stylesheet" href="css/slides.css">
</head>
<body>

<div id="nav"><div class="chs"></div></div>
<div id="slideticks"></div>
<div id="leftnav"></div>
<div id="progress-track"><div id="progress-fill"></div></div>

<div class="reveal">
  <div class="slides">
{slides_html}
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script>
{js}
</script>
</body>
</html>
"""


def build_presentation(portfolio: dict, view_key: str) -> str:
    view_cfg   = VIEW_CONFIG[view_key]
    chapters   = view_cfg["chapters"]
    proj_name  = portfolio["project"].get("name", "Portfolio")

    # Render outer sections (chapters), each containing inner slides
    outer_sections = []
    for ch in chapters:
        inner_slides = [render_slide(s, portfolio, view_cfg) for s in ch["slides"]]
        # Wrap all inner slides in a single outer <section>
        inner_html = "\n".join(inner_slides)
        outer_sections.append(
            f"    <!-- ── {ch['nav_label']} ────────────────────────────── -->\n"
            f"    <section>\n{inner_html}\n    </section>"
        )

    slides_html  = "\n".join(outer_sections)
    chapters_js  = _chapters_data_js(view_cfg)
    js = NAV_JS.replace("/* CHAPTERS_DATA */", chapters_js)

    return HTML_SHELL.format(
        project_name=proj_name,
        view_title=view_cfg["title"],
        slides_html=slides_html,
        js=js,
    )


# ══════════════════════════════════════════════════════════════
# INDEX.HTML
# ══════════════════════════════════════════════════════════════

INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Portfolio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --primary:  #3C4F72;
      --primary-dk: #1C2B48;
      --accent:   #C4933A;
      --text:     #596278;
      --muted:    #8A95AB;
      --surface:  #EEEDF2;
      --border:   #D0D4E2;
      --positive: #27ae60;
      --negative: #c0392b;
      --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    html {{ scroll-behavior: smooth; background: #f8fafc; }}
    body {{ font-family: var(--font); color: var(--text); line-height: 1.6; }}

    /* ── Header ── */
    header {{
      background: linear-gradient(135deg, var(--primary-dk) 0%, var(--primary) 100%);
      color: #fff; padding: 2.8rem 2rem 2.2rem;
    }}
    .header-inner {{ max-width: 900px; margin: 0 auto; }}
    header h1 {{ font-size: 2.1rem; font-weight: 700; margin-bottom: 0.3rem; }}
    .tagline    {{ font-size: 1.05rem; opacity: 0.82; margin-bottom: 0.4rem; }}
    .subtitle   {{ font-size: 0.88rem; opacity: 0.68; margin-bottom: 1.6rem; }}
    .kpi-row    {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 1.2rem; }}
    .kpi {{ background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.18); border-radius: 8px; padding: 10px 16px; text-align: center; min-width: 100px; }}
    .kpi .v {{ font-size: 1.45rem; font-weight: 700; color: #fff; }}
    .kpi .l {{ font-size: 0.65rem; color: rgba(255,255,255,0.55); letter-spacing: 0.04em; margin-top: 2px; }}
    .kpi.positive .v {{ color: #4cd98a; }}
    .kpi.negative .v {{ color: #ff7a7a; }}
    .kpi.amber .v    {{ color: #ffc66d; }}

    /* ── Main ── */
    main {{ max-width: 900px; margin: 0 auto; padding: 3rem 1rem 5rem; }}
    section {{ margin-bottom: 4rem; }}
    .section-label {{ font-size: 0.7rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: var(--accent); margin-bottom: 0.4rem; }}
    h2 {{ font-size: 1.3rem; font-weight: 700; color: var(--primary); margin-bottom: 0.3rem; }}
    .section-intro {{ font-size: 0.9rem; color: var(--text); margin-bottom: 1.6rem; line-height: 1.6; }}

    /* ── View Cards ── */
    .view-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 2rem; }}
    @media (max-width: 640px) {{ .view-grid {{ grid-template-columns: 1fr; }} }}
    .view-card {{
      background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 22px;
      border-top: 4px solid var(--accent); text-decoration: none; color: inherit;
      transition: box-shadow 0.18s, transform 0.18s;
      display: flex; flex-direction: column;
    }}
    .view-card:hover {{ box-shadow: 0 4px 20px rgba(60,79,114,0.14); transform: translateY(-2px); }}
    .view-card.overview  {{ border-top-color: var(--primary); }}
    .view-card.storyview {{ border-top-color: #6c5ce7; }}
    .view-card.techview  {{ border-top-color: var(--accent); }}
    .view-label {{ font-size: 0.66rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 8px; }}
    .view-card.overview  .view-label {{ color: var(--primary); }}
    .view-card.storyview .view-label {{ color: #6c5ce7; }}
    .view-card.techview  .view-label {{ color: var(--accent); }}
    .view-card h3 {{ font-size: 1.1rem; color: var(--primary); margin-bottom: 6px; }}
    .view-card .view-desc {{ font-size: 0.83rem; color: var(--text); margin-bottom: 12px; line-height: 1.5; flex-grow: 1; }}
    .view-meta {{ display: flex; gap: 10px; align-items: center; margin-top: 10px; }}
    .view-time {{ font-size: 0.73rem; color: var(--muted); font-weight: 500; }}
    .view-badge {{ font-size: 0.68rem; font-weight: 600; padding: 3px 9px; border-radius: 4px; }}
    .view-badge.blue   {{ background: #e8edf5; color: var(--primary); }}
    .view-badge.purple {{ background: #f3f0ff; color: #6c5ce7; }}
    .view-badge.amber  {{ background: #fdf5e6; color: var(--accent); }}

    /* ── Quick Links ── */
    .links-box {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 20px; }}
    .links-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; }}
    .quick-link {{
      display: flex; align-items: center; gap: 8px; padding: 10px 14px;
      border-radius: 7px; text-decoration: none; color: var(--primary);
      background: var(--surface); border: 1px solid var(--border);
      font-size: 0.88rem; font-weight: 600; transition: background 0.15s;
    }}
    .quick-link:hover {{ background: #e0e4f0; }}
    .quick-link::before {{ content: "→"; color: var(--accent); font-weight: 700; }}

    /* ── Footer ── */
    footer {{ background: var(--surface); border-top: 1px solid var(--border); padding: 2rem; text-align: center; color: var(--muted); font-size: 0.82rem; margin-top: 3rem; }}
    footer a {{ color: var(--primary); text-decoration: none; }}
    footer a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <h1>{name}</h1>
    <p class="tagline">{tagline}</p>
    <p class="subtitle">{subtitle}</p>
    <div class="kpi-row">
      <div class="kpi"><div class="v">94,4 M</div><div class="l">Halt-Ereignisse</div></div>
      <div class="kpi negative"><div class="v">87 %</div><div class="l">OTP · Ziel: 95 %</div></div>
      <div class="kpi amber"><div class="v">71,3 %</div><div class="l">ohne Puffer</div></div>
      <div class="kpi positive"><div class="v">18,56 s</div><div class="l">MAE LightGBM v2</div></div>
    </div>
  </div>
</header>

<main>
  <section>
    <div class="section-label">Motivation & Ansatz</div>
    <h2>Das Projekt</h2>
    <p class="section-intro">
      Verspätungen sind gelebter Alltag — und deshalb ideal für datengetriebene Analyse.
      Das Zürcher Tramnetz verfehlt seinen 95 %-OTP-Zielwert seit Jahren.
      Dieses Projekt zeigt warum: <strong>71,3 % aller Haltestellen haben 0s Standzeit — kein eingebauter Puffer.</strong>
      LightGBM v2 erreicht 18,56 s MAE (−63 % vs. Baseline) — nicht durch besseren Algorithmus,
      sondern durch das richtige Signal aus der Analyse: <em>prev_trip_delay</em>.
    </p>
  </section>

  <section>
    <div class="section-label">Wähle deine Perspektive</div>
    <h2>Drei kuratierte Präsentationen</h2>
    <p class="section-intro">Gleiche Daten — unterschiedliche Dramaturgie und Tiefe.</p>
    <div class="view-grid">
      <a href="overview.html" class="view-card overview">
        <div class="view-label">Overview</div>
        <h3>Ergebnisse & Empfehlungen</h3>
        <p class="view-desc">Für Entscheider und HR. Findings, Modell-Ergebnis und 4 konkrete Handlungsempfehlungen.</p>
        <div class="view-meta">
          <span class="view-time">⏱ 10 Min</span>
          <span class="view-badge blue">HR · Business</span>
        </div>
      </a>
      <a href="storyview.html" class="view-card storyview">
        <div class="view-label">Story View</div>
        <h3>Vollständiger Projektzyklus</h3>
        <p class="view-desc">Der gesamte Data Cycle: Genesis, Engineering, alle 6 Findings, Modell, Empfehlungen.</p>
        <div class="view-meta">
          <span class="view-time">⏱ 25 Min</span>
          <span class="view-badge purple">Portfolio</span>
        </div>
      </a>
      <a href="techview.html" class="view-card techview">
        <div class="view-label">Tech View</div>
        <h3>Technical Deep-Dive</h3>
        <p class="view-desc">Feature Engineering, Baseline-Benchmark, Modell-Progression, Key Insight für Engineers.</p>
        <div class="view-meta">
          <span class="view-time">⏱ 20 Min</span>
          <span class="view-badge amber">Data Science</span>
        </div>
      </a>
    </div>
  </section>

  <section>
    <div class="section-label">Schneller Zugriff</div>
    <h2>Weitere Ressourcen</h2>
    <div class="links-box">
      <div class="links-grid">
        <a href="{github_url}" target="_blank" class="quick-link">GitHub Repo</a>
        {dashboard_link}
        <a href="network-map.html" class="quick-link">Netzwerk-Karte</a>
        <a href="md/portfolio.md" class="quick-link">portfolio.md (SSOT)</a>
      </div>
    </div>
  </section>
</main>

<footer>
  <p>{name} — Verspätungsvorhersage & Fahrplan-Optimierung<br>
  <a href="https://github.com/kaywiegand">Kay Wiegand</a> ·
  <a href="{github_url}">GitHub</a> · {period}</p>
  <p style="margin-top:0.8rem;font-size:0.73rem;opacity:0.7">
    Generiert aus <a href="md/portfolio.md">portfolio.md</a> via generate_views.py
  </p>
</footer>
</body>
</html>
"""


def build_index(portfolio: dict) -> str:
    proj = portfolio["project"]
    name = proj.get("name", "Portfolio Project")
    gh   = proj.get("github", "kaywiegand/zh-tram-flow")
    dash = proj.get("dashboard", "")
    period = proj.get("period", "")
    github_url = f"https://github.com/{gh}"
    dashboard_link = (
        f'<a href="{dash}" target="_blank" class="quick-link">Live Dashboard</a>'
        if dash else ""
    )
    return INDEX_TEMPLATE.format(
        name=name,
        tagline="Verspätungsvorhersage im Zürcher Tramnetz",
        subtitle=f"Datengetriebenes Analyse- und ML-Projekt · {period}",
        github_url=github_url,
        dashboard_link=dashboard_link,
        period=period,
    )


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    target = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--view" else None

    print(f"📖  Reading {MD_PATH}")
    text = MD_PATH.read_text(encoding="utf-8")
    portfolio = parse_portfolio(text)
    print(f"    Project: {portfolio['project'].get('name', '?')}")
    print(f"    Findings: {len(portfolio['findings'])} · Recos: {len(portfolio['recommendations'])}")

    views = [target] if target else list(VIEW_CONFIG.keys())

    for view_key in views:
        out_path = OUT_DIR / f"{view_key}.html"
        print(f"\n🎨  Generating {view_key}...")
        html = build_presentation(portfolio, view_key)
        out_path.write_text(html, encoding="utf-8")
        print(f"    ✅  {out_path} ({len(html):,} chars)")

    # index.html
    if not target or target == "index":
        idx_path = OUT_DIR / "index.html"
        print(f"\n🏠  Generating index.html...")
        html = build_index(portfolio)
        idx_path.write_text(html, encoding="utf-8")
        print(f"    ✅  {idx_path} ({len(html):,} chars)")

    print("\n✅  Done. Open public/index.html in browser.")


if __name__ == "__main__":
    main()
