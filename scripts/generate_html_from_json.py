#!/usr/bin/env python3
"""
Generate reveal.js HTML presentations from storyline JSON files.

Input:  public/json/storyline-*.json
Output: public/{overview,storyview,techview,socialview}.html

Generates Reveal.js-based HTML slides with CSS styling from template.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_slides_template(path: Path) -> str:
    """Load reveal.js template HTML."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def render_content_item(item: Dict[str, Any]) -> str:
    """Render a single content item based on type."""
    item_type = item.get("type", "")

    if item_type == "figures":
        items = item.get("items", [])
        lines = ['<div class="figures">']
        for fig in items:
            value = fig.get("value", "")
            label = fig.get("label", "")
            sentiment = fig.get("sentiment", "neutral")
            lines.append(f'<div class="figure {sentiment}">')
            lines.append(f'<div class="value">{value}</div>')
            lines.append(f'<div class="label">{label}</div>')
            lines.append('</div>')
        lines.append('</div>')
        return "\n".join(lines)

    elif item_type == "agenda":
        items = item.get("items", [])
        if item.get("grouped"):
            html = '<ul class="agenda grouped">'
            for group in items:
                section = group.get("section", "")
                slides = group.get("slides", [])
                html += f'<li><strong>{section}</strong><ul>'
                for slide in slides:
                    html += f'<li>{slide}</li>'
                html += '</ul></li>'
            html += '</ul>'
            return html
        else:
            html = '<ol class="agenda">'
            for item in items:
                html += f'<li>{item}</li>'
            html += '</ol>'
            return html

    elif item_type == "sections":
        items = item.get("items", [])
        html = '<div class="sections">'
        for sec in items:
            label = sec.get("label", "")
            points = sec.get("points", [])
            html += f'<div class="section"><strong>{label}</strong><ul>'
            for point in points:
                html += f'<li>{point}</li>'
            html += '</ul></div>'
        html += '</div>'
        return html

    elif item_type == "figures_with_context":
        items = item.get("items", [])
        html = '<div class="figures-with-context">'
        for fig in items:
            value = fig.get("value", "")
            label = fig.get("label", "")
            context = fig.get("context", "")
            html += f'<div class="figure-item">'
            html += f'<div class="figure-value">{value}</div>'
            html += f'<div class="figure-label">{label}</div>'
            if context:
                html += f'<div class="figure-context">{context}</div>'
            html += '</div>'
        html += '</div>'
        return html

    elif item_type == "statement":
        text = item.get("text", "")
        return f'<blockquote class="statement">{text}</blockquote>'

    elif item_type == "contrasts":
        items = item.get("items", [])
        html = '<div class="contrasts">'
        for contrast in items:
            assumption = contrast.get("assumption", "")
            finding = contrast.get("finding", "")
            html += f'<div class="contrast">'
            html += f'<div class="assumption"><em>Annahme:</em> {assumption}</div>'
            html += f'<div class="finding"><strong>Befund:</strong> {finding}</div>'
            html += '</div>'
        html += '</div>'
        return html

    elif item_type == "steps":
        items = item.get("items", [])
        html = '<div class="steps">'
        for step in items:
            step_num = step.get("step", "")
            label = step.get("label", "")
            detail = step.get("detail", "")
            html += f'<div class="step"><strong>Schritt {step_num}:</strong> {label}'
            if detail:
                html += f'<br><small>{detail}</small>'
            html += '</div>'
        html += '</div>'
        return html

    elif item_type == "chart_refs":
        items = item.get("items", [])
        html = '<div class="chart-refs">'
        for chart in items:
            label = chart.get("label", "")
            source = chart.get("source", "")
            caption = chart.get("caption", "")
            html += f'<div class="chart-ref">'
            html += f'<div class="chart-label">{label}</div>'
            html += f'<div class="chart-image" data-src="../img/{source}"></div>'
            if caption:
                html += f'<div class="chart-caption">{caption}</div>'
            html += '</div>'
        html += '</div>'
        return html

    else:
        # Fallback for unknown types
        return f'<p><em>Unknown content type: {item_type}</em></p>'


def render_slide(slide: Dict[str, Any]) -> str:
    """Render a single slide as HTML."""
    role = slide.get("role", "standard")
    title = slide.get("title", "")
    subtitle = slide.get("subtitle", "")
    content = slide.get("content", [])

    if role == "title":
        # Title slide
        html = f'<section class="title-slide">'
        html += f'<h1>{title}</h1>'
        if isinstance(subtitle, list):
            for sub in subtitle:
                html += f'<p class="subtitle">{sub}</p>'
        else:
            html += f'<p class="subtitle">{subtitle}</p>'
        for item in content:
            html += render_content_item(item)
        html += '</section>'
    else:
        # Regular slide
        html = f'<section>'
        if title:
            html += f'<h2>{title}</h2>'
        if subtitle:
            html += f'<p class="subline">{subtitle}</p>'
        for item in content:
            html += render_content_item(item)
        html += '</section>'

    return html


