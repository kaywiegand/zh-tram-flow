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
    "reports":   _SRC / "public",
    "figures":   _SRC / "public" / "img",
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


# ─── Auto-Export Decorator ─────────────────────────────────────────────────
# Jede Plot-Funktion speichert automatisch nach PATHS["figures"].
# Kein separater Export-Block in Notebooks nötig.
#
# matplotlib-Funktionen (haben save_as-Parameter):
#   @auto_export("stem.png") → injiziert PATHS["figures"]/stem.png als Default.
#   Explizit überschreiben: plot_xyz(..., save_as="/anderer/pfad.png")
#   Export überspringen:    plot_xyz(..., save_as=None)
#
# Plotly-Funktionen (kein save_as, geben fig zurück):
#   @auto_export("stem") → speichert nach dem Aufruf .html + .png (via kaleido).
#   Export überspringen:    plot_xyz(..., save_as=None)

import inspect as _inspect
from functools import wraps as _wraps


def auto_export(stem: str):
    """Decorator: auto-saves plot to PATHS['figures'] on every call.

    matplotlib (save_as param present):
        Injects PATHS['figures'] / f'{stem}.png' as default save_as.

    Plotly (no save_as param, function must return go.Figure):
        After call, writes .html (CDN) + .png (kaleido, silent fallback).

    Override:  pass save_as="/other/path.png"
    Skip:      pass save_as=None
    """
    def decorator(func):
        sig       = _inspect.signature(func)
        _is_mpl   = "save_as" in sig.parameters
        _fig_path = PATHS["figures"] / stem

        @_wraps(func)
        def wrapper(*args, **kwargs):
            if _is_mpl:
                # matplotlib: inject default path, function handles saving
                if "save_as" not in kwargs:
                    kwargs["save_as"] = _fig_path.with_suffix(".png")
                return func(*args, **kwargs)
            else:
                # Plotly: pop save_as (not a real param), call function, save result
                save_target = kwargs.pop("save_as", _fig_path)
                result = func(*args, **kwargs)
                if save_target is not None and result is not None:
                    p = Path(save_target)
                    PATHS["figures"].mkdir(parents=True, exist_ok=True)
                    html_out = p.parent / f"{p.stem}.html"
                    png_out  = p.parent / f"{p.stem}.png"
                    try:
                        result.write_html(str(html_out), include_plotlyjs="cdn")
                    except Exception:
                        pass
                    try:
                        result.write_image(str(png_out), scale=2)
                    except Exception:
                        pass  # kaleido not available
                return result
        return wrapper
    return decorator
