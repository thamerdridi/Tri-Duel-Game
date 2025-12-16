from locust import HttpUser, task, between

class AuthUser(HttpUser):
    wait_time = between(0.05, 0.1)  # ~20 req/sec per user
    verify = False  # self-signed certs in lab

    @task
    def login(self):
        self.client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "StrongPass123!"
            }
        )
