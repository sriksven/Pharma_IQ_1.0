"""
Speech-to-text using OpenAI Whisper API.
"""

import openai


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Transcribe audio bytes to text using Whisper."""
    from app.config import settings
    client = openai.OpenAI(api_key=settings.openai_api_key)
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes),
    )
    return response.text
