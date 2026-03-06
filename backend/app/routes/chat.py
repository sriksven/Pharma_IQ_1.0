"""
POST /api/v1/chat -- core chat endpoint
"""

import time
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from chat_pipeline.cache import get_cached, set_cached
from chat_pipeline.retry import run_with_retry
from chat_pipeline.provenance import build_provenance
from chat_pipeline.explainer import explain
from chat_pipeline.db import (
    create_session,
    save_message,
    get_session_messages,
    get_session_turn_count,
    update_session_title,
)
from app.utils.chart_hint import infer_chart_hint
from ml_pipeline.monitoring.logger import JSONLogger

router = APIRouter()
logger = JSONLogger()


class ChatRequest(BaseModel):
    session_id: str | None = None
    question: str


@router.post("/chat")
async def chat(req: ChatRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    session_id = req.session_id or str(uuid.uuid4())
    create_session(session_id, title=question[:60])

    logger.log("query_received", {"session_id": session_id, "question": question[:80]})
    t_start = time.time()

    # Save user message
    save_message(session_id, "user", question)

    # Cache check
    cached = get_cached(question)
    if cached:
        cached["cache_hit"] = True
        cached["session_id"] = session_id
        logger.log("cache_hit", {"session_id": session_id})
        return cached

    # Run SQL pipeline with retry
    result_df, sql, llm_used, retry_count, sql_error = run_with_retry(question)

    if sql_error and result_df is None:
        save_message(session_id, "assistant", "I was unable to answer that question.", llm_used=llm_used)
        raise HTTPException(status_code=500, detail=f"SQL execution failed after retries: {sql_error}")

    # Generate provenance and chart hint
    provenance = build_provenance(sql)
    chart_hint = infer_chart_hint(result_df) if result_df is not None else None

    # Generate explanation
    answer, explain_llm, fallback_reason = explain(question, sql, result_df)
    if llm_used == "groq" and explain_llm == "openai":
        llm_used = "openai"

    latency_ms = int((time.time() - t_start) * 1000)

    # Save assistant message
    message_id = save_message(
        session_id,
        "assistant",
        answer,
        sql_query=sql,
        provenance=provenance,
        llm_used=llm_used,
        cache_hit=False,
    )

    # Update session title from first question
    turn_count = get_session_turn_count(session_id)
    if turn_count <= 2:
        update_session_title(session_id, question[:60])

    response = {
        "session_id": session_id,
        "message_id": message_id,
        "answer": answer,
        "sql": sql,
        "provenance": provenance,
        "chart_hint": chart_hint,
        "llm_used": llm_used,
        "fallback_reason": fallback_reason,
        "cache_hit": False,
        "latency_ms": latency_ms,
        "retry_count": retry_count,
    }

    # Write to cache
    set_cached(question, response)

    logger.log("answer_generated", {"session_id": session_id, "latency_ms": latency_ms})
    return response
