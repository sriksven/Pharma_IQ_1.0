# Chat Pipeline

## Overview

The core question-answering pipeline. Takes a user question and returns a plain English answer with SQL, provenance, and chart hint.

## sql_generator.py

Builds a system prompt containing the full schema from `registry.json` (tables, columns, row counts, relationships). Calls Groq openai/gpt-oss-120b at temperature 0. Returns raw SQL only.

Falls back to Groq openai/gpt-oss-20b if primary model raises an exception.

## retry.py

Wraps SQL generation and DuckDB execution in a retry loop (up to 3 attempts). On SQL error, the error message is appended to conversation history so the LLM can self-correct. Accepts `conversation_history` for multi-turn context, which is prepended before retry error messages.

## provenance.py

Parses the generated SQL using regex to extract table names from FROM and JOIN clauses. Maps each table name to its source CSV file using the registry. Returns as a list for display in the UI.

## explainer.py

Second LLM call after SQL execution. Input: original question, the SQL that ran, up to 20 rows of results as a markdown table, and the last 6 messages from the session as conversation history. Output: plain English answer plus one proactive insight. Temperature 0.3. History enables follow-up questions to reference prior context.

Falls back to Groq openai/gpt-oss-20b with a visible fallback_reason notice to the user.

## cache.py

Caches full query responses in Upstash Redis. Key: SHA-256 of `question.lower().strip()`. TTL 1 hour. Write errors are silently swallowed so cache failures do not block queries.

## db.py

SQLite persistence. Tables: `sessions`, `messages`, `eval_results`, `query_metrics`.

## API

- `POST /api/v1/chat` -- accepts `session_id` and `question`; returns `answer`, `sql`, `provenance`, `chart_hint`, `llm_used`, `cache_hit`, `latency_ms`. If SQL fails after all retries, returns a 200 with a friendly "I don't have that information" message instead of an error.
- `GET /api/v1/sessions` -- list all sessions
- `GET /api/v1/sessions/{id}` -- all messages in a session
- `DELETE /api/v1/sessions/{id}` -- delete session and messages
- `GET /api/v1/data/csv/{filename}` -- download a raw CSV from `data_pipeline/raw/` as an attachment

## Conversation Memory

Before each LLM call, the last 6 messages (3 user + 3 assistant turns) from the current session are fetched from SQLite and injected as prior context. This allows the system to correctly handle follow-up questions like:
- "What is the nrx count for Cardiology?" → "10"
- "Why is that number low?" → correctly references Cardiology nrx from the previous answer

Cache hits are also re-attached to the current session's SQLite history so memory continues to work after a cache hit.
