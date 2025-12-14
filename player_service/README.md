# Tri-Duel Player Service

The Player Service manages player profiles, match history, cards, and leaderboards for the Tri-Duel game.

## Responsibilities

- Store and serve the 18 game cards
- Record match results from Game Service
- Track player profiles and statistics
- Provide match history and leaderboards

## Quick Start

### Local Development (with SQLite)

```bash
cd player_service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Service will be available at: http://localhost:8000

If you changed the DB schema and want a fresh dev database, delete `players.db` and restart the service.

## Postman Tests

Assignment Postman collection is available at `postman/player_service.postman_collection.json`.
If running over self-signed HTTPS, disable SSL verification in Postman (or use `--insecure` with Newman).

### With Docker & PostgreSQL

```bash
cd player_service
docker compose up --build
```

Service will be available at: https://localhost:8000 (self-signed)

If you changed the DB schema and just want a fresh dev database:

```bash
docker compose down -v
docker compose up --build
```

If your system uses `docker-compose` (v1), replace `docker compose` with `docker-compose`.

## API Endpoints

### Health Check

**`GET /health`**

Check if the service is running.

**Response:**
```json
{
  "status": "ok"
}
```

---

### Player Profiles

**`GET /players/me`**

Get the current user's profile.

**Auth:** Requires `Authorization: Bearer <jwt>`.

---

### Cards

**`GET /cards`**

Get all 18 Tri-Duel cards.

**Response:**
```json
[
  {
    "id": 1,
    "category": "rock",
    "power": 1,
    "name": "Rock 1"
  },
]
```

**`GET /cards/{card_id}`**

Get a specific card by ID.

**Response:**
```json
{
  "id": 1,
  "category": "rock",
  "power": 1,
  "name": "Rock 1",
}
```

### Player Profiles

**`POST /players`**

Create (or update) the Player Service profile for the authenticated user.

**Auth:** Requires `Authorization: Bearer <jwt>` (validated via Auth Service).

**Request Body:**
```json
{
  "username": "optional-display-name"
}
```

**Response:** Player profile.

---

### Matches (Integration Endpoint)

**`POST /matches`**

 **Called by Game Service** when a match finishes.

**Auth:** Requires `Authorization: Bearer <jwt>` for a token whose `sub` matches `GAME_SERVICE_SUBJECT` (default: `game_service`).

**Request Body:**
```json
{
  "player1_external_id": "user123",
  "player2_external_id": "user456",
  "winner_external_id": "user123",
  "player1_score": 3,
  "player2_score": 2,
  "external_match_id": "game-service-match-id",
  "turns": []
}
```

**Response:**
```json
{
  "id": 1
}
```

**Notes:**
- `winner_external_id` can be `null` for draws
- `external_match_id` is used for idempotency (duplicate posts with the same id won't create duplicate matches)
- Players referenced in a match must already exist in `player_profiles` (create them via `POST /players`).
- Match details include the ordered `turns` list (sequence of moves).

---

### Player Match History

**`GET /players/{external_id}/matches`**

Get all matches for a specific player.

**Response:**
```json
[
  {
    "id": 1,
    "external_match_id": "game-service-match-id",
    "player1_external_id": "user123",
    "player2_external_id": "user456",
    "winner_external_id": "user123",
    "player1_score": 3,
    "player2_score": 2,
    "created_at": "2025-11-21T10:00:00",
  }
]
```

**`GET /players/{external_id}/matches/{match_id}`**

Get match information by ID.

**Response:**
```json
{
  "id": 1,
  "external_match_id": "game-service-match-id",
  "player1_external_id": "user123",
  "player2_external_id": "user456",
  "winner_external_id": "user123",
  "player1_score": 3,
  "player2_score": 2,
  "created_at": "2025-11-21T10:00:00",
  "turns": []
}
```

---

### Leaderboard

**`GET /leaderboard`**

Get player rankings sorted by wins.

**Response:**
```json
[
  {
    "external_id": "user123",
    "username": "user123",
    "wins": 5,
    "matches": 8
  },
  {
    "external_id": "user456",
    "username": "user456",
    "wins": 3,
    "matches": 8
  }
]
```

**Sorting:** Players with more wins appear first. Ties are broken by total matches, then alphabetically by username.

---

## Interactive API Documentation

Once the service is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Architecture

```
player_service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + startup
│   ├── db.py                # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── routers/
│       ├── __init__.py
│       ├── card.py          # Card endpoints
│       ├── players.py       # Player & leaderboard endpoints
│       └── matches.py       # Match ingestion endpoint
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Database Schema

### Tables

**`player_profiles`**
- Stores player information

**`cards`**
- 18 predefined Tri-Duel cards (seeded on startup)

**`matches`**
- Match results with scores and winner

## Integration with Other Services

### Game Service → Player Service

When a match finishes, Game Service calls:

```python
import requests

response = requests.post(
    "http://player-service:8000/matches",
    json=match_result
)

```

### Frontend → Player Service

Frontend fetches data directly:
- Cards for display
- Match history for player profiles
- Leaderboard for rankings

## Docker Configuration

**Environment Variables:**

- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql+psycopg2://user:password@postgres:5432/tri_duel_player`)

**Exposed Port:** `8000`

## Notes

- Players are automatically created with `username = external_id` when they first appear in a match
- Card seeding happens automatically on startup (only runs once)
- All match data is immutable once stored
- The service doesn't validate game logic—it trusts Game Service results

## Team Integration

This service is part of the Tri-Duel microservices architecture:

1. **Auth Service** - User authentication & tokens
2. **Game Service** - Game logic & match execution
3. **Player Service** - Data storage & statistics (this service)

---

Built with FastAPI, SQLAlchemy, and PostgreSQL.
