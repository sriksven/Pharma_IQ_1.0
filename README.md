# 🧬 PharmaIQ 1.0

![PharmaIQ Banner](https://img.shields.io/badge/PharmaIQ-1.0-blue?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python) ![React](https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react) ![FastAPI](https://img.shields.io/badge/FastAPI-0.103+-009688?style=for-the-badge&logo=fastapi) ![DuckDB](https://img.shields.io/badge/DuckDB-Fast-yellow?style=for-the-badge)

**PharmaIQ 1.0** is an intelligent, natural language analytics assistant designed specifically for pharmaceutical sales data. It allows users to ask plain English questions, instantly generating complex SQL queries executed against a blazing-fast in-memory DuckDB engine. 

The platform features a modern React frontend, a ChatGPT-style real-time voice interface powered by Deepgram and LiveKit, dynamic on-the-fly CSV uploads, and a robust multi-LLM routing system (Groq Llama 3 & OpenAI GPT-4o) ensuring high speed and absolute accuracy.

---

## ✨ Key Features

- 🗣️ **Real-Time Voice UI**: A highly responsive, full-screen audio interface using **Deepgram Nova-3 / Aura** and **LiveKit** WebRTC. Speak to the agent and hear instant, contextual responses.
- ⚡ **Lightning Fast Analytics**: Uses **Groq's Llama 3 70B** to generate SQL in milliseconds, executing it instantly against **DuckDB**. 
- 🛡️ **Self-Healing SQL**: If Groq hallucinates a column, an autonomous **OpenAI GPT-4o** fallback agent steps in to debug and correct the query seamlessly.
- 📁 **Dynamic Data Uploads**: Drag and drop new `.csv` datasets (like Prescriptions, Rep Activity, HCPs) directly into the UI. The backend automatically maps the schema to DuckDB—no server restart required.
- 📈 **Smart Data Viz**: Automatically interprets query outputs to generate Recharts-powered KPIs, Bar Charts, and Tables.
- 🔄 **Evaluation & RLHF Ready**: Every interaction is evaluated for faithfulness and relevance by an LLM judge, and user Feedback (+1/-1) is collected to prep for future **Direct Preference Optimization (DPO)** fine-tuning.

---

## 📚 Documentation
For a deep dive into the architecture, multi-LLM routing, testing strategies, and a step-by-step breakdown of how a user question turns into a chart, please read the comprehensive overview:

👉 **[Read the Full Technical Overview & Architecture Guide](docs/overview.md)**

👉 **[View the RLHF Fine-Tuning Future Plan](docs/future_rlhf_plan.md)**

---

## 🛠️ The Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React + Vite + CSS Modules | High-performance, reactive UI. |
| **Backend** | FastAPI (Python) | Async API routing and execution loops. |
| **Query Engine** | DuckDB | In-memory massive parallel SQL execution over CSVs. |
| **Primary LLMs** | Groq (Llama 3 70B) | Ultra-low latency SQL Generation & Explanation. |
| **Fallback LLMs** | OpenAI (GPT-4o) | Complex reasoning and autonomous query fixing. |
| **Cache & State** | SQLite + Upstash Redis | Semantic caching and persistent interaction history. |
| **Voice Agents** | Deepgram + LiveKit | Sub-second STT/TTS via WebRTC data channels. |

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Configure
```bash
git clone <repo>
cd PharmaIQ1.0
cp .env.example .env
```
*You must populate the `.env` file with your `GROQ_API_KEY`, `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `UPSTASH_*`, and `LIVEKIT_*` credentials. See `docs/overview.md` for details.*

### 2. Start the Backend API
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
*The API runs at `http://localhost:8000`. Validates schemas and maps DuckDB views on boot.*

### 3. Start the Frontend UI
```bash
cd frontend
npm install
npm run dev
```
*The UI runs at `http://localhost:5173`.*

### 4. Start the Voice Worker (Optional)
In a third terminal window at the project root:
```bash
DEEPGRAM_API_KEY=your_key LIVEKIT_URL=your_wss LIVEKIT_API_KEY=your_key LIVEKIT_API_SECRET=your_secret python -m voice_pipeline.livekit_agent dev
```

---

## 🧪 Running Evaluations & Tests
The project features a strict **"Gold Eval"** regression suite to ensure new LLMs or code modifications do not degrade SQL generation accuracy. 

To run the entire suite (Data Pipeline, Chat Pipeline, Validators, and Voice Smoke Tests):
```bash
export PYTHONPATH=$(pwd):$(pwd)/backend
pytest data_pipeline/tests/ chat_pipeline/tests/ eval_and_metrics/tests/ backend/tests/ voice_pipeline/tests/ -v
```

---
*Built for modern pharma analytics.*
