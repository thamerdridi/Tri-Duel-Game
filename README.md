# Tri-Duel Game - Microservices Architecture

A rock-paper-scissors card game with three microservices: Auth, Player, and Game.

Authors: Michal Sachanbinski, Othman Alhammali Shoaib Alhadiri, Thamer DRIDI - (Group 5).

## Setup

Before running the application, prepare the environment:

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Generate SSL certificates for secure communication (make sure to run it in bash (ex git bash) - may not work in powershell - if in doubt run it in powershell 6 or 7 times so it can generate all the certificates) :
   ```bash
   ./certs/generate-certs.sh
   ```

This sets up the necessary certificates for HTTPS communication between services and the API Gateway.

## Instructions

To run and test the complete application:

1. Ensure Docker and Docker Compose are installed
2. Run: `sudo docker-compose up -d --build`
3. Wait 30 seconds
4. Follow the instructions below to test the services

All services, databases, and dependencies are containerized.

## Architecture

```
API Gateway (8443) → Auth Service (8001)
                   → Player Service (8002)
                   → Game Service (8003)
```

- **API Gateway**: Routes requests to appropriate services, handles HTTPS
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
curl http://localhost:8003/health  # Game Service - Should return {"status":"ok"}
```

## Playing a Complete Match

### For running this with Postman - just copy the steps with injecting the tokens where needed.

### Step 1: Register Two Players

```bash
# Register player 1
curl -X POST https://localhost:8443/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "email": "player1@test.com", "password": "Password123!"}'

# Register player 2
curl -X POST https://localhost:8443/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "player2", "email": "player2@test.com", "password": "Password123!"}'
```

### Step 2: Login as Player 1 (Get JWT Token)

```bash
curl -X POST https://localhost:8443/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "Password123!"}'
```

### Step 2.2: Login as Player 2 (Get JWT Token)

```bash
curl -X POST https://localhost:8443/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "player2", "password": "Password123!"}'
```

Copy the `access_token` from the response.


### Step 3: View Available Cards

```bash
curl https://localhost:8443/game/cards
```

This endpoint returns an SVG. Open it in a browser for the full deck view, and use `/cards/{id}` for single-card view.

### Step 4: Start a Match

```bash
curl -X POST https://localhost:8443/game/matches/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player1_id": "player1",
    "player2_id": "player2"
  }'
```

Save the `match_id` from the response. Also note the `hand` cards returned - each has a `match_card_id`.

### Step 5: Play Rounds (Best of 5)

Players take turns playing cards. Use the `card_index` from your hand (not the card `id`).

```bash
# Player 1 plays a card
curl -X POST https://localhost:8443/game/matches/MATCH_ID_HERE/move \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "player1",
    "card_index": 0
  }'

# Player 2 plays a card (round completes and shows result)
curl -X POST https://localhost:8443/matches/MATCH_ID_HERE/move \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "player2",
    "card_index": 1
  }'

# Continue alternating until match ends (5 rounds) or surrender using the following command:
curl -X POST https://localhost:8443/game/matches/MATCH_ID_HERE/surrender \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" 
```

### Step 6: View Match Results

This is done to see the match state during or after the match:

```bash
# Get match state from Game Service
curl "https://localhost:8443/game/matches/MATCH_ID_HERE?player_id=player1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Step 7: View statistics in Player Service

After a match completes, it records it in the Player Service for leaderboard tracking:


```bash
# View player match history
curl https://localhost:8443/players/player1/matches

# Check global leaderboard (public endpoint)
curl https://localhost:8443/leaderboard
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

## Service Endpoints (see full list in Openapi file)

### Auth Service (Port 8001)
```
POST /auth/register  - Register new user
POST /auth/login     - Get JWT token
GET  /auth/validate  - Validate token
```

### Player Service (Port 8002)
```
POST /player/players                      - Create/update my profile (protected)
GET  /player/players/me                   - Get my profile (protected)
POST /player/matches                      - Create match record (internal, Game Service only)
GET  /player/players/{external_id}/matches - Get player match history (public)
GET  /player/players/{external_id}/matches/{match_id} - Get match details (public)
GET  /player/leaderboard                  - Get global rankings (public)
GET  /player/health                       - Health check
```

### Game Service (Port 8003)
```
POST /game/matches/                   - Start new match (protected)
GET  /game/matches/{id}                - Get match state (protected)
POST /game/matches/{id}/move           - Submit a card move (protected)
GET  /game/matches/active              - Get active matches for user (protected)
POST /game/matches/{id}/surrender      - Surrender match (protected)
GET  /game/cards                       - Get deck gallery (SVG, public)
GET  /game/cards/{id}                  - Get card detail (SVG, public)
GET  /game/matches/{id}/hand           - Get player's hand (SVG, protected)
GET  /game/health                      - Health check
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
- Auth: https://localhost:8443/docs

## Testing

All tests are in /docs folder as Postman collections for each service.

Additionally we have also pytest unit/integration tests inside each service folder under `tests/`.

To run tests, you would need to install Python dependencies locally (not required for Docker deployment):

```bash
# Individual service tests (optional, requires local Python setup)
cd auth_service && pytest -v
cd player_service && pytest -v
cd game_service && pytest -v
```

## TLS / HTTPS note

Important: Development docker-compose runs services over HTTP on ports 8001/8002/8003 for convenience and faster iteration. The repository includes certificates under `certs/` and a production-ready Dockerfile/compose (`game_service/docker-compose-prod.yml` and `game_service/Dockerfile`) that can run the Game Service with TLS. For full end-to-end HTTPS between services, update the `*_SERVICE_URL` environment variables to `https://...:8443` and enable TLS in the service commands (uvicorn or a reverse proxy). See `docs/openapi.yaml` and `docs/ci-workflow.yml` for API spec and CI workflow copies.

## Project status checklist (quick)

- README with run & test instructions: Yes (see this file)
- Microservice architecture (Auth, Player, Game): Yes
- `docker compose up --build` expected to start services (dev mode uses HTTP): Partially — runs but services are exposed on ports 8001/8002/8003 without TLS in dev compose
- Postman collections: present in `player_service/postman/` and `game_service/game_app/tests/postman/`
- OpenAPI for gateway: `docs/openapi.yaml` (copy added)
- GitHub Actions workflow copy: `docs/ci-workflow.yml` (copy added)

---

Quick Links: [Docker Compose](docker-compose.yml) | [Auth Service](auth_service/) | [Player Service](player_service/) | [Game Service](game_service/)
