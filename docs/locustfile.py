from locust import HttpUser, task, between
import uuid
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BasicUser(HttpUser):
    """
    Comprehensive load test for Tri-Duel Game API.
    Covers:
    - Public endpoints (health, cards gallery)
    - Authentication endpoints (register, login, refresh)
    - Player service endpoints (profile, match history)
    - Game service endpoints (create match, submit move, get state)
    - Authenticated and unauthenticated flows
    """

    host = "https://localhost:8443"
    wait_time = between(1, 3)

    def on_start(self):
        # Disable TLS verification (self-signed certs)
        self.client.verify = False

        self.username = f"user_{uuid.uuid4().hex[:8]}"
        self.password = "Password123456!"
        self.access_token = None
        self.refresh_token = None
        self.match_id = None

        # -------- AUTH: register --------
        with self.client.post(
                "/auth/register",
                json={
                    "username": self.username,
                    "email": f"{self.username}@example.com",
                    "password": self.password,
                },
                catch_response=True,
        ) as r:
            if r.status_code not in [200, 201]:
                r.failure(f"Registration failed ({r.status_code})")

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

            data = r.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")

            if not self.access_token:
                r.failure("JWT access token missing")
                return

            self.client.headers.update(
                {"Authorization": f"Bearer {self.access_token}"}
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

    # ==================================================    # AUTHENTICATED ENDPOINTS
    # ==================================================

    @task(3)
    def validate_token(self):
        """Validate current JWT token"""
        with self.client.get(
                "/auth/validate",
                name="/auth/validate",
                catch_response=True,
        ) as r:
            if r.status_code not in [200, 401]:
                r.failure(f"Token validation error ({r.status_code})")

    @task(2)
    def refresh_token(self):
        """Refresh access token using refresh token"""
        if self.refresh_token:
            with self.client.post(
                    "/auth/refresh",
                    json={"refresh_token": self.refresh_token},
                    name="/auth/refresh",
                    catch_response=True,
            ) as r:
                if r.status_code == 200:
                    data = r.json()
                    new_token = data.get("access_token")
                    if new_token:
                        self.access_token = new_token
                        self.client.headers.update(
                            {"Authorization": f"Bearer {new_token}"}
                        )
                elif r.status_code >= 500:
                    r.failure(f"Token refresh error ({r.status_code})")

    @task(3)
    def get_player_profile(self):
        """Get authenticated player's profile"""
        with self.client.get(
                "/players/me",
                name="/players/me",
                catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")
            elif r.status_code not in [200, 404]:
                r.failure(f"Unexpected status ({r.status_code})")

    @task(2)
    def update_player_profile(self):
        """Update player profile"""
        with self.client.post(
                "/players",
                json={"username": f"updated_{self.username}"},
                name="/players",
                catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")
            elif r.status_code not in [200, 201, 404]:
                r.failure(f"Unexpected status ({r.status_code})")

    @task(2)
    def get_player_matches(self):
        """Get player's match history"""
        with self.client.get(
                f"/players/{self.username}/matches",
                name="/players/:player_id/matches",
                catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")
            elif r.status_code not in [200, 404]:
                r.failure(f"Unexpected status ({r.status_code})")

    @task(1)
    def create_match(self):
        """Create a new match"""
        opponent = f"opponent_{uuid.uuid4().hex[:4]}"
        with self.client.post(
                "/matches",
                json={
                    "player1_id": self.username,
                    "player2_id": opponent,
                },
                name="/matches",
                catch_response=True,
        ) as r:
            if r.status_code == 200:
                data = r.json()
                self.match_id = data.get("match_id")
            elif r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")

    @task(1)
    def get_match_state(self):
        """Get current match state"""
        if self.match_id:
            with self.client.get(
                    f"/matches/{self.match_id}",
                    params={"player_id": self.username},
                    name="/matches/:match_id",
                    catch_response=True,
            ) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error ({r.status_code})")
                elif r.status_code not in [200, 404]:
                    r.failure(f"Unexpected status ({r.status_code})")

    @task(2)
    def get_active_matches(self):
        """Get all active matches for player"""
        with self.client.get(
                "/matches/active",
                name="/matches/active",
                catch_response=True,
        ) as r:
            if r.status_code >= 500:
                r.failure(f"Server error ({r.status_code})")
            elif r.status_code not in [200, 401]:
                r.failure(f"Unexpected status ({r.status_code})")

    @task(1)
    def submit_move(self):
        """Submit a card move in an active match"""
        if self.match_id:
            with self.client.post(
                    f"/matches/{self.match_id}/move",
                    json={
                        "player_id": self.username,
                        "card_index": 0,
                    },
                    name="/matches/:match_id/move",
                    catch_response=True,
            ) as r:
                if r.status_code in [200, 400]:
                    # 200: move executed, 400: invalid move (expected)
                    pass
                elif r.status_code >= 500:
                    r.failure(f"Server error ({r.status_code})")
                elif r.status_code not in [403, 404]:
                    r.failure(f"Unexpected status ({r.status_code})")

    @task(1)
    def get_player_hand_visual(self):
        """Get player's hand visualization"""
        if self.match_id:
            with self.client.get(
                    f"/matches/{self.match_id}/hand",
                    name="/matches/:match_id/hand",
                    catch_response=True,
            ) as r:
                if r.status_code >= 500:
                    r.failure(f"Server error ({r.status_code})")
                elif r.status_code not in [200, 404]:
                    r.failure(f"Unexpected status ({r.status_code})")

    @task(1)
    def surrender_match(self):
        """Surrender an active match"""
        if self.match_id:
            with self.client.post(
                    f"/matches/{self.match_id}/surrender",
                    name="/matches/:match_id/surrender",
                    catch_response=True,
            ) as r:
                if r.status_code in [200, 400]:
                    # 200: surrendered, 400: invalid state
                    self.match_id = None
                elif r.status_code >= 500:
                    r.failure(f"Server error ({r.status_code})")
                elif r.status_code not in [403, 404]:
                    r.failure(f"Unexpected status ({r.status_code})")

    # ==================================================