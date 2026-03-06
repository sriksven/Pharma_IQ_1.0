from fastapi import APIRouter, HTTPException
from chat_pipeline.db import get_sessions, get_session_messages, delete_session

router = APIRouter()


@router.get("/sessions")
def list_sessions():
    return {"sessions": get_sessions()}


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    messages = get_session_messages(session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session_id": session_id, "messages": messages}


@router.delete("/sessions/{session_id}")
def remove_session(session_id: str):
    delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}
