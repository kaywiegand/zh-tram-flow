#!/usr/bin/env python3
"""
Convert storyline JSON files to readable Markdown format.
Transforms presentation structures into digestible markdown documents.
"""

import json
import sys
from pathlib import Path


def extract_figures(items):
    """Extract figures section into markdown bullet points."""
    lines = []
    for item in items:
        value = item.get("value", "")
        label = item.get("label", "")
        lines.append(f"* **{value}** — {label}")
    return lines


def extract_agenda(content_item):
    """Extract agenda items into numbered list."""
    lines = []
    items = content_item.get("items", [])

    # Check if it's a grouped agenda
    if content_item.get("grouped"):
        for group in items:
            section = group.get("section", "")
            slides = group.get("slides", [])
            if section:
                lines.append(f"* **{section}**")
                for slide in slides:
                    lines.append(f"  - {slide}")
    else:
        # Simple agenda
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item}")

    return lines


def extract_sections(items):
    """Extract sections with points into markdown."""
    lines = []
    for item in items:
        label = item.get("label", "")
        points = item.get("points", [])
        if label:
            lines.append(f"* **{label}**")
            for point in points:
                lines.append(f"  - {point}")
    return lines


def extract_figures_with_context(items):
    """Extract figures with context into structured format."""
    lines = []
    for item in items:
        value = item.get("value", "")
        label = item.get("label", "")
        context = item.get("context", "")

        lines.append(f"* **{value}** — {label}")
        if context:
            lines.append(f"  - {context}")
    return lines


def extract_statement(text):
    """Extract statement as blockquote."""
    lines = [f"> {text}"]
    return lines


def extract_contrast(items):
    """Extract contrast items."""
    lines = []
    for item in items:
        label = item.get("label", "")
        points = item.get("points", [])
        if label:
            lines.append(f"* **{label}**")
            for point in points:
                lines.append(f"  - {point}")
    return lines


def process_content(content_list):
    """Process content array into markdown lines."""
    lines = []

    for content in content_list:
        content_type = content.get("type", "")

        if content_type == "figures":
            lines.extend(extract_figures(content.get("items", [])))

        elif content_type == "agenda":
            lines.extend(extract_agenda(content))

        elif content_type == "sections":
            lines.extend(extract_sections(content.get("items", [])))

        elif content_type == "figures_with_context":
            lines.extend(extract_figures_with_context(content.get("items", [])))

        elif content_type == "statement":
            lines.extend(extract_statement(content.get("text", "")))

        elif content_type == "contrasts":
            lines.extend(extract_contrast(content.get("items", [])))

        elif content_type == "text":
            text = content.get("text", "")
            if text:
                lines.append(text)

    return lines


def slide_to_markdown(slide):
    """Convert a single slide to markdown lines."""
    lines = []

    title = slide.get("title", "")
    subtitle = slide.get("subtitle", "")
    role = slide.get("role", "")

    # Title slide special handling
    if role == "title":
        lines.append(f"# {title}\n")
        if isinstance(subtitle, list):
            for s in subtitle:
                lines.append(f"**{s}**")
        else:
            lines.append(f"**{subtitle}**")
        lines.append("")
    else:
        # Regular slide
        if title:
            lines.append(f"## {title}")
        if subtitle:
            lines.append(f"*{subtitle}*")
        lines.append("")

    # Process content
    content = slide.get("content", [])
    content_lines = process_content(content)
    lines.extend(content_lines)

    lines.append("")
    return lines


def chapter_to_markdown(chapter):
    """Convert a chapter to markdown lines."""
    lines = []

    nav_label = chapter.get("nav_label", "")
    if nav_label:
        lines.append(f"\n---\n")
        lines.append(f"### {nav_label}\n")

    slides = chapter.get("slides", [])
    for slide in slides:
        slide_lines = slide_to_markdown(slide)
        lines.extend(slide_lines)

    return lines


def json_to_markdown(json_path, output_path):
    """Convert JSON presentation structure to markdown."""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lines = []
    meta = data.get("meta", {})

    # Header section
    lines.append(f"# {meta.get('project', 'Project')}")
    lines.append("")
    lines.append(f"**Projekt:** {meta.get('project', 'N/A')}")
    lines.append(f"**Beschreibung:** {meta.get('presentation_title', 'N/A')}")
    lines.append(f"**Autor:** {meta.get('author', 'N/A')}")
    lines.append(f"**Zielgruppe:** {meta.get('audience', 'N/A')}")
    lines.append(f"**Dauer:** {meta.get('duration_minutes', 'N/A')} Minuten")
    lines.append(f"**Zeitraum:** {meta.get('period', 'N/A')}")
    lines.append(f"**GitHub:** [{meta.get('github', 'N/A')}](https://github.com/{meta.get('github', '')})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Process chapters
    chapters = data.get("chapters", [])
    for chapter in chapters:
        chapter_lines = chapter_to_markdown(chapter)
        lines.extend(chapter_lines)

    # Write output
    markdown_content = "\n".join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"✓ Created: {output_path}")
    return output_path


def main():
    """Convert all storyline JSON files to markdown."""

    base_dir = Path("/Users/kaywiegand/Workspace/zh-tram-flow")
    json_dir = base_dir / "public" / "json"
    md_dir = base_dir / "public" / "md"

    # Ensure md directory exists
    md_dir.mkdir(parents=True, exist_ok=True)

    # Files to convert
    files = [
        ("overview", "overview.md"),
        ("storyview", "storyview.md"),
        ("techview", "techview.md"),
    ]

    for json_name, md_name in files:
        json_path = json_dir / f"storyline-{json_name}.json"
        md_path = md_dir / md_name

        if json_path.exists():
            json_to_markdown(json_path, md_path)
        else:
            print(f"✗ Not found: {json_path}")

    print("\n✓ All conversions complete!")


if __name__ == "__main__":
    main()
