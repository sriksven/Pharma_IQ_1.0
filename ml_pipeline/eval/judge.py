"""
Orchestrates SQL and answer evaluation after each query.
Writes results to the eval_results SQLite table.
"""

import sqlite3
from datetime import datetime

from ml_pipeline.eval.sql_eval import evaluate_sql
from ml_pipeline.eval.answer_eval import evaluate_answer
from ml_pipeline.monitoring.logger import JSONLogger

logger = JSONLogger()


def _db_path() -> str:
    from app.config import settings
    return settings.sqlite_db_path


def run_eval(
    message_id: int,
    question: str,
    sql: str,
    answer: str,
    sql_error: str | None = None,
):
    """Run both evals and persist results. Called after each successful chat response."""
    try:
        sql_scores = evaluate_sql(question, sql, sql_error)
        answer_scores = evaluate_answer(question, answer)

        conn = sqlite3.connect(_db_path())
        conn.execute(
            """INSERT INTO eval_results
               (message_id, sql_correctness, sql_efficiency,
                answer_relevance, answer_clarity, answer_insight,
                judge_model, reasoning, evaluated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message_id,
                sql_scores["correctness"],
                sql_scores["efficiency"],
                answer_scores["relevance"],
                answer_scores["clarity"],
                answer_scores["insight"],
                "groq/llama3-70b",
                sql_scores["reasoning"],
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        logger.log("eval_completed", {"message_id": message_id})

    except Exception as exc:
        logger.log("eval_error", {"message_id": message_id, "error": str(exc)})
