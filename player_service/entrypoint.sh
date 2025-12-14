#!/usr/bin/env sh
set -eu

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8002}"
APP_MODULE="${APP_MODULE:-app.main:app}"

ENABLE_TLS="${ENABLE_TLS:-0}"
TLS_DIR="${TLS_DIR:-/tmp/player_service_certs}"
TLS_CERTFILE="${TLS_CERTFILE:-$TLS_DIR/cert.pem}"
TLS_KEYFILE="${TLS_KEYFILE:-$TLS_DIR/key.pem}"
TLS_DAYS="${TLS_DAYS:-365}"
TLS_SUBJECT="${TLS_SUBJECT:-/CN=player_service}"

if [ "$ENABLE_TLS" = "1" ] || [ "$ENABLE_TLS" = "true" ]; then
  mkdir -p "$TLS_DIR"

  if [ ! -f "$TLS_CERTFILE" ] || [ ! -f "$TLS_KEYFILE" ]; then
    openssl req -x509 -newkey rsa:2048 -nodes \
      -keyout "$TLS_KEYFILE" \
      -out "$TLS_CERTFILE" \
      -days "$TLS_DAYS" \
      -subj "$TLS_SUBJECT" >/dev/null 2>&1
  fi

  exec uvicorn "$APP_MODULE" \
    --host "$APP_HOST" \
    --port "$APP_PORT" \
    --ssl-certfile "$TLS_CERTFILE" \
    --ssl-keyfile "$TLS_KEYFILE"
fi

exec uvicorn "$APP_MODULE" --host "$APP_HOST" --port "$APP_PORT"
