from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import List

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
from game_app.clients.auth_client import get_current_user
from game_app.configs.logging_config import log_if_enabled

logger = logging.getLogger(__name__)
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
        # Security logging: Unauthorized match creation attempt
        log_if_enabled(
            logger,
            "warning",
            f"⚠️ UNAUTHORIZED_ATTEMPT | action=create_match | "
            f"user={user.get('sub')} | attempted_as={data.player1_id}"
        )
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
        # Security logging: Unauthorized move attempt
        log_if_enabled(
            logger,
            "warning",
            f"⚠️ UNAUTHORIZED_ATTEMPT | action=submit_move | "
            f"user={user.get('sub')} | attempted_as={data.player_id} | match_id={match_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="You can only submit moves for yourself"
        )

    service = MatchService(db)

    try:
        result = service.submit_move(match_id, data.player_id, data.card_index)
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
        # Security logging: Unauthorized match state access
        log_if_enabled(
            logger,
            "warning",
            f"⚠️ UNAUTHORIZED_ATTEMPT | action=view_match_state | "
            f"user={user.get('sub')} | attempted_as={player_id} | match_id={match_id}"
        )
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


@router.get("/matches/active", response_model=List[MatchStateResponse])
def get_active_matches(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Retrieve all active matches for the authenticated user."""
    service = MatchService(db)
    active_matches = service.get_active_matches(user.get("sub"))
    return active_matches


@router.post("/matches/{match_id}/surrender", response_model=MatchStateResponse)
def surrender_match(
    match_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Surrender the match, marking it as a loss for the surrendering player."""
    service = MatchService(db)
    try:
        match_state = service.surrender_match(match_id, user.get("sub"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return match_state


# ============================================================
# CARD VISUALIZATION ENDPOINTS (PUBLIC - SVG Only)
# ============================================================

@router.get("/cards/{card_id}")
async def get_card_detail_svg(card_id: int, db: Session = Depends(get_db)):
    """
    Get card detail view as SVG (VIEW 2: Card Detail).

    Shows single card with all details:
    - Category (Rock/Paper/Scissors)
    - Power level with visual bar
    - Rarity (Common/Rare/Legendary)
    - Card ID

    PUBLIC - no authentication required.

    Usage:
        - Browser: http://localhost:8003/cards/1
        - HTML: <img src="http://localhost:8003/cards/1" alt="Card 1"/>
        - Postman: Direct visualization
    """
    from fastapi.responses import Response

    service = CardService(db)
    svg_content = service.generate_card_svg(card_id)

    if not svg_content:
        raise HTTPException(status_code=404, detail=f"Card with ID {card_id} not found")

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Content-Disposition": f"inline; filename=card_{card_id}.svg",
            "Cache-Control": "public, max-age=3600"
        }
    )


@router.get("/cards")
async def get_deck_gallery(db: Session = Depends(get_db)):
    """
    Get complete deck gallery as SVG (VIEW 1: Deck Gallery).

    Shows all available cards in a grid layout with thumbnails.
    Perfect for browsing all cards in the game.

    PUBLIC - no authentication required.

    Usage:
        - Browser: http://localhost:8003/cards
        - Displays all cards in organized grid (5 per row)
        - Shows statistics (Rock/Paper/Scissors count)
        - All cards with power levels and rarity borders
    """
    from fastapi.responses import Response

    service = CardService(db)
    svg_content = service.generate_deck_gallery_svg()

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Content-Disposition": "inline; filename=deck_gallery.svg",
            "Cache-Control": "public, max-age=3600"
        }
    )


@router.get("/matches/{match_id}/hand")
async def get_player_hand_visual(
    match_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get player's hand visualization as SVG (VIEW 3: Player Hand).

    Shows player's cards in a match with visual distinction:
    - Available cards (can be played) - shown in color
    - Used cards (already played) - shown in grayscale with red X

    AUTHENTICATED - player can only view their own hand.

    Args:
        match_id: Match identifier

    Returns:
        SVG visualization of player's hand

    Usage:
        - Browser: http://localhost:8003/matches/{match_id}/hand
        - Shows available and used cards separately
        - Used cards are grayed out and marked
    """
    from fastapi.responses import Response
    from game_app.utils.card_deck_svg import generate_player_hand_svg

    player_id = user.get("sub")

    match_service = MatchService(db)

    # Get cards with used status
    try:
        cards = match_service.get_player_hand_with_used_status(match_id, player_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Match or player not found: {str(e)}")

    # Generate SVG
    svg_content = generate_player_hand_svg(cards, match_id)

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Content-Disposition": f"inline; filename=hand_{match_id}.svg",
            "Cache-Control": "no-cache"  # Hand changes during match
        }
    )
