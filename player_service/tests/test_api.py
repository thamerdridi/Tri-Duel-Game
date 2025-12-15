def set_user(client, sub: str) -> None:
    from app import auth as auth_module

    async def override_get_current_user():
        return {"sub": sub, "user_id": 1}

    client.app.dependency_overrides[auth_module.get_current_user] = override_get_current_user


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_invalid_path(client):
    resp = client.get("/healthz")
    assert resp.status_code == 404


def test_create_profile_requires_auth(client):
    resp = client.post("/players", json={"username": "Alice"})
    assert resp.status_code == 401


def test_create_profile_ok(client):
    set_user(client, "alice")
    resp = client.post("/players", json={"username": "Alice"})
    assert resp.status_code == 201
    assert resp.json()["external_id"] == "alice"
    assert resp.json()["username"] == "Alice"


def test_get_my_profile_not_found(client):
    set_user(client, "alice")
    resp = client.get("/players/me")
    assert resp.status_code == 404


def test_get_my_profile_ok(client):
    set_user(client, "alice")
    client.post("/players", json={"username": "Alice"})
    resp = client.get("/players/me")
    assert resp.status_code == 200
    assert resp.json()["external_id"] == "alice"


def test_list_player_matches_invalid_player(client):
    resp = client.get("/players/nope/matches")
    assert resp.status_code == 404


def test_post_match_requires_internal_api_key(client):
    payload = {
        "player1_external_id": "alice",
        "player2_external_id": "bob",
        "winner_external_id": "alice",
        "player1_score": 1,
        "player2_score": 0,
        "external_match_id": "match-1",
        "turns": [],
    }
    resp = client.post("/matches", json=payload)
    assert resp.status_code == 401


def test_post_match_validation_error(client):
    from app import auth as auth_module
    auth_module.PLAYER_INTERNAL_API_KEY = "test_key"

    resp = client.post(
        "/matches",
        headers={"X-Internal-Api-Key": "test_key"},
        json={},
    )
    assert resp.status_code == 422


def test_post_match_idempotent_and_history(client):
    set_user(client, "alice")
    client.post("/players", json={"username": "Alice"})
    set_user(client, "bob")
    client.post("/players", json={"username": "Bob"})

    from app import auth as auth_module
    auth_module.PLAYER_INTERNAL_API_KEY = "test_key"

    payload = {
        "player1_external_id": "alice",
        "player2_external_id": "bob",
        "winner_external_id": "alice",
        "player1_score": 3,
        "player2_score": 1,
        "external_match_id": "match-123",
        "moves_log": "turn 1: alice played Rock 1; bob played Paper 2; bob wins",
        "turns": [
            {
                "turn_number": 1,
                "player1_card_name": "Rock 1",
                "player2_card_name": "Paper 2",
                "winner_external_id": "bob",
            }
        ],
    }

    r1 = client.post(
        "/matches",
        headers={"X-Internal-Api-Key": "test_key"},
        json=payload,
    )
    assert r1.status_code == 201
    match_id = r1.json()["id"]

    r2 = client.post(
        "/matches",
        headers={"X-Internal-Api-Key": "test_key"},
        json=payload,
    )
    assert r2.status_code == 201
    assert r2.json()["id"] == match_id

    list_resp = client.get("/players/alice/matches")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    detail_resp = client.get(f"/players/alice/matches/{match_id}")
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    assert body["id"] == match_id
    assert body["external_match_id"] == "match-123"
    assert len(body["turns"]) == 1
    assert body["turns"][0]["player1_card_name"] == "Rock 1"
    assert body["moves_log"] is not None


def test_get_match_detail_invalid_match(client):
    set_user(client, "alice")
    client.post("/players", json={"username": "Alice"})

    resp = client.get("/players/alice/matches/999")
    assert resp.status_code == 404


def test_leaderboard_ok(client):
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_internal_sync_requires_api_key(client):
    resp = client.post("/internal/players", json={"external_id": "alice"})
    assert resp.status_code == 401


def test_internal_sync_ok(client):
    from app import auth as auth_module
    auth_module.PLAYER_INTERNAL_API_KEY = "test_key"

    resp = client.post(
        "/internal/players",
        headers={"X-Internal-Api-Key": "test_key"},
        json={"external_id": "alice", "username": "Alice"},
    )
    assert resp.status_code == 201
    assert resp.json()["external_id"] == "alice"
