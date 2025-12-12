# Game Service - Production Integration Guide

> **Author**: Game Service Team  
> **Last Updated**: 2025-12-12  
> **Service Port**: `8003`  
> **Database**: PostgreSQL (sidecar container `game_postgres`)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Service Dependencies](#service-dependencies)
3. [Authentication Integration (Auth Service)](#authentication-integration-auth-service)
4. [Player Service Integration](#player-service-integration)
5. [API Gateway Integration](#api-gateway-integration)
6. [Network Configuration](#network-configuration)
7. [Environment Variables](#environment-variables)
8. [Database Configuration](#database-configuration)
9. [Health Checks](#health-checks)
10. [Error Handling](#error-handling)
11. [Testing Integration](#testing-integration)

---

## 🎮 Overview

**Game Service** is responsible for:
- ✅ Match creation and lifecycle management
- ✅ Game logic execution (Rock-Paper-Scissors card mechanics)
- ✅ Player hand management and move validation
- ✅ Round resolution and scoring
- ✅ SVG card visualization (deck gallery, card details, player hands)

**What we DON'T do:**
- ❌ User authentication (delegated to **Auth Service**)
- ❌ Player statistics/leaderboard (delegated to **Player Service**)
- ❌ Request routing (handled by **API Gateway**)

---

## 🔗 Service Dependencies

### Required Services

| Service | Purpose | Connection Type | Critical |
|---------|---------|-----------------|----------|
| **Auth Service** | Token verification | HTTP (async) | ✅ Yes |
| **Player Service** | Match finalization | HTTP (async) | ⚠️ Partial* |
| **game_postgres** | Match state storage | PostgreSQL | ✅ Yes |

\* Player Service connection failure won't block match gameplay, but statistics won't be updated.

---

## 🔐 Authentication Integration (Auth Service)

### What We Need From You (Auth Service Team)

#### 1. Token Validation Endpoint

**Endpoint**: `GET /auth/validate`  
**Query Parameter**: `token` (JWT string without "Bearer " prefix)

**Expected Response (200 OK)**:
```json
{
  "sub": "alice",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Error Responses**:
- `401 Unauthorized` - Invalid/expired token
- `500 Internal Server Error` - Auth service error

#### 2. Token Format

We expect tokens in the **Authorization header**:
```
Authorization: Bearer <jwt_token>
```

We extract the token and send it to your `/auth/validate` endpoint.

#### 3. User Identifier Field

**CRITICAL**: We use the `"sub"` field from your JWT payload as the **username/player_id**.

```json
{
  "sub": "alice"  ← This is the player identifier
}
```

**Requirements**:
- `sub` must be a string
- Must match the pattern: `^[a-zA-Z0-9_-]+$`
- Length: 1-100 characters
- Case-sensitive

### How We Use It

#### Our Implementation

**File**: `game_service/game_app/clients/auth_client.py`

```python
async def verify_token(token: str) -> dict:
    """
    Verify JWT token with Auth Service.
    
    Args:
        token: JWT token (without "Bearer " prefix)
    
    Returns:
        dict: {"sub": "username", "exp": ..., "iat": ...}
    
    Raises:
        HTTPException: 401 (invalid token) or 503 (service unavailable)
    """
    response = await client.get(
        f"{AUTH_SERVICE_URL}/auth/validate",
        params={"token": token}
    )
```

**Protected Route Example**:
```python
from game_app.clients.auth_client import get_current_user

@router.post("/matches")
async def create_match(
    data: CreateMatchRequest,
    user: dict = Depends(get_current_user)
):
    # user["sub"] contains the username
    player_id = user["sub"]
```

#### Retry Logic

We implement **3 retry attempts** with **exponential backoff** (2s, 4s, 8s):
- Timeout: 3 seconds per request
- Handles transient network failures gracefully

#### Security Validation

We enforce the following security checks:
1. **Authorization Ownership**: Users can ONLY create matches/submit moves as themselves
   - `player1_id` must equal `user["sub"]` in token
2. **Match Access Control**: Users can ONLY view their own match states

**Example Security Error**:
```json
{
  "detail": "You can only create matches as yourself (player1_id must match your username)"
}
```

### Service URL Configuration

**Docker Compose** (production):
```yaml
environment:
  AUTH_SERVICE_URL: "http://auth_service:8001"
```

**Standalone Development** (for your local testing):
```yaml
environment:
  AUTH_SERVICE_URL: "http://host.docker.internal:8001"
```

---

## 🎯 Player Service Integration

### What We Need From You (Player Service Team)

#### 1. Match Finalization Endpoint

**Endpoint**: `POST /matches`  
**Content-Type**: `application/json`

**Request Body**:
```json
{
  "player1_external_id": "alice",
  "player2_external_id": "bob",
  "winner_external_id": "alice",
  "player1_score": 3,
  "player2_score": 2,
  "rounds": [],
  "seed": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Field Specifications**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `player1_external_id` | string | ✅ Yes | Username of player 1 |
| `player2_external_id` | string | ✅ Yes | Username of player 2 |
| `winner_external_id` | string\|null | ✅ Yes | Winner username or `null` for draw |
| `player1_score` | integer | ✅ Yes | Final score (0-5) |
| `player2_score` | integer | ✅ Yes | Final score (0-5) |
| `rounds` | array | ✅ Yes | Empty array (temporary, will be removed) |
| `seed` | string | ✅ Yes | Match UUID |

**Expected Response (201 Created)**:
```json
{
  "id": 123,
  "message": "Match created successfully"
}
```

**Error Responses**:
- `400 Bad Request` - Invalid data
- `404 Not Found` - Player not found
- `422 Unprocessable Entity` - Validation error

#### 2. Why We Send "rounds": []

This is a **temporary field** that your team is planning to remove from the schema. We currently send an empty array to satisfy your current validation requirements.

**Please let us know when you remove this field** so we can update our schema.

### How We Use It

#### When We Call You

We send match results when a match reaches completion:
- ✅ One player reaches 3 points
- ✅ All 5 rounds are played (best of 5)

**File**: `game_service/game_app/clients/player_client.py`

```python
async def finalize_match(
    match_id: str,
    player1_id: str,
    player2_id: str,
    winner_id: Optional[str],
    points_p1: int,
    points_p2: int
) -> bool:
    """
    Notify Player Service about finished match.
    
    Returns:
        bool: True if successful, False if failed (non-critical)
    """
    response = await client.post(
        f"{PLAYER_SERVICE_URL}/matches",
        json=payload
    )
```

#### Error Handling

**Non-Critical Dependency**: If Player Service is unavailable or returns an error:
- ✅ Match completion proceeds normally
- ⚠️ We log the error for monitoring
- 🔄 We retry 3 times with exponential backoff
- ❌ After all retries fail, we log and continue

**This ensures gameplay isn't blocked by statistics issues.**

#### Retry Configuration

- **Timeout**: 5 seconds per request
- **Max Retries**: 3 attempts
- **Backoff**: 2s → 4s → 8s

### Service URL Configuration

**Docker Compose** (production):
```yaml
environment:
  PLAYER_SERVICE_URL: "http://player_service:8002"
```

**Standalone Development**:
```yaml
environment:
  PLAYER_SERVICE_URL: "http://host.docker.internal:8002"
```

---

## 🌐 API Gateway Integration

### Endpoint Prefix

All Game Service endpoints should be prefixed with `/game` in the API Gateway:

| Internal Endpoint | Gateway Endpoint |
|-------------------|------------------|
| `GET /health` | `GET /game/health` |
| `POST /matches` | `POST /game/matches` |
| `POST /matches/{id}/move` | `POST /game/matches/{id}/move` |
| `GET /matches/{id}` | `GET /game/matches/{id}` |
| `GET /cards` | `GET /game/cards` |
| `GET /cards/{id}` | `GET /game/cards/{id}` |
| `GET /matches/{id}/hand` | `GET /game/matches/{id}/hand` |

### Protected vs Public Endpoints

#### 🔒 Protected Endpoints (Require JWT)

**API Gateway must forward Authorization header:**

```
Authorization: Bearer <jwt_token>
```

**Endpoints**:
- `POST /game/matches` - Create match
- `POST /game/matches/{match_id}/move` - Submit move
- `GET /game/matches/{match_id}` - Get match state
- `GET /game/matches/{match_id}/hand` - Get player hand SVG

#### 🌍 Public Endpoints (No Authentication)

**Endpoints**:
- `GET /game/health` - Health check
- `GET /game/cards` - Deck gallery SVG
- `GET /game/cards/{card_id}` - Card detail SVG

### CORS Configuration

If API Gateway handles CORS, please allow:
- **Methods**: `GET`, `POST`, `OPTIONS`
- **Headers**: `Authorization`, `Content-Type`
- **Origins**: Frontend domain (TBD by team)

### Request Forwarding

**Important**: API Gateway should forward the **original client IP** for logging:
```
X-Forwarded-For: <client_ip>
X-Real-IP: <client_ip>
```

---

## 🔌 Network Configuration

### Docker Networks

Game Service connects to **2 networks**:

#### 1. triduel_network (Main Network)
- **Purpose**: Inter-service communication
- **Connected Services**: auth_service, player_service, game_service
- **Type**: Bridge network

#### 2. game_internal (Isolated Network)
- **Purpose**: Game Service ↔ PostgreSQL only
- **Connected Services**: game_service, game_postgres
- **Type**: Internal bridge (no external access)

**Why 2 networks?**
- Security: Database is isolated from other services
- Performance: Direct container-to-container communication
- Kubernetes-ready: Simulates sidecar pod architecture

### Service Discovery

Services communicate using **Docker DNS**:
- `http://auth_service:8001`
- `http://player_service:8002`
- `postgresql://game_postgres:5432`

**No IP addresses are hardcoded.**

---

## ⚙️ Environment Variables

### Required Variables

```bash
# Service URLs
AUTH_SERVICE_URL=http://auth_service:8001
PLAYER_SERVICE_URL=http://player_service:8002

# Database Connection
DATABASE_URL=postgresql+psycopg2://${GAME_DB_USER}:${GAME_DB_PASSWORD}@game_postgres:5432/${GAME_DB_NAME}

# PostgreSQL Credentials (from .env file)
GAME_DB_USER=game_user
GAME_DB_PASSWORD=game_secret
GAME_DB_NAME=game_db
```

### Optional Variables

```bash
# Timeouts (seconds)
AUTH_TIMEOUT=3
PLAYER_TIMEOUT=5

# Retry Configuration
MAX_RETRY_ATTEMPTS=3
RETRY_BACKOFF_BASE=2

# Database Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
DB_ECHO=false
```

### .env File Example

Create a `.env` file in the project root:

```env
# PostgreSQL for Game Service
GAME_DB_USER=game_user
GAME_DB_PASSWORD=change_me_in_production
GAME_DB_NAME=game_db

# Auth Service (if needed)
AUTH_SECRET_KEY=your-super-secret-key
TOKEN_EXPIRE_MINUTES=60
```

---

## 🗄️ Database Configuration

### PostgreSQL Sidecar

Game Service uses a **dedicated PostgreSQL instance** (not shared):

**Container Name**: `game_postgres`  
**Image**: `postgres:15-alpine`  
**Port**: `5432` (internal only, not exposed to host)

#### Why PostgreSQL?

1. **Concurrency**: Multiple players submitting moves simultaneously
2. **ACID Transactions**: Critical for game state consistency
3. **Performance**: Connection pooling for high throughput
4. **Scalability**: Ready for horizontal scaling

#### Database Schema

**Tables**:
- `card_definitions` - Card templates (Rock/Paper/Scissors types)
- `matches` - Match metadata and state
- `match_cards` - Player hands (cards dealt per match)
- `moves` - Individual card plays per round

**Relationships**:
```
matches 1 ──< ∞ match_cards (player hands)
matches 1 ──< ∞ moves (round history)
card_definitions 1 ──< ∞ match_cards
```

#### Connection String Format

```
postgresql+psycopg2://username:password@host:port/database
```

**Production Example**:
```
postgresql+psycopg2://game_user:game_secret@game_postgres:5432/game_db
```

#### Health Check

PostgreSQL health is monitored:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U $GAME_DB_USER -d $GAME_DB_NAME"]
  interval: 5s
  timeout: 5s
  retries: 5
```

Game Service waits for database health before starting:
```yaml
depends_on:
  game_postgres:
    condition: service_healthy
```

---

## 🏥 Health Checks

### Game Service Health Endpoint

**Endpoint**: `GET /health` or `GET /`  
**Response (200 OK)**:
```json
{
  "status": "ok"
}
```

### Docker Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
  interval: 10s
  timeout: 5s
  retries: 3
```

### Dependency Health

Game Service health depends on:
- ✅ PostgreSQL (`game_postgres`) - **Critical**
- ⚠️ Auth Service - **Needed for protected endpoints**
- ⚠️ Player Service - **Non-critical** (statistics only)

**Startup Order**:
1. `game_postgres` → healthy
2. `auth_service` → healthy
3. `player_service` → healthy
4. `game_service` → starts

---

## ⚠️ Error Handling

### Error Response Format

All Game Service errors follow FastAPI standard format:

```json
{
  "detail": "Error message here"
}
```

### Status Codes We Return

| Code | Meaning | Example |
|------|---------|---------|
| `200` | Success | Move accepted |
| `201` | Created | (Not used by Game Service) |
| `400` | Bad Request | Invalid card ID, match already finished |
| `401` | Unauthorized | Missing/invalid token |
| `403` | Forbidden | Trying to play as another user |
| `404` | Not Found | Match not found, card not found |
| `422` | Validation Error | Invalid request body schema |
| `503` | Service Unavailable | Auth Service down |

### Critical vs Non-Critical Errors

#### Critical (Block Request)
- ❌ Auth Service unavailable → `503 Service Unavailable`
- ❌ Database connection failed → `500 Internal Server Error`
- ❌ Invalid token → `401 Unauthorized`

#### Non-Critical (Log & Continue)
- ⚠️ Player Service unavailable → Match completes, statistics not updated
- ⚠️ Match finalization failed → Logged, retried, gameplay continues

---

## 🧪 Testing Integration

### Local Testing Setup

#### 1. Start All Services

```bash
# From project root
docker-compose up -d
```

#### 2. Wait for Health Checks

```bash
# Check all services are healthy
docker ps

# Should show:
# - auth_service (healthy)
# - player_service (healthy)
# - game_service (healthy)
# - game_postgres (healthy)
```

#### 3. Get JWT Token (from Auth Service)

```bash
# Register user
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@test.com","password":"test123"}'

# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"test123"}'

# Response:
# {"access_token":"eyJ...","token_type":"bearer"}
```

#### 4. Test Game Service

```bash
# Set token
TOKEN="eyJ..."

# Create match
curl -X POST http://localhost:8003/matches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"player1_id":"alice","player2_id":"bob"}'

# Response includes match_id and player hand
```

### Integration Test Checklist

**For Auth Service Team:**
- [ ] `/auth/validate` returns 200 with `{"sub": "username"}`
- [ ] Invalid tokens return 401
- [ ] Token expiration is handled correctly
- [ ] Service is accessible at `http://auth_service:8001` from Docker network

**For Player Service Team:**
- [ ] `POST /matches` accepts our payload format
- [ ] Returns 201 on success
- [ ] Handles duplicate match submissions gracefully
- [ ] Service is accessible at `http://player_service:8002` from Docker network

**For API Gateway Team:**
- [ ] `/game/*` prefix routing works
- [ ] Authorization header is forwarded to Game Service
- [ ] CORS headers are set correctly
- [ ] Health checks pass through

### Testing Without Other Services

You can test Game Service in isolation:

```yaml
# game_service/docker-compose.yml (standalone mode)
services:
  game-service:
    environment:
      AUTH_SERVICE_URL: "http://host.docker.internal:8001"
      PLAYER_SERVICE_URL: "http://host.docker.internal:8002"
```

This allows you to run Game Service while Auth/Player services run outside Docker.

---

## 📊 Logging & Monitoring

### Log Format

We use structured logging:

```
2025-12-12 10:30:45 INFO [game_app.services.match_service] ✅ Match created: id=abc123
2025-12-12 10:30:50 WARNING [game_app.clients.player_client] ⚠️ Player Service timeout (attempt 1/3)
2025-12-12 10:31:00 ERROR [game_app.clients.auth_client] ❌ Auth service returned 401
```

### Key Log Events

**Match Lifecycle**:
- `Match created: id={match_id}`
- `Round {n} completed: winner={player_id}`
- `Match finished: winner={player_id}`

**Security Events**:
- `UNAUTHORIZED_ATTEMPT | action=create_match | user={user} | attempted_as={other_user}`

**Integration Events**:
- `Token verified successfully`
- `Match finalized successfully`
- `Player Service timeout (attempt X/3)`

### Monitoring Endpoints

For production monitoring tools:
- **Health**: `GET /health`
- **Metrics**: (Not implemented yet - can add Prometheus if needed)

---

## 🔧 Common Issues & Solutions

### Issue: "Auth service unavailable" (503)

**Possible Causes**:
1. Auth Service not started
2. Wrong `AUTH_SERVICE_URL`
3. Network connectivity issue

**Solutions**:
```bash
# Check Auth Service is running
docker ps | grep auth

# Check logs
docker logs triduel_auth

# Verify network
docker network inspect triduel_network
```

### Issue: "Match finalization failed" (logged warning)

**Impact**: Non-critical, gameplay continues

**Possible Causes**:
1. Player Service down
2. Player not found in Player Service database
3. Invalid payload format

**Solutions**:
- Check Player Service logs: `docker logs triduel_player`
- Verify players exist in Player Service
- Check payload matches Player Service schema

### Issue: "Token verification timeout"

**Solutions**:
1. Increase `AUTH_TIMEOUT` environment variable
2. Check Auth Service response time
3. Verify network latency between containers

### Issue: Database connection failed

**Solutions**:
```bash
# Check PostgreSQL is running
docker ps | grep game_postgres

# Check connection
docker exec -it game_postgres psql -U game_user -d game_db

# Verify credentials in .env
cat .env | grep GAME_DB
```

---

## 📞 Contact & Support

**Game Service Team**:
- Repository: `game_service/`
- Configuration: `game_service/game_app/configs/`
- Documentation: `game_service/README_prod.md` (this file)

**Integration Questions**:
- Auth integration: `game_service/game_app/clients/auth_client.py`
- Player integration: `game_service/game_app/clients/player_client.py`
- API contracts: `openapi.yaml`

**Quick Reference Files**:
- Main application: `game_service/game_app/main.py`
- API routes: `game_service/game_app/api/router.py`
- Client configs: `game_service/game_app/configs/client_config.py`
- Database models: `game_service/game_app/database/models.py`

---

## 📚 Additional Resources

- **OpenAPI Spec**: `openapi.yaml` (project root)
- **Docker Compose**: `docker-compose.yml` (project root)
- **Game Logic**: `game_service/game_app/logic/`
- **Database Schema**: `game_service/game_app/database/models.py`

---

## ✅ Integration Checklist

### For Auth Service Team
- [ ] Implement `GET /auth/validate?token={jwt}` endpoint
- [ ] Return `{"sub": "username"}` in response
- [ ] Handle invalid tokens with 401 status
- [ ] Deploy on `http://auth_service:8001` in Docker network
- [ ] Add health check endpoint: `GET /health`

### For Player Service Team
- [ ] Implement `POST /matches` endpoint (if not already done)
- [ ] Accept payload with `player1_external_id`, `player2_external_id`, etc.
- [ ] Return 201 on success
- [ ] (Optional) Remove `rounds` field requirement
- [ ] Deploy on `http://player_service:8002` in Docker network
- [ ] Add health check endpoint: `GET /health`

### For API Gateway Team
- [ ] Route `/game/*` to `http://game_service:8003`
- [ ] Forward `Authorization` header to Game Service
- [ ] Set CORS headers for frontend
- [ ] Forward client IP in `X-Forwarded-For` header
- [ ] Configure health check monitoring

### For Game Service Team (Us)
- [x] Implement Auth Service client with retry logic
- [x] Implement Player Service client with graceful degradation
- [x] Configure Docker networking (dual network setup)
- [x] Set up PostgreSQL sidecar with health checks
- [x] Document all integration points
- [x] Create comprehensive README_prod.md

---

**Last Updated**: 2025-12-12  
**Document Version**: 1.0  
**Game Service Version**: 1.0.0

---

## 🚀 Quick Start Commands

### Warning!
**Before starting - copy .env.example to .env**

```bash
# Start entire stack
docker-compose up -d

# View logs
docker-compose logs -f game_service

# Stop all services
docker-compose down

# Rebuild Game Service
docker-compose up -d --build game_service

# Check health
curl http://localhost:8003/health
```

---

**Questions?** Review this document first, then check the OpenAPI specification (`openapi.yaml`), then reach out to the Game Service team.

