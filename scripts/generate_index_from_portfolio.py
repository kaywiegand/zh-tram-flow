#!/usr/bin/env python3
"""
Generate public/index.html (Portfolio-Hub) from portfolio.md + index-template.html.

Input:   public/md/portfolio.md   (Project-Block: name, slug, period, dashboard)
         scripts/index-template.html  (Layout + kuratierte Hub-Copy, {{...}}-Platzhalter)
Output:  public/index.html

Dynamische Werte aus portfolio.md; Layout/Copy aus dem Template.
Run:     python scripts/generate_index_from_portfolio.py
"""

import re
import sys
from pathlib import Path

BASE          = Path(__file__).parent.parent
MD_PATH       = BASE / "public" / "md" / "portfolio.md"
TEMPLATE_PATH = BASE / "scripts" / "index-template.html"
OUT_PATH      = BASE / "public" / "index.html"

GITHUB_USER   = "kaywiegand"   # Workspace-Owner (stabil)


def parse_project(md_text: str) -> dict:
    """Read the fenced code block under '## Project' into a dict."""
    m = re.search(r"## Project\s*```(.*?)```", md_text, re.DOTALL)
    if not m:
        raise SystemExit("❌ '## Project'-Block in portfolio.md nicht gefunden.")
    result = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


def main() -> None:
    if not MD_PATH.exists():
        raise SystemExit(f"❌ {MD_PATH} nicht gefunden.")
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"❌ {TEMPLATE_PATH} nicht gefunden.")

    project = parse_project(MD_PATH.read_text(encoding="utf-8"))

    name   = project.get("name", "Portfolio Project")
    slug   = project.get("slug", "")
    period = project.get("period", "")
    dash   = project.get("dashboard", "").strip()

    repo_url = f"https://github.com/{GITHUB_USER}/{slug}" if slug else f"https://github.com/{GITHUB_USER}"
    user_url = f"https://github.com/{GITHUB_USER}"

    replacements = {
        "{{PROJECT_NAME}}":    name,
        "{{PERIOD}}":          period,
        "{{GITHUB_REPO_URL}}": repo_url,
        "{{GITHUB_USER_URL}}": user_url,
        "{{DASHBOARD_URL}}":   dash or repo_url,   # Fallback: Repo, falls kein Dashboard
    }

    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    for key, val in replacements.items():
        html = html.replace(key, val)

    leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftover:
        print(f"⚠️  Unersetzte Platzhalter: {sorted(set(leftover))}", file=sys.stderr)

    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"✅ Wrote: {OUT_PATH}")
    print(f"   name={name} · period={period} · dashboard={dash or '(Fallback: Repo)'}")


if __name__ == "__main__":
    main()
