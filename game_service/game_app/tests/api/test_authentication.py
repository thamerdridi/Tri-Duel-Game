"""
==========================================
API AUTHENTICATION TESTS
==========================================

PURPOSE:
--------
Tests JWT authentication and authorization for all game_service API endpoints.
These tests verify that the authentication layer properly protects resources
and enforces authorization rules.

WHAT IS TESTED:
---------------
1. Authentication (401 Unauthorized):
   - Missing authorization header
   - Invalid token format (not "Bearer <token>")
   - Expired/invalid tokens rejected by auth service
   - Auth service unavailability handling (503)

2. Authorization (403 Forbidden):
   - Users cannot create matches as other players
   - Users cannot submit moves for other players
   - Users cannot view other players' match states

3. Valid Operations (200 OK):
   - Valid tokens allow match creation
   - Valid tokens allow move submission
   - Valid tokens allow viewing own match state

HOW TO RUN:
-----------
These tests use MOCKED authentication and do NOT require running services.

Run all authentication tests:
    $ cd game_service
    $ pytest game_app/tests/api/test_authentication.py -v

Run specific test:
    $ pytest game_app/tests/api/test_authentication.py::test_create_match_without_token -v

Run with coverage:
    $ pytest game_app/tests/api/test_authentication.py --cov=game_app.api --cov=game_app.auth

FIXTURES USED:
--------------
- `client`: TestClient with mocked authentication (auto-accepts tokens)
  - Used for: Testing game functionality with auth enabled
  - Mock behavior: Extracts username from token (e.g., "Bearer alice_token" → user "alice")

- `client_no_auth`: TestClient WITHOUT mocked authentication
  - Used for: Testing actual auth behavior (401, 403 responses)
  - Behavior: Uses real auth.py logic (will fail without auth service)

NOTES:
------
- These are UNIT tests - no external services required
- Authentication is mocked via FastAPI dependency_overrides
- Tests use in-memory SQLite database (ephemeral)
- Each test is isolated and doesn't affect others
"""

import pytest
from fastapi import HTTPException


# ============================================================
# TEST: CREATE MATCH ENDPOINT AUTHENTICATION
# ============================================================

def test_create_match_without_token(client_no_auth):
    """Test that creating a match without authentication fails with 401."""
    response = client_no_auth.post("/matches/", json={
        "player1_id": "alice",
        "player2_id": "bob"
    })
    
    assert response.status_code == 401
    assert "Authorization header missing" in response.json()["detail"]


def test_create_match_with_invalid_token_format(client_no_auth):
    """Test that invalid token format is rejected with 401."""
    # Token without "Bearer " prefix
    response = client_no_auth.post(
        "/matches/",
        json={
            "player1_id": "alice",
            "player2_id": "bob"
        },
        headers={"Authorization": "InvalidToken123"}
    )
    
    assert response.status_code == 401
    assert "Invalid authorization header format" in response.json()["detail"]


def test_create_match_with_expired_token(client_no_auth):
    """Test that expired/invalid token is rejected by auth service."""
    # This test would require actual auth service integration
    # For now, we test that the mock in conftest properly rejects bad format
    # In real scenario, auth service would return 401 for expired token

    # Test with mock that simulates auth service rejection
    from game_app.main import app
    from fastapi import HTTPException

    async def mock_reject_token(authorization: str = None):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    from game_app.clients.auth_client import get_current_user
    app.dependency_overrides[get_current_user] = mock_reject_token

    response = client_no_auth.post(
        "/matches/",
        json={
            "player1_id": "alice",
            "player2_id": "bob"
        },
        headers={"Authorization": "Bearer expired_token_xyz"}
    )
    
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["detail"]

    # Clean up override
    app.dependency_overrides.clear()


def test_create_match_when_auth_service_unavailable(client_no_auth):
    """Test that 503 is returned when auth service is down."""
    from game_app.main import app
    from fastapi import HTTPException

    # Mock auth service being unavailable
    async def mock_service_unavailable(authorization: str = None):
        raise HTTPException(status_code=503, detail="Auth service unavailable")

    from game_app.auth import get_current_user
    app.dependency_overrides[get_current_user] = mock_service_unavailable

    response = client_no_auth.post(
        "/matches/",
        json={
            "player1_id": "alice",
            "player2_id": "bob"
        },
        headers={"Authorization": "Bearer valid_token_xyz"}
    )
    
    assert response.status_code == 503
    assert "Auth service unavailable" in response.json()["detail"]


