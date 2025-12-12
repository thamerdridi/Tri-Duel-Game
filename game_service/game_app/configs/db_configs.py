import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./game.db")

# ============================================================
# CONNECTION POOL SETTINGS (PostgreSQL only)
# ============================================================

# Import from client_config to avoid duplication
from game_app.configs.client_config import (
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
    DB_ECHO
)
