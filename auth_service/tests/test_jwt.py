import pytest
from jose import jwt
from app.config import settings
from app.auth.jwt_handler import create_access_token, verify_token


def test_token_creation_and_validation():
    subject = "testuser"
    user_id = 1

    token = create_access_token(subject=subject, user_id=user_id)
    assert token is not None

    decoded = verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == subject
    assert decoded["user_id"] == user_id
    assert decoded["iss"] == "triduel-auth"

