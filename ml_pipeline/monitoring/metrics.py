"""
Records per-query metrics to the query_metrics SQLite table.
"""

import sqlite3
from datetime import datetime

from ml_pipeline.monitoring.logger import JSONLogger

logger = JSONLogger()


def _db_path() -> str:
    from app.config import settings
    return settings.sqlite_db_path


def record_metrics(
    message_id: int,
    total_latency_ms: int,
    sql_gen_latency_ms: int,
    explain_latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    retry_count: int,
    llm_used: str,
    cache_hit: bool,
    tables_joined: int,
    session_turn_count: int,
    failed: bool,
):
    try:
        conn = sqlite3.connect(_db_path())
        conn.execute(
            """INSERT INTO query_metrics
               (message_id, total_latency_ms, sql_gen_latency_ms, explain_latency_ms,
                input_tokens, output_tokens, retry_count, llm_used, cache_hit,
                tables_joined, session_turn_count, failed, recorded_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                message_id,
                total_latency_ms,
                sql_gen_latency_ms,
                explain_latency_ms,
                input_tokens,
                output_tokens,
                retry_count,
                llm_used,
                int(cache_hit),
                tables_joined,
                session_turn_count,
                int(failed),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.log("metrics_error", {"error": str(exc)})
