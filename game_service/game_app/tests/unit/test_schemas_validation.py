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
    assert any("at least 1 character" in str(error) for error in errors)


def test_create_match_too_long_player_id():
    """Test that excessively long player IDs are rejected."""
    long_id = "a" * 101  # 101 characters
    with pytest.raises(ValidationError) as exc_info:
        CreateMatchRequest(player1_id=long_id, player2_id="bob")
    errors = exc_info.value.errors()
    assert any("at most 100 characters" in str(error) for error in errors)


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
    request = MoveRequest(match_card_id=42, player_id="alice")
    assert request.match_card_id == 42
    assert request.player_id == "alice"


def test_move_request_negative_card_id():
    """Test that negative card IDs are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        MoveRequest(match_card_id=-1, player_id="alice")
    errors = exc_info.value.errors()
    assert any("greater than or equal to 1" in str(error) for error in errors)


def test_move_request_zero_card_id():
    """Test that zero card ID is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        MoveRequest(match_card_id=0, player_id="alice")
    errors = exc_info.value.errors()
    assert any("greater than or equal to 1" in str(error) for error in errors)


def test_move_request_too_large_card_id():
    """Test that excessively large card IDs are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        MoveRequest(match_card_id=100001, player_id="alice")
    errors = exc_info.value.errors()
    assert any("less than or equal to 100000" in str(error) for error in errors)


def test_move_request_invalid_player_id():
    """Test that invalid player_id format is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        MoveRequest(match_card_id=42, player_id="alice; DROP TABLE;")
    errors = exc_info.value.errors()
    assert any("pattern" in str(error) for error in errors)


# ============================================================
# CardSchema VALIDATION TESTS
# ============================================================

def test_card_schema_valid_rock():
    """Test that valid rock card passes validation."""
    card = CardSchema(id=1, category="rock", power=30)
    assert card.id == 1
    assert card.category == "rock"
    assert card.power == 30


def test_card_schema_valid_paper():
    """Test that valid paper card passes validation."""
    card = CardSchema(id=2, category="paper", power=40)
    assert card.category == "paper"


def test_card_schema_valid_scissors():
    """Test that valid scissors card passes validation."""
    card = CardSchema(id=3, category="scissors", power=50)
    assert card.category == "scissors"


def test_card_schema_invalid_category():
    """Test that invalid categories are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=1, category="invalid", power=30)
    errors = exc_info.value.errors()
    assert any("pattern" in str(error) for error in errors)


def test_card_schema_power_too_low():
    """Test that power below minimum is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=1, category="rock", power=5)
    errors = exc_info.value.errors()
    assert any("greater than or equal to 10" in str(error) for error in errors)


def test_card_schema_power_too_high():
    """Test that power above maximum is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=1, category="rock", power=70)
    errors = exc_info.value.errors()
    assert any("less than or equal to 60" in str(error) for error in errors)


def test_card_schema_negative_id():
    """Test that negative IDs are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=-1, category="rock", power=30)
    errors = exc_info.value.errors()
    assert any("greater than or equal to 1" in str(error) for error in errors)


def test_card_schema_zero_id():
    """Test that zero ID is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        CardSchema(id=0, category="rock", power=30)
    errors = exc_info.value.errors()
    assert any("greater than or equal to 1" in str(error) for error in errors)


# ============================================================
# PlayedCardSchema VALIDATION TESTS
# ============================================================

def test_played_card_valid():
    """Test that valid played card passes validation."""
    card = CardSchema(id=1, category="rock", power=30)
    played = PlayedCardSchema(card=card, round_used=3)
    assert played.round_used == 3


def test_played_card_invalid_round_zero():
    """Test that round 0 is rejected."""
    card = CardSchema(id=1, category="rock", power=30)
    with pytest.raises(ValidationError) as exc_info:
        PlayedCardSchema(card=card, round_used=0)
    errors = exc_info.value.errors()
    assert any("greater than or equal to 1" in str(error) for error in errors)


def test_played_card_invalid_round_too_high():
    """Test that rounds above MAX_ROUNDS are rejected."""
    card = CardSchema(id=1, category="rock", power=30)
    with pytest.raises(ValidationError) as exc_info:
        PlayedCardSchema(card=card, round_used=6)
    errors = exc_info.value.errors()
    assert any("less than or equal to 5" in str(error) for error in errors)


# ============================================================
# BOUNDARY TESTS
# ============================================================

def test_create_match_boundary_min_length():
    """Test minimum valid length for player IDs."""
    request = CreateMatchRequest(player1_id="a", player2_id="b")
    assert len(request.player1_id) == 1


def test_create_match_boundary_max_length():
    """Test maximum valid length for player IDs."""
    max_id = "a" * 100
    request = CreateMatchRequest(player1_id=max_id, player2_id="bob")
    assert len(request.player1_id) == 100


def test_move_request_boundary_min_card_id():
    """Test minimum valid card ID."""
    request = MoveRequest(match_card_id=1, player_id="alice")
    assert request.match_card_id == 1


def test_move_request_boundary_max_card_id():
    """Test maximum valid card ID."""
    request = MoveRequest(match_card_id=100000, player_id="alice")
    assert request.match_card_id == 100000


def test_card_schema_boundary_min_power():
    """Test minimum valid power."""
    card = CardSchema(id=1, category="rock", power=10)
    assert card.power == 10


def test_card_schema_boundary_max_power():
    """Test maximum valid power."""
    card = CardSchema(id=1, category="rock", power=60)
    assert card.power == 60

