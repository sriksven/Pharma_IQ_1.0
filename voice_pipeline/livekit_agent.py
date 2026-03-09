"""
LiveKit voice agent for PharmaIQ -- compatible with livekit-agents 1.x.

Pipeline:
  user speaks -> Silero VAD -> Deepgram Nova-3 STT
  -> PharmaIQ /api/v1/chat HTTP endpoint
  -> Deepgram Aura TTS -> user hears the answer

The agent also publishes data-channel messages so the frontend can display
transcripts in the existing chat thread without an extra API call.

Run from the project root (after pip install -r backend/requirements.txt):

    LIVEKIT_URL=wss://your-project.livekit.cloud \
    LIVEKIT_API_KEY=your_key \
    LIVEKIT_API_SECRET=your_secret \
    OPENAI_API_KEY=your_openai_key \
    DEEPGRAM_API_KEY=your_deepgram_key \
        python -m voice_pipeline.livekit_agent dev

The backend FastAPI server must also be running on localhost:8000 (default),
or set PHARMAIQ_CHAT_URL to point at a different host.
"""

import asyncio
import json
import logging
import os
import sys

import httpx
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.llm.llm import DEFAULT_API_CONNECT_OPTIONS
from livekit.agents.types import APIConnectOptions
from livekit.plugins import deepgram
from livekit.plugins import silero

# Ensure the project root is on sys.path so pipeline imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)

# The FastAPI backend chat endpoint; override with PHARMAIQ_CHAT_URL env var
CHAT_ENDPOINT = os.getenv("PHARMAIQ_CHAT_URL", "http://localhost:8000/api/v1/chat")


class PharmaIQLLM(llm.LLM):
    """
    Custom LLM that routes voice queries through the PharmaIQ FastAPI chat
    endpoint, reusing the full SQL-generation, retry, cache, eval, and
    metrics pipeline without duplication.
    """

    def __init__(self, publish_cb=None) -> None:
        super().__init__()
        self.publish_cb = publish_cb

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        **kwargs,
    ) -> "PharmaIQLLMStream":
        return PharmaIQLLMStream(
            self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
        )


class PharmaIQLLMStream(llm.LLMStream):
    """
    Async stream that calls /api/v1/chat with the user's question and
    yields a single ChatChunk containing the plain-text answer.
    """

    def __init__(
        self,
        llm_instance: PharmaIQLLM,
        *,
        chat_ctx: llm.ChatContext,
        tools: list,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(llm_instance, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options)
        self._pharma_llm = llm_instance

    async def _run(self) -> None:
        # Extract the most recent user message
        question = ""
        for msg in reversed(self._chat_ctx.items):
            if isinstance(msg, llm.ChatMessage) and msg.role == "user":
                # In 1.x, content is list[ChatContent]; use text_content helper
                text = msg.text_content if hasattr(msg, "text_content") else str(msg.content)
                question = text or ""
                break

        if not question:
            return

        # Read the session_id embedded in the system message by entrypoint
        session_id: str | None = None
        for msg in self._chat_ctx.items:
            if isinstance(msg, llm.ChatMessage) and msg.role == "system":
                raw = msg.text_content if hasattr(msg, "text_content") else str(msg.content)
                for line in (raw or "").splitlines():
                    if line.startswith("SESSION_ID:"):
                        session_id = line.split("SESSION_ID:", 1)[1].strip()
                        break

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    CHAT_ENDPOINT,
                    json={"question": question, "session_id": session_id},
                )
                resp.raise_for_status()
                data = resp.json()
                # Status: thinking finished
                answer = data.get("answer", "I could not process that query.")

                if self._pharma_llm.publish_cb:
                    asyncio.create_task(
                        self._pharma_llm.publish_cb(
                            {
                                "type": "assistant",
                                "text": answer,
                                "message_id": data.get("message_id"),
                                "sql": data.get("sql"),
                                "provenance": data.get("provenance", []),
                                "chart_hint": data.get("chart_hint"),
                                "llm_used": data.get("llm_used"),
                                "cache_hit": data.get("cache_hit", False),
                            }
                        )
                    )

        except Exception as exc:
            logger.error("PharmaIQ chat endpoint error: %s", exc)
            answer = "I encountered an error processing your query. Please try again."

        self._event_ch.send_nowait(
            llm.ChatChunk(
                id="pharma_iq",
                delta=llm.ChoiceDelta(role="assistant", content=answer),
            )
        )


