import sys
import os
import sqlite3
from datetime import datetime
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from chat_pipeline.db import save_message, _get_conn

print("Starting debug script")
try:
    print("Testing DB insert")
    msg_id = save_message(
        session_id="debug_session_99",
        role="assistant",
        content="Test content",
        sql_query="SELECT 1",
        provenance=[],
        llm_used="groq",
        cache_hit=False,
        sql_system_prompt="sys",
        explain_system_prompt="exp",
        chart_hint={"type": "table"},
        chart_data=[{"key": "val"}]
    )
    print(f"Success. Inserted msg: {msg_id}")
except Exception as e:
    print(f"Exception caught during save_message: {e}")

try:
    conn = _get_conn()
    print("Fetching sessions")
    res = conn.execute("SELECT * FROM sessions;").fetchall()
    print(res)
    
    print("Fetching messages")
    res2 = conn.execute("SELECT * FROM messages;").fetchall()
    print(len(res2), "messages found")
    
except Exception as e:
    print(f"Exception during verify: {e}")
