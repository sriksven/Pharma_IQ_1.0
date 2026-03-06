# Voice Pipeline

Optional. Adds microphone input and spoken output.

## stt.py

Sends audio bytes to OpenAI Whisper API (`whisper-1`). Returns transcribed text string.

## tts.py

Sends text to OpenAI TTS API (`tts-1`, voice `alloy`). Returns raw MP3 bytes.

## API

- `POST /api/v1/voice/transcribe` -- multipart audio file upload, returns `{"text": "..."}`
- `POST /api/v1/voice/speak` -- JSON body `{"text": "...", "voice": "alloy"}`, returns `audio/mpeg`

## Frontend Integration

The voice route is registered in `main.py`. To wire the frontend, add a microphone button to `InputBar.jsx` that records audio using the Web Audio API and POSTs to `/api/v1/voice/transcribe`. On response, populate the input field with the returned text. Optionally, play the TTS response after the answer renders.

## Requirements

Requires `OPENAI_API_KEY` to be set. No additional packages beyond what is already in `requirements.txt`.
