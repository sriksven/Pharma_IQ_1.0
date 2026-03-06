import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_registry_written_with_correct_structure(monkeypatch, tmp_path):
    from data_pipeline import registry as reg_module
    monkeypatch.setattr(reg_module, "REGISTRY_PATH", str(tmp_path / "registry.json"))

    tables = [
        {
            "name": "fact_rx",
            "file": "fact_rx.csv",
            "row_count": 10,
            "columns": ["hcp_id", "date_id"],
            "types": {"hcp_id": "int64", "date_id": "int64"},
        }
    ]

    result = reg_module.build_registry(tables, str(tmp_path))

    assert "tables" in result
    assert "relationships" in result
    assert "loaded_at" in result
    assert result["tables"][0]["name"] == "fact_rx"

    with open(str(tmp_path / "registry.json")) as f:
        on_disk = json.load(f)
    assert on_disk["tables"][0]["name"] == "fact_rx"
