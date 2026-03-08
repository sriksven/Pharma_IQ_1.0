# Chat Pipeline

The `chat_pipeline` is the core analytics logic layer of the application. It interprets user questions, translates them into DuckDB SQL, runs the queries against CSVs, and extracts a plain English answer and charting hints.

## Key Modules
- **`sql_generator.py`**: Reads `data/registry.json`, builds a system prompt containing the full database schema, and calls an LLM (`openai/gpt-oss-120b`) to return the raw DuckDB SQL. Falls back to a smaller model on API failure.
- **`retry.py`**: Executes the generated DuckDB SQL. If it fails due to a schema error or missing column, it feeds the trace back to the LLM for automatic self-correction (up to 3 times) before giving up and notifying the user.
- **`explainer.py`**: Takes the executed SQL and the markdown results table, sending them to the fast `llama-3.1-8b-instant` LLM. It generates the tight, bullet-free prose answer accompanied by a proactive data insight.
- **`provenance.py`**: Uses regex to parse table names from the generated `FROM` and `JOIN` clauses. Maps these back to their source CSV files for display in the UI as green tags.
- **`cache.py`**: Caches the final `answer`, `sql`, `provenance`, and `chart` objects in Upstash Redis to speed up repeated queries.
- **`db.py`**: Implements SQLite storage for chat session persistence and prompt logging.

*See `/docs/chat_pipeline.md` for more details.*
