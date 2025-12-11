from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from game_app.database.database import get_db
from game_app.services.match_service import MatchService
from game_app.services.card_service import CardService
from game_app.api.schemas import (
    CreateMatchRequest,
    CreateMatchResponse,
    MoveRequest,
    MoveResultSchema,
    WaitingForOpponentSchema,
    MatchStateResponse,
)
from game_app.auth import get_current_user

router = APIRouter(tags=["game"])


# ============================================================
# MATCH ENDPOINTS
# ============================================================

@router.post("/matches", response_model=CreateMatchResponse)
async def create_match(
    data: CreateMatchRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Create a new match between two players."""
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


@router.post(
    "/matches/{match_id}/move",
    response_model=MoveResultSchema | WaitingForOpponentSchema,
)
async def submit_move(
    match_id: str,
    data: MoveRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Submit a card move in an active match."""
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


@router.get("/matches/{match_id}", response_model=MatchStateResponse)
async def get_match_state(
    match_id: str,
    player_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Get complete match state for a player."""
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


# ============================================================
# CARD ENDPOINTS (PUBLIC - No Auth Required)
# ============================================================

@router.get("/cards")
async def list_cards(db: Session = Depends(get_db)):
    """
    Get list of all available cards.

    Returns basic card information with image URLs.
    PUBLIC - no authentication required.
    """
    service = CardService(db)
    cards = service.get_all_cards()

    return {
        "total": len(cards),
        "cards": cards
    }


@router.get("/cards/{card_id}")
async def get_card_detail(card_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific card.

    Returns card data with URLs to images.
    PUBLIC - no authentication required.
    """
    service = CardService(db)
    card = service.get_card_by_id(card_id)

    if not card:
        raise HTTPException(status_code=404, detail=f"Card with ID {card_id} not found")

    return card


@router.get("/cards/{card_id}/image")
async def get_card_image(card_id: int, db: Session = Depends(get_db)):
    """
    Get card as PNG image (300x420).

    Automatically generates and returns a PNG image of the card.
    PUBLIC - no authentication required.
    """
    service = CardService(db)
    image_bytes = service.generate_card_image(card_id)

    if not image_bytes:
        raise HTTPException(status_code=404, detail=f"Card with ID {card_id} not found")

    return StreamingResponse(
        image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=card_{card_id}.png"}
    )


@router.get("/cards/{card_id}/thumbnail")
async def get_card_thumbnail(card_id: int, db: Session = Depends(get_db)):
    """
    Get card as small PNG thumbnail (150x210).

    Automatically generates and returns a small PNG thumbnail.
    PUBLIC - no authentication required.
    """
    service = CardService(db)
    image_bytes = service.generate_card_thumbnail(card_id)

    if not image_bytes:
        raise HTTPException(status_code=404, detail=f"Card with ID {card_id} not found")

    return StreamingResponse(
        image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=card_{card_id}_thumb.png"}
    )


@router.get("/cards/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics for card image generation.

    Shows hits, misses, and cache efficiency.
    Useful for monitoring and optimization.

    PUBLIC - no authentication required.
    """
    stats = CardService.get_cache_info()

    # Calculate hit rates
    for cache_type in ["images", "thumbnails"]:
        total = stats[cache_type]["hits"] + stats[cache_type]["misses"]
        if total > 0:
            stats[cache_type]["hit_rate"] = round(stats[cache_type]["hits"] / total * 100, 2)
        else:
            stats[cache_type]["hit_rate"] = 0.0

    return stats
