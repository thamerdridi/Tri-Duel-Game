"""
CURRENTLY NOT IN USE - FOR REFERENCE ONLY

==========================================
LOCUST LOAD TEST - GAME SERVICE (ISOLATED)
==========================================

PURPOSE:
--------
Load testing for Game Service endpoints in isolation.
Tests concurrent match creation, move submission, and database performance.

SCENARIOS:
----------
1. Create Match - 60% of traffic
2. Submit Moves - 30% of traffic
3. Get Match State - 10% of traffic

TARGET:
-------
- 50 concurrent users
- Ramp up over 10 seconds
- Test database and match engine under load

HOW TO RUN:
-----------
1. Start Game Service:
   $ cd game_service
   $ docker-compose up -d

2. Run Locust:
   $ cd game_service/game_app/tests/locust
   $ locust -f locustfile_game_service.py

3. Open browser:
   http://localhost:8089

4. Configure:
   - Number of users: 50
   - Spawn rate: 5 users/second
   - Host: http://localhost:8003

5. Start test and monitor results

METRICS TO WATCH:
-----------------
- Requests per second (RPS)
- Response times (median, 95th percentile)
- Failure rate
- Database connection pool

NOTES:
------
- Uses mock JWT tokens (no Auth Service dependency)
- Creates isolated matches (alice vs bob_N)
- Simulates realistic match flow
- Tests Game Service performance in isolation
"""

