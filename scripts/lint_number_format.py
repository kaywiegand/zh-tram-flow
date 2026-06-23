#!/usr/bin/env python3
"""
Lint-Check: Prüfe ob JSON/Config-Dateien deutsches Zahlenformat enthalten.

REGEL:
  ✅ RICHTIG:  18.56  (Punkt in Datenquellen)
  ❌ FALSCH:   18,56  (Komma in Datenquellen)

Deutsch-Format ist NUR in Markdown/Portfolio erlaubt, nicht in JSON/Code.
"""

import json
import re
from pathlib import Path

def check_json_files():
    """Suche nach deutschem Zahlenformat in JSON-Dateien."""
    print("🔍 Checking JSON files for German number format...\n")

    json_files = list(Path(".").rglob("*.json"))
    issues = []

    for jf in sorted(json_files):
        if any(skip in str(jf) for skip in [".git", "__pycache__", ".venv", "node_modules"]):
            continue

        try:
            with open(jf) as f:
                content = f.read()
                # Suche nach Kommas in Zahlen: "\d+,\d+"
                matches = re.findall(r'"[^"]*":\s*[0-9.]*[0-9]+,[0-9]+', content)
                if matches:
                    issues.append((str(jf), matches))
        except Exception as e:
            pass

    if issues:
        print("❌ PROBLEME GEFUNDEN:\n")
        for file, matches in issues:
            print(f"  {file}")
            for match in matches[:3]:  # max 3 Beispiele
                print(f"    → {match}")
            print()
        return False
    else:
        print("✅ Alle JSON-Dateien OK (englisches Format)")
        return True

def check_python_files():
    """Suche nach deutschem Zahlenformat in Python-Code."""
    print("\n🔍 Checking Python files...\n")

    py_files = list(Path("src").rglob("*.py")) + list(Path("scripts").rglob("*.py"))
    issues = []

    for pf in sorted(py_files):
        if "__pycache__" in str(pf):
            continue

        try:
            with open(pf) as f:
                for i, line in enumerate(f, 1):
                    # Suche nach deutschem Format in Strings/Zahlen
                    if re.search(r"[0-9]+,[0-9]+\s*s", line) or \
                       re.search(r"['\"][0-9]+,[0-9]+['\"]", line):
                        issues.append((str(pf), i, line.strip()))
        except:
            pass

    if issues:
        print("❌ PROBLEME GEFUNDEN:\n")
        for file, line_no, line in issues[:5]:
            print(f"  {file}:{line_no}")
            print(f"    → {line[:80]}")
            print()
        return False
    else:
        print("✅ Alle Python-Dateien OK")
        return True

if __name__ == "__main__":
    ok1 = check_json_files()
    ok2 = check_python_files()

    if ok1 and ok2:
        print("\n✅ Lint-Check PASSED — alles OK")
        exit(0)
    else:
        print("\n❌ Lint-Check FAILED — deutsches Format in Datenquellen gefunden!")
        exit(1)
