from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..auth import get_current_user
from ..db import get_db
from ..models import PlayerProfile, Match, MatchTurn
from ..schemas import (
    MatchSummaryOut,
    MatchDetailOut,
    MatchTurnOut,
    PlayerProfileOut,
    PlayerProfileUpdate,
    LeaderboardEntry,
)


router = APIRouter(
    tags=["players"],
)


@router.post("/players", response_model=PlayerProfileOut)
async def create_player_profile(
    payload: PlayerProfileUpdate,
    response: Response,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    external_id = user.get("sub")
    if not external_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    profile = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.external_id == external_id)
        .first()
    )

    if profile is None:
        profile = PlayerProfile(
            external_id=external_id,
            username=payload.username or external_id,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        response.status_code = 201
        return profile

    updated = False
    if payload.username is not None:
        profile.username = payload.username
        updated = True

    if updated:
        db.commit()
        db.refresh(profile)

    response.status_code = 200
    return profile


@router.get("/players/me", response_model=PlayerProfileOut)
async def get_my_profile(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    external_id = user.get("sub")
    if not external_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    profile = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.external_id == external_id)
        .first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return profile


def _match_to_summary(m: Match, db: Session) -> MatchSummaryOut:
    p1 = db.get(PlayerProfile, m.player1_id)
    p2 = db.get(PlayerProfile, m.player2_id)
    winner_external_id = None
    if m.winner_id is not None:
        w = db.get(PlayerProfile, m.winner_id)
        winner_external_id = w.external_id if w else None

    return MatchSummaryOut(
        id=m.id,
        external_match_id=m.external_match_id,
        player1_external_id=p1.external_id if p1 else "",
        player2_external_id=p2.external_id if p2 else "",
        winner_external_id=winner_external_id,
        player1_score=m.player1_score,
        player2_score=m.player2_score,
        created_at=m.created_at,
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

    if match.player1_id != player.id and match.player2_id != player.id:
        raise HTTPException(status_code=404, detail="Match not found for this player")

    turns = (
        db.query(MatchTurn)
        .filter(MatchTurn.match_id == match.id)
        .order_by(MatchTurn.turn_number)
        .all()
    )

    turn_out: list[MatchTurnOut] = []
    for t in turns:
        winner_external_id = None
        if t.winner_id is not None:
            w = db.get(PlayerProfile, t.winner_id)
            winner_external_id = w.external_id if w else None

        turn_out.append(
            MatchTurnOut(
                turn_number=t.turn_number,
                player1_card_name=t.player1_card_name,
                player2_card_name=t.player2_card_name,
                winner_external_id=winner_external_id,
            )
        )

    summary = _match_to_summary(match, db)
    return MatchDetailOut(**summary.model_dump(), turns=turn_out)


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(db: Session = Depends(get_db)):
    players = db.query(PlayerProfile).all()
    matches = db.query(Match).all()

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
            continue
        entries.append(
            LeaderboardEntry(
                external_id=p.external_id,
                username=p.username,
                wins=s["wins"],
                matches=s["matches"],
            )
        )

    entries.sort(key=lambda e: (-e.wins, -e.matches, e.username.lower()))

    return entries
