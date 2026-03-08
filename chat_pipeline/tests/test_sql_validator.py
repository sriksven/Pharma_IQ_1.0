"""
Pytest tests for the SQL validator.
These tests validate the validator logic against known-good and known-bad queries.
The validator loads the data registry; tests that exercise schema validation
require the registry to exist (populated by load_all_tables in CI or locally).
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from chat_pipeline.sql_validator import validate_sql


# ---------------------------------------------------------------------------
# Syntax errors
# ---------------------------------------------------------------------------

def test_invalid_syntax_returns_error():
    errors = validate_sql("SELECT FROM WHERE")
    assert len(errors) > 0
    assert any("syntax" in e.lower() or "error" in e.lower() for e in errors)


def test_empty_string_returns_error():
    errors = validate_sql("")
    assert len(errors) > 0


# ---------------------------------------------------------------------------
# Structurally valid queries (schema-agnostic checks)
# ---------------------------------------------------------------------------

def test_select_star_no_errors_structurally():
    """SELECT * should not produce column validation errors even without registry."""
    errors = validate_sql("SELECT * FROM fact_rx LIMIT 5")
    # If registry exists, hallucinated columns are caught but * is always allowed.
    # If registry is absent, the only error would be "registry not found".
    # We just assert this doesn't crash.
    assert isinstance(errors, list)


def test_valid_query_returns_list():
    result = validate_sql("SELECT territory_id FROM territory_dim")
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Schema validation (runs only when registry is populated)
# ---------------------------------------------------------------------------

def _registry_populated() -> bool:
    """Return True if the data registry has been built and contains tables."""
    try:
        from data_pipeline.registry import load_registry
        reg = load_registry()
        return bool(reg and reg.get("tables"))
    except Exception:
        return False


@pytest.mark.skipif(not _registry_populated(), reason="Registry not populated; skipping schema tests")
def test_valid_columns_pass():
    # fact_ln_metrics columns: entity_type, entity_id, quarter_id, ln_patient_cnt, est_market_share
    errors = validate_sql(
        "SELECT entity_type, SUM(ln_patient_cnt) AS total FROM fact_ln_metrics GROUP BY entity_type"
    )
    assert errors == []


@pytest.mark.skipif(not _registry_populated(), reason="Registry not populated; skipping schema tests")
def test_hallucinated_table_caught():
    errors = validate_sql("SELECT * FROM imaginary_table_xyz")
    assert any("imaginary_table_xyz" in e for e in errors)


@pytest.mark.skipif(not _registry_populated(), reason="Registry not populated; skipping schema tests")
def test_hallucinated_column_caught():
    errors = validate_sql("SELECT nonexistent_column_xyz FROM hcp_dim")
    assert any("nonexistent_column_xyz" in e for e in errors)


@pytest.mark.skipif(not _registry_populated(), reason="Registry not populated; skipping schema tests")
def test_wildcard_not_flagged():
    errors = validate_sql("SELECT * FROM hcp_dim LIMIT 5")
    assert errors == []
