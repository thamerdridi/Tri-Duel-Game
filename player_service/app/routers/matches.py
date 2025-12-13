from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PlayerProfile, Match
from ..schemas import MatchCreate


router = APIRouter(
    prefix="/matches",
    tags=["matches"],
)


def get_or_create_player(external_id: str, db: Session) -> PlayerProfile:
    player = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.external_id == external_id)
        .first()
    )
    if player is None:
        player = PlayerProfile(
            external_id=external_id,
            username=external_id,  # simple default
        )
        db.add(player)
        db.flush()  # get player.id
    return player


@router.post("", status_code=201)
def create_match(payload: MatchCreate, db: Session = Depends(get_db)):
    """
    Called by Game Service when a match finishes.
    Stores match history (no per-round details).
    """

    # Players
    p1 = get_or_create_player(payload.player1_external_id, db)
    p2 = get_or_create_player(payload.player2_external_id, db)

    # Match winner (if any)
    winner_id = None
    if payload.winner_external_id is not None:
        w = get_or_create_player(payload.winner_external_id, db)
        winner_id = w.id

    # Create match
    match = Match(
        player1_id=p1.id,
        player2_id=p2.id,
        winner_id=winner_id,
        player1_score=payload.player1_score,
        player2_score=payload.player2_score,
        seed=payload.seed,
    )
    db.add(match)
    db.flush()  # get match.id

    db.commit()

    return {"id": match.id}
