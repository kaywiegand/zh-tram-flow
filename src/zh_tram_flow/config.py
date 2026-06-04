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


# ─── Stadtkreis-Identitätsfarben ───────────────────────────────────────────
# Feste Identitätsfarbe pro Stadtkreis — gleiche Hues wie Tableau-10,
# auf ~30% Sättigung entsättigt damit sie nicht mit den Tramlinien konkurrieren.
# Verwendung: DISTRICT_COLORS["3"] → "#c08888"
# district_color() gibt für unbekannte Kreise einen Fallback zurück.

DISTRICT_COLORS: dict[str, str] = {
    "1":  "#8fa8be",   # Stahlblau
    "2":  "#c8a882",   # Sand
    "3":  "#c08888",   # Altrosa
    "4":  "#8ab0ae",   # Grau-Teal
    "5":  "#82a87e",   # Salbei
    "6":  "#c4b87a",   # Khaki
    "7":  "#a88fa6",   # Mauve
    "8":  "#c8adb0",   # Puder
    "9":  "#a08878",   # Warmgrau
    "10": "#b5b0ac",   # Kiesel
    "11": "#8aa885",   # Olive
    "12": "#b8a87a",   # Tan
}

def district_color(nr: int | str, fallback: str = "#b5b0ac") -> str:
    """Gibt die Identitätsfarbe für einen Stadtkreis zurück."""
    return DISTRICT_COLORS.get(str(int(nr)), fallback)

def district_colors(nrs: list[int | str], fallback: str = "#b5b0ac") -> list[str]:
    """Gibt eine Liste von Identitätsfarben für mehrere Stadtkreise zurück."""
    return [district_color(nr, fallback) for nr in nrs]


# ─── Semantische Analyse-Farben ────────────────────────────────────────────

# Delay / Target — DIE Farbe für arrival_delay, überall gleich.
# Gilt für Histogramme, Zeitreihen, OTP-Balken und ML-Outputs.
DELAY_COLOR:     str = "#E67E22"   # Amber-Orange
ARRIVAL_COLOR:   str = DELAY_COLOR  # arrival_delay IS der Delay → gleiche Farbe
DEPARTURE_COLOR: str = "#5b9eb8"   # kühles Blau — kontrastiert mit Amber

# OTP — Traffic Light (OTP_LATE bewusst = DELAY_COLOR: Verspätung ist Verspätung)
OTP_ON_TIME:  str = "#27ae60"   # grün   ≤ 120s  pünktlich
OTP_LATE:     str = "#E67E22"   # amber  120–300s leicht verspätet  (= DELAY_COLOR)
OTP_CRITICAL: str = "#e74c3c"   # rot    > 300s   stark verspätet

# Wetter-Kontexte — für Vergleichs-Plots Normal / Regen / Starkregen / Schnee
WEATHER_COLORS: dict[str, str] = {
    "normal":      "#8c8c8c",   # grau        Baseline / kein Niederschlag
    "rain":        "#92c5de",   # hell-blau   leichter Regen
    "heavy_rain":  "#4393c3",   # mittel-blau Starkregen
    "snow":        "#2166ac",   # dunkel-blau Schnee
}

# Event-Kontexte — Feiertag positiv (teal), Gross negativ (rot)
EVENT_COLORS: dict[str, str] = {
    "normal":   "#8c8c8c",   # grau   Baseline / kein Event
    "holiday":  "#25ac82",   # teal   Feiertag  (weniger Delay → positiv)
    "small":    "#f1c40f",   # gelb   kleines Event
    "medium":   "#E67E22",   # amber  mittleres Event  (= DELAY_COLOR)
    "large":    "#e74c3c",   # rot    grosses Event
}

# Vergleich Baseline vs. Modell / Vorher vs. Nachher
COMPARE_BASE:  str = "#95a5a6"   # grau   Baseline / Status Quo
COMPARE_MODEL: str = "#27ae60"   # grün   Modell / Verbesserung

# ─── Jahr-Farben ──────────────────────────────────────────────────────────
# Sequenziell (hell → dunkel = alt → neu). Neutral blau-grau, konkurriert
# nicht mit Linien- oder Delay-Farben.
YEAR_COLORS: dict[str, str] = {
    "2023": "#a8bfd4",   # hell stahlblau — ältestes Jahr
    "2024": "#5b8faa",   # mittelblau
    "2025": "#1e4d6b",   # dunkelblau — aktuellstes Jahr
}

