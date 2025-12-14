# Tri-Duel Player Service

Player profiles + match history + leaderboard.

## Run

### Local (SQLite)

```bash
cd player_service
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### Docker (PostgreSQL + self-signed HTTPS)

```bash
cd player_service
docker compose up --build
```

- Base URL: `https://localhost:8002`
- Reset DB (dev): `docker compose down -v`

## Endpoints

- `GET /health` (public)
- `POST /players`, `GET /players/me` (JWT required; token validated via Auth Service)
- `GET /players/{external_id}/matches`, `GET /players/{external_id}/matches/{match_id}` (public; match details include ordered `turns` with `player1_card_name`/`player2_card_name`)
- `GET /leaderboard` (public)
- `POST /matches` (internal; Game Service only)

Docs: `http://localhost:8002/docs` (or `https://localhost:8002/docs` when TLS is enabled).

## Rules we enforce

- Profiles are not auto-created: create them via `POST /players` before recording matches.
- Match history is append-only: no update/delete endpoints for matches.
- Idempotency: `external_match_id` prevents duplicate match inserts.
- Internal auth: `POST /matches` requires a JWT where `sub == GAME_SERVICE_SUBJECT` (default `game_service`).

## Testing

Postman collection: `postman/player_service.postman_collection.json`

OpenAPI spec (repo root): `openapi.yaml`
