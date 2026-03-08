"""
Orchestrates SQL and answer evaluation after each query.
Writes results to the eval_results SQLite table.
"""

import sqlite3
from datetime import datetime

from eval_and_metrics.eval.sql_eval import evaluate_sql
from eval_and_metrics.eval.answer_eval import evaluate_answer
from eval_and_metrics.monitoring.logger import JSONLogger

logger = JSONLogger()


def _db_path() -> str:
    from app.config import settings
    return settings.sqlite_db_path


def run_eval(
    message_id: int,
    question: str,
    sql: str,
    answer: str,
    chart_data: list = None,
    sql_error: str | None = None,
):
    """Run both evals and persist results. Called after each successful chat response."""
    import json
    try:
        sql_result_str = json.dumps(chart_data)[:1500] if chart_data else None
        sql_scores = evaluate_sql(question, sql, sql_error, sql_result=sql_result_str)
        answer_scores = evaluate_answer(
            question,
            answer,
            json.dumps(chart_data)[:2000] if chart_data else "No data returned."
        )

        conn = sqlite3.connect(_db_path())
        conn.execute(
            """INSERT INTO eval_results
               (message_id, sql_correctness, sql_efficiency,
                answer_relevance, answer_clarity, answer_insight,
                judge_model, reasoning, evaluated_at,
                answer_faithfulness, sql_schema_precision)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message_id,
                sql_scores["correctness"],
                sql_scores["efficiency"],
                answer_scores["relevance"],
                answer_scores["clarity"],
                answer_scores["insight"],
                "groq/gpt-oss-120b",
                sql_scores["reasoning"],
                datetime.utcnow().isoformat(),
                answer_scores.get("faithfulness", 0.5),
                sql_scores.get("schema_precision", 0.5),
            ),
        )
        conn.commit()
        conn.close()

        logger.log("eval_completed", {"message_id": message_id})

    except Exception as exc:
        logger.log("eval_error", {"message_id": message_id, "error": str(exc)})
