from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import require_internal_api_key
from ..db import get_db
from ..models import PlayerProfile, Match, MatchTurn
from ..schemas import MatchCreate


router = APIRouter(
    prefix="/matches",
    tags=["matches"],
)


def get_player(external_id: str, db: Session) -> PlayerProfile:
    player = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.external_id == external_id)
        .first()
    )
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player not found: {external_id}")
    return player


@router.post("", status_code=201)
def create_match(
    payload: MatchCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_internal_api_key),
):
    p1 = get_player(payload.player1_external_id, db)
    p2 = get_player(payload.player2_external_id, db)

    external_match_id = payload.external_match_id

    existing = (
        db.query(Match)
        .filter(Match.external_match_id == external_match_id)
        .first()
    )
    if existing is not None:
        return {"id": existing.id}

    winner_id = None
    if payload.winner_external_id is not None:
        w = get_player(payload.winner_external_id, db)
        winner_id = w.id

    match = Match(
        external_match_id=external_match_id,
        player1_id=p1.id,
        player2_id=p2.id,
        winner_id=winner_id,
        player1_score=payload.player1_score,
        player2_score=payload.player2_score,
    )
    db.add(match)

    db.flush()
    for t in payload.turns:
        turn_winner_id = None
        if t.winner_external_id is not None:
            turn_winner_id = get_player(t.winner_external_id, db).id

        db.add(
            MatchTurn(
                match_id=match.id,
                turn_number=t.turn_number,
                player1_card_name=t.player1_card_name,
                player2_card_name=t.player2_card_name,
                winner_id=turn_winner_id,
            )
        )

    db.commit()

    return {"id": match.id}
