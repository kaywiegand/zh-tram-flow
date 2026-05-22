"""
Extract standalone Plotly charts from insights.html (nbconvert export).

Each Plotly chart in the notebook HTML sits on one line as:
  <script src="cdn..."></script>
  <div class="plotly-graph-div" id="UUID" ...></div>
  <script>...Plotly.newPlot("UUID", ...)...</script>

This script wraps each block in a minimal HTML file and saves it to reports/figures/.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT = ROOT / "reports" / "insights.html"
OUTPUT_DIR = ROOT / "reports" / "figures"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #fff; overflow: hidden; }}
    .plotly-graph-div {{ width: 100vw !important; height: 100vh !important; }}
  </style>
</head>
<body>
  {content}
</body>
</html>"""

def extract_charts(html_path: Path) -> list[dict]:
    """Find all lines containing a Plotly chart block and extract them."""
    charts = []
    with open(html_path, encoding="utf-8") as f:
        for line in f:
            if "plotly-graph-div" not in line:
                continue
            # Extract chart UUID
            match = re.search(r'id="([0-9a-f-]{36})"', line)
            if not match:
                continue
            chart_id = match.group(1)

            # The full block is the entire line (CDN script + div + newPlot script)
            # Adjust height/width so it fills the iframe
            content = line.strip()
            content = re.sub(
                r'style="height:\d+px;\s*width:\d+%;"',
                'style="height:100vh; width:100vw;"',
                content,
            )
            charts.append({"id": chart_id, "content": content})
    return charts


def save_chart(chart: dict, name: str, output_dir: Path) -> Path:
    out_path = output_dir / f"{name}.html"
    html = HTML_TEMPLATE.format(title=name, content=chart["content"])
    out_path.write_text(html, encoding="utf-8")
    print(f"  ✅  {out_path.name}  ({out_path.stat().st_size // 1024} KB)")
    return out_path


def main():
    if not INPUT.exists():
        print(f"ERROR: {INPUT} not found", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Reading {INPUT.name} ...")
    charts = extract_charts(INPUT)

    if not charts:
        print("No Plotly charts found.")
        sys.exit(0)

    print(f"Found {len(charts)} Plotly chart(s):\n")

    names = [
        "plotly_chart_1",
        "plotly_chart_2",
        "plotly_chart_3",
        "plotly_chart_4",
        "plotly_chart_5",
    ]

    for i, chart in enumerate(charts):
        name = names[i] if i < len(names) else f"plotly_chart_{i+1}"
        save_chart(chart, name, OUTPUT_DIR)

    print(f"\nDone. Embed in presentation with:")
    for i in range(len(charts)):
        name = names[i] if i < len(names) else f"plotly_chart_{i+1}"
        print(f'  <iframe src="figures/{name}.html" style="width:100%; height:500px; border:none;"></iframe>')


if __name__ == "__main__":
    main()
