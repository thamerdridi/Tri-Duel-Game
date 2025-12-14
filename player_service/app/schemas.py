from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PlayerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: str
    username: str
    created_at: datetime


class PlayerProfileUpdate(BaseModel):
    username: Optional[str] = None


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    power: int
    name: str


class MatchSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_match_id: str
    player1_external_id: str
    player2_external_id: str
    winner_external_id: Optional[str]
    player1_score: int
    player2_score: int
    created_at: datetime


class MatchTurnCreate(BaseModel):
    turn_number: int
    player1_card_id: int
    player2_card_id: int
    winner_external_id: Optional[str] = None


class MatchTurnOut(BaseModel):
    turn_number: int
    player1_card_id: int
    player2_card_id: int
    winner_external_id: Optional[str] = None


class MatchDetailOut(MatchSummaryOut):
    turns: list[MatchTurnOut]


class MatchCreate(BaseModel):
    player1_external_id: str
    player2_external_id: str
    winner_external_id: Optional[str] = None
    player1_score: int
    player2_score: int
    external_match_id: str
    turns: list[MatchTurnCreate] = Field(default_factory=list)


class LeaderboardEntry(BaseModel):
    external_id: str
    username: str
    wins: int
    matches: int
