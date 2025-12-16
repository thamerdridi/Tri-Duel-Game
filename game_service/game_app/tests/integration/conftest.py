"""
==========================================
INTEGRATION TEST CONFIGURATION (FIXTURES)
==========================================

PURPOSE:
--------
Provides pytest fixtures for integration testing.
Sets up test database with real SQLAlchemy sessions.

FIXTURES PROVIDED:
------------------

1. `db_session` - SQLAlchemy database session
   - Use for: Testing service layer with real database
   - Features:
     * In-memory SQLite database (fast, ephemeral)
     * All tables created automatically
     * Card definitions pre-seeded
     * Auto-closed after test
     * Each test gets fresh database
   - Example usage:
     ```python
     def test_service_logic(db_session):
         service = MatchService(db_session)
         match = service.create_match("alice", "bob")
         assert match.id is not None
     ```

HOW IT WORKS:
-------------
1. Database Creation:
   - Creates in-memory SQLite database (sqlite:///:memory:)
   - Applies all schema migrations (Base.metadata.create_all)
   - Database exists only for duration of test

2. Card Seeding:
   - Calls init_cards() to populate card definitions
   - Cards are required for match creation
   - reset=True ensures clean state

3. Cleanup:
   - Session is automatically closed after test
   - Database is destroyed (in-memory)
   - No persistence between tests

NOTES:
------
- Each test gets isolated database
- No external services required
- Faster than using real database
- Perfect for testing business logic + database interaction
"""

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
