"""
==========================================
VALIDATION CONFIGURATION
==========================================

Central configuration for all validation rules used in:
- Pydantic schemas (API request/response validation)
- Unit tests (validation boundary testing)
- Business logic validation

This ensures consistency across the application and makes it easy
to adjust validation rules in one place.
"""

import os

# ============================================================
# CARD VALIDATION
# ============================================================

# Card power bounds
MIN_CARD_POWER = 1
MAX_CARD_POWER = 10  # Allows future expansion beyond current max of 6

# Card ID bounds (for match_card_id, card instance IDs)
MIN_CARD_ID = 1
MAX_CARD_ID = 100000  # Maximum card instance ID in a match

# ============================================================
# PLAYER VALIDATION
# ============================================================

# Player ID (username) length constraints
MIN_PLAYER_ID_LENGTH = 1
MAX_PLAYER_ID_LENGTH = 100

# ============================================================
# GAME LOGIC VALIDATION
# ============================================================

# Re-exported here for easier access
from game_app.configs.logic_configs import (
    HAND_SIZE,
    MAX_ROUNDS
)

# Round number bounds
MIN_ROUND = 1
MAX_ROUND = MAX_ROUNDS

# ============================================================
# MATCH VALIDATION
# ============================================================

# Match ID format (generated as UUID strings)
MAX_MATCH_ID_LENGTH = 100

# ============================================================
# SUMMARY
# ============================================================
#
# Usage examples:
#
# In schemas.py:
#   from game_app.configs.validation_config import MIN_CARD_POWER, MAX_CARD_POWER
#   power: int = Field(ge=MIN_CARD_POWER, le=MAX_CARD_POWER)
#
# In tests:
#   from game_app.configs.validation_config import MAX_CARD_POWER
#   card = CardSchema(id=1, category="rock", power=MAX_CARD_POWER)
#

