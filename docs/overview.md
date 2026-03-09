# PharmaIQ 1.0 - Technical Overview

Welcome to the architectural and operational overview of **PharmaIQ 1.0**. This document is designed to help you quickly understand and explain the platform's core components, pipelines, testing strategies, and data flows.

---

## 1. Project Purpose & Data Sets
**PharmaIQ 1.0** is an intelligent, natural language analytics assistant designed specifically for pharmaceutical sales data. It allows users to ask plain English questions and instantly receive data-driven answers, charts, and the underlying SQL query used to fetch the data.

**Data Sets (The Foundation):**
The platform operates on a star-schema of CSV files placed in the `data_pipeline/raw/` directory. These include:
- `fact_rx.csv` *(Prescription transactions)*
- `fact_rep_activity.csv` *(Sales rep interactions with doctors)*
- `fact_payor_mix.csv` *(Insurance/payer distributions)*
- `fact_ln_metrics.csv` *(Launch and marketing metrics)*
- `hcp_dim.csv` *(Healthcare Provider/Doctor details)*
- `account_dim.csv` *(Hospital/Clinic details)*
- `rep_dim.csv` *(Sales Representative details)*
- `territory_dim.csv` *(Geographical territories)*
- `date_dim.csv` *(Time and calendar dimensions)*

---

## 2. Tech Stack & Startup Commands

**The Stack:**
- **Frontend**: React, Vite, CSS Modules, Recharts (for dynamic data visualization).
- **Backend / API**: FastAPI (Python), Uvicorn.
- **Database Engine**: DuckDB (An incredibly fast, in-memory analytical database for querying cleaned tabular data).
- **Storage / State**: SQLite (Stores chat history, user sessions, and metric evaluations).
- **Caching**: Upstash Redis (Serverless cache for intercepting repeated questions).
- **Voice Agent**: LiveKit (WebRTC server infrastructure), Silero VAD (Voice Activity Detection).

