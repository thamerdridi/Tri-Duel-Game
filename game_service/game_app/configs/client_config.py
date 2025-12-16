"""
Client Configuration - URLs and settings for inter-service communication.

Configuration for HTTP clients to other microservices.
"""
import os

# ============================================================
# SERVICE URLS (Docker internal network)
# ============================================================

# Authentication Service
AUTH_SERVICE_URL = os.getenv(
    "AUTH_SERVICE_URL",
    "http://auth_service:8001"
)

# Player Service
PLAYER_SERVICE_URL = os.getenv(
    "PLAYER_SERVICE_URL",
    "http://player_service:8002"
)

# ============================================================
# TIMEOUT CONFIGURATION
# ============================================================

# Default timeout for HTTP requests (seconds)
DEFAULT_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "5"))

# Specific timeouts per service
AUTH_TIMEOUT = int(os.getenv("AUTH_TIMEOUT", "3"))
PLAYER_TIMEOUT = int(os.getenv("PLAYER_TIMEOUT", "5"))

# ============================================================
# RETRY CONFIGURATION
# ============================================================

# Maximum number of retry attempts
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))

# Exponential backoff multiplier (seconds)
RETRY_BACKOFF_BASE = int(os.getenv("RETRY_BACKOFF_BASE", "2"))

# Maximum wait time between retries (seconds)
MAX_RETRY_WAIT = int(os.getenv("MAX_RETRY_WAIT", "10"))

# ============================================================
# API ENDPOINTS
# ============================================================

# Auth Service Endpoints
AUTH_ENDPOINTS = {
    "verify_token": "/auth/verify",
    "validate": "/auth/validate",
}

# Player Service Endpoints
PLAYER_ENDPOINTS = {
    "finalize_match": "/matches",  # Changed from /matches/finalize to use existing Player Service endpoint
    "get_player": "/players/{player_id}",
    "update_stats": "/players/{player_id}/stats",
}

# Player Service API Key for service-to-service authentication
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "default_key")

