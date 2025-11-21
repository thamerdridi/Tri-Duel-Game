from sqlalchemy.orm import Session
from fastapi import HTTPException

from game_app.configs.cards_config import DOMAIN_CARDS
from game_app.database.models import Match, MatchCard, CardDefinition
from game_app.configs.logic_configs import MAX_ROUNDS
from game_app.logic.models import Card
from game_app.logic.rps import rps_outcome
from game_app.logic.deck import build_deck, deal_two_hands


class MatchService:

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # CREATE MATCH
    # ============================================================
    def create_match(self, player1_id: str, player2_id: str):
        card_defs = (
            self.db.query(CardDefinition)
            .filter(CardDefinition.active == True)
            .all()
        )

        full_deck = build_deck(card_defs)
        deck_p1, deck_p2 = deal_two_hands(full_deck)

        match = Match(
            player1_id=player1_id,
            player2_id=player2_id,
            status="in_progress",
            current_round=1,
            points_p1=0,
            points_p2=0,
            winner=None,
        )

        self.db.add(match)
        self.db.flush()

        for card in deck_p1:
            self._save_match_card(match.id, player1_id, card)

        for card in deck_p2:
            self._save_match_card(match.id, player2_id, card)

        self.db.commit()
        self.db.refresh(match)
        return match

    def _save_match_card(self, match_id, player_id, card: Card):
        mc = MatchCard(
            match_id=match_id,
            player_id=player_id,
            card_def_id=card.id,
            used=False,
            round_used=None,
        )
        self.db.add(mc)

    # ============================================================
    # SUBMIT MOVE
    # ============================================================
    def submit_move(self, match_id: str, player_id: str, match_card_id: int):
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            raise ValueError("Match not found")

        if match.status != "in_progress":
            raise ValueError("Match already finished")

        card = (
            self.db.query(MatchCard)
            .filter_by(id=match_card_id, match_id=match_id, player_id=player_id)
            .first()
        )

        if not card:
            raise ValueError("Invalid card or player")
        if card.used:
            raise ValueError("Card already used")

        card.used = True
        card.round_used = match.current_round
        self.db.commit()

        other_card = (
            self.db.query(MatchCard)
            .filter(
                MatchCard.match_id == match_id,
                MatchCard.player_id != player_id,
                MatchCard.round_used == match.current_round,
            )
            .first()
        )

        if not other_card:
            return {"status": "waiting_for_opponent"}

        return self._resolve_round(match, card, other_card)

    # ============================================================
    # RESOLVE ROUND
    # ============================================================
    def _resolve_round(self, match: Match, card_p1: MatchCard, card_p2: MatchCard):
        c1_def, c2_def = (
            self.db.query(CardDefinition)
            .filter(CardDefinition.id.in_([card_p1.card_def_id, card_p2.card_def_id]))
            .all()
        )

        defs = {c.id: c for c in (c1_def, c2_def)}
        c1_def = defs[card_p1.card_def_id]
        c2_def = defs[card_p2.card_def_id]

        card1 = Card(**c1_def.to_domain_dict())
        card2 = Card(**c2_def.to_domain_dict())

        result = rps_outcome(card1, card2)

        if result.winner == "p1":
            match.points_p1 += 1
        elif result.winner == "p2":
            match.points_p2 += 1

        match.current_round += 1

        if match.current_round > MAX_ROUNDS:
            match.status = "finished"
            if match.points_p1 > match.points_p2:
                match.winner = match.player1_id
            elif match.points_p2 > match.points_p1:
                match.winner = match.player2_id
            else:
                match.winner = None

        self.db.commit()
        self.db.refresh(match)

        return {
            "round": match.current_round - 1,
            "winner": result.winner,
            "reason": result.reason,
            "points_p1": match.points_p1,
            "points_p2": match.points_p2,
            "match_finished": match.status == "finished",
            "match_winner": match.winner,
        }

    # ============================================================
    # GET PLAYER HAND (unused cards)
    # ============================================================
    def get_player_hand(self, match_id: str, player_id: str):
        cards = (
            self.db.query(MatchCard)
            .filter_by(match_id=match_id, player_id=player_id, used=False)
            .all()
        )

        card_defs = self.db.query(CardDefinition).all()
        defs = {d.id: d for d in card_defs}


        return [
            {
                "match_card_id": c.id,
                "card": {
                    domain_key: getattr(defs[c.card_def_id], db_field)
                    for domain_key, db_field in DOMAIN_CARDS.items()
                }
            }
            for c in cards
        ]

    # ============================================================
    # GET USED CARDS FOR ONE PLAYER
    # ============================================================
    def get_used_cards_by_player(self, match_id: str, player_id: str):
        used_cards = (
            self.db.query(MatchCard)
            .filter_by(match_id=match_id, player_id=player_id, used=True)
            .all()
        )

        # Load all card definitions
        card_defs = self.db.query(CardDefinition).all()
        defs = {d.id: d for d in card_defs}

        result = []
        for c in used_cards:
            card_def = defs[c.card_def_id]

            # Dynamic domain card fields
            card_dict = {
                domain_key: getattr(card_def, db_field)
                for domain_key, db_field in DOMAIN_CARDS.items()
            }

            result.append({
                "match_card_id": c.id,
                "card": card_dict,
                "round_used": c.round_used,
            })

        return result

    # ============================================================
    # GET COMPLETE MATCH STATE
    # ============================================================
    def get_state(self, match_id: str, player_id: str):
        match = self.db.query(Match).filter_by(id=match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        opponent_id = (
            match.player2_id if match.player1_id == player_id else match.player1_id
        )

        return {
            "match_id": match.id,
            "status": match.status,
            "current_round": match.current_round,
            "points_p1": match.points_p1,
            "points_p2": match.points_p2,
            "player_hand": self.get_player_hand(match_id, player_id),
            "used_cards": self.get_used_cards_by_player(match_id, player_id),
            "opponent_used_cards": self.get_used_cards_by_player(match_id, opponent_id),
            "match_winner": match.winner,
        }
