"""
Tests unitaires pour la Maintenance Prédictive ChromaDB (tests/test_chroma_maintenance.py).
"""

import os
import shutil
import pytest
import numpy as np

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

import chromadb
from orchestrator.memory.chroma_maintenance import ChromaMaintenanceManager


@pytest.fixture
def temp_chroma_manager(tmp_path):
    db_dir = str(tmp_path / "chroma_test_db")
    cold_dir = str(tmp_path / "cold_storage")
    manager = ChromaMaintenanceManager(db_path=db_dir, cold_storage_dir=cold_dir)
    return manager


def test_audit_health_empty_collection(temp_chroma_manager):
    client = chromadb.Client()
    collection = client.create_collection("test_empty")
    audit = temp_chroma_manager.audit_health(collection)
    assert audit["health_score"] == 1.0
    assert audit["status"] == "HEALTHY"
    assert audit["total_vectors"] == 0


def test_audit_health_and_drift(temp_chroma_manager):
    client = chromadb.Client()
    collection = client.create_collection("test_health")
    
    # 5 vecteurs autour de [1.0, 1.0, 1.0]
    embeddings = [
        [1.0, 1.0, 1.0],
        [1.02, 0.98, 1.01],
        [0.99, 1.01, 0.98],
        [1.01, 1.00, 1.02],
        [0.98, 1.02, 0.99]
    ]
    collection.add(
        ids=[f"id_{i}" for i in range(5)],
        embeddings=embeddings,
        documents=[f"doc_{i}" for i in range(5)]
    )

    baseline = np.array([1.0, 1.0, 1.0])
    audit = temp_chroma_manager.audit_health(collection, baseline_mean=baseline)

    assert audit["total_vectors"] == 5
    assert audit["vector_dim"] == 3
    assert audit["health_score"] > 0.7
    assert audit["drift_zscore"] < 2.0


def test_cleanup_duplicates(temp_chroma_manager):
    client = chromadb.Client()
    collection = client.create_collection("test_dedup")

    # 2 vecteurs identiques (similarity = 1.0) et 1 vecteur différent
    embeddings = [
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],  # Doublon exact de id_0
        [0.0, 1.0, 0.0]
    ]
    collection.add(
        ids=["id_0", "id_1", "id_2"],
        embeddings=embeddings,
        documents=["doc 0", "doc 1", "doc 2"]
    )

    res = temp_chroma_manager.cleanup_duplicates(collection, threshold=0.98)
    assert res["duplicates_found"] == 1
    assert "id_1" in res["deleted_ids"]

    # Vérification dans la collection
    remaining = collection.get()
    assert len(remaining["ids"]) == 2
    assert "id_1" not in remaining["ids"]


def test_check_reindex_trigger(temp_chroma_manager):
    client = chromadb.Client()
    collection = client.create_collection("test_reindex")

    collection.add(
        ids=[f"id_{i}" for i in range(13)],
        embeddings=[[0.1 * i, 0.2] for i in range(13)],
        documents=[f"doc_{i}" for i in range(13)]
    )

    # 13 items vs baseline 10 -> 30% de croissance (> 20%)
    res = temp_chroma_manager.check_reindex_trigger(collection, baseline_count=10, max_growth_ratio=0.20)
    assert res["should_reindex"] is True
    assert res["growth_ratio"] == 0.3
