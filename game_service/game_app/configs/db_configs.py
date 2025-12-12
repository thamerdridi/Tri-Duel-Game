import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./game.db")

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

# Connection pool settings (PostgreSQL only)
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# Enable query logging (development only)
DB_ECHO = os.getenv("DB_ECHO", False)

# ============================================================
# VALIDATION CONSTANTS
# ============================================================
# These have been moved to validation_config.py for centralization
# Re-exported here for backward compatibility
from game_app.configs.validation_config import (
    MIN_PLAYER_ID_LENGTH,
    MAX_PLAYER_ID_LENGTH,
)
