# Voice Pipeline

Real-time voice interface for PharmaIQ powered by [LiveKit](https://livekit.io/).

```
user speaks → Silero VAD → Whisper STT → PharmaIQ chat pipeline → OpenAI TTS → user hears
```

Transcripts appear in the chat thread alongside text messages. SQL, provenance tags, and chart hints are forwarded through the WebRTC data channel so voice turns look the same as typed ones.

---

## Components

| File | Purpose |
|---|---|
| `livekit_agent.py` | LiveKit worker -- joins a room, runs the VAD→STT→LLM→TTS pipeline |
| `stt.py` | Standalone Whisper wrapper (used by the REST `/voice/transcribe` endpoint) |
| `tts.py` | Standalone OpenAI TTS wrapper (used by the REST `/voice/speak` endpoint) |

The agent's "LLM" step calls the existing FastAPI `POST /api/v1/chat` endpoint, so the full SQL-generation, retry, cache, eval, and metrics pipeline is reused without duplication.

---

## Prerequisites

- LiveKit Cloud project (or self-hosted LiveKit server) -- [cloud.livekit.io](https://cloud.livekit.io)
- OpenAI API key (Whisper + TTS)
- Backend requirements installed: `pip install -r backend/requirements.txt`
- Requires `livekit-agents>=1.0.0` (included in `backend/requirements.txt`)

---

## Configuration

Add the following to your `.env` file in the project root:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
```

`OPENAI_API_KEY` must also be set (already required by the rest of the app).

---

## Running the agent

Start the LiveKit worker in a separate terminal **alongside** the FastAPI backend and Vite dev server:

```bash
LIVEKIT_URL=wss://... LIVEKIT_API_KEY=... LIVEKIT_API_SECRET=... \
OPENAI_API_KEY=... \
    python -m voice_pipeline.livekit_agent dev
```

`dev` is the LiveKit CLI mode -- it connects to your LiveKit server and waits for rooms to dispatch jobs to the agent.

If the env vars are already present in your shell (loaded from `.env` via `direnv` or similar), the command shortens to:

```bash
python -m voice_pipeline.livekit_agent dev
```

To point the agent at a non-default backend URL (e.g. staging):

```bash
PHARMAIQ_CHAT_URL=http://my-backend:8000/api/v1/chat \
    python -m voice_pipeline.livekit_agent dev
```

---

## How a voice session works

1. User clicks the mic button in the chat input bar.
2. Frontend calls `POST /api/v1/voice/token` with the current `session_id`.
3. Backend generates a LiveKit JWT for a room named `pharmaiq-{session_id}`.
4. Frontend connects to the LiveKit room and enables the microphone.
5. The agent worker picks up the room job automatically.
6. **Voice loop:**
   - Silero VAD detects the end of an utterance.
   - Whisper transcribes the audio.
   - The agent calls `POST /api/v1/chat` with the transcript, tied to the same `session_id` as the text chat.
   - The answer is spoken aloud via OpenAI TTS.
   - Both the user transcript and assistant answer are sent over the data channel so they appear in the chat thread immediately.
7. User clicks the mic button again to disconnect.

---

## REST endpoints (no LiveKit required)

The backend also exposes simple HTTP endpoints for one-shot audio:

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/voice/transcribe` | Upload audio file → returns `{"text": "..."}` |
| `POST` | `/api/v1/voice/speak` | `{"text": "...", "voice": "alloy"}` → returns `audio/mpeg` |
| `POST` | `/api/v1/voice/token` | `{"session_id": "..."}` → returns LiveKit JWT + room info |