# ─── Jahreszeiten-Farben ───────────────────────────────────────────────────
SEASON_COLORS: dict[str, str] = {
    "Frühling": "#5a9e6f",   # grün
    "Sommer":   "#c8a230",   # gold
    "Herbst":   "#b85c38",   # rost
    "Winter":   "#4a7fa5",   # kühlblau
}

# ─── Balken-Neutral ────────────────────────────────────────────────────────
# Für Balken ohne semantische Bedeutung — unterhalb Durchschnitt / nicht hervorgehoben.
# "Über Durchschnitt" → DELAY_COLOR
BAR_NEUTRAL: str = "#b8b8b8"

# ─── Einheitliche Delay-Farbskala für Maps / Heatmaps ─────────────────────
# grün (gut) → amber (mittel) → rot (schlecht)
DELAY_COLORSCALE: list = [[0.0, "#25ac82"], [0.5, "#ffa600"], [1.0, "#de425b"]]

# ─── Annotation-Overrides ──────────────────────────────────────────────────
# Projektweite Überschreibung der wgnd-Defaults.
# Beide Annotation-Linien in derselben dunklen Anthrazit-Familie:
#   Mean   → gepunktet  (:)
#   Median → gestrichelt (--)
# Farbe identisch, Linienstil unterscheidet sie.
ANNO_MEAN:   str = "#555555"   # dunkles Anthrazit, gepunktet — Mittelwert-Linie
ANNO_MEDIAN: str = "#555555"   # dunkles Anthrazit, gestrichelt — Median-Linie


# ─── Auto-Export Decorator ─────────────────────────────────────────────────
# Jede Plot-Funktion speichert automatisch nach PATHS["figures"].
# Kein separater Export-Block in Notebooks nötig.
#
# matplotlib-Funktionen (haben save_as-Parameter):
#   @auto_export("stem") → speichert plt.gcf() nach dem Aufruf als PNG.
#   Export überspringen:    plot_xyz(..., save_as=None)
#
# Plotly-Funktionen (geben fig zurück):
#   @auto_export("stem") → speichert nach dem Aufruf .html + .png (via kaleido).
#   Export überspringen:    plot_xyz(..., save_as=None)

import inspect as _inspect
from functools import wraps as _wraps


def auto_export(stem: str):
    """Decorator: auto-saves plot to PATHS['figures'] on every call.

    matplotlib (function returns None / calls plt.show()):
        After call, saves plt.gcf() as PNG. Pass save_as=None to skip.

    Plotly (function returns go.Figure):
        After call, writes .html (CDN) + .png (kaleido, silent fallback).
        Pass save_as=None to skip.
    """
    def decorator(func):
        _fig_path = PATHS["figures"] / stem

        @_wraps(func)
        def wrapper(*args, **kwargs):
            import matplotlib.pyplot as _plt
            save_target = kwargs.pop("save_as", _fig_path)

            # Patch plt.show so we can save before the figure is cleared
            _saved = [False]
            _original_show = _plt.show

            def _saving_show(*a, **kw):
                if save_target is not None and not _saved[0]:
                    _saved[0] = True
                    p2 = Path(save_target)
                    PATHS["figures"].mkdir(parents=True, exist_ok=True)
                    try:
                        _plt.gcf().savefig(
                            str(p2.with_suffix(".png")), dpi=150, bbox_inches="tight"
                        )
                    except Exception:
                        pass
                _original_show(*a, **kw)

            _plt.show = _saving_show
            try:
                result = func(*args, **kwargs)
            finally:
                _plt.show = _original_show

            if save_target is None:
                return result

            PATHS["figures"].mkdir(parents=True, exist_ok=True)
            p = Path(save_target)

            # Plotly: result is a Figure object with write_html
            if result is not None and hasattr(result, "write_html"):
                html_out = p.parent / f"{p.stem}.html"
                png_out  = p.parent / f"{p.stem}.png"
                try:
                    result.write_html(str(html_out), include_plotlyjs="cdn")
                except Exception:
                    pass
                try:
                    result.write_image(str(png_out), scale=2)
                except Exception:
                    pass
            return result
        return wrapper
    return decorator
