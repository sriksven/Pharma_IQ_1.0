"""
Builds and writes data/registry.json from loaded table metadata.
Also exposes a function to load the registry back from disk.
"""

import json
import os
from datetime import datetime

from data_pipeline.relationship_detector import detect_relationships

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "registry.json")


def build_registry(tables: list, data_dir: str) -> dict:
    """Build registry dict from table list and write to data/registry.json."""
    relationships = detect_relationships(tables)

    registry = {
        "tables": [
            {
                "name": t["name"],
                "file": t["file"],
                "row_count": t["row_count"],
                "columns": t["columns"],
                "types": t["types"],
            }
            for t in tables
        ],
        "relationships": relationships,
        "loaded_at": datetime.utcnow().isoformat(),
    }

    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)

    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)

    return registry


def load_registry() -> dict:
    """Load registry from disk. Returns empty dict if not found."""
    if not os.path.exists(REGISTRY_PATH):
        return {}
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def get_schema_prompt(registry: dict) -> str:
    """
    Format the registry as a schema description for the LLM system prompt.
    Returns a plain text string listing tables, columns, row counts, and relationships.
    """
    lines = ["Tables available:"]
    for t in registry.get("tables", []):
        cols = ", ".join(t["columns"])
        lines.append(f"- {t['name']} ({cols}) -- {t['row_count']} rows")

    lines.append("")
    lines.append("Relationships (shared columns across tables):")
    for col, tables in registry.get("relationships", {}).items():
        lines.append(f"- {col} links: {', '.join(tables)}")

    return "\n".join(lines)
