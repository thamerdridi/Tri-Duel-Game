from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..db import get_db
from ..models import PlayerProfile, Match, MatchRound, Card
from ..schemas import (
    MatchSummaryOut,
    MatchDetailOut,
    MatchRoundOut,
    CardOut,
    LeaderboardEntry,
)


router = APIRouter(
    tags=["players"],
)


def _match_to_summary(m: Match, db: Session) -> MatchSummaryOut:
    p1 = db.get(PlayerProfile, m.player1_id)
    p2 = db.get(PlayerProfile, m.player2_id)
    winner_external_id = None
    if m.winner_id is not None:
        w = db.get(PlayerProfile, m.winner_id)
        winner_external_id = w.external_id if w else None

    return MatchSummaryOut(
        id=m.id,
        player1_external_id=p1.external_id if p1 else "",
        player2_external_id=p2.external_id if p2 else "",
        winner_external_id=winner_external_id,
        player1_score=m.player1_score,
        player2_score=m.player2_score,
        rounds_played=m.rounds_played,
        created_at=m.created_at,
        finished_at=m.finished_at,
    )


@router.get("/players/{player_external_id}/matches", response_model=List[MatchSummaryOut])
def list_player_matches(
    player_external_id: str,
    db: Session = Depends(get_db),
):
    player = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.external_id == player_external_id)
        .first()
    )
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    matches = (
        db.query(Match)
        .filter(
            or_(
                Match.player1_id == player.id,
                Match.player2_id == player.id,
            )
        )
        .order_by(Match.created_at.desc())
        .all()
    )

    return [_match_to_summary(m, db) for m in matches]


@router.get(
    "/players/{player_external_id}/matches/{match_id}",
    response_model=MatchDetailOut,
)
def get_player_match_detail(
    player_external_id: str,
    match_id: int,
    db: Session = Depends(get_db),
):
    player = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.external_id == player_external_id)
        .first()
    )
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    # Ensure this player participated in the match
    if match.player1_id != player.id and match.player2_id != player.id:
        raise HTTPException(status_code=404, detail="Match not found for this player")

    # Build summary
    summary = _match_to_summary(match, db)

    # Build rounds detail
    rounds = (
        db.query(MatchRound)
        .filter(MatchRound.match_id == match.id)
        .order_by(MatchRound.round_number)
        .all()
    )

    round_out_list: List[MatchRoundOut] = []
    for r in rounds:
        p1_card = db.get(Card, r.player1_card_id)
        p2_card = db.get(Card, r.player2_card_id)

        if p1_card is None or p2_card is None:
            # If something is wrong in DB, skip this round rather than crash
            continue

        winner_external_id = None
        if r.winner_id is not None:
            w = db.get(PlayerProfile, r.winner_id)
            winner_external_id = w.external_id if w else None

        round_out_list.append(
            MatchRoundOut(
                round_number=r.round_number,
                player1_card=CardOut.model_validate(p1_card),
                player2_card=CardOut.model_validate(p2_card),
                winner_external_id=winner_external_id,
            )
        )

    return MatchDetailOut(
        **summary.dict(),
        rounds=round_out_list,
    )


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    players = db.query(PlayerProfile).all()
    matches = db.query(Match).all()

    # stats keyed by player.id
    stats = {p.id: {"wins": 0, "matches": 0} for p in players}

    for m in matches:
        if m.player1_id in stats:
            stats[m.player1_id]["matches"] += 1
        if m.player2_id in stats:
            stats[m.player2_id]["matches"] += 1
        if m.winner_id is not None and m.winner_id in stats:
            stats[m.winner_id]["wins"] += 1

    entries: List[LeaderboardEntry] = []
    for p in players:
        s = stats[p.id]
        if s["matches"] == 0:
            continue  # skip players with no matches
        entries.append(
            LeaderboardEntry(
                external_id=p.external_id,
                username=p.username,
                wins=s["wins"],
                matches=s["matches"],
            )
        )

    # Sort: most wins first, then most matches, then username
    entries.sort(key=lambda e: (-e.wins, -e.matches, e.username.lower()))

    return entries
