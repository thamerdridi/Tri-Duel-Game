#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERBOSE="${VERBOSE:-1}"
HTTP_LOG_BODY="${HTTP_LOG_BODY:-0}"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required (sudo apt-get install -y jq)" >&2
  exit 1
fi

if [ ! -f .env ]; then
  echo "Missing .env in repo root. Create it from .env.example and set SERVICE_API_KEY." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source ./.env
set +a

if [ -z "${SERVICE_API_KEY:-}" ]; then
  if command -v openssl >/dev/null 2>&1; then
    SERVICE_API_KEY="$(openssl rand -hex 16)"
  else
    SERVICE_API_KEY="$(date +%s | sha256sum | awk '{print $1}' | head -c 32)"
  fi
  export SERVICE_API_KEY
  echo "SERVICE_API_KEY is not set in .env; using a generated one for this run:" >&2
  echo "SERVICE_API_KEY=${SERVICE_API_KEY}" >&2
fi

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"

if ! ${COMPOSE_CMD} version >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1 && sudo docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="sudo docker compose"
  else
    echo "docker compose is required (Compose v2)." >&2
    exit 1
  fi
fi

if ! docker ps >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1 && sudo docker ps >/dev/null 2>&1; then
    COMPOSE_CMD="sudo docker compose"
  else
    echo "Cannot access Docker daemon (permission denied). Run this script with sudo or add your user to the docker group." >&2
    exit 1
  fi
fi

wait_for() {
  local url="$1"
  local retries="${2:-60}"
  local sleep_s="${3:-1}"
  local i=0
  until curl -fsS "$url" >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge "$retries" ]; then
      echo "Timed out waiting for $url" >&2
      return 1
    fi
    sleep "$sleep_s"
  done
}

log() {
  echo "[$(date +'%H:%M:%S')] $*" >&2
}

pretty_json() {
  local input
  input="$(cat)"
  if echo "$input" | jq -e . >/dev/null 2>&1; then
    echo "$input" | jq .
  else
    printf '%s\n' "$input"
  fi
}

http() {
  # Usage: http METHOD URL [curl args...]
  local method="$1"
  local url="$2"
  shift 2

  local resp
  resp="$(
    curl -sS -X "$method" "$url" \
      -w $'\n__HTTP_CODE__:%{http_code}' \
      "$@"
  )"

  local code="${resp##*__HTTP_CODE__:}"
  local body="${resp%$'\n'__HTTP_CODE__:*}"

  if [ "$VERBOSE" != "0" ]; then
    log "$method $url -> $code"
    if [ "$HTTP_LOG_BODY" != "0" ] && [ -n "$body" ]; then
      echo "$body" | pretty_json >&2
    fi
  fi

  if [ "$code" -ge 400 ]; then
    echo "$body" >&2
    return 1
  fi

  printf '%s' "$body"
}

AUTH_BASE="${AUTH_BASE:-http://localhost:8001}"
PLAYER_BASE="${PLAYER_BASE:-http://localhost:8002}"
GAME_BASE="${GAME_BASE:-http://localhost:8003}"

ALICE_USER="${ALICE_USER:-alice}"
BOB_USER="${BOB_USER:-bob}"
PASSWORD="${PASSWORD:-Password123}"

log "AUTH_BASE=$AUTH_BASE PLAYER_BASE=$PLAYER_BASE GAME_BASE=$GAME_BASE"

echo "Starting containers..."
${COMPOSE_CMD} up -d --build

echo "Waiting for services..."
wait_for "${AUTH_BASE}/health"
wait_for "${PLAYER_BASE}/health"
wait_for "${GAME_BASE}/health"

register_user() {
  local username="$1"
  local email="$2"
  local password="$3"
  curl -sS -X POST "${AUTH_BASE}/auth/register" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${username}\",\"email\":\"${email}\",\"password\":\"${password}\"}" >/dev/null || true
}

login_user() {
  local username="$1"
  local password="$2"
  http POST "${AUTH_BASE}/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${username}\",\"password\":\"${password}\"}" | jq -r .access_token
}

echo "Registering users (idempotent)..."
register_user "$ALICE_USER" "${ALICE_USER}@example.com" "$PASSWORD"
register_user "$BOB_USER" "${BOB_USER}@example.com" "$PASSWORD"

echo "Logging in..."
ALICE_TOKEN="$(login_user "$ALICE_USER" "$PASSWORD")"
BOB_TOKEN="$(login_user "$BOB_USER" "$PASSWORD")"
log "alice_token_len=${#ALICE_TOKEN} bob_token_len=${#BOB_TOKEN}"

if [ -z "$ALICE_TOKEN" ] || [ "$ALICE_TOKEN" = "null" ]; then
  echo "Failed to login alice" >&2
  exit 1
fi
if [ -z "$BOB_TOKEN" ] || [ "$BOB_TOKEN" = "null" ]; then
  echo "Failed to login bob" >&2
  exit 1
fi

echo "Creating Player Service profiles (JWT-protected)..."
http POST "${PLAYER_BASE}/players" \
  -H "Authorization: Bearer ${ALICE_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"${ALICE_USER}\"}" >/dev/null || true

http POST "${PLAYER_BASE}/players" \
  -H "Authorization: Bearer ${BOB_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"${BOB_USER}\"}" >/dev/null || true

echo "Starting match in Game Service..."
MATCH_CREATE="$(http POST "${GAME_BASE}/matches" \
  -H "Authorization: Bearer ${ALICE_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"player1_id\":\"${ALICE_USER}\",\"player2_id\":\"${BOB_USER}\"}")"

