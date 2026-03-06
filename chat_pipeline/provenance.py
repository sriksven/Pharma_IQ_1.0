"""
Tags query results with source table and file provenance.
Parses the SQL string to identify which tables were used.
"""

import re
from data_pipeline.registry import load_registry


def extract_tables_from_sql(sql: str) -> list[str]:
    """
    Parse SQL to find referenced table/view names.
    Uses a simple regex approach: looks for identifiers after FROM and JOIN keywords.
    """
    pattern = r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    matches = re.findall(pattern, sql, re.IGNORECASE)
    # Deduplicate while preserving order
    seen = set()
    tables = []
    for m in matches:
        if m.lower() not in seen:
            seen.add(m.lower())
            tables.append(m.lower())
    return tables


def build_provenance(sql: str) -> list[dict]:
    """
    Returns a list of provenance dicts for each table referenced in the SQL.

    Example:
        [
            {"table": "fact_rx", "file": "fact_rx.csv"},
            {"table": "hcp_dim", "file": "hcp_dim.csv"}
        ]
    """
    registry = load_registry()
    table_map = {t["name"]: t["file"] for t in registry.get("tables", [])}

    referenced = extract_tables_from_sql(sql)
    provenance = []
    for table_name in referenced:
        if table_name in table_map:
            provenance.append({"table": table_name, "file": table_map[table_name]})

    return provenance
