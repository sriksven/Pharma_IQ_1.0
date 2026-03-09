# Data Pipeline

## Overview

Runs at startup and whenever new CSVs are added to `data/raw/`. Cleans the data, registers all CSVs as DuckDB tables, and writes `data/registry.json`.

## Steps

1. `ingest.py` - scans `data/raw/`, reads each CSV with pandas, cleans the data (drops missing identifiers, imputes numerics with 0 and text with 'Unknown'), records name, row count, columns, and inferred types. Registers the cleaned data as a DuckDB table using `CREATE OR REPLACE TABLE ... AS SELECT * FROM df`.

2. `validate.py` - checks each table for zero rows, fully null columns, and bad date_id format. Logs warnings without crashing.

3. `relationship_detector.py` - finds column names that appear in more than one table. These are treated as foreign keys and included in the schema description sent to the LLM.

4. `registry.py` - writes `data/registry.json` with table names, columns, types, row counts, relationships, and load timestamp. Also provides `get_schema_prompt()` for LLM integration.

## DuckDB Registration

All CSVs are read, cleaned via pandas, and registered as in-memory DuckDB tables for querying.

## Adding New Tables

Drop a CSV into `data/raw/` and restart the backend. The pipeline picks it up automatically. If the CSV has a column name that matches existing tables, it will appear in the relationship map.

## API

- `GET /api/v1/schema` -- full registry including tables and relationships
- `GET /api/v1/tables` -- list of loaded table names
