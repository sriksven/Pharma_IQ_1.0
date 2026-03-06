# Data Pipeline

## Overview

Runs at startup and whenever new CSVs are added to `data/raw/`. Registers all CSVs as DuckDB views and writes `data/registry.json`.

## Steps

1. `ingest.py` - scans `data/raw/`, reads each CSV with pandas, records name, row count, columns, and inferred types. Registers each file as a DuckDB view using `CREATE OR REPLACE VIEW ... AS SELECT * FROM read_csv_auto(...)`.

2. `validate.py` - checks each table for zero rows, fully null columns, and bad date_id format. Logs warnings without crashing.

3. `relationship_detector.py` - finds column names that appear in more than one table. These are treated as foreign keys and included in the schema description sent to the LLM.

4. `registry.py` - writes `data/registry.json` with table names, columns, types, row counts, relationships, and load timestamp. Also provides `get_schema_prompt()` for LLM integration.

## DuckDB Registration

All CSVs are registered as in-memory views. DuckDB reads the files directly on query. No data is copied or imported.

## Adding New Tables

Drop a CSV into `data/raw/` and restart the backend. The pipeline picks it up automatically. If the CSV has a column name that matches existing tables, it will appear in the relationship map.

## API

- `GET /api/v1/schema` -- full registry including tables and relationships
- `GET /api/v1/tables` -- list of loaded table names
