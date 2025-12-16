"""
==========================================
API TEST CONFIGURATION (FIXTURES)
==========================================

PURPOSE:
--------
Provides pytest fixtures for API testing with FastAPI TestClient.
Configures test database, authentication mocking, and test client setup.

FIXTURES PROVIDED:
------------------

1. `client` - TestClient with mocked authentication
   - Use for: Normal functional tests where auth is not the focus
   - Features:
     * In-memory SQLite database (ephemeral, reset each test)
     * Card definitions auto-seeded
     * Authentication MOCKED (auto-accepts Bearer tokens)
     * Extracts username from token format: "Bearer <username>_token"
   - Example usage:
     ```python
     def test_something(client):
         response = client.post("/matches/",
             json={"player1_id": "alice", "player2_id": "bob"},
             headers={"Authorization": "Bearer alice_token"})
     ```

2. `client_no_auth` - TestClient WITHOUT mocked authentication
   - Use for: Testing authentication behavior (401, 403 responses)
   - Features:
     * In-memory SQLite database (ephemeral, reset each test)
     * Card definitions auto-seeded
     * Authentication NOT mocked (uses real auth.py logic)
     * Will fail auth checks without proper token handling
   - Example usage:
     ```python
     def test_auth_required(client_no_auth):
         response = client_no_auth.post("/matches/", json={...})
         assert response.status_code == 401  # No token provided
     ```

HOW IT WORKS:
-------------
1. Database Setup:
   - Creates in-memory SQLite database
   - Applies all schema migrations (Base.metadata.create_all)
   - Seeds card definitions using init_cards()

2. Dependency Override:
   - Overrides `get_db` to use test database
   - Overrides `get_current_user` (only in `client` fixture)

3. Mock Authentication (client fixture only):
   - Mock function signature matches real function exactly
   - Accepts any Bearer token
   - Extracts username: "Bearer alice_token" → {"sub": "alice", "user_id": 123}
   - Returns mock user data for authorization checks

4. Cleanup:
   - Clears dependency overrides after each test
   - Database is automatically destroyed (in-memory)

NOTES:
------
- Each test gets a fresh database (isolation guaranteed)
- Tests run in parallel-safe manner (separate database per test)
- No external services required (auth is mocked)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from game_app.main import app
from game_app.database.database import Base
from game_app.database.database import get_db
from game_app.database.init.initialize_cards import init_cards


@pytest.fixture
def client():
    # Unique in-memory SQLite database per fixture to avoid test cross-talk
    unique_name = uuid4().hex
    DATABASE_URL = f"sqlite+pysqlite:///file:memdb_{unique_name}?mode=memory&cache=shared"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    TestingSessionLocal = sessionmaker(bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Seed card definitions
    db = TestingSessionLocal()
    init_cards(db, reset=True)
    db.commit()
    db.close()

    # Override DB dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Mock authentication dependency
    from fastapi import Header
    from typing import Optional

    async def mock_get_current_user(authorization: Optional[str] = Header(None)):
        """
        Mock authentication for tests.
        Accepts any Bearer token and extracts username from it.
        Format: "Bearer <username>_token" or "Bearer <username>"
        """
        if not authorization or not authorization.startswith("Bearer "):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing"
            )

        # Extract username from token
        token = authorization.split(" ")[1]
        # Remove "_token" suffix if present
        username = token.replace("_token", "").replace("token", "")

        # Default to "alice" if token is generic
        if not username or username == "valid_" or username == "expired_":
            username = "alice"

        return {
            "sub": username,
            "user_id": 123,
            "exp": 9999999999
        }

    from game_app.clients.auth_client import get_current_user

    # Apply overrides BEFORE creating TestClient
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = mock_get_current_user

    # Create test client
    test_client = TestClient(app)

    yield test_client

    # Clean up dependency overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth():
    """
    Client fixture WITHOUT authentication mocking.
    Used for authentication tests that need to test real auth behavior.
    """
    # Unique in-memory SQLite database per fixture to avoid test cross-talk
    unique_name = uuid4().hex
    DATABASE_URL = f"sqlite+pysqlite:///file:memdb_{unique_name}?mode=memory&cache=shared"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    TestingSessionLocal = sessionmaker(bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Seed card definitions
    db = TestingSessionLocal()
    init_cards(db, reset=True)
    db.commit()
    db.close()

    # Override DB dependency only (NOT auth)
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Apply overrides BEFORE creating TestClient
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    test_client = TestClient(app)

    yield test_client

    # Clean up dependency overrides after test
    app.dependency_overrides.clear()
