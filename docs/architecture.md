# Architecture

## System Overview

```
Browser
  |
React + Vite (port 5173)
  |
FastAPI (port 8000)
  |
  +-- data_pipeline  -- CSV ingestion, data cleaning, registry.json
  +-- chat_pipeline  -- SQL gen, retry, provenance, explain, cache, history
  +-- eval_and_metrics    -- Evals, metrics, structured logging
  +-- voice_pipeline -- STT (Whisper), TTS (OpenAI)
```

## Data Flow (Chat Query)

```
User question
  |
 Upstash Redis cache check
  |-- Hit: return cached answer immediately
  |-- Miss: continue
  |
 Groq openai/gpt-oss-120b: generate SQL
  |
 DuckDB: execute SQL against clean tables
  |-- Error: feed error back to LLM, retry (up to 3 times)
  |-- Success: continue
  |
 Provenance: parse SQL for referenced tables
  |
 chart_hint: infer chart type from result shape
  |
 Groq llama-3.1-8b-instant: generate plain English explanation
  |-- Failure: fallback to Groq openai/gpt-oss-20b, notify user
  |
 SQLite: save session and message
 Upstash Redis: write cache entry (1h TTL)
  |
 Background: run SQL eval + answer eval via LLM judge
 Background: write query_metrics to SQLite
  |
 Return: answer, sql, provenance, chart_hint, llm_used, cache_hit
```

## Storage

| Store | Purpose |
|---|---|
| DuckDB (in-memory) | Query engine over cleaned tables |
| data/registry.json | Table schema and FK relationships |
| SQLite | Sessions, messages, eval results, query metrics |
| Upstash Redis | Query result cache (1h TTL) |

## LLM Usage

| Call | Model | Temperature |
|---|---|---|
| SQL generation | Groq openai/gpt-oss-120b | 0 |
| Explanation | Groq llama-3.1-8b-instant | 0.3 |
| SQL eval judge | Groq openai/gpt-oss-120b | 0 |
| Answer eval judge | Groq openai/gpt-oss-120b | 0 |
| Fallback (all) | Groq openai/gpt-oss-20b | same as above |
