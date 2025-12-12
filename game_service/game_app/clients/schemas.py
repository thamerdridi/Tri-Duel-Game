"""
Client Schemas - Pydantic models for inter-service communication.

These schemas define the contract between Game Service and other microservices.
Using Pydantic ensures type safety and prevents "JSON hell".
"""
from typing import Optional
from pydantic import BaseModel, Field


class PlayerServiceMatchFinalize(BaseModel):
    """
    Schema for match finalization request to Player Service.

    Sent to Player Service POST /matches endpoint when a match completes.
    Player Service uses this to update player statistics and match history.

    Note: 'rounds' field is temporarily None - Player Service team is removing
    this requirement from their schema.
    """
    player1_external_id: str = Field(
        ...,
        description="Username of first player",
        min_length=1,
        max_length=100,
        examples=["alice"]
    )
    player2_external_id: str = Field(
        ...,
        description="Username of second player",
        min_length=1,
        max_length=100,
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
    rounds: Optional[list] = Field(
        None,
        description="Round details (temporarily None, will be removed by Player Service)"
    )
    seed: str = Field(
        ...,
        description="Match identifier used as seed",
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
                "rounds": None,
                "seed": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

