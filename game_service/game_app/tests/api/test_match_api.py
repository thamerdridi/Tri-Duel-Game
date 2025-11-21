
def test_create_match_api(client):
    response = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    })
    assert response.status_code == 200

    data = response.json()
    assert "match_id" in data
    assert data["player_id"] == "alice"

def test_get_match_state_api(client):
    # create match first
    create = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    }).json()

    match_id = create["match_id"]

    response = client.get(f"/matches/{match_id}?player_id=alice")
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
    }).json()

    match_id = create["match_id"]

    # get hand
    state = client.get(f"/matches/{match_id}?player_id=alice").json()
    card = state["player_hand"][0]["match_card_id"]

    # submit move
    response = client.post(f"/matches/{match_id}/move", json={
        "player_id": "alice",
        "match_card_id": card
    })

    assert response.status_code == 200
    assert response.json()["status"] == "waiting_for_opponent"

def test_second_move_resolves_round_api(client):
    create = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    }).json()

    match_id = create["match_id"]

    # hands
    hand_a = client.get(f"/matches/{match_id}?player_id=alice").json()["player_hand"]
    hand_b = client.get(f"/matches/{match_id}?player_id=bob").json()["player_hand"]

    # Alice
    client.post(f"/matches/{match_id}/move", json={
        "player_id": "alice",
        "match_card_id": hand_a[0]["match_card_id"]
    })

    # Bob
    result = client.post(f"/matches/{match_id}/move", json={
        "player_id": "bob",
        "match_card_id": hand_b[0]["match_card_id"]
    })

    data = result.json()
    assert "round" in data
    assert "winner" in data
    assert "reason" in data

def test_match_finishes_after_five_rounds_api(client):
    create = client.post("/matches", json={
        "player1_id": "alice",
        "player2_id": "bob"
    }).json()

    match_id = create["match_id"]

    for _ in range(5):
        hand_a = client.get(f"/matches/{match_id}?player_id=alice").json()["player_hand"]
        hand_b = client.get(f"/matches/{match_id}?player_id=bob").json()["player_hand"]

        client.post(f"/matches/{match_id}/move", json={
            "player_id": "alice",
            "match_card_id": hand_a[0]["match_card_id"]
        })

        response = client.post(f"/matches/{match_id}/move", json={
            "player_id": "bob",
            "match_card_id": hand_b[0]["match_card_id"]
        })

    data = response.json()
    assert data["match_finished"] is True
    assert data['match_winner'] is not None
