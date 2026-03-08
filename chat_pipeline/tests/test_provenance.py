"""
Unit tests for SQL provenance extraction.
Tests exercise the regex-based table-name parser without touching DuckDB or the registry.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from chat_pipeline.provenance import extract_tables_from_sql


def test_simple_from_clause():
    tables = extract_tables_from_sql("SELECT * FROM fact_rx")
    assert tables == ["fact_rx"]


def test_inner_join():
    sql = "SELECT * FROM fact_rx JOIN hcp_dim ON fact_rx.hcp_id = hcp_dim.hcp_id"
    tables = extract_tables_from_sql(sql)
    assert "fact_rx" in tables
    assert "hcp_dim" in tables


def test_multiple_joins():
    sql = (
        "SELECT * FROM fact_rx "
        "JOIN hcp_dim ON fact_rx.hcp_id = hcp_dim.hcp_id "
        "JOIN territory_dim ON hcp_dim.territory_id = territory_dim.territory_id"
    )
    tables = extract_tables_from_sql(sql)
    assert "fact_rx" in tables
    assert "hcp_dim" in tables
    assert "territory_dim" in tables


def test_deduplicates_tables():
    sql = "SELECT a.x FROM fact_rx a JOIN fact_rx b ON a.id = b.id"
    tables = extract_tables_from_sql(sql)
    assert tables.count("fact_rx") == 1


def test_case_insensitive_keywords():
    sql = "select * from fact_rx inner join hcp_dim on fact_rx.hcp_id = hcp_dim.hcp_id"
    tables = extract_tables_from_sql(sql)
    assert "fact_rx" in tables
    assert "hcp_dim" in tables


def test_empty_sql_returns_empty_list():
    assert extract_tables_from_sql("") == []


def test_no_from_returns_empty_list():
    assert extract_tables_from_sql("SELECT 1") == []


def test_subquery_tables_captured():
    sql = "SELECT * FROM (SELECT hcp_id FROM hcp_dim) sub JOIN fact_rx ON sub.hcp_id = fact_rx.hcp_id"
    tables = extract_tables_from_sql(sql)
    assert "hcp_dim" in tables
    assert "fact_rx" in tables


def test_tables_returned_lowercase():
    tables = extract_tables_from_sql("SELECT * FROM FACT_RX")
    assert "fact_rx" in tables
