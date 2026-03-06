"""
Text-to-speech using OpenAI TTS API.
"""

import openai


def speak(text: str, voice: str = "alloy") -> bytes:
    """Convert text to speech. Returns raw audio bytes (mp3)."""
    from app.config import settings
    client = openai.OpenAI(api_key=settings.openai_api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )
    return response.content
