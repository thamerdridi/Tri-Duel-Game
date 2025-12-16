import httpx


def _patch_auth_validation(monkeypatch, *, valid_tokens: dict[str, dict]):
    from app import auth as auth_module

    original_async_client = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method != "GET" or request.url.path != "/auth/validate":
            return httpx.Response(404, json={"detail": "not found"})

        token = request.url.params.get("token")
        payload = valid_tokens.get(token)
        if payload is None:
            return httpx.Response(401, json={"detail": "Invalid or expired token"})
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)

    class PatchedAsyncClient:
        def __init__(self, *args, **kwargs):
            self._client = original_async_client(transport=transport)

        async def __aenter__(self):
            return self._client

        async def __aexit__(self, exc_type, exc, tb):
            await self._client.aclose()

    monkeypatch.setattr(auth_module.httpx, "AsyncClient", PatchedAsyncClient)
    monkeypatch.setattr(auth_module, "AUTH_SERVICE_URL", "http://auth.local")


def test_profile_flow_uses_auth_validate(client, monkeypatch):
    _patch_auth_validation(
        monkeypatch,
        valid_tokens={
            "alice_token": {"sub": "alice", "user_id": 1},
        },
    )

    resp = client.post(
        "/players",
        headers={"Authorization": "Bearer alice_token"},
        json={"username": "Alice"},
    )
    assert resp.status_code == 201
    assert resp.json()["external_id"] == "alice"

    me = client.get("/players/me", headers={"Authorization": "Bearer alice_token"})
    assert me.status_code == 200
    assert me.json()["external_id"] == "alice"


def test_profile_invalid_token_rejected(client, monkeypatch):
    _patch_auth_validation(
        monkeypatch,
        valid_tokens={},
    )

    resp = client.post(
        "/players",
        headers={"Authorization": "Bearer bad_token"},
        json={"username": "Alice"},
    )
    assert resp.status_code == 401


def test_game_service_post_match_with_internal_api_key(client, monkeypatch):
    _patch_auth_validation(
        monkeypatch,
        valid_tokens={
            "alice_token": {"sub": "alice", "user_id": 1},
            "bob_token": {"sub": "bob", "user_id": 2},
        },
    )

    client.post(
        "/players",
        headers={"Authorization": "Bearer alice_token"},
        json={"username": "Alice"},
    )
    client.post(
        "/players",
        headers={"Authorization": "Bearer bob_token"},
        json={"username": "Bob"},
    )

    payload = {
        "player1_external_id": "alice",
        "player2_external_id": "bob",
        "winner_external_id": "alice",
        "player1_score": 1,
        "player2_score": 0,
        "external_match_id": "match-1",
        "turns": [
            {
                "turn_number": 1,
                "player1_card_name": "Rock 1",
                "player2_card_name": "Paper 2",
                "winner_external_id": "bob",
            }
        ],
    }

    from app import auth as auth_module
    auth_module.SERVICE_API_KEY = "test_key"

    ok = client.post("/matches", headers={"X-Internal-Api-Key": "test_key"}, json=payload)
    assert ok.status_code == 201
    match_id = ok.json()["id"]

    missing = client.post("/matches", json=payload | {"external_match_id": "match-2"})
    assert missing.status_code == 401

    forbidden = client.post(
        "/matches",
        headers={"X-Internal-Api-Key": "wrong"},
        json=payload | {"external_match_id": "match-3"},
    )
    assert forbidden.status_code == 403

    detail = client.get(f"/players/alice/matches/{match_id}")
    assert detail.status_code == 200
    assert detail.json()["turns"][0]["player1_card_name"] == "Rock 1"
