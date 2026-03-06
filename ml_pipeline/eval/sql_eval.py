"""
LLM-as-judge evaluation of SQL correctness and efficiency.
"""

import json
import re

from groq import Groq
from openai import OpenAI
from ml_pipeline.monitoring.logger import JSONLogger

logger = JSONLogger()


def _judge_sql(question: str, sql: str, sql_error: str | None) -> dict:
    """Score SQL with rule-based checks + LLM judge."""
    # Rule-based: execution success
    execution_ok = sql_error is None

    if not execution_ok:
        return {
            "correctness": 0.0,
            "efficiency": 0.0,
            "reasoning": f"SQL failed to execute: {sql_error}",
        }

    from app.config import settings

    prompt = (
        "Given the following question and the SQL query that was generated, score the SQL.\n\n"
        f"Question: {question}\n\nSQL:\n{sql}\n\n"
        "Return a JSON object with these keys:\n"
        "- correctness (0-10): Does this SQL correctly answer the question?\n"
        "- efficiency (0-10): Is the SQL well-structured with no unnecessary complexity?\n"
        "- reasoning: One sentence explanation.\n\n"
        "Return only valid JSON. Example: {\"correctness\": 8, \"efficiency\": 7, \"reasoning\": \"...\"}"
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0,
            max_tokens=256,
        )
        text = response.choices[0].message.content.strip()
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            scores = json.loads(match.group())
            return {
                "correctness": float(scores.get("correctness", 5)) / 10,
                "efficiency": float(scores.get("efficiency", 5)) / 10,
                "reasoning": scores.get("reasoning", ""),
            }
    except Exception as exc:
        logger.log("sql_eval_error", {"error": str(exc)})

    return {"correctness": 0.5, "efficiency": 0.5, "reasoning": "Eval unavailable."}


def evaluate_sql(question: str, sql: str, sql_error: str | None = None) -> dict:
    return _judge_sql(question, sql, sql_error)
