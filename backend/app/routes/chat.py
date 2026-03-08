"""
POST /api/v1/chat -- core chat endpoint
"""

import time
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks
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
from eval_and_metrics.monitoring.logger import JSONLogger
from eval_and_metrics.eval.judge import run_eval
from eval_and_metrics.monitoring.metrics import record_metrics

router = APIRouter()
logger = JSONLogger()

NO_ANSWER_MSG = (
    "I'm sorry, I don't have enough information in the dataset to answer that question. "
    "Try asking about prescriptions (nrx/trx), doctor specialties, sales rep activity, "
    "territory market share, or payer mix — those are the areas covered by the data."
)

# Number of prior turns to include as memory context
HISTORY_WINDOW = 6


class ChatRequest(BaseModel):
    session_id: str | None = None
    question: str


def _build_conversation_history(session_id: str) -> list:
    """Load the last HISTORY_WINDOW messages from DB as LLM conversation history."""
    messages = get_session_messages(session_id)
    # Take only the last N messages, skip system-only or empty
    recent = [m for m in messages if m["role"] in ("user", "assistant") and m["content"]]
    recent = recent[-HISTORY_WINDOW:]
    return [{"role": m["role"], "content": m["content"]} for m in recent]


@router.post("/chat")
async def chat(req: ChatRequest, background_tasks: BackgroundTasks):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    session_id = req.session_id or str(uuid.uuid4())
    create_session(session_id, title=question[:60])

    logger.log("query_received", {"session_id": session_id, "question": question[:80]})
    t_start = time.time()

    # Save user message
    save_message(session_id, "user", question)

    # --- Cache check ---
    # Fix: on cache hit, rebind session_id to the CURRENT session and save the
    # assistant message to the current session's SQLite history so memory works.
    cached = get_cached(question)
    if cached:
        cached_response = dict(cached)
        cached_response["cache_hit"] = True
        cached_response["session_id"] = session_id

        # Save cached assistant reply to the current session
        save_message(
            session_id=session_id,
            role="assistant",
            content=cached_response.get("answer", ""),
            sql_query=cached_response.get("sql"),
            provenance=cached_response.get("provenance"),
            llm_used=cached_response.get("llm_used"),
            cache_hit=True,
            chart_hint=cached_response.get("chart_hint"),
            chart_data=cached_response.get("chart_data"),
        )

        logger.log("cache_hit", {"session_id": session_id})
        return cached_response

    # --- Build conversation history for memory ---
    conversation_history = _build_conversation_history(session_id)

    # Run SQL pipeline with retry + history for multi-turn context
    sql_start = time.time()
    result_df, sql, llm_used, retry_count, sql_error, sql_system_prompt = run_with_retry(
        question, conversation_history=conversation_history
    )
    sql_gen_latency_ms = int((time.time() - sql_start) * 1000)

    # --- Fix: graceful no-answer instead of HTTP 500 ---
    if sql_error and result_df is None:
        message_id = save_message(
            session_id, "assistant", NO_ANSWER_MSG, llm_used=llm_used
        )

        total_fail_lat = int((time.time() - t_start) * 1000)
        background_tasks.add_task(
            record_metrics,
            message_id=message_id,
            total_latency_ms=total_fail_lat,
            sql_gen_latency_ms=sql_gen_latency_ms,
            explain_latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            retry_count=retry_count,
            llm_used=llm_used,
            cache_hit=False,
            tables_joined=0,
            session_turn_count=get_session_turn_count(session_id),
            failed=True,
        )
        # Return 200 with a friendly answer so the frontend displays it normally
        return {
            "session_id": session_id,
            "message_id": message_id,
            "answer": NO_ANSWER_MSG,
            "sql": None,
            "provenance": [],
            "chart_hint": None,
            "chart_data": [],
            "llm_used": llm_used,
            "fallback_reason": sql_error,
            "cache_hit": False,
            "latency_ms": total_fail_lat,
            "retry_count": retry_count,
        }

    # Generate provenance and chart hint
    provenance = build_provenance(sql)
    chart_hint = infer_chart_hint(result_df) if result_df is not None else None

    # Generate explanation with conversation history for follow-up context
    exp_start = time.time()
    answer, explain_llm, fallback_reason, explain_system_prompt = explain(
        question, sql, result_df, conversation_history=conversation_history
    )
    explain_latency_ms = int((time.time() - exp_start) * 1000)

    if explain_llm == "groq_fallback":
        llm_used = explain_llm

    latency_ms = int((time.time() - t_start) * 1000)

    # Save assistant message
    message_id = save_message(
        session_id=session_id,
        role="assistant",
        content=answer,
        sql_query=sql,
        provenance=provenance,
        llm_used=llm_used,
        cache_hit=False,
        sql_system_prompt=sql_system_prompt,
        explain_system_prompt=explain_system_prompt,
        chart_hint=chart_hint,
        chart_data=result_df.to_dict(orient="records") if result_df is not None else [],
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
        "chart_data": result_df.to_dict(orient="records") if result_df is not None else [],
        "llm_used": llm_used,
        "fallback_reason": fallback_reason,
        "cache_hit": False,
        "latency_ms": latency_ms,
        "retry_count": retry_count,
    }

    # Write to cache
    set_cached(question, response)

    # Launch background tasks
    background_tasks.add_task(
        run_eval,
        message_id=message_id,
        question=question,
        sql=sql,
        answer=answer,
        chart_data=result_df.to_dict(orient="records") if result_df is not None else [],
        sql_error=None,
    )

    background_tasks.add_task(
        record_metrics,
        message_id=message_id,
        total_latency_ms=latency_ms,
        sql_gen_latency_ms=sql_gen_latency_ms,
        explain_latency_ms=explain_latency_ms,
        input_tokens=0,
        output_tokens=0,
        retry_count=retry_count,
        llm_used=llm_used,
        cache_hit=False,
        tables_joined=len(provenance),
        session_turn_count=turn_count,
        failed=False,
    )

    logger.log("answer_generated", {"session_id": session_id, "latency_ms": latency_ms})
    return response

