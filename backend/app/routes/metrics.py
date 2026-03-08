import sqlite3
from fastapi import APIRouter


router = APIRouter()


def _db_path():
    from app.config import settings
    return settings.sqlite_db_path


def _conn():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/metrics/summary")
def metrics_summary():
    conn = _conn()

    qm = conn.execute(
        """SELECT
            COUNT(*) as total_queries,
            AVG(total_latency_ms) as avg_latency_ms,
            SUM(cache_hit) * 1.0 / NULLIF(COUNT(*), 0) as cache_hit_rate,
            SUM(CASE WHEN llm_used = 'groq_fallback' THEN 1 ELSE 0 END) * 1.0
                / NULLIF(COUNT(*), 0) as fallback_rate,
            AVG(retry_count) as avg_retry_count,
            SUM(failed) * 1.0 / NULLIF(COUNT(*), 0) as failed_rate
           FROM query_metrics"""
    ).fetchone()

    er = conn.execute(
        """SELECT
            AVG(sql_correctness) as avg_sql_correctness,
            AVG(answer_relevance) as avg_answer_relevance,
            AVG(answer_faithfulness) as avg_faithfulness,
            AVG(sql_schema_precision) as avg_schema_precision
           FROM eval_results"""
    ).fetchone()

    conn.close()

    return {
        "total_queries": qm["total_queries"] or 0,
        "avg_latency_ms": round(qm["avg_latency_ms"] or 0, 1),
        "cache_hit_rate": round((qm["cache_hit_rate"] or 0) * 100, 1),
        "fallback_rate": round((qm["fallback_rate"] or 0) * 100, 1),
        "avg_retry_count": round(qm["avg_retry_count"] or 0, 2),
        "failed_rate": round((qm["failed_rate"] or 0) * 100, 1),
        "avg_sql_correctness": round((er["avg_sql_correctness"] or 0) * 10, 1),
        "avg_answer_relevance": round((er["avg_answer_relevance"] or 0) * 10, 1),
        "avg_faithfulness": round((er["avg_faithfulness"] or 0) * 10, 1) if er["avg_faithfulness"] is not None else None,
        "avg_schema_precision": round((er["avg_schema_precision"] or 0) * 10, 1) if er["avg_schema_precision"] is not None else None,
    }


@router.get("/metrics/queries")
def recent_queries(limit: int = 20):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM query_metrics ORDER BY recorded_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"queries": [dict(r) for r in rows]}


@router.get("/metrics/evals")
def eval_scores(limit: int = 50):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM eval_results ORDER BY evaluated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"evals": [dict(r) for r in rows]}
