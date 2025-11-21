"""Pytest fixtures for Player Service tests."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test mode BEFORE importing the app
os.environ["TESTING"] = "1"

from app.main import app
from app.db import Base, get_db
from app.models import Card


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_test_cards(db):
    """Seed test database with cards."""
    cards_data = [
        ("rock", "Rock 10", 10), ("rock", "Rock 20", 20), ("rock", "Rock 30", 30),
        ("rock", "Rock 40", 40), ("rock", "Rock 50", 50), ("rock", "Rock 60", 60),
        ("paper", "Paper 10", 10), ("paper", "Paper 20", 20), ("paper", "Paper 30", 30),
        ("paper", "Paper 40", 40), ("paper", "Paper 50", 50), ("paper", "Paper 60", 60),
        ("scissors", "Scissors 10", 10), ("scissors", "Scissors 20", 20), ("scissors", "Scissors 30", 30),
        ("scissors", "Scissors 40", 40), ("scissors", "Scissors 50", 50), ("scissors", "Scissors 60", 60),
    ]
    
    for category, name, power in cards_data:
        card = Card(category=category, name=name, power=power)
        db.add(card)
    db.commit()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_test_cards(db)  # Add cards to test database
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_match_data():
    """Sample match data for testing."""
    return {
        "player1_external_id": "alice",
        "player2_external_id": "bob",
        "winner_external_id": "alice",
        "player1_score": 3,
        "player2_score": 2,
        "rounds": [
            {
                "round_number": 1,
                "player1_card_id": 1,
                "player2_card_id": 2,
                "winner_external_id": "alice"
            },
            {
                "round_number": 2,
                "player1_card_id": 3,
                "player2_card_id": 4,
                "winner_external_id": "bob"
            },
            {
                "round_number": 3,
                "player1_card_id": 5,
                "player2_card_id": 6,
                "winner_external_id": "alice"
            }
        ],
        "seed": "test-seed-123"
    }
