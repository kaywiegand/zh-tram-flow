"""
test_features.py
----------------
Tests für Feature Engineering.
"""

import pytest
import pandas as pd
from zh_tram_flow.features.build_features import add_date_features


def test_add_date_features_creates_columns():
    df = pd.DataFrame({"date": ["2024-01-15", "2024-06-30"]})
    result = add_date_features(df, "date")
    assert "date_year" in result.columns
    assert "date_month" in result.columns
    assert "date_dow" in result.columns


def test_add_date_features_correct_values():
    df = pd.DataFrame({"date": ["2024-01-15"]})
    result = add_date_features(df, "date")
    assert result["date_year"].iloc[0] == 2024
    assert result["date_month"].iloc[0] == 1
