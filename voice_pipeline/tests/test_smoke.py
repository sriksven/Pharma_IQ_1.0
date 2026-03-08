"""
Smoke tests for the voice pipeline modules.
No live API calls are made -- OpenAI and LiveKit dependencies are not contacted.
"""
import asyncio
import importlib
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

# Ensure test env vars are set before any settings import
os.environ.setdefault("GROQ_API_KEY", "test_key")
os.environ.setdefault("OPENAI_API_KEY", "test_key")
os.environ.setdefault("UPSTASH_REDIS_URL", "http://test.invalid")
os.environ.setdefault("UPSTASH_REDIS_TOKEN", "test_token")
os.environ.setdefault("SQLITE_DB_PATH", os.path.join(tempfile.gettempdir(), "pharmaiq_voice_test.db"))
os.environ.setdefault("LIVEKIT_URL", "wss://test.livekit.cloud")
os.environ.setdefault("LIVEKIT_API_KEY", "test_api_key")
os.environ.setdefault("LIVEKIT_API_SECRET", "test_api_secret_minimum_32chars_pad")


# ---------------------------------------------------------------------------
# Module imports
# ---------------------------------------------------------------------------

def test_stt_module_importable():
    from voice_pipeline import stt
    assert callable(stt.transcribe)


def test_tts_module_importable():
    from voice_pipeline import tts
    assert callable(tts.speak)


def test_livekit_agent_importable():
    mod = importlib.import_module("voice_pipeline.livekit_agent")
    assert hasattr(mod, "entrypoint")
    assert hasattr(mod, "PharmaIQLLM")
    assert hasattr(mod, "PharmaIQLLMStream")


# ---------------------------------------------------------------------------
# PharmaIQLLM class structure
# ---------------------------------------------------------------------------

def test_pharma_llm_has_chat_method():
    from voice_pipeline.livekit_agent import PharmaIQLLM
    instance = PharmaIQLLM()
    assert callable(instance.chat)


def test_pharma_llm_last_response_default_empty():
    from voice_pipeline.livekit_agent import PharmaIQLLM
    instance = PharmaIQLLM()
    assert instance.last_response == {}


def test_pharma_llm_stream_created_from_chat():
    async def _inner():
        from voice_pipeline.livekit_agent import PharmaIQLLM, PharmaIQLLMStream
        from livekit.agents.llm.chat_context import ChatContext
        instance = PharmaIQLLM()
        ctx = ChatContext()
        stream = instance.chat(chat_ctx=ctx)
        assert isinstance(stream, PharmaIQLLMStream)
        # Cancel background tasks created by LLMStream.__init__
        for attr in ("_task", "_metrics_task"):
            task = getattr(stream, attr, None)
            if task is not None:
                task.cancel()
    asyncio.run(_inner())


# ---------------------------------------------------------------------------
# LiveKit token generation (unit test -- uses real livekit-api JWT logic)
# ---------------------------------------------------------------------------

def test_livekit_token_generation():
    from livekit.api import AccessToken, VideoGrants
    token = (
        AccessToken("test_key", "test_secret_minimum_32_chars_pad_")
        .with_identity("test-user")
        .with_grants(VideoGrants(room_join=True, room="pharmaiq-test"))
        .to_jwt()
    )
    assert isinstance(token, str)
    assert len(token) > 20


def test_livekit_token_has_three_jwt_parts():
    from livekit.api import AccessToken, VideoGrants
    token = (
        AccessToken("key123456789012", "secret_at_least_32_characters_long_!")
        .with_identity("user-1")
        .with_grants(VideoGrants(room_join=True, room="room-1"))
        .to_jwt()
    )
    parts = token.split(".")
    assert len(parts) == 3
