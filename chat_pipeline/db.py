"""
SQLite persistence for chat sessions and messages.
"""

import json
import os
import sys
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _db_path() -> str:
    from app.config import settings
    return settings.sqlite_db_path


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


async def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT,
            title TEXT
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            sql_query TEXT,
            provenance TEXT,
            llm_used TEXT,
            cache_hit INTEGER,
            created_at TEXT,
            sql_system_prompt TEXT,
            explain_system_prompt TEXT,
            user_feedback INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        CREATE TABLE IF NOT EXISTS eval_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            sql_correctness REAL,
            sql_efficiency REAL,
            answer_relevance REAL,
            answer_clarity REAL,
            answer_insight REAL,
            judge_model TEXT,
            reasoning TEXT,
            evaluated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS query_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            total_latency_ms INTEGER,
            sql_gen_latency_ms INTEGER,
            explain_latency_ms INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            retry_count INTEGER,
            llm_used TEXT,
            cache_hit INTEGER,
            tables_joined INTEGER,
            session_turn_count INTEGER,
            failed INTEGER,
            recorded_at TEXT
        );
        """
    )
    
    try:
        conn.execute("ALTER TABLE messages ADD COLUMN sql_system_prompt TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        conn.execute("ALTER TABLE messages ADD COLUMN explain_system_prompt TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        conn.execute("ALTER TABLE messages ADD COLUMN chart_hint TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        conn.execute("ALTER TABLE messages ADD COLUMN chart_data TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE messages ADD COLUMN user_feedback INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        pass
        
    try:
        conn.execute("ALTER TABLE eval_results ADD COLUMN answer_faithfulness REAL")
    except sqlite3.OperationalError:
        pass
        
    try:
        conn.execute("ALTER TABLE eval_results ADD COLUMN sql_schema_precision REAL")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def create_session(session_id: str, title: str = "New Chat"):
    conn = _get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO sessions (session_id, created_at, title) VALUES (?, ?, ?)",
        (session_id, datetime.utcnow().isoformat(), title),
    )
    conn.commit()
    conn.close()


def save_message(
    session_id: str,
    role: str,
    content: str,
    sql_query: str = None,
    provenance: list = None,
    llm_used: str = None,
    cache_hit: bool = False,
    sql_system_prompt: str = None,
    explain_system_prompt: str = None,
    chart_hint: dict = None,
    chart_data: list = None,
) -> int:
    create_session(session_id)
    
    conn = _get_conn()
    cursor = conn.execute(
        """INSERT INTO messages
           (session_id, role, content, sql_query, provenance, llm_used, cache_hit, created_at, sql_system_prompt, explain_system_prompt, chart_hint, chart_data)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            role,
            content,
            sql_query,
            json.dumps(provenance or []),
            llm_used,
            int(cache_hit),
            datetime.utcnow().isoformat(),
            sql_system_prompt,
            explain_system_prompt,
            json.dumps(chart_hint) if chart_hint else None,
            json.dumps(chart_data) if chart_data else None,
        ),
    )
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return message_id


def get_sessions() -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT session_id, created_at, title FROM sessions ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_messages(session_id: str) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_session(session_id: str):
    conn = _get_conn()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def update_session_title(session_id: str, title: str):
    conn = _get_conn()
    conn.execute(
        "UPDATE sessions SET title = ? WHERE session_id = ?", (title, session_id)
    )
    conn.commit()
    conn.close()


def get_session_turn_count(session_id: str) -> int:
    conn = _get_conn()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0
