"""
check_style.py
--------------
Prüft alle Analytics- und Visualization-Files auf Style-Konformität.
Lauf: python scripts/check_style.py

Exit 0 = alles OK
Exit 1 = Verstöße gefunden
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
FILES = [
    ROOT / "src/zh_tram_flow/analytics/target.py",
    ROOT / "src/zh_tram_flow/analytics/network.py",
    ROOT / "src/zh_tram_flow/analytics/temporal.py",
    ROOT / "src/zh_tram_flow/analytics/spatial.py",
    ROOT / "src/zh_tram_flow/analytics/meteo.py",
    ROOT / "src/zh_tram_flow/analytics/events.py",
    ROOT / "src/zh_tram_flow/visualization/insights.py",
]

# ── German words that must not appear in chart-visible strings ─────────────────
# Only checked in set_title / set_xlabel / set_ylabel / label= / suptitle / text=
GERMAN_PATTERNS = [
    r"Verspätung", r"Haltestelle", r"Stadtkreis", r"Wochentag",
    r"Durchschnitt", r"Haltezeit", r"Fahrplanwechsel", r"Einlaufzeit",
    r"Ankunft(?!s)", r"Abfahrt", r"Schulferien", r"Jahreszeit",
    r"Starkregen", r"Schnee\b", r"Linien\b", r"nach Jahr",
    r"nach Monat", r"nach Saison", r"Ø Verspätung",
]

# Lines that are in chart-output context (not docstrings or comments)
CHART_LINE_RE = re.compile(
    r'(set_title|set_xlabel|set_ylabel|suptitle|fig\.text|\.text\(|label=|name=)[^#\n]*'
)

# ── Rules ──────────────────────────────────────────────────────────────────────
RULES = [
    {
        "id": "R01",
        "desc": "style[\"title\"] must not be used — use TITLE_KW",
        "pattern": re.compile(r'\*\*style\["title"\]'),
        "in_comments": False,
    },
    {
        "id": "R02",
        "desc": "axhline(0) / axvline(0) forbidden (zero lines)",
        "pattern": re.compile(r'ax[hv]line\(\s*0[\s,\)]'),
        "in_comments": False,
    },
    {
        "id": "R03",
        "desc": "Manual fontweight='bold' without TITLE_KW — use TITLE_KW or suptitle pattern",
        "pattern": re.compile(r'set_title\([^)]+fontweight=["\']bold["\']'),
        "in_comments": False,
    },
    {
        "id": "R04",
        "desc": "title=dict(... without plotly_title() — use plotly_title()",
        "pattern": re.compile(r'title=dict\(text='),
        "in_comments": False,
    },
    {
        "id": "R05",
        "desc": "legend(frameon=False) manually — use LEGEND_KW_RIGHT or LEGEND_KW_LEFT",
        "pattern": re.compile(r'\.legend\([^)]*frameon=False'),
        "in_comments": False,
    },
    {
        "id": "R06",
        "desc": "fontsize=14 in set_title — use TITLE_KW (fontsize=11)",
        "pattern": re.compile(r'set_title\([^)]*fontsize=1[4-9]'),
        "in_comments": False,
    },
]

# ── Runner ─────────────────────────────────────────────────────────────────────
def is_comment_or_docstring(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''")


def check_file(path: Path) -> list[dict]:
    issues = []
    lines = path.read_text().splitlines()

    for lineno, line in enumerate(lines, 1):
        if is_comment_or_docstring(line):
            continue

        # Rule checks
        for rule in RULES:
            if rule["pattern"].search(line):
                issues.append({
                    "file": path.name,
                    "line": lineno,
                    "rule": rule["id"],
                    "desc": rule["desc"],
                    "text": line.strip()[:100],
                })

        # German in chart strings
        if CHART_LINE_RE.search(line):
            for pat in GERMAN_PATTERNS:
                if re.search(pat, line):
                    issues.append({
                        "file": path.name,
                        "line": lineno,
                        "rule": "R07",
                        "desc": f"German text in chart output: '{pat}'",
                        "text": line.strip()[:100],
                    })
                    break  # one issue per line

    return issues


def check_ylim_coverage(path: Path) -> list[dict]:
    """Check that all def plot_* functions have at least one ylim parameter."""
    issues = []
    text = path.read_text()
    # Find all plot function definitions
    fn_defs = re.finditer(r'def (plot_\w+)\(([^)]*)\)', text)
    for m in fn_defs:
        fn_name = m.group(1)
        params = m.group(2)
        if "ylim" not in params and "save_as" in params:
            issues.append({
                "file": path.name,
                "line": text[:m.start()].count("\n") + 1,
                "rule": "R08",
                "desc": f"plot function missing ylim parameter",
                "text": f"def {fn_name}(...)",
            })
    return issues


def main():
    all_issues = []
    for f in FILES:
        if not f.exists():
            print(f"  MISSING: {f}")
            continue
        all_issues.extend(check_file(f))
        all_issues.extend(check_ylim_coverage(f))

    if not all_issues:
        print("✅  All style checks passed — 7 files clean.")
        return 0

    # Group by file
    by_file: dict[str, list] = {}
    for issue in all_issues:
        by_file.setdefault(issue["file"], []).append(issue)

    total = len(all_issues)
    print(f"❌  {total} style violation(s) found:\n")
    for fname, issues in by_file.items():
        print(f"  {fname} ({len(issues)} issues)")
        for i in issues:
            print(f"    L{i['line']:4d}  [{i['rule']}]  {i['desc']}")
            print(f"           {i['text']}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
