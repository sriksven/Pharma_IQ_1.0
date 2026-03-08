# Data Pipeline

The `data_pipeline` serves as the ETL (Extract, Transform, Load) and introspection layer of PharmaIQ. All available tabular data gets registered instantly upon application startup through this system.

## Key Modules
- **`ingest.py`**: Locates all raw tabular files (e.g. CSVs) inside `data/raw/` and registers them instantly with DuckDB as queriable views. Because DuckDB natively reads CSVs without copying, this process is incredibly fast and memory efficient.
- **`validate.py`**: Scans the tabular data structure to ensure files conform to standard formats, looking for unexpected nulls, row count discrepancies, and malformed column names across the dataset.
- **`relationship_detector.py`**: The "magic" piece. It performs column-level inference to detect Primary Key and Foreign Key constraints based on standard nomenclature (`_id` suffixes) and datatypes.
- **`registry.py`**: The output compiler. Aggregates the list of views, row counts, and relationships into a massive schema dictionary. It writes the result to `data/registry.json`.

*The resulting `registry.json` is heavily relied upon by the `chat_pipeline/sql_generator.py` to prompt the LLM with the database schema context.*
