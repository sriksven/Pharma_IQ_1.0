import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_hcp_id_detected_across_tables():
    from data_pipeline.relationship_detector import detect_relationships
    tables = [
        {"name": "fact_rx", "columns": ["hcp_id", "date_id", "trx_cnt"]},
        {"name": "hcp_dim", "columns": ["hcp_id", "full_name", "territory_id"]},
        {"name": "fact_rep_activity", "columns": ["hcp_id", "rep_id", "date_id"]},
    ]
    rels = detect_relationships(tables)
    assert "hcp_id" in rels
    assert set(rels["hcp_id"]) == {"fact_rx", "hcp_dim", "fact_rep_activity"}


def test_single_table_columns_excluded():
    from data_pipeline.relationship_detector import detect_relationships
    tables = [
        {"name": "fact_rx", "columns": ["hcp_id", "unique_col"]},
        {"name": "hcp_dim", "columns": ["hcp_id", "full_name"]},
    ]
    rels = detect_relationships(tables)
    assert "unique_col" not in rels
    assert "full_name" not in rels
    assert "hcp_id" in rels
