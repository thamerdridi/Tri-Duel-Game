from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    SmallInteger,
    Text,
)
from sqlalchemy.orm import relationship

from .db import Base


class PlayerProfile(Base):
    __tablename__ = "player_profiles"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(64), unique=True, index=True, nullable=False)
    username = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    external_match_id = Column(String(128), unique=True, index=True, nullable=False)

    player1_id = Column(Integer, ForeignKey("player_profiles.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("player_profiles.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("player_profiles.id"), nullable=True)

    player1_score = Column(SmallInteger, default=0, nullable=False)
    player2_score = Column(SmallInteger, default=0, nullable=False)

    moves_log = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    turns = relationship(
        "MatchTurn",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchTurn.turn_number",
    )


class MatchTurn(Base):
    __tablename__ = "match_turns"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, index=True)

    turn_number = Column(SmallInteger, nullable=False)

    player1_card_name = Column(String(64), nullable=False)
    player2_card_name = Column(String(64), nullable=False)

    winner_id = Column(Integer, ForeignKey("player_profiles.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    match = relationship("Match", back_populates="turns")
