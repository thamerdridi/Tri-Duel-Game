# Tri-Duel Game - Microservices Architecture

A rock-paper-scissors card game with three microservices: Auth, Player, and Game.

## For Evaluators

**IMPORTANT: This application runs 100% in Docker. No dependencies need to be installed on your machine.**

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
- **Player**: Profiles, cards, match history, leaderboard  
- **Game**: Match logic, RPS engine, rounds

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

### Step 3: View Available Cards

```bash
curl http://localhost:8002/cards
```

Note card IDs (1-18). Cards have categories (Rock/Paper/Scissors) and power (10-60).

### Step 4: Start a Match

```bash
curl -X POST http://localhost:8003/match/start \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player1_id": "player1",
    "player2_id": "player2"
  }'
```

Save the `match_id` from the response.

### Step 5: Play Rounds (Best of 5)

```bash
# Round 1
curl -X POST http://localhost:8003/match/round \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": "MATCH_ID_HERE",
    "player1_card_id": 1,
    "player2_card_id": 7
  }'

# Round 2
curl -X POST http://localhost:8003/match/round \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": "MATCH_ID_HERE",
    "player1_card_id": 3,
    "player2_card_id": 15
  }'

# Continue for rounds 3, 4, 5...
```

### Step 6: View Match Results

```bash
# Get match details
curl http://localhost:8003/match/MATCH_ID_HERE \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# View player1's match history
curl http://localhost:8002/players/player1/matches \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Check leaderboard
curl http://localhost:8002/leaderboard
```

## Game Rules

**Card System:**
- 18 cards total: 6 Rock, 6 Paper, 6 Scissors
- Each category has power levels: 10, 20, 30, 40, 50, 60

**Winning Logic:**
1. Rock beats Scissors
2. Scissors beats Paper
3. Paper beats Rock
4. If same category, higher power wins
5. If same category and power, draw

**Match Format:**
- Best of 5 rounds
- First to 3 wins takes the match

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
GET  /cards                        - List all cards (public)
GET  /cards/{id}                   - Get card details (public)
POST /matches                      - Create match record (internal)
GET  /players/{id}/matches         - Get player match history (protected)
GET  /players/{id}/matches/{m_id}  - Get match details (protected)
GET  /leaderboard                  - Get global rankings (public)
GET  /health                       - Health check
```

### Game Service (Port 8003)
```
POST /match/start      - Start new match (protected)
POST /match/round      - Play a round (protected)
GET  /match/{id}       - Get match state (protected)
GET  /                 - Health check
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

```bash
# Run integration tests
make test

# Individual service tests
cd auth_service && pytest -v
cd player_service && pytest -v
cd game_service && pytest -v
```

---

Quick Links: [Docker Compose](docker-compose.yml) | [Makefile](Makefile) | [Auth Service](auth_service/) | [Player Service](player_service/) | [Game Service](game_service/)
