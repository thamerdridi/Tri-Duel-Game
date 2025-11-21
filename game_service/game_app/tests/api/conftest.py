import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from game_app.main import app
from game_app.database.database import Base
from game_app.database.database import get_db
from game_app.database.init.initialize_cards import init_cards


@pytest.fixture
def client():
    # SHARED in-memory SQLite database for SQLAlchemy 2.x
    DATABASE_URL = "sqlite+pysqlite:///file:memdb1?mode=memory&cache=shared"

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

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)
