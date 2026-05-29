"""
config.py
---------
Zentrale Projektkonfiguration: Pfade, Konstanten, Umgebungsvariablen.

Importiere dieses Modul in Notebooks oder Scripts:
    from zh_tram_flow.config import PATHS, PROJECT_NAME
"""

from pathlib import Path

# ─── Projektname ───────────────────────────────────────────────────────────
PROJECT_NAME = "Zürich Tram Flow"
RANDOM_SEED = 42

# ─── Verzeichnisse ─────────────────────────────────────────────────────────
# Basis ist das Verzeichnis, in dem config.py liegt → 2 Ebenen nach oben
_SRC = Path(__file__).resolve().parent.parent.parent

PATHS = {
    "root":      _SRC,
    "data":      _SRC / "data",
    "raw":       _SRC / "data" / "raw",
    "interim":   _SRC / "data" / "interim",
    "processed": _SRC / "data" / "processed",
    "models":    _SRC / "models",
    "reports":   _SRC / "reports",
    "figures":   _SRC / "reports" / "img",
    "configs":   _SRC / "configs",
}

# ─── Modell-Konstanten ──────────────────────────────────────────────────────
TEST_SIZE   = 0.2
VAL_SIZE    = 0.1
N_CV_FOLDS  = 5

# ─── VBZ Linienfarben ──────────────────────────────────────────────────────
# Offizielle Farben aus GTFS routes.txt (route_color), Stand j25 / 2025.
# Verwendung: LINE_COLORS["12"] → "#92D6E3"
# line_color() gibt für unbekannte Linien einen Fallback zurück.

LINE_COLORS: dict[str, str] = {
    "2":  "#E20A16",   # Rot
    "3":  "#00892F",   # Grün
    "4":  "#11296F",   # Dunkelblau
    "5":  "#734522",   # Braun
    "6":  "#CA7D3C",   # Orange
    "7":  "#000000",   # Schwarz
    "8":  "#8AB51F",   # Gelbgrün
    "9":  "#11296F",   # Dunkelblau
    "10": "#E12472",   # Pink
    "11": "#00892F",   # Grün
    "12": "#92D6E3",   # Hellblau
    "13": "#FFCC00",   # Gelb
    "14": "#008DC5",   # Blau
    "15": "#E20A16",   # Rot
    "17": "#8E224D",   # Dunkelrot
    "19": "#E20A16",   # Rot
    "E":  "#E20A16",   # Rot (Expresslinie)
}

LINE_TEXT_COLORS: dict[str, str] = {
    "2":  "#FFFFFF", "3":  "#FFFFFF", "4":  "#FFFFFF",
    "5":  "#FFFFFF", "6":  "#FFFFFF", "7":  "#FFFFFF",
    "8":  "#000000", "9":  "#FFFFFF", "10": "#FFFFFF",
    "11": "#FFFFFF", "12": "#000000", "13": "#000000",
    "14": "#FFFFFF", "15": "#FFFFFF", "17": "#FFFFFF",
    "19": "#FFFFFF", "E":  "#FFFFFF",
}

def line_color(line: str, fallback: str = "#8c8c8c") -> str:
    """Gibt die offizielle VBZ-Farbe für eine Liniennummer zurück."""
    return LINE_COLORS.get(str(line), fallback)

def line_colors(lines: list[str], fallback: str = "#8c8c8c") -> list[str]:
    """Gibt eine Liste offizieller VBZ-Farben für mehrere Linien zurück."""
    return [line_color(ln, fallback) for ln in lines]
