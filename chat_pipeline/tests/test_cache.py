"""
Unit tests for the Upstash Redis cache key logic.
Tests do NOT hit a live Redis instance -- they only exercise the local
key-derivation and serialisation helpers.
"""
import hashlib
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from chat_pipeline.cache import _cache_key


def test_cache_key_has_expected_prefix():
    key = _cache_key("show me top reps")
    assert key.startswith("pharma_iq:")


def test_cache_key_is_deterministic():
    q = "which territory had highest trx last quarter?"
    assert _cache_key(q) == _cache_key(q)


def test_cache_key_normalises_case():
    assert _cache_key("Top Reps") == _cache_key("top reps")


def test_cache_key_trims_whitespace():
    assert _cache_key("  top reps  ") == _cache_key("top reps")


def test_cache_key_hash_is_sha256():
    q = "test query"
    key = _cache_key(q)
    suffix = key[len("pharma_iq:"):]
    expected_hash = hashlib.sha256(q.encode()).hexdigest()
    assert suffix == expected_hash


def test_different_questions_produce_different_keys():
    assert _cache_key("question one") != _cache_key("question two")


def test_empty_question_produces_valid_key():
    key = _cache_key("")
    assert key.startswith("pharma_iq:")
    assert len(key) > len("pharma_iq:")
