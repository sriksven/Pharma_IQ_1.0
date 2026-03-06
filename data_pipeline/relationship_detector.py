"""
Auto-detects foreign key relationships by finding column names shared across multiple tables.
"""

from collections import defaultdict


def detect_relationships(tables: list) -> dict:
    """
    Given a list of table metadata dicts, return a dict mapping column names
    to the list of tables that contain that column.

    Only columns appearing in 2+ tables are included.

    Example:
        {"hcp_id": ["fact_rx", "hcp_dim", "fact_rep_activity"], ...}
    """
    column_to_tables: dict = defaultdict(list)

    for table in tables:
        for col in table["columns"]:
            column_to_tables[col].append(table["name"])

    relationships = {
        col: sorted(tlist)
        for col, tlist in column_to_tables.items()
        if len(tlist) > 1
    }

    return relationships


def format_for_prompt(relationships: dict) -> str:
    """
    Return a human-readable string describing relationships for inclusion
    in the SQL generator system prompt.
    """
    lines = []
    for col, tables in sorted(relationships.items()):
        lines.append(f"- {col} links: {', '.join(tables)}")
    return "\n".join(lines)
