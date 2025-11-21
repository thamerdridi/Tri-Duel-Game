import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from game_app.database.database import Base
from game_app.database.models import *
from game_app.database.init.initialize_cards import init_cards


@pytest.fixture
def db_session():
    """
    Creates a fresh in-memory SQLite DB for each test.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Seed card definitions
    db = TestingSessionLocal()
    init_cards(db, reset=True)
    db.commit()

    try:
        yield db
    finally:
        db.close()
