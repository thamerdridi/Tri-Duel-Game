import os

# All cards
CARDS = {
    "rock":     [1, 2, 3, 4, 5, 6],
    "paper":    [1, 2, 3, 4, 5, 6],
    "scissors": [1, 2, 3, 4, 5, 6],
}

# Map Domain_Card: Database_Card
DOMAIN_CARDS = {
    "id": "id",
    "power": "power",
    "category": "category"
}

# ============================================================
# VALIDATION CONSTANTS
# ============================================================
# These have been moved to validation_config.py for centralization
# Re-exported here for backward compatibility
from game_app.configs.validation_config import (
    MIN_CARD_POWER,
    MAX_CARD_POWER,
    MIN_CARD_ID,
    MAX_CARD_ID,
)
