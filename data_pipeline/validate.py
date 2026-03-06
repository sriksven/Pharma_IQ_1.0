"""
Validates loaded table metadata. Logs warnings for bad files, does not crash.
"""

import pandas as pd
from ml_pipeline.monitoring.logger import JSONLogger

logger = JSONLogger()

REQUIRED_NUMERIC_TYPES = {"int64", "float64", "Int64", "Float64"}


def validate_table(meta: dict) -> bool:
    """
    Validate a single table dict produced by ingest.load_all_tables.
    Returns True if valid, False if the table should be skipped.
    """
    name = meta["name"]

    if meta["row_count"] == 0:
        logger.log("validation_warning", {"table": name, "reason": "zero rows"})
        return False

    for col, dtype in meta["types"].items():
        if dtype == "object":
            continue
        if "date" in col.lower() or col == "date_id":
            pass  # date columns handled separately

    try:
        df = pd.read_csv(meta["filepath"])
    except Exception as exc:
        logger.log("validation_error", {"table": name, "error": str(exc)})
        return False

    # Check no fully empty columns
    for col in df.columns:
        if df[col].isna().all():
            logger.log(
                "validation_warning",
                {"table": name, "reason": f"column '{col}' is fully null"},
            )

    # Check date_id column parses as numeric (YYYYMMDD format)
    if "date_id" in df.columns:
        try:
            pd.to_numeric(df["date_id"].dropna(), errors="raise")
        except Exception:
            logger.log(
                "validation_warning",
                {"table": name, "reason": "date_id column contains non-numeric values"},
            )

    return True


def validate_all(tables: list) -> list:
    """Filter tables list to only valid tables."""
    return [t for t in tables if validate_table(t)]
