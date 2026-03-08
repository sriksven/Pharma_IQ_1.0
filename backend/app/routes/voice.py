import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from voice_pipeline.stt import transcribe
from voice_pipeline.tts import speak

router = APIRouter()


@router.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    text = transcribe(audio_bytes, file.filename)
    return {"text": text}


class SpeakRequest(BaseModel):
    text: str
    voice: str = "alloy"


@router.post("/voice/speak")
def speak_text(req: SpeakRequest):
    audio = speak(req.text, req.voice)
    return Response(content=audio, media_type="audio/mpeg")


class TokenRequest(BaseModel):
    session_id: str | None = None
    room_name: str | None = None
    identity: str | None = None


@router.post("/voice/token")
def create_voice_token(req: TokenRequest):
    """Generate a LiveKit room access token for the frontend."""
    from app.config import settings
    from livekit.api import AccessToken, VideoGrants

    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise HTTPException(
            status_code=503,
            detail="LiveKit is not configured. Set LIVEKIT_API_KEY and LIVEKIT_API_SECRET.",
        )

    room = req.room_name or (
        f"pharmaiq-{req.session_id}" if req.session_id else f"pharmaiq-{uuid.uuid4().hex[:8]}"
    )
    identity = req.identity or f"user-{uuid.uuid4().hex[:8]}"

    token = (
        AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(VideoGrants(room_join=True, room=room))
        .to_jwt()
    )

    return {
        "token": token,
        "url": settings.livekit_url,
        "room": room,
        "identity": identity,
    }
