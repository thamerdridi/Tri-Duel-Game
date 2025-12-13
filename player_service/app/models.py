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

from .db import Base


class PlayerProfile(Base):
    __tablename__ = "player_profiles"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(64), unique=True, index=True, nullable=False)
    username = Column(String(50), nullable=False)
    bio = Column(Text, nullable=True)
    country = Column(String(40), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(16), nullable=False)  # "rock" | "paper" | "scissors"
    power = Column(SmallInteger, nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)

    player1_id = Column(Integer, ForeignKey("player_profiles.id"), nullable=False)
    player2_id = Column(Integer, ForeignKey("player_profiles.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("player_profiles.id"), nullable=True)

    player1_score = Column(SmallInteger, default=0, nullable=False)
    player2_score = Column(SmallInteger, default=0, nullable=False)

    seed = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