def render_chapter(chapter: Dict[str, Any]) -> str:
    """Render a chapter (section group) in reveal.js format."""
    nav_label = chapter.get("nav_label", "")
    slides = chapter.get("slides", [])

    # Wrap slides in a section for chapter grouping
    html = f'<!-- Chapter: {nav_label} -->\n<section>'
    for slide in slides:
        html += render_slide(slide)
    html += '</section>'

    return html


def build_html(json_data: Dict[str, Any], template: str) -> str:
    """Build complete HTML presentation from JSON."""
    meta = json_data.get("meta", {})
    chapters = json_data.get("chapters", [])

    # Render all chapters
    slides_html = ""
    for chapter in chapters:
        slides_html += render_chapter(chapter)

    # Replace placeholder in template
    html = template.replace("<!-- SLIDES_PLACEHOLDER -->", slides_html)

    # Update meta information in HTML
    html = html.replace("{{ PROJECT_TITLE }}", meta.get("project", "Project"))
    html = html.replace("{{ PRESENTATION_TITLE }}", meta.get("presentation_title", ""))
    html = html.replace("{{ AUDIENCE }}", meta.get("audience", ""))
    html = html.replace("{{ DURATION }}", str(meta.get("duration_minutes", "")))
    html = html.replace("{{ AUTHOR }}", meta.get("author", ""))
    html = html.replace("{{ GITHUB }}", meta.get("github", ""))

    return html


def save_html(path: Path, content: str) -> None:
    """Save HTML to file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Wrote: {path}")


def main():
    """Main execution."""
    base_path = Path(__file__).parent.parent
    json_dir = base_path / "public" / "json"
    output_dir = base_path / "public"
    template_path = base_path / ".." / "docs" / "portfolio" / "templates" / "slides-template.html"

    print("Loading template...")
    if not template_path.exists():
        print(f"⚠️  Template not found: {template_path}")
        # Use the slides-template.html from the workspace docs
        workspace_template = Path("/Users/kaywiegand/Workspace/docs/portfolio/templates/slides-template.html")
        if workspace_template.exists():
            template = load_slides_template(workspace_template)
            print(f"✅ Loaded workspace template: {workspace_template}")
        else:
            print("Using fallback template (basic reveal.js)")
            template = get_fallback_template()
    else:
        template = load_slides_template(template_path)
        print(f"✅ Loaded template: {template_path}")

    # Generate HTML for each view
    views = ["overview", "storyview", "techview", "socialview"]

    for view in views:
        json_path = json_dir / f"storyline-{view}.json"
        html_path = output_dir / f"{view}.html"

        print(f"\n📊 Generating {view}...")

        if not json_path.exists():
            print(f"  ⚠️  JSON file not found: {json_path}, skipping")
            continue

        # Load JSON
        json_data = load_json(json_path)
        print(f"  → Loaded JSON: {json_path}")

        # Build HTML
        html_content = build_html(json_data, template)
        print(f"  → Built HTML presentation")

        # Save
        save_html(html_path, html_content)

    print("\n" + "="*60)
    print("✅ HTML generation complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Open generated HTML files in browser")
    print("  2. Compare with html-backup/ visually")
    print("  3. Run: python scripts/convert_json_to_md.py")


def get_fallback_template() -> str:
    """Return a minimal reveal.js template."""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ PROJECT_TITLE }} — {{ PRESENTATION_TITLE }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/theme/black.min.css">
    <style>
        .reveal h1, .reveal h2, .reveal h3 { text-transform: none; }
        .figures { display: flex; gap: 1em; flex-wrap: wrap; }
        .figure { text-align: center; }
        .figure.positive { color: #27ae60; }
        .figure.negative { color: #e74c3c; }
        .figure.warning { color: #f39c12; }
        .value { font-size: 2em; font-weight: bold; }
        .label { font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            <!-- SLIDES_PLACEHOLDER -->
        </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/reveal.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.5.0/plugin/notes/notes.min.js"></script>
    <script>
        Reveal.initialize({
            hash: true,
            center: true,
            transition: 'slide',
            plugins: [RevealNotes]
        });
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
