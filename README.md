# Tri-Duel Game - Microservices Architecture

A rock-paper-scissors card game with three microservices: Auth, Player, and Game.

Authors: Michal Sachanbinski, Othman Alhammali Shoaib Alhadiri, Thamer DRIDI - (Group 5).

## Instructions

To run and test the complete application:

1. Ensure Docker and Docker Compose are installed
2. Run: `sudo docker-compose up -d --build`
3. Wait 30 seconds
4. Follow the instructions below to test the services

All services, databases, and dependencies are containerized.

## Architecture

```
Auth Service (8001) → JWT tokens → Player Service (8002)
                                 → Game Service (8003)
```

- **Auth**: User registration, login, token validation
- **Player**: Profiles, match history, leaderboard  
- **Game**: Match logic, RPS engine, rounds

Postman collections (service-level API tests) live under each service folder, e.g. `player_service/postman/player_service.postman_collection.json`.

## Prerequisites

- Docker
- Docker Compose

**Note: NO other dependencies needed. Everything runs inside Docker containers.**

## Running the Architecture

### Step 1: Start All Services (Only Command Needed)

```bash
sudo docker-compose up -d --build
```

This single command will:
- Build all three Docker images (Auth, Player, Game)
- Create containers with all dependencies installed
- Start all services on ports 8001, 8002, 8003
- Set up networking between services

Wait 30 seconds for services to initialize.

### Step 2: Verify Deployment

Manually verify each service:

```bash
curl http://localhost:8001/health  # Auth Service - Should return {"status":"ok"}
curl http://localhost:8002/health  # Player Service - Should return {"status":"ok"}
curl http://localhost:8003/        # Game Service - Should return {"status":"ok"}
```

## Playing a Complete Match

### Step 1: Register Two Players

```bash
# Register player 1
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "email": "player1@test.com", "password": "pass123"}'

# Register player 2
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "player2", "email": "player2@test.com", "password": "pass456"}'
```

### Step 2: Login as Player 1 (Get JWT Token)

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "pass123"}'
```

Copy the `access_token` from the response.

### Step 2.1: Create Player Service Profile (once per user)

```bash
curl -X POST http://localhost:8002/players \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"username": "player1"}'
```

### Step 3: View Available Cards

```bash
curl http://localhost:8003/cards
```

This endpoint returns an SVG. Open it in a browser for the full deck view, and use `/cards/{id}` for single-card view.

### Step 4: Start a Match

```bash
curl -X POST http://localhost:8003/matches/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player1_id": "player1",
    "player2_id": "player2"
  }'
```

Save the `match_id` from the response. Also note the `hand` cards returned - each has a `match_card_id`.

### Step 5: Play Rounds (Best of 5)

Players take turns playing cards. Use the `match_card_id` from your hand (not the card `id`).

```bash
# Player 1 plays a card
curl -X POST http://localhost:8003/matches/MATCH_ID_HERE/move \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "player1",
    "match_card_id": 1
  }'

# Player 2 plays a card (round completes and shows result)
curl -X POST http://localhost:8003/matches/MATCH_ID_HERE/move \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "player2",
    "match_card_id": 6
  }'

# Continue alternating until match ends (first to 3 round wins)
```

### Step 6: View Match Results

```bash
# Get match state from Game Service
curl "http://localhost:8003/matches/MATCH_ID_HERE?player_id=player1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Step 7: Record Match in Player Service (for statistics)

After a match completes, record it in the Player Service for leaderboard tracking:

```bash
# Manually submit match result to Player Service
curl -X POST http://localhost:8002/matches \
  -H "Authorization: Bearer GAME_SERVICE_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "player1_external_id": "player1",
    "player2_external_id": "player2",
    "winner_external_id": "player1",
    "player1_score": 3,
    "player2_score": 2,
    "external_match_id": "MATCH_ID_HERE",
    "turns": []
  }'
```

### Step 8: View Statistics

```bash
# View player match history
curl http://localhost:8002/players/player1/matches

# Check global leaderboard (public endpoint)
curl http://localhost:8002/leaderboard
```

## Game Rules

**Card System:**
- 18 cards total: 6 Rock, 6 Paper, 6 Scissors
- Power levels vary by category:
  - Rock: 1, 2, 3, 4, 6, 9
  - Paper: 1, 2, 3, 5, 7, 9
  - Scissors: 1, 2, 4, 5, 7, 8

**Winning Logic:**
1. Rock beats Scissors
2. Scissors beats Paper
3. Paper beats Rock
4. If same category, higher power wins
5. If same category and power, draw

**Match Format:**
- Best of 5 rounds
- Each player gets 5 cards from the deck
- Players alternate playing cards until match ends

## Service Endpoints

### Auth Service (Port 8001)
```
POST /auth/register  - Register new user
POST /auth/login     - Get JWT token
GET  /auth/validate  - Validate token
GET  /health         - Health check
```

### Player Service (Port 8002)
```
POST /players                      - Create/update my profile (protected)
GET  /players/me                   - Get my profile (protected)
POST /matches                      - Create match record (internal, Game Service only)
GET  /players/{external_id}/matches - Get player match history (public)
GET  /players/{external_id}/matches/{match_id} - Get match details (public)
GET  /leaderboard                  - Get global rankings (public)
GET  /health                       - Health check
```

### Game Service (Port 8003)
```
POST /matches/                    - Start new match (protected)
POST /matches/{id}/move           - Submit a card move (protected)
GET  /matches/{id}?player_id=...  - Get match state (protected)
GET  /                            - Health check
```

## Development Commands

```bash
# View service logs
sudo docker-compose logs -f auth_service
sudo docker-compose logs -f player_service
sudo docker-compose logs -f game_service

# Stop all services
sudo docker-compose down

# Restart specific service
sudo docker-compose restart player_service

# Rebuild specific service
sudo docker-compose up -d --build game_service

# Remove all containers and volumes
sudo docker-compose down -v
```

## API Documentation

Interactive Swagger docs:
- Auth: http://localhost:8001/docs
- Player: http://localhost:8002/docs
- Game: http://localhost:8003/docs

## Testing

To run tests, you would need to install Python dependencies locally (not required for Docker deployment):

```bash
# Individual service tests (optional, requires local Python setup)
cd auth_service && pytest -v
cd player_service && pytest -v
cd game_service && pytest -v
```

---

Quick Links: [Docker Compose](docker-compose.yml) | [Auth Service](auth_service/) | [Player Service](player_service/) | [Game Service](game_service/)
