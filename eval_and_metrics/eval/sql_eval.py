"""
LLM-as-judge evaluation of SQL correctness and efficiency.
"""

import json
import re
import os

from groq import Groq
from eval_and_metrics.monitoring.logger import JSONLogger

logger = JSONLogger()

GROQ_JUDGE_MODEL = "openai/gpt-oss-120b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-20b"

_REGISTRY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data_pipeline", "registry.json"
)


def _get_schema_summary() -> str:
    """Load a compact schema summary from registry.json for the judge."""
    try:
        with open(_REGISTRY_PATH) as f:
            registry = json.load(f)
        lines = []
        for table in registry.get("tables", []):
            cols = ", ".join(c["name"] for c in table.get("columns", []))
            lines.append(f"  {table['name']} ({cols})")
        return "Available tables:\n" + "\n".join(lines)
    except Exception:
        return "(schema unavailable)"


def _judge_sql(
    question: str,
    sql: str,
    sql_error: str | None,
    sql_result: str | None = None,
) -> dict:
    """Score SQL with rule-based checks + LLM judge."""
    # Rule-based: execution success
    if sql_error:
        return {
            "correctness": 0.0,
            "efficiency": 0.0,
            "schema_precision": 0.0,
            "reasoning": f"SQL failed to execute: {sql_error}",
        }

    from app.config import settings

    schema_summary = _get_schema_summary()
    result_snippet = (sql_result or "(no result data)")[:800]

    prompt = (
        "You are a SQL code reviewer for a pharmaceutical analytics database.\n\n"
        f"{schema_summary}\n\n"
        f"User question: {question}\n\n"
        f"Generated SQL:\n{sql}\n\n"
        f"Query result (sample):\n{result_snippet}\n\n"
        "Score the SQL on three dimensions:\n"
        "- correctness (0-10): Does this SQL produce the right result to answer the question? "
        "The SQL is CORRECT if it executed successfully and its result logically answers the question. "
        "Simple, clean queries like COUNT(*) or SUM() that answer a simple question should score 9-10. "
        "Note: 'hcp_dim' contains only doctors, so COUNT(*) accurately counts doctors.\n"
        "- efficiency (0-10): Is the SQL well-structured? No unnecessary joins or subqueries?\n"
        "- schema_precision (0-10): Does it use only valid tables/columns from the schema above? "
        "Penalise only if it references non-existent columns or joins unnecessary tables.\n"
        "- reasoning: One sentence.\n\n"
        "Return ONLY a clean JSON block (do NOT wrap it in ```json blocks or any other text). Example:\n"
        "{\"correctness\": 9, \"efficiency\": 10, \"schema_precision\": 10, \"reasoning\": \"...\"}"
    )

    messages = [{"role": "user", "content": prompt}]
    client = Groq(api_key=settings.groq_api_key)

    try:
        response = client.chat.completions.create(
            model=GROQ_JUDGE_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=256,
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            scores = json.loads(match.group())
            return {
                "correctness": float(scores.get("correctness", 5)) / 10,
                "efficiency": float(scores.get("efficiency", 5)) / 10,
                "schema_precision": float(scores.get("schema_precision", 5)) / 10,
                "reasoning": scores.get("reasoning", ""),
            }
    except Exception as exc:
        logger.log("sql_eval_error", {"step": "primary", "error": str(exc)})

        try:
            response = client.chat.completions.create(
                model=GROQ_FALLBACK_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=256,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                scores = json.loads(match.group())
                return {
                    "correctness": float(scores.get("correctness", 5)) / 10,
                    "efficiency": float(scores.get("efficiency", 5)) / 10,
                    "schema_precision": float(scores.get("schema_precision", 5)) / 10,
                    "reasoning": scores.get("reasoning", ""),
                }
        except Exception as fallback_exc:
            logger.log("sql_eval_error", {"step": "fallback", "error": str(fallback_exc)})

    return {"correctness": None, "efficiency": None, "schema_precision": None, "reasoning": "Eval unavailable."}


def evaluate_sql(
    question: str,
    sql: str,
    sql_error: str | None = None,
    sql_result: str | None = None,
) -> dict:
    return _judge_sql(question, sql, sql_error, sql_result)

