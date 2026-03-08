# Pharma_IQ_1.0

A natural language analytics assistant over structured pharmaceutical sales data. Ask questions in plain English. The system generates SQL, executes it against CSV files using DuckDB, and returns a plain English answer with an auto-rendered chart and provenance tags pointing back to the source data.

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| Query Engine | DuckDB |
| Primary LLM | Groq Llama 3 70B |
| Fallback LLM | OpenAI GPT-4o |
| Cache | Upstash Redis |
| Chat History | SQLite |
| Charts | Recharts |
| Config | pydantic-settings |

## Quick Start

### 1. Clone and set up environment

```bash
git clone <repo>
cd Pharma_IQ_1.0
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Place your CSV files in `data/raw/`. Then start the server:

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

## Data

Drop CSV files into `data/raw/`. On startup, the backend:

1. Validates each file.
2. Auto-detects foreign key relationships by shared column names.
3. Registers all files as DuckDB views.
4. Writes `data/registry.json` with schema and relationships.

Expected tables: `fact_rx`, `hcp_dim`, `account_dim`, `territory_dim`, `rep_dim`, `date_dim`, `fact_rep_activity`, `fact_payor_mix`, `fact_ln_metrics`.

## API Endpoints

```
GET  /health
GET  /api/v1/schema
GET  /api/v1/tables
POST /api/v1/chat
GET  /api/v1/sessions
GET  /api/v1/sessions/{id}
DELETE /api/v1/sessions/{id}
GET  /api/v1/metrics/summary
GET  /api/v1/metrics/queries
GET  /api/v1/metrics/evals
POST /api/v1/voice/transcribe
POST /api/v1/voice/speak
```

## Project Structure

```
Pharma_IQ_1.0/
  backend/         FastAPI app, routes, config
  chat_pipeline/   SQL generation, retry, provenance, explainer, cache
  data_pipeline/   CSV ingestion, validation, relationship detection, registry
  eval_and_metrics/     Eval scoring, monitoring metrics, structured logger
  voice_pipeline/  Speech-to-text and text-to-speech
  frontend/        React + Vite UI
  data/raw/        CSV files (not committed)
  docs/            Full documentation
```

## Environment Variables

See `.env.example` for all required keys.

## Running Tests

```bash
# Backend
cd backend
pytest ../data_pipeline/tests/ ../chat_pipeline/tests/ ../eval_and_metrics/tests/ tests/ -v

# Frontend
cd frontend
npm test
```

## Documentation

See the `docs/` folder for detailed documentation on each subsystem.

## Version

1.0 - Text-to-SQL over structured tabular data via DuckDB.
