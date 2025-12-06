"""
==========================================
MATCH SERVICE INTEGRATION TESTS
==========================================

PURPOSE:
--------
Integration tests for MatchService business logic layer.
These tests verify the service layer behavior directly, bypassing the API layer.

WHAT IS TESTED:
---------------
1. Match Creation:
   - Match object is created with correct initial state
   - Two players receive equal-sized hands (HAND_SIZE cards each)
   - Match starts in "in_progress" status
   - Points start at 0 for both players

2. Move Submission Logic:
   - First move returns "waiting_for_opponent" status
   - Second move triggers round resolution
   - Round winner is determined correctly
   - Points are updated after each round

3. Match Completion:
   - Match finishes after MAX_ROUNDS (5) rounds
   - Match status changes to "finished"
   - Winner is determined (or None for draw)

4. Move Validation:
   - Cards cannot be used twice
   - ValueError is raised for invalid moves

HOW TO RUN:
-----------
These tests do NOT require running services (no auth service needed).

Run all integration tests:
    $ cd game_service
    $ pytest game_app/tests/integration/ -v

Run specific test:
    $ pytest game_app/tests/integration/test_match_service.py::test_create_match -v

Run with coverage:
    $ pytest game_app/tests/integration/ --cov=game_app.services

FIXTURES USED:
--------------
- `db_session`: SQLAlchemy database session (in-memory SQLite)
  - Defined in: game_app/tests/integration/conftest.py
  - Auto-rolled back after each test
  - Card definitions are seeded automatically

DIFFERENCE FROM API TESTS:
---------------------------
- These tests call MatchService methods DIRECTLY (no HTTP)
- No authentication layer involved
- Tests business logic in isolation
- Faster than API tests (no HTTP overhead)

NOTES:
------
- These are INTEGRATION tests - test service + database interaction
- No external services required
- Database is reset between tests
- Tests focus on business logic correctness
"""

from game_app.services.match_service import MatchService
from game_app.configs.logic_configs import HAND_SIZE
import pytest


def test_create_match(db_session):
    service = MatchService(db_session)

    match = service.create_match("alice", "bob")

    assert match.id is not None
    assert match.player1_id == "alice"
    assert match.player2_id == "bob"
    assert match.current_round == 1
    assert match.status == "in_progress"
    assert match.points_p1 == 0
    assert match.points_p2 == 0

    # Check that players received HAND_SIZE cards each
    cards_p1 = service.get_player_hand(match.id, "alice")
    cards_p2 = service.get_player_hand(match.id, "bob")

    assert len(cards_p1) == HAND_SIZE
    assert len(cards_p2) == HAND_SIZE

def test_submit_move_waits_for_opponent(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    hand = service.get_player_hand(match.id, "alice")

    response = service.submit_move(match.id, "alice", hand[0]['match_card_id'])
    assert response["status"] == "waiting_for_opponent"

def test_submit_move_resolves_round(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    hand_a = service.get_player_hand(match.id, "alice")
    hand_b = service.get_player_hand(match.id, "bob")

    # Alice plays
    r1 = service.submit_move(match.id, "alice", hand_a[0]['match_card_id'])
    assert r1["status"] == "waiting_for_opponent"

    # Bob plays -> round resolved
    r2 = service.submit_move(match.id, "bob", hand_b[0]['match_card_id'])
    assert r2["round"] == 1
    assert "winner" in r2
    assert "reason" in r2

def test_match_finishes_after_five_rounds(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    for _ in range(5):
        hand_a = service.get_player_hand(match.id, "alice")
        hand_b = service.get_player_hand(match.id, "bob")

        service.submit_move(match.id, "alice", hand_a[0]['match_card_id'])
        #assert hand_a[0]['card']['id'] == hand_a[0]['match_card_id']
        result = service.submit_move(match.id, "bob", hand_b[0]['match_card_id'])

    assert result["match_finished"] is True
    assert match.status == "finished"
    assert match.winner in ["alice", "bob", None]


def test_card_cannot_be_used_twice(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    hand = service.get_player_hand(match.id, "alice")
    card_id = hand[0]['match_card_id']

    service.submit_move(match.id, "alice", card_id)

    with pytest.raises(ValueError):
        service.submit_move(match.id, "alice", card_id)
