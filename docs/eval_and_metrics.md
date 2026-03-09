# ML Pipeline

## Eval

After each query completes, `judge.py` runs two evaluations asynchronously and writes the results to the `eval_results` SQLite table.

### sql_eval.py

- Rule-based: was the SQL executed without error?
- LLM judge: correctness (0-10) and efficiency (0-10) scores from Groq openai/gpt-oss-120b.

### answer_eval.py

- LLM judge: relevance, clarity, and insight scores (0-10 each) from Groq openai/gpt-oss-120b.
- Scores are stored normalized to 0-1 in SQLite and displayed as 0-10 in the UI.

## Monitoring

`metrics.py` records per-query data to the `query_metrics` SQLite table:

- Total end-to-end latency
- SQL generation latency
- Explanation latency
- Token counts (where available)
- Retry count
- Which LLM was used
- Cache hit or miss
- Number of tables joined
- Session turn count
- Whether the query failed

## logger.py

Structured JSON logger used across all pipeline modules. Writes to stderr. Every significant event produces a JSON log line with an event name, data dict, and UTC timestamp.

Key events: `query_received`, `cache_hit`, `sql_generated`, `sql_failed`, `sql_retried`, `fallback_triggered`, `answer_generated`, `eval_completed`

## API

- `GET /api/v1/metrics/summary` -- aggregate stats
- `GET /api/v1/metrics/queries` -- last N queries with latency and LLM info
- `GET /api/v1/metrics/evals` -- last N eval score records

## Testing (`eval_and_metrics/tests/`)
*(Run automatically on every Push and Pull Request via `.github/workflows/test.yml`)*
- The gold dataset evaluation scripts exist within `eval_and_metrics/tests/` to guarantee no pipeline modifications break the standard pharmaceutical query results before CI/CD passes.
