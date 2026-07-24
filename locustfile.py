from locust import HttpUser, task, between
import random

QUERIES = [
    "Qu'est-ce que l'architecture RAG ?",
    "Quelles sont les nouveautés de Python 3.13 ?",
    "Comment fonctionne FastAPI avec Uvicorn ?",
    "Quels sont les avantages de ChromaDB par rapport à Pinecone ?",
    "Quelle est la météo aujourd'hui ?"
]

MODES = ["AUTO", "HYBRID", "WEB", "LOCAL"]

class RAGUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def test_rag_query(self):
        query = random.choice(QUERIES)
        mode = random.choice(MODES)
        payload = {
            "query": query,
            "search_mode": mode,
            "max_web_results": 2,
            "n_local_results": 2
        }
        with self.client.post("/query", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "response" in data and "duration_seconds" in data:
                    response.success()
                else:
                    response.failure("Champs de réponse RAG manquants")
            else:
                response.failure(f"Status code inattendu: {response.status_code}")

    @task(1)
    def test_health_check(self):
        self.client.get("/health")

    @task(1)
    def test_metrics(self):
        self.client.get("/metrics")
