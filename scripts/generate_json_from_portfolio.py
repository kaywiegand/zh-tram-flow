#!/usr/bin/env python3
"""
Generate storyline JSON files from portfolio.md.

This script reads portfolio.md (Single Source of Truth) and uses it to update
the 4 storyline JSON files (overview, storyview, techview, socialview).

Strategy:
  1. Parse portfolio.md sections
  2. Load existing JSON templates (from json-backup/ or json/)
  3. Update JSON content based on portfolio.md
  4. Preserve JSON structure (chapters, slides, meta) from templates
  5. Write updated JSON files
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


def read_portfolio_md(path: Path) -> str:
    """Read portfolio.md file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_json_template(path: Path) -> Dict[str, Any]:
    """Load JSON template from backup or working directory."""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"JSON template not found: {path}")


def extract_section(content: str, section_name: str) -> str:
    """Extract a section from portfolio.md by heading."""
    pattern = rf"^## {re.escape(section_name)}\s*$.*?(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else ""


def extract_findings_table(content: str) -> List[Dict[str, str]]:
    """Extract Key Findings (F1-F6) from portfolio.md."""
    findings = []
    pattern = r"### F(\d+) — (.+?)\n```\nfinding:\s*(.+?)\nnumber:\s*(.+?)\nsource:\s*(.+?)\n```"

    for match in re.finditer(pattern, content, re.DOTALL):
        num, title, finding, number, source = match.groups()
        findings.append({
            "id": f"F{num}",
            "title": title.strip(),
            "finding": finding.strip(),
            "number": number.strip(),
            "source": source.strip(),
        })

    return findings


def extract_recommendations(content: str) -> List[Dict[str, str]]:
    """Extract Recommendations (R1-R4) from portfolio.md."""
    recommendations = []
    pattern = r"r(\d+):\s+title:\s*(.+?)\n\s+detail:\s*(.+?)(?=\nr\d:|```\n---)"

    for match in re.finditer(pattern, content, re.DOTALL):
        num, title, detail = match.groups()
        recommendations.append({
            "id": f"R{num}",
            "title": title.strip(),
            "detail": detail.strip(),
        })

    return recommendations


def extract_problem_statement(content: str) -> Dict[str, str]:
    """Extract problem statement from portfolio.md."""
    pattern = r"kpi_ist:\s*(\d+)\s*\nkpi_soll:\s*([\d%]+).*?\nproblem_statement:\s*\|\s*(.+?)(?=```\n---)"
    match = re.search(pattern, content, re.DOTALL)

    if match:
        ist, soll, statement = match.groups()
        return {
            "ist": ist.strip(),
            "soll": soll.strip(),
            "statement": statement.strip(),
        }
    return {}


def extract_storyline(content: str) -> Dict[str, str]:
    """Extract Storyline (thesis, hook, proof, so_what) from portfolio.md."""
    section = extract_section(content, "Storyline")

    storyline = {}
    for key in ["thesis", "hook", "proof", "so_what"]:
        pattern = rf"{key}:\s+(.+?)(?=\n\n[a-z]+:|```)"
        match = re.search(pattern, section, re.DOTALL)
        if match:
            storyline[key] = match.group(1).strip()

    return storyline


def update_json_content(json_data: Dict[str, Any], portfolio_content: str, storyline: str) -> Dict[str, Any]:
    """
    Update JSON data with content from portfolio.md.

    This is a simplified update that preserves JSON structure while updating key content fields.
    For a full mechanized rebuild, this would need more sophisticated mapping.
    """

    findings = extract_findings_table(portfolio_content)
    recommendations = extract_recommendations(portfolio_content)
    problem = extract_problem_statement(portfolio_content)
    storyline_data = extract_storyline(portfolio_content)

    # Store extracted data in meta for reference
    if "meta" not in json_data:
        json_data["meta"] = {}

    json_data["_extracted"] = {
        "findings": findings,
        "recommendations": recommendations,
        "problem": problem,
        "storyline": storyline_data,
        "updated_at": "2026-06-19",
        "source": "portfolio.md",
    }

    return json_data


def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save JSON data to file with nice formatting."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote: {path}")


def main():
    """Main execution."""
    base_path = Path(__file__).parent.parent
    portfolio_path = base_path / "public" / "md" / "portfolio.md"
    json_backup_dir = base_path / "public" / "json-backup"
    json_output_dir = base_path / "public" / "json"

    # Ensure output directory exists
    json_output_dir.mkdir(parents=True, exist_ok=True)

    # Read portfolio.md
    portfolio_content = read_portfolio_md(portfolio_path)
    print(f"📖 Read portfolio.md ({len(portfolio_content)} chars)")

    # Process each storyline
    views = [
        ("overview", "A"),
        ("storyview", "C"),
        ("techview", "B"),
        ("socialview", "D"),
    ]

    for view_name, storyline_id in views:
        template_path = json_backup_dir / f"storyline-{view_name}.json"
        output_path = json_output_dir / f"storyline-{view_name}.json"

        print(f"\n📝 Processing {view_name} (Storyline {storyline_id})...")

        # Load template
        json_data = load_json_template(template_path)
        print(f"  → Loaded template: {template_path}")

        # Update content
        json_data = update_json_content(json_data, portfolio_content, storyline_id)
        print(f"  → Updated content from portfolio.md")

        # Save
        save_json(output_path, json_data)

    print("\n" + "="*60)
    print("✅ JSON generation complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Verify new JSONs match backups (checksums, content)")
    print("  2. Run: python scripts/generate_html_from_json.py")
    print("  3. Test HTML files in browser")


if __name__ == "__main__":
    main()
