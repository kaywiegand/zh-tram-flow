"""
test_data.py
------------
Tests für Datenladen und Validierung.
Ausführen mit: pytest tests/
"""

import pytest
import pandas as pd
from zh_tram_flow.data.make_dataset import validate_dataframe, basic_clean


def test_validate_dataframe_passes():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert validate_dataframe(df, ["a", "b"]) is True


def test_validate_dataframe_raises_on_missing_col():
    df = pd.DataFrame({"a": [1, 2]})
    with pytest.raises(ValueError, match="Fehlende Spalten"):
        validate_dataframe(df, ["a", "missing_col"])


def test_basic_clean_removes_duplicates():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    cleaned = basic_clean(df)
    assert len(cleaned) == 2


def test_basic_clean_normalizes_columns():
    df = pd.DataFrame({"Col A": [1], "Col-B": [2]})
    cleaned = basic_clean(df)
    assert "col_a" in cleaned.columns
