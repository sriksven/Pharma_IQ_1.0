# PharmaIQ Backend API

This directory contains the FastAPI web server that acts as the primary orchestrator for the PharmaIQ application. It routes incoming requests from the frontend, manages the session state, and triggers the various pipelines (chat, data, evals).

## Structure
- `app/main.py` - The FastAPI entry point. Mounts the router and handles CORS setup.
- `app/routes/chat.py` - The core `/chat` endpoint. It receives questions, routes them to the `chat_pipeline` to generate and execute SQL, and then kicks off the asynchronous evaluations and telemetry via `eval_and_metrics`.
- `app/routes/metrics.py` - Endpoints returning summary statistics and historic evaluation data for the frontend Monitoring dashboard.
- `app/routes/sessions.py` - Endpoints for fetching chat history or clearing out old sessions from the SQLite database.
- `app/config.py` - Environment variable and settings management (e.g. Groq/Upstash keys).

## Running Locally
Make sure you are running inside the virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

*For more detailed architecture diagrams and system flow information, refer to the root `/docs/architecture.md` file.*

## API Endpoints

All routes (except `/health`) are prefixed with `http://localhost:8000/api/v1` locally (`/api/v1` in `main.py`).

### Chat
- `POST http://localhost:8000/api/v1/chat` - Submits a question and returns the SQL, explicit natural language answer, and inferred chart-type hint.

### Sessions
- `GET http://localhost:8000/api/v1/sessions` - Returns the list of historical chats (limited to the last 10).
- `GET http://localhost:8000/api/v1/sessions/{session_id}` - Returns the full message history of a specific chat.
- `DELETE http://localhost:8000/api/v1/sessions/{session_id}` - Hard-deletes a chat session and its corresponding messages from the DB.

### Data & Schema
- `GET http://localhost:8000/api/v1/tables` - Returns a flat list of all loaded CSV views in DuckDB.
- `GET http://localhost:8000/api/v1/schema` - Returns the complex graph structure detailing columns, primary keys, and relations.

### Metrics & Evals
- `GET http://localhost:8000/api/v1/metrics/summary` - Returns core KPIs (avg latency, token usage, fallback rates, and overall AI grade averages).
- `GET http://localhost:8000/api/v1/metrics/queries` - Returns the last 20 raw requests and their metadata.
- `GET http://localhost:8000/api/v1/metrics/evals` - Returns the last 50 LLM Judge evaluation scorecards.

### Speech
- `POST http://localhost:8000/api/v1/voice/transcribe` - Accepts audio via multipart form data and returns an OpenAI Whisper text-string.
- `POST http://localhost:8000/api/v1/voice/speak` - Accepts text and returns an OpenAI TTS MPEG audio stream.
