"""
SQL generation via Groq Llama 3 70B.
Falls back to OpenAI GPT-4o if Groq fails.
"""

import os
import sys

from groq import Groq
from openai import OpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_pipeline.registry import load_registry, get_schema_prompt
from ml_pipeline.monitoring.logger import JSONLogger

logger = JSONLogger()

GROQ_SQL_MODEL = "llama3-70b-8192"
OPENAI_FALLBACK_MODEL = "gpt-4o"


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
) -> tuple[str, str]:
    """
    Generate SQL for a question.

    Returns:
        (sql, llm_used) where llm_used is "groq" or "openai"
    """
    from app.config import settings

    system_prompt = _build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": question})

    # Try Groq first
    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=GROQ_SQL_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=1024,
        )
        sql = response.choices[0].message.content.strip()
        logger.log("sql_generated", {"model": "groq", "question": question[:80]})
        return sql, "groq"

    except Exception as groq_err:
        logger.log("fallback_triggered", {"reason": str(groq_err), "step": "sql_gen"})

    # Fallback to OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=OPENAI_FALLBACK_MODEL,
        messages=messages,
        temperature=0,
        max_tokens=1024,
    )
    sql = response.choices[0].message.content.strip()
    logger.log("sql_generated", {"model": "openai", "question": question[:80]})
    return sql, "openai"
