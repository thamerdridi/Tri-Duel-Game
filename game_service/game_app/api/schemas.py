from typing import Optional, List
from pydantic import BaseModel


# ============================================================
# BASIC TYPES (Domain -> API)
# ============================================================
class CardSchema(BaseModel):
    id: int
    category: str
    power: int

class HandCardSchema(BaseModel):
    match_card_id: int
    card: CardSchema


class PlayerHandSchema(BaseModel):
    cards: List[CardSchema]


# ============================================================
# CREATE MATCH
# ============================================================
class CreateMatchRequest(BaseModel):
    player1_id: str
    player2_id: str


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
    match_card_id: int
    player_id: str



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
    round_used: int

class MatchStateRequest(BaseModel): # obsolete
    player_id: str


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
