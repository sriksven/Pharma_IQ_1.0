import pytest
import os
import sys
import tempfile
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def _make_csv(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_valid_table_passes():
    from data_pipeline.validate import validate_table
    with tempfile.TemporaryDirectory() as tmpdir:
        p = os.path.join(tmpdir, "test.csv")
        _make_csv(p, [{"hcp_id": 1, "date_id": 20240101, "value": 10}])
        meta = {
            "name": "test",
            "file": "test.csv",
            "filepath": p,
            "row_count": 1,
            "columns": ["hcp_id", "date_id", "value"],
            "types": {"hcp_id": "int64", "date_id": "int64", "value": "int64"},
        }
        assert validate_table(meta) is True


def test_empty_table_fails():
    from data_pipeline.validate import validate_table
    with tempfile.TemporaryDirectory() as tmpdir:
        p = os.path.join(tmpdir, "empty.csv")
        _make_csv(p, [{"col": ""}])
        meta = {
            "name": "empty",
            "file": "empty.csv",
            "filepath": p,
            "row_count": 0,
            "columns": ["col"],
            "types": {"col": "object"},
        }
        assert validate_table(meta) is False
