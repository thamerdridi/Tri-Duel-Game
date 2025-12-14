"""
Client Schemas - Pydantic models for inter-service communication.

These schemas define the contract between Game Service and other microservices.
Using Pydantic ensures type safety and prevents "JSON hell".
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class MatchTurnPayload(BaseModel):
    """Turn payload sent to Player Service containing card names (strings).

    Fields:
    - turn_number: int
    - player1_card_name: str
    - player2_card_name: str
    - winner_external_id: Optional[str]
    """
    turn_number: int = Field(...)
    player1_card_name: str = Field(...)
    player2_card_name: str = Field(...)
    winner_external_id: Optional[str] = Field(None)


class PlayerServiceMatchFinalize(BaseModel):
    """Schema for match finalization request to Player Service.

    Note: `turns` now contains list of `MatchTurnPayload` with card names as strings.
    Uses `external_match_id` to identify the match.
    """
    player1_external_id: str = Field(
        ...,
        description="Username of first player",
        min_length=1,
        max_length=100000,
        examples=["alice"]
    )
    player2_external_id: str = Field(
        ...,
        description="Username of second player",
        min_length=1,
        max_length=100000,
        examples=["bob"]
    )
    winner_external_id: Optional[str] = Field(
        None,
        description="Username of winner (None for draw)",
        examples=["alice", None]
    )
    player1_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Final score of player1 (0-5 points)"
    )
    player2_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Final score of player2 (0-5 points)"
    )
    turns: List[MatchTurnPayload] = Field(
        default_factory=list,
        description="List of turns with card names and winner information"
    )
    external_match_id: str = Field(
        ...,
        description="External match identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "player1_external_id": "alice",
                "player2_external_id": "bob",
                "winner_external_id": "alice",
                "player1_score": 3,
                "player2_score": 2,
                "turns": [
                    {"turn_number": 1, "player1_card_name": "rock_3", "player2_card_name": "scissors_2", "winner_external_id": "alice"}
                ],
                "external_match_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
