from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from game_app.configs.validation_config import (
    MIN_CARD_POWER,
    MAX_CARD_POWER,
    MIN_CARD_ID,
    MAX_CARD_ID,
    MIN_PLAYER_ID_LENGTH,
    MAX_PLAYER_ID_LENGTH,
    MAX_ROUNDS,
    HAND_SIZE,
)


# ============================================================
# BASIC TYPES (Domain -> API)
# ============================================================
class CardSchema(BaseModel):
    id: int = Field(ge=MIN_CARD_ID, description="Card definition ID")
    category: str = Field(
        pattern=r'^(rock|paper|scissors)$',
        description="Card category (RPS)",
        examples=["rock", "paper", "scissors"]
    )
    power: int = Field(
        ge=MIN_CARD_POWER,
        le=MAX_CARD_POWER,
        description="Card power level",
        examples=[1, 3, 6]
    )

class HandCardSchema(BaseModel):
    """Card in player's hand with index for easy selection."""
    hand_index: int = Field(
        ge=0,
        le=HAND_SIZE-1,
        description="Index in hand (0-4) - USE THIS to select card!",
        examples=[0, 1, 2, 3, 4]
    )
    card: CardSchema


class PlayerHandSchema(BaseModel):
    cards: List[CardSchema]


# ============================================================
# CREATE MATCH
# ============================================================
class CreateMatchRequest(BaseModel):
    player1_id: str = Field(
        min_length=MIN_PLAYER_ID_LENGTH,
        max_length=MAX_PLAYER_ID_LENGTH,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Username (alphanumeric, underscore, hyphen)",
        examples=["alice", "player_123", "bob-2024"]
    )
    player2_id: str = Field(
        min_length=MIN_PLAYER_ID_LENGTH,
        max_length=MAX_PLAYER_ID_LENGTH,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Opponent username",
        examples=["bob", "player_456"]
    )

    @field_validator('player2_id')
    @classmethod
    def validate_not_same_player(cls, v, info):
        """Ensure players are different."""
        player1 = info.data.get('player1_id')
        if player1 and v == player1:
            raise ValueError("Cannot play against yourself")
        return v


class CreateMatchResponse(BaseModel):
    match_id: str
    player_id: str
    hand: List[HandCardSchema]
    status: str


    class Config:
        orm_mode = True


# ============================================================
# SUBMIT MOVE
# ============================================================
class MoveRequest(BaseModel):
    """Request to submit a move - select card by index in hand (0-4)."""
    card_index: int = Field(
        ge=0,
        le=HAND_SIZE-1,
        description="Index of card in hand (0-4)",
        examples=[0, 1, 2, 3, 4]
    )
    player_id: str = Field(
        min_length=MIN_PLAYER_ID_LENGTH,
        max_length=MAX_PLAYER_ID_LENGTH,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Player making the move",
        examples=["alice", "bob"]
    )



class MoveResultSchema(BaseModel):
    round: int
    winner: Optional[str]      # "p1" | "p2" | None (draw)
    reason: str
    points_p1: int
    points_p2: int
    match_finished: bool
    match_winner: Optional[str]

    class Config:
        orm_mode = True


class WaitingForOpponentSchema(BaseModel):
    status: str = "waiting_for_opponent"


# ============================================================
# MATCH STATE (GET /matches/{match_id})
# ============================================================
class PlayedCardSchema(BaseModel):
    card: CardSchema
    round_used: int = Field(
        ge=1,
        le=MAX_ROUNDS,
        description=f"Round number when card was played (1-{MAX_ROUNDS})"
    )

class MatchStateResponse(BaseModel):
    match_id: str
    status: str
    current_round: int
    points_p1: int
    points_p2: int
    player_hand: List[HandCardSchema]
    used_cards: List[PlayedCardSchema]
    opponent_used_cards: List[PlayedCardSchema]

    match_winner: Optional[str]

    class Config:
        orm_mode = True


# ===========================================================
# CARD DISPLAY (GET /cards endpoints)
# ============================================================
class CardDisplaySchema(BaseModel):
    """
    Extended card schema with ASCII art visualization.
    Used for card browsing endpoints.
    """
    id: int
    category: str
    power: int
    emoji: str
    ascii_art: str
    ascii_compact: str
    display_text: str

    class Config:
        orm_mode = True


class CardListResponse(BaseModel):
    """
    Response for GET /cards - list of all cards with display.
    """
    total: int
    cards: List[CardDisplaySchema]
    ascii_list: str  # Full ASCII art list view


class CardDetailResponse(BaseModel):
    """
    Response for GET /cards/{id} - single card detail with full ASCII art.
    """
    card: CardDisplaySchema
    description: str
    beats: str  # What this card beats
    loses_to: str  # What beats this card

