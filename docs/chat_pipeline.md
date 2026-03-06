# Chat Pipeline

## Overview

The core question-answering pipeline. Takes a user question and returns a plain English answer with SQL, provenance, and chart hint.

## sql_generator.py

Builds a system prompt containing the full schema from `registry.json` (tables, columns, row counts, relationships). Calls Groq Llama 3 70B at temperature 0. Returns raw SQL only.

Falls back to OpenAI GPT-4o if Groq raises an exception.

## retry.py

Wraps SQL generation and DuckDB execution in a retry loop (up to 3 attempts). On SQL error, the error message is appended to conversation history so the LLM can correct itself.

## provenance.py

Parses the generated SQL using regex to extract table names from FROM and JOIN clauses. Maps each table name to its source CSV file using the registry. Returns as a list for display in the UI.

## explainer.py

Second LLM call after SQL execution. Input: original question, the SQL that ran, and up to 20 rows of results as a markdown table. Output: plain English answer plus one proactive insight. Temperature 0.3.

Falls back to OpenAI GPT-4o with a visible fallback_reason notice to the user.

## cache.py

Caches full query responses in Upstash Redis. Key: SHA-256 of `question.lower().strip()`. TTL 1 hour. Write errors are silently swallowed so cache failures do not block queries.

## db.py

SQLite persistence. Tables: `sessions`, `messages`, `eval_results`, `query_metrics`.

## API

- `POST /api/v1/chat` -- accepts `session_id` and `question`; returns `answer`, `sql`, `provenance`, `chart_hint`, `llm_used`, `cache_hit`, `latency_ms`
- `GET /api/v1/sessions` -- list all sessions
- `GET /api/v1/sessions/{id}` -- all messages in a session
- `DELETE /api/v1/sessions/{id}` -- delete session and messages
