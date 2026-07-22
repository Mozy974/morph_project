"""
Suite de Benchmarking et de Stress-Test Locust pour l'API SuperAgent Enterprise (tests/locustfile.py).
Simule la charge d'utilisateurs virtuels exécutant des requêtes sur les endpoints d'orchestration et de classification.
"""

import json
from locust import HttpUser, task, between


class SuperAgentUser(HttpUser):
    wait_time = between(1, 2)

    @task(3)
    def process_full_cycle(self):
        """
        Scénario principal : Délégation de tâche -> Streaming SSE -> Inspection du statut
        """
        payload = {
            "user_id": 1,
            "task": "Analyse de sécurité et module Python de validation de jetons JWT avec algorithme HS256",
            "max_retries": 2
        }

        # 1. Délégation de la tâche
        with self.client.post("/delegate_task", json=payload, catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Échec /delegate_task: HTTP {resp.status_code}")
                return

            try:
                data = resp.json()
                job_id = data.get("job_id")
                if not job_id:
                    resp.failure("job_id manquant dans la réponse JSON")
                    return
                resp.success()
            except Exception as e:
                resp.failure(f"Erreur parsing JSON: {e}")
                return

        # 2. Simulation de l'écoute du flux SSE
        with self.client.get(f"/stream/{job_id}", stream=True, catch_response=True) as sse_resp:
            if sse_resp.status_code == 200:
                sse_resp.success()
            else:
                sse_resp.failure(f"Échec stream SSE HTTP {sse_resp.status_code}")

        # 3. Vérification du statut final
        self.client.get(f"/status/{job_id}")

    @task(2)
    def test_classifier_endpoint(self):
        """
        Scénario de classification rapide (< 1ms CPU)
        """
        self.client.get("/metrics")

    @task(1)
    def test_resume_task(self):
        """
        Scénario secondaire : Tentative de reprise d'un job existant
        """
        job_id = "test_job_123"
        self.client.post(f"/resume_task/{job_id}")
