from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PlayerProfile, Match, MatchRound
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
    Stores match + rounds as immutable history.
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
        rounds_played=len(payload.rounds),
        seed=payload.seed,
    )
    db.add(match)
    db.flush()  # get match.id

    # Create rounds
    for r in payload.rounds:
        round_winner_id = None
        if r.winner_external_id is not None:
            rw = get_or_create_player(r.winner_external_id, db)
            round_winner_id = rw.id

        db.add(
            MatchRound(
                match_id=match.id,
                round_number=r.round_number,
                player1_card_id=r.player1_card_id,
                player2_card_id=r.player2_card_id,
                winner_id=round_winner_id,
            )
        )

    db.commit()

    return {"id": match.id}
