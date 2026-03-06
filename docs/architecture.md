# Architecture

## System Overview

```
Browser
  |
React + Vite (port 5173)
  |
FastAPI (port 8000)
  |
  +-- data_pipeline  -- CSV ingestion, DuckDB registration, registry.json
  +-- chat_pipeline  -- SQL gen, retry, provenance, explain, cache, history
  +-- ml_pipeline    -- Evals, metrics, structured logging
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
 Groq Llama 3 70B: generate SQL
  |
 DuckDB: execute SQL against CSV views
  |-- Error: feed error back to LLM, retry (up to 3 times)
  |-- Success: continue
  |
 Provenance: parse SQL for referenced tables
  |
 chart_hint: infer chart type from result shape
  |
 Groq Llama 3 70B: generate plain English explanation
  |-- Failure: fallback to OpenAI GPT-4o, notify user
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
| DuckDB (in-memory) | Query engine over CSV files |
| data/registry.json | Table schema and FK relationships |
| SQLite | Sessions, messages, eval results, query metrics |
| Upstash Redis | Query result cache (1h TTL) |

## LLM Usage

| Call | Model | Temperature |
|---|---|---|
| SQL generation | Groq Llama 3 70B | 0 |
| Explanation | Groq Llama 3 70B | 0.3 |
| SQL eval judge | Groq Llama 3 70B | 0 |
| Answer eval judge | Groq Llama 3 70B | 0 |
| Fallback (all) | OpenAI GPT-4o | same as above |
