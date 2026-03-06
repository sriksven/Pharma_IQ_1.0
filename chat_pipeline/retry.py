"""
Retry logic for SQL generation and execution.
Feeds DuckDB error messages back to the LLM for self-correction.
"""

from ml_pipeline.monitoring.logger import JSONLogger
from data_pipeline.ingest import get_duckdb_conn

logger = JSONLogger()

MAX_RETRIES = 3


def execute_sql(sql: str) -> tuple:
    """
    Execute sql against DuckDB. Returns (result_df, error_string).
    result_df is None on error. error_string is None on success.
    """
    try:
        conn = get_duckdb_conn()
        result = conn.execute(sql).df()
        return result, None
    except Exception as exc:
        return None, str(exc)


def run_with_retry(question: str) -> tuple:
    """
    Attempt SQL generation and execution up to MAX_RETRIES times.
    On error, feeds the error back to the LLM and asks it to fix the SQL.

    Returns:
        (result_df, sql, llm_used, retry_count, error)
    """
    from chat_pipeline.sql_generator import generate_sql

    conversation = []
    llm_used = "groq"
    retry_count = 0

    for attempt in range(MAX_RETRIES):
        sql, llm_used = generate_sql(question, conversation)
        result, error = execute_sql(sql)

        if error is None:
            if attempt > 0:
                logger.log("sql_retried", {"attempt": attempt, "success": True})
            return result, sql, llm_used, attempt, None

        logger.log("sql_failed", {"attempt": attempt, "error": error, "sql": sql[:200]})

        # Feed error back so the LLM can correct itself
        conversation.append({"role": "assistant", "content": sql})
        conversation.append(
            {
                "role": "user",
                "content": (
                    f"That query failed with this error: {error}\n"
                    "Fix the SQL and return only the corrected query. No explanation."
                ),
            }
        )
        retry_count = attempt + 1

    logger.log("sql_failed", {"attempt": MAX_RETRIES, "final": True})
    return None, sql, llm_used, retry_count, error
