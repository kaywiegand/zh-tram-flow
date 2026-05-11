"""
utils.py
--------
Allgemeine Hilfsfunktionen:
  - Timer / Decorator
  - Datei-Helfer
  - Logging-Shortcut
"""

import time
import logging
from pathlib import Path
from functools import wraps

logger = logging.getLogger(__name__)


def timer(func):
    """Decorator: misst und loggt die Laufzeit einer Funktion."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} abgeschlossen in {elapsed:.2f}s")
        return result
    return wrapper


def ensure_dir(path: Path) -> Path:
    """Erstellt Verzeichnis, falls nicht vorhanden. Gibt Pfad zurück."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_files(directory: Path, pattern: str = "*") -> list[Path]:
    """Gibt alle Dateien in einem Verzeichnis zurück, die dem Muster entsprechen."""
    return sorted(Path(directory).glob(pattern))
