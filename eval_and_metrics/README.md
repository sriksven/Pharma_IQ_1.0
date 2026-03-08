# Eval and Metrics Pipeline

This directory acts as the asynchronous background worker layer. After the user receives their chat response, the metrics and evaluation jobs kick off here to record telemetry and grade the AI's performance.

## Key Modules

### `/eval`
- **`judge.py`**: The orchestrator. Instantiates SQLite connection and executes both evaluators, saving the 0.0-1.0 normalized grades into the `eval_results` table.
- **`sql_eval.py`**: Uses a judge LLM (`openai/gpt-oss-120b`) to grade the generated DuckDB SQL on its correctness and efficiency (avoiding unnecessary JOINs).
- **`answer_eval.py`**: Uses the judge LLM to evaluate the final English answer on its relevance to the prompt, overall prose clarity, and whether it uncovered a proactive statistical insight.

### `/monitoring`
- **`metrics.py`**: Tracks the hard telemetry. Saves total request latency, sub-latency across generators/explainers, cache hit ratios, token usage, and retry failure counts into the `query_metrics` SQLite table.
- **`logger.py`**: The structured JSON logging utility used throughout the entire codebase (e.g. `query_received`, `eval_completed`).

*See `/docs/eval_and_metrics.md` and `/docs/monitoring.md` for more details.*
