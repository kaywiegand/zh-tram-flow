#!/usr/bin/env python3
"""
Archiviert den aktuellen Stand der Portfolio-Artefakte VOR einem Regenerierungs-Lauf.

Snapshot der kanonischen Outputs → public/archive/vN/ (N = nächste freie Nummer).
Danach überschreiben die Generatoren die kanonischen Dateien gefahrlos:
stabile Namen bleiben (index.html, overview.html, …), die Historie liegt im Archiv.

Wird VOR generate_json/html/index aufgerufen (sonst ist der Vor-Lauf-Stand schon weg).
Run:  python scripts/archive_portfolio_artifacts.py
"""

import shutil
import re
from pathlib import Path

BASE    = Path(__file__).parent.parent
PUBLIC  = BASE / "public"
ARCHIVE = PUBLIC / "archive"

# Kanonische Artefakte, die ein Lauf überschreibt (relativ zu public/).
ARTIFACTS = [
    "index.html",
    "overview.html",
    "storyview.html",
    "techview.html",
    "json/storyline-overview.json",
    "json/storyline-storyview.json",
    "json/storyline-techview.json",
    "md/overview.md",
    "md/storyview.md",
    "md/techview.md",
]


def next_version() -> int:
    if not ARCHIVE.exists():
        return 1
    nums = [
        int(m.group(1))
        for d in ARCHIVE.iterdir()
        if d.is_dir() and (m := re.fullmatch(r"v(\d+)", d.name))
    ]
    return max(nums, default=0) + 1


def main() -> None:
    existing = [rel for rel in ARTIFACTS if (PUBLIC / rel).exists()]
    if not existing:
        print("ℹ️  Keine bestehenden Artefakte — nichts zu archivieren (erster Lauf).")
        return

    n = next_version()
    dest_root = ARCHIVE / f"v{n}"
    for rel in existing:
        src = PUBLIC / rel
        dst = dest_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    print(f"📦 Archiviert: {len(existing)} Dateien → public/archive/v{n}/")
    for rel in existing:
        print(f"   • {rel}")


if __name__ == "__main__":
    main()
