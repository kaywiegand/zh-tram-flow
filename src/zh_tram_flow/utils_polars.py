"""
polars_utils.py
Dieses Modul enthält Hilfsfunktionen für die effiziente EDA mit Polars,
speziell optimiert für große Datensätze (88 Mio.+ Zeilen).
"""

import polars as pl

def get_categorical_stats(df_or_lf):
    """
    Erzeugt eine detaillierte Übersicht über kategoriale Spalten inkl. Top-Values.
    
    Parameter:
    df_or_lf (pl.DataFrame | pl.LazyFrame): Der zu analysierende Datensatz.
    
    Rückgabe:
    pl.DataFrame: Eine Tabelle mit missing_pct, unique_counts und top_values.
    """
    # ... hier kommt der Code der Funktion rein, den wir zuvor entwickelt haben ...
    
    # Identifiziere, ob wir Lazy oder Eager arbeiten
    is_lazy = isinstance(df_or_lf, pl.LazyFrame)
    lf = df_or_lf if is_lazy else df_or_lf.lazy()
    
    total_rows = lf.select(pl.len()).collect().item()
    cat_cols = [s for s, dtype in lf.collect_schema().items() 
                if dtype in [pl.String, pl.Boolean, pl.Categorical]]

    if not cat_cols:
        return pl.DataFrame({"info": ["Keine kategorialen Spalten gefunden."]})

    # Aggregations-Logik
    exprs = []
    for col in cat_cols:
        exprs.extend([
            pl.col(col).null_count().alias(f"{col}_missing_cnt"),
            pl.col(col).n_unique().alias(f"{col}_unique"),
            pl.col(col).mode().first().cast(pl.String).alias(f"{col}_top_value"),
            pl.col(col).filter(pl.col(col) == pl.col(col).mode().first()).count().alias(f"{col}_top_value_cnt")
        ])

    res = lf.select(exprs).collect()

    # Transformation in das Zielformat (Pivot/Unpivot)

    # --- Korrigierte Transformation in utils_polars.py ---

    summary = (
        res.unpivot()
        .with_columns([
            # Wir extrahieren den Teil VOR dem Suffix und das Suffix selbst
            # Regex Erklärung: 
            # (.*) -> Gruppe 1: Alles bis zum...
            # _(missing_cnt|unique|top_value|top_value_cnt) -> ...letzten passenden Suffix
            pl.col("variable")
            .str.extract(r"(.*)_(missing_cnt|unique|top_value|top_value_cnt)$", 1)
            .alias("column"),
            
            pl.col("variable")
            .str.extract(r"(.*)_(missing_cnt|unique|top_value|top_value_cnt)$", 2)
            .alias("stat")
        ])
        .pivot(index="column", on="stat", values="value")
    )
    
    return summary