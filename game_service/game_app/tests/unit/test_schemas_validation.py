"""
==========================================
PYDANTIC SCHEMA VALIDATION TESTS
==========================================

PURPOSE:
--------
Unit tests for Pydantic validation in API schemas.
Verifies that input validation prevents malicious or invalid data.

WHAT IS TESTED:
---------------
1. CreateMatchRequest:
   - Invalid characters (SQL injection attempts)
   - Self-play prevention
   - Length constraints

2. MoveRequest:
   - Negative/zero card IDs
   - Invalid player_id format
   - Upper bound constraints

3. CardSchema:
   - Invalid categories
   - Power level bounds
   - ID constraints

HOW TO RUN:
-----------
Run validation tests:
    $ cd game_service
    $ pytest game_app/tests/unit/test_schemas_validation.py -v

Run with verbose output:
    $ pytest game_app/tests/unit/test_schemas_validation.py -v -s

NOTES:
------
- These tests verify security constraints
- FastAPI automatically returns 422 for validation errors
- Tests use pytest.raises to catch ValidationError
"""

import pytest
from pydantic import ValidationError
from game_app.api.schemas import CreateMatchRequest, MoveRequest, CardSchema, PlayedCardSchema
from game_app.configs.validation_config import (
    MIN_CARD_POWER,
    MAX_CARD_POWER,
    MIN_CARD_ID,
    MAX_CARD_ID,
    MIN_PLAYER_ID_LENGTH,
    MAX_PLAYER_ID_LENGTH,
    MAX_ROUNDS,
)


# ============================================================
# CreateMatchRequest VALIDATION TESTS
# ============================================================

def test_create_match_valid():
    """Test that valid input passes validation."""
    request = CreateMatchRequest(player1_id="alice", player2_id="bob")
    assert request.player1_id == "alice"
    assert request.player2_id == "bob"


def test_create_match_sql_injection_attempt():
    """Test that SQL injection attempts are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMatchRequest(
            player1_id="alice'; DROP TABLE users;--",
            player2_id="bob"
        )
    errors = exc_info.value.errors()
    assert any("pattern" in str(error) for error in errors)


def test_create_match_xss_attempt():
    """Test that XSS attempts are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMatchRequest(
            player1_id="<script>alert('xss')</script>",
            player2_id="bob"
        )
    errors = exc_info.value.errors()
    assert any("pattern" in str(error) for error in errors)


def test_create_match_same_players():
    """Test that players cannot be the same."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMatchRequest(player1_id="alice", player2_id="alice")
    errors = exc_info.value.errors()
    assert any("Cannot play against yourself" in str(error) for error in errors)


def test_create_match_empty_player_id():
    """Test that empty player IDs are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMatchRequest(player1_id="", player2_id="bob")
    errors = exc_info.value.errors()
    assert any(f"at least {MIN_PLAYER_ID_LENGTH} character" in str(error) for error in errors)


def test_create_match_too_long_player_id():
    """Test that excessively long player IDs are rejected."""
    long_id = "a" * (MAX_PLAYER_ID_LENGTH + 1)  # Over max length
    with pytest.raises(ValidationError) as exc_info:
        CreateMatchRequest(player1_id=long_id, player2_id="bob")
    errors = exc_info.value.errors()
    assert any(f"at most {MAX_PLAYER_ID_LENGTH} characters" in str(error) for error in errors)


def test_create_match_special_chars():
    """Test that special characters are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMatchRequest(player1_id="alice@email.com", player2_id="bob")
    errors = exc_info.value.errors()
    assert any("pattern" in str(error) for error in errors)


def test_create_match_valid_with_underscores_hyphens():
    """Test that underscores and hyphens are allowed."""
    request = CreateMatchRequest(player1_id="alice_123", player2_id="bob-456")
    assert request.player1_id == "alice_123"
    assert request.player2_id == "bob-456"


# ============================================================
# MoveRequest VALIDATION TESTS
# ============================================================

def test_move_request_valid():
    """Test that valid move request passes validation."""
    request = MoveRequest(card_index=2, player_id="alice")
    assert request.card_index == 2
    assert request.player_id == "alice"


def test_move_request_negative_card_index():
    """Test that negative card index is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        MoveRequest(card_index=-1, player_id="alice")
    errors = exc_info.value.errors()
    assert any("greater than or equal to 0" in str(error) for error in errors)


