from fastapi import APIRouter
from data_pipeline.registry import load_registry
from data_pipeline.ingest import get_registry_map

router = APIRouter()


@router.get("/schema")
def get_schema():
    """Returns the full registry including tables, columns, types, and relationships."""
    return load_registry()


@router.get("/tables")
def get_tables():
    """Returns the list of currently loaded table names."""
    registry = load_registry()
    return {"tables": [t["name"] for t in registry.get("tables", [])]}
