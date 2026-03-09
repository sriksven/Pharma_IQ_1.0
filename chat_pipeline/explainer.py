"""
Generates plain English answers from SQL results using Groq.
Falls back to openai/gpt-oss-20b if primary model fails.
"""

import os
import sys
import pandas as pd

from groq import Groq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from eval_and_metrics.monitoring.logger import JSONLogger

logger = JSONLogger()

GROQ_EXPLAIN_MODEL = "openai/gpt-oss-120b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-20b"
MAX_ROWS_IN_PROMPT = 20



def _df_to_markdown(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "(no results)"
    return df.head(MAX_ROWS_IN_PROMPT).to_markdown(index=False)


def _build_messages(
    question: str, sql: str, result_df: pd.DataFrame, conversation_history: list = None
) -> list:
    table_md = _df_to_markdown(result_df)

    system_prompt = (
        "You are a pharmaceutical data analyst. "
        "Answer the user's question based on the SQL query results below. "
        "If there is prior conversation context, use it to understand follow-up questions. "
        "Write in clear, direct prose. No bullet points unless listing items. "
        "Do NOT include long dashes (--) anywhere in your response. "
        "Include one proactive insight beyond the literal answer. "
        "Keep it under 200 words."
    )

    user_message = (
        f"Question: {question}\n\n"
        f"SQL executed:\n{sql}\n\n"
        f"Results:\n{table_md}"
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Inject prior turns for follow-up context (skip the last user msg to avoid duplication)
    if conversation_history:
        messages.extend(conversation_history[:-1] if conversation_history[-1]["role"] == "user" else conversation_history)

    messages.append({"role": "user", "content": user_message})
    return messages, system_prompt


def explain(
    question: str,
    sql: str,
    result_df: pd.DataFrame,
    conversation_history: list = None,
) -> tuple[str, str, str | None, str]:
    """
    Generate a plain English explanation of query results.

    Returns:
        (answer, llm_used, fallback_reason, system_prompt)
        fallback_reason is None if primary Groq model was used successfully.
    """
    from app.config import settings

    messages, system_prompt = _build_messages(question, sql, result_df, conversation_history)

    client = Groq(api_key=settings.groq_api_key)

    # Try Groq primary first
    try:
        response = client.chat.completions.create(
            model=GROQ_EXPLAIN_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )
        answer = response.choices[0].message.content.strip()
        logger.log("answer_generated", {"model": GROQ_EXPLAIN_MODEL})
        return answer, "groq", None, system_prompt

    except Exception as groq_err:
        logger.log("groq_error", {"reason": str(groq_err), "step": "explain"})
        logger.log("fallback_triggered", {"model": GROQ_FALLBACK_MODEL})

        # Try Groq fallback
        try:
            response = client.chat.completions.create(
                model=GROQ_FALLBACK_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=512,
            )
            answer = response.choices[0].message.content.strip()
            logger.log("answer_generated", {"model": GROQ_FALLBACK_MODEL})
            return answer, "groq_fallback", "Primary model failed, used fallback", system_prompt
        except Exception as fallback_err:
            logger.log("groq_error", {"reason": str(fallback_err), "step": "explain_fallback"})
            raise RuntimeError(f"Groq explanation failed entirely: {fallback_err}") from fallback_err


