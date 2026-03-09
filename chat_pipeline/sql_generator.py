"""
SQL generation via Groq.
Falls back to openai/gpt-oss-20b if primary model fails.
"""

import os
import re
import sys

from groq import Groq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_pipeline.registry import load_registry, get_schema_prompt
from eval_and_metrics.monitoring.logger import JSONLogger

logger = JSONLogger()

GROQ_SQL_MODEL = "openai/gpt-oss-120b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-20b"


def _strip_fences(text: str) -> str:
    """Strip markdown code fences that LLMs sometimes add despite instructions."""
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _build_system_prompt() -> str:
    registry = load_registry()
    schema = get_schema_prompt(registry)

    return f"""You are a SQL expert working with DuckDB.
Generate a DuckDB SQL query to answer the user's question.
Return only the raw SQL query. No explanation. No markdown. No code fences.

DuckDB notes:
- Tables are already registered as views. Reference them by name directly.
- Use standard SQL. Avoid non-standard DuckDB-specific syntax unless necessary.
- For date comparisons, date_id is an integer in YYYYMMDD format.
- Use STRPTIME or CAST carefully when converting dates.

{schema}"""


def generate_sql(
    question: str,
    conversation_history: list = None,
) -> tuple[str, str, str]:
    """
    Generate SQL for a question.

    Returns:
        (sql, llm_used, system_prompt) where llm_used is "groq" or "groq_fallback"
    """
    from app.config import settings

    system_prompt = _build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": question})

    # Try Groq primary first
    client = Groq(api_key=settings.groq_api_key)
    try:
        response = client.chat.completions.create(
            model=GROQ_SQL_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=1024,
        )
        sql = _strip_fences(response.choices[0].message.content.strip())
        logger.log("sql_generated", {"model": GROQ_SQL_MODEL, "question": question[:80]})
        return sql, "groq", system_prompt

    except Exception as groq_err:
        logger.log("groq_error", {"reason": str(groq_err), "step": "sql_gen"})
        logger.log("fallback_triggered", {"model": GROQ_FALLBACK_MODEL})
        
        # Try Groq fallback
        try:
            response = client.chat.completions.create(
                model=GROQ_FALLBACK_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=1024,
            )
            sql = _strip_fences(response.choices[0].message.content.strip())
            logger.log("sql_generated", {"model": GROQ_FALLBACK_MODEL, "question": question[:80]})
            return sql, "groq_fallback", system_prompt
        except Exception as fallback_err:
            logger.log("groq_error", {"reason": str(fallback_err), "step": "sql_gen_fallback"})
            raise RuntimeError(f"Groq SQL generation failed entirely: {fallback_err}") from fallback_err

