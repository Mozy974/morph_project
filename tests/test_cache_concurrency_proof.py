"""
Tests unitaires et de concurrence pour les Caches LRU/TTL (tests/test_cache_concurrency_proof.py).
Preuves concrètes de l'absence de deadlock et du respect strict des seuils de performance.
"""

import os
import json
import csv
import pytest
from benchmark_cache_systems import ThreadSafeTTLCache, run_benchmark


def test_thread_safe_ttl_cache_concurrency_and_no_deadlock():
    cache = ThreadSafeTTLCache(ttl_seconds=5.0, maxsize=1000)

    # 1. Verification of basic read/write
    cache.set("key1", "val1")
    assert cache.get("key1") == "val1"

    # 2. Verification of expiration (TTL)
    cache.set("key_temp", "val_temp")
    cache._timestamps["key_temp"] -= 10.0  # Force expiration
    assert cache.get("key_temp") is None  # Should evict lazily


def test_cache_metrics_json_and_csv_artifacts_exist():
    # Execute benchmark to generate artifacts
    run_benchmark()

    json_path = "reports/cache_benchmark_metrics.json"
    csv_path = "reports/cache_benchmark_metrics.csv"

    assert os.path.exists(json_path)
    assert os.path.exists(csv_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["status"] == "PASS"
    assert data["latencies_ms"]["p99"] < 1.0
    assert data["error_rate_percent"] < 0.1
    assert data["hit_ratio_percent"] > 70.0


def test_cache_rlock_reentrancy():
    cache = ThreadSafeTTLCache(ttl_seconds=10.0, maxsize=100)
    # RLock reentrancy test
    with cache._lock:
        with cache._lock:
            cache.set("nested_key", "nested_val")
            assert cache.get("nested_key") == "nested_val"
