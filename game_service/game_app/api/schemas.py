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
