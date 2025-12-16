import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    os.environ["TESTING"] = "1"

    service_root = Path(__file__).resolve().parents[1]
    # Ensure the player_service package is first on sys.path so we don't
    # accidentally import another sibling service's `app` package when running
    # tests from the monorepo root.
    sys.path = [str(service_root)] + [p for p in sys.path if p != str(service_root)]
    for mod in list(sys.modules):
        if mod == "app" or mod.startswith("app."):
            sys.modules.pop(mod, None)

    from app import db as db_module
    from app.db import Base
    from app.main import app
    import app.main as main_module

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    monkeypatch.setattr(db_module, "engine", engine, raising=True)
    monkeypatch.setattr(db_module, "SessionLocal", TestingSessionLocal, raising=True)
    monkeypatch.setattr(main_module, "engine", engine, raising=False)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[db_module.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
