# PharmaIQ 1.0

A natural language analytics assistant over structured pharmaceutical sales data. Ask questions in plain English. The system generates SQL, executes it against CSV files using DuckDB, and returns a plain English answer with an auto-rendered chart and provenance tags pointing back to the source data. Voice input is supported via a LiveKit real-time voice pipeline.

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| Query Engine | DuckDB |
| Primary LLM | Groq |
| Cache | Upstash Redis |
| Chat History | SQLite |
| Charts | Recharts |
| Voice STT | Deepgram Nova-3 |
| Voice TTS | Deepgram Aura |
| Voice Transport | LiveKit (WebRTC) |
| Config | pydantic-settings |

## Quick Start

### 1. Clone and set up environment

```bash
git clone <repo>
cd PharmaIQ1.0
cp .env.example .env
# Fill in API keys -- see Environment Variables below
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Place CSV files in `data_pipeline/raw/`. Then start the server:

```bash
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Health check: `GET /health`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:5173`.

### 4. Voice agent (optional)

```bash
LIVEKIT_URL=wss://pharma-hleoc954.livekit.cloud \
LIVEKIT_API_KEY=APIUC22RKvcMQW9 \
LIVEKIT_API_SECRET=Bd8iGautRwGF0Jlm5fOwonvbByU5NEHC2Mgz7nJ9VNC \
OPENAI_API_KEY=... \
DEEPGRAM_API_KEY=... \
    python -m voice_pipeline.livekit_agent dev
```

See `voice_pipeline/README.md` for details.

## Data

Drop CSV files into `data_pipeline/raw/`. On startup, the backend:

1. Validates each file.
2. Auto-detects foreign key relationships by shared column names.
3. Registers all files as DuckDB views.
4. Writes `data_pipeline/registry.json` with schema and relationships.

Expected tables: `fact_rx`, `hcp_dim`, `account_dim`, `territory_dim`, `rep_dim`, `date_dim`, `fact_rep_activity`, `fact_payor_mix`, `fact_ln_metrics`.

## API Endpoints

```
GET    /health
GET    /api/v1/schema
GET    /api/v1/tables
POST   /api/v1/chat
GET    /api/v1/sessions
GET    /api/v1/sessions/{id}
DELETE /api/v1/sessions/{id}
GET    /api/v1/metrics/summary
GET    /api/v1/metrics/queries
GET    /api/v1/metrics/evals
POST   /api/v1/voice/transcribe
POST   /api/v1/voice/speak
POST   /api/v1/voice/token
```

## Project Structure

```
PharmaIQ1.0/
  backend/          FastAPI app, routes, config
  chat_pipeline/    SQL generation, retry, provenance, explainer, cache
  data_pipeline/    CSV ingestion, validation, relationship detection, registry
  eval_and_metrics/ Eval scoring, monitoring metrics, structured logger
  voice_pipeline/   LiveKit agent, STT, TTS (see voice_pipeline/README.md)
  frontend/         React + Vite UI
  data_pipeline/raw/  CSV files (not committed)
  docs/             Full documentation per subsystem
```

## Environment Variables

See `.env.example` for all required keys. Key variables:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for SQL generation |
| `OPENAI_API_KEY` | OpenAI key for REST STT/TTS fallback |
| `DEEPGRAM_API_KEY` | Deepgram API key for LiveKit STT/TTS |
| `UPSTASH_REDIS_URL` | Upstash Redis URL for query caching |
| `UPSTASH_REDIS_TOKEN` | Upstash Redis token |
| `DATA_DIR` | Absolute path to CSV directory |
| `SQLITE_DB_PATH` | Absolute path to SQLite database file |
| `LIVEKIT_URL` | LiveKit server WebSocket URL |
| `LIVEKIT_API_KEY` | LiveKit API key |
| `LIVEKIT_API_SECRET` | LiveKit API secret |

## Running Tests

```bash
# From project root
export PYTHONPATH=$(pwd):$(pwd)/backend
pytest data_pipeline/tests/ chat_pipeline/tests/ eval_and_metrics/tests/ backend/tests/ voice_pipeline/tests/ -v

# Frontend
cd frontend && npm test
```

## Documentation

See the `docs/` folder for detailed documentation on each subsystem. See `voice_pipeline/README.md` for the voice pipeline.