async def entrypoint(ctx: JobContext) -> None:
    # Derive session_id from the room name (format: "pharmaiq-{session_id}")
    session_id: str | None = None
    room_name: str = ctx.room.name or ""
    if room_name.startswith("pharmaiq-"):
        session_id = room_name[len("pharmaiq-"):]

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Embed session_id in the system instructions so PharmaIQLLMStream can read it
    system_text = (
        "You are PharmaIQ, an intelligent pharmaceutical data assistant. "
        "Answer questions about prescriptions, sales reps, territories, and "
        "payer mix. Keep voice responses concise and suitable for speech."
    )
    if session_id:
        system_text += f"\nSESSION_ID:{session_id}"

    pharma_llm = PharmaIQLLM()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=pharma_llm,
        tts=deepgram.TTS(model="aura-asteria-en"),
        vad=silero.VAD.load(
            min_speech_duration=0.3,
            min_silence_duration=0.5,
            prefix_padding_duration=0.2,
        ),
    )

    async def _publish(payload: dict) -> None:
        """Publish a message to the data channel, with retries for transient failures."""
        logger.debug("Publishing to data channel: %s", payload)
        if not payload.get("session_id"):
            payload["session_id"] = session_id

        for attempt in range(3):
            try:
                await ctx.room.local_participant.publish_data(
                    json.dumps(payload).encode(),
                    reliable=True,
                )
                break
            except Exception as exc:
                if attempt < 2:
                    logger.warning("publish_data failed (attempt %d): %s", attempt + 1, exc)
                    await asyncio.sleep(0.5)
                else:
                    logger.error("publish_data failed after 3 attempts: %s", exc)

    pharma_llm.publish_cb = _publish
    is_speaking = False

    @session.on("agent_speech_started")
    def on_speech_started(ev) -> None:
        nonlocal is_speaking
        is_speaking = True
        logger.info("Agent started speaking")
        asyncio.create_task(_publish({"type": "status", "status": "speaking"}))

    @session.on("agent_speech_stopped")
    def on_speech_stopped(ev) -> None:
        nonlocal is_speaking
        is_speaking = False
        logger.info("Agent stopped speaking")
        asyncio.create_task(_publish({"type": "status", "status": "listening"}))

    @session.on("user_input_transcribed")
    def on_user_transcribed(ev) -> None:
        if ev.is_final:
            if is_speaking:
                logger.debug("Skipping transcription during agent speech (echo protection)")
                return
            logger.info("User transcribed: %s", ev.transcript)
            asyncio.create_task(
                _publish({"type": "user", "text": ev.transcript})
            )
            # Signal thinking
            asyncio.create_task(_publish({"type": "status", "status": "thinking"}))

    @session.on("conversation_item_added")
    def on_item_added(ev) -> None:
        item = ev.item
        if getattr(item, "role", None) == "assistant":
            text = item.text_content if hasattr(item, "text_content") else ""
            resp = pharma_llm.last_response
            logger.info("Assistant answer added to conversation")
            asyncio.create_task(
                _publish(
                    {
                        "type": "assistant",
                        "text": text or "",
                        "message_id": resp.get("message_id"),
                        "sql": resp.get("sql"),
                        "provenance": resp.get("provenance", []),
                        "chart_hint": resp.get("chart_hint"),
                        "llm_used": resp.get("llm_used"),
                        "cache_hit": resp.get("cache_hit", False),
                    }
                )
            )

    try:
        await session.start(
            agent=Agent(instructions=system_text),
            room=ctx.room,
        )
        logger.info("LiveKit agent session started for room: %s", room_name)

        # Keep the job alive until the room is empty or a timeout occurs
        while ctx.room.remote_participants:
            await asyncio.sleep(5)
            
        logger.info("No remote participants left, closing session for room: %s", room_name)
    except Exception as exc:
        logger.error("Error in LiveKit agent entrypoint: %s", exc)
    finally:
        await session.aclose()
        logger.info("LiveKit agent session closed")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
