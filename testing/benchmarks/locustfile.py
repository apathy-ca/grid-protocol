from locust import HttpUser, task, between

class GridUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def authorize_endpoint(self):
        payload = {
            "principal": {"id": "user1", "role": "viewer"},
            "action": {"operation": "read"},
            "resource": {"id": "document/123", "sensitivity": "low"}
        }
        self.client.post("/authorize", json=payload)

    @task(3)
    def authorize_admin(self):
        payload = {
            "principal": {"id": "admin", "role": "admin"},
            "action": {"operation": "write"},
            "resource": {"id": "document/123", "sensitivity": "high"}
        }
        self.client.post("/authorize", json=payload)