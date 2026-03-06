"""
Chart hint inference from result DataFrame shape.
Pure Python logic, no LLM needed.
"""

import pandas as pd


def infer_chart_hint(df: pd.DataFrame) -> dict | None:
    """
    Inspect result DataFrame and return a chart_hint dict.

    Returns None if no chart is appropriate.

    Possible types: "bar", "line", "doughnut", "kpi", "table"
    """
    if df is None or df.empty:
        return None

    num_rows, num_cols = df.shape
    col_names = list(df.columns)
    col_dtypes = [str(df[c].dtype) for c in col_names]

    numeric_cols = [c for c, d in zip(col_names, col_dtypes) if "int" in d or "float" in d]
    date_like_cols = [c for c in col_names if "date" in c.lower() or "month" in c.lower() or "year" in c.lower()]
    text_cols = [c for c in col_names if c not in numeric_cols]

    # Single number result -> KPI
    if num_rows == 1 and num_cols == 1 and numeric_cols:
        return {"type": "kpi", "x_column": None, "y_column": numeric_cols[0]}

    # 5+ columns -> table
    if num_cols >= 5:
        return {"type": "table", "x_column": None, "y_column": None}

    # 1 date-like column + 1 numeric -> line
    if len(date_like_cols) == 1 and len(numeric_cols) == 1:
        return {
            "type": "line",
            "x_column": date_like_cols[0],
            "y_column": numeric_cols[0],
        }

    # 1 categorical + 1 numeric -> bar
    if len(text_cols) >= 1 and len(numeric_cols) == 1:
        # Check if the numeric column looks like a percentage
        col = numeric_cols[0]
        if "share" in col.lower() or "pct" in col.lower() or "percent" in col.lower():
            return {"type": "doughnut", "x_column": text_cols[0], "y_column": col}
        return {"type": "bar", "x_column": text_cols[0], "y_column": col}

    return {"type": "table", "x_column": None, "y_column": None}
