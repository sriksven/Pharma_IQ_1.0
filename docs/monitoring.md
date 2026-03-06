# Monitoring

All metrics are stored in SQLite and available via API.

## query_metrics table

Recorded after every query (cache miss and cache hit both tracked):

| Column | Type | Description |
|---|---|---|
| total_latency_ms | INTEGER | End-to-end request time |
| sql_gen_latency_ms | INTEGER | Time for SQL generation LLM call |
| explain_latency_ms | INTEGER | Time for explanation LLM call |
| input_tokens | INTEGER | Tokens sent to LLM |
| output_tokens | INTEGER | Tokens returned by LLM |
| retry_count | INTEGER | 0-3; number of SQL retries required |
| llm_used | TEXT | "groq" or "openai" |
| cache_hit | INTEGER | 1 if served from cache |
| tables_joined | INTEGER | Number of tables referenced in SQL |
| session_turn_count | INTEGER | Number of messages in the session |
| failed | INTEGER | 1 if query failed after all retries |

## eval_results table

Recorded asynchronously after each query. Scores normalized 0-1 (multiply by 10 for display):

| Column | Description |
|---|---|
| sql_correctness | Does the SQL answer the question? |
| sql_efficiency | Is the SQL well-structured? |
| answer_relevance | Does the answer address the question? |
| answer_clarity | Is the answer readable? |
| answer_insight | Does it offer an observation beyond the literal answer? |

## Summary Endpoint

`GET /api/v1/metrics/summary` returns:

- `total_queries`
- `avg_latency_ms`
- `cache_hit_rate` (percent)
- `fallback_rate` (percent using OpenAI)
- `avg_retry_count`
- `failed_rate` (percent)
- `avg_sql_correctness` (out of 10)
- `avg_answer_relevance` (out of 10)

## Interpreting Results

A high retry count on a particular type of question suggests the LLM's handling of that query pattern should be improved via prompt tuning. A low SQL correctness score combined with a high answer relevance score may indicate the LLM is explaining well but querying wrong tables. Both should be reviewed together.
