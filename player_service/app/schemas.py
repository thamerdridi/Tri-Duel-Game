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


class PlayerProfileSync(BaseModel):
    external_id: str
    username: Optional[str] = None


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
    player1_card_name: str
    player2_card_name: str
    winner_external_id: Optional[str] = None


class MatchTurnOut(BaseModel):
    turn_number: int
    player1_card_name: str
    player2_card_name: str
    winner_external_id: Optional[str] = None


class MatchDetailOut(MatchSummaryOut):
    moves_log: Optional[str] = None
    turns: list[MatchTurnOut]


class MatchCreate(BaseModel):
    player1_external_id: str
    player2_external_id: str
    winner_external_id: Optional[str] = None
    player1_score: int
    player2_score: int
    external_match_id: str
    moves_log: Optional[str] = None
    turns: list[MatchTurnCreate] = Field(default_factory=list)


class LeaderboardEntry(BaseModel):
    external_id: str
    username: str
    wins: int
    matches: int