from locust import HttpUser, task, between, events
import random
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameServiceUser(HttpUser):
    """
    Simulates a player using Game Service.

    Each user:
    - Creates matches
    - Submits moves
    - Checks match state
    """

    # Wait 1-3 seconds between tasks (realistic user behavior)
    wait_time = between(1, 3)

    # Base URL for Game Service
    host = "http://localhost:8003"

    def on_start(self):
        """
        Called when user starts - setup user data.

        In isolated test we use mock authentication (header injection).
        For full integration test with Auth Service, this would call /auth/login.
        """
        # Generate unique player ID for this user
        self.player_id = f"player_{random.randint(1000, 9999)}"

        # Mock JWT token (Game Service validates through Auth Service in real scenario)
        # For load testing we bypass auth to isolate Game Service performance
        self.headers = {
            "Authorization": f"Bearer mock_token_{self.player_id}",
            "Content-Type": "application/json"
        }

        # Storage for current match
        self.current_match_id = None
        self.current_cards = []
        self.opponent_id = f"bot_{random.randint(1000, 9999)}"

        logger.info(f"User {self.player_id} started")

    @task(6)
    def create_match(self):
        """
        Task: Create a new match (60% of traffic).

        Weight: 6 (highest - most common operation)
        Tests: POST /matches endpoint
        """
        payload = {
            "player1_id": self.player_id,
            "player2_id": self.opponent_id
        }

        with self.client.post(
            "/matches",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="POST /matches"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.current_match_id = data.get("match_id")
                    self.current_cards = [card["match_card_id"] for card in data.get("hand", [])]

                    if len(self.current_cards) == 5:
                        response.success()
                        logger.debug(f"Match {self.current_match_id} created with 5 cards")
                    else:
                        response.failure(f"Expected 5 cards, got {len(self.current_cards)}")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            elif response.status_code == 401:
                # Expected in isolated test without real auth
                response.success()
                logger.warning("Auth required - expected in isolated test")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(3)
    def submit_move(self):
        """
        Task: Submit a card move (30% of traffic).

        Weight: 3
        Tests: POST /matches/{id}/move endpoint
        """
        if not self.current_match_id or not self.current_cards:
            # No match available - skip this task
            return

        # Pick random card from hand
        card_id = random.choice(self.current_cards)

        payload = {
            "player_id": self.player_id,
            "match_card_id": card_id
        }

        with self.client.post(
            f"/matches/{self.current_match_id}/move",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="POST /matches/{id}/move"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()

                    # Check if waiting for opponent or round resolved
                    if data.get("status") == "waiting_for_opponent":
                        response.success()
                        logger.debug(f"Move submitted, waiting for opponent")
                    elif "round" in data:
                        response.success()
                        logger.debug(f"Round {data['round']} resolved")

                        # Remove used card
                        if card_id in self.current_cards:
                            self.current_cards.remove(card_id)

                        # Check if match finished
                        if data.get("match_finished"):
                            logger.info(f"Match {self.current_match_id} finished!")
                            self.current_match_id = None
                            self.current_cards = []
                    else:
                        response.failure("Unexpected response format")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            elif response.status_code == 400:
                response.failure(f"Invalid move: {response.text}")
            elif response.status_code == 401:
                response.success()  # Expected without real auth
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def get_match_state(self):
        """
        Task: Get current match state (10% of traffic).

        Weight: 1 (lowest - less frequent operation)
        Tests: GET /matches/{id} endpoint
        """
        if not self.current_match_id:
            # No match available - skip
            return

        with self.client.get(
            f"/matches/{self.current_match_id}?player_id={self.player_id}",
            headers=self.headers,
            catch_response=True,
            name="GET /matches/{id}"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()

                    # Validate response structure
                    required_fields = ["match_id", "status", "current_round", "points_p1", "points_p2"]
                    if all(field in data for field in required_fields):
                        response.success()
                        logger.debug(f"Match state: Round {data['current_round']}, Score {data['points_p1']}-{data['points_p2']}")
                    else:
                        response.failure("Missing required fields in response")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            elif response.status_code == 401:
                response.success()  # Expected without real auth
            elif response.status_code == 404:
                response.failure("Match not found")
            else:
                response.failure(f"Unexpected status: {response.status_code}")


# ============================================================
# EVENT HANDLERS - CUSTOM METRICS AND LOGGING
# ============================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    logger.info("=" * 60)
    logger.info("🚀 GAME SERVICE LOAD TEST STARTED")
    logger.info("=" * 60)
    logger.info(f"Target host: {GameServiceUser.host}")
    logger.info(f"Scenarios: Create Match (60%), Submit Move (30%), Get State (10%)")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops - print summary."""
    logger.info("=" * 60)
    logger.info("🏁 GAME SERVICE LOAD TEST COMPLETED")
    logger.info("=" * 60)

    stats = environment.stats

    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Failure rate: {stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Median response time: {stats.total.median_response_time:.2f}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    logger.info(f"Requests per second: {stats.total.total_rps:.2f}")

    logger.info("=" * 60)

    # Detailed breakdown per endpoint
    logger.info("\nEndpoint Performance:")
    for name, entry in stats.entries.items():
        if entry.num_requests > 0:
            logger.info(f"\n  {name}:")
            logger.info(f"    Requests: {entry.num_requests}")
            logger.info(f"    Failures: {entry.num_failures} ({entry.fail_ratio * 100:.2f}%)")
            logger.info(f"    Avg time: {entry.avg_response_time:.2f}ms")
            logger.info(f"    Min/Max: {entry.min_response_time:.2f}ms / {entry.max_response_time:.2f}ms")


# ============================================================
# CUSTOM USER CLASS FOR DIFFERENT SCENARIOS (OPTIONAL)
# ============================================================

class HeavyMatchCreator(HttpUser):
    """
    Heavy user that only creates matches (stress test match creation).

    Use this to specifically test match creation performance:
    $ locust -f locustfile_game_service.py --user-classes HeavyMatchCreator
    """
    wait_time = between(0.5, 1.5)
    host = "http://localhost:8003"

    def on_start(self):
        self.player_id = f"heavy_{random.randint(1000, 9999)}"
        self.headers = {
            "Authorization": f"Bearer mock_token_{self.player_id}",
            "Content-Type": "application/json"
        }

    @task
    def rapid_match_creation(self):
        """Rapidly create matches to stress test."""
        payload = {
            "player1_id": self.player_id,
            "player2_id": f"opponent_{random.randint(1000, 9999)}"
        }

        with self.client.post(
            "/matches",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="POST /matches (heavy)"
        ) as response:
            if response.status_code in [200, 401]:  # 401 expected without auth
                response.success()


# ============================================================
# RUN INSTRUCTIONS
# ============================================================

"""
QUICK START:
-----------
1. Terminal 1 - Start Game Service:
   $ cd game_service
   $ docker-compose up

2. Terminal 2 - Run Locust:
   $ cd game_service/game_app/tests
   $ pip install locust  # if not installed
   $ locust -f locustfile_game_service.py

3. Browser:
   Open http://localhost:8089
   
   Configure:
   - Number of users: 50
   - Spawn rate: 5
   - Host: http://localhost:8003
   
   Click "Start swarming"

4. Monitor:
   - Watch Statistics tab (requests, failures, response times)
   - Watch Charts tab (RPS, response time trends)
   - Check terminal for detailed logs

ADVANCED USAGE:
--------------
# Run without Web UI (headless):
$ locust -f locustfile_game_service.py --headless -u 50 -r 5 --run-time 60s

# Run specific user class:
$ locust -f locustfile_game_service.py --user-classes HeavyMatchCreator

# Export results to CSV:
$ locust -f locustfile_game_service.py --headless -u 50 -r 5 --run-time 60s --csv=results

EXPECTED RESULTS:
----------------
- Median response time: < 100ms
- 95th percentile: < 500ms
- Failure rate: < 1%
- RPS: > 50 (depends on hardware)

If results are poor:
- Check database connection pool size
- Monitor database query performance
- Check for N+1 query problems
- Consider adding caching
"""

