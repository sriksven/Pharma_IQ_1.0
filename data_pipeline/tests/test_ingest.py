import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
_has_data = os.path.isdir(_DATA_DIR) and bool(
    [f for f in os.listdir(_DATA_DIR) if f.endswith(".csv")]
    if os.path.isdir(_DATA_DIR)
    else []
)
_skip_no_data = pytest.mark.skipif(not _has_data, reason="no CSV files in data_pipeline/raw/")


@_skip_no_data
def test_load_all_tables():
    from data_pipeline.ingest import load_all_tables
    tables = load_all_tables(_DATA_DIR)
    assert len(tables) >= 1
    assert all("name" in t for t in tables)
    assert all("row_count" in t for t in tables)


@_skip_no_data
def test_all_expected_tables_loaded():
    from data_pipeline.ingest import load_all_tables
    tables = load_all_tables(_DATA_DIR)
    names = [t["name"] for t in tables]
    for expected in ["fact_rx", "hcp_dim", "territory_dim"]:
        assert expected in names


@_skip_no_data
def test_tables_have_columns():
    from data_pipeline.ingest import load_all_tables
    tables = load_all_tables(_DATA_DIR)
    for t in tables:
        assert len(t["columns"]) > 0
