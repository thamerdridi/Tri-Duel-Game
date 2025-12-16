#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Configuration
# ============================================================

CERTS_DIR="$(cd "$(dirname "$0")" && pwd)"
CA_DIR="$CERTS_DIR/ca"

# MUST match directory names: certs/auth, certs/player, certs/game
SERVICES=("auth_service" "player_service" "game_service" "gateway")

DAYS_CA=3650
DAYS_CERT=365

# ============================================================
# Helpers
# ============================================================

log() {
  echo "🔐 $1"
}

ensure_dir() {
  mkdir -p "$1"
}

# ============================================================
# CA generation
# ============================================================

ensure_dir "$CA_DIR"

CA_KEY="$CA_DIR/ca.key"
CA_CERT="$CA_DIR/ca.crt"

if [[ ! -f "$CA_KEY" || ! -f "$CA_CERT" ]]; then
  log "Generating internal CA..."

  openssl genrsa -out "$CA_KEY" 4096

  openssl req -x509 -new -nodes \
    -key "$CA_KEY" \
    -sha256 \
    -days "$DAYS_CA" \
    -out "$CA_CERT" \
    -subj "//CN=internal-ca"

  log "CA generated"
else
  log "CA already exists – skipping"
fi

# ============================================================
# Service certificates
# ============================================================

for SERVICE in "${SERVICES[@]}"; do
  SERVICE_DIR="$CERTS_DIR/$SERVICE"
  ensure_dir "$SERVICE_DIR"

  KEY="$SERVICE_DIR/$SERVICE.key"
  CSR="$SERVICE_DIR/$SERVICE.csr"
  CRT="$SERVICE_DIR/$SERVICE.crt"
  CONF="$SERVICE_DIR/$SERVICE.cnf"

  if [[ -f "$KEY" && -f "$CRT" ]]; then
    log "$SERVICE certificate already exists – skipping"
    continue
  fi

  log "Generating certificate for $SERVICE"

  # ----------------------------------------------------------
  # OpenSSL config with SAN
  # ----------------------------------------------------------
  cat > "$CONF" <<EOF
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = req_ext

[ dn ]
CN = $SERVICE

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = $SERVICE
DNS.2 = localhost
IP.1  = 127.0.0.1
EOF

  # ----------------------------------------------------------
  # Key + CSR
  # ----------------------------------------------------------
  openssl genrsa -out "$KEY" 2048

  openssl req -new \
    -key "$KEY" \
    -out "$CSR" \
    -config "$CONF"

  # ----------------------------------------------------------
  # Sign with CA
  # ----------------------------------------------------------
  openssl x509 -req \
    -in "$CSR" \
    -CA "$CA_CERT" \
    -CAkey "$CA_KEY" \
    -CAcreateserial \
    -out "$CRT" \
    -days "$DAYS_CERT" \
    -sha256 \
    -extensions req_ext \
    -extfile "$CONF"

  rm -f "$CSR"
  chmod 644 "$CRT" "$KEY"

  log "$SERVICE certificate generated"
done

log "All certificates ready 🎉"