MATCH_ID="$(echo "$MATCH_CREATE" | jq -r .match_id)"
if [ -z "$MATCH_ID" ] || [ "$MATCH_ID" = "null" ]; then
  echo "Failed to create match: $MATCH_CREATE" >&2
  exit 1
fi
echo "match_id=$MATCH_ID"

echo "Playing match (always choosing card_index=0)..."
for _round in $(seq 1 10); do
  RES_ALICE="$(VERBOSE=0 http POST "${GAME_BASE}/matches/${MATCH_ID}/move" \
    -H "Authorization: Bearer ${ALICE_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "{\"player_id\":\"${ALICE_USER}\",\"card_index\":0}")"
  if [ "$VERBOSE" != "0" ]; then
    echo "$RES_ALICE" | pretty_json
  fi

  RES="$(VERBOSE=0 http POST "${GAME_BASE}/matches/${MATCH_ID}/move" \
    -H "Authorization: Bearer ${BOB_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "{\"player_id\":\"${BOB_USER}\",\"card_index\":0}")"

  FINISHED="$(echo "$RES" | jq -r '.match_finished // false')"
  if [ "$FINISHED" = "true" ]; then
    log "match_finished=true"
    echo "$RES" | pretty_json
    break
  fi
done

echo "Fetching final match state..."
STATE="$(VERBOSE=0 http GET "${GAME_BASE}/matches/${MATCH_ID}" \
  -G \
  -H "Authorization: Bearer ${ALICE_TOKEN}" \
  --data-urlencode "player_id=${ALICE_USER}")"

P1_SCORE="$(echo "$STATE" | jq -r .points_p1)"
P2_SCORE="$(echo "$STATE" | jq -r .points_p2)"
WINNER="$(echo "$STATE" | jq -r '.match_winner // empty')"
log "final_score=${P1_SCORE}-${P2_SCORE} winner=${WINNER:-DRAW}"
if [ "$VERBOSE" != "0" ]; then
  echo "$STATE" | pretty_json
fi

log "building turns[]..."
TURNS_JSON="$(echo "$STATE" | jq -c --arg p1 "$ALICE_USER" --arg p2 "$BOB_USER" '
  def cap(s): (s[0:1] | ascii_upcase) + (s[1:]);
  def cname(c): cap(c.category) + " " + (c.power|tostring);
  ([ (.used_cards // [])[] | {r: .round_used, name: cname(.card)} ] as $p1c
   | [ (.opponent_used_cards // [])[] | {r: .round_used, name: cname(.card)} ] as $p2c
   | [ range(1; ((($p1c|map(.r)|max)//0) + 1)) as $r
       | {
           turn_number: $r,
           player1_card_name: (first($p1c[] | select(.r==$r) | .name) // ""),
           player2_card_name: (first($p2c[] | select(.r==$r) | .name) // "")
         }
     ])
')"

TURNS_COUNT="$(echo "$TURNS_JSON" | jq -r 'length')"
log "turns_count=${TURNS_COUNT}"

echo "Ensuring profiles exist via internal sync (API-key protected)..."
http POST "${PLAYER_BASE}/internal/players" \
  -H "X-Internal-Api-Key: ${SERVICE_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d "{\"external_id\":\"${ALICE_USER}\",\"username\":\"${ALICE_USER}\"}" >/dev/null

http POST "${PLAYER_BASE}/internal/players" \
  -H "X-Internal-Api-Key: ${SERVICE_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d "{\"external_id\":\"${BOB_USER}\",\"username\":\"${BOB_USER}\"}" >/dev/null

echo "Posting match history to Player Service (API key)..."
MATCH_PAYLOAD="$(jq -n \
  --arg p1 "$ALICE_USER" \
  --arg p2 "$BOB_USER" \
  --arg winner "$WINNER" \
  --arg ext "$MATCH_ID" \
  --argjson p1s "$P1_SCORE" \
  --argjson p2s "$P2_SCORE" \
  --argjson turns "$TURNS_JSON" \
  '{
    player1_external_id: $p1,
    player2_external_id: $p2,
    winner_external_id: (if $winner == "" then null else $winner end),
    player1_score: $p1s,
    player2_score: $p2s,
    external_match_id: $ext,
    turns: $turns
  }'
)"

log "posting match payload:"
echo "$MATCH_PAYLOAD" | pretty_json

http POST "${PLAYER_BASE}/matches" \
  -H "X-Internal-Api-Key: ${SERVICE_API_KEY}" \
  -H 'Content-Type: application/json' \
  -d "$MATCH_PAYLOAD" | tee /tmp/player_match_post.json | pretty_json

POSTED_MATCH_ID="$(cat /tmp/player_match_post.json | jq -r '.id // empty' 2>/dev/null || true)"
if [ -n "$POSTED_MATCH_ID" ]; then
  echo "Match detail (includes turns/rounds):"
  MATCH_DETAIL="$(http GET "${PLAYER_BASE}/players/${ALICE_USER}/matches/${POSTED_MATCH_ID}")"
  echo "$MATCH_DETAIL" | pretty_json
  echo "Rounds (turns[]):"
  echo "$MATCH_DETAIL" | jq -r '
    .turns
    | if (type != "array") then "no turns" else . end
    | .[]
    | "turn \(.turn_number): p1=\(.player1_card_name) p2=\(.player2_card_name) winner=\(.winner_external_id // "-")"'
fi

echo "Player history:"
http GET "${PLAYER_BASE}/players/${ALICE_USER}/matches" | pretty_json

echo "Leaderboard:"
http GET "${PLAYER_BASE}/leaderboard" | pretty_json

echo "Done."
