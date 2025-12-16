# Tri-Duel Player Service

Player profiles + match history + leaderboard.

## Run

### Recommended (full system via Gateway)

From the repo root:

```bash
docker compose up -d --build
```

- Base URL (via Gateway): `https://localhost:8443/player`
- Swagger UI (via Gateway): `https://localhost:8443/player/docs`

### Standalone (dev)

This starts Player Service + its own Postgres (and an Auth container for token validation).

```bash
cd player_service
../certs/generate-certs.sh
docker compose up --build
```

- Base URL: `https://localhost:8002`
- Reset DB (dev): `docker compose down -v`

## Endpoints

- `GET /health` (public)
- `POST /internal/players` (internal; API key; create/update profiles)
- `POST /players`, `GET /players/me` (JWT required; token validated via Auth Service)
- `GET /players/{external_id}/matches`, `GET /players/{external_id}/matches/{match_id}` (public)
- `GET /leaderboard` (public)
- `POST /matches` (internal; Game Service only)

## Configuration

- `PLAYER_SERVICE_API_KEY` is required for internal endpoints (`/internal/players`, `/matches`).
- When `AUTH_SERVICE_URL` is `https://...`, the service enforces TLS verification using `CA_BUNDLE_PATH`.

## Testing

### Pytest

```bash
cd player_service
pytest -v
```

### Postman / Newman

Collection: `postman/player_service.postman_collection.json`

- Full system (Gateway): set `auth_base_url=https://localhost:8443/auth` and `player_base_url=https://localhost:8443/player`.
- TLS verification: import `certs/ca/ca.crt` into Postman, or run Newman with `NODE_EXTRA_CA_CERTS=certs/ca/ca.crt`.
