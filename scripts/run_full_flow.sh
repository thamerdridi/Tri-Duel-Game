#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERBOSE="${VERBOSE:-1}"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required (sudo apt-get install -y jq)" >&2
  exit 1
fi

if [ ! -f .env ]; then
  echo "Missing .env in repo root. Create it from .env.example and set PLAYER_SERVICE_API_KEY." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source ./.env
set +a

if [ -z "${PLAYER_SERVICE_API_KEY:-}" ]; then
  if command -v openssl >/dev/null 2>&1; then
    PLAYER_SERVICE_API_KEY="$(openssl rand -hex 16)"
  else
    PLAYER_SERVICE_API_KEY="$(date +%s | sha256sum | awk '{print $1}' | head -c 32)"
  fi
  export PLAYER_SERVICE_API_KEY
  echo "PLAYER_SERVICE_API_KEY is not set in .env; using a generated one for this run:" >&2
  echo "PLAYER_SERVICE_API_KEY=${PLAYER_SERVICE_API_KEY}" >&2
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

CA_CERT_PATH_DEFAULT="${ROOT_DIR}/certs/ca/ca.crt"
CURL_CA_CERT="${CURL_CA_CERT:-$CA_CERT_PATH_DEFAULT}"
CURL_INSECURE="${CURL_INSECURE:-0}"

declare -a CURL_TLS_ARGS=()
if [ "$CURL_INSECURE" = "1" ]; then
  CURL_TLS_ARGS=(-k)
else
  if [ ! -f "$CURL_CA_CERT" ]; then
    echo "CA cert not found at $CURL_CA_CERT (set CURL_CA_CERT=... or CURL_INSECURE=1)" >&2
    exit 1
  fi
  CURL_TLS_ARGS=(--cacert "$CURL_CA_CERT")
fi

dump_service_logs() {
  local tail="${1:-120}"
  echo "---- docker compose ps ----" >&2
  ${COMPOSE_CMD} ps >&2 || true
  echo "---- docker compose logs (tail=${tail}) ----" >&2
  ${COMPOSE_CMD} logs --no-color --tail="$tail" gateway auth_service player_service game_service >&2 || true
}

wait_for() {
  local url="$1"
  local retries="${2:-60}"
  local sleep_s="${3:-1}"
  local i=0
  until curl "${CURL_TLS_ARGS[@]}" -fsS "$url" >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge "$retries" ]; then
      echo "Timed out waiting for $url" >&2
      return 1
    fi
    sleep "$sleep_s"
  done
}

wait_for_auth_login() {
  local url="$1"
  local retries="${2:-60}"
  local sleep_s="${3:-1}"
  local i=0
  local code=""

  until :; do
    code="$(
      curl "${CURL_TLS_ARGS[@]}" -sS -o /dev/null -w '%{http_code}' \
        -X POST "$url" \
        -H 'Content-Type: application/json' \
        -d '{"username":"__probe__","password":"__probe__"}' \
        2>/dev/null || true
    )"
    case "$code" in
      200|400|401|403|405|422) return 0 ;;
    esac
    i=$((i + 1))
    if [ "$i" -ge "$retries" ]; then
      echo "Timed out waiting for auth endpoint $url (last http_code=$code)" >&2
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
    curl "${CURL_TLS_ARGS[@]}" -sS -X "$method" "$url" \
      -w $'\n__HTTP_CODE__:%{http_code}' \
      "$@"
  )"

  local code="${resp##*__HTTP_CODE__:}"
  local body="${resp%$'\n'__HTTP_CODE__:*}"

  HTTP_LAST_CODE="$code"

  if [ "$VERBOSE" != "0" ]; then
    log "$method $url -> $code"
    if [ -n "$body" ]; then
      echo "$body" | pretty_json >&2
    fi
  fi

  if [ "$code" -ge 400 ]; then
    echo "$body" >&2
    return 1
  fi

  printf '%s' "$body"
}

http_any() {
  # Like http(), but never fails on non-2xx.
  local method="$1"
  local url="$2"
  shift 2

  local resp
  resp="$(
    curl "${CURL_TLS_ARGS[@]}" -sS -X "$method" "$url" \
      -w $'\n__HTTP_CODE__:%{http_code}' \
      "$@"
  )"

  local code="${resp##*__HTTP_CODE__:}"
  local body="${resp%$'\n'__HTTP_CODE__:*}"
  HTTP_LAST_CODE="$code"

  if [ "$VERBOSE" != "0" ]; then
    log "$method $url -> $code"
    if [ -n "$body" ]; then
      echo "$body" | pretty_json >&2
    fi
  fi

  printf '%s' "$body"
}

GATEWAY_BASE="${GATEWAY_BASE:-https://localhost:8443}"
AUTH_BASE="${AUTH_BASE:-${GATEWAY_BASE}/auth}"
PLAYER_BASE="${PLAYER_BASE:-${GATEWAY_BASE}/player}"
GAME_BASE="${GAME_BASE:-${GATEWAY_BASE}/game}"

