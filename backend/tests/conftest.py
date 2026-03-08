"""
Pytest configuration for backend tests.
Environment variables are set here, before any app module is imported,
so that pydantic-settings picks up test values when Settings() is first instantiated.
"""
import os
import sys
import tempfile

# Paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override env vars for tests *before* any app import
_TEST_DB = os.path.join(tempfile.gettempdir(), "pharmaiq_test_backend.db")
os.environ.setdefault("GROQ_API_KEY", "test_key")
os.environ.setdefault("OPENAI_API_KEY", "test_key")
os.environ.setdefault("UPSTASH_REDIS_URL", "http://test.invalid")
os.environ.setdefault("UPSTASH_REDIS_TOKEN", "test_token")
os.environ["SQLITE_DB_PATH"] = _TEST_DB
os.environ["LIVEKIT_URL"] = ""
os.environ["LIVEKIT_API_KEY"] = ""
os.environ["LIVEKIT_API_SECRET"] = ""
