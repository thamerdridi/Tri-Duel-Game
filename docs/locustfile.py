from locust import HttpUser, task, between
import uuid
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BasicUser(HttpUser):
    """
    Minimal performance test via API Gateway.
    Covers:
    - Public endpoints (no JWT)
    - Auth (JWT)
    - One authenticated endpoint
    """

    host = "https://localhost:8443"
    wait_time = between(1, 3)

    def on_start(self):
        # Disable TLS verification (self-signed certs)
        self.client.verify = False

        self.username = f"user_{uuid.uuid4().hex[:8]}"
        self.password = "Password123456!"

        # -------- AUTH: register --------
        self.client.post(
            "/auth/register",
            json={
                "username": self.username,
                "email": f"{self.username}@example.com",
                "password": self.password,
            },
        )

        # -------- AUTH: login --------
        with self.client.post(
            "/auth/login",
            json={
                "username": self.username,
                "password": self.password,
            },
            catch_response=True,
        ) as r:
            if r.status_code != 200:
                r.failure(f"Login failed ({r.status_code})")
                return

            token = r.json().get("access_token")
            if not token:
                r.failure("JWT token missing")
                return

            self.client.headers.update(
                {"Authorization": f"Bearer {token}"}
            )

    # ==================================================
    # PUBLIC ENDPOINTS (NO AUTH)
    # ==================================================

    @task(2)
    def game_health(self):
        with self.client.get(
            "/game/health",
            name="/game/health",
            catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")

    @task(2)
    def player_health(self):
        with self.client.get(
            "/player/health",
            name="/player/health",
            catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")

    @task(2)
    def leaderboard(self):
        with self.client.get(
            "/player/leaderboard",
            name="/player/leaderboard",
            catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")

    @task(2)
    def cards_gallery(self):
        with self.client.get(
            "/game/cards",
            name="/game/cards",
            catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")

    @task(1)
    def card_detail(self):
        # Random card id – existence not important for performance
        card_id = 1
        with self.client.get(
            f"/game/cards/{card_id}",
            name="/game/cards/:card_id",
            catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")

    # ==================================================
