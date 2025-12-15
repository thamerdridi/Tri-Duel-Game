import os
from typing import Optional

import httpx
import secrets
from fastapi import Header, HTTPException, status


AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
PLAYER_INTERNAL_API_KEY = os.getenv("PLAYER_INTERNAL_API_KEY")


async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    token = authorization.split(" ", 1)[1]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/auth/validate",
                params={"token": token},
                timeout=5.0
            )

        if response.status_code == 200:
            return response.json()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )


async def require_internal_api_key(
    x_internal_api_key: Optional[str] = Header(None, alias="X-Internal-Api-Key"),
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
) -> None:
    provided_key = x_internal_api_key or x_api_key
    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Internal API key missing",
        )

    if not PLAYER_INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal API key not configured",
        )

    if not secrets.compare_digest(provided_key, PLAYER_INTERNAL_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    return await verify_token(authorization)


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None

    try:
        return await verify_token(authorization)
    except HTTPException:
        return None