**Startup Commands:**
To run the full stack locally across three terminal tabs:
1. **Backend**: `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
2. **Frontend**: `cd frontend && npm run dev`
3. **Voice Worker**: `DEEPGRAM_API_KEY=... python -m voice_pipeline.livekit_agent dev`

---

## 3. The LLM Strategy
We use a multi-LLM routing strategy to balance speed, cost, and complex reasoning:
- **Primary SQL Generator**: **Groq `llama-3.3-70b-versatile`** (or similar Llama3 models). Hosted on Groq's specialized hardware for extreme low-latency processing.
- **Answer Explainer**: Groq Llama 3 (Runs in parallel to format the final English response).
- **Fallback LLM**: **OpenAI `gpt-4o`**. If the Groq model hallucinates or generates invalid SQL 3 times in a row, the request falls back to GPT-4o, which is slower but possesses stronger complex reasoning to fix broken queries.
- **Voice Models**: **Deepgram** models (`Nova-3` for STT, `Aura` for TTS) are used exclusively in the voice pipeline to minimize transcription latency drastically compared to standard OpenAI Whisper.

---

## 4. The Pipelines & Their Tests

### A. The Data Pipeline (`data_pipeline/`)
**What it does:** 
On server startup (inside `app/main.py`), the pipeline scans the raw `.csv` directory, cleans the data, registers each dataset as a highly-efficient **DuckDB Table**, and builds a `registry.json` file. This JSON registry maps out the entire schema (columns, types, and auto-detected foreign-key relationships) so it can be injected into the LLM prompt.

**File Breakdown:**

1.  `ingest.py` - Scans `data/raw/`, reads each CSV with pandas, cleans the data (drops missing identifiers, imputes numerics with 0 and text with 'Unknown'), records name, row count, columns, and inferred types. Registers the cleaned data as a DuckDB table using `CREATE OR REPLACE TABLE ... AS SELECT * FROM df`.

2.  `validate.py` - Checks each table for zero rows, fully null columns, and bad date_id format. Logs warnings without crashing.

3.  `relationship_detector.py` - Finds column names that appear in more than one table. These are treated as foreign keys and included in the schema description sent to the LLM.

4.  `registry.py` - Writes `data/registry.json` with table names, columns, types, row counts, relationships, and load timestamp. Also provides `get_schema_prompt()` for LLM integration.

**Testing (`data_pipeline/tests/`):** 
-   `test_ingest.py`: Ensures all tables load correctly without crashing.
-   `test_registry.py`: Validates the exact JSON structure of the built registry.
-   `test_relationship_detector.py`: Verifies that overlapping columns (like `hcp_id`) map correctly between fact and dimension tables.

**Dynamic CSV Uploads:**
Users can upload their own `.csv` files directly through the frontend UI using the **"+"** button next to "Data sources". The backend securely writes the file to the `data_pipeline/raw/` registry directory and immediately invokes the `load_all_tables()` function in memory. This automatically parses the new schema types, cleans the data, and mounts the file as a new DuckDB Table instantly, meaning the LLM can query it seconds later without requiring a server reboot.

### B. The Chat Pipeline (`chat_pipeline/`)
**What it does:**
This is the core execution loop. It handles caching, prompt engineering, contacting Groq/OpenAI, and validating the returned SQL against DuckDB.

**File Breakdown:**

1.  `sql_generator.py` - The primary entry point. Constructs the prompt using the `registry.json` schema, the user's question, and conversation history, and sends it to the fast Groq LLM to generate raw SQL.

2.  `sql_validator.py` - Validates the raw SQL generated by the LLM against the DuckDB schema. Ensures no hallucinated tables or columns exist and that relations are valid.

3.  `retry.py` - Manages the auto-correction loop. If `sql_validator.py` catches an error or DuckDB throws an execution exception, this script feeds the error message backward to the LLM up to 3 times to let it self-heal.

4.  `explainer.py` - Takes the final executed JSON data output from DuckDB and sends it to a second LLM to format a friendly, plain English summary of the results.

5.  `provenance.py` - Uses Regex to scan the final SQL query and extract exactly which CSV tables were used, so the UI can display clickable source badges.

6.  `cache.py` - Creates a deterministic hash of the user's question. Checks Upstash Redis to see if the semantic question has been asked recently to skip LLM generation entirely.

7.  `db.py` - Interacts with the local SQLite storage to pull previous conversation turns (enabling multi-turn chat) and saves new messages.

**Testing (`chat_pipeline/tests/`):**
-   `test_sql_validator.py`: Ensures hallucinated tables/columns are caught and syntax is verified.
-   `test_cache.py`: Verifies deterministic hashing (so asking the exact same question doesn't waste LLM tokens).
-   `test_provenance.py`: Tests regex extraction of table names from complex SQL joins to power UI source tags.

### C. The Voice Pipeline (`voice_pipeline/`)
**What it does & The Flow:**
The UI overlay establishes a real-time WebRTC connection to a LiveKit cloud server. A headless Python worker (`livekit_agent.py`) listens to this audio stream on the backend.
`Microphone ➔ LiveKit WebRTC ➔ Silero VAD (Detects when user stops speaking) ➔ Deepgram Nova-3 (Speech to Text) ➔ PharmaIQ Backend API (Generates SQL & Answer) ➔ Deepgram Aura (Text to Speech) ➔ LiveKit Data Channel (Syncs text to UI bubbles) ➔ User Hears Response`.

**Testing (`voice_pipeline/tests/`):**
- `test_smoke.py`: Tests the initialization of the `PharmaIQLLM` agent wrapper to ensure metadata (like `message_id` and `llm_used`) is correctly broadcasted back to the UI state.

---

## 5. UI, Backend, and "Gold" Evaluations (`eval_and_metrics/`)

To ensure absolute reliability in a pharmaceutical context, PharmaIQ 1.0 continuously monitors **Performance**, **Quality**, and **User Satisfaction** through a combination of lightweight telemetry and offline LLM-as-a-Judge evaluations.

**File Breakdown:**

1.  `eval/golden_dataset.py` - Contains hundreds of complex "Gold Standard" pharmaceutical questions, paired perfectly with their known, human-verified SQL queries and database results.
2.  `eval/gold_eval.py` - The execution script that runs the entire chat pipeline against `golden_dataset.py`. It compares the generated SQL against the verified Gold SQL to track accuracy/regression across pipeline or LLM changes.
3.  `eval/async_judge.py` - The background "LLM Judge" worker. After a user gets their answer in the UI, this script asynchronously scores the query (from 1-10) on Relevance and Faithfulness without blocking the API.
4.  `monitoring/logger.py` - Structured JSON logging utility used across the app to emit clean telemetry events (like `chat_query_complete`, `table_loaded`, `llm_fallback_triggered`).
5.  `monitoring/metrics_db.py` - Manages inserts into the SQLite metrics tables to permanently store the telemetry from `logger.py` and the 1-10 scores from the `async_judge.py`.

### A. Performance Metrics (Telemetry)
Captured instantly on the backend for every single query to monitor system health and latency.
*   **Total Latency (ms):** The end-to-end time from receiving the HTTP request to returning the final JSON. Crucial for monitoring Groq's streaming speed.
*   **Cache Hit Rate:** The percentage of queries intercepted by Upstash Redis. *Why we track it:* To reduce expensive LLM tokens for identical, repeatedly asked questions.
*   **Fallback Rate:** How often the system is forced to abandon the fast Groq Llama 3 model and utilize the slower, high-reasoning OpenAI GPT-4o model to fix a syntax error.
*   **Retry Count:** How many times the generated SQL failed local DuckDB validation and had to be passed back to the LLM to fix hallucinated column names.
*   **Success Rate:** The percentage of questions that resulted in a successfully executed SQL query and valid answer.

### B. LLM Judge Metrics (The "Vibe Check")
Because SQL correctness doesn't always guarantee a *good human answer*, `async_judge.py` takes the user's prompt, the generated SQL, and the final English answer, and passes them to a secondary "LLM Judge" to score them exclusively from 1 to 10:
*   **SQL Correctness / Schema Precision:** *How:* The judge compares the generated SQL against the injected `registry.json` schema. *Why:* To ensure the LLM didn't hallucinate a column that doesn't exist, and that it actually joined the correct dimensions.
*   **Answer Relevance:** *How:* The judge evaluates if the final English explanation actually addresses the user's original plain-english question. *Why:* To catch edge cases where the SQL query was mathematically correct, but the LLM provided an irrelevant summary.
*   **Avg Faithfulness:** *How:* The judge strictly compares the raw JSON output of the SQL query against the final English answer. *Why:* This is a critical hallucination check. If the SQL returned `[{"sales": 500}]` but the English answer claims "Sales were 1,500", the faithfulness score tanks to 0.

### C. User Satisfaction (RLHF Data)
*   **Thumbs Up  / Thumbs Down :** Calculated strictly from the user's clicks on the frontend UI. *Why:* This serves as explicit human preference data. If an answer gets a Thumbs Down despite having a 10/10 Judge score, it indicates our prompt engineering or Golden Dataset is flawed. This raw data feeds directly into our future **Direct Preference Optimization (DPO)** pipeline to fine-tune open-source models (see Section 7).

### D. The "Gold Eval" (Offline Regression Testing)
*   **What it is & How it Works:** Before merging any new code to `main` (or swapping the Groq LLM for a newer model), developers run `evaluate.py`. It executes the entire chat pipeline against all questions in the Gold Dataset. If accuracy drops below 95%, the build fails. It guarantees that we never accidentally deploy a software update that corrupts how `fact_rx.csv` joins to `hcp_dim.csv`.

---

## 6. End-to-End Example Flow: "How many doctors are there?"

Let's map out exactly what happens under the hood when a user types (or speaks) a simple question:

1. **Frontend Request**: The React `SendMessage` API hits `POST /api/v1/chat`.
2. **Cache Check (Redis)**: The system checks if anyone has asked this exact semantic question recently.
   - *If Yes*: It returns the saved answer instantly.
   - *If No*: It proceeds to the primary pipeline.
3. **Context Gathering**: The backend fetches the last 5 chat messages from SQLite to establish multi-turn conversation history.
4. **Prompt Construction**: The backend merges the user's question, the conversation history, and the complete DuckDB schema registry (tables, columns, types, foreign keys).
5. **Primary SQL Generation**: The ultra-fast Groq LLM streams back a tentative query:
   ```sql
   SELECT COUNT(DISTINCT hcp_id) AS total_doctors FROM hcp_dim;
   ```
6. **SQL Validation & Retry Loop**: 
   - The query is intercepted and validated locally against the DuckDB schema. 
   - If it's invalid (e.g., hallucinates a column), it is sent back to the LLM with the error for up to 3 retries.
   - If Groq fails 3 times, the **OpenAI GPT-4o Fallback** is triggered to execute a final, high-reasoning attempt.
7. **Execution**: The validated SQL query is run against the in-memory DuckDB engine. 
   - *Output*: `[{"total_doctors": 15420}]`.
8. **Provenance & Chart Hinting**: 
   - Regex scans the raw SQL to identify which tables were used (attaching `hcp_dim.csv` as a clickable source badge).
   - Data outputs are recursively analyzed to detect if a specific Chart (Bar/KPI/Table) should be recommended to the UI.
9. **Explanation Generation**: A second LLM call translates the raw JSON data output into a friendly human response: *"There are currently 15,420 unique healthcare providers registered in the database."*
10. **UI Display**: The React frontend receives the payload and renders the message bubble, the large KPI integer (15k), the SQL toggle block, the source badge, and the Thumbs feedback buttons simultaneously.
11. **Background Async Sync**: 
    - The interaction is saved to SQLite.
    - An Async Task assigns it scores (Faithfulness: 10/10, Relevance: 10/10) to update the `/metrics` dashboard without blocking the user's view.

---

## 7. Future Roadmap: RLHF Fine-Tuning

To continually improve accuracy and conform to custom pharmaceutical reporting styles, PharmaIQ 1.0 is instrumented for **Reinforcement Learning from Human Feedback (RLHF)** using **Direct Preference Optimization (DPO)**.

- **Data Collection**: Every interaction records the user's prompt, the generated SQL, and `user_feedback` (+1 for thumbs up, -1 for thumbs down).
- **The Pipeline**: Future work will extract these user preferences into a DPO-formatted dataset (`prompt`, `chosen_sql`, `rejected_sql`).
- **Fine-Tuning**: Using Unsloth or TRL, this dataset will be used to fine-tune open-source models (like Llama 3 8B) entirely locally or on dedicated cloud GPUs (vLLM/Together AI) to ensure maximum privacy and absolute accuracy on the `fact_rx.csv` schemas.