USER1="${USER1:-testuser1}"
USER2="${USER2:-testuser2}"
PASSWORD="${PASSWORD:-TestPass123}"

log "AUTH_BASE=$AUTH_BASE PLAYER_BASE=$PLAYER_BASE GAME_BASE=$GAME_BASE"

echo "Starting containers..."
${COMPOSE_CMD} up -d --build

echo "Waiting for services..."
wait_for "${PLAYER_BASE}/health"
wait_for "${GAME_BASE}/health"
wait_for_auth_login "${AUTH_BASE}/login"

register_user() {
  local username="$1"
  local email="$2"
  local password="$3"
  http_any POST "${AUTH_BASE}/register" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${username}\",\"email\":\"${email}\",\"password\":\"${password}\"}" >/dev/null
  if [ "$HTTP_LAST_CODE" != "200" ] && [ "$HTTP_LAST_CODE" != "400" ]; then
    echo "Unexpected register status ($HTTP_LAST_CODE) for $username" >&2
    dump_service_logs 200
    return 1
  fi
}

login_user() {
  local username="$1"
  local password="$2"
  http POST "${AUTH_BASE}/login" \
    -H 'Content-Type: application/json' \
    -d "{\"username\":\"${username}\",\"password\":\"${password}\"}" | jq -r .access_token
}

echo "Registering users (idempotent)..."
register_user "$USER1" "test1@example.com" "$PASSWORD"
register_user "$USER2" "test2@example.com" "$PASSWORD"

echo "Logging in..."
TOKEN_1="$(login_user "$USER1" "$PASSWORD")"
TOKEN_2="$(login_user "$USER2" "$PASSWORD")"
log "token_1_len=${#TOKEN_1} token_2_len=${#TOKEN_2}"

if [ -z "$TOKEN_1" ] || [ "$TOKEN_1" = "null" ]; then
  echo "Failed to login $USER1" >&2
  exit 1
fi
if [ -z "$TOKEN_2" ] || [ "$TOKEN_2" = "null" ]; then
  echo "Failed to login $USER2" >&2
  exit 1
fi

echo "Starting match in Game Service..."
MATCH_CREATE="$(http POST "${GAME_BASE}/matches" \
  -H "Authorization: Bearer ${TOKEN_1}" \
  -H 'Content-Type: application/json' \
  -d "{\"player1_id\":\"${USER1}\",\"player2_id\":\"${USER2}\"}")"

MATCH_ID="$(echo "$MATCH_CREATE" | jq -r .match_id)"
if [ -z "$MATCH_ID" ] || [ "$MATCH_ID" = "null" ]; then
  echo "Failed to create match: $MATCH_CREATE" >&2
  exit 1
fi
echo "match_id=$MATCH_ID"

echo "Submitting a move for each player (card_index=0)..."
http POST "${GAME_BASE}/matches/${MATCH_ID}/move" \
  -H "Authorization: Bearer ${TOKEN_1}" \
  -H 'Content-Type: application/json' \
  -d "{\"card_index\":0,\"player_id\":\"${USER1}\"}" >/dev/null

http POST "${GAME_BASE}/matches/${MATCH_ID}/move" \
  -H "Authorization: Bearer ${TOKEN_2}" \
  -H 'Content-Type: application/json' \
  -d "{\"card_index\":0,\"player_id\":\"${USER2}\"}" >/dev/null

echo "Surrendering match as ${USER1}..."
SURRENDER_RES="$(http POST "${GAME_BASE}/matches/${MATCH_ID}/surrender" \
  -H "Authorization: Bearer ${TOKEN_1}")"
if [ "$VERBOSE" != "0" ]; then
  echo "$SURRENDER_RES" | pretty_json
fi

echo "Waiting for Player Service to record match..."
FOUND_MATCH=0
for _ in $(seq 1 30); do
  HISTORY="$(VERBOSE=0 http GET "${PLAYER_BASE}/players/${USER1}/matches" \
    -H "Authorization: Bearer ${TOKEN_1}")"
  if echo "$HISTORY" | jq -e --arg match_id "$MATCH_ID" 'any(.[]?; .external_match_id == $match_id)' >/dev/null 2>&1; then
    FOUND_MATCH=1
    break
  fi
  sleep 1
done
if [ "$FOUND_MATCH" != "1" ]; then
  echo "Player Service did not record match_id=${MATCH_ID} within 30s." >&2
  dump_service_logs 200
  exit 1
fi

echo "Match history (${USER1}):"
echo "$HISTORY" | pretty_json

echo "Leaderboard:"
http GET "${PLAYER_BASE}/leaderboard" \
  -H "Authorization: Bearer ${TOKEN_1}" | pretty_json

echo "Done."
