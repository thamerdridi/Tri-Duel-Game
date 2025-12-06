from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from game_app.database.database import get_db
from game_app.services.match_service import MatchService
from game_app.api.schemas import (
    CreateMatchRequest,
    CreateMatchResponse,
    MoveRequest,
    MoveResultSchema,
    WaitingForOpponentSchema,
    MatchStateResponse,
)
from game_app.auth import get_current_user

router = APIRouter(prefix="/matches", tags=["matches"])


# ============================================================
# POST /matches
# Create a new match
# ============================================================
@router.post("/", response_model=CreateMatchResponse)
async def create_match(
    data: CreateMatchRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    # Validate that player1_id matches authenticated user
    if data.player1_id != user.get("sub"):
        raise HTTPException(
            status_code=403,
            detail="You can only create matches as yourself (player1_id must match your username)"
        )

    service = MatchService(db)

    try:
        match = service.create_match(data.player1_id, data.player2_id)
        player_hand = service.get_player_hand(match.id, data.player1_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CreateMatchResponse(
        match_id=match.id,
        player_id=data.player1_id,
        hand=player_hand,
        status=match.status,
    )


# ============================================================
# POST /matches/{match_id}/move
# Submit move (play a card)
# ============================================================
@router.post(
    "/{match_id}/move",
    response_model=MoveResultSchema | WaitingForOpponentSchema,
)
async def submit_move(
    match_id: str,
    data: MoveRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    # Validate that player_id matches authenticated user
    if data.player_id != user.get("sub"):
        raise HTTPException(
            status_code=403,
            detail="You can only submit moves for yourself"
        )

    service = MatchService(db)

    try:
        result = service.submit_move(match_id, data.player_id, data.match_card_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # waiting for opponent
    if result.get("status") == "waiting_for_opponent":
        return WaitingForOpponentSchema()

    # return full round result
    return MoveResultSchema(**result)


# ============================================================
# GET /matches/{match_id}
# Get complete match state for given player
# ============================================================
@router.get("/{match_id}", response_model=MatchStateResponse)
async def get_match_state(
    match_id: str,
    player_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    # Validate that player_id matches authenticated user
    if player_id != user.get("sub"):
        raise HTTPException(
            status_code=403,
            detail="You can only view your own match state"
        )

    service = MatchService(db)

    try:
        state = service.get_state(match_id, player_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MatchStateResponse(**state)
