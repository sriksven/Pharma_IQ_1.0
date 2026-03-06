from fastapi import APIRouter, UploadFile, File
from fastapi.responses import Response
from voice_pipeline.stt import transcribe
from voice_pipeline.tts import speak
from pydantic import BaseModel

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
