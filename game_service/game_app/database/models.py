from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from .database import Base
from game_app.configs.cards_config import *
import uuid  # Re-added to resolve unresolved reference for uuid

DOMAIN_CARDS = os.getenv(
    "DOMAIN_CARDS",
    DOMAIN_CARDS
)

class CardDefinition(Base):
    __tablename__ = "card_definitions"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(10), nullable=False)
    power = Column(Integer, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    def to_domain_dict(self):
        return {
            domain_key: getattr(self, db_key)
            for domain_key, db_key in DOMAIN_CARDS.items()
        }


class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player1_id = Column(String, nullable=False)
    player2_id = Column(String, nullable=False)
    status = Column(String(20), nullable=False, default="in_progress")
    current_round = Column(Integer, nullable=False, default=1)
    points_p1 = Column(Integer, nullable=False, default=0)
    points_p2 = Column(Integer, nullable=False, default=0)
    winner = Column(String, nullable=True, default=None) # Ensure default=None for winner to match expected type


class MatchCard(Base):
    __tablename__ = "match_cards"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(ForeignKey("matches.id", ondelete="CASCADE"))
    player_id = Column(String, nullable=True)
    card_def_id = Column(ForeignKey("card_definitions.id"))
    used = Column(Boolean, default=False, nullable=False)
    round_used = Column(Integer, nullable=True)

class MatchRound(Base):
    __tablename__ = "match_rounds"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(ForeignKey("matches.id", ondelete="CASCADE"))
    match_card_p1 = Column(ForeignKey("match_cards.id"))
    match_card_p2 = Column(ForeignKey("match_cards.id"))
    winner_id = Column(String, nullable=True) # None -> draw
    round_number = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)