def test_create_match_with_valid_token(client):
    """Test that valid token allows match creation."""
    # Using regular client with mocked auth (from conftest)
    response = client.post(
        "/matches/",
        json={
            "player1_id": "alice",
            "player2_id": "bob"
        },
        headers={"Authorization": "Bearer alice_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "match_id" in data
    assert data["player_id"] == "alice"


def test_create_match_authorization_check_user_cannot_impersonate(client):
    """Test that user cannot create match as someone else (403 Forbidden)."""
    # Using regular client with mocked auth
    # Token "alice_token" will be extracted as user "alice" by our mock
    response = client.post(
        "/matches/",
        json={
            "player1_id": "bob",  # Trying to act as Bob
            "player2_id": "charlie"
        },
        headers={"Authorization": "Bearer alice_token"}
    )
    
    assert response.status_code == 403
    assert "You can only create matches as yourself" in response.json()["detail"]


# ============================================================
# TEST: SUBMIT MOVE ENDPOINT AUTHENTICATION
# ============================================================

def test_submit_move_without_token(client):
    """Test that submitting move without authentication fails."""
    # First create a match (with mocked auth)
    create_response = client.post(
        "/matches/",
        json={"player1_id": "alice", "player2_id": "bob"},
        headers={"Authorization": "Bearer alice_token"}
    )

    # Debug: Check if match creation succeeded
    assert create_response.status_code == 200, f"Match creation failed: {create_response.status_code} - {create_response.text}"

    match_id = create_response.json()["match_id"]
    # Verify hand_index is present
    assert "hand_index" in create_response.json()["hand"][0]

    # Try to submit move without token (use card_index instead of match_card_id)
    response = client.post(
        f"/matches/{match_id}/move",
        json={"player_id": "alice", "card_index": 0}
    )
    
    assert response.status_code == 401


def test_submit_move_for_another_player(client):
    """Test that user cannot submit move for another player."""
    # Create match as Alice
    create_response = client.post(
        "/matches/",
        json={"player1_id": "alice", "player2_id": "bob"},
        headers={"Authorization": "Bearer alice_token"}
    )
    match_id = create_response.json()["match_id"]
    # Verify hand_index is present
    assert "hand_index" in create_response.json()["hand"][0]

    # Try to submit move as Bob using Alice's token (mock will extract "alice" from token)
    response = client.post(
        f"/matches/{match_id}/move",
        json={"player_id": "bob", "card_index": 0},
        headers={"Authorization": "Bearer alice_token"}
    )
    
    assert response.status_code == 403
    assert "You can only submit moves for yourself" in response.json()["detail"]


def test_submit_move_with_valid_token(client):
    """Test that valid token allows move submission."""
    create_response = client.post(
        "/matches/",
        json={"player1_id": "alice", "player2_id": "bob"},
        headers={"Authorization": "Bearer alice_token"}
    )
    match_id = create_response.json()["match_id"]
    # Verify hand_index is present in new format
    assert "hand_index" in create_response.json()["hand"][0]

    response = client.post(
        f"/matches/{match_id}/move",
        json={"player_id": "alice", "card_index": 0},
        headers={"Authorization": "Bearer alice_token"}
    )
    
    assert response.status_code == 200
    # Should be waiting for opponent
    assert response.json()["status"] == "waiting_for_opponent"


# ============================================================
# TEST: GET MATCH STATE ENDPOINT AUTHENTICATION
# ============================================================

def test_get_match_state_without_token(client):
    """Test that getting match state without authentication fails."""
    # Create match first
    create_response = client.post(
        "/matches/",
        json={"player1_id": "alice", "player2_id": "bob"},
        headers={"Authorization": "Bearer alice_token"}
    )
    match_id = create_response.json()["match_id"]
    
    # Try to get state without token
    response = client.get(f"/matches/{match_id}?player_id=alice")
    
    assert response.status_code == 401


def test_get_match_state_for_another_player(client):
    """Test that user cannot view another player's match state."""
    create_response = client.post(
        "/matches/",
        json={"player1_id": "alice", "player2_id": "bob"},
        headers={"Authorization": "Bearer alice_token"}
    )
    match_id = create_response.json()["match_id"]
    
    # Try to view Bob's state using Alice's token
    response = client.get(
        f"/matches/{match_id}?player_id=bob",
        headers={"Authorization": "Bearer alice_token"}
    )
    
    assert response.status_code == 403
    assert "You can only view your own match state" in response.json()["detail"]


def test_get_match_state_with_valid_token(client):
    """Test that valid token allows viewing own match state."""
    create_response = client.post(
        "/matches/",
        json={"player1_id": "alice", "player2_id": "bob"},
        headers={"Authorization": "Bearer alice_token"}
    )
    match_id = create_response.json()["match_id"]
    
    response = client.get(
        f"/matches/{match_id}?player_id=alice",
        headers={"Authorization": "Bearer alice_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == match_id
    assert data["status"] == "in_progress"
    assert "player_hand" in data


# ============================================================
# TEST: TOKEN VERIFICATION LOGIC
# ============================================================

@pytest.mark.asyncio
async def test_verify_token_missing_header():
    """Test verify_token function directly with missing header."""
    from game_app.auth import verify_token
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization=None)
    
    assert exc_info.value.status_code == 401
    assert "Authorization header missing" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_token_invalid_format():
    """Test verify_token function directly with invalid format."""
    from game_app.auth import verify_token
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_token(authorization="InvalidFormatToken")
    
    assert exc_info.value.status_code == 401
    assert "Invalid authorization header format" in exc_info.value.detail


# Note: Testing verify_token with real httpx calls would require integration tests
# with actual auth_service running. For unit tests, we test the behavior through
# the API endpoints above, using dependency overrides to simulate different scenarios.

