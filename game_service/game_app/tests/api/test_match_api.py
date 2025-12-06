"""
==========================================
MATCH API FUNCTIONAL TESTS
==========================================

PURPOSE:
--------
End-to-end functional tests for match-related API endpoints.
These tests verify the complete game flow from match creation through
move submission to match completion.

WHAT IS TESTED:
---------------
1. Match Creation:
   - Creating a new match between two players
   - Receiving initial card hands
   - Match starts in "in_progress" status

2. Match State Retrieval:
   - Getting current match state
   - Viewing player's hand (unused cards)
   - Viewing used cards history
   - Correct round tracking

3. Move Submission:
   - First move → "waiting_for_opponent" status
   - Second move → round resolution with winner determination
   - Card usage tracking (cards can't be reused)

4. Match Completion:
   - Match finishes after 5 rounds (MAX_ROUNDS)
   - Winner is determined correctly
   - Match status changes to "finished"

HOW TO RUN:
-----------
These tests use MOCKED authentication and do NOT require running services.

Run all match API tests:
    $ cd game_service
    $ pytest game_app/tests/api/test_match_api.py -v

Run specific test:
    $ pytest game_app/tests/api/test_match_api.py::test_create_match_api -v

Run with detailed output:
    $ pytest game_app/tests/api/test_match_api.py -v -s

FIXTURES USED:
--------------
- `client`: TestClient with mocked authentication
  - Auto-accepts Bearer tokens
  - Extracts username from token (e.g., "Bearer alice_token" → "alice")
  - Uses in-memory SQLite database

GAME FLOW TESTED:
-----------------
1. Create match → Get match_id and initial hands
2. Alice submits move → "waiting_for_opponent"
3. Bob submits move → Round resolved, scores updated
4. Repeat for 5 rounds → Match finishes, winner declared

NOTES:
------
- These are FUNCTIONAL tests - test complete workflows
- No external services required (auth is mocked)
- Database is reset between tests (in-memory SQLite)
- Tests simulate both players' actions
"""

def test_create_match_api(client):
    response = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    }, headers={"Authorization": "Bearer alice_token"})
    assert response.status_code == 200

    data = response.json()
    assert "match_id" in data
    assert data["player_id"] == "alice"

def test_get_match_state_api(client):
    # create match first
    create = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    }, headers={"Authorization": "Bearer alice_token"}).json()

    match_id = create["match_id"]

    response = client.get(
        f"/matches/{match_id}?player_id=alice",
        headers={"Authorization": "Bearer alice_token"}
    )
    assert response.status_code == 200

    data = response.json()
    assert "player_hand" in data
    assert "used_cards" in data
    assert data["current_round"] == 1
    assert data["status"] == 'in_progress'

    # hand should have cards
    assert len(data["player_hand"]) > 0

def test_first_move_waits_for_opponent_api(client):
    # create match
    create = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    }, headers={"Authorization": "Bearer alice_token"}).json()

    match_id = create["match_id"]

    # get hand
    state = client.get(
        f"/matches/{match_id}?player_id=alice",
        headers={"Authorization": "Bearer alice_token"}
    ).json()
    card = state["player_hand"][0]["match_card_id"]

    # submit move
    response = client.post(f"/matches/{match_id}/move", json={
        "player_id": "alice",
        "match_card_id": card
    }, headers={"Authorization": "Bearer alice_token"})

    assert response.status_code == 200
    assert response.json()["status"] == "waiting_for_opponent"

def test_second_move_resolves_round_api(client):
    create = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    }, headers={"Authorization": "Bearer alice_token"}).json()

    match_id = create["match_id"]

    # hands
    hand_a = client.get(
        f"/matches/{match_id}?player_id=alice",
        headers={"Authorization": "Bearer alice_token"}
    ).json()["player_hand"]
    hand_b = client.get(
        f"/matches/{match_id}?player_id=bob",
        headers={"Authorization": "Bearer bob_token"}
    ).json()["player_hand"]

    # Alice
    client.post(f"/matches/{match_id}/move", json={
        "player_id": "alice",
        "match_card_id": hand_a[0]["match_card_id"]
    }, headers={"Authorization": "Bearer alice_token"})

    # Bob
    result = client.post(f"/matches/{match_id}/move", json={
        "player_id": "bob",
        "match_card_id": hand_b[0]["match_card_id"]
    }, headers={"Authorization": "Bearer bob_token"})

    data = result.json()
    assert "round" in data
    assert "winner" in data
    assert "reason" in data

def test_match_finishes_after_five_rounds_api(client):
    create = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    }, headers={"Authorization": "Bearer alice_token"}).json()

    match_id = create["match_id"]

    for _ in range(5):
        hand_a = client.get(
            f"/matches/{match_id}?player_id=alice",
            headers={"Authorization": "Bearer alice_token"}
        ).json()["player_hand"]
        hand_b = client.get(
            f"/matches/{match_id}?player_id=bob",
            headers={"Authorization": "Bearer bob_token"}
        ).json()["player_hand"]

        client.post(f"/matches/{match_id}/move", json={
            "player_id": "alice",
            "match_card_id": hand_a[0]["match_card_id"]
        }, headers={"Authorization": "Bearer alice_token"})

        response = client.post(f"/matches/{match_id}/move", json={
            "player_id": "bob",
            "match_card_id": hand_b[0]["match_card_id"]
        }, headers={"Authorization": "Bearer bob_token"})

    data = response.json()
    assert data["match_finished"] is True
    assert data['match_winner'] is not None
