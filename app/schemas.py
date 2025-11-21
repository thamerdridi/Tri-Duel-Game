from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# ========= Player profile =========

class PlayerProfileOut(BaseModel):
    external_id: str
    username: str
    bio: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PlayerProfileUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None


# ========= Cards =========

class CardOut(BaseModel):
    id: int
    category: str
    power: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ========= Match rounds =========

class MatchRoundCreate(BaseModel):
    round_number: int
    player1_card_id: int
    player2_card_id: int
    winner_external_id: Optional[str] = None  # None = draw


class MatchRoundOut(BaseModel):
    round_number: int
    player1_card: CardOut
    player2_card: CardOut
    winner_external_id: Optional[str] = None

    class Config:
        from_attributes = True


# ========= Matches (history) =========

class MatchSummaryOut(BaseModel):
    id: int
    player1_external_id: str
    player2_external_id: str
    winner_external_id: Optional[str]
    player1_score: int
    player2_score: int
    rounds_played: int
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchDetailOut(MatchSummaryOut):
    rounds: List[MatchRoundOut]


class MatchCreate(BaseModel):
    """
    Payload expected from Game Service when a match finishes.
    """
    player1_external_id: str
    player2_external_id: str
    winner_external_id: Optional[str] = None
    player1_score: int
    player2_score: int
    rounds: List[MatchRoundCreate]
    seed: Optional[str] = None


# ========= Leaderboard =========

class LeaderboardEntry(BaseModel):
    external_id: str
    username: str
    wins: int
    matches: int
