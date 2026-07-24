from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "vector_store_ready" in data


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "rag_queries_total" in response.text or "# HELP" in response.text


def test_query_endpoint_empty():
    response = client.post("/query", json={"query": "   "})
    assert response.status_code == 400


def test_query_endpoint_valid_web_mode():
    response = client.post("/query", json={
        "query": "Quel est le dernier résultat en Formule 1 ?",
        "search_mode": "WEB",
        "max_web_results": 2
    })
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Quel est le dernier résultat en Formule 1 ?"
    assert data["mode_used"] == "WEB"
    assert "response" in data
    assert "context" in data
    assert "duration_seconds" in data