def test_move_request_too_large_card_index():
    """Test that card index > 4 is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        MoveRequest(card_index=5, player_id="alice")
    errors = exc_info.value.errors()
    assert any("less than or equal to 4" in str(error) for error in errors)


def test_move_request_valid_boundaries():
    """Test that card_index boundaries (0 and 4) are valid."""
    request_min = MoveRequest(card_index=0, player_id="alice")
    assert request_min.card_index == 0

    request_max = MoveRequest(card_index=4, player_id="alice")
    assert request_max.card_index == 4


def test_move_request_invalid_player_id():
    """Test that invalid player_id format is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        MoveRequest(card_index=2, player_id="alice; DROP TABLE;")
    errors = exc_info.value.errors()
    assert any("pattern" in str(error) for error in errors)


# ============================================================
# CardSchema VALIDATION TESTS
# ============================================================

def test_card_schema_valid_rock():
    """Test that valid rock card passes validation."""
    card = CardSchema(id=1, category="rock", power=3)
    assert card.id == 1
    assert card.category == "rock"
    assert card.power == 3


def test_card_schema_valid_paper():
    """Test that valid paper card passes validation."""
    card = CardSchema(id=2, category="paper", power=4)
    assert card.category == "paper"


def test_card_schema_valid_scissors():
    """Test that valid scissors card passes validation."""
    card = CardSchema(id=3, category="scissors", power=5)
    assert card.category == "scissors"


def test_card_schema_invalid_category():
    """Test that invalid categories are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=1, category="invalid", power=3)
    errors = exc_info.value.errors()
    assert any("pattern" in str(error) for error in errors)


def test_card_schema_power_too_low():
    """Test that power below minimum is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=1, category="rock", power=MIN_CARD_POWER - 1)
    errors = exc_info.value.errors()
    assert any(f"greater than or equal to {MIN_CARD_POWER}" in str(error) for error in errors)


def test_card_schema_power_too_high():
    """Test that power above maximum is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=1, category="rock", power=MAX_CARD_POWER + 1)
    errors = exc_info.value.errors()
    assert any(f"less than or equal to {MAX_CARD_POWER}" in str(error) for error in errors)


def test_card_schema_negative_id():
    """Test that negative IDs are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=-1, category="rock", power=3)
    errors = exc_info.value.errors()
    assert any(f"greater than or equal to {MIN_CARD_ID}" in str(error) for error in errors)


def test_card_schema_zero_id():
    """Test that zero ID is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=0, category="rock", power=3)
    errors = exc_info.value.errors()
    assert any(f"greater than or equal to {MIN_CARD_ID}" in str(error) for error in errors)


# ============================================================
# PlayedCardSchema VALIDATION TESTS
# ============================================================

def test_played_card_valid():
    """Test that valid played card passes validation."""
    card = CardSchema(id=1, category="rock", power=3)
    played = PlayedCardSchema(card=card, round_used=3)
    assert played.round_used == 3


def test_played_card_invalid_round_zero():
    """Test that round 0 is rejected."""
    card = CardSchema(id=1, category="rock", power=3)
    with pytest.raises(ValidationError) as exc_info:
        PlayedCardSchema(card=card, round_used=0)
    errors = exc_info.value.errors()
    assert any("greater than or equal to 1" in str(error) for error in errors)


def test_played_card_invalid_round_too_high():
    """Test that rounds above MAX_ROUNDS are rejected."""
    card = CardSchema(id=1, category="rock", power=3)
    with pytest.raises(ValidationError) as exc_info:
        PlayedCardSchema(card=card, round_used=MAX_ROUNDS + 1)
    errors = exc_info.value.errors()
    assert any(f"less than or equal to {MAX_ROUNDS}" in str(error) for error in errors)


# ============================================================
# BOUNDARY TESTS
# ============================================================

def test_create_match_boundary_min_length():
    """Test minimum valid length for player IDs."""
    min_id = "a" * MIN_PLAYER_ID_LENGTH
    request = CreateMatchRequest(player1_id=min_id, player2_id="b")
    assert len(request.player1_id) == MIN_PLAYER_ID_LENGTH


def test_create_match_boundary_max_length():
    """Test maximum valid length for player IDs."""
    max_id = "a" * MAX_PLAYER_ID_LENGTH
    request = CreateMatchRequest(player1_id=max_id, player2_id="bob")
    assert len(request.player1_id) == MAX_PLAYER_ID_LENGTH


# Boundary tests for card_index already covered in test_move_request_valid_boundaries above


def test_card_schema_boundary_min_power():
    """Test minimum valid power."""
    card = CardSchema(id=1, category="rock", power=MIN_CARD_POWER)
    assert card.power == MIN_CARD_POWER


def test_card_schema_boundary_max_power():
    """Test maximum valid power."""
    card = CardSchema(id=1, category="rock", power=MAX_CARD_POWER)
    assert card.power == MAX_CARD_POWER

