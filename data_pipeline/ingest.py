"""
Scans data/raw/ for CSV files and loads them into pandas DataFrames.
Returns a list of table metadata dicts.
"""

import os
import pandas as pd
from ml_pipeline.monitoring.logger import JSONLogger

logger = JSONLogger()

_registry: dict = {}
_duckdb_conn = None


def get_duckdb_conn():
    import duckdb
    global _duckdb_conn
    if _duckdb_conn is None:
        _duckdb_conn = duckdb.connect()
    return _duckdb_conn


def load_all_tables(data_dir: str) -> list:
    """Load all CSVs from data_dir. Register as DuckDB views. Return metadata list."""
    conn = get_duckdb_conn()
    tables = []

    if not os.path.isdir(data_dir):
        logger.log("ingest_warning", {"message": f"data_dir not found: {data_dir}"})
        return tables

    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".csv"):
            continue

        filepath = os.path.join(data_dir, filename)
        table_name = filename.replace(".csv", "")

        try:
            df = pd.read_csv(filepath)
            row_count = len(df)
            columns = list(df.columns)
            types = {col: str(df[col].dtype) for col in columns}

            conn.execute(
                f"CREATE OR REPLACE VIEW {table_name} AS "
                f"SELECT * FROM read_csv_auto('{filepath}')"
            )

            tables.append(
                {
                    "name": table_name,
                    "file": filename,
                    "filepath": filepath,
                    "row_count": row_count,
                    "columns": columns,
                    "types": types,
                }
            )

            logger.log("table_loaded", {"table": table_name, "rows": row_count})

        except Exception as exc:
            logger.log("ingest_error", {"file": filename, "error": str(exc)})

    global _registry
    _registry = {t["name"]: t for t in tables}
    return tables


def get_registry_map() -> dict:
    return _registry
