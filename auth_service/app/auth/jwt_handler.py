from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.config import settings


def create_access_token(subject: str, user_id: int):
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "user_id": user_id,
        "exp": expire,
        "iss": "triduel-auth"
    }

    return jwt.encode(
        payload,
        settings.load_private_key(),
        algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str):
    try:
        return jwt.decode(
            token,
            settings.load_public_key(),
            algorithms=[settings.JWT_ALGORITHM],
            audience=None,
            issuer="triduel-auth"
        )
    except JWTError:
        return None
