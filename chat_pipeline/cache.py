"""
Upstash Redis caching for query results.
Cache key: sha256(question.lower().strip())
TTL: 1 hour
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml_pipeline.monitoring.logger import JSONLogger

logger = JSONLogger()

TTL_SECONDS = 3600


def _cache_key(question: str) -> str:
    normalized = question.lower().strip()
    return "pharma_iq:" + hashlib.sha256(normalized.encode()).hexdigest()


def _get_client():
    from app.config import settings
    from upstash_redis import Redis

    return Redis(url=settings.upstash_redis_url, token=settings.upstash_redis_token)


def get_cached(question: str) -> dict | None:
    """Return cached response dict or None on miss/error."""
    try:
        client = _get_client()
        key = _cache_key(question)
        value = client.get(key)
        if value:
            logger.log("cache_hit", {"key": key[:16]})
            return json.loads(value)
    except Exception as exc:
        logger.log("cache_error", {"op": "get", "error": str(exc)})
    return None


def set_cached(question: str, payload: dict):
    """Write response to cache. Silently swallows write errors."""
    try:
        client = _get_client()
        key = _cache_key(question)
        client.setex(key, TTL_SECONDS, json.dumps(payload))
        logger.log("cache_write", {"key": key[:16]})
    except Exception as exc:
        logger.log("cache_error", {"op": "set", "error": str(exc)})
