import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_load_all_tables():
    from data_pipeline.ingest import load_all_tables
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
    tables = load_all_tables(data_dir)
    assert len(tables) >= 1
    assert all("name" in t for t in tables)
    assert all("row_count" in t for t in tables)


def test_all_expected_tables_loaded():
    from data_pipeline.ingest import load_all_tables
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
    tables = load_all_tables(data_dir)
    names = [t["name"] for t in tables]
    for expected in ["fact_rx", "hcp_dim", "territory_dim"]:
        assert expected in names


def test_tables_have_columns():
    from data_pipeline.ingest import load_all_tables
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
    tables = load_all_tables(data_dir)
    for t in tables:
        assert len(t["columns"]) > 0
