from locust import HttpUser, task, between
import random
import uuid

class SuperAgentUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def index_page(self):
        self.client.get("/")

    @task(2)
    def pending_skills(self):
        self.client.get("/skills/pending")

    @task(5)
    def delegate_task(self):
        task_id = str(uuid.uuid4())
        payload = {
            "user_id": random.randint(1, 1000),
            "task": f"Test load from locust {task_id}",
            "max_retries": 2
        }
        with self.client.post("/delegate_task", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "job_id" in data:
                    # Let's also stream the job for a bit or check status
                    job_id = data["job_id"]
                    self.client.get(f"/status/{job_id}", name="/status/[job_id]")
