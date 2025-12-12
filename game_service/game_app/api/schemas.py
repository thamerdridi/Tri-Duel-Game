from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ============================================================
# BASIC TYPES (Domain -> API)
# ============================================================
class CardSchema(BaseModel):
    id: int = Field(ge=1, description="Card definition ID")
    category: str = Field(
        pattern=r'^(rock|paper|scissors)$',
        description="Card category (RPS)",
        examples=["rock", "paper", "scissors"]
    )
    power: int = Field(
        ge=10,
        le=60,
        description="Card power level",
        examples=[10, 30, 60]
    )

class HandCardSchema(BaseModel):
    match_card_id: int = Field(ge=1, description="Match card instance ID")
    card: CardSchema


class PlayerHandSchema(BaseModel):
    cards: List[CardSchema]


# ============================================================
# CREATE MATCH
# ============================================================
class CreateMatchRequest(BaseModel):
    player1_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Username (alphanumeric, underscore, hyphen)",
        examples=["alice", "player_123", "bob-2024"]
    )
    player2_id: str = Field(
        min_length=1,
        max_length=100,
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
    match_card_id: int = Field(
        ge=1,
        le=100000,
        description="ID of card to play from hand",
        examples=[1, 42, 99]
    )
    player_id: str = Field(
        min_length=1,
        max_length=100,
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
        le=5,
        description="Round number when card was played (1-5)"
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


# ============================================================
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
