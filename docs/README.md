# Pharma_IQ_1.0

Natural language analytics assistant over pharmaceutical sales data.

## How It Works

1. User asks a question in plain English.
2. The system loads the last 6 messages from the session as conversation history for multi-turn context.
3. A DuckDB SQL query is generated using Groq openai/gpt-oss-120b.
4. SQL runs against CSV files. If it fails, the error is fed back to the LLM and retried up to 3 times. If all retries fail, a friendly "I don't have that information" message is returned.
5. Results are explained in plain English with one proactive insight, using prior context for follow-up questions.
6. Every answer shows the SQL that ran, the source files it touched (clickable to download the CSV), and which model was used.
7. Identical questions are served from cache (Upstash Redis) with no LLM call, correctly re-attached to the current session.

## Running the Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
# Edit .env and set API keys

uvicorn app.main:app --reload
```

API available at `http://localhost:8000`.

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:5173`.

## Data

Place CSV files in `data/raw/`. The backend registers them automatically at startup. Expected tables:

- `fact_rx` -- prescriptions
- `hcp_dim` -- healthcare providers
- `account_dim` -- accounts
- `territory_dim` -- territories
- `rep_dim` -- sales reps
- `date_dim` -- date dimension
- `fact_rep_activity` -- rep calls and visits
- `fact_payor_mix` -- payer distribution
- `fact_ln_metrics` -- launch metrics

## Environment Variables

See `.env.example`. Required keys:

- `GROQ_API_KEY`
- `UPSTASH_REDIS_URL`
- `UPSTASH_REDIS_TOKEN`

## Documentation

See `docs/` for detailed documentation on each subsystem.
- [Future Plan: RLHF](future_rlhf_plan.md)
