# Tri‑Duel Game Service — Backend API

## Table of Contents
1. **What This Backend Does**
2. **Quick Setup (Local & Docker)**
3. **How the API Works**
   - Creating a Match
   - Getting Match State
   - Submitting a Move
   - Example Gameplay Flow
4. **Testing the API**
5. **Game Logic Overview**
6. **Project Structure**
7. **Configuration**
8. **You’re Ready to Go!**

---

# 1. What This Backend Does

This backend implements **Tri‑Duel**, a fast competitive card game inspired by Rock–Paper–Scissors (RPS+) with power values.

The backend:
- creates matches,
- generates decks,
- deals cards,
- validates moves,
- resolves rounds using RPS rules,
- tracks points,
- determines match winners,
- exposes clean REST API endpoints.

Players receive **unique cards** (from a shared full deck), play one card per round, and the backend handles the entire game logic.

---

# 2. Quick Setup

## **Local Setup**

```bash
pip install -r requirements.txt
uvicorn game_app.main:app --reload
```

API documentation:  
http://localhost:8000/docs

---

## **Running with Docker**

Use docker-compose:
```bash
docker-compose up --build
```

Or docker-compose-prod for production setting (Copies code into container):
```bash
docker-compose -f docker-compose-prod.yml up --build
```

### **Building manually**

Build:
```bash
docker build -t game-service .
```

Run:
```bash
docker run -p 8000:8000 game-service
```

---

# 3. How the API Works

The API is structured around **matches**. A match always involves exactly **two players**.

---

## **POST /matches**  
Create a new match.

### Request:
```json
{
  "player1_id": "alice",
  "player2_id": "bob"
}
```

### Response:
```json
{
  "match_id": "uuid",
  "player_id": "alice",
  "hand": [
    {"id": 3, "category": "rock", "power": 2}
  ],
    "status": "in_progress"
}
```

Player receives their starting hand.

---

## **GET /matches/{match_id}?player_id=alice**  
Get full match state for the player.

### Response:
```json
{
  "match_id": "uuid",
  "status": "in_progress",
  "current_round": 1,
  "points_p1": 0,
  "points_p2": 0,
  "player_hand": [
    {
      "match_card_id": 7,
      "card": {"id": 3, "category": "rock", "power": 2}
    }
  ],
  "used_cards": [],
  "opponent_used_cards": [],
  "match_winner": null
}
```

---

## **POST /matches/{match_id}/move**

### Request:
```json
{
  "player_id": "alice",
  "match_card_id": 7
}
```

### Possible Response 1 — waiting:
```json
{ "status": "waiting_for_opponent" }
```

### Possible Response 2 — round resolved:
```json
{
  "round": 1,
  "winner": "p1",
  "reason": "rock beats scissors",
  "points_p1": 1,
  "points_p2": 0,
  "match_finished": false,
  "match_winner": null
}
```

---

# 4. Example Gameplay Flow

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Player creates match | `POST /matches` |
| 2 | Players check hands | `GET /matches/{id}` |
| 3 | Player 1 submits card | `POST /matches/{id}/move` |
| 4 | Player 2 submits card | `POST /matches/{id}/move` |
| 5 | Backend resolves round | automatic |
| 6 | Repeat for 5 rounds | — |
| 7 | Backend announces winner | returned in response |

---

# 5. Testing the API

### **Run all tests**
```bash
pytest -q
```

### Test categories:
- **Unit tests:** `tests/unit/`
- **Integration tests:** `tests/integration/`
- **API tests:** `tests/api/`

All tests use in‑memory SQLite.

---

# 6. Game Logic Overview

### Card categories:
- **rock:** 1, 2, 3, 4, 6, 9  
- **paper:** 1, 2, 3, 5, 7, 9  
- **scissors:** 1, 2, 4, 5, 7, 8  

### Rounds:
- 5 rounds total  
- each round players play 1 card  
- cards are discarded after use  
- winner gets 1 point

### RPS rules:
- Rock beats Scissors  
- Scissors beats Paper  
- Paper beats Rock  
- If same category → higher power wins  
- If same power → draw  

---

# 7. Project Structure

```
game_app/
│
├── api/
│   ├── router.py
│   ├── schemas.py
├── configs/
│   ├── cards_config.py
│   ├── logic_configs.py
├── database/
│   ├── database.py
│   ├── models.py
│   └── init/initialize_cards.py
├── logic/
│   ├── deck.py
│   ├── rps.py
│   ├── models.py
├── services/
│   └── match_service.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
└── main.py
```

---

# 8. Configuration

Configuration constants (round count, hand size, domain mapping) live in:

```
game_app/configs/
    logic_configs.py
    cards_config.py
    database_config.py
```

Some variables are prepped to be set in docker-compose with ENV variables.

Database is SQLite by default but can be swapped out for PostgreSQL.

---

# You’re Ready to Go!

Tri‑Duel backend is fully functional and prepared for integration with:
- **Auth service (JWT)**
- **Matchmaking service**
- **Frontend client (web/mobile)**

Let the game begin!
