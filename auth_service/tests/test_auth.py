import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine
from app.models import Base, User, RefreshToken, BlacklistedToken

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Clear all data before each test
    db = SessionLocal()
    try:
        # Delete in order to avoid foreign key issues
        db.query(RefreshToken).delete()
        db.query(BlacklistedToken).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()

def test_register():
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    })
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_login():
    # First register
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    })
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "TestPass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

def test_refresh_token():
    # First register and login to get refresh token
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    })
    login_resp = client.post("/auth/login", json={
        "username": "testuser",
        "password": "TestPass123"
    })
    refresh_token = login_resp.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_logout():
    # First register and login
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    })
    login_resp = client.post("/auth/login", json={
        "username": "testuser",
        "password": "TestPass123"
    })
    access_token = login_resp.json()["access_token"]

    response = client.post("/auth/logout", params={"token": access_token})
    assert response.status_code == 200

    # Validate should fail
    validate_resp = client.get("/auth/validate", params={"token": access_token})
    assert validate_resp.status_code == 401

def test_validate_token():
    # First register and login
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    })
    login_resp = client.post("/auth/login", json={
        "username": "testuser",
        "password": "TestPass123"
    })
    access_token = login_resp.json()["access_token"]

    response = client.get("/auth/validate", params={"token": access_token})
    assert response.status_code == 200

def test_password_strength():
    # Weak password
    response = client.post("/auth/register", json={
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "weak"
    })
    assert response.status_code == 422  # Validation error
