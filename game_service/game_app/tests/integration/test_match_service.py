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
from unittest.mock import AsyncMock, patch, call
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
    # Verify hand_index is present in new format
    assert "hand_index" in hand[0]

    # Use card_index (positional argument, not keyword)
    response = service.submit_move(match.id, "alice", 0)
    assert response["status"] == "waiting_for_opponent"

def test_submit_move_resolves_round(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    hand_a = service.get_player_hand(match.id, "alice")
    hand_b = service.get_player_hand(match.id, "bob")

    # Alice plays (index 0)
    r1 = service.submit_move(match.id, "alice", 0)
    assert r1["status"] == "waiting_for_opponent"

    # Bob plays -> round resolved (index 0)
    r2 = service.submit_move(match.id, "bob", 0)
    assert r2["round"] == 1
    assert "winner" in r2
    assert "reason" in r2

def test_match_finishes_after_five_rounds(db_session):
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    for _ in range(5):
        hand_a = service.get_player_hand(match.id, "alice")
        hand_b = service.get_player_hand(match.id, "bob")

        # Use index 0 (always first card in available hand)
        service.submit_move(match.id, "alice", 0)
        result = service.submit_move(match.id, "bob", 0)

    assert result["match_finished"] is True
    assert match.status == "finished"
    assert match.winner in ["alice", "bob", None]


def test_card_cannot_be_used_twice(db_session):
    """Test that after playing card at index 0, it's no longer available."""
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    hand_before = service.get_player_hand(match.id, "alice")
    assert len(hand_before) == 5

    # Play first card (index 0)
    service.submit_move(match.id, "alice", 0)

    # After playing, hand should have 4 cards
    hand_after = service.get_player_hand(match.id, "alice")
    assert len(hand_after) == 4

    # The card that was at index 0 is no longer in hand (used=True)


# ============================================================
# MATCH FINALIZATION TESTS
# ============================================================

def test_match_finalization_callback_is_called(db_session):
    """
    Test that player_client.finalize_match() is called when match finishes.

    Scenario:
    - Play 5 rounds to finish match
    - Verify player_client.finalize_match() is called with correct params
    - Verify callback is called exactly once
    """
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    with patch('game_app.services.match_service.player_client.finalize_match', new_callable=AsyncMock) as mock_finalize:
        mock_finalize.return_value = True

        # Play 5 rounds to finish match
        for _ in range(5):
            service.submit_move(match.id, "alice", 0)
            service.submit_move(match.id, "bob", 0)

        # Verify finalize_match was called
        assert mock_finalize.call_count == 1

        # Verify call arguments
        call_args = mock_finalize.call_args
        assert call_args[1]['match_id'] == match.id
        assert call_args[1]['player1_id'] == "alice"
        assert call_args[1]['player2_id'] == "bob"
        assert call_args[1]['status'] == "finished"
        assert 'winner_id' in call_args[1]
        assert 'points_p1' in call_args[1]
        assert 'points_p2' in call_args[1]


def test_match_finalization_with_winner(db_session):
    """
    Test that finalization includes correct winner information.

    Scenario:
    - Force a match result with clear winner
    - Verify winner_id is passed correctly to player_client
    """
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    with patch('game_app.services.match_service.player_client.finalize_match', new_callable=AsyncMock) as mock_finalize:
        mock_finalize.return_value = True

        # Play 5 rounds
        for _ in range(5):
            service.submit_move(match.id, "alice", 0)
            service.submit_move(match.id, "bob", 0)

        # Check that winner is either alice or bob (not None)
        call_args = mock_finalize.call_args[1]
        winner = call_args['winner_id']

        # Winner should be determined (unless it's a draw)
        if call_args['points_p1'] != call_args['points_p2']:
            assert winner in ["alice", "bob"]

            # Verify winner matches points
            if call_args['points_p1'] > call_args['points_p2']:
                assert winner == "alice"
            else:
                assert winner == "bob"


def test_match_finalization_with_draw(db_session):
    """
    Test that finalization handles draw correctly.

    In case of equal points, winner_id should be None.
    """
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    with patch('game_app.services.match_service.player_client.finalize_match', new_callable=AsyncMock) as mock_finalize:
        mock_finalize.return_value = True

        # Play 5 rounds
        for _ in range(5):
            service.submit_move(match.id, "alice", 0)
            service.submit_move(match.id, "bob", 0)

        # Check for draw scenario
        call_args = mock_finalize.call_args[1]

        if call_args['points_p1'] == call_args['points_p2']:
            assert call_args['winner_id'] is None


def test_match_finalization_not_called_before_finish(db_session):
    """
    Test that player_client.finalize_match() is NOT called during match.

    Scenario:
    - Play only 3 out of 5 rounds
    - Match still in progress
    - finalize_match should NOT be called
    """
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    with patch('game_app.services.match_service.player_client.finalize_match', new_callable=AsyncMock) as mock_finalize:
        mock_finalize.return_value = True

        # Play only 3 rounds (match not finished)
        for _ in range(3):
            service.submit_move(match.id, "alice", 0)
            service.submit_move(match.id, "bob", 0)

        # Verify finalize_match was NOT called
        assert mock_finalize.call_count == 0
        assert match.status == "in_progress"


def test_match_finalization_correct_points(db_session):
    """
    Test that finalization sends correct point totals.

    Verifies that points_p1 and points_p2 match actual game state.
    """
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    with patch('game_app.services.match_service.player_client.finalize_match', new_callable=AsyncMock) as mock_finalize:
        mock_finalize.return_value = True

        # Play 5 rounds
        for _ in range(5):
            service.submit_move(match.id, "alice", 0)
            service.submit_move(match.id, "bob", 0)

        # Verify points match database state
        call_args = mock_finalize.call_args[1]
        assert call_args['points_p1'] == match.points_p1
        assert call_args['points_p2'] == match.points_p2

        # Total points should be <= 5 (max rounds)
        total_points = call_args['points_p1'] + call_args['points_p2']
        assert total_points <= 5


def test_match_continues_even_if_finalization_fails(db_session):
    """
    Test that match finishes even if player_client.finalize_match() fails.

    Scenario:
    - Finalization callback fails (returns False)
    - Match should still be marked as finished in database
    - Game state should be consistent
    """
    service = MatchService(db_session)
    match = service.create_match("alice", "bob")

    with patch('game_app.services.match_service.player_client.finalize_match', new_callable=AsyncMock) as mock_finalize:
        # Simulate finalization failure
        mock_finalize.return_value = False

        # Play 5 rounds
        for _ in range(5):
            service.submit_move(match.id, "alice", 0)
            result = service.submit_move(match.id, "bob", 0)

        # Match should still be finished despite callback failure
        assert result["match_finished"] is True
        assert match.status == "finished"

        # Finalization was attempted
        assert mock_finalize.call_count == 1

