"""
Retry logic for SQL generation and execution.
Feeds DuckDB error messages back to the LLM for self-correction.
"""

from eval_and_metrics.monitoring.logger import JSONLogger
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


def run_with_retry(question: str, conversation_history: list = None) -> tuple:
    """
    Attempt SQL generation and execution up to MAX_RETRIES times.
    On error, feeds the error back to the LLM and asks it to fix the SQL.

    Returns:
        (result_df, sql, llm_used, retry_count, error, sql_system_prompt)
    """
    from chat_pipeline.sql_generator import generate_sql
    from chat_pipeline.sql_validator import validate_sql

    # Start with the provided conversation history for multi-turn context.
    # The retry loop appends SQL/error pairs on top of this.
    conversation = list(conversation_history) if conversation_history else []
    llm_used = "groq"
    retry_count = 0
    sql_system_prompt = None

    for attempt in range(MAX_RETRIES):
        sql, llm_used, sql_system_prompt = generate_sql(question, conversation)

        # 1. Validate AST and Schema using SQLGlot
        validation_errors = validate_sql(sql)

        if validation_errors:
            error = "Schema validation failed: " + "; ".join(validation_errors)
            result = None
        else:
            # 2. Only execute if validation passes
            result, error = execute_sql(sql)

        if error is None:
            if attempt > 0:
                logger.log("sql_retried", {"attempt": attempt, "success": True})
            return result, sql, llm_used, attempt, None, sql_system_prompt

        logger.log("sql_failed", {"attempt": attempt, "error": error, "sql": sql[:200]})

        # Feed error back so the LLM can correct itself
        conversation.append({"role": "assistant", "content": sql})
        conversation.append(
            {
                "role": "user",
                "content": (
                    f"That query failed with this error: {error}\n"
                    "Please review the available schema and relationships.\n"
                    "Fix the SQL by using ONLY the available columns. If you need a column that is not in the current tables, you must JOIN the correct table that contains it.\n"
                    "Return ONLY the corrected raw SQL query. No explanation."
                ),
            }
        )
        retry_count = attempt + 1

    logger.log("sql_failed", {"attempt": MAX_RETRIES, "final": True})
    return None, sql, llm_used, retry_count, error, sql_system_prompt

